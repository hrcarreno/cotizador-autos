"""
Definición de roles y permisos del sistema.
"""

# ===== ROLES DISPONIBLES =====
ROLES = {
    "vendedor": {
        "nombre": "Vendedor/a",
        "permisos": ["cotizar"],
    },
    "supervisor": {
        "nombre": "Supervisor/a",
        "permisos": ["cotizar", "autorizar", "configurar_dolar"],
    },
    "admin": {
        "nombre": "Administrador/a",
        "permisos": ["cotizar", "autorizar", "configurar_dolar", "configurar", "gestionar_usuarios"],
    },
}


def tiene_permiso(rol, permiso):
    """Verifica si un rol tiene un permiso específico."""
    if rol not in ROLES:
        return False
    return permiso in ROLES[rol]["permisos"]


def nombre_rol(rol):
    """Devuelve el nombre legible del rol."""
    return ROLES.get(rol, {}).get("nombre", rol)
