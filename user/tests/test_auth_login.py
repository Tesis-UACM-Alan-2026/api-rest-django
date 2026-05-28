# tests/test_auth_login.py
import pytest
from rest_framework.test import APIClient
from rest_framework.test import APITestCase
from django.contrib.auth import get_user_model
from rest_framework import status
from django.urls import reverse
import json
from unittest.mock import patch
from rest_framework.exceptions import Throttled, PermissionDenied, ValidationError, AuthenticationFailed
from user import messages

User = get_user_model()

@pytest.mark.django_db
class TokenObtainPairTest(APITestCase):
    def setUp(self):
        self.client = APIClient()
        self.password = "SafePass123!"
        self.user = User.objects.create_user(
            email="test@example.com",
            password=self.password,
            name="Test",
            first_lastname="User",
            is_active=True,
        )

    def test_successful_login(self):
    #test cuando se ingresa bien al sistema 
        url = reverse('token_obtain_pair')  
        response = self.client.post(url, {
            "email": self.user.email,
            "password": self.password
        }, format='json')
        
        response_json = json.loads(response.content)
        #verifica que se devuelva un status_code 200 (exito)
        self.assertEqual(response.status_code, 200)
        #se verifica que exista el access_token
        self.assertIn("access_token", response.cookies)
        #se verifica que exista el refresh_token
        self.assertIn("refresh_token", response.cookies)
        #se verifica que en la respuesta se tenga el mismo email del usuario
        self.assertEqual(response_json["message"]["response"]["data"]["email"], self.user.email)

        # --- Verificar trazabilidad ---
        # Refrescar usuario desde la base de datos
        self.user.refresh_from_db()

        # Verificar que se haya actualizado last_login
        self.assertIsNotNone(self.user.last_login)

        # Verificar que la IP fue guardada (puedes usar una IP dummy aquí)
        self.assertIsNotNone(self.user.last_login_IP)
        self.assertTrue(len(self.user.last_login_IP) > 0)

    def test_login_with_invalid_password(self):
    # test cuando la contraseña es incorrecta
        url = reverse('token_obtain_pair')  
        response = self.client.post(url, {
            "email": self.user.email,
            "password": "WrongPass"
        }, format='json')

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertIn(messages.AUTHENTICATION_REQUIRED, response.json()["message"])

    def test_login_missing_fields_returns_400(self):
    #test cuando faltan datos en el body
        url = reverse('token_obtain_pair')  
        response = self.client.post(url, {}, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn(messages.LACK_OR_INVALID_DATA, response.json()["message"])
    
    def test_login_with_inactive_user(self):
    #test de usuario inactivo 
        self.user.is_active = False
        self.user.save()
        url = reverse('token_obtain_pair')  
        response = self.client.post(url, {
            "email": self.user.email,
            "password": self.password
        }, format='json')

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertIn(messages.AUTHENTICATION_REQUIRED, response.json()["message"])

    def test_login_denied_if_user_is_deleted(self):
    #test de usuario esta eliminado logicamente
        # Marcar usuario como eliminado
        self.user.is_deleted = True
        self.user.save()

        # Guardar valores actuales de trazabilidad
        original_last_login = self.user.last_login
        original_last_login_ip = self.user.last_login_IP

        # Ejecutar login
        url = reverse('token_obtain_pair')
        response = self.client.post(url, {
            "email": self.user.email,
            "password": self.password
        }, format='json')

        # Verificar que regresa 403 Forbidden
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        # Verificar mensaje
        self.assertEqual(response.json()["message"], messages.USER_BLOCKED)

        # Verificar que NO se devolvieron tokens
        self.assertNotIn("access_token", response.cookies)
        self.assertNotIn("refresh_token", response.cookies)

        # Verificar que trazabilidad no se modificó
        self.user.refresh_from_db()
        self.assertEqual(self.user.last_login, original_last_login)
        self.assertEqual(self.user.last_login_IP, original_last_login_ip)

    @patch('user.serializers.custom_token_serializer.CustomTokenObtainPairSerializer.is_valid', side_effect=Throttled())
    def test_login_throttled_returns_429(self, mock_is_valid):
    #test si se realiza varias peticiones (logic)
        url = reverse('token_obtain_pair')
        response = self.client.post(url, {
            "email": self.user.email,
            "password": self.password
        }, format='json')

        self.assertEqual(response.status_code, status.HTTP_429_TOO_MANY_REQUESTS)
        self.assertIn(messages.TOO_MANY_REQUESTS, response.json()["message"])

    @patch('user.serializers.custom_token_serializer.CustomTokenObtainPairSerializer.is_valid', side_effect=Exception("Unexpected error"))
    def test_login_internal_server_error_returns_500(self, mock_is_valid):
    #test de error interno (logic)
        url = reverse('token_obtain_pair')
        response = self.client.post(url, {
            "email": self.user.email,
            "password": self.password
        }, format='json')

        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        self.assertIn(messages.UNKNOWN_ERROR, response.json()["message"])  # Mensaje según tu catálogo


    @patch('user.serializers.custom_token_serializer.CustomTokenObtainPairSerializer.validate')
    def test_login_serializer_validate_unexpected_exception_500(self, mock_validate):
    #test serializer error 500
        mock_validate.side_effect = Exception("Falló dentro de validate()")

        url = reverse('token_obtain_pair')
        response = self.client.post(url, {
            "email": self.user.email,
            "password": self.password
        }, format='json')

        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        self.assertIn(messages.UNKNOWN_ERROR, response.json()["message"])


    @patch('rest_framework_simplejwt.serializers.TokenObtainPairSerializer.validate')
    def test_login_serializer_authentication_failed_401(self, mock_validate):
    #test serializer error 401
        mock_validate.side_effect = AuthenticationFailed()
        
        url = reverse('token_obtain_pair')
        response = self.client.post(url, {
            "email": self.user.email,
            "password": self.password
        }, format='json')

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertIn(messages.AUTHENTICATION_REQUIRED, response.json()["message"])

    @patch('rest_framework_simplejwt.serializers.TokenObtainPairSerializer.validate')
    def test_login_serializer_validation_error_400(self, mock_validate):
    #test serializer error 400
        mock_validate.side_effect = ValidationError()
        
        url = reverse('token_obtain_pair')
        response = self.client.post(url, {
            "email": self.user.email,
            "password": self.password
        }, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn(messages.LACK_OR_INVALID_DATA, response.json()["message"])





