import json

from django.shortcuts import render
from django.db.models import Q, Sum, Count
from django.http import JsonResponse
from django.views.decorators.http import require_GET
from django.views.decorators.csrf import csrf_exempt
from django.core.files.storage import default_storage

from .models import Barberia, FotoBarberia
from apps.usuarios.models import Barbero, Servicio
from apps.turnos.models import Turno


def pagina_barberias(request):
    return render(request, 'paginas/indexGuido.html')


# ══════════════════════════════════════════
# Tarea 1: Alta de barbería
# CORREGIDO — la versión original no validaba sesión ni seteaba id_dueno
# (ver INFORME_SEGURIDAD.md para el detalle del hallazgo).
# Aviso: ahora responde JSON, no un template, para que encaje con cómo
# consume datos el resto de la API (fetch + JSON).
# ══════════════════════════════════════════

@csrf_exempt
def agregar_barberia(request):
    if request.method != 'POST':
        return JsonResponse({'ok': False, 'error': 'Método no permitido'})

    id_usuario = request.session.get('id_usuario')
    if not id_usuario:
        return JsonResponse({'ok': False, 'error': 'Debés iniciar sesión.'}, status=401)

    # No modifica usuario.rol (aclaración de la consigna) — la existencia
    # de esta Barberia con id_dueno = id_usuario es lo que define que es dueño.
    if Barberia.objects.filter(id_dueno=id_usuario).exists():
        return JsonResponse({'ok': False, 'error': 'Ya tenés una barbería registrada.'}, status=400)

    try:
        data = json.loads(request.body)

        if not data.get('nombre') or not data.get('direccion'):
            return JsonResponse({'ok': False, 'error': 'Nombre y dirección son obligatorios.'})

        barberia = Barberia.objects.create(
            id_dueno_id=id_usuario,
            nombre=data['nombre'],
            direccion=data['direccion'],
            zona=data.get('zona', ''),
            descripcion=data.get('descripcion', ''),
            telefono=data.get('telefono', ''),
            estado='activa',
        )

        # Sincronizamos la sesión al toque: si el usuario venía sin barbería
        # (es_dueno=False desde el login), ahora ya tiene una.
        request.session['es_dueno'] = True
        request.session['id_barberia'] = barberia.id_barberia

        return JsonResponse({
            'ok': True,
            'id_barberia': barberia.id_barberia,
            'nombre': barberia.nombre,
        })

    except Exception as e:
        return JsonResponse({'ok': False, 'error': str(e)})


# ══════════════════════════════════════════
# Sitio público (Sprint 2) — SIN CAMBIOS
# ══════════════════════════════════════════

def _servicio_a_dict(servicio):
    return {
        'id': servicio.id_servicio,
        'nombre': servicio.nombre,
        'precio': float(servicio.precio),
        'duracion_minutos': servicio.duracion_minutos,
    }


def _barbero_a_dict(barbero):
    return {
        'id': barbero.id_barbero,
        'nombre': f'{barbero.id_usuario.nombre} {barbero.id_usuario.apellido}',
        'foto': barbero.foto,
    }


def _barberia_a_dict(barberia, detalle=False):
    data = {
        'id': barberia.id_barberia,
        'nombre': barberia.nombre,
        'zona': barberia.zona,
        'foto': barberia.logo,
    }
    if detalle:
        servicios = Servicio.objects.filter(id_barberia=barberia.id_barberia)
        barberos = Barbero.objects.filter(id_barberia=barberia.id_barberia)
        fotos = FotoBarberia.objects.filter(id_barberia=barberia.id_barberia).order_by('orden')
        data.update({
            'descripcion': barberia.descripcion,
            'servicios': [_servicio_a_dict(s) for s in servicios],
            'barberos': [_barbero_a_dict(b) for b in barberos],
            'fotos': [f.url for f in fotos],
        })
    return data


@require_GET
def listar_barberias(request):
    texto = request.GET.get('search', '').strip()

    barberias = Barberia.objects.all()
    if texto:
        ids_por_servicio = Servicio.objects.filter(
            nombre__icontains=texto
        ).values_list('id_barberia', flat=True)

        barberias = barberias.filter(
            Q(nombre__icontains=texto) | Q(id_barberia__in=ids_por_servicio)
        )

    data = [_barberia_a_dict(b) for b in barberias]
    return JsonResponse(data, safe=False)


@require_GET
def detalle_barberia(request, id):
    try:
        barberia = Barberia.objects.get(id_barberia=id)
    except Barberia.DoesNotExist:
        return JsonResponse({'error': 'Barbería no encontrada.'}, status=404)

    return JsonResponse(_barberia_a_dict(barberia, detalle=True))


@require_GET
def listar_barberos(request):
    barberia_id = request.GET.get('barberia')

    barberos = Barbero.objects.all()
    if barberia_id:
        barberos = barberos.filter(id_barberia=barberia_id)

    data = [_barbero_a_dict(b) for b in barberos]
    return JsonResponse(data, safe=False)


# ══════════════════════════════════════════
# PANEL DEL DUEÑO — helper común (Tareas 5 a 8)
# ══════════════════════════════════════════

