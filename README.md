# Proyecto HOSPITAL

Este proyecto utiliza Django como framework principal y `pipenv` para la gestión del entorno virtual y las dependencias.

## Instrucciones de ambientación

Revisar el archivo .env.example

### Variable para definir si se ejecuta en modo development o production

DJANGO_ENV=

### Variable para la llave secreta. Para generar el SK se debe ejecutar el archivo generador_sk_django.py

SECRET_KEY=

### Correo del usuario administrador de Django

SUPERUSER_EMAIL=

### Contraseña del usuario administrador de Django

SUPERUSER_PASSWORD=

### Minutos para el Access Token

ACCESS_TOKEN_LIFETIME_MINUTES=

### Días para el Refresh Token

REFRESH_TOKEN_LIFETIME_DAYS=

### Ruta de la clave privada  
PRIVATE_KEY_PATH=

### Ruta de la clave publica
PUBLIC_KEY_PATH=

## Generación de las claves en un directorio key (keys/private.pem y keys/public.pem)

openssl genrsa -out private.pem 2048

openssl rsa -in private.pem -pubout -out public.pem


## Instrucciones de instalación y ejecución

### Instalar pipenv
sudo apt install pipenv

### Crear el entorno virtual con Python 3.12
pipenv --python /usr/bin/python3

### Activar el entorno virtual
pipenv shell

### Instalar las dependencias
pip install -r requirements.txt

### Generar la migraciones de user

python manage.py makemigrations user

### Generar la migraciones en general

python manage.py makemigrations 

### Crear las tablas de las migraciones

python manage.py migrate

### Generar un usuario administrador con valores en .env, los roles y permisos
python manage.py setup_roles

### Ejecutar el servidor de desarrollo
python manage.py runserver

### Abrir el navegador

http://localhost:8000/swagger/


# Estructura de la app user

* **user/**

    * **admin.py**            : Registro y configuración de modelos en el panel de administración de Django
    * **apps.py**             : Configuración de la app (nombre, señales, etc.)
    * **choices.py**          : Enumeraciones de constantes, como los roles de usuario
    * **forms.py**            : Formularios personalizados para el panel admin u otros usos
    * **logic.py** : Lógica de negocio desacoplada de las vistas; contiene funciones como crear_usuario, bloquear_usuario, etc.
    * **managers.py**            : Gestor personalizado para el modelo User. Define los métodos para crear usuarios comunes y superusuarios de manera segura y compatible con Django    
    * **messages.py**           : Mensajes del sistema para operaciones relacionadas con usuarios    
    * **models.py**           : Modelos de la base de datos: User, Employee, PersonalData
    * **permissions.py**           : Códigos de permisos del sistema para el modelo User    
    * **serializers.py**      : Serializadores de DRF para transformar modelos en JSON y viceversa.  Actualmente en blanco el archivo ya que hubo separación en carpetas.
    * **signals.py**          : Conexión de señales para ejecutar lógica automática tras eventos como crear usuario
    * **tests.py**            : Pruebas unitarias de la app
    * **urls.py**             : Rutas propias de la app (se incluye en las rutas del proyecto)
    * **views.py**            : Vistas basadas en clases (API REST con Django REST Framework). Actualmente en blanco el archivo ya que hubo separación en carpetas.
    * **migrations/**         : Archivos de migración generados automáticamente por Django
        * **__init__.py**     :  Inicialización del módulo de migraciones
    * **views/**         : Carpeta que contiene las vistas separadas por funcionalidad
        * **auth_user.py**     :   Vista login (POST ..)
        * **block_user.py**     :   Vista para bloquear usuarios (POST /api/users/{user_id}/block/)
        * **create_user.py**     :  Vista para la creación de nuevos usuarios (POST a /api/users/create/)
        * **list_user.py**     :  Vista para listar usuarios con filtros, búsqueda y ordenamiento (GET a /api/users/)
    * **serializers/**         : Carpeta que contiene las vistas separadas por funcionalidad
        * **block_user_serializer.py**     :   Serializador para el servicio de bloquear usuarios
        * **custom_token_serializer.py**     :  Serializador para el manejo de tokens.
        * **permissions_serializer.py**     :  Serrilizador para los permisos      
        * **roles_serializer.py**     :  Serializador para  los roles
        * **user_serializer.py**     :  Serializador para la gestión de usuarios. 
    * **management**          : Carpeta con los comandos a ejecutar, en particular, setup_roles.py

# Estructura del core

* **core/**

    * **exceptions.py**            : Manejador global de excepciones personalizado para estandarizar errores
    * **middleware.py**             : Middleware personalizado para modificar o inspeccionar solicitudes y respuestas
    * **responses.py**             : Funciones para generar respuestas estándar (success_response, error_response) en la AP