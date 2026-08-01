from datetime import datetime
from django.shortcuts import render
from .models import Barberia, FotoBarberia
from django.db.models import Q
from django.http import JsonResponse
from django.views.decorators.http import require_GET
from django.contrib.auth.hashers import make_password
from apps.usuarios.models import Barbero, Servicio, Usuario
import json

def pagina_barberias(request):
    return render(request, 'paginas/indexGuido.html')

# ══════════════════════════════════════════
# Agregar barbería
# ══════════════════════════════════════════

def agregar_barberia(request):
    if request.method == 'POST':
        Barberia.objects.create(
            nombre=request.POST.get('nombre'),
            direccion=request.POST.get('direccion'),
            telefono=request.POST.get('telefono')
        )
        # Aquí deberías crear un objeto Barberia y guardarlo en la base de datos
        # Barberia.objects.create(nombre=nombre, direccion=direccion, telefono=telefono)

        return render(request, 'barberias/agregar_barberia.html', {'mensaje': 'Barbería agregada exitosamente'})

    return render(request, 'barberias/agregar_barberia.html')


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


# GET /api/barberias/           -> lista todas
# GET /api/barberias/?search=x  -> filtra por nombre o por nombre de servicio
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


# GET /api/barberias/<id>/  -> detalle completo
@require_GET
def detalle_barberia(request, id):
    try:
        barberia = Barberia.objects.get(id_barberia=id)
    except Barberia.DoesNotExist:
        return JsonResponse({'error': 'Barbería no encontrada.'}, status=404)

    return JsonResponse(_barberia_a_dict(barberia, detalle=True))


# GET /api/barberos/?barberia=<id>  -> barberos de una barbería
@require_GET
def listar_barberos(request):
    barberia_id = request.GET.get('barberia')

    barberos = Barbero.objects.all()
    if barberia_id:
        barberos = barberos.filter(id_barberia=barberia_id)

    data = [_barbero_a_dict(b) for b in barberos]
    return JsonResponse(data, safe=False)


# ══════════════════════════════════════════
# Helpers de sesión / pertenencia (dueño)
# ══════════════════════════════════════════

def _usuario_logueado(request):
    # Devuelve el id_usuario de la sesión, o None si no hay sesión activa.
    return request.session.get('id_usuario')


def _barberia_del_dueno(id_usuario):
    # Devuelve la Barberia cuyo dueño es id_usuario, o None si no tiene una.
    return Barberia.objects.filter(id_dueno=id_usuario).first()


def _barbero_del_dueno_a_dict(barbero):
    return {
        'id_barbero': barbero.id_barbero,
        'nombre': barbero.id_usuario.nombre,
        'apellido': barbero.id_usuario.apellido,
        'email': barbero.id_usuario.email,
        'telefono': barbero.id_usuario.telefono,
        'especialidad': barbero.especialidad,
        'foto': barbero.foto,
        'estado': barbero.id_usuario.estado,
    }


# ══════════════════════════════════════════
# Tarea 1: Alta de barbería
# ══════════════════════════════════════════

# POST /api/barberias/nueva/
def crear_barberia(request):
    if request.method != 'POST':
        return JsonResponse({'ok': False, 'error': 'Método no permitido'}, status=405)

    id_usuario = _usuario_logueado(request)
    if not id_usuario:
        return JsonResponse({'ok': False, 'error': 'Tenés que iniciar sesión.'}, status=401)

    if _barberia_del_dueno(id_usuario):
        return JsonResponse({'ok': False, 'error': 'Ya tenés una barbería registrada.'}, status=400)

    try:
        data = json.loads(request.body)

        obligatorios = ['nombre', 'direccion', 'zona']
        for campo in obligatorios:
            if not data.get(campo):
                return JsonResponse({
                    'ok': False,
                    'error': f'El campo {campo} es obligatorio.'
                }, status=400)

        # Nota: esto NO modifica usuario.rol. Ser dueño se determina por
        # tener una Barberia con id_dueno = este usuario, no por el rol.
        barberia = Barberia.objects.create(
            id_dueno_id=id_usuario,
            nombre=data['nombre'],
            direccion=data['direccion'],
            zona=data['zona'],
            descripcion=data.get('descripcion', ''),
            telefono=data.get('telefono', ''),
            estado='ACTIVA'
        )

        # La sesión ya sabe que este usuario ahora es dueño.
        request.session['id_barberia'] = barberia.id_barberia

        return JsonResponse({
            'ok': True,
            'id_barberia': barberia.id_barberia,
            'nombre': barberia.nombre
        }, status=201)

    except Exception as e:
        return JsonResponse({'ok': False, 'error': str(e)}, status=400)


# ══════════════════════════════════════════
# Tarea 3: CRUD de los datos propios de la barbería
# ══════════════════════════════════════════

