"""
URL configuration for gips project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.0/topics/http/urls/
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
from django.urls import path, include, re_path

from entrevistas.views import serve_protected_media, verificar
from gips.views import FrontendAppView

urlpatterns = [
    path("admin/", admin.site.urls),
    path("informes/", include("informes.urls")),
    path(r'verificar/<str:clave_acceso>', verificar, name='verificar'),
    path("api/tests/", include("tests.urls")),
    path("api/entrevistas/", include("entrevistas.urls")),
    re_path(r'^media/(?P<path>.*)$', serve_protected_media),
    re_path(r'^.*$', FrontendAppView.as_view(), name='home'),
]
