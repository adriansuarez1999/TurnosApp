/* ═══════════════════════════════════════════════════════════
   misturnos.js
   Vista "Mis Turnos" (historial de Lautaro), armada acá también
   para poder probar el flujo completo de punta a punta:
   reservar → ver en Mis Turnos → cancelar.

   - GET /mis-turnos/ (Facundo) → devuelve todos los turnos del
     cliente autenticado, ordenados próximos primero.
   - Mientras el endpoint no esté listo, usa TURNOS_MOCK_INICIALES
     guardados en sessionStorage (mock-data.js) — así los turnos
     reservados en reserva.js aparecen acá también.
   - Separa en "Próximos turnos" y "Turnos pasados".
   - Botón "Cancelar" solo en turnos con estado "confirmado".
   - Usa badgeEstadoHTML() de turnos-utils.js para el color.
═══════════════════════════════════════════════════════════ */

const MODO_SIMULADO_MISTURNOS = true;

const API_MISTURNOS = {
  listar:  '/api/mis-turnos/',
  cancelar: id => `/api/turnos/${id}/cancelar/`,
};

let turnoIdPendienteCancelar = null;

/* ── Obtener turnos ───────────────────────────────────────── */
async function obtenerMisTurnos() {
  const proximosCont = document.getElementById('lista-proximos');
  const pasadosCont  = document.getElementById('lista-pasados');
  proximosCont.innerHTML = '<li class="listing__estado">Cargando turnos...</li>';
  pasadosCont.innerHTML  = '';

  try {
    let turnos;

    if (MODO_SIMULADO_MISTURNOS) {
      await new Promise(r => setTimeout(r, 300));
      turnos = obtenerTurnosGuardados();
    } else {
      const resp = await fetch(API_MISTURNOS.listar);
      if (!resp.ok) throw new Error('No se pudieron obtener los turnos');
      turnos = await resp.json();
    }

    renderizarMisTurnos(turnos);

  } catch (err) {
    console.error('Error al obtener mis turnos:', err);
    proximosCont.innerHTML = '<li class="listing__estado">Ocurrió un error al cargar tus turnos.</li>';
  }
}

/* ── Separar próximos / pasados y renderizar ──────────────── */
function renderizarMisTurnos(turnos) {
  const hoy = new Date().toISOString().split('T')[0];

  const proximos = turnos
    .filter(t => t.fecha >= hoy)
    .sort((a, b) => (a.fecha + a.hora).localeCompare(b.fecha + b.hora));

  const pasados = turnos
    .filter(t => t.fecha < hoy)
    .sort((a, b) => (b.fecha + b.hora).localeCompare(a.fecha + a.hora));

  const proximosCont = document.getElementById('lista-proximos');
  const pasadosCont  = document.getElementById('lista-pasados');

  proximosCont.innerHTML = proximos.length
    ? proximos.map(t => turnoCardHTML(t, true)).join('')
    : '<li class="listing__estado">No tenés turnos próximos.</li>';

  pasadosCont.innerHTML = pasados.length
    ? pasados.map(t => turnoCardHTML(t, false)).join('')
    : '<li class="listing__estado">Todavía no tenés turnos pasados.</li>';

  // Conectar botones de cancelar recién creados
  document.querySelectorAll('.btn-cancelar-turno').forEach(btn => {
    btn.addEventListener('click', () => abrirModalCancelar(btn.dataset.id));
  });
}

function turnoCardHTML(turno, esProximo) {
  const fechaFormateada = new Date(turno.fecha + 'T00:00:00').toLocaleDateString('es-AR', {
    day: '2-digit', month: 'short', year: 'numeric',
  });

  const botonCancelar = (esProximo && turno.estado === 'confirmado')
    ? `<button class="btn-cancelar-turno" data-id="${turno.id}">Cancelar</button>`
    : '';

  return `
    <li class="turno-card d-flex align-items-center justify-content-between gap-3 flex-wrap">
      <div class="turno-card__info">
        <p class="turno-card__barberia">${turno.barberia}</p>
        <p class="turno-card__detalle">${turno.servicio} · ${turno.barbero}</p>
        <p class="turno-card__fecha">${fechaFormateada} — ${turno.hora} hs</p>
      </div>
      <div class="turno-card__estado d-flex align-items-center gap-2 flex-wrap">
        ${badgeEstadoHTML(turno.estado)}
        ${botonCancelar}
      </div>
    </li>
  `;
}

/* ── Cancelar turno (con modal de confirmación) ───────────── */
const modalCancelar = document.getElementById('modal-cancelar');

function abrirModalCancelar(id) {
  turnoIdPendienteCancelar = id;
  modalCancelar.classList.add('activo');
}

function cerrarModalCancelar() {
  turnoIdPendienteCancelar = null;
  modalCancelar.classList.remove('activo');
}

document.getElementById('cerrar-modal-cancelar').addEventListener('click', cerrarModalCancelar);
document.getElementById('btn-cancelar-no').addEventListener('click', cerrarModalCancelar);
modalCancelar.addEventListener('click', e => { if (e.target === modalCancelar) cerrarModalCancelar(); });

document.getElementById('btn-cancelar-si').addEventListener('click', async () => {
  const id = turnoIdPendienteCancelar;
  if (!id) return;

  const btn = document.getElementById('btn-cancelar-si');
  btn.disabled = true;
  btn.textContent = 'Cancelando...';

  try {
    if (MODO_SIMULADO_MISTURNOS) {
      await new Promise(r => setTimeout(r, 500));
      const lista = obtenerTurnosGuardados();
      const turno = lista.find(t => String(t.id) === String(id));
      if (turno) turno.estado = 'cancelado';
      guardarTurnos(lista);
    } else {
      const resp = await fetch(API_MISTURNOS.cancelar(id), {
        method: 'PATCH',
        headers: { 'X-CSRFToken': getCookie('csrftoken') },
      });
      if (!resp.ok) throw new Error('No se pudo cancelar el turno');
    }

    cerrarModalCancelar();
    await obtenerMisTurnos();

  } catch (err) {
    console.error(err);
    alert('⚠️ No se pudo cancelar el turno.');
  } finally {
    btn.disabled = false;
    btn.textContent = 'Sí, cancelar';
  }
});

obtenerMisTurnos();
