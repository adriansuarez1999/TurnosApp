from datetime import datetime, timedelta
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.db import transaction, DatabaseError
import json
import logging
from decimal import Decimal
from apps.barberias.models import Barberia
from apps.usuarios.models import Barbero, Servicio, Usuario, Disponibilidad , Promocion, Calificacion, Pago
from .models import Turno
from . import reglas
from .views_notificaciones import (
    crear_notificacion,
    TIPO_TURNO_NUEVO,
    TIPO_TURNO_CANCELADO_CLIENTE,
)
logger = logging.getLogger(__name__)


def _usuario_logueado(request):
    return request.session.get('id_usuario')


def _barberia_del_dueno(id_usuario):
    return Barberia.objects.filter(id_dueno=id_usuario).first()


# Mismo formato que usa Facundo en apps/barberias/views.py (DIAS_VALIDOS):
# 'LUN', 'MAR', 'MIE', 'JUE', 'VIE', 'SAB', 'DOM'.
# date.weekday() de Python devuelve 0=lunes ... 6=domingo, coincide el orden.
DIAS_SEMANA = ['LUN', 'MAR', 'MIE', 'JUE', 'VIE', 'SAB', 'DOM']


def _dia_semana_de(fecha):
    return DIAS_SEMANA[fecha.weekday()]
# ════════════════════════════════════════════════════════════════
# Sprint 7 - Módulo A (Facundo): el backend es la autoridad sobre cada reserva.
# Reglas compartidas con cancelar/reprogramar en apps/turnos/reglas.py
# ════════════════════════════════════════════════════════════════
def _error(mensaje, status):
    return JsonResponse({'ok': False, 'error': mensaje}, status=status)


