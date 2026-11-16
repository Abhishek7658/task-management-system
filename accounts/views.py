from django.contrib.auth import get_user_model
from rest_framework import generics, permissions, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from .serializers import UserSerializer, AdminUserCreateSerializer, RegistrationSerializer
from .permissions import IsAdministrator

User = get_user_model()

class RegistrationView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = RegistrationSerializer
    permission_classes = [permissions.AllowAny]

class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all().order_by("id")
    permission_classes = [IsAdministrator]

    def get_serializer_class(self):
        if self.action == "create":
            return AdminUserCreateSerializer
        return UserSerializer

    @action(detail=False, methods=["get"], permission_classes=[permissions.IsAuthenticated])
    def me(self, request):
        return Response(UserSerializer(request.user).data)
