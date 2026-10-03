import streamlit as st
import pandas as pd

# ===== VALIDAR LOGIN Y ROL =====
if not st.session_state.get("authentication_status"):
    st.error("Debés iniciar sesión.")
    st.stop()

rol = st.session_state.get("_rol", "vendedor")
if rol not in ["supervisor", "admin"]:
    st.error("No tenés permisos para acceder a esta sección.")
    st.stop()

st.title("Configuración")
st.caption("Parámetros del sistema")

# ===== DÓLAR AGENCIA (supervisor + admin) =====
st.markdown("### Dólar Agencia")

if "dolar_agencia" not in st.session_state:
    st.session_state.dolar_agencia = 1500

dolar = st.number_input(
    "Valor del Dólar Agencia",
    value=st.session_state.dolar_agencia,
    step=10,
    min_value=1,
    format="%d",
)

if dolar != st.session_state.dolar_agencia:
    st.session_state.dolar_agencia = dolar
    st.success(f"Dólar Agencia actualizado a ${dolar}")

st.caption(f"Valor actual: **${st.session_state.dolar_agencia}**")

# ===== CONFIGURACIÓN AVANZADA (solo admin) =====
if rol == "admin":
    st.markdown("---")
    st.markdown("### Configuración avanzada")
    st.info("🚧 Próximamente: edición de IVA, comisiones, temas y colores.")
