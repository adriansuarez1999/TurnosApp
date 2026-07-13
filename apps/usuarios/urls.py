from django.urls import path
from . import views

urlpatterns = [
    # Autenticacion
    path('login/', views.login),
    path('registro/', views.registro),

    # Servicios
    path('servicios/', views.servicios),
    path('servicios/<int:id>/', views.servicio_detalle),

    # Turnos
    path('turnos/', views.crear_turno),
    path('turnos/disponibles/', views.turnos_disponibles),
    path('turnos/<int:id>/cancelar/', views.cancelar_turno),
    path('mis-turnos/', views.mis_turnos),
]