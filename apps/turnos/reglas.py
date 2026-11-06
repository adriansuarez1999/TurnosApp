from datetime import datetime, timedelta
from apps.usuarios.models import Barbero, Disponibilidad
from .models import Turno

# ══════════════════════════════════════════
# Sprint 7 - Módulo A (Facundo): reglas de reserva compartidas
# Acá viven las reglas que usan crear, cancelar y reprogramar un turno,
# para que los tres endpoints validen exactamente lo mismo.
# ══════════════════════════════════════════

DIAS_SEMANA = ['LUN', 'MAR', 'MIE', 'JUE', 'VIE', 'SAB', 'DOM']

# Paso de la grilla de horarios que devuelve /turnos/disponibles/.
DURACION_BLOQUE_MINUTOS = 30

# No se puede reservar con más de estos días de anticipación.
MAX_DIAS_ANTICIPACION_RESERVA = 60

# Si la barbería todavía no configuró su límite (Sprint 7 - Módulo B, Gonzalo),
# se usa este valor. Es el punto inicial sugerido por el relevamiento (Ma Barber).
HORAS_CANCELACION_POR_DEFECTO = 2

# Mismo criterio que los triggers trg_turno_no_solapamiento_* de la base:
# estos estados NO ocupan el horario del barbero.
ESTADOS_QUE_LIBERAN_HORARIO = ('CANCELADO', 'AUSENTE')

# Estados desde los que el cliente puede cancelar o reprogramar.
ESTADOS_MODIFICABLES_POR_CLIENTE = ('PENDIENTE', 'CONFIRMADO')


def dia_semana_de(fecha):
    return DIAS_SEMANA[fecha.weekday()]


# ──────────────────────────────────────────
# Cancelación del cliente
# ──────────────────────────────────────────

def horas_cancelacion(barberia):
    # Lee barberia.horas_anticipacion_cancelacion. Mientras el campo no exista
    # en el modelo (o esté vacío) se usa el valor por defecto.
    horas = getattr(barberia, 'horas_anticipacion_cancelacion', None)
    if horas is None or isinstance(horas, bool) or horas < 0:
        return HORAS_CANCELACION_POR_DEFECTO
    return horas


def inicio_del_turno(turno):
    return datetime.combine(turno.fecha, turno.hora_inicio)


# Hora límite para cancelar este turno: inicio - horas de la barbería.
# Se calcula turno por turno porque cada uno empieza a una hora distinta.
def fecha_limite_cancelacion(turno):
    barberia = turno.id_barbero.id_barberia
    return inicio_del_turno(turno) - timedelta(hours=horas_cancelacion(barberia))


def puede_cancelar(turno, ahora=None):
    ahora = ahora or datetime.now()
    if turno.estado not in ESTADOS_MODIFICABLES_POR_CLIENTE:
        return False
    return ahora <= fecha_limite_cancelacion(turno)


def mensaje_fuera_de_plazo(turno):
    horas = horas_cancelacion(turno.id_barbero.id_barberia)
    return (
        'Ya no se puede cancelar online; el plazo de cancelación de esta '
        f'barbería venció (hasta {horas} h antes del turno).'
    )


# ──────────────────────────────────────────
# Validación de la franja pedida
# ──────────────────────────────────────────

def calcular_hora_fin(fecha, hora_inicio, duracion_minutos):
    # Devuelve la hora de fin, o None si el turno cruzaría la medianoche.
    inicio_dt = datetime.combine(fecha, hora_inicio)
    fin_dt = inicio_dt + timedelta(minutes=duracion_minutos)
    if fin_dt.date() != fecha:
        return None
    return fin_dt.time()


