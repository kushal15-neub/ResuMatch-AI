from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.models import User
from django.utils.decorators import method_decorator
from django.views.generic import TemplateView
from django.db.models import Count, Q
from django.utils import timezone
from datetime import timedelta
from .models import Profile, CVTemplate, UserCV, PasswordResetToken
import json


@method_decorator(staff_member_required, name="dispatch")
class AdminDashboardView(TemplateView):
    template_name = "admin/index.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Get current date and calculate date ranges
        now = timezone.now()
        today = now.date()
        week_ago = today - timedelta(days=7)
        month_ago = today - timedelta(days=30)

        # Statistics
        total_users = User.objects.count()
        new_users_today = User.objects.filter(date_joined__date=today).count()

        total_cvs = UserCV.objects.count()
        new_cvs_today = UserCV.objects.filter(created_at__date=today).count()

        total_templates = CVTemplate.objects.count()
        active_templates = CVTemplate.objects.filter(is_active=True).count()

        active_tokens = PasswordResetToken.objects.filter(
            used=False, expires_at__gt=now
        ).count()
        expired_tokens = PasswordResetToken.objects.filter(expires_at__lt=now).count()

        # User registration chart data (last 7 days)
        user_chart_data = []
        user_chart_labels = []

        for i in range(7):
            date = today - timedelta(days=i)
            count = User.objects.filter(date_joined__date=date).count()
            user_chart_data.insert(0, count)
            user_chart_labels.insert(0, date.strftime("%m/%d"))

        # Template usage chart data
        template_usage = (
            UserCV.objects.values("template__name")
            .annotate(count=Count("id"))
            .order_by("-count")[:5]
        )

        template_chart_labels = [
            item["template__name"] or "Unknown" for item in template_usage
        ]
        template_chart_data = [item["count"] for item in template_usage]

        # Recent activities
        recent_activities = []

        # Recent user registrations
        recent_users = User.objects.order_by("-date_joined")[:5]
        for user in recent_users:
            recent_activities.append(
                {
                    "icon": "👤",
                    "description": f"New user registered: {user.get_full_name() or user.username}",
                    "timestamp": user.date_joined.strftime("%Y-%m-%d %H:%M"),
                }
            )

        # Recent CV creations
        recent_cvs = UserCV.objects.order_by("-created_at")[:3]
        for cv in recent_cvs:
            recent_activities.append(
                {
                    "icon": "📄",
                    "description": f"CV created by {cv.user.get_full_name() or cv.user.username}",
                    "timestamp": cv.created_at.strftime("%Y-%m-%d %H:%M"),
                }
            )

        # Recent password reset requests
        recent_tokens = PasswordResetToken.objects.order_by("-created_at")[:2]
        for token in recent_tokens:
            recent_activities.append(
                {
                    "icon": "🔑",
                    "description": f"Password reset requested by {token.user.email}",
                    "timestamp": token.created_at.strftime("%Y-%m-%d %H:%M"),
                }
            )

        # Sort activities by timestamp (most recent first)
        recent_activities.sort(key=lambda x: x["timestamp"], reverse=True)
        recent_activities = recent_activities[:10]  # Limit to 10 most recent

        context.update(
            {
                "total_users": total_users,
                "new_users_today": new_users_today,
                "total_cvs": total_cvs,
                "new_cvs_today": new_cvs_today,
                "total_templates": total_templates,
                "active_templates": active_templates,
                "active_tokens": active_tokens,
                "expired_tokens": expired_tokens,
                "user_chart_data": json.dumps(user_chart_data),
                "user_chart_labels": json.dumps(user_chart_labels),
                "template_chart_data": json.dumps(template_chart_data),
                "template_chart_labels": json.dumps(template_chart_labels),
                "recent_activities": recent_activities,
            }
        )

        return context
