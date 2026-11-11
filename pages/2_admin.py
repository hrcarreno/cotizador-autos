import streamlit as st
import pandas as pd
from cotizador import MODELOS, LINEAS
from supabase import create_client, Client

st.set_page_config(page_title="Admin - Cotizador", layout="wide")

# --- CONEXIÓN SUPABASE ---
@st.cache_resource
def init_connection() -> Client:
    return create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])

@st.cache_resource
def init_admin_connection() -> Client:
    # Usamos la Service Role Key para poder crear/borrar usuarios
    return create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_SERVICE_KEY"])

try:
    supabase = init_connection()
    supabase_admin = init_admin_connection()
except Exception as e:
    st.error(f"Error de conexión: {e}")
    st.stop()

# --- VERIFICACIÓN DE ROL ---
# Esto es para que un vendedor no entre a la fuerza a /admin
rol_usuario = st.session_state.user.user_metadata.get("rol", "Usuario") if "user" in st.session_state and st.session_state.user else "Sin Logueo"
if rol_usuario != "Administrador":
    st.error("Acceso denegado. Solo administradores.")
    st.stop()

st.title("⚙️ Panel de Administración")

tab_vehiculos, tab_usuarios = st.tabs(["🚗 Vehículos y Precios", "👥 Usuarios y Roles"])

# --- PESTAÑA VEHÍCULOS ---
with tab_vehiculos:
    st.subheader("Lista de Precios")
    st.write("Los cambios se aplicarán en esta sesión.")
    
    df_modelos = pd.DataFrame(MODELOS)
    df_modelos_editado = st.data_editor(
        df_modelos, num_rows="dynamic", use_container_width=True,
        column_config={
            "nombre": st.column_config.TextColumn("Modelo"),
            "moneda": st.column_config.SelectboxColumn("Moneda", options=["ARS", "USD"]),
            "precio": st.column_config.NumberColumn("Precio Lista", format="%d"),
            "bonif": st.column_config.NumberColumn("Bonificación", format="%d"),
            "fyf": st.column_config.NumberColumn("FyF", format="%d"),
            "pat": st.column_config.NumberColumn("Patentamiento", format="%d"),
        }
    )
    
    if st.button("Guardar Cambios de Vehículos", type="primary"):
        MODELOS.clear()
        for _, row in df_modelos_editado.iterrows():
            MODELOS.append({
                "nombre": row["nombre"], "moneda": row["moneda"],
                "precio": int(row["precio"]), "bonif": int(row["bonif"]),
                "fyf": int(row["fyf"]), "pat": int(row["pat"])
            })
        st.success("¡Precios actualizados!")

# --- PESTAÑA USUARIOS ---
with tab_usuarios:
    st.subheader("Gestión de Usuarios")
    
    # 1. Formulario para Crear Usuario
    with st.expander("➕ Crear Nuevo Usuario"):
        with st.form("form_crear_usuario"):
            email_nuevo = st.text_input("Email del usuario")
            nombre_nuevo = st.text_input("Nombre y Apellido")
            rol_nuevo = st.selectbox("Rol", ["Usuario", "Supervisor", "Administrador"])
            pass_nueva = st.text_input("Contraseña inicial", type="password")
            
            if st.form_submit_button("Crear Usuario", type="primary"):
                try:
                    # 1. Lo creamos en el Auth de Supabase
                    user = supabase_admin.auth.admin.create_user({
                        "email": email_nuevo,
                        "password": pass_nueva,
                        "email_confirm": True,
                        "user_metadata": {"rol": rol_nuevo}
                    })
                    
                    # 2. Lo guardamos en nuestra tabla de perfiles
                    supabase.table("perfiles").insert({
                        "id": user.user.id,
                        "email": email_nuevo,
                        "nombre_completo": nombre_nuevo,
                        "rol": rol_nuevo
                    }).execute()
                    
                    st.success(f"¡Usuario {nombre_nuevo} creado!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Error al crear: {e}")

    # 2. Listado y Edición de Usuarios
    st.markdown("---")
    try:
        perfiles = supabase.table("perfiles").select("*").execute().data
        
        if not perfiles:
            st.info("No hay usuarios registrados aún.")
        else:
            df_perfiles = pd.DataFrame(perfiles)
            
            for index, row in df_perfiles.iterrows():
                with st.expander(f"👤 {row['nombre_completo']} ({row['email']}) - {row['rol']}"):
                    col1, col2 = st.columns(2)
                    with col1:
                        nuevo_rol = st.selectbox("Cambiar Rol", ["Usuario", "Supervisor", "Administrador"], index=["Usuario", "Supervisor", "Administrador"].index(row['rol']), key=f"rol_{row['id']}")
                        if st.button("Actualizar Rol", key=f"btn_rol_{row['id']}"):
                            supabase.table("perfiles").update({"rol": nuevo_rol}).eq("id", row['id']).execute()
                            # Actualizamos también los metadatos para que el menú cambie
                            supabase_admin.auth.admin.update_user_by_id(row['id'], {"user_metadata": {"rol": nuevo_rol}})
                            st.success("Rol actualizado. El usuario debe volver a loguearse.")
                            st.rerun()
                            
                    with col2:
                        if st.button("🗑️ Eliminar Usuario", key=f"btn_del_{row['id']}", type="secondary"):
                            supabase_admin.auth.admin.delete_user(row['id'])
                            supabase.table("perfiles").delete().eq("id", row['id']).execute()
                            st.success("Usuario eliminado.")
                            st.rerun()

    except Exception as e:
        st.error(f"Error al cargar usuarios: {e}")
