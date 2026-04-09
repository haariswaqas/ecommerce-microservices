import uuid
from decimal import Decimal

from django.core.validators import MinValueValidator
from django.db import models


class Order(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        CONFIRMED = "confirmed", "Confirmed"
        FAILED = "failed", "Failed"
        CANCELLED = "cancelled", "Cancelled"
        COMPLETED = "completed", "Completed"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user_id = models.UUIDField(db_index=True)
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
        db_index=True,
    )
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))
    shipping_address = models.TextField(blank=True)
    notes = models.TextField(blank=True)
    failure_reason = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "orders"
        ordering = ["-created_at"]

    def __str__(self):
        return f"Order<{self.id}> user={self.user_id} status={self.status}"


class OrderItem(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items")
    product_id = models.UUIDField(db_index=True)
    product_name = models.CharField(max_length=255, blank=True)
    quantity = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    unit_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.01"))],
    )
    line_total = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "order_items"
        ordering = ["created_at"]
        constraints = [
            models.UniqueConstraint(fields=["order", "product_id"], name="uniq_order_item_product"),
            models.CheckConstraint(check=models.Q(quantity__gte=1), name="order_item_quantity_gte_1"),
            models.CheckConstraint(check=models.Q(unit_price__gt=0), name="order_item_unit_price_gt_0"),
        ]

    def save(self, *args, **kwargs):
        self.line_total = (self.unit_price or Decimal("0.00")) * self.quantity
        super().save(*args, **kwargs)

    def __str__(self):
        return f"OrderItem<{self.id}> order={self.order_id} product={self.product_id}"
