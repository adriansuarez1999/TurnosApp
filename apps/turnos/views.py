from django.shortcuts import render
from datetime import datetime, timedelta
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.db import transaction
import json

from apps.usuarios.models import Barbero, Servicio
from .models import Turno


@csrf_exempt
def crear_turno(request):
    if request.method != 'POST':
        return JsonResponse({'ok': False, 'error': 'Método no permitido'}, status=405)

    try:
        data = json.loads(request.body)

        id_cliente = data['id_cliente']
        id_barbero = data['id_barbero']
        id_servicio = data['id_servicio']
        fecha = data['fecha']                    # 'YYYY-MM-DD'
        hora_inicio_str = data['hora_inicio']     # 'HH:MM'

        try:
            barbero = Barbero.objects.get(id_barbero=id_barbero)
        except Barbero.DoesNotExist:
            return JsonResponse({'ok': False, 'error': 'Barbero no encontrado'}, status=404)

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
            'hora_inicio': hora_inicio.strftime('%H:%M'),
            'hora_fin': hora_fin.strftime('%H:%M'),
            'estado': turno.estado
        })

    except KeyError as e:
        return JsonResponse({'ok': False, 'error': f'Falta el campo {e}'}, status=400)
    except Exception as e:
        return JsonResponse({'ok': False, 'error': str(e)}, status=400)
