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

# --- PESTAÑAS PRINCIPALES ---
tab1, tab2, tab3 = st.tabs(["📊 Leads Activos", "🗑️ Borrado Múltiple", "📥 Importar desde Excel"])

# ==========================================
# PESTAÑA 1: LEADS ACTIVOS (CON BORRADO INDIVIDUAL)
# ==========================================
with tab1:
    # Alertas de atrasados
    try:
        response = supabase.table("leads").select("*").execute()
        leads_raw = response.data
        if leads_raw:
            df_alerta = pd.DataFrame(leads_raw)
            if 'fecha_proximo_contacto' in df_alerta.columns:
                df_alerta['fecha_proximo_contacto'] = pd.to_datetime(df_alerta['fecha_proximo_contacto']).dt.date
                hoy = date.today()
                atrasados = df_alerta[(df_alerta['fecha_proximo_contacto'] < hoy) & (df_alerta['estado'] != 'Cerrado')]
                
                if not atrasados.empty:
                    st.warning(f"🚨 **¡ATENCIÓN!** Tenés {len(atrasados)} lead(s) atrasado(s) en su atención.")
    except Exception:
        pass

    # Formulario Nuevo Lead
    with st.expander("➕ Cargar Nuevo Lead Manualmente"):
        with st.form("nuevo_lead"):
            c1, c2 = st.columns(2)
            nombre = c1.text_input("Nombre del cliente", placeholder="Ej: Juan Pérez")
            telefono = c1.text_input("Teléfono", placeholder="Ej: 11 2345-6789")
            origen = c2.selectbox("Origen", ["WhatsApp", "Web", "Instagram", "Facebook", "Teléfono", "Presencial", "Excel"])
            modelo = c2.selectbox("Modelo de interés", ["Dolphin Mini", "Song Pro", "Seal U", "SHARK", "TI7", "Seal 5", "Otro"])
            fecha_prox = st.date_input("Fecha próximo contacto", value=date.today() + timedelta(days=1))
            notas = st.text_area("Notas iniciales")
            
            if st.form_submit_button("Guardar Lead", type="primary"):
                try:
                    supabase.table("leads").insert({
                        "nombre": nombre, "telefono": telefono, "origen": origen,
                        "modelo_interes": modelo, "estado": "Nuevo",
                        "fecha_proximo_contacto": str(fecha_prox), "notas": notas
                    }).execute()
                    st.success("¡Lead guardado exitosamente!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Error al guardar: {e}")

    # Listado de Leads
    st.subheader("Listado de Leads")
    try:
        response = supabase.table("leads").select("*").order("id", desc=True).execute()
        leads_raw = response.data
        if not leads_raw:
            st.info("No hay leads cargados todavía.")
        else:
            df = pd.DataFrame(leads_raw)
            
            estados_disponibles = ["Todos"] + list(df['estado'].unique())
            filtro_estado = st.selectbox("Filtrar por estado", estados_disponibles)
            
            if filtro_estado != "Todos":
                df = df[df['estado'] == filtro_estado]
                
            for index, row in df.iterrows():
                fecha_c = pd.to_datetime(row['fecha_proximo_contacto']).date()
                atrasado = fecha_c < date.today() and row['estado'] != 'Cerrado'
                icono = "🔴 " if atrasado else "🟢 "
                
                with st.expander(f"{icono}{row['nombre']} - {row['modelo_interes']} ({row['estado']})"):
                    c1, c2, c3 = st.columns([2, 2, 1])
                    
                    with c1:
                        st.write(f"**Teléfono:** {row['telefono']}")
                        st.write(f"**Origen:** {row['origen']}")
                    with c2:
                        st.write(f"**Próximo Contacto:** {fecha_c.strftime('%d/%m/%Y')}")
                        st.write(f"**Notas:** {row['notas']}")
                    with c3:
                        if st.button("🗑️ Eliminar", key=f"del_{row['id']}", type="secondary"):
                            try:
                                supabase.table("leads").delete().eq("id", row['id']).execute()
                                st.success("Lead eliminado")
                                st.rerun()
                            except Exception as e:
                                st.error(f"Error: {e}")
                    
                    st.divider()
                    
                    opciones_estado = ["Nuevo", "Contactado", "Cotizado", "Negociación", "Cerrado", "Perdido"]
                    idx_actual = opciones_estado.index(row['estado']) if row['estado'] in opciones_estado else 0
                    
                    nuevo_estado = st.selectbox(f"Actualizar estado", opciones_estado, index=idx_actual, key=f"estado_{row['id']}")
                    
                    if st.button("Actualizar Estado", key=f"btn_{row['id']}"):
                        try:
                            supabase.table("leads").update({"estado": nuevo_estado}).eq("id", row['id']).execute()
                            st.success("Estado actualizado")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error: {e}")

    except Exception as e:
        st.error(f"Error al cargar los leads: {e}")


