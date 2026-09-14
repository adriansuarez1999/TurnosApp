from datetime import datetime, timedelta

from django.db import transaction
from django.db.models import Count, Q
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

import json

from apps.barberias.models import Barberia
from apps.usuarios.models import Barbero, Servicio, Usuario
from .models import Turno


# ═══════════════════════════════════════════════════════════════
# HELPERS
# ═══════════════════════════════════════════════════════════════

def _usuario_logueado(request):
    """
    Devuelve el id del usuario guardado en sesión.
    """
    return request.session.get('id_usuario')


def _barberia_del_dueno(id_usuario):
    """
    Devuelve la barbería cuyo dueño es el usuario indicado.
    """
    return Barberia.objects.filter(
        id_dueno=id_usuario
    ).first()


def _cliente_pertenece_a_barberia(id_cliente, id_barberia):
    """
    Un cliente puede ser administrado por un dueño solamente
    si tiene al menos un turno realizado/reservado en esa barbería.

    Esto evita que un dueño pueda bloquear clientes de otra barbería.
    """
    return Turno.objects.filter(
        id_cliente_id=id_cliente,
        id_barbero__id_barberia_id=id_barberia
    ).exists()


def _parsear_hora(valor):
    """
    Acepta HH:MM o HH:MM:SS.
    """
    formato = '%H:%M:%S' if valor.count(':') == 2 else '%H:%M'

    return datetime.strptime(
        valor,
        formato
    ).time()


# ═══════════════════════════════════════════════════════════════
# CREAR TURNO
# ═══════════════════════════════════════════════════════════════

