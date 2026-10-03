"""
Sistema de autenticación con Streamlit-Authenticator.
Lee usuarios desde el Sheet USUARIOS.
"""

import streamlit as st
import streamlit_authenticator as stauth
import pandas as pd
import bcrypt


# ===== URL DE LA HOJA USUARIOS =====
URL_USUARIOS = "https://docs.google.com/spreadsheets/d/1838duFdovU2D_i4huwpntXYiCdi8MFED6Fd8p6imGSk/export?format=csv&gid=2019645833"


@st.cache_data(ttl=300)
def cargar_usuarios():
    """Carga los usuarios desde el Sheet."""
    try:
        df = pd.read_csv(URL_USUARIOS)
        df = df.fillna("")
        return df, None
    except Exception as e:
        return None, str(e)


def construir_credentials(df):
    """
    Convierte el DataFrame de usuarios al formato que espera
    Streamlit-Authenticator.
    """
    credentials = {"usernames": {}}

    for _, row in df.iterrows():
        # Solo usuarios activos
        activo = str(row.get("activo", "TRUE")).upper() == "TRUE"
        if not activo:
            continue

        usuario = str(row.get("usuario", "")).strip()
        if not usuario:
            continue

        credentials["usernames"][usuario] = {
            "name": str(row.get("nombre", usuario)),
            "password": str(row.get("password_hash", "")),
            "role": str(row.get("rol", "vendedor")),
        }

    return credentials


def inicializar_auth():
    """
    Inicializa el sistema de autenticación.
    Devuelve (authenticator, nombre, authentication_status, username) o None si falla.
    """
    df_usuarios, error = cargar_usuarios()

    if error:
        st.error(f"No se pudo cargar la lista de usuarios: {error}")
        return None

    if df_usuarios is None or df_usuarios.empty:
        st.error("No hay usuarios cargados en el sistema.")
        return None

    credentials = construir_credentials(df_usuarios)

    if not credentials["usernames"]:
        st.error("No hay usuarios activos en el sistema. Contactá al administrador.")
        return None

    authenticator = stauth.Authenticate(
        credentials,
        cookie_name=st.secrets["auth"]["cookie_name"],
        cookie_key=st.secrets["auth"]["cookie_key"],
        cookie_expiry_days=st.secrets["auth"]["cookie_expiry_days"],
    )

    return authenticator, df_usuarios


def obtener_rol(usuario, df_usuarios):
    """Devuelve el rol del usuario."""
    if df_usuarios is None:
        return None
    fila = df_usuarios[df_usuarios["usuario"] == usuario]
    if fila.empty:
        return None
    return str(fila.iloc[0].get("rol", "vendedor"))


def hashear_password(password):
    """Genera el hash de una contraseña. Útil para la gestión de usuarios."""
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
