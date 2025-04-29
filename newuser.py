import os
import django
import pandas as pd
import uuid
from django.contrib.auth.hashers import make_password
from api.models import User

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Backend.settings')  # Replace with your actual project name
django.setup()

def create_user(empid, name, email, plain_password):
    try:
        hashed_password = make_password(plain_password)  # Hash the password
        user = User.objects.create(
            uid=uuid.uuid4(),  
            empid=empid,
            name=name,
            email=email,
            password=hashed_password
        )
        print(f"User '{user.name}' created successfully with UID: {user.uid}")
    except Exception as e:
        print("Error creating user:", e)

# Read the CSV file
csv_file = r"C:\Users\bbnit\Downloads\users.csv"  # Update with the correct path to your CSV file
df = pd.read_csv(csv_file)

# Loop through each row in the CSV and create users
for _, row in df.iterrows():
    create_user(row['empid'], row['name'], row['email'], row['password'])
