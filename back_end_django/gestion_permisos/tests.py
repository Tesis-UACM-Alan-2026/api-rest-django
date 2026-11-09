# gestion_permisos/tests.py

from io import StringIO
from unittest.mock import patch

from django.contrib.auth.models import AnonymousUser
from django.core.management import call_command
from django.db.utils import IntegrityError
from django.test import TestCase
from rest_framework.request import Request
from rest_framework.test import APIRequestFactory, APITestCase

from core.testing import (
    crear_rol_con_permisos,
    crear_superusuario,
    crear_usuario,
    crear_usuario_con_permisos,
)
from gestion_permisos.catalogo import PERMISOS, ROLES_BASE
from gestion_permisos.models import Permiso, Rol
from gestion_permisos.exceptions.permisoExceptions import PermisosError
from gestion_permisos.permissions import HasPermission
from gestion_permisos.views import permisoService

PERMISOS_DE_PERMISOS = ["permisos.ver", "permisos.crear", "permisos.editar", "permisos.eliminar"]
PERMISOS_DE_ROLES = [
    "roles.ver", "roles.crear", "roles.editar", "roles.eliminar",
    "roles.asignar_permisos",
]


# =====================================================================
#                              PERMISOS
# =====================================================================
class PermisosAPITests(APITestCase):

    def setUp(self):
        self.url = "/api/permisos/"
        self.gestor = crear_usuario_con_permisos(PERMISOS_DE_PERMISOS, email="gestor@test.com")
        self.client.force_authenticate(user=self.gestor)

        self.permiso = Permiso.objects.create(
            codename="reportes.ver", nombre="Ver reportes", descripcion="Lectura"
        )

    def test_listar_permisos(self):
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertIn("reportes.ver", [p["codename"] for p in response.data])

    def test_consultar_permiso(self):
        response = self.client.get(f"{self.url}{self.permiso.id}/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["nombre"], "Ver reportes")

    def test_consultar_permiso_inexistente_devuelve_404(self):
        self.assertEqual(self.client.get(f"{self.url}999999/").status_code, 404)

    def test_crear_permiso(self):
        response = self.client.post(
            self.url,
            {"codename": "ventas.ver", "nombre": "Ver ventas"},
            format="json"
        )

        self.assertEqual(response.status_code, 201)
        self.assertTrue(Permiso.objects.filter(codename="ventas.ver").exists())

    def test_crear_permiso_duplicado_devuelve_409(self):
        response = self.client.post(
            self.url,
            {"codename": "REPORTES.VER", "nombre": "Otro"},
            format="json"
        )

        self.assertEqual(response.status_code, 409)

    def test_crear_permiso_sin_codename_devuelve_400(self):
        response = self.client.post(self.url, {"nombre": "Sin codename"}, format="json")

        self.assertEqual(response.status_code, 400)

    def test_put_actualiza_el_permiso(self):
        response = self.client.put(
            f"{self.url}{self.permiso.id}/",
            {"codename": "reportes.ver", "nombre": "Ver reportes (nuevo)"},
            format="json"
        )

        self.assertEqual(response.status_code, 200)
        self.permiso.refresh_from_db()
        self.assertEqual(self.permiso.nombre, "Ver reportes (nuevo)")

    def test_put_con_codename_de_otro_permiso_devuelve_409(self):
        Permiso.objects.create(codename="ventas.ver", nombre="Ver ventas")

        response = self.client.put(
            f"{self.url}{self.permiso.id}/",
            {"codename": "ventas.ver", "nombre": "x"},
            format="json"
        )

        self.assertEqual(response.status_code, 409)

    def test_patch_solo_modifica_los_campos_enviados(self):
        response = self.client.patch(
            f"{self.url}{self.permiso.id}/", {"descripcion": "Nueva"}, format="json"
        )

        self.assertEqual(response.status_code, 200)
        self.permiso.refresh_from_db()
        self.assertEqual(self.permiso.descripcion, "Nueva")
        self.assertEqual(self.permiso.codename, "reportes.ver")

    def test_eliminar_permiso_libre(self):
        response = self.client.delete(f"{self.url}{self.permiso.id}/")

        self.assertEqual(response.status_code, 200)
        self.assertFalse(Permiso.objects.filter(id=self.permiso.id).exists())

    def test_no_se_elimina_un_permiso_asignado_a_un_rol(self):
        rol = Rol.objects.create(nombre="Auditor")
        rol.permisos.add(self.permiso)

        response = self.client.delete(f"{self.url}{self.permiso.id}/")

        self.assertEqual(response.status_code, 409)
        self.assertTrue(Permiso.objects.filter(id=self.permiso.id).exists())


class PermisosAutorizacionTests(APITestCase):

    def setUp(self):
        self.url = "/api/permisos/"

    def test_sin_autenticar_devuelve_401(self):
        self.assertEqual(self.client.get(self.url).status_code, 401)

    def test_usuario_sin_roles_devuelve_403(self):
        self.client.force_authenticate(user=crear_usuario())

        self.assertEqual(self.client.get(self.url).status_code, 403)

    def test_staff_sin_permisos_de_rol_devuelve_403(self):
        """Cambio respecto a IsAdminUser: ser staff ya no basta."""
        self.client.force_authenticate(user=crear_usuario("staff@test.com", is_staff=True))

        self.assertEqual(self.client.get(self.url).status_code, 403)

    def test_permiso_de_lectura_no_permite_crear(self):
        self.client.force_authenticate(user=crear_usuario_con_permisos(["permisos.ver"]))

        self.assertEqual(self.client.get(self.url).status_code, 200)
        self.assertEqual(
            self.client.post(
                self.url, {"codename": "x.y", "nombre": "x"}, format="json"
            ).status_code,
            403
        )

    def test_superusuario_tiene_acceso_total(self):
        self.client.force_authenticate(user=crear_superusuario())

        self.assertEqual(self.client.get(self.url).status_code, 200)


# =====================================================================
#                                ROLES
# =====================================================================
class RolesAPITests(APITestCase):

    def setUp(self):
        self.url = "/api/roles/"
        self.gestor = crear_usuario_con_permisos(PERMISOS_DE_ROLES, email="gestor@test.com")
        self.client.force_authenticate(user=self.gestor)

        self.p1 = Permiso.objects.create(codename="reportes.ver", nombre="Ver reportes")
        self.p2 = Permiso.objects.create(codename="ventas.ver", nombre="Ver ventas")
        self.rol = Rol.objects.create(nombre="Analista", descripcion="Solo análisis")

    def _asignar(self, permisos, rol=None):
        return self.client.post(
            f"{self.url}{(rol or self.rol).id}/asignar-permisos/",
            {"permisos": permisos},
            format="json"
        )

    def _quitar(self, permisos, rol=None):
        return self.client.post(
            f"{self.url}{(rol or self.rol).id}/quitar-permisos/",
            {"permisos": permisos},
            format="json"
        )

    # ----- CRUD -----
    def test_crear_rol_devuelve_permisos_vacios(self):
        response = self.client.post(self.url, {"nombre": "Cajero"}, format="json")

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["permisos"], [])

    def test_crear_rol_duplicado_devuelve_409(self):
        response = self.client.post(self.url, {"nombre": "ANALISTA"}, format="json")

        self.assertEqual(response.status_code, 409)

    def test_listar_y_consultar_roles(self):
        self.rol.permisos.add(self.p1)

        listado = self.client.get(self.url)
        detalle = self.client.get(f"{self.url}{self.rol.id}/")

        self.assertEqual(listado.status_code, 200)
        self.assertEqual(detalle.status_code, 200)
        self.assertEqual(
            [p["codename"] for p in detalle.data["permisos"]], ["reportes.ver"]
        )

    def test_consultar_rol_inexistente_devuelve_404(self):
        self.assertEqual(self.client.get(f"{self.url}999999/").status_code, 404)

    def test_put_y_patch_actualizan_el_rol(self):
        put = self.client.put(
            f"{self.url}{self.rol.id}/", {"nombre": "Analista senior"}, format="json"
        )
        patch = self.client.patch(
            f"{self.url}{self.rol.id}/", {"descripcion": "Nueva"}, format="json"
        )

        self.assertEqual(put.status_code, 200)
        self.assertEqual(patch.status_code, 200)
        self.rol.refresh_from_db()
        self.assertEqual(self.rol.nombre, "Analista senior")
        self.assertEqual(self.rol.descripcion, "Nueva")

    def test_renombrar_a_un_nombre_existente_devuelve_409(self):
        Rol.objects.create(nombre="Cajero")

        response = self.client.patch(
            f"{self.url}{self.rol.id}/", {"nombre": "cajero"}, format="json"
        )

        self.assertEqual(response.status_code, 409)

    # ----- Permisos de un rol -----
    def test_asignar_permisos(self):
        response = self._asignar([self.p1.id, self.p2.id])

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            sorted(p["codename"] for p in response.data["permisos"]),
            ["reportes.ver", "ventas.ver"]
        )

    def test_asignar_dos_veces_es_idempotente(self):
        self._asignar([self.p1.id])
        response = self._asignar([self.p1.id, self.p2.id])

        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.rol.permisos.count(), 2)

    def test_asignar_permiso_inexistente_devuelve_400_y_no_asigna_ninguno(self):
        response = self._asignar([self.p1.id, 999999])

        self.assertEqual(response.status_code, 400)
        self.assertIn("999999", response.data["error"])
        self.assertEqual(self.rol.permisos.count(), 0)

    def test_asignar_a_rol_inexistente_devuelve_404(self):
        response = self.client.post(
            f"{self.url}999999/asignar-permisos/",
            {"permisos": [self.p1.id]},
            format="json"
        )

        self.assertEqual(response.status_code, 404)

    def test_asignar_lista_vacia_o_invalida_devuelve_400(self):
        for cuerpo in ({"permisos": []}, {"permisos": ["a"]}, {"permisos": [0]}, {}):
            with self.subTest(cuerpo=cuerpo):
                response = self.client.post(
                    f"{self.url}{self.rol.id}/asignar-permisos/", cuerpo, format="json"
                )
                self.assertEqual(response.status_code, 400)

    def test_quitar_permisos(self):
        self.rol.permisos.add(self.p1, self.p2)

        response = self._quitar([self.p1.id])

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            [p["codename"] for p in response.data["permisos"]], ["ventas.ver"]
        )

    def test_quitar_un_permiso_que_el_rol_no_tiene_no_falla(self):
        self.assertEqual(self._quitar([self.p1.id]).status_code, 200)

    # ----- Eliminación -----
    def test_eliminar_rol_sin_usuarios(self):
        response = self.client.delete(f"{self.url}{self.rol.id}/")

        self.assertEqual(response.status_code, 200)
        self.assertFalse(Rol.objects.filter(id=self.rol.id).exists())

    def test_no_se_elimina_un_rol_asignado_a_un_usuario(self):
        crear_usuario("ana@test.com").roles.add(self.rol)

        response = self.client.delete(f"{self.url}{self.rol.id}/")

        self.assertEqual(response.status_code, 409)
        self.assertTrue(Rol.objects.filter(id=self.rol.id).exists())

    # ----- Autorización -----
    def test_asignar_permisos_exige_su_propio_permiso(self):
        solo_lectura = crear_usuario_con_permisos(
            ["roles.ver", "roles.editar"], email="lector@test.com"
        )
        self.client.force_authenticate(user=solo_lectura)

        self.assertEqual(self._asignar([self.p1.id]).status_code, 403)
        self.assertEqual(self._quitar([self.p1.id]).status_code, 403)
        self.assertEqual(self.client.get(self.url).status_code, 200)

    def test_cambios_de_permisos_de_un_rol_se_reflejan_en_la_siguiente_peticion(self):
        """El caché de permisos es por petición, no entre peticiones."""
        usuario = crear_usuario_con_permisos(["categorias.ver"], email="ana@test.com")
        self.client.force_authenticate(user=usuario)
        self.assertEqual(self.client.get("/api/categorias/").status_code, 200)

        rol = usuario.roles.first()
        rol.permisos.clear()

        self.assertEqual(self.client.get("/api/categorias/").status_code, 403)


