# gestion_usuarios/tests.py

import uuid

from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient, APITestCase

from core.testing import (
    PASSWORD,
    crear_rol_con_permisos,
    crear_superusuario,
    crear_usuario,
    crear_usuario_con_permisos,
)
from datetime import timedelta
from unittest import skipUnless
from unittest.mock import MagicMock, patch

from django.core.exceptions import ValidationError
from django.db.utils import DatabaseError, IntegrityError
from django.utils import timezone

from gestion_permisos.models import Rol
from gestion_usuarios.DAO.usuarioDAO import UsuarioDAO
from gestion_usuarios.exceptions.usuarioExeptions import (
    ConflictoUsuario_409,
    DatosInvalidos_400,
    ErrorInternoServidor_500,
    UsuarioNoAutorizado_401,
    UsuarioNoEncontrado_404,
    UsuarioProhibido_403,
)
from gestion_usuarios.views import usuarioService

User = get_user_model()
class TestEndpointsUsuarios(TestCase):
    """Pruebas sobre /api/users/ — autenticación y operaciones CRUD."""

    def setUp(self):
        self.client = APIClient()
        self.url_login = '/api/auth/token/'
        self.url_users = '/api/usuarios/'  # antes: /api/usuarios/users/

        self.user = User.objects.create_superuser(
            email="admin@example.com",
            password="Admin12345",
            first_name="Administrador",
            last_name="Pruebas"
        )

    def _token_admin(self):
        response = self.client.post(self.url_login, {
            'email': 'admin@example.com',
            'password': 'Admin12345',
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
            'email':      'nuevo@test.com',
            'password':   'NuevoPass123',
            'first_name': 'Nuevo',
            'last_name':  'Usuario',
        }, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_crear_usuario_sin_token_devuelve_401(self):
        """POST /api/users/ sin token debe devolver 401."""
        self.client.credentials()
        response = self.client.post(self.url_users, {
            'email':    'sintoken@test.com',
            'password': 'Pass123',
        }, format='json')

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    # ── Auditoría ──────────────────────────────────────────────────────────────

    def test_crear_usuario_registra_en_log_auditoria(self):
        """Crear un usuario debe escribir una entrada en el log de auditoría."""
        token = self._token_admin()
        self.client.credentials(
            HTTP_AUTHORIZATION=f'Bearer {token}'
        )
        with self.assertLogs('auditoria', level='INFO') as cm:
            self.client.post(self.url_users, {
                'email': 'auditado@test.com',
                'password': 'AuditPass123',
                'first_name': 'Test',
                'last_name': 'Auditoria',
            }, format='json')
        mensajes = '\n'.join(cm.output)
        self.assertIn('CREAR_USUARIO', mensajes)

    def test_login_fallido_registra_en_log_auditoria(self):
        """Un intento de login fallido debe quedar en el log de auditoría."""
        with self.assertLogs('auditoria', level='WARNING') as cm:
            self.client.post(self.url_login, {
                'email': 'admin@example.com',
                'password': 'wrongpassword',
            }, format='json')
        mensajes = '\n'.join(cm.output)
        self.assertIn('LOGIN_FALLIDO', mensajes)

    def test_login_exitoso_registra_en_log_auditoria(self):
        """Un login exitoso debe quedar en el log de auditoría."""
        with self.assertLogs('auditoria', level='INFO') as cm:
            self.client.post(self.url_login, {
                'email': 'admin@example.com',
                'password': 'Admin12345',
            }, format='json')

        mensajes = '\n'.join(cm.output)
        self.assertIn('LOGIN_EXITOSO', mensajes)


# =====================================================================
#                        PRUEBAS NUEVAS
# =====================================================================

class UsuariosCRUDTests(APITestCase):
    """Reglas del DAO/servicio vistas a través de la API."""

    def setUp(self):
        self.url = "/api/usuarios/"
        self.gestor = crear_usuario_con_permisos(
            ["usuarios.ver", "usuarios.crear", "usuarios.editar", "usuarios.eliminar"],
            email="gestor@test.com",
        )
        self.client.force_authenticate(user=self.gestor)
        self.ana = crear_usuario("ana@test.com", first_name="Ana", last_name="Pérez")

    def _datos(self, **cambios):
        datos = {
            "email": "nuevo@test.com",
            "password": "NuevoPass123",
            "first_name": "Nuevo",
            "last_name": "Usuario",
        }
        datos.update(cambios)
        return datos

    # ----- creación -----
    def test_crear_usuario_no_expone_la_password_e_incluye_roles(self):
        response = self.client.post(self.url, self._datos(), format="json")

        self.assertEqual(response.status_code, 201)
        self.assertNotIn("password", response.data)
        self.assertEqual(response.data["roles"], [])

    def test_crear_usuario_guarda_la_password_hasheada_y_puede_iniciar_sesion(self):
        self.client.post(self.url, self._datos(), format="json")

        usuario = get_user_model().objects.get(email="nuevo@test.com")
        self.assertNotEqual(usuario.password, "NuevoPass123")

        login = APIClient().post(
            "/api/auth/token/",
            {"email": "nuevo@test.com", "password": "NuevoPass123"},
            format="json",
        )
        self.assertEqual(login.status_code, 200)

    def test_crear_con_email_repetido_devuelve_409_sin_distinguir_mayusculas(self):
        response = self.client.post(
            self.url, self._datos(email="ANA@test.com"), format="json"
        )

        self.assertEqual(response.status_code, 409)

    def test_crear_con_password_corta_devuelve_400(self):
        response = self.client.post(
            self.url, self._datos(password="corta"), format="json"
        )

        self.assertEqual(response.status_code, 400)

    def test_crear_sin_password_devuelve_400(self):
        datos = self._datos()
        del datos["password"]

        self.assertEqual(self.client.post(self.url, datos, format="json").status_code, 400)

    def test_crear_con_email_invalido_devuelve_400(self):
        response = self.client.post(
            self.url, self._datos(email="no-es-email"), format="json"
        )

        self.assertEqual(response.status_code, 400)

    def test_crear_no_permite_asignarse_roles_ni_privilegios(self):
        rol = Rol.objects.create(nombre="Admin")

        response = self.client.post(
            self.url,
            self._datos(roles=[rol.id], is_superuser=True, is_staff=True),
            format="json",
        )

        self.assertEqual(response.status_code, 201)
        usuario = get_user_model().objects.get(email="nuevo@test.com")
        self.assertFalse(usuario.is_superuser)
        self.assertFalse(usuario.is_staff)
        self.assertEqual(usuario.roles.count(), 0)

    # ----- consulta -----
    def test_listar_usuarios(self):
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        correos = [u["email"] for u in response.data]
        self.assertIn("ana@test.com", correos)
        self.assertTrue(all("password" not in u for u in response.data))

    def test_consultar_usuario(self):
        response = self.client.get(f"{self.url}{self.ana.id}/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["email"], "ana@test.com")

    def test_consultar_usuario_inexistente_devuelve_404(self):
        self.assertEqual(self.client.get(f"{self.url}{uuid.uuid4()}/").status_code, 404)

    def test_id_que_no_es_uuid_devuelve_404_y_no_500(self):
        self.assertEqual(self.client.get(f"{self.url}abc/").status_code, 404)

    # ----- actualización -----
    def test_put_actualiza_nombre_y_apellido(self):
        response = self.client.put(
            f"{self.url}{self.ana.id}/",
            {"email": "ana@test.com", "first_name": "Ana María", "last_name": "López"},
            format="json",
        )

        self.assertEqual(response.status_code, 200)
        self.ana.refresh_from_db()
        self.assertEqual(self.ana.first_name, "Ana María")

    def test_put_con_el_mismo_email_no_es_conflicto(self):
        response = self.client.put(
            f"{self.url}{self.ana.id}/",
            {"email": "ana@test.com", "first_name": "Ana", "last_name": "Pérez"},
            format="json",
        )

        self.assertEqual(response.status_code, 200)

    def test_put_con_password_devuelve_400_y_no_la_cambia(self):
        anterior = self.ana.password

        response = self.client.put(
            f"{self.url}{self.ana.id}/",
            {"email": "ana@test.com", "first_name": "Ana", "last_name": "Pérez",
             "password": "OtraClave123"},
            format="json",
        )

        self.assertEqual(response.status_code, 400)
        self.ana.refresh_from_db()
        self.assertEqual(self.ana.password, anterior)

    def test_patch_solo_modifica_los_campos_enviados(self):
        response = self.client.patch(
            f"{self.url}{self.ana.id}/", {"first_name": "Anita"}, format="json"
        )

        self.assertEqual(response.status_code, 200)
        self.ana.refresh_from_db()
        self.assertEqual(self.ana.first_name, "Anita")
        self.assertEqual(self.ana.last_name, "Pérez")

    def test_patch_con_email_de_otro_usuario_devuelve_409(self):
        crear_usuario("beto@test.com")

        response = self.client.patch(
            f"{self.url}{self.ana.id}/", {"email": "beto@test.com"}, format="json"
        )

        self.assertEqual(response.status_code, 409)

    def test_patch_no_puede_elevar_privilegios(self):
        response = self.client.patch(
            f"{self.url}{self.ana.id}/",
            {"is_superuser": True, "is_staff": True, "is_active": False,
             "password": "Hackeada123"},
            format="json",
        )

        self.assertEqual(response.status_code, 200)
        self.ana.refresh_from_db()
        self.assertFalse(self.ana.is_superuser)
        self.assertFalse(self.ana.is_staff)
        self.assertTrue(self.ana.is_active)
        self.assertTrue(self.ana.check_password(PASSWORD))

    def test_patch_con_email_invalido_devuelve_400(self):
        response = self.client.patch(
            f"{self.url}{self.ana.id}/", {"email": "roto"}, format="json"
        )

        self.assertEqual(response.status_code, 400)

    # ----- eliminación lógica -----
    def test_eliminar_es_logico_y_el_usuario_ya_no_puede_iniciar_sesion(self):
        response = self.client.delete(f"{self.url}{self.ana.id}/")

        self.assertEqual(response.status_code, 200)
        self.ana.refresh_from_db()
        self.assertFalse(self.ana.is_active)

        login = APIClient().post(
            "/api/auth/token/",
            {"email": "ana@test.com", "password": PASSWORD},
            format="json",
        )
        self.assertEqual(login.status_code, 401)

    def test_eliminar_usuario_inexistente_devuelve_404(self):
        self.assertEqual(self.client.delete(f"{self.url}{uuid.uuid4()}/").status_code, 404)


class UsuariosEstadoTests(APITestCase):

    def setUp(self):
        self.url = "/api/usuarios/"
        self.client.force_authenticate(
            user=crear_usuario_con_permisos(["usuarios.cambiar_estado"], email="g@test.com")
        )
        self.ana = crear_usuario("ana@test.com")

    def test_desactivar_y_volver_a_desactivar(self):
        primero = self.client.patch(f"{self.url}{self.ana.id}/deactivate/")
        segundo = self.client.patch(f"{self.url}{self.ana.id}/deactivate/")

        self.assertEqual(primero.status_code, 200)
        self.assertEqual(segundo.status_code, 400)

    def test_activar_un_usuario_ya_activo_devuelve_400(self):
        self.assertEqual(self.client.patch(f"{self.url}{self.ana.id}/activate/").status_code, 400)

    def test_activar_un_usuario_desactivado(self):
        self.ana.is_active = False
        self.ana.save()

        response = self.client.patch(f"{self.url}{self.ana.id}/activate/")

        self.assertEqual(response.status_code, 200)
        self.ana.refresh_from_db()
        self.assertTrue(self.ana.is_active)

    def test_restaurar_usuario_eliminado(self):
        self.ana.is_active = False
        self.ana.save()

        self.assertEqual(self.client.patch(f"{self.url}{self.ana.id}/restore/").status_code, 200)
        self.ana.refresh_from_db()
        self.assertTrue(self.ana.is_active)

    def test_cambiar_estado_exige_su_permiso(self):
        self.client.force_authenticate(
            user=crear_usuario_con_permisos(["usuarios.ver", "usuarios.editar"], email="x@test.com")
        )

        for accion in ("activate", "deactivate", "restore"):
            with self.subTest(accion=accion):
                response = self.client.patch(f"{self.url}{self.ana.id}/{accion}/")
                self.assertEqual(response.status_code, 403)


class UsuariosAutorizacionTests(APITestCase):

    def setUp(self):
        self.url = "/api/usuarios/"
        self.ana = crear_usuario("ana@test.com")

    def test_usuario_sin_roles_recibe_403_en_todo(self):
        self.client.force_authenticate(user=crear_usuario("sin@test.com"))
        detalle = f"{self.url}{self.ana.id}/"
        datos = {"email": "x@test.com", "password": "ClaveSegura1",
                 "first_name": "X", "last_name": "Y"}

        self.assertEqual(self.client.get(self.url).status_code, 403)
        self.assertEqual(self.client.get(detalle).status_code, 403)
        self.assertEqual(self.client.post(self.url, datos, format="json").status_code, 403)
        self.assertEqual(self.client.patch(detalle, {"first_name": "Z"}, format="json").status_code, 403)
        self.assertEqual(self.client.delete(detalle).status_code, 403)

    def test_rol_de_solo_lectura_no_puede_modificar(self):
        self.client.force_authenticate(user=crear_usuario_con_permisos(["usuarios.ver"]))
        detalle = f"{self.url}{self.ana.id}/"

        self.assertEqual(self.client.get(self.url).status_code, 200)
        self.assertEqual(self.client.patch(detalle, {"first_name": "Z"}, format="json").status_code, 403)
        self.assertEqual(self.client.delete(detalle).status_code, 403)


class UsuariosRolesTests(APITestCase):
    """Asignación de roles a usuarios."""

    def setUp(self):
        self.url = "/api/usuarios/"
        self.client.force_authenticate(
            user=crear_usuario_con_permisos(["usuarios.asignar_roles"], email="g@test.com")
        )
        self.ana = crear_usuario("ana@test.com")
        self.vendedor = Rol.objects.create(nombre="Vendedor")
        self.auditor = Rol.objects.create(nombre="Auditor")

    def _asignar(self, roles, usuario=None):
        return self.client.post(
            f"{self.url}{(usuario or self.ana).id}/asignar-roles/",
            {"roles": roles}, format="json",
        )

    def _quitar(self, roles, usuario=None):
        return self.client.post(
            f"{self.url}{(usuario or self.ana).id}/quitar-roles/",
            {"roles": roles}, format="json",
        )

    def test_asignar_roles_devuelve_el_usuario_con_sus_roles(self):
        response = self._asignar([self.vendedor.id, self.auditor.id])

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            sorted(r["nombre"] for r in response.data["roles"]), ["Auditor", "Vendedor"]
        )

    def test_asignar_dos_veces_es_idempotente(self):
        self._asignar([self.vendedor.id])
        response = self._asignar([self.vendedor.id, self.auditor.id])

        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.ana.roles.count(), 2)

    def test_un_rol_inexistente_devuelve_400_y_no_asigna_ninguno(self):
        response = self._asignar([self.vendedor.id, 999999])

        self.assertEqual(response.status_code, 400)
        self.assertEqual(self.ana.roles.count(), 0)

    def test_asignar_a_usuario_inexistente_devuelve_404(self):
        response = self.client.post(
            f"{self.url}{uuid.uuid4()}/asignar-roles/",
            {"roles": [self.vendedor.id]}, format="json",
        )

        self.assertEqual(response.status_code, 404)

    def test_lista_vacia_o_invalida_devuelve_400(self):
        for cuerpo in ({"roles": []}, {"roles": ["a"]}, {"roles": [0]}, {}):
            with self.subTest(cuerpo=cuerpo):
                response = self.client.post(
                    f"{self.url}{self.ana.id}/asignar-roles/", cuerpo, format="json"
                )
                self.assertEqual(response.status_code, 400)

    def test_quitar_roles(self):
        self.ana.roles.add(self.vendedor, self.auditor)

        response = self._quitar([self.vendedor.id])

        self.assertEqual(response.status_code, 200)
        self.assertEqual([r["nombre"] for r in response.data["roles"]], ["Auditor"])

    def test_quitar_un_rol_que_no_tiene_no_falla(self):
        self.assertEqual(self._quitar([self.vendedor.id]).status_code, 200)

    def test_asignar_y_quitar_exigen_el_permiso_de_roles(self):
        self.client.force_authenticate(
            user=crear_usuario_con_permisos(["usuarios.ver", "usuarios.editar"], email="x@test.com")
        )

        self.assertEqual(self._asignar([self.vendedor.id]).status_code, 403)
        self.assertEqual(self._quitar([self.vendedor.id]).status_code, 403)

    def test_staff_sin_permiso_de_rol_no_puede_asignar_roles(self):
        self.client.force_authenticate(user=crear_usuario("staff@test.com", is_staff=True))

        self.assertEqual(self._asignar([self.vendedor.id]).status_code, 403)

    def test_asignar_roles_queda_en_auditoria(self):
        with self.assertLogs("auditoria", level="INFO") as cm:
            self._asignar([self.vendedor.id])

        self.assertIn("ASIGNAR_ROLES_USUARIO", "\n".join(cm.output))

    def test_el_rol_asignado_otorga_acceso_real(self):
        """De punta a punta: usuario -> rol -> permiso -> endpoint."""
        rol = crear_rol_con_permisos("Consulta de categorías", ["categorias.ver"])
        self.client.force_authenticate(user=self.ana)
        self.assertEqual(self.client.get("/api/categorias/").status_code, 403)

        self.ana.roles.add(rol)

        self.assertEqual(self.client.get("/api/categorias/").status_code, 200)


