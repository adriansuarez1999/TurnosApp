import json
from datetime import datetime
from django.http import JsonResponse
from django.db import transaction, IntegrityError
from django.db.models import Avg
from decimal import Decimal, ROUND_HALF_UP
from apps.usuarios.models import Barbero, Calificacion
from .models import Turno


# ══════════════════════════════════════════
# Sprint 6 - Módulo D: Calificación del cliente (CU-09)
# ══════════════════════════════════════════

# POST /api/turnos/<id>/calificar/   body: {"puntuacion": 1-5, "comentario": "..."}
# Solo el cliente dueño del turno, solo si está FINALIZADO y una única vez.
# Al guardar se recalcula barbero.promedio_calificacion.
def calificar_turno(request, id):
    if request.method != 'POST':
        return JsonResponse({'ok': False, 'error': 'Método no permitido'}, status=405)

    id_cliente = request.session.get('id_usuario')
    if not id_cliente:
        return JsonResponse({'ok': False, 'error': 'Tenés que iniciar sesión.'}, status=401)

    try:
        data = json.loads(request.body)
    except ValueError:
        return JsonResponse({'ok': False, 'error': 'El cuerpo tiene que ser un JSON válido.'}, status=400)

    if not isinstance(data, dict):
        return JsonResponse({'ok': False, 'error': 'El cuerpo tiene que ser un objeto JSON.'}, status=400)

    # Se acepta 'puntuacion' (nombre de la columna) o 'puntaje'.
    puntuacion = data.get('puntuacion', data.get('puntaje'))
    if isinstance(puntuacion, bool) or not isinstance(puntuacion, int) or not 1 <= puntuacion <= 5:
        return JsonResponse({'ok': False, 'error': 'El puntaje tiene que ser un número entero de 1 a 5.'}, status=400)

    comentario = data.get('comentario')
    if comentario is not None:
        if not isinstance(comentario, str):
            return JsonResponse({'ok': False, 'error': 'El comentario tiene que ser texto.'}, status=400)
        comentario = comentario.strip() or None
        if comentario and len(comentario) > 1000:
            return JsonResponse({'ok': False, 'error': 'El comentario no puede superar los 1000 caracteres.'}, status=400)

    try:
        with transaction.atomic():
            try:
                turno = Turno.objects.select_for_update().get(id_turno=id)
            except Turno.DoesNotExist:
                return JsonResponse({'ok': False, 'error': 'Turno no encontrado.'}, status=404)

            if turno.id_cliente_id != id_cliente:
                return JsonResponse({'ok': False, 'error': 'Ese turno no es tuyo.'}, status=403)

            if turno.estado != 'FINALIZADO':
                return JsonResponse({
                    'ok': False,
                    'error': 'Solo se puede calificar un turno FINALIZADO.'
                }, status=400)

            if Calificacion.objects.filter(id_turno=turno.id_turno).exists():
                return JsonResponse({'ok': False, 'error': 'Ya calificaste este turno.'}, status=409)

            Calificacion.objects.create(
                id_turno_id=turno.id_turno,
                id_barbero_id=turno.id_barbero_id,
                id_cliente_id=id_cliente,
                puntuacion=puntuacion,
                comentario=comentario,
                fecha=datetime.now()
            )

            promedio = Calificacion.objects.filter(
                id_barbero=turno.id_barbero_id
            ).aggregate(p=Avg('puntuacion'))['p']
            promedio = Decimal(str(promedio)).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

            Barbero.objects.filter(id_barbero=turno.id_barbero_id).update(
                promedio_calificacion=promedio
            )

    except IntegrityError:
        # Por si dos pedidos llegan a la vez: id_turno es UNIQUE en calificacion.
        return JsonResponse({'ok': False, 'error': 'Ya calificaste este turno.'}, status=409)

    # Módulo E (Gonzalo): sin notificación en este evento (solo finalizar,
    # cancelar y turno nuevo generan aviso).
    return JsonResponse({
        'ok': True,
        'id_turno': turno.id_turno,
        'puntuacion': puntuacion,
        'comentario': comentario,
        'promedio_barbero': float(promedio)
    }, status=201)
