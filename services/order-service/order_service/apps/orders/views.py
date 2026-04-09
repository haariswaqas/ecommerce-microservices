import requests
from django.conf import settings
from django.db import transaction
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Order
from .serializers import OrderCreateSerializer, OrderSerializer


class StockReservationError(Exception):
    pass


class OrderViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated]
    http_method_names = ["get", "post", "head", "options"]
    queryset = Order.objects.prefetch_related("items").all()

    def get_queryset(self):
        base_queryset = Order.objects.prefetch_related("items")
        if self.request.user and self.request.user.is_staff:
            return base_queryset
        return base_queryset.filter(user_id=self.request.user.id)

    def get_serializer_class(self):
        if self.action == "create":
            return OrderCreateSerializer
        return OrderSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        with transaction.atomic():
            order = serializer.save(user_id=request.user.id)

        try:
            self._reserve_stock_for_order(order)
        except StockReservationError as exc:
            order.status = Order.Status.FAILED
            order.failure_reason = str(exc)
            order.save(update_fields=["status", "failure_reason", "updated_at"])
            return Response(
                OrderSerializer(order, context=self.get_serializer_context()).data,
                status=status.HTTP_400_BAD_REQUEST,
            )

        order.status = Order.Status.CONFIRMED
        order.failure_reason = ""
        order.save(update_fields=["status", "failure_reason", "updated_at"])

        response_data = OrderSerializer(order, context=self.get_serializer_context()).data
        headers = self.get_success_headers(response_data)
        return Response(response_data, status=status.HTTP_201_CREATED, headers=headers)

    @action(detail=True, methods=["post"])
    def cancel(self, request, pk=None):
        order = self.get_object()
        if order.status not in [Order.Status.PENDING, Order.Status.CONFIRMED]:
            return Response(
                {"detail": f"Order in '{order.status}' status cannot be cancelled."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        order.status = Order.Status.CANCELLED
        order.save(update_fields=["status", "updated_at"])
        return Response(OrderSerializer(order, context=self.get_serializer_context()).data)

    def _reserve_stock_for_order(self, order):
        for item in order.items.all():
            self._reserve_product_stock(item.product_id, item.quantity)

    def _reserve_product_stock(self, product_id, quantity):
        headers = {}
        auth_header = self.request.headers.get("Authorization")
        if auth_header:
            headers["Authorization"] = auth_header

        last_error = None
        for reserve_url in self._build_reservation_urls(product_id):
            try:
                response = requests.post(
                    reserve_url,
                    json={"quantity": quantity},
                    headers=headers,
                    timeout=getattr(settings, "SERVICE_REQUEST_TIMEOUT", 5),
                )
            except requests.RequestException as exc:
                last_error = f"Could not contact product service at {reserve_url}: {exc}"
                continue

            if response.status_code in [status.HTTP_200_OK, status.HTTP_201_CREATED]:
                return

            if response.status_code == status.HTTP_404_NOT_FOUND:
                last_error = f"Reserve endpoint was not found at {reserve_url}."
                continue

            message = self._extract_error_message(response)
            raise StockReservationError(
                f"Unable to reserve stock for product {product_id}: {message}"
            )

        raise StockReservationError(
            last_error or f"Unable to reserve stock for product {product_id}."
        )

    def _build_reservation_urls(self, product_id):
        base_url = settings.PRODUCT_SERVICE_URL.rstrip("/")
        return [
            f"{base_url}/products/{product_id}/reserve_stock/",
            f"{base_url}/api/products/{product_id}/reserve_stock/",
        ]

    @staticmethod
    def _extract_error_message(response):
        try:
            payload = response.json()
        except ValueError:
            return response.text or f"HTTP {response.status_code}"

        return (
            payload.get("detail")
            or payload.get("error")
            or payload.get("message")
            or str(payload)
        )


class InternalOrderView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request, order_id):
        secret = request.headers.get("X-Internal-Secret")
        if secret != settings.INTERNAL_SECRET:
            return Response(status=status.HTTP_403_FORBIDDEN)

        try:
            order = Order.objects.prefetch_related("items").get(id=order_id)
        except Order.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)

        return Response(OrderSerializer(order).data)
