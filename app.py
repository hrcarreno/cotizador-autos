import streamlit as st
from supabase import create_client, Client

st.set_page_config(page_title="Cotizador BYD Inteligente", layout="wide", initial_sidebar_state="expanded")

# --- GESTIÓN DE TEMA ---
if "tema" not in st.session_state:
    st.session_state.tema = "Oscuro"

def aplicar_tema():
    if st.session_state.tema == "Claro":
        st.markdown("""
            <style>
                .stApp { background-color: #F3F4F6 !important; }
                [data-testid="stSidebar"] { background-color: #FFFFFF !important; }
                h1, h2, h3, h4, h5, h6, p, span, div, label, li { color: #111827 !important; }
                .stTextInput input, .stNumberInput input, .stTextArea textarea, .stSelectbox div[data-baseweb="select"] > div {
                    background-color: #FFFFFF !important; color: #111827 !important; border: 1px solid #D1D5DB !important;
                }
                [data-testid="stVerticalBlockBorderWrapper"] { background-color: #FFFFFF !important; border: 1px solid #E5E7EB !important; }
                .stButton button { background-color: #2563EB !important; color: #FFFFFF !important; }
            </style>
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
            <style>
                .stApp { background-color: #0F172A !important; }
                [data-testid="stSidebar"] { background-color: #1E293B !important; }
                h1, h2, h3, h4, h5, h6, p, span, div, label, li { color: #F8FAFC !important; }
                .stTextInput input, .stNumberInput input, .stTextArea textarea, .stSelectbox div[data-baseweb="select"] > div {
                    background-color: #0F172A !important; color: #F8FAFC !important; border: 1px solid #334155 !important;
                }
                [data-testid="stVerticalBlockBorderWrapper"] { background-color: #1E293B !important; border: 1px solid #334155 !important; }
                .stButton button { background-color: #3B82F6 !important; color: #FFFFFF !important; }
            </style>
        """, unsafe_allow_html=True)

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
    aplicar_tema()
    
    st.markdown("""
        <style>
            [data-testid="stSidebar"] { display: none !important; }
            .block-container { padding-top: 5rem; max-width: 500px; }
        </style>
    """, unsafe_allow_html=True)
    
    st.title("🔐 Acceso al Sistema")
    
    tab_login, tab_recuperar = st.tabs(["Ingresar", "Recuperar Contraseña"])
    
    with tab_login:
        with st.container(border=True):
            email = st.text_input("Correo Electrónico", placeholder="tu@email.com")
            password = st.text_input("Contraseña", type="password", placeholder="••••••••")
            if st.button("Ingresar", type="primary", use_container_width=True):
                login(email, password)
                
    with tab_recuperar:
        with st.container(border=True):
            st.write("Ingresá tu correo y te enviaremos un enlace mágico.")
            email_rec = st.text_input("Correo Electrónico", key="rec_email")
            if st.button("Enviar enlace", use_container_width=True):
                enviar_recuperacion(email_rec)
    
    st.stop()

# --- APLICACIÓN PRINCIPAL ---
aplicar_tema()

rol = st.session_state.user.user_metadata.get("rol", "Usuario")

with st.sidebar:
    st.markdown(f"### 👤 {st.session_state.user.email}")
    st.caption(f"Rol: **{rol}**")
    
    st.divider()
    st.caption("Apariencia")
    st.radio("Tema:", ["Oscuro", "Claro"], key="tema", horizontal=True, label_visibility="collapsed")
    aplicar_tema()
    
    st.divider()
    if st.button("Cerrar Sesión", use_container_width=True):
        logout()

# --- MENÚ DINÁMICO ---
paginas = [
    st.Page("pages/1_cotizador.py", title="Cotizador", icon="🚗"),
    st.Page("pages/3_crm.py", title="CRM", icon="📋"),
]

if rol == "Administrador":
    paginas.append(st.Page("pages/2_admin.py", title="Admin", icon="⚙️"))

pg = st.navigation(paginas)
pg.run()
