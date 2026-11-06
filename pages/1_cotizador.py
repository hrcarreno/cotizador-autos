def procesar_pedido_ia(prompt):
    if not ia_activa: return None
    
    system_prompt = """Sos un asistente de ventas de autos BYD. Extraé datos del texto y devolvé SOLO un JSON válido.
    Claves exactas a usar:
    - "modelo": string (ej: "Dolphin Mini", "Song Pro", "Seal U", etc.)
    - "anticipo": número entero (si dice "13 millones", devolver 13000000. Si dice "10 palos", devolver 10000000)
    - "usado": número entero o null
    - "prioridad": string ("cuota", "inicial" o "costo")
    IMPORTANTE: Devuelve estrictamente el objeto JSON, sin textos adicionales."""
    
    try:
        response = client.chat.completions.create(
            model="openai/gpt-oss-120b", # El modelo actual de Groq
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ],
            temperature=0.0
        )
        
        texto_respuesta = response.choices[0].message.content
        # Limpiamos por si Groq pone ```json ... ```
        json_limpio = re.sub(r'```(?:json)?\n?(.*?)\n?```', r'\1', texto_respuesta, flags=re.DOTALL)
        json_limpio = json_limpio[json_limpio.find('{'):json_limpio.rfind('}')+1]
        
        datos = json.loads(json_limpio)
        
        # --- TRADUCTOR DE SEGURIDAD ---
        # Si la IA usa otros nombres de claves, los corregimos acá
        datos_limpios = {}
        if "modelo" in datos: datos_limpios["modelo"] = datos["modelo"]
        elif "auto" in datos: datos_limpios["modelo"] = datos["auto"]
        
        if "anticipo" in datos: datos_limpios["anticipo"] = datos["anticipo"]
        elif "entrega" in datos: datos_limpios["anticipo"] = datos["entrega"]
        elif "pesos" in datos: datos_limpios["anticipo"] = datos["pesos"]
        
        if "usado" in datos: datos_limpios["usado"] = datos["usado"]
        
        if "prioridad" in datos: datos_limpios["prioridad"] = datos["prioridad"]
        
        return datos_limpios
        
    except Exception as e:
        st.error(f"Detalle del error: {e}\n\nRespuesta de Groq: {texto_respuesta if 'texto_respuesta' in locals() else 'No hubo respuesta'}")
        return None
