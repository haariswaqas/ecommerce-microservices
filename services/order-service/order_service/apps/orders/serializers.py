from decimal import Decimal

from rest_framework import serializers

from .models import Order, OrderItem


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


class OrderCreateItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderItem
        fields = ["product_id", "product_name", "quantity", "unit_price"]


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
                    f"Duplicate product_id detected in items: {product_id}."
                )
            seen.add(product_id)
        return value

    def create(self, validated_data):
        items_data = validated_data.pop("items")
        order = Order.objects.create(**validated_data)

        order_items = []
        total_amount = Decimal("0.00")

        for item_data in items_data:
            quantity = item_data["quantity"]
            unit_price = item_data["unit_price"]
            line_total = quantity * unit_price
            total_amount += line_total
            order_items.append(
                OrderItem(
                    order=order,
                    line_total=line_total,
                    **item_data,
                )
            )

        OrderItem.objects.bulk_create(order_items)
        order.total_amount = total_amount
        order.save(update_fields=["total_amount", "updated_at"])
        return order

    def to_representation(self, instance):
        return OrderSerializer(instance, context=self.context).data
