from django.db import models
import uuid



class Product(models.Model):
    
    ELECTRONICS = 'electronics'
    CLOTHING = 'clothing'
    HOME = 'home'
    BOOKS = 'books'
    TOYS = 'toys'
    
    
    CATEGORY_CHOICES = [
        ('electronics', 'Electronics'),
        ('clothing', 'Clothing'),
        ('home', 'Home & Kitchen'),
        ('books', 'Books'),
        ('toys', 'Toys & Games'),
    ]
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, null=True, blank=True, default=ELECTRONICS)
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    stock = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    created_by = models.UUIDField()  # Reference to user — NOT a ForeignKey!
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'products'
        
"""
🚫 Critical Rule
Notice created_by = models.UUIDField() — NOT a ForeignKey to User. 
You never create foreign key relationships across service boundaries. 
Store only the ID reference. This is called "eventual consistency" design.

💡 Why No ForeignKey? 
If you used a ForeignKey to the User model in the user-service, you'd create a tight coupling between the two services. 
The product-service would depend on the user-service's database schema, which violates microservices principles.

"""