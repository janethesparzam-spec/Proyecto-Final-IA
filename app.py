"""Portal de priorización de incidencias con CrewAI y Ollama.

Interfaz Streamlit para registrar, analizar y auditar incidencias.
Conserva la lógica existente de core.py y agents.py.
"""

import json
from html import escape

import streamlit as st

from core import (
    iniciar,
    crear_ticket,
    obtener,
    listar,
    actualizar_ia,
    cambiar_estado,
    ver_historial,
)


st.set_page_config(
    page_title="Centro de soporte IA | Service Desk",
    page_icon="🧑‍💻",
    layout="wide",
    initial_sidebar_state="collapsed",
)
iniciar()

# Solo personalización visual. No altera las reglas de riesgo ni los agentes.
st.markdown(
    """
<style>
    :root {
        --ink: #17253d;
        --navy: #10233f;
        --blue: #2563eb;
        --teal: #0d9488;
        --muted: #62718a;
        --line: #e0e8f1;
        --surface: #ffffff;
    }
    .stApp {
        background: linear-gradient(180deg, #f2f6fc 0%, #f8fafc 42%, #f4f7fb 100%);
        color: var(--ink);
    }
    .block-container {
        max-width: 1480px;
        padding-top: 1.1rem;
        padding-bottom: 3.5rem;
    }
    [data-testid="stHeader"] { background: transparent; }
    #MainMenu { visibility: hidden; }
    /* Encabezado corporativo */
    .portal-hero {
        position: relative;
        overflow: hidden;
        background: linear-gradient(115deg, #10233f 2%, #194b7c 63%, #0e807f 130%);
        border: 1px solid rgba(255,255,255,.14);
        border-radius: 22px;
        padding: 2rem 2.2rem;
        color: white;
        box-shadow: 0 16px 42px rgba(22,48,84,.16);
        margin-bottom: .85rem;
    }
    .portal-hero::after {
        content: "";
        position: absolute;
        right: -65px;
        top: -110px;
        width: 360px;
        height: 360px;
        border: 1px solid rgba(255,255,255,.12);
        border-radius: 50%;
        box-shadow: 0 0 0 65px rgba(255,255,255,.035), 0 0 0 135px rgba(255,255,255,.025);
        pointer-events: none;
    }
    .hero-eyebrow {
        text-transform: uppercase;
        letter-spacing: .17em;
        font-weight: 700;
        font-size: .72rem;
        color: #b9e9e8;
        margin-bottom: .75rem;
    }
    .hero-heading {
        font-size: clamp(1.75rem, 3.2vw, 2.65rem);
        font-weight: 760;
        letter-spacing: -.042em;
        line-height: 1.12;
        margin: 0;
        color: white;
    }
    .hero-description {
        font-size: .98rem;
        line-height: 1.6;
        color: #d9e7f7;
        margin-top: .8rem;
        max-width: 760px;
    }
    .hero-pills { display:flex; flex-wrap:wrap; gap:.5rem; margin-top:1.2rem; }
    .hero-pill {
        background: rgba(255,255,255,.11);
        border: 1px solid rgba(255,255,255,.18);
        border-radius: 50px;
        padding: .32rem .68rem;
        font-size: .76rem;
        color: #f0f8ff;
    }
    .welcome-strip {
        border: 1px solid #cfe3fb;
        background: #edf5ff;
        color: #285080;
        border-radius: 12px;
        padding: .85rem 1rem;
        margin: .45rem 0 1.3rem;
        font-size: .91rem;
    }
    .section-heading { margin: .6rem 0 .15rem; }
    .section-kicker {
        color: #0d9488;
        text-transform: uppercase;
        font-size: .72rem;
        letter-spacing: .12em;
        font-weight: 750;
    }
    .section-title {
        color: var(--navy);
        font-size: 1.42rem;
        font-weight: 750;
        letter-spacing: -.025em;
        margin: .25rem 0;
    }
    .section-note { color: #65738a; font-size: .90rem; margin-bottom: .9rem; }
    /* KPIs */
    [data-testid="stMetric"] {
        background: #fff;
        border: 1px solid var(--line);
        border-radius: 16px;
        padding: .9rem 1.15rem;
        box-shadow: 0 7px 25px rgba(26,51,85,.045);
        min-height: 112px;
    }
    [data-testid="stMetricLabel"] { color: #66758e; font-weight: 600; }
    [data-testid="stMetricValue"] { color: #132a49; font-weight: 780; }
    /* Formularios */
    [data-testid="stForm"] {
        background: white;
        border: 1px solid var(--line);
        border-radius: 18px;
        padding: 1.45rem 1.55rem;
        box-shadow: 0 8px 28px rgba(26,51,85,.045);
    }
    [data-testid="stTextInput"] input,
    [data-testid="stNumberInput"] input,
    [data-testid="stTextArea"] textarea {
        background: #fbfdff;
        border-radius: 9px;
    }
    div[data-testid="stButton"] button[kind="primary"],
    div[data-testid="stFormSubmitButton"] button[kind="primary"] {
        border: 0;
        color: white;
        background: linear-gradient(105deg, #1d4ed8, #1477ad);
        border-radius: 10px;
        font-weight: 680;
        box-shadow: 0 6px 15px rgba(29,78,216,.15);
    }
    div[data-testid="stButton"] button[kind="primary"]:hover,
    div[data-testid="stFormSubmitButton"] button[kind="primary"]:hover {
        background: linear-gradient(105deg, #1e40af, #0e7490);
    }
    /* Pestañas y contenido */
    [data-baseweb="tab-list"] {
        gap: .55rem;
        border-bottom: 1px solid #d9e4f1;
        padding-bottom: .2rem;
        margin-top: .3rem;
    }
    button[data-baseweb="tab"] {
        border-radius: 10px 10px 0 0;
        background: #fff;
        padding: .75rem 1rem;
        color: #50627b;
        border: 1px solid #e4eaf3;
    }
    button[data-baseweb="tab"][aria-selected="true"] {
        background: #eaf2ff;
        border-color: #bed6f9;
        color: #1d4ed8;
        font-weight: 700;
    }
    [data-testid="stExpander"] {
        background: #fff;
        border: 1px solid var(--line);
        border-radius: 12px;
        overflow: hidden;
    }
    [data-testid="stDataFrame"] {
        background: white;
        border: 1px solid var(--line);
        border-radius: 14px;
        padding: .3rem;
        box-shadow: 0 6px 22px rgba(20,41,70,.035);
    }
    .ticket-summary {
        background: #fff;
        border: 1px solid var(--line);
        border-left: 4px solid #2187bb;
        border-radius: 12px;
        padding: 1rem 1.2rem;
        margin: .8rem 0 1rem;
        box-shadow: 0 5px 18px rgba(20,41,70,.035);
    }
    .ticket-summary-title { font-weight: 760; color: #1c3557; margin-bottom: .5rem; }
    .ticket-summary-detail { color: #43536e; line-height: 1.65; font-size: .94rem; }
    .ticket-tags { display:flex; flex-wrap:wrap; gap:.5rem; margin-top:.8rem; }
    .ticket-tag {
        border-radius: 7px;
        padding: .25rem .55rem;
        font-size: .79rem;
        background: #f0f5fa;
        color: #29476a;
        border: 1px solid #dce6f1;
    }
    .portal-footer {
        padding: 1.25rem 0 .5rem;
        color: #78859a;
        font-size: .78rem;
        text-align: center;
    }
    @media(max-width: 700px) {
        .portal-hero { padding: 1.35rem 1.2rem; border-radius: 15px; }
        .hero-heading { font-size: 1.8rem; }
        .block-container { padding-top: .5rem; }
    }
</style>
""",
    unsafe_allow_html=True,
)

