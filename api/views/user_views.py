from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from api.models import Asset, Branch, User
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate
from django.http import JsonResponse
from django.core.cache import cache
from django.utils import timezone


class UserLoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        empid = request.data.get("empid")
        password = request.data.get("password")

        if not empid or not password:
            return Response({"detail": "empid and password required."}, status=status.HTTP_400_BAD_REQUEST)

        # Authenticate user credentials
        user = authenticate(request, username=empid, password=password)

        if user is None or user.is_superuser:
            return Response({"detail": "Invalid credentials or not a regular user."}, status=status.HTTP_401_UNAUTHORIZED)

        # Generate JWT tokens
        refresh = RefreshToken.for_user(user)
        refresh["username"] = user.empid
        refresh["role"] = "user"

        # Create response
        response = JsonResponse({
            "message": "User login successful.",
            "username": user.empid,
            "role": refresh["role"],
            "access": str(refresh.access_token),
            "refresh": str(refresh)
        })

        # Set JWT in cookies
        response.set_cookie('access_token', str(refresh.access_token), httponly=True, secure=True)
        response.set_cookie('refresh_token', str(refresh), httponly=True, secure=True)

        return response
class BranchFilterView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        branch_code = request.query_params.get('branch_code')

        if not branch_code:
            return Response({"error": "branch_code is required"}, status=status.HTTP_400_BAD_REQUEST)

        # Only regular users can access their branch
        is_admin = user.role == 'admin'
        branch = None

        if not is_admin:
            # Check if the user has access to this branch
            try:
                branch = Branch.objects.get(branch_code=branch_code, user=user)
            except Branch.DoesNotExist:
                return Response({"error": "Unauthorized: You don’t have access to this branch."}, status=status.HTTP_403_FORBIDDEN)
        else:
            # Admin can access any branch
            branch = get_object_or_404(Branch, branch_code=branch_code)

        # Fetch assets for the determined branch
        assets = Asset.objects.filter(branch=branch)

        if not assets:
            return Response({"message": f"No assets found for branch_code '{branch_code}'"}, status=status.HTTP_404_NOT_FOUND)

        