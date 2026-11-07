from typing import List

from gestion_usuarios.DAO.usuarioDAO import UsuarioDAO
from gestion_usuarios.VO.usuarioVO import UsuarioVO, UsuarioEntradaVO


class UsuarioService:
    """
    Capa de servicio de usuarios.
    Recibe/devuelve VOs; las vistas nunca tocan el DAO ni el modelo.
    Las excepciones del DAO (404, 400, 409, 500) se propagan a la vista.
    """

    # ---------- Consultas ----------
    def listar_usuarios(self) -> List[UsuarioVO]:
        usuarios = UsuarioDAO.obtener_todos()
        return [UsuarioVO.desde_modelo(u) for u in usuarios]

    def obtener_usuario(self, usuario_id) -> UsuarioVO:
        usuario = UsuarioDAO.obtener_usuario_por_id(usuario_id)
        return UsuarioVO.desde_modelo(usuario)

    # ---------- Escritura ----------
    def crear_usuario(self, entrada: UsuarioEntradaVO) -> UsuarioVO:
        usuario = UsuarioDAO.crear_usuario(**entrada.a_dict_creacion())
        return UsuarioVO.desde_modelo(usuario)

    def actualizar_usuario(self, usuario_id, entrada: UsuarioEntradaVO) -> UsuarioVO:
        # actualizar_usuario recibe un dict (no **kwargs)
        usuario = UsuarioDAO.actualizar_usuario(
            usuario_id,
            entrada.a_dict_actualizacion()
        )
        return UsuarioVO.desde_modelo(usuario)

    def actualizar_usuario_parcial(self, usuario_id, entrada: UsuarioEntradaVO) -> UsuarioVO:
        usuario = UsuarioDAO.actualizar_usuario_parcial(
            usuario_id,
            **entrada.a_dict_actualizacion(solo_informados=True)
        )
        return UsuarioVO.desde_modelo(usuario)

    # ---------- Estado ----------
    def eliminar_usuario(self, usuario_id) -> None:
        """Borrado lógico (is_active = False)."""
        UsuarioDAO.eliminar_usuario(usuario_id)

    def restaurar_usuario(self, usuario_id) -> UsuarioVO:
        usuario = UsuarioDAO.restaurar_usuario(usuario_id)
        return UsuarioVO.desde_modelo(usuario)

    def activar_usuario(self, usuario_id) -> UsuarioVO:
        usuario = UsuarioDAO.activar_usuario(usuario_id)
        return UsuarioVO.desde_modelo(usuario)

    def desactivar_usuario(self, usuario_id) -> None:
        UsuarioDAO.desactivar_usuario(usuario_id)

    def verificar_email(self, usuario_id) -> None:
        UsuarioDAO.verificar_email(usuario_id)

    # ---------- Contraseña ----------
    def cambiar_contrasena(self, usuario_id, actual: str, nueva: str, confirmacion: str) -> None:
        UsuarioDAO.actualizar_contrasena(usuario_id, actual, nueva, confirmacion)

    def solicitar_reset_password(self, email: str) -> dict:
        """
        Devuelve {"token", "expires_at"} para que la capa que envía el correo
        lo use. La vista NO debe exponer el token en la respuesta HTTP.
        """
        return UsuarioDAO.reset_password_request(email)

    def reset_password(self, token, nueva_contrasena: str) -> None:
        UsuarioDAO.reset_password(token, nueva_contrasena)

    # ---------- Roles ----------
    def asignar_roles(self, usuario_id, roles_ids) -> UsuarioVO:
        usuario = UsuarioDAO.asignar_roles(usuario_id, roles_ids)
        return UsuarioVO.desde_modelo(usuario)

    def quitar_roles(self, usuario_id, roles_ids) -> UsuarioVO:
        usuario = UsuarioDAO.quitar_roles(usuario_id, roles_ids)
        return UsuarioVO.desde_modelo(usuario)