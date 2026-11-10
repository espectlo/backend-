from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models
from django.utils import timezone


class Insumo(models.Model):
    nombre = models.CharField(max_length=120, unique=True)
    cantidad = models.PositiveIntegerField(validators=[MinValueValidator(0)])
    stock_minimo = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['nombre']
        verbose_name = 'insumo'
        verbose_name_plural = 'insumos'

    def __str__(self):
        return self.nombre

    @property
    def estado(self):
        if self.cantidad == 0:
            return 'Sin stock'
        if self.cantidad <= self.stock_minimo:
            return 'Stock bajo'
        return 'Disponible'


class Herramienta(models.Model):
    class Estado(models.TextChoices):
        DISPONIBLE = 'Disponible', 'Disponible'
        MANTENIMIENTO = 'En mantenimiento', 'En mantenimiento'
        DANADA = 'Dañada', 'Dañada'

    nombre = models.CharField(max_length=120, unique=True)
    estado = models.CharField(max_length=30, choices=Estado.choices, default=Estado.DISPONIBLE)
    tratamiento = models.CharField(max_length=240, blank=True)

    class Meta:
        ordering = ['nombre']
        verbose_name = 'herramienta'
        verbose_name_plural = 'herramientas'

    def __str__(self):
        return self.nombre

    @property
    def descripcion(self):
        return self.tratamiento

    @property
    def puede_usarse(self):
        return self.estado == self.Estado.DISPONIBLE


class Solicitud(models.Model):
    class Estado(models.TextChoices):
        PENDIENTE = 'Pendiente', 'Pendiente'
        APROBADA = 'Aprobado', 'Aprobado'
        RECHAZADA = 'Rechazado', 'Rechazado'

    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='solicitudes_inventario',
    )
    usuario_nombre = models.CharField(max_length=150)
    id_origen = models.PositiveIntegerField(unique=True, null=True, blank=True)
    insumo = models.ForeignKey(Insumo, on_delete=models.SET_NULL, null=True, related_name='solicitudes')
    insumo_nombre = models.CharField(max_length=120)
    cantidad_solicitada = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    creado = models.DateTimeField(default=timezone.now)
    estado = models.CharField(max_length=20, choices=Estado.choices, default=Estado.PENDIENTE)
    justificacion = models.TextField(blank=True)

    class Meta:
        ordering = ['-creado']
        verbose_name = 'solicitud'
        verbose_name_plural = 'solicitudes'

    def __str__(self):
        return f'{self.insumo_nombre}: {self.cantidad_solicitada} ({self.estado})'

    def clean(self):
        if self.estado != self.Estado.PENDIENTE and not self.justificacion.strip():
            raise ValidationError({
                'justificacion': 'Escribe el motivo para aceptar o rechazar esta solicitud.'
            })

    @property
    def fecha(self):
        return timezone.localtime(self.creado).date()

    @property
    def hora(self):
        return timezone.localtime(self.creado).strftime('%H:%M:%S')


class RegistroAuditoria(models.Model):
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='acciones_inventario',
    )
    usuario_nombre = models.CharField(max_length=150)
    id_origen = models.PositiveIntegerField(unique=True, null=True, blank=True)
    accion = models.CharField(max_length=60)
    objeto = models.CharField(max_length=120, blank=True)
    detalle = models.JSONField(default=dict, blank=True)
    direccion_ip = models.GenericIPAddressField(null=True, blank=True)
    ocurrido = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ['-ocurrido']
        verbose_name = 'registro de auditoría'
        verbose_name_plural = 'registros de auditoría'

    def __str__(self):
        return f'{self.usuario_nombre}: {self.accion} ({self.ocurrido:%Y-%m-%d %H:%M:%S})'