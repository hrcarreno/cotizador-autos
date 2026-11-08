import streamlit as st
import json
from cotizador import MODELOS, LINEAS

st.set_page_config(page_title="Admin - Cotizador", layout="wide")

st.title("⚙️ Panel de Administración")
st.write("Desde acá podés actualizar los precios y las tasas de financiación sin tocar el código.")

# --- CONTRASEÑA ---
# Podés cambiar esta clave por la que quieras
if "admin_autenticado" not in st.session_state:
    st.session_state.admin_autenticado = False

if not st.session_state.admin_autenticado:
    pwd = st.text_input("Ingresá la contraseña de administrador:", type="password")
    if st.button("Entrar"):
        if pwd == "byd2026": # <--- ACÁ PONÉ TU CONTRASEÑA
            st.session_state.admin_autenticado = True
            st.rerun()
        else:
            st.error("Contraseña incorrecta")
    st.stop()

st.success("Acceso concedido")

# --- EDITOR DE MODELOS ---
st.header("1. Vehículos y Precios")
st.write("Editá los valores de la lista. Los cambios se aplicarán en esta sesión.")

# Creamos un DataFrame editable
import pandas as pd
df_modelos = pd.DataFrame(MODELOS)
df_modelos_editado = st.data_editor(
    df_modelos,
    num_rows="dynamic",
    use_container_width=True,
    column_config={
        "nombre": st.column_config.TextColumn("Modelo"),
        "moneda": st.column_config.SelectboxColumn("Moneda", options=["ARS", "USD"]),
        "precio": st.column_config.NumberColumn("Precio Lista", format="%d"),
        "bonif": st.column_config.NumberColumn("Bonificación", format="%d"),
        "fyf": st.column_config.NumberColumn("FyF", format="%d"),
        "pat": st.column_config.NumberColumn("Patentamiento", format="%d"),
    }
)

# --- EDITOR DE LÍNEAS DE FINANCIACIÓN ---
st.header("2. Líneas de Financiación (Santander)")
st.write("Por ahora la edición de tasas y plazos se hace desde el código para evitar errores de estructura. Si necesitás agregar una línea nueva, avisame.")

# Mostramos las líneas actuales como información
for l in LINEAS:
    with st.expander(l["n"]):
        st.write(f"**Categoría:** {l['k']}")
        st.write(f"**UVA:** {'Sí' if l['uva'] else 'No'}")
        if "aplica" in l:
            st.write(f"**Aplica a:** {', '.join(l['aplica'])}")
        st.write("**Plazos:**")
        for r in l["r"]:
            st.write(f"- {r[0]} meses | TNA: {r[1]}% | Quebranto: {r[2]}% | Tope: {r[3] or 'Sin tope'}")

# --- GUARDAR CAMBIOS ---
if st.button("Guardar Cambios de Vehículos", type="primary", use_container_width=True):
    # Actualizamos la lista en memoria
    MODELOS.clear()
    for _, row in df_modelos_editado.iterrows():
        MODELOS.append({
            "nombre": row["nombre"],
            "moneda": row["moneda"],
            "precio": int(row["precio"]),
            "bonif": int(row["bonif"]),
            "fyf": int(row["fyf"]),
            "pat": int(row["pat"])
        })
    st.success("¡Precios actualizados! Volvé al Cotizador para ver los cambios.")

st.markdown("---")
if st.button("Cerrar Sesión de Admin"):
    st.session_state.admin_autenticado = False
    st.rerun()
