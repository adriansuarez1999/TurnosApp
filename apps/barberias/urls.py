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
]