##############Codigo 24########################################################
from rest_framework import serializers
from .models import Usuario


class UsuarioParcialSerializer(serializers.ModelSerializer):
    """Serializador para actualizar parcialmente un usuario (PATCH)."""

    class Meta:
        model = Usuario
        fields = [
            'username',
            'password',
            'date_of_birth',
            'first_name',
            'last_name',
            'email'
        ]
        extra_kwargs = {
            field: {'required': False}
            for field in fields
        }

    @staticmethod
    def validar_username(username):
        """Valida que el username no tenga más de 20 caracteres."""
        if len(username) > 20:
            raise serializers.ValidationError(
                "El nombre de usuario no puede tener más de 20 caracteres."
            )
        return username
#########Codigo 39########################################################
class UsuarioCompletoSerializer(serializers.ModelSerializer):
    """Serializador para actualizar completamente un usuario (PUT)."""

    class Meta:
        model = Usuario
        fields = ["id","username", "password", "date_of_birth", "first_name", "last_name", "email"]
        extra_kwargs = {
            "password": {"write_only": True}
        }

    def validate_username(self, username):
        if len(username) > 20:
            raise serializers.ValidationError(
                "El nombre de usuario no puede tener más de 20 caracteres."
            )
        return username
class UsuarioContrasenaSerializer(serializers.ModelSerializer):
    """Serializador para actualizar la contraseña."""

    current_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True)
    confirm_password = serializers.CharField(write_only=True)

    class Meta:
        model = Usuario
        fields = ["current_password", "new_password", "confirm_password"]

    def validate(self, data):
        if len(data["new_password"]) < 8:
            raise serializers.ValidationError(
                "La nueva contraseña debe contener al menos 8 caracteres."
            )

        if data["new_password"] != data["confirm_password"]:
            raise serializers.ValidationError("Las contraseñas no coinciden.")

        return data
#######codigo 42########################################################
class PasswordResetRequestSerializer(serializers.Serializer):
    """Serializador para solicitar el restablecimiento de contraseña."""
    email = serializers.EmailField()