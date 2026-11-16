import json
import re
from datetime import date, datetime, timedelta
from django.db import connection
from django.contrib.auth.hashers import make_password
from django.test import Client, TestCase
from apps.barberias.models import Barberia
from apps.turnos.models import Turno
from apps.usuarios.models import Barbero, Pago, PlanSuscripcion, Servicio, Suscripcion, Usuario

# ══════════════════════════════════════════
# Tests del panel del superadministrador. Corren con el runner del Sprint 7.
# Los valores de los ENUM que no son seguros (estado de suscripción) se leen de
# la base de prueba.
# ══════════════════════════════════════════


def _valores_enum(tabla, columna):
    with connection.cursor() as cursor:
        cursor.execute(f'SHOW COLUMNS FROM {tabla} LIKE %s', [columna])
        tipo = cursor.fetchone()[1]
    if isinstance(tipo, bytes):
        tipo = tipo.decode()
    return re.findall(r"'([^']*)'", tipo)


class SuperadminBase(TestCase):
    _contador = 0

    def _usuario(self, rol, estado='ACTIVO'):
        SuperadminBase._contador += 1
        return Usuario.objects.create(
            nombre='Nombre', apellido='Apellido',
            email=f'sa{SuperadminBase._contador}@test.com', telefono='1100000000',
            password='x', rol=rol, estado=estado, fecha_registro=datetime.now(),
        )

    def _barberia(self, nombre):
        dueno = self._usuario('DUENO')
        barberia = Barberia.objects.create(
            id_dueno=dueno, nombre=nombre, direccion='Calle 1', zona='Centro', estado='ACTIVA')
        usuario_barbero = self._usuario('BARBERO')
        barbero = Barbero.objects.create(id_usuario=usuario_barbero, id_barberia=barberia, promedio_calificacion=0)
        servicio = Servicio.objects.create(
            id_barberia=barberia, nombre='Corte', precio=1000, duracion_minutos=30, estado=1)
        return dueno, barberia, barbero, servicio

    def _turno(self, barbero, servicio, cliente, fecha, estado='FINALIZADO', hora=10, monto=1000, cobrado=True):
        ahora = datetime.now()
        turno = Turno.objects.create(
            id_cliente=cliente, id_barbero=barbero, id_servicio=servicio, fecha=fecha,
            hora_inicio=f'{hora:02d}:00', hora_fin=f'{hora:02d}:30', estado=estado,
            monto_total=monto, fecha_reserva=ahora, created_at=ahora, updated_at=ahora,
        )
        if cobrado:
            Pago.objects.create(
                id_turno=turno, fecha_pago=ahora, monto=monto, metodo_pago='EFECTIVO',
                estado='APROBADO', tipo_pago='TOTAL', created_at=ahora, updated_at=ahora,
            )
        return turno

    def _http(self, usuario=None):
        cliente = Client()
        if usuario:
            sesion = cliente.session
            sesion['id_usuario'] = usuario.id_usuario
            sesion.save()
        return cliente

    def _patch(self, http, url, datos=None):
        return http.patch(url, data=json.dumps(datos or {}), content_type='application/json')

    def setUp(self):
        self.admin = self._usuario('ADMIN')
        self.http = self._http(self.admin)
        self.dueno_a, self.barberia_a, self.barbero_a, self.servicio_a = self._barberia('Barbería A')
        self.dueno_b, self.barberia_b, self.barbero_b, self.servicio_b = self._barberia('Barbería B')
        self.cliente = self._usuario('CLIENTE')


class AccesoSuperadminTest(SuperadminBase):
    URLS = ['/api/superadmin/resumen/', '/api/superadmin/ingresos/',
            '/api/superadmin/barberias/', '/api/superadmin/suscripciones/']

    def test_sin_sesion_responde_401(self):
        for url in self.URLS:
            self.assertEqual(self._http().get(url).status_code, 401, url)

    def test_los_otros_roles_responden_403(self):
        for usuario in (self.cliente, self.dueno_a, self.barbero_a.id_usuario):
            for url in self.URLS:
                self.assertEqual(self._http(usuario).get(url).status_code, 403, url)

    def test_el_bloqueo_tambien_esta_protegido(self):
        url = f'/api/superadmin/barberias/{self.barberia_a.id_barberia}/bloquear/'
        self.assertEqual(self._patch(self._http(), url, {'motivo': 'x'}).status_code, 401)
        self.assertEqual(self._patch(self._http(self.dueno_a), url, {'motivo': 'x'}).status_code, 403)
        self.assertEqual(Barberia.objects.get(id_barberia=self.barberia_a.id_barberia).estado, 'ACTIVA')

    def test_un_admin_bloqueado_o_inactivo_pierde_el_acceso(self):
        Usuario.objects.filter(id_usuario=self.admin.id_usuario).update(estado='BLOQUEADO')
        self.assertEqual(self.http.get('/api/superadmin/resumen/').status_code, 403)

    def test_el_rol_se_verifica_en_la_base_y_no_en_la_sesion(self):
        sesion = self.http.session
        sesion['rol'] = 'ADMIN'
        sesion.save()
        otro = self._http(self.cliente)
        sesion = otro.session
        sesion['rol'] = 'ADMIN'  # sesión adulterada
        sesion.save()
        self.assertEqual(otro.get('/api/superadmin/resumen/').status_code, 403)