def crear_turno(request):
    if request.method != 'POST':
        return JsonResponse({'ok': False, 'error': 'Método no permitido'}, status=405)

    id_cliente = request.session.get('id_usuario')
    if not id_cliente:
        return JsonResponse({'ok': False, 'error': 'Tenés que iniciar sesión para reservar un turno.'}, status=401)

    # Sprint 4 - Módulo B, Tarea 4: un cliente bloqueado no puede reservar.
    try:
        cliente = Usuario.objects.get(id_usuario=id_cliente)
    except Usuario.DoesNotExist:
        return JsonResponse({'ok': False, 'error': 'Usuario no encontrado.'}, status=404)

    if cliente.estado == 'BLOQUEADO':
        return JsonResponse({
            'ok': False,
            'error': 'Tu cuenta está bloqueada por inasistencias a turnos anteriores. Contactá a la barbería para más información.'
        }, status=403)

    if cliente.estado != 'ACTIVO':
        return _error('Tu cuenta no está activa. Contactá a la barbería para más información.', 403)

    try:
        data = json.loads(request.body)
    except ValueError:
        return _error('El cuerpo tiene que ser un JSON válido.', 400)

    if not isinstance(data, dict):
        return _error('El cuerpo tiene que ser un objeto JSON.', 400)

    try:
        id_barbero = data.get('id_barbero')   # puede venir None → asignación automática
        id_servicio = data['id_servicio']
        fecha = data['fecha']
        hora_inicio_str = data['hora_inicio']

        try:
            id_servicio = int(id_servicio)
            id_barbero = int(id_barbero) if id_barbero not in (None, '') else None
            hora_inicio = _parsear_hora(hora_inicio_str)
            fecha_dt = datetime.strptime(fecha, '%Y-%m-%d').date()
        except (ValueError, TypeError, AttributeError):
            return _error('Servicio, barbero, fecha (YYYY-MM-DD) u hora (HH:MM) con formato inválido.', 400)

        try:
            servicio = Servicio.objects.select_related('id_barberia').get(id_servicio=id_servicio)
        except Servicio.DoesNotExist:
            return JsonResponse({'ok': False, 'error': 'Servicio no encontrado'}, status=404)

        hora_fin, rechazo = reglas.validar_reglas_generales(servicio, fecha_dt, hora_inicio)
        if rechazo:
            return _error(*rechazo)

        if id_barbero:
            try:
                barbero = Barbero.objects.select_related('id_usuario').get(id_barbero=id_barbero)
            except Barbero.DoesNotExist:
                return JsonResponse({'ok': False, 'error': 'Barbero no encontrado'}, status=404)

            rechazo = reglas.validar_barbero_para_servicio(barbero, servicio, fecha_dt, hora_inicio, hora_fin)
            if rechazo:
                return _error(*rechazo)

            candidatos = [barbero]
        else:
            # Asignación automática: solo barberos de la barbería del servicio
            # que estén activos y atiendan en ese horario.
            candidatos = [
                c for c in Barbero.objects.select_related('id_usuario').filter(
                    id_barberia=servicio.id_barberia_id
                ).order_by('id_barbero')
                if reglas.validar_barbero_para_servicio(c, servicio, fecha_dt, hora_inicio, hora_fin) is None
            ]
            if not candidatos:
                return _error('No hay barberos disponibles en ese horario', 409)

        with transaction.atomic():

            # Bloqueo por barbero ANTES de comprobar solapamientos: sin esto,
            # dos pedidos simultáneos para la misma franja pasan los dos.
            reglas.bloquear_barberos([c.id_barbero for c in candidatos])

            barbero = None
            for candidato in candidatos:
                if not reglas.hay_solapamiento(candidato.id_barbero, fecha_dt, hora_inicio, hora_fin):
                    barbero = candidato
                    break

            if barbero is None:
                if id_barbero:
                    return JsonResponse({
                        'ok': False,
                        'error': 'El horario ya está ocupado para ese barbero'
                    }, status=409)
                return JsonResponse({
                    'ok': False,
                    'error': 'No hay barberos disponibles en ese horario'
                }, status=409)

            id_barbero = barbero.id_barbero

            # ════════════════════════════════════════════════════════════════
            # Sprint 5 - Módulo D (Tarea 5): Aplicar descuento de promoción
            # ════════════════════════════════════════════════════════════════
            monto_final = Decimal(str(servicio.precio))
            promo = Promocion.objects.filter(
                id_servicio=id_servicio,
                activa=1,
                fecha_inicio__lte=fecha_dt,
                fecha_fin__gte=fecha_dt
            ).first()

            if promo:
                descuento = (monto_final * promo.porcentaje_descuento) / Decimal('100')
                monto_final = monto_final - descuento

            turno = Turno.objects.create(
                id_cliente_id=id_cliente,
                id_barbero_id=id_barbero,
                id_servicio_id=id_servicio,
                fecha=fecha_dt,
                hora_inicio=hora_inicio,
                hora_fin=hora_fin,
                estado='CONFIRMADO',
                monto_total=monto_final,
                fecha_reserva=datetime.now(),
                created_at=datetime.now(),
                updated_at=datetime.now(),
                created_by_id=id_cliente
            )

            # ════════════════════════════════════════════════════════════════
            # Sprint 6 - Faltante 1: Notificación automática al barbero asignado
            # ════════════════════════════════════════════════════════════════
            crear_notificacion(
                barbero.id_usuario_id,
                TIPO_TURNO_NUEVO,
                f'Nuevo turno: {servicio.nombre} {fecha_dt} {hora_inicio.strftime("%H:%M")}.'
            )

        return JsonResponse({
            'ok': True,
            'id_turno': turno.id_turno,
            'id_barbero': id_barbero,
            'hora_inicio': hora_inicio.strftime('%H:%M'),
            'hora_fin': hora_fin.strftime('%H:%M'),
            'estado': turno.estado,
            'monto_total': float(turno.monto_total)
        })

    except KeyError as e:
        return JsonResponse({'ok': False, 'error': f'Falta el campo {e}'}, status=400)
    except DatabaseError as e:
        # Última barrera: el trigger de la base rechazó un solapamiento.
        if reglas.es_error_de_solapamiento(e):
            return _error('El horario ya está ocupado para ese barbero', 409)
        if reglas.es_error_de_concurrencia(e):
            return _error('Hubo muchas reservas a la vez; intentá de nuevo.', 409)
        logger.exception('Error de base al crear un turno')
        return _error('No se pudo crear el turno.', 400)
    except Exception:
        logger.exception('Error inesperado al crear un turno')
        return _error('No se pudo crear el turno.', 400)

def _parsear_hora(valor):
    # Acepta 'HH:MM' o 'HH:MM:SS'
    formato = '%H:%M:%S' if valor.count(':') == 2 else '%H:%M'
    return datetime.strptime(valor, formato).time()


