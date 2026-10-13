from django.urls import path

from . import views, views_barbero, views_calificacion


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
]
