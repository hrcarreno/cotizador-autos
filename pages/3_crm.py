import streamlit as st
import pandas as pd
from datetime import date, timedelta
from supabase import create_client, Client
import urllib.parse

st.set_page_config(page_title="CRM Profesional", layout="wide")

# --- SEGURIDAD: VERIFICAR LOGIN ---
if 'rol_actual' not in st.session_state:
    st.warning("Por favor, iniciá sesión en la página principal.")
    st.stop()

rol = st.session_state['rol_actual']
usuario = st.session_state['nombre_actual']

@st.cache_resource
def init_connection() -> Client:
    return create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])

try:
    supabase = init_connection()
except Exception as e:
    st.error(f"Error de conexión: {e}")
    st.stop()

st.title("📋 CRM de Leads")

# Lista de vendedores para asignar (si sos admin)
VENDEDORES = ["Seba", "Luis", "Hernán Carreño", "Damián", "Sin Asignar"]

# --- 2. FORMULARIO NUEVO LEAD ---
with st.expander("➕ Cargar Nuevo Lead"):
    with st.form("nuevo_lead"):
        c1, c2 = st.columns(2)
        nombre = c1.text_input("Nombre")
        telefono = c1.text_input("Teléfono")
        modelo = c2.selectbox("Modelo", ["Dolphin Mini", "Song Pro", "Seal U", "SHARK", "Otro"])
        origen = c2.selectbox("Origen", ["WhatsApp", "Instagram", "Facebook", "Salón", "Otro"])
        notas = st.text_area("Notas iniciales")
        
        # Si es admin, puede asignar el lead a otro vendedor
        if rol == 'admin':
            asignado = st.selectbox("Asignar a Vendedor:", VENDEDORES)
        else:
            asignado = usuario # Si es vendedor, se asigna a sí mismo
            
        if st.form_submit_button("Guardar", type="primary"):
            supabase.table("leads").insert({
                "nombre": nombre, "telefono": telefono, "modelo_interes": modelo,
                "origen": origen, "estado": "Nuevo", "notas": notas,
                "fecha_proximo_contacto": str(date.today()), "vendedor": asignado
            }).execute()
            st.rerun()

# --- 3. LISTADO Y FICHA DEL LEAD (CON FILTRO) ---
st.subheader("Base de Datos de Clientes")

# Filtros
col_f1, col_f2 = st.columns(2)
with col_f1:
    estados = ["Todos", "Nuevo", "Contactado", "Cotizado", "Negociación", "Cerrado", "Perdido"]
    filtro = st.selectbox("Filtrar por estado", estados)

with col_f2:
    if rol == 'admin':
        filtro_vendedor = st.selectbox("Filtrar por Vendedor", ["Todos"] + VENDEDORES)
    else:
        st.info(f"Viendo leads asignados a: {usuario}")
        filtro_vendedor = usuario

try:
    query = supabase.table("leads").select("*").order("id", desc=True)
    
    # Aplicamos filtros
    if filtro != "Todos":
        query = query.eq("estado", filtro)
    if filtro_vendedor != "Todos":
        query = query.eq("vendedor", filtro_vendedor)
        
    leads = query.execute().data

    if not leads:
        st.info("No hay leads que coincidan con el filtro.")
    else:
        for lead in leads:
            icono = "🟢" if lead['estado'] != "Perdido" else "🔴"
            vendedor_lead = lead.get('vendedor', 'Sin Asignar')
            
            with st.expander(f"{icono} {lead['nombre']} - {lead['modelo_interes']} (Asignado a: {vendedor_lead})"):
                
                col_edit, col_hist = st.columns([1.5, 1])
                
                with col_edit:
                    st.markdown("### Datos del Cliente")
                    tel_limpio = str(lead.get('telefono', '')).replace('.0', '')
                    
                    with st.form(key=f"edit_{lead['id']}"):
                        nom_edit = st.text_input("Nombre", value=lead['nombre'])
                        tel_edit = st.text_input("Teléfono", value=tel_limpio)
                        mod_edit = st.text_input("Modelo", value=lead['modelo_interes'])
                        
                        idx_est = estados[1:].index(lead['estado']) if lead['estado'] in estados[1:] else 0
                        est_edit = st.selectbox("Estado", estados[1:], index=idx_est)
                        
                        fecha_defecto = pd.to_datetime(lead['fecha_proximo_contacto']).date() if lead['fecha_proximo_contacto'] else date.today()
                        fecha_edit = st.date_input("Próximo contacto", value=fecha_defecto)
                        
                        notas_edit = st.text_area("Notas generales", value=lead['notas'] if lead['notas'] else "")
                        
                        # Solo el admin puede reasignar
                        if rol == 'admin':
                            vendedor_edit = st.selectbox("Vendedor Asignado", VENDEDORES, index=VENDEDORES.index(vendedor_lead) if vendedor_lead in VENDEDORES else 0)
                        else:
                            vendedor_edit = vendedor_lead
                            
                        if st.form_submit_button("💾 Guardar Cambios", use_container_width=True):
                            supabase.table("leads").update({
                                "nombre": nom_edit,
                                "telefono": tel_edit,
                                "modelo_interes": mod_edit,
                                "estado": est_edit,
                                "fecha_proximo_contacto": str(fecha_edit),
                                "notas": notas_edit,
                                "vendedor": vendedor_edit
                            }).eq("id", lead['id']).execute()
                            st.success("¡Actualizado!")
                            st.rerun()

                with col_hist:
                    st.markdown("### Historial de Interacciones")
                    hist = supabase.table("interacciones").select("*").eq("lead_id", lead['id']).order("fecha", desc=True).execute().data
                    
                    if not hist:
                        st.caption("No hay interacciones.")
                    else:
                        for h in hist:
                            fecha_h = pd.to_datetime(h['fecha']).strftime("%d/%m %H:%M")
                            st.info(f"**{fecha_h} - {h['tipo']}** (por {h.get('vendedor', 'N/A')}):\n{h['detalle']}")
                    
                    with st.form(key=f"hist_{lead['id']}"):
                        tipo_int = st.selectbox("Tipo", ["Llamada", "WhatsApp", "Email", "Nota", "Test Drive"])
                        detalle_int = st.text_input("Detalle")
                        if st.form_submit_button("Agregar", use_container_width=True):
                            supabase.table("interacciones").insert({
                                "lead_id": lead['id'],
                                "tipo": tipo_int,
                                "detalle": detalle_int,
                                "vendedor": usuario # Guarda quién hizo la interacción
                            }).execute()
                            st.rerun()

except Exception as e:
    st.error(f"Error cargando datos: {e}")
