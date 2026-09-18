# gestion_usuarios/tests.py

import logging
from django.test import TestCase
from django.contrib.auth.models import User
from rest_framework.test import APIClient
from rest_framework import status


class TestEndpointsUsuarios(TestCase):
    """Pruebas sobre /api/users/ — autenticación y operaciones CRUD."""

    def setUp(self):
        self.client     = APIClient()
        self.url_login  = '/api/auth/token/'
        self.url_users  = '/api/usuarios/users/'

        # Superusuario para pruebas con permisos completos
        self.admin = User.objects.create_superuser(
            username='admin_test',
            password='Admin123',
            email='admin@test.com',
        )

    def _token_admin(self):
        """Helper: devuelve el access token del admin."""
        response = self.client.post(self.url_login, {
            'username': 'admin_test',
            'password': 'Admin123',
        }, format='json')
        return response.data['access']

    # ── Protección de endpoints ────────────────────────────────────────────────

    def test_listar_usuarios_sin_token_devuelve_401(self):
        """GET /api/users/ sin token debe devolver 401."""
        self.client.credentials()
        response = self.client.get(self.url_users)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_listar_usuarios_con_token_valido_devuelve_200(self):
        """GET /api/users/ con token válido debe devolver 200."""
        self.client.credentials(
            HTTP_AUTHORIZATION=f'Bearer {self._token_admin()}'
        )
        response = self.client.get(self.url_users)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_listar_usuarios_con_token_falso_devuelve_401(self):
        """GET /api/users/ con token inventado debe devolver 401."""
        self.client.credentials(
            HTTP_AUTHORIZATION='Bearer token.falso.abc123'
        )
        response = self.client.get(self.url_users)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    # ── Creación ───────────────────────────────────────────────────────────────

    def test_crear_usuario_devuelve_201(self):
        """POST /api/users/ con datos válidos debe devolver 201."""
        self.client.credentials(
            HTTP_AUTHORIZATION=f'Bearer {self._token_admin()}'
        )
        response = self.client.post(self.url_users, {
            'username':   'nuevo_usuario',
            'email':      'nuevo@test.com',
            'password':   'NuevoPass123',
            'first_name': 'Nuevo',
            'last_name':  'Usuario',
            'date_of_birth': '1990-01-01',
        }, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_crear_usuario_sin_token_devuelve_401(self):
        """POST /api/users/ sin token debe devolver 401."""
        self.client.credentials()
        response = self.client.post(self.url_users, {
            'username': 'sin_token',
            'email':    'sintoken@test.com',
            'date_of_birth': '1990-01-01',
            'password': 'Pass123',
        }, format='json')

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    # ── Auditoría ──────────────────────────────────────────────────────────────

    def test_crear_usuario_registra_en_log_auditoria(self):
        """Crear un usuario debe escribir una entrada en el log de auditoría."""
        log_auditoria = logging.getLogger('auditoria')

        with self.assertLogs('auditoria', level='INFO') as cm:
            self.client.credentials(
                HTTP_AUTHORIZATION=f'Bearer {self._token_admin()}'
            )
            self.client.post(self.url_users, {
                'username':   'auditado',
                'email':      'auditado@test.com',
                'password':   'AuditPass123',
                'first_name': 'Test',
                'date_of_birth': '1990-01-01',
                'last_name':  'Auditoria',
            }, format='json')

        # Verificar que al menos una entrada menciona la acción
        mensajes = '\n'.join(cm.output)
        self.assertIn('CREAR_USUARIO', mensajes)

    def test_login_fallido_registra_en_log_auditoria(self):
        """Un intento de login fallido debe quedar en el log de auditoría."""
        with self.assertLogs('auditoria', level='WARNING') as cm:
            self.client.post(self.url_login, {
                'username': 'admin_test',
                'password': 'wrongpassword',
            }, format='json')

        mensajes = '\n'.join(cm.output)
        self.assertIn('LOGIN_FALLIDO', mensajes)

    def test_login_exitoso_registra_en_log_auditoria(self):
        """Un login exitoso debe quedar en el log de auditoría."""
        with self.assertLogs('auditoria', level='INFO') as cm:
            self.client.post(self.url_login, {
                'username': 'admin_test',
                'password': 'Admin123',
            }, format='json')

        mensajes = '\n'.join(cm.output)
        self.assertIn('LOGIN_EXITOSO', mensajes)