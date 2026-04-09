from django.urls import include, path

urlpatterns = [
    path("api/", include("user_service.apps.users.urls")),
]