@csrf_exempt
def turnos_disponibles(request):
    # GET /turnos/disponibles/?fecha=<yyyy-mm-dd>&barbero=<id>
    # o  GET /turnos/disponibles/?fecha=<yyyy-mm-dd>&barberia=<id>  (sin barbero puntual)
    # Sprint 7: parámetros opcionales
    #   &servicio=<id>        el horario solo es válido si el servicio ENTERO entra
    #   &excluir_turno=<id>   ignora ese turno (para reprogramar sin chocar con el propio)
    # Cada horario trae 'estado': DISPONIBLE, OCUPADO o NO_PERMITIDO (pasado,
    # fuera de rango o el servicio no entra en la disponibilidad del barbero).
    if request.method != 'GET':
        return JsonResponse({'error': 'Metodo no permitido'}, status=405)

    try:
        id_barbero = request.GET.get('barbero')
        id_barberia = request.GET.get('barberia')
        id_servicio = request.GET.get('servicio')
        excluir_turno = request.GET.get('excluir_turno')
        fecha = request.GET.get('fecha')

        if not fecha or (not id_barbero and not id_barberia):
            return JsonResponse({
                'error': 'Falta la fecha, y el barbero o la barbería.'
            }, status=400)

        fecha_obj = datetime.strptime(fecha, '%Y-%m-%d').date()
        dia_semana = _dia_semana_de(fecha_obj)

        duracion_bloque = reglas.DURACION_BLOQUE_MINUTOS
        duracion_servicio = duracion_bloque
        if id_servicio:
            try:
                servicio = Servicio.objects.get(id_servicio=int(id_servicio))
            except Servicio.DoesNotExist:
                return JsonResponse({'error': 'Servicio no encontrado'}, status=404)
            duracion_servicio = servicio.duracion_minutos

        if id_barbero:
            ids_barberos = [int(id_barbero)]
        else:
            ids_barberos = list(
                Barbero.objects.filter(id_barberia=id_barberia).values_list('id_barbero', flat=True)
            )

        # Solo barberos activos, y (si se pidió un servicio) de su misma barbería.
        barberos_validos = Barbero.objects.filter(
            id_barbero__in=ids_barberos
        ).exclude(id_usuario__estado='INACTIVO')
        if id_servicio:
            barberos_validos = barberos_validos.filter(id_barberia=servicio.id_barberia_id)
        ids_barberos = list(barberos_validos.values_list('id_barbero', flat=True))

        # Bloques de disponibilidad configurados por el dueño para ESOS
        # barberos, en ESE día de la semana (ya no hay franja fija 14-21
        # para todos: cada barbero atiende según lo que se le cargó).
        bloques_por_barbero = {}
        for bloque in Disponibilidad.objects.filter(id_barbero__in=ids_barberos, dia_semana=dia_semana):
            bloques_por_barbero.setdefault(bloque.id_barbero_id, []).append(
                (bloque.hora_inicio, bloque.hora_fin)
            )

        turnos_ocupados = Turno.objects.filter(
            id_barbero__in=ids_barberos,
            fecha=fecha_obj
        ).exclude(estado__in=reglas.ESTADOS_QUE_LIBERAN_HORARIO)
        if excluir_turno:
            turnos_ocupados = turnos_ocupados.exclude(id_turno=int(excluir_turno))
        turnos_ocupados = list(turnos_ocupados)

        # Juntamos todos los horarios de 30 min que caen DENTRO de algún
        # bloque de disponibilidad de alguno de los barberos candidatos.
        horarios_posibles = set()
        for rangos in bloques_por_barbero.values():
            for hora_inicio_bloque, hora_fin_bloque in rangos:
                actual = datetime.combine(fecha_obj, hora_inicio_bloque)
                fin_bloque_dt = datetime.combine(fecha_obj, hora_fin_bloque)
                while actual + timedelta(minutes=duracion_bloque) <= fin_bloque_dt:
                    horarios_posibles.add(actual.time())
                    actual += timedelta(minutes=duracion_bloque)

        ahora = datetime.now()
        fuera_de_rango = fecha_obj > ahora.date() + timedelta(days=reglas.MAX_DIAS_ANTICIPACION_RESERVA)

        horarios = []
        for bloque_inicio in sorted(horarios_posibles):
            inicio_dt = datetime.combine(fecha_obj, bloque_inicio)
            bloque_fin_dt = inicio_dt + timedelta(minutes=duracion_servicio)
            # Si el servicio cruza la medianoche, bloque_fin queda en otro día
            # y ningún bloque lo contiene.
            bloque_fin = bloque_fin_dt.time() if bloque_fin_dt.date() == fecha_obj else None

            # NO_PERMITIDO: ya pasó o está fuera del máximo de anticipación.
            permitido = inicio_dt > ahora and not fuera_de_rango

            # libre si ALGÚN barbero de la lista atiende en ese horario
            # (según su disponibilidad cargada) Y no tiene un turno ahí.
            libre_en_alguno = False
            atiende_alguno = False
            for bid in ids_barberos:
                atiende_en_este_horario = bloque_fin is not None and any(
                    ini <= bloque_inicio and bloque_fin <= fin
                    for ini, fin in bloques_por_barbero.get(bid, [])
                )
                if not atiende_en_este_horario:
                    continue
                atiende_alguno = True

                ocupado = any(
                    bloque_inicio < t.hora_fin and bloque_fin > t.hora_inicio
                    for t in turnos_ocupados if t.id_barbero_id == bid
                )
                if not ocupado:
                    libre_en_alguno = True
                    break

            if not permitido or not atiende_alguno:
                estado = 'NO_PERMITIDO'
            elif libre_en_alguno:
                estado = 'DISPONIBLE'
            else:
                estado = 'OCUPADO'

            horarios.append({
                'hora': bloque_inicio.strftime('%H:%M'),
                'disponible': estado == 'DISPONIBLE',
                'estado': estado,
            })

        return JsonResponse(horarios, safe=False)

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)
def cancelar_turno(request, id):
    if request.method == 'PATCH':
        id_cliente = request.session.get('id_usuario')
        if not id_cliente:
            return JsonResponse({'ok': False, 'error': 'Tenés que iniciar sesión.'}, status=401)

        try:
            # Sprint 7 - Módulo B: con el turno bloqueado, dos pedidos
            # simultáneos no lo cancelan dos veces ni se pisan con una reprogramación.
            with transaction.atomic():
                try:
                    turno = Turno.objects.select_for_update().select_related(
                        'id_barbero__id_barberia', 'id_barbero__id_usuario'
                    ).get(id_turno=id)
                except Turno.DoesNotExist:
                    return JsonResponse({'ok': False, 'error': 'Turno no encontrado.'}, status=404)

                if turno.id_cliente_id != id_cliente:
                    return JsonResponse({
                        'ok': False,
                        'error': 'No tenes permiso para cancelar este turno.'
                    }, status=403)

                if turno.estado not in reglas.ESTADOS_MODIFICABLES_POR_CLIENTE:
                    return JsonResponse({
                        'ok': False,
                        'error': f'No se puede cancelar un turno {turno.estado}.'
                    }, status=400)

                # Sprint 7 - Módulo B: ventana de cancelación configurada por el
                # dueño. Solo aplica al cliente; el barbero cancela por otra ruta
                # (views_barbero.cancelar_turno_barbero) y no pasa por acá.
                if not reglas.puede_cancelar(turno):
                    return JsonResponse({
                        'ok': False,
                        'error': reglas.mensaje_fuera_de_plazo(turno),
                        'fecha_limite_cancelacion': reglas.fecha_limite_cancelacion(turno).strftime('%Y-%m-%d %H:%M'),
                    }, status=400)

                turno.estado = 'CANCELADO'
                turno.updated_at = datetime.now()
                turno.save()

            # ════════════════════════════════════════════════════════════════
            # Sprint 6 - Faltante 1: Notificar al barbero cuando el cliente cancela
            # ════════════════════════════════════════════════════════════════
            crear_notificacion(
                turno.id_barbero.id_usuario_id,
                TIPO_TURNO_CANCELADO_CLIENTE,
                f'El cliente canceló el turno del {turno.fecha} a las {turno.hora_inicio.strftime("%H:%M")}.'
            )

            return JsonResponse({
                'ok': True,
                'id_turno': turno.id_turno,
                'estado': turno.estado,
            }, status=200)

        except Exception as e:
            logger.exception('Error al cancelar el turno %s', id)
            return JsonResponse({'ok': False, 'error': 'No se pudo cancelar el turno.'}, status=400)

    return JsonResponse({'ok': False, 'error': 'Metodo no permitido'}, status=405)

