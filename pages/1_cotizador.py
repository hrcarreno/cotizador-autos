import streamlit as st
import pandas as pd
from google import genai
import json
import re
from cotizador import MODELOS, LINEAS, calcular_frances, evaluar_linea, generar_codigo_disfrazado

st.set_page_config(page_title="Cotizador BYD", layout="wide")

# --- CONFIGURACIÓN DE GEMINI ---
try:
    API_KEY = st.secrets["GEMINI_API_KEY"]
    genai.configure(api_key=API_KEY)
    ia_activa = True
except:
    ia_activa = False

# --- ESTADO DE LA SESIÓN ---
if "datos_ia" not in st.session_state:
    st.session_state.datos_ia = None

# --- FUNCIÓN PARA LA IA ---
def procesar_pedido_ia(prompt):
    if not ia_activa: return None
    model = genai.GenerativeModel('gemini-1.5-flash')
    system_prompt = """Sos un asistente de ventas de autos BYD. Tu única tarea es extraer datos del texto del vendedor y devolverlos en un JSON estricto.
    Claves permitidas:
    - "modelo": (string, buscar en la lista de modelos)
    - "anticipo": (número entero en pesos, si el cliente dice "10 palos", es 10000000)
    - "usado": (número entero en pesos)
    - "prioridad": (string: "cuota", "inicial" o "costo")
    Si no se menciona algo, devolver null.
    """
    try:
        response = model.generate_content(f"{system_prompt}\n\nTexto del vendedor: {prompt}")
        json_str = re.search(r'\{.*\}', response.text, re.DOTALL).group()
        return json.loads(json_str)
    except:
        return None

# --- BARRA LATERAL: ASISTENTE ---
with st.sidebar:
    st.header("🤖 Asistente IA")
    if ia_activa:
        st.write("Contale qué pide el cliente.")
        prompt_ia = st.chat_input("Ej: Quiere una Song Pro, entrega 10 palos...")
        if prompt_ia:
            with st.spinner("Procesando..."):
                datos = procesar_pedido_ia(prompt_ia)
                if datos:
                    st.session_state.datos_ia = datos
                    st.success("¡Datos cargados! Revisá el formulario.")
                    st.rerun()
                else:
                    st.error("No entendí. Probá de nuevo.")
    else:
        st.info("Para usar la IA, configurá GEMINI_API_KEY en los Secrets.")

# --- INTERFAZ PRINCIPAL ---
st.title("Cotizador BYD 0 km")

col1, col2 = st.columns(2)

with col1:
    st.subheader("1. Vehículo")
    nombres_modelos = [m["nombre"] for m in MODELOS]
    
    index_mod = 0
    if st.session_state.datos_ia and st.session_state.datos_ia.get("modelo"):
        mod_ia = st.session_state.datos_ia["modelo"].lower()
        for i, n in enumerate(nombres_modelos):
            if mod_ia in n.lower():
                index_mod = i
                break
                
    modelo_sel = st.selectbox("Modelo", nombres_modelos, index=index_mod)
    datos_mod = next(m for m in MODELOS if m["nombre"] == modelo_sel)
    es_usd = datos_mod["moneda"] == "USD"
    
    st.markdown("---")
    aplicar_bonif = st.checkbox("Aplicar bonificación manual")
    bonif_monto = 0
    if aplicar_bonif:
        bonif_monto = st.number_input(f"Monto bonif. ({datos_mod['moneda']})", min_value=0, step=1000)
        if bonif_monto > 0:
            st.code(f"Código: {generar_codigo_disfrazado(bonif_monto)}", language=None)
    
    patenta = st.selectbox("Patentamiento", ["Concesionario", "Cliente"])
    
    precio_cot = datos_mod["precio"] - bonif_monto
    pat_monto = datos_mod["pat"] if patenta == "Concesionario" else 0
    total_abonar = precio_cot + datos_mod["fyf"] + pat_monto
    
    moneda_simbolo = "u$s" if es_usd else "$"
    st.info(f"**Total a abonar:** {moneda_simbolo} {total_abonar:,.0f}")

    st.subheader("2. Forma de pago")
    tc = st.number_input("Dólar agencia ($)", min_value=0, step=10, value=1450)
    
    anticipo_ars = 0
    if st.checkbox("Entrego anticipo"):
        col_ant1, col_ant2 = st.columns(2)
        with col_ant1:
            ant_pesos = st.number_input("En pesos", min_value=0, step=100000)
        with col_ant2:
            ant_usd = st.number_input("En dólares", min_value=0, step=100)
        anticipo_ars = ant_pesos + (ant_usd * tc)
        
    usado_ars = 0
    if st.checkbox("Entrego vehículo en parte de pago"):
        col_us1, col_us2 = st.columns(2)
        with col_us1:
            tasacion = st.number_input("Tasación", min_value=0, step=100000)
        with col_us2:
            moneda_usado = st.selectbox("Moneda", ["Pesos", "Dólares"])
        if moneda_usado == "Dólares":
            usado_ars = tasacion * tc
        else:
            usado_ars = tasacion

    total_ars = total_abonar * tc if es_usd else total_abonar
    dif_ars = total_ars - anticipo_ars - usado_ars
    
    if dif_ars < 0:
        st.warning(f"Saldo a favor: $ {abs(dif_ars):,.0f}")
    else:
        st.info(f"Diferencia a financiar: $ {dif_ars:,.0f}")

