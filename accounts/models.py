from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta

# Create your models here.


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    phone = models.CharField(max_length=15, blank=True)
    job_title = models.CharField(max_length=100, blank=True)
    experience = models.CharField(max_length=20, blank=True)

    def __str__(self):
        return f"{self.user.username}'s profile"


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)


@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    instance.profile.save()


def default_token_expiry():
    return timezone.now() + timedelta(hours=1)


class PasswordResetToken(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    token = models.CharField(max_length=100, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(default=default_token_expiry)
    used = models.BooleanField(default=False)

    def is_valid(self):
        return not self.used and timezone.now() < self.expires_at

    def __str__(self):
        return f"Reset Token for {self.user.email}"


class CVTemplate(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField()
    html_template = models.TextField()  # HTML template content
    css_styles = models.TextField()  # CSS styles
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class UserCV(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    template = models.ForeignKey(
        CVTemplate, on_delete=models.CASCADE, null=True, blank=True
    )
    name = models.CharField(max_length=200, default="My CV")  # User-friendly name
    version = models.IntegerField(default=1)
    personal_info = models.JSONField(default=dict)  # Store CV data as JSON
    experience = models.JSONField(default=list)
    education = models.JSONField(default=list)
    skills = models.JSONField(default=list)
    projects = models.JSONField(default=list)
    profile_photo = models.TextField(blank=True)  # Base64 encoded image
    template_choice = models.CharField(max_length=20, default="classic")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-updated_at"]
        unique_together = ["user", "name", "version"]

    def __str__(self):
        return f"{self.user.username}'s CV - {self.name} (v{self.version})"

    def get_latest_version(self):
        """Get the latest version number for this CV name"""
        return (
            UserCV.objects.filter(user=self.user, name=self.name).aggregate(
                max_version=models.Max("version")
            )["max_version"]
            or 0
        )