def mis_turnos(request):
    if request.method == 'GET':
        id_cliente = request.session.get('id_usuario')
        if not id_cliente:
            return JsonResponse({'error': 'Tenés que iniciar sesión.'}, status=401)

        try:
            hoy = datetime.now().date()

            # select_related: el serializador lee barbería, barbero y servicio de cada turno.
            proximos = Turno.objects.filter(
                id_cliente=id_cliente,
                fecha__gte=hoy
            ).select_related(
                'id_barbero__id_barberia', 'id_barbero__id_usuario', 'id_servicio'
            ).order_by('fecha', 'hora_inicio')

            pasados = Turno.objects.filter(
                id_cliente=id_cliente,
                fecha__lt=hoy
            ).select_related(
                'id_barbero__id_barberia', 'id_barbero__id_usuario', 'id_servicio'
            ).order_by('-fecha', '-hora_inicio')

            # Sprint 6 - Módulo D: para mostrar "Calificar" solo en los turnos sin calificar.
            calificados = set(Calificacion.objects.filter(
                id_cliente=id_cliente
            ).values_list('id_turno', flat=True))

            # Sprint 7 - Módulo C: turnos de este cliente con el cobro ya confirmado por el barbero.
            cobrados = set(Pago.objects.filter(
                id_turno__id_cliente=id_cliente,
                tipo_pago='TOTAL',
                estado='APROBADO',
            ).values_list('id_turno', flat=True))

            ahora = datetime.now()

            def serializar(turno):
                barberia = turno.id_barbero.id_barberia
                modificable = turno.estado in reglas.ESTADOS_MODIFICABLES_POR_CLIENTE
                finalizado = turno.estado == 'FINALIZADO'
                return {
                    'id': turno.id_turno,
                    'barberia': barberia.nombre,
                    'barbero': f'{turno.id_barbero.id_usuario.nombre} {turno.id_barbero.id_usuario.apellido}',
                    'servicio': turno.id_servicio.nombre,
                    'fecha': str(turno.fecha),
                    'hora': turno.hora_inicio.strftime('%H:%M'),
                    'estado': turno.estado,
                    'calificado': turno.id_turno in calificados,
                    # Sprint 7 - Módulo B: el backend decide; el front solo muestra.
                    # Es la misma regla que aplica cancelar_turno, así que nunca se contradicen.
                    'puede_cancelar': reglas.puede_cancelar(turno, ahora),
                    'fecha_limite_cancelacion': (
                        reglas.fecha_limite_cancelacion(turno).strftime('%Y-%m-%d %H:%M')
                        if modificable else None
                    ),
                    # Sprint 7 - Módulo C: el alias es informativo (BarberApp no verifica la
                    # transferencia) y solo se expone en turnos FINALIZADOS. None = la barbería
                    # no cargó alias: el front debe decir que consulte con la barbería.
                    'alias_cobro': barberia.alias_cobro if finalizado else None,
                    'cobro_registrado': turno.id_turno in cobrados,
                }

            lista = [serializar(t) for t in proximos] + [serializar(t) for t in pasados]
            return JsonResponse(lista, safe=False)

        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)

    return JsonResponse({'error': 'Metodo no permitido'}, status=405)

