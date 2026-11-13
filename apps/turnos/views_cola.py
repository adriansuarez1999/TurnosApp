import json
from datetime import date, datetime
from django.db import IntegrityError, OperationalError, transaction
from django.db.models import Q
from django.http import JsonResponse
from apps.barberias.models import Barberia
from apps.usuarios.models import Barbero, ColaAtencion, Servicio, Usuario
from . import permisos, reglas

# ══════════════════════════════════════════
# Sprint 7 - Módulo D (Gonzalo): atención por orden de llegada
#
# Una sola cola por barbería y por día (numero_orden = 1, 2, 3...). Es una tabla
# aparte (cola_atencion): nunca crea un Turno ni ocupa una franja reservada.
# Estados: ESPERA -> ATENCION -> CERRADO, o CANCELADO si se va antes de que lo atiendan.
# La barbería sale SIEMPRE de la sesión (permisos.personal_de_barberia): ningún
# endpoint acepta un id de barbería, así que no se puede operar la cola de otra.
# ══════════════════════════════════════════

ESPERA = 'ESPERA'
ATENCION = 'ATENCION'
CERRADO = 'CERRADO'
CANCELADO = 'CANCELADO'
ESTADOS_ACTIVOS = (ESPERA, ATENCION)


def _error(mensaje, status=400):
    return JsonResponse({'ok': False, 'error': mensaje}, status=status)


def _leer_json(request):
    # Devuelve (dict, None) o (None, respuesta_de_error). Sin cuerpo = {}.
    if not request.body:
        return {}, None
    try:
        data = json.loads(request.body)
    except ValueError:
        return None, _error('El cuerpo tiene que ser un JSON válido.')
    if not isinstance(data, dict):
        return None, _error('El cuerpo tiene que ser un objeto JSON.')
    return data, None


def _entero(valor):
    if isinstance(valor, bool):
        return None
    if isinstance(valor, int):
        return valor
    if isinstance(valor, str) and valor.strip().isdigit():
        return int(valor.strip())
    return None


def _es_dueno(request, barberia):
    return barberia.id_dueno_id == request.session.get('id_usuario')


def _consulta_completa():
    return ColaAtencion.objects.select_related(
        'id_cliente', 'id_servicio', 'id_barbero__id_usuario'
    )


def _entrada_a_dict(entrada):
    if entrada.id_cliente_id:
        cliente = f'{entrada.id_cliente.nombre} {entrada.id_cliente.apellido}'
    else:
        cliente = entrada.nombre_cliente

    barbero = None
    if entrada.id_barbero_id:
        usuario = entrada.id_barbero.id_usuario
        barbero = f'{usuario.nombre} {usuario.apellido}'

    return {
        'id': entrada.id_cola,
        'numero_orden': entrada.numero_orden,
        'fecha': str(entrada.fecha),
        'hora_llegada': entrada.hora_llegada.strftime('%Y-%m-%d %H:%M'),
        'estado': entrada.estado,
        'id_cliente': entrada.id_cliente_id,
        'cliente': cliente,
        'telefono_cliente': entrada.telefono_cliente,
        'id_servicio': entrada.id_servicio_id,
        'servicio': entrada.id_servicio.nombre,
        'id_barbero': entrada.id_barbero_id,
        'barbero': barbero,
    }


def _personas_delante(entrada):
    # Cuántos esperan antes que esta entrada. Es un conteo real: no se calcula ni
    # se promete ningún tiempo de espera.
    return ColaAtencion.objects.filter(
        id_barberia=entrada.id_barberia_id,
        fecha=entrada.fecha,
        estado=ESPERA,
        numero_orden__lt=entrada.numero_orden,
    ).count()


def _barbero_de_la_barberia(barberia, id_barbero):
    # Devuelve (barbero, None) o (None, respuesta_de_error).
    barbero = Barbero.objects.select_related('id_usuario').filter(id_barbero=id_barbero).first()
    if not barbero or barbero.id_barberia_id != barberia.id_barberia:
        return None, _error('Ese barbero no pertenece a la barbería.')
    if not reglas.barbero_activo(barbero):
        return None, _error('Ese barbero no está disponible.')
    return barbero, None


# GET  /api/cola/  -> cola de HOY de la barbería del usuario, ordenada por llegada.
# POST /api/cola/  -> registra una llegada sin turno reservado.
#   body: {"id_servicio": 1,
#          "id_cliente": 5            (cliente registrado)  O  "nombre_cliente": "Juan",
#          "telefono_cliente": "..."  (opcional),
#          "id_barbero": 3            (opcional: barbero que prefiere/asignado)}
def cola(request):
    if request.method == 'GET':
        return _listar_cola(request)
    if request.method == 'POST':
        return _registrar_llegada(request)
    return _error('Método no permitido', 405)


def _listar_cola(request):
    barberia, barbero, error = permisos.personal_de_barberia(request)
    if error:
        return error

    hoy = date.today()
    entradas = _consulta_completa().filter(
        id_barberia=barberia.id_barberia, fecha=hoy
    ).order_by('numero_orden')

    return JsonResponse({
        'ok': True,
        'fecha': str(hoy),
        'habilitada': bool(barberia.orden_llegada_habilitado),
        'cola': [_entrada_a_dict(e) for e in entradas],
    })


