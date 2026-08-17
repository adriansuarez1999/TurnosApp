from django.contrib import admin
from django.urls import path, include
from django.shortcuts import render
from django.views.decorators.csrf import ensure_csrf_cookie
from django.conf import settings
from django.conf.urls.static import static


@ensure_csrf_cookie
def home(request):
    return render(request, 'index.html')

def pagina_barberia(request):
    return render(request, 'paginas/barberia.html')

def pagina_reservar(request):
    return render(request, 'paginas/reservar.html')

def pagina_misturnos(request):
    return render(request, 'paginas/misturnos.html')

def pagina_registrar_barberia(request):
    return render(request, 'paginas/registrar-barberia.html')

def pagina_mi_barberia(request):
    return render(request, 'paginas/mi-barberia.html', {'seccion_activa': 'barberia'})

def pagina_mis_barberos(request):
    return render(request, 'paginas/mis-barberos.html', {'seccion_activa': 'barberos'})

def pagina_mis_fotos(request):
    return render(request, 'paginas/mis-fotos.html', {'seccion_activa': 'fotos'})

def pagina_mis_servicios(request):
    return render(request, 'paginas/mis-servicios.html', {'seccion_activa': 'servicios'})

def pagina_mis_informes(request):
    return render(request, 'paginas/mis-informes.html', {'seccion_activa': 'informes'})


urlpatterns = [
    path('admin/', admin.site.urls),

    path('', home, name='index'),
    path('paginas/barberia.html', pagina_barberia, name='barberia'),
    path('paginas/reservar.html', pagina_reservar, name='reservar'),
    path('paginas/misturnos.html', pagina_misturnos, name='misturnos'),
    path('paginas/registrar-barberia.html', pagina_registrar_barberia, name='registrar_barberia'),
    path('paginas/mi-barberia.html', pagina_mi_barberia, name='mi_barberia'),
    path('paginas/mis-barberos.html', pagina_mis_barberos, name='mis_barberos'),
    path('paginas/mis-fotos.html', pagina_mis_fotos, name='mis_fotos'),
    path('paginas/mis-servicios.html', pagina_mis_servicios, name='mis_servicios'),
    path('paginas/mis-informes.html', pagina_mis_informes, name='mis_informes'),

    path('api/', include('apps.usuarios.urls')),
    path('api/', include('apps.turnos.urls')),
    path('api/', include('apps.barberias.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)