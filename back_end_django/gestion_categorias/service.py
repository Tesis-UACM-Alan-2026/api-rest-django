from typing import List

from gestion_categorias.DAO.categoriaDAO import CategoriaDAO
from gestion_categorias.VO.categoriaVO import CategoriaVO


class CategoriaService:
    """
    Capa de servicio de categorías.
    Recibe/devuelve VOs; las excepciones del DAO
    (CategoriaNoEncontrada_404, CategoriaDuplicada_409, CategoriaConProductos_409)
    se propagan a la vista.
    """

    def listar_categorias(self) -> List[CategoriaVO]:
        categorias = CategoriaDAO.obtener_todas()
        return [CategoriaVO.desde_modelo(c) for c in categorias]

    def obtener_categoria(self, categoria_id) -> CategoriaVO:
        categoria = CategoriaDAO.obtener_por_id(categoria_id)
        return CategoriaVO.desde_modelo(categoria)

    def crear_categoria(self, categoria_vo: CategoriaVO) -> CategoriaVO:
        categoria = CategoriaDAO.crear_categoria(**categoria_vo.a_dict())
        return CategoriaVO.desde_modelo(categoria)

    def actualizar_categoria(self, categoria_id, categoria_vo: CategoriaVO) -> CategoriaVO:
        categoria = CategoriaDAO.actualizar_categoria(
            categoria_id,
            **categoria_vo.a_dict(solo_informados=True)
        )
        return CategoriaVO.desde_modelo(categoria)

    def actualizar_categoria_parcial(self, categoria_id, categoria_vo: CategoriaVO) -> CategoriaVO:
        categoria = CategoriaDAO.actualizar_categoria_parcial(
            categoria_id,
            **categoria_vo.a_dict(solo_informados=True)
        )
        return CategoriaVO.desde_modelo(categoria)

    def eliminar_categoria(self, categoria_id) -> None:
        CategoriaDAO.eliminar_categoria(categoria_id)