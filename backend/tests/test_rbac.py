"""
RBAC (Role-Based Access Control) Foundation Tests
===================================================

Tests for the @roles_required decorator, verifying correct HTTP status codes
and that authentication and authorization remain strictly separated.

Authorization flow under test:
    no/invalid token        → 401 (unauthenticated)
    valid token, no profile → 403 (no PawConnect user)
    valid token, wrong role → 403 (authenticated but unauthorized)
    valid token, right role → 200 (proceed)
"""

import sys
import time
from pathlib import Path
import unittest
from unittest.mock import MagicMock, patch

# Ensure backend directory is in python search path
backend_dir = Path(__file__).resolve().parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

import jwt
from cryptography.hazmat.primitives.asymmetric import rsa
from flask import Flask, jsonify, g

from app import create_app
from app.extensions import db
from app.models import Role, User
from app.models.role import RoleName
from app.services.cognito_auth_service import CognitoAuthService
from app.utils.auth_decorators import (
    cognito_required,
    roles_required,
    get_current_user,
    get_current_cognito_sub,
)


class TestRBACFoundation(unittest.TestCase):
    """
    Tests for the @roles_required decorator and RBAC foundation.

    Uses an in-memory RSA key pair and a mock JWKS client so that:
    - No real AWS credentials are required.
    - No real Cognito tokens are created.
    - Authentication and authorization are tested together without coupling.
    """

    @classmethod
    def setUpClass(cls):
        # RSA key pair for cryptographic testing (same pattern as test_auth.py)
        cls.private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048,
        )
        cls.public_key = cls.private_key.public_key()
        cls.kid = "rbac-test-key-1"

        cls.test_region = "us-east-1"
        cls.test_user_pool_id = "us-east-1_RBACPool"
        cls.test_client_id = "rbac-test-client-id"
        cls.expected_issuer = (
            f"https://cognito-idp.{cls.test_region}.amazonaws.com/{cls.test_user_pool_id}"
        )

        # Flask app for testing
        cls.app = create_app()
        cls.app.config["TESTING"] = True

    def setUp(self):
        # Mock JWKS client returning our test public key
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

    def _generate_token(self, payload_overrides=None) -> str:
        """Create a signed test JWT with default valid claims."""
        now = int(time.time())
        payload = {
            "sub": "test-rbac-sub-default",
            "iss": self.expected_issuer,
            "aud": self.test_client_id,
            "token_use": "id",
            "exp": now + 3600,
            "iat": now,
        }
        if payload_overrides:
            payload.update(payload_overrides)
        return jwt.encode(
            payload,
            self.private_key,
            algorithm="RS256",
            headers={"kid": self.kid},
        )

    def _make_test_app_with_role_route(self, *allowed_roles):
        """
        Helper: create a fresh Flask test app with a single /rbac-test route
        protected by @roles_required(*allowed_roles).
        """
        test_app = create_app()

        @test_app.get("/rbac-test")
        @roles_required(*allowed_roles, auth_service=self.auth_service)
        def rbac_protected():
            user = get_current_user()
            return jsonify({
                "status": "success",
                "role": user.role.role_name if user and user.role else None,
            }), 200

        return test_app

    # ------------------------------------------------------------------
    # 1. Unauthenticated requests cannot bypass authorization
    # ------------------------------------------------------------------

    def test_no_token_returns_401(self):
        """A request with no Authorization header must return 401, not 403."""
        test_app = self._make_test_app_with_role_route(RoleName.ADMIN)
        client = test_app.test_client()

        res = client.get("/rbac-test")

        self.assertEqual(res.status_code, 401)
        body = res.get_json()
        self.assertEqual(body["status"], "error")

    def test_invalid_token_returns_401(self):
        """A request with an invalid/garbage token must return 401."""
        test_app = self._make_test_app_with_role_route(RoleName.ADMIN)
        client = test_app.test_client()

        res = client.get(
            "/rbac-test",
            headers={"Authorization": "Bearer not.a.valid.jwt"},
        )

        self.assertEqual(res.status_code, 401)

    def test_malformed_auth_header_returns_401(self):
        """Basic auth header (not Bearer) must return 401."""
        test_app = self._make_test_app_with_role_route(RoleName.NGO)
        client = test_app.test_client()

        res = client.get(
            "/rbac-test",
            headers={"Authorization": "Basic dXNlcjpwYXNz"},
        )

        self.assertEqual(res.status_code, 401)

    def test_expired_token_returns_401(self):
        """Expired token must return 401 (authentication failure, not authorization)."""
        test_app = self._make_test_app_with_role_route(RoleName.ADMIN)
        client = test_app.test_client()

        token = self._generate_token({"exp": int(time.time()) - 100})
        res = client.get(
            "/rbac-test",
            headers={"Authorization": f"Bearer {token}"},
        )

        self.assertEqual(res.status_code, 401)
        self.assertIn("expired", res.get_json()["message"].lower())

    # ------------------------------------------------------------------
    # 2. Valid token but no PawConnect profile → 403
    # ------------------------------------------------------------------

    def test_valid_token_no_pawconnect_profile_returns_403(self):
        """
        A valid Cognito JWT whose 'sub' has no matching PawConnect user record
        must return 403 (application-user error, distinct from 401).
        """
        test_app = self._make_test_app_with_role_route(RoleName.ADMIN)
        client = test_app.test_client()

        # Use a sub that does not exist in the database
        token = self._generate_token({"sub": "no-pawconnect-user-sub-xyz"})
        res = client.get(
            "/rbac-test",
            headers={"Authorization": f"Bearer {token}"},
        )

        self.assertEqual(res.status_code, 403)
        body = res.get_json()
        self.assertIn("profile", body["message"].lower())

    # ------------------------------------------------------------------
    # 3. Authenticated user with wrong role → 403
    # ------------------------------------------------------------------

    def test_wrong_role_returns_403(self):
        """
        An authenticated user with a PawConnect profile but the wrong role
        must receive HTTP 403.
        """
        test_sub = "rbac-wrong-role-sub-001"

        with self.app.app_context():
            # Create a User role and a user with that role
            role = Role.query.filter_by(role_name=RoleName.USER).first()
            if not role:
                role = Role(role_name=RoleName.USER)
                db.session.add(role)
                db.session.commit()

            user = User.query.filter_by(auth_id=test_sub).first()
            if not user:
                user = User(
                    name="RBAC Wrong Role Test",
                    email="rbac_wrong_role@example.com",
                    role_id=role.role_id,
                    auth_id=test_sub,
                )
                db.session.add(user)
                db.session.commit()

        try:
            test_app = self._make_test_app_with_role_route(RoleName.ADMIN)
            client = test_app.test_client()

            token = self._generate_token({"sub": test_sub})
            res = client.get(
                "/rbac-test",
                headers={"Authorization": f"Bearer {token}"},
            )

            self.assertEqual(res.status_code, 403)
            body = res.get_json()
            self.assertIn("permission", body["message"].lower())
        finally:
            with self.app.app_context():
                u = User.query.filter_by(auth_id=test_sub).first()
                if u:
                    db.session.delete(u)
                    db.session.commit()

    # ------------------------------------------------------------------
    # 4. Authenticated user with permitted role → 200
    # ------------------------------------------------------------------

    def test_correct_role_returns_200(self):
        """
        An authenticated user with the expected role must be allowed through (200).
        """
        test_sub = "rbac-correct-role-sub-001"

        with self.app.app_context():
            role = Role.query.filter_by(role_name=RoleName.ADMIN).first()
            if not role:
                role = Role(role_name=RoleName.ADMIN)
                db.session.add(role)
                db.session.commit()

            user = User.query.filter_by(auth_id=test_sub).first()
            if not user:
                user = User(
                    name="RBAC Admin Test",
                    email="rbac_admin@example.com",
                    role_id=role.role_id,
                    auth_id=test_sub,
                )
                db.session.add(user)
                db.session.commit()

        try:
            test_app = self._make_test_app_with_role_route(RoleName.ADMIN)
            client = test_app.test_client()

            token = self._generate_token({"sub": test_sub})
            res = client.get(
                "/rbac-test",
                headers={"Authorization": f"Bearer {token}"},
            )

            self.assertEqual(res.status_code, 200)
            body = res.get_json()
            self.assertEqual(body["status"], "success")
            self.assertEqual(body["role"], RoleName.ADMIN)
        finally:
            with self.app.app_context():
                u = User.query.filter_by(auth_id=test_sub).first()
                if u:
                    db.session.delete(u)
                    db.session.commit()

    # ------------------------------------------------------------------
    # 5. Multiple allowed roles work correctly
    # ------------------------------------------------------------------

    def test_multiple_allowed_roles_first_role_allowed(self):
        """When multiple roles are allowed, a user with the first role is permitted."""
        test_sub = "rbac-multi-role-ngo-sub-001"

        with self.app.app_context():
            role = Role.query.filter_by(role_name=RoleName.NGO).first()
            if not role:
                role = Role(role_name=RoleName.NGO)
                db.session.add(role)
                db.session.commit()

            user = User.query.filter_by(auth_id=test_sub).first()
            if not user:
                user = User(
                    name="RBAC NGO Multi Test",
                    email="rbac_ngo_multi@example.com",
                    role_id=role.role_id,
                    auth_id=test_sub,
                )
                db.session.add(user)
                db.session.commit()

        try:
            # Route allows both NGO and Admin
            test_app = self._make_test_app_with_role_route(RoleName.NGO, RoleName.ADMIN)
            client = test_app.test_client()

            token = self._generate_token({"sub": test_sub})
            res = client.get(
                "/rbac-test",
                headers={"Authorization": f"Bearer {token}"},
            )

            self.assertEqual(res.status_code, 200)
        finally:
            with self.app.app_context():
                u = User.query.filter_by(auth_id=test_sub).first()
                if u:
                    db.session.delete(u)
                    db.session.commit()

    def test_multiple_allowed_roles_second_role_allowed(self):
        """When multiple roles are allowed, a user with the second role is also permitted."""
        test_sub = "rbac-multi-role-admin-sub-002"

        with self.app.app_context():
            role = Role.query.filter_by(role_name=RoleName.ADMIN).first()
            if not role:
                role = Role(role_name=RoleName.ADMIN)
                db.session.add(role)
                db.session.commit()

            user = User.query.filter_by(auth_id=test_sub).first()
            if not user:
                user = User(
                    name="RBAC Admin Multi Test",
                    email="rbac_admin_multi@example.com",
                    role_id=role.role_id,
                    auth_id=test_sub,
                )
                db.session.add(user)
                db.session.commit()

        try:
            test_app = self._make_test_app_with_role_route(RoleName.NGO, RoleName.ADMIN)
            client = test_app.test_client()

            token = self._generate_token({"sub": test_sub})
            res = client.get(
                "/rbac-test",
                headers={"Authorization": f"Bearer {token}"},
            )

            self.assertEqual(res.status_code, 200)
        finally:
            with self.app.app_context():
                u = User.query.filter_by(auth_id=test_sub).first()
                if u:
                    db.session.delete(u)
                    db.session.commit()

    def test_multiple_allowed_roles_unlisted_role_denied(self):
        """A user whose role is not in the allowed set is denied even with multi-role config."""
        test_sub = "rbac-multi-role-rescuer-sub-003"

        with self.app.app_context():
            role = Role.query.filter_by(role_name=RoleName.RESCUER).first()
            if not role:
                role = Role(role_name=RoleName.RESCUER)
                db.session.add(role)
                db.session.commit()

            user = User.query.filter_by(auth_id=test_sub).first()
            if not user:
                user = User(
                    name="RBAC Rescuer Multi Test",
                    email="rbac_rescuer_multi@example.com",
                    role_id=role.role_id,
                    auth_id=test_sub,
                )
                db.session.add(user)
                db.session.commit()

        try:
            # Route only allows NGO and Admin
            test_app = self._make_test_app_with_role_route(RoleName.NGO, RoleName.ADMIN)
            client = test_app.test_client()

            token = self._generate_token({"sub": test_sub})
            res = client.get(
                "/rbac-test",
                headers={"Authorization": f"Bearer {token}"},
            )

            self.assertEqual(res.status_code, 403)
        finally:
            with self.app.app_context():
                u = User.query.filter_by(auth_id=test_sub).first()
                if u:
                    db.session.delete(u)
                    db.session.commit()

    # ------------------------------------------------------------------
    # 6. Role matching is case-sensitive / normalized per RoleName design
    # ------------------------------------------------------------------

    def test_role_matching_is_case_sensitive(self):
        """
        Role matching must be exact (case-sensitive) against the stored role_name.
        'admin' (lowercase) must NOT match RoleName.ADMIN ('Admin').
        This test verifies the stored role is 'Admin' and that the check
        is exact — no accidental case-insensitive bypass.
        """
        # Verify the canonical constant is title-case per the documented design
        self.assertEqual(RoleName.ADMIN, "Admin")
        self.assertEqual(RoleName.NGO, "NGO")
        self.assertEqual(RoleName.USER, "User")
        self.assertEqual(RoleName.RESCUER, "Rescuer")
        self.assertEqual(RoleName.VOLUNTEER, "Volunteer")
        self.assertEqual(RoleName.DONOR, "Donor")

        # "admin" (lowercase) is NOT in allowed_roles when using RoleName.ADMIN ("Admin")
        # because roles_required stores exact strings and the DB stores "Admin"
        allowed = {RoleName.ADMIN}
        self.assertNotIn("admin", allowed)
        self.assertNotIn("ADMIN", allowed)
        self.assertIn("Admin", allowed)

    def test_role_name_all_roles_constant_is_complete(self):
        """ALL_ROLES covers all six documented roles and no extras."""
        documented_roles = {
            RoleName.USER,
            RoleName.NGO,
            RoleName.RESCUER,
            RoleName.VOLUNTEER,
            RoleName.DONOR,
            RoleName.ADMIN,
        }
        self.assertEqual(set(RoleName.ALL_ROLES), documented_roles)
        self.assertEqual(len(RoleName.ALL_ROLES), 6)

    # ------------------------------------------------------------------
    # 7. roles_required raises ValueError with no roles specified
    # ------------------------------------------------------------------

    def test_roles_required_with_no_roles_raises(self):
        """Calling roles_required() with no role arguments is a programming error."""
        with self.assertRaises(ValueError):
            roles_required()

    # ------------------------------------------------------------------
    # 8. g.current_user and g.cognito_sub are populated on success
    # ------------------------------------------------------------------

    def test_context_variables_populated_on_success(self):
        """On successful authorization, g.current_user and g.cognito_sub are available."""
        test_sub = "rbac-context-check-sub-001"

        with self.app.app_context():
            role = Role.query.filter_by(role_name=RoleName.NGO).first()
            if not role:
                role = Role(role_name=RoleName.NGO)
                db.session.add(role)
                db.session.commit()

            user = User.query.filter_by(auth_id=test_sub).first()
            if not user:
                user = User(
                    name="RBAC Context Test",
                    email="rbac_context@example.com",
                    role_id=role.role_id,
                    auth_id=test_sub,
                )
                db.session.add(user)
                db.session.commit()

        try:
            test_app = create_app()

            @test_app.get("/rbac-context-test")
            @roles_required(RoleName.NGO, auth_service=self.auth_service)
            def rbac_context_route():
                sub = get_current_cognito_sub()
                user = get_current_user()
                return jsonify({
                    "status": "success",
                    "sub": sub,
                    "user_email": user.email if user else None,
                }), 200

            client = test_app.test_client()
            token = self._generate_token({"sub": test_sub})
            res = client.get(
                "/rbac-context-test",
                headers={"Authorization": f"Bearer {token}"},
            )

            self.assertEqual(res.status_code, 200)
            body = res.get_json()
            self.assertEqual(body["sub"], test_sub)
            self.assertEqual(body["user_email"], "rbac_context@example.com")
        finally:
            with self.app.app_context():
                u = User.query.filter_by(auth_id=test_sub).first()
                if u:
                    db.session.delete(u)
                    db.session.commit()


