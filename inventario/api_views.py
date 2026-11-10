from rest_framework import filters, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import DjangoModelPermissions
from rest_framework.response import Response

from .api_permissions import SolicitudAPIPermission
from .api_serializers import (
    HerramientaSerializer,
    InsumoSerializer,
    SolicitudDecisionSerializer,
    SolicitudSerializer,
)
from .auditoria import registrar_accion
from .models import Herramienta, Insumo, Solicitud


class AuditedModelViewSet(viewsets.ModelViewSet):
    def perform_create(self, serializer):
        instance = serializer.save()
        registrar_accion(
            self.request,
            'api_crear',
            instance,
            {
                'recurso': self.basename,
                'despues': serializer.to_representation(instance),
            },
        )

    def perform_update(self, serializer):
        previous = serializer.to_representation(serializer.instance)
        instance = serializer.save()
        registrar_accion(
            self.request,
            'api_actualizar',
            instance,
            {
                'recurso': self.basename,
                'antes': previous,
                'despues': serializer.to_representation(instance),
            },
        )

    def perform_destroy(self, instance):
        previous = self.get_serializer(instance).data
        registrar_accion(
            self.request,
            'api_eliminar',
            instance,
            {'recurso': self.basename, 'antes': previous},
        )
        instance.delete()


class InsumoViewSet(AuditedModelViewSet):
    queryset = Insumo.objects.all()
    serializer_class = InsumoSerializer
    permission_classes = (DjangoModelPermissions,)
    search_fields = ('nombre',)
    ordering_fields = ('nombre', 'cantidad', 'stock_minimo')


class HerramientaViewSet(AuditedModelViewSet):
    queryset = Herramienta.objects.all()
    serializer_class = HerramientaSerializer
    permission_classes = (DjangoModelPermissions,)
    search_fields = ('nombre', 'estado', 'tratamiento')
    ordering_fields = ('nombre', 'estado')


class SolicitudViewSet(AuditedModelViewSet):
    queryset = Solicitud.objects.select_related('usuario', 'insumo')
    serializer_class = SolicitudSerializer
    permission_classes = (SolicitudAPIPermission,)
    filter_backends = (filters.SearchFilter, filters.OrderingFilter)
    search_fields = ('insumo_nombre', 'usuario_nombre')
    ordering_fields = ('creado', 'estado')

    def get_serializer_class(self):
        if self.action in ('update', 'partial_update', 'resolver'):
            return SolicitudDecisionSerializer
        return super().get_serializer_class()

        super().perform_update(serializer)

    @action(detail=True, methods=('post',), permission_classes=(SolicitudAPIPermission,))
    def resolver(self, request, pk=None):
        solicitud = self.get_object()
        serializer = self.get_serializer(
            solicitud,
            data=request.data,
            partial=True,
        )
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return Response(serializer.data, status=status.HTTP_200_OK)
