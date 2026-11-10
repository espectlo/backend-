import json
from datetime import datetime

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from inventario.models import Herramienta, Insumo, Solicitud


class Command(BaseCommand):
    help = 'Importa o actualiza insumos y herramientas desde inventario.json.'

    @transaction.atomic
    def handle(self, *args, **options):
        try:
            with open(settings.JSON_FILE, encoding='utf-8') as archivo:
                datos = json.load(archivo)
            insumos = datos['insumos']
            herramientas = datos['herramientas']
            solicitudes_path = settings.BASE_DIR / 'solicitudes.json'
            if solicitudes_path.exists():
                with open(solicitudes_path, encoding='utf-8') as archivo:
                    solicitudes = json.load(archivo)
            else:
                solicitudes = []
        except (OSError, json.JSONDecodeError, KeyError, TypeError) as error:
            raise CommandError(f'No se pudieron leer los datos JSON: {error}') from error

        for dato in insumos:
            Insumo.objects.update_or_create(
                nombre=dato['nombre'],
                defaults={
                    'cantidad': dato['cantidad'],
                    'stock_minimo': dato['stock_minimo'],
                },
            )

        for dato in herramientas:
            Herramienta.objects.update_or_create(
                nombre=dato['nombre'],
                defaults={
                    'estado': dato['estado'],
                    'tratamiento': dato.get('tratamiento', dato.get('descripcion', '')),
                },
            )

        user_model = get_user_model()
        for dato in solicitudes:
            created = datetime.strptime(
                f"{dato['fecha']} {dato['hora']}", '%Y-%m-%d %H:%M:%S'
            )
            usuario = user_model.objects.filter(username=dato.get('usuario', '')).first()
            insumo_nombre = dato['insumo']
            insumo = Insumo.objects.filter(nombre=insumo_nombre).first()
            Solicitud.objects.update_or_create(
                id_origen=dato['id_solicitud'],
                defaults={
                    'usuario': usuario,
                    'usuario_nombre': dato.get('usuario', ''),
                    'insumo': insumo,
                    'insumo_nombre': insumo_nombre,
                    'cantidad_solicitada': dato['cantidad_solicitada'],
                    'estado': dato.get('estado', Solicitud.Estado.PENDIENTE),
                    'creado': timezone.make_aware(created, timezone.get_current_timezone()),
                },
            )

        self.stdout.write(self.style.SUCCESS(
            f"Importados {len(insumos)} insumos, {len(herramientas)} herramientas "
            f"y {len(solicitudes)} solicitudes."
        ))