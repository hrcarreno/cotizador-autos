class CotizacionGuardar(BaseModel):
    cliente_nombre: str
    cliente_telefono: str
    modelo: str
    moneda: str
    total: float
    anticipo: float
    diferencia: float
    financiado: bool
    linea_financiacion: Optional[str] = None
    plazo: Optional[int] = None
    cuota_inicial: Optional[float] = None

@app.post("/api/cotizaciones")
async def guardar_cotizacion(data: CotizacionGuardar):
    try:
        supabase.table("cotizaciones").insert({
            "cliente_nombre": data.cliente_nombre,
            "cliente_telefono": data.cliente_telefono,
            "modelo": data.modelo,
            "moneda": data.moneda,
            "total": data.total,
            "anticipo": data.anticipo,
            "diferencia": data.diferencia,
            "financiado": data.financiado,
            "linea_financiacion": data.linea_financiacion,
            "plazo": data.plazo,
            "cuota_inicial": data.cuota_inicial
        }).execute()
        return {"status": "ok", "message": "Cotización guardada exitosamente"}
    except Exception as e:
        return {"error": str(e)}
