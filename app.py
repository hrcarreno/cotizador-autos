import streamlit as st
import pandas as pd

# ===== CONFIGURACIÓN =====
st.set_page_config(
    page_title="Cotizador de Autos",
    page_icon="🚗",
    layout="wide"
)

# ===== URL DATOS_LIMPIOS (¡NO TIPEAR A MANO!) =====
URL_DATOS = "https://docs.google.com/spreadsheets/d/1838duFdovU2D_i4huwpntXYiCdi8MFED6Fd8p6imGSk/export?format=csv&gid=200943046"

# ===== CARGA DE DATOS =====
@st.cache_data(ttl=600)
def cargar_datos():
    try:
        df = pd.read_csv(URL_DATOS)
        columnas_numericas = [
            "precio_lista", "bonif", "precio_autogenerali",
            "flete", "alistamiento", "patentamiento", "sellado"
        ]
        for col in columnas_numericas:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)
        return df, None
    except Exception as e:
        return None, str(e)

df_datos, error_carga = cargar_datos()

# ===== ENCABEZADO =====
st.title("🚗 Cotizador de Autos")
st.markdown("Motor de cuotas — Etapa 5")
st.markdown("---")

# ===== MODO DEGRADADO (si el Sheet falla, sigue funcionando) =====
modo_manual = error_carga is not None
if modo_manual:
    st.warning(
        f"⚠️ No se pudieron cargar los datos del Sheet ({error_carga}). "
        "Usando valores por defecto (modo manual)."
    )
    df_datos = pd.DataFrame(columns=[
        "marca", "modelo", "version", "codigo", "etiqueta",
        "precio_lista", "bonif", "precio_autogenerali",
        "flete", "alistamiento", "patentamiento", "sellado"
    ])
else:
    df_datos["etiqueta"] = (
        df_datos["marca"].astype(str) + " " +
        df_datos["modelo"].astype(str) + " " +
        df_datos["version"].astype(str)
    )

# ===== SELECTOR DE VEHÍCULO =====
st.sidebar.header("🚙 Selección del Vehículo")

if modo_manual or df_datos.empty:
    opciones = ["— Elegir manualmente —"]
else:
    opciones = ["— Elegir manualmente —"] + sorted(df_datos["etiqueta"].unique().tolist())

seleccion = st.sidebar.selectbox("Modelo", opciones)

# Valores por defecto según selección
if seleccion != "— Elegir manualmente —" and not modo_manual:
    fila = df_datos[df_datos["etiqueta"] == seleccion].iloc[0]
    # Usar precio_autogenerali si existe, si no precio_lista
    if "precio_autogenerali" in fila and fila["precio_autogenerali"] > 0:
        precio_default = int(fila["precio_autogenerali"])
    else:
        precio_default = int(fila["precio_lista"])

    gastos_default = int(
        fila.get("flete", 0) +
        fila.get("alistamiento", 0) +
        fila.get("patentamiento", 0) +
        fila.get("sellado", 0)
    )
    codigo = fila.get("codigo", "—")
    st.sidebar.success(f"Código: `{codigo}`")
else:
    precio_default = 26_160_990
    gastos_default = 3_382_470

# ===== PARÁMETROS EDITABLES =====
st.sidebar.header("⚙️ Parámetros")

precio_vehiculo = st.sidebar.number_input(
    "Precio del Vehículo", value=precio_default, step=10_000, format="%d"
)
gastos = st.sidebar.number_input(
    "Gastos (flete, patentamiento, etc.)", value=gastos_default, step=10_000, format="%d"
)
anticipo = st.sidebar.number_input(
    "Anticipo", value=5_000_000, step=10_000, format="%d"
)
cuotas = st.sidebar.number_input(
    "Cantidad de Cuotas", value=36, step=1, min_value=1, max_value=120
)
tna = st.sidebar.number_input(
    "TNA (Tasa Nominal Anual)", value=0.60, step=0.01, format="%.2f"
)
comision_vendedor = st.sidebar.number_input(
    "Comisión Vendedor (oculta)", value=0.10, step=0.01, format="%.2f"
)

