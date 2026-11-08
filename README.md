# Mesa de ayuda TI multiagente — Fase 3

Prototipo académico de soporte TI. El usuario crea tickets mediante **Streamlit**, Python calcula el riesgo con criterios explícitos, y **3 agentes CrewAI** (riesgo, soporte y seguimiento) generan recomendaciones utilizando **Ollama** local. Los tickets y su historial se guardan en **SQLite**.

## Requisitos

- Windows, macOS o Linux con **Python 3.12** (también otras versiones compatibles con CrewAI).
- Ollama instalado y el modelo `llama3.2:latest` descargado.
- Espacio y memoria suficientes para ejecutar el modelo local.
- No requiere API de pago.

## Inicio rápido (PowerShell / VS Code)

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
ollama list
python -m streamlit run app.py
```

Si `ollama list` no muestra `llama3.2:latest`, descargar con `ollama pull llama3.2:latest`. Asegura que Ollama esté abierto. Si PowerShell bloquea la activación, ejecuta `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass` solo en esa terminal y reactiva.

Navega a `http://localhost:8501`. Crea un ticket; en **Incidencias y atención** haz clic en el botón para ejecutar los 3 agentes; revisa el reporte y cambia estados en **Seguimiento**.

## Arquitectura

`Formulario Streamlit → SQLite → riesgo verificable en Python → CrewAI (Analista de riesgo → Especialista de soporte → Coordinador de seguimiento) → recomendaciones guardadas → persona verifica / actualiza / cierra ticket`

Se utiliza `Process.sequential` con `context` en las tareas. Los agentes tienen roles, goals, backstories, y no pueden delegar. El cálculo de riesgo **no** lo decide un LLM: los agentes interpretan el resultado validado. Las ponderaciones proceden del prototipo previo y son **ilustrativas** (no son SLA de producción).

## Alcance y límites

- **Sí:** registro, puntuación/prioridad, orientación de soporte de primer nivel, seguimiento manual con historial y cierre confirmado por usuario.
- **No:** acceso real a equipos, contraseñas, servidores, correo, asignación real a personal TI, notificaciones automáticas, resolución autónoma o servicio multiusuario con autenticación.
- SQLite local: todos los usuarios de la misma ejecución local comparten datos; no exponer públicamente sin controles de acceso y privacidad.
- El botón ejecuta los agentes bajo demanda; los agentes no actúan continuamente en segundo plano.
- La respuesta textual de Llama puede contener errores; validar antes de aplicar instrucciones.

## GitHub / equipo

Comparte `app.py`, `agents.py`, `core.py`, `requirements.txt`, `README.md`, `.gitignore`. **No** subas `.venv/`, `tickets.db`, claves ni datos reales. Cada integrante instala Ollama y ejecuta el proyecto local. Para colaborar, invita a compañeros desde Settings → Collaborators. El repositorio solo almacena el código; no hospeda Ollama.

## Verificación rápida

```powershell
python -m unittest discover -s tests -v
```
