from types import SimpleNamespace

from rest_framework.test import APITestCase

from gestion_categorias.models import Categoria
from gestion_productos.models import Productos


class CategoriaViewSetTestCase(APITestCase):
    """Pruebas de integración para el módulo de categorías."""

    def setUp(self):
        usuario = SimpleNamespace(is_authenticated=True)
        self.client.force_authenticate(user=usuario)

        self.url = "/api/categorias/categories/"

        self.categoria = Categoria.objects.create(
            nombre="Electrónica",
            descripcion="Productos electrónicos"
        )

    def test_listar_categorias(self):
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)

    def test_consultar_categoria(self):
        response = self.client.get(
            f"{self.url}{self.categoria.id}/"
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["nombre"], "Electrónica")

    def test_consultar_categoria_inexistente(self):
        response = self.client.get(
            f"{self.url}999999/"
        )

        self.assertEqual(response.status_code, 404)

    def test_crear_categoria(self):
        datos = {
            "nombre": "Computación",
            "descripcion": "Equipos y accesorios de cómputo"
        }

        response = self.client.post(
            self.url,
            datos,
            format="json"
        )

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["nombre"], "Computación")

    def test_rechazar_categoria_duplicada(self):
        datos = {
            "nombre": "Electrónica",
            "descripcion": "Categoría duplicada"
        }

        response = self.client.post(
            self.url,
            datos,
            format="json"
        )

        self.assertEqual(response.status_code, 400)

    def test_actualizar_categoria(self):
        datos = {
            "nombre": "Electrónica y tecnología",
            "descripcion": "Equipos tecnológicos"
        }

        response = self.client.put(
            f"{self.url}{self.categoria.id}/",
            datos,
            format="json"
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.data["nombre"],
            "Electrónica y tecnología"
        )

    def test_actualizar_categoria_parcialmente(self):
        datos = {
            "descripcion": "Descripción actualizada"
        }

        response = self.client.patch(
            f"{self.url}{self.categoria.id}/",
            datos,
            format="json"
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.data["nombre"],
            "Electrónica"
        )
        self.assertEqual(
            response.data["descripcion"],
            "Descripción actualizada"
        )

    def test_eliminar_categoria(self):
        response = self.client.delete(
            f"{self.url}{self.categoria.id}/"
        )

        self.assertEqual(response.status_code, 200)

        self.assertFalse(
            Categoria.objects.filter(
                id=self.categoria.id
            ).exists()
        )

    def test_no_eliminar_categoria_con_productos(self):
        Productos.objects.create(
            nombre="Laptop Lenovo",
            precio="12500.00",
            stock=10,
            categoria=self.categoria
        )

        response = self.client.delete(
            f"{self.url}{self.categoria.id}/"
        )

        self.assertEqual(response.status_code, 409)

        self.assertTrue(
            Categoria.objects.filter(
                id=self.categoria.id
            ).exists()
        )