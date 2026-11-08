"""Reglas verificables y almacenamiento local del prototipo académico."""
import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

DB = Path(__file__).resolve().parent / 'tickets.db'
SEVERIDAD = {'Baja': 5, 'Media': 10, 'Alta': 18, 'Crítica': 25}


def ahora():
    return datetime.now(timezone.utc).isoformat(timespec='seconds')


def riesgo(ticket):
    """Ponderaciones demostrativas de las fases previas; no son un SLA real."""
    def numero(k):
        x = ticket[k]
        if isinstance(x, bool) or not isinstance(x, int) or x < 0:
            raise ValueError(f'{k} debe ser entero no negativo')
        return x
    severidad = ticket['severidad']
    if severidad not in SEVERIDAD:
        raise ValueError('Severidad no válida')
    if not isinstance(ticket['workaround'], bool):
        raise ValueError('workaround debe ser booleano')
    f = {
        'severidad': SEVERIDAD[severidad],
        'usuarios': min(20, round(numero('usuarios_afectados') / 50)),
        'bloqueos': min(25, numero('procesos_bloqueados') * 9),
        'sin_workaround': 0 if ticket['workaround'] else 15,
        'antiguedad': min(8, (numero('antiguedad_horas') // 12) * 2),
        'dependencias': min(7, numero('dependencias') * 3),
    }
    total = sum(f.values())
    return {'puntuacion': total, 'prioridad': 'Crítica' if total >= 75 else 'Alta' if total >= 50 else 'Media' if total >= 25 else 'Baja', 'factores': f}


def conectar(db=DB):
    con = sqlite3.connect(str(db), timeout=20)
    con.row_factory = sqlite3.Row
    return con


def iniciar(db=DB):
    with conectar(db) as con:
        con.execute('''CREATE TABLE IF NOT EXISTS tickets (
            id INTEGER PRIMARY KEY AUTOINCREMENT, creado TEXT NOT NULL,
            actualizado TEXT NOT NULL, solicitante TEXT NOT NULL,
            categoria TEXT NOT NULL, asunto TEXT NOT NULL, descripcion TEXT NOT NULL,
            severidad TEXT NOT NULL, usuarios_afectados INTEGER NOT NULL,
            procesos_bloqueados INTEGER NOT NULL, workaround INTEGER NOT NULL,
            antiguedad_horas INTEGER NOT NULL, dependencias INTEGER NOT NULL,
            estado TEXT NOT NULL, puntuacion INTEGER NOT NULL, prioridad TEXT NOT NULL,
            factores_json TEXT NOT NULL, evaluacion_ia TEXT DEFAULT '',
            propuesta_soporte TEXT DEFAULT '', seguimiento_ia TEXT DEFAULT ''
        )''')
        con.execute('''CREATE TABLE IF NOT EXISTS historial (
            id INTEGER PRIMARY KEY AUTOINCREMENT, ticket_id INTEGER NOT NULL,
            fecha TEXT NOT NULL, actor TEXT NOT NULL, evento TEXT NOT NULL,
            FOREIGN KEY(ticket_id) REFERENCES tickets(id)
        )''')


def historial(ticket_id, actor, evento, db=DB):
    with conectar(db) as con:
        con.execute('INSERT INTO historial(ticket_id, fecha, actor, evento) VALUES(?,?,?,?)',
                    (ticket_id, ahora(), actor, evento))


def crear_ticket(datos, db=DB):
    if not datos['solicitante'].strip() or not datos['asunto'].strip() or not datos['descripcion'].strip():
        raise ValueError('Solicitante, asunto y descripción son obligatorios')
    r = riesgo(datos)
    t = ahora()
    with conectar(db) as con:
        cur = con.execute('''INSERT INTO tickets
            (creado, actualizado, solicitante, categoria, asunto, descripcion, severidad,
            usuarios_afectados, procesos_bloqueados, workaround, antiguedad_horas, dependencias,
            estado, puntuacion, prioridad, factores_json)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)''',
            (t, t, datos['solicitante'].strip(), datos['categoria'], datos['asunto'].strip(),
             datos['descripcion'].strip(), datos['severidad'], datos['usuarios_afectados'],
             datos['procesos_bloqueados'], int(datos['workaround']), datos['antiguedad_horas'],
             datos['dependencias'], 'Abierta', r['puntuacion'], r['prioridad'], json.dumps(r['factores'], ensure_ascii=False)))
        pk = cur.lastrowid
    historial(pk, 'Sistema', f'Ticket creado. Riesgo {r["puntuacion"]}/100, prioridad {r["prioridad"]}.', db)
    return pk


def obtener(pk, db=DB):
    with conectar(db) as con:
        row = con.execute('SELECT * FROM tickets WHERE id=?', (pk,)).fetchone()
        return dict(row) if row else None


def listar(db=DB):
    with conectar(db) as con:
        return [dict(x) for x in con.execute('SELECT * FROM tickets ORDER BY CASE prioridad WHEN "Crítica" THEN 1 WHEN "Alta" THEN 2 WHEN "Media" THEN 3 ELSE 4 END, puntuacion DESC, id DESC')]


def actualizar_ia(pk, evaluacion, soporte, seguimiento, db=DB):
    with conectar(db) as con:
        con.execute('UPDATE tickets SET evaluacion_ia=?, propuesta_soporte=?, seguimiento_ia=?, actualizado=? WHERE id=?',
                    (evaluacion, soporte, seguimiento, ahora(), pk))
    historial(pk, 'CrewAI', 'Los tres agentes generaron recomendaciones; requieren validación humana.', db)


def cambiar_estado(pk, nuevo, actor, comentario, db=DB):
    permitidos = {'Abierta': {'En atención', 'Escalada'}, 'En atención': {'En espera del usuario', 'Resuelta propuesta', 'Escalada'},
                  'En espera del usuario': {'En atención', 'Escalada'}, 'Resuelta propuesta': {'Cerrada', 'En atención'},
                  'Escalada': {'En atención'}, 'Cerrada': {'En atención'}}
    actual = obtener(pk, db)
    if not actual:
        raise ValueError('Ticket inexistente')
    if nuevo not in permitidos.get(actual['estado'], set()):
        raise ValueError(f'Transición no permitida: {actual["estado"]} → {nuevo}')
    if not comentario.strip():
        raise ValueError('Escribe una explicación para registrar el seguimiento')
    if nuevo == 'Cerrada' and actor != 'Usuario':
        raise ValueError('El cierre requiere confirmación del usuario')
    with conectar(db) as con:
        con.execute('UPDATE tickets SET estado=?, actualizado=? WHERE id=?', (nuevo, ahora(), pk))
    historial(pk, actor, f'{actual["estado"]} → {nuevo}. {comentario.strip()}', db)


def ver_historial(pk, db=DB):
    with conectar(db) as con:
        return [dict(x) for x in con.execute('SELECT fecha, actor, evento FROM historial WHERE ticket_id=? ORDER BY id', (pk,))]


def actualizar_factores(pk, cambios, actor, motivo, db=DB):
    """Reevalúa un ticket existente y registra cambios auditables en una transacción."""
    campos = ('severidad', 'usuarios_afectados', 'procesos_bloqueados',
              'workaround', 'antiguedad_horas', 'dependencias')
    if not motivo.strip():
        raise ValueError('Indica el motivo de la actualización')
    if not actor.strip():
        raise ValueError('Indica quién registra el cambio')
    if set(cambios) != set(campos):
        raise ValueError('Se requieren los seis factores de riesgo')
    with conectar(db) as con:
        anterior = con.execute('SELECT * FROM tickets WHERE id=?', (pk,)).fetchone()
        if anterior is None:
            raise ValueError('Ticket inexistente')
        anterior = dict(anterior)
        if anterior['estado'] == 'Cerrada':
            raise ValueError('No se pueden modificar factores de un ticket cerrado')
        nuevo = dict(anterior)
        nuevo.update(cambios)
        nuevo['workaround'] = cambios['workaround']
        evaluacion = riesgo(nuevo)
        diferencias = [f'{c}: {bool(anterior[c]) if c == "workaround" else anterior[c]} → {cambios[c]}'
                       for c in campos if (bool(anterior[c]) if c == 'workaround' else anterior[c]) != cambios[c]]
        if not diferencias:
            raise ValueError('No se detectaron cambios en los factores')
        fecha = ahora()
        con.execute("""UPDATE tickets SET severidad=?, usuarios_afectados=?, procesos_bloqueados=?,
            workaround=?, antiguedad_horas=?, dependencias=?, puntuacion=?, prioridad=?,
            factores_json=?, evaluacion_ia='', propuesta_soporte='', seguimiento_ia='', actualizado=?
            WHERE id=?""",
            (cambios['severidad'], cambios['usuarios_afectados'], cambios['procesos_bloqueados'],
             int(cambios['workaround']), cambios['antiguedad_horas'], cambios['dependencias'],
             evaluacion['puntuacion'], evaluacion['prioridad'],
             json.dumps(evaluacion['factores'], ensure_ascii=False), fecha, pk))
        evento = (f'Factores actualizados: {"; ".join(diferencias)}. '
                  f'Riesgo {anterior["puntuacion"]}/100 ({anterior["prioridad"]}) → '
                  f'{evaluacion["puntuacion"]}/100 ({evaluacion["prioridad"]}). '
                  f'Motivo: {motivo.strip()}. Análisis IA anterior invalidado; requiere nueva ejecución.')
        con.execute('INSERT INTO historial(ticket_id, fecha, actor, evento) VALUES(?,?,?,?)',
                    (pk, fecha, actor.strip(), evento))
    return evaluacion
