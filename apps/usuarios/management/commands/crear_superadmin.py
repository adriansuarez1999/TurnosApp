from datetime import datetime
from getpass import getpass
from django.contrib.auth.hashers import make_password
from django.core.management.base import BaseCommand, CommandError
from apps.usuarios.constants import PASSWORD_MIN_LARGO
from apps.usuarios.models import Usuario

# Crea el usuario superadministrador (rol ADMIN). Es la ÚNICA forma de obtener ese
# rol: ningún endpoint de la API permite crearlo ni asignarlo.
#
#   python manage.py crear_superadmin --email admin@barberapp.com
#
# La contraseña se pide por consola (no queda en el historial ni en el repositorio).
class Command(BaseCommand):
    help = 'Crea un usuario superadministrador (rol ADMIN).'

    def add_arguments(self, parser):
        parser.add_argument('--email', required=True)
        parser.add_argument('--nombre', default='Super')
        parser.add_argument('--apellido', default='Admin')

    def handle(self, *args, **opciones):
        email = opciones['email'].strip()
        if not email:
            raise CommandError('El email no puede estar vacío.')
        if Usuario.objects.filter(email=email).exists():
            raise CommandError('Ya existe un usuario con ese email.')

        password = getpass('Contraseña: ')
        if len(password) < PASSWORD_MIN_LARGO:
            raise CommandError(f'La contraseña tiene que tener al menos {PASSWORD_MIN_LARGO} caracteres.')
        if password != getpass('Repetí la contraseña: '):
            raise CommandError('Las contraseñas no coinciden.')

        Usuario.objects.create(
            nombre=opciones['nombre'],
            apellido=opciones['apellido'],
            email=email,
            telefono='',
            password=make_password(password),
            rol='ADMIN',
            estado='ACTIVO',
            fecha_registro=datetime.now(),
        )
        self.stdout.write(self.style.SUCCESS(f'Superadministrador creado: {email}'))
