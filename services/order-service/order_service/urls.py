from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path('admin/', admin.site.urls),
    path("api/orders/", include("order_service.apps.orders.urls")),
]
