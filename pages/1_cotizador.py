import streamlit as st
import json
import re
from openai import OpenAI
from supabase import create_client, Client
from cotizador import MODELOS, LINEAS, calcular_frances, evaluar_linea, generar_codigo_disfrazado

st.set_page_config(page_title="Cotizador BYD v2", layout="wide")

# --- CONEXIÓN SUPABASE ---
@st.cache_resource
def init_connection() -> Client:
    return create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])

try:
    supabase = init_connection()
except Exception as e:
    st.error(f"Error de conexión con Supabase: {e}")
    st.stop()

# --- CONFIGURACIÓN IA ---
try:
    API_KEY = st.secrets["GROQ_API_KEY"]
    client = OpenAI(base_url="https://api.groq.com/openai/v1", api_key=API_KEY)
    ia_activa = True
except Exception:
    ia_activa = False

if "datos_ia" not in st.session_state:
    st.session_state.datos_ia = None
if "vista_cliente" not in st.session_state:
    st.session_state.vista_cliente = False

def input_moneda(label, value, key, help=None):
    val_str = f"{value:,.0f}".replace(",", ".") if value > 0 else ""
    txt = st.text_input(label, value=val_str, key=key, help=help)
    num = int(re.sub(r'[^\d]', '', txt)) if txt else 0
    return num

def procesar_pedido_ia(prompt):
    if not ia_activa: return None
    system_prompt = """Sos un asistente de ventas de autos. Extraé datos y devolvé SOLO un JSON válido.
    Claves: "modelo" (string), "anticipo" (entero en pesos), "usado" (entero en pesos), "prioridad" (string)."""
    try:
        response = client.chat.completions.create(
            model="openai/gpt-oss-120b",
            messages=[{"role": "system", "content": system_prompt}, {"role": "user", "content": prompt}],
            temperature=0.0
        )
        texto = response.choices[0].message.content
        json_limpio = re.sub(r'```(?:json)?\n?(.*?)\n?```', r'\1', texto, flags=re.DOTALL)
        json_limpio = json_limpio[json_limpio.find('{'):json_limpio.rfind('}')+1]
        datos = json.loads(json_limpio)
        return {
            "modelo": datos.get("modelo"),
            "anticipo": datos.get("anticipo") or 0,
            "usado": datos.get("usado") or 0,
            "prioridad": datos.get("prioridad")
        }
    except Exception:
        return None

# --- BARRA LATERAL ---
with st.sidebar:
    st.header("🤖 Asistente")
    st.write("Contale qué pide el cliente.")
    prompt_ia = st.chat_input("Ej: Quiere una Song Pro, entrega 10 palos...")
    if prompt_ia and ia_activa:
        with st.spinner("Procesando..."):
            datos = procesar_pedido_ia(prompt_ia)
            if datos:
                st.session_state.datos_ia = datos
                st.success("¡Datos cargados!")
                st.rerun()

st.title("Cotizador BYD 0 km")
st.toggle("Vista cliente", key="vista_cliente", help="Oculta las herramientas secretas del vendedor.")

col1, col2 = st.columns([1.2, 1])

# --- VARIABLES GLOBALES PARA EVITAR ERRORES ---
tc = 1
ant_ars = 0
ant_usd = 0
usado_ars = 0
ant_pesos = 0
tot_ars = 0
dif = 0
res_final = None
mostrar_capital = 0
mostrar_gasto = 0

