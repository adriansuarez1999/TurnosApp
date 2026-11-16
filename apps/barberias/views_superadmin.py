import json
import os
from datetime import date, datetime, timedelta
from django.contrib.auth.hashers import check_password
from django.db import transaction
from django.db.models import Count, Q, Sum
from django.db.models.functions import TruncMonth
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import ensure_csrf_cookie
from apps.turnos import cobros
from apps.turnos.models import Turno
from apps.usuarios.models import Barbero, Suscripcion, Usuario
from .models import Barberia

# ══════════════════════════════════════════
# Panel del superadministrador (rol ADMIN)
#
# - Solo lectura de estadísticas de toda la plataforma + bloqueo de barberías.
# - Cada endpoint vuelve a consultar en la base que el usuario de la sesión sea
#   ADMIN y esté ACTIVO (no se confía en lo guardado en la sesión).
# - El rol ADMIN no se puede obtener desde la API: se crea con
#   `python manage.py crear_superadmin`.
# - Los ingresos usan el criterio único de apps/turnos/cobros.py (cobros que el
#   barbero registró), así los números coinciden con los de dueños y barberos.
# - "Bloquear" una barbería = pasarla a INACTIVA (la base solo tiene ACTIVA e
#   INACTIVA). Con INACTIVA no se reservan turnos (reglas.py), no opera la cola
#   (permisos.py) y deja de verse en el listado público.
# ══════════════════════════════════════════

ESTADO_ACTIVA = 'ACTIVA'
ESTADO_BLOQUEADA = 'INACTIVA'
MAX_LARGO_MOTIVO = 255
DIAS_POR_VENCER = 30


def _error(mensaje, status=400):
    return JsonResponse({'ok': False, 'error': mensaje}, status=status)


def _requerir_admin(request):
    # Devuelve (admin, None) o (None, respuesta_de_error).
    id_usuario = request.session.get('id_usuario')
    if not id_usuario:
        return None, _error('Tenés que iniciar sesión.', 401)
    admin = Usuario.objects.filter(id_usuario=id_usuario, rol='ADMIN', estado='ACTIVO').first()
    if not admin:
        return None, _error('Solo el superadministrador puede hacer esto.', 403)
    return admin, None


def _leer_json(request):
    if not request.body:
        return {}, None
    try:
        data = json.loads(request.body)
    except ValueError:
        return None, _error('El cuerpo tiene que ser un JSON válido.')
    if not isinstance(data, dict):
        return None, _error('El cuerpo tiene que ser un objeto JSON.')
    return data, None


# Devuelve ((desde, hasta), None) o (None, respuesta_de_error). Ambos opcionales.
def _leer_rango(request):
    try:
        desde = request.GET.get('desde')
        hasta = request.GET.get('hasta')
        desde = datetime.strptime(desde, '%Y-%m-%d').date() if desde else None
        hasta = datetime.strptime(hasta, '%Y-%m-%d').date() if hasta else None
    except ValueError:
        return None, _error('Las fechas tienen que tener formato YYYY-MM-DD.')
    if desde and hasta and desde > hasta:
        return None, _error('La fecha desde no puede ser posterior a hasta.')
    return (desde, hasta), None


def _pagos_confirmados_en(desde, hasta):
    pagos = cobros.pagos_confirmados()
    if desde:
        pagos = pagos.filter(id_turno__fecha__gte=desde)
    if hasta:
        pagos = pagos.filter(id_turno__fecha__lte=hasta)
    return pagos


def _conteo(consulta, campo):
    # {valor: cantidad} de una consulta agrupada por 'campo'.
    return {fila[campo]: fila['n'] for fila in consulta.values(campo).annotate(n=Count('pk'))}


# ── Página del panel y su login propio ──────────────────────────────────────
# GET /api/superadmin/panel/  -> la página (HTML). No muestra datos: pide los
# endpoints de abajo, que verifican el rol ADMIN en cada pedido.
@ensure_csrf_cookie
def panel(request):
    if request.method != 'GET':
        return _error('Método no permitido', 405)
    ruta = os.path.join(os.path.dirname(__file__), 'panel_superadmin.html')
    with open(ruta, encoding='utf-8') as f:
        return HttpResponse(f.read(), content_type='text/html; charset=utf-8')


