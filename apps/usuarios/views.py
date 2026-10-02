from datetime import datetime
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.hashers import make_password, check_password
from django.http import JsonResponse
from .models import Usuario, Servicio , Promocion
from apps.barberias.models import Barberia
from django.shortcuts import render
import json
from decimal import Decimal

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



# ══════════════════════════════════════════
# CRUD PROMOCIONES (Sprint 5 - Módulo D)
# ══════════════════════════════════════════

def promociones(request):
    id_usuario = request.session.get('id_usuario')
    if not id_usuario:
        return JsonResponse({'ok': False, 'error': 'Tenés que iniciar sesión.'}, status=401)

    barberia = Barberia.objects.filter(id_dueno=id_usuario).first()
    if not barberia:
        return JsonResponse({'ok': False, 'error': 'No tenés una barbería registrada.'}, status=404)

    # Tarea 3: Consulta de promociones (activas e inactivas)
    if request.method == 'GET':
        promos = Promocion.objects.filter(id_servicio__id_barberia=barberia.id_barberia)
        lista = []
        for p in promos:
            lista.append({
                'id_promocion': p.id_promocion,
                'id_servicio': p.id_servicio_id,
                'servicio_nombre': p.id_servicio.nombre,
                'nombre': p.nombre,
                'porcentaje_descuento': float(p.porcentaje_descuento),
                'fecha_inicio': str(p.fecha_inicio),
                'fecha_fin': str(p.fecha_fin),
                'activa': p.activa
            })
        return JsonResponse({'ok': True, 'promociones': lista})

    # Tarea 1: Alta de promoción
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            id_servicio = data.get('id_servicio')
            nombre = data.get('nombre')
            porcentaje_descuento = data.get('porcentaje_descuento')
            fecha_inicio_str = data.get('fecha_inicio')
            fecha_fin_str = data.get('fecha_fin')

            if not all([id_servicio, nombre, porcentaje_descuento, fecha_inicio_str, fecha_fin_str]):
                return JsonResponse({'ok': False, 'error': 'Todos los campos son obligatorios.'}, status=400)

            # Pertenencia del servicio
            try:
                servicio = Servicio.objects.get(id_servicio=id_servicio, id_barberia=barberia.id_barberia)
            except Servicio.DoesNotExist:
                return JsonResponse({'ok': False, 'error': 'El servicio no pertenece a tu barbería.'}, status=403)

            # Tarea 4: Validaciones
            try:
                porcentaje = Decimal(str(porcentaje_descuento))
                if porcentaje < 1 or porcentaje > 100:
                    return JsonResponse({'ok': False, 'error': 'El porcentaje de descuento debe estar entre 1 y 100.'}, status=400)
            except Exception:
                return JsonResponse({'ok': False, 'error': 'El porcentaje debe ser un valor numérico válido.'}, status=400)

            fecha_inicio = datetime.strptime(fecha_inicio_str, '%Y-%m-%d').date()
            fecha_fin = datetime.strptime(fecha_fin_str, '%Y-%m-%d').date()

            if fecha_fin < fecha_inicio:
                return JsonResponse({'ok': False, 'error': 'La fecha de fin debe ser posterior o igual a la fecha de inicio.'}, status=400)

            p = Promocion.objects.create(
                id_servicio=servicio,
                nombre=nombre,
                porcentaje_descuento=porcentaje,
                fecha_inicio=fecha_inicio,
                fecha_fin=fecha_fin,
                activa=1
            )

            return JsonResponse({'ok': True, 'id_promocion': p.id_promocion, 'nombre': p.nombre}, status=201)

        except Exception as e:
            return JsonResponse({'ok': False, 'error': str(e)}, status=400)

    return JsonResponse({'ok': False, 'error': 'Método no permitido'}, status=405)


def promocion_detalle(request, id):
    id_usuario = request.session.get('id_usuario')
    if not id_usuario:
        return JsonResponse({'ok': False, 'error': 'Tenés que iniciar sesión.'}, status=401)

    barberia = Barberia.objects.filter(id_dueno=id_usuario).first()
    if not barberia:
        return JsonResponse({'ok': False, 'error': 'No tenés una barbería registrada.'}, status=404)

    try:
        p = Promocion.objects.get(id_promocion=id)
    except Promocion.DoesNotExist:
        return JsonResponse({'ok': False, 'error': 'Promoción no encontrada.'}, status=404)

    # Pertenencia
    if p.id_servicio.id_barberia_id != barberia.id_barberia:
        return JsonResponse({'ok': False, 'error': 'Esta promoción no pertenece a tu barbería.'}, status=403)

    # Tarea 2: Edición (PUT)
    if request.method == 'PUT':
        try:
            data = json.loads(request.body)

            if 'porcentaje_descuento' in data:
                porcentaje = Decimal(str(data['porcentaje_descuento']))
                if porcentaje < 1 or porcentaje > 100:
                    return JsonResponse({'ok': False, 'error': 'El porcentaje debe estar entre 1 y 100.'}, status=400)
                p.porcentaje_descuento = porcentaje

            if 'fecha_inicio' in data:
                p.fecha_inicio = datetime.strptime(data['fecha_inicio'], '%Y-%m-%d').date()
            if 'fecha_fin' in data:
                p.fecha_fin = datetime.strptime(data['fecha_fin'], '%Y-%m-%d').date()

            if p.fecha_fin < p.fecha_inicio:
                return JsonResponse({'ok': False, 'error': 'La fecha de fin debe ser posterior o igual a la fecha de inicio.'}, status=400)

            p.nombre = data.get('nombre', p.nombre)
            p.activa = data.get('activa', p.activa)
            p.save()

            return JsonResponse({'ok': True, 'nombre': p.nombre})

        except Exception as e:
            return JsonResponse({'ok': False, 'error': str(e)}, status=400)

    # Tarea 2: Baja (DELETE)
    if request.method == 'DELETE':
        p.delete()
        return JsonResponse({'ok': True})

    return JsonResponse({'ok': False, 'error': 'Método no permitido'}, status=405)