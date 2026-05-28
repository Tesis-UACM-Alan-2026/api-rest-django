"""
Esta clase contiene las validaciones para actualizar y registrar un nuevo usuario
"""

from django.core.validators import RegexValidator
from user import messages

name_validator = RegexValidator(
    regex=r'^[A-Z0-9Á-ÚÄ-Ü\'`´\s\-]{1,50}$',
    message= messages.LENGTH_EXCEEDED
)

gender_validator = RegexValidator(
    regex=r'^[HMX]{1,1}$',
    message=messages.GENDER_ERROR
) 

curp_validator = RegexValidator(
    regex=r'^[A-Z0-9]{18}$',
    message=messages.CURP_AND_RFC_LENGHT_EXCEEDED
)

rfc_validator = RegexValidator(
    regex=r'^[A-Z0-9]{13}$',
    message=messages.CURP_AND_RFC_LENGHT_EXCEEDED
)

password_validator = RegexValidator(
    regex=r'^(?=.*[A-Z])(?=.*[a-z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{8,}$',

)