def _registrar_llegada(request):
    barberia, barbero, error = permisos.personal_de_barberia(request)
    if error:
        return error

    if not barberia.orden_llegada_habilitado:
        return _error('Esta barbería no tiene habilitada la atención por orden de llegada.', 403)

    data, error = _leer_json(request)
    if error:
        return error

    # Servicio: de ESTA barbería y activo.
    id_servicio = _entero(data.get('id_servicio'))
    if id_servicio is None:
        return _error('Falta indicar el servicio.')
    servicio = Servicio.objects.filter(id_servicio=id_servicio).first()
    if not servicio or servicio.id_barberia_id != barberia.id_barberia:
        return _error('El servicio no pertenece a esta barbería.')
    if servicio.estado != 1:
        return _error('Ese servicio no está disponible.')

    # Barbero (opcional): si se manda, tiene que ser de esta barbería y estar activo.
    asignado = None
    if data.get('id_barbero') is not None:
        id_barbero = _entero(data.get('id_barbero'))
        if id_barbero is None:
            return _error('El barbero indicado no es válido.')
        asignado, error = _barbero_de_la_barberia(barberia, id_barbero)
        if error:
            return error

    # Cliente: registrado (y no bloqueado) o solo el nombre de quien llegó.
    cliente = None
    nombre = None
    if data.get('id_cliente') is not None:
        id_cliente = _entero(data.get('id_cliente'))
        if id_cliente is None:
            return _error('El cliente indicado no es válido.')
        cliente = Usuario.objects.filter(id_usuario=id_cliente).first()
        if not cliente:
            return _error('Cliente no encontrado.')
        if cliente.estado == 'BLOQUEADO':
            return _error('Ese cliente está bloqueado y no puede ingresar a la cola.', 403)
        if cliente.estado != 'ACTIVO':
            return _error('Ese cliente no está activo.')
    else:
        nombre = data.get('nombre_cliente')
        if not isinstance(nombre, str) or not nombre.strip():
            return _error('Indicá un cliente registrado o el nombre de quien llegó.')
        nombre = nombre.strip()
        if len(nombre) > 100:
            return _error('El nombre no puede superar los 100 caracteres.')

    telefono = data.get('telefono_cliente')
    if telefono is not None:
        if not isinstance(telefono, str) or len(telefono.strip()) > 20:
            return _error('El teléfono no puede superar los 20 caracteres.')
        telefono = telefono.strip() or None

    ahora = datetime.now()
    hoy = ahora.date()

    try:
        with transaction.atomic():
            # Se bloquea la fila de la barbería (siempre existe): dos registros
            # simultáneos se ordenan y no calculan el mismo número. El UNIQUE de la
            # tabla es la última barrera.
            Barberia.objects.select_for_update().get(id_barberia=barberia.id_barberia)

            if cliente and ColaAtencion.objects.select_for_update().filter(
                id_barberia=barberia.id_barberia,
                fecha=hoy,
                id_cliente=cliente.id_usuario,
                estado__in=ESTADOS_ACTIVOS,
            ).exists():
                return _error('Ese cliente ya está en la cola de hoy.', 409)

            ultimo = ColaAtencion.objects.select_for_update().filter(
                id_barberia=barberia.id_barberia, fecha=hoy
            ).order_by('-numero_orden').values_list('numero_orden', flat=True).first()

            entrada = ColaAtencion.objects.create(
                id_barberia_id=barberia.id_barberia,
                id_barbero_id=asignado.id_barbero if asignado else None,
                id_cliente_id=cliente.id_usuario if cliente else None,
                nombre_cliente=nombre,
                telefono_cliente=telefono,
                id_servicio_id=servicio.id_servicio,
                fecha=hoy,
                numero_orden=(ultimo or 0) + 1,
                hora_llegada=ahora,
                estado=ESPERA,
                created_at=ahora,
                updated_at=ahora,
                created_by_id=request.session.get('id_usuario'),
            )
    except IntegrityError:
        return _error('No se pudo asignar el orden. Probá de nuevo.', 409)
    except OperationalError as e:
        if reglas.es_error_de_concurrencia(e):
            return _error('Hay mucha actividad en este momento. Probá de nuevo.', 409)
        raise

    entrada = _consulta_completa().get(id_cola=entrada.id_cola)
    respuesta = _entrada_a_dict(entrada)
    respuesta['personas_delante'] = _personas_delante(entrada)
    return JsonResponse({'ok': True, 'entrada': respuesta}, status=201)


