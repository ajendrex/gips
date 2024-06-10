from django.contrib import admin
from django_hosts import patterns, host

host_patterns = patterns('',
    host(r'admin', 'gips.admin_urls', name='admin'),  # Rutas para el subdominio de administración
    host(r'', 'gips.urls', name=''),  # Rutas para el subdominio principal
)
