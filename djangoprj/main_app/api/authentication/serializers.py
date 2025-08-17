from django.contrib.auth.models import User
from rest_framework import serializers
from main_app.api.authentication.models import Profile


class UserRegisterSerializer(serializers.ModelSerializer):
    """
    Serializer for registering a new user.

    Includes username, email, and password fields. 
    The password is write-only and used to create a new User instance.
    """
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ['username', 'email', 'password']

    def create(self, validated_data):
        """
        Create a new user instance with the given validated data.

        Args:
            validated_data (dict): Dictionary containing username, email, and password.

        Returns:
            User: A newly created User instance.
        """
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data.get('email'),
            password=validated_data['password']
        )
        return user

class LoginSerializer(serializers.Serializer):
    """
    Serializer for user login.

    Requires username and password credentials.
    """
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)


class ProfileSerializer(serializers.ModelSerializer):
    """
    Serializer for the Profile model.

    Provides user-related information such as name, company, team, position,
    and the associated user's email (read-only).
    """
    user_email = serializers.EmailField(source='user.email', read_only=True)

    class Meta:
        model = Profile
        fields = ['name', 'company', 'team', 'position', 'user_email']
