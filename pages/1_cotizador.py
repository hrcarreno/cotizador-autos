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

# --- VARIABLES GLOBALES ---
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
        st.markdown("### Resumen Rápido")
        
        precio_base = dm["precio"] - bon
        pat_monto = dm["pat"] if patenta == "Concesionario" else 0
        tot_abonar = precio_base + dm["fyf"] + pat_monto

        with st.container(border=True):
            st.markdown(f"**Precio de Lista:** {simbolo} {dm['precio']:,.0f}")
            if bon > 0:
                st.markdown(f"**Bonificación:** - {simbolo} {bon:,.0f}")
            st.markdown(f"**Fletes y Formularios:** {simbolo} {dm['fyf']:,.0f}")
            if patenta == "Concesionario":
                st.markdown(f"**Patentamiento:** {simbolo} {pat_monto:,.0f}")
            else:
                st.markdown(f"**Patentamiento:** A cargo del cliente")
            
            st.divider()
            st.markdown(f"#### **Total Auto:** {simbolo} {tot_abonar:,.0f}")

st.markdown("---")
st.header("3 y 4. Financiación y Cierre")

financiar = st.checkbox("Simular Financiación", value=False)

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
                    st.markdown(f"**{o['linea']['n']}**")
                    st.markdown(f"### Cuota: $ {o['cuota']:,.0f}")
                    st.caption(f"{o['plazo']} meses | Debe poner: ${o['mostrar_poner']:,.0f}")
                    if st.button("Elegir", key=f"btn_{i}", use_container_width=True, type="primary"):
                        st.session_state["linea_elegida"] = o["linea"]["n"]
                        st.session_state["plazo_elegido"] = o["plazo"]
                        st.session_state["prioridad_elegida"] = pr

        # --- ELECCIÓN Y DESGLOSE FINAL (REDISEÑADO) ---
        st.markdown("---")
        linea_actual = st.session_state.get("linea_elegida", l_validas[0]["n"])
        plazo_actual = st.session_state.get("plazo_elegido", l_validas[0]["r"][0][0])
        pr_actual = st.session_state.get("prioridad_elegida", pr)
        
        l_sel = next((l for l in l_validas if l["n"] == linea_actual), l_validas[0])
        idx_plazo = next((i for i, r in enumerate(l_sel["r"]) if r[0] == plazo_actual), 0)
        
        col_aj1, col_aj2, col_aj3 = st.columns(3)
        with col_aj1:
            linea_sel_nombre = st.selectbox("Línea elegida", [l["n"] for l in l_validas], index=[l["n"] for l in l_validas].index(l_sel["n"]))
        with col_aj2:
            plazo_sel = st.selectbox("Plazo", [r[0] for r in l_sel["r"]], index=idx_plazo)
        with col_aj3:
            ex_c = st.number_input("Gasto Adicional Concesionario (%)", min_value=0.0, step=0.1)
        
        qr = st.checkbox("Cobrar el quebranto (desmarcar si BYD lo reintegra)", value=True)
        
        l_sel = next(l for l in l_validas if l["n"] == linea_sel_nombre)
        p_data = next((r for r in l_sel["r"] if r[0] == plazo_sel), l_sel["r"][0])
        
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

        if res_final:
            mostrar_gasto = res_final["gasto_ars"]
            mostrar_total_banco = mostrar_capital + mostrar_gasto

            st.markdown("### 📝 Resumen Final de la Operación")
            
            # --- BLOQUE ÚNICO DE CIERRE ---
            with st.container(border=True):
                # Usamos columnas para que se lea como una factura
                c_fact1, c_fact2 = st.columns([2, 1])
                
                with c_fact1:
                    st.markdown("**CONCEPTO**")
                    st.write(f"Valor del Vehículo")
                    if ant_ars > 0 or usado_ars > 0:
                        st.write(f"(-) Anticipo / Usado")
                    st.write(f"Saldo a Financiar")
                    st.write(f"(+) Gasto de Otorgamiento ({res_final['gasto_pct']:.2f}%)")
                    
                with c_fact2:
                    st.markdown("**MONTO**")
                    st.write(f"{simbolo} {tot_abonar:,.0f}")
                    if ant_ars > 0 or usado_ars > 0:
                        st.write(f"- $ {ant_ars + usado_ars:,.0f}")
                    st.write(f"$ {mostrar_capital:,.0f}")
                    st.write(f"$ {mostrar_gasto:,.0f}")
                    
                st.divider()
                
                # Resultado Destacado
                col_res1, col_res2 = st.columns(2)
                with col_res1:
                    st.markdown("**EL CLIENTE DEBE PONER AL INICIO:**")
                    # Acá mostramos el anticipo + el gasto (si no es equilibrado)
                    if pr_actual == "Equilibrado (no poner extra)":
                        st.markdown(f"## {simbolo} {(ant_ars + usado_ars)/tc:,.0f}" if es_usd else f"## $ {ant_ars + usado_ars:,.0f}")
                        st.caption("(El gasto ya está incluido en este monto)")
                    else:
                        monto_inicial = res_final['poner_ars']
                        st.markdown(f"## {simbolo} {monto_inicial/tc:,.0f}" if es_usd else f"## $ {monto_inicial:,.0f}")
                
                with col_res2:
                    st.markdown("**CUOTA MENSUAL:**")
                    if res_final["uva"]:
                        st.markdown(f"## $ {res_final['cuota']:,.0f} (UVA)")
                    else:
                        st.markdown(f"## $ {res_final['cuota']:,.0f}")
                    st.caption(f"Plazo: {res_final['plazo']} meses")

                st.divider()

                # --- DATOS TÉCNICOS PARA EL BANCO (En un expander para no ensuciar) ---
                with st.expander("📋 Ver datos exactos para el Boleto y Sistema Santander"):
                    st.write(f"**Capital a pedir:** $ {mostrar_capital:,.0f}")
                    st.write(f"**Gasto de otorgamiento:** $ {mostrar_gasto:,.0f}")
                    st.write(f"**TOTAL A SOLICITAR:** $ {mostrar_total_banco:,.0f}")
                    if not res_final["uva"]:
                        st.write(f"**Última Cuota:** $ {res_final['cuota_fin']:,.0f}")

            # --- BOTÓN PARA GUARDAR EN SUPABASE ---
            if st.button("💾 Guardar Cotización en CRM", type="primary", use_container_width=True):
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
                    st.success("¡Cotización guardada!")
                except Exception as e:
                    st.error(f"Error: {e}")

