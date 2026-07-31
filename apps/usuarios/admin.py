from django.contrib import admin
from .models import Usuario, Barbero, Servicio


@admin.register(Usuario)
class UsuarioAdmin(admin.ModelAdmin):
    list_display = ('id_usuario', 'nombre', 'apellido', 'email', 'rol', 'estado')
    search_fields = ('nombre', 'apellido', 'email')


@admin.register(Barbero)
class BarberoAdmin(admin.ModelAdmin):
    list_display = ('id_barbero', 'id_usuario', 'id_barberia', 'especialidad')


@admin.register(Servicio)
class ServicioAdmin(admin.ModelAdmin):
    list_display = ('id_servicio', 'nombre', 'id_barberia', 'precio', 'duracion_minutos', 'estado')