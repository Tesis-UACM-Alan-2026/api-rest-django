from collections import deque
from pathlib import Path

from django.conf import settings

from autentificacion.exceptions.autenticacionExceptions import LogNoDisponible_500


class LogDAO:
    """
    Acceso a los archivos de log. Solo se pueden leer los archivos de esta
    lista blanca; el nombre nunca viene del cliente.
    """

    ARCHIVOS = {
        "auditoria": "auditoria.log",
        "tecnico": "tecnico.log",
    }

    @staticmethod
    def leer(tipo, filtros=None, limite=100):
        """
        Devuelve las últimas `limite` líneas que cumplan TODOS los filtros
        (búsqueda sin distinguir mayúsculas), de la más reciente a la más antigua.
        Se recorre el archivo línea a línea; en memoria solo quedan `limite` líneas.
        """
        if tipo not in LogDAO.ARCHIVOS:
            raise ValueError(f"Tipo de log desconocido: {tipo}")

        ruta = Path(settings.LOGS_DIR) / LogDAO.ARCHIVOS[tipo]

        if not ruta.exists():
            return []

        terminos = [v.lower() for v in (filtros or {}).values() if v]
        ultimas = deque(maxlen=limite)

        try:
            with open(ruta, encoding="utf-8", errors="replace") as archivo:
                for linea in archivo:
                    # Solo líneas que inician un registro (se omiten tracebacks)
                    if not linea.startswith("["):
                        continue

                    texto = linea.lower()
                    if all(t in texto for t in terminos):
                        ultimas.append(linea.strip())
        except OSError:
            raise LogNoDisponible_500()

        return list(reversed(ultimas))