import json
from datetime import datetime
from django.http import JsonResponse
from django.db import transaction
from apps.usuarios.models import Usuario
from apps.usuarios.views import _barbero_logueado
from .models import Turno
from .views import _turno_calendario_a_dict
from .views_notificaciones import (
    crear_notificacion,
    TIPO_TURNO_CANCELADO_BARBERO,
    TIPO_TURNO_FINALIZADO,
)

# ══════════════════════════════════════════
# Sprint 6 - Módulo B: Agenda y gestión de turnos del barbero
# Ningún endpoint recibe un id de barbero: el backend lo deduce de la sesión
# con _barbero_logueado(). El criterio de pertenencia es "este turno es mío".
# ══════════════════════════════════════════

def _requerir_barbero(request):
    # Devuelve (barbero, None) o (None, respuesta_de_error).
    if not request.session.get('id_usuario'):
        return None, JsonResponse({'ok': False, 'error': 'Tenés que iniciar sesión.'}, status=401)

    barbero = _barbero_logueado(request)
    if not barbero:
        return None, JsonResponse({'ok': False, 'error': 'No sos barbero.'}, status=403)

    return barbero, None


def _turno_agenda_a_dict(turno):
    datos = _turno_calendario_a_dict(turno)
    # El front lo necesita para abrir el historial del cliente (Tarea 4).
    datos['id_cliente'] = turno.id_cliente_id
    return datos


# GET /api/mi-agenda/turnos/?desde=YYYY-MM-DD&hasta=YYYY-MM-DD
# Tarea 1: turnos del barbero de la sesión en el rango pedido, ordenados por
# fecha y hora. 400 si falta desde/hasta, si el formato es inválido o si el
# rango está invertido.
def mi_agenda_turnos(request):
    if request.method != 'GET':
        return JsonResponse({'ok': False, 'error': 'Método no permitido'}, status=405)

    barbero, error = _requerir_barbero(request)
    if error:
        return error

    desde = request.GET.get('desde')
    hasta = request.GET.get('hasta')
    if not desde or not hasta:
        return JsonResponse({'ok': False, 'error': 'Los parámetros desde y hasta son obligatorios.'}, status=400)

    try:
        desde = datetime.strptime(desde, '%Y-%m-%d').date()
        hasta = datetime.strptime(hasta, '%Y-%m-%d').date()
    except ValueError:
        return JsonResponse({'ok': False, 'error': 'Las fechas tienen que tener formato YYYY-MM-DD.'}, status=400)

    if desde > hasta:
        return JsonResponse({'ok': False, 'error': 'La fecha desde no puede ser posterior a hasta.'}, status=400)

    turnos = Turno.objects.filter(
        id_barbero=barbero.id_barbero,
        fecha__gte=desde,
        fecha__lte=hasta
    ).select_related('id_cliente', 'id_servicio').order_by('fecha', 'hora_inicio')

    return JsonResponse({
        'ok': True,
        'turnos': [_turno_agenda_a_dict(t) for t in turnos]
    })


def _ya_empezo(turno):
    inicio = datetime.combine(turno.fecha, turno.hora_inicio)
    return inicio <= datetime.now()


# Valida pertenencia y estado dentro de una transacción (con el turno bloqueado
# para que dos pedidos simultáneos no lo cierren dos veces) y aplica el cambio.
# 'debe_haber_empezado' distingue finalizar/ausente (True) de cancelar (False).
def _cambiar_estado_turno(request, id, nuevo_estado, debe_haber_empezado):
    if request.method != 'PATCH':
        return JsonResponse({'ok': False, 'error': 'Método no permitido'}, status=405)

    barbero, error = _requerir_barbero(request)
    if error:
        return error

    with transaction.atomic():
        try:
            turno = Turno.objects.select_for_update().get(id_turno=id)
        except Turno.DoesNotExist:
            return JsonResponse({'ok': False, 'error': 'Turno no encontrado.'}, status=404)

        if turno.id_barbero_id != barbero.id_barbero:
            return JsonResponse({'ok': False, 'error': 'Ese turno no es tuyo.'}, status=403)

        if turno.estado != 'CONFIRMADO':
            return JsonResponse({
                'ok': False,
                'error': f'Solo se puede modificar un turno CONFIRMADO (este está {turno.estado}).'
            }, status=400)

        if debe_haber_empezado and not _ya_empezo(turno):
            return JsonResponse({
                'ok': False,
                'error': 'El turno todavía no empezó, no se puede cerrar.'
            }, status=400)

        if not debe_haber_empezado and _ya_empezo(turno):
            return JsonResponse({
                'ok': False,
                'error': 'El turno ya empezó, no se puede cancelar. Marcalo como finalizado o ausente.'
            }, status=400)

        turno.estado = nuevo_estado
        turno.updated_at = datetime.now()
        turno.save()

    return turno


