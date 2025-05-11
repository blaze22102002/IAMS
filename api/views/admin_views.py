from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate
from django.http import JsonResponse
from django.utils import timezone

from django.views.decorators.csrf import csrf_exempt

class AdminLoginView(APIView):
    permission_classes = [AllowAny]

    @csrf_exempt
    def post(self, request):
        identifier = request.data.get("empid")
        password = request.data.get("password")

        if not identifier or not password:
            return Response({"detail": "empid/email and password are required."}, status=status.HTTP_400_BAD_REQUEST)

        # Authenticate the user
        user = authenticate(request, username=identifier, password=password)
        
        if user is None or not user.is_superuser:
            return Response({"detail": "Invalid admin credentials"}, status=status.HTTP_401_UNAUTHORIZED)

        # Generate JWT tokens
        refresh = RefreshToken.for_user(user)
        refresh['username'] = user.empid
        refresh['role'] = 'admin'

        access_token = str(refresh.access_token)
        refresh_token = str(refresh)

        # Update last login timestamp
        user.last_login = timezone.now()
        user.save()

        response = JsonResponse({
            'message': 'Admin login successful.',
            'access': access_token,
            'refresh': refresh_token
        })
        
        # Set JWT tokens in cookies
        response.set_cookie('access_token', access_token, httponly=True, secure=True)
        response.set_cookie('refresh_token', refresh_token, httponly=True, secure=True)

        return response
