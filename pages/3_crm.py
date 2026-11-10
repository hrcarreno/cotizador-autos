import streamlit as st
import pandas as pd
from datetime import date, datetime, timedelta
from st_supabase_connection import SupabaseConnection

st.set_page_config(page_title="CRM - Cotizador", layout="wide")

# --- CONEXIÓN SUPABASE ---
try:
    conn = st.connection("supabase", type=SupabaseConnection)
except Exception:
    st.error("Error de conexión con Supabase. Revisá los Secrets.")
    st.stop()

st.title("📋 CRM de Leads")

# --- ALERTAS DE LEADS ATRASADOS ---
try:
    leads_raw = conn.query("*", table="leads", ttl="10s").execute().data
    if leads_raw:
        df_alerta = pd.DataFrame(leads_raw)
        if 'fecha_proximo_contacto' in df_alerta.columns:
            df_alerta['fecha_proximo_contacto'] = pd.to_datetime(df_alerta['fecha_proximo_contacto']).dt.date
            hoy = date.today()
            atrasados = df_alerta[(df_alerta['fecha_proximo_contacto'] < hoy) & (df_alerta['estado'] != 'Cerrado')]
            
            if not atrasados.empty:
                st.warning(f"🚨 **¡ATENCIÓN!** Tenés {len(atrasados)} lead(s) atrasado(s) en su atención. Revisalos abajo.")
except Exception:
    pass

# --- FORMULARIO PARA NUEVO LEAD ---
with st.expander("➕ Cargar Nuevo Lead"):
    with st.form("nuevo_lead"):
        c1, c2 = st.columns(2)
        nombre = c1.text_input("Nombre del cliente", placeholder="Ej: Juan Pérez")
        telefono = c1.text_input("Teléfono", placeholder="Ej: 11 2345-6789")
        origen = c2.selectbox("Origen", ["WhatsApp", "Web", "Instagram", "Facebook", "Teléfono", "Presencial"])
        modelo = c2.selectbox("Modelo de interés", ["Dolphin Mini", "Song Pro", "Seal U", "SHARK", "TI7", "Seal 5", "Otro"])
        fecha_prox = st.date_input("Fecha próximo contacto", value=date.today() + timedelta(days=1))
        notas = st.text_area("Notas iniciales")
        
        if st.form_submit_button("Guardar Lead", type="primary"):
            try:
                conn.table("leads").insert({
                    "nombre": nombre,
                    "telefono": telefono,
                    "origen": origen,
                    "modelo_interes": modelo,
                    "estado": "Nuevo",
                    "fecha_proximo_contacto": str(fecha_prox),
                    "notas": notas
                }).execute()
                st.success("¡Lead guardado exitosamente!")
                st.rerun()
            except Exception as e:
                st.error(f"Error al guardar: {e}")

# --- LISTADO DE LEADS ---
st.subheader("Leads Registrados")
try:
    leads_raw = conn.query("*", table="leads", ttl="10s").execute().data
    if not leads_raw:
        st.info("No hay leads cargados todavía. Usá el botón de arriba para agregar el primero.")
    else:
        df = pd.DataFrame(leads_raw)
        
        # Filtro por estado
        estados_disponibles = ["Todos"] + list(df['estado'].unique())
        filtro_estado = st.selectbox("Filtrar por estado", estados_disponibles)
        
        if filtro_estado != "Todos":
            df = df[df['estado'] == filtro_estado]
            
        for index, row in df.iterrows():
            # Color de alerta si está atrasado
            fecha_c = pd.to_datetime(row['fecha_proximo_contacto']).date()
            atrasado = fecha_c < date.today() and row['estado'] != 'Cerrado'
            icono = "🔴 " if atrasado else "🟢 "
            
            with st.expander(f"{icono}{row['nombre']} - {row['modelo_interes']} ({row['estado']})"):
                c1, c2, c3 = st.columns(3)
                c1.write(f"**Teléfono:** {row['telefono']}")
                c1.write(f"**Origen:** {row['origen']}")
                c2.write(f"**Próximo Contacto:** {fecha_c.strftime('%d/%m/%Y')}")
                c2.write(f"**Fecha de Alta:** {row['created_at'][:10] if 'created_at' in row else 'N/A'}")
                c3.write(f"**Notas:** {row['notas']}")
                
                # Cambiar estado
                nuevo_estado = st.selectbox(f"Actualizar estado para {row['nombre']}", 
                                            ["Nuevo", "Contactado", "Cotizado", "Negociación", "Cerrado", "Perdido"], 
                                            index=["Nuevo", "Contactado", "Cotizado", "Negociación", "Cerrado", "Perdido"].index(row['estado']) if row['estado'] in ["Nuevo", "Contactado", "Cotizado", "Negociación", "Cerrado", "Perdido"] else 0,
                                            key=f"estado_{row['id']}")
                
                if st.button("Actualizar", key=f"btn_{row['id']}"):
                    try:
                        conn.table("leads").update({"estado": nuevo_estado}).eq("id", row['id']).execute()
                        st.success("Estado actualizado")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error: {e}")

except Exception as e:
    st.error(f"Error al cargar los leads: {e}")
