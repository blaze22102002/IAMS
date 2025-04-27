from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate
from rest_framework.permissions import AllowAny
from .models import User, Asset,Branch
from .serializers import AssetSerializer
import requests
from rest_framework.decorators import api_view, permission_classes
from django.db import connection
from rest_framework_simplejwt.tokens import RefreshToken
from django.conf import settings
from rest_framework.response import Response
from rest_framework_simplejwt.exceptions import InvalidToken
from django.http import JsonResponse
from rest_framework.permissions import IsAuthenticated
from django.http import HttpResponse


class LoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        empid = request.data.get("empid")
        password = request.data.get("password")

        # Authenticate the user
        user = authenticate(request, username=empid, password=password)

        if user is not None:
          
            refresh = RefreshToken.for_user(user)
            access_token = str(refresh.access_token)
            refresh_token = str(refresh)

       
            response = JsonResponse({
                'message': 'Login successful.',
                'empid': user.empid ,
                  'access': access_token,
                  'refresh': refresh_token
                  
            })
            # Set Access Token in cookie
            response.set_cookie(
                'access_token', access_token,
                httponly=True,
                secure=True, 
                max_age=5*60,  
                samesite='Strict'
            )
            # Set Refresh Token in cookie
            response.set_cookie(
                'refresh_token', refresh_token,
                httponly=True,
                secure=True, 
                max_age=24*60*60,  
                samesite='Strict'
            )
            return response
        else:
            return Response({"detail": "Invalid credentials"}, status=status.HTTP_401_UNAUTHORIZED)
