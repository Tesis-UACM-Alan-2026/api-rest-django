"""
update_me_partial.py

Se ocupa cuando el mismo usuario ya autenticado quiere editar algunos
o varios de sus datos personales.
"""
from rest_framework import serializers
from user.models import User
from user.validators import name_validator, gender_validator, curp_validator, rfc_validator
from user import messages

def validate_rfc(value):
    if not value.isupper():
        raise serializers.ValidationError(messages.ERROR_CAPITAL_LETTERS)
        
    try:
        rfc_validator(value)
    except ValueError:
        raise serializers.ValidationError(messages.LENGTH_EXCEEDED)
        
def validate_name(value):
    if not value.isupper():
        raise serializers.ValidationError(messages.ERROR_CAPITAL_LETTERS)
        
    try:
        name_validator(value)
    except ValueError:
        raise serializers.ValidationError(messages.LENGTH_EXCEEDED)
    
def validate_curp(value):
    if not value.isupper():
        raise serializers.ValidationError(messages.ERROR_CAPITAL_LETTERS)
        
    try:
        curp_validator(value)
    except ValueError:
        raise serializers.ValidationError(messages.LENGTH_EXCEEDED)
        
def validate_gender(value):
    if not value.isupper():
        raise serializers.ValidationError(messages.ERROR_CAPITAL_LETTERS)
        
    try:
        gender_validator(value)
    except ValueError:
        raise serializers.ValidationError(messages.GENDER_ERROR)
    
class UserUpdateMe(serializers.ModelSerializer):
    """
    Serealizador para las actualizaciones del modelo User.

    Se encarga de:
    -Actualizar los datos parciales del usuario
    """

    rfc = serializers.CharField(required=False, validators=[validate_rfc])    
    name = serializers.CharField(required=False, validators=[validate_name])
    middlename = serializers.CharField(required=False, validators=[validate_name])
    first_lastname = serializers.CharField(required=False, validators=[validate_name])
    second_lastname = serializers.CharField(required=False, validators=[validate_name])
    curp = serializers.CharField(required=False, validators=[validate_curp])
    gender = serializers.CharField(required=False, validators=[validate_gender])

    class Meta:
        model = User
        #PATCH
        fields = (
            'name', 'middlename', 'first_lastname','second_lastname','birthdate', 
            'gender', 'curp', 'phone_number', 'cellphone', 'address_cat_nacionalidad_id',
            'address_cat_entidad_id', 'address_city', 'address_zip_code', 
            'address_neighborhood', 'address', 'address_number','address_interior_number', 
            'address_complement','job_position', 'employee_number', 'license', 'rfc', 
            'marital_status', 'notes', 'profile_picture'
        )


    def update_me(self, instance, validated_data):
        """
        Actualiza un usuario existente, y registra el usuario que realizó la modificación.

        Args:
            instance (User): Instancia del usuario a actualizar.
            validated_data (dict): Datos validados del usuario.

        Returns:
            User: Instancia actualizada del usuario.
        """
        request = self.context.get('request')
        updateby = request.user if request and request.user.is_authenticated else None
        
        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        if updateby:
            instance.updated_by = updateby

        instance.save()

        return instance    