from rest_framework.test import APITestCase
from django.contrib.auth import get_user_model
from rest_framework import status
from django.urls import reverse
from user.messages import (
    REQUIRED_FIELD,
    MIN_LENGTH_PASSWORD,
    MAX_LENGTH_PASSWORD,
    PASSWORD_DONT_MATCH,
    TYPE_PASSWORD,
    INVALID_PASSWORD_FORMAT,
    CHANGE_PASSWORD_USER_DELETED_INHABILITED,
    INCORRECT_PASSWORD,
    NOT_BLANK_FIELD,
    AUTHENTICATION_REQUIRED,
    LACK_OR_INVALID_DATA,
    AUTHENTICATION_REQUIRED,
    UNKNOWN_ERROR,
    INSUFFICIENT_PERMISSIONS,
)
import uuid

User = get_user_model()


class ChangeUserPasswordTest(APITestCase):
    """
    Tests para el endpoint de cambio de contraseña de un usuario.
    Conjunto de pruebas para el endpoint de cambio de contraseña de un usuario autenticado.
    """

    def setUp(self):
        """
        Configura un usuario autenticado y genera la URL para las pruebas.
        """
        self.email = "user@test.com"
        self.password = "Pa$$w0rd"
        self.user = User.objects.create_user(email=self.email, password=self.password)
        self.url = reverse("change-password")
        self.client.force_authenticate(user=self.user)

    def test_001_change_password_successfully(self):
        """
        Verifica que la contraseña se cambia correctamente cuando los datos son válidos.
        """
        data = {
            "currentPassword": "Pa$$w0rd",
            "newPassword": "newPa$$w0rd",
            "newPasswordConfirmation": "newPa$$w0rd",
        }

        response = self.client.post(self.url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password("newPa$$w0rd"))

    def test_002_change_password_wrong_current_password(self):
        """
        Verifica que se retorne un error si la contraseña actual es incorrecta.
        """
        data = {
            "currentPassword": "wrongPa$$w0rd",
            "newPassword": "newPa$$w0rd",
            "newPasswordConfirmation": "newPa$$w0rd",
        }

        response = self.client.post(self.url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertIn(AUTHENTICATION_REQUIRED, response.json()["message"])

    def test_003_change_password_mismatch(self):
        """
        Verifica que se retorne un error si la nueva contraseña y su confirmación no coinciden.
        """
        data = {
            "currentPassword": "newPa$$w0rd",
            "newPassword": "P4$$w0rd",
            "newPasswordConfirmation": "Pa$$w0rd",
        }

        response = self.client.post(self.url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn(
            LACK_OR_INVALID_DATA,
            response.json()["message"],
        )

    def test_004_data_missing(self):
        """
        Verifica que se retorne un error si faltan todos los datos
        """
        data = {}
        response = self.client.post(self.url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn(LACK_OR_INVALID_DATA, response.json()["message"])

    def test_005_missing_fields(self):
        """
        Verifica que se retorne un error si falta alguno de los campos
        """
        fields = ["currentPassword", "newPassword", "newPasswordConfirmation"]
        data = {
            "currentPassword": "newPa$$w0rd",
            "newPassword": "Pa$$w0rd",
            "newPasswordConfirmation": "Pa$$w0rd",
        }
        for field in fields:
            temporal_data = data.copy()
            temporal_data.pop(field)
            with self.subTest(input=temporal_data):
                response = self.client.post(self.url, temporal_data, format="json")
                self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
                self.assertIn(LACK_OR_INVALID_DATA, response.json()["message"])

    def test_006_null_values(self):
        """
        Verifica que se retorne un error si alguno de los campos es nulo
        """
        fields = ["currentPassword", "newPassword", "newPasswordConfirmation"]
        data = {
            "currentPassword": "newPa$$w0rd",
            "newPassword": "Pa$$w0rd",
            "newPasswordConfirmation": "Pa$$w0rd",
        }
        for field in fields:
            temporal_data = data.copy()
            temporal_data[field] = None
            with self.subTest(input=temporal_data):
                response = self.client.post(self.url, temporal_data, format="json")
                self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
                self.assertIn(LACK_OR_INVALID_DATA, response.json()["message"])

    def test_007_invalid_length_password(self):
        """
        Verifica que se retorne un error si las contraseñas enviadas son menores a 8 caracteres.
        """
        data = {
            "currentPassword": "Pa$$w0",
            "newPassword": "nPa$$w0",
            "newPasswordConfirmation": "nPa$$w0",
        }
        response = self.client.post(self.url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn(LACK_OR_INVALID_DATA, response.json()["message"])

    def test_008_invalid_length_password(self):
        """
        Verifica que se retorne un error si la contraseña enviada es menor a 8 caracteres.
        """
        fields = ["currentPassword", "newPassword", "newPasswordConfirmation"]
        values = ["Pa$$w0", "nPa$$w0", "nPa$$w0"]
        data = {
            "currentPassword": "Pa$$w0rd.",
            "newPassword": "newPa$$w0rd",
            "newPasswordConfirmation": "newPa$$w0rd",
        }
        for field, value in zip(fields, values):
            temporal_data = data.copy()
            temporal_data[field] = value
            with self.subTest(input=temporal_data):
                response = self.client.post(self.url, temporal_data, format="json")
                self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
                self.assertIn(LACK_OR_INVALID_DATA, response.json()["message"])

    def test_009_invalid_length_password(self):
        """
        Verifica que se retorne un error si las contraseñas enviadas son mayores a 64 caracteres.
        """
        letters = ["P", "4", "$", "w", "0", "r", "D"]
        password = "".join([letter * 10 for letter in letters])

        data = {
            "currentPassword": password,
            "newPassword": password,
            "newPasswordConfirmation": password,
        }

        response = self.client.post(self.url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn(LACK_OR_INVALID_DATA, response.json()["message"])

    def test_010_invalid_length_password(self):
        """
        Verifica que se retorne un error si la contraseña enviada es mayor a 64 caracteres.
        """
        letters = ["P", "4", "$", "w", "0", "r", "D"]
        password = "".join([letter * 10 for letter in letters])
        fields = ["currentPassword", "newPassword", "newPasswordConfirmation"]
        data = {
            "currentPassword": "Pa$$w0rd.",
            "newPassword": "newPa$$w0rd",
            "newPasswordConfirmation": "newPa$$w0rd",
        }
        for field in fields:
            temporal_data = data.copy()
            temporal_data[field] = password
            with self.subTest(input=temporal_data):
                response = self.client.post(self.url, temporal_data, format="json")
                self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
                self.assertIn(LACK_OR_INVALID_DATA, response.json()["message"])

    def test_011_invalid_format_password(self):
        """
        Verifica que se retorne un error si las contraseña enviada no es una cadena de caracteres
        """
        data = {
            "currentPassword": True,
            "newPassword": 12345678,
            "newPasswordConfirmation": 12345678,
        }
        response = self.client.post(self.url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn(LACK_OR_INVALID_DATA, response.json()["message"])

    def test_012_invalid_type_password(self):
        """
        Verifica que se retorne un error si la contraseña enviada no es una cadena de caracteres
        """
        data = {
            "currentPassword": "Pa$$w0rd.",
            "newPassword": "newPa$$w0rd",
            "newPasswordConfirmation": "newPa$$w0rd",
        }
        for field in data.keys():
            temporal_data = data.copy()
            temporal_data[field] = True
            response = self.client.post(self.url, temporal_data, format="json")
            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
            self.assertIn(LACK_OR_INVALID_DATA, response.json()["message"])

    def test_013_invalid_format_password(self):
        """
        Verifica que las contraseñas enviadas cumplan el formato especificado
        """
        data = {
            "currentPassword": "12345678",
            "newPassword": "password",
            "newPasswordConfirmation": "password",
        }
        response = self.client.post(self.url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn(LACK_OR_INVALID_DATA, response.json()["message"])

    def test_014_blank_fields(self):
        """
        Verifica que se retorne error si las contraseñas son cadenas vacias.
        """
        data = {"currentPassword": "", "newPassword": "", "newPasswordConfirmation": ""}
        response = self.client.post(self.url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn(LACK_OR_INVALID_DATA, response.json()["message"])

    def test_015_blank_field(self):
        """
        Verifica que la contraseña enviada no sean una cadena vacia.
        """
        data = {
            "currentPassword": "Pa$$w0rd.",
            "newPassword": "newPa$$w0rd",
            "newPasswordConfirmation": "newPa$$w0rd",
        }
        for field in data.keys():
            temporal_data = data.copy()
            temporal_data[field] = ""
            response = self.client.post(self.url, temporal_data, format="json")
            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
            self.assertIn(LACK_OR_INVALID_DATA, response.json()["message"])

    def test_016_change_password_user_disabled(self):
        """
        Verifica que se retorne un error si el usuario está deshabilitado.
        """
        self.user.is_active = False
        self.user.save()

        data = {
            "currentPassword": "Pa$$w0rd",
            "newPassword": "P4$$w0rd.",
            "newPasswordConfirmation": "P4$$w0rd.",
        }

        response = self.client.post(self.url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertIn(INSUFFICIENT_PERMISSIONS, response.json()["message"])

    def test_017_change_password_user_deleted(self):
        """
        Verifica que se retorne un error si el usuario está marcado como eliminado.
        """
        self.user.is_active = True
        self.user.is_deleted = True
        self.user.save()

        data = {
            "currentPassword": "Pa$$w0rd",
            "newPassword": "P4$$w0rd.",
            "newPasswordConfirmation": "P4$$w0rd.",
        }

        response = self.client.post(self.url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertIn(INSUFFICIENT_PERMISSIONS, response.json()["message"])

    def test_018_user_not_authenticated(self):
        """
        Verifica que el usuario este autenticado
        """
        self.client.force_authenticate(user=None)
        data = {
            "currentPassword": "Pa$$w0rd",
            "newPassword": "newPa$$w0rd",
            "newPasswordConfirmation": "newPa$$w0rd",
        }
        response = self.client.post(self.url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertIn(
            "Las credenciales de autenticación no se proveyeron.",
            response.json()["message"],
        )
