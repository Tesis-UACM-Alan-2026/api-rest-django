from dataclasses import dataclass, field
from typing import Optional, Set


@dataclass
class PermisoVO:
    """Value Object de Permiso (sirve de entrada y de salida)."""
    id: Optional[int] = None
    codename: Optional[str] = None
    nombre: Optional[str] = None
    descripcion: Optional[str] = None

    # Campos que realmente vinieron en la petición (para PUT/PATCH)
    campos_informados: Set[str] = field(
        default_factory=set, repr=False, compare=False
    )

    CAMPOS = ("codename", "nombre", "descripcion")

    @classmethod
    def desde_modelo(cls, permiso):
        return cls(
            id=permiso.id,
            codename=permiso.codename,
            nombre=permiso.nombre,
            descripcion=permiso.descripcion,
        )

    @classmethod
    def desde_dict(cls, datos: dict):
        filtrados = {k: v for k, v in datos.items() if k in cls.CAMPOS}
        return cls(**filtrados, campos_informados=set(filtrados.keys()))

    def a_dict(self, solo_informados: bool = False) -> dict:
        datos = {
            "codename": self.codename,
            "nombre": self.nombre,
            "descripcion": self.descripcion,
        }

        if solo_informados:
            return {k: v for k, v in datos.items() if k in self.campos_informados}

        return datos