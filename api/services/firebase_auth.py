from ..repositories.user_repository import UserRepository
from ..integrations.firebase_integration import FirebaseIntegration

"""
Firebase Authentication for Django REST Framework.

Verifies Firebase ID tokens and maps them to Django User objects.
"""
import logging
from rest_framework import authentication, exceptions
from firebase_admin import auth as firebase_auth
from django.contrib.auth import get_user_model

User = get_user_model()
logger = logging.getLogger(__name__)


class FirebaseAuthentication(authentication.BaseAuthentication):
    """
    DRF authentication class that verifies Firebase ID tokens.
    
    Expects: Authorization: Bearer <firebase_id_token>
    Returns: (user, decoded_token)
    """

    def authenticate(self, request):
        if hasattr(request, '_request') and getattr(request._request, 'user', None) and request._request.user.is_authenticated:
            return (request._request.user, None)

        auth_header = request.META.get('HTTP_AUTHORIZATION', '')
        if not auth_header.startswith('Bearer '):
            return None

        token = auth_header.split('Bearer ')[1].strip()
        if not token:
            return None

        try:
            decoded_token = FirebaseIntegration.verify_id_token(token)
        except firebase_auth.ExpiredIdTokenError:
            raise exceptions.AuthenticationFailed('Firebase token has expired.')
        except firebase_auth.InvalidIdTokenError:
            raise exceptions.AuthenticationFailed('Invalid Firebase token.')
        except firebase_auth.RevokedIdTokenError:
            raise exceptions.AuthenticationFailed('Firebase token has been revoked.')
        except Exception as e:
            logger.error(f"Firebase token verification failed: {e}")
            raise exceptions.AuthenticationFailed('Failed to verify Firebase token.')

        uid = decoded_token.get('uid')
        email = decoded_token.get('email', '').lower().strip()

        if not uid or not email:
            raise exceptions.AuthenticationFailed('Firebase token missing uid or email.')

        # Look up the Django user by email (username is also email in this system)
        user = UserRepository.filter_users(email=email).first()
        if not user:
            user = UserRepository.filter_users(username=email).first()

        if not user:
            # User hasn't registered via /api/auth/firebase-login yet
            raise exceptions.AuthenticationFailed('User not found. Please register first.')

        return (user, decoded_token)

    def authenticate_header(self, request):
        return 'Bearer realm="Firebase"'
