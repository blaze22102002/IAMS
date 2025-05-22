# serializers.py
from rest_framework import serializers
from api.models import AssetAddition
from api.models import Asset,ProductModel

class AssetAdditionSerializer(serializers.ModelSerializer):
    class Meta:
        model = AssetAddition
        fields = [
            'asset_id', 'branch', 'employee_id', 'employee_name', 'group', 
            'business_impact', 'asset_tag', 'description', 'product_name', 
            'serial_number', 'remarks', 'status', 'it_poc_remarks', 'timestamp'
        ]
class AssetSerializer(serializers.ModelSerializer):
    branch_code = serializers.CharField(source='branch.branch_code')
    branch_name = serializers.CharField(source='branch.branch_name')
    class Meta:
        model = Asset
        fields = ['asset_id', 'branch_code', 'branch_name', 'employee_id', 'employee_name', 'group', 'business_impact', 
                  'asset_tag', 'description', 'product_name', 'serial_number', 'remarks', 'status', 
                  'it_poc_remarks'] 
        
# serializers.py
class ProductModelSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductModel
        fields = ['model_name']
