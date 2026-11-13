import json
import re
from datetime import date, datetime
from django.db import connection
from django.test import Client, TestCase
from apps.barberias.models import Barberia
from apps.usuarios.models import Barbero, ColaAtencion, Servicio, Usuario
from .models import Turno

# ══════════════════════════════════════════
# Sprint 7 - Módulo D (Gonzalo): tests de la cola por orden de llegada.
# Corren con el runner del Sprint 7 (esquema SQL real + migración).
# Los valores de los ENUM de usuario (rol, estado) se leen de la base de prueba
# para no depender de cómo están escritos.
# ══════════════════════════════════════════


def _valores_enum(tabla, columna):
    with connection.cursor() as cursor:
        cursor.execute(f'SHOW COLUMNS FROM {tabla} LIKE %s', [columna])
        tipo = cursor.fetchone()[1]
    if isinstance(tipo, bytes):
        tipo = tipo.decode()
    return re.findall(r"'([^']*)'", tipo)


def _valor_enum(tabla, columna, prefijo):
    return next(v for v in _valores_enum(tabla, columna) if v.upper().startswith(prefijo))


class ColaBase(TestCase):
    _contador = 0

    def _usuario(self, rol, estado='ACT'):
        ColaBase._contador += 1
        return Usuario.objects.create(
            nombre='Nombre', apellido='Apellido',
            email=f'cola{ColaBase._contador}@test.com', telefono='1100000000',
            password='x', rol=_valor_enum('usuario', 'rol', rol),
            estado=_valor_enum('usuario', 'estado', estado),
            fecha_registro=datetime.now(),
        )

    def _barberia(self, nombre, habilitada=1):
        dueno = self._usuario('DUE')
        barberia = Barberia.objects.create(
            id_dueno=dueno, nombre=nombre, direccion='Calle 1', zona='Centro',
            estado='ACTIVA', orden_llegada_habilitado=habilitada,
        )
        usuario_barbero = self._usuario('BAR')
        barbero = Barbero.objects.create(id_usuario=usuario_barbero, id_barberia=barberia, promedio_calificacion=0)
        servicio = Servicio.objects.create(
            id_barberia=barberia, nombre='Corte', precio=1000, duracion_minutos=30, estado=1)
        return dueno, barberia, usuario_barbero, barbero, servicio

    def _cliente_http(self, usuario=None):
        cliente = Client()
        if usuario:
            sesion = cliente.session
            sesion['id_usuario'] = usuario.id_usuario
            sesion.save()
        return cliente

    def _post(self, cliente, url, datos=None):
        return cliente.post(url, data=json.dumps(datos or {}), content_type='application/json')

    def _patch(self, cliente, url):
        return cliente.patch(url, data='{}', content_type='application/json')

    def setUp(self):
        (self.dueno, self.barberia, self.u_barbero, self.barbero, self.servicio) = self._barberia('Barbería A')
        (self.dueno_b, self.barberia_b, self.u_barbero_b, self.barbero_b, self.servicio_b) = self._barberia('Barbería B')
        self.http_dueno = self._cliente_http(self.dueno)
        self.http_barbero = self._cliente_http(self.u_barbero)

    def _llegada(self, nombre='Juan', http=None, **extra):
        datos = {'id_servicio': self.servicio.id_servicio, 'nombre_cliente': nombre}
        datos.update(extra)
        return self._post(http or self.http_dueno, '/api/cola/', datos)


