from datetime import datetime
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.hashers import make_password, check_password
from django.http import JsonResponse
from django.shortcuts import render
from .models import Usuario, Servicio
from apps.barberias.models import Barberia
import json


def home(request):
    return render(request, 'index.html')


# ══════════════════════════════════════════
# AUTENTICACION
# ══════════════════════════════════════════

# LOGIN
def login(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)

            user = Usuario.objects.get(email=data['email'])

            if not check_password(data['password'], user.password):
                return JsonResponse({
                    'ok': False,
                    'error': 'Credenciales incorrectas'
                })

            # A partir de acá, el backend sabe quién sos por la sesión,
            # no por lo que mande el frontend en cada pedido.
            request.session['id_usuario'] = user.id_usuario
            request.session['rol'] = user.rol

            # Tarea 2: la sesión reconoce si el usuario es dueño de una barbería.
            # El frontend consulta 'es_dueno' para decidir si muestra el acceso al panel.
            barberia = Barberia.objects.filter(id_dueno=user.id_usuario).first()
            request.session['es_dueno'] = barberia is not None
            request.session['id_barberia'] = barberia.id_barberia if barberia else None

            return JsonResponse({
                'ok': True,
                'id_usuario': user.id_usuario,
                'nombre': user.nombre,
                'es_dueno': request.session['es_dueno'],
            })

        except Usuario.DoesNotExist:
            return JsonResponse({
                'ok': False,
                'error': 'Credenciales incorrectas'
            })

        except Exception as e:
            return JsonResponse({
                'ok': False,
                'error': str(e)
            })

    return JsonResponse({
        'ok': False,
        'error': 'Método no permitido'
    })


# LOGOUT
def logout(request):
    request.session.flush()
    return JsonResponse({'ok': True})


# REGISTRO
def registro(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)

            if Usuario.objects.filter(email=data['email']).exists():
                return JsonResponse({
                    'ok': False,
                    'error': 'El email ya está registrado'
                })

            Usuario.objects.create(
                nombre=data['nombre'],
                apellido=data['apellido'],
                email=data['email'],
                telefono=data.get('telefono', ''),
                password=make_password(data['password']),
                rol='cliente',
                estado='activo',
                fecha_registro=datetime.now()
            )

            return JsonResponse({
                'ok': True,
                'nombre': data['nombre']
            })

        except Exception as e:
            return JsonResponse({
                'ok': False,
                'error': str(e)
            })

    return JsonResponse({
        'ok': False,
        'error': 'Método no permitido'
    })


# ══════════════════════════════════════════
# CRUD SERVICIOS  (Tarea 5)
# ══════════════════════════════════════════

def _servicio_a_dict(s):
    return {
        'id_servicio': s.id_servicio,
        'nombre': s.nombre,
        'precio': float(s.precio),
        'descripcion': s.descripcion,
        'duracion_minutos': s.duracion_minutos,
        'estado': s.estado,
    }


def _get_barberia_del_dueno(request):
    """
    Devuelve (barberia, None) si hay un usuario logueado con una barbería propia.
    Si no, devuelve (None, JsonResponse_de_error) listo para retornar tal cual.
    """
    id_usuario = request.session.get('id_usuario')
    if not id_usuario:
        return None, JsonResponse({'ok': False, 'error': 'Debés iniciar sesión.'}, status=401)

    barberia = Barberia.objects.filter(id_dueno=id_usuario).first()
    if not barberia:
        return None, JsonResponse({'ok': False, 'error': 'No tenés una barbería registrada.'}, status=403)

    return barberia, None


@csrf_exempt
def servicios(request):
    # GET: listado público — SIN CAMBIOS, lo sigue usando el sitio público (Sprint 2)
    if request.method == 'GET':
        lista = list(Servicio.objects.values(
            'id_servicio', 'nombre', 'precio', 'descripcion'
        ))
        return JsonResponse({'ok': True, 'servicios': lista})

    # POST: alta de servicio — ahora atada a la barbería del dueño logueado
    if request.method == 'POST':
        barberia, error = _get_barberia_del_dueno(request)
        if error:
            return error

        try:
            data = json.loads(request.body)

            if not data.get('nombre') or not data.get('precio'):
                return JsonResponse({
                    'ok': False,
                    'error': 'Nombre y precio son obligatorios.'
                })

            s = Servicio.objects.create(
                id_barberia=barberia,
                nombre=data['nombre'],
                precio=data['precio'],
                descripcion=data.get('descripcion', ''),
                duracion_minutos=data.get('duracion_minutos', 30),
                estado=data.get('estado', 1),
            )

            return JsonResponse({'ok': True, 'servicio': _servicio_a_dict(s)})

        except Exception as e:
            return JsonResponse({'ok': False, 'error': str(e)})

    return JsonResponse({'ok': False, 'error': 'Metodo no permitido'})


@csrf_exempt
def servicio_detalle(request, id):
    # GET: detalle público — SIN CAMBIOS
    if request.method == 'GET':
        try:
            s = Servicio.objects.get(id_servicio=id)
        except Servicio.DoesNotExist:
            return JsonResponse({'ok': False, 'error': 'Servicio no encontrado.'}, status=404)
        return JsonResponse({'ok': True, 'servicio': _servicio_a_dict(s)})

    # PUT / DELETE: requieren dueño logueado Y que el servicio sea de SU barbería
    barberia, error = _get_barberia_del_dueno(request)
    if error:
        return error

    try:
        s = Servicio.objects.get(id_servicio=id)
    except Servicio.DoesNotExist:
        return JsonResponse({'ok': False, 'error': 'Servicio no encontrado.'}, status=404)

    if s.id_barberia_id != barberia.id_barberia:
        return JsonResponse({'ok': False, 'error': 'Ese servicio no pertenece a tu barbería.'}, status=403)

    if request.method == 'PUT':
        try:
            data = json.loads(request.body)

            s.nombre = data.get('nombre', s.nombre)
            s.precio = data.get('precio', s.precio)
            s.descripcion = data.get('descripcion', s.descripcion)
            s.duracion_minutos = data.get('duracion_minutos', s.duracion_minutos)
            s.estado = data.get('estado', s.estado)
            s.save()

            return JsonResponse({'ok': True, 'servicio': _servicio_a_dict(s)})

        except Exception as e:
            return JsonResponse({'ok': False, 'error': str(e)})

    if request.method == 'DELETE':
        s.delete()
        return JsonResponse({'ok': True})

    return JsonResponse({'ok': False, 'error': 'Metodo no permitido'})