from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from main_app.api.authentication.models import Profile

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """
    Signal handler that creates a Profile whenever a new User is created.

    Args:
        sender (Model): The model class (User) that triggered the signal.
        instance (User): The actual User instance being saved.
        created (bool): Whether this instance was created (True) or updated (False).
        **kwargs: Additional keyword arguments.

    Returns:
        None
    """
    if created:
        Profile.objects.create(user=instance)
