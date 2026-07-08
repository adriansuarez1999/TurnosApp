/* ═══════════════════════════════════════════════════════════
   reserva.js
   Sprint 2 — Tarea 3: Formulario de reserva paso a paso.

   Paso 1: elegir servicio (nombre y precio)
   Paso 2: elegir barbero, o "Cualquiera" para asignación automática
           → consume GET /barberos/ (Gonzalo)
   Paso 3: elegir fecha y horario
           → consume GET /turnos/disponibles/ (Facundo)
   Confirmar: POST /turnos/ (lo conecta Adrián). Acá ya queda
   armado el fetch real + fallback simulado para no bloquear
   el desarrollo mientras el endpoint no esté listo.
═══════════════════════════════════════════════════════════ */

const MODO_SIMULADO_RESERVA = true;

const API_RESERVA = {
  barberos:    id => `http://localhost:8000/api/barberos/?barberia=${id}`,
  disponibles: (barberoId, fecha) => `http://localhost:8000/api/turnos/disponibles/?barbero=${barberoId}&fecha=${fecha}`,
  crearTurno:  'http://localhost:8000/api/turnos/',
};

/* ── Estado del formulario ────────────────────────────────── */
const estadoReserva = {
  barberiaId: null,
  barberia: null,
  servicio: null,   // { id, nombre, precio }
  barbero: null,    // { id, nombre } o null si es "cualquiera"
  barberoLabel: 'Cualquiera disponible',
  fecha: null,
  horario: null,
};

function obtenerIdDeURL() {
  return new URLSearchParams(window.location.search).get('id');
}

/* ── Inicialización ───────────────────────────────────────── */
async function iniciarReserva() {
  const id = obtenerIdDeURL();
  estadoReserva.barberiaId = id;

  if (!id) {
    document.getElementById('reserva-contenido').innerHTML =
      '<p class="listing__estado">Falta indicar la barbería a reservar.</p>';
    return;
  }

  // Traemos la barbería (para sus servicios) — mismo mock que detalle.js
  estadoReserva.barberia = BARBERIAS_MOCK.find(b => String(b.id) === String(id)) || null;

  if (!estadoReserva.barberia) {
    document.getElementById('reserva-contenido').innerHTML =
      '<p class="listing__estado">No se encontró la barbería.</p>';
    return;
  }

  document.getElementById('reserva-nombre-barberia').textContent = estadoReserva.barberia.nombre;

  renderizarPasoServicio();
  await renderizarPasoBarbero();
  irAPaso(1);
}

/* ── Navegación entre pasos ───────────────────────────────── */
function irAPaso(numero) {
  document.querySelectorAll('.reserva__panel').forEach(p => p.classList.remove('activo'));
  document.getElementById('panel-paso-' + numero).classList.add('activo');

  document.querySelectorAll('.reserva__paso-indicador').forEach(ind => {
    const n = Number(ind.dataset.paso);
    ind.classList.toggle('activo', n === numero);
    ind.classList.toggle('completo', n < numero);
  });
}

/* ── PASO 1: Servicio ─────────────────────────────────────── */
function renderizarPasoServicio() {
  const cont = document.getElementById('lista-opciones-servicio');
  const servicios = estadoReserva.barberia.servicios || [];

  cont.innerHTML = servicios.map(s => `
    <div class="opcion-card" data-id="${s.id}">
      <span class="opcion-card__nombre">${s.nombre}</span>
      <span class="opcion-card__precio">$${s.precio.toLocaleString('es-AR')}</span>
    </div>
  `).join('');

  cont.querySelectorAll('.opcion-card').forEach(card => {
    card.addEventListener('click', () => {
      const servicio = servicios.find(s => String(s.id) === card.dataset.id);
      estadoReserva.servicio = servicio;

      cont.querySelectorAll('.opcion-card').forEach(c => c.classList.remove('seleccionada'));
      card.classList.add('seleccionada');

      document.getElementById('btn-paso1-siguiente').disabled = false;
    });
  });

  document.getElementById('btn-paso1-siguiente').addEventListener('click', () => irAPaso(2));
}

