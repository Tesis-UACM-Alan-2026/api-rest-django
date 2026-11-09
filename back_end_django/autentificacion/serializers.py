from rest_framework import serializers


class LoginSerializer(serializers.Serializer):
    """Credenciales de inicio de sesión."""

    email = serializers.EmailField()
    password = serializers.CharField(
        write_only=True,
        trim_whitespace=False,
        style={"input_type": "password"},
    )


class SesionSerializer(serializers.Serializer):
    """Tokens que se devuelven al iniciar sesión."""

    access = serializers.CharField(read_only=True)
    refresh = serializers.CharField(read_only=True)


class LogoutSerializer(serializers.Serializer):
    """Refresh token que se desea invalidar."""

    refresh = serializers.CharField(write_only=True)


# ---------------------------- Logs ----------------------------
class _LogQuerySerializer(serializers.Serializer):
    limite = serializers.IntegerField(
        required=False, default=100, min_value=1, max_value=1000
    )


class LogAuditoriaQuerySerializer(_LogQuerySerializer):
    usuario = serializers.CharField(required=False, allow_blank=True, max_length=100)
    accion = serializers.CharField(required=False, allow_blank=True, max_length=100)


class LogTecnicoQuerySerializer(_LogQuerySerializer):
    nivel = serializers.CharField(required=False, allow_blank=True, max_length=20)
    modulo = serializers.CharField(required=False, allow_blank=True, max_length=100)


class LogConsultaSerializer(serializers.Serializer):
    total = serializers.IntegerField(read_only=True)
    filtros_aplicados = serializers.DictField(
        child=serializers.CharField(), read_only=True
    )
    entradas = serializers.ListField(child=serializers.CharField(), read_only=True)