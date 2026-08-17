/* ═══════════════════════════════════════════════════════════
   mis-servicios.js
   CRUD de Servicio en el panel del dueño (Sprint 3, Tarea 5).
   Consume /api/servicios/ real.
═══════════════════════════════════════════════════════════ */

const API_SERVICIOS = '/api/servicios/';

let serviciosActuales = [];

const alertaForm  = document.getElementById('alerta-form-servicio');
const inputIdEdit = document.getElementById('sv-id-editando');
const tituloForm  = document.getElementById('titulo-form-servicio');
const btnGuardar  = document.getElementById('btn-guardar-servicio');
const btnCancelar = document.getElementById('btn-cancelar-servicio');

function mostrarAlertaForm(mensaje, tipo) {
  alertaForm.textContent = mensaje;
  alertaForm.className = 'modal__alerta ' + tipo;
}

/* ── Cargar listado ──────────────────────────────────────── */
async function cargarServicios() {
  const lista = document.getElementById('lista-mis-servicios');

  try {
    const resp = await fetch(API_SERVICIOS);
    const datos = await resp.json();

    if (!datos.ok) {
      lista.innerHTML = `<li class="col-12 listing__estado">${datos.error || 'No se pudieron cargar los servicios.'}</li>`;
      return;
    }

    serviciosActuales = datos.servicios;

    lista.innerHTML = serviciosActuales.length
      ? serviciosActuales.map(s => `
          <li class="col">
            <div class="barbero-panel-card">
              <div style="display:flex; justify-content:space-between; align-items:center;">
                <span class="barbero-panel-card__nombre">${s.nombre}</span>
                <span style="color:var(--color-accent); font-weight:700;">$${Number(s.precio).toLocaleString('es-AR')}</span>
              </div>
              <span class="barbero-panel-card__dato">${s.duracion_minutos} min</span>
              ${s.estado ? '' : '<span class="badge-inactivo">Inactivo</span>'}
              ${s.descripcion ? `<span class="barbero-panel-card__dato">${s.descripcion}</span>` : ''}
              <div class="barbero-panel-card__acciones">
                <button class="btn-editar-barbero" data-id="${s.id_servicio}">Editar</button>
                <button class="btn-toggle-servicio" data-id="${s.id_servicio}" data-estado="${s.estado}">
                  ${s.estado ? 'Dar de baja' : 'Reactivar'}
                </button>
              </div>
            </div>
          </li>
        `).join('')
      : '<li class="col-12 listing__estado">Todavía no cargaste ningún servicio.</li>';

    lista.querySelectorAll('.btn-editar-barbero').forEach(btn => {
      btn.addEventListener('click', () => entrarModoEdicion(btn.dataset.id));
    });
    lista.querySelectorAll('.btn-toggle-servicio').forEach(btn => {
      btn.addEventListener('click', () => toggleEstadoServicio(btn.dataset.id, btn.dataset.estado));
    });

  } catch (err) {
    console.error(err);
    lista.innerHTML = '<li class="col-12 listing__estado">Ocurrió un error al cargar los servicios.</li>';
  }
}

/* ── Modo edición ─────────────────────────────────────────── */
function entrarModoEdicion(id) {
  const servicio = serviciosActuales.find(s => String(s.id_servicio) === String(id));
  if (!servicio) return;

  inputIdEdit.value = servicio.id_servicio;
  document.getElementById('sv-nombre').value = servicio.nombre;
  document.getElementById('sv-precio').value = servicio.precio;
  document.getElementById('sv-duracion').value = servicio.duracion_minutos;
  document.getElementById('sv-descripcion').value = servicio.descripcion || '';

  tituloForm.textContent = 'Editar servicio';
  btnGuardar.textContent = 'Guardar cambios';
  btnCancelar.style.display = 'block';

  window.scrollTo({ top: 0, behavior: 'smooth' });
}

function salirModoEdicion() {
  inputIdEdit.value = '';
  document.getElementById('sv-nombre').value = '';
  document.getElementById('sv-precio').value = '';
  document.getElementById('sv-duracion').value = '';
  document.getElementById('sv-descripcion').value = '';

  tituloForm.textContent = 'Agregar servicio';
  btnGuardar.textContent = 'Agregar servicio';
  btnCancelar.style.display = 'none';
  alertaForm.className = 'modal__alerta';
}

btnCancelar.addEventListener('click', (e) => {
  e.preventDefault();
  salirModoEdicion();
});

/* ── Guardar (alta o edición) ────────────────────────────── */
btnGuardar.addEventListener('click', async () => {
  const idEditando = inputIdEdit.value;
  const esEdicion = !!idEditando;

  const nombre      = document.getElementById('sv-nombre').value.trim();
  const precio       = document.getElementById('sv-precio').value;
  const duracion_minutos = document.getElementById('sv-duracion').value;
  const descripcion  = document.getElementById('sv-descripcion').value.trim();

  if (!nombre || !precio || !duracion_minutos) {
    mostrarAlertaForm('⚠️ Nombre, precio y duración son obligatorios.', 'error');
    return;
  }

  btnGuardar.disabled = true;
  btnGuardar.textContent = esEdicion ? 'Guardando...' : 'Agregando...';

  try {
    const url = esEdicion ? API_SERVICIOS + idEditando + '/' : API_SERVICIOS;
    const method = esEdicion ? 'PUT' : 'POST';

    const resp = await fetch(url, {
      method,
      headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': getCookie('csrftoken'),
      },
      body: JSON.stringify({ nombre, precio, duracion_minutos, descripcion }),
    });
    const datos = await resp.json();

    if (datos.ok) {
      mostrarAlertaForm(esEdicion ? '✅ Cambios guardados.' : '✅ Servicio agregado.', 'exito');
      salirModoEdicion();
      cargarServicios();
    } else {
      mostrarAlertaForm('❌ ' + (datos.error || 'No se pudo guardar.'), 'error');
    }
  } catch (err) {
    mostrarAlertaForm('⚠️ No se pudo conectar con el servidor.', 'error');
    console.error(err);
  } finally {
    btnGuardar.disabled = false;
    btnGuardar.textContent = esEdicion ? 'Guardar cambios' : 'Agregar servicio';
  }
});

async function toggleEstadoServicio(id, estadoActual) {
  const nuevoEstado = Number(estadoActual) ? 0 : 1;

  try {
    const resp = await fetch(API_SERVICIOS + id + '/', {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': getCookie('csrftoken'),
      },
      body: JSON.stringify({ estado: nuevoEstado }),
    });
    const datos = await resp.json();

    if (datos.ok) {
      cargarServicios();
    } else {
      alert('❌ ' + (datos.error || 'No se pudo cambiar el estado.'));
    }
  } catch (err) {
    alert('⚠️ No se pudo conectar con el servidor.');
    console.error(err);
  }
}

cargarServicios();