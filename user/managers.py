from django.contrib.auth.models import BaseUserManager
from django.utils import timezone


class UserManager(BaseUserManager):
    """
    Gestor personalizado para el modelo User. Define los métodos para
    crear usuarios comunes y superusuarios de manera segura y compatible
    con Django. Métodos de BaseUserManager a sobreescribir:
    create_user(): creación segura de usuarios normales.
    create_superuser(): creación segura de superusuarios con los permisos correctos.
    Otros métodos:
        all()	Devuelve todos los objetos.
        filter(**kwargs)	Filtra por campos.
        get(**kwargs)	Devuelve un solo objeto o lanza excepción.
        create(**kwargs)	Crea y guarda un nuevo objeto.
        get_or_create()	Intenta obtener, si no existe lo crea.
        update_or_create()	Similar a get_or_create, pero actualiza.
        exclude(**kwargs)	Excluye resultados según el filtro.
        exists()	Devuelve True si hay resultados.
        count()	Cuenta resultados.
        order_by('campo')	Ordena los resultados.
    """

    def create_user(self, email, password=None, **extra_fields):
        """
        Crea y guarda un usuario con el correo y contraseña dados.

        Args:
            email (str): Dirección de correo electrónico del usuario.
            password (str): Contraseña sin encriptar.
            extra_fields (dict): Campos adicionales a asignar.

        Returns:
            User: Instancia del usuario creado.

        Raises:
            ValueError: Si el email no fue proporcionado.
        """
        if not email:
            raise ValueError("El email es obligatorio")
        #Convierte el correo a minúsculas y estandariza el dominio
        email = self.normalize_email(email)
        #Crea un nuevo objeto User, usando el modelo asociado al UserManager
        user = self.model(email=email, **extra_fields)
        #Se encripta la contraseña en un hash seguro,
        user.set_password(password)  
        #Establece manualmente la fecha en la que se creó el usuario
        user.date_joined = timezone.now()
        #Guarda al usuario en la base de datos
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password, **extra_fields):
        """
        Crea y guarda un superusuario con permisos de administración.

        Args:
            email (str): Dirección de correo del superusuario.
            password (str): Contraseña del superusuario.
            extra_fields (dict): Campos adicionales.

        Returns:
            User: Instancia del superusuario creado.
        """
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_staff", True)
        return self.create_user(email, password, **extra_fields)