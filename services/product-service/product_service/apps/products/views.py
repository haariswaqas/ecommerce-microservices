from django.db import transaction
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import Product
from .permissions import IsSellerOrReadOnly, IsInternalService
from .serializers import ProductSerializer


class ProductViewSet(viewsets.ModelViewSet):
    serializer_class = ProductSerializer
    permission_classes = [IsSellerOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['category']
    search_fields = ['name', 'description', 'category']
    ordering_fields = ['price', 'created_at']

    def get_queryset(self):
        queryset = Product.objects.filter(is_active=True)

        if self.action not in ['list', 'retrieve']:
            if getattr(self.request.user, 'role', None) == 'seller':
                queryset = queryset.filter(created_by=self.request.user.id)

        return queryset

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user.id)

    @action(detail=True, methods=['post'], permission_classes=[IsInternalService])
    def reserve_stock(self, request, pk=None):
        """Called by Order Service to reserve items."""
        quantity = request.data.get('quantity', 1)

        with transaction.atomic():
            product = Product.objects.select_for_update().get(pk=pk)
            if product.stock < quantity:
                return Response(
                    {'error': 'Insufficient stock'},
                    status=400,
                )
            product.stock -= quantity
            product.save()

        return Response({'reserved': quantity, 'remaining': product.stock})