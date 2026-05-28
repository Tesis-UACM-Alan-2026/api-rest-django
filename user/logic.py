# user/logic.py

from django.shortcuts import get_object_or_404
from django.utils import timezone
from user.models import User
from user import messages
from rest_framework import status
from user.serializers import UserUpdate
from user.serializers import UserSerializer, CustomTokenObtainPairSerializer
from user.serializers import CustomTokenRefreshSerializer
from user.serializers import UserUpdateMe
from rest_framework.exceptions import (
    ValidationError,
    AuthenticationFailed,
    NotFound,
    ParseError,
    PermissionDenied,
    NotAuthenticated,
)
from rest_framework_simplejwt.exceptions import TokenError
from django.core.exceptions import PermissionDenied
from user.serializers import CustomTokenObtainPairSerializer
from rest_framework.exceptions import Throttled
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import RefreshToken
import re
import logging


def bloquear_usuario(user_id, usuario_actual):
    """
    Bloquea un usuario si está activo y retorna un mensaje.

    Args:
        user_id (UUID): ID del usuario a bloquear.
        usuario_actual (User): Usuario que ejecuta el bloqueo.

    Returns:
        Tuple (bool, dict, int): Éxito, cuerpo de respuesta, código HTTP
    """
    user_to_block = get_object_or_404(User, user_id=user_id)

    if not user_to_block.is_active:
        return False, {"detail": messages.BLOCK_ALREADY}, 400

    user_to_block.is_active = False
    user_to_block.blocked_at = timezone.now()
    user_to_block.blocked_by = usuario_actual
    user_to_block.unblocked_at = None
    user_to_block.unblocked_by = None
    user_to_block.save()

    return (
        True,
        {"detail": messages.BLOCK_SUCCESS.format(email=user_to_block.email)},
        200,
    )


def desbloquear_usuario(user_id, usuario_actual):
    """
    Desbloquea un usuario si no esta activo y retorna un mensaje.

    Args:
        - user_id (UUID): ID del usuario a desbloquear
        - usuario_actual (user): Usuario que ejecuta el bloqueo
    Returns:
        Tuple(bool,dict,int): Éxito, cuerpo de respuesta, código HTTP
    """
    user_to_unblock = get_object_or_404(User, user_id=user_id)
    if user_to_unblock.is_active:
        return False, {"detail": messages.UNBLOCK_ALREADY}, 400

    user_to_unblock.is_active = True
    user_to_unblock.unblocked_at = timezone.now()
    user_to_unblock.unblocked_by = usuario_actual
    user_to_unblock.blocked_at = None
    user_to_unblock.blocked_by = None
    user_to_unblock.save()

    return (
        True,
        {"detail": messages.UNBLOCK_SUCCESS.format(email=user_to_unblock.email)},
        200,
    )


def restore_user(user_id, user_responsable):
    """
    Restaurasr un usuario si esta eliminado logicamente y retorna un mensaje.

    Args:
        - user_id (UUID): ID del usuario a restaurar
        - user_responsable (user): Usuario responsable de la restauraración
    Returns:
        Tuple(bool,dict,int): Éxito, cuerpo de respuesta, código HTTP
    """
    
    user_to_restore = get_object_or_404(User,user_id= user_id)
    
    """
    Verificamos que el usuario este eliminado de no estarlo regresamos un status 400.
    """

    if not user_to_restore.is_deleted:
        return False, messages.LACK_OR_INVALID_DATA, 400

    user_to_restore.is_deleted = False
    user_to_restore.restored_at = timezone.now()
    user_to_restore.restored_by = user_responsable
    user_to_restore.save()

    return (
        True,
        {"message": messages.RESTORE_SUCCESS},
        200,
    )


def crear_usuario(data):
    """
    Lógica de negocio para la creación de un nuevo usuario.

    Args:
        data (dict): Datos recibidos desde la solicitud HTTP.

    Returns:
        (bool, dict, int): Éxito, datos o errores, código de estado HTTP.
    """
    serializer = UserSerializer(data=data)
    if serializer.is_valid():
        user = serializer.save()

        return (
            True,
            {
                "message": messages.CREATE_SUCCESS.format(email=user.email),
                "data": serializer.data,
            },
            status.HTTP_201_CREATED,
        )
    else:
        # Mensaje general + errores detallados
        return (
            False,
            {"detail": messages.INVALID_DATA, "errors": serializer.errors},
            status.HTTP_400_BAD_REQUEST,
        )