# --- PASO 5: MENSAJE PROFESIONAL PARA EL CLIENTE ---
# ... (El resto del código del mensaje queda exactamente igual que antes) ...
st.markdown("---")
st.header("5. Mensaje para el cliente")

msg = f"¡Hola! 👋 Te paso el detalle de la cotización por tu *BYD {mod_sel}*:\n\n"
msg += f"📋 *DETALLE DEL VEHÍCULO:*\n"
msg += f"• Precio de Lista: {simbolo} {dm['precio']:,.0f}\n"
if bon > 0:
    msg += f"• Bonificación aplicada: - {simbolo} {bon:,.0f}\n"
    msg += f"• Precio Cotizado: {simbolo} {precio_base:,.0f}\n"
msg += f"• Fletes y Formularios: {simbolo} {dm['fyf']:,.0f}\n"
if patenta == "Concesionario":
    msg += f"• Patentamiento: {simbolo} {pat_monto:,.0f}\n"
else:
    msg += f"• Patentamiento: A tu cargo\n"
msg += f"\n💰 *TOTAL A ABONAR:* {simbolo} {tot_abonar:,.0f}\n"

if ant_ars > 0 or usado_ars > 0:
    msg += f"\n💵 *FORMA DE PAGO:*\n"
    if ant_ars > 0:
        msg += f"• Anticipo: $ {ant_ars:,.0f}\n"
    if usado_ars > 0:
        msg += f"• Vehículo en parte de pago: $ {usado_ars:,.0f}\n"
    msg += f"• Diferencia a Financiar: $ {dif:,.0f}\n"

if financiar and dif > 0 and res_final:
    msg += f"\n🏦 *CONDICIONES DE FINANCIACIÓN (Banco Santander):*\n"
    msg += f"• Línea: {res_final['linea']['n']}\n"
    msg += f"• Plazo: {res_final['plazo']} meses\n"
    msg += f"• TNA: {res_final['tna']}%\n"
    if not res_final["uva"]:
        msg += f"• Primera Cuota: $ {res_final['cuota']:,.0f}\n"
        msg += f"• Última Cuota: $ {res_final['cuota_fin']:,.0f}\n"
    else:
        msg += f"• Cuota Inicial (UVA): $ {res_final['cuota']:,.0f} (sujeta a ajuste)\n"
    msg += f"• Dinero a poner al inicio (incluye gastos): {fmt(res_final['poner_ars'])}\n"

msg += f"\n*Los valores están sujetos a la lista vigente y aprobación crediticia. No incluye seguro.*\n"
msg += f"Quedo a tu disposición por cualquier duda. ¡Saludos!"

st.text_area("Copiar y pegar en WhatsApp", msg, height=250)
