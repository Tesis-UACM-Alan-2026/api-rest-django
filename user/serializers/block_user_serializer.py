from rest_framework import serializers


class BlockUserSerializer(serializers.Serializer):
    """
    Serializador utilizado para validar la entrada al bloquear un usuario.

    Campo requerido:
        - user_id: UUID del usuario a bloquear.
    """
    user_id = serializers.UUIDField(
        help_text="UUID del usuario que se desea bloquear.",
        required=True
    )