/* ── PASO 2: Barbero ──────────────────────────────────────── */
async function obtenerBarberos() {
  if (MODO_SIMULADO_RESERVA) {
    await new Promise(r => setTimeout(r, 250));
    return BARBEROS_MOCK.filter(b => String(b.barberia) === String(estadoReserva.barberiaId));
  }
  try {
    const resp = await fetch(API_RESERVA.barberos(estadoReserva.barberiaId));
    if (!resp.ok) throw new Error('No se pudo obtener barberos');
    return await resp.json();
  } catch (err) {
    console.error(err);
    return BARBEROS_MOCK.filter(b => String(b.barberia) === String(estadoReserva.barberiaId));
  }
}

async function renderizarPasoBarbero() {
  const cont = document.getElementById('lista-opciones-barbero');
  const barberos = await obtenerBarberos();

  const opcionCualquiera = `
    <div class="opcion-card opcion-cualquiera" data-id="cualquiera">
      <span class="opcion-card__nombre">✂️ Cualquiera disponible (asignación automática)</span>
    </div>
  `;

  const opcionesBarberos = barberos.map(b => `
    <div class="opcion-card" data-id="${b.id}">
      <span class="opcion-card__nombre">${b.nombre}</span>
    </div>
  `).join('');

  cont.innerHTML = opcionCualquiera + opcionesBarberos;

  cont.querySelectorAll('.opcion-card').forEach(card => {
    card.addEventListener('click', () => {
      cont.querySelectorAll('.opcion-card').forEach(c => c.classList.remove('seleccionada'));
      card.classList.add('seleccionada');

      if (card.dataset.id === 'cualquiera') {
        estadoReserva.barbero = null;
        estadoReserva.barberoLabel = 'Cualquiera disponible';
      } else {
        const barbero = barberos.find(b => String(b.id) === card.dataset.id);
        estadoReserva.barbero = barbero;
        estadoReserva.barberoLabel = barbero.nombre;
      }

      document.getElementById('btn-paso2-siguiente').disabled = false;
    });
  });

  document.getElementById('btn-paso2-atras').addEventListener('click', () => irAPaso(1));
  document.getElementById('btn-paso2-siguiente').addEventListener('click', () => irAPaso(3));
}

/* ── PASO 3: Fecha y horario ──────────────────────────────── */
async function obtenerHorariosDisponibles(fecha) {
  const barberoId = estadoReserva.barbero ? estadoReserva.barbero.id : 'cualquiera';

  if (MODO_SIMULADO_RESERVA) {
    await new Promise(r => setTimeout(r, 300));
    // Simulamos que algunos horarios ya están ocupados
    const ocupados = ['10:00', '14:30'];
    return HORARIOS_MOCK.map(h => ({ hora: h, disponible: !ocupados.includes(h) }));
  }

  try {
    const resp = await fetch(API_RESERVA.disponibles(barberoId, fecha));
    if (!resp.ok) throw new Error('No se pudieron obtener los horarios');
    return await resp.json();
  } catch (err) {
    console.error(err);
    return HORARIOS_MOCK.map(h => ({ hora: h, disponible: true }));
  }
}

const inputFecha = document.getElementById('input-fecha');
inputFecha.min = new Date().toISOString().split('T')[0];

inputFecha.addEventListener('change', async () => {
  estadoReserva.fecha = inputFecha.value;
  estadoReserva.horario = null;
  document.getElementById('btn-paso3-siguiente').disabled = true;

  const grid = document.getElementById('horarios-grid');
  grid.innerHTML = '<p class="listing__estado">Buscando horarios...</p>';

  const horarios = await obtenerHorariosDisponibles(estadoReserva.fecha);

  grid.innerHTML = horarios.map(h => `
    <button class="horario-btn" data-hora="${h.hora}" ${h.disponible ? '' : 'disabled'}>
      ${h.hora}
    </button>
  `).join('');

  grid.querySelectorAll('.horario-btn:not(:disabled)').forEach(btn => {
    btn.addEventListener('click', () => {
      grid.querySelectorAll('.horario-btn').forEach(b => b.classList.remove('seleccionado'));
      btn.classList.add('seleccionado');
      estadoReserva.horario = btn.dataset.hora;
      document.getElementById('btn-paso3-siguiente').disabled = false;
    });
  });
});