with col2:
    st.subheader("3. Financiación Banco Santander")
    quiere_financiar = st.checkbox("Financiar la diferencia")
    
    if quiere_financiar and dif_ars > 0:
        lineas_validas = []
        for l in LINEAS:
            if "aplica" in l:
                if any(app in datos_mod["nombre"] for app in l["aplica"]):
                    lineas_validas.append(l)
            else:
                lineas_validas.append(l)
                
        nombres_lineas = [l["n"] for l in lineas_validas]
        linea_sel_nombre = st.selectbox("Línea", nombres_lineas)
        linea_sel = next(l for l in lineas_validas if l["n"] == linea_sel_nombre)
        
        plazos_disp = [r[0] for r in linea_sel["r"]]
        plazo_sel = st.radio("Plazo (meses)", plazos_disp, horizontal=True)
        
        ex_conce = st.number_input("Adicional concesionario (%)", min_value=0.0, value=0.0, step=0.1)
        qr = st.checkbox("Cobrar quebranto aunque BYD lo reintegre")
        
        plazo_data = next(r for r in linea_sel["r"] if r[0] == plazo_sel)
        res = evaluar_linea(linea_sel, plazo_data, dif_ars, total_ars, anticipo_ars, ex_conce, qr)
        
        if not res["alcanza"]:
            st.error(f"Línea no alcanza. Financia hasta $ {res['tope']:,.0f}. Faltan $ {res['falta']:,.0f}.")
        else:
            st.markdown(f"### Cuota: $ {res['cuota']:,.0f}")
            if res["uva"]:
                st.caption("Cuota UVA inicial (se ajusta por inflación)")
            else:
                st.caption(f"Última cuota: $ {res['cuota_fin']:,.0f}")
                
            st.write(f"Gasto otorgamiento ({res['gasto_pct']:.2f}%): $ {res['gasto_ars']:,.0f}")
            st.write(f"**Debés poner:** $ {res['poner_ars']:,.0f}")

        st.markdown("### 🏆 Mejores opciones")
        prioridad = st.selectbox("Priorizar:", ["Cuota más baja", "Poner menos al inicio", "Menor costo total"])
        
        opciones = []
        for l in lineas_validas:
            for r in l["r"]:
                o = evaluar_linea(l, r, dif_ars, total_ars, anticipo_ars, ex_conce, qr)
                if o["alcanza"]:
                    opciones.append(o)
                    
        if prioridad == "Cuota más baja":
            opciones.sort(key=lambda x: x["cuota"])
        elif prioridad == "Poner menos al inicio":
            opciones.sort(key=lambda x: x["poner_ars"])
        else:
            opciones.sort(key=lambda x: x["costo_fin"])
            
        for i, opt in enumerate(opciones[:3]):
            with st.expander(f"{i+1}. {opt['linea']['n']} ({opt['plazo']} meses) - ${opt['cuota']:,.0f}/mes"):
                st.write(f"TNA: {opt['tna']}%")
                st.write(f"Debés poner: $ {opt['poner_ars']:,.0f}")
                st.write(f"Costo financiero total: $ {opt['costo_fin']:,.0f}")
    
    st.markdown("---")
    st.subheader("4. Mensaje para WhatsApp")
    msg = f"Hola! Te paso la cotización de tu BYD {modelo_sel}.\nTotal: {moneda_simbolo} {total_abonar:,.0f}\nCualquier duda avisame."
    st.text_area("Mensaje", msg, height=100)