# PATCH /api/mi-agenda/turnos/<id>/finalizar/
# Tarea 2: solo turnos propios, solo desde CONFIRMADO y solo si ya empezó.
def finalizar_turno(request, id):
    resultado = _cambiar_estado_turno(request, id, 'FINALIZADO', True)
    if isinstance(resultado, JsonResponse):
        return resultado

    # Notificación al cliente para que califique
    crear_notificacion(
        resultado.id_cliente_id,
        TIPO_TURNO_FINALIZADO,
        'Tu turno fue finalizado. Ya podés calificar la atención recibida.'
    )

    return JsonResponse({'ok': True, 'turno': _turno_agenda_a_dict(resultado)})
# PATCH /api/mi-agenda/turnos/<id>/ausente/
# Tarea 2: mismas reglas que finalizar.
def ausente_turno(request, id):
    resultado = _cambiar_estado_turno(request, id, 'AUSENTE', True)
    if isinstance(resultado, JsonResponse):
        return resultado
    return JsonResponse({'ok': True, 'turno': _turno_agenda_a_dict(resultado)})


# PATCH /api/mi-agenda/turnos/<id>/cancelar/   (body opcional: {"motivo": "..."})
# Tarea 3: cancelación por imposibilidad del barbero. Solo turnos propios,
# solo desde CONFIRMADO y solo si todavía no empezó. No penaliza al cliente
# y libera el horario (las consultas de disponibilidad excluyen CANCELADO).
def cancelar_turno_barbero(request, id):
    motivo = ''
    if request.method == 'PATCH' and request.body:
        try:
            data = json.loads(request.body)
        except ValueError:
            return JsonResponse({'ok': False, 'error': 'El cuerpo tiene que ser un JSON válido.'}, status=400)

        if not isinstance(data, dict):
            return JsonResponse({'ok': False, 'error': 'El cuerpo tiene que ser un objeto JSON.'}, status=400)

        motivo = data.get('motivo') or ''
        if not isinstance(motivo, str):
            return JsonResponse({'ok': False, 'error': 'El motivo tiene que ser texto.'}, status=400)

        motivo = motivo.strip()
        if len(motivo) > 255:
            return JsonResponse({'ok': False, 'error': 'El motivo no puede superar los 255 caracteres.'}, status=400)

    resultado = _cambiar_estado_turno(request, id, 'CANCELADO', False)
    if isinstance(resultado, JsonResponse):
        return resultado

    # Notificación al cliente
    mensaje = f'Tu turno del {resultado.fecha} a las {resultado.hora_inicio.strftime("%H:%M")} fue cancelado por el barbero.'
    if motivo:
        mensaje += f' Motivo: {motivo}'

    crear_notificacion(
        resultado.id_cliente_id,
        TIPO_TURNO_CANCELADO_BARBERO,
        mensaje
    )

    return JsonResponse({
        'ok': True,
        'turno': _turno_agenda_a_dict(resultado),
        'motivo': motivo or None
    })


# GET /api/mi-agenda/clientes/<id>/historial/
# Tarea 4: totales del cliente en la barbería del barbero. Se valida que el
# cliente tenga al menos un turno con ESTE barbero (no alcanza con que exista).
def historial_cliente(request, id):
    if request.method != 'GET':
        return JsonResponse({'ok': False, 'error': 'Método no permitido'}, status=405)

    barbero, error = _requerir_barbero(request)
    if error:
        return error

    if not Turno.objects.filter(id_cliente_id=id, id_barbero=barbero.id_barbero).exists():
        return JsonResponse({'ok': False, 'error': 'Ese cliente no tiene turnos con vos.'}, status=403)

    try:
        cliente = Usuario.objects.get(id_usuario=id)
    except Usuario.DoesNotExist:
        return JsonResponse({'ok': False, 'error': 'Cliente no encontrado.'}, status=404)

    turnos_en_barberia = Turno.objects.filter(
        id_cliente_id=id, id_barbero__id_barberia=barbero.id_barberia_id
    )

    return JsonResponse({
        'ok': True,
        'id_cliente': cliente.id_usuario,
        'cliente': f'{cliente.nombre} {cliente.apellido}',
        'turnos_totales': turnos_en_barberia.count(),
        'turnos_finalizados': turnos_en_barberia.filter(estado='FINALIZADO').count(),
        'turnos_ausente': turnos_en_barberia.filter(estado='AUSENTE').count(),
        'turnos_cancelados': turnos_en_barberia.filter(estado='CANCELADO').count(),
    })
