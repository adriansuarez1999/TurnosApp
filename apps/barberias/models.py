from django.db import models


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

class FotoBarberia(models.Model):
    id_foto = models.AutoField(primary_key=True)
    id_barberia = models.ForeignKey(Barberia, models.CASCADE, db_column='id_barberia', related_name='fotos')
    url = models.CharField(max_length=255)
    orden = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        managed = False
        db_table = 'foto_barberia'
        ordering = ['orden']