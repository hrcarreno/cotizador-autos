import math

# [nombre, moneda, precio_lista, bonif, fyf, patentamiento]
MODELOS = [
    {"nombre": "Dolphin Mini EV GL", "moneda": "ARS", "precio": 36200000, "bonif": 2172000, "fyf": 800000, "pat": 2381960},
    {"nombre": "Dolphin Mini EV GS", "moneda": "ARS", "precio": 37700000, "bonif": 2262000, "fyf": 800000, "pat": 2480660},
    {"nombre": "Yuan Pro EV GL", "moneda": "USD", "precio": 30990, "bonif": 0, "fyf": 500, "pat": 2169},
    {"nombre": "Yuan Pro EV GS", "moneda": "USD", "precio": 31990, "bonif": 0, "fyf": 500, "pat": 2239},
    {"nombre": "Atto 2 DM-I GS", "moneda": "USD", "precio": 32291, "bonif": 1615, "fyf": 500, "pat": 2147},
    {"nombre": "Song Pro DM-I GL", "moneda": "USD", "precio": 33716, "bonif": 1686, "fyf": 500, "pat": 2242},
    {"nombre": "Song Pro DM-I GS", "moneda": "USD", "precio": 35616, "bonif": 1781, "fyf": 500, "pat": 2368},
    {"nombre": "Seal U DM-I GS", "moneda": "USD", "precio": 47990, "bonif": 0, "fyf": 800, "pat": 3359},
    {"nombre": "SHARK DM-O GS", "moneda": "USD", "precio": 59990, "bonif": 4799, "fyf": 800, "pat": 3863},
    {"nombre": "TI7 GS", "moneda": "USD", "precio": 65500, "bonif": 0, "fyf": 800, "pat": 4585},
    {"nombre": "Seal 5", "moneda": "USD", "precio": 31990, "bonif": 1600, "fyf": 500, "pat": 2127}
]

LINEAS = [
    {"n": "Convenio BYD · UVA 0%", "k": "conv", "uva": True, "aplica": ["Dolphin Mini", "Song Pro", "Yuan Pro", "Seal 5", "Atto 2"], 
     "r": [[12, 0, 6.56, 25000000], [18, 0, 9.64, 17000000]]},
    {"n": "Convenio BYD · Fija 0%", "k": "conv", "uva": False, "aplica": ["Dolphin Mini", "Song Pro", "Yuan Pro", "Seal 5", "Atto 2"], 
     "r": [[12, 0, 16.39, 10000000]]},
    {"n": "Convenio BYD · Fija 9,90%", "k": "conv", "uva": False, "aplica": ["Dolphin Mini", "Song Pro", "Yuan Pro", "Seal 5", "Atto 2"], 
     "r": [[12, 9.9, 10.93, 15000000]]},
    {"n": "Convenio BYD · Fija 14,90%", "k": "conv", "uva": False, "aplica": ["Dolphin Mini", "Song Pro", "Yuan Pro", "Seal 5", "Atto 2"], 
     "r": [[18, 14.9, 12.61, 13000000]]},
    {"n": "Quebranto concesionario · Fija 0%", "k": "queb", "uva": False, "ltv": [90, 100], 
     "r": [[12, 0, 15.8, None], [18, 0, 21.9, None], [24, 0, 27.5, None], [36, 0, 37, None], [48, 0, 44.8, None]]},
    {"n": "Quebranto concesionario · UVA 0%", "k": "queb", "uva": True, "ltv": [85], 
     "r": [[12, 0, 6.5, None], [18, 0, 9.3, None], [24, 0, 12, None], [36, 0, 17, None], [48, 0, 21.6, None]]},
    {"n": "Quebranto concesionario · UVA 9,90%", "k": "queb", "uva": True, "ltv": [85], 
     "r": [[12, 9.9, 1.4, None], [18, 9.9, 2, None], [24, 9.9, 2.6, None], [36, 9.9, 3.7, None], [48, 9.9, 4.8, None]]},
    {"n": "Sin quebranto · UVA 12,50%", "k": "sin", "uva": True, "ltv": [85], 
     "r": [[12, 12.5, 0, None], [18, 12.5, 0, None], [24, 12.5, 0, None], [36, 12.5, 0, None], [48, 12.5, 0, None]]},
    {"n": "Sin quebranto · Fija 32,90%", "k": "sin", "uva": False, "ltv": [90, 100], 
     "r": [[12, 32.9, 0, None], [18, 32.9, 0, None], [24, 32.9, 0, None], [36, 32.9, 0, None], [48, 32.9, 0, None], [60, 32.9, 0, None]]},
    {"n": "Comisión · UVA 14,50%", "k": "com", "uva": True, "ltv": [85], 
     "r": [[12, 14.5, 0, None], [18, 14.5, 0, None], [24, 14.5, 0, None], [36, 14.5, 0, None], [48, 14.5, 0, None]]},
    {"n": "Comisión · Fija 34,90%", "k": "com", "uva": False, "ltv": [90, 100], 
     "r": [[12, 34.9, 0, None], [18, 34.9, 0, None], [24, 34.9, 0, None], [36, 34.9, 0, None], [48, 34.9, 0, None], [60, 34.9, 0, None]]}
]

def calcular_frances(monto, tna, meses):
    if monto <= 0: return {"first": 0, "last": 0, "sum": 0}
    i = tna / 1200
    pura = monto * i / (1 - math.pow(1 + i, -meses)) if i > 0 else monto / meses
    deuda = monto
    sum_cuotas = 0
    first = 0
    last = 0
    for k in range(1, meses + 1):
        interes = deuda * i
        if k == meses:
            amort = deuda
            cuota = deuda + (deuda * i * 0.21)
        else:
            amort = pura - interes
            cuota = pura + (interes * 0.21)
        if k == 1: first = cuota
        last = cuota
        sum_cuotas += cuota
        deuda -= amort
        if deuda < 0: deuda = 0
    return {"first": first, "last": last, "sum": sum_cuotas}

def generar_codigo_disfrazado(monto):
    n = round(monto)
    if n <= 0: return ""
    return f"FC{n // 1000000:03d}AG{(n % 1000000) // 1000:03d}HC{n % 1000:03d}"

def evaluar_linea(linea, plazo_data, dif_ars, cot_ars, anticipo_ars, ex_conce, qr):
    plazo, tna, quebranto, tope = plazo_data
    ltv_pct = linea.get("ltv", [100])[0] if linea.get("ltv") else None
    tope_final = min(tope or float('inf'), (ltv_pct / 100) * cot_ars if ltv_pct else float('inf'))
    q_pct = (quebranto * 1.21) if (linea["k"] != "conv" or qr) else 0
    gp_pct = q_pct + ex_conce
    gasto = dif_ars * (gp_pct / 100)
    fr = calcular_frances(dif_ars, tna, plazo)
    return {
        "linea": linea, "plazo": plazo, "tna": tna, "quebranto": quebranto,
        "tope": tope_final, "gasto_pct": gp_pct, "gasto_ars": gasto,
        "poner_ars": anticipo_ars + gasto, "cuota": fr["first"],
        "cuota_fin": fr["last"], "total_cuotas": fr["sum"],
        "alcanza": dif_ars <= tope_final, "falta": max(0, dif_ars - tope_final),
        "costo_fin": fr["sum"] - dif_ars + gasto, "uva": linea["uva"]
    }
