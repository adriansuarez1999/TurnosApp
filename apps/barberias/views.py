from django.shortcuts import render
from usuarios.models import Barberia

# ══════════════════════════════════════════
# Agregar barbería
# ══════════════════════════════════════════

def agregar_barberia(request):
    if request.method == 'POST':
        Barberia.objects.create(
            nombre=request.POST.get('nombre'),
            direccion=request.POST.get('direccion'),
            telefono=request.POST.get('telefono')
        )
        # Aquí deberías crear un objeto Barberia y guardarlo en la base de datos
        # Barberia.objects.create(nombre=nombre, direccion=direccion, telefono=telefono)

        return render(request, 'barberias/agregar_barberia.html', {'mensaje': 'Barbería agregada exitosamente'})

    return render(request, 'barberias/agregar_barberia.html')