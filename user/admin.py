from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User
from .forms import UserCreationForm, UserChangeForm
from django.dispatch import receiver
from django.db.models.signals import post_migrate
from .models import User

@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """
    Configuración personalizada para el modelo User en el panel de administración de Django.
    Se hereda de BaseUserAdmin, la cual tiene atributos:
        model:	Indica qué modelo administra esta clase.
        add_form:	Especifica el formulario que se usará al crear un nuevo usuario desde el admin.
        form:	Especifica el formulario que se usará para editar un usuario.
        list_display:	Define qué columnas se muestran en la tabla del listado de objetos.
        list_filter:	Agrega filtros laterales en la vista de lista.
        ordering:	Establece el orden predeterminado en que se muestran los objetos.
        search_fields:	Permite búsquedas por campos específicos.
        fieldsets:	Organiza los campos cuando editas un objeto en el admin.
        add_fieldsets:	Organiza los campos cuando creas un nuevo objeto en el admin.

    Esta clase:
    - Usa formularios personalizados para crear y editar usuarios.
    - Define qué campos se muestran en la lista, los filtros, y los formularios.
    """

   
    model = User
    add_form = UserCreationForm  # Formulario para agregar usuarios desde el admin.
    form = UserChangeForm        # Formulario para editar usuarios desde el admin.

    list_display = ('email', 'role','is_staff', 'is_superuser')
    list_filter = ('is_staff', 'is_superuser')

    ordering = ('email',)
    search_fields = ('email',)

    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Permisos', {'fields': ('is_active','is_staff','is_superuser','groups','user_permissions',)}),
        ('Fechas importantes', {'fields': ('last_login',)}),
    )

    add_fieldsets = (
        (None, {'classes': ('wide',),'fields': ('email', 'password1', 'password2'),}),
    )