# POST /api/cola/siguiente/   body (opcional para un barbero): {"id_barbero": 3}
# El barbero pasa a atender al primero en ESPERA que no tenga otro barbero asignado
# (o que lo tenga asignado a él). Tiene que haber cerrado la atención anterior.
# Un dueño que no es barbero indica qué barbero atiende.
def siguiente(request):
    if request.method != 'POST':
        return _error('Método no permitido', 405)

    barberia, barbero, error = permisos.personal_de_barberia(request)
    if error:
        return error

    data, error = _leer_json(request)
    if error:
        return error

    if data.get('id_barbero') is not None:
        id_barbero = _entero(data.get('id_barbero'))
        if id_barbero is None:
            return _error('El barbero indicado no es válido.')
        objetivo, error = _barbero_de_la_barberia(barberia, id_barbero)
        if error:
            return error
    elif barbero:
        objetivo = barbero
    else:
        return _error('Indicá qué barbero atiende.')

    # Un barbero (que no es el dueño) solo toma clientes para sí mismo.
    if not _es_dueno(request, barberia) and (not barbero or objetivo.id_barbero != barbero.id_barbero):
        return _error('Solo podés tomar clientes de la cola para vos.', 403)

    ahora = datetime.now()
    hoy = ahora.date()

    try:
        with transaction.atomic():
            Barberia.objects.select_for_update().get(id_barberia=barberia.id_barberia)

            if ColaAtencion.objects.filter(
                id_barberia=barberia.id_barberia, fecha=hoy,
                id_barbero=objetivo.id_barbero, estado=ATENCION,
            ).exists():
                return _error('Cerrá la atención en curso antes de pasar al siguiente.', 409)

            proximo = ColaAtencion.objects.select_for_update().filter(
                id_barberia=barberia.id_barberia, fecha=hoy, estado=ESPERA,
            ).filter(
                Q(id_barbero__isnull=True) | Q(id_barbero=objetivo.id_barbero)
            ).order_by('numero_orden').first()

            if not proximo:
                return _error('No hay clientes en espera.', 404)

            proximo.id_barbero_id = objetivo.id_barbero
            proximo.estado = ATENCION
            proximo.updated_at = ahora
            proximo.save(update_fields=['id_barbero', 'estado', 'updated_at'])
    except OperationalError as e:
        if reglas.es_error_de_concurrencia(e):
            return _error('Hay mucha actividad en este momento. Probá de nuevo.', 409)
        raise

    return JsonResponse({'ok': True, 'entrada': _entrada_a_dict(_consulta_completa().get(id_cola=proximo.id_cola))})


# Cambia el estado de UNA entrada de la cola de la barbería del usuario.
# Con la entrada bloqueada, dos pedidos simultáneos no pueden cerrarla dos veces.
# Una entrada de otra barbería responde 404 (no se revela que existe).
def _cambiar_estado(request, id, estados_origen, nuevo_estado, solo_asignado):
    if request.method != 'PATCH':
        return _error('Método no permitido', 405)

    barberia, barbero, error = permisos.personal_de_barberia(request)
    if error:
        return error

    ahora = datetime.now()

    with transaction.atomic():
        entrada = ColaAtencion.objects.select_for_update().filter(id_cola=id).first()
        if not entrada or entrada.id_barberia_id != barberia.id_barberia:
            return _error('Entrada de la cola no encontrada.', 404)

        if entrada.estado not in estados_origen:
            return _error(f'No se puede hacer eso con una entrada en estado {entrada.estado}.', 400)

        # Cerrar una atención: solo el barbero que la está haciendo o el dueño.
        if solo_asignado and not _es_dueno(request, barberia):
            if not barbero or entrada.id_barbero_id != barbero.id_barbero:
                return _error('Esa atención no es tuya.', 403)

        entrada.estado = nuevo_estado
        entrada.updated_at = ahora
        entrada.save(update_fields=['estado', 'updated_at'])

    return JsonResponse({'ok': True, 'entrada': _entrada_a_dict(_consulta_completa().get(id_cola=id))})


# PATCH /api/cola/<id>/cerrar/   ATENCION -> CERRADO
def cerrar(request, id):
    return _cambiar_estado(request, id, (ATENCION,), CERRADO, solo_asignado=True)


# PATCH /api/cola/<id>/cancelar/   ESPERA -> CANCELADO (se fue antes de que lo atiendan)
def cancelar(request, id):
    return _cambiar_estado(request, id, (ESPERA,), CANCELADO, solo_asignado=False)


# GET /api/mi-cola/  -> las entradas activas de HOY del cliente logueado.
# 'personas_delante' es un conteo real; no se promete ningún tiempo de espera.
def mi_cola(request):
    if request.method != 'GET':
        return _error('Método no permitido', 405)

    id_usuario = request.session.get('id_usuario')
    if not id_usuario:
        return _error('Tenés que iniciar sesión.', 401)

    entradas = _consulta_completa().select_related('id_barberia').filter(
        id_cliente=id_usuario, fecha=date.today(), estado__in=ESTADOS_ACTIVOS
    ).order_by('numero_orden')

    resultado = []
    for entrada in entradas:
        datos = _entrada_a_dict(entrada)
        datos['barberia'] = entrada.id_barberia.nombre
        datos['personas_delante'] = _personas_delante(entrada) if entrada.estado == ESPERA else None
        resultado.append(datos)

    return JsonResponse({'ok': True, 'entradas': resultado})
