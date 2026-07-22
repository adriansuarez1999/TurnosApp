from django.shortcuts import render
from .models import Barberia, FotoBarberia
from django.db.models import Q
from django.http import JsonResponse
from django.views.decorators.http import require_GET
from apps.usuarios.models import Barbero, Servicio

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