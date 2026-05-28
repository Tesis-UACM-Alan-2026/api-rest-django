from django.test import TestCase
from rest_framework.test import APITestCase
from rest_framework import status
from django.urls import reverse
from django.contrib.auth import get_user_model
from uuid import uuid4, UUID

"""
Test para el endpoint PATCH /users/{$user_id}.
"""

User = get_user_model()

class TestUserUpdatePartial(APITestCase):
    @classmethod
    def setUpTestData(cls):
        # Usuario con permisos
        cls.admin_user = User.objects.create_user(
            email='luis@gmail.com',
            password='pedro1234',
            is_superuser=True,
            is_staff=True,
            is_active=True,
            name="Admin",
            first_lastname="Test",
            curp="ADMIN123456MDFRNS0"
        )

        # Usuario normal
        cls.regular_user = User.objects.create_user(
            email='user@test.com',
            password='user123',
            is_active=True,
            name="Juan",
            first_lastname="Pérez",
            curp="PEPJ800101HDFRRN00"
        )

    def setUp(self):
        self.client.force_authenticate(user=self.admin_user)  # Autenticar al admin

    def test_update_partial_user_success(self):
        url = reverse('user-data', args=[str(self.regular_user.user_id)])
        patch_data = {"name": "PEDRO"}
        response = self.client.patch(url, patch_data, format='json')
        response_data = response.json() 
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('message', response_data)
    
        self.assertEqual(
            response_data['message']['response'],
            "Usuario actualizado correctamente."
        )

    def test_update_partial_user_not_found(self):
      
        non_existent_uuid = uuid4()
        url = reverse('user-data', args=[str(non_existent_uuid)])
        response = self.client.patch(url, {"name": "Desconocido"}, format='json')
        response_data = response.json()
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertIn('message', response_data)