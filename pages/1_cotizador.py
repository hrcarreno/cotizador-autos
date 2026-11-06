import streamlit as st
import json
import re
from openai import OpenAI
from cotizador import MODELOS, LINEAS, calcular_frances, evaluar_linea, generar_codigo_disfrazado

st.set_page_config(page_title="Cotizador BYD", layout="wide")

# --- CONFIGURACIÓN DE GROQ ---
try:
    # Groq usa la misma sintaxis que OpenAI
    API_KEY = st.secrets["GROQ_API_KEY"]
    client = OpenAI(
        base_url="https://api.groq.com/openai/v1",
        api_key=API_KEY
    )
    ia_activa = True
except Exception as e:
    ia_activa = False

if "datos_ia" not in st.session_state:
    st.session_state.datos_ia = None

def procesar_pedido_ia(prompt):
    if not ia_activa: return None
    system_prompt = """Sos un asistente de ventas de autos BYD. Extraé datos del texto del vendedor y devolvé un JSON estricto.
    Claves permitidas: "modelo" (string), "anticipo" (entero en pesos, "10 palos" son 10000000), "usado" (entero en pesos), "prioridad" (string: cuota/inicial/costo).
    Si no se menciona algo, devolver null. No agregues texto extra, solo el JSON."""
    
    try:
        response = client.chat.completions.create(
            model="openai/gpt-oss-120b",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ],
            response_format={ "type": "json_object" }
        )
        # Groq devuelve el JSON listo, no hace falta regex
        return json.loads(response.choices[0].message.content)
    except Exception as e:
        st.error(f"Error de IA: {e}")
        return None

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
                    st.success("¡Datos cargados!")
                    st.rerun()
                else:
                    st.error("No entendí. Reformulá.")
    else:
        st.info("Para usar la IA, configurá GROQ_API_KEY en los Secrets.")

st.title("Cotizador BYD 0 km")
col1, col2 = st.columns(2)

with col1:
    st.subheader("1. Vehículo")
    nombres = [m["nombre"] for m in MODELOS]
    
    idx_mod = 0
    if st.session_state.datos_ia and st.session_state.datos_ia.get("modelo"):
        mod_ia = st.session_state.datos_ia["modelo"].lower()
        for i, n in enumerate(nombres):
            if mod_ia in n.lower():
                idx_mod = i
                break
                
    mod_sel = st.selectbox("Modelo", nombres, index=idx_mod)
    dm = next(m for m in MODELOS if m["nombre"] == mod_sel)
    es_usd = dm["moneda"] == "USD"
    
    st.markdown("---")
    if st.checkbox("Aplicar bonificación manual"):
        bon = st.number_input(f"Monto bonif. ({dm['moneda']})", min_value=0, step=1000)
        if bon > 0:
            st.code(f"Código: {generar_codigo_disfrazado(bon)}", language=None)
    else:
        bon = 0
        
    patenta = st.selectbox("Patentamiento", ["Concesionario", "Cliente"])
    tot_abonar = (dm["precio"] - bon) + dm["fyf"] + (dm["pat"] if patenta == "Concesionario" else 0)
    
    simbolo = "u$s" if es_usd else "$"
    st.info(f"**Total a abonar:** {simbolo} {tot_abonar:,.0f}")

    st.subheader("2. Forma de pago")
    tc = st.number_input("Dólar agencia ($)", min_value=1, step=10, value=1450)
    
    ant_ars = 0
    if st.checkbox("Entrego anticipo"):
        c1, c2 = st.columns(2)
        ant_ars = c1.number_input("En pesos", min_value=0, step=100000) + (c2.number_input("En dólares", min_value=0, step=100) * tc)
        
    usado_ars = 0
    if st.checkbox("Entrego vehículo en parte de pago"):
        c3, c4 = st.columns(2)
        tas = c3.number_input("Tasación", min_value=0, step=100000)
        usado_ars = tas * tc if c4.selectbox("Moneda", ["Pesos", "Dólares"]) == "Dólares" else tas

    tot_ars = tot_abonar * tc if es_usd else tot_abonar
    dif = tot_ars - ant_ars - usado_ars
    st.info(f"{'Saldo a favor' if dif < 0 else 'Diferencia a financiar'}: $ {abs(dif):,.0f}")

with col2:
    st.subheader("3. Financiación")
    if st.checkbox("Financiar la diferencia") and dif > 0:
        l_validas = [l for l in LINEAS if "aplica" not in l or any(app in dm["nombre"] for app in l["aplica"])]
        l_sel = next(l for l in l_validas if l["n"] == st.selectbox("Línea", [l["n"] for l in l_validas]))
        
        plazo = st.radio("Plazo (meses)", [r[0] for r in l_sel["r"]], horizontal=True)
        ex_c = st.number_input("Adicional concesionario (%)", min_value=0.0, step=0.1)
        qr = st.checkbox("Cobrar quebranto aunque BYD lo reintegre")
        
        res = evaluar_linea(l_sel, next(r for r in l_sel["r"] if r[0] == plazo), dif, tot_ars, ant_ars, ex_c, qr)
        
        if not res["alcanza"]:
            st.error(f"No alcanza. Faltan $ {res['falta']:,.0f}.")
        else:
            st.markdown(f"### Cuota: $ {res['cuota']:,.0f}")
            st.caption("Cuota inicial UVA" if res["uva"] else f"Última cuota: $ {res['cuota_fin']:,.0f}")
            st.write(f"Gasto otorgamiento ({res['gasto_pct']:.2f}%): $ {res['gasto_ars']:,.0f}")
            st.write(f"**Debés poner:** $ {res['poner_ars']:,.0f}")

        st.markdown("### 🏆 Mejores opciones")
        pr = st.selectbox("Priorizar:", ["Cuota más baja", "Poner menos al inicio", "Menor costo total"])
        opts = [evaluar_linea(l, r, dif, tot_ars, ant_ars, ex_c, qr) for l in l_validas for r in l["r"]]
        opts = [o for o in opts if o["alcanza"]]
        
        if pr == "Cuota más baja": opts.sort(key=lambda x: x["cuota"])
        elif pr == "Poner menos al inicio": opts.sort(key=lambda x: x["poner_ars"])
        else: opts.sort(key=lambda x: x["costo_fin"])
            
        for i, o in enumerate(opts[:3]):
            with st.expander(f"{i+1}. {o['linea']['n']} ({o['plazo']}m) - ${o['cuota']:,.0f}/mes"):
                st.write(f"TNA: {o['tna']}% | Inicio: $ {o['poner_ars']:,.0f} | Costo: $ {o['costo_fin']:,.0f}")
    
    st.markdown("---")
    st.subheader("4. Mensaje WhatsApp")
    st.text_area("Mensaje", f"Hola! Te paso la cotización de tu BYD {mod_sel}.\nTotal: {simbolo} {tot_abonar:,.0f}", height=100)
