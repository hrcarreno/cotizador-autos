import subprocess
import sys
import importlib.util

if importlib.util.find_spec("python_multipart") is None:
    print("Instalando python-multipart...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "python-multipart"])

from fastapi import FastAPI, UploadFile, File, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from supabase import create_client, Client
from openai import OpenAI
import os
import json
import io
import csv
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
# ENDPOINTS DE USUARIO Y AUTENTICACIÓN
# ==========================================

@app.get("/api/usuarios/me")
async def get_current_user(authorization: str = Header(None)):
    if not authorization:
        raise HTTPException(status_code=401, detail="No autorizado")
    token = authorization.replace("Bearer ", "")
    
    try:
        # Validar el token con Supabase Auth
        user_response = supabase.auth.get_user(token)
        user_email = user_response.user.email
        
        # Buscar el perfil en la tabla perfiles
        perfil_res = supabase.table("perfiles").select("*").eq("email", user_email).execute()
        
        if not perfil_res.data:
            return {"email": user_email, "rol": "Usuario"} # Rol por defecto
            
        return perfil_res.data[0]
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Token inválido: {str(e)}")

# ==========================================
# ENDPOINTS PÚBLICOS
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
    res = supabase.table("lineas_financiacion").select("*").eq("activo", True).execute()
    return res.data

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
    modelos = supabase.table("modelos").select("*").execute().data
    lineas = supabase.table("lineas_financiacion").select("*").execute().data

    output = io.StringIO()
    
    output.write("--- MODELOS ---\n")
    if modelos:
        writer_m = csv.writer(output, lineterminator='\n')
        writer_m.writerow(["nombre", "moneda", "precio", "bonif", "fyf", "pat", "activo"])
        for m in modelos:
            writer_m.writerow([m["nombre"], m["moneda"], m["precio"], m["bonif"], m["fyf"], m["pat"], m["activo"]])
    
    output.write("\n--- LINEAS ---\n")
    if lineas:
        writer_l = csv.writer(output, lineterminator='\n')
        writer_l.writerow(["nombre", "tipo", "uva", "aplica_a", "plazo", "tna", "quebranto", "tope", "activo"])
        for l in lineas:
            aplica_str = ",".join(l["aplica_a"]) if isinstance(l["aplica_a"], list) else ""
            writer_l.writerow([l["nombre"], l["tipo"], l["uva"], aplica_str, l["plazo"], l["tna"], l["quebranto"], l["tope"], l["activo"]])

    output.seek(0)
    return StreamingResponse(
        io.BytesIO(output.getvalue().encode('utf-8-sig')),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=datos_byd.csv"}
    )

@app.post("/api/admin/importar")
async def importar_datos(file: UploadFile = File(...)):
    try:
        contents = await file.read()
        try:
            texto = contents.decode("utf-8-sig")
        except UnicodeDecodeError:
            texto = contents.decode("latin-1")
        
        partes = texto.split("--- LINEAS ---")
        parte_modelos = partes[0].replace("--- MODELOS ---", "").strip()
        parte_lineas = partes[1].strip() if len(partes) > 1 else ""

        supabase.table("modelos").delete().neq("id", 0).execute()
        supabase.table("lineas_financiacion").delete().neq("id", 0).execute()

        reader_m = csv.DictReader(io.StringIO(parte_modelos))
        for row in reader_m:
            if not row.get("nombre"): continue
            supabase.table("modelos").insert({
                "nombre": row["nombre"],
                "moneda": row["moneda"],
                "precio": float(row["precio"]),
                "bonif": float(row["bonif"] or 0),
                "fyf": float(row["fyf"] or 0),
                "pat": float(row["pat"] or 0),
                "activo": str(row["activo"]).lower() == 'true'
            }).execute()

        reader_l = csv.DictReader(io.StringIO(parte_lineas))
        for row in reader_l:
            if not row.get("nombre"): continue
            aplica_val = row.get("aplica_a", "")
            aplica_val = aplica_val.strip('"').strip("'")
            aplica_list = [x.strip() for x in aplica_val.split(",") if x.strip()]
            
            tope_val = row.get("tope")
            tope_final = float(tope_val) if tope_val and str(tope_val).strip().lower() not in ['none', 'null', ''] else None

            try:
                plazo_val = int(row["plazo"])
            except (ValueError, TypeError):
                plazo_val = 12

            supabase.table("lineas_financiacion").insert({
                "nombre": row["nombre"],
                "tipo": row["tipo"],
                "uva": str(row["uva"]).lower() == 'true',
                "aplica_a": aplica_list,
                "plazo": plazo_val,
                "tna": float(row["tna"]),
                "quebranto": float(row["quebranto"]),
                "tope": tope_final,
                "activo": str(row["activo"]).lower() == 'true'
            }).execute()

        return {"status": "ok", "message": "Datos importados correctamente"}
    except Exception as e:
        return {"error": f"Error al importar: {str(e)}"}

# ==========================================
# GUARDAR COTIZACIÓN EN CRM
# ==========================================

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
... (el resto del prompt de IA queda igual) ..."""

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
