from datetime import datetime
from .models import Barberia, FotoBarberia
from django.db.models import Q, Sum, Count
from django.http import JsonResponse
from django.views.decorators.http import require_GET
from django.contrib.auth.hashers import make_password
from django.core.files.storage import default_storage
from apps.usuarios.models import Barbero, Servicio, Usuario, Disponibilidad
from apps.turnos.models import Turno
import json


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
        servicios = Servicio.objects.filter(id_barberia=barberia.id_barberia, estado=1)
        barberos = Barbero.objects.filter(id_barberia=barberia.id_barberia).exclude(id_usuario__estado='INACTIVO')
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

    barberos = Barbero.objects.all().exclude(id_usuario__estado='INACTIVO')
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
            usuario.estado = data.get('estado', usuario.estado)
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


# ══════════════════════════════════════════
# Sprint 4 - Módulo A: Disponibilidad de barberos (CU-10)
# ══════════════════════════════════════════

DIAS_VALIDOS = ('LUN', 'MAR', 'MIE', 'JUE', 'VIE', 'SAB', 'DOM')


def _parsear_hora(valor):
    # Acepta 'HH:MM' o 'HH:MM:SS'
    formato = '%H:%M:%S' if valor.count(':') == 2 else '%H:%M'
    return datetime.strptime(valor, formato).time()


def _disponibilidad_a_dict(bloque):
    return {
        'id': bloque.id_disponibilidad,
        'id_barbero': bloque.id_barbero_id,
        'dia_semana': bloque.dia_semana,
        'hora_inicio': bloque.hora_inicio.strftime('%H:%M'),
        'hora_fin': bloque.hora_fin.strftime('%H:%M'),
    }


# Tarea 4: hora_fin > hora_inicio y sin superposición entre bloques del mismo
# barbero el mismo día (mismo criterio de superposición usado para turnos en el Sprint 2).
def _validar_bloque_disponibilidad(id_barbero, dia_semana, hora_inicio, hora_fin, excluir_id=None):
    if dia_semana not in DIAS_VALIDOS:
        return f'El día tiene que ser uno de {", ".join(DIAS_VALIDOS)}.'

    if hora_fin <= hora_inicio:
        return 'La hora de fin tiene que ser mayor a la hora de inicio.'

    superpuestos = Disponibilidad.objects.filter(
        id_barbero=id_barbero,
        dia_semana=dia_semana,
        hora_inicio__lt=hora_fin,
        hora_fin__gt=hora_inicio
    )
    if excluir_id:
        superpuestos = superpuestos.exclude(id_disponibilidad=excluir_id)

    if superpuestos.exists():
        return 'Ese barbero ya tiene un bloque cargado que se superpone con ese horario ese día.'

    return None


# GET  /api/mi-barberia/barberos/<id>/disponibilidad/  -> tarea 3: bloques del barbero
# POST /api/mi-barberia/barberos/<id>/disponibilidad/   -> tarea 1: alta de un bloque
def disponibilidad_barbero(request, id):
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

    # Mismo chequeo de pertenencia que en el resto del panel (Sprint 3).
    if barbero.id_barberia_id != barberia.id_barberia:
        return JsonResponse({'ok': False, 'error': 'Ese barbero no pertenece a tu barbería.'}, status=403)

    if request.method == 'GET':
        bloques = Disponibilidad.objects.filter(id_barbero=barbero.id_barbero).order_by('dia_semana', 'hora_inicio')
        return JsonResponse({
            'ok': True,
            'disponibilidad': [_disponibilidad_a_dict(b) for b in bloques]
        })

    if request.method == 'POST':
        try:
            data = json.loads(request.body)

            obligatorios = ['dia_semana', 'hora_inicio', 'hora_fin']
            for campo in obligatorios:
                if not data.get(campo):
                    return JsonResponse({
                        'ok': False,
                        'error': f'El campo {campo} es obligatorio.'
                    }, status=400)

            dia_semana = data['dia_semana'].upper()
            hora_inicio = _parsear_hora(data['hora_inicio'])
            hora_fin = _parsear_hora(data['hora_fin'])

            error = _validar_bloque_disponibilidad(barbero.id_barbero, dia_semana, hora_inicio, hora_fin)
            if error:
                return JsonResponse({'ok': False, 'error': error}, status=400)

            bloque = Disponibilidad.objects.create(
                id_barbero_id=barbero.id_barbero,
                dia_semana=dia_semana,
                hora_inicio=hora_inicio,
                hora_fin=hora_fin
            )

            return JsonResponse({'ok': True, 'id': bloque.id_disponibilidad}, status=201)

        except Exception as e:
            return JsonResponse({'ok': False, 'error': str(e)}, status=400)

    return JsonResponse({'ok': False, 'error': 'Método no permitido'}, status=405)


