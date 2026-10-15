import json
from django.contrib.auth.hashers import check_password, make_password
from django.http import JsonResponse
from apps.usuarios.models import Disponibilidad, Usuario
from apps.barberias.views import (
    _parsear_hora,
    _disponibilidad_a_dict,
    _validar_bloque_disponibilidad,
    _guardar_archivo,
)
from .views_barbero import _requerir_barbero


# ══════════════════════════════════════════
# Sprint 6 - Módulo C (Gonzalo): disponibilidad y perfil propios
# El barbero sale siempre de la sesión (_requerir_barbero); ningún
# endpoint recibe un id de barbero.
# ══════════════════════════════════════════

# ⚠ Tiene que ser el mismo mínimo que usa el registro. Confirmar contra
# apps/usuarios/views.py (registro) antes de entregar.
PASSWORD_MIN_LARGO = 6

TAMANO_MAX_FOTO = 5 * 1024 * 1024  # 5 MB


def _leer_json(request):
    # Devuelve (dict, None) o (None, respuesta_de_error).
    try:
        data = json.loads(request.body) if request.body else {}
    except ValueError:
        return None, JsonResponse({'ok': False, 'error': 'El cuerpo tiene que ser un JSON válido.'}, status=400)
    if not isinstance(data, dict):
        return None, JsonResponse({'ok': False, 'error': 'El cuerpo tiene que ser un objeto JSON.'}, status=400)
    return data, None


def _leer_bloque(data, bloque=None):
    # Devuelve ((dia, hora_inicio, hora_fin), None) o (None, mensaje_de_error).
    # Con 'bloque' (edición) los campos que no vienen se mantienen.
    dia = data.get('dia_semana', bloque.dia_semana if bloque else None)
    inicio = data.get('hora_inicio')
    fin = data.get('hora_fin')

    if not bloque:
        for campo, valor in (('dia_semana', dia), ('hora_inicio', inicio), ('hora_fin', fin)):
            if not valor:
                return None, f'El campo {campo} es obligatorio.'

    if not isinstance(dia, str):
        return None, 'El día tiene que ser texto (LUN, MAR, MIE, JUE, VIE, SAB o DOM).'

    try:
        hora_inicio = _parsear_hora(inicio) if inicio else bloque.hora_inicio
        hora_fin = _parsear_hora(fin) if fin else bloque.hora_fin
    except (ValueError, AttributeError):
        return None, 'Las horas tienen que tener formato HH:MM.'

    return (dia.upper(), hora_inicio, hora_fin), None


# ══════════════════════════════════════════
# Tarea 1: disponibilidad propia
# ══════════════════════════════════════════

# GET  /api/mi-agenda/disponibilidad/  -> bloques del barbero de la sesión
# POST /api/mi-agenda/disponibilidad/  -> alta de un bloque
def mi_disponibilidad(request):
    if request.method not in ('GET', 'POST'):
        return JsonResponse({'ok': False, 'error': 'Método no permitido'}, status=405)

    barbero, error = _requerir_barbero(request)
    if error:
        return error

    if request.method == 'GET':
        bloques = Disponibilidad.objects.filter(
            id_barbero=barbero.id_barbero
        ).order_by('dia_semana', 'hora_inicio')
        return JsonResponse({
            'ok': True,
            'disponibilidad': [_disponibilidad_a_dict(b) for b in bloques]
        })

    data, error = _leer_json(request)
    if error:
        return error

    valores, mensaje = _leer_bloque(data)
    if mensaje:
        return JsonResponse({'ok': False, 'error': mensaje}, status=400)
    dia, hora_inicio, hora_fin = valores

    mensaje = _validar_bloque_disponibilidad(barbero.id_barbero, dia, hora_inicio, hora_fin)
    if mensaje:
        return JsonResponse({'ok': False, 'error': mensaje}, status=400)

    bloque = Disponibilidad.objects.create(
        id_barbero_id=barbero.id_barbero,
        dia_semana=dia,
        hora_inicio=hora_inicio,
        hora_fin=hora_fin,
    )
    return JsonResponse({'ok': True, 'id': bloque.id_disponibilidad}, status=201)


# PUT    /api/mi-agenda/disponibilidad/<id>/  -> edición de un bloque propio
# DELETE /api/mi-agenda/disponibilidad/<id>/  -> baja de un bloque propio
def mi_disponibilidad_detalle(request, id):
    if request.method not in ('PUT', 'DELETE'):
        return JsonResponse({'ok': False, 'error': 'Método no permitido'}, status=405)

    barbero, error = _requerir_barbero(request)
    if error:
        return error

    try:
        bloque = Disponibilidad.objects.get(id_disponibilidad=id)
    except Disponibilidad.DoesNotExist:
        return JsonResponse({'ok': False, 'error': 'Bloque de disponibilidad no encontrado.'}, status=404)

    # Pertenencia: el bloque tiene que ser del barbero de la sesión.
    if bloque.id_barbero_id != barbero.id_barbero:
        return JsonResponse({'ok': False, 'error': 'Ese bloque no es tuyo.'}, status=403)

    if request.method == 'DELETE':
        bloque.delete()
        return JsonResponse({'ok': True})

    data, error = _leer_json(request)
    if error:
        return error

    valores, mensaje = _leer_bloque(data, bloque)
    if mensaje:
        return JsonResponse({'ok': False, 'error': mensaje}, status=400)
    dia, hora_inicio, hora_fin = valores

    mensaje = _validar_bloque_disponibilidad(
        barbero.id_barbero, dia, hora_inicio, hora_fin,
        excluir_id=bloque.id_disponibilidad
    )
    if mensaje:
        return JsonResponse({'ok': False, 'error': mensaje}, status=400)

    bloque.dia_semana = dia
    bloque.hora_inicio = hora_inicio
    bloque.hora_fin = hora_fin
    bloque.save()
    return JsonResponse({'ok': True, 'id': bloque.id_disponibilidad})


