import base64

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.mail import send_mail
from django.conf import settings
from django.utils.crypto import get_random_string
from django.utils import timezone
from datetime import timedelta
from django.http import HttpResponse
from django.template.loader import render_to_string
from django.urls import reverse
from django.views.decorators.cache import never_cache
from django.views.decorators.vary import vary_on_headers
from .models import PasswordResetToken, UserCV, CVTemplate
from jobs.models import JobApplication
from .email_utils import send_cv_saved_email, send_job_application_email
import re
from . import views
from pdf_generator import cv_pdf_response
import json


def validate_person_name(name: str) -> bool:
    """Allow letters, spaces, apostrophes, periods, and hyphens. No digits."""
    if not name:
        return False
    return re.fullmatch(r"[A-Za-z][A-Za-z\s.'-]{0,98}", name.strip()) is not None


def validate_email_domain(email):
    """
    Validate email domain and check for invalid domains like @example.com
    """
    if not email:
        return False, "Email address is required."

    # Basic email format validation
    email_pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    if not re.match(email_pattern, email):
        return False, "Please enter a valid email address."

    # Extract domain from email
    domain = email.split("@")[1].lower()

    # Check for invalid domains
    invalid_domains = [
        "example.com",
        "test.com",
        "demo.com",
        "sample.com",
        "temp.com",
        "ss.com",
    ]

    # Check for suspiciously short domains (less than 4 characters)
    if len(domain) < 4:
        return False, "Please enter a valid email address with a proper domain."

    # Check for domains that are too short or suspicious
    if len(domain.split(".")[0]) < 2:
        return False, "Please enter a valid email address with a proper domain."

    # Check for invalid domains
    if domain in invalid_domains:
        return False, "Invalid credentials. Please use a valid email address."

    # Additional validation for common email providers and business domains
    # This helps catch obvious fake domains
    if domain.count(".") > 2:
        return False, "Please enter a valid email address with a proper domain."

    return True, ""


def validate_password_strength(password):
    """
    Validate password strength - more user-friendly version
    """
    if len(password) < 8:
        return False, "Password must be at least 8 characters long."

    # Check for at least one uppercase and one lowercase letter
    if not re.search(r"[A-Z]", password):
        return False, "Password must contain at least one uppercase letter."

    if not re.search(r"[a-z]", password):
        return False, "Password must contain at least one lowercase letter."

    # Check for at least one number
    if not re.search(r"\d", password):
        return False, "Password must contain at least one number."

    # Special characters are optional but recommended
    # Only show warning, don't block submission
    if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        return (
            True,
            "Password is good, but consider adding special characters for extra security.",
        )

    return True, "Strong password!"