class UsuariosContrasenaTests(APITestCase):

    def setUp(self):
        self.url = "/api/usuarios/"
        self.ana = crear_usuario("ana@test.com")
        self.beto = crear_usuario("beto@test.com")
        self.client.force_authenticate(user=self.ana)

    def _cambiar(self, usuario=None, **cambios):
        datos = {
            "current_password": PASSWORD,
            "new_password": "NuevaClave456",
            "confirm_password": "NuevaClave456",
        }
        datos.update(cambios)
        return self.client.post(
            f"{self.url}{(usuario or self.ana).id}/change-password/", datos, format="json"
        )

    def test_cambiar_la_propia_contrasena_sin_necesitar_permisos_de_rol(self):
        response = self._cambiar()

        self.assertEqual(response.status_code, 200)
        self.ana.refresh_from_db()
        self.assertTrue(self.ana.check_password("NuevaClave456"))

    def test_despues_del_cambio_solo_sirve_la_nueva_contrasena(self):
        self._cambiar()
        cliente = APIClient()

        viejo = cliente.post("/api/auth/token/", {"email": "ana@test.com", "password": PASSWORD}, format="json")
        nuevo = cliente.post("/api/auth/token/", {"email": "ana@test.com", "password": "NuevaClave456"}, format="json")

        self.assertEqual(viejo.status_code, 401)
        self.assertEqual(nuevo.status_code, 200)

    def test_no_se_puede_cambiar_la_contrasena_de_otro_usuario(self):
        response = self._cambiar(usuario=self.beto)

        self.assertEqual(response.status_code, 403)
        self.beto.refresh_from_db()
        self.assertTrue(self.beto.check_password(PASSWORD))

    def test_contrasena_actual_incorrecta_devuelve_400(self):
        self.assertEqual(self._cambiar(current_password="incorrecta").status_code, 400)

    def test_confirmacion_distinta_devuelve_400(self):
        self.assertEqual(self._cambiar(confirm_password="OtraDistinta1").status_code, 400)

    def test_contrasena_nueva_corta_devuelve_400(self):
        self.assertEqual(
            self._cambiar(new_password="corta", confirm_password="corta").status_code, 400
        )

    def test_la_nueva_no_puede_ser_igual_a_la_actual(self):
        self.assertEqual(
            self._cambiar(new_password=PASSWORD, confirm_password=PASSWORD).status_code, 400
        )

    def test_sin_autenticar_devuelve_401(self):
        self.client.force_authenticate(user=None)

        self.assertEqual(self._cambiar().status_code, 401)


