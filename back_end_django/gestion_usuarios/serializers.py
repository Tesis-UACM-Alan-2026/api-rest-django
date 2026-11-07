from rest_framework import serializers
from .models import Usuario


class RolResumenSerializer(serializers.Serializer):
    """Representación resumida de un rol dentro de un usuario."""

    id = serializers.IntegerField(read_only=True)
    nombre = serializers.CharField(read_only=True)


class UsuarioParcialSerializer(serializers.ModelSerializer):
    """Serializador para actualizar parcialmente un usuario (PATCH)."""

    class Meta:
        model = Usuario
        fields = [
            "email",
            "first_name",
            "last_name",
        ]
        extra_kwargs = {
            # La unicidad del email la valida el DAO (responde 409)
            "email": {"required": False, "validators": []},
            "first_name": {"required": False},
            "last_name": {"required": False},
        }


class UsuarioCompletoSerializer(serializers.ModelSerializer):
    """
    Serializador para crear (POST), actualizar completamente (PUT)
    y representar un usuario. La contraseña es solo de escritura.
    """

    password = serializers.CharField(
        write_only=True,
        required=False,
        min_length=8,
        trim_whitespace=False,
        style={"input_type": "password"},
    )

    roles = RolResumenSerializer(many=True, read_only=True)

    class Meta:
        model = Usuario
        fields = [
            "id",
            "email",
            "password",
            "first_name",
            "last_name",
            "roles",
        ]
        read_only_fields = ["id"]
        extra_kwargs = {
            # La unicidad del email la valida el DAO (responde 409)
            "email": {"validators": []},
        }


class UsuarioContrasenaSerializer(serializers.Serializer):
    """
    Serializador para cambiar la contraseña.
    La verificación de la contraseña actual la realiza el DAO.
    """

    current_password = serializers.CharField(
        write_only=True,
        trim_whitespace=False,
        style={"input_type": "password"},
    )
    new_password = serializers.CharField(
        write_only=True,
        min_length=8,
        trim_whitespace=False,
        style={"input_type": "password"},
    )
    confirm_password = serializers.CharField(
        write_only=True,
        trim_whitespace=False,
        style={"input_type": "password"},
    )

    def validate(self, data):
        if data["new_password"] != data["confirm_password"]:
            raise serializers.ValidationError(
                "Las contraseñas no coinciden."
            )

        if data["new_password"] == data["current_password"]:
            raise serializers.ValidationError(
                "La nueva contraseña debe ser distinta de la actual."
            )

        return data


class PasswordResetRequestSerializer(serializers.Serializer):
    """Serializador para solicitar el restablecimiento de contraseña."""

    email = serializers.EmailField()


class UsuarioRolesSerializer(serializers.Serializer):
    """Lista de ids de roles para asignar o quitar de un usuario."""

    roles = serializers.ListField(
        child=serializers.IntegerField(min_value=1),
        allow_empty=False
    )