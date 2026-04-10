# order_service/apps/orders/serializers.py
from decimal import Decimal

import requests
from django.conf import settings
from rest_framework import serializers

from .models import Order, OrderItem


def fetch_product(product_id: str) -> dict:
    """Fetch product details from product service."""
    try:
        base_url = settings.PRODUCT_SERVICE_URL.rstrip("/")
        response = requests.get(
            f"{base_url}/api/products/products/{product_id}/",
            headers={"X-Internal-Secret": settings.INTERNAL_SECRET},
            timeout=getattr(settings, "SERVICE_REQUEST_TIMEOUT", 5),
        )
        if response.status_code == 200:
            return response.json()
        if response.status_code == 404:
            raise serializers.ValidationError(f"Product {product_id} not found.")
        raise serializers.ValidationError(f"Could not fetch product {product_id}.")
    except requests.RequestException as e:
        raise serializers.ValidationError(f"Product service unavailable: {e}")


class OrderItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderItem
        fields = [
            "id",
            "product_id",
            "product_name",
            "quantity",
            "unit_price",
            "line_total",
            "created_at",
        ]
        read_only_fields = ["id", "line_total", "created_at"]


class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)

    class Meta:
        model = Order
        fields = [
            "id",
            "user_id",
            "status",
            "total_amount",
            "shipping_address",
            "notes",
            "failure_reason",
            "created_at",
            "updated_at",
            "items",
        ]
        read_only_fields = [
            "id",
            "user_id",
            "status",
            "total_amount",
            "failure_reason",
            "created_at",
            "updated_at",
            "items",
        ]


class OrderCreateItemSerializer(serializers.Serializer):
    """Client only sends product_id and quantity — price comes from product service."""
    product_id = serializers.UUIDField()
    quantity = serializers.IntegerField(min_value=1)


class OrderCreateSerializer(serializers.ModelSerializer):
    items = OrderCreateItemSerializer(many=True, write_only=True)

    class Meta:
        model = Order
        fields = ["shipping_address", "notes", "items"]

    def validate_items(self, value):
        if not value:
            raise serializers.ValidationError("At least one item is required.")

        seen = set()
        for item in value:
            product_id = str(item["product_id"])
            if product_id in seen:
                raise serializers.ValidationError(
                    f"Duplicate product_id: {product_id}."
                )
            seen.add(product_id)
        return value

    def create(self, validated_data):
        items_data = validated_data.pop("items")
        order = Order.objects.create(**validated_data)

        order_items = []
        total_amount = Decimal("0.00")

        for item_data in items_data:
            product_id = str(item_data["product_id"])
            quantity = item_data["quantity"]

            # Fetch price and name from product service — never trust the client
            product = fetch_product(product_id)
            unit_price = Decimal(str(product["price"]))
            product_name = product.get("name", "")
            line_total = unit_price * quantity
            total_amount += line_total

            order_items.append(
                OrderItem(
                    order=order,
                    product_id=product_id,
                    product_name=product_name,
                    quantity=quantity,
                    unit_price=unit_price,
                    line_total=line_total,
                )
            )

        OrderItem.objects.bulk_create(order_items)
        order.total_amount = total_amount
        order.save(update_fields=["total_amount", "updated_at"])
        return order

    def to_representation(self, instance):
        return OrderSerializer(instance, context=self.context).data