from django.urls import path
from . import views

urlpatterns = [
    path("recommendations/", views.job_recommendations, name="job_recommendations"),
    path("<int:job_id>/", views.job_detail, name="job_detail"),
    path("applications/", views.job_applications, name="job_applications"),
]
