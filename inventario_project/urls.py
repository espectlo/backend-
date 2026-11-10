"""
URL configuration for inventario_project project.
"""
from django.urls import path, include
from django.contrib import admin

urlpatterns = [
    path('admin/', admin.site.urls),
    path(
        'api/v1/',
        include(('inventario.api_urls', 'inventario_api'), namespace='v1'),
    ),
    path('', include('inventario.urls')),
]
