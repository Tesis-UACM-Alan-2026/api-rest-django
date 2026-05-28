"""
view_user.py

Se usa para obtener la lista de usuarios, se establecen los parametros a mostrar
contraseña no se muestra por seguridad.
"""
from rest_framework import serializers
from user.models import User
from user.choices import assign_user_to_role, RoleChoices


class ViewUser(serializers.ModelSerializer):
    """
    Serializador principal para el modelo User.

    Se encarga de:
    - Mostrar los datos usuario.
    """
    class Meta:
        model = User
        #GET
        fields = (
            'user_id', 'email', 'email_verified', 'email_verified_at', 'last_login','last_login_IP',
            'role', 'is_superuser', 'is_staff', 'is_active', 'name', 'middlename', 'first_lastname',
            'second_lastname','birthdate', 'gender', 'curp', 'phone_number', 'cellphone', 
            'address_cat_nacionalidad_id','address_cat_entidad_id', 'address_city', 'address_zip_code', 
            'address_neighborhood', 'address', 'address_number','address_interior_number', 
            'address_complement','job_position', 'employee_number', 'license', 'rfc', 
            'marital_status', 'notes', 'profile_picture', 'date_joined', 'created_at',
            'updated_at', 'is_deleted', 'deleted_at', 'restored_at', 'blocked_at', 'unblocked_at', 'blocked_by',
            'created_by', 'deleted_by', 'restored_by', 'unblocked_by', 'updated_by'
        )