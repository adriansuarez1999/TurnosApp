/* ═══════════════════════════════════════════════════════════
   barberias.js
   Sprint 2 — Tarea 1: Conectar cards de barberías con datos reales.

   - Hace fetch a GET /barberias/ (endpoint de Gonzalo).
   - Mientras Gonzalo no entrega el endpoint, usa BARBERIAS_MOCK
     (array de mock-data.js) con 3 barberías de prueba.
   - Renderiza las cards en #listado-barberias.
   - Al hacer click en una card, navega a paginas/barberia.html?id=<id>
   - Incluye el buscador (filtra por nombre/servicio).
═══════════════════════════════════════════════════════════ */

// Cambiar a false cuando el endpoint de Gonzalo esté disponible.
const MODO_SIMULADO_BARBERIAS = true;

const API_BARBERIAS = {
  listar:  '/api/barberias/',
  buscar:  '/api/barberias/?search=',
};

let barberiasActuales = []; // guardamos la última lista traída, para el buscador

/* ── Obtener barberías (real o simulado) ─────────────────── */
async function obtenerBarberias() {
  const listado = document.getElementById('listado-barberias');
  listado.innerHTML = '<li class="col-12 listing__estado">Cargando barberías...</li>';

  try {
    let datos;

    if (MODO_SIMULADO_BARBERIAS) {
      await new Promise(r => setTimeout(r, 400)); // simula latencia de red
      datos = BARBERIAS_MOCK;
    } else {
      const respuesta = await fetch(API_BARBERIAS.listar);
      if (!respuesta.ok) throw new Error('Respuesta no OK: ' + respuesta.status);
      datos = await respuesta.json();
    }

    barberiasActuales = datos;
    renderizarBarberias(datos);

  } catch (err) {
    console.error('Error al obtener barberías:', err);
    // Si falla el fetch real, mostramos igual el mock para no dejar la página vacía
    barberiasActuales = BARBERIAS_MOCK;
    renderizarBarberias(BARBERIAS_MOCK);
  }
}

/* ── Renderizar cards ─────────────────────────────────────── */
function renderizarBarberias(barberias) {
  const listado = document.getElementById('listado-barberias');
  listado.innerHTML = '';

  if (!barberias || barberias.length === 0) {
    listado.innerHTML = '<li class="col-12 listing__estado">No hay barberías para mostrar.</li>';
    return;
  }

  barberias.forEach(barberia => {
    const li = document.createElement('li');
    li.className = 'col';
    li.innerHTML = `
      <div class="barber-card">
        <div class="barber-card__logo">
          ${barberia.foto
            ? `<img src="${barberia.foto}" alt="Foto de ${barberia.nombre}">`
            : `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                 <path d="M6 3v12"/>
                 <path d="M18 9a3 3 0 1 0 0-6"/>
                 <path d="M6 21a3 3 0 1 0 0-6"/>
                 <path d="M15 6l-9 9"/>
                 <path d="M18 15l-3-3"/>
               </svg>`}
        </div>
        <p class="barber-card__name">${barberia.nombre}</p>
        <button class="btn-card" data-id="${barberia.id}">Ver turnos</button>
      </div>
    `;
    listado.appendChild(li);
  });

  // Delegamos el click de "Ver turnos" en cada botón recién creado
  listado.querySelectorAll('.btn-card').forEach(btn => {
    btn.addEventListener('click', () => abrirBarberia(btn.dataset.id));
  });
}

/* ── Navegar al detalle ───────────────────────────────────── */
function abrirBarberia(id) {
  window.location.href = 'paginas/barberia.html?id=' + id;
}

/* ── Buscador (filtra sobre la última lista traída) ───────── */
function ejecutarBusqueda() {
  const texto = document.getElementById('search-input').value.trim().toLowerCase();

  if (!texto) {
    renderizarBarberias(barberiasActuales);
    return;
  }

  const filtradas = barberiasActuales.filter(b => {
    const enNombre = b.nombre.toLowerCase().includes(texto);
    const enServicios = (b.servicios || []).some(s => s.nombre.toLowerCase().includes(texto));
    return enNombre || enServicios;
  });

  renderizarBarberias(filtradas);

  if (filtradas.length === 0) {
    const listado = document.getElementById('listado-barberias');
    listado.innerHTML = `<li class="col-12 sin-resultados">No se encontraron barberías con "${texto}"</li>`;
  }

  // 🔌 Cuando el buscador de Gonzalo esté listo (CU-03), reemplazar lo de arriba por:
  // const respuesta = await fetch(API_BARBERIAS.buscar + encodeURIComponent(texto));
  // const datos = await respuesta.json();
  // renderizarBarberias(datos);
}

document.getElementById('btn-buscar').addEventListener('click', ejecutarBusqueda);
document.getElementById('search-input').addEventListener('keydown', e => {
  if (e.key === 'Enter') ejecutarBusqueda();
});
document.getElementById('search-input').addEventListener('input', e => {
  if (e.target.value === '') ejecutarBusqueda();
});

// Carga inicial
obtenerBarberias();
