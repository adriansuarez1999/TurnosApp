from django.urls import path
from . import views, views_dueno_barbero, views_superadmin

urlpatterns = [
    path("barberias/", views.listar_barberias),
    path("barberias/nueva/", views.crear_barberia),
    path("barberias/<int:id>/", views.detalle_barberia),
    path("barberos/", views.listar_barberos),
    path("servicios/<int:id>/promocion/", views.promocion_servicio),
    # Panel del dueño
    path("mi-barberia/", views.mi_barberia),
    path("mi-barberia/barberos/", views.mis_barberos),
    path("mi-barberia/barberos/yo/", views_dueno_barbero.agregarme_como_barbero),
    path("mi-barberia/barberos/<int:id>/", views.mi_barbero_detalle),
    # Sprint 4 - Módulo A: disponibilidad de barberos
    path("mi-barberia/barberos/<int:id>/disponibilidad/", views.disponibilidad_barbero),
    path("mi-barberia/disponibilidad/<int:id>/", views.mi_disponibilidad_detalle),
    path("mi-barberia/fotos/", views.mis_fotos_barberia),
    path("mi-barberia/fotos/<int:id>/", views.mi_foto_detalle),
    # Tarea 6: informes
    path("mi-barberia/informes/", views.informes),
    # Tarea 7: carga real de archivos
    path("mi-barberia/logo/", views.subir_logo_barberia),
    path("mi-barberia/portada/", views.subir_foto_portada),
    path("mi-barberia/barberos/<int:id>/foto/", views.subir_foto_barbero),
    # Panel del superadministrador (rol ADMIN)
    path("superadmin/panel/", views_superadmin.panel),
    path("superadmin/login/", views_superadmin.login_admin),
    path("superadmin/logout/", views_superadmin.logout_admin),
    path("superadmin/resumen/", views_superadmin.resumen),
    path("superadmin/ingresos/", views_superadmin.ingresos),
    path("superadmin/barberias/", views_superadmin.barberias),
    path("superadmin/barberias/<int:id>/bloquear/", views_superadmin.bloquear_barberia),
    path("superadmin/barberias/<int:id>/desbloquear/", views_superadmin.desbloquear_barberia),
    path("superadmin/suscripciones/", views_superadmin.suscripciones),
]