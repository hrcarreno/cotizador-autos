import streamlit as st
import pandas as pd
from datetime import date, timedelta
from supabase import create_client, Client
import re

st.set_page_config(page_title="CRM Profesional", layout="wide")

@st.cache_resource
def init_connection() -> Client:
    return create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])

try:
    supabase = init_connection()
except Exception as e:
    st.error(f"Error de conexión: {e}")
    st.stop()

st.title("📋 CRM de Leads")

# --- 1. IMPORTACIÓN EXCEL ---
with st.expander("📥 Importar desde Excel"):
    archivo = st.file_uploader("Subí el Excel", type=["xlsx"])
    if archivo:
        df = pd.read_excel(archivo)
        if st.button("Confirmar Importación"):
            for _, row in df.iterrows():
                try:
                    supabase.table("leads").insert({
                        "nombre": str(row.get('Nombre', 'S/N')),
                        "telefono": str(row.get('Telefono', '')),
                        "origen": str(row.get('Origen', 'Excel')),
                        "modelo_interes": str(row.get('Modelo', '')),
                        "estado": "Nuevo",
                        "fecha_proximo_contacto": str(date.today() + timedelta(days=1)),
                        "notas": str(row.get('Notas', ''))
                    }).execute()
                except: pass
            st.success("Importado!")
            st.rerun()

# --- 2. FORMULARIO NUEVO LEAD ---
with st.expander("➕ Cargar Nuevo Lead"):
    with st.form("nuevo_lead"):
        c1, c2 = st.columns(2)
        nombre = c1.text_input("Nombre")
        telefono = c1.text_input("Teléfono")
        modelo = c2.selectbox("Modelo", ["Dolphin Mini", "Song Pro", "Seal U", "SHARK", "Otro"])
        origen = c2.selectbox("Origen", ["WhatsApp", "Instagram", "Facebook", "Salón"])
        notas = st.text_area("Notas iniciales")
        if st.form_submit_button("Guardar"):
            supabase.table("leads").insert({
                "nombre": nombre, "telefono": telefono, "modelo_interes": modelo,
                "origen": origen, "estado": "Nuevo", "notas": notas,
                "fecha_proximo_contacto": str(date.today())
            }).execute()
            st.rerun()

# --- 3. LISTADO Y FICHA DEL LEAD ---
st.subheader("Base de Datos de Clientes")

# Filtros
estados = ["Todos", "Nuevo", "Contactado", "Cotizado", "Negociación", "Cerrado", "Perdido"]
filtro = st.selectbox("Filtrar por estado", estados)

try:
    query = supabase.table("leads").select("*").order("id", desc=True)
    if filtro != "Todos":
        query = query.eq("estado", filtro)
    leads = query.execute().data

    if not leads:
        st.info("No hay leads.")
    else:
        for lead in leads:
            icono = "🟢" if lead['estado'] != "Perdido" else "🔴"
            with st.expander(f"{icono} {lead['nombre']} - {lead['modelo_interes']} ({lead['estado']})"):
                
                # Dividimos la ficha en dos columnas: Edición e Historial
                col_edit, col_hist = st.columns([1.5, 1])
                
                with col_edit:
                    st.markdown("### Datos del Cliente")
                    # Formulario de edición
                    with st.form(key=f"edit_{lead['id']}"):
                        nom_edit = st.text_input("Nombre", value=lead['nombre'])
                        tel_edit = st.text_input("Teléfono", value=lead['telefono'])
                        mod_edit = st.text_input("Modelo", value=lead['modelo_interes'])
                        est_edit = st.selectbox("Estado", estados[1:], index=estados[1:].index(lead['estado']) if lead['estado'] in estados[1:] else 0)
                        fecha_edit = st.date_input("Próximo contacto", value=pd.to_datetime(lead['fecha_proximo_contacto']).date())
                        notas_edit = st.text_area("Notas generales", value=lead['notas'])
                        
                        if st.form_submit_button("💾 Guardar Cambios"):
                            supabase.table("leads").update({
                                "nombre": nom_edit,
                                "telefono": tel_edit,
                                "modelo_interes": mod_edit,
                                "estado": est_edit,
                                "fecha_proximo_contacto": str(fecha_edit),
                                "notas": notas_edit
                            }).eq("id", lead['id']).execute()
                            st.success("¡Actualizado!")
                            st.rerun()

                with col_hist:
                    st.markdown("### Historial de Interacciones")
                    
                    # Cargar historial desde Supabase
                    hist = supabase.table("interacciones").select("*").eq("lead_id", lead['id']).order("fecha", desc=True).execute().data
                    
                    if not hist:
                        st.caption("No hay interacciones registradas todavía.")
                    else:
                        for h in hist:
                            fecha_h = pd.to_datetime(h['fecha']).strftime("%d/%m %H:%M")
                            st.info(f"**{fecha_h} - {h['tipo']}:**\n{h['detalle']}")
                    
                    # Formulario para agregar interacción
                    with st.form(key=f"hist_{lead['id']}"):
                        tipo_int = st.selectbox("Tipo", ["Llamada", "WhatsApp", "Email", "Nota"])
                        detalle_int = st.text_input("Detalle")
                        if st.form_submit_button("Agregar al historial"):
                            supabase.table("interacciones").insert({
                                "lead_id": lead['id'],
                                "tipo": tipo_int,
                                "detalle": detalle_int
                            }).execute()
                            st.rerun()

except Exception as e:
    st.error(f"Error cargando datos: {e}")
