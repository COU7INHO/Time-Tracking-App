# accounts/views.py
from rest_framework import generics, status, permissions
from rest_framework.permissions import AllowAny
from django.contrib.auth.models import User
from rest_framework.authtoken.models import Token
from rest_framework.authentication import TokenAuthentication
from rest_framework.response import Response
from django.contrib.auth import authenticate
from main_app.api.authentication.models import Profile
from main_app.api.authentication.serializers import UserRegisterSerializer, LoginSerializer, ProfileSerializer

class RegisterView(generics.CreateAPIView):
    """
    API endpoint for registering a new user.

    This view allows anyone (no authentication required) to create a new User 
    instance using the UserRegisterSerializer.
    """
    queryset = User.objects.all()
    serializer_class = UserRegisterSerializer
    permission_classes = [AllowAny]

class LoginView(generics.GenericAPIView):
    """
    API endpoint for user login.

    This view allows users to authenticate with their username and password.
    If the credentials are valid, an authentication token is returned along with 
    the user's ID and username.
    """
    permission_classes = [AllowAny]
    serializer_class = LoginSerializer

    def post(self, request, *args, **kwargs):
        """
        Handle POST requests for user authentication.

        Args:
            request (Request): The HTTP request containing username and password.
            *args: Additional positional arguments.
            **kwargs: Additional keyword arguments.

        Returns:
            Response: 
                - 200 OK with token, user_id, and username if authentication succeeds.
                - 401 Unauthorized with an error message if credentials are invalid.
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = authenticate(
            username=serializer.validated_data['username'],
            password=serializer.validated_data['password']
        )
        if not user:
            return Response({"detail": "Invalid credentials"}, status=status.HTTP_401_UNAUTHORIZED)

        token, created = Token.objects.get_or_create(user=user)
        return Response({
            'token': token.key,
            'user_id': user.id,
            'username': user.username
        })


class ProfileView(generics.GenericAPIView):
    """
    API endpoint for retrieving and updating the authenticated user's profile.

    This view ensures that only the logged-in user can access and modify 
    their own Profile instance. Authentication via token is required.
    """
    serializer_class = ProfileSerializer
    permission_classes = [permissions.IsAuthenticated]
    authentication_classes = [TokenAuthentication]

    def get_queryset(self):
        """
        Define the queryset as the profile of the currently authenticated user.

        Returns:
            QuerySet: A queryset containing the profile linked to the logged-in user.
        """
        return Profile.objects.filter(user=self.request.user)

    def get_object(self):
        """
        Retrieve the single Profile object for the authenticated user.

        Unlike typical DRF behavior, this method does not rely on a 'pk'
        in the URL but instead fetches the profile directly from the queryset.

        Returns:
            Profile: The profile instance associated with the authenticated user.
        """
        queryset = self.get_queryset()
        obj = generics.get_object_or_404(queryset)
        return obj

    def get(self, request, *args, **kwargs):
        """
        Handle GET requests to fetch the user's profile data.

        Args:
            request (Request): The HTTP request object.
            *args: Additional positional arguments.
            **kwargs: Additional keyword arguments.

        Returns:
            Response: JSON representation of the user's profile.
        """
        profile = self.get_object()
        serializer = self.get_serializer(profile)
        return Response(serializer.data)

    def patch(self, request, *args, **kwargs):
        """
        Handle PATCH requests to update the user's profile.

        Args:
            request (Request): The HTTP request containing updated profile fields.
            *args: Additional positional arguments.
            **kwargs: Additional keyword arguments.

        Returns:
            Response: JSON representation of the updated profile.
        """
        profile = self.get_object()
        serializer = self.get_serializer(profile, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)