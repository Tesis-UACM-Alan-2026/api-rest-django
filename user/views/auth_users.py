from rest_framework_simplejwt.tokens import UntypedToken
from rest_framework_simplejwt.exceptions import TokenError, InvalidToken, ExpiredTokenError
from rest_framework_simplejwt.views import TokenObtainPairView
from ..serializers import CustomTokenObtainPairSerializer
from ..serializers import CustomTokenRefreshSerializer
from rest_framework_simplejwt.views import TokenRefreshView
import logging
import time
from user.logic import get_token_pair, verificate_token_refresh
from core.responses import success_response, error_response, empty_data
from rest_framework.response import Response
from rest_framework.throttling import UserRateThrottle
from rest_framework.request import Request
from django.http import HttpRequest
from django.contrib.auth.hashers import make_password
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import UntypedToken
from rest_framework import status
from user import messages
from rest_framework.permissions import IsAuthenticated
from drf_spectacular.utils import extend_schema
from drf_yasg.utils import swagger_auto_schema

from rest_framework.permissions import AllowAny
from rest_framework.authentication import BaseAuthentication
from drf_spectacular.utils import OpenApiResponse, OpenApiExample
from django.conf import settings

logger = logging.getLogger(__name__)

class FakeRequest(HttpRequest):
    """
    Simula un objeto HttpRequest con datos modificados (por ejemplo, datos sanitizados).
    
    Esta clase se utiliza comúnmente para propósitos como logging o construcción
    de respuestas, donde no se desea incluir información sensible como contraseñas.
    Copia los atributos esenciales del request original pero reemplaza el cuerpo (`data`).
    """

    def __init__(self, original_request, new_data):
        """
        Inicializa el objeto FakeRequest con los datos del request original
        y nuevos datos para reemplazar el cuerpo del request.

        Args:
            original_request (HttpRequest): El request original enviado por el cliente.
            new_data (Any): Los datos que reemplazarán a los originales (por ejemplo, datos filtrados).
        """
        super().__init__()
        self.method = original_request.method  # Copia el método HTTP (GET, POST, etc.).
        self.path = original_request.path      # Copia la URL del request original.
        self.GET = original_request.GET        # Copia los parámetros de la URL.
        self.META = original_request.META      # Copia los metadatos (cabeceras, IP, etc.).
        self._data = new_data                  # Guarda los nuevos datos sanitizados.

    @property
    def data(self):
        """
        Devuelve los datos modificados que sustituyen al cuerpo original del request.

        Returns:
            Any: Los datos que se quieren exponer o usar (por ejemplo, sin contraseñas).
        """
        return self._data


@extend_schema(tags=["Auth"])
class CustomTokenObtainPairView(TokenObtainPairView):
    """
    Esta vista reemplaza la vista estándar de obtención de tokens de SimpleJWT,
    utilizando una lógica personalizada definida en la función `getTokenPair`.
    Autentica a un usuario y genera un par de tokens (access y refresh) en las cookies.

    Endpoint:
        POST api/auth/login

    Autenticación:
        None
    
    Permisos:
        correo y contraseña valalidas, usuario no bloqueado y activo.

    Buenas practicas:
        Decoradores Swagger , uso de logger , validación defensiva ,
        respuestas centralizadas , medición  de tiempos .
    """

    throttle_classes = [UserRateThrottle] #manda error por varias peticiones en poco tiempo
    @swagger_auto_schema(
        tags=["Auth"],
        operation_description="Endpoint para iniciar sesión en el sistema. Este endpoint establece en la respuesta HTTP dos cookies seguras: access_token y refresh_token. El access_token permite autenticar las solicitudes al API durante un período corto, mientras que el refresh_token permite obtener nuevos tokens de acceso sin requerir volver a iniciar sesión. Requiere email y contraseña válidos.",
        Response={
            200: " Usuario verificado correctamente." ,
            400: " Solicitud mal formada. ",
            401: " Los datos proporcionados no son válidos. " ,
            403: " Esta acción no está permitida. " ,
            429: " Demasiadas peticiones. " ,
            500: " Error interno . "
        }
    )
    def post(self, request, *args, **kwargs):
        """
        Autentica a un usuario y devuelve sus tokens junto con la información del usuario.
        Args:
            request (HttpRequest): Objeto de solicitud HTTP con las credenciales de autenticación.
        Returns:
            Response:
                200: si la autenticación es exitosa y devuelve los tokens e información del usuario.
                400: si esta mal escrito o faltan campos en la solicitud.
                401: si el email o contraseña son inválidas.
                403: si esta bloqueado.
                429: si se realiza varias peticiones en un periodo corto de tiempo.
                500: si ocurre un error inesperado.
        Raises:
            Exception: Cualquier error inesperado durante la autenticación.
        Buenas prácticas:
            - Medición del tiempo de ejecución del endpoint.
            - Registro (logger) de eventos importantes con datos sensibles ofuscados.
            - Control seguro de cookies para tokens.
        """
        #medir el tiempo que tarda el endpoint en realizar la accion o el error
        start_time = time.time() 
        
        #se modifica el request original para sustituir la contraseña por *****
        sanitized_data = request.data.copy()
        if 'password' in sanitized_data:
            sanitized_data['password'] = "********"
        
        #se crea un nuevo request donde la contraseña ha sido modificada para mostrar en la respuesta
        fake_request = FakeRequest(request, sanitized_data)

        success, result, code = get_token_pair(request)
        if success:
            #trazabilidad en caso de un loggin exitoso
            logger.info("Exito: Solicitud de token para el usuario: %s", fake_request.data)

            tokens = result.get("tokens")
            user_info = result.get("user")
            message = result.get("message")
            response_message = {
                "message": message,
                "data": user_info
            }            
            response  = success_response(status_code=code, 
                                    execution_time_ms=int((time.time() - start_time) * 1000), 
                                    request=fake_request,
                                    response=response_message)
            
            # Establecer tokens como cookies seguras
            response.set_cookie(
                key='access_token',
                value=tokens.get("access"),
                httponly=True,
                #secure=True,  # si se ocupa HTTPS
                samesite='Lax',
                max_age=60 * 60,  # 1 hora
            )

            response.set_cookie(
                key='refresh_token',
                value=tokens.get('refresh'),
                httponly=True,
                #secure=True,  # si se ocupa HTTPS
                samesite='Lax',
                max_age=1 * 24 * 60 * 60,  # 1 dia
            )
            return response
        else:
            logger.info("Error al solicitar de token de acceso para el usuario con email:%s", result.get("email"))
            return error_response(status_code=code,
                                execution_time_ms=int((time.time() - start_time) * 1000),
                                message=result.get("detail")
                                )
        
