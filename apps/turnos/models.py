from django.db import models

# Create your models here.
class Turno(models.Model):
    id_turno = models.AutoField(primary_key=True)
    id_cliente = models.ForeignKey('usuarios.Usuario', models.DO_NOTHING, db_column='id_cliente')
    id_barbero = models.ForeignKey('usuarios.Barbero', models.DO_NOTHING, db_column='id_barbero')
    id_servicio = models.ForeignKey('usuarios.Servicio', models.DO_NOTHING, db_column='id_servicio')
    fecha = models.DateField()
    hora_inicio = models.TimeField()
    hora_fin = models.TimeField()
    ESTADO_CHOICES = [
        ('PENDIENTE', 'Pendiente'),
        ('CONFIRMADO', 'Confirmado'),
        ('CANCELADO', 'Cancelado'),
        ('FINALIZADO', 'Finalizado'),
        ('AUSENTE', 'Ausente'),
        
    ]
    estado = models.CharField(max_length=10, choices=ESTADO_CHOICES)
    monto_total = models.DecimalField(max_digits=10, decimal_places=2)
    fecha_reserva = models.DateTimeField()
    created_at = models.DateTimeField()
    updated_at = models.DateTimeField()
    created_by = models.ForeignKey('usuarios.Usuario', models.DO_NOTHING, db_column='created_by', related_name='turno_created_by_set', blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'turno'