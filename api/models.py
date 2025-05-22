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
    
    def save(self, *args, **kwargs):
        # Check if the asset is being updated (i.e., it has an existing primary key `pk`)
        is_update = self.pk is not None

        # Save the asset in the Asset table (original table)
        super().save(*args, **kwargs)

        # If it's an update, copy this asset to AssetAddition table
        if is_update:
            # Create a new entry in AssetAddition with the same data
            asset_addition = AssetAddition(
                asset_id=self.asset_id,
                branch=self.branch,
                employee_id=self.employee_id,
                employee_name=self.employee_name,
                group=self.group,
                business_impact=self.business_impact,
                asset_tag=self.asset_tag,
                description=self.description,
                product_name=self.product_name,
                serial_number=self.serial_number,
                remarks=self.remarks,
                status=self.status,
                it_poc_remarks=self.it_poc_remarks
            )
            asset_addition.save()
    

class AssetAddition(models.Model):
    asset_id = models.CharField(max_length=50, unique=True, blank=True)  # Make sure this is blank initially
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
    timestamp = models.DateTimeField(auto_now_add=True)  # Timestamp when the asset was added/updated

    def __str__(self):
        return f"{self.asset_tag} - {self.serial_number}"

    def save(self, *args, **kwargs):
        # Auto-generate asset_id if it doesn't already exist
        if not self.asset_id:
            # Get the last asset by asset_id and increment it
            last_asset = AssetAddition.objects.order_by('-asset_id').first()
            if last_asset:
                # Extract the last numeric part and increment it
                last_asset_number = int(last_asset.asset_id.split('-')[-1])
                new_asset_number = last_asset_number + 1
            else:
                # If no assets exist, start from 1
                new_asset_number = 1

            # Format the asset_id (for example: "ASSET-001")
            self.asset_id = f"ASSET-{str(new_asset_number).zfill(3)}"
        
        super().save(*args, **kwargs)


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

# models.py
class ProductModel(models.Model):
    product_name = models.CharField(max_length=100)  # e.g., Webcam, Printer
    model_name = models.CharField(max_length=100)    # e.g., C270, LX-310

    def __str__(self):
        return f"{self.product_name} - {self.model_name}"
