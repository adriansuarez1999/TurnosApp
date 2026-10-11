from django.urls import path
from . import views

urlpatterns = [
    # ═══════════════════════════════════════════════════════
    # AUTENTICACIÓN
    # ═══════════════════════════════════════════════════════
    path("login/", views.login),
    path("registro/", views.registro),
    path("logout/", views.logout),
    # ═══════════════════════════════════════════════════════
    # SERVICIOS
    # ═══════════════════════════════════════════════════════
    path("servicios/", views.servicios),
    path("servicios/<int:id>/", views.servicio_detalle),
    # ═══════════════════════════════════════════════════════
    # PROMOCIONES — SPRINT 5
    # ═══════════════════════════════════════════════════════
    path("promociones/", views.promociones),
    path("promociones/<int:id>/", views.promocion_detalle),
]
