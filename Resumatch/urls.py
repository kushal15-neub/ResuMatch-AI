"""
URL configuration for Resumatch project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from django.urls import path, include
from django.views.generic import RedirectView


urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("accounts.urls")),
    path("auth/", include("social_django.urls", namespace="social")),
    path("jobs/", include("jobs.urls")),
    path("favicon.ico", RedirectView.as_view(url="/static/favicon.ico")),
]

# Serve static files during development
if settings.DEBUG:
    # Use Django's staticfiles finders and also expose STATICFILES_DIRS directly
    urlpatterns += staticfiles_urlpatterns()
    try:
        # Serve from the first STATICFILES_DIRS entry to ensure files in backend/static are found
        urlpatterns += static(
            settings.STATIC_URL, document_root=settings.STATICFILES_DIRS[0]
        )
    except Exception:
        # Fallback to STATIC_ROOT if STATICFILES_DIRS isn't configured
        urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
