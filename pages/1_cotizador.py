import streamlit as st
import pandas as pd
from cotizador import cotizar_completo, generar_tabla_amortizacion
from codigo_disfrazado import generar_codigo_disfrazado

# ===== VALIDAR LOGIN =====
if not st.session_state.get("authentication_status"):
    st.error("Debés iniciar sesión para ver esta página.")
    st.stop()

# ===== TEMAS DISPONIBLES =====
TEMAS = {
    "Ambar Oscuro": {
        "bg": "#0E1117", "card": "#1A1D24", "border": "#2A2E38",
        "accent": "#F59E0B", "text": "#FAFAFA", "text_sec": "#8B92A0",
    },
    "Azul Oscuro": {
        "bg": "#0E1117", "card": "#1A1D24", "border": "#2A2E38",
        "accent": "#4A9EFF", "text": "#FAFAFA", "text_sec": "#8B92A0",
    },
    "Claro": {
        "bg": "#F5F7FA", "card": "#FFFFFF", "border": "#E2E8F0",
        "accent": "#D97706", "text": "#1A202C", "text_sec": "#718096",
    },
}

# ===== TEMA ACTUAL =====
if "tema_actual" not in st.session_state:
    st.session_state.tema_actual = "Ambar Oscuro"
T = TEMAS[st.session_state.tema_actual]

# ===== CSS =====
st.markdown(f"""
<style>
    .stApp {{ background-color: {T['bg']}; }}
    section[data-testid="stSidebar"] {{
        background-color: {T['card']};
        border-right: 1px solid {T['border']};
    }}
    .stApp, .stMarkdown, p, span, label {{ color: {T['text']} !important; }}
    h1, h2, h3, h4 {{
        color: {T['text']} !important;
        font-weight: 600 !important;
        letter-spacing: -0.02em;
    }}
    div[data-testid="stMetric"] {{
        background-color: {T['card']};
        border: 1px solid {T['border']};
        border-radius: 12px;
        padding: 20px 22px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.15);
    }}
    div[data-testid="stMetricLabel"] {{
        color: {T['text_sec']} !important;
        font-size: 0.78rem !important;
        font-weight: 500 !important;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }}
    div[data-testid="stMetricValue"] {{
        color: {T['text']} !important;
        font-size: 1.8rem !important;
        font-weight: 600 !important;
    }}
    .codigo-disfrazado {{
        background-color: {T['card']};
        border: 1px solid {T['border']};
        border-left: 3px solid {T['accent']};
        border-radius: 8px;
        padding: 12px 16px;
        font-family: monospace;
        font-size: 1.05rem;
        color: {T['accent']} !important;
        letter-spacing: 0.15em;
        font-weight: 600;
    }}
    .codigo-label {{
        font-size: 0.7rem;
        color: {T['text_sec']};
        text-transform: uppercase;
        letter-spacing: 0.1em;
        margin-bottom: 4px;
    }}
    hr {{ border-color: {T['border']} !important; margin: 1.5rem 0 !important; }}
</style>
""", unsafe_allow_html=True)

# ===== HEADER =====
st.markdown(f"""
<div style="border-bottom: 1px solid {T['border']}; padding-bottom: 1rem; margin-bottom: 2rem;">
    <div style="font-size: 1.6rem; font-weight: 700; color: {T['text']}; margin: 0;">Cotizador</div>
    <div style="font-size: 0.85rem; color: {T['text_sec']}; margin-top: 0.25rem;">
        Sistema de cotización de vehículos
    </div>
</div>
""", unsafe_allow_html=True)

# ===== URL DATOS_LIMPIOS =====
URL_DATOS = "https://docs.google.com/spreadsheets/d/1838duFdovU2D_i4huwpntXYiCdi8MFED6Fd8p6imGSk/export?format=csv&gid=200943046"

# ===== CARGAR DATOS =====
@st.cache_data(ttl=600)
def cargar_datos():
    try:
        df = pd.read_csv(URL_DATOS)
        columnas_numericas = [
            "precio_lista", "bonif", "precio_autogenerali",
            "flete", "alistamiento", "patentamiento", "sellado",
        ]
        for col in columnas_numericas:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)
        return df, None
    except Exception as e:
        return None, str(e)


df_datos, error_carga = cargar_datos()
modo_manual = error_carga is not None

