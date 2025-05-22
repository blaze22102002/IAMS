from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from api.models import Asset, Branch, User,AssetAddition,ProductModel
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate
from django.http import JsonResponse
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import api_view, permission_classes
from ..serializers import AssetAdditionSerializer,ProductModelSerializer
from ..serializers import AssetSerializer
from django.http import HttpResponse
import csv
class UserLoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        empid = request.data.get("empid")
        password = request.data.get("password")

        if not empid or not password:
            return Response({"detail": "empid and password required."}, status=status.HTTP_400_BAD_REQUEST)

      
        user = authenticate(request, username=empid, password=password)

        if user is None or user.is_superuser:
            return Response({"detail": "Invalid credentials or not a regular user."}, status=status.HTTP_401_UNAUTHORIZED)

       
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

        # Ensure branch_code is provided in the request
        if not branch_code:
            return Response({"error": "branch_code is required"}, status=status.HTTP_400_BAD_REQUEST)

        
        is_admin = user.role == 'admin'
        branch = None

        if not is_admin:
            try:
               
                branch = Branch.objects.get(branch_code=branch_code, user=user)
            except Branch.DoesNotExist:
                return Response({"error": "Unauthorized: You don’t have access to this branch."}, status=status.HTTP_403_FORBIDDEN)
        else:
            branch = get_object_or_404(Branch, branch_code=branch_code)

        # Query assets based on the branch
        assets = Asset.objects.filter(branch=branch)

        if not assets:
            return Response({"message": f"No assets found for branch_code '{branch_code}'"}, status=status.HTTP_404_NOT_FOUND)

        # Serialize the asset data
        serializer = AssetSerializer(assets, many=True)
        total_count = assets.count()
        monitor_count = assets.filter(group__iexact="IT").count()
        
        response_data = {
            "branch_code": branch.branch_code,
            "branch_name": branch.branch_name,
            "assets": serializer.data,
            "All asset":total_count,
            "monitor":monitor_count
        }

        
        return Response(response_data, status=status.HTTP_200_OK)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def asset_tag_generate(request):
    branch_code = request.data.get('branch_code')
    ownership = request.data.get('ownership')
    group = request.data.get('group')
    serial_number = request.data.get('serial_number')

    if not (branch_code and ownership and group):
        return Response({"detail": "Missing required fields."}, status=400)

    middle_code = 'UST' if ownership == "UST" else 'MPG'

    group_map = {
        'SDWAN': 'SDW',
        'Switch': 'SWT',
        'Monitor': 'MON',
        'Modem': 'MOD',
        'DotMatrix': 'PTR',
        'All in One': 'AIO',
        'Laser': 'LSRPTR',
        'Inkjet': 'INJPTR',
        'Webcam': 'WCM',
        'UPS': 'UPS',
        'Datacard': 'DC'
    }

    try:
        branch = Branch.objects.get(branch_code=branch_code)
    except Branch.DoesNotExist:
        return Response({"detail": "Invalid branch code."}, status=404)

    branch_code_upper = branch_code.upper()

    if group not in group_map:
        return Response({"detail": "Invalid group."}, status=400)

    last_asset = Asset.objects.filter(branch=branch, group=group).order_by('-asset_tag').first()
    last_asset_tag = last_asset.asset_tag if last_asset else None

    if group == 'Webcam':
        prefix = f"MPG-{branch_code_upper}"
        if last_asset_tag:
            last_number = int(last_asset_tag.split('-')[-1])
            new_number = str(last_number + 1).zfill(3)
        else:
            new_number = '001'
        new_asset_tag = f"{prefix}-{new_number}"

    elif group == 'Datacard':
        prefix = f"{middle_code}-{branch_code_upper}"
        if last_asset_tag:
            last_number = int(last_asset_tag.split('-')[-1])
            new_number = str(last_number + 1).zfill(3)
        else:
            new_number = '001'
        new_asset_tag = f"{prefix}-{new_number}"

    elif group == 'UPS':
        prefix = f"MUTMPG-{branch_code_upper}"
        if last_asset_tag:
            last_number = int(last_asset_tag.split('-')[-1])
            new_number = str(last_number + 1).zfill(3)
        else:
            new_number = '001'
        new_asset_tag = f"{prefix}-{new_number}"

    else:
        t = group_map[group]
        if last_asset_tag:
            parts = last_asset_tag.split('-')

            if group == 'Modem':
                parts[1] = middle_code
            elif group == 'SDWAN':
                parts[1] = 'UST'
            else:
                parts[1] = 'MPG'

            last_number = int(parts[-1])
            parts[-1] = str(last_number + 1).zfill(3)
            new_asset_tag = '-'.join(parts)
        else:
            if group == 'Modem':
                middle_code = middle_code
            elif group == 'SDWAN':
                middle_code = 'UST'
            else:
                middle_code = 'MPG'

            new_asset_tag = f"USTMUT-{middle_code}-{branch_code_upper}-{t}-001"

    return Response({
        "new_asset_tag": new_asset_tag
    })


