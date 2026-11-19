"""Interfaz Streamlit de la mesa de ayuda TI."""

import json
import math
from html import escape

import streamlit as st

from core import (
    actualizar_factores,
    actualizar_ia,
    cambiar_estado,
    crear_ticket,
    iniciar,
    listar,
    obtener,
    riesgo,
    ver_historial,
)

st.set_page_config(
    page_title="Mesa de ayuda TI",
    page_icon="🛠️",
    layout="wide",
    initial_sidebar_state="collapsed",
)
iniciar()

# Diseño
PRIORIDADES = ["Crítica", "Alta", "Media", "Baja"]
COLOR_PRIORIDAD = {
    "Crítica": ("#FF5D6C", "rgba(255,93,108,.14)"),
    "Alta": ("#FF9F43", "rgba(255,159,67,.14)"),
    "Media": ("#F7CB4D", "rgba(247,203,77,.14)"),
    "Baja": ("#3FD99B", "rgba(63,217,155,.14)"),
}
# Pesos máximos de core.riesgo
FACTORES = [
    ("severidad", "Gravedad reportada", 25),
    ("usuarios", "Usuarios afectados", 20),
    ("bloqueos", "Procesos bloqueados", 25),
    ("sin_workaround", "Sin solución temporal", 15),
    ("antiguedad", "Antigüedad del ticket", 8),
    ("dependencias", "Dependencias", 7),
]
FLUJO = ["Abierta", "En atención", "Resuelta propuesta", "Cerrada"]
ESTADO_EN_FLUJO = {"En espera del usuario": 1, "Escalada": 1}
TRANSICIONES = {
    "Abierta": ["En atención", "Escalada"],
    "En atención": ["En espera del usuario", "Resuelta propuesta", "Escalada"],
    "En espera del usuario": ["En atención", "Escalada"],
    "Resuelta propuesta": ["Cerrada", "En atención"],
    "Escalada": ["En atención"],
    "Cerrada": ["En atención"],
}
ETIQUETAS_IA = {
    "factores_riesgo": "Factores de riesgo",
    "nivel_riesgo_cualitativo": "Nivel de riesgo (apreciación)",
    "justificacion": "Justificación",
    "datos_faltantes": "Datos faltantes",
    "impactos_observados": "Impactos observados",
    "dependencias": "Dependencias registradas",
    "efectos_potenciales": "Efectos potenciales (sin confirmar)",
    "urgencia_operativa": "Urgencia operativa",
}
AGENTES = [
    ("Analista de riesgo", "Evalúa los factores con la evidencia del ticket."),
    ("Impacto y dependencias", "Separa impactos observados de efectos posibles."),
    ("Priorizador y auditor", "Integra ambos análisis y deja la decisión trazable."),
]

ESTILOS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Figtree:wght@400;500;600;700;800&display=swap');
:root{
  --bg:#090F1A; --surface:#0F1828; --surface-2:#142034; --line:#1F2D45; --line-2:#2C3E5C;
  --ink:#E8EEF8; --ink-2:#B4C0D4; --muted:#7F90AB; --track:#1B2A42;
  --cyan:#4CC9F0; --cyan-2:#7ADCF7; --on-cyan:#04202B; --radius:12px;
}
html, body, .stApp, .stApp p, .stApp label, .stApp li, .stApp input, .stApp textarea, .stApp button,
.stApp select, .stApp h1, .stApp h2, .stApp h3, .stApp h4, [data-baseweb="select"], [data-baseweb="tab"]{
  font-family:'Figtree','Segoe UI',system-ui,sans-serif;
}
.stApp{
  background:radial-gradient(1100px 480px at 12% -8%, rgba(76,201,240,.11), transparent 62%),
             radial-gradient(900px 420px at 95% 0%, rgba(110,90,255,.07), transparent 60%), var(--bg);
  color:var(--ink); font-variant-numeric:tabular-nums;
}
[data-testid="stHeader"]{ background:transparent; height:0; }
[data-testid="stDecoration"], #MainMenu, footer{ display:none; }
[data-testid="stMainBlockContainer"]{ max-width:1400px; padding:0 2rem 3rem; }
.stApp h1,.stApp h2,.stApp h3,.stApp h4,.stApp h5{ color:var(--ink); letter-spacing:-.01em; }
.stApp p, .stApp li{ color:var(--ink-2); }
.stApp ::-webkit-scrollbar{ width:8px; height:8px; }
.stApp ::-webkit-scrollbar-thumb{ background:var(--line-2); border-radius:8px; }
.stApp ::-webkit-scrollbar-track{ background:transparent; }

