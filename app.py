import streamlit as st

# ===== CONFIGURACIÓN (PRIMERO) =====
st.set_page_config(
    page_title="Cotizador",
    page_icon=None,
    layout="wide",
    initial_sidebar_state="expanded",
)

from auth import inicializar_auth, obtener_rol
from roles import ROLES, nombre_rol

# ===== INICIALIZAR AUTH =====
resultado = inicializar_auth()

if resultado is None:
    st.stop()

authenticator, df_usuarios = resultado

# ===== LOGIN =====
try:
    authenticator.login(location="main")
except Exception as e:
    st.error(f"Error en el login: {e}")
    st.stop()

# ===== VALIDAR ESTADO =====
authentication_status = st.session_state.get("authentication_status")
name = st.session_state.get("name")
username = st.session_state.get("username")

if authentication_status is False:
    st.error("Usuario o contraseña incorrectos.")
    st.stop()

if authentication_status is None:
    st.info("Ingresá tu usuario y contraseña para continuar.")
    st.stop()

# ===== USUARIO AUTENTICADO =====
rol = obtener_rol(username, df_usuarios)

if rol is None:
    st.error(f"El usuario {username} no tiene un rol asignado. Contactá al administrador.")
    authenticator.logout("Cerrar sesión", location="sidebar")
    st.stop()

# ===== SIDEBAR =====
with st.sidebar:
    st.markdown(f"### Hola, {name}")
    st.caption(f"Rol: {nombre_rol(rol)}")
    st.markdown("---")

# ===== NAVEGACIÓN SEGÚN ROL =====
paginas = []

# Todos pueden cotizar
paginas.append(st.Page("pages/1_cotizador.py", title="Cotizador", icon=None))

# Supervisor y admin
if rol in ["supervisor", "admin"]:
    paginas.append(st.Page("pages/2_autorizaciones.py", title="Autorizaciones", icon=None))

# Solo admin
if rol == "admin":
    paginas.append(st.Page("pages/3_usuarios.py", title="Usuarios", icon=None))

# Supervisor y admin
if rol in ["supervisor", "admin"]:
    paginas.append(st.Page("pages/4_configuracion.py", title="Configuración", icon=None))

# ===== LOGOUT EN SIDEBAR =====
authenticator.logout("Cerrar sesión", location="sidebar")

# ===== RENDERIZAR NAVEGACIÓN =====
pg = st.navigation(paginas)
pg.run()
