from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from . import views

urlpatterns = [
    # Public
    path('register/', views.RegisterView.as_view()),
    path('login/', TokenObtainPairView.as_view()),
    path('token/refresh/', TokenRefreshView.as_view()),
    path('profile/', views.ProfileView.as_view()),

    # Internal (service-to-service only)
    path('internal/users/<uuid:user_id>/', views.InternalUserView.as_view()),
]