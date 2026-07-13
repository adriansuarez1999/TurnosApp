from django.urls import path
from . import views

urlpatterns = [
    path('turnos/', views.crear_turno),
]