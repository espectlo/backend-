from django.contrib import admin
from django.contrib.admin.models import LogEntry
from django.contrib.auth.models import Permission, User
from django.contrib.auth.models import Group
from django.core.management import call_command
from django.test import Client, TestCase
from django.urls import reverse
from io import StringIO

from .models import Herramienta, Insumo, RegistroAuditoria, Solicitud


class InventarioCrudTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='operador', password='Clave-segura-123!')
        auxiliary_group, _ = Group.objects.get_or_create(name='Auxiliares')
        self.user.groups.add(auxiliary_group)
        self.insumo = Insumo.objects.create(nombre='Guantes', cantidad=12, stock_minimo=4)
        self.herramienta = Herramienta.objects.create(nombre='Taladro', tratamiento='Revisión')
        self.user.user_permissions.add(Permission.objects.get(codename='add_solicitud'))
        self.client.force_login(self.user)

    def grant_permissions(self, *codenames):
        permissions = Permission.objects.filter(codename__in=codenames)
        self.user.user_permissions.add(*permissions)

    def test_insumo_crud_persists_and_requires_permissions(self):
        create_url = reverse('insumo_nuevo')
        self.assertEqual(self.client.get(create_url).status_code, 403)

        self.grant_permissions('add_insumo', 'change_insumo', 'delete_insumo')
        response = self.client.post(create_url, {
            'nombre': 'Mascarillas', 'cantidad': 25, 'stock_minimo': 8,
        })
        self.assertRedirects(response, reverse('vista_insumos'))
        created = Insumo.objects.get(nombre='Mascarillas')
        create_event = RegistroAuditoria.objects.get(accion='crear', objeto='Mascarillas')
        self.assertEqual(create_event.detalle['despues']['cantidad'], 25)

        response = self.client.post(reverse('insumo_editar', args=[created.pk]), {
            'nombre': 'Mascarillas', 'cantidad': 18, 'stock_minimo': 8,
        })
        self.assertRedirects(response, reverse('vista_insumos'))
        created.refresh_from_db()
        self.assertEqual(created.cantidad, 18)
        update_event = RegistroAuditoria.objects.get(accion='actualizar', objeto='Mascarillas')
        self.assertEqual(update_event.detalle['cambios']['cantidad'], {'antes': 25, 'despues': 18})

        response = self.client.post(reverse('insumo_eliminar', args=[created.pk]))
        self.assertRedirects(response, reverse('vista_insumos'))
        self.assertFalse(Insumo.objects.filter(pk=created.pk).exists())
        self.assertTrue(RegistroAuditoria.objects.filter(
            accion='eliminar', objeto='Mascarillas', usuario=self.user
        ).exists())

    def test_invalid_insumo_data_is_not_saved(self):
        self.grant_permissions('add_insumo')
        response = self.client.post(reverse('insumo_nuevo'), {
            'nombre': 'Cantidad inválida', 'cantidad': -1, 'stock_minimo': 0,
        })
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Insumo.objects.filter(nombre='Cantidad inválida').exists())

    def test_herramienta_crud_persists(self):
        self.grant_permissions('add_herramienta', 'change_herramienta', 'delete_herramienta')
        response = self.client.post(reverse('herramienta_nueva'), {
            'nombre': 'Sierra', 'estado': Herramienta.Estado.DISPONIBLE,
            'tratamiento': 'Mantención preventiva',
        })
        self.assertRedirects(response, reverse('vista_herramientas'))
        sierra = Herramienta.objects.get(nombre='Sierra')

        response = self.client.post(reverse('herramienta_editar', args=[sierra.pk]), {
            'nombre': 'Sierra', 'estado': Herramienta.Estado.MANTENIMIENTO,
            'tratamiento': 'Cambio de disco',
        })
        self.assertRedirects(response, reverse('vista_herramientas'))
        sierra.refresh_from_db()
        self.assertEqual(sierra.estado, Herramienta.Estado.MANTENIMIENTO)

        response = self.client.post(reverse('herramienta_eliminar', args=[sierra.pk]))
        self.assertRedirects(response, reverse('vista_herramientas'))
        self.assertFalse(Herramienta.objects.filter(pk=sierra.pk).exists())

    def test_request_uses_database_insumo_and_authenticated_user(self):
        response = self.client.post(reverse('solicitar_insumo'), {
            'insumo_id': self.insumo.pk,
            'insumo_nombre': 'Nombre manipulado',
            'cantidad': '3',
        })
        self.assertRedirects(response, reverse('inventario'))
        solicitud = Solicitud.objects.get()
        self.assertEqual(solicitud.usuario, self.user)
        self.assertEqual(solicitud.insumo_nombre, self.insumo.nombre)
        self.assertTrue(RegistroAuditoria.objects.filter(
            usuario=self.user, accion='crear_solicitud'
        ).exists())

        self.client.post(reverse('solicitar_insumo'), {
            'insumo_id': self.insumo.pk, 'cantidad': '-5',
        })
        self.assertEqual(Solicitud.objects.count(), 1)

    def test_admin_cannot_see_or_submit_stock_order_form(self):
        admin_user = User.objects.create_superuser(
            username='admin_pedidos', email='orders@example.test', password='Clave-segura-123!'
        )
        self.client.force_login(admin_user)
        response = self.client.get(reverse('vista_insumos'))
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, 'Solicitar Más')
        self.assertNotContains(response, 'class="solicitud-form"')

        response = self.client.post(reverse('solicitar_insumo'), {
            'insumo_id': self.insumo.pk, 'cantidad': '2',
        })
        self.assertEqual(response.status_code, 403)
        self.assertFalse(Solicitud.objects.exists())

    def test_dashboard_expanded_cards_are_auxiliary_only(self):
        response = self.client.get(reverse('dashboard'))
        self.assertContains(response, 'class="dashboard-auxiliar"')

        admin_user = User.objects.create_superuser(
            username='admin_dashboard',
            email='dashboard@example.test',
            password='Clave-segura-123!',
        )
        self.client.force_login(admin_user)
        response = self.client.get(reverse('dashboard'))
        self.assertNotContains(response, 'class="dashboard-auxiliar"')

    def test_logout_requires_post_and_inventory_views_render_from_database(self):
        response = self.client.get(reverse('logout'))
        self.assertEqual(response.status_code, 405)
        self.assertTrue(response.wsgi_request.user.is_authenticated)

        self.assertEqual(self.client.get(reverse('vista_insumos')).status_code, 200)
        self.assertEqual(self.client.get(reverse('vista_herramientas')).status_code, 200)
        self.assertEqual(self.client.get(reverse('logout')).status_code, 405)
        response = self.client.post(reverse('logout'))
        self.assertRedirects(response, reverse('login'))
        self.assertEqual(self.client.get(reverse('vista_insumos')).status_code, 302)

    def test_admin_registers_every_collection(self):
        self.assertIn(Insumo, admin.site._registry)
        self.assertIn(Herramienta, admin.site._registry)
        self.assertIn(Solicitud, admin.site._registry)
        self.assertIn(RegistroAuditoria, admin.site._registry)
        self.assertIn(LogEntry, admin.site._registry)

    def test_logout_post_requires_a_csrf_token(self):
        csrf_client = Client(enforce_csrf_checks=True)
        csrf_client.force_login(self.user)
        response = csrf_client.post(reverse('logout'))
        self.assertEqual(response.status_code, 403)

        csrf_client.get(reverse('vista_insumos'))
        csrf_token = csrf_client.cookies['csrftoken'].value
        response = csrf_client.post(
            reverse('logout'), {'csrfmiddlewaretoken': csrf_token}
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('login'))

    def test_json_import_is_repeatable(self):
        call_command('importar_json', stdout=StringIO())
        expected = (Insumo.objects.count(), Herramienta.objects.count(), Solicitud.objects.count())
        call_command('importar_json', stdout=StringIO())
        self.assertEqual(expected, (10, 10, 4))
        self.assertEqual(
            expected,
            (Insumo.objects.count(), Herramienta.objects.count(), Solicitud.objects.count()),
        )
        legacy_request = Solicitud.objects.get(id_origen=1)
        self.assertEqual(legacy_request.usuario_nombre, 'mario')
        self.assertEqual(legacy_request.insumo_nombre, 'Desinfectante')
        self.assertEqual(str(legacy_request.fecha), '2026-09-12')
        self.assertEqual(self.client.get(reverse('ver_solicitudes')).status_code, 403)
        self.grant_permissions('view_solicitud')
        response = self.client.get(reverse('ver_solicitudes'))
        self.assertContains(response, 'mario')
        self.assertContains(response, 'Desinfectante')
        self.assertContains(response, f'#{legacy_request.pk}')

    def test_role_setup_assigns_auxiliaries_and_creates_admin(self):
        call_command('configurar_roles', stdout=StringIO())
        self.user.refresh_from_db()
        admin_user = User.objects.get(username='admin')
        self.assertTrue(self.user.groups.filter(name='Auxiliares').exists())
        self.assertTrue(self.user.has_perm('inventario.view_insumo'))
        self.assertTrue(self.user.has_perm('inventario.view_herramienta'))
        self.assertTrue(self.user.has_perm('inventario.add_solicitud'))
        self.assertFalse(self.user.has_perm('inventario.view_solicitud'))
        self.assertTrue(admin_user.is_superuser)
        self.assertTrue(admin_user.has_usable_password() is False)
        self.assertEqual(
            RegistroAuditoria.objects.filter(id_origen__isnull=False).count(), 12
        )

    def test_auxiliary_cannot_view_global_requests_but_admin_can(self):
        self.assertEqual(self.client.get(reverse('ver_solicitudes')).status_code, 403)
        admin_user = User.objects.create_superuser(
            username='admin_temporal', email='admin@example.test', password='Clave-segura-123!'
        )
        self.client.force_login(admin_user)
        response = self.client.get(reverse('ver_solicitudes'))
        self.assertEqual(response.status_code, 200)
        self.assertTrue(RegistroAuditoria.objects.filter(
            usuario=admin_user, accion='consultar_solicitudes'
        ).exists())

    def test_admin_must_justify_accepting_or_rejecting_a_request(self):
        admin_user = User.objects.create_superuser(
            username='admin_solicitudes',
            email='requests@example.test',
            password='Clave-segura-123!',
        )
        solicitud = Solicitud.objects.create(
            usuario=self.user,
            usuario_nombre=self.user.username,
            insumo=self.insumo,
            insumo_nombre=self.insumo.nombre,
            cantidad_solicitada=5,
        )
        self.client.force_login(admin_user)
        change_url = reverse('admin:inventario_solicitud_change', args=[solicitud.pk])

        response = self.client.post(change_url, {
            'estado': Solicitud.Estado.APROBADA,
            'justificacion': '',
            '_save': 'Guardar',
        })
        self.assertEqual(response.status_code, 200)
        solicitud.refresh_from_db()
        self.assertEqual(solicitud.estado, Solicitud.Estado.PENDIENTE)

        response = self.client.post(change_url, {
            'estado': Solicitud.Estado.APROBADA,
            'justificacion': 'Compra necesaria para reponer el stock mínimo.',
            '_save': 'Guardar',
        })
        self.assertEqual(response.status_code, 302)
        solicitud.refresh_from_db()
        self.assertEqual(solicitud.estado, Solicitud.Estado.APROBADA)
        self.assertEqual(
            solicitud.justificacion,
            'Compra necesaria para reponer el stock mínimo.',
        )
        event = RegistroAuditoria.objects.get(
            usuario=admin_user, accion='actualizar', objeto=str(solicitud)
        )
        self.assertEqual(
            event.detalle['despues']['justificacion'],
            'Compra necesaria para reponer el stock mínimo.',
        )

        rechazo = Solicitud.objects.create(
            usuario=self.user,
            usuario_nombre=self.user.username,
            insumo=self.insumo,
            insumo_nombre=self.insumo.nombre,
            cantidad_solicitada=2,
        )
        reject_url = reverse('admin:inventario_solicitud_change', args=[rechazo.pk])
        response = self.client.post(reject_url, {
            'estado': Solicitud.Estado.RECHAZADA,
            'justificacion': '',
            '_save': 'Guardar',
        })
        self.assertEqual(response.status_code, 200)
        rechazo.refresh_from_db()
        self.assertEqual(rechazo.estado, Solicitud.Estado.PENDIENTE)

        response = self.client.post(reject_url, {
            'estado': Solicitud.Estado.RECHAZADA,
            'justificacion': 'La cantidad solicitada supera el presupuesto disponible.',
            '_save': 'Guardar',
        })
        self.assertEqual(response.status_code, 302)
        rechazo.refresh_from_db()
        self.assertEqual(rechazo.estado, Solicitud.Estado.RECHAZADA)
        self.assertEqual(
            rechazo.justificacion,
            'La cantidad solicitada supera el presupuesto disponible.',
        )

    def test_request_list_buttons_resolve_pending_requests_as_admin_only(self):
        solicitud = Solicitud.objects.create(
            usuario=self.user,
            usuario_nombre=self.user.username,
            insumo=self.insumo,
            insumo_nombre=self.insumo.nombre,
            cantidad_solicitada=4,
        )
        decision_url = reverse('resolver_solicitud', args=[solicitud.pk])
        self.assertEqual(self.client.get(reverse('ver_solicitudes')).status_code, 403)
        self.assertEqual(self.client.post(decision_url, {
            'estado': Solicitud.Estado.APROBADA,
            'justificacion': 'Aprobación no autorizada',
        }).status_code, 403)

        admin_user = User.objects.create_superuser(
            username='admin_decisiones',
            email='decisions@example.test',
            password='Clave-segura-123!',
        )
        self.client.force_login(admin_user)
        response = self.client.get(reverse('ver_solicitudes'))
        self.assertContains(response, 'Aceptar')
        self.assertContains(response, 'Rechazar')
        self.assertContains(response, 'Motivo obligatorio')

        response = self.client.post(decision_url, {
            'estado': Solicitud.Estado.RECHAZADA,
            'justificacion': 'El proveedor no dispone de unidades.',
        })
        self.assertRedirects(response, reverse('ver_solicitudes'))
        solicitud.refresh_from_db()
        self.assertEqual(solicitud.estado, Solicitud.Estado.RECHAZADA)
        self.assertEqual(solicitud.justificacion, 'El proveedor no dispone de unidades.')
        event = RegistroAuditoria.objects.get(
            usuario=admin_user, accion='rechazar_solicitud'
        )
        self.assertEqual(event.detalle['antes']['estado'], Solicitud.Estado.PENDIENTE)
        self.assertEqual(event.detalle['despues']['estado'], Solicitud.Estado.RECHAZADA)

    def test_stock_consultation_is_audited(self):
        response = self.client.get(reverse('vista_insumos'))
        self.assertEqual(response.status_code, 200)
        event = RegistroAuditoria.objects.get(accion='consultar_stock_insumos')
        self.assertEqual(event.usuario, self.user)

    def test_successful_login_is_audited(self):
        self.client.post(reverse('logout'))
        response = self.client.post(reverse('login'), {
            'username': 'operador', 'password': 'Clave-segura-123!',
        })
        self.assertRedirects(response, reverse('dashboard'))
        self.assertTrue(RegistroAuditoria.objects.filter(
            usuario=self.user, accion='inicio_sesion'
        ).exists())

    def test_failed_login_is_audited_without_recording_password(self):
        self.client.post(reverse('logout'))
        response = self.client.post(reverse('login'), {
            'username': 'operador', 'password': 'incorrecta',
        })
        self.assertEqual(response.status_code, 200)
        event = RegistroAuditoria.objects.get(accion='fallo_inicio_sesion')
        self.assertEqual(event.detalle, {'usuario_intentado': 'operador'})
        self.assertEqual(event.objeto, 'operador')
        self.assertNotIn('password', event.detalle)

        admin_user = User.objects.create_superuser(
            username='admin_auditoria', email='audit@example.test', password='Clave-segura-123!'
        )
        self.client.force_login(admin_user)
        response = self.client.get(reverse('admin:inventario_registroauditoria_changelist'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'operador')
        self.assertContains(response, 'fallo_inicio_sesion')