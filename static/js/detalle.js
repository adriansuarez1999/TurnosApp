/* ═══════════════════════════════════════════════════════════
   detalle.js
   Sprint 2 — Tarea 2: Vista de detalle de barbería.

   - Toma el id desde la URL (?id=...)
   - GET /barberias/<id>/ → nombre, descripción, foto, servicios
   - GET /barberos/?barberia=<id> → lista de barberos (de Gonzalo)
   - Botón "Reservar turno" → paginas/reservar.html?id=<id>
═══════════════════════════════════════════════════════════ */

const MODO_SIMULADO_DETALLE = false;

const API_DETALLE = {
  barberia: id => `/api/barberias/${id}/`,
  barberos: id => `/api/barberos/?barberia=${id}`,
};

function obtenerIdDeURL() {
  const params = new URLSearchParams(window.location.search);
  return params.get('id');
}

async function cargarDetalleBarberia() {
  const id = obtenerIdDeURL();
  const cont = document.getElementById('detalle-contenido');

  if (!id) {
    cont.innerHTML = '<p class="listing__estado">No se especificó una barbería.</p>';
    return;
  }

  try {
    let barberia, barberos;

    if (MODO_SIMULADO_DETALLE) {
      await new Promise(r => setTimeout(r, 300));
      barberia = BARBERIAS_MOCK.find(b => String(b.id) === String(id));
      barberos = BARBEROS_MOCK.filter(b => String(b.barberia) === String(id));
    } else {
      const [respBarberia, respBarberos] = await Promise.all([
        fetch(API_DETALLE.barberia(id)),
        fetch(API_DETALLE.barberos(id)),
      ]);
      if (!respBarberia.ok) throw new Error('Barbería no encontrada');
      barberia = await respBarberia.json();
      barberos = respBarberos.ok ? await respBarberos.json() : [];
    }

    if (!barberia) {
      cont.innerHTML = '<p class="listing__estado">No se encontró la barbería solicitada.</p>';
      return;
    }

    renderizarDetalle(barberia, barberos);

  } catch (err) {
    console.error('Error al cargar el detalle:', err);
    cont.innerHTML = '<p class="listing__estado">Ocurrió un error al cargar la barbería.</p>';
  }
}

function renderizarDetalle(barberia, barberos) {
  // ── Hero ──
  document.getElementById('detalle-nombre').textContent = barberia.nombre;
  document.getElementById('detalle-zona').textContent = barberia.zona || '';
  document.getElementById('detalle-descripcion').textContent = barberia.descripcion || '';
  document.title = barberia.nombre + ' — BarberApp';

  const fotoWrap = document.getElementById('detalle-foto');
  fotoWrap.innerHTML = barberia.foto
    ? `<img src="${barberia.foto}" alt="Foto de ${barberia.nombre}">`
    : `<svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
         <path d="M6 3v12"/><path d="M18 9a3 3 0 1 0 0-6"/><path d="M6 21a3 3 0 1 0 0-6"/>
         <path d="M15 6l-9 9"/><path d="M18 15l-3-3"/>
       </svg>`;

  // ── Portada (fondo del hero) ──
  const portada = document.getElementById('detalle-portada');
  const fotos = barberia.fotos || [];

  if (fotos.length > 0) {
    portada.innerHTML = fotos.map((url, i) =>
      `<img src="${url}" alt="" class="${i === 0 ? 'activa' : ''}">`
    ).join('');

    if (fotos.length > 1) {
      const imgs = portada.querySelectorAll('img');
      let actual = 0;
      setInterval(() => {
        imgs[actual].classList.remove('activa');
        actual = (actual + 1) % imgs.length;
        imgs[actual].classList.add('activa');
      }, 5000);
    }
  }

// ── Servicios ──
const listaServicios = document.getElementById('lista-servicios');
const servicios = barberia.servicios || [];
listaServicios.innerHTML = servicios.length
  ? servicios.map(s => `
      <li class="servicio-card col">
        <span class="servicio-card__nombre">${s.nombre}</span>
        <span class="servicio-card__precio">$${s.precio.toLocaleString('es-AR')}</span>
      </li>
    `).join('')
  : '<li class="col-12 listing__estado">Esta barbería todavía no cargó servicios.</li>';

// ── Barberos ──
const listaBarberos = document.getElementById('lista-barberos');
listaBarberos.innerHTML = barberos.length
  ? barberos.map(b => `
      <li class="barbero-card col">
        <div class="barbero-card__foto">
          ${b.foto
            ? `<img src="${b.foto}" alt="Foto de ${b.nombre}">`
            : `<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                 <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/>
               </svg>`}
        </div>
        <p class="barbero-card__nombre">${b.nombre}</p>
      </li>
    `).join('')
  : '<li class="col-12 listing__estado">Todavía no hay barberos cargados.</li>';

  // ── Botón reservar ──
  document.getElementById('btn-reservar-turno').addEventListener('click', () => {
    window.location.href = 'reservar.html?id=' + barberia.id;
  });
}

cargarDetalleBarberia();
