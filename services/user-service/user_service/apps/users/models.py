from django.contrib.auth.models import AbstractUser
from django.db import models
import uuid

class User(AbstractUser):
    
    CUSTOMER = 'customer'
    SELLER = 'seller'
    
    ROLE_CHOICES = [
        (CUSTOMER, 'Customer'),
        (SELLER, 'Seller'),
    ]
    # Use UUID as PK — safer across services than integer IDs
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )
    first_name = models.CharField(max_length=30)
    last_name = models.CharField(max_length=30)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=20, blank=True)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default=CUSTOMER, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    class Meta:
        db_table = 'users'
        
"""
💡 UUID vs Integer PKs
Always use UUIDs in microservices. Integer auto-increment IDs will collide across databases.
UUIDs are globally unique — a user created in your user-service DB will never conflict with an order in your orders DB.
"""