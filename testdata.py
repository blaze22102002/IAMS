import random
import uuid
from api.models import User, Branch, Asset  


# Create multiple users
users = []
for i in range(5):
    user = User.objects.create_user(
        empid=f'EMP10{i}',
        email=f'user{i}@example.com',
        password='password123',
        name=f'User {i}',
        is_superuser=False
    )
    users.append(user)

# Create 10 branches and assign random users to each
branch_codes = [f'F{str(i).zfill(3)}' for i in range(1, 11)]  
branches = []

for code in branch_codes:
    branch = Branch.objects.create(
        branch_code=code,
        branch_name=f"Branch {code}",
        user=random.choice(users)
    )
    branches.append(branch)

# Asset groups
asset_groups = [
    'Dotmatrix printer', 'All-in-one printer', 'Biometric',
    'SD-WAN', 'Modem', 'Monitor', 'Desktop',
    'Laptop', 'ThinClient', 'UPS', 'Webcam'
]

# Create 20 assets
for i in range(20):
    branch = random.choice(branches)
    group = random.choice(asset_groups)
    Asset.objects.create(
        asset_id=f"AST{i+1:03d}",
        branch=branch,
        employee_id=f"EMP{i+20:03d}",
        employee_name=f"Employee {i+20}",
        group=group,
        business_impact=random.choice(['High', 'Medium', 'Low']),
        asset_tag=f"TAG{i+1:04d}",
        description=f"Asset {group} assigned to {branch.branch_code}",
        product_name=f"{group} Model {chr(65 + i % 26)}",
        serial_number=f"SN{i+1000}",
        remarks="Auto-generated asset",
        status=random.choice(['Active', 'Inactive']),
        it_poc_remarks="Initial load"
    )

print("Users, branches, and assets created successfully.")
