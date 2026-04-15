from __future__ import annotations

from django.contrib.auth import authenticate, get_user_model
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

User = get_user_model()


class AdminRegisterApi(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        username = (request.data.get("username") or "").strip()
        password = request.data.get("password") or ""
        email = (request.data.get("email") or "").strip()

        if not username or not password:
            return Response({"detail": "username and password are required"}, status=status.HTTP_400_BAD_REQUEST)
        if User.objects.filter(username=username).exists():
            return Response({"detail": "username already exists"}, status=status.HTTP_400_BAD_REQUEST)

        user = User.objects.create_user(username=username, email=email, password=password)
        user.is_staff = True
        user.is_superuser = False
        user.save(update_fields=["is_staff", "is_superuser"])

        return Response({"detail": "admin registered", "username": user.username}, status=status.HTTP_201_CREATED)


class AdminMeApi(APIView):
    def get(self, request):
        if not request.user or not request.user.is_authenticated:
            return Response({"authenticated": False}, status=status.HTTP_200_OK)
        return Response(
            {
                "authenticated": True,
                "username": request.user.username,
                "is_staff": bool(getattr(request.user, "is_staff", False)),
            }
        )