def crear_turno(request):
    if request.method != 'POST':
        return JsonResponse(
            {
                'ok': False,
                'error': 'Método no permitido'
            },
            status=405
        )

    id_cliente = _usuario_logueado(request)

    if not id_cliente:
        return JsonResponse(
            {
                'ok': False,
                'error': 'Tenés que iniciar sesión para reservar un turno.'
            },
            status=401
        )

    # ───────────────────────────────────────────────────────────
    # Sprint 4 - Módulo B
    # Validación de cliente bloqueado.
    # ───────────────────────────────────────────────────────────

    try:
        cliente = Usuario.objects.get(
            id_usuario=id_cliente
        )

    except Usuario.DoesNotExist:
        return JsonResponse(
            {
                'ok': False,
                'error': 'Usuario no encontrado.'
            },
            status=404
        )

    if cliente.estado == 'BLOQUEADO':
        return JsonResponse(
            {
                'ok': False,
                'error': (
                    'Tu cuenta está bloqueada y no podés reservar turnos. '
                    'Contactá con la barbería para más información.'
                )
            },
            status=403
        )

    # ───────────────────────────────────────────────────────────

    try:
        data = json.loads(request.body)

        id_barbero = data.get('id_barbero')
        id_servicio = data['id_servicio']
        fecha = data['fecha']
        hora_inicio_str = data['hora_inicio']

        try:
            servicio = Servicio.objects.get(
                id_servicio=id_servicio
            )

        except Servicio.DoesNotExist:
            return JsonResponse(
                {
                    'ok': False,
                    'error': 'Servicio no encontrado'
                },
                status=404
            )

        hora_inicio = datetime.strptime(
            hora_inicio_str,
            '%H:%M'
        ).time()

        fecha_dt = datetime.strptime(
            fecha,
            '%Y-%m-%d'
        ).date()

        inicio_dt = datetime.combine(
            fecha_dt,
            hora_inicio
        )

        fin_dt = inicio_dt + timedelta(
            minutes=servicio.duracion_minutos
        )

        hora_fin = fin_dt.time()

        with transaction.atomic():

            # ───────────────────────────────────────────────────
            # BARBERO SELECCIONADO
            # ───────────────────────────────────────────────────

            if id_barbero:

                try:
                    barbero = Barbero.objects.get(
                        id_barbero=id_barbero
                    )

                except Barbero.DoesNotExist:
                    return JsonResponse(
                        {
                            'ok': False,
                            'error': 'Barbero no encontrado'
                        },
                        status=404
                    )

                superpuesto = (
                    Turno.objects
                    .select_for_update()
                    .filter(
                        id_barbero=id_barbero,
                        fecha=fecha_dt,
                        hora_inicio__lt=hora_fin,
                        hora_fin__gt=hora_inicio
                    )
                    .exclude(
                        estado='CANCELADO'
                    )
                    .exists()
                )

                if superpuesto:
                    return JsonResponse(
                        {
                            'ok': False,
                            'error': (
                                'El horario ya está ocupado '
                                'para ese barbero'
                            )
                        },
                        status=409
                    )

            # ───────────────────────────────────────────────────
            # ASIGNACIÓN AUTOMÁTICA DE BARBERO
            # ───────────────────────────────────────────────────

            else:

                candidatos = Barbero.objects.filter(
                    id_barberia=servicio.id_barberia_id
                )

                barbero = None

                for candidato in candidatos:

                    ocupado = (
                        Turno.objects
                        .select_for_update()
                        .filter(
                            id_barbero=candidato.id_barbero,
                            fecha=fecha_dt,
                            hora_inicio__lt=hora_fin,
                            hora_fin__gt=hora_inicio
                        )
                        .exclude(
                            estado='CANCELADO'
                        )
                        .exists()
                    )

                    if not ocupado:
                        barbero = candidato
                        break

                if barbero is None:
                    return JsonResponse(
                        {
                            'ok': False,
                            'error': (
                                'No hay barberos disponibles '
                                'en ese horario'
                            )
                        },
                        status=409
                    )

                id_barbero = barbero.id_barbero

            # ───────────────────────────────────────────────────
            # CREAR TURNO
            # ───────────────────────────────────────────────────

            turno = Turno.objects.create(
                id_cliente_id=id_cliente,
                id_barbero_id=id_barbero,
                id_servicio_id=id_servicio,
                fecha=fecha_dt,
                hora_inicio=hora_inicio,
                hora_fin=hora_fin,
                estado='CONFIRMADO',
                monto_total=servicio.precio,
                fecha_reserva=datetime.now(),
                created_at=datetime.now(),
                updated_at=datetime.now(),
                created_by_id=id_cliente
            )

        return JsonResponse(
            {
                'ok': True,
                'id_turno': turno.id_turno,
                'id_barbero': id_barbero,
                'hora_inicio': hora_inicio.strftime('%H:%M'),
                'hora_fin': hora_fin.strftime('%H:%M'),
                'estado': turno.estado
            },
            status=201
        )

    except KeyError as e:
        return JsonResponse(
            {
                'ok': False,
                'error': f'Falta el campo {e}'
            },
            status=400
        )

    except Exception as e:
        return JsonResponse(
            {
                'ok': False,
                'error': str(e)
            },
            status=400
        )


# ═══════════════════════════════════════════════════════════════
# TURNOS DISPONIBLES
# ═══════════════════════════════════════════════════════════════

