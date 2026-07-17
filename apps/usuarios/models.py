from django.db import models


class Barbero(models.Model):
    id_barbero = models.AutoField(primary_key=True)
    id_usuario = models.OneToOneField('Usuario', models.DO_NOTHING, db_column='id_usuario')
    id_barberia = models.ForeignKey('barberias.Barberia', models.DO_NOTHING, db_column='id_barberia')
    especialidad = models.CharField(max_length=100, blank=True, null=True)
    promedio_calificacion = models.DecimalField(max_digits=3, decimal_places=2)

    class Meta:
        managed = False
        db_table = 'barbero'


class Calificacion(models.Model):
    id_calificacion = models.AutoField(primary_key=True)
    id_turno = models.OneToOneField('turnos.Turno', models.DO_NOTHING, db_column='id_turno')
    id_barbero = models.ForeignKey(Barbero, models.DO_NOTHING, db_column='id_barbero')
    id_cliente = models.ForeignKey('Usuario', models.DO_NOTHING, db_column='id_cliente')
    puntuacion = models.IntegerField()
    comentario = models.TextField(blank=True, null=True)
    fecha = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'calificacion'


class Disponibilidad(models.Model):
    id_disponibilidad = models.AutoField(primary_key=True)
    id_barbero = models.ForeignKey(Barbero, models.DO_NOTHING, db_column='id_barbero')
    dia_semana = models.CharField(max_length=3)
    hora_inicio = models.TimeField()
    hora_fin = models.TimeField()

    class Meta:
        managed = False
        db_table = 'disponibilidad'


class Notificacion(models.Model):
    id_notificacion = models.AutoField(primary_key=True)
    id_usuario = models.ForeignKey('Usuario', models.DO_NOTHING, db_column='id_usuario')
    tipo = models.CharField(max_length=50)
    mensaje = models.TextField()
    fecha_envio = models.DateTimeField()
    estado = models.CharField(max_length=9)

    class Meta:
        managed = False
        db_table = 'notificacion'


class Pago(models.Model):
    id_pago = models.AutoField(primary_key=True)
    id_turno = models.ForeignKey('turnos.Turno', models.DO_NOTHING, db_column='id_turno')
    fecha_pago = models.DateTimeField()
    monto = models.DecimalField(max_digits=10, decimal_places=2)
    metodo_pago = models.CharField(max_length=13)
    estado = models.CharField(max_length=9)
    tipo_pago = models.CharField(max_length=7)
    created_at = models.DateTimeField()
    updated_at = models.DateTimeField()
    created_by = models.ForeignKey('Usuario', models.DO_NOTHING, db_column='created_by', blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'pago'


class PlanSuscripcion(models.Model):
    id_plan = models.AutoField(primary_key=True)
    nombre = models.CharField(max_length=50)
    precio = models.DecimalField(max_digits=10, decimal_places=2)
    incluye_estadisticas = models.IntegerField()
    incluye_promociones = models.IntegerField()

    class Meta:
        managed = False
        db_table = 'plan_suscripcion'


class Promocion(models.Model):
    id_promocion = models.AutoField(primary_key=True)
    id_servicio = models.ForeignKey('Servicio', models.DO_NOTHING, db_column='id_servicio')
    nombre = models.CharField(max_length=100)
    porcentaje_descuento = models.DecimalField(max_digits=5, decimal_places=2)
    fecha_inicio = models.DateField()
    fecha_fin = models.DateField()
    activa = models.IntegerField()

    class Meta:
        managed = False
        db_table = 'promocion'


class Servicio(models.Model):
    id_servicio = models.AutoField(primary_key=True)
    id_barberia = models.ForeignKey('barberias.Barberia', models.DO_NOTHING, db_column='id_barberia')
    nombre = models.CharField(max_length=100)
    descripcion = models.TextField(blank=True, null=True)
    precio = models.DecimalField(max_digits=10, decimal_places=2)
    duracion_minutos = models.IntegerField()
    estado = models.IntegerField()

    class Meta:
        managed = False
        db_table = 'servicio'


class Suscripcion(models.Model):
    id_suscripcion = models.AutoField(primary_key=True)
    id_barberia = models.ForeignKey('barberias.Barberia', models.DO_NOTHING, db_column='id_barberia')
    id_plan = models.ForeignKey(PlanSuscripcion, models.DO_NOTHING, db_column='id_plan')
    fecha_inicio = models.DateField()
    fecha_fin = models.DateField()
    estado = models.CharField(max_length=7)
    created_at = models.DateTimeField()
    updated_at = models.DateTimeField()
    created_by = models.ForeignKey('Usuario', models.DO_NOTHING, db_column='created_by', blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'suscripcion'


class Usuario(models.Model):
    id_usuario = models.AutoField(primary_key=True)
    nombre = models.CharField(max_length=100)
    apellido = models.CharField(max_length=100)
    email = models.CharField(unique=True, max_length=150)
    telefono = models.CharField(max_length=20)
    password = models.CharField(max_length=255)
    rol = models.CharField(max_length=7)
    estado = models.CharField(max_length=9)
    fecha_registro = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'usuario'
