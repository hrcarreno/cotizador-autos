import streamlit as st
import pandas as pd
from cotizador import (
    cotizar_completo,
    generar_tabla_amortizacion,
)
from codigo_disfrazado import generar_codigo_disfrazado

# ===== CONFIGURACIÓN =====
st.set_page_config(
    page_title="Cotizador",
    page_icon=None,
    layout="wide",
    initial_sidebar_state="expanded",
)

# ===== TEMAS DISPONIBLES =====
TEMAS = {
    "Ambar Oscuro": {
        "bg": "#0E1117",
        "card": "#1A1D24",
        "border": "#2A2E38",
        "accent": "#F59E0B",
        "text": "#FAFAFA",
        "text_sec": "#8B92A0",
        "success": "#10B981",
        "danger": "#EF4444",
    },
    "Azul Oscuro": {
        "bg": "#0E1117",
        "card": "#1A1D24",
        "border": "#2A2E38",
        "accent": "#4A9EFF",
        "text": "#FAFAFA",
        "text_sec": "#8B92A0",
        "success": "#10B981",
        "danger": "#EF4444",
    },
    "Claro": {
        "bg": "#F5F7FA",
        "card": "#FFFFFF",
        "border": "#E2E8F0",
        "accent": "#D97706",
        "text": "#1A202C",
        "text_sec": "#718096",
        "success": "#059669",
        "danger": "#DC2626",
    },
}

# ===== SELECTOR DE TEMA =====
if "tema_actual" not in st.session_state:
    st.session_state.tema_actual = "Ambar Oscuro"

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

# ===== SELECTOR DE TEMA EN SIDEBAR (arriba de todo) =====
with st.sidebar:
    st.markdown("### Configuracion")
    tema_elegido = st.selectbox(
        "Tema",
        list(TEMAS.keys()),
        index=list(TEMAS.keys()).index(st.session_state.tema_actual),
        label_visibility="collapsed",
    )
    if tema_elegido != st.session_state.tema_actual:
        st.session_state.tema_actual = tema_elegido
        st.rerun()

T = TEMAS[st.session_state.tema_actual]

# ===== CSS DINÁMICO =====
st.markdown(f"""
<style>
    /* Fondo general */
    .stApp {{
        background-color: {T['bg']};
    }}

    /* Sidebar */
    section[data-testid="stSidebar"] {{
        background-color: {T['card']};
        border-right: 1px solid {T['border']};
    }}

    /* Texto general */
    .stApp, .stMarkdown, p, span, label {{
        color: {T['text']} !important;
    }}

    /* Títulos */
    h1, h2, h3, h4 {{
        color: {T['text']} !important;
        font-weight: 600 !important;
        letter-spacing: -0.02em;
    }}

    /* Inputs */
    .stTextInput input, .stNumberInput input, .stSelectbox div[data-baseweb="select"] {{
        background-color: {T['bg']} !important;
        color: {T['text']} !important;
        border: 1px solid {T['border']} !important;
    }}

    /* Cards de métricas */
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

    /* Botón primario */
    .stButton button {{
        background-color: {T['accent']} !important;
        color: #FFFFFF !important;
        border: none !important;
        border-radius: 8px !important;
        font-weight: 500 !important;
    }}
    .stButton button:hover {{
        opacity: 0.9;
    }}

    /* Expander */
    .streamlit-expanderHeader {{
        background-color: {T['card']} !important;
        border: 1px solid {T['border']} !important;
        border-radius: 8px !important;
        color: {T['text']} !important;
    }}

    /* Divider */
    hr {{
        border-color: {T['border']} !important;
        margin: 1.5rem 0 !important;
    }}

    /* Header personalizado */
    .app-header {{
        border-bottom: 1px solid {T['border']};
        padding-bottom: 1rem;
        margin-bottom: 2rem;
    }}
    .app-title {{
        font-size: 1.6rem;
        font-weight: 700;
        color: {T['text']};
        margin: 0;
        letter-spacing: -0.02em;
    }}
    .app-subtitle {{
        font-size: 0.85rem;
        color: {T['text_sec']};
        margin-top: 0.25rem;
    }}

    /* Código disfrazado */
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

    /* Ocultar branding de Streamlit */
    #MainMenu {{visibility: hidden;}}
    footer {{visibility: hidden;}}
</style>
""", unsafe_allow_html=True)

# ===== HEADER =====
st.markdown("""
<div class="app-header">
    <div class="app-title">Cotizador</div>
    <div class="app-subtitle">Sistema de cotizacion de vehiculos</div>
</div>
""", unsafe_allow_html=True)

# ===== MODO DEGRADADO =====
if modo_manual:
    st.warning(
        f"No se pudieron cargar los datos del catalogo ({error_carga}). "
        "Modo manual activado."
    )
    df_datos = pd.DataFrame(columns=[
        "marca", "modelo", "version", "codigo", "etiqueta",
        "precio_lista", "bonif", "precio_autogenerali",
        "flete", "alistamiento", "patentamiento", "sellado",
    ])
