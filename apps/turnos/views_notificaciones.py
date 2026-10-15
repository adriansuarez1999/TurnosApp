import logging
from datetime import datetime
from django.db import transaction
from django.http import JsonResponse
from apps.usuarios.models import Notificacion

logger = logging.getLogger(__name__)


# ══════════════════════════════════════════
# Sprint 6 - Módulo E (Gonzalo): notificaciones dentro de la app
#
# Decisión pendiente del sprint: cómo se marca una notificación como leída.
# Acá está la OPCIÓN A (sin tocar la base): PENDIENTE = sin leer y
# ENVIADA = leída. Si el equipo elige la opción B (agregar LEIDA al ENUM con
# un ALTER TABLE), solo hay que cambiar ESTADO_LEIDA.
#
# Este archivo NO importa views_barbero ni views: así los endpoints de
# turnos pueden importar crear_notificacion sin generar imports circulares.
# ══════════════════════════════════════════

ESTADO_SIN_LEER = 'PENDIENTE'
ESTADO_LEIDA = 'ENVIADA'

TIPO_TURNO_NUEVO = 'TURNO_NUEVO'                          # aviso al barbero
TIPO_TURNO_CANCELADO_CLIENTE = 'TURNO_CANCELADO_CLIENTE'  # aviso al barbero
TIPO_TURNO_CANCELADO_BARBERO = 'TURNO_CANCELADO_BARBERO'  # aviso al cliente
TIPO_TURNO_FINALIZADO = 'TURNO_FINALIZADO'                # aviso al cliente (invitación a calificar)

LIMITE_LISTADO = 50


# Tarea 1: helper único para generar avisos.
# Nunca rompe la operación que lo llama: si falla guardar el aviso, se
# registra en el log y se sigue (cancelar un turno no puede fallar porque
# no se pudo escribir una notificación). El atomic() interno crea un
# savepoint, así un error de base no invalida la transacción de quien llama.
def crear_notificacion(id_usuario, tipo, mensaje):
    try:
        with transaction.atomic():
            return Notificacion.objects.create(
                id_usuario_id=id_usuario,
                tipo=tipo,
                mensaje=mensaje,
                fecha_envio=datetime.now(),
                estado=ESTADO_SIN_LEER,
            )
    except Exception:
        logger.exception('No se pudo crear la notificación (usuario %s, tipo %s)', id_usuario, tipo)
        return None


def _notificacion_a_dict(n):
    return {
        'id': n.id_notificacion,
        'tipo': n.tipo,
        'mensaje': n.mensaje,
        'fecha': n.fecha_envio.strftime('%Y-%m-%d %H:%M'),
        'leida': n.estado == ESTADO_LEIDA,
    }


def _usuario_o_error(request):
    id_usuario = request.session.get('id_usuario')
    if not id_usuario:
        return None, JsonResponse({'ok': False, 'error': 'Tenés que iniciar sesión.'}, status=401)
    return id_usuario, None


# GET /api/notificaciones/
# Tarea 2: las notificaciones propias (más recientes primero, hasta 50) con
# la cantidad sin leer. Sirve para cualquier usuario logueado.
def mis_notificaciones(request):
    if request.method != 'GET':
        return JsonResponse({'ok': False, 'error': 'Método no permitido'}, status=405)

    id_usuario, error = _usuario_o_error(request)
    if error:
        return error

    propias = Notificacion.objects.filter(
        id_usuario=id_usuario, estado__in=(ESTADO_SIN_LEER, ESTADO_LEIDA)
    )
    sin_leer = propias.filter(estado=ESTADO_SIN_LEER).count()
    recientes = propias.order_by('-fecha_envio', '-id_notificacion')[:LIMITE_LISTADO]

    return JsonResponse({
        'ok': True,
        'sin_leer': sin_leer,
        'notificaciones': [_notificacion_a_dict(n) for n in recientes],
    })


# PATCH /api/notificaciones/<id>/leida/
# Marca una notificación propia como leída (si ya lo estaba, no cambia nada).
def marcar_leida(request, id):
    if request.method != 'PATCH':
        return JsonResponse({'ok': False, 'error': 'Método no permitido'}, status=405)

    id_usuario, error = _usuario_o_error(request)
    if error:
        return error

    try:
        notificacion = Notificacion.objects.get(id_notificacion=id)
    except Notificacion.DoesNotExist:
        return JsonResponse({'ok': False, 'error': 'Notificación no encontrada.'}, status=404)

    if notificacion.id_usuario_id != id_usuario:
        return JsonResponse({'ok': False, 'error': 'Esa notificación no es tuya.'}, status=403)

    if notificacion.estado == ESTADO_SIN_LEER:
        notificacion.estado = ESTADO_LEIDA
        notificacion.save(update_fields=['estado'])

    return JsonResponse({'ok': True, 'notificacion': _notificacion_a_dict(notificacion)})


# PATCH /api/notificaciones/leidas/
# Marca todas las notificaciones propias como leídas.
def marcar_todas_leidas(request):
    if request.method != 'PATCH':
        return JsonResponse({'ok': False, 'error': 'Método no permitido'}, status=405)

    id_usuario, error = _usuario_o_error(request)
    if error:
        return error

    marcadas = Notificacion.objects.filter(
        id_usuario=id_usuario, estado=ESTADO_SIN_LEER
    ).update(estado=ESTADO_LEIDA)

    return JsonResponse({'ok': True, 'marcadas': marcadas})