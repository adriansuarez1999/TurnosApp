import threading
from datetime import datetime, time, timedelta
from decimal import Decimal
from types import SimpleNamespace
from unittest import mock
from django.db import connection
from django.test import TestCase, TransactionTestCase
from apps.usuarios.models import Notificacion
from . import reglas
from .models import Turno
from .helpers_tests import (
    Escenario, cliente_http, patch_json, crear_usuario, crear_turno_directo,
    dias_desde_hoy, limpiar_tablas,
)


# ══════════════════════════════════════════
# Sprint 7 - Módulo B (Facundo): cancelación con ventana y reprogramación
# ══════════════════════════════════════════

def url_cancelar(turno):
    return f'/api/turnos/{turno.id_turno}/cancelar/'


def url_reprogramar(turno):
    return f'/api/turnos/{turno.id_turno}/reprogramar/'


def con_horas(horas):
    # Simula la configuración del dueño (horas_anticipacion_cancelacion).
    return mock.patch.object(reglas, 'horas_cancelacion', return_value=horas)


class VentanaDeCancelacionTests(Escenario, TestCase):
    def setUp(self):
        self.crear_escenario()
        # Turno de mañana a las 10:00: siempre está a más de 10 h de distancia.
        self.turno = crear_turno_directo(self.c1, self.bo1, self.s30, self.manana, time(10, 0))

    def test_el_limite_se_calcula_por_turno(self):
        with con_horas(2):
            self.assertEqual(
                reglas.fecha_limite_cancelacion(self.turno),
                datetime.combine(self.manana, time(8, 0)),
            )
        otro = crear_turno_directo(self.c1, self.bo2, self.s30, self.manana, time(15, 30))
        with con_horas(2):
            self.assertEqual(
                reglas.fecha_limite_cancelacion(otro),
                datetime.combine(self.manana, time(13, 30)),
            )

    def test_borde_exacto_del_limite(self):
        with con_horas(2):
            limite = reglas.fecha_limite_cancelacion(self.turno)
            self.assertTrue(reglas.puede_cancelar(self.turno, ahora=limite))
            self.assertFalse(reglas.puede_cancelar(self.turno, ahora=limite + timedelta(seconds=1)))
            self.assertTrue(reglas.puede_cancelar(self.turno, ahora=limite - timedelta(hours=5)))

    def test_cero_horas_se_puede_hasta_el_inicio(self):
        with con_horas(0):
            inicio = datetime.combine(self.manana, time(10, 0))
            self.assertTrue(reglas.puede_cancelar(self.turno, ahora=inicio))
            self.assertFalse(reglas.puede_cancelar(self.turno, ahora=inicio + timedelta(minutes=1)))

    def test_estados_no_cancelables(self):
        for estado in ('CANCELADO', 'FINALIZADO', 'AUSENTE'):
            self.turno.estado = estado
            self.assertFalse(reglas.puede_cancelar(self.turno), estado)

    def test_horas_configuradas_y_valor_por_defecto(self):
        self.assertEqual(reglas.horas_cancelacion(SimpleNamespace(horas_anticipacion_cancelacion=6)), 6)
        self.assertEqual(reglas.horas_cancelacion(SimpleNamespace(horas_anticipacion_cancelacion=0)), 0)
        # Sin el campo, vacío o inválido: valor por defecto (2 h).
        self.assertEqual(reglas.horas_cancelacion(SimpleNamespace()), reglas.HORAS_CANCELACION_POR_DEFECTO)
        self.assertEqual(reglas.horas_cancelacion(SimpleNamespace(horas_anticipacion_cancelacion=None)), 2)
        self.assertEqual(reglas.horas_cancelacion(SimpleNamespace(horas_anticipacion_cancelacion=-3)), 2)