/* Barra superior */
.appbar{ display:flex; align-items:center; justify-content:space-between; gap:1rem; padding:1rem 0 .95rem; }
.brand{ display:flex; align-items:center; gap:.85rem; }
.brand-mark{ width:36px; height:36px; border-radius:10px; display:grid; place-items:center;
  background:linear-gradient(145deg,#1B3A5C,#0F2038); border:1px solid var(--line-2);
  box-shadow:0 0 18px rgba(76,201,240,.28); }
.brand-name{ font-weight:750; font-size:1.08rem; color:var(--ink); line-height:1.1; }
.brand-sub{ font-size:.8rem; color:var(--muted); margin-top:2px; }
.appbar-meta{ display:flex; gap:.5rem; flex-wrap:wrap; justify-content:flex-end; }
.meta-chip{ font-size:.78rem; color:var(--ink-2); background:var(--surface); border:1px solid var(--line);
  border-radius:999px; padding:.3rem .75rem; }
.live{ display:inline-block; width:7px; height:7px; border-radius:50%; background:#3FD99B; margin-right:.45rem;
  box-shadow:0 0 0 0 rgba(63,217,155,.6); animation:ping 2.4s ease-out infinite; }
@keyframes ping{ 70%,100%{ box-shadow:0 0 0 7px rgba(63,217,155,0); } }

/* Navegación */
[data-baseweb="tab-list"]{ gap:.25rem; border-bottom:1px solid var(--line); margin-bottom:1.1rem; }
button[data-baseweb="tab"]{ background:transparent; border:0; padding:.7rem .95rem; margin-bottom:-1px; color:var(--muted);
  font-weight:600; font-size:.95rem; border-bottom:2px solid transparent; border-radius:0; }
button[data-baseweb="tab"]:hover{ color:var(--ink); background:transparent; }
button[data-baseweb="tab"][aria-selected="true"]{ color:var(--cyan-2); border-bottom-color:var(--cyan); }
[data-baseweb="tab-highlight"], [data-baseweb="tab-border"]{ display:none; }

/* Franja de indicadores */
.stats{ display:grid; grid-template-columns:repeat(4,1fr); background:var(--surface); border:1px solid var(--line);
  border-radius:var(--radius); margin-bottom:.9rem; }
.stat{ padding:.9rem 1.2rem; border-right:1px solid var(--line); }
.stat:last-child{ border-right:0; }
.stat-label{ font-size:.8rem; color:var(--muted); font-weight:500; }
.stat-value{ font-size:1.8rem; font-weight:760; color:var(--ink); line-height:1.15; margin-top:.1rem; }
.stat-note{ font-size:.78rem; color:var(--muted); margin-top:.1rem; }
.mix{ display:flex; gap:2px; height:7px; border-radius:99px; overflow:hidden; margin:.55rem 0 .4rem; }
.mix span{ display:block; height:100%; }
.mix-legend{ display:flex; gap:.9rem; flex-wrap:wrap; font-size:.78rem; color:var(--ink-2); }
.mix-legend b{ color:var(--ink); }
.dot{ display:inline-block; width:8px; height:8px; border-radius:50%; margin-right:.3rem; }

/* Paneles */
.panel{ background:var(--surface); border:1px solid var(--line); border-radius:var(--radius); padding:1.15rem 1.3rem; margin-bottom:.9rem; }
.panel-title{ font-size:.98rem; font-weight:700; color:var(--ink); margin:0 0 .15rem; }
.panel-note{ font-size:.84rem; color:var(--muted); margin:0 0 .85rem; line-height:1.5; }
.queue-title{ font-size:.98rem; font-weight:700; color:var(--ink); margin:.1rem 0 .1rem; }
.queue-note{ font-size:.82rem; color:var(--muted); margin-bottom:.5rem; }

/* Cabecera del ticket con medidor */
.hero{ display:grid; grid-template-columns:1fr 230px; gap:1.4rem; align-items:center; }
.t-top{ display:flex; align-items:center; gap:.55rem; flex-wrap:wrap; margin-bottom:.45rem; }
.t-id{ font-weight:700; font-size:.84rem; color:var(--ink); background:var(--surface-2); border:1px solid var(--line-2);
  border-radius:6px; padding:.1rem .5rem; }
.t-date{ font-size:.8rem; color:var(--muted); }
.t-title{ font-size:1.55rem; font-weight:760; line-height:1.22; margin:.1rem 0 .6rem; color:var(--ink); letter-spacing:-.015em; }
.t-desc{ font-size:.95rem; line-height:1.65; color:var(--ink-2); max-width:68ch; margin:0; }
.badge{ display:inline-flex; align-items:center; gap:.35rem; font-size:.78rem; font-weight:650; border-radius:999px; padding:.2rem .7rem; }
.badge-state{ background:var(--surface-2); color:var(--ink-2); border:1px solid var(--line-2); }
.gauge-wrap{ text-align:center; }
.gauge{ display:block; margin:0 auto; overflow:visible; }
.gauge-val{ animation:gauge-in 1.2s cubic-bezier(.2,.7,.2,1) both; }
@keyframes gauge-in{ from{ stroke-dasharray:0 440; } }
.gauge-cap{ font-size:.8rem; color:var(--muted); margin-top:-.3rem; }
.facts{ display:grid; grid-template-columns:repeat(5,1fr); margin-top:1.1rem; border-top:1px solid var(--line); }
.fact{ padding:.8rem .9rem .1rem 0; }
.fact-label{ font-size:.78rem; color:var(--muted); }
.fact-value{ font-size:1.2rem; font-weight:700; color:var(--ink); }

/* Desglose del riesgo */
.factor{ display:grid; grid-template-columns:170px 1fr 56px; align-items:center; gap:.8rem; padding:.32rem 0; font-size:.88rem; }
.factor-name{ color:var(--ink-2); }
.factor-bar{ height:8px; border-radius:99px; background:var(--track); overflow:hidden; }
.factor-bar span{ display:block; height:100%; border-radius:99px; animation:grow .9s cubic-bezier(.2,.7,.2,1) both; }
@keyframes grow{ from{ width:0; } }
.factor-val{ text-align:right; color:var(--ink); font-weight:650; }
.factor-val small{ color:var(--muted); font-weight:500; }
.rule-note{ margin-top:.7rem; font-size:.8rem; color:var(--muted); }

/* Mapa de riesgo */
.map svg{ width:100%; height:auto; display:block; overflow:visible; }
.map text{ font-family:'Figtree','Segoe UI',sans-serif; }

/* Agentes */
.pipe{ display:grid; grid-template-columns:1fr 30px 1fr 30px 1fr; align-items:stretch; margin:.2rem 0 .3rem; }
.agent{ border:1px solid var(--line); border-radius:var(--radius); padding:.85rem 1rem; background:var(--bg); }
.agent.done{ background:var(--surface-2); border-color:rgba(76,201,240,.45); }
.agent.run{ border-color:var(--cyan); animation:glow 1.6s ease-in-out infinite; }
@keyframes glow{ 0%,100%{ box-shadow:0 0 0 0 rgba(76,201,240,.0); } 50%{ box-shadow:0 0 0 4px rgba(76,201,240,.16); } }
.agent-n{ display:inline-grid; place-items:center; width:22px; height:22px; border-radius:50%; font-size:.76rem; font-weight:700;
  background:var(--track); color:var(--muted); margin-right:.5rem; vertical-align:middle; }
.agent.done .agent-n{ background:var(--cyan); color:var(--on-cyan); }
.agent.run .agent-n{ background:transparent; border:2px solid var(--cyan); color:var(--cyan); }
.agent-role{ font-weight:700; font-size:.92rem; color:var(--ink); vertical-align:middle; }
.agent-what{ font-size:.8rem; color:var(--muted); margin:.4rem 0 .5rem; line-height:1.45; }
.agent-state{ font-size:.78rem; font-weight:650; color:var(--muted); }
.agent.done .agent-state{ color:var(--cyan-2); }
.agent.run .agent-state{ color:var(--cyan-2); }
.link{ display:grid; place-items:center; color:var(--line-2); }
.link.flow{ color:var(--cyan); }
.link.flow svg{ animation:nudge 1.1s ease-in-out infinite; }
@keyframes nudge{ 0%,100%{ transform:translateX(-2px); opacity:.5; } 50%{ transform:translateX(2px); opacity:1; } }
.run-note{ font-size:.84rem; color:var(--cyan-2); margin-top:.7rem; }
.ia-block{ font-size:.92rem; color:var(--ink-2); line-height:1.6; padding-bottom:.4rem; }
.ia-block h5{ margin:1rem 0 .15rem !important; padding:0 !important; line-height:1.3; font-size:.8rem; color:var(--muted); font-weight:650; }
.ia-block h5:first-child{ margin-top:0; }
.ia-block ul{ margin:0 0 0 1.1rem; padding:0; }
.ia-block p, .ia-block li{ margin:0 0 .1rem !important; color:var(--ink-2); }
.disclaimer{ font-size:.8rem; color:var(--muted); margin-top:.7rem; }

/* Línea de estado */
.steps{ display:flex; align-items:center; margin:.35rem 0 .2rem; }
.step{ display:flex; align-items:center; gap:.5rem; font-size:.86rem; color:var(--muted); font-weight:550; white-space:nowrap; }
.step-dot{ width:24px; height:24px; border-radius:50%; display:grid; place-items:center; font-size:.72rem;
  border:2px solid var(--line-2); background:var(--bg); color:var(--muted); }
.step.done .step-dot{ background:var(--cyan); border-color:var(--cyan); color:var(--on-cyan); }
.step.now .step-dot{ border-color:var(--cyan); color:var(--cyan-2); box-shadow:0 0 0 4px rgba(76,201,240,.18); }
.step.now{ color:var(--ink); font-weight:700; }
.step.done{ color:var(--ink-2); }
.step-line{ flex:1; height:2px; background:var(--line); margin:0 .7rem; min-width:20px; }
.step-line.done{ background:var(--cyan); }
.side-note{ margin-top:.6rem; font-size:.84rem; color:var(--ink-2); }

/* Historial */
.tl{ position:relative; margin:.2rem 0 0 .35rem; padding-left:1.25rem; border-left:2px solid var(--line); }
.tl-item{ position:relative; padding:0 0 1.05rem; }
.tl-item::before{ content:""; position:absolute; left:calc(-1.25rem - 6px); top:.3rem; width:10px; height:10px; border-radius:50%;
  background:var(--bg); border:2px solid var(--cyan); }
.tl-item.ia::before{ border-color:#A78BFA; }
.tl-item.sys::before{ border-color:var(--line-2); }
.tl-meta{ font-size:.78rem; color:var(--muted); }
.tl-meta b{ color:var(--ink-2); font-weight:650; margin-right:.4rem; }
.tl-text{ font-size:.9rem; color:var(--ink); line-height:1.5; margin-top:.1rem; }

/* Cola de tickets */
[class*="st-key-tk_"]{ margin-bottom:-.35rem; width:100%; }
[class*="st-key-tk_"] [data-testid="stButton"]{ width:100%; }
[class*="st-key-tk_"] button{
  width:100%; justify-content:flex-start; text-align:left; background:var(--surface); border:1px solid var(--line);
  border-left-width:4px; border-radius:9px; padding:.6rem .85rem; min-height:0; color:var(--ink); box-shadow:none;
  transition:background .15s, border-color .15s;
}
[class*="st-key-tk_"] button > div, [class*="st-key-tk_"] button [data-testid="stMarkdownContainer"]{ width:100%; justify-content:flex-start; text-align:left; }
[class*="st-key-tk_"] button:hover{ background:var(--surface-2); border-color:var(--line-2); }
[class*="st-key-tk_"] button p{ margin:0; font-size:.86rem; line-height:1.4; text-align:left; color:var(--ink-2); }
[class*="st-key-tk_"] button p strong{ color:var(--ink); font-weight:700; }

/* Controles */
button[kind^="primary"]{
  background:var(--cyan); border:1px solid var(--cyan); color:var(--on-cyan); font-weight:700; border-radius:9px; padding:.5rem 1.15rem; }
button[kind^="primary"], button[kind^="primary"] *{ color:var(--on-cyan) !important; }
button[kind^="primary"]:hover{
  background:var(--cyan-2); border-color:var(--cyan-2); }
button[kind^="secondary"]{
  background:var(--surface-2); border:1px solid var(--line-2); color:var(--ink); border-radius:9px; font-weight:600; }
button:focus-visible, input:focus-visible, textarea:focus-visible{ outline:3px solid rgba(76,201,240,.55) !important; outline-offset:1px; }
[data-testid="stTextInput"] input, [data-testid="stNumberInput"] input, [data-testid="stTextArea"] textarea,
[data-baseweb="select"] > div, [data-baseweb="input"], [data-baseweb="textarea"]{
  background:var(--surface-2) !important; color:var(--ink) !important; border-color:var(--line-2) !important; border-radius:9px; }
[data-testid="stNumberInput"] button{ background:var(--surface-2); color:var(--ink-2); border-color:var(--line-2); }
[data-baseweb="popover"] [data-baseweb="menu"], [data-baseweb="popover"] ul{ background:var(--surface-2) !important; }
[data-baseweb="popover"] li{ color:var(--ink) !important; }
[data-testid="stWidgetLabel"] p, label p{ font-size:.86rem; font-weight:600; color:var(--ink-2) !important; }
[data-testid="stCaptionContainer"], .stApp small{ color:var(--muted); }
[data-testid="stForm"]{ background:var(--surface); border:1px solid var(--line); border-radius:var(--radius); padding:1.1rem 1.3rem; }
[data-testid="stExpander"]{ background:var(--surface); border:1px solid var(--line); border-radius:var(--radius); }
[data-testid="stExpander"] summary{ color:var(--ink); }
[data-testid="stExpander"] summary p{ font-weight:650; font-size:.92rem; color:var(--ink) !important; }
[data-testid="stExpanderDetails"] h1{ font-size:1.05rem; font-weight:750; margin:.2rem 0 .6rem; padding:0; }
[data-testid="stExpanderDetails"] h2, [data-testid="stExpanderDetails"] h3, [data-testid="stExpanderDetails"] h4{
  font-size:.82rem; font-weight:650; color:var(--muted); margin:.9rem 0 .1rem; padding:0; letter-spacing:0; }
[data-testid="stExpanderDetails"] p{ font-size:.92rem; color:var(--ink-2); line-height:1.6; }
[data-testid="stAlert"]{ border-radius:var(--radius); }
.form-sec{ font-size:.98rem; font-weight:700; margin:1.1rem 0 .1rem; color:var(--ink); }
.form-sec:first-child{ margin-top:0; }
.form-help{ font-size:.82rem; color:var(--muted); margin-bottom:.4rem; }
.empty{ text-align:center; padding:2.6rem 1rem; color:var(--muted); background:var(--surface); border:1px dashed var(--line-2); border-radius:var(--radius); }
.empty b{ display:block; color:var(--ink); font-size:1.02rem; margin-bottom:.25rem; }

@media (max-width:900px){
  [data-testid="stMainBlockContainer"]{ padding:0 1rem 2rem; }
  .stats{ grid-template-columns:repeat(2,1fr); } .stat:nth-child(2){ border-right:0; }
  .stat:nth-child(-n+2){ border-bottom:1px solid var(--line); }
  .hero{ grid-template-columns:1fr; } .facts{ grid-template-columns:repeat(2,1fr); }
  .pipe{ grid-template-columns:1fr; gap:.5rem; } .link{ display:none; }
  .factor{ grid-template-columns:120px 1fr 52px; } .appbar-meta{ display:none; }
}
@media (prefers-reduced-motion:reduce){ *{ transition:none !important; animation:none !important; } }
</style>
"""
st.markdown(ESTILOS, unsafe_allow_html=True)


# Utilidades de presentación
def fecha_corta(iso):
    return str(iso)[:16].replace("T", " ")


def badge_prioridad(prioridad):
    fuerte, suave = COLOR_PRIORIDAD.get(prioridad, ("#B4C0D4", "rgba(180,192,212,.14)"))
    return (
        f'<span class="badge" style="color:{fuerte};background:{suave};border:1px solid {fuerte}55">'
        f'<span class="dot" style="background:{fuerte};margin:0"></span>{escape(str(prioridad))}</span>'
    )


def medidor_circular(puntos, prioridad, tam=210):
    """Arco de 270° con marcas en 25, 50 y 75."""
    fuerte = COLOR_PRIORIDAD[prioridad][0]
    p = max(0, min(100, int(puntos)))
    r, c = 70, 2 * math.pi * 70
    arco = c * 0.75
    marcas = ""
    for umbral in (25, 50, 75):
        ang = math.radians(135 + 270 * umbral / 100)
        x1, y1 = 90 + (r - 11) * math.cos(ang), 90 + (r - 11) * math.sin(ang)
        x2, y2 = 90 + (r + 11) * math.cos(ang), 90 + (r + 11) * math.sin(ang)
        marcas += f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" stroke="#0F1828" stroke-width="3"/>'
    valor = (
        f'<circle class="gauge-val" cx="90" cy="90" r="{r}" fill="none" stroke="{fuerte}" stroke-width="12" '
        f'stroke-linecap="round" stroke-dasharray="{arco * p / 100:.1f} {c:.1f}" '
        f'style="filter:drop-shadow(0 0 7px {fuerte}99)"/>' if p > 0 else ""
    )
    return (
        f'<svg class="gauge" viewBox="0 0 180 180" width="{tam}" height="{tam}" role="img" '
        f'aria-label="Riesgo {p} de 100, prioridad {escape(prioridad)}">'
        f'<g transform="rotate(135 90 90)"><circle cx="90" cy="90" r="{r}" fill="none" stroke="#1B2A42" stroke-width="12" '
        f'stroke-linecap="round" stroke-dasharray="{arco:.1f} {c:.1f}"/>{valor}{marcas}</g>'
        f'<text x="90" y="92" text-anchor="middle" font-size="42" font-weight="800" fill="#E8EEF8">{p}</text>'
        f'<text x="90" y="112" text-anchor="middle" font-size="11" fill="#7F90AB">de 100</text>'
        f'<text x="90" y="150" text-anchor="middle" font-size="13" font-weight="700" fill="{fuerte}">{escape(prioridad)}</text></svg>'
    )


def desglose(factores, color):
    filas = []
    for i, (clave, nombre, maximo) in enumerate(FACTORES):
        valor = int(factores.get(clave, 0))
        pct = round(valor / maximo * 100)
        filas.append(
            f'<div class="factor"><span class="factor-name">{nombre}</span>'
            f'<span class="factor-bar"><span style="width:{pct}%;background:{color};animation-delay:{i * 60}ms"></span></span>'
            f'<span class="factor-val">{valor}<small> / {maximo}</small></span></div>'
        )
    return "".join(filas)


def mapa_de_riesgo(tickets, seleccionado):
    """Horas sin resolver (x) contra puntuación (y)."""
    if not tickets:
        return ""
    w, h, izq, der, arriba, abajo = 330, 190, 30, 8, 8, 24
    xmax = max(48, math.ceil(max(t["antiguedad_horas"] for t in tickets) / 12) * 12)
    px = lambda horas: izq + (w - izq - der) * min(horas, xmax) / xmax
    py = lambda pts: arriba + (h - arriba - abajo) * (1 - pts / 100)
    partes = []
    for desde, hasta, prio in ((0, 25, "Baja"), (25, 50, "Media"), (50, 75, "Alta"), (75, 100, "Crítica")):
        partes.append(
            f'<rect x="{izq}" y="{py(hasta):.1f}" width="{w - izq - der}" height="{py(desde) - py(hasta):.1f}" '
            f'fill="{COLOR_PRIORIDAD[prio][0]}" opacity=".07"/>'
        )
    for nivel in (0, 25, 50, 75, 100):
        partes.append(f'<line x1="{izq}" x2="{w - der}" y1="{py(nivel):.1f}" y2="{py(nivel):.1f}" stroke="#1F2D45" stroke-width="1"/>')
        partes.append(f'<text x="{izq - 6}" y="{py(nivel) + 3:.1f}" text-anchor="end" font-size="9" fill="#7F90AB">{nivel}</text>')
    for horas in (0, xmax // 2, xmax):
        partes.append(f'<text x="{px(horas):.1f}" y="{h - 8}" text-anchor="middle" font-size="9" fill="#7F90AB">{horas} h</text>')
    for t in sorted(tickets, key=lambda t: t["id"] == seleccionado):
        fuerte = COLOR_PRIORIDAD[t["prioridad"]][0]
        cx, cy = px(t["antiguedad_horas"]), py(t["puntuacion"])
        radio = 4 + min(8, math.sqrt(max(t["usuarios_afectados"], 1)) / 2.2)
        titulo = escape(f'TI-{t["id"]:04d} · {t["asunto"]} · {t["puntuacion"]}/100 · {t["usuarios_afectados"]} usuarios')
        if t["id"] == seleccionado:
            partes.append(f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="{radio + 5:.1f}" fill="none" stroke="#E8EEF8" stroke-width="1.5"/>')
        partes.append(
            f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="{radio:.1f}" fill="{fuerte}" fill-opacity=".85" stroke="#0F1828" stroke-width="1.5">'
            f'<title>{titulo}</title></circle>'
        )
        if t["id"] == seleccionado:
            ancla = "end" if cx > w * 0.7 else "start"
            dx = -(radio + 8) if ancla == "end" else radio + 8
            partes.append(f'<text x="{cx + dx:.1f}" y="{cy + 3.5:.1f}" text-anchor="{ancla}" font-size="10" font-weight="700" fill="#E8EEF8">TI-{t["id"]:04d}</text>')
    return f'<div class="map"><svg viewBox="0 0 {w} {h}" role="img" aria-label="Mapa de riesgo de los tickets pendientes">{"".join(partes)}</svg></div>'


def render_ia(contenido):
    """HTML legible de la salida JSON; None si no es JSON."""
    try:
        datos = json.loads(contenido)
    except (ValueError, TypeError):
        return None
    if not isinstance(datos, dict):
        return None
    partes = []
    for clave, valor in datos.items():
        if clave == "ticket_id":
            continue
        etiqueta = escape(ETIQUETAS_IA.get(clave, clave.replace("_", " ").capitalize()))
        if isinstance(valor, list):
            cuerpo = (
                "<ul>" + "".join(f"<li>{escape(str(v))}</li>" for v in valor) + "</ul>"
                if valor else "<p>Ninguno</p>"
            )
        else:
            cuerpo = f"<p>{escape(str(valor))}</p>"
        partes.append(f"<h5>{etiqueta}</h5>{cuerpo}")
    return '<div class="ia-block">' + "".join(partes) + "</div>"


def panel_agentes(hecho, ejecutando=False):
    flecha = ('<svg width="18" height="18" viewBox="0 0 18 18" fill="none"><path d="M4 9h10m-4-4 4 4-4 4" stroke="currentColor" '
              'stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/></svg>')
    check = ('<svg width="12" height="12" viewBox="0 0 12 12" fill="none"><path d="m2.5 6.2 2.3 2.3 4.7-5" stroke="currentColor" '
             'stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/></svg>')
    piezas = []
    for i, (rol, que) in enumerate(AGENTES):
        clase = "run" if ejecutando else "done" if hecho[i] else ""
        estado = "Analizando…" if ejecutando else "Análisis listo" if hecho[i] else "Pendiente de ejecutar"
        marca = check if (hecho[i] and not ejecutando) else str(i + 1)
        piezas.append(
            f'<div class="agent {clase}"><div><span class="agent-n">{marca}</span><span class="agent-role">{rol}</span></div>'
            f'<div class="agent-what">{que}</div><div class="agent-state">{estado}</div></div>'
        )
        if i < 2:
            piezas.append(f'<div class="link {"flow" if ejecutando else ""}">{flecha}</div>')
    nota = ('<div class="run-note">Los agentes trabajan en orden con el modelo local. Puede tardar unos minutos; '
            'no cierres esta página.</div>') if ejecutando else ""
    return (
        '<div class="panel" style="margin-bottom:.5rem"><div class="panel-title">Análisis de los agentes</div>'
        '<div class="panel-note">Tres agentes trabajan en orden y cada uno usa el resultado del anterior. '
        'Se ejecutan solo cuando tú lo pides.</div>'
        f'<div class="pipe">{"".join(piezas)}</div>{nota}</div>'
    )


def linea_de_estado(estado):
    actual = ESTADO_EN_FLUJO.get(estado, FLUJO.index(estado) if estado in FLUJO else 0)
    piezas = []
    for i, nombre in enumerate(FLUJO):
        clase = "done" if i < actual else "now" if i == actual else ""
        marca = "✓" if i < actual else str(i + 1)
        if i == actual and estado in ESTADO_EN_FLUJO:
            nombre = estado
        piezas.append(f'<div class="step {clase}"><span class="step-dot">{marca}</span>{escape(nombre)}</div>')
        if i < len(FLUJO) - 1:
            piezas.append(f'<div class="step-line {"done" if i < actual else ""}"></div>')
    nota = ""
    if estado == "Escalada":
        nota = '<div class="side-note">El ticket está escalado; vuelve a «En atención» cuando se retome.</div>'
    elif estado == "En espera del usuario":
        nota = '<div class="side-note">Se espera una respuesta del usuario para continuar.</div>'
    elif estado == "Cerrada":
        nota = '<div class="side-note">Ticket cerrado con confirmación del usuario.</div>'
    return f'<div class="steps">{"".join(piezas)}</div>{nota}'


def linea_de_tiempo(eventos):
    if not eventos:
        return '<div class="empty"><b>Sin movimientos</b>Aún no hay eventos registrados.</div>'
    items = []
    for e in reversed(eventos):
        actor = str(e["actor"])
        clase = "sys" if actor == "Sistema" else "ia" if actor == "CrewAI" else ""
        items.append(
            f'<div class="tl-item {clase}"><div class="tl-meta"><b>{escape(actor)}</b>{escape(fecha_corta(e["fecha"]))} UTC</div>'
            f'<div class="tl-text">{escape(str(e["evento"]))}</div></div>'
        )
    return f'<div class="tl">{"".join(items)}</div>'


# Estado
BORRADOR = {
    "nt_solicitante": "", "nt_categoria": "Incidencia", "nt_asunto": "", "nt_desc": "",
    "nt_sev": "Media", "nt_usuarios": 1, "nt_bloqueos": 0, "nt_workaround": False,
    "nt_horas": 1, "nt_dep": 0,
}
for _k, _v in BORRADOR.items():
    st.session_state.setdefault(_k, _v)


def seleccionar(pk):
    st.session_state["sel"] = pk


def sincronizar_seguimiento():
    st.session_state["sel"] = st.session_state["sel_seg"]


def crear_desde_formulario():
    s = st.session_state
    try:
        pk = crear_ticket({
            "solicitante": s["nt_solicitante"], "categoria": s["nt_categoria"],
            "asunto": s["nt_asunto"], "descripcion": s["nt_desc"], "severidad": s["nt_sev"],
            "usuarios_afectados": int(s["nt_usuarios"]), "procesos_bloqueados": int(s["nt_bloqueos"]),
            "workaround": bool(s["nt_workaround"]), "antiguedad_horas": int(s["nt_horas"]),
            "dependencias": int(s["nt_dep"]),
        })
    except Exception as exc:
        s["flash"] = ("error", str(exc))
        return
    for clave, valor in BORRADOR.items():
        s[clave] = valor
    s["sel"] = pk
    s["flash"] = ("ok", f"Ticket TI-{pk:04d} creado. Ya puedes analizarlo en «Análisis multiagente».")


registros = listar()
ids_validos = [t["id"] for t in registros]
if registros and st.session_state.get("sel") not in ids_validos:
    st.session_state["sel"] = ids_validos[0]

# Encabezado
st.markdown(
    '<div class="appbar"><div class="brand">'
    '<div class="brand-mark"><svg width="18" height="18" viewBox="0 0 18 18" fill="none">'
    '<rect x="2" y="3" width="14" height="2.6" rx="1.3" fill="#7ADCF7"/>'
    '<rect x="2" y="7.7" width="10" height="2.6" rx="1.3" fill="#7ADCF7" opacity=".75"/>'
    '<rect x="2" y="12.4" width="6" height="2.6" rx="1.3" fill="#7ADCF7" opacity=".5"/></svg></div>'
    '<div><div class="brand-name">Mesa de ayuda TI</div>'
    '<div class="brand-sub">Priorización de incidencias con agentes de IA</div></div></div>'
    '<div class="appbar-meta"><span class="meta-chip"><span class="live"></span>Modelo local · llama3.2</span>'
    '<span class="meta-chip">Prototipo académico</span></div></div>',
    unsafe_allow_html=True,
)

pendientes = [t for t in registros if t["estado"] != "Cerrada"]
abiertas = sum(t["estado"] == "Abierta" for t in registros)
urgentes = sum(t["prioridad"] in ("Crítica", "Alta") for t in pendientes)
con_ia = sum(bool(t["seguimiento_ia"]) for t in registros)
conteo = {p: sum(t["prioridad"] == p for t in pendientes) for p in PRIORIDADES}
if pendientes:
    mezcla = "".join(
        f'<span style="width:{conteo[p] / len(pendientes) * 100:.1f}%;background:{COLOR_PRIORIDAD[p][0]}"></span>'
        for p in PRIORIDADES if conteo[p]
    )
    leyenda = "".join(
        f'<span><span class="dot" style="background:{COLOR_PRIORIDAD[p][0]}"></span>{p} <b>{conteo[p]}</b></span>'
        for p in PRIORIDADES
    )
    bloque_mezcla = f'<div class="mix">{mezcla}</div><div class="mix-legend">{leyenda}</div>'
else:
    bloque_mezcla = '<div class="stat-note">Sin tickets pendientes</div>'
st.markdown(
    '<div class="stats">'
    f'<div class="stat"><div class="stat-label">Pendientes de cierre</div><div class="stat-value">{len(pendientes)}</div>{bloque_mezcla}</div>'
    f'<div class="stat"><div class="stat-label">Crítica o alta prioridad</div><div class="stat-value">{urgentes}</div>'
    '<div class="stat-note">Entre los tickets pendientes</div></div>'
    f'<div class="stat"><div class="stat-label">Sin atender</div><div class="stat-value">{abiertas}</div>'
    '<div class="stat-note">Tickets en estado Abierta</div></div>'
    f'<div class="stat"><div class="stat-label">Con análisis de agentes</div><div class="stat-value">{con_ia}'
    f'<span style="font-size:.95rem;color:#7F90AB;font-weight:600"> de {len(registros)}</span></div>'
    '<div class="stat-note">Informe de priorización generado</div></div>'
    '</div>',
    unsafe_allow_html=True,
)

tab_nuevo, tab_bandeja, tab_seguimiento = st.tabs(["Registro de tickets", "Análisis multiagente", "Seguimiento y cierre"])

# Análisis multiagente
with tab_bandeja:
    if not registros:
        st.markdown(
            '<div class="empty"><b>Aún no hay incidencias</b>'
            'Crea el primer ticket en la pestaña «Registro de tickets» para empezar a priorizar.</div>',
            unsafe_allow_html=True,
        )
    else:
        col_cola, col_detalle = st.columns([4, 9], gap="large")

        with col_cola:
            if pendientes:
                st.markdown(
                    '<div class="panel"><div class="panel-title">Mapa de riesgo</div>'
                    '<div class="panel-note">Cada punto es un ticket pendiente: más arriba, más riesgo; más a la derecha, más horas sin resolver. '
                    'El tamaño indica usuarios afectados.</div>'
                    f'{mapa_de_riesgo(pendientes, st.session_state["sel"])}</div>',
                    unsafe_allow_html=True,
                )
            st.markdown('<div class="queue-title">Cola de atención</div>'
                        '<div class="queue-note">Ordenada por prioridad y puntuación de riesgo.</div>',
                        unsafe_allow_html=True)
            texto = st.text_input("Buscar", placeholder="Buscar por asunto, solicitante o número",
                                  label_visibility="collapsed", key="busqueda")
            filtro = st.segmented_control("Prioridad", ["Todas"] + PRIORIDADES, default="Todas",
                                          label_visibility="collapsed", key="filtro_prioridad")
            ocultar = st.toggle("Ocultar tickets cerrados", value=False, key="ocultar_cerrados")

            visibles = []
            for t in registros:
                if filtro not in (None, "Todas") and t["prioridad"] != filtro:
                    continue
                if ocultar and t["estado"] == "Cerrada":
                    continue
                if texto.strip():
                    pajar = f'ti-{t["id"]:04d} {t["asunto"]} {t["solicitante"]}'.lower()
                    if texto.strip().lower() not in pajar:
                        continue
                visibles.append(t)

            # Borde por prioridad y ticket activo
            css_cola = []
            for t in visibles:
                fuerte = COLOR_PRIORIDAD[t["prioridad"]][0]
                regla = f"border-left-color:{fuerte} !important;"
                if t["id"] == st.session_state["sel"]:
                    regla += "background:rgba(76,201,240,.10) !important;border-color:rgba(76,201,240,.55) !important;"
                css_cola.append(f".st-key-tk_{t['id']} button{{{regla}}}")
            if css_cola:
                st.markdown(f"<style>{''.join(css_cola)}</style>", unsafe_allow_html=True)

            with st.container(height=440, border=False):
                if not visibles:
                    st.markdown('<div class="empty"><b>Sin resultados</b>Prueba con otra búsqueda o filtro.</div>',
                                unsafe_allow_html=True)
                for t in visibles:
                    etiqueta = (
                        f'**TI-{t["id"]:04d}** · {t["prioridad"]} · {t["puntuacion"]}/100  \n'
                        f'{t["asunto"]}  \n:gray[{t["estado"]}]'
                    )
                    st.button(etiqueta, key=f'tk_{t["id"]}', on_click=seleccionar, args=(t["id"],))

        with col_detalle:
            t = obtener(st.session_state["sel"])
            pk = t["id"]
            factores = json.loads(t["factores_json"])
            fuerte = COLOR_PRIORIDAD[t["prioridad"]][0]
            sw = "Sí" if t["workaround"] else "No"
            st.markdown(
                f'<div class="panel" style="background:radial-gradient(620px 240px at 100% 0%, {fuerte}26, transparent 70%), var(--surface)">'
                '<div class="hero"><div>'
                f'<div class="t-top"><span class="t-id">TI-{pk:04d}</span>{badge_prioridad(t["prioridad"])}'
                f'<span class="badge badge-state">{escape(t["estado"])}</span></div>'
                f'<div class="t-date">{escape(t["categoria"])} · reportó {escape(t["solicitante"])} · {escape(fecha_corta(t["creado"]))} UTC</div>'
                f'<div class="t-title" style="margin-top:.5rem">{escape(t["asunto"])}</div>'
                f'<p class="t-desc">{escape(t["descripcion"])}</p></div>'
                f'<div class="gauge-wrap">{medidor_circular(t["puntuacion"], t["prioridad"])}'
                '<div class="gauge-cap">Riesgo calculado con reglas fijas</div></div></div>'
                '<div class="facts">'
                f'<div class="fact"><div class="fact-label">Usuarios afectados</div><div class="fact-value">{t["usuarios_afectados"]}</div></div>'
                f'<div class="fact"><div class="fact-label">Procesos bloqueados</div><div class="fact-value">{t["procesos_bloqueados"]}</div></div>'
                f'<div class="fact"><div class="fact-label">Horas sin resolver</div><div class="fact-value">{t["antiguedad_horas"]}</div></div>'
                f'<div class="fact"><div class="fact-label">Dependencias</div><div class="fact-value">{t["dependencias"]}</div></div>'
                f'<div class="fact"><div class="fact-label">Solución temporal</div><div class="fact-value">{sw}</div></div>'
                '</div></div>',
                unsafe_allow_html=True,
            )

            st.markdown(
                '<div class="panel"><div class="panel-title">De dónde sale la puntuación</div>'
                '<div class="panel-note">Peso de cada factor sobre el máximo que puede aportar. La IA no interviene en este cálculo.</div>'
                f'{desglose(factores, fuerte)}</div>',
                unsafe_allow_html=True,
            )

            hecho = [bool(t["evaluacion_ia"]), bool(t["propuesta_soporte"]), bool(t["seguimiento_ia"])]
            ranura = st.empty()
            ranura.markdown(panel_agentes(hecho), unsafe_allow_html=True)

            ya_analizado = all(hecho)
            if st.button("Volver a ejecutar el análisis" if ya_analizado else "Ejecutar análisis con los 3 agentes",
                         type="secondary" if ya_analizado else "primary", key=f"run_{pk}"):
                ranura.markdown(panel_agentes(hecho, ejecutando=True), unsafe_allow_html=True)
                try:
                    from agents import ejecutar_agentes
                    outputs = ejecutar_agentes(t)
                    actualizar_ia(pk, outputs["evaluacion"], outputs["soporte"], outputs["seguimiento"])
                    st.rerun()
                except Exception as exc:
                    ranura.markdown(panel_agentes(hecho), unsafe_allow_html=True)
                    st.error(f"No se pudo completar el análisis: {exc}")
                    st.caption("Comprueba que Ollama esté abierto y que el modelo llama3.2:latest esté descargado.")

            for titulo, campo, abierto in [
                ("Agente 1 · Análisis de riesgo", "evaluacion_ia", False),
                ("Agente 2 · Impacto y dependencias", "propuesta_soporte", False),
                ("Agente 3 · Informe de priorización y auditoría", "seguimiento_ia", True),
            ]:
                if t[campo]:
                    with st.expander(titulo, expanded=abierto):
                        if campo == "seguimiento_ia":
                            st.markdown(t[campo])
                        else:
                            bloque = render_ia(t[campo])
                            if bloque:
                                st.markdown(bloque, unsafe_allow_html=True)
                            else:
                                st.markdown(t[campo])
            st.markdown(
                '<div class="disclaimer">Las respuestas de la IA son orientativas y pueden contener errores. '
                'La puntuación y la prioridad oficiales las calcula Python; los agentes no las modifican.</div>',
                unsafe_allow_html=True,
            )

# Registro de tickets
with tab_nuevo:
    aviso = st.session_state.pop("flash", None)
    if aviso:
        (st.success if aviso[0] == "ok" else st.error)(aviso[1])

    c_form, c_prev = st.columns([7, 4], gap="large")
    with c_form:
        st.markdown('<div class="form-sec">Quién reporta</div>', unsafe_allow_html=True)
        a, b = st.columns(2)
        a.text_input("Nombre de la persona *", key="nt_solicitante", placeholder="Ej.: Ana Torres")
        b.selectbox("Tipo de solicitud", ["Incidencia", "Duda", "Solicitud de soporte"], key="nt_categoria")

        st.markdown('<div class="form-sec">Qué sucede</div>', unsafe_allow_html=True)
        st.text_input("Asunto *", key="nt_asunto", placeholder="Ej.: No hay conexión a la VPN en la sucursal Norte")
        st.text_area("Descripción *", key="nt_desc", height=130,
                     placeholder="Cuenta qué pasó, desde cuándo y qué intentaste. Entre más claro, mejor el análisis.")

        st.markdown('<div class="form-sec">Alcance e impacto</div>'
                    '<div class="form-help">Estos datos alimentan el cálculo de riesgo; mira la vista previa a la derecha.</div>',
                    unsafe_allow_html=True)
        c1, c2, c3 = st.columns(3)
        c1.selectbox("Gravedad reportada", ["Baja", "Media", "Alta", "Crítica"], key="nt_sev")
        c2.number_input("Usuarios afectados (estimado)", min_value=0, step=1, key="nt_usuarios")
        c3.number_input("Procesos bloqueados", min_value=0, step=1, key="nt_bloqueos")
        c4, c5, c6 = st.columns(3)
        c4.number_input("Horas desde que empezó", min_value=0, step=1, key="nt_horas")
        c5.number_input("Tickets o actividades dependientes", min_value=0, step=1, key="nt_dep")
        c6.write("")
        c6.checkbox("Existe una solución temporal", key="nt_workaround")
        st.write("")
        st.button("Crear ticket", type="primary", on_click=crear_desde_formulario)

    with c_prev:
        s = st.session_state
        try:
            vista = riesgo({
                "severidad": s["nt_sev"], "usuarios_afectados": int(s["nt_usuarios"]),
                "procesos_bloqueados": int(s["nt_bloqueos"]), "workaround": bool(s["nt_workaround"]),
                "antiguedad_horas": int(s["nt_horas"]), "dependencias": int(s["nt_dep"]),
            })
            col = COLOR_PRIORIDAD[vista["prioridad"]][0]
            st.markdown(
                f'<div class="panel" style="background:radial-gradient(420px 200px at 100% 0%, {col}26, transparent 70%), var(--surface)">'
                '<div class="panel-title">Vista previa de prioridad</div>'
                '<div class="panel-note">Se actualiza al cambiar los datos del formulario.</div>'
                f'<div class="gauge-wrap">{medidor_circular(vista["puntuacion"], vista["prioridad"], 190)}</div>'
                f'<div style="height:.6rem"></div>{desglose(vista["factores"], col)}'
                '<div class="rule-note">Cálculo con reglas fijas; las ponderaciones son ilustrativas, no un SLA real.</div></div>',
                unsafe_allow_html=True,
            )
        except Exception as exc:
            st.warning(f"No se pudo calcular la vista previa: {exc}")

# Seguimiento
with tab_seguimiento:
    if not registros:
        st.markdown('<div class="empty"><b>Nada que seguir todavía</b>Cuando existan tickets podrás cambiar su estado aquí.</div>',
                    unsafe_allow_html=True)
    else:
        st.session_state["sel_seg"] = st.session_state["sel"]
        st.selectbox(
            "Ticket", ids_validos, key="sel_seg", on_change=sincronizar_seguimiento,
            format_func=lambda v: f'TI-{v:04d} · {next(x["asunto"] for x in registros if x["id"] == v)}',
        )
        tid = st.session_state["sel"]
        t = obtener(tid)

        st.markdown(
            '<div class="panel"><div class="t-top">'
            f'<span class="t-id">TI-{tid:04d}</span>{badge_prioridad(t["prioridad"])}'
            f'<span class="t-date">Riesgo {t["puntuacion"]}/100 · actualizado {escape(fecha_corta(t["actualizado"]))} UTC</span></div>'
            f'<div class="t-title" style="font-size:1.2rem;margin-bottom:.9rem">{escape(t["asunto"])}</div>'
            f'{linea_de_estado(t["estado"])}</div>',
            unsafe_allow_html=True,
        )

        col_a, col_b = st.columns([5, 6], gap="large")
        with col_a:
            st.markdown('<div class="panel-title">Registrar avance</div>'
                        '<div class="panel-note">Cada cambio queda guardado con fecha y responsable.</div>',
                        unsafe_allow_html=True)
            with st.form("estado"):
                nuevo = st.selectbox("Cambiar estado a", TRANSICIONES[t["estado"]])
                actor = st.radio("Quién confirma el cambio", ["Responsable", "Usuario"], horizontal=True)
                comentario = st.text_area("Comentario o resultado de la prueba *",
                                          placeholder="Ej.: El usuario confirmó que ya puede iniciar sesión")
                guardar = st.form_submit_button("Registrar seguimiento", type="primary")
            if guardar:
                try:
                    cambiar_estado(tid, nuevo, actor, comentario)
                    st.rerun()
                except Exception as exc:
                    st.error(str(exc))
            st.caption("El cierre solo se acepta cuando lo confirma el usuario.")

            with st.expander("Actualizar factores y recalcular la prioridad"):
                st.caption("Registra información nueva del mismo ticket. El análisis de los agentes se invalida hasta que lo ejecutes otra vez.")
                with st.form(f"factores_{tid}"):
                    niveles = ["Baja", "Media", "Alta", "Crítica"]
                    sev_nueva = st.selectbox("Gravedad actualizada", niveles, index=niveles.index(t["severidad"]))
                    usuarios_nuevos = st.number_input("Usuarios afectados", min_value=0, value=int(t["usuarios_afectados"]), step=1)
                    bloqueos_nuevos = st.number_input("Procesos bloqueados", min_value=0, value=int(t["procesos_bloqueados"]), step=1)
                    horas_nuevas = st.number_input("Horas sin resolver", min_value=0, value=int(t["antiguedad_horas"]), step=1)
                    dependencias_nuevas = st.number_input("Dependencias", min_value=0, value=int(t["dependencias"]), step=1)
                    workaround_nuevo = st.checkbox("Existe una solución temporal", value=bool(t["workaround"]))
                    motivo = st.text_area("Motivo o nueva evidencia *", placeholder="Ej.: Se confirmó que hay más usuarios afectados")
                    responsable = st.text_input("Responsable del cambio *", value="Responsable")
                    reevaluar = st.form_submit_button("Guardar y recalcular", type="primary")
                if reevaluar:
                    try:
                        actualizar_factores(tid, {
                            "severidad": sev_nueva, "usuarios_afectados": int(usuarios_nuevos),
                            "procesos_bloqueados": int(bloqueos_nuevos), "workaround": bool(workaround_nuevo),
                            "antiguedad_horas": int(horas_nuevas), "dependencias": int(dependencias_nuevas),
                        }, responsable, motivo)
                        st.rerun()
                    except Exception as exc:
                        st.error(str(exc))

        with col_b:
            st.markdown('<div class="panel-title">Historial</div>'
                        '<div class="panel-note">Del movimiento más reciente al más antiguo.</div>',
                        unsafe_allow_html=True)
            st.markdown(linea_de_tiempo(ver_historial(tid)), unsafe_allow_html=True)
            if t["seguimiento_ia"]:
                with st.expander("Último informe de priorización y auditoría"):
                    st.markdown(t["seguimiento_ia"])
