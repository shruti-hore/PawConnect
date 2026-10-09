from typing import Any, Dict, Optional, Sequence
import jwt
from flask import current_app

from ..models import User


class CognitoAuthError(Exception):
    """Base exception for Cognito authentication failures."""
    pass


class ConfigurationError(CognitoAuthError):
    """Raised when Cognito configuration is missing or invalid."""
    pass


class TokenExpiredError(CognitoAuthError):
    """Raised when a token has expired."""
    pass


class InvalidTokenError(CognitoAuthError):
    """Raised when a token fails verification or claim checks."""
    pass


class CognitoAuthService:
    """
    Validates Amazon Cognito JWTs (ID and Access tokens) and resolves
    associated PawConnect user identities without storing credentials locally.
    """

    def __init__(
        self,
        region: Optional[str] = None,
        user_pool_id: Optional[str] = None,
        client_id: Optional[str] = None,
        jwks_url: Optional[str] = None,
        jwk_client: Optional[jwt.PyJWKClient] = None,
    ):
        self._region = region
        self._user_pool_id = user_pool_id
        self._client_id = client_id
        self._jwks_url = jwks_url
        self._jwk_client = jwk_client

    @property
    def region(self) -> str:
        region = (
            self._region
            or (current_app and (current_app.config.get("COGNITO_REGION") or current_app.config.get("AWS_REGION")))
        )
        if not region:
            raise ConfigurationError("COGNITO_REGION or AWS_REGION is not configured.")
        return region

    @property
    def user_pool_id(self) -> str:
        user_pool_id = self._user_pool_id or (current_app and current_app.config.get("COGNITO_USER_POOL_ID"))
        if not user_pool_id:
            raise ConfigurationError("COGNITO_USER_POOL_ID is not configured.")
        return user_pool_id

    @property
    def client_id(self) -> Optional[str]:
        return self._client_id or (current_app and current_app.config.get("COGNITO_APP_CLIENT_ID"))

    @property
    def issuer(self) -> str:
        return f"https://cognito-idp.{self.region}.amazonaws.com/{self.user_pool_id}"

    @property
    def jwks_url(self) -> str:
        if self._jwks_url:
            return self._jwks_url
        config_url = current_app and current_app.config.get("COGNITO_JWKS_URL")
        if config_url:
            return config_url
        return f"{self.issuer}/.well-known/jwks.json"

    def get_jwk_client(self) -> jwt.PyJWKClient:
        """Returns or creates the PyJWKClient instance for retrieving signing keys."""
        if self._jwk_client is None:
            self._jwk_client = jwt.PyJWKClient(self.jwks_url, cache_keys=True, max_cached_keys=16)
        return self._jwk_client

    def validate_token(
        self,
        token: str,
        allowed_token_uses: Sequence[str] = ("id", "access"),
    ) -> Dict[str, Any]:
        """
        Cryptographically validates a Cognito-issued JWT token.

        Validations performed:
        - Token structure and unverified header checks (RS256 algorithm enforcement).
        - Signature verification against the User Pool JWKS public keys.
        - Token expiration ('exp') and not-before claims.
        - Issuer ('iss') matches the configured Cognito User Pool.
        - 'token_use' claim is within allowed types ('id', 'access').
        - Audience ('aud') or client_id matches the configured Cognito App Client ID.
        - Cognito subject ('sub') presence and non-emptiness.

        Returns:
            Dict[str, Any]: Verified claims dictionary.
        """
        # 0. Configuration check (fail fast if region or user pool is unconfigured)
        expected_issuer = self.issuer

        if not token or not isinstance(token, str):
            raise InvalidTokenError("Token must be a non-empty string.")

        # 1. Header validation
        try:
            unverified_header = jwt.get_unverified_header(token)
        except Exception as e:
            raise InvalidTokenError(f"Malformed token header: {str(e)}")

        alg = unverified_header.get("alg")
        if alg != "RS256":
            raise InvalidTokenError(f"Invalid algorithm '{alg}'. Only RS256 is supported.")

        kid = unverified_header.get("kid")
        if not kid:
            raise InvalidTokenError("Token header is missing 'kid' (Key ID).")

        # 2. Key retrieval from JWKS
        try:
            signing_key = self.get_jwk_client().get_signing_key_from_jwt(token)
        except Exception as e:
            raise InvalidTokenError(f"Unable to find matching public key for kid '{kid}': {str(e)}")

        # 3. Cryptographic signature and core claim verification
        try:
            claims = jwt.decode(
                token,
                signing_key.key,
                algorithms=["RS256"],
                issuer=expected_issuer,
                options={
                    "verify_signature": True,
                    "verify_exp": True,
                    "verify_iss": True,
                    "verify_aud": False,  # Cognito ID and Access tokens handle audience differently
                    "require": ["exp", "iss", "sub", "token_use"],
                },
            )
        except jwt.ExpiredSignatureError:
            raise TokenExpiredError("Token has expired.")
        except jwt.InvalidIssuerError:
            raise InvalidTokenError("Token issuer does not match configured Cognito User Pool.")
        except jwt.InvalidSignatureError:
            raise InvalidTokenError("Token signature verification failed.")
        except jwt.PyJWTError as e:
            raise InvalidTokenError(f"Token validation failed: {str(e)}")

        # 4. Token use verification
        token_use = claims.get("token_use")
        if token_use not in allowed_token_uses:
            raise InvalidTokenError(
                f"Invalid token_use '{token_use}'. Allowed: {list(allowed_token_uses)}."
            )

        # 5. Client ID / Audience verification
        configured_client_id = self.client_id
        if configured_client_id:
            if token_use == "id":
                aud = claims.get("aud")
                if aud != configured_client_id:
                    raise InvalidTokenError("Token audience ('aud') does not match configured App Client ID.")
            elif token_use == "access":
                client_id_claim = claims.get("client_id")
                if client_id_claim != configured_client_id:
                    raise InvalidTokenError("Token client_id does not match configured App Client ID.")

        # 6. Subject identifier verification
        sub = claims.get("sub")
        if not sub or not isinstance(sub, str) or not sub.strip():
            raise InvalidTokenError("Token must contain a valid non-empty 'sub' identifier.")

        return claims

    def get_user_by_auth_id(self, auth_id: str) -> Optional[User]:
        """
        Looks up a PawConnect User in the local database matching the Cognito `sub` identifier.

        Returns None if the authenticated user has not yet been provisioned in PawConnect.
        """
        if not auth_id:
            return None
        return User.query.filter_by(auth_id=auth_id).first()
