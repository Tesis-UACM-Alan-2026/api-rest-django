from dataclasses import dataclass, field
from typing import Optional, Set


@dataclass
class CategoriaVO:
    """Value Object de Categoría (sirve de entrada y de salida)."""
    id: Optional[int] = None
    nombre: Optional[str] = None
    descripcion: Optional[str] = None

    # Campos que realmente vinieron en la petición (para PUT/PATCH)
    campos_informados: Set[str] = field(
        default_factory=set, repr=False, compare=False
    )

    CAMPOS = ("nombre", "descripcion")

    @classmethod
    def desde_modelo(cls, categoria):
        """Convierte una instancia del modelo Categoria en VO."""
        return cls(
            id=categoria.id,
            nombre=categoria.nombre,
            descripcion=categoria.descripcion,
        )

    @classmethod
    def desde_dict(cls, datos: dict):
        """Crea el VO a partir de validated_data, ignorando claves desconocidas."""
        filtrados = {k: v for k, v in datos.items() if k in cls.CAMPOS}
        return cls(**filtrados, campos_informados=set(filtrados.keys()))

    def a_dict(self, solo_informados: bool = False) -> dict:
        """Convierte el VO a dict para el DAO."""
        datos = {
            "nombre": self.nombre,
            "descripcion": self.descripcion,
        }

        if solo_informados:
            return {k: v for k, v in datos.items() if k in self.campos_informados}

        return datos