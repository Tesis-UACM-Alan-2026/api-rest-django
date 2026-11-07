class CategoriaError(Exception):
    """Base de las excepciones del módulo de categorías."""
    mensaje_por_defecto = "Error en la categoría."

    def __init__(self, mensaje=None):
        super().__init__(mensaje or self.mensaje_por_defecto)


class CategoriaNoEncontrada_404(CategoriaError):
    mensaje_por_defecto = "Categoría no encontrada."


class CategoriaDuplicada_409(CategoriaError):
    mensaje_por_defecto = "Ya existe una categoría con ese nombre."


class CategoriaConProductos_409(CategoriaError):
    mensaje_por_defecto = (
        "No se puede eliminar la categoría porque tiene productos asociados."
    )