class IngresosSuperadminTest(SuperadminBase):
    def setUp(self):
        super().setUp()
        hoy = date.today()
        self._turno(self.barbero_a, self.servicio_a, self.cliente, hoy, hora=10, monto=1000)
        self._turno(self.barbero_a, self.servicio_a, self.cliente, hoy, hora=11, monto=500)
        self._turno(self.barbero_b, self.servicio_b, self.cliente, hoy, hora=10, monto=300)
        # No suman: finalizado sin cobro, ausente y cancelado.
        self._turno(self.barbero_a, self.servicio_a, self.cliente, hoy, hora=12, monto=999, cobrado=False)
        self._turno(self.barbero_a, self.servicio_a, self.cliente, hoy, estado='AUSENTE', hora=13, monto=999, cobrado=False)
        self._turno(self.barbero_b, self.servicio_b, self.cliente, hoy, estado='CANCELADO', hora=13, monto=999, cobrado=False)

    def test_el_total_solo_suma_cobros_confirmados(self):
        r = self.http.get('/api/superadmin/ingresos/').json()
        self.assertEqual(r['total'], 1800.0)
        self.assertEqual(r['cobros_registrados'], 3)

    def test_ranking_por_barberia_ordenado(self):
        r = self.http.get('/api/superadmin/ingresos/').json()
        self.assertEqual([(f['barberia'], f['total']) for f in r['por_barberia']],
                         [('Barbería A', 1500.0), ('Barbería B', 300.0)])

    def test_top_limita_el_ranking(self):
        r = self.http.get('/api/superadmin/ingresos/?top=1').json()
        self.assertEqual(len(r['por_barberia']), 1)

    def test_top_invalido_se_rechaza(self):
        self.assertEqual(self.http.get('/api/superadmin/ingresos/?top=0').status_code, 400)
        self.assertEqual(self.http.get('/api/superadmin/ingresos/?top=abc').status_code, 400)

    def test_el_rango_de_fechas_filtra(self):
        ayer = date.today() - timedelta(days=1)
        r = self.http.get(f'/api/superadmin/ingresos/?hasta={ayer}').json()
        self.assertEqual(r['total'], 0.0)

    def test_fechas_invalidas_se_rechazan(self):
        self.assertEqual(self.http.get('/api/superadmin/ingresos/?desde=hoy').status_code, 400)
        self.assertEqual(
            self.http.get('/api/superadmin/ingresos/?desde=2026-12-31&hasta=2026-01-01').status_code, 400)

    def test_serie_mensual(self):
        r = self.http.get('/api/superadmin/ingresos/').json()
        self.assertEqual(r['por_mes'][0]['mes'], date.today().strftime('%Y-%m'))
        self.assertEqual(r['por_mes'][0]['total'], 1800.0)

    def test_coincide_con_lo_que_ve_cada_dueno(self):
        # El total de la plataforma es la suma de lo cobrado en cada barbería.
        r = self.http.get('/api/superadmin/barberias/').json()['barberias']
        self.assertEqual(sum(b['ingresos_confirmados'] for b in r), 1800.0)

    def test_resumen(self):
        r = self.http.get('/api/superadmin/resumen/').json()
        self.assertEqual(r['barberias']['por_estado']['ACTIVA'], 2)
        self.assertEqual(r['barberias']['por_estado']['INACTIVA'], 0)
        self.assertEqual(r['ingresos']['total'], 1800.0)
        self.assertEqual(r['turnos']['por_estado']['FINALIZADO'], 4)
        self.assertEqual(r['turnos']['total'], 6)