# PUT    /api/mi-barberia/disponibilidad/<id>/  -> tarea 2: edición de un bloque
# DELETE /api/mi-barberia/disponibilidad/<id>/  -> tarea 2: baja de un bloque
def mi_disponibilidad_detalle(request, id):
    id_usuario = _usuario_logueado(request)
    if not id_usuario:
        return JsonResponse({'ok': False, 'error': 'Tenés que iniciar sesión.'}, status=401)

    barberia = _barberia_del_dueno(id_usuario)
    if not barberia:
        return JsonResponse({'ok': False, 'error': 'No tenés una barbería registrada.'}, status=404)

    try:
        bloque = Disponibilidad.objects.get(id_disponibilidad=id)
    except Disponibilidad.DoesNotExist:
        return JsonResponse({'ok': False, 'error': 'Bloque de disponibilidad no encontrado.'}, status=404)

    # Validar pertenencia acá también, no solo en la consulta: mismo criterio
    # que en mi_barbero_detalle.
    if bloque.id_barbero.id_barberia_id != barberia.id_barberia:
        return JsonResponse({'ok': False, 'error': 'Ese bloque no pertenece a tu barbería.'}, status=403)

    if request.method == 'PUT':
        try:
            data = json.loads(request.body)

            dia_semana = data.get('dia_semana', bloque.dia_semana).upper()
            hora_inicio = _parsear_hora(data['hora_inicio']) if data.get('hora_inicio') else bloque.hora_inicio
            hora_fin = _parsear_hora(data['hora_fin']) if data.get('hora_fin') else bloque.hora_fin

            error = _validar_bloque_disponibilidad(
                bloque.id_barbero_id, dia_semana, hora_inicio, hora_fin,
                excluir_id=bloque.id_disponibilidad
            )
            if error:
                return JsonResponse({'ok': False, 'error': error}, status=400)

            bloque.dia_semana = dia_semana
            bloque.hora_inicio = hora_inicio
            bloque.hora_fin = hora_fin
            bloque.save()

            return JsonResponse({'ok': True, 'id': bloque.id_disponibilidad})

        except Exception as e:
            return JsonResponse({'ok': False, 'error': str(e)}, status=400)

    if request.method == 'DELETE':
        bloque.delete()
        return JsonResponse({'ok': True})

    return JsonResponse({'ok': False, 'error': 'Método no permitido'}, status=405)


def _foto_a_dict(foto):
    return {
        'id': foto.id_foto,
        'url': foto.url,
        'orden': foto.orden,
    }


# ══════════════════════════════════════════
# Fotos de portada (panel del dueño)
# ══════════════════════════════════════════

# GET  /api/mi-barberia/fotos/  -> listar las fotos de portada propias
# POST /api/mi-barberia/fotos/  -> agregar una foto nueva
def mis_fotos_barberia(request):
    id_usuario = _usuario_logueado(request)
    if not id_usuario:
        return JsonResponse({'ok': False, 'error': 'Tenés que iniciar sesión.'}, status=401)

    barberia = _barberia_del_dueno(id_usuario)
    if not barberia:
        return JsonResponse({'ok': False, 'error': 'No tenés una barbería registrada.'}, status=404)

    if request.method == 'GET':
        fotos = FotoBarberia.objects.filter(id_barberia=barberia.id_barberia).order_by('orden')
        return JsonResponse({
            'ok': True,
            'fotos': [_foto_a_dict(f) for f in fotos]
        })

    if request.method == 'POST':
        try:
            data = json.loads(request.body)

            if not data.get('url'):
                return JsonResponse({'ok': False, 'error': 'Falta la url de la foto.'}, status=400)

            ultimo_orden = FotoBarberia.objects.filter(id_barberia=barberia.id_barberia).count()

            foto = FotoBarberia.objects.create(
                id_barberia_id=barberia.id_barberia,
                url=data['url'],
                orden=data.get('orden', ultimo_orden),
            )

            return JsonResponse({'ok': True, 'id': foto.id_foto}, status=201)

        except Exception as e:
            return JsonResponse({'ok': False, 'error': str(e)}, status=400)

    return JsonResponse({'ok': False, 'error': 'Método no permitido'}, status=405)