st.markdown(
    """
<section class="portal-hero">
    <div class="hero-eyebrow">Service Desk · Gestión de solicitudes </div>
    <h1 class="hero-heading">Centro de soporte IA</h1>
    <div class="hero-description">
        Un solo lugar para registrar incidencias, analizar riesgos e impactos
        y justificar prioridades mediante un sistema multiagente.
    </div>
    <div class="hero-pills">
        <span class="hero-pill">Atención de incidencias</span>
        <span class="hero-pill">Evaluación de riesgo</span>
        <span class="hero-pill">Impacto y dependencias</span>
        <span class="hero-pill">Priorización y auditoría</span>
    </div>
</section>
<div class="welcome-strip">
    <strong>Bienvenido.</strong> Registra una incidencia, revisa el análisis de los tres agentes
    y consulta su prioridad validada y el historial de seguimiento.
</div>
""",
    unsafe_allow_html=True,
)

# Indicadores construidos exclusivamente con los tickets reales de SQLite.
registros_resumen = listar()
total_tickets = len(registros_resumen)
abiertos = sum(t["estado"] == "Abierta" for t in registros_resumen)
criticos_altos = sum(
    t["prioridad"] in ("Alta", "Crítica") and t["estado"] != "Cerrada"
    for t in registros_resumen
)
pendientes = sum(t["estado"] != "Cerrada" for t in registros_resumen)

