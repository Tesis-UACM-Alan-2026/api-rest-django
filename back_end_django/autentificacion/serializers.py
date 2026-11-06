
import logging

from django.contrib.auth import authenticate
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.exceptions import AuthenticationFailed


logger_auditoria = logging.getLogger("auditoria")


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):

    username_field = "email"

    def validate(self, attrs):
        email = attrs.get("email")
        password = attrs.get("password")

        request = self.context.get("request")

        user = authenticate(
            request=request,
            email=email,
            password=password
        )

        ip = (
            request.META.get("REMOTE_ADDR", "IP desconocida")
            if request else "IP desconocida"
        )

        if user is None:
            logger_auditoria.warning(
                f"[ip:{ip}] [accion:LOGIN_FALLIDO] "
                f"[usuario:{email}] "
                f"[detalle:credenciales incorrectas]"
            )

            raise AuthenticationFailed("Credenciales inválidas.")

        data = super().validate(attrs)

        logger_auditoria.info(
            f"[ip:{ip}] [accion:LOGIN_EXITOSO] "
            f"[usuario:{email}] "
            f"[id:{user.id}]"
        )

        return data
