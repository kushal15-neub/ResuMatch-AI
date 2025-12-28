"""
Example URL patterns for CV functionality
Add these to your main urls.py file
"""
from django.urls import path
from . import views

urlpatterns = [
    # Existing URLs...
    
    # CV-related URLs
    path('cv-templates/', views.cv_templates, name='cv_templates'),
    path('cv-builder/<int:template_id>/', views.cv_builder, name='cv_builder'),
    path('cv-preview/<int:template_id>/', views.cv_preview, name='cv_preview'),
    path('cv-download-pdf/', views.cv_download_pdf, name='cv_download_pdf'),
]

