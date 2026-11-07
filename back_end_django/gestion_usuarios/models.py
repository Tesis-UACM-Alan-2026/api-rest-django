# gestion_usuarios/models.py

import uuid
from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.utils import timezone

from .managers import UsuarioManager


class Usuario(AbstractBaseUser, PermissionsMixin):

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )

    email = models.EmailField(
        max_length=254,
        unique=True
    )
    email_verified = models.BooleanField(default=False)
    email_verified_at = models.DateTimeField(null=True, blank=True)

    first_name = models.CharField(max_length=150)

    last_name = models.CharField(max_length=150)

    roles = models.ManyToManyField(
        "gestion_permisos.Rol",
        related_name="usuarios",
        blank=True
    )

    reset_password_token = models.UUIDField(
        null=True,
        blank=True,
        unique=True
    )

    reset_password_expires_at = models.DateTimeField(
        null=True,
        blank=True
    )

    is_active = models.BooleanField(default=True)

    is_staff = models.BooleanField(default=False)

    date_joined = models.DateTimeField(default=timezone.now)

    objects = UsuarioManager()

    USERNAME_FIELD = "email"

    REQUIRED_FIELDS = ["first_name", "last_name"]

    def __str__(self):
        return self.email

    class Meta:
        db_table = "usuarios"
        verbose_name = "Usuario"
        verbose_name_plural = "Usuarios"