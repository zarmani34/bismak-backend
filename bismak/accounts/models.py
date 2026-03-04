from django.db import models

# Create your models here.
# apps/accounts/models.py
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.contrib.auth.base_user import BaseUserManager
from commmon.models import UUIDTimeStampedModel


class UserManager(BaseUserManager):
    use_in_migrations = True

    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("The Email must be set")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self.create_user(email, password, **extra_fields)

class Organisation(UUIDTimeStampedModel):
    company_name = models.CharField(max_length=255)
    company_address = models.CharField(max_length=255, blank=True)

    def __str__(self):
        return self.company_name


class User(AbstractUser):
    username = None
    email = models.EmailField(unique=True)
    phone_number = models.CharField(max_length=20, blank=True)
    user_id = models.CharField(max_length=30, blank=True, unique=True, null=True)  # Only for staff and admin, auto-generated based on role and count of existing users in that role
    
    ROLE_CHOICES = (
        ('admin', 'Admin'),
        ('staff', 'Staff'),
        ('client', 'Client'),
    )
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='client') #Users should not be able to change their role
    organisation = models.OneToOneField(
        Organisation, on_delete=models.SET_NULL,
        null=True, blank=True, related_name="user"
    )

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    objects = UserManager()

    def __str__(self):
        return f"{self.get_full_name()} ({self.email})"
    
    def generate_user_id(self):
        if self.role == 'admin':
            prefix = 'BE-ADM'
        elif self.role == 'staff':
            prefix = 'BE-STF'
        elif self.role == 'client':
            prefix = 'BE-CLT' 
        count = User.objects.filter(role=self.role).count() + 1
        
        return f"{prefix}-{str(count).zfill(4)}" 
    
    def save(self, *args, **kwargs):
        if not self.user_id and self.role in ('staff', 'admin'):
            self.user_id = self.generate_user_id()
        super().save(*args, **kwargs)


# To add other organizational user types like contractors, suppliers etc, we can either:
# 1. Add more roles to the existing User model and use the 'role' field to differentiate them.
# 2. Create separate models for each user type (e.g., Contractor, Supplier) that have a OneToOne relationship with the User model. This allows for more specific fields and permissions for each user type while still maintaining a common authentication system through the User model.   