from django.urls import include, path

urlpatterns = [
    path("api/", include("product_service.apps.products.urls")),
]
