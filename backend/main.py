import csv
import io
from fastapi import UploadFile, File
from fastapi.responses import StreamingResponse

# ... (tus imports y código anterior)

# ==========================================
# ENDPOINTS DE IMPORTACIÓN / EXPORTACIÓN
# ==========================================

@app.get("/api/admin/exportar")
async def exportar_datos():
    # Exportar Modelos
    modelos = supabase.table("modelos").select("*").execute().data
    output_m = io.StringIO()
    writer_m = csv.writer(output_m)
    if modelos:
        writer_m.writerow(modelos[0].keys())
        for m in modelos:
            writer_m.writerow(m.values())
    
    # Exportar Líneas (Simplificado para CSV)
    lineas = supabase.table("lineas_financiacion").select("*").execute().data
    output_l = io.StringIO()
    writer_l = csv.writer(output_l)
    if lineas:
        writer_l.writerow(["id", "nombre", "tipo", "uva", "aplica_a", "plazos", "activo"])
        for l in lineas:
            writer_l.writerow([l["id"], l["nombre"], l["tipo"], l["uva"], ",".join(l["aplica_a"] or []), str(l["plazos"]), l["activo"]])

    # Juntamos todo en un solo archivo separado por un encabezado
    contenido_final = "--- MODELOS ---\n" + output_m.getvalue() + "\n\n--- LINEAS ---\n" + output_l.getvalue()
    
    return StreamingResponse(
        io.BytesIO(contenido_final.encode('utf-8')),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=datos_byd.csv"}
    )

@app.post("/api/admin/importar")
async def importar_datos(file: UploadFile = File(...)):
    try:
        contents = await file.read()
        texto = contents.decode("utf-8")
        
        # Separar las dos partes del archivo
        partes = texto.split("--- LINEAS ---")
        parte_modelos = partes[0].replace("--- MODELOS ---", "").strip()
        parte_lineas = partes[1].strip() if len(partes) > 1 else ""

        # 1. BORRAR DATOS ANTIGUOS (Para evitar duplicados)
        supabase.table("modelos").delete().neq("id", 0).execute()
        supabase.table("lineas_financiacion").delete().neq("id", 0).execute()

        # 2. IMPORTAR MODELOS
        reader_m = csv.DictReader(io.StringIO(parte_modelos))
        nuevos_modelos = []
        for row in reader_m:
            if not row.get("nombre"): continue
            nuevos_modelos.append({
                "nombre": row["nombre"],
                "moneda": row["moneda"],
                "precio": float(row["precio"]),
                "bonif": float(row["bonif"] or 0),
                "fyf": float(row["fyf"] or 0),
                "pat": float(row["pat"] or 0),
                "activo": row["activo"].lower() == 'true'
            })
        if nuevos_modelos:
            supabase.table("modelos").insert(nuevos_modelos).execute()

        # 3. IMPORTAR LINEAS
        reader_l = csv.DictReader(io.StringIO(parte_lineas))
        nuevas_lineas = []
        for row in reader_l:
            if not row.get("nombre"): continue
            # Convertimos el string de plazos a JSON real
            plazos_json = eval(row["plazos"]) if row["plazos"] else []
            nuevas_lineas.append({
                "nombre": row["nombre"],
                "tipo": row["tipo"],
                "uva": row["uva"].lower() == 'true',
                "aplica_a": row["aplica_a"].split(",") if row["aplica_a"] else [],
                "plazos": plazos_json,
                "activo": row["activo"].lower() == 'true'
            })
        if nuevas_lineas:
            supabase.table("lineas_financiacion").insert(nuevas_lineas).execute()

        return {"status": "ok", "message": "Datos importados y reemplazados correctamente"}
    except Exception as e:
        return {"error": f"Error al importar: {str(e)}"}
