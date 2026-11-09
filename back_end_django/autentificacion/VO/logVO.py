from dataclasses import dataclass, field
from typing import Dict, List


@dataclass
class LogConsultaVO:
    """Resultado de consultar un archivo de log."""
    total: int
    filtros_aplicados: Dict[str, str] = field(default_factory=dict)
    entradas: List[str] = field(default_factory=list)