# ══════════════════════════════════════════
# Sprint 4 - Módulo B: Bloqueo de clientes ausentes (CU-13)
# Bloqueo GLOBAL: reutiliza usuario.estado (ACTIVO / BLOQUEADO / INACTIVO).
# Si el equipo define que sea por barbería, esto hay que migrarlo a una
# tabla intermedia — avisar antes de tocarlo a mitad de sprint.
# ══════════════════════════════════════════

def _cliente_a_dict(cliente, barberia):
    turnos_en_esta_barberia = Turno.objects.filter(
        id_cliente=cliente, id_barbero__id_barberia=barberia
    )
    return {
        'id_usuario': cliente.id_usuario,
        'nombre': cliente.nombre,
        'apellido': cliente.apellido,
        'email': cliente.email,
        'telefono': cliente.telefono,
        'estado': cliente.estado,
        'turnos_totales': turnos_en_esta_barberia.count(),
        'turnos_ausente': turnos_en_esta_barberia.filter(estado='AUSENTE').count(),
    }


# GET /api/mi-barberia/clientes/
# Tarea 1: clientes que reservaron en la barbería propia, con su cantidad
# de turnos AUSENTE, para identificar a quién conviene bloquear.
def clientes_barberia(request):
    if request.method != 'GET':
        return JsonResponse({'ok': False, 'error': 'Método no permitido'}, status=405)

    id_usuario = _usuario_logueado(request)
    if not id_usuario:
        return JsonResponse({'ok': False, 'error': 'Tenés que iniciar sesión.'}, status=401)

    barberia = _barberia_del_dueno(id_usuario)
    if not barberia:
        return JsonResponse({'ok': False, 'error': 'No tenés una barbería registrada.'}, status=404)

    ids_clientes = Turno.objects.filter(
        id_barbero__id_barberia=barberia
    ).values_list('id_cliente', flat=True).distinct()

    clientes = Usuario.objects.filter(id_usuario__in=ids_clientes)

    data = [_cliente_a_dict(c, barberia) for c in clientes]
    data.sort(key=lambda c: c['turnos_ausente'], reverse=True)

    return JsonResponse({'ok': True, 'clientes': data})