class CancelarTurnoTests(Escenario, TestCase):
    def setUp(self):
        self.crear_escenario()
        self.turno = crear_turno_directo(self.c1, self.bo1, self.s30, self.manana, time(10, 0))
        self.http = cliente_http(self.c1)

    def estado_en_base(self):
        return Turno.objects.get(id_turno=self.turno.id_turno).estado

    def test_cancelar_dentro_del_plazo(self):
        with con_horas(2):
            r = patch_json(self.http, url_cancelar(self.turno))
        self.assertEqual(r.status_code, 200, r.content)
        self.assertEqual(r.json()['estado'], 'CANCELADO')
        self.assertEqual(self.estado_en_base(), 'CANCELADO')

    def test_cancelar_avisa_al_barbero(self):
        with con_horas(2):
            patch_json(self.http, url_cancelar(self.turno))
        self.assertTrue(Notificacion.objects.filter(
            id_usuario=self.u_bo1, tipo='TURNO_CANCELADO_CLIENTE').exists())

    def test_fuera_de_plazo_se_rechaza_en_el_endpoint(self):
        # Llamada directa a la API, sin pasar por ninguna pantalla.
        with con_horas(48):
            r = patch_json(self.http, url_cancelar(self.turno))
        self.assertEqual(r.status_code, 400)
        datos = r.json()
        self.assertFalse(datos['ok'])
        self.assertIn('plazo de cancelación', datos['error'])
        self.assertIn('fecha_limite_cancelacion', datos)
        self.assertEqual(self.estado_en_base(), 'CONFIRMADO')

    def test_sin_configuracion_usa_el_valor_por_defecto(self):
        # Turno de mañana 10:00 con 2 h por defecto: se puede.
        r = patch_json(self.http, url_cancelar(self.turno))
        self.assertEqual(r.status_code, 200)

    def test_turno_ajeno(self):
        r = patch_json(cliente_http(self.c2), url_cancelar(self.turno))
        self.assertEqual(r.status_code, 403)
        self.assertEqual(self.estado_en_base(), 'CONFIRMADO')

    def test_turno_inexistente(self):
        self.assertEqual(patch_json(self.http, '/api/turnos/99999/cancelar/').status_code, 404)

    def test_sin_sesion(self):
        self.assertEqual(patch_json(cliente_http(), url_cancelar(self.turno)).status_code, 401)

    def test_metodo_no_permitido(self):
        self.assertEqual(self.http.get(url_cancelar(self.turno)).status_code, 405)

    def test_estados_que_no_se_pueden_cancelar(self):
        for estado in ('CANCELADO', 'FINALIZADO', 'AUSENTE'):
            Turno.objects.filter(id_turno=self.turno.id_turno).update(estado=estado)
            r = patch_json(self.http, url_cancelar(self.turno))
            self.assertEqual(r.status_code, 400, estado)
            self.assertEqual(self.estado_en_base(), estado)

    def test_el_barbero_puede_cancelar_fuera_del_plazo_del_cliente(self):
        # La ventana es solo para el cliente: el barbero usa su propia ruta.
        with con_horas(48):
            r = patch_json(cliente_http(self.u_bo1), f'/api/mi-agenda/turnos/{self.turno.id_turno}/cancelar/')
        self.assertEqual(r.status_code, 200, r.content)
        self.assertEqual(self.estado_en_base(), 'CANCELADO')

    def test_cancelar_libera_el_horario(self):
        patch_json(self.http, url_cancelar(self.turno))
        h = cliente_http().get('/api/turnos/disponibles/', {
            'fecha': str(self.manana), 'barbero': self.bo1.id_barbero}).json()
        self.assertEqual({x['hora']: x['estado'] for x in h}['10:00'], 'DISPONIBLE')


