from rest_framework import serializers
from .models import Asset

class AssetSerializer(serializers.ModelSerializer):
    class Meta:
        model = Asset
        fields = '__all__' # Or use fields='__all__' if you prefer


# serializers.py

from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from api.models import User  # Only import User here

class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        # This is only used for the User model, not Admin
        token = super().get_token(user)

        # Add custom claims
        token['username'] = user.empid  # or user.email if you prefer
        token['role'] = 'user'

        return token
