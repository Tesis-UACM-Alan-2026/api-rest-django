# gestion_productos/models.py

from django.db import models
from gestion_categorias.models import Categoria


class Productos(models.Model):

    id = models.BigAutoField(primary_key=True)

    nombre = models.CharField(
        max_length=150
    )

    precio = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )

    stock = models.PositiveIntegerField(
        default=0
    )

    categoria = models.ForeignKey(
        Categoria,
        on_delete=models.PROTECT,
        related_name="productos",
        null=True,
        blank=True
    )

    def __str__(self):
        return self.nombre

    class Meta:
        db_table = "productos"
        verbose_name = "Producto"
        verbose_name_plural = "Productos"