class ColaRegistroTest(ColaBase):
    def test_los_ingresos_se_numeran_en_orden(self):
        numeros = [self._llegada(f'Cliente {i}').json()['entrada']['numero_orden'] for i in range(3)]
        self.assertEqual(numeros, [1, 2, 3])

    def test_la_cola_se_lista_ordenada(self):
        self._llegada('Uno')
        self._llegada('Dos')
        r = self.http_dueno.get('/api/cola/').json()
        self.assertEqual([e['cliente'] for e in r['cola']], ['Uno', 'Dos'])
        self.assertTrue(r['habilitada'])

    def test_no_registra_si_la_modalidad_esta_deshabilitada(self):
        Barberia.objects.filter(id_barberia=self.barberia.id_barberia).update(orden_llegada_habilitado=0)
        self.assertEqual(self._llegada().status_code, 403)

    def test_el_barbero_tambien_puede_registrar(self):
        self.assertEqual(self._llegada(http=self.http_barbero).status_code, 201)

    def test_la_llegada_no_crea_turnos(self):
        antes = Turno.objects.count()
        self._llegada()
        self.assertEqual(Turno.objects.count(), antes)

    def test_servicio_de_otra_barberia_se_rechaza(self):
        r = self._llegada(id_servicio=self.servicio_b.id_servicio)
        self.assertEqual(r.status_code, 400)

    def test_barbero_de_otra_barberia_se_rechaza(self):
        r = self._llegada(id_barbero=self.barbero_b.id_barbero)
        self.assertEqual(r.status_code, 400)

    def test_hace_falta_cliente_o_nombre(self):
        r = self._post(self.http_dueno, '/api/cola/', {'id_servicio': self.servicio.id_servicio})
        self.assertEqual(r.status_code, 400)

    def test_cliente_bloqueado_no_puede_entrar(self):
        bloqueado = self._usuario('CLI', estado='BLOQ')
        r = self._post(self.http_dueno, '/api/cola/',
                       {'id_servicio': self.servicio.id_servicio, 'id_cliente': bloqueado.id_usuario})
        self.assertEqual(r.status_code, 403)
        self.assertEqual(ColaAtencion.objects.count(), 0)

    def test_cliente_registrado_no_se_repite_en_la_cola(self):
        cliente = self._usuario('CLI')
        datos = {'id_servicio': self.servicio.id_servicio, 'id_cliente': cliente.id_usuario}
        self.assertEqual(self._post(self.http_dueno, '/api/cola/', datos).status_code, 201)
        self.assertEqual(self._post(self.http_dueno, '/api/cola/', datos).status_code, 409)

    def test_el_orden_es_por_barberia(self):
        # Cada barbería lleva su propia numeración.
        http_b = self._cliente_http(self.dueno_b)
        self._llegada('A1')
        r = self._post(http_b, '/api/cola/', {'id_servicio': self.servicio_b.id_servicio, 'nombre_cliente': 'B1'})
        self.assertEqual(r.json()['entrada']['numero_orden'], 1)


class ColaPermisosTest(ColaBase):
    def test_sin_sesion_responde_401(self):
        self.assertEqual(self._cliente_http().get('/api/cola/').status_code, 401)
        self.assertEqual(self._cliente_http().post('/api/cola/').status_code, 401)

    def test_un_cliente_comun_no_accede_a_la_cola(self):
        cliente = self._usuario('CLI')
        r = self._cliente_http(cliente).get('/api/cola/')
        self.assertIn(r.status_code, (403, 404))

    def test_no_se_ve_ni_se_opera_la_cola_de_otra_barberia(self):
        entrada_id = self._llegada('Juan').json()['entrada']['id']
        http_b = self._cliente_http(self.dueno_b)
        self.assertEqual(http_b.get('/api/cola/').json()['cola'], [])
        self.assertEqual(self._patch(http_b, f'/api/cola/{entrada_id}/cancelar/').status_code, 404)
        self.assertEqual(ColaAtencion.objects.get(id_cola=entrada_id).estado, 'ESPERA')

    def test_el_barbero_de_otra_barberia_no_opera_esta_cola(self):
        entrada_id = self._llegada('Juan').json()['entrada']['id']
        http_otro = self._cliente_http(self.u_barbero_b)
        self.assertEqual(self._patch(http_otro, f'/api/cola/{entrada_id}/cancelar/').status_code, 404)
        self.assertEqual(self._post(http_otro, '/api/cola/siguiente/').status_code, 404)


