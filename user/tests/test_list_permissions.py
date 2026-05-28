"""
Clase creada para testear la endpoint 'listar permisos del sistema' los cuales tiene que manegar 4 test:
    - 200 OK Para el caso de exito.
    - 403 FORBIDDEN Para el caso del usuario no tenga los suficientes permisos. 
"""
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import AccessToken

#Variable global
User = get_user_model()

class TestListPermissions(APITestCase):
    """
    En Django y DRF el setUp se usa para inicializar datos
    """
    def setUp(self):
     self.client = APIClient()
     #Creamos un usuario administrador
     self.admin_user = User.objects.create_superuser(
        email="admin@example.com",
        password="adminpass",
        name="Admin",
        first_lastname="Super",
        curp="CURPADMIN12345678",
        is_deleted=False
        )
    #Crear un usuario sin credenciales suficientes para restaurar usuarios
     self.obrero_user = User.objects.create_user(
        email="obrero@example.com",
        password="obreropass",
        role = "Can add user",
        name="Obrero",
        first_lastname="Perez",
        curp="CURPADMIN13245678",
        is_deleted=False
        )
     #Usario con permisos suficientes
     self.url_list_permission = reverse("permission-list")
    """
    Tester en la sutuación:
    - Listar permisos exitosamente.
    - Estatus: 200.
    - Descripción:
        - El usuario hizo la petición de listar permisos en el sistema con los 
          permisos suficientes.
    """

    def test_list_permission_ok(self):
       token = str(AccessToken.for_user(self.admin_user))

       #Creamos la petición
       response = self.client.get(
           self.url_list_permission,
           HTTP_AUTHORIZATION=f"Bearer {token}",
           format='json'
       )
       #Verificamos lo que nos devolvio con lo que tiene que devolver la respuesta
       self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    """
    Tester en la situación:
        - Usuario no tiene permisos suficientes para obtener la lista de permisos.
        - Estatus:403.
        - Descripción: 
            - Usuario sin permisos suficientes para hacer la petición de listar permisos en el sistema. 
    """
    def test_list_permission_forbidden(self):
        token = str(AccessToken.for_user(self.obrero_user))

        #Creamos la peticón
        response = self.client.get(
                    self.url_list_permission,
                    HTTP_AUTHORIZATION=f"Bearer {token}",
                    format='json'
                )
        #Verificamos lo que nos devolvio con lo que tiene que devolver la respuesta
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)       

    """
    Tester en la situación:
        - Token formado incorrectamente.
        - Estatus:401.
        - Descripción: 
            - El token que se maneja en este caso es uno en cuya formación del token expiro o no esta bien estructurada. 
    """
    def test_invalid_token(self):
        response = self.client.get(
            self.url_list_permission,
            HTTP_AUTHORIZATION="Bearer abc.def.ghi",
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        