with col1:
    st.header("1. Vehículo")
    nombres = [m["nombre"] for m in MODELOS]

    if st.session_state.datos_ia and st.session_state.datos_ia.get("modelo"):
        mod_ia = str(st.session_state.datos_ia["modelo"]).lower()
        for n in nombres:
            if mod_ia in n.lower():
                st.session_state["select_modelo"] = n
                st.session_state.datos_ia["modelo"] = None
                break
                
    if "select_modelo" not in st.session_state:
        st.session_state["select_modelo"] = nombres[0]

    mod_sel = st.selectbox("Modelo", nombres, key="select_modelo")
    dm = next(m for m in MODELOS if m["nombre"] == mod_sel)
    es_usd = dm["moneda"] == "USD"
    simbolo = "u$s" if es_usd else "$"

    # --- BONIFICACIÓN ---
    bon = 0
    if not st.session_state.vista_cliente:
        if dm.get("bonif", 0) > 0:
            aplicar_bonif = st.checkbox("Aplicar bonificación")
            if aplicar_bonif:
                bon_mod = input_moneda(f"Modificar monto bonif. ({simbolo})", 0, key="bon_input")
                if bon_mod == 0:
                    bon = dm["bonif"]
                else:
                    bon = bon_mod
                st.code(generar_codigo_disfrazado(bon), language=None)
        else:
            st.caption("Este modelo no tiene bonificación de lista.")

    patenta = st.selectbox("Patentamiento", ["Concesionario", "Cliente"])

    st.header("2. Qué entrega el cliente")
    tc = input_moneda("Dólar agencia ($)", 0, key="tc_input")
    if tc == 0: tc = 1

    ia_anticipo = st.session_state.datos_ia.get("anticipo", 0) if st.session_state.datos_ia else 0
    ia_usado = st.session_state.datos_ia.get("usado", 0) if st.session_state.datos_ia else 0

    check_ant = st.checkbox("Entrego anticipo", value=False)
    if check_ant:
        c1, c2 = st.columns(2)
        ant_pesos = input_moneda("En pesos ($)", int(ia_anticipo), key="ant_pesos")
        ant_usd = input_moneda("En dólares (u$s)", 0, key="ant_usd")
        ant_ars = ant_pesos + (ant_usd * tc)

    check_usado = st.checkbox("Entrego vehículo en parte de pago", value=(ia_usado > 0))
    if check_usado:
        c3, c4 = st.columns(2)
        tas = input_moneda("Tasación", int(ia_usado), key="tas_input")
        moneda_usado = c4.selectbox("Moneda", ["Pesos", "Dólares"])
        usado_ars = tas * tc if moneda_usado == "Dólares" else tas

with col2:
    with st.container(height=600, border=False):
        st.markdown("### Resumen de Cotización")
        
        precio_base = dm["precio"] - bon
        pat_monto = dm["pat"] if patenta == "Concesionario" else 0
        tot_abonar = precio_base + dm["fyf"] + pat_monto

        with st.container(border=True):
            st.markdown(f"**Precio de Lista:** {simbolo} {dm['precio']:,.0f}")
            if bon > 0:
                st.markdown(f"**Bonificación:** - {simbolo} {bon:,.0f}")
                st.markdown(f"**Precio Cotizado:** {simbolo} {precio_base:,.0f}")
            
            st.divider()
            
            st.markdown(f"**Fletes y Formularios (FyF):** {simbolo} {dm['fyf']:,.0f}")
            if patenta == "Concesionario":
                st.markdown(f"**Patentamiento:** {simbolo} {pat_monto:,.0f}")
            else:
                st.markdown(f"**Patentamiento:** A cargo del cliente (No incluye {simbolo} {dm['pat']:,.0f})")
            
            st.divider()
            
            st.markdown(f"#### **Total a Abonar:**")
            st.markdown(f"### {simbolo} {tot_abonar:,.0f}")
            
            tot_ars = tot_abonar * tc if es_usd else tot_abonar
            dif = tot_ars - ant_ars - usado_ars
            
            if ant_ars > 0 or usado_ars > 0:
                st.divider()
                if ant_ars > 0:
                    st.markdown(f"**(-) Anticipo:** - $ {ant_ars:,.0f}")
                if usado_ars > 0:
                    st.markdown(f"**(-) Vehículo en Parte de Pago:** - $ {usado_ars:,.0f}")
                
                st.markdown(f"**Diferencia a Financiar:**")
                if es_usd:
                    st.markdown(f"### u$s {dif/tc:,.0f} (${dif:,.0f})")
                else:
                    st.markdown(f"### $ {dif:,.0f}")

st.markdown("---")
st.header("3 y 4. Financiación y Cuenta Final")
financiar = st.checkbox("Financiar la diferencia", value=False)

