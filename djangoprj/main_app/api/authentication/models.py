from django.db import models
from django.contrib.auth.models import User


class Profile(models.Model):
    """
    Represents additional user information linked to the built-in Django User model.

    Each user has a single Profile object that stores personal and professional
    details such as full name, company, team, and position.
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")
    name = models.CharField(max_length=100, blank=True, help_text="Full name")
    company = models.CharField(max_length=100, blank=True, help_text="Company's name")
    team = models.CharField(max_length=100, blank=True, help_text="Team name")
    position = models.CharField(max_length=100, blank=True, help_text="Job title or role")

    def __str__(self):
        return f"{self.user.username}'s Profile"
