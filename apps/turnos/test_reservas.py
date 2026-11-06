import threading
from datetime import time
from unittest import mock
from django.db import connection
from django.test import TestCase, TransactionTestCase
from apps.usuarios.models import Disponibilidad
from . import reglas
from .models import Turno
from .helpers_tests import (
    Escenario, cliente_http, post_json, crear_usuario, crear_turno_directo,
    dias_desde_hoy, limpiar_tablas, crear_servicio,
)

URL = '/api/turnos/'


# ══════════════════════════════════════════
# Sprint 7 - Módulo A (Facundo): pruebas de reservas confiables
# ══════════════════════════════════════════

class CrearTurnoTests(Escenario, TestCase):
    def setUp(self):
        self.crear_escenario()
        self.http = cliente_http(self.c1)

    def reservar(self, servicio=None, barbero='bo1', fecha=None, hora='10:00', http=None):
        datos = {
            'id_servicio': (servicio or self.s30).id_servicio,
            'fecha': str(fecha or self.manana),
            'hora_inicio': hora,
        }
        if barbero:
            datos['id_barbero'] = getattr(self, barbero).id_barbero
        return post_json(http or self.http, URL, datos)

    def test_reserva_valida(self):
        r = self.reservar()
        self.assertEqual(r.status_code, 200, r.content)
        datos = r.json()
        self.assertTrue(datos['ok'])
        self.assertEqual(datos['hora_fin'], '10:30')
        self.assertEqual(datos['estado'], 'CONFIRMADO')
        self.assertEqual(Turno.objects.count(), 1)

    def test_sin_sesion(self):
        r = self.reservar(http=cliente_http())
        self.assertEqual(r.status_code, 401)

    def test_metodo_no_permitido(self):
        self.assertEqual(self.http.get(URL).status_code, 405)

    # --- relación entre entidades ---

    def test_barbero_de_otra_barberia(self):
        r = self.reservar(barbero='bo3')
        self.assertEqual(r.status_code, 400)
        self.assertIn('no pertenece', r.json()['error'])
        self.assertEqual(Turno.objects.count(), 0)

    def test_servicio_de_otra_barberia(self):
        r = self.reservar(servicio=self.s_b2, barbero='bo1')
        self.assertEqual(r.status_code, 400)
        self.assertEqual(Turno.objects.count(), 0)

    def test_servicio_inactivo(self):
        self.s30.estado = 0
        self.s30.save()
        r = self.reservar()
        self.assertEqual(r.status_code, 400)
        self.assertIn('servicio', r.json()['error'].lower())

    def test_barbero_inactivo(self):
        self.u_bo1.estado = 'INACTIVO'
        self.u_bo1.save()
        r = self.reservar()
        self.assertEqual(r.status_code, 400)

    def test_barberia_inactiva(self):
        self.b1.estado = 'INACTIVA'
        self.b1.save()
        r = self.reservar()
        self.assertEqual(r.status_code, 400)

    def test_ids_inexistentes(self):
        self.assertEqual(post_json(self.http, URL, {
            'id_servicio': 99999, 'fecha': str(self.manana), 'hora_inicio': '10:00'}).status_code, 404)
        self.assertEqual(post_json(self.http, URL, {
            'id_servicio': self.s30.id_servicio, 'id_barbero': 99999,
            'fecha': str(self.manana), 'hora_inicio': '10:00'}).status_code, 404)

    # --- fechas y disponibilidad ---

    def test_fecha_pasada(self):
        r = self.reservar(fecha=dias_desde_hoy(-1))
        self.assertEqual(r.status_code, 400)
        self.assertIn('pasada', r.json()['error'])

    def test_demasiado_adelante(self):
        r = self.reservar(fecha=dias_desde_hoy(reglas.MAX_DIAS_ANTICIPACION_RESERVA + 1))
        self.assertEqual(r.status_code, 400)

    def test_fuera_de_disponibilidad(self):
        self.assertEqual(self.reservar(hora='08:00').status_code, 400)
        self.assertEqual(self.reservar(hora='18:00').status_code, 400)

    def test_el_servicio_completo_tiene_que_entrar_en_el_bloque(self):
        # Bloque hasta las 18:00: un servicio de 60 min no puede empezar 17:30.
        r = self.reservar(servicio=self.s60, hora='17:30')
        self.assertEqual(r.status_code, 400)
        self.assertEqual(self.reservar(servicio=self.s60, hora='17:00').status_code, 200)

    def test_barbero_sin_disponibilidad_ese_dia(self):
        Disponibilidad.objects.filter(id_barbero=self.bo1).delete()
        r = self.reservar()
        self.assertEqual(r.status_code, 400)
        self.assertIn('no atiende', r.json()['error'])

    def test_el_turno_no_puede_cruzar_la_medianoche(self):
        self.assertIsNone(reglas.calcular_hora_fin(self.manana, time(23, 30), 60))
        self.assertEqual(reglas.calcular_hora_fin(self.manana, time(10, 0), 30), time(10, 30))

    def test_formatos_invalidos(self):
        for cuerpo in (
            {'id_servicio': self.s30.id_servicio, 'fecha': '2026-13-45', 'hora_inicio': '10:00'},
            {'id_servicio': self.s30.id_servicio, 'fecha': str(self.manana), 'hora_inicio': 'abc'},
            {'id_servicio': 'xx', 'fecha': str(self.manana), 'hora_inicio': '10:00'},
            {'id_servicio': self.s30.id_servicio, 'id_barbero': 'xx', 'fecha': str(self.manana), 'hora_inicio': '10:00'},
        ):
            r = post_json(self.http, URL, cuerpo)
            self.assertEqual(r.status_code, 400, cuerpo)
            self.assertNotIn('Traceback', r.json()['error'])

    def test_faltan_campos_y_json_invalido(self):
        self.assertEqual(post_json(self.http, URL, {'fecha': str(self.manana)}).status_code, 400)
        self.assertEqual(self.http.post(URL, data='no es json', content_type='application/json').status_code, 400)
        self.assertEqual(post_json(self.http, URL, [1, 2]).status_code, 400)

    # --- solapamientos ---

    def test_misma_franja_ocupada(self):
        self.assertEqual(self.reservar().status_code, 200)
        r = self.reservar(http=cliente_http(self.c2))
        self.assertEqual(r.status_code, 409)
        self.assertEqual(Turno.objects.count(), 1)

    def test_solapamiento_parcial(self):
        self.reservar(hora='10:00')                       # 10:00-10:30
        self.assertEqual(self.reservar(hora='10:15', http=cliente_http(self.c2)).status_code, 409)
        self.assertEqual(self.reservar(hora='09:45', http=cliente_http(self.c2)).status_code, 409)

    def test_turnos_contiguos_no_se_solapan(self):
        self.assertEqual(self.reservar(hora='10:00').status_code, 200)
        self.assertEqual(self.reservar(hora='10:30', http=cliente_http(self.c2)).status_code, 200)
        self.assertEqual(self.reservar(hora='09:30', http=cliente_http(self.c2)).status_code, 200)

    def test_la_reserva_ocupa_toda_la_duracion(self):
        self.assertEqual(self.reservar(servicio=self.s60, hora='10:00').status_code, 200)   # 10:00-11:00
        self.assertEqual(self.reservar(hora='10:30', http=cliente_http(self.c2)).status_code, 409)
        self.assertEqual(self.reservar(hora='11:00', http=cliente_http(self.c2)).status_code, 200)

    def test_turno_cancelado_libera_el_horario(self):
        crear_turno_directo(self.c2, self.bo1, self.s30, self.manana, time(10, 0), estado='CANCELADO')
        self.assertEqual(self.reservar().status_code, 200)

    def test_mismo_horario_con_otro_barbero(self):
        self.assertEqual(self.reservar(barbero='bo1').status_code, 200)
        self.assertEqual(self.reservar(barbero='bo2', http=cliente_http(self.c2)).status_code, 200)

    def test_el_trigger_de_la_base_frena_un_solapamiento_que_se_escapa(self):
        crear_turno_directo(self.c2, self.bo1, self.s30, self.manana, time(10, 0))
        with mock.patch.object(reglas, 'hay_solapamiento', return_value=False):
            r = self.reservar()
        self.assertEqual(r.status_code, 409)
        self.assertEqual(Turno.objects.count(), 1)

    # --- asignación automática ---

    def test_asignacion_automatica_salta_al_barbero_ocupado(self):
        crear_turno_directo(self.c2, self.bo1, self.s30, self.manana, time(10, 0))
        r = self.reservar(barbero=None)
        self.assertEqual(r.status_code, 200, r.content)
        self.assertEqual(r.json()['id_barbero'], self.bo2.id_barbero)

    def test_asignacion_automatica_sin_barberos_libres(self):
        crear_turno_directo(self.c2, self.bo1, self.s30, self.manana, time(10, 0))
        crear_turno_directo(self.c2, self.bo2, self.s30, self.manana, time(10, 0))
        self.assertEqual(self.reservar(barbero=None).status_code, 409)

    def test_asignacion_automatica_nunca_elige_barbero_de_otra_barberia(self):
        # Solo bo3 (de B2) está libre ese día: no puede quedar con un servicio de B1.
        Disponibilidad.objects.filter(id_barbero__in=[self.bo1, self.bo2]).delete()
        r = self.reservar(barbero=None)
        self.assertEqual(r.status_code, 409)
        self.assertEqual(Turno.objects.count(), 0)

    # --- clientes bloqueados ---

    def test_cliente_bloqueado_no_puede_reservar(self):
        self.c1.estado = 'BLOQUEADO'
        self.c1.save()
        r = self.reservar()
        self.assertEqual(r.status_code, 403)
        self.assertIn('bloqueada', r.json()['error'])
        self.assertEqual(Turno.objects.count(), 0)

    def test_cliente_inactivo_no_puede_reservar(self):
        self.c1.estado = 'INACTIVO'
        self.c1.save()
        self.assertEqual(self.reservar().status_code, 403)

    def test_cliente_desbloqueado_vuelve_a_reservar(self):
        self.c1.estado = 'BLOQUEADO'
        self.c1.save()
        self.assertEqual(self.reservar().status_code, 403)
        self.c1.estado = 'ACTIVO'
        self.c1.save()
        self.assertEqual(self.reservar().status_code, 200)

    # --- promociones (Sprint 5) siguen funcionando ---

    def test_la_promocion_sigue_aplicandose(self):
        from apps.usuarios.models import Promocion
        Promocion.objects.create(
            id_servicio=self.s30, nombre='Promo', porcentaje_descuento=10,
            fecha_inicio=dias_desde_hoy(-1), fecha_fin=dias_desde_hoy(10), activa=1,
        )
        self.assertEqual(self.reservar().json()['monto_total'], 900.0)


