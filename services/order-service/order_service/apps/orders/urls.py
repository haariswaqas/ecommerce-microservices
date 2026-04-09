from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import InternalOrderView, OrderViewSet

router = DefaultRouter()
router.register(r"orders", OrderViewSet, basename="order")

urlpatterns = [
    path("", include(router.urls)),
    path("internal/orders/<uuid:order_id>/", InternalOrderView.as_view(), name="internal-order-detail"),
]
