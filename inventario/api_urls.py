from django.urls import include, path
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import (
    TokenBlacklistView,
    TokenObtainPairView,
    TokenRefreshView,
)

from .api_views import HerramientaViewSet, InsumoViewSet, SolicitudViewSet

app_name = 'inventario_api'

router = DefaultRouter()
router.register('insumos', InsumoViewSet, basename='insumo')
router.register('herramientas', HerramientaViewSet, basename='herramienta')
router.register('solicitudes', SolicitudViewSet, basename='solicitud')

urlpatterns = [
    path('auth/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('auth/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('auth/token/blacklist/', TokenBlacklistView.as_view(), name='token_blacklist'),
    path('', include(router.urls)),
]
