import json
from datetime import datetime, timedelta, time
from django.db import connection
from django.test import Client
from apps.barberias.models import Barberia
from apps.usuarios.models import Usuario, Barbero, Servicio, Disponibilidad
from .models import Turno

# Datos de prueba compartidos por los tests de reservas, cancelación,
# reprogramación y permisos (Sprint 7 - Facundo).

TABLAS = [
    'calificacion', 'pago', 'notificacion', 'turno', 'promocion', 'disponibilidad',
    'servicio', 'barbero', 'barberia', 'usuario',
]


def limpiar_tablas():
    # Los modelos son managed=False: TransactionTestCase no vacía estas tablas solo.
    with connection.cursor() as cursor:
        cursor.execute('SET FOREIGN_KEY_CHECKS=0')
        for tabla in TABLAS:
            cursor.execute(f'DELETE FROM {tabla}')
        cursor.execute('SET FOREIGN_KEY_CHECKS=1')


def crear_usuario(email, rol='CLIENTE', estado='ACTIVO'):
    return Usuario.objects.create(
        nombre=email.split('@')[0], apellido='Test', email=email, telefono='1100000000',
        password='x', rol=rol, estado=estado, fecha_registro=datetime.now(),
    )


def crear_barberia(dueno, nombre='Barbería'):
    return Barberia.objects.create(
        id_dueno=dueno, nombre=nombre, direccion='Calle 1', zona='Centro', estado='ACTIVA',
    )


def crear_barbero(usuario, barberia):
    return Barbero.objects.create(
        id_usuario=usuario, id_barberia=barberia, promedio_calificacion=0,
    )


def crear_servicio(barberia, nombre='Corte', duracion=30, precio=1000, estado=1):
    return Servicio.objects.create(
        id_barberia=barberia, nombre=nombre, precio=precio, duracion_minutos=duracion, estado=estado,
    )


def cargar_disponibilidad(barbero, inicio=time(9, 0), fin=time(18, 0)):
    for dia in ['LUN', 'MAR', 'MIE', 'JUE', 'VIE', 'SAB', 'DOM']:
        Disponibilidad.objects.create(id_barbero=barbero, dia_semana=dia, hora_inicio=inicio, hora_fin=fin)


def crear_turno_directo(cliente, barbero, servicio, fecha, hora_inicio, estado='CONFIRMADO'):
    inicio = datetime.combine(fecha, hora_inicio)
    fin = inicio + timedelta(minutes=servicio.duracion_minutos)
    ahora = datetime.now()
    return Turno.objects.create(
        id_cliente=cliente, id_barbero=barbero, id_servicio=servicio, fecha=fecha,
        hora_inicio=hora_inicio, hora_fin=fin.time(), estado=estado,
        monto_total=servicio.precio, fecha_reserva=ahora, created_at=ahora, updated_at=ahora,
        created_by=cliente,
    )


def dias_desde_hoy(dias):
    return datetime.now().date() + timedelta(days=dias)


def cliente_http(usuario=None):
    c = Client()
    if usuario is not None:
        sesion = c.session
        sesion['id_usuario'] = usuario.id_usuario
        sesion.save()
    return c


def post_json(client, url, datos):
    return client.post(url, data=json.dumps(datos), content_type='application/json')


def patch_json(client, url, datos=None):
    return client.patch(url, data=json.dumps(datos or {}), content_type='application/json')


class Escenario:
    # Dos barberías independientes, para probar que no se mezclan.
    #   B1: dueño d1, barberos bo1 y bo2, servicios s30 (30 min) y s60 (60 min)
    #   B2: dueño d2, barbero bo3, servicio s_b2
    # Todos los barberos atienden todos los días de 09:00 a 18:00.
    def crear_escenario(self):
        self.d1 = crear_usuario('dueno1@t.com', 'DUENO')
        self.b1 = crear_barberia(self.d1, 'Barbería Uno')
        self.u_bo1 = crear_usuario('barbero1@t.com', 'BARBERO')
        self.u_bo2 = crear_usuario('barbero2@t.com', 'BARBERO')
        self.bo1 = crear_barbero(self.u_bo1, self.b1)
        self.bo2 = crear_barbero(self.u_bo2, self.b1)
        self.s30 = crear_servicio(self.b1, 'Corte', 30, 1000)
        self.s60 = crear_servicio(self.b1, 'Corte y barba', 60, 1800)

        self.d2 = crear_usuario('dueno2@t.com', 'DUENO')
        self.b2 = crear_barberia(self.d2, 'Barbería Dos')
        self.u_bo3 = crear_usuario('barbero3@t.com', 'BARBERO')
        self.bo3 = crear_barbero(self.u_bo3, self.b2)
        self.s_b2 = crear_servicio(self.b2, 'Corte B2', 30, 900)

        for barbero in (self.bo1, self.bo2, self.bo3):
            cargar_disponibilidad(barbero)

        self.c1 = crear_usuario('cliente1@t.com')
        self.c2 = crear_usuario('cliente2@t.com')
        self.manana = dias_desde_hoy(1)
