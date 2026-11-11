import streamlit as st
import streamlit.components.v1 as components
from supabase import create_client, Client

# Forzamos que la barra lateral esté ABIERTA
st.set_page_config(page_title="Cotizador BYD Inteligente", layout="wide", initial_sidebar_state="expanded")

# --- 1. GESTIÓN DE TEMA Y CSS GLOBAL ---
if "tema" not in st.session_state:
    st.session_state.tema = "Oscuro"

def aplicar_tema():
    # CSS para ocultar SOLO los botones de Streamlit y estilizar la barra lateral
    st.markdown("""
        <style>
            /* Ocultamos el menú de opciones y el botón de Deploy */
            #MainMenu { visibility: hidden !important; }
            [data-testid="stToolbar"] { display: none !important; }
            .stDeployButton { display: none !important; }
            footer { visibility: hidden !important; }
            
            /* Ocultamos la flechita nativa de Streamlit (la reemplazaremos por JS) */
            [data-testid="stSidebarCollapseButton"] { display: none !important; }
            
            /* Importar fuente Inter */
            @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
            * { font-family: 'Inter', sans-serif !important; }
        </style>
    """, unsafe_allow_html=True)

    # --- MODO CLARO PREMIUM ---
    if st.session_state.tema == "Claro":
        st.markdown("""
            <style>
                .stApp { background-color: #F3F4F6 !important; }
                [data-testid="stSidebar"] { background-color: #FFFFFF !important; border-right: 1px solid #E5E7EB; }
                [data-testid="stSidebar"] * { color: #111827 !important; }
                h1, h2, h3, h4, h5, h6, p, span, div, label, li { color: #111827 !important; }
                .stTextInput input, .stNumberInput input, .stTextArea textarea, .stSelectbox div[data-baseweb="select"] > div {
                    background-color: #FFFFFF !important; color: #111827 !important; border: 1px solid #D1D5DB !important; border-radius: 8px !important;
                }
                [data-testid="stVerticalBlockBorderWrapper"] { 
                    background-color: #FFFFFF !important; border: 1px solid #E5E7EB !important; border-radius: 12px !important; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05) !important;
                }
                .stButton button { background-color: #2563EB !important; color: #FFFFFF !important; border-radius: 8px !important; font-weight: 600 !important; }
            </style>
        """, unsafe_allow_html=True)
    else:
        # --- MODO OSCURO PREMIUM ---
        st.markdown("""
            <style>
                .stApp { background-color: #0F172A !important; }
                [data-testid="stSidebar"] { background-color: #1E293B !important; border-right: 1px solid #334155; }
                [data-testid="stSidebar"] * { color: #F8FAFC !important; }
                h1, h2, h3, h4, h5, h6, p, span, div, label, li { color: #F8FAFC !important; }
                .stTextInput input, .stNumberInput input, .stTextArea textarea, .stSelectbox div[data-baseweb="select"] > div {
                    background-color: #0F172A !important; color: #F8FAFC !important; border: 1px solid #334155 !important; border-radius: 8px !important;
                }
                [data-testid="stVerticalBlockBorderWrapper"] { 
                    background-color: #1E293B !important; border: 1px solid #334155 !important; border-radius: 12px !important; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.3) !important;
                }
                .stButton button { background-color: #3B82F6 !important; color: #FFFFFF !important; border-radius: 8px !important; font-weight: 600 !important; }
            </style>
        """, unsafe_allow_html=True)

# --- INYECCIÓN DE BOTÓN FLOTANTE PARA ABRIR LA BARRA LATERAL ---
# Este script se asegura de que siempre haya un botón para abrir la barra, incluso si Streamlit lo oculta.
def boton_abrir_sidebar():
    components.html(
        """
        <script>
            function checkSidebar() {
                const sidebar = window.parent.document.querySelector('[data-testid="stSidebar"]');
                if (sidebar) {
                    // Si la barra lateral está colapsada, mostramos el botón
                    if (sidebar.getAttribute('aria-expanded') === 'false') {
                        let btn = window.parent.document.getElementById('custom-sidebar-btn');
                        if (!btn) {
                            btn = window.parent.document.createElement('button');
                            btn.id = 'custom-sidebar-btn';
                            btn.innerHTML = '☰';
                            btn.style.position = 'fixed';
                            btn.style.top = '15px';
                            btn.style.left = '15px';
                            btn.style.zIndex = '999999';
                            btn.style.padding = '10px 15px';
                            btn.style.backgroundColor = '#2563EB';
                            btn.style.color = 'white';
                            btn.style.border = 'none';
                            btn.style.borderRadius = '8px';
                            btn.style.cursor = 'pointer';
                            btn.style.fontSize = '20px';
                            btn.onclick = function() {
                                const toggleBtn = window.parent.document.querySelector('[data-testid="collapsedControl"]');
                                if (toggleBtn) toggleBtn.click();
                            };
                            window.parent.document.body.appendChild(btn);
                        }
                    } else {
                        // Si está abierta, ocultamos el botón
                        const btn = window.parent.document.getElementById('custom-sidebar-btn');
                        if (btn) btn.remove();
                    }
                }
            }
            // Revisamos cada segundo si la barra se cerró
            setInterval(checkSidebar, 1000);
            checkSidebar();
        </script>
        """,
        height=0,
    )

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
    boton_abrir_sidebar() # Inyectamos el botón por si la barra está cerrada
    
    st.markdown("<style>[data-testid='stSidebarNav'] {display: none;}</style>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 1.2, 1])
    with col2:
        st.markdown("<br><br>", unsafe_allow_html=True)
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
        
        st.markdown("<br>", unsafe_allow_html=True)
        c1, c2, c3 = st.columns([1, 1, 1])
        with c2:
            st.radio("Tema:", ["Oscuro", "Claro"], key="tema", horizontal=True, label_visibility="collapsed")
        aplicar_tema()
    
    st.stop()

# --- 5. APLICACIÓN PRINCIPAL ---
aplicar_tema()
boton_abrir_sidebar() # Inyectamos el botón por si la barra está cerrada

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

# --- 6. MENÚ DINÁMICO ---
paginas = [
    st.Page("pages/1_cotizador.py", title="Cotizador", icon="🚗"),
    st.Page("pages/3_crm.py", title="CRM", icon="📋"),
]

if rol == "Administrador":
    paginas.append(st.Page("pages/2_admin.py", title="Admin", icon="⚙️"))

pg = st.navigation(paginas)
pg.run()
