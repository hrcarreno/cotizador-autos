from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from supabase import create_client, Client
from openai import OpenAI
import os
import json
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

# --- CONEXIONES ---
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

# --- ENDPOINTS PÚBLICOS (Para el cotizador) ---

@app.get("/api/config")
async def get_config():
    res = supabase.table("configuracion_global").select("*").execute()
    # Devuelve un diccionario simple: {"dolar_agencia": 1450}
    return {item["clave"]: item["valor"] for item in res.data}

@app.get("/api/modelos")
async def get_modelos():
    res = supabase.table("modelos").select("*").eq("activo", True).order("id").execute()
    return res.data

@app.get("/api/lineas")
async def get_lineas():
    res = supabase.table("lineas_financiacion").select("*").eq("activo", True).execute()
    # Convertimos el JSONB de "plazos" a una lista de Python real
    for linea in res.data:
        if isinstance(linea["plazos"], str):
            linea["plazos"] = json.loads(linea["plazos"])
    return res.data

# --- ENDPOINTS DE ADMINISTRACIÓN ---
# (Nota: En un futuro cercano, acá validaremos el token del usuario Admin)

class UpdateConfig(BaseModel):
    clave: str
    valor: float

@app.put("/api/admin/config")
async def update_config(data: UpdateConfig):
    supabase.table("configuracion_global").upsert({"clave": data.clave, "valor": data.valor}).execute()
    return {"status": "ok"}

class UpdateLinea(BaseModel):
    plazos: list
    activo: bool

@app.put("/api/admin/lineas/{linea_id}")
async def update_linea(linea_id: int, data: UpdateLinea):
    supabase.table("lineas_financiacion").update({
        "plazos": data.plazos,
        "activo": data.activo
    }).eq("id", linea_id).execute()
    return {"status": "ok"}

# --- ENDPOINT DE LA IA (Se mantiene igual) ---
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
