import pandas as pd
from .models import User, Branch, Asset
from django.contrib.auth.hashers import make_password
from django.db import transaction

@transaction.atomic
def import_users_from_csv(file_path):
    df = pd.read_csv(file_path)
    for _, row in df.iterrows():
        User.objects.update_or_create(
            empid=row['empid'],
            defaults={
                'name': row['name'],
                'email': row['email'],
                'password': make_password(row['password']),
                'role': 'user',
                'is_staff': False,
                'is_superuser': False,
            }
        )

@transaction.atomic
def import_branches_from_csv(file_path):
    df = pd.read_csv(file_path)
    for _, row in df.iterrows():
        user = User.objects.get(empid=row['user_empid'])
        Branch.objects.update_or_create(
            branch_code=row['branch_code'],
            defaults={
                'branch_name': row['branch_name'],
                'user': user,
            }
        )

@transaction.atomic
def import_assets_from_csv(file_path):
    df = pd.read_csv(file_path)
    for _, row in df.iterrows():
        branch = Branch.objects.get(branch_code=row['branch_code'])
        Asset.objects.update_or_create(
            asset_id=row['asset_id'],
            defaults={
                'branch': branch,
                'employee_id': row['employee_id'],
                'employee_name': row['employee_name'],
                'group': row['group'],
                'business_impact': row['business_impact'],
                'asset_tag': row['asset_tag'],
                'description': row.get('description', ''),
                'product_name': row['product_name'],
                'serial_number': row['serial_number'],
                'remarks': row.get('remarks', ''),
                'status': row['status'],
                'it_poc_remarks': row.get('it_poc_remarks', ''),
            }
        )
