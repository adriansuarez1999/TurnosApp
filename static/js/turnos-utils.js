/* ═══════════════════════════════════════════════════════════
   turnos-utils.js
   Utilidad compartida para mostrar el ESTADO de un turno con
   un badge de color en cualquier vista (detalle, historial, etc).

   Estados soportados (los que devuelve el backend en /mis-turnos/
   y en /turnos/):
     - "confirmado" → verde
     - "cancelado"  → rojo
     - "pendiente"  → gris

   Uso:
     contenedor.innerHTML = badgeEstadoHTML(turno.estado);
═══════════════════════════════════════════════════════════ */

function badgeEstadoHTML(estado) {
  const normalizado = (estado || '').toLowerCase();

  const etiquetas = {
    confirmado: 'Confirmado',
    cancelado:  'Cancelado',
    pendiente:  'Pendiente',
  };

  // Si llega un estado que no reconocemos, lo tratamos como pendiente
  const clave = etiquetas[normalizado] ? normalizado : 'pendiente';

  return `<span class="badge-turno badge-turno--${clave}">${etiquetas[clave]}</span>`;
}

/* ── Helper: leer el token CSRF de la cookie ──────────────── */
function getCookie(nombre) {
  const match = document.cookie.match('(^|;)\\s*' + nombre + '\\s*=\\s*([^;]+)');
  return match ? match.pop() : '';
}