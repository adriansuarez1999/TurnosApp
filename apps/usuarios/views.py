from datetime import datetime
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.hashers import make_password, check_password
from django.http import JsonResponse
from .models import Usuario, Servicio
from apps.barberias.models import Barberia
from django.shortcuts import render
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
            # Esto NO se decide por usuario.rol, sino por si existe una Barberia
            # cuyo id_dueno sea este usuario. El frontend consulta 'es_dueno'
            # para decidir si muestra el acceso al panel.
            barberia_propia = Barberia.objects.filter(id_dueno=user.id_usuario).first()
            request.session['id_barberia'] = barberia_propia.id_barberia if barberia_propia else None

            return JsonResponse({
                'ok': True,
                'id_usuario': user.id_usuario,
                'nombre': user.nombre,
                'es_dueno': barberia_propia is not None,
                'id_barberia': barberia_propia.id_barberia if barberia_propia else None
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
# CRUD SERVICIOS
# ══════════════════════════════════════════

def servicios(request):
    id_usuario = request.session.get('id_usuario')
    if not id_usuario:
        return JsonResponse({'ok': False, 'error': 'Tenés que iniciar sesión.'}, status=401)

    barberia = Barberia.objects.filter(id_dueno=id_usuario).first()
    if not barberia:
        return JsonResponse({'ok': False, 'error': 'No tenés una barbería registrada.'}, status=404)

    # Listar: solo los servicios de la barbería del dueño logueado.
    if request.method == 'GET':
        lista = list(Servicio.objects.filter(id_barberia=barberia.id_barberia).values(
            'id_servicio', 'nombre', 'precio', 'duracion_minutos', 'descripcion', 'estado'
        ))
        return JsonResponse({'ok': True, 'servicios': lista})

    # Crear: siempre queda asociado a la barbería propia, nunca a otra.
    if request.method == 'POST':
        try:
            data = json.loads(request.body)

            if not data.get('nombre') or not data.get('precio') or not data.get('duracion_minutos'):
                return JsonResponse({
                    'ok': False,
                    'error': 'Nombre, precio y duración son obligatorios.'
                }, status=400)

            s = Servicio.objects.create(
                id_barberia_id=barberia.id_barberia,
                nombre=data['nombre'],
                precio=data['precio'],
                duracion_minutos=data['duracion_minutos'],
                descripcion=data.get('descripcion', ''),
                estado=1
            )

            return JsonResponse({
                'ok': True,
                'id_servicio': s.id_servicio,
                'nombre': s.nombre
            }, status=201)

        except Exception as e:
            return JsonResponse({'ok': False, 'error': str(e)}, status=400)

    return JsonResponse({'ok': False, 'error': 'Metodo no permitido'}, status=405)


def servicio_detalle(request, id):
    id_usuario = request.session.get('id_usuario')
    if not id_usuario:
        return JsonResponse({'ok': False, 'error': 'Tenés que iniciar sesión.'}, status=401)

    barberia = Barberia.objects.filter(id_dueno=id_usuario).first()
    if not barberia:
        return JsonResponse({'ok': False, 'error': 'No tenés una barbería registrada.'}, status=404)

    try:
        s = Servicio.objects.get(id_servicio=id)
    except Servicio.DoesNotExist:
        return JsonResponse({'ok': False, 'error': 'Servicio no encontrado.'}, status=404)

    # Validar pertenencia antes de dejar editar o eliminar — no alcanza con
    # que el servicio exista, tiene que ser de la barbería del dueño logueado.
    if s.id_barberia_id != barberia.id_barberia:
        return JsonResponse({'ok': False, 'error': 'Ese servicio no pertenece a tu barbería.'}, status=403)

    # Editar
    if request.method == 'PUT':
        try:
            data = json.loads(request.body)

            s.nombre = data.get('nombre', s.nombre)
            s.precio = data.get('precio', s.precio)
            s.duracion_minutos = data.get('duracion_minutos', s.duracion_minutos)
            s.descripcion = data.get('descripcion', s.descripcion)
            s.estado = data.get('estado', s.estado)
            s.save()

            return JsonResponse({'ok': True, 'nombre': s.nombre})

        except Exception as e:
            return JsonResponse({'ok': False, 'error': str(e)}, status=400)

    # Eliminar
    if request.method == 'DELETE':
        s.delete()
        return JsonResponse({'ok': True})

    return JsonResponse({'ok': False, 'error': 'Metodo no permitido'}, status=405)
