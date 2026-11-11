import streamlit as st
from supabase import create_client, Client

st.set_page_config(page_title="Cotizador BYD Inteligente", layout="wide", initial_sidebar_state="collapsed")

# --- CONEXIÓN SUPABASE ---
@st.cache_resource
def init_connection() -> Client:
    return create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])

supabase = init_connection()

# --- LÓGICA DE AUTENTICACIÓN ---
if "user" not in st.session_state:
    st.session_state.user = None

def login(email, password):
    try:
        res = supabase.auth.sign_in_with_password({"email": email, "password": password})
        st.session_state.user = res.user
        st.rerun()
    except Exception as e:
        st.error("Usuario o contraseña incorrectos.")

def logout():
    supabase.auth.sign_out()
    st.session_state.user = None
    st.rerun()

def enviar_recuperacion(email):
    try:
        supabase.auth.reset_password_for_email(email)
        st.success("Te enviamos un correo con el enlace para restablecer tu contraseña.")
    except Exception as e:
        st.error(f"Error al enviar el correo: {e}")

# --- PANTALLA DE LOGIN ---
if st.session_state.user is None:
    # Ocultamos el menú solo si no está logueado
    st.markdown("""
    <style>
        [data-testid="stSidebarNav"] {display: none;}
    </style>
    """, unsafe_allow_html=True)
    
    st.title("🔐 Acceso al Sistema")
    
    tab_login, tab_recuperar = st.tabs(["Ingresar", "Recuperar Contraseña"])
    
    with tab_login:
        with st.container(border=True):
            email = st.text_input("Correo Electrónico")
            password = st.text_input("Contraseña", type="password")
            if st.button("Ingresar", type="primary", use_container_width=True):
                login(email, password)
                
    with tab_recuperar:
        with st.container(border=True):
            st.write("Ingresá tu correo y te enviaremos un enlace mágico para crear una nueva contraseña.")
            email_rec = st.text_input("Correo Electrónico", key="rec_email")
            if st.button("Enviar enlace", use_container_width=True):
                enviar_recuperacion(email_rec)
    
    st.stop() # Evita que se cargue el resto de la app

# --- SI ESTÁ LOGUEADO, MOSTRAMOS EL MENÚ ---
rol = st.session_state.user.user_metadata.get("rol", "Usuario")

with st.sidebar:
    st.write(f"👤 **{st.session_state.user.email}**")
    st.caption(f"Rol: {rol}")
    if st.button("Cerrar Sesión", use_container_width=True):
        logout()

# --- MENÚ DINÁMICO SEGÚN EL ROL ---
paginas = [
    st.Page("pages/1_cotizador.py", title="Cotizador", icon="🚗"),
    st.Page("pages/3_crm.py", title="CRM", icon="📋"),
]

if rol == "Administrador":
    paginas.append(st.Page("pages/2_admin.py", title="Admin", icon="⚙️"))

pg = st.navigation(paginas)
pg.run()