# ===== SIDEBAR: SELECCIÓN =====
with st.sidebar:
    st.markdown("### Vehículo")

    if modo_manual or df_datos.empty:
        marcas = ["Todas"]
        modelos_filtrados = []
    else:
        df_datos["etiqueta"] = (
            df_datos["marca"].astype(str) + " " +
            df_datos["modelo"].astype(str) + " " +
            df_datos["version"].astype(str)
        )
        marcas = ["Todas"] + sorted(df_datos["marca"].dropna().unique().tolist())

    if modo_manual:
        st.warning("Modo manual (no se pudieron cargar los datos).")
        seleccion = "— Elegir manualmente —"
        marca_sel = "Todas"
    else:
        marca_sel = st.selectbox("Marca", marcas)
        if marca_sel == "Todas":
            df_filtrado = df_datos
        else:
            df_filtrado = df_datos[df_datos["marca"] == marca_sel]
        modelos_filtrados = ["— Elegir manualmente —"] + sorted(
            df_filtrado["etiqueta"].dropna().unique().tolist()
        )
        seleccion = st.selectbox("Modelo", modelos_filtrados)

    # Valores por defecto
    if seleccion != "— Elegir manualmente —" and not modo_manual:
        fila = df_datos[df_datos["etiqueta"] == seleccion].iloc[0]
        if "precio_autogenerali" in fila and fila["precio_autogenerali"] > 0:
            precio_default = int(fila["precio_autogenerali"])
        else:
            precio_default = int(fila["precio_lista"])
        lista_default = int(fila.get("precio_lista", precio_default))
        gastos_default = int(
            fila.get("flete", 0) + fila.get("alistamiento", 0) +
            fila.get("patentamiento", 0) + fila.get("sellado", 0)
        )
        descuento_max = lista_default - precio_default
        codigo_dis = generar_codigo_disfrazado(descuento_max) if descuento_max > 0 else ""
        if codigo_dis:
            st.markdown(f"""
            <div class="codigo-label">Código</div>
            <div class="codigo-disfrazado">{codigo_dis}</div>
            """, unsafe_allow_html=True)
    else:
        precio_default = 26_160_990
        gastos_default = 3_382_470

    st.markdown("### Parámetros")
    precio_vehiculo = st.number_input("Precio", value=precio_default, step=10_000, format="%d")
    gastos = st.number_input("Gastos", value=gastos_default, step=10_000, format="%d")
    anticipo = st.number_input("Anticipo", value=5_000_000, step=10_000, format="%d")
    cuotas = st.number_input("Cuotas", value=36, step=1, min_value=1, max_value=120)
    tna = st.number_input("TNA", value=0.60, step=0.01, format="%.2f")
    comision_vendedor = st.number_input("Comisión vendedor", value=0.10, step=0.01, format="%.2f")

# ===== CÁLCULO =====
resultado = cotizar_completo(
    precio_vehiculo=precio_vehiculo,
    gastos=gastos,
    anticipo=anticipo,
    cuotas=cuotas,
    tna=tna,
    comision_vendedor=comision_vendedor,
)

if resultado["monto_financiado"] <= 0:
    st.error("El anticipo es mayor o igual al total a cobrar.")
    st.stop()

# ===== RESULTADOS =====
st.markdown("### Resumen")

c1, c2, c3 = st.columns(3)
with c1:
    st.metric("Total a cobrar", f"${resultado['total_a_cobrar']:,.0f}".replace(",", "."))
with c2:
    st.metric(f"Gasto otorgamiento ({resultado['gasto_otorgamiento_pct']*100:.2f}%)",
              f"${resultado['gasto_otorgamiento']:,.0f}".replace(",", "."))
with c3:
    st.metric("Debe poner", f"${resultado['debe_poner']:,.0f}".replace(",", "."))

st.markdown("")
c4, c5, c6 = st.columns(3)
with c4:
    st.metric("Cuota pura", f"${resultado['cuota_pura']:,.0f}".replace(",", "."))
with c5:
    st.metric("Primera cuota", f"${resultado['primera_cuota']:,.0f}".replace(",", "."))
with c6:
    st.metric("Última cuota", f"${resultado['ultima_cuota']:,.0f}".replace(",", "."))

st.markdown("---")

with st.expander("Ver plan de cuotas completo"):
    tabla = generar_tabla_amortizacion(
        monto_financiado=resultado["monto_financiado"],
        cuotas=cuotas,
        tna=tna,
    )
    if tabla:
        df_tabla = pd.DataFrame(tabla)
        st.dataframe(df_tabla, use_container_width=True, hide_index=True)
