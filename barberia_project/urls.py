from django.contrib import admin
from django.urls import path, include
from django.shortcuts import render
from django.views.decorators.csrf import ensure_csrf_cookie
from django.conf import settings
from django.conf.urls.static import static
from apps.barberias.views import pagina_barberias


@ensure_csrf_cookie
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

    path('', home, name='index'),
    path('barberias/', pagina_barberias, name='barberias'),
    path('paginas/barberia.html', pagina_barberia, name='barberia'),
    path('paginas/reservar.html', pagina_reservar, name='reservar'),
    path('paginas/misturnos.html', pagina_misturnos, name='misturnos'),

    path('api/', include('apps.usuarios.urls')),
    path('api/', include('apps.turnos.urls')),
    path('api/', include('apps.barberias.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)