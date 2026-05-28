"""
Mensajes del sistema para operaciones relacionadas con usuarios.

Este módulo contiene constantes de texto utilizadas en respuestas del backend,
evitando el uso de cadenas de texto hardcodeadas en vistas, servicios o validaciones.
Agrupar y centralizar estos mensajes mejora la mantenibilidad, facilita la localización
(multilenguaje) y permite modificaciones consistentes.

Se recomienda utilizar estos mensajes con `.format()` o `f-strings` si contienen variables dinámicas.
"""

# === BLOQUEO DE USUARIOS ===
BLOCK_SUCCESS = "Usuario {email} bloqueado correctamente."
BLOCK_ALREADY = "El usuario ya está bloqueado."
BLOCK_NO_PERMISSION = "No tiene permiso para bloquear usuarios."
BLOCK_USER_ID_REQUIRED = "Se requiere el parámetro 'user_id'."

# === DESBLOQUEO DE USUARIOS ===
UNBLOCK_SUCCESS = "Usuario {email} desbloqueado correctamente."
UNBLOCK_ALREADY = "El usuario no está bloqueado."
UNBLOCK_NO_PERMISSION = "No tiene permiso para desbloquear usuarios."

# === RESTAURACIÓN DE USUARIOS ===
RESTORE_SUCCESS = "El usuario ha sido restaurado correctamente."
RESTORE_NO_PERMISSION = "No tiene permiso para restaurar usuarios."
RESTORE_ALREADY = "El usuario no esta eliminado."

# === CONSULTA DE USUARIOS ===
USER_LIST_SUCCESS = "Lista de usuarios recuperada exitosamente."

# === CREACIÓN DE USUARIOS ===
CREATE_SUCCESS = "Usuario {email} creado exitosamente."
CREATE_EMAIL_EXISTS = "Ya existe un usuario con ese correo electrónico."
CREATE_MISSING_FIELDS = "Faltan campos obligatorios para crear el usuario."
CREATE_NO_PERMISSION = "No tiene permiso para crear usuarios"

# --- Mensajes de error para validaciones de creación de usuario ---
CREATE_PASSWORDS_DO_NOT_MATCH = "Las contraseñas no coinciden."
CREATE_SIGNING_PASSWORDS_DO_NOT_MATCH = "Las contraseñas de firma no coinciden."
NUMBER_EMPLOYEE_ALREADY_EXISTS = "El número de empleado ya existe."
LICENSE_USER_ALREADY_EXISTS = "La licencia ya existe en el sistema."
RFC_FORMAT_INVALID = "Formato de RFC invalido."
RFC_LENGHT_INCORRECT = "La longitud del RFC es incorrecta."
RFC_ALREADY_EXISTS = "El RFC ya existe en el sistema."
CURP_FORMAT_INVALID = "Formato de CURP invalido."
CURP_ALREADY_EXISTS = "La CURP ya existe en el sistema"
CURP_LENGHT_INCORRECT = "La longitud de la CURP es incorrecta"
PASSWORD_LENGHT_INCORRECT = "La longitud de la contraseña es incorrecta"
PASSWORD_FORMAT_INCORERCT = "Formato incorrecto de la contraseña"
CREATE_ERROR="Error inesperado al procesar la solicitud de creación de usuario"
GENDER_REQUIRED="El género es un campo obligatorio."
BIRTHDATE_REQUIRED= "La fecha de nacimiento es un campo obligatorio."
BIRTHDATE_INVALID = "Formato de fecha invalido. Formato correcto: YYYY-MM-DD"
ROLE_REQUIRED = 'El rol es un campo obligatorio.'
CURP_REQUIRED = "El CURP es un campo obligatorio."
PASSWORD_REQUIRED = "La contraseña es un campo obligatorio."
EMAIL_REQUIRED = "El correo electrónico es un campo obligatorio."
NAME_REQUIRED = "El nombre es un campo obligatorio."
FIRST_LAST_NAME_REQUIRED = "El primer apellido es un campo obligatorio."
# === ACTUALIZACIÓN DE USUARIOS ===
UPDATE_SUCCESS = "Usuario {email} actualizado correctamente."
UPDATE_PARTIAL_SUCCESS = "Usuario actualizado correctamente."
UPDATE_NO_PERMISSION = "No tiene permiso para modificar usuarios."
LENGTH_EXCEEDED = "Longitud no permitida."
GENDER_ERROR = "Valor no permitido."
CURP_AND_RFC_LENGHT_EXCEEDED = "Longitud no permitida."
ERROR_CAPITAL_LETTERS = "El texto debe estar en mayúsculas."

