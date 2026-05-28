from rest_framework.serializers import Serializer, CharField, ValidationError
from user.messages import (
    MIN_LENGTH_PASSWORD,
    MAX_LENGTH_PASSWORD,
    REQUIRED_FIELD,
    PASSWORD_DONT_MATCH,
    TYPE_PASSWORD,
    INVALID_PASSWORD_FORMAT,
    NOT_BLANK_FIELD,
    LACK_OR_INVALID_DATA,
)
from user.logic import valid_password


class ChangeUserPasswordSerializer(Serializer):
    """
    Serializer para gestionar el cambio de contraseña de un usuario.

    Este serializer espera los siguientes campos:
    - current_password: La contraseña actual del usuario.
    - new_password: La nueva contraseña deseada.
    - new_password_confirmation: Confirmación de la nueva contraseña.

    Valida que la nueva contraseña y su confirmación coincidan.
    """

    current_password = CharField(
        write_only=True,
        required=True,
        style={"input_type": "password"},
        min_length=8,
        max_length=64,
        allow_blank=False,
        help_text="Contraseña actual del usuario.",
        error_messages={
            "required": REQUIRED_FIELD,
            "min_length": MIN_LENGTH_PASSWORD,
            "max_length": MAX_LENGTH_PASSWORD,
            "invalid": TYPE_PASSWORD,
            "blank": NOT_BLANK_FIELD,
            "null": REQUIRED_FIELD,
        },
    )

    new_password = CharField(
        write_only=True,
        required=True,
        style={"input_type": "password"},
        min_length=8,
        max_length=64,
        allow_blank=False,
        help_text="Nueva contraseña del usuario.",
        error_messages={
            "required": REQUIRED_FIELD,
            "min_length": MIN_LENGTH_PASSWORD,
            "max_length": MAX_LENGTH_PASSWORD,
            "invalid": TYPE_PASSWORD,
            "blank": NOT_BLANK_FIELD,
            "null": REQUIRED_FIELD,
        },
    )

    new_password_confirmation = CharField(
        write_only=True,
        required=True,
        style={"input_type": "password"},
        min_length=8,
        max_length=64,
        allow_blank=False,
        help_text="Confirmación de la nueva contraseña del usuario.",
        error_messages={
            "required": REQUIRED_FIELD,
            "min_length": MIN_LENGTH_PASSWORD,
            "max_length": MAX_LENGTH_PASSWORD,
            "invalid": TYPE_PASSWORD,
            "blank": NOT_BLANK_FIELD,
            "null": REQUIRED_FIELD,
        },
    )

    def is_valid(self, *, raise_exception=False):
        valid = super().is_valid(raise_exception=False)
        if not valid:
            errors = {field: self.errors[field][0] for field in self.errors}

            if raise_exception:
                raise ValidationError(
                    {"message": LACK_OR_INVALID_DATA, "details": errors}
                )

    def validate(self, data):
        """
        Valida que la nueva contraseña y su confirmación sean iguales.

        Args:
            data (dict): Diccionario con los datos validados.

        Returns:
            dict: Datos validados si no hay errores.

        Raises:
            serializers.ValidationError: Si las nuevas contraseñas no coinciden.
        """
        if data["new_password"] != data["new_password_confirmation"]:
            raise ValidationError({"error": [PASSWORD_DONT_MATCH]})

        if not valid_password(data["current_password"]) or not valid_password(
            data["new_password"]
            or not valid_password(data["new_password_confirmation"])
        ):
            raise ValidationError({"error": INVALID_PASSWORD_FORMAT})

        return data
