from rest_framework import serializers
from user.models import User


class UserMeSerializer(serializers.ModelSerializer):
    """
        Serializador de solo lectura para el endpoint GET /users/me.

        Se encarga de:
        - Mostrar los datos personales, laborales y de cuenta del usuario autenticado.
        - Todos los campos están marcados como de solo lectura.
        """
    class Meta:
        model = User
        #GET
        fields = (
            'user_id',
            'email',
            'email_verified',
            'role',
            'is_superuser',
            'is_staff',
            'is_active',
            'name',
            'middlename',
            'first_lastname',
            'second_lastname',
            'birthdate',
            'gender',
            'curp',
            'phone_number',
            'cellphone',
            'address_cat_nacionalidad_id',
            'address_cat_entidad_id',
            'address_city',
            'address_zip_code',
            'address_neighborhood',
            'address',
            'address_number',
            'address_interior_number',
            'address_complement',
            'job_position',
            'employee_number',
            'license',
            'rfc',
            'marital_status',
            'notes',
            'date_joined',
            'created_at',
            'updated_at',
        )
        read_only_fields = fields  # todos los campos son solo de lectura