class AssetAdditionView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        # Collect data from the request
        asset_data = request.data
        
        # Ensure all required fields are in the request data
        required_fields = ['branch_code', 'employee_id', 'employee_name', 'group', 'business_impact', 'asset_tag', 'product_name', 'serial_number', 'status']
        if not all(field in asset_data for field in required_fields):
            return Response({"detail": "Missing required fields."}, status=status.HTTP_400_BAD_REQUEST)

        try:
           
            branch = Branch.objects.get(branch_code=asset_data['branch_code'])
        except Branch.DoesNotExist:
            return Response({"detail": "Invalid branch_code."}, status=status.HTTP_400_BAD_REQUEST)

        
        last_asset = AssetAddition.objects.filter(branch=branch).order_by('asset_id').last()
        
        # Generate a new asset_id based on the last one
        if last_asset:
            last_asset_number = int(last_asset.asset_id.split('-')[-1])
            new_asset_number = str(last_asset_number + 1).zfill(3)  # Increment and pad with zeros (e.g., ASSET-BR001-002)
        else:
            new_asset_number = '001'  

        new_asset_id = f"ASSET-{branch.branch_code}-{new_asset_number}"

        # Create the new asset addition entry
        asset_addition = AssetAddition.objects.create(
            asset_id=new_asset_id,  
            branch=branch,
            employee_id=asset_data['employee_id'],
            employee_name=asset_data['employee_name'],
            group=asset_data['group'],
            business_impact=asset_data['business_impact'],
            asset_tag=asset_data['asset_tag'], 
            description=asset_data.get('description', ''), 
            product_name=asset_data['product_name'],
            serial_number=asset_data['serial_number'],
            remarks=asset_data.get('remarks', ''),
            status=asset_data['status'],
            it_poc_remarks=asset_data.get('it_poc_remarks', ''), 
        )

        
        serializer = AssetAdditionSerializer(asset_addition)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    
class AssetUpdateView(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request):
        asset_id = request.data.get('asset_id')
        new_status = request.data.get('status')
        new_it_poc_remarks = request.data.get('it_poc_remarks', '')

        if not asset_id or not new_status:
            return Response({"detail": "Asset ID and status are required."}, status=status.HTTP_400_BAD_REQUEST)

        asset = get_object_or_404(Asset, asset_id=asset_id)

      
        asset_addition, created = AssetAddition.objects.update_or_create(
            asset_id=asset.asset_id,
            defaults={
                'branch': asset.branch,
                'employee_id': asset.employee_id,
                'employee_name': asset.employee_name,
                'group': asset.group,
                'business_impact': asset.business_impact,
                'asset_tag': asset.asset_tag,
                'description': asset.description,
                'product_name': asset.product_name,
                'serial_number': asset.serial_number,
                'remarks': asset.remarks,
                'status': new_status, 
                'it_poc_remarks': new_it_poc_remarks  
            }
        )

        serializer = AssetAdditionSerializer(asset_addition)
        return Response(serializer.data, status=status.HTTP_200_OK if not created else status.HTTP_201_CREATED)
    


class Echo:
    """A helper class to stream CSV rows (acts like a file object)."""
    def write(self, value):
        return value

class AssetExportStreamView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
       
        user = request.user
        user_uid = user.uid 
        
      
        try:
            branch = Branch.objects.get(user=user)  
        except Branch.DoesNotExist:
            return HttpResponse("No branch assigned to user.", status=400)

     
        assets = Asset.objects.filter(branch=branch)

        if not assets:
            return HttpResponse("No assets found for the assigned branch.", status=404)

        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="assets.csv"'

        writer = csv.writer(response)

        writer.writerow([
            'Asset ID', 'Branch Code', 'Employee ID', 'Employee Name', 'Group', 'Business Impact', 
            'Asset Tag', 'Description', 'Product Name', 'Serial Number', 'Remarks', 'Status', 'IT POC Remarks'
        ])

       
        for asset in assets:
            writer.writerow([
                asset.asset_id,
                asset.branch.branch_code,
                asset.employee_id,
                asset.employee_name,
                asset.group,
                asset.business_impact,
                asset.asset_tag,
                asset.description,
                asset.product_name,
                asset.serial_number,
                asset.remarks,
                asset.status,
                asset.it_poc_remarks
            ])

        return response
    

class ExportBranchCSVView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        branch_code = request.query_params.get('branch_code')

        if not branch_code:
            return Response({"error": "branch_code is required"}, status=status.HTTP_400_BAD_REQUEST)

        user = request.user
        is_admin = user.role == 'admin'

        if is_admin:
            branch = get_object_or_404(Branch, branch_code=branch_code)
        else:
            try:
                branch = Branch.objects.get(branch_code=branch_code, user=user)
            except Branch.DoesNotExist:
                return Response({"error": "Unauthorized access to this branch."}, status=status.HTTP_403_FORBIDDEN)

        assets = Asset.objects.filter(branch=branch)

        # Prepare CSV response
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="{branch_code}_assets.csv"'

        writer = csv.writer(response)
        writer.writerow([
        'Asset ID', 'Employee ID', 'Employee Name', 'Group', 'Business Impact',
        'Asset Tag', 'Description', 'Product Name', 'Serial Number',
        'Remarks', 'Status', 'IT POC Remarks', 'Branch Code'
    ])

    
        for asset in assets:
            writer.writerow([
                asset.asset_id,
                asset.employee_id,
                asset.employee_name,
                asset.group,
                asset.business_impact,
                asset.asset_tag,
                asset.description,
                asset.product_name,
                asset.serial_number,
                asset.remarks,
                asset.status,
                asset.it_poc_remarks,
                asset.branch.branch_code  # Assuming ForeignKey to Branch
            ])

        return response
    
class ProductModelListView(APIView):
    def get(self, request):
        product_name = request.query_params.get('product_name')
        if not product_name:
            return Response({"error": "product_name is required"}, status=status.HTTP_400_BAD_REQUEST)

        models = ProductModel.objects.filter(product_name__iexact=product_name).values_list('model_name', flat=True)
        return Response(list(models), status=status.HTTP_200_OK)