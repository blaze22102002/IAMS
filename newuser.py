# newuser.py
import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Backend.settings')  
django.setup()

from django.contrib.auth.hashers import make_password
from api.models import User
import uuid

def create_user(empid,name, email, plain_password):
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

# Call the function to create a new user
create_user("test2","test222", "test1@gmail.com", "pass23")
