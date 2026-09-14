from django.urls import path

from . import views


urlpatterns = [

    # Turnos públicos / cliente
    path('turnos/', views.crear_turno),
    path('turnos/disponibles/', views.turnos_disponibles),
    path('turnos/<int:id>/cancelar/', views.cancelar_turno),
    path('mis-turnos/', views.mis_turnos),

    path('mi-barberia/clientes/', views.clientes_barberia),
    path('mi-barberia/clientes/<int:id>/bloquear/', views.bloquear_cliente),
    path('mi-barberia/clientes/<int:id>/desbloquear/', views.desbloquear_cliente),
]