# Reglas que no dependen del barbero: servicio activo, fecha futura y dentro
# del máximo de anticipación, y que el turno termine el mismo día.
# Devuelve (hora_fin, None) o (None, (mensaje, status)).
def validar_reglas_generales(servicio, fecha, hora_inicio, ahora=None):
    ahora = ahora or datetime.now()

    if servicio.estado != 1:
        return None, ('Ese servicio no está disponible.', 400)

    if servicio.id_barberia.estado != 'ACTIVA':
        return None, ('Esa barbería no está disponible.', 400)

    if datetime.combine(fecha, hora_inicio) <= ahora:
        return None, ('No se puede reservar en una fecha u hora pasada.', 400)

    if fecha > ahora.date() + timedelta(days=MAX_DIAS_ANTICIPACION_RESERVA):
        return None, (
            f'Solo se puede reservar con hasta {MAX_DIAS_ANTICIPACION_RESERVA} días de anticipación.', 400
        )

    hora_fin = calcular_hora_fin(fecha, hora_inicio, servicio.duracion_minutos)
    if hora_fin is None:
        return None, ('El turno no puede terminar después de la medianoche.', 400)

    return hora_fin, None


def barbero_activo(barbero):
    return barbero.id_usuario.estado != 'INACTIVO'


# El turno completo (inicio + duración) tiene que entrar en UN bloque de
# disponibilidad del barbero para ese día de la semana.
def barbero_atiende(id_barbero, fecha, hora_inicio, hora_fin):
    return Disponibilidad.objects.filter(
        id_barbero=id_barbero,
        dia_semana=dia_semana_de(fecha),
        hora_inicio__lte=hora_inicio,
        hora_fin__gte=hora_fin,
    ).exists()


# Reglas que dependen del barbero elegido. Devuelve None si está todo bien
# o (mensaje, status).
def validar_barbero_para_servicio(barbero, servicio, fecha, hora_inicio, hora_fin):
    if barbero.id_barberia_id != servicio.id_barberia_id:
        return ('El barbero no pertenece a la barbería de ese servicio.', 400)

    if not barbero_activo(barbero):
        return ('Ese barbero no está disponible.', 400)

    if not barbero_atiende(barbero.id_barbero, fecha, hora_inicio, hora_fin):
        return ('El barbero no atiende en ese horario.', 400)

    return None


# ──────────────────────────────────────────
# Concurrencia
# ──────────────────────────────────────────

# Bloqueo estable por barbero: se toma el lock de la fila del barbero (que
# siempre existe) dentro de la transacción. Un select_for_update sobre los
# turnos solos no alcanza: si todavía no hay turnos en esa franja no bloquea
# nada y dos pedidos simultáneos pasan los dos. Se piden siempre en orden de
# id para que dos reprogramaciones cruzadas no se bloqueen entre sí.
# Tiene que llamarse DENTRO de transaction.atomic().
def bloquear_barberos(ids_barberos):
    ids = sorted(set(ids_barberos))
    list(Barbero.objects.select_for_update().filter(id_barbero__in=ids).order_by('id_barbero'))


# Con el barbero bloqueado, se vuelve a consultar si el horario está ocupado.
# El select_for_update fuerza a leer lo último confirmado (no la foto vieja
# de la transacción), así se ve el turno que otro pedido acaba de guardar.
def hay_solapamiento(id_barbero, fecha, hora_inicio, hora_fin, excluir_turno=None):
    qs = Turno.objects.select_for_update().filter(
        id_barbero=id_barbero,
        fecha=fecha,
        hora_inicio__lt=hora_fin,
        hora_fin__gt=hora_inicio,
    ).exclude(estado__in=ESTADOS_QUE_LIBERAN_HORARIO)
    if excluir_turno:
        qs = qs.exclude(id_turno=excluir_turno)
    return qs.exists()


# Los triggers de la base son la última barrera: si saltan, se traducen a 409.
def es_error_de_solapamiento(error):
    return bool(error.args) and error.args[0] == 1644


# Deadlock (1213) o espera de lock agotada (1205): pasa si dos pedidos se
# cruzan justo; el cliente puede simplemente reintentar.
def es_error_de_concurrencia(error):
    return bool(error.args) and error.args[0] in (1213, 1205)
