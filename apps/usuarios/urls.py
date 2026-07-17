from django.urls import include, path
from . import views

urlpatterns = [
    # Autenticacion
    path('login/', views.login),
    path('registro/', views.registro),

    # Servicios
    path('servicios/', views.servicios),
    path('servicios/<int:id>/', views.servicio_detalle),
]
