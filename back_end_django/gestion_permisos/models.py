# gestion_permisos/models.py

from django.db import models


class Permiso(models.Model):

    id = models.BigAutoField(primary_key=True)

    codename = models.CharField(
        max_length=100,
        unique=True
    )

    nombre = models.CharField(
        max_length=150
    )

    descripcion = models.TextField(
        blank=True,
        null=True
    )

    def __str__(self):
        return self.nombre

    class Meta:
        db_table = "permisos"
        verbose_name = "Permiso"
        verbose_name_plural = "Permisos"


class Rol(models.Model):

    id = models.BigAutoField(primary_key=True)

    nombre = models.CharField(
        max_length=100,
        unique=True
    )

    descripcion = models.TextField(
        blank=True,
        null=True
    )

    permisos = models.ManyToManyField(
        Permiso,
        related_name="roles",
        blank=True
    )

    def __str__(self):
        return self.nombre

    class Meta:
        db_table = "roles"
        verbose_name = "Rol"
        verbose_name_plural = "Roles"