class ReprogramarTurnoTests(Escenario, TestCase):
    def setUp(self):
        self.crear_escenario()
        self.turno = crear_turno_directo(self.c1, self.bo1, self.s30, self.manana, time(10, 0))
        self.http = cliente_http(self.c1)
        self.pasado_manana = dias_desde_hoy(2)

    def reprogramar(self, fecha=None, hora='11:00', barbero=None, http=None, turno=None):
        cuerpo = {'fecha': str(fecha or self.manana), 'hora_inicio': hora}
        if barbero:
            cuerpo['id_barbero'] = barbero.id_barbero
        return patch_json(http or self.http, url_reprogramar(turno or self.turno), cuerpo)

    def turno_en_base(self):
        return Turno.objects.get(id_turno=self.turno.id_turno)

    def assert_original_intacto(self):
        t = self.turno_en_base()
        self.assertEqual((t.fecha, t.hora_inicio, t.hora_fin, t.id_barbero_id, t.estado),
                         (self.manana, time(10, 0), time(10, 30), self.bo1.id_barbero, 'CONFIRMADO'))

    def test_reprogramacion_valida(self):
        r = self.reprogramar(fecha=self.pasado_manana, hora='14:00')
        self.assertEqual(r.status_code, 200, r.content)
        t = self.turno_en_base()
        self.assertEqual((t.fecha, t.hora_inicio, t.hora_fin), (self.pasado_manana, time(14, 0), time(14, 30)))
        self.assertEqual(t.estado, 'CONFIRMADO')
        self.assertEqual(t.monto_total, Decimal('1000.00'))
        self.assertEqual(Turno.objects.count(), 1)            # se movió, no se duplicó
        self.assertTrue(Notificacion.objects.filter(id_usuario=self.u_bo1, tipo='TURNO_REPROGRAMADO').exists())

    def test_la_duracion_del_servicio_se_respeta(self):
        t60 = crear_turno_directo(self.c2, self.bo2, self.s60, self.manana, time(10, 0))
        r = self.reprogramar(hora='16:00', turno=t60, http=cliente_http(self.c2))
        self.assertEqual(r.status_code, 200)
        self.assertEqual(Turno.objects.get(id_turno=t60.id_turno).hora_fin, time(17, 0))
        # 17:30 + 60 min se pasa del bloque (18:00)
        r = self.reprogramar(hora='17:30', turno=t60, http=cliente_http(self.c2))
        self.assertEqual(r.status_code, 400)

    def test_franja_ocupada_conserva_el_turno_original(self):
        crear_turno_directo(self.c2, self.bo1, self.s30, self.manana, time(11, 0))
        r = self.reprogramar(hora='11:00')
        self.assertEqual(r.status_code, 409)
        self.assert_original_intacto()

    def test_solapamiento_parcial_conserva_el_original(self):
        crear_turno_directo(self.c2, self.bo1, self.s30, self.manana, time(11, 0))
        self.assertEqual(self.reprogramar(hora='11:15').status_code, 409)
        self.assert_original_intacto()

    def test_puede_correrse_sobre_su_propio_horario(self):
        # 10:00-10:30 -> 10:15-10:45 se pisa solo con sí mismo: es válido.
        r = self.reprogramar(hora='10:15')
        self.assertEqual(r.status_code, 200, r.content)
        self.assertEqual(self.turno_en_base().hora_inicio, time(10, 15))

    def test_mismo_horario(self):
        r = self.reprogramar(hora='10:00')
        self.assertEqual(r.status_code, 400)
        self.assertIn('ya está en ese horario', r.json()['error'])

    def test_fuera_de_disponibilidad(self):
        self.assertEqual(self.reprogramar(hora='08:00').status_code, 400)
        self.assertEqual(self.reprogramar(hora='18:00').status_code, 400)
        self.assert_original_intacto()

    def test_fecha_pasada(self):
        self.assertEqual(self.reprogramar(fecha=dias_desde_hoy(-1)).status_code, 400)
        self.assert_original_intacto()

    def test_demasiado_adelante(self):
        r = self.reprogramar(fecha=dias_desde_hoy(reglas.MAX_DIAS_ANTICIPACION_RESERVA + 1))
        self.assertEqual(r.status_code, 400)
        self.assert_original_intacto()

    def test_cambiar_de_barbero_de_la_misma_barberia(self):
        r = self.reprogramar(barbero=self.bo2)
        self.assertEqual(r.status_code, 200, r.content)
        self.assertEqual(self.turno_en_base().id_barbero_id, self.bo2.id_barbero)
        # Se avisa al barbero nuevo y al que se liberó.
        self.assertTrue(Notificacion.objects.filter(id_usuario=self.u_bo2, tipo='TURNO_REPROGRAMADO').exists())
        self.assertTrue(Notificacion.objects.filter(id_usuario=self.u_bo1, tipo='TURNO_REPROGRAMADO').exists())

    def test_barbero_de_otra_barberia(self):
        r = self.reprogramar(barbero=self.bo3)
        self.assertEqual(r.status_code, 400)
        self.assert_original_intacto()

    def test_barbero_inexistente(self):
        r = patch_json(self.http, url_reprogramar(self.turno), {
            'fecha': str(self.manana), 'hora_inicio': '11:00', 'id_barbero': 99999})
        self.assertEqual(r.status_code, 404)
        self.assert_original_intacto()

    def test_barbero_inactivo(self):
        self.u_bo2.estado = 'INACTIVO'
        self.u_bo2.save()
        self.assertEqual(self.reprogramar(barbero=self.bo2).status_code, 400)
        self.assert_original_intacto()

    def test_turno_ajeno(self):
        r = self.reprogramar(http=cliente_http(self.c2))
        self.assertEqual(r.status_code, 403)
        self.assert_original_intacto()

    def test_turno_inexistente(self):
        r = patch_json(self.http, '/api/turnos/99999/reprogramar/', {'fecha': str(self.manana), 'hora_inicio': '11:00'})
        self.assertEqual(r.status_code, 404)

    def test_estados_que_no_se_pueden_reprogramar(self):
        for estado in ('CANCELADO', 'FINALIZADO', 'AUSENTE'):
            Turno.objects.filter(id_turno=self.turno.id_turno).update(estado=estado)
            self.assertEqual(self.reprogramar().status_code, 400, estado)
            self.assertEqual(self.turno_en_base().hora_inicio, time(10, 0))

    def test_fuera_del_plazo_de_cancelacion_tampoco_se_reprograma(self):
        with con_horas(48):
            r = self.reprogramar()
        self.assertEqual(r.status_code, 400)
        self.assertIn('reprogramar', r.json()['error'])
        self.assert_original_intacto()

    def test_cliente_bloqueado_no_puede_reprogramar(self):
        self.c1.estado = 'BLOQUEADO'
        self.c1.save()
        r = self.reprogramar()
        self.assertEqual(r.status_code, 403)
        self.assertIn('bloqueada', r.json()['error'])
        self.assert_original_intacto()

    def test_sin_sesion_metodo_y_cuerpo(self):
        self.assertEqual(self.reprogramar(http=cliente_http()).status_code, 401)
        self.assertEqual(self.http.get(url_reprogramar(self.turno)).status_code, 405)
        self.assertEqual(patch_json(self.http, url_reprogramar(self.turno), {'fecha': str(self.manana)}).status_code, 400)
        self.assertEqual(self.http.patch(url_reprogramar(self.turno), data='x', content_type='application/json').status_code, 400)
        self.assertEqual(self.reprogramar(hora='abc').status_code, 400)
        self.assert_original_intacto()

    def test_si_el_trigger_de_la_base_rechaza_el_turno_original_queda_igual(self):
        crear_turno_directo(self.c2, self.bo1, self.s30, self.manana, time(11, 0))
        with mock.patch.object(reglas, 'hay_solapamiento', return_value=False):
            r = self.reprogramar(hora='11:00')
        self.assertEqual(r.status_code, 409)
        self.assert_original_intacto()

    def test_el_horario_viejo_queda_libre_y_el_nuevo_ocupado(self):
        self.reprogramar(hora='14:00')
        h = cliente_http().get('/api/turnos/disponibles/', {
            'fecha': str(self.manana), 'barbero': self.bo1.id_barbero}).json()
        estados = {x['hora']: x['estado'] for x in h}
        self.assertEqual(estados['10:00'], 'DISPONIBLE')
        self.assertEqual(estados['14:00'], 'OCUPADO')


