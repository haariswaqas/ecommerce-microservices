from django.urls import include, path

urlpatterns = [
    path("api/", include("order_service.apps.orders.urls")),
]
