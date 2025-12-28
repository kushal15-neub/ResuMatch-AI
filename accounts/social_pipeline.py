"""
Custom social auth pipeline functions
"""

from social_core.pipeline.user import get_username
from social_core.exceptions import AuthAlreadyAssociated
from django.contrib.auth.models import User


def associate_by_email(backend, details, user=None, *args, **kwargs):
    """
    Associate user by email if user is None
    """
    if user:
        return None

    email = details.get("email")
    if email:
        try:
            # Try to find existing user by email
            existing_user = User.objects.get(email=email)
            return {"user": existing_user, "is_new": False}
        except User.DoesNotExist:
            pass
        except User.MultipleObjectsReturned:
            # If multiple users exist, get the most recent one
            existing_user = (
                User.objects.filter(email=email).order_by("-date_joined").first()
            )
            return {"user": existing_user, "is_new": False}

    return None


def create_user_with_unique_username(
    strategy, details, backend, user=None, *args, **kwargs
):
    """
    Create user with unique username if user doesn't exist
    """
    if user:
        return {"is_new": False, "user": user}

    email = details.get("email")
    if not email:
        return None

    # Generate unique username
    username = get_username(details)

    # If username already exists, make it unique
    counter = 1
    original_username = username
    while User.objects.filter(username=username).exists():
        username = f"{original_username}{counter}"
        counter += 1

    # Create user with unique username
    user = strategy.create_user(
        username=username,
        email=email,
        first_name=details.get("first_name", ""),
        last_name=details.get("last_name", ""),
    )

    return {"is_new": True, "user": user}
