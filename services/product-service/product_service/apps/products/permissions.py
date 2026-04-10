# product_service/apps/products/permissions.py
from rest_framework.permissions import BasePermission
import hmac
from django.conf import settings
class IsSellerOrReadOnly(BasePermission):
    """
    Customers and unauthenticated users can read.
    Only sellers can create/update/delete their own products.
    """

    def has_permission(self, request, view):
        if view.action in ['list', 'retrieve']:
            return True

        if not request.user or not request.user.is_authenticated:
            return False

        # Role comes from JWT token claim
        role = request.user.role if request.user else None
        if role != 'seller':
            return False

        return True

    def has_object_permission(self, request, view, obj):
        if view.action == 'retrieve':
            return True

        # Seller can only manage their own products
        return str(obj.created_by) == str(request.user.id)
    
class IsInternalService(BasePermission):
    """Only internal services can access this endpoint via shared secret."""
    def has_permission(self, request, view):
        secret = request.headers.get('X-Internal-Secret', '')
        return hmac.compare_digest(secret, settings.INTERNAL_SECRET)