# POST /api/superadmin/login/   body: {"email": "...", "password": "..."}
# Solo inicia sesión una cuenta ADMIN activa. Distingue "cuenta que no es admin"
# únicamente después de validar la contraseña, para no revelar si un email existe.
def login_admin(request):
    if request.method != 'POST':
        return _error('Método no permitido', 405)
    data, error = _leer_json(request)
    if error:
        return error
    email, password = data.get('email'), data.get('password')
    if not isinstance(email, str) or not isinstance(password, str):
        return _error('Ingresá email y contraseña.')

    usuario = Usuario.objects.filter(email=email.strip()).first()
    if not usuario or not check_password(password, usuario.password):
        return _error('Credenciales incorrectas.', 401)
    if usuario.rol != 'ADMIN' or usuario.estado != 'ACTIVO':
        return _error('Esa cuenta no es de superadministrador.', 403)

    request.session.flush()  # sesión nueva: evita reutilizar una anterior
    request.session['id_usuario'] = usuario.id_usuario
    request.session['rol'] = usuario.rol
    return JsonResponse({'ok': True, 'nombre': usuario.nombre})


# POST /api/superadmin/logout/
def logout_admin(request):
    request.session.flush()
    return JsonResponse({'ok': True})


# GET /api/superadmin/resumen/?desde=YYYY-MM-DD&hasta=YYYY-MM-DD
# Vista general. El rango (por fecha del turno) afecta a turnos e ingresos.
def resumen(request):
    if request.method != 'GET':
        return _error('Método no permitido', 405)
    admin, error = _requerir_admin(request)
    if error:
        return error
    rango, error = _leer_rango(request)
    if error:
        return error
    desde, hasta = rango

    barberias = _conteo(Barberia.objects, 'estado')
    barberias.setdefault(ESTADO_ACTIVA, 0)
    barberias.setdefault(ESTADO_BLOQUEADA, 0)

    turnos = Turno.objects.all()
    if desde:
        turnos = turnos.filter(fecha__gte=desde)
    if hasta:
        turnos = turnos.filter(fecha__lte=hasta)
    turnos_por_estado = _conteo(turnos, 'estado')

    total_cobrado, cobros_registrados = cobros.resumen_cobros(_pagos_confirmados_en(desde, hasta))

    hoy = date.today()
    return JsonResponse({
        'ok': True,
        'desde': str(desde) if desde else None,
        'hasta': str(hasta) if hasta else None,
        'barberias': {'por_estado': barberias, 'total': sum(barberias.values())},
        'usuarios': {
            'por_rol': _conteo(Usuario.objects, 'rol'),
            'por_estado': _conteo(Usuario.objects, 'estado'),
        },
        'turnos': {'por_estado': turnos_por_estado, 'total': sum(turnos_por_estado.values())},
        'ingresos': {'total': float(total_cobrado), 'cobros_registrados': cobros_registrados},
        'suscripciones': {
            'vencidas': Suscripcion.objects.filter(fecha_fin__lt=hoy).count(),
            'por_vencer': Suscripcion.objects.filter(
                fecha_fin__gte=hoy, fecha_fin__lte=hoy + timedelta(days=DIAS_POR_VENCER)
            ).count(),
        },
    })


