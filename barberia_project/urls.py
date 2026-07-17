from django.contrib import admin
from django.urls import path, include
from django.shortcuts import render
from apps.barberias.views import pagina_barberias


def home(request):
    return render(request, 'index.html')

def pagina_barberia(request):
    return render(request, 'paginas/barberia.html')

def pagina_reservar(request):
    return render(request, 'paginas/reservar.html')

def pagina_misturnos(request):
    return render(request, 'paginas/misturnos.html')


urlpatterns = [
    path('admin/', admin.site.urls),

    path('', home),
    path('barberias/', pagina_barberias),
    path('paginas/barberia.html', pagina_barberia),
    path('paginas/reservar.html', pagina_reservar),
    path('paginas/misturnos.html', pagina_misturnos),

    path('api/', include('apps.usuarios.urls')),
    path('api/', include('apps.turnos.urls')),
    path('api/', include('apps.barberias.urls')),
]