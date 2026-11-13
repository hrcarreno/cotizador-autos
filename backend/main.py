from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from supabase import create_client, Client
from openai import OpenAI
import os
import json
from dotenv import load_dotenv

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

class PedidoIA(BaseModel):
    prompt: str

@app.post("/api/ia")
async def procesar_ia(pedido: PedidoIA):
    try:
        system_prompt = """Sos un asistente de ventas de autos en Argentina. Extraé datos del texto y devolvé SOLO un JSON válido.
        
        Claves exactas:
        - "modelo": string (ej: "Dolphin Mini GS", "Song Pro", "Seal U", "Atto 2")
        - "anticipo_pesos": número entero en pesos. 
          REGLAS: Si el usuario dice "20 palos", devolver 20000000. Si dice "5 lucas", devolver 5000. Si usa el símbolo "$" SIN mencionar "dólares", asumí que son PESOS.
        - "anticipo_usd": número entero en dólares. 
          REGLAS: Si el usuario dice "20.000 dólares", "20.000 USD", "20k verdes" o "U$S 20.000", devolver 20000.
        - "usado": número entero en pesos (si no menciona, devolver 0). Si menciona que el usado es en dólares, convertí a pesos usando el valor del dólar que mencione (o 1000 por defecto).
        - "financiar": boolean (true si pide financiar, false si no)
        - "aplicar_bonif": boolean (true si pide aplicar el descuento/bonificación máxima)
        
        IMPORTANTE: 
        1. Si el usuario menciona "dólares", "USD" o "verdes", el monto va en "anticipo_usd".
        2. Si el usuario menciona "pesos", "palos", "lucas" o solo el símbolo "$", el monto va en "anticipo_pesos".
        3. Devuelve estrictamente el objeto JSON, sin textos adicionales."""        
        response = client_ia.chat.completions.create(
            model="openai/gpt-oss-120b",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": pedido.prompt}
            ],
            response_format={ "type": "json_object" }
        )
        
        texto = response.choices[0].message.content
        datos = json.loads(texto)
        
        # Normalizamos los datos por si la IA devuelve strings
        resultado = {
            "modelo": str(datos.get("modelo", "")),
            "anticipo": int(datos.get("anticipo", 0)),
            "usado": int(datos.get("usado", 0)),
            "financiar": bool(datos.get("financiar", False)),
            "aplicar_bonif": bool(datos.get("aplicar_bonif", False))
        }
        
        return {"respuesta": json.dumps(resultado)}
    except Exception as e:
        return {"error": str(e)}
