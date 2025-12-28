from django.contrib import admin
from django.contrib.auth.models import User
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.html import format_html
from django.urls import reverse
from django.utils import timezone
from .models import Profile, PasswordResetToken, CVTemplate, UserCV
import csv
from django.http import HttpResponse


# Inline Profile in User Admin
class ProfileInline(admin.StackedInline):
    model = Profile
    can_delete = False
    verbose_name_plural = "Profile Information"
    fields = ("phone", "job_title", "experience")


# Enhanced User Admin
class CustomUserAdmin(BaseUserAdmin):
    inlines = (ProfileInline,)
    list_display  = (
        "email",
        "full_name",
        "job_title_display",
        "is_staff",
        "is_active",
        "date_joined",
    )
    list_filter = ("is_staff", "is_active", "date_joined", "profile__experience")
    search_fields = (
        "email",
        "first_name",
        "last_name",
        "profile__phone",
        "profile__job_title",
    )
    ordering = ("-date_joined",)
    list_per_page = 25

    def full_name(self, obj):
        return (
            f"{obj.first_name} {obj.last_name}"
            if obj.first_name or obj.last_name
            else obj.username
        )

    full_name.short_description = "Full Name"

    def job_title_display(self, obj):
        try:
            return obj.profile.job_title or "-"
        except:
            return "-"

    job_title_display.short_description = "Job Title"

    actions = ["activate_users", "deactivate_users", "export_to_csv"]

    def activate_users(self, request, queryset):
        updated = queryset.update(is_active=True)
        self.message_user(request, f"{updated} user(s) activated successfully.")

    activate_users.short_description = "Activate selected users"

    def deactivate_users(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(request, f"{updated} user(s) deactivated successfully.")

    deactivate_users.short_description = "Deactivate selected users"

    def export_to_csv(self, request, queryset):
        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = 'attachment; filename="users_export.csv"'
        writer = csv.writer(response)
        writer.writerow(
            [
                "Email",
                "First Name",
                "Last Name",
                "Job Title",
                "Phone",
                "Experience",
                "Date Joined",
                "Active",
            ]
        )

        for user in queryset:
            try:
                profile = user.profile
                writer.writerow(
                    [
                        user.email,
                        user.first_name,
                        user.last_name,
                        profile.job_title,
                        profile.phone,
                        profile.experience,
                        user.date_joined.strftime("%Y-%m-%d"),
                        "Yes" if user.is_active else "No",
                    ]
                )
            except:
                writer.writerow(
                    [
                        user.email,
                        user.first_name,
                        user.last_name,
                        "",
                        "",
                        "",
                        user.date_joined.strftime("%Y-%m-%d"),
                        "Yes" if user.is_active else "No",
                    ]
                )

        return response

    export_to_csv.short_description = "Export selected to CSV"


# Unregister default User admin and register custom one
admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ("user_email", "user_name", "phone", "job_title", "experience")
    list_filter = ("experience", "job_title")
    search_fields = ("user__username", "user__email", "phone", "job_title")
    list_per_page = 25

    def user_email(self, obj):
        return obj.user.email

    user_email.short_description = "Email"
    user_email.admin_order_field = "user__email"

    def user_name(self, obj):
        return (
            f"{obj.user.first_name} {obj.user.last_name}"
            if obj.user.first_name
            else obj.user.username
        )

    user_name.short_description = "Name"


@admin.register(PasswordResetToken)
class PasswordResetTokenAdmin(admin.ModelAdmin):
    list_display = (
        "user_email",
        "token_preview",
        "created_at",
        "expires_at",
        "status_badge",
        "used",
    )
    list_filter = ("used", "created_at", "expires_at")
    search_fields = ("user__email", "token")
    readonly_fields = ("token", "created_at", "expires_at")
    list_per_page = 25
    date_hierarchy = "created_at"

    def user_email(self, obj):
        return obj.user.email

    user_email.short_description = "User Email"
    user_email.admin_order_field = "user__email"

    def token_preview(self, obj):
        return f"{obj.token[:20]}..." if len(obj.token) > 20 else obj.token

    token_preview.short_description = "Token"

    def status_badge(self, obj):
        if obj.used:
            return format_html('<span style="color: #999;">Used</span>')
        elif timezone.now() > obj.expires_at:
            return format_html('<span style="color: #dc3545;">Expired</span>')
        else:
            return format_html('<span style="color: #28a745;">Valid</span>')

    status_badge.short_description = "Status"

    actions = ["delete_expired_tokens", "delete_used_tokens"]

    def delete_expired_tokens(self, request, queryset):
        expired = queryset.filter(expires_at__lt=timezone.now())
        count = expired.count()
        expired.delete()
        self.message_user(request, f"{count} expired token(s) deleted.")

    delete_expired_tokens.short_description = "Delete expired tokens"

    def delete_used_tokens(self, request, queryset):
        used = queryset.filter(used=True)
        count = used.count()
        used.delete()
        self.message_user(request, f"{count} used token(s) deleted.")

    delete_used_tokens.short_description = "Delete used tokens"


@admin.register(CVTemplate)
class CVTemplateAdmin(admin.ModelAdmin):
    list_display = ("name", "status_badge", "usage_count", "created_at")
    list_filter = ("is_active", "created_at")
    search_fields = ("name", "description")
    list_per_page = 25
    date_hierarchy = "created_at"
    fieldsets = (
        ("Basic Information", {"fields": ("name", "description", "is_active")}),
        (
            "Template Content",
            {"fields": ("html_template", "css_styles"), "classes": ("collapse",)},
        ),
    )

    def status_badge(self, obj):
        if obj.is_active:
            return format_html(
                '<span style="color: #28a745; font-weight: bold;">● Active</span>'
            )
        return format_html('<span style="color: #dc3545;">○ Inactive</span>')

    status_badge.short_description = "Status"
    status_badge.admin_order_field = "is_active"

    def usage_count(self, obj):
        count = obj.usercv_set.count()
        return format_html('<span style="font-weight: bold;">{}</span>', count)

    usage_count.short_description = "CVs Created"

    actions = ["activate_templates", "deactivate_templates"]

    def activate_templates(self, request, queryset):
        updated = queryset.update(is_active=True)
        self.message_user(request, f"{updated} template(s) activated successfully.")

    activate_templates.short_description = "Activate selected templates"

    def deactivate_templates(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(request, f"{updated} template(s) deactivated successfully.")

    deactivate_templates.short_description = "Deactivate selected templates"


@admin.register(UserCV)
class UserCVAdmin(admin.ModelAdmin):
    list_display = (
        "user_email",
        "user_name",
        "template_name",
        "created_at",
        "updated_at",
        "view_cv_link",
    )
    list_filter = ("template", "created_at", "updated_at")
    search_fields = ("user__username", "user__email", "template__name")
    readonly_fields = (
        "created_at",
        "updated_at",
        "formatted_personal_info",
        "formatted_experience",
        "formatted_education",
        "formatted_skills",
    )
    list_per_page = 25
    date_hierarchy = "created_at"

    fieldsets = (
        (
            "CV Information",
            {"fields": ("user", "template", "created_at", "updated_at")},
        ),
        (
            "Personal Information",
            {"fields": ("formatted_personal_info",), "classes": ("collapse",)},
        ),
        ("Experience", {"fields": ("formatted_experience",), "classes": ("collapse",)}),
        ("Education", {"fields": ("formatted_education",), "classes": ("collapse",)}),
        ("Skills", {"fields": ("formatted_skills",), "classes": ("collapse",)}),
    )

    def user_email(self, obj):
        return obj.user.email

    user_email.short_description = "User Email"
    user_email.admin_order_field = "user__email"

    def user_name(self, obj):
        return (
            f"{obj.user.first_name} {obj.user.last_name}"
            if obj.user.first_name
            else obj.user.username
        )

    user_name.short_description = "User Name"

    def template_name(self, obj):
        return obj.template.name

    template_name.short_description = "Template"
    template_name.admin_order_field = "template__name"

    def view_cv_link(self, obj):
        return format_html(
            '<a href="#" style="color: #6366f1; font-weight: bold;">View CV</a>'
        )

    view_cv_link.short_description = "Actions"

    def formatted_personal_info(self, obj):
        if obj.personal_info:
            html = '<div style="line-height: 1.8;">'
            for key, value in obj.personal_info.items():
                html += f'<strong>{key.replace("_", " ").title()}:</strong> {value}<br>'
            html += "</div>"
            return format_html(html)
        return "-"

    formatted_personal_info.short_description = "Personal Information"

    def formatted_experience(self, obj):
        if obj.experience:
            return format_html(
                '<pre style="white-space: pre-wrap;">{}</pre>', str(obj.experience)
            )
        return "-"

    formatted_experience.short_description = "Experience Details"

    def formatted_education(self, obj):
        if obj.education:
            return format_html(
                '<pre style="white-space: pre-wrap;">{}</pre>', str(obj.education)
            )
        return "-"

    formatted_education.short_description = "Education Details"

    def formatted_skills(self, obj):
        if obj.skills:
            skills_list = obj.skills if isinstance(obj.skills, list) else []
            return format_html("<div>{}</div>", ", ".join(skills_list))
        return "-"

    formatted_skills.short_description = "Skills"

    actions = ["export_cvs_to_csv"]

    def export_cvs_to_csv(self, request, queryset):
        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = 'attachment; filename="cvs_export.csv"'
        writer = csv.writer(response)
        writer.writerow(
            ["User Email", "User Name", "Template", "Created At", "Updated At"]
        )

        for cv in queryset:
            writer.writerow(
                [
                    cv.user.email,
                    f"{cv.user.first_name} {cv.user.last_name}",
                    cv.template.name,
                    cv.created_at.strftime("%Y-%m-%d %H:%M"),
                    cv.updated_at.strftime("%Y-%m-%d %H:%M"),
                ]
            )

        return response

    export_cvs_to_csv.short_description = "Export selected CVs to CSV"


# Customize admin site headers
admin.site.site_header = "ResuMatch AI Administration"
admin.site.site_title = "ResuMatch AI Admin"
admin.site.index_title = "Welcome to ResuMatch AI Admin Panel"
