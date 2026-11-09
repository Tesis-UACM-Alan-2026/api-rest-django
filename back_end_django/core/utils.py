import logging

logger_auditoria = logging.getLogger("auditoria")


def obtener_ip(request):
    """Extrae la IP real del cliente, considerando proxies y balanceadores."""
    x_forwarded = request.META.get("HTTP_X_FORWARDED_FOR")

    if x_forwarded:
        return x_forwarded.split(",")[0].strip()

    return request.META.get("REMOTE_ADDR", "IP desconocida")


def auditar(ip, accion, request, **extra):
    """Registra una línea de auditoría con formato uniforme."""
    detalle = "".join(f" [{k}:{v}]" for k, v in extra.items())

    logger_auditoria.info(
        f"[ip:{ip}] [accion:{accion}] [realizado_por:{request.user}]{detalle}"
    )