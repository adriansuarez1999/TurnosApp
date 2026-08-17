from django.urls import path
from . import views

urlpatterns = [
    path('barberias/', views.listar_barberias),
    path('barberias/nueva/', views.crear_barberia),
    path('barberias/<int:id>/', views.detalle_barberia),
    path('barberos/', views.listar_barberos),

    # Panel del dueño
    path('mi-barberia/', views.mi_barberia),
    path('mi-barberia/barberos/', views.mis_barberos),
    path('mi-barberia/barberos/<int:id>/', views.mi_barbero_detalle),
    path('mi-barberia/fotos/', views.mis_fotos_barberia),
    path('mi-barberia/fotos/<int:id>/', views.mi_foto_detalle),

    # Tarea 6: informes
    path('mi-barberia/informes/', views.informes),

    # Tarea 7: carga real de archivos
    path('mi-barberia/logo/', views.subir_logo_barberia),
    path('mi-barberia/portada/', views.subir_foto_portada),
    path('mi-barberia/barberos/<int:id>/foto/', views.subir_foto_barbero),
]