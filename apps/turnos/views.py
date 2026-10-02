from datetime import datetime, timedelta
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.db import transaction
import json
from decimal import Decimal
from apps.barberias.models import Barberia
from apps.usuarios.models import Barbero, Servicio, Usuario, Disponibilidad , Promocion
from .models import Turno


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

    try:
        data = json.loads(request.body)

        id_barbero = data.get('id_barbero')   # puede venir None → asignación automática
        id_servicio = data['id_servicio']
        fecha = data['fecha']
        hora_inicio_str = data['hora_inicio']

        try:
            servicio = Servicio.objects.get(id_servicio=id_servicio)
        except Servicio.DoesNotExist:
            return JsonResponse({'ok': False, 'error': 'Servicio no encontrado'}, status=404)

        hora_inicio = datetime.strptime(hora_inicio_str, '%H:%M').time()
        fecha_dt = datetime.strptime(fecha, '%Y-%m-%d').date()

        inicio_dt = datetime.combine(fecha_dt, hora_inicio)
        fin_dt = inicio_dt + timedelta(minutes=servicio.duracion_minutos)
        hora_fin = fin_dt.time()

        with transaction.atomic():

            if id_barbero:
                try:
                    barbero = Barbero.objects.get(id_barbero=id_barbero)
                except Barbero.DoesNotExist:
                    return JsonResponse({'ok': False, 'error': 'Barbero no encontrado'}, status=404)

                superpuesto = Turno.objects.select_for_update().filter(
                    id_barbero=id_barbero,
                    fecha=fecha_dt,
                    hora_inicio__lt=hora_fin,
                    hora_fin__gt=hora_inicio
                ).exclude(estado='CANCELADO').exists()

                if superpuesto:
                    return JsonResponse({
                        'ok': False,
                        'error': 'El horario ya está ocupado para ese barbero'
                    }, status=409)

            else:
                candidatos = Barbero.objects.filter(id_barberia=servicio.id_barberia_id)

                barbero = None
                for candidato in candidatos:
                    ocupado = Turno.objects.select_for_update().filter(
                        id_barbero=candidato.id_barbero,
                        fecha=fecha_dt,
                        hora_inicio__lt=hora_fin,
                        hora_fin__gt=hora_inicio
                    ).exclude(estado='CANCELADO').exists()

                    if not ocupado:
                        barbero = candidato
                        break

                if barbero is None:
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
    except Exception as e:
        return JsonResponse({'ok': False, 'error': str(e)}, status=400)
    
    
def _parsear_hora(valor):
    # Acepta 'HH:MM' o 'HH:MM:SS'
    formato = '%H:%M:%S' if valor.count(':') == 2 else '%H:%M'
    return datetime.strptime(valor, formato).time()


@csrf_exempt
def turnos_disponibles(request):
    # GET /turnos/disponibles/?fecha=<yyyy-mm-dd>&barbero=<id>
    # o  GET /turnos/disponibles/?fecha=<yyyy-mm-dd>&barberia=<id>  (sin barbero puntual)
    if request.method != 'GET':
        return JsonResponse({'error': 'Metodo no permitido'}, status=405)

    try:
        id_barbero = request.GET.get('barbero')
        id_barberia = request.GET.get('barberia')
        fecha = request.GET.get('fecha')

        if not fecha or (not id_barbero and not id_barberia):
            return JsonResponse({
                'error': 'Falta la fecha, y el barbero o la barbería.'
            }, status=400)

        fecha_obj = datetime.strptime(fecha, '%Y-%m-%d').date()
        dia_semana = _dia_semana_de(fecha_obj)

        if id_barbero:
            ids_barberos = [int(id_barbero)]
        else:
            ids_barberos = list(
                Barbero.objects.filter(id_barberia=id_barberia).values_list('id_barbero', flat=True)
            )

        duracion_bloque = 30

        # Bloques de disponibilidad configurados por el dueño para ESOS
        # barberos, en ESE día de la semana (ya no hay franja fija 14-21
        # para todos: cada barbero atiende según lo que se le cargó).
        bloques_por_barbero = {}
        for bloque in Disponibilidad.objects.filter(id_barbero__in=ids_barberos, dia_semana=dia_semana):
            bloques_por_barbero.setdefault(bloque.id_barbero_id, []).append(
                (bloque.hora_inicio, bloque.hora_fin)
            )

        turnos_ocupados = list(Turno.objects.filter(
            id_barbero__in=ids_barberos,
            fecha=fecha_obj
        ).exclude(estado='CANCELADO'))

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

        horarios = []
        for bloque_inicio in sorted(horarios_posibles):
            bloque_fin = (datetime.combine(fecha_obj, bloque_inicio) + timedelta(minutes=duracion_bloque)).time()

            # libre si ALGÚN barbero de la lista atiende en ese horario
            # (según su disponibilidad cargada) Y no tiene un turno ahí.
            libre_en_alguno = False
            for bid in ids_barberos:
                atiende_en_este_horario = any(
                    ini <= bloque_inicio and bloque_fin <= fin
                    for ini, fin in bloques_por_barbero.get(bid, [])
                )
                if not atiende_en_este_horario:
                    continue

                ocupado = any(
                    bloque_inicio < t.hora_fin and bloque_fin > t.hora_inicio
                    for t in turnos_ocupados if t.id_barbero_id == bid
                )
                if not ocupado:
                    libre_en_alguno = True
                    break

            horarios.append({
                'hora': bloque_inicio.strftime('%H:%M'),
                'disponible': libre_en_alguno,
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
            turno = Turno.objects.get(id_turno=id)
        except Turno.DoesNotExist:
            return JsonResponse({'ok': False, 'error': 'Turno no encontrado.'}, status=404)

        if turno.id_cliente_id != id_cliente:
            return JsonResponse({
                'ok': False,
                'error': 'No tenes permiso para cancelar este turno.'
            }, status=403)

        try:
            turno.estado = 'CANCELADO'
            turno.updated_at = datetime.now()
            turno.save()

            return JsonResponse({
                'ok': True,
                'id_turno': turno.id_turno,
                'estado': turno.estado,
            }, status=200)

        except Exception as e:
            return JsonResponse({'ok': False, 'error': str(e)})

    return JsonResponse({'ok': False, 'error': 'Metodo no permitido'})


def mis_turnos(request):
    if request.method == 'GET':
        id_cliente = request.session.get('id_usuario')
        if not id_cliente:
            return JsonResponse({'error': 'Tenés que iniciar sesión.'}, status=401)

        try:
            hoy = datetime.now().date()

            proximos = Turno.objects.filter(
                id_cliente=id_cliente,
                fecha__gte=hoy
            ).order_by('fecha', 'hora_inicio')

            pasados = Turno.objects.filter(
                id_cliente=id_cliente,
                fecha__lt=hoy
            ).order_by('-fecha', '-hora_inicio')

            def serializar(turno):
                return {
                    'id': turno.id_turno,
                    'barberia': turno.id_barbero.id_barberia.nombre,
                    'barbero': f'{turno.id_barbero.id_usuario.nombre} {turno.id_barbero.id_usuario.apellido}',
                    'servicio': turno.id_servicio.nombre,
                    'fecha': str(turno.fecha),
                    'hora': turno.hora_inicio.strftime('%H:%M'),
                    'estado': turno.estado,
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