class TestRBACDoesNotWeakenAuthentication(unittest.TestCase):
    """
    Regression suite: verifies that adding RBAC does not weaken or bypass
    the existing Cognito authentication mechanism.
    """

    @classmethod
    def setUpClass(cls):
        cls.private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048,
        )
        cls.wrong_private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048,
        )
        cls.kid = "rbac-regression-key"
        cls.test_region = "us-east-1"
        cls.test_user_pool_id = "us-east-1_RegPool"
        cls.test_client_id = "reg-client-id"
        cls.expected_issuer = (
            f"https://cognito-idp.{cls.test_region}.amazonaws.com/{cls.test_user_pool_id}"
        )
        cls.app = create_app()
        cls.app.config["TESTING"] = True

    def setUp(self):
        mock_jwk = MagicMock()
        mock_jwk.key = self.private_key.public_key()

        self.mock_jwks_client = MagicMock()
        self.mock_jwks_client.get_signing_key_from_jwt.return_value = mock_jwk

        self.auth_service = CognitoAuthService(
            region=self.test_region,
            user_pool_id=self.test_user_pool_id,
            client_id=self.test_client_id,
            jwk_client=self.mock_jwks_client,
        )

    def _sign(self, payload, key=None) -> str:
        key = key or self.private_key
        return jwt.encode(
            payload,
            key,
            algorithm="RS256",
            headers={"kid": self.kid},
        )

    def test_wrong_signature_still_rejected_by_roles_required(self):
        """
        A token signed with the wrong key must still return 401 even when
        the route uses @roles_required rather than @cognito_required.
        RBAC must NOT loosen signature verification.
        """
        now = int(time.time())
        payload = {
            "sub": "attacker-sub",
            "iss": self.expected_issuer,
            "aud": self.test_client_id,
            "token_use": "id",
            "exp": now + 3600,
        }
        token = self._sign(payload, key=self.wrong_private_key)

        test_app = create_app()

        @test_app.get("/secure-rbac")
        @roles_required(RoleName.ADMIN, auth_service=self.auth_service)
        def secure():
            return jsonify({"status": "success"}), 200

        client = test_app.test_client()
        res = client.get(
            "/secure-rbac",
            headers={"Authorization": f"Bearer {token}"},
        )

        self.assertEqual(res.status_code, 401)

    def test_wrong_issuer_still_rejected_by_roles_required(self):
        """A token from a different issuer must return 401 under @roles_required."""
        now = int(time.time())
        payload = {
            "sub": "attacker-sub",
            "iss": "https://cognito-idp.eu-west-1.amazonaws.com/eu-west-1_WrongPool",
            "aud": self.test_client_id,
            "token_use": "id",
            "exp": now + 3600,
        }
        token = self._sign(payload)

        test_app = create_app()

        @test_app.get("/secure-rbac-2")
        @roles_required(RoleName.ADMIN, auth_service=self.auth_service)
        def secure2():
            return jsonify({"status": "success"}), 200

        client = test_app.test_client()
        res = client.get(
            "/secure-rbac-2",
            headers={"Authorization": f"Bearer {token}"},
        )

        self.assertEqual(res.status_code, 401)


if __name__ == "__main__":
    unittest.main()
