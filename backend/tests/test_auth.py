import sys
from pathlib import Path
import time
import unittest
from unittest.mock import MagicMock

# Ensure backend directory is in python search path
backend_dir = Path(__file__).resolve().parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

import jwt
from cryptography.hazmat.primitives.asymmetric import rsa
from flask import Flask, jsonify

from app import create_app
from app.extensions import db
from app.models import Role, User
from app.services.cognito_auth_service import (
    CognitoAuthService,
    ConfigurationError,
    InvalidTokenError,
    TokenExpiredError,
)
from app.utils.auth_decorators import cognito_required, get_current_cognito_sub, get_current_user


class TestCognitoAuthentication(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Generate an in-memory RSA keypair for cryptographic testing
        cls.private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048,
        )
        cls.public_key = cls.private_key.public_key()
        cls.kid = "test-key-id-1"

        # Another keypair to test signature tampering/mismatches
        cls.wrong_private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048,
        )

        # Standard test configuration
        cls.test_region = "us-east-1"
        cls.test_user_pool_id = "us-east-1_TestPool123"
        cls.test_client_id = "test-client-id-abc"
        cls.expected_issuer = f"https://cognito-idp.{cls.test_region}.amazonaws.com/{cls.test_user_pool_id}"

        # Flask app for testing
        cls.app = create_app()
        cls.app.config["TESTING"] = True

    def setUp(self):
        # Set up a mock JWKS client that returns the test public key
        mock_jwk = MagicMock()
        mock_jwk.key = self.public_key

        self.mock_jwks_client = MagicMock()
        self.mock_jwks_client.get_signing_key_from_jwt.return_value = mock_jwk

        self.auth_service = CognitoAuthService(
            region=self.test_region,
            user_pool_id=self.test_user_pool_id,
            client_id=self.test_client_id,
            jwk_client=self.mock_jwks_client,
        )

    def _generate_token(
        self,
        payload_overrides=None,
        headers_overrides=None,
        signing_key=None,
    ) -> str:
        """Helper to create cryptographically signed test JWT tokens."""
        now = int(time.time())
        payload = {
            "sub": "test-cognito-sub-12345",
            "iss": self.expected_issuer,
            "aud": self.test_client_id,
            "token_use": "id",
            "exp": now + 3600,
            "iat": now,
            "auth_time": now,
        }
        if payload_overrides:
            payload.update(payload_overrides)

        headers = {
            "kid": self.kid,
            "alg": "RS256",
        }
        if headers_overrides:
            headers.update(headers_overrides)

        key = signing_key or self.private_key
        return jwt.encode(payload, key, algorithm="RS256", headers=headers)

    # ---------------------------------------------------------
    # 1. Cryptographic and Claim Validation Tests
    # ---------------------------------------------------------

    def test_valid_id_token_verification(self):
        token = self._generate_token({"token_use": "id", "sub": "user-uuid-1"})
        claims = self.auth_service.validate_token(token)

        self.assertEqual(claims["sub"], "user-uuid-1")
        self.assertEqual(claims["token_use"], "id")
        self.assertEqual(claims["iss"], self.expected_issuer)
        self.assertEqual(claims["aud"], self.test_client_id)

    def test_valid_access_token_verification(self):
        token = self._generate_token({
            "token_use": "access",
            "client_id": self.test_client_id,
            "sub": "user-uuid-2",
        })
        claims = self.auth_service.validate_token(token)

        self.assertEqual(claims["sub"], "user-uuid-2")
        self.assertEqual(claims["token_use"], "access")
        self.assertEqual(claims["client_id"], self.test_client_id)

    def test_invalid_signature_is_rejected(self):
        # Signed with a different private key that does not match the public key in JWKS
        token = self._generate_token(signing_key=self.wrong_wrong_key if hasattr(self, 'wrong_wrong_key') else self.wrong_private_key)
        with self.assertRaises(InvalidTokenError) as ctx:
            self.auth_service.validate_token(token)
        self.assertIn("signature verification failed", str(ctx.exception).lower())

    def test_expired_token_is_rejected(self):
        token = self._generate_token({"exp": int(time.time()) - 100})
        with self.assertRaises(TokenExpiredError):
            self.auth_service.validate_token(token)

    def test_wrong_issuer_is_rejected(self):
        token = self._generate_token({"iss": "https://cognito-idp.us-west-2.amazonaws.com/us-west-2_WrongPool"})
        with self.assertRaises(InvalidTokenError) as ctx:
            self.auth_service.validate_token(token)
        self.assertIn("issuer", str(ctx.exception).lower())

    def test_wrong_client_id_is_rejected(self):
        token = self._generate_token({"aud": "wrong-client-id"})
        with self.assertRaises(InvalidTokenError) as ctx:
            self.auth_service.validate_token(token)
        self.assertIn("client id", str(ctx.exception).lower())

    def test_missing_sub_claim_is_rejected(self):
        now = int(time.time())
        payload = {
            "iss": self.expected_issuer,
            "aud": self.test_client_id,
            "token_use": "id",
            "exp": now + 3600,
        }
        token = jwt.encode(payload, self.private_key, algorithm="RS256", headers={"kid": self.kid})
        with self.assertRaises(InvalidTokenError) as ctx:
            self.auth_service.validate_token(token)
        self.assertIn("sub", str(ctx.exception).lower())

    def test_unsupported_algorithm_is_rejected(self):
        # Even if token is valid HMAC, only RS256 must be accepted
        payload = {
            "sub": "user-uuid-3",
            "iss": self.expected_issuer,
            "aud": self.test_client_id,
            "token_use": "id",
            "exp": int(time.time()) + 3600,
        }
        token = jwt.encode(payload, "a" * 32, algorithm="HS256", headers={"kid": self.kid})
        with self.assertRaises(InvalidTokenError) as ctx:
            self.auth_service.validate_token(token)
        self.assertIn("only rs256 is supported", str(ctx.exception).lower())

    def test_missing_configuration_raises_error(self):
        unconfigured_service = CognitoAuthService(
            region=None,
            user_pool_id=None,
        )
        with self.app.app_context():
            # Clear config temporarily to verify fail-fast error
            self.app.config["COGNITO_REGION"] = None
            self.app.config["AWS_REGION"] = None
            with self.assertRaises(ConfigurationError):
                unconfigured_service.validate_token("dummy.token.here")

    # ---------------------------------------------------------
    # 2. Reusable Route Decorator Tests (@cognito_required)
    # ---------------------------------------------------------

    def test_decorator_missing_auth_header(self):
        test_app = create_app()

        @test_app.get("/test-protected-1")
        @cognito_required(auth_service=self.auth_service)
        def protected_route():
            return jsonify({"status": "success"}), 200

        client = test_app.test_client()
        res = client.get("/test-protected-1")
        self.assertEqual(res.status_code, 401)
        self.assertEqual(res.get_json()["status"], "error")

    def test_decorator_malformed_auth_header(self):
        test_app = create_app()

        @test_app.get("/test-protected-2")
        @cognito_required(auth_service=self.auth_service)
        def protected_route():
            return jsonify({"status": "success"}), 200

        client = test_app.test_client()
        res = client.get("/test-protected-2", headers={"Authorization": "Basic dXNlcjpwYXNz"})
        self.assertEqual(res.status_code, 401)
        self.assertIn("Bearer", res.get_json()["message"])

    def test_decorator_valid_token_populates_context(self):
        test_app = create_app()
        target_sub = "cognito-user-abc-123"

        @test_app.get("/test-protected-3")
        @cognito_required(auth_service=self.auth_service)
        def protected_route():
            sub = get_current_cognito_sub()
            return jsonify({"status": "success", "sub": sub}), 200

        token = self._generate_token({"sub": target_sub})
        client = test_app.test_client()
        res = client.get("/test-protected-3", headers={"Authorization": f"Bearer {token}"})

        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.get_json()["sub"], target_sub)

    def test_decorator_expired_token_returns_401(self):
        test_app = create_app()

        @test_app.get("/test-protected-4")
        @cognito_required(auth_service=self.auth_service)
        def protected_route():
            return jsonify({"status": "success"}), 200

        token = self._generate_token({"exp": int(time.time()) - 50})
        client = test_app.test_client()
        res = client.get("/test-protected-4", headers={"Authorization": f"Bearer {token}"})

        self.assertEqual(res.status_code, 401)
        self.assertIn("expired", res.get_json()["message"].lower())

    # ---------------------------------------------------------
    # 3. Cognito sub mapping to users.auth_id
    # ---------------------------------------------------------

    def test_cognito_sub_maps_to_pawconnect_user(self):
        test_sub = "cognito-sub-mapping-test-uuid"

        with self.app.app_context():
            # Clean up test user if exists
            existing = User.query.filter_by(auth_id=test_sub).first()
            if existing:
                db.session.delete(existing)
                db.session.commit()

            # Ensure a test role exists
            role = Role.query.first()
            if not role:
                role = Role(role_name="TestRole")
                db.session.add(role)
                db.session.commit()

            # Create PawConnect user with auth_id = test_sub
            user = User(
                name="Test Cognito User",
                email="cognito_test@example.com",
                role_id=role.role_id,
                auth_id=test_sub,
            )
            db.session.add(user)
            db.session.commit()

            try:
                # Lookup via auth service
                found_user = self.auth_service.get_user_by_auth_id(test_sub)
                self.assertIsNotNone(found_user)
                self.assertEqual(found_user.auth_id, test_sub)
                self.assertEqual(found_user.email, "cognito_test@example.com")

                # Test unknown sub returns None (distinguishing auth from DB profile)
                unknown_user = self.auth_service.get_user_by_auth_id("non-existent-sub")
                self.assertIsNone(unknown_user)
            finally:
                db.session.delete(user)
                if role.role_name == "TestRole":
                    db.session.delete(role)
                db.session.commit()


if __name__ == "__main__":
    unittest.main()
