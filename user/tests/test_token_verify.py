"""
Clase creada para testear la endpoint 'verificar token' los cuales tiene que manegar 4 test:
    - 200 OK Para el caso de exito.
    - 404 not found para el caso de no encontrar token. 
    - 401 unauthorized  para cuando el token no sea valido (token con bearer).
    - 500 internal server error para cuando el token no este bien formado (token sin bearer). 
"""

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import AccessToken
from user import messages

class TestCustomTokenVerifyView(APITestCase):
    def setUp(self):
        self.url = reverse("token_verify")  # usa el nombre

    """
    Tester en la situación:
        - No se encontro token.
        - Estatus: 400.
        - Descripción:
            - El token no fue encontrado.
    """
    def test_token_not_found(self):
        response = self.client.post(
            self.url,
            data={},  # payload vacio.
            format="json"  # importante para evitar el 415.
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.json().get("message"), messages.TOKEN_NOT_FOUND)

    """
    Tester en la situación:
        - Token se verifico exitosamente.
        - Estatus: 200.
        - Descripción:
            - El token esta bien estructurado.
    """

    def test_valid_token(self):
       User = get_user_model()
       user = User.objects.create_user(email="test@example.com", password="pass1234")
       token = str(AccessToken.for_user(user))

       response = self.client.post(
           self.url,
           data={"email": user.email},
           HTTP_AUTHORIZATION=f"Bearer {token}",
           format='json'
       )
       #$print("Aqui la respuesta: ",response.json())
       self.assertEqual(response.status_code, status.HTTP_200_OK)
        # según tu success_response el message viene en response["message"]
       self.assertEqual(response.json().get("message", {}).get("response", {}).get("message"),messages.VERIFIED_TOKEN)

    """
    Tester en la situación:
        - Token formado incorrectamente.
        - Estatus:401.
        - Descripción: 
            - El token que se maneja en este caso es uno en cuya formación del token expiro o no esta bien estructurada. 
    """
    def test_invalid_token(self):
        response = self.client.post(
            self.url,
            data={},
            HTTP_AUTHORIZATION="Bearer abc.def.ghi",
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        #self.assertEqual(response.json().get("message"), messages.INVALID_TOKEN)
    """
    Tester en la situación:
        - Token formado incorrectamente.
        - Estatus: 500.
        - Descripción: 
            - El token que se maneja en este caso es uno en cuya formación no esta bien estructurada. 
    """

    def test_invalid_header_format(self):
        response = self.client.post(
            self.url,
            data={},
            HTTP_AUTHORIZATION="InvalidHeader",
            format='json'
        )
        print(response.json())
        self.assertEqual(response.status_code,status.HTTP_500_INTERNAL_SERVER_ERROR)
        #self.assertEqual(response.json().get("message"), messages.UNKNOWN_ERROR)