from django.db.models import Count, Sum
from apps.usuarios.models import Pago

# ══════════════════════════════════════════
# Sprint 7 - Módulo E (Gonzalo): criterio ÚNICO de "ingreso confirmado".
# Lo usan los informes del dueño y las estadísticas del barbero, así los dos
# totales coinciden cuando se filtra la misma barbería y período.
#
# Un ingreso es un Pago TOTAL APROBADO (lo crea el barbero al registrar el cobro)
# de un turno FINALIZADO. Un turno cancelado, ausente o sin cobro registrado
# no suma, y un turno FINALIZADO sin cobro tampoco.
# ══════════════════════════════════════════


def pagos_confirmados():
    return Pago.objects.filter(
        tipo_pago='TOTAL',
        estado='APROBADO',
        id_turno__estado='FINALIZADO',
    )


# Devuelve (total_cobrado, cantidad_de_turnos_cobrados) del queryset de pagos dado.
# La cantidad cuenta turnos distintos, no filas de pago.
def resumen_cobros(pagos):
    datos = pagos.aggregate(total=Sum('monto'), cantidad=Count('id_turno', distinct=True))
    return datos['total'] or 0, datos['cantidad'] or 0
