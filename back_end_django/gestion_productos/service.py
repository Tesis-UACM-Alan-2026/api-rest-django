from decimal import Decimal
from typing import List

from gestion_productos.DAO.productoDAO import ProductoDAO
from gestion_productos.VO.productoVO import ProductoVO


class ProductoService:

    def listar_productos(self) -> List[ProductoVO]:
        productos = ProductoDAO.obtener_todos()
        return [ProductoVO.desde_modelo(p) for p in productos]

    def obtener_producto(self, producto_id) -> ProductoVO:
        # Lanza ProductoNoEncontrado_404 si no existe
        producto = ProductoDAO.obtener_producto_por_id(producto_id)
        return ProductoVO.desde_modelo(producto)

    def crear_producto(self, producto_vo: ProductoVO) -> ProductoVO:
        producto = ProductoDAO.crear_producto(**producto_vo.a_dict())
        return ProductoVO.desde_modelo(producto)

    def actualizar_producto(self, producto_id, producto_vo: ProductoVO) -> ProductoVO:
        producto = ProductoDAO.actualizar_producto(
            producto_id,
            **producto_vo.a_dict()
        )
        return ProductoVO.desde_modelo(producto)

    def actualizar_producto_parcial(self, producto_id, producto_vo: ProductoVO) -> ProductoVO:
        producto = ProductoDAO.actualizar_producto_parcial(
            producto_id,
            **producto_vo.a_dict(solo_informados=True)
        )
        return ProductoVO.desde_modelo(producto)

    def eliminar_producto(self, producto_id) -> None:
        # Tu lógica actual de eliminación (ya existente)
        ...

    def buscar_productos(self, texto: str) -> List[ProductoVO]:
        productos = ProductoDAO.buscar_productos(texto)
        return [ProductoVO.desde_modelo(p) for p in productos]

    def filtrar_por_rango_precio(self, precio_min: Decimal, precio_max: Decimal) -> List[ProductoVO]:
        productos = ProductoDAO.filtrar_por_rango_precio(precio_min, precio_max)
        return [ProductoVO.desde_modelo(p) for p in productos]