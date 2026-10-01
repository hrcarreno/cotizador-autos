import streamlit as st
import pandas as pd

# ===== CONFIGURACIÓN DE PÁGINA =====
st.set_page_config(
    page_title="Cotizador de Autos",
    page_icon="🚗",
    layout="wide"
)

st.title("🚗 Cotizador de Autos")
st.markdown("Motor de cuotas — Etapa 4")
st.markdown("---")

# ===== PANEL DE ENTRADAS (SIDEBAR) =====
st.sidebar.header("Datos de la Cotización")

precio_vehiculo = st.sidebar.number_input(
    "Precio del Vehículo",
    value=26_160_990,
    step=10_000,
    format="%d"
)

gastos = st.sidebar.number_input(
    "Gastos (flete, patentamiento, etc.)",
    value=3_382_470,
    step=10_000,
    format="%d"
)

anticipo = st.sidebar.number_input(
    "Anticipo",
    value=5_000_000,
    step=10_000,
    format="%d"
)

cuotas = st.sidebar.number_input(
    "Cantidad de Cuotas",
    value=36,
    step=1,
    min_value=1,
    max_value=120
)

tna = st.sidebar.number_input(
    "TNA (Tasa Nominal Anual)",
    value=0.60,
    step=0.01,
    format="%.2f"
)

comision_vendedor = st.sidebar.number_input(
    "Comisión Vendedor (oculta)",
    value=0.10,
    step=0.01,
    format="%.2f"
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

cuota_pura = (
    monto_financiado
    * (tasa_mensual * (1 + tasa_mensual) ** cuotas)
    / ((1 + tasa_mensual) ** cuotas - 1)
)

# Primera cuota (incluye IVA sobre interés inicial)
deuda = monto_financiado
interes_inicial = deuda * tasa_mensual
primera_cuota = cuota_pura + interes_inicial * iva

# Última cuota (simulando amortización completa)
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

# ===== TABLA DE AMORTIZACIÓN (OPCIONAL) =====
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
    df = pd.DataFrame(tabla)
    st.dataframe(
        df.style.format("${:,.2f}"),
        use_container_width=True
    )

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

    *Estos valores se obtienen con los datos precargados por defecto.
    Modificá los parámetros en el panel izquierdo para recalcular.*
    """)
