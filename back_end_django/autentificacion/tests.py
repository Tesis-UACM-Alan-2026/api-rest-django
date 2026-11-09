# autentificacion/tests.py

import tempfile
from pathlib import Path

from django.contrib.auth import get_user_model
from django.test import SimpleTestCase, TestCase, override_settings
from rest_framework import status
from rest_framework.test import APIClient

from unittest.mock import patch

from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import RefreshToken

from autentificacion.exceptions.autenticacionExceptions import LogNoDisponible_500
from autentificacion.log_views import logService
from autentificacion.service import LogService
from core.testing import (
    PASSWORD,
    crear_superusuario,
    crear_usuario,
    crear_usuario_con_permisos,
)

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


# =====================================================================
#                        PRUEBAS NUEVAS
# =====================================================================

class TestLoginCasosLimite(TestCase):
    """Login: usuarios inactivos, formatos inválidos y forma de la respuesta."""

    def setUp(self):
        self.client = APIClient()
        self.url_login = '/api/auth/token/'
        self.usuario = crear_usuario("ana@test.com")

    def _login(self, email="ana@test.com", password=PASSWORD):
        return self.client.post(
            self.url_login, {'email': email, 'password': password}, format='json'
        )

    def test_login_usuario_inactivo_devuelve_401(self):
        self.usuario.is_active = False
        self.usuario.save()

        self.assertEqual(self._login().status_code, status.HTTP_401_UNAUTHORIZED)

    def test_login_email_con_formato_invalido_devuelve_400(self):
        self.assertEqual(
            self._login(email="no-es-un-email").status_code,
            status.HTTP_400_BAD_REQUEST
        )

    def test_login_respuesta_solo_contiene_los_tokens(self):
        response = self._login()

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(set(response.data.keys()), {'access', 'refresh'})

    def test_mismo_mensaje_si_el_usuario_no_existe_o_la_password_es_incorrecta(self):
        inexistente = self._login(email="nadie@test.com")
        incorrecta = self._login(password="otra-cosa")

        self.assertEqual(inexistente.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(inexistente.data, incorrecta.data)

    def test_login_con_token_vencido_en_cabecera_no_bloquea_el_login(self):
        self.client.credentials(HTTP_AUTHORIZATION='Bearer token.vencido.xyz')

        self.assertEqual(self._login().status_code, status.HTTP_200_OK)

    def test_usuario_desactivado_despues_de_loguearse_no_puede_usar_su_access(self):
        access = self._login().data['access']
        self.usuario.is_active = False
        self.usuario.save()

        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access}')
        response = self.client.get('/api/categorias/')

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class TestLogoutCasosLimite(TestCase):
    """Logout: validaciones y protección contra tokens de otro usuario."""

    def setUp(self):
        self.client = APIClient()
        self.url_login = '/api/auth/token/'
        self.url_refresh = '/api/auth/token/refresh/'
        self.url_logout = '/api/auth/logout/'

        crear_usuario("ana@test.com")
        crear_usuario("beto@test.com")

    def _login(self, email):
        response = self.client.post(
            self.url_login, {'email': email, 'password': PASSWORD}, format='json'
        )
        return response.data

    def _autenticar(self, access):
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access}')

    def test_logout_con_refresh_de_otro_usuario_devuelve_403(self):
        ana = self._login("ana@test.com")
        beto = self._login("beto@test.com")

        self._autenticar(ana['access'])
        response = self.client.post(
            self.url_logout, {'refresh': beto['refresh']}, format='json'
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_refresh_ajeno_no_queda_invalidado_tras_el_intento(self):
        ana = self._login("ana@test.com")
        beto = self._login("beto@test.com")

        self._autenticar(ana['access'])
        self.client.post(self.url_logout, {'refresh': beto['refresh']}, format='json')

        self.client.credentials()
        response = self.client.post(
            self.url_refresh, {'refresh': beto['refresh']}, format='json'
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_logout_con_token_ajeno_queda_en_auditoria_como_warning(self):
        ana = self._login("ana@test.com")
        beto = self._login("beto@test.com")
        self._autenticar(ana['access'])

        with self.assertLogs('auditoria', level='WARNING') as cm:
            self.client.post(
                self.url_logout, {'refresh': beto['refresh']}, format='json'
            )

        self.assertIn('LOGOUT_TOKEN_AJENO', '\n'.join(cm.output))

    def test_logout_sin_refresh_devuelve_400(self):
        self._autenticar(self._login("ana@test.com")['access'])

        response = self.client.post(self.url_logout, {}, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_logout_con_refresh_basura_devuelve_400(self):
        self._autenticar(self._login("ana@test.com")['access'])

        response = self.client.post(
            self.url_logout, {'refresh': 'esto.no.es.un.token'}, format='json'
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_logout_dos_veces_con_el_mismo_refresh_devuelve_400_la_segunda(self):
        sesion = self._login("ana@test.com")
        self._autenticar(sesion['access'])

        primero = self.client.post(
            self.url_logout, {'refresh': sesion['refresh']}, format='json'
        )
        segundo = self.client.post(
            self.url_logout, {'refresh': sesion['refresh']}, format='json'
        )

        self.assertEqual(primero.status_code, status.HTTP_200_OK)
        self.assertEqual(segundo.status_code, status.HTTP_400_BAD_REQUEST)

    def test_logout_exitoso_queda_en_auditoria(self):
        sesion = self._login("ana@test.com")
        self._autenticar(sesion['access'])

        with self.assertLogs('auditoria', level='INFO') as cm:
            self.client.post(
                self.url_logout, {'refresh': sesion['refresh']}, format='json'
            )

        self.assertIn('LOGOUT', '\n'.join(cm.output))


class TestLogsConRBAC(TestCase):
    """Los logs exigen permisos de rol, no solo is_staff."""

    def setUp(self):
        self.client = APIClient()
        self.url_auditoria = '/api/auth/logs/auditoria/'
        self.url_tecnico = '/api/auth/logs/tecnico/'

    def test_usuario_con_permiso_de_auditoria_puede_leerla(self):
        usuario = crear_usuario_con_permisos(['logs.ver_auditoria'])
        self.client.force_authenticate(user=usuario)

        response = self.client.get(self.url_auditoria)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_los_permisos_de_auditoria_y_tecnico_son_independientes(self):
        usuario = crear_usuario_con_permisos(['logs.ver_tecnico'])
        self.client.force_authenticate(user=usuario)

        self.assertEqual(
            self.client.get(self.url_auditoria).status_code, status.HTTP_403_FORBIDDEN
        )
        self.assertEqual(
            self.client.get(self.url_tecnico).status_code, status.HTTP_200_OK
        )

    def test_staff_sin_permiso_de_rol_recibe_403(self):
        """Cambio respecto a IsAdminUser: ser staff ya no basta."""
        usuario = crear_usuario("staff@test.com", is_staff=True)
        self.client.force_authenticate(user=usuario)

        self.assertEqual(
            self.client.get(self.url_auditoria).status_code, status.HTTP_403_FORBIDDEN
        )

    def test_superusuario_puede_leer_ambos_logs(self):
        self.client.force_authenticate(user=crear_superusuario())

        self.assertEqual(self.client.get(self.url_auditoria).status_code, 200)
        self.assertEqual(self.client.get(self.url_tecnico).status_code, 200)

    def test_limite_invalido_devuelve_400(self):
        self.client.force_authenticate(user=crear_superusuario())

        for valor in ('abc', '0', '-5', '5000'):
            with self.subTest(limite=valor):
                response = self.client.get(self.url_auditoria, {'limite': valor})
                self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_limite_valido_devuelve_200(self):
        self.client.force_authenticate(user=crear_superusuario())

        response = self.client.get(self.url_auditoria, {'limite': 50})

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_consultar_la_auditoria_deja_registro(self):
        self.client.force_authenticate(user=crear_superusuario())

        with self.assertLogs('auditoria', level='INFO') as cm:
            self.client.get(self.url_auditoria)

        self.assertIn('CONSULTAR_LOG_AUDITORIA', '\n'.join(cm.output))


class TestLecturaDeLogs(SimpleTestCase):
    """LogService/LogDAO sobre un directorio temporal de logs."""

    LINEAS = [
        "[2026-11-08 10:00:01] [AUDITORIA] [Usuario: [ip:1.1.1.1] [accion:LOGIN_EXITOSO] [usuario:ana@x.com]]\n",
        "[2026-11-08 10:00:02] [AUDITORIA] [Usuario: [ip:2.2.2.2] [accion:LOGIN_FALLIDO] [usuario:bob@x.com]]\n",
        "Traceback (most recent call last):\n",
        "  File x.py\n",
        "[2026-11-08 10:00:03] [AUDITORIA] [Usuario: [ip:1.1.1.1] [accion:CREAR_USUARIO] [realizado_por:ana@x.com]]\n",
        "[2026-11-08 10:00:04] [AUDITORIA] [Usuario: [ip:3.3.3.3] [accion:LOGIN_EXITOSO] [usuario:cris@x.com]]\n",
    ]

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)

        with open(Path(self._tmp.name) / "auditoria.log", "wb") as archivo:
            for linea in self.LINEAS:
                archivo.write(linea.encode())
            archivo.write(b"[2026-11-08 10:00:05] [AUDITORIA] bytes invalidos \xff\xfe fin\n")

        override = override_settings(LOGS_DIR=Path(self._tmp.name))
        override.enable()
        self.addCleanup(override.disable)

        self.servicio = LogService()

    def test_devuelve_registros_mas_recientes_primero_y_omite_tracebacks(self):
        consulta = self.servicio.consultar("auditoria", {}, 100)

        self.assertEqual(consulta.total, 5)
        self.assertIn("10:00:05", consulta.entradas[0])

    def test_bytes_no_utf8_no_rompen_la_lectura(self):
        consulta = self.servicio.consultar("auditoria", {}, 100)

        self.assertTrue(any("fin" in e for e in consulta.entradas))

    def test_filtro_por_accion(self):
        consulta = self.servicio.consultar(
            "auditoria", {"accion": "login_exitoso", "usuario": None}, 100
        )

        self.assertEqual(consulta.total, 2)
        self.assertEqual(consulta.filtros_aplicados, {"accion": "login_exitoso"})

    def test_filtros_combinados(self):
        consulta = self.servicio.consultar(
            "auditoria", {"accion": "login_exitoso", "usuario": "cris"}, 100
        )

        self.assertEqual(consulta.total, 1)
        self.assertIn("cris@x.com", consulta.entradas[0])

    def test_limite_devuelve_las_mas_recientes(self):
        consulta = self.servicio.consultar("auditoria", {}, 2)

        self.assertEqual(consulta.total, 2)
        self.assertIn("10:00:05", consulta.entradas[0])
        self.assertIn("10:00:04", consulta.entradas[1])

    def test_archivo_inexistente_devuelve_lista_vacia(self):
        self.assertEqual(self.servicio.consultar("tecnico", {}, 100).total, 0)

    def test_solo_se_permiten_los_archivos_de_la_lista_blanca(self):
        with self.assertRaises(ValueError):
            self.servicio.consultar("../../etc/passwd", {}, 10)


class TestRamasDeErrorDeAutenticacion(TestCase):
    """Fallos inesperados: nunca deben llegar al cliente como un error sin formato."""

    def setUp(self):
        self.client = APIClient()
        crear_usuario("ana@test.com")

    def _login(self):
        return self.client.post(
            '/api/auth/token/',
            {'email': 'ana@test.com', 'password': PASSWORD},
            format='json'
        ).data

    def test_si_el_blacklist_falla_el_logout_devuelve_400(self):
        sesion = self._login()
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {sesion['access']}")

        with patch.object(RefreshToken, "blacklist", side_effect=TokenError("fallo")):
            response = self.client.post(
                '/api/auth/logout/', {'refresh': sesion['refresh']}, format='json'
            )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_logs_devuelven_500_con_formato_si_no_se_puede_leer_el_archivo(self):
        self.client.force_authenticate(user=crear_superusuario())

        with patch.object(logService, "consultar", side_effect=LogNoDisponible_500()):
            auditoria = self.client.get('/api/auth/logs/auditoria/')
            tecnico = self.client.get('/api/auth/logs/tecnico/')

        self.assertEqual(auditoria.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        self.assertEqual(tecnico.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        self.assertIn('error', auditoria.data)

    def test_log_tecnico_valida_el_limite(self):
        self.client.force_authenticate(user=crear_superusuario())

        response = self.client.get('/api/auth/logs/tecnico/', {'limite': 'abc'})

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_log_tecnico_acepta_filtros(self):
        self.client.force_authenticate(user=crear_superusuario())

        response = self.client.get(
            '/api/auth/logs/tecnico/', {'nivel': 'ERROR', 'modulo': 'views', 'limite': 10}
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            response.data['filtros_aplicados'], {'nivel': 'ERROR', 'modulo': 'views'}
        )


class TestLogDAOFallosDeLectura(SimpleTestCase):

    def test_un_error_del_sistema_de_archivos_se_traduce_a_logNoDisponible(self):
        with tempfile.TemporaryDirectory() as carpeta:
            (Path(carpeta) / "auditoria.log").write_text("[x] linea\n", encoding="utf-8")

            with override_settings(LOGS_DIR=Path(carpeta)), \
                    patch("autentificacion.DAO.logDAO.open", side_effect=OSError, create=True):
                with self.assertRaises(LogNoDisponible_500):
                    LogService().consultar("auditoria", {}, 10)