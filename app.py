import streamlit as st
import streamlit_authenticator as stauth
import yaml
from yaml.loader import SafeLoader

st.set_page_config(page_title="Sistema Concesionaria", layout="wide")

# --- CONFIGURACIÓN DE USUARIOS ---
# En producción esto va en un archivo config.yaml o en los Secrets, pero para arrancar lo dejamos acá
config = {
    'credentials': {
        'usernames': {
            'hrcarreno': {
                'email': 'admin@byd.com',
                'name': 'Hernán (Admin)',
                'password': 'admin123', # Encriptaremos esto después
                'role': 'admin'
            },
            'seba': {
                'email': 'seba@byd.com',
                'name': 'Seba',
                'password': 'seba123',
                'role': 'vendedor'
            },
            'luis': {
                'email': 'luis@byd.com',
                'name': 'Luis',
                'password': 'luis123',
                'role': 'vendedor'
            }
        }
    },
    'cookie': {
        'expiry_days': 30,
        'key': 'clave_secreta_super_segura',
        'name': 'concesionaria_cookie'
    }
}

authenticator = stauth.Authenticate(
    config['credentials'],
    config['cookie']['name'],
    config['cookie']['key'],
    config['cookie']['expiry_days']
)

# --- MUESTRA EL LOGIN ---
name, authentication_status, username = authenticator.login('main')

if authentication_status == False:
    st.error('Usuario o contraseña incorrectos')
elif authentication_status == None:
    st.warning('Por favor, ingresá tus credenciales')
elif authentication_status:
    # --- ROUTER SI ESTÁ LOGUEADO ---
    with st.sidebar:
        st.write(f"👤 Logueado como: **{name}**")
        authenticator.logout('Cerrar Sesión', 'sidebar')
    
    # Guardamos el rol en la sesión para usarlo en el CRM
    st.session_state['usuario_actual'] = username
    st.session_state['rol_actual'] = config['credentials']['usernames'][username]['role']
    st.session_state['nombre_actual'] = name

    pg = st.navigation([
        st.Page("pages/1_cotizador.py", title="Cotizador", icon="🚗"),
        st.Page("pages/2_admin.py", title="Admin", icon="⚙️"),
        st.Page("pages/3_crm.py", title="CRM", icon="📋"),
    ])
    pg.run()
