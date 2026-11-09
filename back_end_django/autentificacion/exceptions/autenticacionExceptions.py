class AutenticacionError(Exception):
    """Base de las excepciones del módulo de autenticación."""
    mensaje_por_defecto = "Error de autenticación."

    def __init__(self, mensaje=None):
        super().__init__(mensaje or self.mensaje_por_defecto)


class CredencialesInvalidas_401(AutenticacionError):
    mensaje_por_defecto = "Credenciales inválidas."


class TokenInvalido_400(AutenticacionError):
    mensaje_por_defecto = "Token inválido o ya expirado."


class TokenAjeno_403(AutenticacionError):
    mensaje_por_defecto = "El token no pertenece al usuario autenticado."


class LogNoDisponible_500(AutenticacionError):
    mensaje_por_defecto = "No fue posible leer el archivo de logs."