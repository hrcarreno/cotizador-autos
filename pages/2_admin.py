import streamlit as st
import pandas as pd
from cotizador import MODELOS, LINEAS

st.set_page_config(page_title="Admin - Cotizador", layout="wide")

if not st.session_state.get("logueado") or st.session_state.get("rol") != "admin":
    st.error("Acceso denegado. Solo administradores.")
    st.stop()

st.title("⚙️ Panel de Administración")
st.write("Desde acá podés actualizar los precios. (Los cambios son temporales hasta reconectar a Supabase).")

df_modelos = pd.DataFrame(MODELOS)
df_editado = st.data_editor(df_modelos, num_rows="dynamic", use_container_width=True)

if st.button("Guardar Cambios (Temporal)", type="primary"):
    MODELOS.clear()
    for _, row in df_editado.iterrows():
        MODELOS.append({
            "nombre": row["nombre"], "moneda": row["moneda"], "precio": int(row["precio"]),
            "bonif": int(row["bonif"]), "fyf": int(row["fyf"]), "pat": int(row["pat"])
        })
    st.success("¡Precios actualizados para esta sesión!")