@extend_schema(tags=["Auth"])        
class CustomTokenRefreshView(TokenRefreshView):
    throttle_classes = [] 
    """
    Esta vista extiende la vista original de SimpleJWT (`TokenRefreshView`)
    y utiliza un serializer personalizado (`CustomTokenRefreshSerializer`)
    y lógica adicional definida en `verificateTokenRefresh`, genera nuevos tokens (access y refresh) en las cookies.

    Endpoint:
        POST /api/token/refresh

    Autenticación:
        token refresh en las cookies.

    Permisos:
        usuario ha iniciado anteriormente sesion.

    Buenas practicas:
        Decoradores Swagger , uso de logger , validación defensiva ,
        respuestas centralizadas , medición de tiempos.
    """

    serializer_class = CustomTokenRefreshSerializer
    @swagger_auto_schema(
        tags=["Auth"],
        operation_description="Este endpoint lee el refresh_token desde la cookie enviada por el cliente y genera un nuevo access_token y refresh_token. Los nuevos token son devueltos en cookies.",
        Response={
            200: " Usuario verificado correctamente." ,
            400: " Solicitud mal formada. ",
            401: " Los datos proporcionados no son válidos. " ,
            403: " Esta acción no está permitida. " ,
            500: " Error interno . "
        }
    )
    def post(self, request):
        """
        Refresca el par de tokens (access y refresh) de un usuario autenticado.
        Args:
            request (HttpRequest): Objeto de solicitud HTTP que contiene el token de refresh.
        Returns:
            Response:
            - 200 si el refresh de tokens es exitoso.
            - 400/401 si el token de refresh es inválido o ha expirado.
            - 403: si esta bloqueado.
            - 500 si ocurre un error inesperado.
        Raises:
            Exception: Cualquier error inesperado durante el proceso.
        Buenas prácticas:
            - Medición del tiempo de ejecución.
            - Registro de logs para trazabilidad de éxito/error.
            - Establecimiento seguro de cookies.
        """
        start_time = time.time()
        success, result, code = verificate_token_refresh(request)
        if success:
            logger.info("Solicitud de token refresh exitosa para el usuario con email:%s", result.get("email"))
            tokens = result.get("tokens")
            message = result.get("message")
            response = success_response(status_code=code, 
                            execution_time_ms=int((time.time() - start_time) * 1000), 
                            request=request,
                            response={
                                "message": message
                            })
            # Establecer tokens como cookies seguras
            response.set_cookie(
                key='access_token',
                value=tokens.get("access"),
                httponly=True,
                #secure=True,  # si se ocupa HTTPS
                samesite='Lax',
                max_age=60 * 60,  # 1 hora
            )

            response.set_cookie(
                key='refresh_token',
                value=tokens.get('refresh'),
                httponly=True,
                #secure=True,  # si se ocupa HTTPS
                samesite='Lax',
                max_age=1 * 24 * 60 * 60,  # 1 dia
            )
            return response
        else:
            logger.info("Error al solicitar de token refresh")
            return error_response(status_code=code,
                                  execution_time_ms=int((time.time() - start_time) * 1000),
                                  message=result.get("detail")
                                  )

