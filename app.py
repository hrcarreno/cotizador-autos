import streamlit as st

st.set_page_config(page_title="Cotizador BYD Inteligente", layout="wide")

# --- LOGIN DE EMERGENCIA ---
if "autenticado" not in st.session_state:
    st.session_state.autenticado = False

if not st.session_state.autenticado:
    st.title("🔐 Acceso al Sistema")
    
    with st.container(border=True):
        usuario = st.text_input("Usuario")
        password = st.text_input("Contraseña", type="password")
        
        if st.button("Ingresar", type="primary"):
            # ACÁ PONÉS EL USUARIO Y CONTRASEÑA QUE QUIERAS USAR
            if usuario == "hrcarreno" and password == "admin123":
                st.session_state.autenticado = True
                st.rerun()
            else:
                st.error("Usuario o contraseña incorrectos.")
    st.stop() # Detiene la ejecución para que no cargue el menú hasta que se loguee

# --- MENÚ PRINCIPAL (UNA VEZ LOGUEADO) ---
pg = st.navigation([
    st.Page("pages/1_cotizador.py", title="Cotizador", icon="🚗"),
    st.Page("pages/2_admin.py", title="Admin", icon="⚙️"),
    st.Page("pages/3_crm.py", title="CRM", icon="📋"),
])

# Agregamos un botón para cerrar sesión en la barra lateral
with st.sidebar:
    st.write("---")
    if st.button("Cerrar Sesión"):
        st.session_state.autenticado = False
        st.rerun()

pg.run()
