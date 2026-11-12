import os
import json
import re
from flask import Flask, render_template, request, jsonify
from openai import OpenAI
from dotenv import load_dotenv

# Cargamos las variables de entorno (.env o las de Render)
load_dotenv()

app = Flask(__name__)

# Configuramos Groq (la IA que ya veníamos usando)
try:
    client = OpenAI(
        base_url="https://api.groq.com/openai/v1",
        api_key=os.getenv("GROQ_API_KEY", "")
    )
    ia_activa = True
except Exception:
    ia_activa = False

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/ia', methods=['POST'])
def api_ia():
    if not ia_activa:
        return jsonify({"error": "Falta configurar la API Key de Groq en las variables de entorno."}), 500

    data = request.json
    prompt = data.get("prompt", "")
    estado_actual = data.get("estado", "")

    system_prompt = """Sos un asistente de ventas de autos. Extraé datos y devolvé SOLO un JSON válido.
    Claves permitidas: "modelo" (string), "anticipo" (entero), "usado" (entero), "financiar" (bool), "prioridad" (string).
    Si no se menciona algo, devolver null. No agregues texto extra, solo el JSON."""
    
    try:
        response = client.chat.completions.create(
            model="openai/gpt-oss-120b",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Estado actual del cotizador:\n{estado_actual}\n\nPedido del cliente: {prompt}"}
            ],
            temperature=0.0,
            response_format={ "type": "json_object" }
        )
        
        texto_respuesta = response.choices[0].message.content
        return jsonify({"respuesta": texto_respuesta})
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, port=int(os.getenv("PORT", 5000)))