class CustomTokenVerifyView(APIView):
    """
    Verifica si un access token JWT enviado por el cliente es válido.

    Endpoint:
        POST /api/token/verify/

    Esta vista verifica la validez del token de acceso JWT enviado en el encabezado
    Authorization. Si el token es válido, retorna un status HTTP 200; si es inválido
    o ha expirado, retorna un status HTTP 401.
    """
    @swagger_auto_schema(
        tags=["Auth"],
        operation_description="Verifica si un access token JWT enviado por el cliente es válido. Retorna un status HTTP 200 si el token es válido o un 401 si el token es inválido o ha expirado.",
    )
    def post(self, request, *args, **kwargs):
        
        start_time = time.time()
        
        auth_header = request.headers.get('Authorization', None)

        #Verificamos que el token de acceso este en el header
        if not auth_header:
            logger.warning(f"{messages.TOKEN_NOT_FOUND} para el usuario con email:%s", request.data.get("email"))
            return empty_data(
                status_code=status.HTTP_404_NOT_FOUND,
                execution_time_ms=int((time.time() - start_time) * 1000),
                message= messages.TOKEN_NOT_FOUND, 
                )

        if auth_header and auth_header.startswith('Bearer '):
            access_token = auth_header.split(' ')[1]
        else:
            logger.error(f"{messages.INVALID_TOKEN} para el usuario con email:%s: {error_token}", request.data.get("email"))
            return error_response(
                status_code=status.HTTP_401_UNAUTHORIZED,
                execution_time_ms=int((time.time() - start_time) * 1000),
                message= messages.INVALID_TOKEN
                )
        
        try:
            
            UntypedToken(access_token)
            logger.info(f"{messages.VERIFIED_TOKEN} para el usuario con email:%s", request.data.get("email"))
            
            response_message = {
                    "message": messages.VERIFIED_TOKEN,
                    }
            #No se le agrega un status code 200 porque es el por defecto en success_response.
            return success_response(
                execution_time_ms=int((time.time() - start_time) * 1000),
                request= request,
                response= response_message,
            )
        except TokenError as error_token:
            
            logger.error(f"{messages.INVALID_TOKEN} para el usuario con email:%s: {error_token}", request.data.get("email"))
            return error_response(
                status_code=status.HTTP_401_UNAUTHORIZED,
                execution_time_ms=int((time.time() - start_time) * 1000),
                message= messages.INVALID_TOKEN
            )
        except Exception as e:
            
            logger.error( messages.VERIFIED_USER + f": {e}", exc_info=True)
            return error_response(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                execution_time_ms=int((time.time() - start_time) * 1000),
                message= messages.UNKNOWN_ERROR
            )
        

class NoAuth(BaseAuthentication):
    def authenticate(self, request):
        return None

@extend_schema(
    tags=["Auth"],
    summary="Obtener clave pública para verificar tokens JWT",
    description=(
        "Devuelve la clave pública RSA usada para verificar tokens JWT "
        "firmados con el algoritmo RS256. Ideal para servicios externos que "
        "requieren validar la firma de tokens emitidos por este backend."
    ),
    responses={
        200: OpenApiResponse(
            description="Clave pública entregada correctamente.",
            examples=[
                OpenApiExample(
                    "Ejemplo de clave pública",
                    value={
                        "public_key": (
                            "-----BEGIN PUBLIC KEY-----\n"
                            "MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEAn...\n"
                            "-----END PUBLIC KEY-----"
                        )
                    },
                ),
            ],
        ),
        500: OpenApiResponse(
            description="Error al obtener la clave pública.",
            examples=[
                OpenApiExample(
                    "Error",
                    value={"detail": "No se pudo obtener la clave pública"},
                ),
            ],
        ),
    }
)
class PublicKeyView(APIView):
    """
    Devuelve la clave pública para verificación de tokens JWT con RS256.

    Endpoint:
        GET /api/auth/public-key/

    No requiere autenticación.
    """

    permission_classes = [AllowAny]
    authentication_classes = [NoAuth]
    @swagger_auto_schema(
        tags=["Auth"],
        operation_description="Devuelve la clave pública para verificación de tokens JWT con RS256.",
    )
    def get(self, request):
        try:
            public_key_path = getattr(settings, "PUBLIC_KEY_PATH", "keys/public.pem")

            with open(public_key_path, "r") as f:
                public_key = f.read()

            return Response({"public_key": public_key}, status=status.HTTP_200_OK)

        except Exception as e:
            logger.error("Error al obtener la clave pública", exc_info=True)
            return Response(
                {"detail": "No se pudo obtener la clave pública"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