def actualiza_usuario_parcial(user, data):
    """
    Lógica de negocio para actualizar un usuario parcial.

    Args:
        -user: Id del usuario de tipo UUID.
        -data (dict): Datos recibidos de la solicitud HTTP.

    Returns:
        (bool, dict, int): Éxito, datos o errores, código de estado HTTP.
    """
    serializer = UserUpdate(instance=user, data=data, partial=True)
    if serializer.is_valid():
        user = serializer.save()

        return (
            True,
            {
                "user_id": user.user_id,
                "email": user.email,
                "detail": messages.UPDATE_SUCCESS.format(email=user.email),
            },
            status.HTTP_200_OK,
        )
    else:
        return (
            False,
            {"detail": messages.INVALID_DATA, "errors": serializer.errors},
            status.HTTP_400_BAD_REQUEST,
        )


def update_me_partial(user, data):
    """
    Lógica de negocio para actualizar un usuario parcial.

    Args:
        -user: Id del usuario de tipo UUID.
        -data (dict): Datos recibidos de la solicitud HTTP.

    Returns:
        (bool, dict, int): Éxito, datos o errores, código de estado HTTP.
    """

    serializer = UserUpdateMe(instance=user, data=data, partial=True)
    if serializer.is_valid():
        user = serializer.save()

        return (
            True,
            {
                "user_id": user.user_id,
                "email": user.email,
                "detail": messages.UPDATE_SUCCESS.format(email=user.email),
            },
            status.HTTP_200_OK,
        )
    else:
        return (
            False,
            {"detail": messages.INVALID_DATA, "errors": serializer.errors},
            status.HTTP_400_BAD_REQUEST,
        )


def get_user_by_id(user_id):
    """
    Obtiene toda la información de un usuario en el sistema a partir de su `id`.

    Args:
        user_id (UUID): Identificador único del usuario, que representa la clave primaria del
                        usuario en el sistema.

    Returns:
        User: Objeto `User` correspondiente al `id` proporcionado.

    Raises:
        Http404: Si no se encuentra un usuario con el `id` dado.

    Esta función usa `get_object_or_404` para lanzar automáticamente un error HTTP 404 si
    el usuario no existe. Utilizando una respuesta estándar en vistas API.
    """
    return get_object_or_404(User, user_id=user_id)


