from django.contrib import admin
from .models import Barberia, FotoBarberia


@admin.register(Barberia)
class BarberiaAdmin(admin.ModelAdmin):
    list_display = ('id_barberia', 'nombre', 'zona', 'estado')
    search_fields = ('nombre', 'zona')


@admin.register(FotoBarberia)
class FotoBarberiaAdmin(admin.ModelAdmin):
    list_display = ('id_foto', 'id_barberia', 'url', 'orden')
    list_filter = ('id_barberia',)