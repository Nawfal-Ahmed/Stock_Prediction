from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.utils import timezone
class AdminManager(BaseUserManager):
    def create_admin(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("Admin must have an email")
        email = self.normalize_email(email)
        admin = self.model(email=email, **extra_fields)
        admin.set_password(password)
        admin.save(using=self._db)
        return admin

class AdminUser(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(unique=True)
    full_name = models.CharField(max_length=100)
    is_active = models.BooleanField(default=True)
    is_superadmin = models.BooleanField(default=False)

    # Fix for clashes
    groups = models.ManyToManyField(
        "auth.Group",
        related_name="admin_users",  # unique name
        blank=True
    )
    user_permissions = models.ManyToManyField(
        "auth.Permission",
        related_name="admin_users_permissions",  #unique name
        blank=True
    )

    objects = AdminManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['full_name']

    def __str__(self):
        return self.email