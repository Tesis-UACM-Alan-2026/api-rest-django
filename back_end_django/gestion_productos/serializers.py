# gestion_productos/serializers.py

from rest_framework import serializers
from .models import Productos


class ProductoCompletoSerializer(serializers.ModelSerializer):

    class Meta:
        model = Productos
        fields = [
            "id",
            "nombre",
            "precio",
            "stock",
            "categoria",
        ]
        read_only_fields = ["id"]


class ProductoParcialSerializer(serializers.ModelSerializer):

    class Meta:
        model = Productos
        fields = [
            "nombre",
            "precio",
            "stock",
            "categoria",
        ]
        extra_kwargs = {
            campo: {"required": False}
            for campo in fields
        }