def _get_barberia_del_dueno(request):
    """
    Devuelve (barberia, None) si hay un usuario logueado con una barbería propia.
    Si no, devuelve (None, JsonResponse_de_error) listo para retornar tal cual.
    Se usa en TODOS los endpoints del panel para no operar nunca sobre datos
    que no pertenezcan al dueño autenticado (Tarea 8).
    """
    id_usuario = request.session.get('id_usuario')
    if not id_usuario:
        return None, JsonResponse({'ok': False, 'error': 'Debés iniciar sesión.'}, status=401)

    barberia = Barberia.objects.filter(id_dueno=id_usuario).first()
    if not barberia:
        return None, JsonResponse({'ok': False, 'error': 'No tenés una barbería registrada.'}, status=403)

    return barberia, None


def _guardar_archivo(archivo, carpeta):
    """Guarda un archivo subido en media/<carpeta>/ y devuelve la URL pública."""
    ruta_guardada = default_storage.save(f'{carpeta}/{archivo.name}', archivo)
    return default_storage.url(ruta_guardada)


# ══════════════════════════════════════════
# Tarea 6: Informes
# GET /api/panel/informes/?desde=YYYY-MM-DD&hasta=YYYY-MM-DD
# ══════════════════════════════════════════

@require_GET
def informes(request):
    barberia, error = _get_barberia_del_dueno(request)
    if error:
        return error

    # Siempre filtrado por la barbería del dueño logueado (nunca datos de otra)
    turnos = Turno.objects.filter(id_barbero__id_barberia=barberia)

    desde = request.GET.get('desde')
    hasta = request.GET.get('hasta')
    if desde:
        turnos = turnos.filter(fecha__gte=desde)
    if hasta:
        turnos = turnos.filter(fecha__lte=hasta)

    turnos_por_dia = list(
        turnos.values('fecha')
              .annotate(cantidad=Count('id_turno'))
              .order_by('fecha')
    )

    ingresos_totales = turnos.aggregate(total=Sum('monto_total'))['total'] or 0

    turnos_por_estado = list(
        turnos.values('estado')
              .annotate(cantidad=Count('id_turno'))
              .order_by('estado')
    )

    return JsonResponse({
        'ok': True,
        'barberia': barberia.nombre,
        'turnos_por_dia': turnos_por_dia,
        'ingresos_totales': float(ingresos_totales),
        'turnos_por_estado': turnos_por_estado,
    })


# ══════════════════════════════════════════
# Tarea 7: carga real de archivos
# Reemplaza la carga manual de rutas del Sprint 2.
# ══════════════════════════════════════════

@csrf_exempt
def subir_logo_barberia(request):
    """POST multipart/form-data con el campo 'logo' -> media/logos/"""
    if request.method != 'POST':
        return JsonResponse({'ok': False, 'error': 'Método no permitido'})

    barberia, error = _get_barberia_del_dueno(request)
    if error:
        return error

    archivo = request.FILES.get('logo')
    if not archivo:
        return JsonResponse({'ok': False, 'error': 'No se recibió ningún archivo (campo "logo").'})

    barberia.logo = _guardar_archivo(archivo, 'logos')
    barberia.save()

    return JsonResponse({'ok': True, 'logo': barberia.logo})


@csrf_exempt
def subir_foto_portada(request):
    """POST multipart/form-data con el campo 'foto' -> media/portadas/"""
    if request.method != 'POST':
        return JsonResponse({'ok': False, 'error': 'Método no permitido'})

    barberia, error = _get_barberia_del_dueno(request)
    if error:
        return error

    archivo = request.FILES.get('foto')
    if not archivo:
        return JsonResponse({'ok': False, 'error': 'No se recibió ningún archivo (campo "foto").'})

    url = _guardar_archivo(archivo, 'portadas')
    orden = FotoBarberia.objects.filter(id_barberia=barberia).count()

    foto = FotoBarberia.objects.create(
        id_barberia=barberia,
        url=url,
        orden=orden,
    )

    return JsonResponse({'ok': True, 'id_foto': foto.id_foto, 'url': foto.url})


@csrf_exempt
def subir_foto_barbero(request, id):
    """POST multipart/form-data con el campo 'foto' -> media/barberos/"""
    if request.method != 'POST':
        return JsonResponse({'ok': False, 'error': 'Método no permitido'})

    barberia, error = _get_barberia_del_dueno(request)
    if error:
        return error

    try:
        barbero = Barbero.objects.get(id_barbero=id)
    except Barbero.DoesNotExist:
        return JsonResponse({'ok': False, 'error': 'Barbero no encontrado.'}, status=404)

    # Validar pertenencia: el barbero tiene que ser de ESTA barbería (Tareas 4 y 8)
    if barbero.id_barberia_id != barberia.id_barberia:
        return JsonResponse({'ok': False, 'error': 'Ese barbero no pertenece a tu barbería.'}, status=403)

    archivo = request.FILES.get('foto')
    if not archivo:
        return JsonResponse({'ok': False, 'error': 'No se recibió ningún archivo (campo "foto").'})

    barbero.foto = _guardar_archivo(archivo, 'barberos')
    barbero.save()

    return JsonResponse({'ok': True, 'foto': barbero.foto})