class AssetWebhookView(APIView):
    def post(self, request):
        try:
            response = requests.get('http://localhost:5001/external-api/assets',timeout=5)
            if response.status_code == 200:
                assets_data = response.json()
            else:
                return Response({"error": "Failed to fetch data from Flask API"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        except requests.exceptions.RequestException as e:
            return Response({"error": f"Error fetching data: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        for asset_data in assets_data:
            branch_code = asset_data.pop("branch_code", None)

            try:
                branch = Branch.objects.get(branch_code=branch_code)
            except Branch.DoesNotExist:
                return Response({"error": f"Branch code {branch_code} does not exist"}, status=status.HTTP_400_BAD_REQUEST)

            asset_data["branch"] = branch.id

            try:
                asset_instance = Asset.objects.get(asset_id=asset_data['asset_id'])
            
                serializer = AssetSerializer(instance=asset_instance, data=asset_data)
            except Asset.DoesNotExist:
              
                serializer = AssetSerializer(data=asset_data)

            if serializer.is_valid():
                serializer.save()
            else:
                return Response({
                    "error": f"Invalid data for asset {asset_data.get('asset_id')}",
                    "details": serializer.errors
                }, status=status.HTTP_400_BAD_REQUEST)

        return Response({"message": "Assets created or updated successfully."}, status=status.HTTP_200_OK)
    

@api_view(['GET','POST'])
@permission_classes([IsAuthenticated])
def filter_branch(request):
    user = request.user

    branch_code = request.query_params.get('branch_code') or request.data.get('branch_code')
    print(branch_code)
   
    
    if not branch_code:
        return Response({"error": "branch_code is required"}, status=status.HTTP_400_BAD_REQUEST)

    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT branch.id 
            FROM api_branch AS branch
            INNER JOIN api_user AS user ON branch.user_id = user.uid
            WHERE branch.branch_code = %s AND user.empid = %s
        """, [branch_code, user.empid])
        branch_row = cursor.fetchone()

    if not branch_row:
        return Response({"error": "Unauthorized: You don’t have access to this branch."}, status=status.HTTP_403_FORBIDDEN)

    branch_id = branch_row[0]

    # Fetch assets
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT 
                asset.asset_id, asset.employee_id, asset.employee_name,
                asset.`group`, asset.business_impact, asset.asset_tag,
                asset.description, asset.product_name, asset.serial_number,
                asset.remarks, asset.status, asset.it_poc_remarks
            FROM api_asset AS asset
            WHERE asset.branch_id = %s
        """, [branch_id])

        columns = [col[0] for col in cursor.description]
        assets = [dict(zip(columns, row)) for row in cursor.fetchall()]


    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT
                COUNT(IF(`group` = 'Laptop', 1, NULL))    AS laptop,
                COUNT(IF(`group` = 'Biometric', 1, NULL)) AS biometric,
                COUNT(IF(`group` = 'ThinClient', 1, NULL)) AS thinclient
            FROM api_asset
            WHERE branch_id = %s
        """, [branch_id])
        counts = dict(zip([col[0] for col in cursor.description], cursor.fetchone()))

    if not assets:
        return Response({"message": f"No assets found for branch_code '{branch_code}'"}, status=status.HTTP_404_NOT_FOUND)

    return Response({
        "assets": assets,
        "counts": counts
    }, status=status.HTTP_200_OK)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def asset_tag_generate(request):
    branch_code = request.data.get('branch_code')
    ownership = request.data.get('ownership')
    group = request.data.get('group')
    serial_number = request.data.get('serial_number')

    if ownership == "UST":
        middle_code = 'UST'
    else:
        middle_code = 'MPG'

    group_map = {
        'SDWAN': 'SDW',
        'Switch': 'SWT',
        'Monitor':'MON',
        'Modem':'MOD',
        'DotMatrix':'PTR',
        'All in One':'AIO',
        'Laser':'LSRPTR',
        'Inkjet':'INJPTR'
    }
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT asset.asset_tag
            FROM api_asset AS asset
            INNER JOIN api_branch AS branch ON asset.branch_id = branch.id
            WHERE asset.`group` = %s AND branch.branch_code = %s
            ORDER BY asset.asset_tag DESC
            LIMIT 1
        """, [group, branch_code])
        
        row = cursor.fetchone()

    last_asset_tag = row[0] if row else None

    if group in ['Monitor', 'SDWAN', 'Switch', 'DotMatrix', 'All in One', 'Laser', 'Inkjet','Modem']:
        
         
        t = group_map[group]
         
            
        print(middle_code,branch_code,t)
        if last_asset_tag:
        
            parts = last_asset_tag.split('-')
            print(parts[3])

            if group in['Modem'] :
                parts[1] = middle_code
            elif group in ['SDWAN']:
                parts[1]='UST'
            else:
                parts[1]='MPG'  

            last_number = int(parts[-1])
            next_number = last_number + 1
            parts[-1] = str(next_number).zfill(3)

            new_asset_tag = '-'.join(parts)
        else:
            if group in['Modem'] :
                middle_code = middle_code
            elif group in['SDWAN']:
                middle_code='UST'
            else:
                middle_code='MPG'  
                
            branch = branch_code.upper()  
            new_asset_tag = f"USTMUT-{middle_code}-{branch}-{t}-001"

    return Response({
        "new_asset_tag": new_asset_tag
                    })             
    




# import csv
# import datetime


# def download_assets(request):
#     assets = Asset.objects.all()

    
#     response = HttpResponse(content_type='text/csv')
    
#     # Dynamically set the filename with a timestamp
#     filename = f"assets_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
#     response['Content-Disposition'] = f'attachment; filename="{filename}"'

#     # Create CSV writer
#     writer = csv.writer(response)
#     writer.writerow([
#         'employee_id', 'employee_name', 'group', 'business_impact', 'asset_tag',
#         'description', 'product_name', 'serial_number', 'remarks', 'status', 'branch_code', 'branch_name'
#     ])

#     # Write asset data rows
#     for asset in assets:
#         branch_id = Branch.objects.get(id=asset.branch_id)
#         branch_code = asset.branch_id.branch_code if asset.branch_id else ''
#         branch_name = asset.branch_id.name if asset.branch_id else ''

#         writer.writerow([
#             asset.employee_id, asset.employee_name, asset.group, asset.business_impact, asset.asset_tag,
#             asset.description, asset.product_name, asset.serial_number, asset.remarks, asset.status,
#             branch_code, branch_name
#         ])

#     return response