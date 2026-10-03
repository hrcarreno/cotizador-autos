import streamlit as st

if not st.session_state.get("authentication_status"):
    st.error("Debés iniciar sesión.")
    st.stop()

rol = st.session_state.get("_rol", "vendedor")
if rol not in ["supervisor", "admin"]:
    st.error("No tenés permisos para acceder a esta sección.")
    st.stop()

st.title("Autorizaciones")
st.caption("Solicitudes de descuento pendientes de aprobación")

st.info("Esta sección estará activa cuando implementemos el flujo de descuentos variables (Etapa 8).")

st.markdown("### Solicitudes pendientes")
st.write("No hay solicitudes pendientes por ahora.")
