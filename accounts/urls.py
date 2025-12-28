from django.urls import path
from . import views
from . import admin_views

urlpatterns = [
    path("", views.home, name="home"),
    path("login/", views.login_view, name="login"),
    path("register/", views.register, name="register"),
    path("logout/", views.logout_view, name="logout"),
    path("forgot-password/", views.forgot_password, name="forgot_password"),
    path("reset-password/<str:token>/", views.reset_password, name="reset_password"),
    path("cv-templates/", views.cv_templates, name="cv_templates"),
    path("cv-builder/<int:template_id>/", views.cv_builder, name="cv_builder"),
    path("cv-preview/", views.cv_preview, name="cv_preview"),
    path("cv-download/", views.cv_download_pdf, name="cv_download_pdf"),
    path("cv-dashboard/", views.cv_dashboard, name="cv_dashboard"),
    path("cv-edit/<int:cv_id>/", views.cv_edit, name="cv_edit"),
    path("cv-delete/<int:cv_id>/", views.cv_delete, name="cv_delete"),
    path("cv-load/<int:cv_id>/", views.cv_load, name="cv_load"),
    # Admin dashboard
    path(
        "admin/dashboard/",
        admin_views.AdminDashboardView.as_view(),
        name="admin_dashboard",
    ),
]
