from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from supabase import create_client, Client
from openai import OpenAI
import os
import json
import io
import pandas as pd
from dotenv import load_dotenv
from typing import List, Optional

load_dotenv()

app = FastAPI(title="Cotizador BYD API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

try:
    supabase: Client = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))
    client_ia = OpenAI(
        base_url="https://api.groq.com/openai/v1",
        api_key=os.getenv("GROQ_API_KEY")
    )
except Exception as e:
    print(f"Error de conexión: {e}")

@app.get("/")
def read_root():
    return {"status": "ok", "message": "API del Cotizador funcionando"}

# ==========================================
# ENDPOINTS PÚBLICOS (Para el Frontend)
# ==========================================

@app.get("/api/config")
async def get_config():
    res = supabase.table("configuracion_global").select("*").execute()
    return {item["clave"]: item["valor"] for item in res.data}

@app.get("/api/modelos")
async def get_modelos():
    res = supabase.table("modelos").select("*").eq("activo", True).order("id").execute()
    return res.data

@app.get("/api/lineas")
async def get_lineas():
    # Traemos todas las filas de la tabla plana y las agrupamos por nombre de línea
    res = supabase.table("lineas_financiacion").select("*").eq("activo", True).execute()
    lineas_planas = res.data
    
    agrupadas = {}
    for fila in lineas_planas:
        nombre = fila["nombre"]
        if nombre not in agrupadas:
            agrupadas[nombre] = {
                "id": fila["id"], # Usamos el primer ID como referencia
                "nombre": nombre,
                "tipo": fila["tipo"],
                "uva": fila["uva"],
                "aplica_a": fila["aplica_a"],
                "activo": fila["activo"],
                "plazos": []
            }
        agrupadas[nombre]["plazos"].append([
            int(fila["plazo"]),
            float(fila["tna"]),
            float(fila["quebranto"]),
            tope_val = fila.get("tope")
            tope_final = float(tope_val) if tope_val is not None and str(tope_val).strip() != "" else None
        ])
    
    return list(agrupadas.values())

# ==========================================
# ENDPOINTS DE ADMINISTRACIÓN
# ==========================================

class UpdateConfig(BaseModel):
    clave: str
    valor: float

@app.put("/api/admin/config")
async def update_config(data: UpdateConfig):
    supabase.table("configuracion_global").upsert({"clave": data.clave, "valor": data.valor}).execute()
    return {"status": "ok"}

@app.get("/api/admin/exportar")
async def exportar_datos():
    # 1. Traer Modelos
    modelos = supabase.table("modelos").select("*").execute().data
    df_modelos = pd.DataFrame(modelos)
    if not df_modelos.empty:
        df_modelos = df_modelos[["nombre", "moneda", "precio", "bonif", "fyf", "pat", "activo"]]

    # 2. Traer Líneas (Ya vienen planas desde la BD)
    lineas = supabase.table("lineas_financiacion").select("*").execute().data
    df_lineas = pd.DataFrame(lineas)
    if not df_lineas.empty:
        df_lineas = df_lineas[["nombre", "tipo", "uva", "aplica_a", "plazo", "tna", "quebranto", "tope", "activo"]]
        df_lineas["aplica_a"] = df_lineas["aplica_a"].apply(lambda x: ",".join(x) if isinstance(x, list) else "")

    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df_modelos.to_excel(writer, sheet_name='Modelos', index=False)
        df_lineas.to_excel(writer, sheet_name='Financiacion', index=False)
    
    output.seek(0)
    return StreamingResponse(
        output,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=datos_byd.xlsx"}
    )

@app.post("/api/admin/importar")
async def importar_datos(file: UploadFile = File(...)):
    try:
        contents = await file.read()
        xls = pd.ExcelFile(io.BytesIO(contents))
        
        df_modelos = pd.read_excel(xls, sheet_name='Modelos')
        df_lineas = pd.read_excel(xls, sheet_name='Financiacion')

        # BORRAR TODO (Limpieza total para evitar duplicados)
        supabase.table("modelos").delete().neq("id", 0).execute()
        supabase.table("lineas_financiacion").delete().neq("id", 0).execute()

        # CARGAR MODELOS
        for _, row in df_modelos.iterrows():
            if pd.isna(row['nombre']): continue
            supabase.table("modelos").insert({
                "nombre": str(row['nombre']),
                "moneda": str(row['moneda']),
                "precio": float(row['precio']),
                "bonif": float(row['bonif'] or 0),
                "fyf": float(row['fyf'] or 0),
                "pat": float(row['pat'] or 0),
                "activo": bool(row['activo'])
            }).execute()

        # CARGAR LINEAS (Fila por fila, ya que ahora la tabla es plana)
        for _, row in df_lineas.iterrows():
            if pd.isna(row['nombre']): continue
            aplica_list = str(row['aplica_a']).split(",") if not pd.isna(row['aplica_a']) else []
            supabase.table("lineas_financiacion").insert({
                "nombre": str(row['nombre']),
                "tipo": str(row['tipo']),
                "uva": bool(row['uva']),
                "aplica_a": aplica_list,
                "plazo": int(row['plazo']),
                "tna": float(row['tna']),
                "quebranto": float(row['quebranto']),
                "tope": float(row['tope']) if not pd.isna(row['tope']) else None,
                "activo": bool(row['activo'])
            }).execute()

        return {"status": "ok", "message": "Datos importados correctamente"}
    except Exception as e:
        return {"error": f"Error al importar: {str(e)}"}

