import streamlit as st
import json
import re
from openai import OpenAI
from cotizador import MODELOS, LINEAS, calcular_frances, evaluar_linea, generar_codigo_disfrazado

st.set_page_config(page_title="Cotizador BYD v2", layout="wide")

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

# --- ENCABEZADO ---
st.title("Cotizador BYD 0 km")
st.toggle("Vista cliente", key="vista_cliente", help="Oculta las herramientas secretas del vendedor.")

# --- DIVIDIMOS EN DOS COLUMNAS ---
col1, col2 = st.columns([1.2, 1])

with col1:
    # PASO 1: VEHÍCULO
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

    # --- OPCIÓN DE BONIFICACIÓN Y CÓDIGO DISFRAZADO ---
    bon = 0
    if not st.session_state.vista_cliente:
        if dm.get("bonif", 0) > 0:
            aplicar_bonif = st.checkbox("Aplicar bonificación de lista")
            if aplicar_bonif:
                bon = dm["bonif"]
                # Mostramos SOLO el código limpio
                st.code(generar_codigo_disfrazado(bon), language=None)
        else:
            st.caption("Este modelo no tiene bonificación de lista.")

    patenta = st.selectbox("Patentamiento", ["Concesionario", "Cliente"])

    # PASO 2: QUÉ ENTREGA EL CLIENTE
    st.header("2. Qué entrega el cliente")
    tc = st.number_input("Dólar agencia ($)", min_value=1, step=10, value=1450)

    ia_anticipo = st.session_state.datos_ia.get("anticipo", 0) if st.session_state.datos_ia else 0
    ia_usado = st.session_state.datos_ia.get("usado", 0) if st.session_state.datos_ia else 0

    check_ant = st.checkbox("Entrego anticipo", value=(ia_anticipo > 0))
    ant_ars = 0
    if check_ant:
        c1, c2 = st.columns(2)
        ant_pesos = c1.number_input("En pesos ($)", min_value=0, step=100000, value=int(ia_anticipo))
        ant_usd = c2.number_input("En dólares (USD)", min_value=0, step=100)
        ant_ars = ant_pesos + (ant_usd * tc)

    check_usado = st.checkbox("Entrego vehículo en parte de pago", value=(ia_usado > 0))
    usado_ars = 0
    if check_usado:
        c3, c4 = st.columns(2)
        tas = c3.number_input("Tasación", min_value=0, step=100000, value=int(ia_usado))
        moneda_usado = c4.selectbox("Moneda", ["Pesos", "Dólares"])
        usado_ars = tas * tc if moneda_usado == "Dólares" else tas

with col2:
    # --- PANEL DE RESUMEN (TIPO FLOTANTE) ---
    st.markdown("### Resumen de Cotización")
    
    # Calculos para el desglose
    precio_base = dm["precio"] - bon
    pat_monto = dm["pat"] if patenta == "Concesionario" else 0
    tot_abonar = precio_base + dm["fyf"] + pat_monto

    # Tarjeta de desglose
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
            st.markdown("*Patentamiento a cargo del cliente.*")
        st.divider()
        st.markdown(f"#### **Total a Abonar:** {simbolo} {tot_abonar:,.0f}")

    # PASO 3: RESULTADO
    tot_ars = tot_abonar * tc if es_usd else tot_abonar
    dif = tot_ars - ant_ars - usado_ars

    st.markdown("### 3. Resultado")
    if dif < 0:
        st.success(f"**Saldo a favor:** $ {abs(dif):,.0f}")
    else:
        st.info(f"**Diferencia a Financiar:** $ {dif:,.0f}")

    # PASO 4: FINANCIACIÓN
    st.markdown("### 4. Financiación")
    financiar = st.checkbox("Financiar la diferencia", value=(dif > 0))

    res_final = None

    if financiar and dif > 0:
        l_validas = [l for l in LINEAS if "aplica" not in l or any(app in dm["nombre"] for app in l["aplica"])]
        opts = [evaluar_linea(l, r, dif, tot_ars, ant_ars, 0.0, False) for l in l_validas for r in l["r"]]
        opts = [o for o in opts if o["alcanza"]]
        
        pr = st.selectbox("Priorizar:", ["Cuota más baja", "Poner menos al inicio", "Menor costo total"])
        
        if not opts:
            st.error("Ninguna línea alcanza a financiar este monto. Aumentá el anticipo o el usado.")
        else:
            if pr == "Cuota más baja": opts.sort(key=lambda x: x["cuota"])
            elif pr == "Poner menos al inicio": opts.sort(key=lambda x: x["poner_ars"])
            else: opts.sort(key=lambda x: x["costo_fin"])
            
            cols_opts = st.columns(3)
            for i, o in enumerate(opts[:3]):
                with cols_opts[i]:
                    st.markdown(f"**Opción {i+1}**")
                    st.markdown(f"{o['linea']['n']}")
                    st.markdown(f"**Cuota: $ {o['cuota']:,.0f}**")
                    st.caption(f"{o['plazo']} meses | Debe poner: $ {o['poner_ars']:,.0f}")
                    if st.button("Elegir", key=f"btn_{i}"):
                        st.session_state["linea_elegida"] = o["linea"]["n"]
                        st.session_state["plazo_elegido"] = o["plazo"]

            st.subheader("Opción elegida")
            linea_actual = st.session_state.get("linea_elegida", l_validas[0]["n"])
            plazo_actual = st.session_state.get("plazo_elegido", l_validas[0]["r"][0][0])
            
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
                
                qr = st.checkbox("Cobrar el quebranto aunque BYD lo reintegre")
                
                l_sel = next(l for l in l_validas if l["n"] == linea_sel_nombre)
                res_final = evaluar_linea(l_sel, next(r for r in l_sel["r"] if r[0] == plazo_sel), dif, tot_ars, ant_ars, ex_c, qr)
            else:
                res_final = evaluar_linea(l_sel, next(r for r in l_sel["r"] if r[0] == plazo_actual), dif, tot_ars, ant_ars, 0.0, False)

            if res_final:
                st.markdown("### Resumen de la financiación")
                st.write(f"- **Cuota inicial:** $ {res_final['cuota']:,.0f}")
                if not res_final["uva"]:
                    st.write(f"- **Última cuota:** $ {res_final['cuota_fin']:,.0f}")
                st.write(f"- **Gasto de otorgamiento:** $ {res_final['gasto_ars']:,.0f}")
                st.write(f"- **Debe poner (sin contar el usado):** $ {res_final['poner_ars']:,.0f}")

    # PASO 5: MENSAJE
    st.markdown("---")
    st.subheader("5. Mensaje WhatsApp")
    msg_defecto = f"Hola! Te paso la cotización de tu BYD {mod_sel}.\nTotal: {simbolo} {tot_abonar:,.0f}\nCualquier duda avisame."
    if financiar and dif > 0 and res_final:
        msg_defecto += f"\nFinanciación: {res_final['linea']['n']} a {res_final['plazo']} meses.\nCuota inicial: $ {res_final['cuota']:,.0f}"
    
    st.text_area("Copiar y pegar en WhatsApp", msg_defecto, height=120)