# GET /api/superadmin/ingresos/?desde=&hasta=&top=10
# Ingresos confirmados de toda la plataforma, ranking por barbería y serie mensual.
def ingresos(request):
    if request.method != 'GET':
        return _error('Método no permitido', 405)
    admin, error = _requerir_admin(request)
    if error:
        return error
    rango, error = _leer_rango(request)
    if error:
        return error
    desde, hasta = rango

    top = request.GET.get('top')
    if top is not None:
        if not top.isdigit() or not (1 <= int(top) <= 100):
            return _error('top tiene que ser un número entre 1 y 100.')
        top = int(top)

    pagos = _pagos_confirmados_en(desde, hasta)
    total, cantidad = cobros.resumen_cobros(pagos)

    clave = 'id_turno__id_barbero__id_barberia'
    ranking = pagos.values(clave, clave + '__nombre').annotate(
        total=Sum('monto'), cobros=Count('id_turno', distinct=True)
    ).order_by('-total', clave + '__nombre')
    if top:
        ranking = ranking[:top]

    por_mes = pagos.annotate(mes=TruncMonth('id_turno__fecha')).values('mes').annotate(
        total=Sum('monto'), cobros=Count('id_turno', distinct=True)
    ).order_by('mes')

    return JsonResponse({
        'ok': True,
        'desde': str(desde) if desde else None,
        'hasta': str(hasta) if hasta else None,
        'total': float(total),
        'cobros_registrados': cantidad,
        'por_barberia': [
            {
                'id_barberia': fila[clave],
                'barberia': fila[clave + '__nombre'],
                'total': float(fila['total']),
                'cobros': fila['cobros'],
            }
            for fila in ranking
        ],
        'por_mes': [
            {'mes': fila['mes'].strftime('%Y-%m'), 'total': float(fila['total']), 'cobros': fila['cobros']}
            for fila in por_mes
        ],
    })


# GET /api/superadmin/barberias/?estado=ACTIVA|INACTIVA&search=texto
def barberias(request):
    if request.method != 'GET':
        return _error('Método no permitido', 405)
    admin, error = _requerir_admin(request)
    if error:
        return error

    consulta = Barberia.objects.select_related('id_dueno').order_by('nombre')

    estado = request.GET.get('estado')
    if estado:
        if estado not in (ESTADO_ACTIVA, ESTADO_BLOQUEADA):
            return _error('El estado tiene que ser ACTIVA o INACTIVA.')
        consulta = consulta.filter(estado=estado)

    texto = request.GET.get('search', '').strip()
    if texto:
        consulta = consulta.filter(
            Q(nombre__icontains=texto) | Q(zona__icontains=texto) | Q(id_dueno__email__icontains=texto)
        )

    # Tres consultas agrupadas en lugar de una por barbería.
    barberos = {f['id_barberia']: f['n'] for f in Barbero.objects.values('id_barberia').annotate(n=Count('pk'))}
    clave = 'id_barbero__id_barberia'
    turnos = {f[clave]: f['n'] for f in Turno.objects.values(clave).annotate(n=Count('pk'))}
    clave_pago = 'id_turno__id_barbero__id_barberia'
    cobrado = {
        f[clave_pago]: f['total']
        for f in cobros.pagos_confirmados().values(clave_pago).annotate(total=Sum('monto'))
    }

    return JsonResponse({
        'ok': True,
        'barberias': [
            {
                'id': b.id_barberia,
                'nombre': b.nombre,
                'zona': b.zona,
                'estado': b.estado,
                'bloqueada': b.estado == ESTADO_BLOQUEADA,
                'dueno': {
                    'id': b.id_dueno_id,
                    'nombre': f'{b.id_dueno.nombre} {b.id_dueno.apellido}',
                    'email': b.id_dueno.email,
                },
                'barberos': barberos.get(b.id_barberia, 0),
                'turnos_totales': turnos.get(b.id_barberia, 0),
                'ingresos_confirmados': float(cobrado.get(b.id_barberia, 0)),
            }
            for b in consulta
        ],
    })


# Aviso interno al dueño. Es un extra: si falla, el cambio de estado igual queda hecho
# y la respuesta lo informa con aviso_enviado = false.
def _avisar_al_dueno(barberia, tipo, mensaje):
    try:
        from apps.turnos.views_notificaciones import crear_notificacion
        crear_notificacion(barberia.id_dueno_id, tipo, mensaje)
        return True
    except Exception:
        return False


