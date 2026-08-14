from django.urls import path
from . import views

urlpatterns = [
    # Público (Sprint 2) — sin cambios
    path('barberias/', views.listar_barberias),
    path('barberias/<int:id>/', views.detalle_barberia),
    path('barberos/', views.listar_barberos),

    # Panel del dueño (Tareas 5 a 8)
    path('panel/informes/', views.informes),
    path('panel/barberia/logo/', views.subir_logo_barberia),
    path('panel/barberia/portada/', views.subir_foto_portada),
    path('panel/barberos/<int:id>/foto/', views.subir_foto_barbero),
]