class UsuariosRestablecerContrasenaTests(APITestCase):

    def setUp(self):
        self.url = "/api/usuarios/request-password-reset/"
        self.ana = crear_usuario("ana@test.com")

    def test_es_publico_y_genera_token_con_vencimiento(self):
        response = self.client.post(self.url, {"email": "ana@test.com"}, format="json")

        self.assertEqual(response.status_code, 200)
        self.ana.refresh_from_db()
        self.assertIsNotNone(self.ana.reset_password_token)
        self.assertIsNotNone(self.ana.reset_password_expires_at)

    def test_la_respuesta_no_expone_el_token(self):
        response = self.client.post(self.url, {"email": "ana@test.com"}, format="json")
        self.ana.refresh_from_db()

        self.assertNotIn(str(self.ana.reset_password_token), str(response.data))

    def test_email_inexistente_devuelve_404(self):
        """Comportamiento actual (permite enumerar correos): pendiente de decisión."""
        response = self.client.post(self.url, {"email": "nadie@test.com"}, format="json")

        self.assertEqual(response.status_code, 404)

    def test_email_con_formato_invalido_devuelve_400(self):
        self.assertEqual(
            self.client.post(self.url, {"email": "roto"}, format="json").status_code, 400
        )

    def test_usuario_inactivo_no_puede_solicitar_el_restablecimiento(self):
        self.ana.is_active = False
        self.ana.save()

        response = self.client.post(self.url, {"email": "ana@test.com"}, format="json")

        self.assertEqual(response.status_code, 404)


