from django.urls import path

from . import (
    views,
    views_barbero,
    views_calificacion,
    views_cobro,
    views_perfil,
    views_estadisticas,
    views_notificaciones,
)


urlpatterns = [

    # Turnos públicos / cliente
    path('turnos/', views.crear_turno),
    path('turnos/disponibles/', views.turnos_disponibles),
    path('turnos/<int:id>/cancelar/', views.cancelar_turno),
    path('mis-turnos/', views.mis_turnos),

    path('mi-barberia/clientes/', views.clientes_barberia),
    path('mi-barberia/clientes/<int:id>/bloquear/', views.bloquear_cliente),
    path('mi-barberia/clientes/<int:id>/desbloquear/', views.desbloquear_cliente),

    # Sprint 5 - Módulo C: calendario de turnos por barbero
    path('mi-barberia/barberos/<int:id>/turnos/', views.turnos_por_barbero),

    # Sprint 6 - Módulo B: agenda del barbero (el id sale de la sesión)
    path('mi-agenda/turnos/', views_barbero.mi_agenda_turnos),
    path('mi-agenda/turnos/<int:id>/finalizar/', views_barbero.finalizar_turno),
    path('mi-agenda/turnos/<int:id>/ausente/', views_barbero.ausente_turno),
    path('mi-agenda/turnos/<int:id>/cancelar/', views_barbero.cancelar_turno_barbero),
    path('mi-agenda/clientes/<int:id>/historial/', views_barbero.historial_cliente),

    # Sprint 6 - Módulo D: calificación del cliente
    path('turnos/<int:id>/calificar/', views_calificacion.calificar_turno),

    # Sprint 6 - Módulo B (Gonzalo): cobro al finalizar un turno
    path('mi-agenda/turnos/<int:id>/cobro/', views_cobro.registrar_cobro),

    # Sprint 6 - Módulo C (Gonzalo): disponibilidad y perfil propios
    path('mi-agenda/disponibilidad/', views_perfil.mi_disponibilidad),
    path('mi-agenda/disponibilidad/<int:id>/', views_perfil.mi_disponibilidad_detalle),
    path('mi-agenda/perfil/', views_perfil.mi_perfil),
    path('mi-agenda/perfil/foto/', views_perfil.mi_perfil_foto),
    path('mi-agenda/perfil/password/', views_perfil.mi_password),

    # Sprint 6 - Módulo D (Gonzalo): estadísticas y calificaciones propias
    path('mi-agenda/estadisticas/', views_estadisticas.mis_estadisticas),
    path('mi-agenda/calificaciones/', views_estadisticas.mis_calificaciones),

    # Sprint 6 - Módulo E (Gonzalo): notificaciones dentro de la app
    path('notificaciones/', views_notificaciones.mis_notificaciones),
    path('notificaciones/leidas/', views_notificaciones.marcar_todas_leidas),
    path('notificaciones/<int:id>/leida/', views_notificaciones.marcar_leida),
]