document.getElementById('btn-paso3-atras').addEventListener('click', () => irAPaso(2));
document.getElementById('btn-paso3-siguiente').addEventListener('click', () => {
  renderizarResumen();
  irAPaso(4);
});

/* ── PASO 4: Resumen y confirmación ───────────────────────── */
function renderizarResumen() {
  const cont = document.getElementById('reserva-resumen-datos');
  cont.innerHTML = `
    <div class="reserva__resumen-fila"><span>Barbería</span><span>${estadoReserva.barberia.nombre}</span></div>
    <div class="reserva__resumen-fila"><span>Servicio</span><span>${estadoReserva.servicio.nombre} — $${estadoReserva.servicio.precio.toLocaleString('es-AR')}</span></div>
    <div class="reserva__resumen-fila"><span>Barbero</span><span>${estadoReserva.barberoLabel}</span></div>
    <div class="reserva__resumen-fila"><span>Fecha</span><span>${estadoReserva.fecha}</span></div>
    <div class="reserva__resumen-fila"><span>Horario</span><span>${estadoReserva.horario}</span></div>
  `;
}

document.getElementById('btn-paso4-atras').addEventListener('click', () => irAPaso(3));

document.getElementById('btn-confirmar-reserva').addEventListener('click', async () => {
  const btn = document.getElementById('btn-confirmar-reserva');
  btn.disabled = true;
  btn.textContent = 'Confirmando...';

  const payload = {
    barberia: estadoReserva.barberiaId,
    servicio: estadoReserva.servicio.id,
    barbero: estadoReserva.barbero ? estadoReserva.barbero.id : null,
    fecha: estadoReserva.fecha,
    horario: estadoReserva.horario,
  };

  try {
    let datos;

    if (MODO_SIMULADO_RESERVA) {
      await new Promise(r => setTimeout(r, 700));
      datos = { ok: true, id: Math.floor(Math.random() * 1000), estado: 'pendiente' };

      // Guardamos el turno para que aparezca en Mis Turnos sin backend real
      agregarTurnoGuardado({
        id: datos.id,
        barberia: estadoReserva.barberia.nombre,
        barbero: estadoReserva.barberoLabel,
        servicio: estadoReserva.servicio.nombre,
        fecha: estadoReserva.fecha,
        hora: estadoReserva.horario,
        estado: datos.estado,
      });
    } else {
      // 🔌 Adrián: acá se conecta el POST real a /turnos/
      const resp = await fetch(API_RESERVA.crearTurno, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });
      datos = await resp.json();
    }

    if (datos.ok) {
      mostrarConfirmacionFinal(datos.estado || 'pendiente');
    } else {
      alert('❌ ' + (datos.error || 'No se pudo confirmar el turno.'));
      btn.disabled = false;
      btn.textContent = 'Confirmar reserva';
    }
  } catch (err) {
    console.error(err);
    alert('⚠️ No se pudo conectar con el servidor.');
    btn.disabled = false;
    btn.textContent = 'Confirmar reserva';
  }
});

function mostrarConfirmacionFinal(estado) {
  document.querySelectorAll('.reserva__panel').forEach(p => p.classList.remove('activo'));
  document.querySelectorAll('.reserva__paso-indicador').forEach(ind => ind.classList.add('completo'));

  const panel = document.getElementById('panel-confirmacion');
  panel.classList.add('activo');
  panel.innerHTML = `
    <div class="reserva__confirmacion">
      <div class="icono">✅</div>
      <h2 class="reserva__titulo">¡Turno reservado!</h2>
      <p style="margin-bottom:1rem; color: rgba(17,17,17,0.6);">Estado actual de tu turno:</p>
      ${badgeEstadoHTML(estado)}
      <div style="margin-top:2rem;">
        <a href="misturnos.html" class="btn-primario" style="display:inline-block; width:auto; padding:0.875rem 2rem;">Ver mis turnos</a>
      </div>
    </div>
  `;
}

iniciarReserva();
