from django.db import models


# Create your models here.
class Barberia(models.Model):
    id_barberia = models.AutoField(primary_key=True)
    id_dueno = models.ForeignKey('usuarios.Usuario', models.DO_NOTHING, db_column='id_dueno')
    nombre = models.CharField(max_length=150)
    direccion = models.CharField(max_length=200)
    zona = models.CharField(max_length=100)
    descripcion = models.TextField(blank=True, null=True)
    logo = models.CharField(max_length=255, blank=True, null=True)
    telefono = models.CharField(max_length=20, blank=True, null=True)
    estado = models.CharField(max_length=8)

    class Meta:
        managed = False
        db_table = 'barberia'