from django import forms
from django.contrib.auth.forms import ReadOnlyPasswordHashField
from .models import User


class UserCreationForm(forms.ModelForm):
    """
    Formulario para crear nuevos usuarios en el panel de administración.

    Permite capturar una contraseña doblemente para validación.

    Args:
        forms.ModelForm: Clase base de Django para construir formularios ligados a modelos.

    Attributes:
        password1 (CharField): Primer campo de contraseña.
        password2 (CharField): Campo para confirmar la contraseña.
    """

    password1 = forms.CharField(label='Contraseña', widget=forms.PasswordInput)
    password2 = forms.CharField(label='Confirmar contraseña', widget=forms.PasswordInput)

    class Meta:
        model = User
        fields = ('email',)

    def clean_password2(self):
        """
        Valida que las contraseñas coincidan.

        Returns:
            str: Contraseña validada.

        Raises:
            forms.ValidationError: Si las contraseñas no coinciden.
        """
        password1 = self.cleaned_data.get("password1")
        password2 = self.cleaned_data.get("password2")
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError("Las contraseñas no coinciden.")
        return password2

    def save(self, commit=True):
        """
        Guarda el usuario con la contraseña encriptada.

        Args:
            commit (bool): Si es True, guarda el usuario en la base de datos.

        Returns:
            User: El nuevo usuario creado.
        """
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password1"])
        if commit:
            user.save()
        return user


class UserChangeForm(forms.ModelForm):
    """
    Formulario para actualizar usuarios existentes en el panel de administración.

    Muestra la contraseña en formato de solo lectura.

    Args:
        forms.ModelForm: Clase base de Django para formularios ligados a modelos.
    """

    password = ReadOnlyPasswordHashField(
        label="Contraseña",
        help_text="Las contraseñas no se almacenan en texto plano, por seguridad no puedes ver esta contraseña."
    )

    class Meta:
        model = User
        fields = ('email', 'password', 'is_active', 'is_staff', 'is_superuser')
