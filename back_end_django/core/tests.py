# core/tests.py

import logging

from django.test import RequestFactory, SimpleTestCase

from core.utils import auditar, obtener_ip


class ObtenerIpTests(SimpleTestCase):

    def setUp(self):
        self.factory = RequestFactory()

    def test_usa_remote_addr_por_defecto(self):
        request = self.factory.get("/", REMOTE_ADDR="10.0.0.5")

        self.assertEqual(obtener_ip(request), "10.0.0.5")

    def test_prefiere_x_forwarded_for_y_toma_la_primera_ip(self):
        request = self.factory.get(
            "/",
            HTTP_X_FORWARDED_FOR="203.0.113.7, 10.0.0.1",
            REMOTE_ADDR="10.0.0.1",
        )

        self.assertEqual(obtener_ip(request), "203.0.113.7")

    def test_sin_ip_devuelve_ip_desconocida(self):
        request = self.factory.get("/")
        del request.META["REMOTE_ADDR"]

        self.assertEqual(obtener_ip(request), "IP desconocida")


class AuditarTests(SimpleTestCase):

    class _Request:
        user = "admin@test.com"

    def test_formato_con_request(self):
        with self.assertLogs("auditoria", level="INFO") as cm:
            auditar("1.2.3.4", "CREAR_USUARIO", self._Request(), id_afectado=7)

        mensaje = cm.records[0].getMessage()
        self.assertEqual(cm.records[0].levelno, logging.INFO)
        self.assertIn("[ip:1.2.3.4]", mensaje)
        self.assertIn("[accion:CREAR_USUARIO]", mensaje)
        self.assertIn("[realizado_por:admin@test.com]", mensaje)
        self.assertIn("[id_afectado:7]", mensaje)

    def test_sin_request_no_incluye_realizado_por(self):
        with self.assertLogs("auditoria", level="INFO") as cm:
            auditar("1.2.3.4", "LOGIN_EXITOSO", None, usuario="ana@test.com")

        mensaje = cm.records[0].getMessage()
        self.assertNotIn("realizado_por", mensaje)
        self.assertIn("[usuario:ana@test.com]", mensaje)

    def test_nivel_warning(self):
        with self.assertLogs("auditoria", level="WARNING") as cm:
            auditar("1.2.3.4", "LOGIN_FALLIDO", None, nivel=logging.WARNING)

        self.assertEqual(cm.records[0].levelno, logging.WARNING)

    def test_saltos_de_linea_no_pueden_falsificar_otra_entrada(self):
        with self.assertLogs("auditoria", level="INFO") as cm:
            auditar(
                "1.2.3.4", "LOGIN_FALLIDO", None,
                usuario="x\n[accion:LOGIN_EXITOSO]\r\nmas"
            )

        self.assertEqual(len(cm.records), 1)
        self.assertNotIn("\n", cm.records[0].getMessage())
        self.assertNotIn("\r", cm.records[0].getMessage())