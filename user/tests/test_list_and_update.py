from django.test import TestCase
from rest_framework.test import APITestCase
from rest_framework import status
from django.urls import reverse
from django.contrib.auth import get_user_model

"""
Test para PATCH /users/{$user_id}.
"""

User = get_user_model()

class UserViewTests(APITestCase):
    @classmethod
    def setUpTestData(cls):
        # Usuario con permisos
        cls.admin_user = User.objects.create_user(
            email='admin@gmail.com',
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
        self.client.force_authenticate(user=self.admin_user)

    def test_list_users_success(self):
        url = reverse('user-list')
        response = self.client.get(url)
        response_data = response.json()
    
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
        self.assertIn('message', response_data)
        self.assertIsInstance(response_data['message'], dict)
        self.assertIn('response', response_data['message'])
        self.assertIn('data', response_data['message']['response'])
        self.assertEqual(
        response_data['message']['response']['message'], 
        'Lista de usuarios recuperada exitosamente.'
    )

    def test_list_users_requires_auth(self):
        self.client.logout()
        url = reverse('user-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_list_users_filter_is_active_true(self):
        url = reverse('user-list') + '?isActive=true'
        response = self.client.get(url)
        response_data = response.json()
    
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        users_data = response_data['message']['response']['data']  # Ruta corregida
        self.assertTrue(all(user['isActive'] is True for user in users_data))