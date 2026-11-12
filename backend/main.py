from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from supabase import create_client, Client
from openai import OpenAI
import os
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(title="Cotizador BYD API")

# Permitir que React (en localhost o Vercel) se conecte
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Conexiones
try:
    supabase: Client = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))
    client_ia = OpenAI(base_url="https://api.groq.com/openai/v1", api_key=os.getenv("GROQ_API_KEY"))
    print("Conexiones establecidas")
except Exception as e:
    print(f"Error de conexión: {e}")

@app.get("/")
def read_root():
    return {"status": "ok", "message": "API del Cotizador funcionando"}

class PedidoIA(BaseModel):
    prompt: str

@app.post("/api/ia")
async def procesar_ia(pedido: PedidoIA):
    try:
        # Aquí iría el prompt completo que teníamos en el HTML
        response = client_ia.chat.completions.create(
            model="openai/gpt-oss-120b",
            messages=[
                {"role": "system", "content": "Sos un asistente. Extraé modelo, anticipo, usado, prioridad en JSON. Solo devolvé el JSON."},
                {"role": "user", "content": pedido.prompt}
            ],
            response_format={ "type": "json_object" }
        )
        return {"respuesta": response.choices[0].message.content}
    except Exception as e:
        return {"error": str(e)}

# Ruta de prueba para los modelos
@app.get("/api/modelos")
def get_modelos():
    return [
        {"nombre": "Dolphin Mini EV GS", "precio": 37700000, "moneda": "ARS"},
        {"nombre": "Song Pro DM-I GS", "precio": 35616, "moneda": "USD"}
    ]
