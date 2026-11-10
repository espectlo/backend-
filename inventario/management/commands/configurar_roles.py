import json
from datetime import datetime

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group, Permission
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone

from inventario.models import RegistroAuditoria


class Command(BaseCommand):
    help = 'Configura el grupo Auxiliares, crea la cuenta admin y migra el historial de accesos.'

    def add_arguments(self, parser):
        parser.add_argument('--admin-username', default='admin')

    def handle(self, *args, **options):
        user_model = get_user_model()
        auxiliary_group, _ = Group.objects.get_or_create(name='Auxiliares')
        permissions = Permission.objects.filter(
            content_type__app_label='inventario',
            codename__in=('view_insumo', 'view_herramienta', 'add_solicitud'),
        )
        auxiliary_group.permissions.set(permissions)

        for user in user_model.objects.exclude(username=options['admin_username']):
            user.groups.add(auxiliary_group)

        admin_user, created = user_model.objects.get_or_create(
            username=options['admin_username'],
            defaults={'is_staff': True, 'is_superuser': True},
        )
        if created:
            admin_user.set_unusable_password()
        admin_user.is_staff = True
        admin_user.is_superuser = True
        admin_user.is_active = True
        admin_user.save()

        self._import_login_history()
        self.stdout.write(self.style.SUCCESS(
            f"Auxiliares configurado; {user_model.objects.exclude(username=options['admin_username']).count()} "
            f"usuarios asignados. Admin '{admin_user.username}' "
            f"{'creado' if created else 'actualizado'} sin contraseña configurada."
        ))
        self.stdout.write(
            f"Define su contraseña con: python manage.py changepassword {admin_user.username}"
        )

    def _import_login_history(self):
        history_path = settings.BASE_DIR / 'accesos.json'
        if not history_path.exists():
            return
        try:
            with history_path.open(encoding='utf-8') as history_file:
                records = json.load(history_file)
        except (OSError, json.JSONDecodeError) as error:
            raise CommandError(f'No se pudo importar accesos.json: {error}') from error

        user_model = get_user_model()
        for index, record in enumerate(records, start=1):
            occurred = datetime.strptime(
                f"{record['fecha']} {record['hora']}", '%Y-%m-%d %H:%M:%S'
            )
            username = record.get('usuario', 'Desconocido')
            RegistroAuditoria.objects.update_or_create(
                id_origen=index,
                defaults={
                    'usuario': user_model.objects.filter(username=username).first(),
                    'usuario_nombre': username,
                    'accion': 'inicio_sesion',
                    'objeto': 'Sesión',
                    'detalle': {'origen': 'accesos.json'},
                    'ocurrido': timezone.make_aware(occurred, timezone.get_current_timezone()),
                },
            )