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
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import api_view, permission_classes
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
           
            try:
                branch = Branch.objects.get(branch_code=branch_code, user=user)
            except Branch.DoesNotExist:
                return Response({"error": "Unauthorized: You don’t have access to this branch."}, status=status.HTTP_403_FORBIDDEN)
        else:
            
            branch = get_object_or_404(Branch, branch_code=branch_code)

      
        assets = Asset.objects.filter(branch=branch)

        if not assets:
            return Response({"message": f"No assets found for branch_code '{branch_code}'"}, status=status.HTTP_404_NOT_FOUND)

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
