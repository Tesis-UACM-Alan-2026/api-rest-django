
from rest_framework import serializers
from .models import Usuario


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
            field: {"required": False}
            for field in fields
        }


class UsuarioCompletoSerializer(serializers.ModelSerializer):
    """Serializador para actualizar completamente un usuario (PUT)."""

    password = serializers.CharField(
        write_only=True,
        required=False
    )

    class Meta:
        model = Usuario
        fields = [
            "id",
            "email",
            "password",
            "first_name",
            "last_name",
        ]
        read_only_fields = ["id"]

    def update(self, instance, validated_data):
        password = validated_data.pop("password", None)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        if password:
            instance.set_password(password)

        instance.save()
        return instance


class UsuarioContrasenaSerializer(serializers.ModelSerializer):
    """Serializador para actualizar la contraseña."""

    current_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True)
    confirm_password = serializers.CharField(write_only=True)

    class Meta:
        model = Usuario
        fields = [
            "current_password",
            "new_password",
            "confirm_password",
        ]

    def validate(self, data):
        if len(data["new_password"]) < 8:
            raise serializers.ValidationError(
                "La nueva contraseña debe contener al menos 8 caracteres."
            )

        if data["new_password"] != data["confirm_password"]:
            raise serializers.ValidationError(
                "Las contraseñas no coinciden."
            )

        return data

    def validate_current_password(self, value):
        user = self.instance

        if user is None or not user.check_password(value):
            raise serializers.ValidationError(
                "La contraseña actual es incorrecta."
            )

        return value

    def update(self, instance, validated_data):
        instance.set_password(validated_data["new_password"])
        instance.save()
        return instance


class PasswordResetRequestSerializer(serializers.Serializer):
    """Serializador para solicitar el restablecimiento de contraseña."""

    email = serializers.EmailField()