@csrf_exempt
def turnos_disponibles(request):

    if request.method != 'GET':
        return JsonResponse(
            {
                'error': 'Metodo no permitido'
            },
            status=405
        )

    try:
        id_barbero = request.GET.get('barbero')
        id_barberia = request.GET.get('barberia')
        fecha = request.GET.get('fecha')

        if not fecha or (
            not id_barbero
            and not id_barberia
        ):
            return JsonResponse(
                {
                    'error': (
                        'Falta la fecha, y el barbero '
                        'o la barbería.'
                    )
                },
                status=400
            )

        fecha_obj = datetime.strptime(
            fecha,
            '%Y-%m-%d'
        ).date()

        if id_barbero:

            ids_barberos = [
                int(id_barbero)
            ]

        else:

            ids_barberos = list(
                Barbero.objects
                .filter(
                    id_barberia=id_barberia
                )
                .values_list(
                    'id_barbero',
                    flat=True
                )
            )

        duracion_bloque = 30

        hora_apertura = datetime.combine(
            fecha_obj,
            _parsear_hora('14:00')
        )

        hora_cierre = datetime.combine(
            fecha_obj,
            _parsear_hora('21:00')
        )

        turnos_ocupados = list(
            Turno.objects
                .filter(
                    id_barbero__in=ids_barberos,
                    fecha=fecha_obj
                )
                .exclude(
                    estado='CANCELADO'
                )
        )

        horarios = []

        actual = hora_apertura

        while (
            actual
            + timedelta(minutes=duracion_bloque)
            <= hora_cierre
        ):

            bloque_inicio = actual.time()

            bloque_fin = (
                actual
                + timedelta(minutes=duracion_bloque)
            ).time()

            libre_en_alguno = any(
                not any(
                    bloque_inicio < turno.hora_fin
                    and bloque_fin > turno.hora_inicio
                    for turno in turnos_ocupados
                    if turno.id_barbero_id == id_barbero_actual
                )
                for id_barbero_actual in ids_barberos
            )

            horarios.append(
                {
                    'hora': bloque_inicio.strftime('%H:%M'),
                    'disponible': libre_en_alguno,
                }
            )

            actual += timedelta(
                minutes=duracion_bloque
            )

        return JsonResponse(
            horarios,
            safe=False
        )

    except Exception as e:
        return JsonResponse(
            {
                'error': str(e)
            },
            status=400
        )


# ═══════════════════════════════════════════════════════════════
# CANCELAR TURNO
# ═══════════════════════════════════════════════════════════════

def cancelar_turno(request, id):

    if request.method != 'PATCH':
        return JsonResponse(
            {
                'ok': False,
                'error': 'Metodo no permitido'
            },
            status=405
        )

    id_cliente = _usuario_logueado(request)

    if not id_cliente:
        return JsonResponse(
            {
                'ok': False,
                'error': 'Tenés que iniciar sesión.'
            },
            status=401
        )

    try:
        turno = Turno.objects.get(
            id_turno=id
        )

    except Turno.DoesNotExist:
        return JsonResponse(
            {
                'ok': False,
                'error': 'Turno no encontrado.'
            },
            status=404
        )

    if turno.id_cliente_id != id_cliente:
        return JsonResponse(
            {
                'ok': False,
                'error': (
                    'No tenes permiso para cancelar este turno.'
                )
            },
            status=403
        )

    try:
        turno.estado = 'CANCELADO'
        turno.updated_at = datetime.now()
        turno.save()

        return JsonResponse(
            {
                'ok': True,
                'id_turno': turno.id_turno,
                'estado': turno.estado,
            },
            status=200
        )

    except Exception as e:
        return JsonResponse(
            {
                'ok': False,
                'error': str(e)
            },
            status=400
        )


# ═══════════════════════════════════════════════════════════════
# MIS TURNOS
# ═══════════════════════════════════════════════════════════════

def mis_turnos(request):

    if request.method != 'GET':
        return JsonResponse(
            {
                'error': 'Metodo no permitido'
            },
            status=405
        )

    id_cliente = _usuario_logueado(request)

    if not id_cliente:
        return JsonResponse(
            {
                'error': 'Tenés que iniciar sesión.'
            },
            status=401
        )

    try:
        hoy = datetime.now().date()

        proximos = (
            Turno.objects
            .filter(
                id_cliente=id_cliente,
                fecha__gte=hoy
            )
            .order_by(
                'fecha',
                'hora_inicio'
            )
        )

        pasados = (
            Turno.objects
            .filter(
                id_cliente=id_cliente,
                fecha__lt=hoy
            )
            .order_by(
                '-fecha',
                '-hora_inicio'
            )
        )

        def serializar(turno):
            return {
                'id': turno.id_turno,

                'barberia':
                    turno.id_barbero
                    .id_barberia
                    .nombre,

                'barbero':
                    (
                        f'{turno.id_barbero.id_usuario.nombre} '
                        f'{turno.id_barbero.id_usuario.apellido}'
                    ),

                'servicio':
                    turno.id_servicio.nombre,

                'fecha':
                    str(turno.fecha),

                'hora':
                    turno.hora_inicio.strftime('%H:%M'),

                'estado':
                    turno.estado,
            }

        lista = (
            [serializar(turno) for turno in proximos]
            +
            [serializar(turno) for turno in pasados]
        )

        return JsonResponse(
            lista,
            safe=False
        )

    except Exception as e:
        return JsonResponse(
            {
                'error': str(e)
            },
            status=400
        )