class BloqueoBarberiaTest(SuperadminBase):
    def _url(self, barberia, accion):
        return f'/api/superadmin/barberias/{barberia.id_barberia}/{accion}/'

    def _estado(self, barberia):
        return Barberia.objects.get(id_barberia=barberia.id_barberia).estado

    def test_bloquear_pasa_la_barberia_a_inactiva(self):
        r = self._patch(self.http, self._url(self.barberia_a, 'bloquear'), {'motivo': 'Falta de pago'})
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json()['estado'], 'INACTIVA')
        self.assertEqual(self._estado(self.barberia_a), 'INACTIVA')
        self.assertEqual(self._estado(self.barberia_b), 'ACTIVA')

    def test_el_motivo_es_obligatorio_para_bloquear(self):
        for cuerpo in ({}, {'motivo': ''}, {'motivo': '   '}):
            r = self._patch(self.http, self._url(self.barberia_a, 'bloquear'), cuerpo)
            self.assertEqual(r.status_code, 400)
        self.assertEqual(self._estado(self.barberia_a), 'ACTIVA')

    def test_motivo_demasiado_largo(self):
        r = self._patch(self.http, self._url(self.barberia_a, 'bloquear'), {'motivo': 'x' * 256})
        self.assertEqual(r.status_code, 400)

    def test_no_se_bloquea_dos_veces(self):
        self._patch(self.http, self._url(self.barberia_a, 'bloquear'), {'motivo': 'x'})
        r = self._patch(self.http, self._url(self.barberia_a, 'bloquear'), {'motivo': 'x'})
        self.assertEqual(r.status_code, 409)

    def test_desbloquear_vuelve_a_activa(self):
        self._patch(self.http, self._url(self.barberia_a, 'bloquear'), {'motivo': 'x'})
        r = self._patch(self.http, self._url(self.barberia_a, 'desbloquear'))
        self.assertEqual(r.status_code, 200)
        self.assertEqual(self._estado(self.barberia_a), 'ACTIVA')

    def test_no_se_desbloquea_una_activa(self):
        r = self._patch(self.http, self._url(self.barberia_a, 'desbloquear'))
        self.assertEqual(r.status_code, 409)

    def test_barberia_inexistente(self):
        r = self._patch(self.http, '/api/superadmin/barberias/999999/bloquear/', {'motivo': 'x'})
        self.assertEqual(r.status_code, 404)

    def test_metodo_incorrecto(self):
        r = self.http.get(self._url(self.barberia_a, 'bloquear'))
        self.assertEqual(r.status_code, 405)

    def test_una_barberia_bloqueada_deja_de_verse_al_publico(self):
        self._patch(self.http, self._url(self.barberia_a, 'bloquear'), {'motivo': 'x'})
        publico = self._http()
        ids = [b['id'] for b in publico.get('/api/barberias/').json()]
        self.assertNotIn(self.barberia_a.id_barberia, ids)
        self.assertIn(self.barberia_b.id_barberia, ids)
        self.assertEqual(publico.get(f'/api/barberias/{self.barberia_a.id_barberia}/').status_code, 404)

    def test_una_barberia_bloqueada_no_puede_operar_la_cola(self):
        Barberia.objects.filter(id_barberia=self.barberia_a.id_barberia).update(orden_llegada_habilitado=1)
        self._patch(self.http, self._url(self.barberia_a, 'bloquear'), {'motivo': 'x'})
        self.assertEqual(self._http(self.dueno_a).get('/api/cola/').status_code, 403)

    def test_el_dueno_no_puede_desbloquearse_solo(self):
        self._patch(self.http, self._url(self.barberia_a, 'bloquear'), {'motivo': 'x'})
        r = self._patch(self._http(self.dueno_a), self._url(self.barberia_a, 'desbloquear'))
        self.assertEqual(r.status_code, 403)
        self._http(self.dueno_a).put(
            '/api/mi-barberia/', data=json.dumps({'estado': 'ACTIVA'}), content_type='application/json')
        self.assertEqual(self._estado(self.barberia_a), 'INACTIVA')

    def test_listado_filtra_por_estado(self):
        self._patch(self.http, self._url(self.barberia_a, 'bloquear'), {'motivo': 'x'})
        r = self.http.get('/api/superadmin/barberias/?estado=INACTIVA').json()['barberias']
        self.assertEqual([b['nombre'] for b in r], ['Barbería A'])
        self.assertTrue(r[0]['bloqueada'])
        self.assertEqual(self.http.get('/api/superadmin/barberias/?estado=otra').status_code, 400)

    def test_listado_busca_por_nombre_y_email_del_dueno(self):
        r = self.http.get('/api/superadmin/barberias/?search=Barbería B').json()['barberias']
        self.assertEqual([b['nombre'] for b in r], ['Barbería B'])
        email = self.dueno_a.email
        r = self.http.get(f'/api/superadmin/barberias/?search={email}').json()['barberias']
        self.assertEqual([b['nombre'] for b in r], ['Barbería A'])