# =====================================================================
#                          HasPermission (unitarias)
# =====================================================================
class _VistaDeAccion:
    """ViewSet de mentira: un permiso por acción."""
    permisos_requeridos = {"list": "cosas.ver", "create": "cosas.crear"}

    def __init__(self, action):
        self.action = action


class _VistaSimple:
    """APIView de mentira: un único permiso."""
    permiso_requerido = "logs.ver_auditoria"


class HasPermissionTests(TestCase):

    def setUp(self):
        self.permiso = HasPermission()
        self.factory = APIRequestFactory()

    def _request(self, usuario):
        request = Request(self.factory.get("/"))
        request.user = usuario
        return request

    def test_anonimo_es_rechazado(self):
        self.assertFalse(
            self.permiso.has_permission(self._request(AnonymousUser()), _VistaDeAccion("list"))
        )

    def test_superusuario_pasa_aunque_la_accion_no_este_declarada(self):
        request = self._request(crear_superusuario())

        self.assertTrue(self.permiso.has_permission(request, _VistaDeAccion("accion_no_declarada")))

    def test_superusuario_inactivo_es_rechazado(self):
        admin = crear_superusuario()
        admin.is_active = False

        self.assertFalse(
            self.permiso.has_permission(self._request(admin), _VistaDeAccion("list"))
        )

    def test_usuario_con_el_permiso_de_la_accion_pasa(self):
        usuario = crear_usuario_con_permisos(["cosas.ver"])

        self.assertTrue(
            self.permiso.has_permission(self._request(usuario), _VistaDeAccion("list"))
        )

    def test_el_permiso_de_otra_accion_no_sirve(self):
        usuario = crear_usuario_con_permisos(["cosas.ver"])

        self.assertFalse(
            self.permiso.has_permission(self._request(usuario), _VistaDeAccion("create"))
        )

    def test_accion_no_declarada_se_deniega_por_defecto(self):
        usuario = crear_usuario_con_permisos(["cosas.ver", "cosas.crear"])

        self.assertFalse(
            self.permiso.has_permission(self._request(usuario), _VistaDeAccion("destroy"))
        )

    def test_usuario_sin_roles_es_rechazado(self):
        self.assertFalse(
            self.permiso.has_permission(self._request(crear_usuario()), _VistaDeAccion("list"))
        )

    def test_apiview_con_permiso_unico(self):
        con_permiso = crear_usuario_con_permisos(["logs.ver_auditoria"], email="a@test.com")
        sin_permiso = crear_usuario_con_permisos(["logs.ver_tecnico"], email="b@test.com")

        self.assertTrue(self.permiso.has_permission(self._request(con_permiso), _VistaSimple()))
        self.assertFalse(self.permiso.has_permission(self._request(sin_permiso), _VistaSimple()))

    def test_permiso_obtenido_por_varios_roles(self):
        usuario = crear_usuario("multi@test.com")
        usuario.roles.add(crear_rol_con_permisos("Rol A", ["cosas.ver"]))
        usuario.roles.add(crear_rol_con_permisos("Rol B", ["cosas.crear"]))
        request = self._request(usuario)

        self.assertTrue(self.permiso.has_permission(request, _VistaDeAccion("list")))
        self.assertTrue(self.permiso.has_permission(request, _VistaDeAccion("create")))

    def test_los_permisos_se_consultan_una_sola_vez_por_peticion(self):
        usuario = crear_usuario_con_permisos(["cosas.ver", "cosas.crear"])
        request = self._request(usuario)

        with self.assertNumQueries(1):
            self.permiso.has_permission(request, _VistaDeAccion("list"))
            self.permiso.has_permission(request, _VistaDeAccion("create"))
            self.permiso.has_permission(request, _VistaDeAccion("list"))


