from rest_framework import generics, permissions, status
from rest_framework.response import Response
from django.conf import settings
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView
from .models import User
from .serializers import UserSerializer, RegisterSerializer


class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = RegisterSerializer
    permission_classes = [permissions.AllowAny]

class ProfileView(generics.RetrieveUpdateAPIView):
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user

class InternalUserView(APIView):
    """
    Used ONLY by other services for internal lookups.
    Protected by a shared secret header, NOT JWT.
    """
    permission_classes = [permissions.AllowAny]

    def get(self, request, user_id):
        secret = request.headers.get('X-Internal-Secret')
        if secret != settings.INTERNAL_SECRET:
            return Response(status=status.HTTP_403_FORBIDDEN)
        try:
            user = User.objects.get(id=user_id)
            return Response(UserSerializer(user).data)
        except User.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)