# gestion_categorias/models.py

from django.db import models


class Categoria(models.Model):

    id = models.BigAutoField(primary_key=True)

    nombre = models.CharField(
        max_length=150,
        unique=True
    )

    descripcion = models.TextField(
        blank=True,
        null=True
    )

    def __str__(self):
        return self.nombre

    class Meta:
        db_table = "categorias"
        verbose_name = "Categoría"
        verbose_name_plural = "Categorías"
