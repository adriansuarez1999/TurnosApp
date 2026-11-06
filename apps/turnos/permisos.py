from django.http import JsonResponse
from apps.barberias.models import Barberia
from apps.usuarios.models import Barbero

# ══════════════════════════════════════════
# Sprint 7 - Módulo D (Facundo): permisos de la cola de atención por orden de llegada
# Helper para los endpoints de la cola que desarrolla Gonzalo. Resuelve a qué
# barbería puede operar el usuario logueado, SIEMPRE desde la sesión: el cliente
# nunca decide la barbería con un id que manda en el pedido sin que se verifique.
# ══════════════════════════════════════════

# Uso en un endpoint de la cola:
#
#     barberia, barbero, error = permisos.personal_de_barberia(request)
#     if error:
#         return error
#     # barberia: la Barberia sobre la que puede operar (dueño o barbero de ella)
#     # barbero:  su Barbero en esa barbería, o None si solo es dueño
#
# Si el pedido trae un id_barberia (por ejemplo en la URL), se pasa como segundo
# argumento y se rechaza con 403 si no es una barbería suya:
#
#     barberia, barbero, error = permisos.personal_de_barberia(request, id_barberia)
#
# Casos: dueño -> accede; barbero de esa barbería -> accede; dueño-barbero -> accede;
# cliente, barbero/dueño de OTRA barbería o sin sesión -> 401/403/404.
def personal_de_barberia(request, id_barberia=None):
    id_usuario = request.session.get('id_usuario')
    if not id_usuario:
        return None, None, JsonResponse({'ok': False, 'error': 'Tenés que iniciar sesión.'}, status=401)

    propias = list(Barberia.objects.filter(id_dueno=id_usuario))
    barbero = Barbero.objects.filter(id_usuario=id_usuario).select_related('id_barberia').first()

    if id_barberia is None:
        # Sin id: la propia (primero la de dueño, después en la que trabaja).
        if propias:
            barberia = propias[0]
        elif barbero:
            barberia = barbero.id_barberia
        else:
            return None, None, JsonResponse(
                {'ok': False, 'error': 'No tenés una barbería asociada.'}, status=404)
    else:
        barberia = next((b for b in propias if b.id_barberia == int(id_barberia)), None)
        if barberia is None and barbero and barbero.id_barberia_id == int(id_barberia):
            barberia = barbero.id_barberia
        if barberia is None:
            return None, None, JsonResponse(
                {'ok': False, 'error': 'No tenés permiso sobre esa barbería.'}, status=403)

    # El Barbero que se devuelve es el de ESTA barbería (puede ser dueño y barbero a la vez).
    if barbero and barbero.id_barberia_id != barberia.id_barberia:
        barbero = None

    if barberia.estado != 'ACTIVA':
        return None, None, JsonResponse({'ok': False, 'error': 'Esa barbería no está activa.'}, status=403)

    return barberia, barbero, None
