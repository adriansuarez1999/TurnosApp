from django.db import models


class Usuario(models.Model):
    nombre = models.CharField(max_length=100)
    apellido = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    telefono = models.CharField(max_length=20, blank=True)
    password = models.CharField(max_length=255)

    class Meta:
        db_table = 'Cliente'

    def __str__(self):
        return self.email


class Barberia(models.Model):
    id_barberia = models.AutoField(primary_key=True)
    nombre = models.CharField(max_length=25)
    duenio = models.CharField(max_length=30)
    direccion = models.CharField(max_length=60)

    class Meta:
        db_table = 'Barberia'

    def __str__(self):
        return self.nombre


class Servicio(models.Model):
    id_servicio = models.AutoField(primary_key=True)
    nombre = models.CharField(max_length=45)
    precio = models.DecimalField(max_digits=10, decimal_places=2)
    descripcion = models.CharField(max_length=100, blank=True, null=True)

    class Meta:
        db_table = 'Servicio'

    def __str__(self):
        return self.nombre


class Profesionales(models.Model):
    id_profesional = models.AutoField(primary_key=True)
    nombre = models.CharField(max_length=45)
    apellido = models.CharField(max_length=45)
    edad = models.IntegerField(blank=True, null=True)
    red_social = models.CharField(max_length=45, blank=True, null=True)
    telefono = models.CharField(max_length=20, blank=True, null=True)
    id_barberia = models.ForeignKey(
        Barberia,
        on_delete=models.PROTECT,
        db_column='id_barberia'
    )

    class Meta:
        db_table = 'Profesionales'

    def __str__(self):
        return f'{self.nombre} {self.apellido}'


class Turno(models.Model):
    ESTADO_CHOICES = [
        ('libre', 'Libre'),
        ('reservado', 'Reservado'),
        ('terminado', 'Terminado'),
        ('cancelado', 'Cancelado'),
    ]

    id_turno = models.AutoField(primary_key=True)
    id_cliente = models.ForeignKey(
        Usuario,
        on_delete=models.PROTECT,
        db_column='id_cliente'
    )
    id_profesional = models.ForeignKey(
        Profesionales,
        on_delete=models.PROTECT,
        db_column='id_profesional'
    )
    fecha = models.DateField()
    hora_inicio = models.TimeField()
    hora_fin = models.TimeField()
    estado = models.CharField(max_length=10, choices=ESTADO_CHOICES, default='libre')
    monto_total = models.DecimalField(max_digits=10, decimal_places=2)
    creado_el = models.DateTimeField(auto_now_add=True)
    id_barberia = models.ForeignKey(
        Barberia,
        on_delete=models.PROTECT,
        db_column='id_barberia'
    )
    monto_propina = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    metodo_pago = models.CharField(max_length=20)
    id_servicio = models.ForeignKey(
        Servicio,
        on_delete=models.PROTECT,
        db_column='id_servicio'
    )

    class Meta:
        db_table = 'Turno'

    def __str__(self):
        return f'Turno {self.id_turno} - {self.fecha}'


class Calificaciones(models.Model):
    id_calificaciones = models.AutoField(primary_key=True)
    id_cliente = models.ForeignKey(
        Usuario,
        on_delete=models.PROTECT,
        db_column='id_cliente'
    )
    id_profesional = models.ForeignKey(
        Profesionales,
        on_delete=models.PROTECT,
        db_column='id_profesional'
    )
    descripcion = models.CharField(max_length=150, blank=True, null=True)
    fecha_hora = models.DateTimeField(auto_now_add=True)
    puntaje = models.PositiveSmallIntegerField()

    class Meta:
        db_table = 'Calificaciones'

    def __str__(self):
        return f'Calificacion {self.id_calificaciones} - puntaje {self.puntaje}'


class BarberiaServicio(models.Model):
    id_barberia_servicio = models.AutoField(primary_key=True)
    id_barberia = models.ForeignKey(
        Barberia,
        on_delete=models.PROTECT,
        db_column='id_barberia'
    )
    id_servicio = models.ForeignKey(
        Servicio,
        on_delete=models.PROTECT,
        db_column='id_servicio'
    )

    class Meta:
        db_table = 'Barberia_Servicio'

    def __str__(self):
        return f'Barberia {self.id_barberia_id} - Servicio {self.id_servicio_id}'
