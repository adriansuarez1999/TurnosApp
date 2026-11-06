import json
import logging
from datetime import datetime
from django.db import transaction, DatabaseError
from django.http import JsonResponse
from apps.usuarios.models import Barbero, Usuario
from .models import Turno
from . import reglas
from .views import _error, _parsear_hora
from .views_notificaciones import crear_notificacion

logger = logging.getLogger(__name__)

# ══════════════════════════════════════════
# Sprint 7 - Módulo B (Facundo): reprogramación del turno por el cliente
# ══════════════════════════════════════════

TIPO_TURNO_REPROGRAMADO = 'TURNO_REPROGRAMADO'   # aviso al barbero


def _turno_reprogramado_a_dict(turno):
    return {
        'id_turno': turno.id_turno,
        'id_barbero': turno.id_barbero_id,
        'fecha': str(turno.fecha),
        'hora_inicio': turno.hora_inicio.strftime('%H:%M'),
        'hora_fin': turno.hora_fin.strftime('%H:%M'),
        'estado': turno.estado,
        'monto_total': float(turno.monto_total),
    }


# PATCH /api/turnos/<id>/reprogramar/
# body: {"fecha": "YYYY-MM-DD", "hora_inicio": "HH:MM", "id_barbero": <opcional>}
# Si no viene id_barbero se conserva el mismo barbero del turno.
#
# El turno original NO se toca hasta que la nueva franja pasó todas las
# validaciones y el barbero está bloqueado; el cambio es un único UPDATE dentro
# de la transacción. Ante cualquier error el turno queda exactamente como estaba.
# El monto no se recalcula: se mantiene el precio acordado al reservar.
def reprogramar_turno(request, id):
    if request.method != 'PATCH':
        return _error('Método no permitido', 405)

    id_cliente = request.session.get('id_usuario')
    if not id_cliente:
        return _error('Tenés que iniciar sesión.', 401)

    # Un cliente bloqueado tampoco puede reprogramar (es un camino más para crear turnos).
    try:
        cliente = Usuario.objects.get(id_usuario=id_cliente)
    except Usuario.DoesNotExist:
        return _error('Usuario no encontrado.', 404)

    if cliente.estado == 'BLOQUEADO':
        return _error(
            'Tu cuenta está bloqueada por inasistencias a turnos anteriores. Contactá a la barbería para más información.',
            403
        )

    if cliente.estado != 'ACTIVO':
        return _error('Tu cuenta no está activa. Contactá a la barbería para más información.', 403)

    try:
        data = json.loads(request.body)
    except ValueError:
        return _error('El cuerpo tiene que ser un JSON válido.', 400)

    if not isinstance(data, dict):
        return _error('El cuerpo tiene que ser un objeto JSON.', 400)

    try:
        fecha_str = data['fecha']
        hora_str = data['hora_inicio']
    except KeyError as e:
        return _error(f'Falta el campo {e}', 400)

    try:
        nueva_fecha = datetime.strptime(fecha_str, '%Y-%m-%d').date()
        nueva_hora = _parsear_hora(hora_str)
        id_barbero_nuevo = data.get('id_barbero')
        id_barbero_nuevo = int(id_barbero_nuevo) if id_barbero_nuevo not in (None, '') else None
    except (ValueError, TypeError, AttributeError):
        return _error('Barbero, fecha (YYYY-MM-DD) u hora (HH:MM) con formato inválido.', 400)

    try:
        with transaction.atomic():
            # Se bloquea el turno para que una cancelación y una reprogramación
            # simultáneas no se pisen.
            try:
                turno = Turno.objects.select_for_update().select_related(
                    'id_barbero__id_barberia', 'id_servicio__id_barberia'
                ).get(id_turno=id)
            except Turno.DoesNotExist:
                return _error('Turno no encontrado.', 404)

            if turno.id_cliente_id != id_cliente:
                return _error('No tenés permiso para reprogramar este turno.', 403)

            if turno.estado not in reglas.ESTADOS_MODIFICABLES_POR_CLIENTE:
                return _error(f'No se puede reprogramar un turno {turno.estado}.', 400)

            # Mismo plazo que la cancelación: si ya no puede cancelar, tampoco
            # puede mover el turno (si no, se saltearía la regla del dueño).
            if not reglas.puede_cancelar(turno):
                return _error(reglas.mensaje_fuera_de_plazo(turno).replace('cancelar', 'reprogramar'), 400)

            servicio = turno.id_servicio

            hora_fin, rechazo = reglas.validar_reglas_generales(servicio, nueva_fecha, nueva_hora)
            if rechazo:
                return _error(*rechazo)

            if id_barbero_nuevo and id_barbero_nuevo != turno.id_barbero_id:
                try:
                    barbero = Barbero.objects.select_related('id_usuario').get(id_barbero=id_barbero_nuevo)
                except Barbero.DoesNotExist:
                    return _error('Barbero no encontrado', 404)
            else:
                barbero = Barbero.objects.select_related('id_usuario').get(id_barbero=turno.id_barbero_id)

            rechazo = reglas.validar_barbero_para_servicio(barbero, servicio, nueva_fecha, nueva_hora, hora_fin)
            if rechazo:
                return _error(*rechazo)

            if (barbero.id_barbero == turno.id_barbero_id and nueva_fecha == turno.fecha
                    and nueva_hora == turno.hora_inicio):
                return _error('El turno ya está en ese horario.', 400)

            # Bloqueo por barbero y recién ahí se comprueba el solapamiento,
            # ignorando el propio turno (puede correrse 30 min sobre sí mismo).
            reglas.bloquear_barberos([turno.id_barbero_id, barbero.id_barbero])

            if reglas.hay_solapamiento(barbero.id_barbero, nueva_fecha, nueva_hora, hora_fin, excluir_turno=turno.id_turno):
                return _error('El horario ya está ocupado para ese barbero', 409)

            id_barbero_anterior = turno.id_barbero_id
            fecha_anterior = turno.fecha
            hora_anterior = turno.hora_inicio

            turno.id_barbero_id = barbero.id_barbero
            turno.fecha = nueva_fecha
            turno.hora_inicio = nueva_hora
            turno.hora_fin = hora_fin
            turno.updated_at = datetime.now()
            turno.save()

    except DatabaseError as e:
        # Última barrera: el trigger de la base rechazó un solapamiento.
        # La transacción se revirtió, así que el turno original sigue igual.
        if reglas.es_error_de_solapamiento(e):
            return _error('El horario ya está ocupado para ese barbero', 409)
        if reglas.es_error_de_concurrencia(e):
            return _error('Hubo muchas operaciones a la vez; intentá de nuevo.', 409)
        logger.exception('Error de base al reprogramar el turno %s', id)
        return _error('No se pudo reprogramar el turno.', 400)
    except Exception:
        logger.exception('Error inesperado al reprogramar el turno %s', id)
        return _error('No se pudo reprogramar el turno.', 400)

    mensaje = (
        f'El cliente reprogramó el turno del {fecha_anterior} {hora_anterior.strftime("%H:%M")} '
        f'para el {nueva_fecha} {nueva_hora.strftime("%H:%M")}.'
    )
    crear_notificacion(barbero.id_usuario_id, TIPO_TURNO_REPROGRAMADO, mensaje)

    # Si cambió de barbero, el anterior también tiene que enterarse de que se liberó el horario.
    if id_barbero_anterior != barbero.id_barbero:
        anterior = Barbero.objects.get(id_barbero=id_barbero_anterior)
        crear_notificacion(anterior.id_usuario_id, TIPO_TURNO_REPROGRAMADO, mensaje)

    return JsonResponse({'ok': True, 'turno': _turno_reprogramado_a_dict(turno)})
