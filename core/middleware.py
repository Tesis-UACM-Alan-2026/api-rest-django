class RequestResponseMiddleware:
    """
    Middleware personalizado para modificar o inspeccionar solicitudes y respuestas.

    Ejemplo: Agrega cabeceras o loguea información para trazabilidad.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Aquí puedes agregar lógica antes de ejecutar la vista
        response = self.get_response(request)
        # Aquí puedes modificar la respuesta antes de devolverla
        response["X-Api-Version"] = "1.0"
        return response