class ReprogramarConcurrenteTests(Escenario, TransactionTestCase):
    def setUp(self):
        limpiar_tablas()
        self.crear_escenario()

    def tearDown(self):
        limpiar_tablas()

    def test_dos_reprogramaciones_a_la_misma_franja(self):
        t1 = crear_turno_directo(self.c1, self.bo1, self.s30, self.manana, time(9, 0))
        t2 = crear_turno_directo(self.c2, self.bo1, self.s30, self.manana, time(9, 30))
        barrera = threading.Barrier(2)
        resultados = [None, None]

        def correr(i, turno, cliente):
            try:
                http = cliente_http(cliente)
                barrera.wait()
                resultados[i] = patch_json(http, url_reprogramar(turno), {
                    'fecha': str(self.manana), 'hora_inicio': '15:00'}).status_code
            except Exception as e:
                resultados[i] = repr(e)
            finally:
                connection.close()

        hilos = [threading.Thread(target=correr, args=(0, t1, self.c1)),
                 threading.Thread(target=correr, args=(1, t2, self.c2))]
        [h.start() for h in hilos]
        [h.join() for h in hilos]

        self.assertEqual(sorted(resultados), [200, 409], resultados)
        en_las_15 = Turno.objects.filter(id_barbero=self.bo1, hora_inicio=time(15, 0))
        self.assertEqual(en_las_15.count(), 1)

    def test_reprogramar_y_reservar_a_la_vez_la_misma_franja(self):
        propio = crear_turno_directo(self.c1, self.bo1, self.s30, self.manana, time(9, 0))
        barrera = threading.Barrier(2)
        resultados = [None, None]

        def reprogramar():
            try:
                http = cliente_http(self.c1)
                barrera.wait()
                resultados[0] = patch_json(http, url_reprogramar(propio), {
                    'fecha': str(self.manana), 'hora_inicio': '16:00'}).status_code
            except Exception as e:
                resultados[0] = repr(e)
            finally:
                connection.close()

        def reservar():
            try:
                http = cliente_http(self.c2)
                barrera.wait()
                import json
                resultados[1] = http.post('/api/turnos/', data=json.dumps({
                    'id_servicio': self.s30.id_servicio, 'id_barbero': self.bo1.id_barbero,
                    'fecha': str(self.manana), 'hora_inicio': '16:00'}), content_type='application/json').status_code
            except Exception as e:
                resultados[1] = repr(e)
            finally:
                connection.close()

        hilos = [threading.Thread(target=reprogramar), threading.Thread(target=reservar)]
        [h.start() for h in hilos]
        [h.join() for h in hilos]

        self.assertEqual(sorted(resultados), [200, 409], resultados)
        self.assertEqual(Turno.objects.filter(id_barbero=self.bo1, hora_inicio=time(16, 0)).count(), 1)