# =====================================================================
#              COBERTURA DE RAMAS DE ERROR Y RESTABLECIMIENTO
# =====================================================================

class UsuarioDAOValidacionesTests(TestCase):
    """Validaciones del DAO invocadas directamente (sin pasar por la API)."""

    def setUp(self):
        self.ana = crear_usuario("ana@test.com")

    def test_crear_usuario_con_email_invalido(self):
        with self.assertRaises(DatosInvalidos_400):
            UsuarioDAO.crear_usuario("roto", "ClaveSegura1", "N", "U")

    def test_crear_usuario_sin_nombre_o_apellido(self):
        with self.assertRaises(DatosInvalidos_400):
            UsuarioDAO.crear_usuario("n@test.com", "ClaveSegura1", "", "U")
        with self.assertRaises(DatosInvalidos_400):
            UsuarioDAO.crear_usuario("n@test.com", "ClaveSegura1", "N", "")

    def test_crear_usuario_con_password_vacia_o_corta(self):
        for password in ("", None, "corta"):
            with self.subTest(password=password), self.assertRaises(DatosInvalidos_400):
                UsuarioDAO.crear_usuario("n@test.com", password, "N", "U")

    def test_actualizar_usuario_rechaza_campos_fuera_de_la_lista(self):
        with self.assertRaises(DatosInvalidos_400):
            UsuarioDAO.actualizar_usuario(self.ana.id, {"is_superuser": True})

        self.ana.refresh_from_db()
        self.assertFalse(self.ana.is_superuser)

    def test_actualizar_usuario_con_email_invalido(self):
        with self.assertRaises(DatosInvalidos_400):
            UsuarioDAO.actualizar_usuario(self.ana.id, {"email": "roto"})

    def test_actualizar_usuario_parcial_aplica_las_mismas_reglas(self):
        with self.assertRaises(DatosInvalidos_400):
            UsuarioDAO.actualizar_usuario_parcial(self.ana.id, password="x")

    def test_contrasena_nueva_corta_directo_en_el_dao(self):
        with self.assertRaises(ValidationError):
            UsuarioDAO.actualizar_contrasena(self.ana.id, PASSWORD, "corta", "corta")

    def test_confirmacion_distinta_directo_en_el_dao(self):
        with self.assertRaises(ValidationError):
            UsuarioDAO.actualizar_contrasena(
                self.ana.id, PASSWORD, "NuevaClave456", "OtraDistinta1"
            )


