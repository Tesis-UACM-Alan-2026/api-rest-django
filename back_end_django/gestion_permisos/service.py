from typing import List
from gestion_permisos.DAO.permisoDAO import PermisoDAO
from gestion_permisos.DAO.rolDAO import RolDAO
from gestion_permisos.VO.permisoVO import PermisoVO
from gestion_permisos.VO.rolVO import RolVO


class PermisoService:
    """
    Servicio de permisos. Recibe/devuelve VOs; las excepciones del DAO
    se propagan a la vista.
    """

    def listar_permisos(self) -> List[PermisoVO]:
        return [PermisoVO.desde_modelo(p) for p in PermisoDAO.obtener_todos()]

    def obtener_permiso(self, permiso_id) -> PermisoVO:
        return PermisoVO.desde_modelo(PermisoDAO.obtener_por_id(permiso_id))

    def crear_permiso(self, permiso_vo: PermisoVO) -> PermisoVO:
        permiso = PermisoDAO.crear_permiso(**permiso_vo.a_dict())
        return PermisoVO.desde_modelo(permiso)

    def actualizar_permiso(self, permiso_id, permiso_vo: PermisoVO) -> PermisoVO:
        permiso = PermisoDAO.actualizar_permiso(
            permiso_id,
            **permiso_vo.a_dict(solo_informados=True)
        )
        return PermisoVO.desde_modelo(permiso)

    def actualizar_permiso_parcial(self, permiso_id, permiso_vo: PermisoVO) -> PermisoVO:
        permiso = PermisoDAO.actualizar_permiso_parcial(
            permiso_id,
            **permiso_vo.a_dict(solo_informados=True)
        )
        return PermisoVO.desde_modelo(permiso)

    def eliminar_permiso(self, permiso_id) -> None:
        PermisoDAO.eliminar_permiso(permiso_id)

    def obtener_codenames_usuario(self, usuario_id) -> set:
        """Codenames de los permisos efectivos de un usuario (vía sus roles)."""
        return PermisoDAO.obtener_codenames_por_usuario(usuario_id)


class RolService:
    """Servicio de roles y de la relación Rol-Permiso."""

    def listar_roles(self) -> List[RolVO]:
        return [RolVO.desde_modelo(r) for r in RolDAO.obtener_todos()]

    def obtener_rol(self, rol_id) -> RolVO:
        return RolVO.desde_modelo(RolDAO.obtener_por_id(rol_id))

    def crear_rol(self, rol_vo: RolVO) -> RolVO:
        rol = RolDAO.crear_rol(**rol_vo.a_dict())
        return RolVO.desde_modelo(rol)

    def actualizar_rol(self, rol_id, rol_vo: RolVO) -> RolVO:
        rol = RolDAO.actualizar_rol(
            rol_id,
            **rol_vo.a_dict(solo_informados=True)
        )
        return RolVO.desde_modelo(rol)

    def actualizar_rol_parcial(self, rol_id, rol_vo: RolVO) -> RolVO:
        rol = RolDAO.actualizar_rol_parcial(
            rol_id,
            **rol_vo.a_dict(solo_informados=True)
        )
        return RolVO.desde_modelo(rol)

    def eliminar_rol(self, rol_id) -> None:
        RolDAO.eliminar_rol(rol_id)

    def asignar_permisos(self, rol_id, permisos_ids) -> RolVO:
        return RolVO.desde_modelo(RolDAO.asignar_permisos(rol_id, permisos_ids))

    def quitar_permisos(self, rol_id, permisos_ids) -> RolVO:
        return RolVO.desde_modelo(RolDAO.quitar_permisos(rol_id, permisos_ids))