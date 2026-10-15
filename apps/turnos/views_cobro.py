import json
from datetime import datetime
from django.db import transaction
from django.http import JsonResponse
from apps.usuarios.models import Pago
from .models import Turno
from .views_barbero import _requerir_barbero


# ══════════════════════════════════════════
# Sprint 6 - Módulo B (Gonzalo): registrar cobro al finalizar un turno
# ══════════════════════════════════════════

# Valores que acepta el ENUM pago.metodo_pago para este flujo.
METODOS_COBRO = ('EFECTIVO', 'TRANSFERENCIA')


def _pago_a_dict(pago):
    return {
        'id_pago': pago.id_pago,
        'id_turno': pago.id_turno_id,
        'monto': float(pago.monto),
        'metodo_pago': pago.metodo_pago,
        'tipo_pago': pago.tipo_pago,
        'estado': pago.estado,
        'fecha_pago': pago.fecha_pago.strftime('%Y-%m-%d %H:%M'),
    }


# POST /api/mi-agenda/turnos/<id>/cobro/   body: {"metodo_pago": "EFECTIVO" | "TRANSFERENCIA"}
# Solo sobre turnos propios en estado FINALIZADO y una única vez por turno.
# El monto siempre sale de turno.monto_total (el front lo muestra prellenado);
# no se acepta uno distinto desde el pedido.
def registrar_cobro(request, id):
    if request.method != 'POST':
        return JsonResponse({'ok': False, 'error': 'Método no permitido'}, status=405)

    barbero, error = _requerir_barbero(request)
    if error:
        return error

    try:
        data = json.loads(request.body) if request.body else {}
    except ValueError:
        return JsonResponse({'ok': False, 'error': 'El cuerpo tiene que ser un JSON válido.'}, status=400)

    if not isinstance(data, dict):
        return JsonResponse({'ok': False, 'error': 'El cuerpo tiene que ser un objeto JSON.'}, status=400)

    metodo = data.get('metodo_pago')
    if not isinstance(metodo, str) or metodo.strip().upper() not in METODOS_COBRO:
        return JsonResponse({
            'ok': False,
            'error': 'El método de pago tiene que ser EFECTIVO o TRANSFERENCIA.'
        }, status=400)
    metodo = metodo.strip().upper()

    # Con el turno bloqueado, dos pedidos simultáneos no pueden registrar el cobro dos veces.
    with transaction.atomic():
        try:
            turno = Turno.objects.select_for_update().get(id_turno=id)
        except Turno.DoesNotExist:
            return JsonResponse({'ok': False, 'error': 'Turno no encontrado.'}, status=404)

        if turno.id_barbero_id != barbero.id_barbero:
            return JsonResponse({'ok': False, 'error': 'Ese turno no es tuyo.'}, status=403)

        if turno.estado != 'FINALIZADO':
            return JsonResponse({
                'ok': False,
                'error': f'Solo se puede cobrar un turno FINALIZADO (este está {turno.estado}).'
            }, status=400)

        ya_cobrado = Pago.objects.filter(
            id_turno=turno.id_turno, tipo_pago='TOTAL'
        ).exclude(estado='RECHAZADO').exists()
        if ya_cobrado:
            return JsonResponse({'ok': False, 'error': 'Este turno ya tiene el cobro registrado.'}, status=409)

        ahora = datetime.now()
        pago = Pago.objects.create(
            id_turno_id=turno.id_turno,
            fecha_pago=ahora,
            monto=turno.monto_total,
            metodo_pago=metodo,
            estado='APROBADO',
            tipo_pago='TOTAL',
            created_at=ahora,
            updated_at=ahora,
            created_by_id=request.session.get('id_usuario'),
        )

    return JsonResponse({'ok': True, 'pago': _pago_a_dict(pago)}, status=201)