# ══════════════════════════════════════════
# Tarea 2: perfil propio
# ══════════════════════════════════════════

def _perfil_a_dict(barbero):
    usuario = barbero.id_usuario
    return {
        'id_barbero': barbero.id_barbero,
        'nombre': usuario.nombre,
        'apellido': usuario.apellido,
        'email': usuario.email,
        'telefono': usuario.telefono,
        'especialidad': barbero.especialidad,
        'foto': barbero.foto,
        'promedio_calificacion': float(barbero.promedio_calificacion),
    }


# GET /api/mi-agenda/perfil/  -> datos del perfil
# PUT /api/mi-agenda/perfil/  -> actualiza teléfono y/o especialidad
def mi_perfil(request):
    if request.method not in ('GET', 'PUT'):
        return JsonResponse({'ok': False, 'error': 'Método no permitido'}, status=405)

    barbero, error = _requerir_barbero(request)
    if error:
        return error

    if request.method == 'GET':
        return JsonResponse({'ok': True, 'perfil': _perfil_a_dict(barbero)})

    data, error = _leer_json(request)
    if error:
        return error

    usuario = barbero.id_usuario
    cambios_usuario = []
    cambios_barbero = []

    if 'telefono' in data:
        telefono = data['telefono']
        if not isinstance(telefono, str) or not telefono.strip():
            return JsonResponse({'ok': False, 'error': 'El teléfono no puede estar vacío.'}, status=400)
        telefono = telefono.strip()
        if len(telefono) > 20:
            return JsonResponse({'ok': False, 'error': 'El teléfono no puede superar los 20 caracteres.'}, status=400)
        usuario.telefono = telefono
        cambios_usuario.append('telefono')

    if 'especialidad' in data:
        especialidad = data['especialidad']
        if especialidad is not None and not isinstance(especialidad, str):
            return JsonResponse({'ok': False, 'error': 'La especialidad tiene que ser texto.'}, status=400)
        especialidad = (especialidad or '').strip()
        if len(especialidad) > 100:
            return JsonResponse({'ok': False, 'error': 'La especialidad no puede superar los 100 caracteres.'}, status=400)
        barbero.especialidad = especialidad
        cambios_barbero.append('especialidad')

    # update_fields: solo se escribe lo que cambió, así no se pisa
    # promedio_calificacion si entra una calificación en el mismo momento.
    if cambios_usuario:
        usuario.save(update_fields=cambios_usuario)
    if cambios_barbero:
        barbero.save(update_fields=cambios_barbero)

    return JsonResponse({'ok': True, 'perfil': _perfil_a_dict(barbero)})


# POST /api/mi-agenda/perfil/foto/   multipart/form-data, campo 'foto'
def mi_perfil_foto(request):
    if request.method != 'POST':
        return JsonResponse({'ok': False, 'error': 'Método no permitido'}, status=405)

    barbero, error = _requerir_barbero(request)
    if error:
        return error

    archivo = request.FILES.get('foto')
    if not archivo:
        return JsonResponse({'ok': False, 'error': 'No se recibió ningún archivo (campo "foto").'}, status=400)

    if not (archivo.content_type or '').startswith('image/'):
        return JsonResponse({'ok': False, 'error': 'El archivo tiene que ser una imagen.'}, status=400)

    if archivo.size > TAMANO_MAX_FOTO:
        return JsonResponse({'ok': False, 'error': 'La imagen no puede superar los 5 MB.'}, status=400)

    barbero.foto = _guardar_archivo(archivo, 'barberos')
    barbero.save(update_fields=['foto'])

    return JsonResponse({'ok': True, 'foto': barbero.foto})


# ══════════════════════════════════════════
# Tarea 3: cambio de contraseña
# Solo usa el usuario de la sesión (no hace falta ser barbero).
# ══════════════════════════════════════════

# POST /api/mi-agenda/perfil/password/   body: {"password_actual": "...", "password_nueva": "..."}
def mi_password(request):
    if request.method != 'POST':
        return JsonResponse({'ok': False, 'error': 'Método no permitido'}, status=405)

    id_usuario = request.session.get('id_usuario')
    if not id_usuario:
        return JsonResponse({'ok': False, 'error': 'Tenés que iniciar sesión.'}, status=401)

    data, error = _leer_json(request)
    if error:
        return error

    actual = data.get('password_actual')
    nueva = data.get('password_nueva')
    if not isinstance(actual, str) or not actual or not isinstance(nueva, str) or not nueva:
        return JsonResponse({
            'ok': False,
            'error': 'Tenés que enviar la contraseña actual y la nueva.'
        }, status=400)

    try:
        usuario = Usuario.objects.get(id_usuario=id_usuario)
    except Usuario.DoesNotExist:
        return JsonResponse({'ok': False, 'error': 'Usuario no encontrado.'}, status=404)

    if not check_password(actual, usuario.password):
        return JsonResponse({'ok': False, 'error': 'La contraseña actual no es correcta.'}, status=400)

    if len(nueva) < PASSWORD_MIN_LARGO:
        return JsonResponse({
            'ok': False,
            'error': f'La nueva contraseña tiene que tener al menos {PASSWORD_MIN_LARGO} caracteres.'
        }, status=400)

    if nueva == actual:
        return JsonResponse({'ok': False, 'error': 'La nueva contraseña tiene que ser distinta de la actual.'}, status=400)

    usuario.password = make_password(nueva)
    usuario.save(update_fields=['password'])

    return JsonResponse({'ok': True})