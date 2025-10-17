from django.contrib.auth.models import AbstractUser
from django.db import models
from .managers import CustomUserManager  

class User(AbstractUser):
    objects = CustomUserManager()
    USER_TYPES = (
        ('manager', 'manager'),
        ('staff', 'staff'),
    )
    
    user_type = models.CharField(max_length=20, choices=USER_TYPES, default='resident')
    phone = models.CharField(max_length=15, unique=True, null=True, blank=True)
    national_code = models.CharField(max_length=10, null=True, blank=True)
    is_verified = models.BooleanField(default=False)
    avatar = models.ImageField(upload_to='avatars/', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # 
    username = None
    email = models.EmailField(unique=True)
    
    # for 
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name']
    
    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.user_type})"
    
    class Meta:
        db_table = 'users'
        verbose_name = 'user'
        verbose_name_plural = 'users'