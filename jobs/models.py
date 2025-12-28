from django.db import models
from django.contrib.auth.models import User


class Job(models.Model):
    """
    Model to store job postings from the Kaggle dataset.
    This will be used to match user skills with job requirements.
    """

    title = models.CharField(max_length=500)
    company = models.CharField(max_length=300)
    location = models.CharField(max_length=200, blank=True)
    description = models.TextField()
    required_skills = models.JSONField(default=list, blank=True)  # Store list of skills
    experience_level = models.CharField(max_length=50, blank=True
    )  # e.g., Entry, Mid, Senior
    job_type = models.CharField(max_length=50, blank=True)  # e.g., Full-time, Part-time
    salary_min = models.IntegerField(null=True, blank=True)
    salary_max = models.IntegerField(null=True, blank=True)
    salary_currency = models.CharField(max_length=10, default="USD")
    posted_date = models.DateField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-posted_date", "-created_at"]
        indexes = [
            models.Index(fields=["title"]),
            models.Index(fields=["company"]),
            models.Index(fields=["is_active"]),
        ]

    def __str__(self):
        return f"{self.title} at {self.company}"

    @property
    def required_skills_list(self):
        """Return skills as a list"""
        if isinstance(self.required_skills, list):
            return self.required_skills
        return []

    @property
    def salary_range(self):
        """Return formatted salary range"""
        if self.salary_min and self.salary_max:
            return f"{self.salary_currency} {self.salary_min:,} - {self.salary_max:,}"
        elif self.salary_min:
            return f"{self.salary_currency} {self.salary_min:,}+"
        return "Not specified"


class JobMatchScore(models.Model):
    """
    Model to store recommendation scores for users and jobs.
    This helps track which jobs were recommended to which users.
    """

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    job = models.ForeignKey(Job, on_delete=models.CASCADE)
    match_score = models.FloatField(help_text="Similarity score from 0 to 100")
    matched_skills = models.JSONField(default=list)  # List of matched skills
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ["user", "job"]
        ordering = ["-match_score", "-created_at"]

    def __str__(self):
        return f"User: {self.user.username} - Job: {self.job.title} - Score: {self.match_score:.2f}%"


class JobApplication(models.Model):
    """Model to store job applications"""

    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("reviewed", "Reviewed"),
        ("interview", "Interview Scheduled"),
        ("rejected", "Rejected"),
        ("accepted", "Accepted"),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    job = models.ForeignKey(Job, on_delete=models.CASCADE)
    cv = models.ForeignKey(
        "accounts.UserCV", on_delete=models.SET_NULL, null=True, blank=True
    )
    cover_letter = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")
    applied_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    notes = models.TextField(blank=True)

    class Meta:
        unique_together = ["user", "job"]
        ordering = ["-applied_at"]

    def __str__(self):
        return f"{self.user.username} applied for {self.job.title} - {self.status}"
