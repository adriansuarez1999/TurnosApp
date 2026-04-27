from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from .models import Usuario
import json

# LOGIN
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


# REGISTRO
@csrf_exempt
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
                password=data['password']
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