class UsuarioDAOResetPasswordTests(TestCase):
    """reset_password aún no tiene endpoint: se prueba la regla de negocio."""

    def setUp(self):
        self.ana = crear_usuario("ana@test.com")

    def _solicitar(self):
        return UsuarioDAO.reset_password_request("ana@test.com")["token"]

    def test_flujo_completo_cambia_la_contrasena_y_consume_el_token(self):
        token = self._solicitar()

        UsuarioDAO.reset_password(token, "ClaveRestablecida1")

        self.ana.refresh_from_db()
        self.assertTrue(self.ana.check_password("ClaveRestablecida1"))
        self.assertFalse(self.ana.check_password(PASSWORD))
        self.assertIsNone(self.ana.reset_password_token)
        self.assertIsNone(self.ana.reset_password_expires_at)

    def test_el_token_es_de_un_solo_uso(self):
        token = self._solicitar()
        UsuarioDAO.reset_password(token, "ClaveRestablecida1")

        with self.assertRaises(DatosInvalidos_400):
            UsuarioDAO.reset_password(token, "OtraClaveDistinta2")

    def test_token_vencido_es_rechazado_y_no_cambia_la_contrasena(self):
        token = self._solicitar()
        User.objects.filter(pk=self.ana.pk).update(
            reset_password_expires_at=timezone.now() - timedelta(minutes=1)
        )

        with self.assertRaises(DatosInvalidos_400):
            UsuarioDAO.reset_password(token, "ClaveRestablecida1")

        self.ana.refresh_from_db()
        self.assertTrue(self.ana.check_password(PASSWORD))

    def test_el_token_dura_una_hora(self):
        info = UsuarioDAO.reset_password_request("ana@test.com")
        restante = info["expires_at"] - timezone.now()

        self.assertGreater(restante, timedelta(minutes=59))
        self.assertLessEqual(restante, timedelta(hours=1))

    def test_token_con_formato_invalido(self):
        with self.assertRaises(DatosInvalidos_400):
            UsuarioDAO.reset_password("esto-no-es-un-uuid", "ClaveRestablecida1")

    def test_token_inexistente(self):
        with self.assertRaises(DatosInvalidos_400):
            UsuarioDAO.reset_password(str(uuid.uuid4()), "ClaveRestablecida1")

    def test_contrasena_nueva_invalida_no_consume_el_token(self):
        token = self._solicitar()

        for password in ("", "corta"):
            with self.subTest(password=password), self.assertRaises(DatosInvalidos_400):
                UsuarioDAO.reset_password(token, password)

        UsuarioDAO.reset_password(token, "ClaveRestablecida1")  # el token sigue vivo

    def test_solicitar_un_nuevo_token_invalida_el_anterior(self):
        primero = self._solicitar()
        segundo = self._solicitar()

        with self.assertRaises(DatosInvalidos_400):
            UsuarioDAO.reset_password(primero, "ClaveRestablecida1")
        UsuarioDAO.reset_password(segundo, "ClaveRestablecida1")


