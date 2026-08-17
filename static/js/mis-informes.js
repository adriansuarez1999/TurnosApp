/* ═══════════════════════════════════════════════════════════
   mis-informes.js
   Informes del panel del dueño (Sprint 3, Tarea 6).
   Consume GET /api/mi-barberia/informes/ real.
═══════════════════════════════════════════════════════════ */

const API_INFORMES = '/api/mi-barberia/informes/';

const contenido = document.getElementById('informes-contenido');

function formatearFecha(fechaStr) {
  const [anio, mes, dia] = fechaStr.split('-');
  return `${dia}/${mes}/${anio}`;
}

async function cargarInformes() {
  contenido.innerHTML = '<p class="listing__estado">Cargando...</p>';

  const desde = document.getElementById('inf-desde').value;
  const hasta = document.getElementById('inf-hasta').value;

  const params = new URLSearchParams();
  if (desde) params.set('desde', desde);
  if (hasta) params.set('hasta', hasta);

  try {
    const resp = await fetch(API_INFORMES + (params.toString() ? '?' + params.toString() : ''));
    const datos = await resp.json();

    if (!datos.ok) {
      contenido.innerHTML = `<p class="listing__estado">${datos.error || 'No se pudieron cargar los informes.'}</p>`;
      return;
    }

    renderizarInformes(datos);

  } catch (err) {
    console.error(err);
    contenido.innerHTML = '<p class="listing__estado">Ocurrió un error al cargar los informes.</p>';
  }
}

function renderizarInformes(datos) {
  const totalTurnos = datos.turnos_por_estado.reduce((acum, e) => acum + e.cantidad, 0);

  const filasPorDia = datos.turnos_por_dia.length
    ? datos.turnos_por_dia.map(d => `
        <tr>
          <td>${formatearFecha(d.fecha)}</td>
          <td>${d.cantidad}</td>
        </tr>
      `).join('')
    : `<tr><td colspan="2" class="listing__estado">Sin turnos en este período.</td></tr>`;

  const badgesPorEstado = datos.turnos_por_estado.length
    ? datos.turnos_por_estado.map(e => `
        <span class="badge-turno badge-turno--${e.estado.toLowerCase()}">${e.estado} · ${e.cantidad}</span>
      `).join('')
    : '<p class="listing__estado">Sin datos.</p>';

  contenido.innerHTML = `
    <div class="informes-stats">
      <div class="informe-stat">
        <div class="informe-stat__valor">$${Number(datos.ingresos_totales).toLocaleString('es-AR')}</div>
        <div class="informe-stat__label">Ingresos totales</div>
      </div>
      <div class="informe-stat">
        <div class="informe-stat__valor">${totalTurnos}</div>
        <div class="informe-stat__label">Turnos totales</div>
      </div>
    </div>

    <div class="panel-card" style="margin-bottom:1.5rem;">
      <h3 class="reserva__titulo" style="margin-bottom:1rem;">Turnos por estado</h3>
      <div class="informes-badges">${badgesPorEstado}</div>
    </div>

    <div class="panel-card">
      <h3 class="reserva__titulo" style="margin-bottom:1rem;">Turnos por día</h3>
      <table class="tabla-informe">
        <thead>
          <tr><th>Fecha</th><th>Cantidad</th></tr>
        </thead>
        <tbody>${filasPorDia}</tbody>
      </table>
    </div>
  `;
}

document.getElementById('btn-filtrar-informes').addEventListener('click', cargarInformes);

document.getElementById('btn-limpiar-filtro').addEventListener('click', (e) => {
  e.preventDefault();
  document.getElementById('inf-desde').value = '';
  document.getElementById('inf-hasta').value = '';
  cargarInformes();
});

cargarInformes();