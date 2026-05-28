from rest_framework.test import APITestCase
from rest_framework import status
from django.urls import reverse
from django.contrib.auth import get_user_model
from uuid import uuid4
from user import messages

"""
Test para DELETE /users/{user_id}
"""

User = get_user_model()

class DeleteUserViewTests(APITestCase):
    @classmethod
    def setUpTestData(cls):
        # Administrador
        cls.admin_user = User.objects.create_user(
            email='admin@example.com',
            password='admin1234',
            is_superuser=True,
            is_staff=True,
            is_active=True,
            name='Administrator',
            first_lastname='Test',
            curp='ADMIN123456MDFRNS0'
        )

        # Usuario normal
        cls.normal_user = User.objects.create_user(
            email='user@example.com',
            password='user1234',
            is_superuser=False,
            is_staff=False,
            is_active=True,
            name='User',
            first_lastname='Test',
            curp='USER123456MDFRNS0'
        )

        cls.target_user = User.objects.create_user(
            email='victima@test.com',
            password='victima123',
            is_active=True,
            is_deleted=False,
            name="Víctima",
            first_lastname="Objetivo",
            curp="VICT800101HDFRRN00"
        )

    def setUp(self):
        self.client.force_authenticate(user=self.admin_user)

    def _url(self, user_id):
        return reverse('user-data', args=[str(user_id)])

    def test_delete_user_success(self):
        """
        Eliminacion de un usuario existente y activo
        """
        url=self._url(self.target_user.user_id)
        response = self.client.delete(url)
        data = response.json()

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('message', data)
        self.assertIn('response', data['message'])
        self.assertEqual(
            data['message']['response']['message'],
            'Usuario eliminado exitosamente'
        )

        # Hay que confirmar que el usuarios no esta activo
        #  y esta borrado de manera logica
        self.target_user.refresh_from_db()
        self.assertFalse(self.target_user.is_active)
        self.assertTrue(self.target_user.is_deleted)

    def test_delete_user_not_found(self):
        """
        Intento de eliminar un usuario que no existe
        """
        non_existent_user_id = uuid4()
        url = self._url(non_existent_user_id)
        response = self.client.delete(url)
        data = response.json()

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertIn('message', data)

    def test_delete_user_already_deleted(self):
        """
        Intento de eliminar un usuario que ya fue eliminado
        """
        first_response = self.client.delete(self._url(self.target_user.user_id))
        self.assertEqual(first_response.status_code, status.HTTP_200_OK)

        second_response = self.client.delete(self._url(self.target_user.user_id))
        data = second_response.json()

        self.assertEqual(second_response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertIn('message', data)
        self.assertEqual(data['message'], messages.DELETE_ALREADY)

    def test_delete_user_requires_auth(self):
        """
        Verifica que se requiere autenticación para eliminar un usuario
        """
        self.client.logout()
        url = self._url(self.target_user.user_id)
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_delete_user_forbidden_without_permission(self):
        """
        Verifica que un usuario sin permisos no puede eliminar a otro usuario
        """
        self.client.logout()
        self.client.force_authenticate(user=self.normal_user)
        url = self._url(self.target_user.user_id)
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)