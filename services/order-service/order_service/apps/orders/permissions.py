# order_service/apps/orders/permissions.py
import requests
from django.conf import settings
from rest_framework.permissions import BasePermission


def get_role(request) -> str | None:
    """Extract role directly from FakeUser."""
    return getattr(request.user, 'role', None)


def _get_seller_product_ids(seller_id: str) -> list[str]:
    """Fetch product IDs belonging to this seller from product service."""
    try:
        base_url = settings.PRODUCT_SERVICE_URL.rstrip("/")
        response = requests.get(
            f"{base_url}/api/products/products/",
            params={"created_by": seller_id},
            headers={"X-Internal-Secret": settings.INTERNAL_SECRET},
            timeout=getattr(settings, "SERVICE_REQUEST_TIMEOUT", 5),
        )
        if response.status_code == 200:
            return [p["id"] for p in response.json().get("results", [])]
    except requests.RequestException:
        pass
    return []


class OrderAccessPermission(BasePermission):
    """
    - Admins: full access
    - Customers: own orders only, can place and cancel
    - Sellers: orders containing their products, read only
    - Others: denied
    """

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False

        if request.user.is_staff:
            return True

        role = get_role(request)

        if view.action in ('create', 'cancel'):
            return role == 'customer'

        return role in ('customer', 'seller')

    def has_object_permission(self, request, view, obj):
        if request.user.is_staff:
            return True

        role = get_role(request)

        if role == 'customer':
            return str(obj.user_id) == str(request.user.id)

        if role == 'seller':
            seller_product_ids = _get_seller_product_ids(str(request.user.id))
            order_product_ids = [str(item.product_id) for item in obj.items.all()]
            return bool(set(seller_product_ids) & set(order_product_ids))

        return False