# ==========================================
# PESTAÑA 2: BORRADO MÚLTIPLE
# ==========================================
with tab2:
    st.subheader("Borrado Múltiple de Leads")
    st.write("Seleccioná los leads que querés eliminar de la base de datos. Esta acción es irreversible.")
    
    try:
        response = supabase.table("leads").select("id, nombre, telefono, modelo_interes, origen").order("id", desc=True).execute()
        leads_raw = response.data
        
        if not leads_raw:
            st.info("No hay leads para borrar.")
        else:
            df_borrar = pd.DataFrame(leads_raw)
            
            # Creamos la columna 'Seleccionar' con False por defecto
            df_borrar["Seleccionar"] = False
            cols = ["Seleccionar"] + [c for c in df_borrar.columns if c != "Seleccionar"]
            df_borrar = df_borrar[cols]

            # --- BOTONES PARA SELECCIONAR/DESELECCIONAR TODO ---
            col_btn1, col_btn2, _ = st.columns([1, 1, 2])
            
            if col_btn1.button("✅ Seleccionar Todo", use_container_width=True):
                df_borrar["Seleccionar"] = True
                st.rerun()
                
            if col_btn2.button("❌ Deseleccionar Todo", use_container_width=True):
                df_borrar["Seleccionar"] = False
                st.rerun()

            # --- TABLA EDITABLE CON TRADUCCIÓN AL ESPAÑOL ---
            df_seleccion = st.data_editor(
                df_borrar,
                hide_index=True,
                use_container_width=True,
                column_config={
                    "Seleccionar": st.column_config.CheckboxColumn("🗑️"),
                    "id": st.column_config.NumberColumn("ID", disabled=True),
                    "nombre": st.column_config.TextColumn("Nombre", disabled=True),
                    "telefono": st.column_config.TextColumn("Teléfono", disabled=True),
                    "modelo_interes": st.column_config.TextColumn("Modelo", disabled=True),
                    "origen": st.column_config.TextColumn("Origen", disabled=True),
                },
                # Acá forzamos la traducción de los menús al español
                key="tabla_borrado"
            )
            
            seleccionados = df_seleccion[df_seleccion["Seleccionar"] == True]
            
            if not seleccionados.empty:
                st.warning(f"Tenés {len(seleccionados)} lead(s) seleccionado(s) para eliminar.")
                
                if st.button("🗑️ ELIMINAR SELECCIONADOS", type="primary", use_container_width=True):
                    ids_a_borrar = seleccionados["id"].tolist()
                    try:
                        supabase.table("leads").delete().in_("id", ids_a_borrar).execute()
                        st.success(f"¡Se eliminaron {len(ids_a_borrar)} leads exitosamente!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error al eliminar: {e}")
            else:
                st.info("Tildá la casilla en la primera columna de la tabla para habilitar el borrado.")
                
    except Exception as e:
        st.error(f"Error al cargar la tabla: {e}")


# ==========================================
# PESTAÑA 3: IMPORTAR EXCEL
# ==========================================
with tab3:
    st.subheader("Importar Leads desde Excel")
    st.write("Subí tu planilla. El sistema buscará columnas llamadas Nombre, Teléfono, Origen, Modelo y Notas.")
    archivo_excel = st.file_uploader("Seleccioná el archivo Excel (.xlsx)", type=["xlsx"])
    
    if archivo_excel is not None:
        try:
            df_excel = pd.read_excel(archivo_excel)
            st.write("Vista previa de los datos a importar:")
            st.dataframe(df_excel.head(5))
            
            if st.button("Confirmar e Importar a la Base de Datos", type="primary"):
                exito = 0
                errores = 0
                for index, row in df_excel.iterrows():
                    try:
                        nombre = str(row.get('nombre', row.get('Nombre', row.get('Cliente', 'Sin Nombre'))))
                        telefono = str(row.get('telefono', row.get('Teléfono', row.get('Telefono', row.get('Celular', '')))))
                        origen = str(row.get('origen', row.get('Origen', 'Importado Excel')))
                        modelo = str(row.get('modelo_interes', row.get('Modelo', row.get('Modelo de interés', 'Desconocido'))))
                        notas = str(row.get('notas', row.get('Notas', row.get('Comentarios', ''))))
                        
                        supabase.table("leads").insert({
                            "nombre": nombre,
                            "telefono": telefono,
                            "origen": origen,
                            "modelo_interes": modelo,
                            "estado": "Nuevo",
                            "fecha_proximo_contacto": str(date.today() + timedelta(days=1)),
                            "notas": notas
                        }).execute()
                        exito += 1
                    except Exception as e:
                        errores += 1
                
                st.success(f"¡Importación terminada! Se cargaron {exito} leads. Errores: {errores}.")
                st.rerun()
                
        except Exception as e:
            st.error(f"Error al leer el archivo: {e}")
