from rest_framework import viewsets, filters, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db import transaction
from .models import Product
from .serializers import ProductSerializer

class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.filter(is_active=True).select_related('category')
    serializer_class = ProductSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'description']
    ordering_fields = ['price', 'created_at']

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [permissions.AllowAny()]
        return [permissions.IsAuthenticated()]

    def perform_create(self, serializer):
        # Get user ID from JWT token (validated by gateway)
        user_id = self.request.user.id
        serializer.save(created_by=user_id)

    @action(detail=True, methods=['post'])
    def reserve_stock(self, request, pk=None):
        """Called by Order Service to reserve items"""
        product = self.get_object()
        quantity = request.data.get('quantity', 1)

        with transaction.atomic():
            # select_for_update prevents race conditions
            product = Product.objects.select_for_update().get(pk=pk)
            if product.stock < quantity:
                return Response(
                    {'error': 'Insufficient stock'},
                    status=400
                )
            product.stock -= quantity
            product.save()
        return Response({'reserved': quantity, 'remaining': product.stock})