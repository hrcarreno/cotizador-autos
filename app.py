import streamlit as st
import streamlit.components.v1 as components
from supabase import create_client, Client

st.set_page_config(page_title="Cotizador BYD Inteligente", layout="wide", initial_sidebar_state="expanded")

# --- 1. GESTIÓN DE TEMA Y CSS GLOBAL ---
if "tema" not in st.session_state:
    st.session_state.tema = "Oscuro"

def aplicar_tema():
    st.markdown("""
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
            * { font-family: 'Inter', sans-serif !important; }
            
            /* OCULTAMOS EL BOTÓN NATIVO DE STREAMLIT (que se rompe) */
            [data-testid="stSidebarCollapseButton"] { display: none !important; }
            [data-testid="collapsedControl"] { display: none !important; }
            
            /* BOTÓN FLOTANTE PERSONALIZADO */
            #custom-toggle-btn {
                position: fixed;
                top: 50%;
                left: 10px; /* Ajustar según barra lateral */
                transform: translateY(-50%);
                z-index: 9999;
                background-color: #2563EB;
                color: white;
                border: none;
                border-radius: 50%;
                width: 36px;
                height: 36px;
                font-size: 16px;
                cursor: pointer;
                box-shadow: 0 2px 5px rgba(0,0,0,0.2);
                transition: all 0.2s;
                display: flex;
                align-items: center;
                justify-content: center;
            }
            #custom-toggle-btn:hover { background-color: #1D4ED8; }
        </style>
    """, unsafe_allow_html=True)

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

# --- 2. INYECCIÓN DEL BOTÓN FLOTANTE ---
# Este script crea un botón flotante y lo conecta al botón nativo de Streamlit
def inyectar_boton_flotante():
    components.html(
        """
        <script>
            // Esperamos a que cargue el DOM
            setTimeout(function() {
                const btn = window.parent.document.createElement('button');
                btn.id = 'custom-toggle-btn';
                btn.innerHTML = '❮'; // Flecha izquierda por defecto
                
                // Buscamos el botón nativo de Streamlit para hacerle clic
                const nativeBtn = window.parent.document.querySelector('[data-testid="stSidebarCollapseButton"]') || 
                                  window.parent.document.querySelector('[data-testid="collapsedControl"]');
                
                if (nativeBtn) {
                    btn.onclick = function() { nativeBtn.click(); };
                    window.parent.document.body.appendChild(btn);
                }
            }, 1000);
        </script>
        """,
        height=0,
    )

# --- 3. CONEXIÓN SUPABASE ---
@st.cache_resource
def init_connection() -> Client:
    return create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])

supabase = init_connection()

# --- 4. LÓGICA DE AUTENTICACIÓN ---
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

# --- 5. PANTALLA DE LOGIN ---
if st.session_state.user is None:
    aplicar_tema() 
    
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

# --- 6. APLICACIÓN PRINCIPAL ---
aplicar_tema()
inyectar_boton_flotante() # Inyectamos el botón aquí

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

# --- 7. MENÚ DINÁMICO ---
paginas = [
    st.Page("pages/1_cotizador.py", title="Cotizador", icon="🚗"),
    st.Page("pages/3_crm.py", title="CRM", icon="📋"),
]

if rol == "Administrador":
    paginas.append(st.Page("pages/2_admin.py", title="Admin", icon="⚙️"))

pg = st.navigation(paginas)
pg.run()