# =====================================================================
#                       Comando sembrar_permisos
# =====================================================================
class SembrarPermisosTests(TestCase):

    def _ejecutar(self):
        salida = StringIO()
        call_command("sembrar_permisos", stdout=salida)
        return salida.getvalue()

    def test_crea_todos_los_permisos_del_catalogo(self):
        self._ejecutar()

        self.assertEqual(Permiso.objects.count(), len(PERMISOS))
        for codename, _, _ in PERMISOS:
            self.assertTrue(Permiso.objects.filter(codename=codename).exists(), codename)

    def test_es_idempotente(self):
        self._ejecutar()
        self._ejecutar()

        self.assertEqual(Permiso.objects.count(), len(PERMISOS))
        self.assertEqual(Rol.objects.count(), len(ROLES_BASE))

    def test_administrador_recibe_todos_los_permisos(self):
        self._ejecutar()

        self.assertEqual(
            Rol.objects.get(nombre="Administrador").permisos.count(), len(PERMISOS)
        )

    def test_consulta_solo_recibe_permisos_de_lectura_y_ninguno_de_logs(self):
        self._ejecutar()

        codenames = set(
            Rol.objects.get(nombre="Consulta").permisos.values_list("codename", flat=True)
        )

        self.assertTrue(codenames)
        self.assertTrue(all(c.endswith(".ver") for c in codenames))
        self.assertFalse(any(c.startswith("logs.") for c in codenames))

    def test_no_quita_permisos_agregados_a_mano(self):
        self._ejecutar()
        extra = Permiso.objects.create(codename="extra.cosa", nombre="Extra")
        Rol.objects.get(nombre="Consulta").permisos.add(extra)

        self._ejecutar()

        self.assertTrue(Rol.objects.get(nombre="Consulta").permisos.filter(id=extra.id).exists())

    def test_el_catalogo_cubre_los_permisos_que_exigen_las_vistas(self):
        """Evita que una vista pida un codename que nunca se siembra."""
        from autentificacion.log_views import LogAuditoriaView, LogTecnicoView
        from gestion_categorias.views import CategoriasViewSet
        from gestion_permisos.views import PermisosViewSet, RolesViewSet
        from gestion_usuarios.views import UsuarioViewSet

        exigidos = set()
        for vista in (CategoriasViewSet, PermisosViewSet, RolesViewSet, UsuarioViewSet):
            exigidos.update(vista.permisos_requeridos.values())
        exigidos.update([LogAuditoriaView.permiso_requerido, LogTecnicoView.permiso_requerido])

        catalogo = {codename for codename, _, _ in PERMISOS}

        self.assertEqual(exigidos - catalogo, set())


