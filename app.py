import streamlit as st
from supabase import create_client, Client

st.set_page_config(page_title="Cotizador BYD Inteligente", layout="wide", initial_sidebar_state="collapsed")

# --- 1. GESTIÓN DE TEMA PROFESIONAL ---
if "tema" not in st.session_state:
    st.session_state.tema = "Oscuro"

def aplicar_tema():
    if st.session_state.tema == "Claro":
        # INYECCIÓN QUIRÚRGICA DE CSS PARA MODO CLARO
        st.markdown("""
            <style>
                /* Variables base */
                :root { color-scheme: light; }
                
                /* Fondo general de la app */
                .stApp { background-color: #F8FAFC; }
                
                /* Sidebar */
                [data-testid="stSidebar"] { background-color: #FFFFFF; border-right: 1px solid #E2E8F0; }
                
                /* Textos generales */
                h1, h2, h3, h4, h5, h6, p, span, div, label { color: #1E293B !important; }
                
                /* Inputs, Selects, Textareas */
                .stTextInput input, .stNumberInput input, .stTextArea textarea, 
                .stSelectbox div[data-baseweb="select"] > div,
                .stMultiSelect div[data-baseweb="select"] > div {
                    background-color: #FFFFFF !important; 
                    color: #1E293B !important;
                    border: 1px solid #CBD5E1 !important;
                    border-radius: 8px !important;
                }
                
                /* Botones */
                .stButton button { 
                    background-color: #1E40AF !important; /* Azul profundo */
                    color: #FFFFFF !important; 
                    border: none !important;
                    border-radius: 8px !important;
                    transition: all 0.2s ease;
                }
                .stButton button:hover { background-color: #1D4ED8 !important; }
                
                /* Pestañas */
                .stTabs [data-baseweb="tab-list"] { background-color: #FFFFFF; border-radius: 8px; padding: 4px; }
                .stTabs [data-baseweb="tab"] { color: #64748B !important; }
                .stTabs [aria-selected="true"] { color: #1E40AF !important; font-weight: bold; }
                
                /* Expanders */
                .streamlit-expanderHeader { 
                    background-color: #FFFFFF !important; 
                    color: #1E293B !important; 
                    border: 1px solid #E2E8F0 !important;
                    border-radius: 8px !important;
                }
                .streamlit-expanderContent { background-color: #FFFFFF !important; }
                
                /* Tablas de datos */
                [data-testid="stTable"], [data-testid="stDataFrame"] { 
                    background-color: #FFFFFF !important; 
                    color: #1E293B !important; 
                    border: 1px solid #E2E8F0 !important;
                }
                
                /* Métricas del CRM */
                [data-testid="stMetricValue"] { color: #0F172A !important; }
                [data-testid="stMetricLabel"] { color: #64748B !important; }
                
                /* Contenedores con borde (Cards) */
                [data-testid="stVerticalBlockBorderWrapper"] { 
                    background-color: #FFFFFF !important; 
                    border: 1px solid #E2E8F0 !important; 
                    border-radius: 12px !important;
                    box-shadow: 0 1px 3px rgba(0,0,0,0.05) !important;
                }
                
                /* Ajuste para el botón de píldora (radio horizontal) */
                div[role="radiogroup"] > label { 
                    background-color: #E2E8F0; 
                    padding: 8px 16px; 
                    border-radius: 20px; 
                    color: #1E293B !important;
                }
                div[role="radiogroup"] > label[data-checked="true"] {
                    background-color: #1E40AF; 
                    color: white !important;
                }
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
        st.caption("Preferencia de visualización")
        st.radio("Tema:", ["Oscuro", "Claro"], key="tema", horizontal=True, label_visibility="collapsed")
        aplicar_tema()
    
    st.stop()

# --- 5. APLICACIÓN PRINCIPAL (SI ESTÁ LOGUEADO) ---
aplicar_tema()

rol = st.session_state.user.user_metadata.get("rol", "Usuario")

with st.sidebar:
    st.write(f"👤 **{st.session_state.user.email}**")
    st.caption(f"Rol: {rol}")
    
    st.divider()
    st.caption("Preferencia de visualización")
    st.radio("Tema:", ["Oscuro", "Claro"], key="tema", horizontal=True, label_visibility="collapsed")
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
