import streamlit as st
import pandas as pd
from datetime import date, timedelta
from supabase import create_client, Client

st.set_page_config(page_title="CRM Inteligente", layout="wide")

# --- CONEXIÓN SUPABASE ---
@st.cache_resource
def init_connection() -> Client:
    return create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])

try:
    supabase = init_connection()
except Exception as e:
    st.error(f"Error de conexión con Supabase: {e}")
    st.stop()

st.title("📋 CRM Inteligente")

tab1, tab2, tab3 = st.tabs(["📊 Tablero de Ventas", "🗑️ Borrado Múltiple", "📥 Importar desde Excel"])

# ==========================================
# PESTAÑA 1: TABLERO KANBAN Y MÉTRICAS
# ==========================================
with tab1:
    # Traemos todos los leads
    try:
        response = supabase.table("leads").select("*").execute()
        leads_raw = response.data
    except Exception as e:
        st.error(f"Error al cargar datos: {e}")
        leads_raw = []

    if not leads_raw:
        st.info("No hay leads cargados todavía. Usá la pestaña de importar o agregá uno nuevo.")
    else:
        df = pd.DataFrame(leads_raw)
        df['fecha_proximo_contacto'] = pd.to_datetime(df['fecha_proximo_contacto']).dt.date
        hoy = date.today()

        # --- 1. DASHBOARD DE MÉTRICAS (ADMIN) ---
        st.markdown("### 🎯 Resumen de Rendimiento")
        col1, col2, col3, col4 = st.columns(4)
        
        total_leads = len(df)
        leads_cerrados = len(df[df['estado'] == 'Cerrado'])
        tasa_cierre = (leads_cerrados / total_leads * 100) if total_leads > 0 else 0
        
        atrasados = df[(df['fecha_proximo_contacto'] < hoy) & (df['estado'] != 'Cerrado')]
        
        col1.metric("Leads Totales", total_leads)
        col2.metric("Tasa de Cierre", f"{tasa_cierre:.1f}%")
        col3.metric("Leads Atrasados", len(atrasados), delta="Requieren atención", delta_color="inverse")
        col4.metric("Ventas Cerradas", leads_cerrados)

        st.divider()

        # --- 2. CONTROLES Y CARGA RÁPIDA ---
        col_ctrl1, col_ctrl2 = st.columns([3, 1])
        with col_ctrl1:
            busqueda = st.text_input("🔍 Buscar cliente por nombre o teléfono", "")
        with col_ctrl2:
            st.write("") # Espacio para alinear
            st.write("")
            with st.popover("➕ Nuevo Lead", use_container_width=True):
                with st.form("nuevo_lead"):
                    n_nombre = st.text_input("Nombre")
                    n_tel = st.text_input("Teléfono")
                    n_mod = st.selectbox("Modelo", ["Dolphin Mini", "Song Pro", "Seal U", "SHARK", "TI7", "Seal 5", "Otro"])
                    n_origen = st.selectbox("Origen", ["WhatsApp", "Web", "Instagram", "Facebook", "Presencial"])
                    n_notas = st.text_area("Notas")
                    if st.form_submit_button("Guardar Lead"):
                        supabase.table("leads").insert({
                            "nombre": n_nombre, "telefono": n_tel, "origen": n_origen,
                            "modelo_interes": n_mod, "estado": "Nuevo",
                            "fecha_proximo_contacto": str(hoy + timedelta(days=1)), "notas": n_notas
                        }).execute()
                        st.rerun()

        # Filtro de búsqueda
        if busqueda:
            df = df[df['nombre'].str.contains(busqueda, case=False, na=False) | df['telefono'].astype(str).str.contains(busqueda, na=False)]

        # --- 3. TABLERO KANBAN VISUAL ---
        st.markdown("### 🗂️ Flujo de Ventas")
        st.caption("Gestioná el avance de cada cliente a lo largo del embudo de ventas.")
        
        estados_columnas = ["Nuevo", "Contactado", "Cotizado", "Negociación", "Cerrado", "Perdido"]
        cols = st.columns(len(estados_columnas))

        # Renderizamos cada columna
        for idx, estado in enumerate(estados_columnas):
            with cols[idx]:
                # Título de la columna con contador
                df_col = df[df['estado'] == estado]
                st.markdown(f"**{estado} ({len(df_col)})**")
                
                # Contenedor para las tarjetas de esta columna
                with st.container(height=600, border=False):
                    for _, row in df_col.iterrows():
                        # Lógica de alerta de atraso
                        fecha_c = row['fecha_proximo_contacto']
                        atrasado = fecha_c < hoy and estado != 'Cerrado' and estado != 'Perdido'
                        borde = "🔴 " if atrasado else ""
                        
                        # Tarjeta del Lead
                        with st.container(border=True):
                            st.markdown(f"{borde}**{row['nombre']}**")
                            st.caption(f"📱 {row['telefono']}")
                            st.caption(f"🚗 {row['modelo_interes']}")
                            if pd.notna(row['notas']) and row['notas'] != "":
                                st.caption(f"📝 {str(row['notas'])[:40]}...")
                            
                            # Botones de acción rápida
                            c_btn1, c_btn2 = st.columns(2)
                            with c_btn1:
                                # Botón de WhatsApp Web
                                tel_limpio = "".join(filter(str.isdigit, str(row['telefono'])))
                                if tel_limpio:
                                    url_wp = f"https://wa.me/{tel_limpio}?text=Hola%20{row['nombre']}!"
                                    st.link_button("💬 WP", url_wp, use_container_width=True)
                            with c_btn2:
                                # Botón de avanzar etapa
                                if estado != "Cerrado" and estado != "Perdido":
                                    sig_etapa = estados_columnas[estados_columnas.index(estado) + 1]
                                    if st.button("➡️ Avanzar", key=f"avz_{row['id']}", use_container_width=True):
                                        supabase.table("leads").update({"estado": sig_etapa}).eq("id", row['id']).execute()
                                        st.rerun()
                            
                            # Expander para ver detalle o eliminar
                            with st.expander("⚙️ Opciones"):
                                st.write(f"**Origen:** {row['origen']}")
                                st.write(f"**Próx. Contacto:** {fecha_c.strftime('%d/%m/%Y')}")
                                nuevo_est = st.selectbox("Mover a:", estados_columnas, index=estados_columnas.index(estado), key=f"sel_{row['id']}")
                                if st.button("Actualizar", key=f"upd_{row['id']}"):
                                    supabase.table("leads").update({"estado": nuevo_est}).eq("id", row['id']).execute()
                                    st.rerun()
                                if st.button("🗑️ Eliminar", key=f"del_{row['id']}", type="primary"):
                                    supabase.table("leads").delete().eq("id", row['id']).execute()
                                    st.rerun()