# DELETE /api/mi-barberia/fotos/<id>/  -> sacar una foto de portada
def mi_foto_detalle(request, id):
    if request.method != 'DELETE':
        return JsonResponse({'ok': False, 'error': 'Método no permitido'}, status=405)

    id_usuario = _usuario_logueado(request)
    if not id_usuario:
        return JsonResponse({'ok': False, 'error': 'Tenés que iniciar sesión.'}, status=401)

    barberia = _barberia_del_dueno(id_usuario)
    if not barberia:
        return JsonResponse({'ok': False, 'error': 'No tenés una barbería registrada.'}, status=404)

    try:
        foto = FotoBarberia.objects.get(id_foto=id)
    except FotoBarberia.DoesNotExist:
        return JsonResponse({'ok': False, 'error': 'Foto no encontrada.'}, status=404)

    if foto.id_barberia_id != barberia.id_barberia:
        return JsonResponse({'ok': False, 'error': 'Esa foto no pertenece a tu barbería.'}, status=403)

    foto.delete()
    return JsonResponse({'ok': True})


# ══════════════════════════════════════════
# Tarea 6: Informes
# ══════════════════════════════════════════

# GET /api/mi-barberia/informes/?desde=YYYY-MM-DD&hasta=YYYY-MM-DD
@require_GET
def informes(request):
    id_usuario = _usuario_logueado(request)
    if not id_usuario:
        return JsonResponse({'ok': False, 'error': 'Tenés que iniciar sesión.'}, status=401)

    barberia = _barberia_del_dueno(id_usuario)
    if not barberia:
        return JsonResponse({'ok': False, 'error': 'No tenés una barbería registrada.'}, status=404)

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
# Reemplaza (o complementa) la carga manual de rutas del Sprint 2.
# ══════════════════════════════════════════

def _guardar_archivo(archivo, carpeta):
    """Guarda un archivo subido en media/<carpeta>/ y devuelve la URL pública."""
    ruta_guardada = default_storage.save(f'{carpeta}/{archivo.name}', archivo)
    return default_storage.url(ruta_guardada)


# POST multipart/form-data con el campo 'logo' -> media/logos/
def subir_logo_barberia(request):
    if request.method != 'POST':
        return JsonResponse({'ok': False, 'error': 'Método no permitido'}, status=405)

    id_usuario = _usuario_logueado(request)
    if not id_usuario:
        return JsonResponse({'ok': False, 'error': 'Tenés que iniciar sesión.'}, status=401)

    barberia = _barberia_del_dueno(id_usuario)
    if not barberia:
        return JsonResponse({'ok': False, 'error': 'No tenés una barbería registrada.'}, status=404)

    archivo = request.FILES.get('logo')
    if not archivo:
        return JsonResponse({'ok': False, 'error': 'No se recibió ningún archivo (campo "logo").'}, status=400)

    barberia.logo = _guardar_archivo(archivo, 'logos')
    barberia.save()

    return JsonResponse({'ok': True, 'logo': barberia.logo})


# POST multipart/form-data con el campo 'foto' -> media/portadas/
def subir_foto_portada(request):
    if request.method != 'POST':
        return JsonResponse({'ok': False, 'error': 'Método no permitido'}, status=405)

    id_usuario = _usuario_logueado(request)
    if not id_usuario:
        return JsonResponse({'ok': False, 'error': 'Tenés que iniciar sesión.'}, status=401)

    barberia = _barberia_del_dueno(id_usuario)
    if not barberia:
        return JsonResponse({'ok': False, 'error': 'No tenés una barbería registrada.'}, status=404)

    archivo = request.FILES.get('foto')
    if not archivo:
        return JsonResponse({'ok': False, 'error': 'No se recibió ningún archivo (campo "foto").'}, status=400)

    url = _guardar_archivo(archivo, 'portadas')
    orden = FotoBarberia.objects.filter(id_barberia=barberia.id_barberia).count()

    foto = FotoBarberia.objects.create(
        id_barberia_id=barberia.id_barberia,
        url=url,
        orden=orden,
    )

    return JsonResponse({'ok': True, 'id': foto.id_foto, 'url': foto.url}, status=201)


# POST multipart/form-data con el campo 'foto' -> media/barberos/
def subir_foto_barbero(request, id):
    if request.method != 'POST':
        return JsonResponse({'ok': False, 'error': 'Método no permitido'}, status=405)

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

    if barbero.id_barberia_id != barberia.id_barberia:
        return JsonResponse({'ok': False, 'error': 'Ese barbero no pertenece a tu barbería.'}, status=403)

    archivo = request.FILES.get('foto')
    if not archivo:
        return JsonResponse({'ok': False, 'error': 'No se recibió ningún archivo (campo "foto").'}, status=400)

    barbero.foto = _guardar_archivo(archivo, 'barberos')
    barbero.save()

    return JsonResponse({'ok': True, 'foto': barbero.foto})

