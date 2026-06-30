from datetime import datetime
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from .models import Usuario, Servicio
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