# ==========================================
# PESTAÑA 2: BORRADO MÚLTIPLE (SE MANTIENE)
# ==========================================
with tab2:
    st.subheader("Borrado Múltiple de Leads")
    
    try:
        response = supabase.table("leads").select("id, nombre, telefono, modelo_interes, origen").order("id", desc=True).execute()
        leads_raw = response.data
        
        if not leads_raw:
            st.info("No hay leads para borrar.")
        else:
            df_borrar = pd.DataFrame(leads_raw)
            df_borrar["Seleccionar"] = False
            cols = ["Seleccionar"] + [c for c in df_borrar.columns if c != "Seleccionar"]
            df_borrar = df_borrar[cols]

            if "select_all_trigger" not in st.session_state:
                st.session_state.select_all_trigger = False

            col_btn1, col_btn2, _ = st.columns([1, 1, 2])
            if col_btn1.button("✅ Seleccionar Todo", use_container_width=True):
                st.session_state.select_all_trigger = True
                st.rerun()
            if col_btn2.button("❌ Deseleccionar Todo", use_container_width=True):
                st.session_state.select_all_trigger = False
                st.rerun()

            if st.session_state.select_all_trigger:
                df_borrar["Seleccionar"] = True

            df_seleccion = st.data_editor(
                df_borrar, hide_index=True, use_container_width=True,
                column_config={
                    "Seleccionar": st.column_config.CheckboxColumn("🗑️"),
                    "id": st.column_config.NumberColumn("ID", disabled=True),
                },
                key="tabla_borrado"
            )
            
            seleccionados = df_seleccion[df_seleccion["Seleccionar"] == True]
            
            if not seleccionados.empty:
                st.warning(f"Tenés {len(seleccionados)} lead(s) seleccionado(s).")
                if st.button("🗑️ ELIMINAR SELECCIONADOS", type="primary", use_container_width=True):
                    ids_a_borrar = seleccionados["id"].tolist()
                    supabase.table("leads").delete().in_("id", ids_a_borrar).execute()
                    st.session_state.select_all_trigger = False
                    st.rerun()
    except Exception as e:
        st.error(f"Error: {e}")

# ==========================================
# PESTAÑA 3: IMPORTAR EXCEL (SE MANTIENE)
# ==========================================
with tab3:
    st.subheader("Importar Leads desde Excel")
    archivo_excel = st.file_uploader("Seleccioná el archivo Excel (.xlsx)", type=["xlsx"])
    
    if archivo_excel is not None:
        try:
            df_excel = pd.read_excel(archivo_excel)
            st.dataframe(df_excel.head(5))
            
            if st.button("Confirmar e Importar", type="primary"):
                exito, errores = 0, 0
                for _, row in df_excel.iterrows():
                    try:
                        supabase.table("leads").insert({
                            "nombre": str(row.get('nombre', row.get('Nombre', 'Sin Nombre'))),
                            "telefono": str(row.get('telefono', row.get('Teléfono', ''))),
                            "origen": str(row.get('origen', row.get('Origen', 'Excel'))),
                            "modelo_interes": str(row.get('modelo_interes', row.get('Modelo', 'Desconocido'))),
                            "estado": "Nuevo",
                            "fecha_proximo_contacto": str(date.today() + timedelta(days=1)),
                            "notas": str(row.get('notas', row.get('Notas', '')))
                        }).execute()
                        exito += 1
                    except:
                        errores += 1
                st.success(f"¡Importados {exito} leads! Errores: {errores}.")
                st.rerun()
        except Exception as e:
            st.error(f"Error: {e}")
