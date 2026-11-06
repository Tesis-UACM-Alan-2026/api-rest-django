from decimal import Decimal
from types import SimpleNamespace

from rest_framework.test import APITestCase

from gestion_productos.models import Productos


class ProductoViewSetTestCase(APITestCase):

    def setUp(self):
        # Simular un usuario autenticado para las pruebas.
        usuario = SimpleNamespace(is_authenticated=True)
        self.client.force_authenticate(user=usuario)

        self.url = "/api/productos/products/"

        self.producto = Productos.objects.create(
            nombre="Laptop Lenovo",
            precio=Decimal("12500.00"),
            stock=10,
            categoria=None
        )

    def test_listar_productos(self):
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)

    def test_consultar_producto(self):
        response = self.client.get(
            f"{self.url}{self.producto.id}/"
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["nombre"], "Laptop Lenovo")

    def test_crear_producto(self):
        datos = {
            "nombre": "Mouse Logitech",
            "precio": "450.00",
            "stock": 20,
            "categoria": None
        }

        response = self.client.post(
            self.url,
            datos,
            format="json"
        )

        self.assertEqual(response.status_code, 201)
        self.assertEqual(
            response.data["nombre"],
            "Mouse Logitech"
        )

    def test_actualizar_producto(self):
        datos = {
            "nombre": "Laptop Lenovo ThinkPad",
            "precio": "13500.00",
            "stock": 8,
            "categoria": None
        }

        response = self.client.put(
            f"{self.url}{self.producto.id}/",
            datos,
            format="json"
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.data["nombre"],
            "Laptop Lenovo ThinkPad"
        )

    def test_actualizar_producto_parcialmente(self):
        datos = {"stock": 15}

        response = self.client.patch(
            f"{self.url}{self.producto.id}/",
            datos,
            format="json"
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["stock"], 15)

    def test_buscar_productos(self):
        response = self.client.get(
            f"{self.url}search/?q=Lenovo"
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)

    def test_filtrar_por_precio(self):
        response = self.client.get(
            f"{self.url}filtrar-precio/",
            {
                "precio_min": "10000",
                "precio_max": "15000"
            }
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)

    def test_eliminar_producto(self):
        response = self.client.delete(
            f"{self.url}{self.producto.id}/"
        )

        self.assertEqual(response.status_code, 200)

        self.assertFalse(
            Productos.objects.filter(
                id=self.producto.id
            ).exists()
        )