# ===== CONSTANTES =====
iva = 0.21

# ===== MOTOR DE CÁLCULO =====
total_a_cobrar = precio_vehiculo + gastos
gasto_otorgamiento_pct = comision_vendedor * (1 + iva) + 0.02
diferencia = total_a_cobrar - anticipo
gasto_otorgamiento = diferencia * gasto_otorgamiento_pct

monto_financiado = diferencia
tasa_mensual = tna / 12

# --- CASOS BORDE ---
if monto_financiado <= 0:
    st.error("⚠️ El anticipo es mayor o igual al total a cobrar. No hay monto para financiar.")
    st.stop()

if tasa_mensual == 0:
    cuota_pura = monto_financiado / cuotas
else:
    cuota_pura = (
        monto_financiado
        * (tasa_mensual * (1 + tasa_mensual) ** cuotas)
        / ((1 + tasa_mensual) ** cuotas - 1)
    )

deuda = monto_financiado
interes_inicial = deuda * tasa_mensual
primera_cuota = cuota_pura + interes_inicial * iva

deuda = monto_financiado
ultima_cuota = 0
for i in range(1, int(cuotas) + 1):
    interes = deuda * tasa_mensual
    capital = cuota_pura - interes
    deuda -= capital
    if i == int(cuotas):
        ultima_cuota = cuota_pura + interes * iva

debe_poner = anticipo + gasto_otorgamiento

# ===== RESULTADOS =====
st.header("📊 Resumen de la Cotización")

col1, col2, col3 = st.columns(3)
with col1:
    st.metric("Total a Cobrar", f"${total_a_cobrar:,.0f}".replace(",", "."))
with col2:
    st.metric(
        f"Gasto Otorgamiento ({gasto_otorgamiento_pct * 100:.2f}%)",
        f"${gasto_otorgamiento:,.0f}".replace(",", ".")
    )
with col3:
    st.metric("Debe Poner", f"${debe_poner:,.0f}".replace(",", "."))

st.markdown("---")

col4, col5, col6 = st.columns(3)
with col4:
    st.metric("Cuota Pura", f"${cuota_pura:,.0f}".replace(",", "."))
with col5:
    st.metric("Primera Cuota", f"${primera_cuota:,.0f}".replace(",", "."))
with col6:
    st.metric("Última Cuota", f"${ultima_cuota:,.0f}".replace(",", "."))

# ===== TABLA DE AMORTIZACIÓN =====
if st.checkbox("Mostrar tabla de amortización completa"):
    tabla = []
    deuda_actual = monto_financiado
    for i in range(1, int(cuotas) + 1):
        interes = deuda_actual * tasa_mensual
        iva_cuota = interes * iva
        cuota_total = cuota_pura + iva_cuota
        capital = cuota_pura - interes
        deuda_actual -= capital
        tabla.append({
            "Cuota": i,
            "Interés": round(interes, 2),
            "IVA s/Interés": round(iva_cuota, 2),
            "Cuota Total": round(cuota_total, 2),
            "Capital": round(capital, 2),
            "Saldo": round(max(0, deuda_actual), 2),
        })
    df_tabla = pd.DataFrame(tabla)
    st.dataframe(df_tabla.style.format("${:,.2f}"), use_container_width=True)

# ===== VALORES DE REFERENCIA =====
st.markdown("---")
with st.expander("📌 Valores de referencia (Argo Drive 1.3 MT)"):
    st.write("""
    - **Total a cobrar:** $29.543.460
    - **Gasto otorgamiento:** $3.460.628 (14,10%)
    - **Cuota pura:** $1.483.271
    - **Primera cuota:** $1.740.977
    - **Última cuota:** $1.498.103
    - **Debe poner:** $8.460.628
    """)

# ===== DEBUG =====
if not modo_manual:
    with st.expander("🔧 Debug — columnas del Sheet"):
        st.write("Columnas detectadas:", list(df_datos.columns))
        st.dataframe(df_datos.head(10))
