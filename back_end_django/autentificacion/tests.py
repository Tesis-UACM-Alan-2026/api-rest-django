
# autentificacion/tests.py

from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status

User = get_user_model()


class TestLogin(TestCase):
    """Pruebas sobre los endpoints de autenticación JWT."""

    def setUp(self):
        self.client = APIClient()

        self.url_login = '/api/auth/token/'
        self.url_refresh = '/api/auth/token/refresh/'
        self.url_logout = '/api/auth/logout/'
        self.url_logs = '/api/auth/logs/auditoria/'

        self.user = User.objects.create_superuser(
            email="admin@example.com",
            password="Admin12345",
            first_name="Administrador",
            last_name="Pruebas"
        )

    # ---------------- LOGIN ----------------

    def test_login_exitoso_devuelve_tokens(self):
        response = self.client.post(
            self.url_login,
            {
                'email': 'admin@example.com',
                'password': 'Admin12345',
            },
            format='json'
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)

    def test_login_password_incorrecta_devuelve_401(self):
        response = self.client.post(
            self.url_login,
            {
                'email': 'admin@example.com',
                'password': 'wrongpassword',
            },
            format='json'
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_401_UNAUTHORIZED
        )

    def test_login_usuario_inexistente_devuelve_401(self):
        response = self.client.post(
            self.url_login,
            {
                'email': 'noexiste@example.com',
                'password': 'TestPass123',
            },
            format='json'
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_401_UNAUTHORIZED
        )

    def test_login_sin_credenciales_devuelve_400(self):
        response = self.client.post(
            self.url_login,
            {},
            format='json'
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST
        )

    # ---------------- REFRESH ----------------

    def test_refresh_token_valido_devuelve_nuevo_access(self):
        login = self.client.post(
            self.url_login,
            {
                'email': 'admin@example.com',
                'password': 'Admin12345',
            },
            format='json'
        )

        self.assertEqual(login.status_code, status.HTTP_200_OK)

        response = self.client.post(
            self.url_refresh,
            {
                'refresh': login.data['refresh'],
            },
            format='json'
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)

    def test_refresh_token_invalido_devuelve_401(self):
        response = self.client.post(
            self.url_refresh,
            {
                'refresh': 'token.falso.invalido',
            },
            format='json'
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_401_UNAUTHORIZED
        )

    # ---------------- LOGOUT ----------------

    def test_logout_invalida_refresh_token(self):
        login = self.client.post(
            self.url_login,
            {
                'email': 'admin@example.com',
                'password': 'Admin12345',
            },
            format='json'
        )

        self.assertEqual(login.status_code, status.HTTP_200_OK)

        access = login.data['access']
        refresh = login.data['refresh']

        self.client.credentials(
            HTTP_AUTHORIZATION=f'Bearer {access}'
        )

        logout = self.client.post(
            self.url_logout,
            {
                'refresh': refresh,
            },
            format='json'
        )

        self.assertEqual(
            logout.status_code,
            status.HTTP_200_OK
        )

        reuso = self.client.post(
            self.url_refresh,
            {
                'refresh': refresh,
            },
            format='json'
        )

        self.assertIn(
            reuso.status_code,
            [
                status.HTTP_401_UNAUTHORIZED,
                status.HTTP_400_BAD_REQUEST,
            ]
        )

    def test_logout_sin_token_devuelve_401(self):
        self.client.credentials()

        response = self.client.post(
            self.url_logout,
            {
                'refresh': 'cualquier-cosa',
            },
            format='json'
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_401_UNAUTHORIZED
        )

    # ---------------- LOGS DE AUDITORÍA ----------------

    def test_logs_auditoria_accesible_para_admin(self):
        login = self.client.post(
            self.url_login,
            {
                'email': 'admin@example.com',
                'password': 'Admin12345',
            },
            format='json'
        )

        self.assertEqual(login.status_code, status.HTTP_200_OK)

        self.client.credentials(
            HTTP_AUTHORIZATION=f'Bearer {login.data["access"]}'
        )

        response = self.client.get(self.url_logs)

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK
        )

        self.assertIn('entradas', response.data)
        self.assertIn('total', response.data)

    def test_logs_auditoria_bloqueado_para_usuario_normal(self):
        User.objects.create_user(
            email='normal@test.com',
            password='Normal123',
            first_name='Usuario',
            last_name='Normal'
        )

        login = self.client.post(
            self.url_login,
            {
                'email': 'normal@test.com',
                'password': 'Normal123',
            },
            format='json'
        )

        self.assertEqual(login.status_code, status.HTTP_200_OK)

        self.client.credentials(
            HTTP_AUTHORIZATION=f'Bearer {login.data["access"]}'
        )

        response = self.client.get(self.url_logs)

        self.assertEqual(
            response.status_code,
            status.HTTP_403_FORBIDDEN
        )

    def test_logs_auditoria_bloqueado_sin_autenticacion(self):
        self.client.credentials()

        response = self.client.get(self.url_logs)

        self.assertEqual(
            response.status_code,
            status.HTTP_401_UNAUTHORIZED
        )