# ==========================================
# ASISTENTE IA
# ==========================================
class Mensaje(BaseModel):
    role: str
    content: str

class PedidoIA(BaseModel):
    prompt: str
    historial: Optional[List[Mensaje]] = []

@app.post("/api/ia")
async def procesar_ia(pedido: PedidoIA):
    try:
        system_prompt = """Sos un asistente de ventas de autos BYD en Argentina. Tu objetivo es extraer datos del texto para armar una cotización.

REGLAS DE ORO (OBLIGATORIAS):
1. Si el usuario menciona un monto de dinero para el anticipo pero NO especifica si es en pesos o en dólares, DEBÉS preguntarle antes de continuar. No asumas nada.
2. Si el usuario menciona un modelo pero NO especifica la versión (GL o GS) Y el modelo tiene ambas versiones (Dolphin Mini, Yuan Pro, Song Pro), DEBÉS preguntarle qué versión prefiere. No asumas.
3. Si el usuario dice "dólares", "USD", "verdes", "U$S", "lucas verdes" → el monto va en "anticipo_usd".
4. Si dice "pesos", "palos", "lucas", o solo el símbolo "$" sin aclarar dólares → va en "anticipo_pesos". "1 palo" = 1.000.000, "1 luca" = 1.000.
5. Si el usuario ya respondió la pregunta en el historial, NO vuelvas a preguntar; usá esa respuesta.
6. Si el usuario dice "mínimo anticipo", "sin anticipo", "nada de anticipo", "financia todo" o similar, significa que el anticipo es CERO. Devolvé "anticipo_pesos": 0 y "anticipo_usd": 0. En este caso, NO preguntes la moneda, porque el monto es 0.

Si tenés TODOS los datos, devolvé un JSON con estas claves exactas:
- "modelo": string (ej: "Dolphin Mini GS", "Song Pro GS", "Seal U GS", "Atto 2 GS", "Yuan Pro GL", "SHARK GS", "TI7 GS", "Seal 5")
- "anticipo_pesos": número entero en pesos (si no menciona o es mínimo, 0)
- "anticipo_usd": número entero en dólares (si no menciona o es mínimo, 0)
- "usado": número entero en pesos (si no menciona, 0)
- "financiar": boolean (true si pide financiar, false si no)
- "aplicar_bonif": boolean (true si pide aplicar el descuento máximo)

Si falta la moneda del anticipo (y el monto es mayor a 0) O la versión GL/GS, devolvé un JSON con UNA SOLA CLAVE:
- "pregunta": "Texto corto y claro de la pregunta (ej: ¿Los 20.000 son en pesos o en dólares?)"

IMPORTANTE: Devolvé estrictamente el objeto JSON, sin textos adicionales, sin markdown."""

        mensajes = [{"role": "system", "content": system_prompt}]
        for msg in pedido.historial:
            mensajes.append({"role": msg.role, "content": msg.content})
        mensajes.append({"role": "user", "content": pedido.prompt})

        response = client_ia.chat.completions.create(
            model="openai/gpt-oss-120b",
            messages=mensajes,
            response_format={"type": "json_object"},
            temperature=0.1,
        )

        texto = response.choices[0].message.content
        datos = json.loads(texto)

        if "pregunta" in datos and datos["pregunta"]:
            return {"pregunta": datos["pregunta"]}

        resultado = {
            "modelo": str(datos.get("modelo", "")),
            "anticipo_pesos": int(datos.get("anticipo_pesos", 0) or 0),
            "anticipo_usd": int(datos.get("anticipo_usd", 0) or 0),
            "usado": int(datos.get("usado", 0) or 0),
            "financiar": bool(datos.get("financiar", False)),
            "aplicar_bonif": bool(datos.get("aplicar_bonif", False)),
        }

        return {"respuesta": json.dumps(resultado)}
    except Exception as e:
        return {"error": str(e)}
