-- ============================================================================
-- BarberApp - Sprint 7 - Migración SQL (PROPUESTA a acordar con Gonzalo)
-- Facundo: revisión de compatibilidad del modelo (Módulo D, tarea "Compatibilidad").
--
-- Los modelos son managed=False y no se versionan migraciones de Django, así que
-- el cambio de esquema se hace con este script. Ejecutarlo UNA sola vez sobre
-- barberapp_db (MySQL 8) y después agregar los campos a los modelos Django:
--   apps/barberias/models.py -> Barberia (3 campos nuevos)
--   apps/usuarios/models.py  -> ColaAtencion (modelo nuevo, ver al final)
--
-- No toca la tabla `turno` ni sus triggers: la cola de llegada NO ocupa franjas
-- de turnos reservados (criterio de aceptación del Módulo D).
-- ============================================================================

USE `barberapp_db`;

-- ----------------------------------------------------------------------------
-- 1) Configuración por barbería (Módulos B, C y D - las usa Gonzalo)
-- ----------------------------------------------------------------------------
ALTER TABLE `barberia`
  -- Horas de anticipación mínima para que el CLIENTE pueda cancelar.
  -- Lo lee apps/turnos/reglas.py (horas_cancelacion). 2 = valor sugerido por Ma Barber.
  ADD COLUMN `horas_anticipacion_cancelacion` int NOT NULL DEFAULT 2,
  -- Alias de transferencia que se le muestra al cliente cuando el turno se finaliza.
  -- Es solo informativo: BarberApp no verifica ninguna transferencia.
  ADD COLUMN `alias_cobro` varchar(60) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  -- 1 = la barbería ofrece atención por orden de llegada además de los turnos.
  ADD COLUMN `orden_llegada_habilitado` tinyint(1) NOT NULL DEFAULT 0,
  ADD CONSTRAINT `chk_barberia_horas_cancelacion` CHECK (`horas_anticipacion_cancelacion` BETWEEN 0 AND 168);

-- ----------------------------------------------------------------------------
-- 2) Cola de atención por orden de llegada (Módulo D)
-- Una fila por persona que llega sin turno. Se numera por barbería y por día.
-- Estados mínimos: ESPERA -> ATENCION -> CERRADO  (o CANCELADO si se va antes).
-- ----------------------------------------------------------------------------
DROP TABLE IF EXISTS `cola_atencion`;
CREATE TABLE `cola_atencion` (
  `id_cola` int NOT NULL AUTO_INCREMENT,
  `id_barberia` int NOT NULL,
  `id_barbero` int DEFAULT NULL,                -- NULL hasta que se asigna a un barbero
  `id_cliente` int DEFAULT NULL,                -- cliente registrado (opcional)
  `nombre_cliente` varchar(100) COLLATE utf8mb4_unicode_ci DEFAULT NULL,   -- datos básicos si no tiene cuenta
  `telefono_cliente` varchar(20) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `id_servicio` int NOT NULL,
  `fecha` date NOT NULL,
  `numero_orden` int NOT NULL,                  -- 1, 2, 3... dentro de (barbería, fecha)
  `hora_llegada` datetime NOT NULL,
  `estado` enum('ESPERA','ATENCION','CERRADO','CANCELADO') COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT 'ESPERA',
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `created_by` int DEFAULT NULL,
  PRIMARY KEY (`id_cola`),
  -- Orden único por barbería y día: la base lo garantiza aunque dos personas se registren a la vez.
  UNIQUE KEY `uq_cola_orden` (`id_barberia`,`fecha`,`numero_orden`),
  KEY `idx_cola_barbero` (`id_barbero`),
  KEY `idx_cola_cliente` (`id_cliente`),
  KEY `fk_cola_servicio` (`id_servicio`),
  KEY `fk_cola_created_by` (`created_by`),
  CONSTRAINT `fk_cola_barberia` FOREIGN KEY (`id_barberia`) REFERENCES `barberia` (`id_barberia`) ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT `fk_cola_barbero` FOREIGN KEY (`id_barbero`) REFERENCES `barbero` (`id_barbero`) ON DELETE SET NULL ON UPDATE CASCADE,
  CONSTRAINT `fk_cola_cliente` FOREIGN KEY (`id_cliente`) REFERENCES `usuario` (`id_usuario`) ON DELETE SET NULL ON UPDATE CASCADE,
  CONSTRAINT `fk_cola_servicio` FOREIGN KEY (`id_servicio`) REFERENCES `servicio` (`id_servicio`) ON DELETE RESTRICT ON UPDATE CASCADE,
  CONSTRAINT `fk_cola_created_by` FOREIGN KEY (`created_by`) REFERENCES `usuario` (`id_usuario`) ON DELETE SET NULL ON UPDATE CASCADE,
  CONSTRAINT `chk_cola_orden` CHECK (`numero_orden` > 0)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ----------------------------------------------------------------------------
-- Modelos Django que acompañan al script (copiar a los models.py):
--
-- apps/barberias/models.py -> dentro de class Barberia:
--     horas_anticipacion_cancelacion = models.IntegerField(default=2)
--     alias_cobro = models.CharField(max_length=60, blank=True, null=True)
--     orden_llegada_habilitado = models.IntegerField(default=0)
--
-- apps/usuarios/models.py:
--     class ColaAtencion(models.Model):
--         id_cola = models.AutoField(primary_key=True)
--         id_barberia = models.ForeignKey('barberias.Barberia', models.DO_NOTHING, db_column='id_barberia')
--         id_barbero = models.ForeignKey(Barbero, models.DO_NOTHING, db_column='id_barbero', blank=True, null=True)
--         id_cliente = models.ForeignKey('Usuario', models.DO_NOTHING, db_column='id_cliente', blank=True, null=True, related_name='cola_cliente_set')
--         nombre_cliente = models.CharField(max_length=100, blank=True, null=True)
--         telefono_cliente = models.CharField(max_length=20, blank=True, null=True)
--         id_servicio = models.ForeignKey('Servicio', models.DO_NOTHING, db_column='id_servicio')
--         fecha = models.DateField()
--         numero_orden = models.IntegerField()
--         hora_llegada = models.DateTimeField()
--         estado = models.CharField(max_length=9)
--         created_at = models.DateTimeField()
--         updated_at = models.DateTimeField()
--         created_by = models.ForeignKey('Usuario', models.DO_NOTHING, db_column='created_by', blank=True, null=True, related_name='cola_created_by_set')
--         class Meta:
--             managed = False
--             db_table = 'cola_atencion'
--
-- Para asignar el número de orden sin repetir (Gonzalo): dentro de transaction.atomic(),
-- select_for_update() sobre la fila de la barbería y luego max(numero_orden) + 1 del día.
-- El UNIQUE KEY de arriba es la última barrera si dos pedidos igual se cruzan.
-- ----------------------------------------------------------------------------