class UsuarioDAOFallosDeBaseDeDatosTests(TestCase):
    """
    Si la base de datos falla, el DAO traduce el error (409 o 500) y no deja
    escapar excepciones crudas de Django.
    """

    def setUp(self):
        self.ana = crear_usuario("ana@test.com")

    def _falla_save(self, error=DatabaseError):
        return patch.object(User, "save", side_effect=error)

    def test_crear_usuario(self):
        with self._falla_save(IntegrityError), self.assertRaises(ConflictoUsuario_409):
            UsuarioDAO.crear_usuario("n@test.com", "ClaveSegura1", "N", "U")

        with self._falla_save(DatabaseError), self.assertRaises(ErrorInternoServidor_500):
            UsuarioDAO.crear_usuario("n@test.com", "ClaveSegura1", "N", "U")

    def test_actualizar_usuario(self):
        with self._falla_save(IntegrityError), self.assertRaises(ConflictoUsuario_409):
            UsuarioDAO.actualizar_usuario(self.ana.id, {"first_name": "X"})

        with self._falla_save(DatabaseError), self.assertRaises(ErrorInternoServidor_500):
            UsuarioDAO.actualizar_usuario(self.ana.id, {"first_name": "X"})

    def test_cambios_de_estado(self):
        acciones = {
            "eliminar_usuario": UsuarioDAO.eliminar_usuario,
            "desactivar_usuario": UsuarioDAO.desactivar_usuario,
        }
        for nombre, accion in acciones.items():
            with self.subTest(accion=nombre), self._falla_save(), \
                    self.assertRaises(ErrorInternoServidor_500):
                accion(self.ana.id)

        self.ana.is_active = False
        self.ana.save()
        acciones = {
            "activar_usuario": UsuarioDAO.activar_usuario,
            "restaurar_usuario": UsuarioDAO.restaurar_usuario,
        }
        for nombre, accion in acciones.items():
            with self.subTest(accion=nombre), self._falla_save(), \
                    self.assertRaises(ErrorInternoServidor_500):
                accion(self.ana.id)

    def test_actualizar_contrasena(self):
        with self._falla_save(), self.assertRaises(ErrorInternoServidor_500):
            UsuarioDAO.actualizar_contrasena(
                self.ana.id, PASSWORD, "NuevaClave456", "NuevaClave456"
            )

    def test_reset_password_request(self):
        with self._falla_save(), self.assertRaises(ErrorInternoServidor_500):
            UsuarioDAO.reset_password_request("ana@test.com")

    def test_reset_password_al_guardar(self):
        token = UsuarioDAO.reset_password_request("ana@test.com")["token"]

        with self._falla_save(), self.assertRaises(ErrorInternoServidor_500):
            UsuarioDAO.reset_password(token, "ClaveRestablecida1")

    def test_reset_password_al_consultar(self):
        with patch.object(User.objects, "filter", side_effect=DatabaseError), \
                self.assertRaises(ErrorInternoServidor_500):
            UsuarioDAO.reset_password(str(uuid.uuid4()), "ClaveRestablecida1")

    def test_obtener_usuario_por_id(self):
        with patch.object(User.objects, "prefetch_related", side_effect=DatabaseError), \
                self.assertRaises(ErrorInternoServidor_500):
            UsuarioDAO.obtener_usuario_por_id(self.ana.id)

    def test_asignar_roles(self):
        rol = Rol.objects.create(nombre="Vendedor")

        with patch.object(Rol.objects, "filter", side_effect=DatabaseError), \
                self.assertRaises(ErrorInternoServidor_500):
            UsuarioDAO.asignar_roles(self.ana.id, [rol.id])

    def test_quitar_roles(self):
        falso = MagicMock()
        falso.roles.remove.side_effect = DatabaseError

        with patch.object(UsuarioDAO, "obtener_usuario_por_id", return_value=falso), \
                self.assertRaises(ErrorInternoServidor_500):
            UsuarioDAO.quitar_roles(self.ana.id, [1])


