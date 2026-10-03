import streamlit as st
import pandas as pd

# ===== VALIDAR LOGIN Y ROL =====
if not st.session_state.get("authentication_status"):
    st.error("Debés iniciar sesión.")
    st.stop()

rol = st.session_state.get("_rol", "vendedor")
if rol != "admin":
    st.error("Solo el administrador puede acceder a esta sección.")
    st.stop()

st.title("Gestión de Usuarios")
st.caption("Alta, baja y modificación de usuarios del sistema")

st.info("🚧 Esta sección estará activa cuando implementemos la gestión de usuarios (Etapa 6.6).")

# Placeholder
st.markdown("### Usuarios actuales")
st.write("Próximamente: tabla de usuarios con acciones de alta/baja/modificación.")
