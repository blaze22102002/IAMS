from django.db import models
import uuid
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager
from django.contrib.auth.models import BaseUserManager
from django.contrib.auth.models import PermissionsMixin
from django.utils import timezone

class UserManager(BaseUserManager):
    def get_by_natural_key(self, empid):
        return self.get(empid=empid)

    def create_user(self, empid, email, password=None,**extra_fields):
        if not empid:
            raise ValueError('The EmpID must be set')
        email = self.normalize_email(email)
        user = self.model(empid=empid, email=email, **extra_fields)
        user.set_password(password) 
        user.save(using=self._db)
        return user

    def create_superuser(self, empid, email, password=None, **extra_fields):
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_staff', True) 
        extra_fields.setdefault('role', 'admin')
        return self.create_user(empid, email, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    uid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    empid = models.CharField(max_length=150, unique=True)
    name = models.CharField(max_length=150)
    email = models.EmailField(max_length=255, unique=True)
    password = models.CharField(max_length=255)
    last_login = models.DateTimeField(blank=True, null=True)
    is_superuser = models.BooleanField(default=False)
    is_staff = models.BooleanField(default=False)
    role = models.CharField(max_length=20, choices=[('admin', 'Admin'), ('user', 'User')], default='user')

    objects = UserManager()  

    
    def save(self, *args, **kwargs):
        if not self.last_login and self.pk:  # Check if the user is already created
            self.last_login = timezone.now()
        super().save(*args, **kwargs)

    USERNAME_FIELD = 'empid'
    REQUIRED_FIELDS = ['email','name','password',] 

    def __str__(self):
        return self.empid

class Branch(models.Model):
    branch_code = models.CharField(max_length=10, unique=True)
    branch_name = models.CharField(max_length=100) 
    user = models.ForeignKey(User, on_delete=models.PROTECT, to_field='uid')

    def __str__(self):
        return f"{self.branch_code} - {self.branch_name}"


class Asset(models.Model):
    asset_id = models.CharField(max_length=50, unique=True)  
    branch = models.ForeignKey(Branch, on_delete=models.PROTECT)
    employee_id = models.CharField(max_length=50)
    employee_name = models.CharField(max_length=100)
    group = models.CharField(max_length=100)
    business_impact = models.CharField(max_length=100)
    asset_tag = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    product_name = models.CharField(max_length=100)
    serial_number = models.CharField(max_length=100)  
    remarks = models.TextField(blank=True)
    status = models.CharField(max_length=100)
    it_poc_remarks = models.TextField(blank=True)

    def __str__(self):
        return f"{self.asset_tag} - {self.serial_number}"


class Admin(models.Model):
    uid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    empid = models.CharField(max_length=150, unique=True)
    email = models.EmailField(max_length=255, unique=True)
    password = models.CharField(max_length=255)

    objects = UserManager()

    USERNAME_FIELD = 'empid'
    REQUIRED_FIELDS = ['email', 'password'] 

    

    



    def __str__(self):
        return self.empid