k1, k2, k3, k4 = st.columns(4)
k1.metric("Tickets registrados", total_tickets)
k2.metric("Nuevos / abiertos", abiertos)
k3.metric("Prioridad alta o crítica", criticos_altos)
k4.metric("Pendientes de cierre", pendientes)

st.write("")
tab1, tab2, tab3 = st.tabs(
    ["Registro de tickets", "Análisis multiagente", "Seguimiento y cierre"]
)

with tab1:
    st.markdown(
        '<div class="section-heading"><div class="section-kicker">Nueva solicitud</div>'
        '<div class="section-title">¿En qué podemos ayudarte?</div>'
        '<div class="section-note">Describe tu necesidad para que el equipo de soporte pueda atenderla.</div></div>',
        unsafe_allow_html=True,
    )
    with st.form("ticket"):
        c1, c2 = st.columns(2, gap="large")
        with c1:
            solicitante = st.text_input("Nombre de la persona *")
            categoria = st.selectbox("Tipo de solicitud", ["Incidencia", "Duda", "Solicitud de soporte"])
            asunto = st.text_input("Asunto *")
            descripcion = st.text_area(
                "Describe qué sucede o qué necesitas *",
                height=145,
                placeholder="Ejemplo: No puedo conectarme al Wi-Fi de la oficina desde las 9:00",
            )
            severidad = st.selectbox("Gravedad reportada", ["Baja", "Media", "Alta", "Crítica"], index=1)
        with c2:
            usuarios = st.number_input("Usuarios afectados (estimación)", min_value=0, value=1, step=1)
            bloqueos = st.number_input("Procesos o actividades bloqueadas", min_value=0, value=0, step=1)
            temporal = st.checkbox("Existe una solución temporal (workaround)")
            horas = st.number_input("Horas desde que comenzó", min_value=0, value=1, step=1)
            dependencias = st.number_input("Actividades o tickets dependientes", min_value=0, value=0, step=1)
        enviado = st.form_submit_button("Crear ticket", type="primary")
    if enviado:
        try:
            pk = crear_ticket({
                "solicitante": solicitante,
                "categoria": categoria,
                "asunto": asunto,
                "descripcion": descripcion,
                "severidad": severidad,
                "usuarios_afectados": usuarios,
                "procesos_bloqueados": bloqueos,
                "workaround": temporal,
                "antiguedad_horas": horas,
                "dependencias": dependencias,
            })
            st.success(f'Ticket TI-{pk:04d} registrado. Puedes procesarlo en "Análisis Multiagente".')
        except Exception as exc:
            st.error(str(exc))