TIENE_VERIFICACION_EMAIL = any(
    campo.name == "email_verified" for campo in User._meta.get_fields()
)


@skipUnless(
    TIENE_VERIFICACION_EMAIL,
    "El modelo Usuario aún no define email_verified / email_verified_at",
)
class UsuarioVerificarEmailTests(APITestCase):

    def setUp(self):
        self.url = "/api/usuarios/"
        self.client.force_authenticate(
            user=crear_usuario_con_permisos(["usuarios.verificar_email"], email="g@test.com")
        )
        self.ana = crear_usuario("ana@test.com")

    def test_verificar_email_marca_el_campo_y_la_fecha(self):
        response = self.client.post(f"{self.url}{self.ana.id}/verify_email/")

        self.assertEqual(response.status_code, 200)
        self.ana.refresh_from_db()
        self.assertTrue(self.ana.email_verified)
        self.assertIsNotNone(self.ana.email_verified_at)

    def test_verificar_dos_veces_devuelve_400(self):
        self.client.post(f"{self.url}{self.ana.id}/verify_email/")

        response = self.client.post(f"{self.url}{self.ana.id}/verify_email/")

        self.assertEqual(response.status_code, 400)

    def test_exige_su_propio_permiso(self):
        self.client.force_authenticate(
            user=crear_usuario_con_permisos(["usuarios.ver"], email="x@test.com")
        )

        response = self.client.post(f"{self.url}{self.ana.id}/verify_email/")

        self.assertEqual(response.status_code, 403)

    def test_dao_con_fallo_de_bd_devuelve_500(self):
        with patch.object(User, "save", side_effect=DatabaseError), \
                self.assertRaises(ErrorInternoServidor_500):
            UsuarioDAO.verificar_email(self.ana.id)


