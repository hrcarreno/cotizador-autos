import streamlit as st
from supabase import create_client, Client

st.set_page_config(page_title="Cotizador BYD Inteligente", layout="wide", initial_sidebar_state="collapsed")

# --- 1. CONFIGURACIÓN DEL TEMA (MODO CLARO / OSCURO) ---
if "tema" not in st.session_state:
    st.session_state.tema = "Oscuro"

def aplicar_tema():
    if st.session_state.tema == "Claro":
        st.markdown("""
            <style>
                /* Fondo general */
                .stApp { background-color: #f8f9fa; color: #1b2430; }
                [data-testid="stSidebar"] { background-color: #ffffff; border-right: 1px solid #e0e0e0; }
                
                /* Textos generales */
                h1, h2, h3, h4, h5, h6, p, span, label, div { color: #1b2430 !important; }
                
                /* Inputs, selects y textareas */
                .stTextInput input, .stNumberInput input, .stTextArea textarea, .stSelectbox div[data-baseweb="select"] > div {
                    background-color: #ffffff !important; 
                    color: #1b2430 !important;
                    border: 1px solid #cccccc !important;
                }
                
                /* Botones */
                .stButton button { 
                    background-color: #1f78b4 !important; 
                    color: white !important; 
                    border: none !important;
                }
                .stButton button:hover { background-color: #155a8a !important; }
                
                /* Pestañas y Expanders */
                .stTabs [data-baseweb="tab-list"] { background-color: #ffffff; }
                .stTabs [data-baseweb="tab"] { color: #1b2430 !important; }
                .streamlit-expanderHeader { color: #1b2430 !important; background-color: #ffffff !important; }
                
                /* Tablas */
                [data-testid="stTable"] table { background-color: #ffffff !important; color: #1b2430 !important; }
                [data-testid="stDataFrame"] { color: #1b2430 !important; }
                
                /* Métricas */
                [data-testid="stMetricValue"] { color: #1b2430 !important; }
                [data-testid="stMetricLabel"] { color: #555555 !important; }
                
                /* Contenedores con borde */
                [data-testid="stVerticalBlockBorderWrapper"] { background-color: #ffffff; border-color: #e0e0e0 !important; }
            </style>
        """, unsafe_allow_html=True)
    else:
        # Modo oscuro (por defecto, no forzamos casi nada para no romper lo nativo)
        st.markdown("""
            <style>
                .stApp { background-color: #0e1117; color: #fafafa; }
                [data-testid="stSidebar"] { background-color: #262730; }
            </style>
        """, unsafe_allow_html=True)

# --- 2. CONEXIÓN SUPABASE ---
@st.cache_resource
def init_connection() -> Client:
    return create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])

supabase = init_connection()

# --- 3. LÓGICA DE AUTENTICACIÓN ---
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

# --- 4. PANTALLA DE LOGIN ---
if st.session_state.user is None:
    aplicar_tema() 
    
    st.markdown("<style>[data-testid='stSidebarNav'] {display: none;}</style>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 1.5, 1])
    with col2:
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
                st.write("Ingresá tu correo y te enviaremos un enlace mágico.")
                email_rec = st.text_input("Correo Electrónico", key="rec_email")
                if st.button("Enviar enlace", use_container_width=True):
                    enviar_recuperacion(email_rec)
        
        st.divider()
        st.radio("Preferencia de Tema:", ["Oscuro", "Claro"], key="tema", horizontal=True)
        aplicar_tema()
    
    st.stop()

# --- 5. APLICACIÓN PRINCIPAL (SI ESTÁ LOGUEADO) ---
aplicar_tema()

rol = st.session_state.user.user_metadata.get("rol", "Usuario")

with st.sidebar:
    st.write(f"👤 **{st.session_state.user.email}**")
    st.caption(f"Rol: {rol}")
    
    st.divider()
    st.radio("Tema de la App:", ["Oscuro", "Claro"], key="tema", horizontal=True)
    aplicar_tema()
    
    st.divider()
    if st.button("Cerrar Sesión", use_container_width=True):
        logout()

# --- 6. MENÚ DINÁMICO SEGÚN ROL ---
paginas = [
    st.Page("pages/1_cotizador.py", title="Cotizador", icon="🚗"),
    st.Page("pages/3_crm.py", title="CRM", icon="📋"),
]

if rol == "Administrador":
    paginas.append(st.Page("pages/2_admin.py", title="Admin", icon="⚙️"))

pg = st.navigation(paginas)
pg.run()
