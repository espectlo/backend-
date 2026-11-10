from django.contrib.auth.models import Group, Permission, User
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from .models import Herramienta, Insumo, RegistroAuditoria, Solicitud


class InventarioAPITests(APITestCase):
    def setUp(self):
        self.auxiliar = User.objects.create_user(
            username='auxiliar_api',
            password='Clave-segura-123!',
        )
        self.auxiliar.groups.add(Group.objects.create(name='Auxiliares'))
        self.auxiliar.user_permissions.add(*Permission.objects.filter(
            codename__in=('view_insumo', 'view_herramienta', 'add_solicitud'),
        ))
        self.insumo = Insumo.objects.create(
            nombre='Guantes API',
            cantidad=12,
            stock_minimo=4,
        )
        self.herramienta = Herramienta.objects.create(
            nombre='Taladro API',
            estado=Herramienta.Estado.DISPONIBLE,
            tratamiento='Revisión',
        )
        self.admin = User.objects.create_superuser(
            username='admin_api',
            email='admin-api@example.test',
            password='Clave-segura-123!',
        )
        self.token_url = reverse('v1:token_obtain_pair')
        self.insumos_url = reverse('v1:insumo-list')
        self.herramientas_url = reverse('v1:herramienta-list')
        self.solicitudes_url = reverse('v1:solicitud-list')

    def authenticate_as(self, user, password='Clave-segura-123!'):
        response = self.client.post(
            self.token_url,
            {'username': user.username, 'password': password},
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {response.data['access']}")
        return response.data

    def test_jwt_authentication_and_expiring_rotating_refresh_tokens(self):
        response = self.client.get(self.insumos_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(response.data['detail'].code, 'not_authenticated')

        tokens = self.authenticate_as(self.auxiliar)
        self.assertIn('refresh', tokens)
        listing = self.client.get(self.insumos_url)
        self.assertEqual(listing.status_code, status.HTTP_200_OK)
        self.assertEqual(listing.data['results'][0]['estado'], 'Disponible')

        refresh_url = reverse('v1:token_refresh')
        rotated = self.client.post(
            refresh_url,
            {'refresh': tokens['refresh']},
            format='json',
        )
        self.assertEqual(rotated.status_code, status.HTTP_200_OK)
        self.assertIn('refresh', rotated.data)
        reused = self.client.post(
            refresh_url,
            {'refresh': tokens['refresh']},
            format='json',
        )
        self.assertEqual(reused.status_code, status.HTTP_401_UNAUTHORIZED)

        blacklist = self.client.post(
            reverse('v1:token_blacklist'),
            {'refresh': rotated.data['refresh']},
            format='json',
        )
        self.assertEqual(blacklist.status_code, status.HTTP_200_OK)
        revoked = self.client.post(
            refresh_url,
            {'refresh': rotated.data['refresh']},
            format='json',
        )
        self.assertEqual(revoked.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_auxiliary_can_read_inventory_but_cannot_modify_it(self):
        self.authenticate_as(self.auxiliar)
        listing = self.client.get(self.herramientas_url)
        self.assertEqual(listing.status_code, status.HTTP_200_OK)
        self.assertTrue(listing.data['results'][0]['puede_usarse'])

        create = self.client.post(
            self.insumos_url,
            {'nombre': 'No autorizado', 'cantidad': 1, 'stock_minimo': 0},
            format='json',
        )
        self.assertEqual(create.status_code, status.HTTP_403_FORBIDDEN)
        self.assertFalse(Insumo.objects.filter(nombre='No autorizado').exists())

    def test_authenticated_model_permissions_control_inventory_crud(self):
        self.admin.user_permissions.add(*Permission.objects.filter(
            content_type__app_label='inventario',
            codename__in=(
                'view_insumo', 'add_insumo', 'change_insumo', 'delete_insumo',
                'view_herramienta', 'add_herramienta', 'change_herramienta',
                'delete_herramienta',
            ),
        ))
        self.authenticate_as(self.admin)
        created = self.client.post(
            self.insumos_url,
            {'nombre': 'Mascarillas API', 'cantidad': 25, 'stock_minimo': 8},
            format='json',
        )
        self.assertEqual(created.status_code, status.HTTP_201_CREATED)
        item_url = reverse('v1:insumo-detail', args=[created.data['id']])

        updated = self.client.patch(
            item_url,
            {'cantidad': 18},
            format='json',
        )
        self.assertEqual(updated.status_code, status.HTTP_200_OK)
        self.assertEqual(updated.data['cantidad'], 18)

        invalid = self.client.patch(
            item_url,
            {'cantidad': -1},
            format='json',
        )
        self.assertEqual(invalid.status_code, status.HTTP_400_BAD_REQUEST)

        deleted = self.client.delete(item_url)
        self.assertEqual(deleted.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Insumo.objects.filter(nombre='Mascarillas API').exists())
        self.assertEqual(
            RegistroAuditoria.objects.filter(objeto='Mascarillas API').count(),
            3,
        )

        tool = self.client.post(
            self.herramientas_url,
            {
                'nombre': 'Sierra API',
                'estado': Herramienta.Estado.DISPONIBLE,
                'tratamiento': 'Revisión',
            },
            format='json',
        )
        self.assertEqual(tool.status_code, status.HTTP_201_CREATED)
        tool_url = reverse('v1:herramienta-detail', args=[tool.data['id']])
        changed_tool = self.client.patch(
            tool_url,
            {'estado': Herramienta.Estado.MANTENIMIENTO},
            format='json',
        )
        self.assertEqual(changed_tool.status_code, status.HTTP_200_OK)
        self.assertFalse(changed_tool.data['puede_usarse'])
        self.assertEqual(
            self.client.delete(tool_url).status_code,
            status.HTTP_204_NO_CONTENT,
        )

    def test_auxiliary_creates_request_using_authenticated_identity(self):
        self.authenticate_as(self.auxiliar)
        response = self.client.post(
            self.solicitudes_url,
            {
                'insumo': self.insumo.pk,
                'cantidad_solicitada': 3,
                'usuario': self.admin.pk,
                'usuario_nombre': 'suplantado',
                'estado': Solicitud.Estado.APROBADA,
            },
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        solicitud = Solicitud.objects.get()
        self.assertEqual(solicitud.usuario, self.auxiliar)
        self.assertEqual(solicitud.usuario_nombre, self.auxiliar.username)
        self.assertEqual(solicitud.insumo_nombre, self.insumo.nombre)
        self.assertEqual(solicitud.estado, Solicitud.Estado.PENDIENTE)
        self.assertTrue(RegistroAuditoria.objects.filter(
            accion='api_crear',
            usuario=self.auxiliar,
            objeto=str(solicitud),
        ).exists())

        self.assertEqual(
            self.client.get(self.solicitudes_url).status_code,
            status.HTTP_403_FORBIDDEN,
        )

    def test_admin_resolves_request_with_required_reason_and_cannot_reopen(self):
        solicitud = Solicitud.objects.create(
            usuario=self.auxiliar,
            usuario_nombre=self.auxiliar.username,
            insumo=self.insumo,
            insumo_nombre=self.insumo.nombre,
            cantidad_solicitada=3,
        )
        self.admin.user_permissions.add(*Permission.objects.filter(
            content_type__app_label='inventario',
            codename__in=('view_solicitud', 'change_solicitud'),
        ))
        self.authenticate_as(self.admin)
        detail_url = reverse('v1:solicitud-detail', args=[solicitud.pk])

        invalid = self.client.patch(
            detail_url,
            {'estado': Solicitud.Estado.APROBADA, 'justificacion': ' '},
            format='json',
        )
        self.assertEqual(invalid.status_code, status.HTTP_400_BAD_REQUEST)
        solicitud.refresh_from_db()
        self.assertEqual(solicitud.estado, Solicitud.Estado.PENDIENTE)

        resolved = self.client.post(
            reverse('v1:solicitud-resolver', args=[solicitud.pk]),
            {
                'estado': Solicitud.Estado.APROBADA,
                'justificacion': 'Reposición autorizada.',
            },
            format='json',
        )
        self.assertEqual(resolved.status_code, status.HTTP_200_OK)
        solicitud.refresh_from_db()
        self.assertEqual(solicitud.estado, Solicitud.Estado.APROBADA)
        self.assertEqual(solicitud.justificacion, 'Reposición autorizada.')

        reopened = self.client.patch(
            detail_url,
            {'estado': Solicitud.Estado.PENDIENTE},
            format='json',
        )
        self.assertEqual(reopened.status_code, status.HTTP_400_BAD_REQUEST)

    def test_json_pagination_search_and_ordering(self):
        self.authenticate_as(self.auxiliar)
        for index in range(22):
            Insumo.objects.create(
                nombre=f'Guante de prueba {index:02}',
                cantidad=index,
                stock_minimo=1,
            )

        listing = self.client.get(self.insumos_url, {'search': 'Guante'})
        self.assertEqual(listing.status_code, status.HTTP_200_OK)
        self.assertTrue(listing['Content-Type'].startswith('application/json'))
        self.assertEqual(listing.data['count'], 23)
        self.assertEqual(len(listing.data['results']), 20)
        self.assertIsNotNone(listing.data['next'])

        smaller_page = self.client.get(
            self.insumos_url,
            {'search': 'Guante', 'page_size': 1},
        )
        self.assertEqual(len(smaller_page.data['results']), 1)

        ordered = self.client.get(self.insumos_url, {'ordering': '-cantidad'})
        self.assertEqual(ordered.data['results'][0]['cantidad'], 21)