# =====================================================================
#          Validaciones, inexistentes y fallos (permisos y roles)
# =====================================================================
class PermisosYRolesErroresTests(APITestCase):

    def setUp(self):
        self.client.force_authenticate(user=crear_superusuario())
        self.permiso = Permiso.objects.create(codename="reportes.ver", nombre="Ver reportes")
        self.rol = Rol.objects.create(nombre="Analista")

    # ----- 404 en operaciones de escritura -----
    def test_modificar_o_eliminar_un_permiso_inexistente_devuelve_404(self):
        url = "/api/permisos/999999/"

        self.assertEqual(
            self.client.put(url, {"codename": "a.b", "nombre": "x"}, format="json").status_code, 404
        )
        self.assertEqual(self.client.patch(url, {"nombre": "x"}, format="json").status_code, 404)
        self.assertEqual(self.client.delete(url).status_code, 404)

    def test_modificar_o_eliminar_un_rol_inexistente_devuelve_404(self):
        url = "/api/roles/999999/"

        self.assertEqual(self.client.put(url, {"nombre": "x"}, format="json").status_code, 404)
        self.assertEqual(self.client.patch(url, {"nombre": "x"}, format="json").status_code, 404)
        self.assertEqual(self.client.delete(url).status_code, 404)

    # ----- validación del serializer -----
    def test_put_y_patch_invalidos_de_permisos_devuelven_400(self):
        url = f"/api/permisos/{self.permiso.id}/"

        self.assertEqual(self.client.put(url, {}, format="json").status_code, 400)
        self.assertEqual(self.client.patch(url, {"codename": ""}, format="json").status_code, 400)

    def test_put_y_patch_invalidos_de_roles_devuelven_400(self):
        url = f"/api/roles/{self.rol.id}/"

        self.assertEqual(self.client.put(url, {}, format="json").status_code, 400)
        self.assertEqual(self.client.patch(url, {"nombre": ""}, format="json").status_code, 400)

    def test_quitar_permisos_con_cuerpo_invalido_devuelve_400(self):
        response = self.client.post(
            f"/api/roles/{self.rol.id}/quitar-permisos/", {"permisos": []}, format="json"
        )

        self.assertEqual(response.status_code, 400)

    def test_quitar_permisos_de_un_rol_inexistente_devuelve_404(self):
        response = self.client.post(
            "/api/roles/999999/quitar-permisos/", {"permisos": [1]}, format="json"
        )

        self.assertEqual(response.status_code, 404)

    # ----- patch con conflicto -----
    def test_patch_de_codename_existente_devuelve_409(self):
        Permiso.objects.create(codename="ventas.ver", nombre="Ver ventas")

        response = self.client.patch(
            f"/api/permisos/{self.permiso.id}/", {"codename": "ventas.ver"}, format="json"
        )

        self.assertEqual(response.status_code, 409)

    # ----- condiciones de carrera: la BD rechaza lo que el DAO dejó pasar -----
    def test_condicion_de_carrera_en_permisos_devuelve_409(self):
        with patch.object(Permiso.objects, "create", side_effect=IntegrityError):
            crear = self.client.post(
                "/api/permisos/", {"codename": "nuevo.ver", "nombre": "x"}, format="json"
            )
        with patch.object(Permiso, "save", side_effect=IntegrityError):
            editar = self.client.patch(
                f"/api/permisos/{self.permiso.id}/", {"nombre": "otro"}, format="json"
            )

        self.assertEqual(crear.status_code, 409)
        self.assertEqual(editar.status_code, 409)

    def test_condicion_de_carrera_en_roles_devuelve_409(self):
        with patch.object(Rol.objects, "create", side_effect=IntegrityError):
            crear = self.client.post("/api/roles/", {"nombre": "Nuevo"}, format="json")
        with patch.object(Rol, "save", side_effect=IntegrityError):
            editar = self.client.patch(
                f"/api/roles/{self.rol.id}/", {"descripcion": "otra"}, format="json"
            )

        self.assertEqual(crear.status_code, 409)
        self.assertEqual(editar.status_code, 409)

    # ----- errores no previstos del módulo -----
    def test_un_error_del_modulo_sin_codigo_asignado_se_traduce_a_500_con_formato(self):
        with patch.object(permisoService, "obtener_permiso", side_effect=PermisosError("falla")):
            response = self.client.get(f"/api/permisos/{self.permiso.id}/")

        self.assertEqual(response.status_code, 500)
        self.assertEqual(response.data, {"error": "falla"})