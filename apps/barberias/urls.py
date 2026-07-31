from django.urls import path
from . import views

urlpatterns = [
    path('barberias/', views.listar_barberias),
    path('barberias/<int:id>/', views.detalle_barberia),
    path('barberos/', views.listar_barberos),
]