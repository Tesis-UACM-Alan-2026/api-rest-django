# tests/test_auth_refresh.py
import pytest
from rest_framework.test import APITestCase
from rest_framework.test import APIClient
from django.urls import reverse
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from user import messages
from django.contrib.auth import get_user_model
from unittest.mock import patch
from rest_framework.exceptions import ValidationError, AuthenticationFailed
from rest_framework_simplejwt.exceptions import TokenError

User = get_user_model()

@pytest.mark.django_db
class TokenRefreshTestCase(APITestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            email="test@example.com",
            password="testpassword123",
            is_active=True,
        )
        self.refresh = RefreshToken.for_user(self.user)
        self.access_token = str(self.refresh.access_token)
        self.refresh_token = str(self.refresh)
        self.url = reverse("token_refresh") 

    def test_refresh_token_successful(self):
        """Debe devolver 200 OK con nuevos tokens si el refresh token es válido (en cookies)"""
        self.client.cookies['refresh_token'] = self.refresh_token

        response = self.client.post(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access_token', response.cookies)
        self.assertIn('refresh_token', response.cookies)
        self.assertEqual(response.json()["message"]['response']['message'], messages.REFRESH_SUCCESS)

    def test_refresh_token_missing_cookie(self):
        """Debe devolver 403 si no se envía refresh_token en cookies"""
        response = self.client.post(self.url)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(response.json()['message'], messages.INSUFFICIENT_PERMISSIONS)

    def test_refresh_token_invalid_token(self):
        """Debe devolver 401 si el token en cookie es inválido"""
        self.client.cookies['refresh_token'] = "token_invalido"

        response = self.client.post(self.url)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(response.json()['message'], messages.INVALID_TOKEN)

    def test_refresh_token_inactive_user(self):
        """Debe devolver 403 si el usuario está inactivo"""
        self.user.is_active = False
        self.user.save()
        self.client.cookies['refresh_token'] = self.refresh_token

        response = self.client.post(self.url)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(response.json()['message'], messages.USER_BLOCKED)

    def test_refresh_token_with_data_should_return_400(self):
        """Debe devolver 400 si se envian datos en la peticion """
        # Preparar datos inválidos que no deberían enviarse en esta petición
        invalid_data = {
            "email": "ejemplo@email.com",
            "password": "cualquiervalor"
        }

        # Hacer la petición POST con datos en el body
        response = self.client.post(self.url, data=invalid_data, format='json')

        # Verificar respuesta
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn(messages.LACK_OR_INVALID_DATA, response.json()["message"])

    @patch('user.serializers.custom_token_serializer.CustomTokenRefreshSerializer.is_valid', side_effect=ValidationError())
    def test_login_internal_validation_error_returns_400(self, mock_is_valid):
        """Debe de falla y entra a la except ValidationError en logic"""
        self.client.cookies['refresh_token'] = self.refresh_token

        response = self.client.post(self.url)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn(messages.LACK_OR_INVALID_DATA, response.json()["message"])

    @patch('user.serializers.custom_token_serializer.CustomTokenRefreshSerializer.is_valid', side_effect=Exception("Unexpected error"))
    def test_login_internal_server_error_returns_500(self, mock_is_valid):
        """Debe de falla y entrar a la except Exception en logic"""
        self.client.cookies['refresh_token'] = self.refresh_token  # o un dummy válido

        response = self.client.post(self.url)

        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        self.assertIn(messages.UNKNOWN_ERROR, response.json()["message"])  # Mensaje según tu catálogo


    @patch('user.serializers.custom_token_serializer.CustomTokenRefreshSerializer.validate')
    def test_login_serializer_validate_unexpected_exception_500(self, mock_validate):
        """Debe falla y entrar al except Exception en serializer"""
        mock_validate.side_effect = Exception("Falló dentro de validate()")
        self.client.cookies['refresh_token'] = self.refresh_token 
        response = self.client.post(self.url)

        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        self.assertIn(messages.UNKNOWN_ERROR, response.json()["message"])


    @patch('rest_framework_simplejwt.serializers.TokenRefreshSerializer.validate')
    def test_login_serializer_authentication_failed_401(self, mock_validate):
        """debe de fallar y entrar al except AuthenticationFailed de serializer"""
        mock_validate.side_effect = AuthenticationFailed("Token inválido o expirado.")
        self.client.cookies['refresh_token'] = self.refresh_token 
        response = self.client.post(self.url)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertIn(messages.AUTHENTICATION_REQUIRED, response.json()["message"])

    @patch('rest_framework_simplejwt.serializers.TokenRefreshSerializer.validate')
    def test_login_serializer_validation_error_400(self, mock_validate):
        """debe de fallar y entrar al except ValidationError de serializer"""
        mock_validate.side_effect = ValidationError("falta campos")
        self.client.cookies['refresh_token'] = self.refresh_token 
        response = self.client.post(self.url)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn(messages.LACK_OR_INVALID_DATA, response.json()["message"])
    
    @patch('rest_framework_simplejwt.serializers.TokenRefreshSerializer.validate')
    def test_login_serializer_token_error_401(self, mock_validate):
        """debe de fallar y entrar al except TokenError de serializer"""
        mock_validate.side_effect = TokenError("token incorrecto")
        self.client.cookies['refresh_token'] = self.refresh_token 
        response = self.client.post(self.url)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertIn(messages.INVALID_TOKEN, response.json()["message"])