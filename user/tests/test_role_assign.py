from rest_framework.test import APITestCase
from rest_framework import status
from django.urls import reverse
from django.contrib.auth import get_user_model
from uuid import uuid4
from user import messages

"""
Test para POST /users/{user_id}/assign-role
"""

User = get_user_model()

class AssignRoleToUser(APITestCase):
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
        return reverse('assign-role-to-user', args=[str(user_id)])
    
    def test_assign_role_success(self):
        url = self._url(self.target_user.user_id)
        payload = [{"role": "Solicitante"}]
        response = self.client.post(url, payload, format='json')
        data = response.json()

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('message', data)
        self.assertIn('response', data['message'])
        self.assertEqual(
            data['message']['response'], messages.ROLE_ASSIGN_SUCCESS.format(role="Solicitante")
        )

    def test_assign_role_requires_auth(self):
        self.client.logout()
        url = self._url(self.target_user.user_id)
        response = self.client.post(url, [{"role": "Solicitante"}], format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_assign_role_forbidden_without_permission(self):
        self.client.logout()
        self.client.force_authenticate(user=self.normal_user)
        url = self._url(self.target_user.user_id)
        response = self.client.post(url, [{"role": "Solicitante"}], format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_assign_role_user_not_found(self):
        uid = uuid4()
        url = self._url(uid)
        response = self.client.post(url, [{"role": "Solicitante"}], format='json')
        data = response.json()

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertIn('message', data)

        self.assertEqual(data['message'], messages.USER_NOT_FOUND.format(uuid=str(uid)))

    def test_assign_role_invalid_payload(self):
        url = self._url(self.target_user.user_id)
        response = self.client.post(url, [{}], format='json')
        data = response.json()

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('message', data)

    def test_assign_role_invalid_role(self):
        """
        Intenta asignar un rol inexistente que debe fallar con 400
        """
        url = self._url(self.target_user.user_id)
        payload = [{"role": "Inexistente"}]
        response = self.client.post(url, payload, format='json')
        data = response.json()

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('message', data)

    def test_assign_multiple_roles_not_allowed(self):
        """
        Intenta asignar multiples roles en una sola llamada debe fallar con 400
        """
        url = self._url(self.target_user.user_id)
        payload = [{"role": "Solicitante"}, {"role": "Administrador"}]
        response = self.client.post(url, payload, format='json')
        data = response.json()

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('message', data)

    def test_assign_role_user_deleted(self):
        """
        No debe poder asignarse rol a un usuario eliminado logicamente
        Debe responder 404
        """
        self.target_user.is_deleted = True
        self.target_user.save()

        url = self._url(self.target_user.user_id)
        payload = [{"role": "Solicitante"}]
        response = self.client.post(url, payload, format='json')
        data = response.json()

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertIn('message', data)

    def test_assign_role_user_inactivate(self):
        """
        No debe poder asignar rol a un usuario desactivado
        Se espera 400 por conflicto de estado
        """
        self.target_user.is_active = False
        self.target_user.save()

        url = self._url(self.target_user.user_id)
        payload = [{"role": "Solicitante"}]
        response = self.client.post(url, payload, format='json')
        data = response.json()

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('message', data)
        self.assertEqual(data['message'], messages.LACK_OR_INVALID_DATA)