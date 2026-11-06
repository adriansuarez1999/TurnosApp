from datetime import time
from django.test import TestCase
from apps.usuarios.models import Notificacion, Pago
from .models import Turno
from .helpers_tests import (
    Escenario, cliente_http, patch_json, post_json, crear_barbero, crear_turno_directo,
    dias_desde_hoy,
)


# ══════════════════════════════════════════
# Sprint 7 - Módulo E (Facundo): permisos y aislamiento entre barberías
# Roles probados: cliente, dueño, barbero, dueño-barbero y usuario sin sesión.
# Ningún usuario debe operar turnos, configuración o pagos de otra barbería.
# ══════════════════════════════════════════

class PermisosTests(Escenario, TestCase):
    def setUp(self):
        self.crear_escenario()
        # d1 es dueño de B1 y además atiende como barbero en B1 (dueño-barbero).
        self.bo_dueno = crear_barbero(self.d1, self.b1)
        from .helpers_tests import cargar_disponibilidad
        cargar_disponibilidad(self.bo_dueno)

        # Turnos de B1 (cliente c1) y de B2 (el mismo cliente c1 y c2)
        self.t_b1 = crear_turno_directo(self.c1, self.bo1, self.s30, self.manana, time(10, 0))
        self.t_b1_dueno = crear_turno_directo(self.c2, self.bo_dueno, self.s30, self.manana, time(12, 0))
        self.t_b2 = crear_turno_directo(self.c1, self.bo3, self.s_b2, self.manana, time(10, 0))
        self.t_b2_c2 = crear_turno_directo(self.c2, self.bo3, self.s_b2, self.manana, time(11, 0))

        self.rango = {'desde': str(dias_desde_hoy(0)), 'hasta': str(dias_desde_hoy(5))}

    # ---------- sin sesión ----------

    def test_sin_sesion_todo_devuelve_401(self):
        anonimo = cliente_http()
        get = [
            '/api/mis-turnos/', '/api/mi-barberia/clientes/', '/api/mi-barberia/informes/',
            '/api/mi-agenda/turnos/', '/api/mi-agenda/estadisticas/', '/api/notificaciones/',
            f'/api/mi-barberia/barberos/{self.bo1.id_barbero}/turnos/',
        ]
        for url in get:
            self.assertEqual(anonimo.get(url, self.rango).status_code, 401, url)
        patch = [
            f'/api/turnos/{self.t_b1.id_turno}/cancelar/',
            f'/api/turnos/{self.t_b1.id_turno}/reprogramar/',
            f'/api/mi-barberia/clientes/{self.c1.id_usuario}/bloquear/',
            f'/api/mi-agenda/turnos/{self.t_b1.id_turno}/finalizar/',
            f'/api/mi-agenda/turnos/{self.t_b1.id_turno}/ausente/',
            f'/api/mi-agenda/turnos/{self.t_b1.id_turno}/cancelar/',
        ]
        for url in patch:
            self.assertEqual(patch_json(anonimo, url).status_code, 401, url)
        self.assertEqual(post_json(anonimo, f'/api/mi-agenda/turnos/{self.t_b1.id_turno}/cobro/', {}).status_code, 401)
        self.assertEqual(post_json(anonimo, '/api/turnos/', {}).status_code, 401)

    # ---------- cliente (sin barbería ni barbero) ----------

    def test_cliente_no_accede_a_paneles_de_dueno_ni_barbero(self):
        http = cliente_http(self.c1)
        self.assertEqual(http.get('/api/mi-barberia/clientes/').status_code, 404)
        self.assertEqual(http.get('/api/mi-barberia/informes/').status_code, 404)
        self.assertEqual(http.get('/api/mi-barberia/barberos/').status_code, 404)
        self.assertEqual(patch_json(http, f'/api/mi-barberia/clientes/{self.c2.id_usuario}/bloquear/').status_code, 404)
        self.assertEqual(http.get(f'/api/mi-barberia/barberos/{self.bo1.id_barbero}/turnos/', self.rango).status_code, 404)
        self.assertEqual(http.get('/api/mi-agenda/turnos/', self.rango).status_code, 403)
        self.assertEqual(http.get('/api/mi-agenda/estadisticas/').status_code, 403)
        for accion in ('finalizar', 'ausente', 'cancelar'):
            self.assertEqual(patch_json(http, f'/api/mi-agenda/turnos/{self.t_b1.id_turno}/{accion}/').status_code, 403, accion)
        self.assertEqual(post_json(http, f'/api/mi-agenda/turnos/{self.t_b1.id_turno}/cobro/',
                                   {'metodo_pago': 'EFECTIVO'}).status_code, 403)
        self.assertEqual(Pago.objects.count(), 0)

    def test_cliente_ve_solo_sus_turnos(self):
        datos = cliente_http(self.c1).get('/api/mis-turnos/').json()
        self.assertEqual({t['id'] for t in datos}, {self.t_b1.id_turno, self.t_b2.id_turno})

    def test_cliente_no_opera_turnos_ajenos(self):
        http = cliente_http(self.c2)
        self.assertEqual(patch_json(http, f'/api/turnos/{self.t_b1.id_turno}/cancelar/').status_code, 403)
        self.assertEqual(patch_json(http, f'/api/turnos/{self.t_b1.id_turno}/reprogramar/',
                                    {'fecha': str(self.manana), 'hora_inicio': '15:00'}).status_code, 403)
        self.assertEqual(post_json(http, f'/api/turnos/{self.t_b1.id_turno}/calificar/', {'puntuacion': 5}).status_code, 403)
        self.assertEqual(Turno.objects.get(id_turno=self.t_b1.id_turno).estado, 'CONFIRMADO')

    # ---------- dueño ----------

    def test_dueno_ve_solo_los_clientes_de_su_barberia(self):
        datos = cliente_http(self.d1).get('/api/mi-barberia/clientes/').json()
        por_id = {c['id_usuario']: c for c in datos['clientes']}
        self.assertEqual(set(por_id), {self.c1.id_usuario, self.c2.id_usuario})
        # c1 tiene un turno en B1 y otro en B2: el dueño de B1 solo cuenta el suyo.
        self.assertEqual(por_id[self.c1.id_usuario]['turnos_totales'], 1)

    def test_dueno_no_bloquea_clientes_que_nunca_reservaron_en_su_barberia(self):
        from .helpers_tests import crear_usuario
        ajeno = crear_usuario('ajeno@t.com')
        r = patch_json(cliente_http(self.d1), f'/api/mi-barberia/clientes/{ajeno.id_usuario}/bloquear/')
        self.assertEqual(r.status_code, 403)

    def test_dueno_no_ve_el_calendario_de_barberos_de_otra_barberia(self):
        r = cliente_http(self.d1).get(f'/api/mi-barberia/barberos/{self.bo3.id_barbero}/turnos/', self.rango)
        self.assertEqual(r.status_code, 403)
        r = cliente_http(self.d2).get(f'/api/mi-barberia/barberos/{self.bo1.id_barbero}/turnos/', self.rango)
        self.assertEqual(r.status_code, 403)

    def test_dueno_no_toca_barberos_ni_disponibilidad_de_otra_barberia(self):
        http = cliente_http(self.d2)
        self.assertEqual(http.get(f'/api/mi-barberia/barberos/{self.bo1.id_barbero}/').status_code in (403, 404, 405), True)
        self.assertEqual(http.get(f'/api/mi-barberia/barberos/{self.bo1.id_barbero}/disponibilidad/').status_code, 403)
        self.assertEqual(post_json(http, f'/api/mi-barberia/barberos/{self.bo1.id_barbero}/disponibilidad/', {
            'dia_semana': 'LUN', 'hora_inicio': '01:00', 'hora_fin': '02:00'}).status_code, 403)

    def test_informes_de_cada_dueno_son_solo_de_su_barberia(self):
        r1 = cliente_http(self.d1).get('/api/mi-barberia/informes/').json()
        r2 = cliente_http(self.d2).get('/api/mi-barberia/informes/').json()
        self.assertEqual(sum(e['cantidad'] for e in r1['turnos_por_estado']), 2)   # t_b1 y t_b1_dueno
        self.assertEqual(sum(e['cantidad'] for e in r2['turnos_por_estado']), 2)   # t_b2 y t_b2_c2
        self.assertEqual(r2['barberia'], 'Barbería Dos')

    def test_dueno_bloquea_y_el_cliente_queda_bloqueado_en_el_servidor(self):
        r = patch_json(cliente_http(self.d1), f'/api/mi-barberia/clientes/{self.c1.id_usuario}/bloquear/')
        self.assertEqual(r.status_code, 200)
        # Reservar y reprogramar (los dos caminos que crean/mueven turnos) quedan rechazados.
        http = cliente_http(self.c1)
        self.assertEqual(post_json(http, '/api/turnos/', {
            'id_servicio': self.s30.id_servicio, 'id_barbero': self.bo1.id_barbero,
            'fecha': str(self.manana), 'hora_inicio': '13:00'}).status_code, 403)
        self.assertEqual(patch_json(http, f'/api/turnos/{self.t_b1.id_turno}/reprogramar/', {
            'fecha': str(self.manana), 'hora_inicio': '13:00'}).status_code, 403)
        self.assertEqual(Turno.objects.get(id_turno=self.t_b1.id_turno).hora_inicio, time(10, 0))
        # Al desbloquear vuelve a poder.
        patch_json(cliente_http(self.d1), f'/api/mi-barberia/clientes/{self.c1.id_usuario}/desbloquear/')
        self.assertEqual(post_json(http, '/api/turnos/', {
            'id_servicio': self.s30.id_servicio, 'id_barbero': self.bo1.id_barbero,
            'fecha': str(self.manana), 'hora_inicio': '13:00'}).status_code, 200)

    # ---------- barbero ----------

    def test_barbero_solo_ve_y_opera_su_agenda(self):
        http = cliente_http(self.u_bo1)
        ids = {t['id'] for t in http.get('/api/mi-agenda/turnos/', self.rango).json()['turnos']}
        self.assertEqual(ids, {self.t_b1.id_turno})
        # Turno de un compañero de la misma barbería y turno de otra barbería.
        for turno in (self.t_b1_dueno, self.t_b2):
            for accion in ('finalizar', 'ausente', 'cancelar'):
                self.assertEqual(patch_json(http, f'/api/mi-agenda/turnos/{turno.id_turno}/{accion}/').status_code, 403)
            self.assertEqual(post_json(http, f'/api/mi-agenda/turnos/{turno.id_turno}/cobro/',
                                       {'metodo_pago': 'EFECTIVO'}).status_code, 403)

    def test_barbero_no_ve_el_historial_de_clientes_que_no_atiende(self):
        http = cliente_http(self.u_bo1)
        self.assertEqual(http.get(f'/api/mi-agenda/clientes/{self.c2.id_usuario}/historial/').status_code, 403)
        self.assertEqual(http.get(f'/api/mi-agenda/clientes/{self.c1.id_usuario}/historial/').status_code, 200)

    def test_barbero_no_accede_al_panel_del_dueno(self):
        http = cliente_http(self.u_bo1)
        self.assertEqual(http.get('/api/mi-barberia/clientes/').status_code, 404)
        self.assertEqual(http.get('/api/mi-barberia/informes/').status_code, 404)
        self.assertEqual(patch_json(http, f'/api/mi-barberia/clientes/{self.c1.id_usuario}/bloquear/').status_code, 404)

    def test_cobro_solo_al_barbero_del_turno_y_una_vez(self):
        Turno.objects.filter(id_turno=self.t_b1.id_turno).update(estado='FINALIZADO')
        # otro barbero de la misma barbería no puede cobrarlo
        self.assertEqual(post_json(cliente_http(self.u_bo2), f'/api/mi-agenda/turnos/{self.t_b1.id_turno}/cobro/',
                                   {'metodo_pago': 'EFECTIVO'}).status_code, 403)
        self.assertEqual(Pago.objects.count(), 0)
        http = cliente_http(self.u_bo1)
        self.assertEqual(post_json(http, f'/api/mi-agenda/turnos/{self.t_b1.id_turno}/cobro/',
                                   {'metodo_pago': 'TRANSFERENCIA'}).status_code, 201)
        self.assertEqual(post_json(http, f'/api/mi-agenda/turnos/{self.t_b1.id_turno}/cobro/',
                                   {'metodo_pago': 'EFECTIVO'}).status_code, 409)
        self.assertEqual(Pago.objects.count(), 1)

    def test_cobro_rechaza_metodos_online(self):
        Turno.objects.filter(id_turno=self.t_b1.id_turno).update(estado='FINALIZADO')
        http = cliente_http(self.u_bo1)
        for metodo in ('MERCADOPAGO', 'TARJETA', '', None):
            r = post_json(http, f'/api/mi-agenda/turnos/{self.t_b1.id_turno}/cobro/', {'metodo_pago': metodo})
            self.assertEqual(r.status_code, 400, metodo)
        self.assertEqual(Pago.objects.count(), 0)

    # ---------- dueño-barbero ----------

    def test_dueno_barbero_usa_los_dos_paneles_pero_solo_de_su_barberia(self):
        http = cliente_http(self.d1)
        # Panel de barbero: solo sus turnos como barbero.
        ids = {t['id'] for t in http.get('/api/mi-agenda/turnos/', self.rango).json()['turnos']}
        self.assertEqual(ids, {self.t_b1_dueno.id_turno})
        # Panel de dueño: ve el calendario de todos los barberos de B1...
        self.assertEqual(http.get(f'/api/mi-barberia/barberos/{self.bo1.id_barbero}/turnos/', self.rango).status_code, 200)
        # ...pero nada de B2.
        self.assertEqual(http.get(f'/api/mi-barberia/barberos/{self.bo3.id_barbero}/turnos/', self.rango).status_code, 403)
        # Y como barbero no opera los turnos de otros barberos, ni siquiera de su barbería.
        self.assertEqual(patch_json(http, f'/api/mi-agenda/turnos/{self.t_b1.id_turno}/finalizar/').status_code, 403)
        self.assertEqual(patch_json(http, f'/api/mi-agenda/turnos/{self.t_b2.id_turno}/finalizar/').status_code, 403)

    # ---------- notificaciones ----------

    def test_notificaciones_ajenas(self):
        from datetime import datetime
        n = Notificacion.objects.create(id_usuario=self.c2, tipo='X', mensaje='m', fecha_envio=datetime.now(), estado='PENDIENTE')
        self.assertEqual(patch_json(cliente_http(self.c1), f'/api/notificaciones/{n.id_notificacion}/leida/').status_code, 403)
        self.assertEqual(Notificacion.objects.get(id_notificacion=n.id_notificacion).estado, 'PENDIENTE')
        self.assertEqual(cliente_http(self.c1).get('/api/notificaciones/').json()['notificaciones'], [])
