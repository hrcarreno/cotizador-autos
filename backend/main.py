import { useState } from 'react';
import './App.css';

const MODELOS = [
  { nombre: "Dolphin Mini EV GL", moneda: "ARS", precio: 36200000, bonif: 2172000, fyf: 800000, pat: 2381960 },
  { nombre: "Dolphin Mini EV GS", moneda: "ARS", precio: 37700000, bonif: 2262000, fyf: 800000, pat: 2480660 },
  { nombre: "Yuan Pro EV GL", moneda: "USD", precio: 30990, bonif: 0, fyf: 500, pat: 2169 },
  { nombre: "Yuan Pro EV GS", moneda: "USD", precio: 31990, bonif: 0, fyf: 500, pat: 2239 },
  { nombre: "Atto 2 DM-I GS", moneda: "USD", precio: 32291, bonif: 1615, fyf: 500, pat: 2147 },
  { nombre: "Song Pro DM-I GL", moneda: "USD", precio: 33716, bonif: 1686, fyf: 500, pat: 2242 },
  { nombre: "Song Pro DM-I GS", moneda: "USD", precio: 35616, bonif: 1781, fyf: 500, pat: 2368 },
  { nombre: "Seal U DM-I GS", moneda: "USD", precio: 47990, bonif: 0, fyf: 800, pat: 3359 },
  { nombre: "SHARK DM-O GS", moneda: "USD", precio: 59990, bonif: 4799, fyf: 800, pat: 3863 },
  { nombre: "TI7 GS", moneda: "USD", precio: 65500, bonif: 0, fyf: 800, pat: 4585 },
  { nombre: "Seal 5", moneda: "USD", precio: 31990, bonif: 1600, fyf: 500, pat: 2127 }
];

const LINEAS = [
  { n: "Convenio BYD · UVA 0%", k: "conv", uva: true, aplica: ["Dolphin Mini", "Song Pro", "Yuan Pro", "Seal 5", "Atto 2"], r: [[12, 0, 6.56, 25000000], [18, 0, 9.64, 17000000]] },
  { n: "Convenio BYD · Fija 0%", k: "conv", uva: false, aplica: ["Dolphin Mini", "Song Pro", "Yuan Pro", "Seal 5", "Atto 2"], r: [[12, 0, 16.39, 10000000]] },
  { n: "Convenio BYD · Fija 9,90%", k: "conv", uva: false, aplica: ["Dolphin Mini", "Song Pro", "Yuan Pro", "Seal 5", "Atto 2"], r: [[12, 9.9, 10.93, 15000000]] },
  { n: "Convenio BYD · Fija 14,90%", k: "conv", uva: false, aplica: ["Dolphin Mini", "Song Pro", "Yuan Pro", "Seal 5", "Atto 2"], r: [[18, 14.9, 12.61, 13000000]] },
  { n: "Quebranto concesionario · Fija 0%", k: "queb", uva: false, ltv: [90, 100], r: [[12, 0, 15.8, null], [18, 0, 21.9, null], [24, 0, 27.5, null], [36, 0, 37, null], [48, 0, 44.8, null]] },
  { n: "Quebranto concesionario · UVA 0%", k: "queb", uva: true, ltv: [85], r: [[12, 0, 6.5, null], [18, 0, 9.3, null], [24, 0, 12, null], [36, 0, 17, null], [48, 0, 21.6, null]] },
  { n: "Quebranto concesionario · UVA 9,90%", k: "queb", uva: true, ltv: [85], r: [[12, 9.9, 1.4, null], [18, 9.9, 2, null], [24, 9.9, 2.6, null], [36, 9.9, 3.7, null], [48, 9.9, 4.8, null]] },
  { n: "Sin quebranto · UVA 12,50%", k: "sin", uva: true, ltv: [85], r: [[12, 12.5, 0, null], [18, 12.5, 0, null], [24, 12.5, 0, null], [36, 12.5, 0, null], [48, 12.5, 0, null]] },
  { n: "Sin quebranto · Fija 32,90%", k: "sin", uva: false, ltv: [90, 100], r: [[12, 32.9, 0, null], [18, 32.9, 0, null], [24, 32.9, 0, null], [36, 32.9, 0, null], [48, 32.9, 0, null], [60, 32.9, 0, null]] },
  { n: "Comisión · UVA 14,50%", k: "com", uva: true, ltv: [85], r: [[12, 14.5, 0, null], [18, 14.5, 0, null], [24, 14.5, 0, null], [36, 14.5, 0, null], [48, 14.5, 0, null]] },
  { n: "Comisión · Fija 34,90%", k: "com", uva: false, ltv: [90, 100], r: [[12, 34.9, 0, null], [18, 34.9, 0, null], [24, 34.9, 0, null], [36, 34.9, 0, null], [48, 34.9, 0, null], [60, 34.9, 0, null]] }
];