# GET /api/mi-barberia/  -> datos de la barbería del dueño logueado
# PUT /api/mi-barberia/  -> actualiza nombre, direccion, zona, descripcion, logo y estado
def mi_barberia(request):
    id_usuario = _usuario_logueado(request)
    if not id_usuario:
        return JsonResponse({'ok': False, 'error': 'Tenés que iniciar sesión.'}, status=401)

    # Al buscar la barbería por id_dueno (y no por un id que mande el cliente),
    # es imposible operar sobre una barbería que no sea la del usuario en sesión.
    barberia = _barberia_del_dueno(id_usuario)
    if not barberia:
        return JsonResponse({'ok': False, 'error': 'No tenés una barbería registrada.'}, status=404)

    if request.method == 'GET':
        return JsonResponse({
            'ok': True,
            'id_barberia': barberia.id_barberia,
            'nombre': barberia.nombre,
            'direccion': barberia.direccion,
            'zona': barberia.zona,
            'descripcion': barberia.descripcion,
            'logo': barberia.logo,
            'telefono': barberia.telefono,
            'estado': barberia.estado,
        })

    if request.method == 'PUT':
        try:
            data = json.loads(request.body)

            barberia.nombre = data.get('nombre', barberia.nombre)
            barberia.direccion = data.get('direccion', barberia.direccion)
            barberia.zona = data.get('zona', barberia.zona)
            barberia.descripcion = data.get('descripcion', barberia.descripcion)
            barberia.logo = data.get('logo', barberia.logo)
            barberia.estado = data.get('estado', barberia.estado)
            barberia.save()

            return JsonResponse({'ok': True, 'nombre': barberia.nombre})

        except Exception as e:
            return JsonResponse({'ok': False, 'error': str(e)}, status=400)

    return JsonResponse({'ok': False, 'error': 'Método no permitido'}, status=405)


# ══════════════════════════════════════════
# Tarea 4: CRUD de Barbero (panel del dueño)
# ══════════════════════════════════════════

# GET  /api/mi-barberia/barberos/  -> lista de barberos de la barbería propia
# POST /api/mi-barberia/barberos/  -> alta de un barbero nuevo
def mis_barberos(request):
    id_usuario = _usuario_logueado(request)
    if not id_usuario:
        return JsonResponse({'ok': False, 'error': 'Tenés que iniciar sesión.'}, status=401)

    barberia = _barberia_del_dueno(id_usuario)
    if not barberia:
        return JsonResponse({'ok': False, 'error': 'No tenés una barbería registrada.'}, status=404)

    if request.method == 'GET':
        barberos = Barbero.objects.filter(id_barberia=barberia.id_barberia)
        return JsonResponse({
            'ok': True,
            'barberos': [_barbero_del_dueno_a_dict(b) for b in barberos]
        })

    if request.method == 'POST':
        try:
            data = json.loads(request.body)

            obligatorios = ['nombre', 'apellido', 'email', 'telefono', 'password']
            for campo in obligatorios:
                if not data.get(campo):
                    return JsonResponse({
                        'ok': False,
                        'error': f'El campo {campo} es obligatorio.'
                    }, status=400)

            if Usuario.objects.filter(email=data['email']).exists():
                return JsonResponse({'ok': False, 'error': 'El email ya está registrado'}, status=400)

            nuevo_usuario = Usuario.objects.create(
                nombre=data['nombre'],
                apellido=data['apellido'],
                email=data['email'],
                telefono=data['telefono'],
                password=make_password(data['password']),
                rol='BARBERO',
                estado='ACTIVO',
                fecha_registro=datetime.now()
            )

            barbero = Barbero.objects.create(
                id_usuario=nuevo_usuario,
                id_barberia_id=barberia.id_barberia,
                especialidad=data.get('especialidad', ''),
                foto=data.get('foto'),
                promedio_calificacion=0
            )

            return JsonResponse({
                'ok': True,
                'id_barbero': barbero.id_barbero,
                'nombre': nuevo_usuario.nombre
            }, status=201)

        except Exception as e:
            return JsonResponse({'ok': False, 'error': str(e)}, status=400)

    return JsonResponse({'ok': False, 'error': 'Método no permitido'}, status=405)


# PUT    /api/mi-barberia/barberos/<id>/  -> edición
# DELETE /api/mi-barberia/barberos/<id>/  -> baja (lógica)
def mi_barbero_detalle(request, id):
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

    # Validar pertenencia (Tarea 4): no solo en la lectura, también acá,
    # antes de dejar editar o dar de baja.
    if barbero.id_barberia_id != barberia.id_barberia:
        return JsonResponse({'ok': False, 'error': 'Ese barbero no pertenece a tu barbería.'}, status=403)

    if request.method == 'PUT':
        try:
            data = json.loads(request.body)

            barbero.especialidad = data.get('especialidad', barbero.especialidad)
            barbero.foto = data.get('foto', barbero.foto)
            barbero.save()

            usuario = barbero.id_usuario
            usuario.nombre = data.get('nombre', usuario.nombre)
            usuario.apellido = data.get('apellido', usuario.apellido)
            usuario.telefono = data.get('telefono', usuario.telefono)
            usuario.save()

            return JsonResponse({'ok': True, 'id_barbero': barbero.id_barbero})

        except Exception as e:
            return JsonResponse({'ok': False, 'error': str(e)}, status=400)

    if request.method == 'DELETE':
        # Baja lógica: se inactiva al usuario asociado, no se borra el registro.
        usuario = barbero.id_usuario
        usuario.estado = 'INACTIVO'
        usuario.save()

        return JsonResponse({'ok': True})

    return JsonResponse({'ok': False, 'error': 'Método no permitido'}, status=405)