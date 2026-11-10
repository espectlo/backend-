"""
URL configuration para la app inventario.
"""
from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('inventario/', views.inventario, name='inventario'),
    path('insumos/', views.vista_insumos, name='vista_insumos'),
    path('herramientas/', views.vista_herramientas, name='vista_herramientas'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('insumos/nuevo/', views.insumo_crear, name='insumo_nuevo'),
    path('insumos/<int:pk>/editar/', views.insumo_editar, name='insumo_editar'),
    path('insumos/<int:pk>/eliminar/', views.insumo_eliminar, name='insumo_eliminar'),
    path('herramientas/nueva/', views.herramienta_crear, name='herramienta_nueva'),
    path('herramientas/<int:pk>/editar/', views.herramienta_editar, name='herramienta_editar'),
    path('herramientas/<int:pk>/eliminar/', views.herramienta_eliminar, name='herramienta_eliminar'),
    path('solicitar-insumo/', views.solicitar_insumo, name='solicitar_insumo'),
    path('solicitudes/', views.ver_solicitudes, name='ver_solicitudes'),
    path('solicitudes/<int:pk>/resolver/', views.resolver_solicitud, name='resolver_solicitud'),
]