with tab2:
    st.markdown(
        '<div class="section-heading"><div class="section-kicker">Evaluación multiagente</div>'
        '<div class="section-title">Bandeja de tickets</div>'
        '<div class="section-note">Consulta las incidencias y ejecuta el análisis de riesgo, impacto y priorización.</div></div>',
        unsafe_allow_html=True,
    )
    registros = listar()
    if not registros:
        st.info("Todavía no hay tickets. Crea el primero en Registro de tickets.")
    else:
        st.dataframe(
            [{
                "Ticket": f'TI-{t["id"]:04d}',
                "Asunto": t["asunto"],
                "Tipo": t["categoria"],
                "Prioridad": t["prioridad"],
                "Riesgo /100": t["puntuacion"],
                "Estado": t["estado"],
            } for t in registros],
            hide_index=True,
            use_container_width=True,
        )
        seleccion = st.selectbox(
            "Selecciona un ticket",
            [t["id"] for t in registros],
            format_func=lambda v: f'TI-{v:04d} · {next(x["asunto"] for x in registros if x["id"] == v)}',
        )
        t = obtener(seleccion)
        prioridad = escape(str(t["prioridad"]))
        estado = escape(str(t["estado"]))
        descripcion = escape(str(t["descripcion"]))
        st.markdown(
            f'<div class="ticket-summary">'
            f'<div class="ticket-summary-title">Detalle de la solicitud · TI-{seleccion:04d}</div>'
            f'<div class="ticket-summary-detail">{descripcion}</div>'
            f'<div class="ticket-tags">'
            f'<span class="ticket-tag">Riesgo: {t["puntuacion"]}/100</span>'
            f'<span class="ticket-tag">Prioridad: {prioridad}</span>'
            f'<span class="ticket-tag">Estado: {estado}</span>'
            f'</div></div>',
            unsafe_allow_html=True,
        )

        # ---------------------------------------------------------
        # APORTE STREAMLIT - RESUMEN EJECUTIVO DEL TICKET - JORGE
        # ---------------------------------------------------------

        st.markdown("### Resumen ejecutivo del ticket")

        r1, r2, r3, r4, r5 = st.columns(5)

        r1.metric(
            "Riesgo",
            f'{t["puntuacion"]}/100'
        )

        r2.metric(
            "Prioridad",
            str(t["prioridad"])
        )

        r3.metric(
            "Estado",
            str(t["estado"])
        )

        r4.metric(
            "Usuarios afectados",
            int(t["usuarios_afectados"])
        )

        r5.metric(
            "Dependencias",
            int(t["dependencias"])
        )

        # ---------------------------------------------------------
        # FIN DEL RESUMEN EJECUTIVO DEL TICKET - JORGE
        # ---------------------------------------------------------

        with st.expander("Factores utilizados para el cálculo de riesgo"):
            st.json(json.loads(t["factores_json"]))
        if st.button("Analizar incidencia con 3 agentes", type="primary"):
            try:
                from agents import ejecutar_agentes
                with st.spinner("CrewAI está ejecutando tres tareas con Ollama local…"):
                    outputs = ejecutar_agentes(t)
                    actualizar_ia(
                        seleccion,
                        outputs["evaluacion"],
                        outputs["soporte"],
                        outputs["seguimiento"],
                    )
                st.success("Los tres agentes terminaron. Revisa las evaluaciones y el informe de priorización.")
                st.rerun()
            except Exception as exc:
                st.error(f"No fue posible completar CrewAI: {exc}")
                st.caption("Comprueba que Ollama esté encendido y que tengas descargado llama3.2:latest.")
        for titulo, campo in [
            ("01 · Análisis de riesgo", "evaluacion_ia"),
            ("02 · Impacto y dependencias", "propuesta_soporte"),
            ("03 · Priorización y auditoría", "seguimiento_ia"),
        ]:
            if t[campo]:
                with st.expander(titulo, expanded=(campo == "propuesta_soporte")):
                    contenido = t[campo]
                    if campo in ("evaluacion_ia", "propuesta_soporte"):
                        try:
                            st.json(json.loads(contenido))
                        except (ValueError, TypeError):
                            st.markdown(contenido)
                    else:
                        st.markdown(contenido)
        st.caption(
            "Las evaluaciones de IA son orientativas y pueden contener errores. "
            "La puntuación y la prioridad oficial se calculan con Python; los agentes no las modifican."
        )