class DisponiblesTests(Escenario, TestCase):
    def setUp(self):
        self.crear_escenario()
        self.http = cliente_http()

    def pedir(self, **params):
        params.setdefault('fecha', str(self.manana))
        return self.http.get('/api/turnos/disponibles/', params)

    def horarios(self, r):
        return {h['hora']: h for h in r.json()}

    def test_estados_disponible_y_ocupado(self):
        crear_turno_directo(self.c1, self.bo1, self.s30, self.manana, time(10, 0))
        h = self.horarios(self.pedir(barbero=self.bo1.id_barbero))
        self.assertEqual(h['09:00']['estado'], 'DISPONIBLE')
        self.assertTrue(h['09:00']['disponible'])
        self.assertEqual(h['10:00']['estado'], 'OCUPADO')
        self.assertFalse(h['10:00']['disponible'])

    def test_con_servicio_se_valida_la_duracion_completa(self):
        crear_turno_directo(self.c1, self.bo1, self.s30, self.manana, time(10, 30))
        h = self.horarios(self.pedir(barbero=self.bo1.id_barbero, servicio=self.s60.id_servicio))
        self.assertEqual(h['10:00']['estado'], 'OCUPADO')        # 10:00-11:00 pisa el de 10:30
        self.assertEqual(h['09:00']['estado'], 'DISPONIBLE')
        self.assertEqual(h['17:30']['estado'], 'NO_PERMITIDO')   # 17:30-18:30 no entra en el bloque

    def test_dia_pasado_todo_no_permitido(self):
        h = self.horarios(self.pedir(barbero=self.bo1.id_barbero, fecha=str(dias_desde_hoy(-1))))
        self.assertTrue(h)
        self.assertEqual({x['estado'] for x in h.values()}, {'NO_PERMITIDO'})

    def test_dia_demasiado_adelante_no_permitido(self):
        fecha = str(dias_desde_hoy(reglas.MAX_DIAS_ANTICIPACION_RESERVA + 1))
        h = self.horarios(self.pedir(barbero=self.bo1.id_barbero, fecha=fecha))
        self.assertEqual({x['estado'] for x in h.values()}, {'NO_PERMITIDO'})

    def test_excluir_turno_para_reprogramar(self):
        propio = crear_turno_directo(self.c1, self.bo1, self.s30, self.manana, time(10, 0))
        h = self.horarios(self.pedir(barbero=self.bo1.id_barbero, excluir_turno=propio.id_turno))
        self.assertEqual(h['10:00']['estado'], 'DISPONIBLE')

    def test_turno_cancelado_no_ocupa(self):
        crear_turno_directo(self.c1, self.bo1, self.s30, self.manana, time(10, 0), estado='CANCELADO')
        h = self.horarios(self.pedir(barbero=self.bo1.id_barbero))
        self.assertEqual(h['10:00']['estado'], 'DISPONIBLE')

    def test_por_barberia_libre_si_algun_barbero_esta_libre(self):
        crear_turno_directo(self.c1, self.bo1, self.s30, self.manana, time(10, 0))
        h = self.horarios(self.pedir(barberia=self.b1.id_barberia))
        self.assertEqual(h['10:00']['estado'], 'DISPONIBLE')     # bo2 sigue libre
        crear_turno_directo(self.c1, self.bo2, self.s30, self.manana, time(10, 0))
        h = self.horarios(self.pedir(barberia=self.b1.id_barberia))
        self.assertEqual(h['10:00']['estado'], 'OCUPADO')

    def test_barbero_inactivo_no_ofrece_horarios(self):
        self.u_bo1.estado = 'INACTIVO'
        self.u_bo1.save()
        self.assertEqual(self.pedir(barbero=self.bo1.id_barbero).json(), [])

    def test_coincide_con_lo_que_acepta_crear_turno(self):
        # Todo horario DISPONIBLE debe poder reservarse, y ninguno que no lo sea.
        crear_turno_directo(self.c2, self.bo1, self.s30, self.manana, time(10, 0))
        horarios = self.horarios(self.pedir(barbero=self.bo1.id_barbero, servicio=self.s60.id_servicio)).values()
        http = cliente_http(self.c1)
        for h in horarios:
            r = post_json(http, URL, {
                'id_servicio': self.s60.id_servicio, 'id_barbero': self.bo1.id_barbero,
                'fecha': str(self.manana), 'hora_inicio': h['hora']})
            if h['estado'] == 'DISPONIBLE':
                self.assertEqual(r.status_code, 200, h)
                Turno.objects.all().exclude(id_cliente=self.c2).delete()
            else:
                self.assertIn(r.status_code, (400, 409), h)


