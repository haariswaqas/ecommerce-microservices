# product_service/apps/products/authentication.py
import uuid
from rest_framework_simplejwt.authentication import JWTAuthentication


class FakeUser:
    """Lightweight user object built from JWT claims — no DB query."""
    is_anonymous = False

    def __init__(self, payload):
        self.id = uuid.UUID(str(payload['user_id']))
        self.email = payload.get('email', '')
        self.username = payload.get('username', '')
        self.first_name = payload.get('first_name', '')
        self.last_name = payload.get('last_name', '')
        self.role = payload.get('role', '')
        self.is_staff = payload.get('is_staff', False)
        self.is_authenticated = True

    def __str__(self):
        return self.email


class ServiceJWTAuthentication(JWTAuthentication):
    def get_user(self, validated_token):
        return FakeUser(validated_token)