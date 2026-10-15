import json
from django.db import IntegrityError, transaction
from django.http import JsonResponse
from apps.usuarios.models import Barbero
from .views import _usuario_logueado, _barberia_del_dueno


# ══════════════════════════════════════════
# Sprint 6 - Módulo F (Gonzalo): dueño que también es barbero
# ══════════════════════════════════════════

# POST /api/mi-barberia/barberos/yo/   body opcional: {"especialidad": "..."}
# Crea el registro Barbero del usuario de la sesión dentro de SU barbería y
# actualiza la sesión para que "Mi agenda" aparezca sin volver a loguearse
# (mismo criterio que el alta de barbería del Sprint 3). No toca usuario.rol:
# ser barbero se determina por la existencia del registro Barbero.
def agregarme_como_barbero(request):
    if request.method != 'POST':
        return JsonResponse({'ok': False, 'error': 'Método no permitido'}, status=405)

    id_usuario = _usuario_logueado(request)
    if not id_usuario:
        return JsonResponse({'ok': False, 'error': 'Tenés que iniciar sesión.'}, status=401)

    barberia = _barberia_del_dueno(id_usuario)
    if not barberia:
        return JsonResponse({'ok': False, 'error': 'No tenés una barbería registrada.'}, status=404)

    especialidad = ''
    if request.body:
        try:
            data = json.loads(request.body)
        except ValueError:
            return JsonResponse({'ok': False, 'error': 'El cuerpo tiene que ser un JSON válido.'}, status=400)

        if not isinstance(data, dict):
            return JsonResponse({'ok': False, 'error': 'El cuerpo tiene que ser un objeto JSON.'}, status=400)

        especialidad = data.get('especialidad') or ''
        if not isinstance(especialidad, str):
            return JsonResponse({'ok': False, 'error': 'La especialidad tiene que ser texto.'}, status=400)

        especialidad = especialidad.strip()
        if len(especialidad) > 100:
            return JsonResponse({'ok': False, 'error': 'La especialidad no puede superar los 100 caracteres.'}, status=400)

    if Barbero.objects.filter(id_usuario=id_usuario).exists():
        return JsonResponse({'ok': False, 'error': 'Ya sos barbero.'}, status=409)

    try:
        with transaction.atomic():
            barbero = Barbero.objects.create(
                id_usuario_id=id_usuario,
                id_barberia_id=barberia.id_barberia,
                especialidad=especialidad,
                foto=None,
                promedio_calificacion=0,
            )
    except IntegrityError:
        # Dos pedidos a la vez: id_usuario es único en la tabla barbero.
        return JsonResponse({'ok': False, 'error': 'Ya sos barbero.'}, status=409)

    request.session['es_barbero'] = True
    request.session['id_barbero'] = barbero.id_barbero

    return JsonResponse({
        'ok': True,
        'id_barbero': barbero.id_barbero,
        'es_barbero': True,
    }, status=201)