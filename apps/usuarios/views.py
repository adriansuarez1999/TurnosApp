from datetime import datetime, timedelta
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from .models import Usuario, Servicio, Turno
from django.contrib import admin
from django.urls import path, include
from django.shortcuts import render
import json


def home(request):
    return render(request, 'index.html')

urlpatterns = [
    path('admin/', admin.site.urls),

    path('', home),

    path('api/', include('apps.usuarios.urls')),
]


# ══════════════════════════════════════════
# AUTENTICACION
# ══════════════════════════════════════════

@csrf_exempt
def login(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)

            user = Usuario.objects.get(
                email=data['email'],
                password=data['password']
            )

            return JsonResponse({
                'ok': True,
                'nombre': user.nombre
            })

        except Usuario.DoesNotExist:
            return JsonResponse({
                'ok': False,
                'error': 'Email o contrasena incorrectos.'
            })

        except Exception as e:
            return JsonResponse({
                'ok': False,
                'error': str(e)
            })

    return JsonResponse({'ok': False, 'error': 'Metodo no permitido'})


@csrf_exempt
def registro(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)

            if Usuario.objects.filter(email=data['email']).exists():
                return JsonResponse({
                    'ok': False,
                    'error': 'El email ya esta registrado.'
                })

            Usuario.objects.create(
                nombre=data['nombre'],
                apellido=data['apellido'],
                email=data['email'],
                telefono=data.get('telefono', ''),
                password=data['password'],
                rol='cliente',
                estado='activo',
                fecha_registro=datetime.now(),
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

    return JsonResponse({'ok': False, 'error': 'Metodo no permitido'})


# ══════════════════════════════════════════
# CRUD SERVICIOS
# ══════════════════════════════════════════

@csrf_exempt
def servicios(request):
    # Listar todos
    if request.method == 'GET':
        lista = list(Servicio.objects.values(
            'id_servicio', 'nombre', 'precio', 'descripcion'
        ))
        return JsonResponse({'ok': True, 'servicios': lista})

    # Crear nuevo
    if request.method == 'POST':
        try:
            data = json.loads(request.body)

            if not data.get('nombre') or not data.get('precio'):
                return JsonResponse({
                    'ok': False,
                    'error': 'Nombre y precio son obligatorios.'
                })

            s = Servicio.objects.create(
                nombre=data['nombre'],
                precio=data['precio'],
                descripcion=data.get('descripcion', '')
            )

            return JsonResponse({
                'ok': True,
                'id_servicio': s.id_servicio,
                'nombre': s.nombre
            })

        except Exception as e:
            return JsonResponse({'ok': False, 'error': str(e)})

    return JsonResponse({'ok': False, 'error': 'Metodo no permitido'})


@csrf_exempt
def servicio_detalle(request, id):
    # Editar
    if request.method == 'PUT':
        try:
            data = json.loads(request.body)
            s = Servicio.objects.get(id_servicio=id)

            s.nombre = data.get('nombre', s.nombre)
            s.precio = data.get('precio', s.precio)
            s.descripcion = data.get('descripcion', s.descripcion)
            s.save()

            return JsonResponse({'ok': True, 'nombre': s.nombre})

        except Servicio.DoesNotExist:
            return JsonResponse({'ok': False, 'error': 'Servicio no encontrado.'})

        except Exception as e:
            return JsonResponse({'ok': False, 'error': str(e)})

    # Eliminar
    if request.method == 'DELETE':
        try:
            s = Servicio.objects.get(id_servicio=id)
            s.delete()
            return JsonResponse({'ok': True})

        except Servicio.DoesNotExist:
            return JsonResponse({'ok': False, 'error': 'Servicio no encontrado.'})

        except Exception as e:
            return JsonResponse({'ok': False, 'error': str(e)})

    return JsonResponse({'ok': False, 'error': 'Metodo no permitido'})


# ══════════════════════════════════════════
# TURNOS
# ══════════════════════════════════════════

def _parsear_hora(valor):
    # Acepta 'HH:MM' o 'HH:MM:SS'
    formato = '%H:%M:%S' if valor.count(':') == 2 else '%H:%M'
    return datetime.strptime(valor, formato).time()


def _hay_superposicion(id_barbero, fecha_obj, hora_inicio, hora_fin, excluir_id=None):
    # Logica de validacion de superposicion (punto 2 de Adrian)
    turnos = Turno.objects.filter(
        id_barbero=id_barbero,
        fecha=fecha_obj,
        estado='confirmado'
    )

    if excluir_id:
        turnos = turnos.exclude(id_turno=excluir_id)

    for turno in turnos:
        if hora_inicio < turno.hora_fin and hora_fin > turno.hora_inicio:
            return True

    return False


@csrf_exempt
def crear_turno(request):
    # POST /turnos/
    if request.method == 'POST':
        try:
            data = json.loads(request.body)

            obligatorios = ['id_cliente', 'id_barbero', 'id_servicio', 'fecha', 'hora']
            for campo in obligatorios:
                if not data.get(campo):
                    return JsonResponse({
                        'ok': False,
                        'error': f'El campo {campo} es obligatorio.'
                    }, status=400)

            try:
                servicio = Servicio.objects.get(id_servicio=data['id_servicio'])
            except Servicio.DoesNotExist:
                return JsonResponse({'ok': False, 'error': 'El servicio no existe.'}, status=404)

            fecha_obj = datetime.strptime(data['fecha'], '%Y-%m-%d').date()
            hora_inicio = _parsear_hora(data['hora'])

            dt_inicio = datetime.combine(fecha_obj, hora_inicio)
            hora_fin = (dt_inicio + timedelta(minutes=servicio.duracion_minutos)).time()

            # Validar que el barbero no tenga otro turno confirmado en ese horario
            if _hay_superposicion(data['id_barbero'], fecha_obj, hora_inicio, hora_fin):
                return JsonResponse({
                    'ok': False,
                    'error': 'El horario ya esta ocupado para ese barbero.'
                }, status=409)

            turno = Turno.objects.create(
                id_cliente_id=data['id_cliente'],
                id_barbero_id=data['id_barbero'],
                id_servicio_id=data['id_servicio'],
                fecha=fecha_obj,
                hora_inicio=hora_inicio,
                hora_fin=hora_fin,
                estado='confirmado',
                monto_total=servicio.precio,
                fecha_reserva=datetime.now(),
                created_at=datetime.now(),
                updated_at=datetime.now(),
            )

            return JsonResponse({
                'ok': True,
                'id_turno': turno.id_turno,
                'fecha': str(turno.fecha),
                'hora_inicio': turno.hora_inicio.strftime('%H:%M'),
                'hora_fin': turno.hora_fin.strftime('%H:%M'),
                'estado': turno.estado,
                'monto_total': str(turno.monto_total),
            }, status=201)

        except Exception as e:
            return JsonResponse({'ok': False, 'error': str(e)})

    return JsonResponse({'ok': False, 'error': 'Metodo no permitido'})


@csrf_exempt
def turnos_disponibles(request):
    # GET /turnos/disponibles/?barbero=<id>&fecha=<yyyy-mm-dd>
    if request.method == 'GET':
        try:
            id_barbero = request.GET.get('barbero')
            fecha = request.GET.get('fecha')

            if not id_barbero or not fecha:
                return JsonResponse({
                    'ok': False,
                    'error': 'Los parametros barbero y fecha son obligatorios.'
                }, status=400)

            fecha_obj = datetime.strptime(fecha, '%Y-%m-%d').date()

            # Bloques de 30 minutos entre las 14:00 y las 21:00
            duracion_bloque = 30
            hora_apertura = datetime.combine(fecha_obj, _parsear_hora('14:00'))
            hora_cierre = datetime.combine(fecha_obj, _parsear_hora('21:00'))

            turnos_ocupados = Turno.objects.filter(
                id_barbero=id_barbero,
                fecha=fecha_obj,
                estado='confirmado'
            )

            horarios_libres = []
            actual = hora_apertura

            while actual + timedelta(minutes=duracion_bloque) <= hora_cierre:
                bloque_inicio = actual.time()
                bloque_fin = (actual + timedelta(minutes=duracion_bloque)).time()

                ocupado = any(
                    bloque_inicio < t.hora_fin and bloque_fin > t.hora_inicio
                    for t in turnos_ocupados
                )

                if not ocupado:
                    horarios_libres.append(bloque_inicio.strftime('%H:%M'))

                actual += timedelta(minutes=duracion_bloque)

            return JsonResponse({'ok': True, 'horarios': horarios_libres})

        except Exception as e:
            return JsonResponse({'ok': False, 'error': str(e)})

    return JsonResponse({'ok': False, 'error': 'Metodo no permitido'})


@csrf_exempt
def cancelar_turno(request, id):
    # PATCH /turnos/<id>/cancelar/
    if request.method == 'PATCH':
        try:
            data = json.loads(request.body)

            try:
                id_cliente = int(data.get('id_cliente'))
            except (TypeError, ValueError):
                return JsonResponse({'ok': False, 'error': 'id_cliente invalido.'}, status=400)

            try:
                turno = Turno.objects.get(id_turno=id)
            except Turno.DoesNotExist:
                return JsonResponse({'ok': False, 'error': 'Turno no encontrado.'}, status=404)

            if turno.id_cliente_id != id_cliente:
                return JsonResponse({
                    'ok': False,
                    'error': 'No tenes permiso para cancelar este turno.'
                }, status=403)

            turno.estado = 'cancelado'
            turno.updated_at = datetime.now()
            turno.save()

            return JsonResponse({
                'ok': True,
                'id_turno': turno.id_turno,
                'estado': turno.estado,
            }, status=200)

        except Exception as e:
            return JsonResponse({'ok': False, 'error': str(e)})

    return JsonResponse({'ok': False, 'error': 'Metodo no permitido'})


@csrf_exempt
def mis_turnos(request):
    # GET /mis-turnos/?id_cliente=<id>
    if request.method == 'GET':
        try:
            id_cliente = request.GET.get('id_cliente')

            if not id_cliente:
                return JsonResponse({
                    'ok': False,
                    'error': 'El parametro id_cliente es obligatorio.'
                }, status=400)

            hoy = datetime.now().date()

            proximos = Turno.objects.filter(
                id_cliente=id_cliente,
                fecha__gte=hoy
            ).order_by('fecha', 'hora_inicio')

            pasados = Turno.objects.filter(
                id_cliente=id_cliente,
                fecha__lt=hoy
            ).order_by('-fecha', '-hora_inicio')

            def serializar(turno):
                return {
                    'id_turno': turno.id_turno,
                    'barberia': turno.id_barbero.id_barberia.nombre,
                    'barbero': f'{turno.id_barbero.id_usuario.nombre} {turno.id_barbero.id_usuario.apellido}',
                    'servicio': turno.id_servicio.nombre,
                    'fecha': str(turno.fecha),
                    'hora': turno.hora_inicio.strftime('%H:%M'),
                    'estado': turno.estado,
                }

            lista = [serializar(t) for t in proximos] + [serializar(t) for t in pasados]

            return JsonResponse({'ok': True, 'turnos': lista})

        except Exception as e:
            return JsonResponse({'ok': False, 'error': str(e)})

    return JsonResponse({'ok': False, 'error': 'Metodo no permitido'})