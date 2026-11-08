import tempfile
import unittest
from pathlib import Path
from core import iniciar, crear_ticket, obtener, cambiar_estado, riesgo, ver_historial

BASE = {'solicitante':'Ana', 'categoria':'Incidencia', 'asunto':'Error VPN', 'descripcion':'No conecta la VPN',
        'severidad':'Media','usuarios_afectados':1000,'procesos_bloqueados':3,'workaround':False,
        'antiguedad_horas':18,'dependencias':2}

class TestMesaAyuda(unittest.TestCase):
    def test_riesgo_original(self):
        self.assertEqual(riesgo(BASE)['puntuacion'], 78)
        self.assertEqual(riesgo(BASE)['prioridad'], 'Crítica')
    def test_ticket_y_cierre_humano(self):
        with tempfile.TemporaryDirectory() as d:
            db=Path(d)/'x.db'; iniciar(db)
            pk=crear_ticket(BASE, db)
            self.assertEqual(obtener(pk, db)['estado'], 'Abierta')
            cambiar_estado(pk, 'En atención', 'Responsable TI', 'Investigación iniciada', db)
            cambiar_estado(pk, 'Resuelta propuesta', 'Responsable TI', 'Pasos sugeridos', db)
            with self.assertRaises(ValueError):
                cambiar_estado(pk, 'Cerrada', 'Responsable TI', 'Terminó', db)
            cambiar_estado(pk, 'Cerrada', 'Usuario', 'Confirmo que funciona', db)
            self.assertEqual(obtener(pk, db)['estado'], 'Cerrada')
            self.assertEqual(len(ver_historial(pk, db)), 4)

if __name__=='__main__':
    unittest.main()
