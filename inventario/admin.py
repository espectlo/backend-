from django.contrib import admin
from django.contrib.admin.models import LogEntry
from django.core.serializers.json import DjangoJSONEncoder
import json

from .auditoria import registrar_accion
from .models import Herramienta, Insumo, RegistroAuditoria, Solicitud


class AuditedModelAdmin(admin.ModelAdmin):
    def save_model(self, request, obj, form, change):
        previous = self.model.objects.get(pk=obj.pk) if change else None
        super().save_model(request, obj, form, change)
        registrar_accion(
            request,
            'actualizar' if change else 'crear',
            obj,
            {
                'antes': _snapshot(previous) if previous else None,
                'despues': _snapshot(obj),
            },
        )

    def delete_model(self, request, obj):
        snapshot = _snapshot(obj)
        registrar_accion(request, 'eliminar', obj, {'antes': snapshot})
        super().delete_model(request, obj)

    def delete_queryset(self, request, queryset):
        for obj in queryset:
            registrar_accion(request, 'eliminar', obj, {'antes': _snapshot(obj)})
        super().delete_queryset(request, queryset)


def _snapshot(obj):
    values = {
        field.name: field.value_from_object(obj)
        for field in obj._meta.concrete_fields
        if not field.primary_key
    }
    return json.loads(json.dumps(values, cls=DjangoJSONEncoder))


@admin.register(Insumo)
class InsumoAdmin(AuditedModelAdmin):
    list_display = ('nombre', 'cantidad', 'stock_minimo', 'estado')
    list_filter = ('cantidad',)
    search_fields = ('nombre',)
    ordering = ('nombre',)


@admin.register(Herramienta)
class HerramientaAdmin(AuditedModelAdmin):
    list_display = ('nombre', 'estado', 'tratamiento')
    list_filter = ('estado',)
    search_fields = ('nombre', 'tratamiento')
    ordering = ('nombre',)


@admin.register(Solicitud)
class SolicitudAdmin(AuditedModelAdmin):
    list_display = (
        'insumo_nombre', 'cantidad_solicitada', 'usuario_nombre', 'estado',
        'justificacion_resumen', 'creado',
    )
    list_filter = ('estado', 'creado')
    search_fields = ('insumo_nombre', 'usuario_nombre')
    readonly_fields = (
        'usuario', 'usuario_nombre', 'id_origen', 'insumo', 'insumo_nombre',
        'cantidad_solicitada', 'creado',
    )
    fields = (
        'usuario', 'usuario_nombre', 'insumo', 'insumo_nombre', 'cantidad_solicitada',
        'creado', 'estado', 'justificacion',
    )
    ordering = ('-creado',)

    def has_add_permission(self, request):
        return False

    @admin.display(description='Justificación')
    def justificacion_resumen(self, obj):
        return obj.justificacion[:80] or 'Pendiente de resolución'


@admin.register(RegistroAuditoria)
class RegistroAuditoriaAdmin(admin.ModelAdmin):
    list_display = ('ocurrido', 'usuario_nombre', 'accion', 'objeto', 'direccion_ip')
    list_filter = ('accion', 'ocurrido')
    search_fields = ('usuario_nombre', 'accion', 'objeto')
    readonly_fields = (
        'usuario', 'usuario_nombre', 'id_origen', 'accion', 'objeto',
        'detalle', 'direccion_ip', 'ocurrido',
    )
    ordering = ('-ocurrido',)

    def has_add_permission(self, request):
        return False

    def has_view_permission(self, request, obj=None):
        return request.user.is_superuser

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(LogEntry)
class LogEntryAdmin(admin.ModelAdmin):
    list_display = ('action_time', 'user', 'content_type', 'object_repr', 'action_flag')
    list_filter = ('action_flag', 'content_type', 'action_time')
    search_fields = ('user__username', 'object_repr', 'change_message')
    readonly_fields = (
        'action_time', 'user', 'content_type', 'object_id', 'object_repr',
        'action_flag', 'change_message',
    )
    ordering = ('-action_time',)

    def has_add_permission(self, request):
        return False

    def has_view_permission(self, request, obj=None):
        return request.user.is_superuser

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False