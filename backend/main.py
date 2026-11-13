from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
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
    client_ia = OpenAI(
        base_url="https://api.groq.com/openai/v1",
        api_key=os.getenv("GROQ_API_KEY")
    )
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
        system_prompt = """Sos un asistente de ventas de autos BYD en Argentina. Tu objetivo es extraer datos del texto para armar una cotización.

REGLAS DE ORO (OBLIGATORIAS):
1. Si el usuario menciona un monto de dinero para el anticipo pero NO especifica si es en pesos o en dólares, DEBÉS preguntarle antes de continuar. No asumas nada.
2. Si el usuario menciona un modelo pero NO especifica la versión (GL o GS) Y el modelo tiene ambas versiones (Dolphin Mini, Yuan Pro, Song Pro), DEBÉS preguntarle qué versión prefiere. No asumas.
3. Si el usuario dice "dólares", "USD", "verdes", "U$S", "lucas verdes" → el monto va en "anticipo_usd".
4. Si dice "pesos", "palos", "lucas", o solo el símbolo "$" sin aclarar dólares → va en "anticipo_pesos". "1 palo" = 1.000.000, "1 luca" = 1.000.
5. Si el usuario ya respondió la pregunta en el historial, NO vuelvas a preguntar; usá esa respuesta.

Si tenés TODOS los datos, devolvé un JSON con estas claves exactas:
- "modelo": string (ej: "Dolphin Mini GS", "Song Pro GS", "Seal U GS", "Atto 2 GS", "Yuan Pro GL", "SHARK GS", "TI7 GS", "Seal 5")
- "anticipo_pesos": número entero en pesos (si no menciona, 0)
- "anticipo_usd": número entero en dólares (si no menciona, 0)
- "usado": número entero en pesos (si no menciona, 0)
- "financiar": boolean (true si pide financiar, false si no)
- "aplicar_bonif": boolean (true si pide aplicar el descuento máximo)

Si falta la moneda del anticipo O la versión GL/GS, devolvé un JSON con UNA SOLA CLAVE:
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
