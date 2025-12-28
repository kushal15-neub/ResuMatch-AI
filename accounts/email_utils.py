"""
Email notification utilities for ResuMatch AI
"""

from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string
from django.utils.html import strip_tags


def send_cv_saved_email(user, cv_name):
    """Send email when CV is saved"""
    subject = f"CV '{cv_name}' Saved Successfully - ResuMatch AI"
    html_message = render_to_string(
        "emails/cv_saved.html",
        {
            "user": user,
            "cv_name": cv_name,
            "site_url": getattr(settings, "SITE_URL", "http://127.0.0.1:8000"),
        },
    )
    plain_message = strip_tags(html_message)

    try:
        send_mail(
            subject,
            plain_message,
            settings.DEFAULT_FROM_EMAIL,
            [user.email],
            html_message=html_message,
            fail_silently=False,
        )
        return True
    except Exception as e:
        print(f"Error sending email: {e}")
        return False


def send_job_application_email(user, job, application):
    """Send email when job application is submitted"""
    subject = f"Application Submitted: {job.title} at {job.company}"
    html_message = render_to_string(
        "emails/job_application.html",
        {
            "user": user,
            "job": job,
            "application": application,
            "site_url": getattr(settings, "SITE_URL", "http://127.0.0.1:8000"),
        },
    )
    plain_message = strip_tags(html_message)

    try:
        send_mail(
            subject,
            plain_message,
            settings.DEFAULT_FROM_EMAIL,
            [user.email],
            html_message=html_message,
            fail_silently=False,
        )
        return True
    except Exception as e:
        print(f"Error sending email: {e}")
        return False


def send_job_recommendations_email(user, job_count):
    """Send email with job recommendations"""
    subject = f"New Job Recommendations Available - {job_count} Jobs Found"
    html_message = render_to_string(
        "emails/job_recommendations.html",
        {
            "user": user,
            "job_count": job_count,
            "site_url": getattr(settings, "SITE_URL", "http://127.0.0.1:8000"),
        },
    )
    plain_message = strip_tags(html_message)

    try:
        send_mail(
            subject,
            plain_message,
            settings.DEFAULT_FROM_EMAIL,
            [user.email],
            html_message=html_message,
            fail_silently=False,
        )
        return True
    except Exception as e:
        print(f"Error sending email: {e}")
        return False
