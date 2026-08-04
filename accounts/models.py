from django.db import models
from django.contrib.auth.models import AbstractUser

class RoleChoice(models.TextChoices):
    SUPER_ADMIN = 'Super Admin', 'Super Admin'
    ADMINISTRATOR = 'Administrator', 'Administrator'
    STAFF = 'Staff', 'Staff'

class User(AbstractUser):
    role = models.CharField(max_length=20, choices=RoleChoice.choices, default=RoleChoice.STAFF)
    mobile = models.CharField(max_length=20, blank=True, null=True)
    
    # Module Permissions for Staff
    can_view_dashboard = models.BooleanField(default=False)
    can_manage_entry = models.BooleanField(default=False)
    can_edit_entry = models.BooleanField(default=False)
    can_manage_exit = models.BooleanField(default=False)
    can_edit_exit = models.BooleanField(default=False)
    can_collect_cash = models.BooleanField(default=False)
    can_view_reports = models.BooleanField(default=False)
    can_download_reports = models.BooleanField(default=False)
    can_manage_zones = models.BooleanField(default=False)
    can_edit_zones = models.BooleanField(default=False)
    can_manage_settings = models.BooleanField(default=False)

    def save(self, *args, **kwargs):
        if self.role == RoleChoice.SUPER_ADMIN:
            self.is_superuser = True
            self.is_staff = True
            # Super Admin has all permissions implicitly or explicitly
            self._set_all_permissions(True)
        elif self.role == RoleChoice.ADMINISTRATOR:
            self.is_staff = True
            # Administrator has almost all, except maybe some settings handled in views
            self._set_all_permissions(True)
        super().save(*args, **kwargs)

    def _set_all_permissions(self, val):
        self.can_view_dashboard = val
        self.can_manage_entry = val
        self.can_edit_entry = val
        self.can_manage_exit = val
        self.can_edit_exit = val
        self.can_collect_cash = val
        self.can_view_reports = val
        self.can_download_reports = val
        self.can_manage_zones = val
        self.can_edit_zones = val
        self.can_manage_settings = val

    def __str__(self):
        return f"{self.username} ({self.role})"