# ═══════════════════════════════════════════════════════════════
# SPRINT 4 - MÓDULO B
# GESTIÓN DE CLIENTES / BLOQUEOS
# ═══════════════════════════════════════════════════════════════


# GET /api/mi-barberia/clientes/
#
# Lista solamente los usuarios que tienen al menos un turno
# en la barbería del dueño actualmente autenticado.
#
# Incluye:
# - cantidad total de turnos
# - cantidad de ausencias
# - estado actual del usuario
#
def clientes_barberia(request):

    if request.method != 'GET':
        return JsonResponse(
            {
                'ok': False,
                'error': 'Método no permitido'
            },
            status=405
        )

    id_usuario = _usuario_logueado(request)

    if not id_usuario:
        return JsonResponse(
            {
                'ok': False,
                'error': 'Tenés que iniciar sesión.'
            },
            status=401
        )

    barberia = _barberia_del_dueno(
        id_usuario
    )

    if not barberia:
        return JsonResponse(
            {
                'ok': False,
                'error': 'No tenés una barbería registrada.'
            },
            status=404
        )

    try:

        clientes = (
            Turno.objects
            .filter(
                id_barbero__id_barberia_id=barberia.id_barberia
            )
            .values(
                'id_cliente_id',
                'id_cliente__nombre',
                'id_cliente__apellido',
                'id_cliente__email',
                'id_cliente__telefono',
                'id_cliente__estado'
            )
            .annotate(
                total_turnos=Count(
                    'id_turno'
                ),

                ausencias=Count(
                    'id_turno',
                    filter=Q(
                        estado='AUSENTE'
                    )
                )
            )
            .order_by(
                '-ausencias',
                'id_cliente__apellido',
                'id_cliente__nombre'
            )
        )

        lista = []

        for cliente in clientes:

            lista.append(
                {
                    'id_usuario':
                        cliente['id_cliente_id'],

                    'nombre':
                        cliente['id_cliente__nombre'],

                    'apellido':
                        cliente['id_cliente__apellido'],

                    'email':
                        cliente['id_cliente__email'],

                    'telefono':
                        cliente['id_cliente__telefono'],

                    'estado':
                        cliente['id_cliente__estado'],

                    'total_turnos':
                        cliente['total_turnos'],

                    'ausencias':
                        cliente['ausencias'],
                }
            )

        return JsonResponse(
            {
                'ok': True,
                'clientes': lista
            },
            status=200
        )

    except Exception as e:

        return JsonResponse(
            {
                'ok': False,
                'error': str(e)
            },
            status=400
        )


