from rest_framework import serializers
from .models import Permiso, Rol


class PermisoSerializer(serializers.ModelSerializer):

    class Meta:
        model = Permiso
        fields = [
            "id",
            "codename",
            "nombre",
            "descripcion",
        ]
        read_only_fields = ["id"]
        # La unicidad del codename la valida el DAO (responde 409).
        extra_kwargs = {
            "codename": {"validators": []}
        }


class RolSerializer(serializers.ModelSerializer):
    """
    En escritura solo se usan nombre y descripcion; los permisos se
    gestionan con los endpoints asignar-permisos / quitar-permisos.
    """

    permisos = PermisoSerializer(many=True, read_only=True)

    class Meta:
        model = Rol
        fields = [
            "id",
            "nombre",
            "descripcion",
            "permisos",
        ]
        read_only_fields = ["id"]
        # La unicidad del nombre la valida el DAO (responde 409).
        extra_kwargs = {
            "nombre": {"validators": []}
        }


class RolPermisosSerializer(serializers.Serializer):
    """Lista de ids de permisos para asignar o quitar de un rol."""

    permisos = serializers.ListField(
        child=serializers.IntegerField(min_value=1),
        allow_empty=False
    )