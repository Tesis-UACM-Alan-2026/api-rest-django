"""
serializers.py

Definición de los serializadores para la app de usuarios. Estos se encargan de transformar
las instancias de los modelos a representaciones JSON y viceversa, aplicando validaciones
y lógica personalizada para la creación y manipulación de usuarios, empleados y datos personales.
"""

from rest_framework import serializers
from user.models import User
from user.choices import assign_user_to_role, RoleChoices
import re
from rest_framework.exceptions import ValidationError
from user import messages
from django.contrib.auth.hashers import make_password
class UserSerializer(serializers.ModelSerializer):
    password_confirmation = serializers.CharField(write_only=True, required=True)
    signing_password_confirmation = serializers.CharField(write_only=True, required=True)

    def validate(self, attrs):
        password = attrs.get('password')
        password_confirmation = attrs.get('password_confirmation')
        signing_password = attrs.get('signing_password')
        signing_password_confirmation = attrs.get('signing_password_confirmation')
        birthdate = attrs.get('birthdate')
        gender= attrs.get('gender')
        name=attrs.get('name')
        first_lastname=attrs.get('first_lastname')
        role= attrs.get('role')
        curp = attrs.get('curp')
        if not gender:
            raise ValidationError({
                'gender':messages.GENDER_REQUIRED
                })
        if not password or not password_confirmation:
            raise ValidationError({'password': messages.PASSWORD_REQUIRED})
        if not signing_password or not signing_password_confirmation:
            raise ValidationError({'signing_password': messages.PASSWORD_REQUIRED})
        if not role:
            raise ValidationError({'role': messages.ROLE_REQUIRED})
        if not curp:
            raise ValidationError({'curp': messages.CURP_REQUIRED})
        if not name:
            raise ValidationError({'name': messages.NAME_REQUIRED})
        if not first_lastname:
            raise ValidationError({'first_lastname': messages.FIRST_LAST_NAME_REQUIRED})
        if not birthdate:
            raise ValidationError({'birthdate': messages.BIRTHDATE_REQUIRED})
        if password != password_confirmation:
            raise ValidationError({'password_confirmation': messages.CREATE_PASSWORDS_DO_NOT_MATCH})
        if signing_password != signing_password_confirmation:
            raise ValidationError({'signing_password_confirmation': messages.CREATE_SIGNING_PASSWORDS_DO_NOT_MATCH})
        if birthdate is None or str(birthdate).strip() == '':
            raise ValidationError({'birthdate': messages.BIRTHDATE_REQUIRED})
        return attrs
    """
    Serializador principal para el modelo User.

    Se encarga de:
    - Mostrar los datos básicos del usuario.
    - Crear el usuario con la contraseña encriptada.
    - Asignar grupos y roles en la creación.
    """
    
     
    class Meta:
        model = User
        #GET
        fields = (
            'user_id', 'password', 'password_confirmation', 'signing_password', 'signing_password_confirmation', 'email', 'role',
            'profile_picture', 'name', 'middlename', 'first_lastname', 'second_lastname',
            'birthdate', 'gender', 'curp', 'phone_number', 'cellphone',
            'address_cat_nacionalidad_id', 'address_cat_entidad_id', 'address_city',
            'address_zip_code', 'address_neighborhood', 'address', 'address_number',
            'address_interior_number', 'address_complement',
            'job_position', 'employee_number', 'license', 'rfc',
            'marital_status', 'notes','is_active', 'is_superuser',
            'email_verified', 'email_verified_at', 'last_login', 'last_login_IP',
            'is_staff', 'date_joined', 'created_at', 'updated_at',
            'is_deleted', 'deleted_at', 'restored_at', 'blocked_at', 'unblocked_at',
            'blocked_by', 'created_by', 'deleted_by', 'restored_by', 'unblocked_by', 'updated_by',
        )
        #-POST 
        extra_kwargs = {
            'password':{ 'write_only': True},
            'password_confirmation': {'write_only': True},
            'signing_password': {'write_only': True},
            'signing_password_confirmation': {'write_only': True},
            'user_id': {'read_only': True},
            'last_login': {'read_only': True},
            'last_login_IP': {'read_only': True},
            'email_verified': {'read_only': True},
            'email_verified_at': {'read_only': True},
            'is_staff': {'read_only': True},
            'is_superuser': {'read_only': True},
            'is_active': {'read_only': True},
            'is_blocked': {'read_only': True},
            'blocked_at': {'read_only': True},
            'created_at': {'read_only': True},
            'updated_at': {'read_only': True},
            'date_joined': {'read_only': True},
            'is_deleted': {'read_only': True},
            'deleted_at': {'read_only': True},
            'created_by': {'read_only': True},
            'updated_by': {'read_only': True},
            'deleted_by': {'read_only': True},
            'restored_at': {'read_only': True},
            'restored_by': {'read_only': True},
            'unblocked_at': {'read_only': True},
            'blocked_by': {'read_only': True},
            'unblocked_by': {'read_only': True},
        }

    # Funcion para validar que el email sea proveido por el usuario
    def validate_email(self,value):
        if not value: 
            raise ValidationError({
                'message':messages.EMAIL_REQUIRED,
            })
        return value
    # Función que valida la unicidad del numero de empleado
    def validate_employee_number(self,value):
        if User.objects.filter(employee_number=value).exists():
            raise ValidationError({
                'message':messages.NUMBER_EMPLOYEE_ALREADY_EXISTS,
            })
        return value
    def validate_role(self, value):
        """
        Valida que el rol proporcionado sea uno de los roles permitidos.
        """
        if not value:
            raise ValidationError({
                'message': messages.ROLE_REQUIRED
            })
        try:
            RoleChoices(value)  # Intenta convertir el valor al enum
        except ValueError:
            raise ValidationError({
                'message': messages.ROLE_INVALID
            })
        return value
    # Función para validar la fecha de nacimiento en formato ISO 8601 (ejemplo: 2025-08-06T22:12:36.628Z)
    def validate_birthdate(self, value):
        
        if not value or len(str(value)) == 0:
            raise ValidationError({
                'message': messages.BIRTHDATE_REQUIRED,
            })
        
        return value
    # Función para validar el genero
    def validate_gender(self,value):
        pattern=r'^[HMX]$'
        if len(value)==0:
            raise ValidationError({
                'message':messages.GENDER_REQUIRED,
            })
        if not bool(re.fullmatch(pattern,value)):
            raise ValidationError({
                'message':messages.GENDER_ERROR,
            })
        return value
    # Función para validar la licencia
    def validate_license(self,value):
        
        if User.objects.filter(license=value).exists():
            raise ValidationError({
                'message':messages.LICENSE_USER_ALREADY_EXISTS,
            })
        return value
    # Función para validar RFC
    def validate_rfc(self,value):
        pattern= r'^([A-ZÑ&]{3,4})(\d{2})(0[1-9]|1[0-2])(0[1-9]|[12]\d|3[01])([A-Z\d]{2})([A\d])$'
        if len(value)>14 or len(value)<13:
            raise ValidationError({
                'message':messages.RFC_LENGHT_INCORRECT,
            })
        if not bool(re.fullmatch(pattern,value)):
            raise ValidationError({
                'message':messages.RFC_FORMAT_INVALID,
            })
        if User.objects.filter(rfc=value).exists():
            raise ValidationError({
                'message':messages.RFC_ALREADY_EXISTS,
            })
        return value
        
    # Función para validar curp
    def validate_curp(self,value):
        """
            Se valida la CURP haciendo uso de todas la reglas oficiales de la RENAPO
        """

        pattern = r'^[A-Z]{4}\d{6}[HMX][A-Z]{5}[0-9A-Z]\d$'
        if not value:
            raise ValidationError({
                'message': messages.CURP_REQUIRED,
            })
        if len(value)!=18:
            raise ValidationError({
                'message':messages.CURP_LENGHT_INCORRECT,
            })
        if not bool(re.fullmatch(pattern,value)):
            raise ValidationError({
                'message':messages.CURP_FORMAT_INVALID,
            })
        
        """
            Se valida la unicidad de la CURP 
        """
        if User.objects.filter(curp=value).exists():
            raise ValidationError({
                'message':messages.CURP_ALREADY_EXISTS,
            })
        
        return value
    # Función que valida una contraseña
    def _validate_password(self,value):
        """
        Valida que la contraseña cumpla con los requisitos de seguridad:
        - Mínimo 8 caracteres
        - Al menos una mayúscula
        - Al menos una minúscula
        - Al menos un número
        - Al menos un caracter especial
        """
        if not value: 
            raise ValidationError({
                'error':messages.PASSWORD_REQUIRED
            })
        if len(value) < 8:
            raise ValidationError({
                'error':messages.PASSWORD_LENGHT_INCORRECT
            })
        if len(value)>64:
            raise ValidationError({
                'error':messages.PASSWORD_LENGHT_INCORRECT
            })
        if not re.search(r'[A-Z]', value):
            raise ValidationError({
                'error':messages.PASSWORD_FORMAT_INCORERCT
            })
        
        if not re.search(r'[a-z]', value):
            raise ValidationError({
                'error':messages.PASSWORD_FORMAT_INCORERCT
            })
        
        if not re.search(r'\d', value):
            raise ValidationError({
                'error':messages.PASSWORD_FORMAT_INCORERCT
            })
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', value):
            raise ValidationError({
                'error':messages.PASSWORD_FORMAT_INCORERCT
            })
        
        return value
    # Función para validar el formato de los nombres
    def _names_validate(self,value,field):
        """
        Valida que el nombre(s) y apellido(s) esté en mayúsculas y solo contenga letras y espacios.
        """

        if not re.match(r'^[A-ZÁÉÍÓÚÜÑ\s]+$', value):
            raise ValidationError({
                'error':messages.ERROR_CAPITAL_LETTERS
                }
            )
        return value
    
    # Función para validar la contraseña
    def validate_password(self,value):
        return self._validate_password(value)

    # Función que valida signingPassword
    def validate_signing_password(self,value):
        return self._validate_password(value)
    #Función para validar nombres opcionales
    def _validate_optional_name(self,value,field):
        if value: 
            return self._names_validate(value,field)
        return value
    # Función para validar el primer nombre 
    def validate_name(self,value):
        if not value:
            raise ValidationError({
                'message': messages.NAME_REQUIRED,
            })
        return self._names_validate(value,"nombre")
    # Función para validar el segundo nombre en caso de que exista
    def validate_middlename(self,value):
        return self._validate_optional_name(value,"segundo nombre")
    # Función que valida el primer apellido
    def validate_first_lastname(self,value):
        if not value:
            raise ValidationError({
                'message': messages.FIRST_LAST_NAME_REQUIRED,
            })
        return self._names_validate(value,"Primer apellido")
    #Función que valida el segundo apellido si existe
    def validate_second_lastname(self,value):
        return self._validate_optional_name(value,"Segundo apellido")
    

    

    def create(self, validated_data):
        # Eliminar los campos de confirmación si existen
        validated_data.pop('password_confirmation', None)
        validated_data.pop('signing_password_confirmation', None)
        """
        Crea un nuevo usuario, encripta la contraseña y la contraseña de firma, asigna roles y crea
        registros vinculados de Employee y PersonalData.
        """
        request = self.context.get('request')
        createby = request.user if request and request.user.is_authenticated else None

        password = validated_data.pop('password', None)
        signing_password = validated_data.pop('signing_password', None)
        role_str = validated_data.get('role')
        groups = validated_data.pop('groups', [])

        user = User(**validated_data)
        if password:
            user.set_password(password)
        if signing_password:
            user.signing_password = make_password(signing_password)

        if createby:
            user.created_by = createby
        user.save()

        # Validar y asignar el rol
        try:
            role_enum = RoleChoices(role_str)
        except ValueError:
            raise serializers.ValidationError({'role': 'El rol seleccionado es inválido.'})
        assign_user_to_role(user, role_enum)

        # Asignar grupos
        if groups:
            user.groups.set(groups)

        return user

    def update(self, instance, validated_data):
        """
        Actualiza un usuario existente, encripta la contraseña si se proporciona
        y registra el usuario que realizó la modificación.

        Args:
            instance (User): Instancia del usuario a actualizar.
            validated_data (dict): Datos validados del usuario.

        Returns:
            User: Instancia actualizada del usuario.
        """
        request = self.context.get('request')
        updateby = request.user if request and request.user.is_authenticated else None

        password = validated_data.pop('password', None)
        role_str = validated_data.get('role')
        groups = validated_data.pop('groups', None)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        if password:
            instance.set_password(password)

        if updateby:
            instance.updated_by = updateby

        instance.save()

        # Validar y asignar rol (opcional si se quiere permitir cambiar el rol)
        if role_str:
            try:
                role_enum = RoleChoices(role_str)
                assign_user_to_role(instance, role_enum)
            except ValueError:
                raise serializers.ValidationError({'role': 'El rol proporcionado no es válido.'})

        # Asignar grupos (si se proporcionan)
        if groups is not None:
            instance.groups.set(groups)

        return instance
