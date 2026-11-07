from dataclasses import dataclass, field
from typing import List, Optional, Set

from gestion_permisos.VO.permisoVO import PermisoVO


@dataclass
class RolVO:
    """
    Value Object de Rol. Como salida incluye sus permisos (lista de PermisoVO);
    como entrada solo se usan nombre y descripcion (los permisos se asignan
    con asignar_permisos / quitar_permisos).
    """
    id: Optional[int] = None
    nombre: Optional[str] = None
    descripcion: Optional[str] = None
    permisos: List[PermisoVO] = field(default_factory=list)

    # Campos que realmente vinieron en la petición (para PUT/PATCH)
    campos_informados: Set[str] = field(
        default_factory=set, repr=False, compare=False
    )

    CAMPOS = ("nombre", "descripcion")

    @classmethod
    def desde_modelo(cls, rol):
        return cls(
            id=rol.id,
            nombre=rol.nombre,
            descripcion=rol.descripcion,
            permisos=[PermisoVO.desde_modelo(p) for p in rol.permisos.all()],
        )

    @classmethod
    def desde_dict(cls, datos: dict):
        filtrados = {k: v for k, v in datos.items() if k in cls.CAMPOS}
        return cls(**filtrados, campos_informados=set(filtrados.keys()))

    def a_dict(self, solo_informados: bool = False) -> dict:
        datos = {
            "nombre": self.nombre,
            "descripcion": self.descripcion,
        }

        if solo_informados:
            return {k: v for k, v in datos.items() if k in self.campos_informados}

        return datos