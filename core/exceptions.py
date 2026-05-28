from rest_framework.views import exception_handler
from rest_framework.exceptions import (
    ParseError,
    AuthenticationFailed,
    NotAuthenticated,
    PermissionDenied,
    NotFound,
    ValidationError,
)
from django.http import JsonResponse
from rest_framework import status
from datetime import datetime


def custom_exception_handler(exc, context):
    """
    Manejador global de excepciones personalizado para estandarizar errores
    y devolver respuestas con un único formato.

    Args:
        exc (Exception): La excepción que fue lanzada.
        context (dict): Contexto de la ejecución en el que ocurrió la excepción,
                        incluyendo la vista y el request (`{'view': view, 'request': request}`).

    Returns:
        Response | JsonResponse:
            - Un objeto `Response` de DRF con formato estándar si la excepción es manejada por DRF.
            - Un objeto `JsonResponse` genérico (código 500) si no se puede manejar.

    Retorna una respuesta con la siguiente estructura:
        {
            "statusCode":status_code,
            "executionTimeMs": None,
            "timeStamp":timestamp,
            "message":message
        }
    """


def custom_exception_handler(exc, context):
    """
    Manejador global de excepciones personalizado para estandarizar errores.
    """
    response = exception_handler(exc, context)

    timestamp = datetime.now().isoformat()

    if response is not None:
        if isinstance(exc, (ParseError, ValidationError)):
            message = exc.detail
            status_code = status.HTTP_400_BAD_REQUEST
        elif isinstance(exc, (AuthenticationFailed, NotAuthenticated)):
            message = exc.detail
            status_code = status.HTTP_401_UNAUTHORIZED
        elif isinstance(exc, PermissionDenied):
            message = exc.detail
            status_code = status.HTTP_403_FORBIDDEN
        elif isinstance(exc, NotFound):
            message = exc.detail
            status_code = status.HTTP_404_NOT_FOUND
        else:
            message = response.data
            status_code = response.status_code
        response.data = {
            "statusCode": status_code,
            "executionTimeMs": None,
            "timeStamp": timestamp,
            "message": message,
        }

        return response

    # Si no fue manejado por DRF, responde genéricamente
    return JsonResponse(
        {
            "statusCode": status.HTTP_500_INTERNAL_SERVER_ERROR,
            "executionTimeMs": None,
            "timeStamp": timestamp,
            "message": "Error interno del servidor",
        },
        status=status.HTTP_500_INTERNAL_SERVER_ERROR,
    )
