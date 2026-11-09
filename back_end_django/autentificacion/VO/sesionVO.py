import uuid
from dataclasses import dataclass
from typing import Optional


@dataclass
class SesionVO:
    """
    Resultado de un inicio de sesión.
    access y refresh se devuelven al cliente; usuario_id y email
    quedan para la auditoría y no se exponen en la respuesta.
    """
    access: str
    refresh: str
    usuario_id: Optional[uuid.UUID] = None
    email: Optional[str] = None