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

try:
    supabase: Client = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))
    client_ia = OpenAI(base_url="https://api.groq.com/openai/v1", api_key=os.getenv("GROQ_API_KEY"))
except Exception as e:
    print(f"Error de conexión: {e}")

@app.get("/")
def read_root():
    return {"status": "ok", "message": "API del Cotizador funcionando"}

class Mensaje(BaseModel):
    role: str
    content: str

class PedidoIA(BaseModel):
    prompt: str
    historial: Optional[List[Mensaje]] = []

@app.post("/api/ia")
async def procesar_ia(pedido: PedidoIA):
    try:
        system_prompt = """Sos un asistente de ventas de autos en Argentina. Tu objetivo es extraer datos del texto para armar una cotización.
        
        REGLA DE ORO: Si el usuario menciona un monto de dinero para el anticipo pero NO especifica si es en pesos o en dólares, DEBÉS preguntarle antes de continuar. No asumas nada.
        
        Si tenés todos los datos, devolvé un JSON con estas claves exactas:
        - "modelo": string (ej: "Dolphin Mini GS", "Song Pro", "Seal U", "Atto 2")
        - "anticipo_pesos": número entero en pesos (si dice "20 palos", devolver 20000000)
        - "anticipo_usd": número entero en dólares (si dice "20.000 dólares", devolver 20000)
        - "usado": número entero en pesos (si no menciona, devolver 0)
        - "financiar": boolean (true si pide financiar, false si no)
        - "aplicar_bonif": boolean (true si pide aplicar descuento)
        
        Si falta la moneda del anticipo, devolvé un JSON con una sola clave:
        - "pregunta": "Texto de la pregunta para el usuario (ej: ¿Los 20.000 son en pesos o en dólares?)"
        
        IMPORTANTE: Devuelve estrictamente el objeto JSON, sin textos adicionales."""
        
        mensajes = [{"role": "system", "content": system_prompt}]
        
        for msg in pedido.historial:
            mensajes.append({"role": msg.role, "content": msg.content})
            
        mensajes.append({"role": "user", "content": pedido.prompt})

        response = client_ia.chat.completions.create(
            model="openai/gpt-oss-120b",
            messages=mensajes,
            response_format={ "type": "json_object" }
        )
        
        texto = response.choices[0].message.content
        datos = json.loads(texto)
        
        if "pregunta" in datos:
            return {"pregunta": datos["pregunta"]}
        
        resultado = {
            "modelo": str(datos.get("modelo", "")),
            "anticipo_pesos": int(datos.get("anticipo_pesos", 0)),
            "anticipo_usd": int(datos.get("anticipo_usd", 0)),
            "usado": int(datos.get("usado", 0)),
            "financiar": bool(datos.get("financiar", False)),
            "aplicar_bonif": bool(datos.get("aplicar_bonif", False))
        }
        
        return {"respuesta": json.dumps(resultado)}
    except Exception as e:
        return {"error": str(e)}
