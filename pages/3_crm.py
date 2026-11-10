import streamlit as st
import hashlib

st.set_page_config(page_title="Sistema Concesionaria", layout="wide")

# --- FUNCIÓN PARA ENCRIPTAR CONTRASEÑAS ---
def hash_password(password):
    return hashlib.sha256(str.encode(password)).hexdigest()

# --- BASE DE DATOS DE USUARIOS (En el código para simplificar) ---
# Para cambiar la contraseña, cambiá el texto antes de hash_password()
USUARIOS = {
    "hrcarreno": {"pass": hash_password("admin123"), "nombre": "Hernán (Admin)", "rol": "admin"},
    "seba": {"pass": hash_password("seba123"), "nombre": "Seba", "rol": "vendedor"},
    "luis": {"pass": hash_password("luis123"), "nombre": "Luis", "rol": "vendedor"},
    "damian": {"pass": hash_password("damian123"), "nombre": "Damián", "rol": "vendedor"},
}

# --- ESTADO DE LA SESIÓN ---
if "logueado" not in st.session_state:
    st.session_state.logueado = False

# --- FORMULARIO DE LOGIN ---
if not st.session_state.logueado:
    st.title("🔐 Acceso al Sistema")
    with st.form("login_form"):
        usuario_input = st.text_input("Usuario").lower()
        pass_input = st.text_input("Contraseña", type="password")
        submit = st.form_submit_button("Ingresar", type="primary")
        
        if submit:
            if usuario_input in USUARIOS and USUARIOS[usuario_input]["pass"] == hash_password(pass_input):
                st.session_state.logueado = True
                st.session_state.usuario = usuario_input
                st.session_state.nombre = USUARIOS[usuario_input]["nombre"]
                st.session_state.rol = USUARIOS[usuario_input]["rol"]
                st.rerun()
            else:
                st.error("Usuario o contraseña incorrectos.")
    st.stop() # Detiene la app acá hasta que se loguee

# --- BARRA LATERAL (Si ya está logueado) ---
with st.sidebar:
    st.markdown(f"👤 **{st.session_state.nombre}**")
    st.caption(f"Rol: {st.session_state.rol.capitalize()}")
    if st.button("Cerrar Sesión", use_container_width=True):
        st.session_state.logueado = False
        st.rerun()

# --- ROUTER PRINCIPAL ---
pg = st.navigation([
    st.Page("pages/1_cotizador.py", title="Cotizador", icon="🚗"),
    st.Page("pages/2_admin.py", title="Admin", icon="⚙️"),
    st.Page("pages/3_crm.py", title="CRM", icon="📋"),
])
pg.run()