def _cambiar_estado_cliente(request, id, nuevo_estado):
    if request.method not in ('PATCH', 'POST'):
        return JsonResponse({'ok': False, 'error': 'Método no permitido'}, status=405)

    id_usuario = _usuario_logueado(request)
    if not id_usuario:
        return JsonResponse({'ok': False, 'error': 'Tenés que iniciar sesión.'}, status=401)

    barberia = _barberia_del_dueno(id_usuario)
    if not barberia:
        return JsonResponse({'ok': False, 'error': 'No tenés una barbería registrada.'}, status=404)

    # Pertenencia (mismo criterio del Sprint 3): el cliente tiene que haber
    # reservado en ESTA barbería. No alcanza con que el id_usuario exista.
    tiene_turno_aca = Turno.objects.filter(
        id_cliente_id=id, id_barbero__id_barberia=barberia
    ).exists()
    if not tiene_turno_aca:
        return JsonResponse({'ok': False, 'error': 'Ese cliente no tiene turnos en tu barbería.'}, status=403)

    try:
        cliente = Usuario.objects.get(id_usuario=id)
    except Usuario.DoesNotExist:
        return JsonResponse({'ok': False, 'error': 'Cliente no encontrado.'}, status=404)

    cliente.estado = nuevo_estado
    cliente.save()

    return JsonResponse({'ok': True, 'id_usuario': cliente.id_usuario, 'estado': cliente.estado})


# PATCH /api/mi-barberia/clientes/<id>/bloquear/
# Tarea 2: bloqueo global (usuario.estado = 'BLOQUEADO')
def bloquear_cliente(request, id):
    return _cambiar_estado_cliente(request, id, 'BLOQUEADO')


# PATCH /api/mi-barberia/clientes/<id>/desbloquear/
# Tarea 3: acción inversa
def desbloquear_cliente(request, id):
    return _cambiar_estado_cliente(request, id, 'ACTIVO')


# ══════════════════════════════════════════
# Sprint 5 - Módulo C: Calendario de turnos por barbero
# Solo lectura: consulta turnos, nunca los crea ni los modifica.
# ══════════════════════════════════════════

def _turno_calendario_a_dict(turno):
    return {
        'id': turno.id_turno,
        'cliente': f'{turno.id_cliente.nombre} {turno.id_cliente.apellido}',
        'servicio': turno.id_servicio.nombre,
        'fecha': str(turno.fecha),
        'hora_inicio': turno.hora_inicio.strftime('%H:%M'),
        'hora_fin': turno.hora_fin.strftime('%H:%M'),
        'estado': turno.estado,
        'monto': float(turno.monto_total),
    }


# GET /api/mi-barberia/barberos/<id>/turnos/?desde=YYYY-MM-DD&hasta=YYYY-MM-DD
# Tarea 1: turnos del barbero en el rango pedido (valida pertenencia).
# Tarea 2: ordenados por fecha y hora_inicio.
# Tarea 3: 400 si falta desde/hasta, si el formato es inválido o si desde > hasta.
def turnos_por_barbero(request, id):
    if request.method != 'GET':
        return JsonResponse({'ok': False, 'error': 'Método no permitido'}, status=405)

    id_usuario = _usuario_logueado(request)
    if not id_usuario:
        return JsonResponse({'ok': False, 'error': 'Tenés que iniciar sesión.'}, status=401)

    barberia = _barberia_del_dueno(id_usuario)
    if not barberia:
        return JsonResponse({'ok': False, 'error': 'No tenés una barbería registrada.'}, status=404)

    try:
        barbero = Barbero.objects.get(id_barbero=id)
    except Barbero.DoesNotExist:
        return JsonResponse({'ok': False, 'error': 'Barbero no encontrado.'}, status=404)

    # Mismo chequeo de pertenencia que en el resto del panel.
    if barbero.id_barberia_id != barberia.id_barberia:
        return JsonResponse({'ok': False, 'error': 'Ese barbero no pertenece a tu barbería.'}, status=403)

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
        'barbero': f'{barbero.id_usuario.nombre} {barbero.id_usuario.apellido}',
        'turnos': [_turno_calendario_a_dict(t) for t in turnos]
    })
