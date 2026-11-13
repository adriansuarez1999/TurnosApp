import re
from django.db import connections
from django.test.runner import DiscoverRunner

# ══════════════════════════════════════════
# Sprint 7 - Facundo: runner de pruebas para el esquema SQL real
# Los modelos son managed=False, así que Django no crea las tablas en la base
# de pruebas. Este runner carga database/TurnosAppDB.sql en la base de prueba
# (con sus FOREIGN KEY, CHECK y triggers de solapamiento) y recién ahí corre los tests.
# Usa una base aparte (test_<DB_NAME>): nunca toca los datos reales.
# ══════════════════════════════════════════

RUTA_SQL = 'database/TurnosAppDB.sql'
RUTA_MIGRACION_SPRINT7 = 'database/Sprint7_migracion.sql'


def _sentencias_del_dump(ruta):
    # El dump usa DELIMITER (comando del cliente mysql, no SQL): se parte a mano.
    with open(ruta, encoding='utf-8') as f:
        lineas = f.read().splitlines()

    delimitador = ';'
    actual = []
    for linea in lineas:
        if linea.startswith('DELIMITER '):
            delimitador = linea.split()[1]
            continue
        if not actual and (not linea.strip() or linea.startswith('--')):
            continue
        # El dump crea/usa la base de producción: acá se usa la de prueba.
        if not actual and re.match(r'^(CREATE DATABASE|USE )', linea):
            continue
        actual.append(linea)
        if linea.rstrip().endswith(delimitador):
            sentencia = '\n'.join(actual).rstrip()[:-len(delimitador)]
            actual = []
            # El DEFINER apunta a root@localhost, que puede no existir en otra máquina.
            sentencia = re.sub(r'/\*!50017 DEFINER=`[^`]+`@`[^`]+`\*/', '', sentencia)
            # Collation propia de MySQL 8: se cambia para que también corra en MariaDB.
            sentencia = sentencia.replace('utf8mb4_0900_ai_ci', 'utf8mb4_unicode_ci')
            if sentencia.strip():
                yield sentencia


# TurnosAppDB.sql quedó atrasado respecto de los modelos: le faltan barbero.foto
# y la tabla foto_barberia (las usa el panel de fotos). Se agregan solo si faltan,
# para que las pruebas corran igual con un dump viejo o ya actualizado.
def _aplicar_parches_de_esquema(cursor):
    cursor.execute(
        "SELECT COUNT(*) FROM information_schema.columns "
        "WHERE table_schema = DATABASE() AND table_name = 'barbero' AND column_name = 'foto'"
    )
    if cursor.fetchone()[0] == 0:
        cursor.execute('ALTER TABLE barbero ADD COLUMN foto varchar(255) NULL')

    cursor.execute(
        'CREATE TABLE IF NOT EXISTS foto_barberia ('
        ' id_foto int NOT NULL AUTO_INCREMENT,'
        ' id_barberia int NOT NULL,'
        ' url varchar(255) NOT NULL,'
        ' orden int NOT NULL DEFAULT 0,'
        ' created_at datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,'
        ' PRIMARY KEY (id_foto),'
        ' CONSTRAINT fk_foto_barberia FOREIGN KEY (id_barberia) REFERENCES barberia (id_barberia) ON DELETE CASCADE'
        ')'
    )


# Sprint 7 (Gonzalo): el dump todavía no trae las columnas ni la tabla de la cola.
# Se aplica la migración solo si falta, así los tests también corren cuando
# TurnosAppDB.sql ya se re-exportó con los cambios incluidos.
def _aplicar_migracion_sprint7(cursor):
    cursor.execute(
        "SELECT COUNT(*) FROM information_schema.columns "
        "WHERE table_schema = DATABASE() AND table_name = 'barberia' "
        "AND column_name = 'orden_llegada_habilitado'"
    )
    if cursor.fetchone()[0] == 0:
        for sentencia in _sentencias_del_dump(RUTA_MIGRACION_SPRINT7):
            cursor.execute(sentencia)


class RunnerConEsquemaSQL(DiscoverRunner):
    def setup_databases(self, **kwargs):
        configuracion = super().setup_databases(**kwargs)
        conexion = connections['default']
        with conexion.cursor() as cursor:
            for sentencia in _sentencias_del_dump(RUTA_SQL):
                cursor.execute(sentencia)
            _aplicar_parches_de_esquema(cursor)
            _aplicar_migracion_sprint7(cursor)
        return configuracion
