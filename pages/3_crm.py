import streamlit as st
import pandas as pd
from datetime import date, timedelta
from supabase import create_client, Client

st.set_page_config(page_title="CRM - Cotizador", layout="wide")

# --- CONEXIÓN SUPABASE ---
@st.cache_resource
def init_connection() -> Client:
    return create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])

try:
    supabase = init_connection()
except Exception as e:
    st.error(f"Error de conexión con Supabase: {e}")
    st.stop()

st.title("📋 CRM de Leads")

tab1, tab2, tab3 = st.tabs(["📊 Leads Activos", "🗑️ Borrado Múltiple", "📥 Importar desde Excel"])

# ==========================================
# PESTAÑA 1: LEADS ACTIVOS (REDISEÑO PROFESIONAL)
# ==========================================
with tab1:
    # --- MÉTRICAS SUPERIORES ---
    try:
        res_all = supabase.table("leads").select("*").execute()
        leads_all = res_all.data
        if leads_all:
            df_all = pd.DataFrame(leads_all)
            df_all['fecha_proximo_contacto'] = pd.to_datetime(df_all['fecha_proximo_contacto']).dt.date
            hoy = date.today()
            
            total_leads = len(df_all)
            atrasados = len(df_all[(df_all['fecha_proximo_contacto'] < hoy) & (df_all['estado'] != 'Cerrado')])
            
            col1, col2, col3 = st.columns(3)
            col1.metric("Total de Leads", total_leads)
            col2.metric("Leads Atrasados", atrasados, delta="-Atención", delta_color="inverse")
            col3.metric("Leads Cerrados", len(df_all[df_all['estado'] == 'Cerrado']))
            
            if atrasados > 0:
                st.warning(f"🚨 Tenés {atrasados} leads atrasados. Filtrá por 'Atrasados' para verlos.")
    except Exception:
        pass

    st.markdown("---")
    
    # --- FORMULARIO DE CARGA (OCULTO EN UN BOTÓN) ---
    with st.popover("➕ Cargar Nuevo Lead"):
        with st.form("nuevo_lead"):
            c1, c2 = st.columns(2)
            nombre = c1.text_input("Nombre")
            telefono = c1.text_input("Teléfono")
            origen = c2.selectbox("Origen", ["WhatsApp", "Web", "Instagram", "Facebook", "Teléfono", "Presencial", "Excel"])
            modelo = c2.selectbox("Modelo", ["Dolphin Mini", "Song Pro", "Seal U", "SHARK", "TI7", "Seal 5", "Otro"])
            fecha_prox = st.date_input("Próximo Contacto", value=date.today() + timedelta(days=1))
            notas = st.text_area("Notas")
            
            if st.form_submit_button("Guardar", type="primary"):
                try:
                    supabase.table("leads").insert({
                        "nombre": nombre, "telefono": telefono, "origen": origen,
                        "modelo_interes": modelo, "estado": "Nuevo",
                        "fecha_proximo_contacto": str(fecha_prox), "notas": notas
                    }).execute()
                    st.success("¡Lead guardado!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Error: {e}")

    # --- TABLA PRINCIPAL DE LEADS ---
    try:
        response = supabase.table("leads").select("*").order("id", desc=True).execute()
        leads_raw = response.data
        
        if not leads_raw:
            st.info("No hay leads cargados todavía.")
        else:
            df = pd.DataFrame(leads_raw)
            df['fecha_proximo_contacto'] = pd.to_datetime(df['fecha_proximo_contacto']).dt.date
            
            # Filtros
            col_f1, col_f2 = st.columns(2)
            with col_f1:
                filtro_estado = st.multiselect("Filtrar por Estado", ["Nuevo", "Contactado", "Cotizado", "Negociación", "Cerrado", "Perdido"], default=[])
            with col_f2:
                filtro_atraso = st.checkbox("Mostrar solo Atrasados")
            
            df_filtrado = df.copy()
            if filtro_estado:
                df_filtrado = df_filtrado[df_filtrado['estado'].isin(filtro_estado)]
            if filtro_atraso:
                hoy = date.today()
                df_filtrado = df_filtrado[(df_filtrado['fecha_proximo_contacto'] < hoy) & (df_filtrado['estado'] != 'Cerrado')]
                
            # Mostramos la tabla
            df_mostrar = df_filtrado[['id', 'nombre', 'telefono', 'modelo_interes', 'origen', 'estado', 'fecha_proximo_contacto', 'notas']]
            
            evento_tabla = st.dataframe(
                df_mostrar,
                use_container_width=True,
                hide_index=True,
                on_select="rerun",
                selection_mode="single-row",
                column_config={
                    "id": st.column_config.NumberColumn("ID", width="small"),
                    "nombre": st.column_config.TextColumn("Cliente", width="medium"),
                    "telefono": st.column_config.TextColumn("Teléfono", width="medium"),
                    "modelo_interes": st.column_config.TextColumn("Modelo", width="medium"),
                    "origen": st.column_config.TextColumn("Origen"),
                    "estado": st.column_config.TextColumn("Estado"),
                    "fecha_proximo_contacto": st.column_config.DateColumn("Próximo Contacto", format="DD/MM/YYYY"),
                    "notas": st.column_config.TextColumn("Notas", width="large"),
                }
            )
            
            # --- PANEL DE DETALLE (SE ABRE AL TOCAR UNA FILA) ---
            if evento_tabla.selection.rows:
                idx_seleccionado = evento_tabla.selection.rows[0]
                lead_sel = df_mostrar.iloc[idx_seleccionado]
                
                st.markdown("---")
                st.subheader(f"Detalle del Lead: {lead_sel['nombre']}")
                
                with st.container(border=True):
                    c1, c2 = st.columns(2)
                    with c1:
                        st.write(f"**Teléfono:** {lead_sel['telefono']}")
                        st.write(f"**Modelo:** {lead_sel['modelo_interes']}")
                        st.write(f"**Origen:** {lead_sel['origen']}")
                        st.write(f"**Próximo Contacto:** {lead_sel['fecha_proximo_contacto'].strftime('%d/%m/%Y')}")
                    with c2:
                        st.write(f"**Notas:** {lead_sel['notas']}")
                        
                        # Actualizar estado
                        opciones_estado = ["Nuevo", "Contactado", "Cotizado", "Negociación", "Cerrado", "Perdido"]
                        idx_actual = opciones_estado.index(lead_sel['estado']) if lead_sel['estado'] in opciones_estado else 0
                        nuevo_estado = st.selectbox("Cambiar estado a:", opciones_estado, index=idx_actual, key=f"det_estado_{lead_sel['id']}")
                        
                        if st.button("Actualizar Estado", type="primary"):
                            supabase.table("leads").update({"estado": nuevo_estado}).eq("id", int(lead_sel['id'])).execute()
                            st.success("Estado actualizado")
                            st.rerun()
                            
                        if st.button("🗑️ Eliminar Lead", type="secondary"):
                            supabase.table("leads").delete().eq("id", int(lead_sel['id'])).execute()
                            st.success("Lead eliminado")
                            st.rerun()

    except Exception as e:
        st.error(f"Error al cargar los leads: {e}")


# ==========================================
# PESTAÑA 2: BORRADO MÚLTIPLE
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
                    st.success(f"¡Se eliminaron {len(ids_a_borrar)} leads!")
                    st.session_state.select_all_trigger = False
                    st.rerun()
    except Exception as e:
        st.error(f"Error: {e}")


# ==========================================
# PESTAÑA 3: IMPORTAR EXCEL
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
