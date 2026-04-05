import re
from django import forms
from .models import User, Person
 
 
class RegisterForm(forms.Form):
    """
    Formulario de registro seguro para el modelo de Usuario personalizado. 
    Valida todos los campos antes de crear Person + User.
    """
 
    first_name = forms.CharField(
        label="Nombre",
        max_length=100,
        error_messages={'required': 'El nombre es obligatorio.'}
    )
    last_name = forms.CharField(
        label="Apellido",
        max_length=100,
        error_messages={'required': 'El apellido es obligatorio.'}
    )
    email = forms.EmailField(
        label="Correo electrónico",
        required=False,
        error_messages={'invalid': 'Ingresa un correo válido.'}
    )
    login = forms.CharField(
        label="Usuario",
        max_length=150,
        min_length=4,
        error_messages={
            'required': 'El nombre de usuario es obligatorio.',
            'min_length': 'El usuario debe tener al menos 4 caracteres.',
        }
    )
    password = forms.CharField(
        label="Contraseña",
        widget=forms.PasswordInput,
        min_length=8,
        error_messages={
            'required': 'La contraseña es obligatoria.',
            'min_length': 'La contraseña debe tener al menos 8 caracteres.',
        }
    )
    confirm_password = forms.CharField(
        label="Confirmar contraseña",
        widget=forms.PasswordInput,
        error_messages={'required': 'Debes confirmar la contraseña.'}
    )

 
    def clean_first_name(self):
        value = self.cleaned_data.get('first_name', '').strip()
        if not re.match(r"^[a-zA-ZáéíóúÁÉÍÓÚñÑüÜ ]+$", value):
            raise forms.ValidationError("El nombre solo puede contener letras y espacios.")
        return value
 
    def clean_last_name(self):
        value = self.cleaned_data.get('last_name', '').strip()
        if not re.match(r"^[a-zA-ZáéíóúÁÉÍÓÚñÑüÜ ]+$", value):
            raise forms.ValidationError("El apellido solo puede contener letras y espacios.")
        return value
 
    def clean_login(self):
        login = self.cleaned_data.get('login', '').strip()
        if not re.match(r"^[a-zA-Z0-9]+$", login):
            raise forms.ValidationError(
                "El usuario debe contener solo letras y números."
            )
        if User.objects.filter(login=login).exists():
            raise forms.ValidationError("Ese nombre de usuario ya está en uso.")
        return login
 
    def clean_password(self):
        password = self.cleaned_data.get('password', '')
        if not re.search(r'[A-Z]', password):
            raise forms.ValidationError("La contraseña debe tener al menos una letra mayúscula.")
        if not re.search(r'[0-9]', password):
            raise forms.ValidationError("La contraseña debe tener al menos un número.")
        if not re.search(r'[!@#$%^&*(),.?\":{}|<>_\-]', password):
            raise forms.ValidationError("La contraseña debe tener al menos un carácter especial (!@#$%...).")
        return password
 
    # ── Cross-field validation ─────────────────────────────
 
    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        confirm  = cleaned_data.get('confirm_password')
 
        if password and confirm and password != confirm:
            self.add_error('confirm_password', "Las contraseñas no coinciden.")
 
        return cleaned_data