from django.contrib import admin
from .models import Job, JobMatchScore, JobApplication


@admin.register(Job)
class JobAdmin(admin.ModelAdmin):
    list_display = [
        "title",
        "company",
        "location",
        "experience_level",
        "is_active",
        "created_at",
    ]
    list_filter = ["is_active", "experience_level", "job_type", "created_at"]
    search_fields = ["title", "company", "description", "location"]
    readonly_fields = ["created_at", "updated_at"]
    list_editable = ["is_active"]

    fieldsets = (
        (
            "Job Information",
            {"fields": ("title", "company", "location", "description")},
        ),
        (
            "Requirements",
            {"fields": ("required_skills", "experience_level", "job_type")},
        ),
        ("Salary", {"fields": ("salary_min", "salary_max", "salary_currency")}),
        (
            "Metadata",
            {"fields": ("posted_date", "is_active", "created_at", "updated_at")},
        ),
    )


@admin.register(JobMatchScore)
class JobMatchScoreAdmin(admin.ModelAdmin):
    list_display = ["user", "job", "match_score", "created_at"]
    list_filter = ["created_at", "match_score"]
    search_fields = ["user__username", "user__email", "job__title", "job__company"]
    readonly_fields = ["created_at"]
    ordering = ["-match_score", "-created_at"]


@admin.register(JobApplication)
class JobApplicationAdmin(admin.ModelAdmin):
    list_display = ["user", "job", "status", "applied_at", "cv"]
    list_filter = ["status", "applied_at"]
    search_fields = ["user__username", "user__email", "job__title", "job__company"]
    readonly_fields = ["applied_at", "updated_at"]
    ordering = ["-applied_at"]
