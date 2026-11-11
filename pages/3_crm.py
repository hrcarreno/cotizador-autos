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

# --- OBTENER USUARIO Y ROL ---
if "user" not in st.session_state or st.session_state.user is None:
    st.error("Debés iniciar sesión para acceder al CRM.")
    st.stop()

usuario_actual = st.session_state.user.email
rol = st.session_state.user.user_metadata.get("rol", "Usuario")
es_admin_o_super = rol in ["Administrador", "Supervisor"]

st.title("📋 CRM Inteligente")

# --- OBTENER LISTA DE VENDEDORES ---
try:
    perfiles_res = supabase.table("perfiles").select("email").execute()
    lista_vendedores = [p["email"] for p in perfiles_res.data]
except:
    lista_vendedores = []

# --- PESTAÑAS DINÁMICAS SEGÚN EL ROL ---
if es_admin_o_super:
    tab1, tab2, tab3, tab4 = st.tabs(["📊 Panel de Ventas", "👥 Asignación Masiva", "🗑️ Borrado Múltiple", "📥 Importar desde Excel"])
else:
    tab1 = st.tabs(["📊 Panel de Ventas"])[0]
    tab2, tab3, tab4 = None, None, None

# ==========================================
# PESTAÑA 1: PANEL DE VENTAS
# ==========================================
with tab1:
    try:
        response = supabase.table("leads").select("*").order("id", desc=True).execute()
        leads_raw = response.data
    except Exception as e:
        st.error(f"Error: {e}")
        leads_raw = []

    if not leads_raw:
        st.info("No hay leads cargados.")
    else:
        df = pd.DataFrame(leads_raw)
        
        # FILTRO BASE POR ROL (Vendedor solo ve lo suyo)
        if not es_admin_o_super:
            df = df[df['vendedor'] == usuario_actual]
            if df.empty:
                st.info("Todavía no tenés leads asignados.")
                st.stop()

        df['fecha_proximo_contacto'] = pd.to_datetime(df['fecha_proximo_contacto']).dt.date
        hoy = date.today()

        # DASHBOARD
        c1, c2, c3, c4 = st.columns(4)
        total = len(df)
        cerrados = len(df[df['estado'] == 'Cerrado'])
        tasa = (cerrados / total * 100) if total > 0 else 0
        atrasados = len(df[(df['fecha_proximo_contacto'] < hoy) & (df['estado'] != 'Cerrado')])
        
        c1.metric("📊 Leads Totales", total)
        c2.metric("🏆 Tasa de Cierre", f"{tasa:.1f}%")
        c3.metric("🚨 Atrasados", atrasados)
        c4.metric("💰 Ventas Cerradas", cerrados)

        st.divider()

        # --- PANEL DE FILTROS AVANZADOS (SOLO ADMIN/SUPER) ---
        if es_admin_o_super:
            with st.expander("🔍 Filtros Avanzados de Búsqueda", expanded=True):
                f_col1, f_col2, f_col3, f_col4 = st.columns(4)
                
                with f_col1:
                    filtro_vend = st.multiselect("Vendedor", lista_vendedores, default=[])
                with f_col2:
                    filtro_mod = st.multiselect("Modelo", df['modelo_interes'].unique(), default=[])
                with f_col3:
                    filtro_est = st.multiselect("Estado", df['estado'].unique(), default=[])
                with f_col4:
                    fecha_desde = st.date_input("Próximo contacto desde", value=None)

                # Aplicamos los filtros
                if filtro_vend:
                    df = df[df['vendedor'].isin(filtro_vend)]
                if filtro_mod:
                    df = df[df['modelo_interes'].isin(filtro_mod)]
                if filtro_est:
                    df = df[df['estado'].isin(filtro_est)]
                if fecha_desde:
                    df = df[df['fecha_proximo_contacto'] >= fecha_desde]

        # BÚSQUEDA GENERAL Y NUEVO LEAD
        col_search, col_btn = st.columns([4, 1])
        with col_search:
            busqueda = st.text_input("🔍 Buscar por nombre o teléfono...", "").lower()
        with col_btn:
            st.write("")
            st.write("")
            with st.popover("➕ Nuevo Lead", use_container_width=True):
                with st.form("form_nuevo"):
                    nom = st.text_input("Nombre")
                    tel = st.text_input("Teléfono")
                    mod = st.selectbox("Modelo", ["Dolphin Mini", "Song Pro", "Seal U", "SHARK", "TI7", "Seal 5", "Otro"])
                    ori = st.selectbox("Origen", ["WhatsApp", "Web", "Instagram", "Facebook", "Salón"])
                    not_ = st.text_area("Notas")
                    if st.form_submit_button("Guardar Lead", type="primary"):
                        supabase.table("leads").insert({
                            "nombre": nom, "telefono": tel, "origen": ori,
                            "modelo_interes": mod, "estado": "Nuevo",
                            "fecha_proximo_contacto": str(hoy + timedelta(days=1)), 
                            "notas": not_,
                            "vendedor": usuario_actual
                        }).execute()
                        st.rerun()

        # Búsqueda de texto
        if busqueda:
            df = df[df['nombre'].str.lower().str.contains(busqueda, na=False) | df['telefono'].astype(str).str.contains(busqueda, na=False)]
            if df.empty:
                st.warning("No se encontraron coincidencias.")
                st.stop()

        st.markdown(f"### 📋 Gestión de Clientes ({len(df)} resultados)")
        
        if len(df) > 20:
            st.caption(f"Mostrando los primeros 20 de {len(df)} clientes. Usá los filtros para refinar.")
            df = df.head(20)

        for _, row in df.iterrows():
            fecha_c = row['fecha_proximo_contacto']
            is_atrasado = fecha_c < hoy and row['estado'] not in ['Cerrado', 'Perdido']
            
            with st.container(border=True):
                col_info, col_datos, col_acciones = st.columns([2, 2, 1])
                
                with col_info:
                    st.markdown(f"**{row['nombre']}**")
                    st.caption(f"📱 {row['telefono']}")
                    st.caption(f"🚗 {row['modelo_interes']}")
                    if es_admin_o_super:
                        st.caption(f"👤 Asignado a: {row['vendedor']}")
                    
                with col_datos:
                    st.caption(f"📅 Próximo: {fecha_c.strftime('%d/%m/%Y') if pd.notna(fecha_c) else 'Sin fecha'}")
                    st.caption(f"🏷️ Etapa: {row['estado']}")
                    st.caption(f"📝 {str(row['notas'])[:50]}...")
                    
                with col_acciones:
                    tel_limpio = "".join(filter(str.isdigit, str(row['telefono'])))
                    if tel_limpio:
                        st.link_button("💬 WhatsApp", f"https://wa.me/{tel_limpio}", use_container_width=True)
                        
                    with st.expander("⚙️ Gestionar"):
                        estados = ["Nuevo", "Contactado", "Cotizado", "Negociación", "Cerrado", "Perdido"]
                        nuevo_est = st.selectbox("Mover a:", estados, index=estados.index(row['estado']), key=f"sel_{row['id']}")
                        
                        if es_admin_o_super:
                            nuevo_vendedor = st.text_input("Asignar a (Email):", value=row['vendedor'], key=f"vend_{row['id']}")
                        else:
                            nuevo_vendedor = row['vendedor']

                        if st.button("Actualizar", key=f"upd_{row['id']}", type="primary", use_container_width=True):
                            supabase.table("leads").update({
                                "estado": nuevo_est,
                                "vendedor": nuevo_vendedor
                            }).eq("id", row['id']).execute()
                            st.rerun()
                            
                        if es_admin_o_super:
                            if st.button("🗑️ Eliminar", key=f"del_{row['id']}", type="secondary", use_container_width=True):
                                supabase.table("leads").delete().eq("id", row['id']).execute()
                                st.rerun()

                with st.expander("💰 Ver Cotizaciones Guardadas"):
                    try:
                        cot_res = supabase.table("cotizaciones").select("*").eq("lead_id", row['id']).execute()
                        if cot_res.data:
                            st.write(f"Se encontraron {len(cot_res.data)} cotización(es) para este cliente:")
                            for c in cot_res.data:
                                st.info(f"**{c['linea']}** a {c['plazo_meses']} meses | Cuota: ${c['cuota_inicial']:,.0f} | Vendedor: {c.get('vendedor', 'N/A')}")
                        else:
                            st.write("No hay cotizaciones guardadas para este cliente.")
                    except Exception as e:
                        st.error(f"Error al buscar cotizaciones: {e}")


