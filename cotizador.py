"""
Motor de cálculo del cotizador.
Funciones puras, sin dependencias de Streamlit.
"""


def calcular_gasto_otorgamiento(diferencia, comision_vendedor, iva=0.21):
    """
    Calcula el gasto de otorgamiento.
    Regla de negocio: comision × (1 + IVA) + 2%
    """
    porcentaje = comision_vendedor * (1 + iva) + 0.02
    monto = diferencia * porcentaje
    return monto, porcentaje


def calcular_cuota_pura(monto_financiado, cuotas, tna):
    """
    Calcula la cuota pura (PMT clásico).
    Maneja el caso TNA = 0 sin romper.
    """
    if monto_financiado <= 0:
        return 0
    if cuotas <= 0:
        return 0

    tasa_mensual = tna / 12

    if tasa_mensual == 0:
        return monto_financiado / cuotas

    factor = (1 + tasa_mensual) ** cuotas
    return monto_financiado * (tasa_mensual * factor) / (factor - 1)


def calcular_primera_y_ultima_cuota(monto_financiado, cuotas, tna, iva=0.21):
    """
    Calcula la primera y última cuota incluyendo IVA sobre el interés.
    Devuelve (primera_cuota, ultima_cuota).
    """
    if monto_financiado <= 0 or cuotas <= 0:
        return 0, 0

    tasa_mensual = tna / 12
    cuota_pura = calcular_cuota_pura(monto_financiado, cuotas, tna)

    # Primera cuota
    interes_inicial = monto_financiado * tasa_mensual
    primera_cuota = cuota_pura + interes_inicial * iva

    # Última cuota: simular amortización completa
    deuda = monto_financiado
    ultima_cuota = 0
    for i in range(1, int(cuotas) + 1):
        interes = deuda * tasa_mensual
        capital = cuota_pura - interes
        deuda -= capital
        if i == int(cuotas):
            ultima_cuota = cuota_pura + interes * iva

    return primera_cuota, ultima_cuota


def generar_tabla_amortizacion(monto_financiado, cuotas, tna, iva=0.21):
    """
    Devuelve una lista de diccionarios con la amortización cuota por cuota.
    """
    if monto_financiado <= 0 or cuotas <= 0:
        return []

    tasa_mensual = tna / 12
    cuota_pura = calcular_cuota_pura(monto_financiado, cuotas, tna)

    tabla = []
    deuda = monto_financiado

    for i in range(1, int(cuotas) + 1):
        interes = deuda * tasa_mensual
        iva_cuota = interes * iva
        cuota_total = cuota_pura + iva_cuota
        capital = cuota_pura - interes
        deuda -= capital

        tabla.append({
            "Cuota": i,
            "Interes": round(interes, 2),
            "IVA s/Interes": round(iva_cuota, 2),
            "Cuota Total": round(cuota_total, 2),
            "Capital": round(capital, 2),
            "Saldo": round(max(0, deuda), 2),
        })

    return tabla


def cotizar_completo(
    precio_vehiculo,
    gastos,
    anticipo,
    cuotas,
    tna,
    comision_vendedor,
    iva=0.21,
):
    """
    Realiza el cálculo completo y devuelve un diccionario con todos los resultados.
    """
    total_a_cobrar = precio_vehiculo + gastos
    diferencia = total_a_cobrar - anticipo

    gasto_otorgamiento, gasto_otorgamiento_pct = calcular_gasto_otorgamiento(
        diferencia, comision_vendedor, iva
    )

    monto_financiado = diferencia
    cuota_pura = calcular_cuota_pura(monto_financiado, cuotas, tna)
    primera_cuota, ultima_cuota = calcular_primera_y_ultima_cuota(
        monto_financiado, cuotas, tna, iva
    )

    debe_poner = anticipo + gasto_otorgamiento

    return {
        "total_a_cobrar": total_a_cobrar,
        "diferencia": diferencia,
        "monto_financiado": monto_financiado,
        "gasto_otorgamiento": gasto_otorgamiento,
        "gasto_otorgamiento_pct": gasto_otorgamiento_pct,
        "cuota_pura": cuota_pura,
        "primera_cuota": primera_cuota,
        "ultima_cuota": ultima_cuota,
        "debe_poner": debe_poner,
    }
