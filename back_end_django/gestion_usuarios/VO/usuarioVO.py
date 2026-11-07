import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional, Set


@dataclass
class RolResumenVO:
    """Resumen de un rol dentro de la representación de un usuario."""
    id: int
    nombre: str


@dataclass
class UsuarioVO:
    """
    VO de SALIDA. Representa un usuario hacia afuera del servicio.
    No incluye password ni datos de reseteo de contraseña.
    """
    id: Optional[uuid.UUID] = None
    email: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    is_active: Optional[bool] = None
    date_joined: Optional[datetime] = None
    roles: List[RolResumenVO] = field(default_factory=list)

    @classmethod
    def desde_modelo(cls, usuario):
        """Convierte una instancia del modelo Usuario en VO."""
        return cls(
            id=usuario.id,
            email=usuario.email,
            first_name=usuario.first_name,
            last_name=usuario.last_name,
            is_active=usuario.is_active,
            date_joined=usuario.date_joined,
            roles=[
                RolResumenVO(id=r.id, nombre=r.nombre)
                for r in usuario.roles.all()
            ],
        )


@dataclass
class UsuarioEntradaVO:
    """
    VO de ENTRADA. Transporta los datos que llegan en la petición
    (POST / PUT / PATCH). Es el único VO que puede llevar password.
    """
    email: Optional[str] = None
    password: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None

    # Campos que realmente vinieron en la petición (para PATCH)
    campos_informados: Set[str] = field(
        default_factory=set, repr=False, compare=False
    )

    CAMPOS = ("email", "password", "first_name", "last_name")

    @classmethod
    def desde_dict(cls, datos: dict):
        """Crea el VO a partir de validated_data, ignorando claves desconocidas."""
        filtrados = {k: v for k, v in datos.items() if k in cls.CAMPOS}
        return cls(**filtrados, campos_informados=set(filtrados.keys()))

    def a_dict_creacion(self) -> dict:
        """Datos para UsuarioDAO.crear_usuario (incluye password)."""
        return {
            "email": self.email,
            "password": self.password,
            "first_name": self.first_name,
            "last_name": self.last_name,
        }

    def a_dict_actualizacion(self, solo_informados: bool = False) -> dict:
        """
        Datos para actualizar el perfil. NUNCA incluye password:
        la contraseña solo se cambia con change_password.
        """
        datos = {
            "email": self.email,
            "first_name": self.first_name,
            "last_name": self.last_name,
        }

        if solo_informados:
            return {k: v for k, v in datos.items() if k in self.campos_informados}

        return datos