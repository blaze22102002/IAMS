from rest_framework import serializers
from .models import Asset

class AssetSerializer(serializers.ModelSerializer):
    class Meta:
        model = Asset
        fields = '__all__' # Or use fields='__all__' if you prefer
