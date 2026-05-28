from rest_framework import serializers
from django.contrib.auth.models import Group
from user.choices import RoleChoices
import datetime 

class RoleCreateSerializer(serializers.Serializer):
    """
    Serializador para crear un nuevo rol (grupo) en el sistema.

    Campos:
    - name (str): Nombre único del rol a crear.
    """
    name = serializers.CharField(max_length=150)

class RoleListSerializer(serializers.ModelSerializer):

    description = serializers.SerializerMethodField()
    label= serializers.SerializerMethodField()
    createdAt=serializers.SerializerMethodField()
    updatedAt=serializers.SerializerMethodField()

    class Meta:
        model = Group
        fields = ['id', 'name','label','description','createdAt','updatedAt']
        read_only_fields = ['id']
    
    def get_description(self,obj):
        return None

    def get_label(self,obj):
        return None

    def get_createdAt(self,obj):
        return None
            
    def get_updatedAt(self,obj):
        return None


