"""
Clase creada para testear la endpoint 'restaurar usuario' los cuales tiene que manegar 4 test:
    - 200 OK Para el caso de exito.
    - 404 not found para el caso de no encontrar token. 
    - 401 unauthorized  para cuando el token no sea valido (token con bearer).
    - 403 Usuario no tiene las creenciales suficientes. 
"""

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework.test import APIClient

#Variable global 
User = get_user_model()
plain_password = "adminpass123"

class TestRestoreUser(APITestCase):
    def setUp(self):
        self.client = APIClient()
        #Crear un usuario administrador para loguearse
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

        # Crear usuario eliminado
        self.deleted_user = User.objects.create_user(
            email="deleted@example.com",
            password="deletedpass",
            name="Deleted",
            first_lastname="User",
            curp="CURPDEL123456789",
            is_deleted=True,
            deleted_at=timezone.now()
        )
        #Usuario eliminado 
        self.deleted_user_two = User.objects.create_user(
            email="deletedtwo@example.com",
            password="deletedtwopass",
            name="deletedtwo",
            first_lastname="Perez",
            curp="CURPADMIN13254678",
            is_deleted=True,
            deleted_at=timezone.now()
        )

        #Usario no eliminado
        self.not_deleted_user = User.objects.create_user(
            email="notDeleted@example.com",
            password="notDeletedpass",
            name="notDeleted",
            first_lastname="UserTwo",
            curp="CURPDEL213456789",
            is_deleted=False,
            deleted_at=None
        )


        #En esta ruta se pasa el ID del usuario eliminado
        self.url_restore_deleted_user = reverse("user-restore", kwargs={"user_id": self.deleted_user.user_id})

        #En esta ruta se pasa el ID del usuario eliminado
        self.url_restore_not_deleted_user = reverse("user-restore", kwargs={"user_id": self.not_deleted_user.user_id})

        #En esta ruta se pasa un ID de un usuario que no existe en la BD.
        id_user_not_found = "00000001-dead-beef-0000-0000deadbe02"
        self.url_user_not_fount = reverse("user-restore", kwargs={"user_id": id_user_not_found})

        #En esta ruta se pasa el ID del usuario eliminado dos
        self.url_restore_deleted_user_two = reverse("user-restore", kwargs={"user_id": self.deleted_user_two.user_id})


    """
    Tester en la sutuación:
    - Restaurar un usuario eliminado.
    - Estatus: 200
    - Descripción:
        - El usuario se restauro correctamente
    """
    def test_restore_user_success(self):
        """
        - force_authenticate
            Simula que las peticiones siguientes vienen autenticadas con ese usuario. 
            Es útil en tests porque evita hacer login o trabajar con tokens. Con esto, 
            cuando tu view consulta request.user, va a recibir self.admin_user.

            No hace hashing de contraseñas ni sesiones reales; 
            sólo inyecta user/auth en las peticiones de prueba.
        """
        
        self.client.force_authenticate(user=self.admin_user)

        # Hacer petición para restaurar usuario
        response = self.client.post(self.url_restore_deleted_user)

        # Validar status HTTP
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        
        """
        - refresh_from_db 
            Recarga ese objeto desde la base de datos para reflejar 
            los cambios que hizo la view. Sin refresh_from_db() compararías valores desactualizados.
        """
        self.deleted_user.refresh_from_db()

        
        """
        - assertFalse:
            Asegura que el flag de eliminación lógica se quitó.
        - assertIsNotNone:
            Comprueba que el endpoint haya puesto la fecha/hora de restauración.
        - assertEqual:
            Verifica que el campo que guarda quién restauró quedó con el user_id del admin que hizo la petición.
        """
        self.assertFalse(self.deleted_user.is_deleted) 
        self.assertIsNotNone(self.deleted_user.restored_at)
        self.assertEqual(self.deleted_user.restored_by_id, self.admin_user.user_id)

    """
    Tester en la sutuación:
    - Restaurar un usuario no eliminado.
    - Estatus: 400
    - Descripción:
        - Se intetanta restaurar un usuario que no esta eliminado, regresando un error 400. 
    """
    def test_restore_user_not_deleted(self): 
        #Forzamos la autentficación.
        self.client.force_authenticate(user=self.admin_user)
        #Solicitamos la restauración con el usuario no eliminado.
        response = self.client.post(self.url_restore_not_deleted_user)
        #Comparamos la respuestas.
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    """
    Tester en la sutuación:
    - Restaurar un usuario no encontrado en la BD.
    - Estatus: 404 
    - Descripción:
        - Se intetanta restaurar un usuario que no se encontro en la BD. 
    """
    def test_restore_user_not_found(self):
        #Forzamos la autentficación.
        self.client.force_authenticate(user=self.admin_user)
         #Solicitamos la restauración con el usuario no eliminado.
        response = self.client.post(self.url_user_not_fount)
        #Comparamos la respuestas.
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    """
    Tester en la sutuación:
    - Restaurar un usuario sin tener los permisos suficientes.
    - Estatus: 403 
    - Descripción:
        - Se intetanta restaurar un usuario sin tener las credenciales suficientes para su restauración. 
    """

    def test_restore_user_insufficient_permissions(self):
        #Forzamos la autentficación.
        self.client.force_authenticate(user=self.obrero_user)
         #Solicitamos la restauración con el usuario no eliminado.
        response = self.client.post(self.url_restore_deleted_user_two)
        #Comparamos la respuestas.
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    """
    Tester en la situación:
        - Token formado incorrectamente.
        - Estatus:401.
        - Descripción: 
            - El token que se maneja en este caso es uno en cuya formación del token expiro o no esta bien estructurada. 
    """
    def test_invalid_token(self):
        #Hacermos la petición.
        response = self.client.post(
            self.url_restore_deleted_user_two,
            HTTP_AUTHORIZATION="Bearer abc.def.ghi",
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        