# PATCH /api/mi-barberia/clientes/<id>/bloquear/
#
# El bloqueo es GLOBAL en esta versión del proyecto:
# se reutiliza usuario.estado = BLOQUEADO.
#
def bloquear_cliente(request, id):

    if request.method != 'PATCH':
        return JsonResponse(
            {
                'ok': False,
                'error': 'Método no permitido'
            },
            status=405
        )

    id_usuario = _usuario_logueado(
        request
    )

    if not id_usuario:
        return JsonResponse(
            {
                'ok': False,
                'error': 'Tenés que iniciar sesión.'
            },
            status=401
        )

    barberia = _barberia_del_dueno(
        id_usuario
    )

    if not barberia:
        return JsonResponse(
            {
                'ok': False,
                'error': 'No tenés una barbería registrada.'
            },
            status=404
        )

    try:
        cliente = Usuario.objects.get(
            id_usuario=id
        )

    except Usuario.DoesNotExist:
        return JsonResponse(
            {
                'ok': False,
                'error': 'Cliente no encontrado.'
            },
            status=404
        )

    # El dueño no puede enviar el ID de cualquier usuario.
    # Ese cliente debe haber reservado previamente en SU barbería.
    if not _cliente_pertenece_a_barberia(
        cliente.id_usuario,
        barberia.id_barberia
    ):
        return JsonResponse(
            {
                'ok': False,
                'error': (
                    'Ese cliente no pertenece '
                    'a tu barbería.'
                )
            },
            status=403
        )

    if cliente.estado == 'BLOQUEADO':
        return JsonResponse(
            {
                'ok': True,
                'id_usuario': cliente.id_usuario,
                'estado': cliente.estado,
                'mensaje': 'El cliente ya estaba bloqueado.'
            },
            status=200
        )

    # No convertimos automáticamente un usuario INACTIVO
    # en otro estado mediante esta acción.
    if cliente.estado == 'INACTIVO':
        return JsonResponse(
            {
                'ok': False,
                'error': (
                    'El cliente está inactivo '
                    'y no puede ser bloqueado.'
                )
            },
            status=400
        )

    try:

        cliente.estado = 'BLOQUEADO'

        cliente.save(
            update_fields=['estado']
        )

        return JsonResponse(
            {
                'ok': True,
                'id_usuario': cliente.id_usuario,
                'estado': cliente.estado,
                'mensaje': (
                    'Cliente bloqueado correctamente.'
                )
            },
            status=200
        )

    except Exception as e:

        return JsonResponse(
            {
                'ok': False,
                'error': str(e)
            },
            status=400
        )


# PATCH /api/mi-barberia/clientes/<id>/desbloquear/
#
def desbloquear_cliente(request, id):

    if request.method != 'PATCH':
        return JsonResponse(
            {
                'ok': False,
                'error': 'Método no permitido'
            },
            status=405
        )

    id_usuario = _usuario_logueado(
        request
    )

    if not id_usuario:
        return JsonResponse(
            {
                'ok': False,
                'error': 'Tenés que iniciar sesión.'
            },
            status=401
        )

    barberia = _barberia_del_dueno(
        id_usuario
    )

    if not barberia:
        return JsonResponse(
            {
                'ok': False,
                'error': 'No tenés una barbería registrada.'
            },
            status=404
        )

    try:
        cliente = Usuario.objects.get(
            id_usuario=id
        )

    except Usuario.DoesNotExist:
        return JsonResponse(
            {
                'ok': False,
                'error': 'Cliente no encontrado.'
            },
            status=404
        )

    if not _cliente_pertenece_a_barberia(
        cliente.id_usuario,
        barberia.id_barberia
    ):
        return JsonResponse(
            {
                'ok': False,
                'error': (
                    'Ese cliente no pertenece '
                    'a tu barbería.'
                )
            },
            status=403
        )

    if cliente.estado != 'BLOQUEADO':
        return JsonResponse(
            {
                'ok': False,
                'error': (
                    'El cliente no está bloqueado.'
                )
            },
            status=400
        )

    try:

        cliente.estado = 'ACTIVO'

        cliente.save(
            update_fields=['estado']
        )

        return JsonResponse(
            {
                'ok': True,
                'id_usuario': cliente.id_usuario,
                'estado': cliente.estado,
                'mensaje': (
                    'Cliente desbloqueado correctamente.'
                )
            },
            status=200
        )

    except Exception as e:

        return JsonResponse(
            {
                'ok': False,
                'error': str(e)
            },
            status=400
        )