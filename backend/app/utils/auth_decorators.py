from functools import wraps
from typing import Callable, Optional, Sequence
from flask import g, jsonify, request

from ..models import User
from ..models.role import RoleName
from ..services.cognito_auth_service import (
    CognitoAuthService,
    ConfigurationError,
    InvalidTokenError,
    TokenExpiredError,
)


def get_current_user() -> Optional[User]:
    """Retrieve the resolved PawConnect User from Flask request context, if available."""
    return getattr(g, "current_user", None)


def get_current_cognito_sub() -> Optional[str]:
    """Retrieve the authenticated Cognito subject identifier (`sub`) from request context."""
    return getattr(g, "cognito_sub", None)


def get_current_cognito_claims() -> Optional[dict]:
    """Retrieve the full verified Cognito claims dictionary from request context."""
    return getattr(g, "cognito_claims", None)


def cognito_required(
    allowed_token_uses: Sequence[str] = ("id", "access"),
    require_pawconnect_user: bool = False,
    auth_service: Optional[CognitoAuthService] = None,
) -> Callable:
    """
    Decorator for Flask routes requiring Amazon Cognito authentication.

    Verifies the Bearer JWT token from the Authorization header and populates:
    - g.cognito_claims: verified claims dict
    - g.cognito_sub: Cognito user identifier (`sub`)
    - g.current_user: matching PawConnect User record (if found in PostgreSQL)

    Parameters:
        allowed_token_uses: Sequence of accepted token types ('id', 'access').
        require_pawconnect_user: If True, returns 403 when no matching PawConnect User
                                 record exists for the Cognito `sub`.
        auth_service: Optional CognitoAuthService instance (useful for testing/injection).
    """

    def decorator(fn: Callable) -> Callable:
        @wraps(fn)
        def wrapper(*args, **kwargs):
            auth_header = request.headers.get("Authorization")
            if not auth_header:
                return (
                    jsonify({
                        "status": "error",
                        "message": "Authorization header is required.",
                    }),
                    401,
                )

            parts = auth_header.strip().split()
            if len(parts) != 2 or parts[0].lower() != "bearer":
                return (
                    jsonify({
                        "status": "error",
                        "message": "Invalid Authorization header format. Expected 'Bearer <token>'.",
                    }),
                    401,
                )

            token = parts[1]
            service = auth_service or CognitoAuthService()

            try:
                claims = service.validate_token(token, allowed_token_uses=allowed_token_uses)
            except TokenExpiredError:
                return (
                    jsonify({
                        "status": "error",
                        "message": "Authentication token has expired.",
                    }),
                    401,
                )
            except InvalidTokenError as e:
                return (
                    jsonify({
                        "status": "error",
                        "message": f"Authentication failed: {str(e)}",
                    }),
                    401,
                )
            except ConfigurationError as e:
                return (
                    jsonify({
                        "status": "error",
                        "message": f"Authentication service configuration error: {str(e)}",
                    }),
                    503,
                )
            except Exception:
                return (
                    jsonify({
                        "status": "error",
                        "message": "Authentication verification failed.",
                    }),
                    401,
                )

            # Populate request context
            g.cognito_claims = claims
            g.cognito_sub = claims.get("sub")
            try:
                g.current_user = service.get_user_by_auth_id(g.cognito_sub)
            except Exception:
                g.current_user = None

            if require_pawconnect_user and g.current_user is None:
                return (
                    jsonify({
                        "status": "error",
                        "message": "No registered PawConnect profile found for this authenticated user.",
                    }),
                    403,
                )

            return fn(*args, **kwargs)

        return wrapper

    return decorator


def roles_required(
    *allowed_roles: str,
    auth_service: Optional[CognitoAuthService] = None,
) -> Callable:
    """
    Decorator for Flask routes requiring Cognito authentication AND a specific PawConnect role.

    Enforces the two-stage authorization pipeline:

        1. Authentication
           - Missing/invalid/expired token → HTTP 401
        2. PawConnect profile resolution
           - Valid Cognito identity but no matching PawConnect user → HTTP 403
        3. Role authorization
           - Authenticated user's role not in allowed_roles → HTTP 403
           - Authenticated user has an allowed role → route proceeds

    Parameters:
        *allowed_roles: One or more canonical role name strings from RoleName
                        (e.g. RoleName.ADMIN, RoleName.NGO).
                        Role matching is exact and case-sensitive against the stored role_name.
        auth_service:   Optional CognitoAuthService instance (for testing/injection).

    Usage::

        @app.route("/admin/dashboard")
        @roles_required(RoleName.ADMIN)
        def admin_dashboard():
            ...

        @app.route("/ngo/animals")
        @roles_required(RoleName.NGO, RoleName.ADMIN)
        def ngo_animals():
            ...
    """
    if not allowed_roles:
        raise ValueError("roles_required requires at least one allowed role.")

    def decorator(fn: Callable) -> Callable:
        @wraps(fn)
        def wrapper(*args, **kwargs):
            # --- Step 1: Authentication ---
            auth_header = request.headers.get("Authorization")
            if not auth_header:
                return (
                    jsonify({
                        "status": "error",
                        "message": "Authorization header is required.",
                    }),
                    401,
                )

            parts = auth_header.strip().split()
            if len(parts) != 2 or parts[0].lower() != "bearer":
                return (
                    jsonify({
                        "status": "error",
                        "message": "Invalid Authorization header format. Expected 'Bearer <token>'.",
                    }),
                    401,
                )

            token = parts[1]
            service = auth_service or CognitoAuthService()

            try:
                claims = service.validate_token(token)
            except TokenExpiredError:
                return (
                    jsonify({
                        "status": "error",
                        "message": "Authentication token has expired.",
                    }),
                    401,
                )
            except InvalidTokenError as e:
                return (
                    jsonify({
                        "status": "error",
                        "message": f"Authentication failed: {str(e)}",
                    }),
                    401,
                )
            except ConfigurationError as e:
                return (
                    jsonify({
                        "status": "error",
                        "message": f"Authentication service configuration error: {str(e)}",
                    }),
                    503,
                )
            except Exception:
                return (
                    jsonify({
                        "status": "error",
                        "message": "Authentication verification failed.",
                    }),
                    401,
                )

            # Populate request context (mirrors cognito_required behaviour)
            g.cognito_claims = claims
            g.cognito_sub = claims.get("sub")
            try:
                g.current_user = service.get_user_by_auth_id(g.cognito_sub)
            except Exception:
                g.current_user = None

            # --- Step 2: PawConnect profile check ---
            if g.current_user is None:
                return (
                    jsonify({
                        "status": "error",
                        "message": "No registered PawConnect profile found for this authenticated user.",
                    }),
                    403,
                )

            # --- Step 3: Role authorization ---
            user: User = g.current_user
            user_role_name: Optional[str] = (
                user.role.role_name if user.role is not None else None
            )

            if user_role_name not in allowed_roles:
                return (
                    jsonify({
                        "status": "error",
                        "message": "You do not have permission to access this resource.",
                    }),
                    403,
                )

            return fn(*args, **kwargs)

        return wrapper

    return decorator