# ==========================================
# PESTAÑA 2: ASIGNACIÓN MASIVA (SOLO ADMIN/SUPER)
# ==========================================
if tab2 is not None:
    with tab2:
        st.subheader("Asignación Masiva de Leads")
        st.write("Seleccioná los leads y asignáselos a un vendedor en un solo clic.")
        
        try:
            response = supabase.table("leads").select("id, nombre, telefono, modelo_interes, vendedor").order("id", desc=True).execute()
            leads_raw = response.data
            
            if not leads_raw:
                st.info("No hay leads para asignar.")
            else:
                df_asig = pd.DataFrame(leads_raw)
                df_asig["Seleccionar"] = False
                cols = ["Seleccionar"] + [c for c in df_asig.columns if c != "Seleccionar"]
                df_asig = df_asig[cols]

                if lista_vendedores:
                    vendedor_destino = st.selectbox("Asignar los seleccionados a:", lista_vendedores)
                else:
                    st.warning("No hay vendedores registrados.")
                    vendedor_destino = None

                col_btn1, col_btn2, _ = st.columns([1, 1, 2])
                if col_btn1.button("✅ Seleccionar Todo", use_container_width=True, key="asig_sel_all"):
                    st.session_state.asig_select_all = True
                    st.rerun()
                if col_btn2.button("❌ Deseleccionar Todo", use_container_width=True, key="asig_desel_all"):
                    st.session_state.asig_select_all = False
                    st.rerun()

                if st.session_state.get("asig_select_all", False):
                    df_asig["Seleccionar"] = True

                df_seleccion = st.data_editor(
                    df_asig, hide_index=True, use_container_width=True,
                    column_config={
                        "Seleccionar": st.column_config.CheckboxColumn("🗑️"),
                        "id": st.column_config.NumberColumn("ID", disabled=True),
                    },
                    key="tabla_asignacion"
                )
                
                seleccionados = df_seleccion[df_seleccion["Seleccionar"] == True]
                
                if not seleccionados.empty and vendedor_destino:
                    st.warning(f"Tenés {len(seleccionados)} lead(s) seleccionado(s).")
                    if st.button(f"👤 ASIGNAR A {vendedor_destino}", type="primary", use_container_width=True):
                        ids_a_asignar = seleccionados["id"].tolist()
                        try:
                            supabase.table("leads").update({"vendedor": vendedor_destino}).in_("id", ids_a_asignar).execute()
                            st.success(f"¡Se asignaron {len(ids_a_asignar)} leads a {vendedor_destino}!")
                            st.session_state.asig_select_all = False
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error al asignar: {e}")
        except Exception as e:
            st.error(f"Error: {e}")

# ==========================================
# PESTAÑA 3: BORRADO MÚLTIPLE (SOLO ADMIN/SUPER)
# ==========================================
if tab3 is not None:
    with tab3:
        st.subheader("Borrado Múltiple de Leads")
        
        try:
            response = supabase.table("leads").select("id, nombre, telefono, modelo_interes, origen, vendedor").order("id", desc=True).execute()
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
# PESTAÑA 4: IMPORTAR EXCEL (SOLO ADMIN/SUPER)
# ==========================================
if tab4 is not None:
    with tab4:
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
                                "notas": str(row.get('notas', row.get('Notas', ''))),
                                "vendedor": usuario_actual
                            }).execute()
                            exito += 1
                        except:
                            errores += 1
                    st.success(f"¡Importados {exito} leads! Errores: {errores}.")
                    st.rerun()
            except Exception as e:
                st.error(f"Error: {e}")