const f = (n) => "$ " + Math.round(n).toLocaleString("es-AR");
const u = (n) => "USD " + (Math.round(n * 100) / 100).toLocaleString("es-AR", { maximumFractionDigits: 2 });
const cod = (n) => {
  n = Math.round(n);
  return "FC" + Math.floor(n / 1000000) + "AG" + String(Math.floor((n % 1000000) / 1000)).padStart(3, "0") + "HC" + String(n % 1000).padStart(3, "0");
};

function frances(mo, tna, n) {
  const i = tna / 1200;
  const pura = i ? (mo * i) / (1 - Math.pow(1 + i, -n)) : mo / n;
  let d = mo, sum = 0, first = 0, last = 0;
  for (let k = 1; k <= n; k++) {
    const it = d * i;
    let c = pura + it * 0.21;
    if (k === n) { c = d + d * i * 0.21; }
    if (k === 1) first = c;
    last = c;
    sum += c;
    d -= pura - it;
    if (d < 0) d = 0;
  }
  return { first, last, sum };
}

function App() {
  const [modeloIdx, setModeloIdx] = useState(0);
  const [patenta, setPatenta] = useState("con");
  const [tc, setTc] = useState(1450);
  
  const [aplicarBonif, setAplicarBonif] = useState(false);
  const [bonifMonto, setBonifMonto] = useState(0);
  const [antPesos, setAntPesos] = useState(0);
  const [antUsd, setAntUsd] = useState(0);
  const [checkUsado, setCheckUsado] = useState(false);
  const [tasacion, setTasacion] = useState(0);
  const [monedaUsado, setMonedaUsado] = useState("ars");

  const [financiar, setFinanciar] = useState(false);
  const [lineaIdx, setLineaIdx] = useState(0);
  const [plazo, setPlazo] = useState(12);
  const [prioridad, setPrioridad] = useState("cuota");

  const [nombreCliente, setNombreCliente] = useState("");
  const [telefonoCliente, setTelefonoCliente] = useState("");
  const [iaInput, setIaInput] = useState("");
  const [iaOutput, setIaOutput] = useState("");
  const [iaHistorial, setIaHistorial] = useState([]);

  const dm = MODELOS[modeloIdx];
  const esUsd = dm.moneda === "USD";
  const nf = esUsd ? u : f;

  const bonifEfectiva = aplicarBonif ? (bonifMonto > 0 ? Math.min(bonifMonto, dm.precio) : dm.bonif) : 0;
  
  const precioBase = dm.precio - bonifEfectiva;
  const patMonto = patenta === "con" ? dm.pat : 0;
  const total = precioBase + dm.fyf + patMonto;
  
  const totalEnMoneda = total;
  const anticipoEnMoneda = esUsd ? (antUsd + (antPesos / (tc || 1))) : (antPesos + (antUsd * tc));
  const usadoEnMoneda = esUsd ? (monedaUsado === "usd" ? tasacion : tasacion / (tc || 1)) : (monedaUsado === "usd" ? tasacion * tc : tasacion);
  const dif = totalEnMoneda - anticipoEnMoneda - (checkUsado ? usadoEnMoneda : 0);
  const difEnPesos = esUsd ? dif * tc : dif;

  const lineasValidas = LINEAS.filter(l => !l.aplica || l.aplica.some(a => dm.nombre.includes(a)));
  
  let mejores = [];
  if (financiar && dif > 0) {
    const difArs = difEnPesos;
    const opciones = [];
    lineasValidas.forEach((l, i) => {
      l.r.forEach(r => {
        const tna = r[1];
        const quebranto = r[2] * 1.21;
        const gast = difArs * (quebranto / 100);
        const fr = frances(difArs, tna, r[0]);
        const tope = r[3] ? r[3] : Infinity;
        if (difArs <= tope) {
          opciones.push({ l, i, r, cuota: fr.first, gast, pon: anticipoEnMoneda + gast, costo: fr.sum - difArs + gast });
        }
      });
    });
    if (prioridad === "cuota") opciones.sort((a, b) => a.cuota - b.cuota);
    else if (prioridad === "inicial") opciones.sort((a, b) => a.pon - b.pon);
    else opciones.sort((a, b) => a.costo - b.costo);
    
    mejores = opciones.slice(0, 10);
  }

  const lineaSel = lineasValidas[lineaIdx] || lineasValidas[0];
  const plazoData = lineaSel.r.find(r => r[0] === plazo) || lineaSel.r[0];
  
  let resumenFin = null;
  if (financiar && dif > 0) {
    const difArs = difEnPesos;
    const tna = plazoData[1];
    const quebranto = plazoData[2] * 1.21;
    const gasto = difArs * (quebranto / 100);
    const fr = frances(difArs, tna, plazo);
    resumenFin = {
      linea: lineaSel.n,
      plazo: plazo,
      aFinanciar: difArs,
      gasto: gasto,
      cuota: fr.first,
      ultimaCuota: fr.last,
      totalCuotas: fr.sum,
      tope: plazoData[3] || null
    };
  }

  const handleIA = async () => {
    if (!iaInput.trim()) return;
    const msgUser = iaInput;
    setIaOutput("Conectando...");
    setIaHistorial(prev => [...prev, { role: "user", content: msgUser }]);

    try {
      const res = await fetch("https://cotizador-byd.onrender.com/api/ia", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ prompt: msgUser, historial: iaHistorial })
      });
      if (!res.ok) throw new Error(`Error ${res.status}`);
      const data = await res.json();
      
      if (data.error) { 
        setIaOutput("Error: " + data.error);
        setIaHistorial(prev => [...prev, { role: "assistant", content: "Error: " + data.error }]);
        return; 
      }

      if (data.pregunta) {
        setIaOutput(data.pregunta);
        setIaHistorial(prev => [...prev, { role: "assistant", content: data.pregunta }]);
        setIaInput("");
        return;
      }

      const datos = JSON.parse(data.respuesta);
      
      if (datos.modelo) {
        const busq = datos.modelo.toLowerCase().replace(/[^a-z0-9]/g, "");
        const idx = MODELOS.findIndex(m => {
          const nom = m.nombre.toLowerCase().replace(/[^a-z0-9]/g, "");
          return nom.includes(busq) || busq.includes(nom);
        });
        
        if (idx >= 0) {
          setModeloIdx(idx);
          if (datos.aplicar_bonif) {
            const nuevoModelo = MODELOS[idx];
            if (nuevoModelo.bonif > 0) {
              setAplicarBonif(true);
              setBonifMonto(nuevoModelo.bonif); 
            }
          }
        }
      }
      
      if (datos.anticipo_pesos) setAntPesos(Number(datos.anticipo_pesos));
      if (datos.anticipo_usd) setAntUsd(Number(datos.anticipo_usd));
      if (datos.usado) { setCheckUsado(true); setTasacion(Number(datos.usado)); }
      if (datos.financiar !== undefined) setFinanciar(Boolean(datos.financiar));
      
      setIaOutput("¡Datos cargados exitosamente!");
      setIaHistorial(prev => [...prev, { role: "assistant", content: "Datos cargados exitosamente." }]);
      setIaInput("");
    } catch (e) {
      setIaOutput("Fallo: " + e.message);
      setIaHistorial(prev => [...prev, { role: "assistant", content: "Fallo: " + e.message }]);
    }
  };

  const guardarEnCRM = () => {
    alert(`Guardando en CRM:\nCliente: ${nombreCliente}\nTeléfono: ${telefonoCliente}\nModelo: ${dm.nombre}\nDiferencia: ${nf(dif)}`);
  };

  const generarMensaje = () => {
    let msg = `Hola! Te paso la cotización de tu *BYD ${dm.nombre}*:\n\n`;
    msg += `*Precio de Lista:* ${nf(dm.precio)}\n`;
    if (bonifEfectiva > 0) msg += `*Bonificación aplicada:* - ${nf(bonifEfectiva)}\n`;
    msg += `*Fletes y Formularios:* ${nf(dm.fyf)}\n`;
    if (patenta === "con") msg += `*Patentamiento:* ${nf(patMonto)}\n`;
    msg += `*Total a Abonar:* ${nf(total)}\n\n`;
    
    if (antPesos > 0 || antUsd > 0) {
      msg += `*FORMA DE PAGO:*\n`;
      if (antPesos > 0) msg += `• Anticipo en Pesos: $ ${antPesos.toLocaleString("es-AR")}\n`;
      if (antUsd > 0) msg += `• Anticipo en Dólares: USD ${antUsd.toLocaleString("es-AR")}\n`;
    }
    if (checkUsado) {
      msg += `• Vehículo en parte de pago: $ ${tasacion.toLocaleString("es-AR")} (${monedaUsado})\n`;
    }
    msg += `*Diferencia a abonar:* ${nf(dif)}\n`;

    if (resumenFin) {
      msg += `\n*FINANCIACIÓN (Banco Santander):*\n`;
      msg += `• Línea: ${resumenFin.linea}\n`;
      msg += `• Plazo: ${resumenFin.plazo} meses\n`;
      msg += `• A financiar: ${f(resumenFin.aFinanciar)}\n`;
      msg += `• Cuota inicial: ${f(resumenFin.cuota)}\n`;
    }
    msg += `\n*Los valores están sujetos a la lista vigente y aprobación crediticia. No incluye seguro.*\n`;
    return msg;
  };

  const msgFinal = generarMensaje();

  const copiarMensaje = () => {
    navigator.clipboard.writeText(msgFinal);
    alert("Mensaje copiado al portapapeles");
  };

  const enviarWhatsApp = () => {
    const url = `https://wa.me/?text=${encodeURIComponent(msgFinal)}`;
    window.open(url, '_blank');
  };

  const descargarPDF = () => {
    window.print();
  };

  return (
    <div className="app-container">
      <header>
        <h1>Cotizador BYD 0 km</h1>
        <p className="sub">Lista de precios 2026 · Banco Santander</p>
      </header>

      <div className="asistente-card">
        <h2>Asistente IA</h2>
        <div className="historial-chat">
          {iaHistorial.map((h, i) => (
            <div key={i} className={`chat-msg ${h.role}`}>
              <b>{h.role === "user" ? "Vos:" : "Asistente:"}</b> {h.content}
            </div>
          ))}
        </div>
        <textarea 
          value={iaInput} 
          onChange={(e) => setIaInput(e.target.value)} 
          placeholder="Ej: Quiere una Song Pro, entrega 10 palos y financia el resto..."
        />
        <button onClick={handleIA}>Armar cotización</button>
        <button 
          onClick={() => { setIaInput(""); setIaOutput(""); setIaHistorial([]); }} 
          style={{ marginLeft: '10px', background: 'transparent', border: '1px solid var(--line)' }}
        >
          Nueva consulta
        </button>
        {iaOutput && !iaHistorial.length && <p className="ia-output">{iaOutput}</p>}
      </div>

      <div className="layout-grid">
        <div className="col">
          <div className="card">
            <h2>Vehículo</h2>
            <label>Modelo</label>
            <select value={modeloIdx} onChange={(e) => setModeloIdx(Number(e.target.value))}>
              {MODELOS.map((m, i) => <option key={i} value={i}>{m.nombre}</option>)}
            </select>

            {dm.bonif > 0 && (
              <div style={{ marginTop: '10px' }}>
                <label className="switch">
                  <input type="checkbox" checked={aplicarBonif} onChange={(e) => setAplicarBonif(e.target.checked)} />
                  <span>Aplicar bonificación</span>
                </label>
                {aplicarBonif && (
                  <>
                    <label>Monto bonif. ({dm.moneda})</label>
                    <input type="number" value={bonifMonto} onChange={(e) => setBonifMonto(Number(e.target.value))} />
                    {bonifEfectiva > 0 && (
                      <div className="codigo-disfrazado">
                        Código: {cod(bonifEfectiva)}
                      </div>
                    )}
                  </>
                )}
              </div>
            )}

            <label>Patentamiento</label>
            <select value={patenta} onChange={(e) => setPatenta(e.target.value)}>
              <option value="con">Concesionario</option>
              <option value="cli">Cliente</option>
            </select>
            
            <div className="resumen" style={{ marginTop: '15px' }}>
              <div className="row"><span>Precio Lista:</span> <span>{nf(dm.precio)}</span></div>
              {bonifEfectiva > 0 && <div className="row"><span>Bonificación:</span> <span>- {nf(bonifEfectiva)}</span></div>}
              <div className="row"><span>FyF:</span> <span>{nf(dm.fyf)}</span></div>
              {patenta === "con" && <div className="row"><span>Patentamiento:</span> <span>{nf(patMonto)}</span></div>}
              <div className="row total"><span>Total:</span> <span>{nf(total)}</span></div>
            </div>
          </div>

          <div className="card">
            <h2>Pago</h2>
            <label>Dólar Agencia ($)</label>
            <input type="number" value={tc} onChange={(e) => setTc(Number(e.target.value))} />
            
            <label>Anticipo en Pesos ($)</label>
            <input type="number" value={antPesos} onChange={(e) => setAntPesos(Number(e.target.value))} />
            {tc > 0 && <div className="conv">≈ USD {Math.round(antPesos / tc).toLocaleString("es-AR")}</div>}

            <label>Anticipo en Dólares (USD)</label>
            <input type="number" value={antUsd} onChange={(e) => setAntUsd(Number(e.target.value))} />
            {tc > 0 && <div className="conv">≈ $ {Math.round(antUsd * tc).toLocaleString("es-AR")}</div>}

            <label className="switch">
              <input type="checkbox" checked={checkUsado} onChange={(e) => setCheckUsado(e.target.checked)} />
              <span>Entrego vehículo en parte de pago</span>
            </label>
            {checkUsado && (
              <div className="two">
                <div>
                  <label>Tasación</label>
                  <input type="number" value={tasacion} onChange={(e) => setTasacion(Number(e.target.value))} />
                </div>
                <div>
                  <label>Moneda</label>
                  <select value={monedaUsado} onChange={(e) => setMonedaUsado(e.target.value)}>
                    <option value="ars">Pesos</option>
                    <option value="usd">Dólares</option>
                  </select>
                </div>
              </div>
            )}
          </div>
        </div>

        <div className="col">
          <div className="card big">
            <h2>Diferencia a abonar</h2>
            <div className="cuota">{nf(dif)}</div>
            {esUsd && <div className="conv" style={{ fontSize: '14px', marginTop: '4px' }}>≈ $ {Math.round(difEnPesos).toLocaleString("es-AR")}</div>}
            {!esUsd && tc > 0 && <div className="conv" style={{ fontSize: '14px', marginTop: '4px' }}>≈ USD {Math.round(dif / tc).toLocaleString("es-AR")}</div>}
          </div>

          <div className="card">
            <label className="switch">
              <input type="checkbox" checked={financiar} onChange={(e) => setFinanciar(e.target.checked)} />
              <span>Financiar la diferencia</span>
            </label>
            
            {financiar && (
              <>
                <label>Línea Santander</label>
                <select value={lineaIdx} onChange={(e) => setLineaIdx(Number(e.target.value))}>
                  {lineasValidas.map((l, i) => <option key={i} value={i}>{l.n}</option>)}
                </select>
                
                <label>Plazo</label>
                <div className="chips">
                  {lineaSel.r.map(r => (
                    <button key={r[0]} className={plazo === r[0] ? "chip active" : "chip"} onClick={() => setPlazo(r[0])}>{r[0]}</button>
                  ))}
                </div>
                
                {resumenFin && (
                  <div className="detalle-financiacion">
                    <h2 style={{ marginTop: '15px' }}>Detalle de la Opción</h2>
                    <div className="row"><span>Línea:</span> <span>{resumenFin.linea}</span></div>
                    <div className="row"><span>Plazo:</span> <span>{resumenFin.plazo} meses</span></div>
                    <div className="row"><span>A financiar:</span> <span>{f(resumenFin.aFinanciar)}</span></div>
                    <div className="row mut"><span>Gasto de otorgamiento:</span> <span>{f(resumenFin.gasto)}</span></div>
                    <div className="row"><span>Cuota inicial:</span> <span className="cuota-detalle">{f(resumenFin.cuota)}</span></div>
                    <div className="row mut"><span>Última cuota:</span> <span>{f(resumenFin.ultimaCuota)}</span></div>
                    <div className="row mut"><span>Total de cuotas:</span> <span>{f(resumenFin.totalCuotas)}</span></div>
                  </div>
                )}

                <h2 style={{ marginTop: '20px' }}>Mejores opciones</h2>
                <label>Qué prioriza el cliente</label>
                <select value={prioridad} onChange={(e) => setPrioridad(e.target.value)}>
                  <option value="cuota">Cuota más baja</option>
                  <option value="inicial">Poner menos al inicio</option>
                  <option value="costo">Menor costo total</option>
                </select>
                
                <div className="lista-opciones">
                  {mejores.map((opt, idx) => (
                    <div 
                      key={idx} 
                      className={`opcion-card ${opt.l.n === lineaSel.n && opt.r[0] === plazo ? 'selected' : ''}`} 
                      onClick={() => { setLineaIdx(opt.i); setPlazo(opt.r[0]); }}
                    >
                      <div className="opcion-info">
                        <b>{opt.l.n}</b>
                        <span>{opt.r[0]} cuotas</span>
                      </div>
                      <div className="opcion-cuota">
                        {f(opt.cuota)}
                      </div>
                    </div>
                  ))}
                </div>
              </>
            )}
          </div>

          <div className="card">
            <h2>Acciones</h2>
            <div className="acciones">
              <button className="btn-sec" onClick={copiarMensaje}>Copiar Mensaje</button>
              <button className="btn-sec" onClick={enviarWhatsApp}>Enviar WhatsApp</button>
              <button className="btn-sec" onClick={descargarPDF}>Descargar PDF</button>
            </div>
          </div>

          <button className="btn-guardar" onClick={guardarEnCRM}>Guardar Cotización en CRM</button>
        </div>
      </div>
    </div>
  );
}

export default App;