class ColaAtencionTest(ColaBase):
    def test_siguiente_toma_al_primero_y_lo_asigna_al_barbero(self):
        self._llegada('Uno')
        self._llegada('Dos')
        r = self._post(self.http_barbero, '/api/cola/siguiente/')
        self.assertEqual(r.status_code, 200)
        entrada = r.json()['entrada']
        self.assertEqual(entrada['cliente'], 'Uno')
        self.assertEqual(entrada['estado'], 'ATENCION')
        self.assertEqual(entrada['id_barbero'], self.barbero.id_barbero)

    def test_no_se_pasa_al_siguiente_con_una_atencion_abierta(self):
        self._llegada('Uno')
        self._llegada('Dos')
        self._post(self.http_barbero, '/api/cola/siguiente/')
        self.assertEqual(self._post(self.http_barbero, '/api/cola/siguiente/').status_code, 409)

    def test_siguiente_sin_nadie_en_espera(self):
        self.assertEqual(self._post(self.http_barbero, '/api/cola/siguiente/').status_code, 404)

    def test_cerrar_y_seguir_con_el_siguiente(self):
        self._llegada('Uno')
        self._llegada('Dos')
        primero = self._post(self.http_barbero, '/api/cola/siguiente/').json()['entrada']
        r = self._patch(self.http_barbero, f'/api/cola/{primero["id"]}/cerrar/')
        self.assertEqual(r.json()['entrada']['estado'], 'CERRADO')
        segundo = self._post(self.http_barbero, '/api/cola/siguiente/').json()['entrada']
        self.assertEqual(segundo['cliente'], 'Dos')

    def test_no_se_cierra_dos_veces(self):
        self._llegada('Uno')
        entrada = self._post(self.http_barbero, '/api/cola/siguiente/').json()['entrada']
        self._patch(self.http_barbero, f'/api/cola/{entrada["id"]}/cerrar/')
        self.assertEqual(self._patch(self.http_barbero, f'/api/cola/{entrada["id"]}/cerrar/').status_code, 400)

    def test_no_se_cierra_a_alguien_que_sigue_esperando(self):
        entrada_id = self._llegada('Uno').json()['entrada']['id']
        self.assertEqual(self._patch(self.http_barbero, f'/api/cola/{entrada_id}/cerrar/').status_code, 400)

    def test_otro_barbero_no_cierra_una_atencion_ajena(self):
        otro_usuario = self._usuario('BAR')
        Barbero.objects.create(id_usuario=otro_usuario, id_barberia=self.barberia, promedio_calificacion=0)
        self._llegada('Uno')
        entrada = self._post(self.http_barbero, '/api/cola/siguiente/').json()['entrada']
        r = self._patch(self._cliente_http(otro_usuario), f'/api/cola/{entrada["id"]}/cerrar/')
        self.assertEqual(r.status_code, 403)

    def test_el_dueno_si_puede_cerrar_cualquier_atencion(self):
        self._llegada('Uno')
        entrada = self._post(self.http_barbero, '/api/cola/siguiente/').json()['entrada']
        self.assertEqual(self._patch(self.http_dueno, f'/api/cola/{entrada["id"]}/cerrar/').status_code, 200)

    def test_cancelar_solo_vale_para_quien_espera(self):
        espera = self._llegada('Uno').json()['entrada']['id']
        self.assertEqual(self._patch(self.http_barbero, f'/api/cola/{espera}/cancelar/').status_code, 200)
        self._llegada('Dos')
        atendido = self._post(self.http_barbero, '/api/cola/siguiente/').json()['entrada']['id']
        self.assertEqual(self._patch(self.http_barbero, f'/api/cola/{atendido}/cancelar/').status_code, 400)

    def test_un_cancelado_no_vuelve_a_ser_el_siguiente(self):
        espera = self._llegada('Uno').json()['entrada']['id']
        self._llegada('Dos')
        self._patch(self.http_dueno, f'/api/cola/{espera}/cancelar/')
        entrada = self._post(self.http_barbero, '/api/cola/siguiente/').json()['entrada']
        self.assertEqual(entrada['cliente'], 'Dos')

    def test_dueno_sin_barbero_tiene_que_indicar_quien_atiende(self):
        self._llegada('Uno')
        self.assertEqual(self._post(self.http_dueno, '/api/cola/siguiente/').status_code, 400)
        r = self._post(self.http_dueno, '/api/cola/siguiente/', {'id_barbero': self.barbero.id_barbero})
        self.assertEqual(r.status_code, 200)


class MiColaTest(ColaBase):
    def test_el_cliente_ve_su_lugar_en_la_cola(self):
        self._llegada('Otro')
        cliente = self._usuario('CLI')
        self._post(self.http_dueno, '/api/cola/',
                   {'id_servicio': self.servicio.id_servicio, 'id_cliente': cliente.id_usuario})
        r = self._cliente_http(cliente).get('/api/mi-cola/').json()
        self.assertEqual(len(r['entradas']), 1)
        self.assertEqual(r['entradas'][0]['numero_orden'], 2)
        self.assertEqual(r['entradas'][0]['personas_delante'], 1)
        self.assertNotIn('minutos', json.dumps(r).lower())

    def test_sin_sesion_responde_401(self):
        self.assertEqual(self._cliente_http().get('/api/mi-cola/').status_code, 401)


class ConfiguracionOrdenLlegadaTest(ColaBase):
    def test_el_dueno_habilita_y_deshabilita(self):
        r = self.http_dueno.put('/api/mi-barberia/', data=json.dumps({'orden_llegada_habilitado': False}),
                                content_type='application/json')
        self.assertEqual(r.status_code, 200)
        self.assertFalse(r.json()['orden_llegada_habilitado'])
        self.assertEqual(Barberia.objects.get(id_barberia=self.barberia.id_barberia).orden_llegada_habilitado, 0)

    def test_valor_no_booleano_se_rechaza(self):
        r = self.http_dueno.put('/api/mi-barberia/', data=json.dumps({'orden_llegada_habilitado': 'si'}),
                                content_type='application/json')
        self.assertEqual(r.status_code, 400)
