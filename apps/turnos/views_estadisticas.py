from datetime import datetime
from decimal import Decimal, ROUND_HALF_UP
from django.db.models import Avg, Count, Sum
from django.http import JsonResponse
from apps.usuarios.models import Calificacion
from .models import Turno
from .views_barbero import _requerir_barbero


# ══════════════════════════════════════════
# Sprint 6 - Módulo D (Gonzalo): estadísticas y calificaciones propias
# El barbero sale siempre de la sesión; todo es solo lectura.
# ══════════════════════════════════════════

def _leer_rango_opcional(request):
    # Devuelve ((desde, hasta), None) o (None, respuesta_de_error).
    # Los dos parámetros son opcionales (sin rango = todo el historial).
    desde = request.GET.get('desde')
    hasta = request.GET.get('hasta')

    try:
        desde = datetime.strptime(desde, '%Y-%m-%d').date() if desde else None
        hasta = datetime.strptime(hasta, '%Y-%m-%d').date() if hasta else None
    except ValueError:
        return None, JsonResponse({'ok': False, 'error': 'Las fechas tienen que tener formato YYYY-MM-DD.'}, status=400)

    if desde and hasta and desde > hasta:
        return None, JsonResponse({'ok': False, 'error': 'La fecha desde no puede ser posterior a hasta.'}, status=400)

    return (desde, hasta), None


# GET /api/mi-agenda/estadisticas/?desde=YYYY-MM-DD&hasta=YYYY-MM-DD
# Tarea 1: turnos atendidos (FINALIZADO), ausencias, cancelados, ingresos
# generados (suma de monto_total de los finalizados) y servicios más pedidos
# (los 5 con más turnos finalizados).
def mis_estadisticas(request):
    if request.method != 'GET':
        return JsonResponse({'ok': False, 'error': 'Método no permitido'}, status=405)

    barbero, error = _requerir_barbero(request)
    if error:
        return error

    rango, error = _leer_rango_opcional(request)
    if error:
        return error
    desde, hasta = rango

    turnos = Turno.objects.filter(id_barbero=barbero.id_barbero)
    if desde:
        turnos = turnos.filter(fecha__gte=desde)
    if hasta:
        turnos = turnos.filter(fecha__lte=hasta)

    finalizados = turnos.filter(estado='FINALIZADO')

    ingresos = finalizados.aggregate(total=Sum('monto_total'))['total'] or 0

    servicios = finalizados.values('id_servicio__nombre').annotate(
        cantidad=Count('id_turno')
    ).order_by('-cantidad', 'id_servicio__nombre')[:5]

    return JsonResponse({
        'ok': True,
        'desde': str(desde) if desde else None,
        'hasta': str(hasta) if hasta else None,
        'turnos_atendidos': finalizados.count(),
        'ausencias': turnos.filter(estado='AUSENTE').count(),
        'cancelados': turnos.filter(estado='CANCELADO').count(),
        'ingresos_generados': float(ingresos),
        'servicios_mas_pedidos': [
            {'servicio': s['id_servicio__nombre'], 'cantidad': s['cantidad']}
            for s in servicios
        ],
    })


# GET /api/mi-agenda/calificaciones/
# Tarea 2: promedio actual y listado de calificaciones recibidas (más
# recientes primero). Solo el nombre de pila del cliente.
def mis_calificaciones(request):
    if request.method != 'GET':
        return JsonResponse({'ok': False, 'error': 'Método no permitido'}, status=405)

    barbero, error = _requerir_barbero(request)
    if error:
        return error

    calificaciones = Calificacion.objects.filter(
        id_barbero=barbero.id_barbero
    ).select_related('id_cliente').order_by('-fecha', '-id_calificacion')

    promedio = calificaciones.aggregate(p=Avg('puntuacion'))['p']
    promedio = (
        Decimal(str(promedio)).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        if promedio is not None else Decimal('0.00')
    )

    return JsonResponse({
        'ok': True,
        'promedio': float(promedio),
        'cantidad': calificaciones.count(),
        'calificaciones': [
            {
                'id': c.id_calificacion,
                'puntuacion': c.puntuacion,
                'comentario': c.comentario,
                'fecha': c.fecha.strftime('%Y-%m-%d'),
                'cliente': c.id_cliente.nombre,
            }
            for c in calificaciones
        ],
    })