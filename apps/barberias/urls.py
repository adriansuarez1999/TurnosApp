from django.urls import path
from . import views

urlpatterns = [
    # ══════════════════════════════════════════
    # Público (Sprint 2)
    # ══════════════════════════════════════════
    path('barberias/', views.listar_barberias),
    path('barberias/<int:id>/', views.detalle_barberia),
    path('barberos/', views.listar_barberos),

    # ══════════════════════════════════════════
    # Panel del dueño — Tareas 1 a 4 (Sprint 3)
    # ══════════════════════════════════════════
    path('barberias/nueva/', views.crear_barberia),
    path('mi-barberia/', views.mi_barberia),
    path('mi-barberia/barberos/', views.mis_barberos),
    path('mi-barberia/barberos/<int:id>/', views.mi_barbero_detalle),

    # ══════════════════════════════════════════
    # Panel del dueño — Tareas 6 y 7 (Sprint 3)
    # ══════════════════════════════════════════
    path('mi-barberia/informes/', views.informes),
    path('mi-barberia/logo/', views.subir_logo_barberia),
    path('mi-barberia/portada/', views.subir_foto_portada),
    path('mi-barberia/barberos/<int:id>/foto/', views.subir_foto_barbero),
    path('mi-barberia/fotos/', views.mis_fotos_barberia),
    path('mi-barberia/fotos/<int:id>/', views.mi_foto_detalle),

    # ══════════════════════════════════════════
    # Sprint 4 - Módulo A: Disponibilidad de barberos (Facundo)
    # ══════════════════════════════════════════
    path('mi-barberia/barberos/<int:id>/disponibilidad/', views.disponibilidad_barbero),
    path('mi-barberia/disponibilidad/<int:id>/', views.mi_disponibilidad_detalle),

    # ══════════════════════════════════════════
    # Sprint 4 - Módulo B: Bloqueo de clientes ausentes (Gonzalo)
    # ══════════════════════════════════════════
    path('mi-barberia/clientes/', views.mis_clientes),
    path('mi-barberia/clientes/<int:id>/bloquear/', views.bloquear_cliente),
    path('mi-barberia/clientes/<int:id>/desbloquear/', views.desbloquear_cliente),
]