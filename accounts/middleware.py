"""
Authentication-aware navigation middleware
Prevents logged-in users from accessing login/register pages
"""

from django.shortcuts import redirect
from django.urls import reverse
from django.contrib.auth import logout


class AuthenticationNavigationMiddleware:
    """
    Middleware to handle authentication-aware navigation
    Prevents logged-in users from accessing auth pages
    """

    def __init__(self, get_response):
        self.get_response = get_response

        # Pages that authenticated users shouldn't access
        self.auth_pages = [
            "/login/",
            "/register/",
            "/forgot-password/",
            "/reset-password/",
        ]

        # Pages that unauthenticated users should be redirected from
        self.protected_pages = [
            "/cv-templates/",
            "/cv-builder/",
            "/cv-preview/",
            "/cv-download/",
        ]

    def __call__(self, request):
        # Check if user is authenticated
        is_authenticated = request.user.is_authenticated

        # Get current path
        current_path = request.path

        # Check if this is a browser back button request to auth pages
        is_back_request = (
            request.META.get("HTTP_REFERER")
            and any(
                auth_page in request.META.get("HTTP_REFERER", "")
                for auth_page in self.auth_pages
            )
            and current_path in self.auth_pages
        )

        # If user is authenticated and trying to access auth pages
        if is_authenticated and current_path in self.auth_pages:
            # Always redirect authenticated users away from auth pages
            # Check if user came from a protected page (likely back button)
            referrer = request.META.get("HTTP_REFERER", "")
            if any(
                protected_page in referrer for protected_page in self.protected_pages
            ):
                return redirect("cv_templates")
            # Otherwise, redirect to home page
            return redirect("home")

        # If user is not authenticated and trying to access protected pages
        if not is_authenticated and current_path in self.protected_pages:
            # Redirect to login page
            return redirect("login")

        response = self.get_response(request)

        # Add navigation headers to prevent back button issues
        if response.status_code == 200:
            response["Cache-Control"] = "no-cache, no-store, must-revalidate"
            response["Pragma"] = "no-cache"
            response["Expires"] = "0"

            # Add custom header to indicate authentication state
            response["X-Auth-Status"] = (
                "authenticated" if is_authenticated else "anonymous"
            )

        return response