# ══════════════════════════════════════════
# Concurrencia: requests simultáneos reales contra la base.
# TransactionTestCase porque cada hilo necesita ver lo que confirmó el otro.
# ══════════════════════════════════════════

class ConcurrenciaTests(Escenario, TransactionTestCase):
    def setUp(self):
        limpiar_tablas()
        self.crear_escenario()
        self.clientes = [crear_usuario(f'conc{i}@t.com') for i in range(8)]

    def tearDown(self):
        limpiar_tablas()

    def disparar(self, tareas):
        # Todas las tareas arrancan a la vez (barrera) y devuelven el status.
        barrera = threading.Barrier(len(tareas))
        resultados = [None] * len(tareas)

        def correr(i, tarea):
            try:
                barrera.wait()
                resultados[i] = tarea()
            except Exception as e:   # un hilo roto tiene que hacer fallar el test
                resultados[i] = repr(e)
            finally:
                connection.close()

        hilos = [threading.Thread(target=correr, args=(i, t)) for i, t in enumerate(tareas)]
        for h in hilos:
            h.start()
        for h in hilos:
            h.join()
        return resultados

    def test_ocho_pedidos_a_la_vez_para_la_misma_franja(self):
        def reservar(cliente):
            def tarea():
                r = post_json(cliente_http(cliente), URL, {
                    'id_servicio': self.s30.id_servicio, 'id_barbero': self.bo1.id_barbero,
                    'fecha': str(self.manana), 'hora_inicio': '10:00'})
                return r.status_code
            return tarea

        resultados = self.disparar([reservar(c) for c in self.clientes])
        self.assertEqual(sorted(resultados), [200] + [409] * 7, resultados)
        self.assertEqual(Turno.objects.filter(id_barbero=self.bo1).count(), 1)

    def test_pedidos_simultaneos_superpuestos_no_dejan_turnos_encimados(self):
        horas = ['10:00', '10:15', '10:30', '10:45', '10:00', '10:15', '10:30', '10:45']

        def reservar(cliente, hora):
            def tarea():
                return post_json(cliente_http(cliente), URL, {
                    'id_servicio': self.s30.id_servicio, 'id_barbero': self.bo1.id_barbero,
                    'fecha': str(self.manana), 'hora_inicio': hora}).status_code
            return tarea

        resultados = self.disparar([reservar(c, h) for c, h in zip(self.clientes, horas)])
        self.assertTrue(all(r in (200, 409) for r in resultados), resultados)
        turnos = list(Turno.objects.filter(id_barbero=self.bo1).order_by('hora_inicio'))
        self.assertTrue(turnos)
        for anterior, siguiente in zip(turnos, turnos[1:]):
            self.assertLessEqual(anterior.hora_fin, siguiente.hora_inicio)

    def test_asignacion_automatica_simultanea_reparte_entre_barberos(self):
        def reservar(cliente):
            def tarea():
                r = post_json(cliente_http(cliente), URL, {
                    'id_servicio': self.s30.id_servicio, 'fecha': str(self.manana), 'hora_inicio': '11:00'})
                return r.status_code
            return tarea

        resultados = self.disparar([reservar(c) for c in self.clientes[:5]])
        self.assertEqual(sorted(resultados), [200, 200, 409, 409, 409], resultados)
        self.assertEqual(Turno.objects.filter(hora_inicio=time(11, 0)).values('id_barbero').distinct().count(), 2)