with tab3:
    st.markdown(
        '<div class="section-heading"><div class="section-kicker">Control del servicio</div>'
        '<div class="section-title">Seguimiento y cierre</div>'
        '<div class="section-note">Registra avances y conserva el historial de cada incidencia.</div></div>',
        unsafe_allow_html=True,
    )
    registros = listar()
    if registros:
        tid = st.selectbox(
            "Ticket para seguimiento",
            [t["id"] for t in registros],
            format_func=lambda v: f"TI-{v:04d}",
            key="seguimiento_id",
        )
        t = obtener(tid)
        st.markdown(
            f'<div class="ticket-summary"><div class="ticket-summary-title">Ticket TI-{tid:04d}</div>'
            f'<div class="ticket-tags"><span class="ticket-tag">Estado: {escape(str(t["estado"]))}</span>'
            f'<span class="ticket-tag">Prioridad: {escape(str(t["prioridad"]))}</span></div></div>',
            unsafe_allow_html=True,
        )
        opciones = {
            "Abierta": ["En atención", "Escalada"],
            "En atención": ["En espera del usuario", "Resuelta propuesta", "Escalada"],
            "En espera del usuario": ["En atención", "Escalada"],
            "Resuelta propuesta": ["Cerrada", "En atención"],
            "Escalada": ["En atención"],
            "Cerrada": ["En atención"],
        }[t["estado"]]
        with st.form("estado"):
            nuevo = st.selectbox("Cambiar estado a", opciones)
            actor = st.radio("Quién confirma este cambio", ["Responsable", "Usuario"], horizontal=True)
            comentario = st.text_area(
                "Comentario / resultado de la prueba *",
                placeholder="Ej.: El usuario comprobó que ya puede iniciar sesión",
            )
            guardar = st.form_submit_button("Registrar seguimiento", type="primary")
        if guardar:
            try:
                cambiar_estado(tid, nuevo, actor, comentario)
                st.success("Se guardó el cambio con fecha y responsable.")
                st.rerun()
            except Exception as exc:
                st.error(str(exc))
        with st.expander("Actualizar factores y reevaluar prioridad (prueba de adaptación)"):
            st.caption("Registra nueva información del mismo ticket. Se conservará el historial y se invalidará el análisis IA anterior hasta ejecutarlo nuevamente.")
            with st.form(f"factores_{tid}"):
                c1, c2 = st.columns(2)
                with c1:
                    sev_actual = ["Baja", "Media", "Alta", "Crítica"].index(t["severidad"])
                    sev_nueva = st.selectbox("Gravedad actualizada", ["Baja", "Media", "Alta", "Crítica"], index=sev_actual)
                    usuarios_nuevos = st.number_input("Usuarios afectados", min_value=0, value=int(t["usuarios_afectados"]), step=1)
                    bloqueos_nuevos = st.number_input("Procesos bloqueados", min_value=0, value=int(t["procesos_bloqueados"]), step=1)
                with c2:
                    workaround_nuevo = st.checkbox("Existe workaround", value=bool(t["workaround"]))
                    horas_nuevas = st.number_input("Antigüedad (horas)", min_value=0, value=int(t["antiguedad_horas"]), step=1)
                    dependencias_nuevas = st.number_input("Dependencias", min_value=0, value=int(t["dependencias"]), step=1)
                motivo_factores = st.text_area("Motivo / nueva evidencia *", placeholder="Ej.: Se confirmó que ahora hay más usuarios afectados")
                responsable_factores = st.text_input("Responsable del cambio *", value="Responsable")
                reevaluar = st.form_submit_button("Guardar cambios y recalcular", type="primary")
            if reevaluar:
                try:
                    from core import actualizar_factores
                    nuevo_riesgo = actualizar_factores(tid, {
                        "severidad": sev_nueva,
                        "usuarios_afectados": int(usuarios_nuevos),
                        "procesos_bloqueados": int(bloqueos_nuevos),
                        "workaround": bool(workaround_nuevo),
                        "antiguedad_horas": int(horas_nuevas),
                        "dependencias": int(dependencias_nuevas),
                    }, responsable_factores, motivo_factores)
                    st.success(f'Prioridad actualizada: {nuevo_riesgo["puntuacion"]}/100 — {nuevo_riesgo["prioridad"]}. Ejecuta de nuevo los tres agentes.')
                    st.rerun()
                except Exception as exc:
                    st.error(str(exc))
        st.markdown("#### Historial del ticket")
        st.dataframe(ver_historial(tid), hide_index=True, use_container_width=True)
        if t["seguimiento_ia"]:
            with st.expander("Último informe de priorización y auditoría"):
                st.markdown(t["seguimiento_ia"])
    else:
        st.info("No hay tickets para dar seguimiento.")

st.markdown(
    '<div class="portal-footer">Centro de soporte IA · Análisis multiagente de riesgo, impacto y priorización</div>',
    unsafe_allow_html=True,
)