if financiar and dif > 0:
    l_validas = [l for l in LINEAS if "aplica" not in l or any(app in dm["nombre"] for app in l["aplica"])]
    
    pr = st.selectbox("Qué prioriza el cliente:", ["Cuota más baja", "Poner menos al inicio", "Menor costo total", "Equilibrado (no poner extra)"])
    
    opts = []
    for l in l_validas:
        for r in l["r"]:
            test_o = evaluar_linea(l, r, dif, tot_ars, ant_ars, 0.0, True)
            if not test_o["alcanza"]: continue
                
            gasto_pct = test_o["gasto_pct"] / 100
            
            if pr == "Equilibrado (no poner extra)":
                dinero_cliente = ant_ars + usado_ars
                capital_eq = tot_ars - (dinero_cliente / (1 + gasto_pct))
                o = evaluar_linea(l, r, capital_eq, tot_ars, 0, 0.0, True)
                o["mostrar_poner"] = dinero_cliente
            else:
                o = test_o
                o["mostrar_poner"] = test_o["poner_ars"]
                
            opts.append(o)

    if not opts:
        st.error("Ninguna línea alcanza a financiar este monto con los parámetros actuales.")
    else:
        if pr == "Cuota más baja": opts.sort(key=lambda x: x["cuota"])
        elif pr == "Poner menos al inicio" or pr == "Equilibrado (no poner extra)": opts.sort(key=lambda x: x["mostrar_poner"])
        else: opts.sort(key=lambda x: x["costo_fin"])
        
        st.subheader("Mejores opciones")
        cols_opts = st.columns(3)
        for i, o in enumerate(opts[:3]):
            with cols_opts[i]:
                with st.container(border=True):
                    st.markdown(f"**Opción {i+1}**")
                    st.markdown(f"{o['linea']['n']}")
                    st.markdown(f"**Cuota: $ {o['cuota']:,.0f}**")
                    st.caption(f"{o['plazo']} meses | Debe poner: ${o['mostrar_poner']:,.0f}")
                    if st.button("Elegir", key=f"btn_{i}", use_container_width=True):
                        st.session_state["linea_elegida"] = o["linea"]["n"]
                        st.session_state["plazo_elegido"] = o["plazo"]
                        st.session_state["prioridad_elegida"] = pr

        st.subheader("Opción elegida")
        linea_actual = st.session_state.get("linea_elegida", l_validas[0]["n"])
        plazo_actual = st.session_state.get("plazo_elegido", l_validas[0]["r"][0][0])
        pr_actual = st.session_state.get("prioridad_elegida", pr)
        
        st.info(f"**{linea_actual}** a **{plazo_actual} meses**")
        
        l_sel = next((l for l in l_validas if l["n"] == linea_actual), l_validas[0])
        idx_plazo = next((i for i, r in enumerate(l_sel["r"]) if r[0] == plazo_actual), 0)
        
        if not st.session_state.vista_cliente:
            st.markdown("**Ajustes del vendedor**")
            col_aj1, col_aj2, col_aj3 = st.columns(3)
            
            with col_aj1:
                linea_sel_nombre = st.selectbox("Línea", [l["n"] for l in l_validas], index=[l["n"] for l in l_validas].index(l_sel["n"]))
            with col_aj2:
                plazo_sel = st.selectbox("Plazo (meses)", [r[0] for r in l_sel["r"]], index=idx_plazo)
            with col_aj3:
                ex_c = st.number_input("Adicional concesionario (%)", min_value=0.0, step=0.1)
            
            qr = st.checkbox("Cobrar el quebranto", value=True)
            
            l_sel = next(l for l in l_validas if l["n"] == linea_sel_nombre)
            p_data = next(r for r in l_sel["r"] if r[0] == plazo_sel)
            
            if pr_actual == "Equilibrado (no poner extra)":
                o_test = evaluar_linea(l_sel, p_data, dif, tot_ars, ant_ars, ex_c, qr)
                gasto_pct = o_test["gasto_pct"] / 100
                dinero_cliente = ant_ars + usado_ars
                capital_final = tot_ars - (dinero_cliente / (1 + gasto_pct))
                
                res_final = evaluar_linea(l_sel, p_data, capital_final, tot_ars, 0, ex_c, qr)
                res_final["poner_ars"] = dinero_cliente
                mostrar_capital = capital_final
            else:
                res_final = evaluar_linea(l_sel, p_data, dif, tot_ars, ant_ars, ex_c, qr)
                mostrar_capital = dif
        else:
            res_final = evaluar_linea(l_sel, next(r for r in l_sel["r"] if r[0] == plazo_actual), dif, tot_ars, ant_ars, 0.0, True)
            mostrar_capital = dif

        if res_final:
            mostrar_gasto = res_final["gasto_ars"]
            mostrar_total_banco = mostrar_capital + mostrar_gasto

            st.markdown("---")
            st.subheader("📄 Estado de Cuenta y Financiación")
            
            col_cuenta, col_banco = st.columns(2)
            
            fmt = lambda v: f"u$s {v/tc:,.0f} (${v:,.0f})" if es_usd else f"$ {v:,.0f}"

            with col_cuenta:
                st.markdown("**CUENTA DEL CLIENTE**")
                with st.container(border=True):
                    st.markdown(f"**Valor del Vehículo:** {simbolo} {tot_abonar:,.0f}")
                    
                    if ant_usd > 0:
                        st.markdown(f"**(-) Anticipo en Dólares:** - u$s {ant_usd:,.0f}")
                    if ant_pesos > 0:
                        st.markdown(f"**(-) Anticipo en Pesos:** - $ {ant_pesos:,.0f}")
                    if usado_ars > 0:
                        st.markdown(f"**(-) Vehículo en Parte de Pago:** - {fmt(usado_ars)}")
                    
                    st.divider()
                    st.markdown(f"**Capital a Financiar:** {fmt(mostrar_capital)}")
                    st.markdown(f"**(+) Gasto de Otorgamiento ({res_final['gasto_pct']:.2f}%):** {fmt(mostrar_gasto)}")
                    st.divider()
                    
                    debe_poner_txt = fmt(res_final['poner_ars'])
                    st.markdown(f"### 💰 Debe poner al inicio: {debe_poner_txt}")
                    if pr_actual == "Equilibrado (no poner extra)":
                        st.caption("El cliente pone exactamente el dinero declarado. El gasto se descuenta del valor del auto.")

            with col_banco:
                st.markdown("**DATOS PARA EL BANCO (Boleto/Santander)**")
                with st.container(border=True):
                    ref_cap = f"u$s {mostrar_capital/tc:,.0f}" if es_usd else ""
                    ref_gasto = f"u$s {mostrar_gasto/tc:,.0f}" if es_usd else ""
                    ref_total = f"u$s {mostrar_total_banco/tc:,.0f}" if es_usd else ""

                    st.metric("Capital a pedir (Monto del auto)", f"$ {mostrar_capital:,.0f}", delta=ref_cap if es_usd else None, delta_color="off")
                    st.metric("Quebranto (Gasto)", f"$ {mostrar_gasto:,.0f}", delta=ref_gasto if es_usd else None, delta_color="off")
                    st.metric("TOTAL A SOLICITAR AL BANCO", f"$ {mostrar_total_banco:,.0f}", delta=ref_total if es_usd else None, delta_color="off")
                    
                    st.markdown("---")
                    st.markdown("**Condiciones de la Cuota:**")
                    if not res_final["uva"]:
                        st.write(f"**Primera Cuota:** $ {res_final['cuota']:,.0f}")
                        st.write(f"**Última Cuota:** $ {res_final['cuota_fin']:,.0f}")
                    else:
                        st.write(f"**Cuota Inicial (UVA):** $ {res_final['cuota']:,.0f}")
                        st.caption("Sujeta a ajuste por inflación.")
                    st.write(f"**Plazo:** {res_final['plazo']} meses")
                    st.write(f"**TNA:** {res_final['tna']}%")

            # --- BOTÓN PARA GUARDAR EN SUPABASE ---
            if st.button("💾 Guardar esta cotización en el CRM", type="primary", use_container_width=True):
                try:
                    supabase.table("cotizaciones").insert({
                        "modelo": mod_sel,
                        "precio_total": tot_abonar,
                        "moneda": dm["moneda"],
                        "capital_financiado": mostrar_capital,
                        "gasto_otorgamiento": mostrar_gasto,
                        "cuota_inicial": res_final["cuota"],
                        "plazo_meses": res_final["plazo"],
                        "linea": res_final["linea"]["n"],
                        "anticipo": ant_ars,
                        "usado": usado_ars
                    }).execute()
                    st.success("¡Cotización guardada en el CRM exitosamente!")
                except Exception as e:
                    st.error(f"Error al guardar en Supabase: {e}")

st.markdown("---")
st.header("5. Mensaje para el cliente")
msg_defecto = f"Hola! Te paso la cotización de tu BYD {mod_sel}.\nTotal: {simbolo} {tot_abonar:,.0f}\nCualquier duda avisame."
if financiar and dif > 0 and res_final:
    msg_defecto += f"\nFinanciación: {res_final['linea']['n']} a {res_final['plazo']} meses.\nCuota inicial: $ {res_final['cuota']:,.0f}"

st.text_area("Copiar y pegar en WhatsApp", msg_defecto, height=120)