# === ELIMINACIÓN DE USUARIOS ===
DELETE_SUCCESS = "Usuario {email} eliminado correctamente."
DELETE_NO_PERMISSION = "No tiene permiso para eliminar usuarios."
DELETE_ALREADY = "El usuario ya ha sido eliminado anteriormente."

# === CONSULTA DE USUARIOS ===
USER_FOUND = "Usuario encontrado."
USER_ID_REQUIRED = "Debe proporcionar el ID del usuario."
USER_PROFILE_FOUND = "Perfil de usuario obtenido correctamente."

# === PERMISOS ===
CANNOT_MODIFY_SELF = "No puede realizar esta operación sobre su propio usuario."

# === ROLES ===
ROLE_ASSIGN_SUCCESS = "Rol {role} asignado correctamente al usuario."
ROLE_INVALID = "El rol proporcionado no es válido."
ROLE_REQUIRED = "Debe especificar un rol para esta operación."

# === LISTAR PERMISOS ===
PERMISSION_LIST_SUCCESS = "Lista de permisos en el sistema recuperada exitosamente."

# === GENERALES ===
INVALID_DATA = "Los datos proporcionados no son válidos."
ACTION_NOT_ALLOWED = "Esta acción no está permitida."
LACK_OF_FIELD = "Solicitud mal formada."

# == PETICION DE TOKENS ==
REFRESH_SUCCESS = "Token actualizado correctamente."
VERIFIED_USER = "Usuario verificado correctamente."
VERIFIED_TOKEN = "Token de acceso verificado correctamente."


# == CAMBIO DE CONTRASEÑA ==
REQUIRED_FIELD = "Este campo es obligatorio."
NOT_BLANK_FIELD = "Este campo no puede estar vacio."
MIN_LENGTH_PASSWORD = "La contraseña debe tener un mínimo de 8 caracteres."
MAX_LENGTH_PASSWORD = "La contraseña debe tener como máximo 64 caracteres."
PASSWORD_DONT_MATCH = "La nueva contraseña y su confirmación no coinciden."
TYPE_PASSWORD = "La contraseña debe ser una cadena de caracteres."
INVALID_PASSWORD_FORMAT = "La contraseña no cumple con la especificación."
CHANGE_PASSWORD_USER_DELETED_INHABILITED = (
    "No se pudo actualizar la contraseña el usuario esta inhabilitado."
)
INCORRECT_PASSWORD = "La contraseña actual es incorrecta."
UPDATED_PASSWORD = "Contraseña actualizada exitosamente."

# 400 Bad Request
LACK_OR_INVALID_DATA = "Faltan campos obligatorios o los datos proporcionados son inválidos."

# 401 Unauthorized
INVALID_TOKEN = "Autenticación fallida: Token inválido o expirado."
AUTHENTICATION_REQUIRED = "Las credenciales proporcionadas no son válidas."

# 403 Forbidden
USER_BLOCKED = "No se puede iniciar sesión: el usuario está bloqueado o suspendido."
INSUFFICIENT_PERMISSIONS = "El usuario no tiene permisos para esta operación."

# 404 Not Found
USER_NOT_FOUND = "No se encontró ningún recurso con ID: {uuid}"
TOKEN_NOT_FOUND = "Token no encontrado."

# 429 Too Many Request
TOO_MANY_REQUESTS = "Has excedido el número máximo de intentos permitidos."

# 500 Internal Server Error
UNKNOWN_ERROR = "Se ha producido una excepción no controlada."