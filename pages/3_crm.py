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

tab1, tab2, tab3 = st.tabs(["📊 Panel de Ventas", "🗑️ Borrado Múltiple", "📥 Importar desde Excel"])

# ==========================================
# PESTAÑA 1: PANEL DE VENTAS
# ==========================================
with tab1:
    try:
        # Traemos todos los leads
        response = supabase.table("leads").select("*").order("id", desc=True).execute()
        leads_raw = response.data
    except Exception as e:
        st.error(f"Error: {e}")
        leads_raw = []

    if not leads_raw:
        st.info("No hay leads cargados. Empezá importando un Excel.")
    else:
        df = pd.DataFrame(leads_raw)
        
        # --- FILTRO POR ROL ---
        # Si NO es admin/super, solo ve los leads asignados a su email
        if not es_admin_o_super:
            df = df[df['vendedor'] == usuario_actual]
            if df.empty:
                st.info("Todavía no tenés leads asignados.")
                st.stop()

        df['fecha_proximo_contacto'] = pd.to_datetime(df['fecha_proximo_contacto']).dt.date
        hoy = date.today()

        # --- DASHBOARD (TARJETAS) ---
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

        # --- BÚSQUEDA Y NUEVO LEAD ---
        col_search, col_btn = st.columns([4, 1])
        with col_search:
            busqueda = st.text_input("🔍 Buscar cliente o teléfono...", "").lower()
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
                            "vendedor": usuario_actual # Se asigna automáticamente a quien lo crea
                        }).execute()
                        st.rerun()

        # Filtro de búsqueda
        if busqueda:
            df = df[df['nombre'].str.lower().str.contains(busqueda, na=False) | df['telefono'].astype(str).str.contains(busqueda, na=False)]
            if df.empty:
                st.warning("No se encontraron coincidencias.")
                st.stop()

        # --- LISTA DE TARJETAS ---
        st.markdown("### 📋 Gestión de Clientes")
        
        if len(df) > 20:
            st.caption(f"Mostrando los primeros 20 de {len(df)} clientes. Usá el buscador para filtrar.")
            df = df.head(20)

        for _, row in df.iterrows():
            fecha_c = row['fecha_proximo_contacto']
            is_atrasado = fecha_c < hoy and row['estado'] not in ['Cerrado', 'Perdido']
            
            # Contenedor visual
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
                            
                        # SOLO Admin y Supervisor pueden borrar
                        if es_admin_o_super:
                            if st.button("🗑️ Eliminar", key=f"del_{row['id']}", type="secondary", use_container_width=True):
                                supabase.table("leads").delete().eq("id", row['id']).execute()
                                st.rerun()


# ==========================================
# PESTAÑA 2: BORRADO MÚLTIPLE (Solo Admin/Super)
# ==========================================
with tab2:
    if not es_admin_o_super:
        st.warning("Acceso restringido. Solo supervisores y administradores pueden borrar leads.")
    else:
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
                            "notas": str(row.get('notas', row.get('Notas', ''))),
                            "vendedor": usuario_actual # El que importa se lo queda
                        }).execute()
                        exito += 1
                    except:
                        errores += 1
                st.success(f"¡Importados {exito} leads! Errores: {errores}.")
                st.rerun()
        except Exception as e:
            st.error(f"Error: {e}")
