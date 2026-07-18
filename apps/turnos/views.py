from datetime import datetime, timedelta
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.db import transaction
import json

from apps.usuarios.models import Barbero, Servicio
from .models import Turno


def crear_turno(request):
    if request.method != 'POST':
        return JsonResponse({'ok': False, 'error': 'Método no permitido'}, status=405)

    id_cliente = request.session.get('id_usuario')
    if not id_cliente:
        return JsonResponse({'ok': False, 'error': 'Tenés que iniciar sesión para reservar un turno.'}, status=401)

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

            turno = Turno.objects.create(
                id_cliente_id=id_cliente,
                id_barbero_id=id_barbero,
                id_servicio_id=id_servicio,
                fecha=fecha_dt,
                hora_inicio=hora_inicio,
                hora_fin=hora_fin,
                estado='PENDIENTE',
                monto_total=servicio.precio,
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
            'estado': turno.estado
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
    # GET /turnos/disponibles/?barbero=<id>&fecha=<yyyy-mm-dd>
    if request.method == 'GET':
        try:
            id_barbero = request.GET.get('barbero')
            fecha = request.GET.get('fecha')

            if not id_barbero or not fecha:
                return JsonResponse({
                    'ok': False,
                    'error': 'Los parametros barbero y fecha son obligatorios.'
                }, status=400)

            fecha_obj = datetime.strptime(fecha, '%Y-%m-%d').date()

            # Bloques de 30 minutos entre las 14:00 y las 21:00
            duracion_bloque = 30
            hora_apertura = datetime.combine(fecha_obj, _parsear_hora('14:00'))
            hora_cierre = datetime.combine(fecha_obj, _parsear_hora('21:00'))

            turnos_ocupados = Turno.objects.filter(
                id_barbero=id_barbero,
                fecha=fecha_obj
            ).exclude(estado='CANCELADO')

            horarios_libres = []
            actual = hora_apertura

            while actual + timedelta(minutes=duracion_bloque) <= hora_cierre:
                bloque_inicio = actual.time()
                bloque_fin = (actual + timedelta(minutes=duracion_bloque)).time()

                ocupado = any(
                    bloque_inicio < t.hora_fin and bloque_fin > t.hora_inicio
                    for t in turnos_ocupados
                )

                if not ocupado:
                    horarios_libres.append(bloque_inicio.strftime('%H:%M'))

                actual += timedelta(minutes=duracion_bloque)

            return JsonResponse({'ok': True, 'horarios': horarios_libres})

        except Exception as e:
            return JsonResponse({'ok': False, 'error': str(e)})

    return JsonResponse({'ok': False, 'error': 'Metodo no permitido'})


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
            return JsonResponse({'ok': False, 'error': 'Tenés que iniciar sesión.'}, status=401)

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
                    'id_turno': turno.id_turno,
                    'barberia': turno.id_barbero.id_barberia.nombre,
                    'barbero': f'{turno.id_barbero.id_usuario.nombre} {turno.id_barbero.id_usuario.apellido}',
                    'servicio': turno.id_servicio.nombre,
                    'fecha': str(turno.fecha),
                    'hora': turno.hora_inicio.strftime('%H:%M'),
                    'estado': turno.estado,
                }

            lista = [serializar(t) for t in proximos] + [serializar(t) for t in pasados]

            return JsonResponse({'ok': True, 'turnos': lista})

        except Exception as e:
            return JsonResponse({'ok': False, 'error': str(e)})

    return JsonResponse({'ok': False, 'error': 'Metodo no permitido'})