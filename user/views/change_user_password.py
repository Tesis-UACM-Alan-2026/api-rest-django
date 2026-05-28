import logging
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from drf_yasg.utils import swagger_auto_schema
from drf_yasg.openapi import Response
from user.serializers.change_password_serializer import ChangeUserPasswordSerializer
from user.logic import change_password_user
from core.responses import success_response_custom_body, error_response
from user.messages import UPDATED_PASSWORD, UNKNOWN_ERROR
import time, traceback
from rest_framework.exceptions import ValidationError
from rest_framework import status
from user.messages import (
    UPDATED_PASSWORD,
    LACK_OR_INVALID_DATA,
    AUTHENTICATION_REQUIRED,
    UNKNOWN_ERROR,
    INSUFFICIENT_PERMISSIONS,
)


class ChangeUserPasswordView(APIView):
    """
    Vista para permitir a un usuario autenticado cambiar su contraseña.

    Solo usuarios autenticados pueden acceder a esta vista.
    Requiere que el cuerpo de la solicitud contenga la contraseña actual,
    la nueva contraseña y la confirmación de la nueva contraseña.
    """

    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        request_body=ChangeUserPasswordSerializer,
        tags=["Profile"],
        operation_summary="Cambiar contraseña de usuario autenticado",
        operation_description="Permite al usuario autenticado cambiar su propia contraseña. "
        "El usuario debe proporcionar la contraseña actual, la nueva contraseña y su confirmación. "
        "Esta operación no afecta a otros usuarios y requiere autenticación válida.",
        responses={
            200: Response(description=UPDATED_PASSWORD),
            400: Response(description=LACK_OR_INVALID_DATA),
            401: Response(description=AUTHENTICATION_REQUIRED),
            500: Response(description=UNKNOWN_ERROR),
        },
    )
    def post(self, request):
        """
        Maneja solicitudes POST para cambiar la contraseña de un usuario.

        Args:
            request (Request): La solicitud HTTP entrante con los datos de la nueva contraseña.
            user_id (int, opcional): El ID del usuario al que se le desea cambiar la contraseña.

        Returns:
            Response: Una respuesta JSON siguiendo el formato especificado por la función de éxito.

        Excepciones:
            DoesNotExist: Si el UUID del usuario no existe el en sistema.
            ValidationError: Si los datos del serializer son inválidos o las contraseñas no coinciden.
            PermissionDenied: Si el usuario no tiene permisos para cambiar la contraseña especificada.
            NotAuthenticated: Si el usuario ingresa una contraseña incorrecta.
        """
        start_time = time.time()

        serializer = ChangeUserPasswordSerializer(data=request.data)
        try:
            serializer.is_valid(raise_exception=True)
        except ValidationError as e:
            execution_time_ms = int((time.time() - start_time) * 1000)
            return error_response(
                status_code=status.HTTP_400_BAD_REQUEST,
                execution_time_ms=execution_time_ms,
                message=e.detail["message"],
            )
        except Exception as e:
            execution_time_ms = int((time.time() - start_time) * 1000)
            return error_response(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                execution_time_ms=execution_time_ms,
                message=UNKNOWN_ERROR,
            )

        status_code = change_password_user(serializer.validated_data, request.user)
        execution_time_ms = int((time.time() - start_time) * 1000)

        if status_code == status.HTTP_200_OK:

            return success_response_custom_body(
                status_code=status_code,
                execution_time_ms=execution_time_ms,
                request=request,
                response={"message": UPDATED_PASSWORD},
                body={},
            )
        if status_code == status.HTTP_401_UNAUTHORIZED:

            return error_response(
                status_code=status.HTTP_401_UNAUTHORIZED,
                execution_time_ms=execution_time_ms,
                message=AUTHENTICATION_REQUIRED,
            )
        elif status_code == status.HTTP_403_FORBIDDEN:

            return error_response(
                status_code=status.HTTP_403_FORBIDDEN,
                execution_time_ms=execution_time_ms,
                message=INSUFFICIENT_PERMISSIONS,
            )

        else:
            return error_response(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                execution_time_ms=execution_time_ms,
                message=UNKNOWN_ERROR,
            )