def _cambiar_estado_barberia(request, id, nuevo_estado):
    if request.method != 'PATCH':
        return _error('Método no permitido', 405)
    admin, error = _requerir_admin(request)
    if error:
        return error
    data, error = _leer_json(request)
    if error:
        return error

    bloquear = nuevo_estado == ESTADO_BLOQUEADA
    motivo = data.get('motivo')
    if motivo is not None and not isinstance(motivo, str):
        return _error('El motivo tiene que ser texto.')
    motivo = (motivo or '').strip()
    if len(motivo) > MAX_LARGO_MOTIVO:
        return _error(f'El motivo no puede superar los {MAX_LARGO_MOTIVO} caracteres.')
    if bloquear and not motivo:
        return _error('Indicá el motivo del bloqueo.')

    with transaction.atomic():
        barberia = Barberia.objects.select_for_update().filter(id_barberia=id).first()
        if not barberia:
            return _error('Barbería no encontrada.', 404)
        if barberia.estado == nuevo_estado:
            return _error(
                'Esa barbería ya está bloqueada.' if bloquear else 'Esa barbería ya está activa.', 409
            )
        barberia.estado = nuevo_estado
        barberia.save(update_fields=['estado'])

    if bloquear:
        mensaje = (
            f'Tu barbería "{barberia.nombre}" fue bloqueada por la administración de '
            f'BarberApp. Motivo: {motivo}'
        )
        tipo = 'BARBERIA_BLOQUEADA'
    else:
        mensaje = f'Tu barbería "{barberia.nombre}" fue habilitada nuevamente.'
        if motivo:
            mensaje += f' {motivo}'
        tipo = 'BARBERIA_DESBLOQUEADA'

    return JsonResponse({
        'ok': True,
        'id': barberia.id_barberia,
        'estado': barberia.estado,
        'aviso_enviado': _avisar_al_dueno(barberia, tipo, mensaje),
    })


# PATCH /api/superadmin/barberias/<id>/bloquear/     body: {"motivo": "..."}  (obligatorio)
def bloquear_barberia(request, id):
    return _cambiar_estado_barberia(request, id, ESTADO_BLOQUEADA)


# PATCH /api/superadmin/barberias/<id>/desbloquear/  body: {"motivo": "..."}  (opcional)
def desbloquear_barberia(request, id):
    return _cambiar_estado_barberia(request, id, ESTADO_ACTIVA)


# GET /api/superadmin/suscripciones/?filtro=vencidas|por_vencer&dias=30
# 'vencida' se calcula por fecha_fin, sin depender de los valores del campo estado.
def suscripciones(request):
    if request.method != 'GET':
        return _error('Método no permitido', 405)
    admin, error = _requerir_admin(request)
    if error:
        return error

    hoy = date.today()
    consulta = Suscripcion.objects.select_related('id_barberia', 'id_plan').order_by('fecha_fin')

    filtro = request.GET.get('filtro')
    if filtro == 'vencidas':
        consulta = consulta.filter(fecha_fin__lt=hoy)
    elif filtro == 'por_vencer':
        dias = request.GET.get('dias', str(DIAS_POR_VENCER))
        if not dias.isdigit() or not (1 <= int(dias) <= 365):
            return _error('dias tiene que ser un número entre 1 y 365.')
        consulta = consulta.filter(fecha_fin__gte=hoy, fecha_fin__lte=hoy + timedelta(days=int(dias)))
    elif filtro:
        return _error('filtro tiene que ser vencidas o por_vencer.')

    return JsonResponse({
        'ok': True,
        'suscripciones': [
            {
                'id': s.id_suscripcion,
                'id_barberia': s.id_barberia_id,
                'barberia': s.id_barberia.nombre,
                'plan': s.id_plan.nombre,
                'fecha_inicio': str(s.fecha_inicio),
                'fecha_fin': str(s.fecha_fin),
                'estado': s.estado,
                'vencida': s.fecha_fin < hoy,
                'dias_restantes': (s.fecha_fin - hoy).days,
            }
            for s in consulta
        ],
    })
