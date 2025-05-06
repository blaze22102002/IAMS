from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate
from rest_framework.permissions import AllowAny
from .models import User, Asset,Branch,Admin
from .serializers import AssetSerializer
import requests
from rest_framework.decorators import api_view, permission_classes
from django.db import connection
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.response import Response
from django.http import JsonResponse
from rest_framework.permissions import IsAuthenticated
from django.contrib.auth import authenticate, get_user_model
from django.db import IntegrityError
from django.core.mail import send_mail
from django.core.cache import cache
from django.http import JsonResponse
import random
import string
from django.utils import timezone


User = get_user_model()
class LoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        identifier = request.data.get("empid")  # Could be empid or email
        password = request.data.get("password")
        otp = request.data.get("otp")  # Optional on first call

        if not identifier or not password:
            return Response({"detail": "empid/email and password are required."}, status=status.HTTP_400_BAD_REQUEST)

        # Authenticate credentials
        user = authenticate(request, username=identifier, password=password)
        if user is None:
            return Response({"detail": "Invalid credentials"}, status=status.HTTP_401_UNAUTHORIZED)

        # Check if OTP is provided
        if not otp:
            # First step: generate and send OTP
            generated_otp = ''.join(random.choices(string.digits, k=6))
            cache.set(f"otp_{user.empid}", generated_otp, timeout=300)  
            from_email = 'no-reply@example.com' 

            # Send email
            send_mail(
                subject='Your OTP for Login',
                message=f'Your OTP is {generated_otp}. It is valid for 5 minutes.',
                from_email=from_email,
                recipient_list=[user.email],
                fail_silently=False,
            )

            return Response({"detail": "OTP sent to registered email. Please verify.", "empid": user.empid}, status=status.HTTP_200_OK)

    
        cached_otp = cache.get(f"otp_" + user.empid)
        if cached_otp != otp:
            return Response({"detail": "Invalid or expired OTP"}, status=status.HTTP_401_UNAUTHORIZED)

      
        refresh = RefreshToken.for_user(user)
        refresh['username'] = user.empid
        refresh['role'] = 'admin' if user.is_superuser else 'user'

        access_token = str(refresh.access_token)
        refresh_token = str(refresh)

        response = JsonResponse({
            'message': 'Login successful.',
            'username': user.empid,
            'role': refresh['role'],
            'access': access_token,
            'refresh': refresh_token
        })

        # Set secure HTTP-only cookies
        response.set_cookie('access_token', access_token, httponly=True, secure=True, max_age=5 * 60, samesite='Strict')
        response.set_cookie('refresh_token', refresh_token, httponly=True, secure=True, max_age=24 * 60 * 60, samesite='Strict')

        user.last_login = timezone.now()
        user.save()

        # Clear OTP from cache after success
        cache.delete(f"otp_{user.empid}")

        return response

    
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
    

@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def filter_branch(request):
    user = request.user

    branch_code = request.query_params.get('branch_code') or request.data.get('branch_code')
    print(branch_code)
    
    if not branch_code:
        return Response({"error": "branch_code is required"}, status=status.HTTP_400_BAD_REQUEST)

    # Check if user is admin or not
    is_admin = user.role == 'admin'  

    branch_id = None
    if not is_admin:
      
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
    else:
      
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT branch.id
                FROM api_branch AS branch
                WHERE branch.branch_code = %s
            """, [branch_code])
            branch_row = cursor.fetchone()

        if not branch_row:
            return Response({"error": "Branch not found."}, status=status.HTTP_404_NOT_FOUND)

        branch_id = branch_row[0]

    # Fetch assets for the determined branch_id
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
                COUNT(IF(`group` = 'Laptop', 1, NULL)) AS laptop,
                COUNT(IF(`group` = 'Biometric', 1, NULL)) AS biometric,
                COUNT(IF(`group` = 'ThinClient', 1, NULL)) AS thinclient
            FROM api_asset
            WHERE branch_id = %s
        """, [branch_id])
        counts = dict(zip([col[0] for col in cursor.description], cursor.fetchone()))

    if not assets:
        return Response({"message": f"No assets found for branch_code '{branch_code}'"}, status=status.HTTP_404_NOT_FOUND)

    return Response({
        "branch_code": branch_code,
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


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def add_asset(request):
    try:
        data = request.data
        empid = data.get('empid')
        branch_code = data.get('branch_code')

        if not empid or not branch_code:
            return Response({'error': 'empid and branch_code are required.'}, status=status.HTTP_400_BAD_REQUEST)

        # Check if the user exists
        try:
            user = User.objects.get(empid=empid)
        except User.DoesNotExist:
            return Response({'error': 'User with this empid does not exist.'}, status=status.HTTP_404_NOT_FOUND)

        # Check if branch exists
        try:
            branch = Branch.objects.get(branch_code=branch_code)
        except Branch.DoesNotExist:
            return Response({'error': 'Branch with this code does not exist.'}, status=status.HTTP_404_NOT_FOUND)

      
        if branch.user != user:
            return Response({'error': 'User does not have permission to add assets for this branch.'}, status=status.HTTP_403_FORBIDDEN)

        # Create asset
        asset = Asset.objects.create(
            asset_id=data.get('asset_id'),
            branch=branch,
            employee_id=data.get('employee_id'),
            employee_name=data.get('employee_name'),
            group=data.get('group'),
            business_impact=data.get('business_impact'),
            asset_tag=data.get('asset_tag'),
            description=data.get('description', ''),
            product_name=data.get('product_name'),
            serial_number=data.get('serial_number'),
            remarks=data.get('remarks', ''),
            status=data.get('status'),
            it_poc_remarks=data.get('it_poc_remarks', '')
        )

        return Response({'message': 'Asset created successfully!', 'asset_id': asset.asset_id}, status=status.HTTP_201_CREATED)
    
    except IntegrityError:
        return Response({'error': 'Asset with this ID or tag already exists.'}, status=status.HTTP_400_BAD_REQUEST)
    
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)