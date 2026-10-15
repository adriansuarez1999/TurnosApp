from django.contrib import admin
from django.urls import path, include
from django.shortcuts import render
from django.views.decorators.csrf import ensure_csrf_cookie
from django.conf import settings
from django.conf.urls.static import static


@ensure_csrf_cookie
def home(request):
    return render(request, "index.html")


def pagina_barberia(request):
    return render(request, "paginas/barberia.html")


def pagina_reservar(request):
    return render(request, "paginas/reservar.html")


def pagina_misturnos(request):
    return render(request, "paginas/misturnos.html")


def pagina_registrar_barberia(request):
    return render(request, "paginas/registrar-barberia.html")


def pagina_mi_barberia(request):
    return render(
        request,
        "paginas/mi-barberia.html",
        {
            "seccion_activa": "barberia",
            "modo_panel": "admin",
        },
    )


def pagina_mis_barberos(request):
    return render(
        request,
        "paginas/mis-barberos.html",
        {
            "seccion_activa": "barberos",
            "modo_panel": "admin",
        },
    )


def pagina_disponibilidad(request):
    return render(
        request,
        "paginas/disponibilidad.html",
        {
            "seccion_activa": "disponibilidad",
            "modo_panel": "admin",
        },
    )


def pagina_turnos_barbero(request):
    return render(
        request,
        "paginas/turnos-barbero.html",
        {
            "seccion_activa": "turnos_barbero",
            "modo_panel": "admin",
        },
    )


def pagina_clientes(request):
    return render(
        request,
        "paginas/clientes.html",
        {
            "seccion_activa": "clientes",
            "modo_panel": "admin",
        },
    )


def pagina_mis_fotos(request):
    return render(
        request,
        "paginas/mis-fotos.html",
        {
            "seccion_activa": "fotos",
            "modo_panel": "admin",
        },
    )


def pagina_mis_servicios(request):
    return render(
        request,
        "paginas/mis-servicios.html",
        {
            "seccion_activa": "servicios",
            "modo_panel": "admin",
        },
    )


def pagina_mis_informes(request):
    return render(
        request,
        "paginas/mis-informes.html",
        {
            "seccion_activa": "informes",
            "modo_panel": "admin",
        },
    )


@ensure_csrf_cookie
def pagina_promociones(request):
    return render(
        request,
        "paginas/promociones.html",
        {
            "seccion_activa": "promociones",
            "modo_panel": "admin",
        },
    )


def pagina_mi_agenda(request):
    return render(
        request,
        "paginas/mi-agenda.html",
        {
            "seccion_activa": "agenda",
            "modo_panel": "agenda",
        },
    )


def pagina_mi_disponibilidad(request):
    return render(
        request,
        "paginas/mi-disponibilidad.html",
        {
            "seccion_activa": "mi_disponibilidad",
            "modo_panel": "agenda",
        },
    )


@ensure_csrf_cookie
def pagina_mi_perfil(request):
    return render(
        request,
        "paginas/mi-perfil.html",
        {
            "seccion_activa": "mi_perfil",
            "modo_panel": "agenda",
        },
    )


def pagina_mi_estadisticas(request):
    return render(
        request,
        "paginas/mi-estadisticas.html",
        {
            "seccion_activa": "mi_estadisticas",
            "modo_panel": "agenda",
        },
    )


def pagina_mis_calificaciones(request):
    return render(
        request,
        "paginas/mis-calificaciones.html",
        {
            "seccion_activa": "mis_calificaciones",
            "modo_panel": "agenda",
        },
    )


urlpatterns = [
    path("admin/", admin.site.urls),
    path("", home, name="index"),
    path(
        "paginas/barberia.html",
        pagina_barberia,
        name="barberia",
    ),
    path(
        "paginas/reservar.html",
        pagina_reservar,
        name="reservar",
    ),
    path(
        "paginas/misturnos.html",
        pagina_misturnos,
        name="misturnos",
    ),
    path(
        "paginas/registrar-barberia.html",
        pagina_registrar_barberia,
        name="registrar_barberia",
    ),
    path(
        "paginas/mi-barberia.html",
        pagina_mi_barberia,
        name="mi_barberia",
    ),
    path(
        "paginas/mis-barberos.html",
        pagina_mis_barberos,
        name="mis_barberos",
    ),
    path(
        "paginas/disponibilidad.html",
        pagina_disponibilidad,
        name="disponibilidad",
    ),
    path(
        "paginas/turnos-barbero.html",
        pagina_turnos_barbero,
        name="turnos_barbero",
    ),
    path(
        "paginas/clientes.html",
        pagina_clientes,
        name="clientes",
    ),
    path(
        "paginas/mis-fotos.html",
        pagina_mis_fotos,
        name="mis_fotos",
    ),
    path(
        "paginas/mis-servicios.html",
        pagina_mis_servicios,
        name="mis_servicios",
    ),
    path(
        "paginas/promociones.html",
        pagina_promociones,
        name="promociones",
    ),
    path(
        "paginas/mis-informes.html",
        pagina_mis_informes,
        name="mis_informes",
    ),
    path(
        "paginas/mi-agenda.html",
        pagina_mi_agenda,
        name="mi_agenda",
    ),
    path(
        "paginas/mi-disponibilidad.html",
        pagina_mi_disponibilidad,
        name="mi_disponibilidad",
    ),
    path(
        "paginas/mi-perfil.html",
        pagina_mi_perfil,
        name="mi_perfil",
    ),
    path(
        "paginas/mi-estadisticas.html",
        pagina_mi_estadisticas,
        name="mi_estadisticas",
    ),
    path(
        "paginas/mis-calificaciones.html",
        pagina_mis_calificaciones,
        name="mis_calificaciones",
    ),
    path("api/", include("apps.usuarios.urls")),
    path("api/", include("apps.turnos.urls")),
    path("api/", include("apps.barberias.urls")),
]


if settings.DEBUG:
    urlpatterns += static(
        settings.MEDIA_URL,
        document_root=settings.MEDIA_ROOT,
    )
