# Contrato de API – Sprint 7 (Facundo, backend de reservas)

Todos los endpoints responden JSON. Errores: `{"ok": false, "error": "mensaje"}` con el status indicado.
Todos usan la sesión (`id_usuario`) y requieren el header `X-CSRFToken` como el resto de la app.

## 1. Reglas que ahora valida el backend al reservar / reprogramar

| Regla | Respuesta |
|---|---|
| Sin sesión | 401 |
| Cliente `BLOQUEADO` | 403 ("Tu cuenta está bloqueada…") |
| Cliente `INACTIVO` | 403 |
| Servicio inexistente / barbero inexistente | 404 |
| Servicio inactivo (`estado = 0`) o barbería `INACTIVA` | 400 |
| Barbero de otra barbería que el servicio | 400 ("El barbero no pertenece a la barbería de ese servicio.") |
| Barbero inactivo (`usuario.estado = INACTIVO`) | 400 |
| Fecha/hora pasada | 400 |
| Más de 60 días de anticipación | 400 (`MAX_DIAS_ANTICIPACION_RESERVA` en `reglas.py`) |
| El turno cruzaría la medianoche | 400 |
| El turno completo (inicio + duración) no entra en un bloque de disponibilidad del barbero | 400 ("El barbero no atiende en ese horario.") |
| Horario ocupado (cualquier solapamiento, incluso parcial) | **409** |
| Sin barberos libres (asignación automática) | 409 |
| Dos pedidos a la vez por la misma franja | uno 200, el resto 409 |

Los estados `CANCELADO` y `AUSENTE` liberan el horario (igual que los triggers de la base).

## 2. `POST /api/turnos/` – crear turno
Body: `{"id_servicio": 1, "fecha": "2026-11-10", "hora_inicio": "10:00", "id_barbero": 3}`
(`id_barbero` opcional → asignación automática entre los barberos activos de la barbería que atienden a esa hora).
200: `{ok, id_turno, id_barbero, hora_inicio, hora_fin, estado, monto_total}` (sin cambios respecto de antes).

## 3. `GET /api/turnos/disponibles/?fecha=YYYY-MM-DD&barbero=<id>` (o `&barberia=<id>`)
Parámetros **nuevos y opcionales**:
- `servicio=<id>`: el horario solo es válido si el servicio ENTERO entra (si no se manda, se asume 30 min como antes).
- `excluir_turno=<id>`: ignora ese turno. **Usar al reprogramar**, así el horario actual del propio turno aparece libre.

Respuesta: lista de `{"hora": "10:00", "disponible": true, "estado": "DISPONIBLE"}`.
`estado`: `DISPONIBLE` | `OCUPADO` (tomado por otro turno) | `NO_PERMITIDO` (ya pasó, fuera del máximo de anticipación o el servicio no entra en la disponibilidad).
`disponible` se mantiene (`true` solo con `DISPONIBLE`) para no romper el front actual.
Un horario `DISPONIBLE` es exactamente uno que `POST /api/turnos/` va a aceptar.

## 4. `PATCH /api/turnos/<id>/cancelar/` – cancelación del cliente
Sin body. Cambios:
- Solo desde `PENDIENTE` / `CONFIRMADO` (antes dejaba cancelar un turno FINALIZADO). Otro estado → 400.
- **Ventana de cancelación**: límite = `inicio del turno − horas_anticipacion_cancelacion` de la barbería. Si ya pasó → **400**:
  ```json
  {"ok": false,
   "error": "Ya no se puede cancelar online; el plazo de cancelación de esta barbería venció (hasta 2 h antes del turno).",
   "fecha_limite_cancelacion": "2026-11-10 08:00"}
  ```
- Método distinto de PATCH → 405 (antes devolvía 200).
- No afecta la cancelación del barbero (`/api/mi-agenda/turnos/<id>/cancelar/`), que sigue sin ventana.
- 200: `{ok, id_turno, estado: "CANCELADO"}`.

## 5. `PATCH /api/turnos/<id>/reprogramar/` – NUEVO
Body: `{"fecha": "2026-11-12", "hora_inicio": "15:30", "id_barbero": 4}` (`id_barbero` opcional; si no viene, se conserva el barbero).
200: `{"ok": true, "turno": {id_turno, id_barbero, fecha, hora_inicio, hora_fin, estado, monto_total}}`

Reglas: turno propio (403 si es ajeno), estado `PENDIENTE`/`CONFIRMADO`, cliente no bloqueado, nueva franja con las mismas validaciones que crear (sección 1),
y **respeta el mismo plazo que la cancelación** (si ya no puede cancelar, tampoco puede reprogramar; 400).
Mismo horario que el actual → 400. Franja ocupada → 409.
**Atómica**: si algo falla, el turno original queda exactamente como estaba. El monto no se recalcula (se mantiene el precio acordado al reservar).
Se crea una notificación interna `TURNO_REPROGRAMADO` para el barbero (y para el anterior si cambió de barbero).

Para armar la pantalla: pedir `/api/turnos/disponibles/?fecha=…&barbero=…&servicio=<id del servicio del turno>&excluir_turno=<id del turno>`.

## 6. Pendiente de Gonzalo (para cerrar el Módulo B)
1. **Campo de configuración**: `barberia.horas_anticipacion_cancelacion` (int, default 2, rango 0–168). Script en `database/Sprint7_migracion.sql`.
   `reglas.horas_cancelacion()` ya lo lee: mientras el campo no exista en el modelo, usa 2 horas.
2. **Elegibilidad en Mis turnos** (`views.mis_turnos`, función `serializar`). Agregar:
   ```python
   from . import reglas
   ...
   'puede_cancelar': reglas.puede_cancelar(turno),
   'fecha_limite_cancelacion': reglas.fecha_limite_cancelacion(turno).strftime('%Y-%m-%d %H:%M'),
   ```
   (conviene sumar `.select_related('id_barbero__id_barberia', 'id_barbero__id_usuario', 'id_servicio')` a las dos consultas de `mis_turnos`).
3. GET/PUT del dueño para la configuración (y alias / orden de llegada). Cuando cambien el valor, el límite de los turnos cambia solo.
4. Cola de llegada: para validar permisos usar `permisos.personal_de_barberia(request, id_barberia)` (ver `apps/turnos/permisos.py`).
   El número de orden se asigna con `select_for_update()` sobre la fila de la barbería + `max(numero_orden)+1` del día (hay UNIQUE como respaldo).
