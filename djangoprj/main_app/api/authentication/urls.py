# accounts/urls.py
from django.urls import path
from main_app.api.authentication import views

"""
Authentication URL patterns.

This module defines the endpoints for user authentication and profile handling:
- /register/ : Register a new user account.
- /login/    : Authenticate an existing user.
- /profile/  : Retrieve or update the profile information of the logged-in user.
"""

AUTH_URLS = [
    path('register/', views.RegisterView.as_view(), name='register'),
    path('login/', views.LoginView.as_view(), name='login'),
    path('profile/', views.ProfileView.as_view(), name='profile'),
]