def get_token_pair(request):
    """
    Obtiene el par de tokens (access y refresh) para un usuario autenticado.
    Args:
        request (HttpRequest): Objeto de solicitud HTTP con las credenciales de autenticación.
    Returns:
        Tuple:
        - (True, datos del usuario y tokens, 200) si la autenticación es exitosa.
        - (False, mensaje de error, código de estado HTTP) si ocurre un error.
    Raises:
        Throttled: Si se exceden los intentos de autenticación permitidos.
        PermissionDenied: Si el usuario no tiene permisos para autenticarse.
        AuthenticationFailed: Si las credenciales son inválidas.
        ValidationError: Si la solicitud no contiene los campos requeridos.
        Exception: Cualquier error inesperado durante el proceso.
    Buenas prácticas:
        - Validación explícita de errores esperados (throttle, permisos, autenticación, validaciones).
        - Retorno controlado de errores con mensajes claros.
        - Comprobación de eliminación lógica del usuario.
    """
    email = request.data.get("email", None)
    try:
        serializer = CustomTokenObtainPairSerializer(
            data=request.data, context={"request": request}
        )
        # se valida el usuario y se verifica si esta eliminado logicamente antes de obtner los tokens
        user = serializer.get_user_instance(request.data)
        if user.is_deleted:
            return (
                False,
                {
                    "detail": messages.USER_BLOCKED,
                    "errors": {"auth": str(PermissionDenied())},
                },
                status.HTTP_403_FORBIDDEN,
            )
        # se obtienen los tokens
        serializer.is_valid(raise_exception=True)
    except Throttled as e:
        return (
            False,
            {"detail": messages.TOO_MANY_REQUESTS, "errors": {"throttle": str(e)}},
            status.HTTP_429_TOO_MANY_REQUESTS,
        )
    except AuthenticationFailed as e:
        return (
            False,
            {"detail": messages.AUTHENTICATION_REQUIRED, "errors": {"auth": str(e)}},
            status.HTTP_401_UNAUTHORIZED,
        )
    except ValidationError as e:
        return (
            False,
            {"detail": messages.LACK_OR_INVALID_DATA, "errors": {"auth": str(e)}},
            status.HTTP_400_BAD_REQUEST,
        )
    except Exception as e:
        import logging
        logging.exception("Error inesperado durante la autenticación")
        return (
            False,
            {"detail": messages.UNKNOWN_ERROR, "errors": {"exception": str(e)}, "email": email},
            status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    # se obtiene los datos del usuario
    validated_data = serializer.validated_data
    user_info = validated_data.pop("user", {})

    tokens = {
        "access": validated_data.get("access"),
        "refresh": validated_data.get("refresh"),
    }
    return (
        True,
        {"tokens": tokens, "user": user_info, "message": messages.VERIFIED_USER},
        status.HTTP_200_OK,
    )


User = get_user_model()


def verificate_token_refresh(request):
    """
    Valida un token de refresh enviado en las cookies y genera un nuevo par de tokens (access y refresh).
    Args:
        request (HttpRequest): Objeto de solicitud HTTP que debe contener el refresh token en las cookies.
    Returns:
        Tuple:
        - (True, nuevos tokens, 200) si el refresh es exitoso.
        - (False, mensaje de error, código HTTP) si ocurre un error en la validación.
    Raises:
        AuthenticationFailed: Si el token es inválido o expiró.
        ValidationError: Si faltan campos requeridos.
        Exception: Cualquier otro error inesperado.
    Buenas prácticas:
        - Validación de estructura de la petición.
        - Validación segura de tokens.
        - Manejo detallado de errores.
    """

    # se verifica que no se tenga nada en el body de la peticion
    if request.data:
        return (
            False,
            {
                "detail": messages.LACK_OR_INVALID_DATA,
                "errors": {"auth": str(ValidationError())},
            },
            status.HTTP_400_BAD_REQUEST,
        )

    # se obtiene el refresh token de las cookies
    token_refresh = request.COOKIES.get("refresh_token")

    # se verifica que existe algun token
    if token_refresh is None:
        return (
            False,
            {
                "detail": messages.INSUFFICIENT_PERMISSIONS,
                "errors": {"auth": str(PermissionDenied())},
            },
            status.HTTP_403_FORBIDDEN,
        )
    serializer = CustomTokenRefreshSerializer(data={"refresh": token_refresh})
    try:
        # Extraer el user_id del refresh token en caso de que no se obtenga el id del usuario con el refresh token se envia un error 401
        refresh = RefreshToken(token_refresh)
        user_id = refresh.get("user_id")
        user = User.objects.get(user_id=user_id)
        email = user.email

        # se verifica que el usuario este activo
        if not user.is_active:
            return (
                False,
                {
                    "detail": messages.USER_BLOCKED,
                    "errors": {"auth": str(PermissionDenied())},
                },
                status.HTTP_403_FORBIDDEN,
            )
        serializer.is_valid(raise_exception=True)
    except AuthenticationFailed as e:
        return (
            False,
            {"detail": messages.AUTHENTICATION_REQUIRED, "errors": {"auth": str(e)}},
            status.HTTP_401_UNAUTHORIZED,
        )
    except TokenError as e:
        return (
            False,
            {"detail": messages.INVALID_TOKEN, "errors": {"auth": str(e)}},
            status.HTTP_401_UNAUTHORIZED,
        )
    except ValidationError as e:
        return (
            False,
            {
                "detail": messages.LACK_OR_INVALID_DATA,
                "errors": {"auth": str(e)},
            },
            status.HTTP_400_BAD_REQUEST,
        )
    except Exception as e:
        return (
            False,
            {"detail": messages.UNKNOWN_ERROR, "errors": {"exception": str(e)}},
            status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    # se obtienen los nuevos tokens
    validated_data = serializer.validated_data

    tokens = {
        "access": validated_data.get("access"),
        "refresh": validated_data.get("refresh"),
    }
    return (
        True,
        {"tokens": tokens, "message": messages.REFRESH_SUCCESS, "email": email},
        status.HTTP_200_OK,
    )


def delete_user(user_id, usuario_actual):
    """
    Realiza el borrado lógico de un usuario del sistema.

    Args:
        user_id (UUID): ID del usuario a eliminar.
        usuario_actual (User): Usuario que ejecuta la eliminación.

    Returns:
        Tuple (bool, dict, int): Éxito, cuerpo de respuesta, código HTTP
    """

    user = get_object_or_404(
        User, user_id=user_id
    )  # Django maneja el 404 automáticamente

    if user.is_deleted:
        return False, {"detail": messages.DELETE_ALREADY}, status.HTTP_404_NOT_FOUND

    user.is_deleted = True
    user.deleted_at = timezone.now()
    user.deleted_by = usuario_actual
    user.is_active = False
    user.blocked_at = timezone.now()
    user.save()

    return (
        True,
        {
            "user_id": user.user_id,
            "email": user.email,
            "detail": messages.DELETE_SUCCESS.format(email=user.email),
        },
        status.HTTP_200_OK,
    )


def assign_user_role(user_id, role_id, usuario_actual):
    """
    Asigna un nuevo rol a un usuario específico del sistema.

    Args:
        user_id (UUID): ID del usuario al cual se asignará el rol.
        role_id (str): Identificador del rol según RoleChoices.
        usuario_actual (User): Usuario que ejecuta la asignación.

    Returns:
        Tuple (bool, dict, int): Éxito, cuerpo de respuesta, código HTTP
    """
    user = get_object_or_404(User, user_id=user_id)  # Django maneja 404 automáticamente

    if user.is_deleted:
        return False, {"detail": messages.USER_NOT_FOUND.format(uuid=user.user_id)}, status.HTTP_404_NOT_FOUND
    
    if not user.is_active:
        return False, {"detail": messages.LACK_OR_INVALID_DATA}, status.HTTP_400_BAD_REQUEST
    
    user.role = role_id
    user.updated_by = usuario_actual
    user.save()

    return (
        True,
        {
            "user_id": user.user_id,
            "email": user.email,
            "role": role_id,
            "detail": messages.ROLE_ASSIGN_SUCCESS.format(
                role=role_id
            ),
        },
        status.HTTP_200_OK,
    )


def change_password_user(data, user_requesting):
    """
    Lógica de negocio para cambiar la contraseña de un usuario

    Regla de negocio: no se puede cambiar la contraseña de otro usuario.
    Args:
        data (dict): Diccionario con las claves: current_password, new_password, new_password_confirmation
        user_requesting (User): Usuario autenticado que hace la solicitud

    Returns:
        HTTPStatus: Código de estado HTTP
    """
    current_password = data.get("current_password")
    new_password = data.get("new_password")

    user = User.objects.get(pk=user_requesting.user_id)

    if not user.is_active or user.is_deleted:
        return status.HTTP_403_FORBIDDEN

    if not user.check_password(current_password):
        return status.HTTP_401_UNAUTHORIZED

    user.set_password(new_password)
    user.save()

    return status.HTTP_200_OK


def valid_password(password):
    """
    Verifica que una contraseña sea valida.

    Una contraseña es valida cuando tiene al menos 8 caracteres y como máximo 64, debe tener al menos una letra mayuscula,
    una minúscula, un número, un caracter especial y no debe tener caracteres no imprimibles de la tabla ascii.

    Args:
        password (str): Contraseña en texto plano
    Returns:
        bool: Si la contraseña es correcta devuelve True, False en otro caso.
    """

    pattern = re.compile(
        r"^(?=.*[A-Z])(?=.*[a-z])(?=.*\d)(?=.*[^A-Za-z0-9])[!-~]{8,64}$"
    )

    if pattern.fullmatch(password):
        return True
    return False