class SuscripcionesSuperadminTest(SuperadminBase):
    def setUp(self):
        super().setUp()
        plan = PlanSuscripcion.objects.create(
            nombre='Básico', precio=1000, incluye_estadisticas=0, incluye_promociones=0)
        estado = _valores_enum('suscripcion', 'estado')[0]
        hoy = date.today()
        ahora = datetime.now()

        def crear(barberia, fin):
            return Suscripcion.objects.create(
                id_barberia=barberia, id_plan=plan, fecha_inicio=hoy - timedelta(days=60),
                fecha_fin=fin, estado=estado, created_at=ahora, updated_at=ahora)

        crear(self.barberia_a, hoy - timedelta(days=5))   # vencida
        crear(self.barberia_b, hoy + timedelta(days=10))  # por vencer

    def test_lista_todas_con_su_estado_de_vencimiento(self):
        r = self.http.get('/api/superadmin/suscripciones/').json()['suscripciones']
        self.assertEqual([(s['barberia'], s['vencida']) for s in r],
                         [('Barbería A', True), ('Barbería B', False)])

    def test_filtro_vencidas(self):
        r = self.http.get('/api/superadmin/suscripciones/?filtro=vencidas').json()['suscripciones']
        self.assertEqual([s['barberia'] for s in r], ['Barbería A'])

    def test_filtro_por_vencer(self):
        r = self.http.get('/api/superadmin/suscripciones/?filtro=por_vencer').json()['suscripciones']
        self.assertEqual([s['barberia'] for s in r], ['Barbería B'])
        r = self.http.get('/api/superadmin/suscripciones/?filtro=por_vencer&dias=5').json()['suscripciones']
        self.assertEqual(r, [])

    def test_filtro_invalido(self):
        self.assertEqual(self.http.get('/api/superadmin/suscripciones/?filtro=otro').status_code, 400)
        self.assertEqual(
            self.http.get('/api/superadmin/suscripciones/?filtro=por_vencer&dias=0').status_code, 400)

    def test_el_resumen_cuenta_vencidas_y_por_vencer(self):
        r = self.http.get('/api/superadmin/resumen/').json()['suscripciones']
        self.assertEqual(r, {'vencidas': 1, 'por_vencer': 1})


class LoginPanelTest(SuperadminBase):
    def _login(self, email, password):
        return Client().post('/api/superadmin/login/', data=json.dumps({'email': email, 'password': password}),
                             content_type='application/json')

    def setUp(self):
        super().setUp()
        Usuario.objects.filter(id_usuario=self.admin.id_usuario).update(password=make_password('clave-segura-1'))
        Usuario.objects.filter(id_usuario=self.cliente.id_usuario).update(password=make_password('clave-segura-1'))

    def test_el_admin_entra_y_queda_con_sesion(self):
        cliente = Client()
        r = cliente.post('/api/superadmin/login/', data=json.dumps({'email': self.admin.email, 'password': 'clave-segura-1'}),
                         content_type='application/json')
        self.assertEqual(r.status_code, 200)
        self.assertEqual(cliente.get('/api/superadmin/resumen/').status_code, 200)

    def test_contrasena_incorrecta(self):
        self.assertEqual(self._login(self.admin.email, 'mala').status_code, 401)

    def test_email_inexistente(self):
        self.assertEqual(self._login('nadie@test.com', 'x').status_code, 401)

    def test_un_cliente_con_clave_correcta_no_entra(self):
        self.assertEqual(self._login(self.cliente.email, 'clave-segura-1').status_code, 403)

    def test_logout_cierra_la_sesion(self):
        cliente = self._http(self.admin)
        cliente.post('/api/superadmin/logout/')
        self.assertEqual(cliente.get('/api/superadmin/resumen/').status_code, 401)

    def test_la_pagina_del_panel_se_sirve(self):
        r = Client().get('/api/superadmin/panel/')
        self.assertEqual(r.status_code, 200)
        self.assertIn('text/html', r['Content-Type'])