@never_cache
def home(request):
    response = render(request, "index.html")
    response["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response["Pragma"] = "no-cache"
    response["Expires"] = "0"
    return response


def login_view(request):
    # Redirect authenticated users to home page
    if request.user.is_authenticated:
        return redirect("home")

    if request.method == "POST":
        email = request.POST.get("email")
        password = request.POST.get("password")

        print(f"Login attempt for email: {email}")  # Debug log

        # Validate email domain
        is_valid_email, email_error = validate_email_domain(email)
        if not is_valid_email:
            messages.error(request, email_error)
            return render(request, "login.html")

        # Validate password length (minimum 6 for login)
        if len(password) < 6:
            messages.error(request, "Password must be at least 6 characters long.")
            return render(request, "login.html")

        # Try to authenticate with email as username first
        user = authenticate(request, username=email, password=password)

        # If that fails, try to find user by email and authenticate with username
        if user is None:
            try:
                # Handle potential duplicate users by getting the first one
                user_objects = User.objects.filter(email=email)
                if user_objects.exists():
                    # Get the most recent user (last created)
                    user_obj = user_objects.order_by("-date_joined").first()
                    print(f"User found by email: {user_obj.username}")  # Debug log
                    user = authenticate(
                        request, username=user_obj.username, password=password
                    )
                    print(f"Authentication with username result: {user}")  # Debug log
                else:
                    print(f"No user found with email: {email}")  # Debug log
                    user = None
            except Exception as e:
                print(f"Error finding user by email: {str(e)}")  # Debug log
                user = None

        if user is not None:
            print(f"Login successful for user: {user.email}")  # Debug log
            print(f"User password hash: {user.password[:20]}...")  # Debug log
            login(request, user)
            messages.success(request, f"Welcome back, {user.first_name}!")
            return redirect("home")
        else:
            print(f"Login failed for email: {email}")  # Debug log
            messages.error(request, "Invalid email or password.")

    return render(request, "login.html")


def register(request):
    # Redirect authenticated users to home page
    if request.user.is_authenticated:
        return redirect("home")

    if request.method == "POST":
        first_name = request.POST.get("firstName")
        last_name = request.POST.get("lastName")
        email = request.POST.get("email")
        phone = request.POST.get("phone")
        job_title = request.POST.get("jobTitle")
        experience = request.POST.get("experience")
        password = request.POST.get("password")
        confirm_password = request.POST.get("confirmPassword")
        terms = request.POST.get("terms")

        # Required field validation
        if not first_name or not first_name.strip():
            messages.error(request, "First Name is required.")
            return render(request, "register.html")
        if not validate_person_name(first_name):
            messages.error(
                request, "First Name must contain only letters (no numbers)."
            )
            return render(request, "register.html")

        if not last_name or not last_name.strip():
            messages.error(request, "Last Name is required.")
            return render(request, "register.html")
        if not validate_person_name(last_name):
            messages.error(request, "Last Name must contain only letters (no numbers).")
            return render(request, "register.html")

        if not email or not email.strip():
            messages.error(request, "Email Address is required.")
            return render(request, "register.html")

        if not job_title or not job_title.strip():
            messages.error(request, "Job Title is required.")
            return render(request, "register.html")

        if not experience or not experience.strip():
            messages.error(request, "Experience Level is required.")
            return render(request, "register.html")

        # Email domain validation
        is_valid_email, email_error = validate_email_domain(email)
        if not is_valid_email:
            messages.error(request, email_error)
            return render(request, "register.html")

        # Password validation
        is_valid_password, password_error = validate_password_strength(password)
        if not is_valid_password:
            messages.error(request, password_error)
            return render(request, "register.html")

        # Password confirmation validation
        if password != confirm_password:
            messages.error(request, "Passwords do not match.")
            return render(request, "register.html")

        # Terms agreement validation
        if not terms:
            messages.error(request, "Please agree to the Terms of Service.")
            return render(request, "register.html")

        # Check if user already exists
        if User.objects.filter(email=email).exists():
            messages.error(request, "A user with this email already exists.")
            return render(request, "register.html")

        # Create user
        try:
            user = User.objects.create_user(
                username=email,  # Use email as username
                email=email,
                password=password,
                first_name=first_name,
                last_name=last_name,
            )

            # Update profile with additional fields

            user.profile.phone = phone
            user.profile.job_title = job_title
            user.profile.experience = experience
            user.profile.save()

            # Log the user in (authenticate first to select the correct backend)
            authenticated_user = authenticate(
                request, username=email, password=password
            )
            if authenticated_user is not None:
                login(request, authenticated_user)
            else:
                # Fallback: explicitly specify the ModelBackend if authenticate didn't return a user
                login(
                    request, user, backend="django.contrib.auth.backends.ModelBackend"
                )
            messages.success(request, f"Welcome to ResuMatch AI, {first_name}!")
            return redirect("home")

        except Exception as e:
            messages.error(request, f"Error creating account: {str(e)}")

    return render(request, "register.html")


def logout_view(request):
    logout(request)
    messages.info(request, "You have been logged out successfully.")
    return redirect("login")


def forgot_password(request):
    if request.method == "POST":
        email = request.POST.get("email")
        print(f"Forgot password request for email: {email}")  # Debug log

        # Validate email
        is_valid_email, email_error = validate_email_domain(email)
        if not is_valid_email:
            print(f"Email validation failed: {email_error}")  # Debug log
            messages.error(request, email_error)
            return render(request, "forgot-password.html")

        # Check if user exists
        try:
            user = User.objects.get(email=email)
            print(f"User found: {user.username}")  # Debug log

            # Generate reset token
            token = get_random_string(64)
            print(f"Generated token: {token[:20]}...")  # Debug log

            # Save token to database
            PasswordResetToken.objects.create(user=user, token=token)
            print("Token saved to database")  # Debug log

            # Build absolute reset URL and send email
            reset_url = request.build_absolute_uri(
                reverse("reset_password", args=[token])
            )
            print(f"Reset URL: {reset_url}")  # Debug log

            try:
                send_mail(
                    subject="Reset your ResuMatch AI password",
                    message=(
                        f"You requested a password reset for your ResuMatch AI account.\n\n"
                        f"Click the link below to set a new password (valid for 1 hour):\n{reset_url}\n\n"
                        "If you did not request this, you can safely ignore this email."
                    ),
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[email],
                    fail_silently=False,
                )
                print("Email sent successfully")  # Debug log
                messages.success(
                    request,
                    f"Password reset link sent to {email}. Please check your email and click the reset link.",
                )

                # Always stay on the page with success message for better UX
                return render(request, "forgot-password.html")

            except Exception as email_error:
                print(f"Email sending failed: {str(email_error)}")  # Debug log
                # Delete the token if email failed
                PasswordResetToken.objects.filter(token=token).delete()
                messages.error(
                    request,
                    f"Failed to send email: {str(email_error)}. Please try again or contact support.",
                )
                return render(request, "forgot-password.html")

        except User.DoesNotExist:
            print(f"No user found with email: {email}")  # Debug log
            # Don't reveal if email exists or not (security)
            messages.info(
                request,
                "If an account with this email exists, a reset link has been sent. Please check your email.",
            )
            return render(request, "forgot-password.html")

    return render(request, "forgot-password.html")


def reset_password(request, token):
    print(f"Reset password request for token: {token[:20]}...")  # Debug log
    try:
        reset_token = PasswordResetToken.objects.get(token=token)
        print(f"Token found for user: {reset_token.user.email}")  # Debug log

        if not reset_token.is_valid():
            print("Token is invalid or expired")  # Debug log
            messages.error(request, "This reset link has expired or is invalid.")
            return redirect("login")

        if request.method == "POST":
            password = request.POST.get("password")
            confirm_password = request.POST.get("confirmPassword")
            print(f"Password reset attempt - length: {len(password)}")  # Debug log

            # Check password confirmation first
            if password != confirm_password:
                print("Passwords do not match")  # Debug log
                messages.error(request, "Passwords do not match.")
                return render(request, "reset-password.html")

            # Validate password strength
            is_valid_password, password_message = validate_password_strength(password)
            if not is_valid_password:
                print(f"Password validation failed: {password_message}")  # Debug log
                messages.error(request, password_message)
                return render(request, "reset-password.html")

            # If password is valid but has a warning message, show it as info
            if password_message and password_message != "Strong password!":
                print(f"Password warning: {password_message}")  # Debug log
                messages.info(request, password_message)

            # Update user password
            user = reset_token.user
            old_password_hash = user.password  # Store old hash for comparison
            user.set_password(password)
            user.save()
            print(f"Password updated for user: {user.email}")  # Debug log
            print(f"Old password hash: {old_password_hash[:20]}...")  # Debug log
            print(f"New password hash: {user.password[:20]}...")  # Debug log

            # Force user to login again by clearing any existing sessions
            # Note: Django doesn't have session_set on User objects
            # The logout() call below will handle session clearing

            # Mark token as used
            reset_token.used = True
            reset_token.save()
            print("Token marked as used")  # Debug log

            # Clear any existing sessions for this user
            from django.contrib.auth import logout

            logout(request)

            messages.success(
                request,
                f"Password updated successfully for {user.email}! Please login with your new password.",
            )
            return redirect("login")

        return render(request, "reset-password.html")

    except PasswordResetToken.DoesNotExist:
        print(f"Token not found: {token[:20]}...")  # Debug log
        messages.error(request, "Invalid reset link.")
        return redirect("login")

    # CV functionality will be implemented here


# CV Template Functions
@login_required
@never_cache
def cv_templates(request):
    """Display available CV templates"""
    # Get user's profile data
    user = request.user
    profile = user.profile

    # Create a default template with user's data
    default_template = {
        "id": 1,
        "name": "Professional Template",
        "description": f"Customized template for {user.get_full_name() or user.username}",
        "user_data": {
            "full_name": f"{user.first_name} {user.last_name}".strip() or user.username,
            "email": user.email,
            "phone": profile.phone or "",
            "job_title": profile.job_title or "",
            "experience": profile.experience or "",
        },
    }

    templates = [default_template]

    response = render(
        request,
        "cv-templates.html",
        {"templates": templates, "user_data": default_template["user_data"]},
    )
    response["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response["Pragma"] = "no-cache"
    response["Expires"] = "0"
    return response


@login_required
def cv_builder(request, template_id):
    """CV builder form"""
    # Get user's profile data
    user = request.user
    profile = user.profile

    # Create a template with user's data
    template = {
        "id": template_id,
        "name": "Professional Template",
        "user_data": {
            "full_name": f"{user.first_name} {user.last_name}".strip() or user.username,
            "email": user.email,
            "phone": profile.phone or "",
            "job_title": profile.job_title or "",
            "experience": profile.experience or "",
        },
    }

    # Get existing CV data from session or create empty
    existing_cv_data = request.session.get("cv_data", {})
    if "personal_info" not in existing_cv_data:
        existing_cv_data["personal_info"] = {}
    if "template_choice" not in existing_cv_data:
        existing_cv_data["template_choice"] = "classic"
    for key in ["experience", "education", "skills", "projects"]:
        if key not in existing_cv_data:
            existing_cv_data[key] = []

    if request.method == "POST":
        # Handle CV data submission
        template_choice = request.POST.get(
            "template_choice",
            existing_cv_data.get("template_choice", "classic"),
        )
        previous_photo = existing_cv_data.get("profile_photo")

        cv_data = {
            "personal_info": {
                "full_name": request.POST.get("full_name"),
                "email": request.POST.get("email"),
                "phone": request.POST.get("phone"),
                "location": request.POST.get("location"),
                "summary": request.POST.get("summary"),
            },
            "template_choice": template_choice,
            "profile_photo": previous_photo,
            "experience": [],
            "education": [],
            "skills": [],
            "projects": [],
        }

        # Handle optional profile photo
        photo_file = request.FILES.get("profile_photo")
        if photo_file:
            try:
                mime_type = photo_file.content_type or "image/png"
                encoded = base64.b64encode(photo_file.read()).decode("utf-8")
                cv_data["profile_photo"] = f"data:{mime_type};base64,{encoded}"
            except Exception:
                cv_data["profile_photo"] = previous_photo

        # Handle multiple experience entries
        titles = request.POST.getlist("experience_title")
        descriptions = request.POST.getlist("experience_description")
        companies = request.POST.getlist("experience_company")
        locations = request.POST.getlist("experience_location")
        starts = request.POST.getlist("experience_start")
        ends = request.POST.getlist("experience_end")

        for i in range(len(titles)):
            title = titles[i].strip() if i < len(titles) else ""
            company = companies[i].strip() if i < len(companies) else ""
            description = descriptions[i].strip() if i < len(descriptions) else ""
            location = locations[i].strip() if i < len(locations) else ""
            start = starts[i].strip() if i < len(starts) else ""
            end = ends[i].strip() if i < len(ends) else ""

            # Clean template syntax from data (prevent template injection)
            template_pattern = r"\{[%#]\s*.*?\s*[%#]\}"
            start = re.sub(template_pattern, "", start)
            end = re.sub(template_pattern, "", end)
            title = re.sub(template_pattern, "", title)
            company = re.sub(template_pattern, "", company)
            description = re.sub(template_pattern, "", description)
            location = re.sub(template_pattern, "", location)

            if any([title, company, description, location, start, end]):
                cv_data["experience"].append(
                    {
                        "title": title,
                        "company": company,
                        "location": location,
                        "start": start,
                        "end": end,
                        "description": description,
                    }
                )

        # Handle multiple education entries
        degrees = request.POST.getlist("education_degree")
        institutions = request.POST.getlist("education_institution")
        locations = request.POST.getlist("education_location")
        starts = request.POST.getlist("education_start")
        ends = request.POST.getlist("education_end")
        details = request.POST.getlist("education_details")

        for i in range(len(degrees)):
            degree = degrees[i].strip() if i < len(degrees) else ""
            institution = institutions[i].strip() if i < len(institutions) else ""
            location = locations[i].strip() if i < len(locations) else ""
            start = starts[i].strip() if i < len(starts) else ""
            end = ends[i].strip() if i < len(ends) else ""
            detail = details[i].strip() if i < len(details) else ""

            # Clean template syntax from data (prevent template injection)
            template_pattern = r"\{[%#]\s*.*?\s*[%#]\}"
            start = re.sub(template_pattern, "", start)
            end = re.sub(template_pattern, "", end)
            degree = re.sub(template_pattern, "", degree)
            institution = re.sub(template_pattern, "", institution)
            location = re.sub(template_pattern, "", location)
            detail = re.sub(template_pattern, "", detail)

            if any([degree, institution, location, start, end, detail]):
                cv_data["education"].append(
                    {
                        "degree": degree,
                        "institution": institution,
                        "location": location,
                        "start": start,
                        "end": end,
                        "details": detail,
                    }
                )

        # Handle skills
        skill_entries = request.POST.getlist("skills")
        parsed_skills = []
        for entry in skill_entries:
            parsed_skills.extend(
                [skill.strip() for skill in entry.split(",") if skill.strip()]
            )
        cv_data["skills"] = parsed_skills

        # Handle projects
        project_names = request.POST.getlist("project_name")
        project_links = request.POST.getlist("project_link")
        project_descriptions = request.POST.getlist("project_description")

        for i in range(len(project_names)):
            if project_names[i].strip():
                cv_data["projects"].append(
                    {
                        "name": project_names[i],
                        "link": project_links[i] if i < len(project_links) else "",
                        "description": (
                            project_descriptions[i]
                            if i < len(project_descriptions)
                            else ""
                        ),
                    }
                )

        # Store in session for preview
        request.session["cv_data"] = cv_data
        request.session["template_id"] = template_id

        # Save to database
        cv_name = request.POST.get("cv_name", "My CV")
        save_to_db = request.POST.get("save_to_db", False)

        if save_to_db:
            try:
                # Get or create template
                template_obj, _ = CVTemplate.objects.get_or_create(
                    id=template_id,
                    defaults={
                        "name": "Professional Template",
                        "description": "Default template",
                    },
                )

                # Get latest version for this CV name
                latest_cv = (
                    UserCV.objects.filter(user=request.user, name=cv_name)
                    .order_by("-version")
                    .first()
                )

                new_version = (latest_cv.version + 1) if latest_cv else 1

                # Create new CV version
                user_cv = UserCV.objects.create(
                    user=request.user,
                    template=template_obj,
                    name=cv_name,
                    version=new_version,
                    personal_info=cv_data.get("personal_info", {}),
                    experience=cv_data.get("experience", []),
                    education=cv_data.get("education", []),
                    skills=cv_data.get("skills", []),
                    projects=cv_data.get("projects", []),
                    profile_photo=cv_data.get("profile_photo", ""),
                    template_choice=cv_data.get("template_choice", "classic"),
                )

                # Send email notification
                send_cv_saved_email(request.user, cv_name)

                messages.success(
                    request,
                    f"CV '{cv_name}' saved successfully! (Version {new_version})",
                )
                request.session["saved_cv_id"] = user_cv.id
            except Exception as e:
                messages.warning(
                    request, f"CV preview saved, but database save failed: {str(e)}"
                )

        return redirect("cv_preview")

    context = {
        "template": template,
        "cv_data": existing_cv_data,
        "user_data": template["user_data"],
    }
    return render(request, "cv-builder.html", context)


@login_required
def cv_preview(request):
    """Preview CV before download"""
    cv_data = request.session.get("cv_data", {})
    template_id = request.session.get("template_id")

    if not cv_data:
        messages.error(request, "No CV data found. Please build your CV first.")
        return redirect("cv_templates")

    # Ensure template_choice is set
    if "template_choice" not in cv_data:
        cv_data["template_choice"] = "classic"

    # Ensure all required keys exist
    if "personal_info" not in cv_data:
        cv_data["personal_info"] = {}
    for key in ["experience", "education", "skills", "projects"]:
        if key not in cv_data:
            cv_data[key] = []

    context = {"cv_data": cv_data, "template_id": template_id}
    return render(request, "cv-preview.html", context)


@login_required
def cv_download_pdf(request):
    """Generate and download PDF"""
    cv_data = request.session.get("cv_data", {})
    if not cv_data:
        messages.error(request, "No CV data found. Please build your CV first.")
        return redirect("cv_templates")

    # Ensure all required keys exist
    if "personal_info" not in cv_data:
        cv_data["personal_info"] = {}
    for key in ["experience", "education", "skills", "projects"]:
        if key not in cv_data:
            cv_data[key] = []
    if "template_choice" not in cv_data:
        cv_data["template_choice"] = "classic"

    filename = f"CV_{cv_data.get('personal_info', {}).get('full_name', 'User').replace(' ', '_')}.pdf"
    template_choice = cv_data.get("template_choice", "classic")
    pdf_template = (
        "cv_pdf_modern.html" if template_choice == "modern" else "cv_pdf_classic.html"
    )

    try:
        response = cv_pdf_response(
            cv_data, filename=filename, template_name=pdf_template
        )

        # If response is an error, show message to user
        if response.status_code == 500:
            try:
                error_content = response.content.decode("utf-8")
                # Extract just the error message part
                if "Error generating PDF:" in error_content:
                    error_msg = error_content.split("Error generating PDF:")[-1].strip()
                    messages.error(request, error_msg)
                else:
                    messages.error(
                        request,
                        "Failed to generate PDF. Please check server console for details.",
                    )
            except:
                messages.error(
                    request,
                    "Failed to generate PDF. Please check server console for details.",
                )
            return redirect("cv_preview")

        return response
    except Exception as e:
        messages.error(request, f"Error generating PDF: {str(e)}")
        return redirect("cv_preview")


@login_required
def cv_dashboard(request):
    """User dashboard to manage all saved CVs"""
    user_cvs = UserCV.objects.filter(user=request.user, is_active=True).order_by(
        "-updated_at"
    )

    # Group CVs by name to show versions
    cv_groups = {}
    for cv in user_cvs:
        if cv.name not in cv_groups:
            cv_groups[cv.name] = []
        cv_groups[cv.name].append(cv)

    context = {
        "cv_groups": cv_groups,
        "total_cvs": user_cvs.count(),
    }
    return render(request, "cv-dashboard.html", context)


@login_required
def cv_edit(request, cv_id):
    """Edit an existing CV"""
    user_cv = get_object_or_404(UserCV, id=cv_id, user=request.user)

    if request.method == "POST":
        # Update CV data
        cv_data = {
            "personal_info": {
                "full_name": request.POST.get("full_name"),
                "email": request.POST.get("email"),
                "phone": request.POST.get("phone"),
                "location": request.POST.get("location"),
                "summary": request.POST.get("summary"),
            },
            "template_choice": request.POST.get("template_choice", "classic"),
            "profile_photo": user_cv.profile_photo,
            "experience": [],
            "education": [],
            "skills": [],
            "projects": [],
        }

        # Handle profile photo update
        photo_file = request.FILES.get("profile_photo")
        if photo_file:
            try:
                mime_type = photo_file.content_type or "image/png"
                encoded = base64.b64encode(photo_file.read()).decode("utf-8")
                cv_data["profile_photo"] = f"data:{mime_type};base64,{encoded}"
            except Exception:
                pass

        # Process experience (same as cv_builder)
        titles = request.POST.getlist("experience_title")
        companies = request.POST.getlist("experience_company")
        locations = request.POST.getlist("experience_location")
        starts = request.POST.getlist("experience_start")
        ends = request.POST.getlist("experience_end")
        descriptions = request.POST.getlist("experience_description")

        for i in range(len(titles)):
            title = titles[i].strip() if i < len(titles) else ""
            company = companies[i].strip() if i < len(companies) else ""
            location = locations[i].strip() if i < len(locations) else ""
            start = starts[i].strip() if i < len(starts) else ""
            end = ends[i].strip() if i < len(ends) else ""
            description = descriptions[i].strip() if i < len(descriptions) else ""

            # Clean template syntax from data (prevent template injection)
            template_pattern = r"\{[%#]\s*.*?\s*[%#]\}"
            start = re.sub(template_pattern, "", start)
            end = re.sub(template_pattern, "", end)
            title = re.sub(template_pattern, "", title)
            company = re.sub(template_pattern, "", company)
            description = re.sub(template_pattern, "", description)
            location = re.sub(template_pattern, "", location)

            if any([title, company, location, start, end, description]):
                cv_data["experience"].append(
                    {
                        "title": title,
                        "company": company,
                        "location": location,
                        "start": start,
                        "end": end,
                        "description": description,
                    }
                )

        # Process education
        degrees = request.POST.getlist("education_degree")
        institutions = request.POST.getlist("education_institution")
        edu_locations = request.POST.getlist("education_location")
        edu_starts = request.POST.getlist("education_start")
        edu_ends = request.POST.getlist("education_end")
        edu_details = request.POST.getlist("education_details")

        for i in range(len(degrees)):
            degree = degrees[i].strip() if i < len(degrees) else ""
            institution = institutions[i].strip() if i < len(institutions) else ""
            location = edu_locations[i].strip() if i < len(edu_locations) else ""
            start = edu_starts[i].strip() if i < len(edu_starts) else ""
            end = edu_ends[i].strip() if i < len(edu_ends) else ""
            detail = edu_details[i].strip() if i < len(edu_details) else ""

            # Clean template syntax from data (prevent template injection)
            template_pattern = r"\{[%#]\s*.*?\s*[%#]\}"
            start = re.sub(template_pattern, "", start)
            end = re.sub(template_pattern, "", end)
            degree = re.sub(template_pattern, "", degree)
            institution = re.sub(template_pattern, "", institution)
            location = re.sub(template_pattern, "", location)
            detail = re.sub(template_pattern, "", detail)

            if any([degree, institution, location, start, end, detail]):
                cv_data["education"].append(
                    {
                        "degree": degree,
                        "institution": institution,
                        "location": location,
                        "start": start,
                        "end": end,
                        "details": detail,
                    }
                )

        # Process skills
        skill_entries = request.POST.getlist("skills")
        parsed_skills = []
        for entry in skill_entries:
            parsed_skills.extend(
                [skill.strip() for skill in entry.split(",") if skill.strip()]
            )
        cv_data["skills"] = parsed_skills

        # Process projects
        project_names = request.POST.getlist("project_name")
        project_links = request.POST.getlist("project_link")
        project_descriptions = request.POST.getlist("project_description")

        for i in range(len(project_names)):
            if project_names[i].strip():
                cv_data["projects"].append(
                    {
                        "name": project_names[i],
                        "link": project_links[i] if i < len(project_links) else "",
                        "description": (
                            project_descriptions[i]
                            if i < len(project_descriptions)
                            else ""
                        ),
                    }
                )

        # Update the CV
        user_cv.personal_info = cv_data["personal_info"]
        user_cv.experience = cv_data["experience"]
        user_cv.education = cv_data["education"]
        user_cv.skills = cv_data["skills"]
        user_cv.projects = cv_data["projects"]
        user_cv.profile_photo = cv_data["profile_photo"]
        user_cv.template_choice = cv_data["template_choice"]
        user_cv.save()

        # Update session for preview
        request.session["cv_data"] = cv_data
        request.session["template_id"] = user_cv.template.id if user_cv.template else 1

        messages.success(request, "CV updated successfully!")
        return redirect("cv_preview")

    # Load CV data into form
    cv_data = {
        "personal_info": user_cv.personal_info or {},
        "experience": user_cv.experience or [],
        "education": user_cv.education or [],
        "skills": user_cv.skills or [],
        "projects": user_cv.projects or [],
        "profile_photo": user_cv.profile_photo or "",
        "template_choice": user_cv.template_choice or "classic",
    }

    template = {
        "id": user_cv.template.id if user_cv.template else 1,
        "name": user_cv.template.name if user_cv.template else "Professional Template",
        "user_data": {
            "full_name": cv_data["personal_info"].get("full_name", ""),
            "email": cv_data["personal_info"].get("email", ""),
            "phone": cv_data["personal_info"].get("phone", ""),
        },
    }

    context = {
        "template": template,
        "cv_data": cv_data,
        "user_cv": user_cv,
        "editing": True,
    }
    return render(request, "cv-builder.html", context)


@login_required
def cv_delete(request, cv_id):
    """Delete a CV (soft delete)"""
    user_cv = get_object_or_404(UserCV, id=cv_id, user=request.user)

    if request.method == "POST":
        user_cv.is_active = False
        user_cv.save()
        messages.success(request, f"CV '{user_cv.name}' deleted successfully!")
        return redirect("cv_dashboard")

    context = {"cv": user_cv}
    return render(request, "cv-delete-confirm.html", context)


@login_required
def cv_load(request, cv_id):
    """Load a saved CV into session for preview/edit"""
    user_cv = get_object_or_404(UserCV, id=cv_id, user=request.user)

    cv_data = {
        "personal_info": user_cv.personal_info or {},
        "experience": user_cv.experience or [],
        "education": user_cv.education or [],
        "skills": user_cv.skills or [],
        "projects": user_cv.projects or [],
        "profile_photo": user_cv.profile_photo or "",
        "template_choice": user_cv.template_choice or "classic",
    }

    request.session["cv_data"] = cv_data
    request.session["template_id"] = user_cv.template.id if user_cv.template else 1
    request.session["saved_cv_id"] = user_cv.id

    messages.success(request, f"CV '{user_cv.name}' loaded successfully!")
    return redirect("cv_preview")