class UsuariosErroresDeVistaTests(APITestCase):
    """Ramas de error de las vistas: inexistente (404), traducciones y fallos internos."""

    def setUp(self):
        self.url = "/api/usuarios/"
        self.client.force_authenticate(user=crear_superusuario())
        self.ana = crear_usuario("ana@test.com")
        self.fantasma = uuid.uuid4()

    def _llamar(self, verbo, ruta, cuerpo=None):
        metodo = getattr(self.client, verbo)
        if verbo == "get":
            return metodo(self.url + ruta)
        return metodo(self.url + ruta, cuerpo, format="json")

    def test_acciones_sobre_un_usuario_inexistente_devuelven_404(self):
        datos_put = {"email": "x@test.com", "first_name": "X", "last_name": "Y"}
        casos = [
            ("get", "", None),
            ("put", "", datos_put),
            ("patch", "", {"first_name": "X"}),
            ("delete", "", None),
            ("patch", "activate/", None),
            ("patch", "deactivate/", None),
            ("patch", "restore/", None),
            ("post", "verify_email/", None),
            ("post", "asignar-roles/", {"roles": [1]}),
            ("post", "quitar-roles/", {"roles": [1]}),
        ]
        for verbo, sufijo, cuerpo in casos:
            with self.subTest(verbo=verbo, ruta=sufijo):
                response = self._llamar(verbo, f"{self.fantasma}/{sufijo}", cuerpo)
                self.assertEqual(response.status_code, 404)

    def test_el_servicio_devuelve_fallo_interno_se_traduce_a_500_json(self):
        datos = {"email": "n@test.com", "password": "ClaveSegura1",
                 "first_name": "N", "last_name": "U"}
        datos_put = {"email": "ana@test.com", "first_name": "X", "last_name": "Y"}
        a = f"{self.ana.id}/"
        casos = [
            ("listar_usuarios", "get", "", None),
            ("obtener_usuario", "get", a, None),
            ("crear_usuario", "post", "", datos),
            ("actualizar_usuario", "put", a, datos_put),
            ("actualizar_usuario_parcial", "patch", a, {"first_name": "X"}),
            ("eliminar_usuario", "delete", a, None),
            ("activar_usuario", "patch", a + "activate/", None),
            ("desactivar_usuario", "patch", a + "deactivate/", None),
            ("restaurar_usuario", "patch", a + "restore/", None),
            ("asignar_roles", "post", a + "asignar-roles/", {"roles": [1]}),
            ("quitar_roles", "post", a + "quitar-roles/", {"roles": [1]}),
        ]
        for metodo, verbo, ruta, cuerpo in casos:
            with self.subTest(servicio=metodo), patch.object(
                    usuarioService, metodo, side_effect=ErrorInternoServidor_500("fallo")
            ):
                response = self._llamar(verbo, ruta, cuerpo)
                self.assertEqual(response.status_code, 500)
                self.assertEqual(response.data, {"error": "fallo"})

    def test_cambiar_contrasena_y_solicitar_reset_tambien_devuelven_500_json(self):
        self.client.force_authenticate(user=self.ana)
        cambio = {"current_password": PASSWORD, "new_password": "NuevaClave456",
                  "confirm_password": "NuevaClave456"}

        with patch.object(usuarioService, "cambiar_contrasena",
                          side_effect=ErrorInternoServidor_500("fallo")):
            response = self._llamar("post", f"{self.ana.id}/change-password/", cambio)
        self.assertEqual(response.status_code, 500)

        with patch.object(usuarioService, "solicitar_reset_password",
                          side_effect=ErrorInternoServidor_500("fallo")):
            response = self._llamar("post", "request-password-reset/", {"email": "ana@test.com"})
        self.assertEqual(response.status_code, 500)

    def test_cambiar_contrasena_con_usuario_que_desaparece_devuelve_404(self):
        self.client.force_authenticate(user=self.ana)
        cambio = {"current_password": PASSWORD, "new_password": "NuevaClave456",
                  "confirm_password": "NuevaClave456"}

        with patch.object(usuarioService, "cambiar_contrasena",
                          side_effect=UsuarioNoEncontrado_404("no existe")):
            response = self._llamar("post", f"{self.ana.id}/change-password/", cambio)

        self.assertEqual(response.status_code, 404)

    def test_errores_de_validacion_del_servicio_se_traducen_a_400_y_409(self):
        datos = {"email": "n@test.com", "password": "ClaveSegura1",
                 "first_name": "N", "last_name": "U"}
        datos_put = {"email": "ana@test.com", "first_name": "X", "last_name": "Y"}
        a = f"{self.ana.id}/"
        casos = [
            ("crear_usuario", "post", "", datos, DatosInvalidos_400, 400),
            ("crear_usuario", "post", "", datos, ConflictoUsuario_409, 409),
            ("actualizar_usuario", "put", a, datos_put, DatosInvalidos_400, 400),
            ("actualizar_usuario", "put", a, datos_put, ConflictoUsuario_409, 409),
            ("actualizar_usuario_parcial", "patch", a, {"first_name": "X"}, DatosInvalidos_400, 400),
            ("actualizar_usuario_parcial", "patch", a, {"first_name": "X"}, ConflictoUsuario_409, 409),
        ]
        for metodo, verbo, ruta, cuerpo, excepcion, esperado in casos:
            with self.subTest(servicio=metodo, error=excepcion.__name__), patch.object(
                    usuarioService, metodo, side_effect=excepcion("detalle")
            ):
                self.assertEqual(self._llamar(verbo, ruta, cuerpo).status_code, esperado)

    def test_listar_y_consultar_traducen_401_y_403_del_servicio(self):
        for excepcion, esperado in ((UsuarioNoAutorizado_401, 401), (UsuarioProhibido_403, 403)):
            with self.subTest(error=excepcion.__name__):
                with patch.object(usuarioService, "listar_usuarios", side_effect=excepcion("x")):
                    self.assertEqual(self._llamar("get", "").status_code, esperado)
                with patch.object(usuarioService, "obtener_usuario", side_effect=excepcion("x")):
                    self.assertEqual(self._llamar("get", f"{self.ana.id}/").status_code, esperado)

    def test_verificar_email_no_filtra_el_detalle_de_errores_inesperados(self):
        with patch.object(
                usuarioService, "verificar_email",
                side_effect=RuntimeError("secreto: clave de la base de datos")
        ):
            response = self._llamar("post", f"{self.ana.id}/verify_email/")

        self.assertEqual(response.status_code, 500)
        self.assertNotIn("secreto", str(response.data))

    def test_la_validacion_del_serializer_en_put_y_patch_devuelve_400(self):
        a = f"{self.ana.id}/"

        self.assertEqual(self._llamar("put", a, {}).status_code, 400)
        self.assertEqual(self._llamar("patch", a, {"email": "roto"}).status_code, 400)
        self.assertEqual(self._llamar("post", "", {}).status_code, 400)
        self.assertEqual(self._llamar("post", a + "asignar-roles/", {}).status_code, 400)
        self.assertEqual(self._llamar("post", a + "quitar-roles/", {}).status_code, 400)
        self.assertEqual(self._llamar("post", "request-password-reset/", {}).status_code, 400)