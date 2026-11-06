######################CODIGO 14############################
from dataclasses import dataclass
from datetime import date
from typing import Optional
from uuid import UUID

@dataclass
class UsuarioDTO:
    """
    Data Transfer Object (DTO) para la entidad Usuario.
    Define los datos que se transfieren entre la base de datos y la aplicación.
    """
    id: UUID
    email: str
    first_name: str
    last_name: str