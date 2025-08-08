from django.db import models
from django.contrib.auth.models import User


class UserProfile(models.Model):
    ORGANIZATION_TYPES = [
        ('government', 'Government Agency'),
        ('academic', 'Academic Institution'),
        ('ngo', 'Non-Government Organization'),
        ('private', 'Private Organization'),
        ('individual', 'Individual Researcher'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    organization = models.CharField(max_length=255, blank=True)
    organization_type = models.CharField(max_length=20, choices=ORGANIZATION_TYPES, blank=True)
    department = models.CharField(max_length=255, blank=True)
    phone = models.CharField(max_length=20, blank=True)
    bio = models.TextField(blank=True)
    preferred_language = models.CharField(max_length=10, default='en')
    timezone = models.CharField(max_length=50, default='UTC')
    notification_preferences = models.JSONField(default=dict)
    api_access_level = models.CharField(
        max_length=20,
        choices=[
            ('basic', 'Basic'),
            ('advanced', 'Advanced'),
            ('admin', 'Administrator'),
        ],
        default='basic'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.get_full_name() or self.user.username} - {self.organization}"

    @property
    def display_name(self):
        return self.user.get_full_name() or self.user.username