"""
Módulo de respuestas estándar para la API.

Proporciona funciones utilitarias para generar respuestas HTTP consistentes
en formato JSON, usadas en vistas para representar tanto respuestas exitosas
como errores de forma uniforme.

Estructura de respuesta exitosa:
{
    "statusCode": status_code,
    "executionTimeMs": execution_time_ms,
    "timeStamp": timestamp,
    "message": {
        "headers": headers,
        "request": request,
        "response": response
    }
}

Estructura de respuesta de error:
{
    "statusCode": status_code,
    "executionTimeMs": execution_time_ms,
    "timeStamp": timestamp,
    "message": message
}
"""

import json
import logging
import traceback
from datetime import datetime
from http import HTTPStatus

from django.http import JsonResponse
from rest_framework.utils.serializer_helpers import ReturnDict, ReturnList

from user import messages

logger = logging.getLogger(__name__)


def to_camel(snake_str):
    """
    Convierte un string de snake_case a camelCase.

    Args:
        snake_str (str): Cadena en formato snake_case.

    Returns:
        str: Cadena en formato camelCase.
    """
    parts = snake_str.split('_')
    return parts[0] + ''.join(word.capitalize() for word in parts[1:])


def camelize_keys(obj):
    """
    Convierte recursivamente todas las claves de un diccionario (o lista de diccionarios) a camelCase.

    Args:
        obj (dict | list): Objeto con claves en snake_case.

    Returns:
        dict | list: Objeto con claves convertidas a camelCase.
    """
    if isinstance(obj, dict):
        return {to_camel(k): camelize_keys(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [camelize_keys(item) for item in obj]
    else:
        return obj


def safe_data(data, fields_to_mask=("password,signing_password,signing_password_confirmation,'password_confirmation'")):
    """
    Convierte datos complejos como ReturnDict o ReturnList en estructuras JSON serializables.

    Args:
        data (any): Objeto potencialmente no serializable.

    Returns:
        any: Objeto serializable.
    """
    if isinstance(data, (ReturnDict, ReturnList)):
        return json.loads(json.dumps(data, default=str))
    if isinstance(data, dict):
        cleaned = {}
        for k, v in data.items():
            if k in fields_to_mask:
                cleaned[k] = "********"
            else:
                cleaned[k] = safe_data(v, fields_to_mask)
        return cleaned
    
    if isinstance(data, list):
        return [safe_data(item) for item in data]
    try:
        return json.loads(json.dumps(data, default=str))
    except Exception:
        return str(data)


def success_response(status_code=HTTPStatus.OK, execution_time_ms=None, request=None, response=None):
    """
    Genera una respuesta exitosa con metadatos de la solicitud.

    Args:
        status_code (int): Código de estado HTTP.
        execution_time_ms (float): Tiempo de ejecución en milisegundos.
        request (HttpRequest): Solicitud recibida.
        response (any): Contenido de la respuesta.

    Returns:
        JsonResponse: Respuesta en formato estandarizado.
    """
    timestamp = datetime.now().isoformat()
    data = {
        "statusCode": status_code,
        "executionTimeMs": execution_time_ms,
        "timestamp": timestamp,
        "message": {
            "headers": {
                "Host": request.META.get("HTTP_HOST"),
                "User-Agent": request.META.get("HTTP_USER_AGENT"),
                "Accept": request.META.get("HTTP_ACCEPT"),
                "Content-Type": request.META.get("CONTENT_TYPE"),
            },
            "request": {
                "method": request.method,
                "path": request.path,
                "query": dict(request.GET),
                "body": safe_data(request.data),
            },
            "response": response
        },
    }
    return JsonResponse(camelize_keys(data), status=status_code, safe=False, json_dumps_params={"default": str})


def get_list_success_response(status_code=HTTPStatus.OK, execution_time_ms=None, request=None, response_message=None, pagination=None):
    """
    Genera una respuesta exitosa para una lista de resultados con paginación.

    Args:
        status_code (int): Código de estado HTTP.
        execution_time_ms (float): Tiempo de ejecución en milisegundos.
        request (HttpRequest): Solicitud recibida.
        response_message (list | dict): Lista de resultados.
        pagination (dict): Información de paginación.

    Returns:
        JsonResponse: Respuesta en formato estandarizado.
    """
    try:
        timestamp = datetime.now().isoformat()
        default_pagination = {
            "page": 1,
            "perPage": 10,
            "totalPages": 1,
            "totalItems": len(response_message) if response_message else 0
        }
        pagination_data = pagination or default_pagination

        response = {
            "statusCode": status_code,
            "executionTimeMs": execution_time_ms,
            "timestamp": timestamp,
            "message": {
                "headers": {
                    "Host": request.META.get('HTTP_HOST'),
                    "User-Agent": request.META.get('HTTP_USER_AGENT'),
                    "Accept": request.META.get('HTTP_ACCEPT'),
                    "Content-Type": request.META.get('CONTENT_TYPE'),
                },
                "request": {
                    "method": request.method,
                    "path": request.path,
                    "query": dict(request.GET),
                    "body": safe_data(request.data)
                },
                "response": {
                    "message": messages.USER_LIST_SUCCESS,
                    "data": safe_data(response_message),
                    "pagination": pagination_data
                }
            }
        }

        return JsonResponse(camelize_keys(response), status=status_code, safe=False, json_dumps_params={"default": str})
    except Exception as e:
        logger.error("Error en get_list_success_response: %s", traceback.format_exc())
        return JsonResponse({"error": str(e)}, status=500)


def success_response_custom_body(status_code=HTTPStatus.OK, execution_time_ms=None, request=None, response=None, body=None):
    """
    Genera una respuesta exitosa personalizada, omitiendo algunos datos del cliente si es necesario.

    Args:
        status_code (int): Código de estado HTTP.
        execution_time_ms (float): Tiempo de ejecución.
        request (HttpRequest): Objeto de solicitud.
        response (any): Contenido de la respuesta.
        body (dict): Cuerpo personalizado en la sección request.

    Returns:
        JsonResponse: Respuesta JSON estructurada.
    """
    timestamp = datetime.now().isoformat()
    data = {
        "statusCode": status_code,
        "executionTimeMs": execution_time_ms,
        "timestamp": timestamp,
        "message": {
            "headers": {
                "Host": request.META.get("HTTP_HOST"),
                "User-Agent": request.META.get("HTTP_USER_AGENT"),
                "Accept": request.META.get("HTTP_ACCEPT"),
                "Content-Type": request.META.get("CONTENT_TYPE"),
            },
            "request": {
                "method": request.method,
                "path": request.path,
                "query": dict(request.GET),
                "body": body,
            },
            "response": response,
        },
    }
    return JsonResponse(camelize_keys(data), status=status_code, safe=False, json_dumps_params={"default": str})


def error_response(status_code=HTTPStatus.INTERNAL_SERVER_ERROR, execution_time_ms=None, message=None):
    """
    Genera una respuesta para errores genéricos.

    Args:
        status_code (int): Código HTTP.
        execution_time_ms (float): Tiempo de ejecución.
        message (str): Mensaje descriptivo del error.

    Returns:
        JsonResponse: Objeto de respuesta con error.
    """
    timestamp = datetime.now().isoformat()
    response = {
        "statusCode": status_code,
        "executionTimeMs": execution_time_ms,
        "timestamp": timestamp,
        "message": message,
    }

    return JsonResponse(camelize_keys(response), status=status_code, safe=False, json_dumps_params={"default": str})


def user_not_found(status_code=HTTPStatus.NOT_FOUND, execution_time_ms=None, message=None):
    """
    Genera una respuesta estandarizada cuando no se encuentra un usuario.

    Args:
        status_code (int): Código HTTP (por defecto 404).
        execution_time_ms (float): Tiempo de ejecución.
        message (str): Mensaje descriptivo.

    Returns:
        JsonResponse: Objeto de respuesta para error 404.
    """
    timestamp = datetime.now().isoformat()
    response = {
        "statusCode": status_code,
        "executionTimeMs": execution_time_ms,
        "timestamp": timestamp,
        "message": message
    }

    return JsonResponse(camelize_keys(response), status=status_code, safe=False, json_dumps_params={"default": str})


def empty_data(status_code=HTTPStatus.BAD_REQUEST, execution_time_ms=None, message=None):
    """
    Genera una respuesta de error cuando un campo obligatorio está vacío.

    Args:
        status_code (int): Código HTTP (por defecto 400).
        execution_time_ms (float): Tiempo de ejecución.
        message (str): Mensaje de error.

    Returns:
        JsonResponse: Objeto de respuesta con error 400.
    """
    timestamp = datetime.now().isoformat()
    response = {
        "statusCode": status_code,
        "executionTimeMs": execution_time_ms,
        "timestamp": timestamp,
        "message": message
    }

    return JsonResponse(camelize_keys(response), status=status_code, safe=False, json_dumps_params={"default": str})


def get_request_body(request):
    """
    Extrae el cuerpo de una solicitud HTTP como un diccionario, dependiendo del Content-Type.

    Args:
        request (HttpRequest): Objeto de solicitud.

    Returns:
        dict: Contenido del cuerpo parseado como diccionario.
    """
    if request.method in ['POST', 'PUT', 'PATCH']:
        if request.content_type == 'application/json':
            try:
                return json.loads(request.body.decode('utf-8'))
            except Exception:
                return {}
        else:
            return request.POST.dict()
    return {}