else:
    df_datos["etiqueta"] = (
        df_datos["marca"].astype(str) + " " +
        df_datos["modelo"].astype(str) + " " +
        df_datos["version"].astype(str)
    )

# ===== SIDEBAR: SELECCIÓN =====
with st.sidebar:
    st.markdown("### Vehiculo")

    if modo_manual or df_datos.empty:
        marcas = ["Todas"]
        modelos_filtrados = []
    else:
        marcas = ["Todas"] + sorted(df_datos["marca"].dropna().unique().tolist())
        marca_sel = st.selectbox("Marca", marcas)

        if marca_sel == "Todas":
            df_filtrado = df_datos
        else:
            df_filtrado = df_datos[df_datos["marca"] == marca_sel]

        modelos_filtrados = ["— Elegir manualmente —"] + sorted(
            df_filtrado["etiqueta"].dropna().unique().tolist()
        )

    if modelos_filtrados:
        seleccion = st.selectbox("Modelo", modelos_filtrados)
    else:
        seleccion = "— Elegir manualmente —"

    # Valores por defecto
    if seleccion != "— Elegir manualmente —" and not modo_manual:
        fila = df_datos[df_datos["etiqueta"] == seleccion].iloc[0]

        if "precio_autogenerali" in fila and fila["precio_autogenerali"] > 0:
            precio_default = int(fila["precio_autogenerali"])
        else:
            precio_default = int(fila["precio_lista"])

        lista_default = int(fila.get("precio_lista", precio_default))

        gastos_default = int(
            fila.get("flete", 0) +
            fila.get("alistamiento", 0) +
            fila.get("patentamiento", 0) +
            fila.get("sellado", 0)
        )
        codigo_real = fila.get("codigo", "")

        # Código disfrazado del descuento (se muestra solo en pantalla)
        descuento = lista_default - precio_default
        codigo_dis = generar_codigo_disfrazado(descuento) if descuento > 0 else ""

        if codigo_dis:
            st.markdown(f"""
            <div class="codigo-label">Codigo</div>
            <div class="codigo-disfrazado">{codigo_dis}</div>
            """, unsafe_allow_html=True)
    else:
        precio_default = 26_160_990
        lista_default = 26_160_990
        gastos_default = 3_382_470

    # Parámetros
    st.markdown("### Parametros")

    precio_vehiculo = st.number_input(
        "Precio", value=precio_default, step=10_000, format="%d"
    )
    gastos = st.number_input(
        "Gastos", value=gastos_default, step=10_000, format="%d"
    )
    anticipo = st.number_input(
        "Anticipo", value=5_000_000, step=10_000, format="%d"
    )
    cuotas = st.number_input(
        "Cuotas", value=36, step=1, min_value=1, max_value=120
    )
    tna = st.number_input(
        "TNA", value=0.60, step=0.01, format="%.2f"
    )
    comision_vendedor = st.number_input(
        "Comision vendedor", value=0.10, step=0.01, format="%.2f"
    )

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
    st.error("El anticipo es mayor o igual al total a cobrar. No hay monto para financiar.")
    st.stop()

# ===== RESULTADOS =====
st.markdown("### Resumen")

col1, col2, col3 = st.columns(3)
with col1:
    st.metric(
        "Total a cobrar",
        f"${resultado['total_a_cobrar']:,.0f}".replace(",", "."),
    )
with col2:
    st.metric(
        f"Gasto otorgamiento ({resultado['gasto_otorgamiento_pct'] * 100:.2f}%)",
        f"${resultado['gasto_otorgamiento']:,.0f}".replace(",", "."),
    )
with col3:
    st.metric(
        "Debe poner",
        f"${resultado['debe_poner']:,.0f}".replace(",", "."),
    )

st.markdown("")

col4, col5, col6 = st.columns(3)
with col4:
    st.metric(
        "Cuota pura",
        f"${resultado['cuota_pura']:,.0f}".replace(",", "."),
    )
with col5:
    st.metric(
        "Primera cuota",
        f"${resultado['primera_cuota']:,.0f}".replace(",", "."),
    )
with col6:
    st.metric(
        "Ultima cuota",
        f"${resultado['ultima_cuota']:,.0f}".replace(",", "."),
    )

st.markdown("---")

# ===== TABLA DE AMORTIZACIÓN =====
with st.expander("Ver plan de cuotas completo"):
    tabla = generar_tabla_amortizacion(
        monto_financiado=resultado["monto_financiado"],
        cuotas=cuotas,
        tna=tna,
    )
    if tabla:
        df_tabla = pd.DataFrame(tabla)
        st.dataframe(
            df_tabla.style.format({
                "Interes": "${:,.2f}",
                "IVA s/Interes": "${:,.2f}",
                "Cuota Total": "${:,.2f}",
                "Capital": "${:,.2f}",
                "Saldo": "${:,.2f}",
            }),
            use_container_width=True,
            hide_index=True,
        )

# ===== DEBUG =====
if not modo_manual:
    with st.expander("Informacion del catalogo"):
        st.caption(f"Registros cargados: {len(df_datos)}")
        st.dataframe(df_datos.head(10), use_container_width=True, hide_index=True)
