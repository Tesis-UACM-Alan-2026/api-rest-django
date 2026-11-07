from dataclasses import dataclass, field, fields
from decimal import Decimal
from typing import Optional, Set


@dataclass
class ProductoVO:
    """Value Object de Producto. Transporta datos entre vista y servicio."""
    id: Optional[int] = None
    nombre: Optional[str] = None
    precio: Optional[Decimal] = None
    stock: Optional[int] = None
    categoria: Optional[int] = None  # id de la categoría (FK, nullable)

    # Campos que realmente vinieron en la petición (para PATCH)
    campos_informados: Set[str] = field(default_factory=set, repr=False, compare=False)

    @classmethod
    def desde_modelo(cls, producto):
        """Convierte una instancia de Productos en VO."""
        return cls(
            id=producto.id,
            nombre=producto.nombre,
            precio=producto.precio,
            stock=producto.stock,
            categoria=producto.categoria_id,
        )

    @classmethod
    def desde_dict(cls, datos: dict):
        """Crea un VO a partir de validated_data, ignorando claves desconocidas."""
        permitidos = {f.name for f in fields(cls)} - {"campos_informados"}
        filtrados = {k: v for k, v in datos.items() if k in permitidos}
        informados = set(filtrados.keys())

        # Si el serializer entrega un objeto Categoria, nos quedamos con su id
        categoria = filtrados.get("categoria")
        if categoria is not None and hasattr(categoria, "pk"):
            filtrados["categoria"] = categoria.pk

        return cls(**filtrados, campos_informados=informados)

    def a_dict(self, solo_informados: bool = False) -> dict:
        """Convierte el VO a dict listo para el DAO (usa categoria_id)."""
        datos = {
            "nombre": self.nombre,
            "precio": self.precio,
            "stock": self.stock,
            "categoria_id": self.categoria,
        }

        if solo_informados:
            informados = {
                "categoria_id" if c == "categoria" else c
                for c in self.campos_informados
            }
            return {k: v for k, v in datos.items() if k in informados}

        return datos