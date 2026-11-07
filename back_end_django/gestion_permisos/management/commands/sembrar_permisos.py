from django.core.management.base import BaseCommand
from django.db import transaction

from gestion_permisos.catalogo import PERMISOS, ROLES_BASE
from gestion_permisos.models import Permiso, Rol


class Command(BaseCommand):
    help = (
        "Crea (o actualiza) los permisos del catálogo y los roles base "
        "'Administrador' y 'Consulta'. Es seguro ejecutarlo varias veces."
    )

    @transaction.atomic
    def handle(self, *args, **options):
        permisos = {}
        creados = 0

        for codename, nombre, descripcion in PERMISOS:
            permiso, creado = Permiso.objects.update_or_create(
                codename=codename,
                defaults={"nombre": nombre, "descripcion": descripcion},
            )
            permisos[codename] = permiso
            creados += int(creado)

        self.stdout.write(
            f"Permisos: {creados} creados, {len(PERMISOS) - creados} ya existían."
        )

        for nombre_rol, (descripcion, codenames) in ROLES_BASE.items():
            rol, creado = Rol.objects.get_or_create(
                nombre=nombre_rol,
                defaults={"descripcion": descripcion},
            )
            rol.permisos.add(*[permisos[c] for c in codenames])

            estado = "creado" if creado else "actualizado"
            self.stdout.write(
                f"Rol '{nombre_rol}' {estado} con {len(codenames)} permisos."
            )

        self.stdout.write(self.style.SUCCESS("Catálogo de permisos listo."))