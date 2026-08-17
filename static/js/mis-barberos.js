/* ═══════════════════════════════════════════════════════════
   mis-barberos.js
   CRUD de Barbero en el panel del dueño (Sprint 3, Tarea 4).
   Consume /api/mi-barberia/barberos/ real, sin mock.
═══════════════════════════════════════════════════════════ */

const API_MIS_BARBEROS = '/api/mi-barberia/barberos/';

let barberosActuales = [];

const alertaForm    = document.getElementById('alerta-form-barbero');
const inputIdEdit    = document.getElementById('bb-id-editando');
const grupoPassword  = document.getElementById('grupo-bb-password');
const tituloForm     = document.getElementById('titulo-form-barbero');
const btnGuardar     = document.getElementById('btn-guardar-barbero');
const btnCancelar    = document.getElementById('btn-cancelar-edicion');
const inputEmail     = document.getElementById('bb-email');

function mostrarAlertaForm(mensaje, tipo) {
  alertaForm.textContent = mensaje;
  alertaForm.className = 'modal__alerta ' + tipo;
}

/* ── Cargar listado ──────────────────────────────────────── */
async function cargarBarberos() {
  const lista = document.getElementById('lista-mis-barberos');

  try {
    const resp = await fetch(API_MIS_BARBEROS);
    const datos = await resp.json();

    if (!datos.ok) {
      lista.innerHTML = `<li class="col-12 listing__estado">${datos.error || 'No se pudieron cargar los barberos.'}</li>`;
      return;
    }

    barberosActuales = datos.barberos;

    lista.innerHTML = barberosActuales.length
      ? barberosActuales.map(b => `
          <li class="col">
            <div class="barbero-panel-card">
              <div style="display:flex; align-items:center; gap:0.75rem;">
                <div class="subir-archivo-preview" style="width:2.75rem; height:2.75rem; border-radius:50%; font-size:0.55rem;">
                  ${b.foto ? `<img src="${b.foto}" alt="Foto de ${b.nombre}">` : '<span>Sin foto</span>'}
                </div>
                <div>
                  <span class="barbero-panel-card__nombre">${b.nombre} ${b.apellido}</span>
                  ${b.estado === 'INACTIVO' ? '<span class="badge-inactivo">Inactivo</span>' : ''}
                </div>
              </div>
              <span class="barbero-panel-card__dato">${b.email}</span>
              <span class="barbero-panel-card__dato">${b.telefono || 'Sin teléfono'}</span>
              ${b.especialidad ? `<span class="barbero-panel-card__dato">Especialidad: ${b.especialidad}</span>` : ''}
              <input type="file" accept="image/*" class="input-foto-barbero" data-id="${b.id_barbero}" style="display:none;">
              <div class="barbero-panel-card__acciones">
                <button class="btn-editar-barbero" data-id="${b.id_barbero}">Editar</button>
                <button class="btn-editar-barbero btn-subir-foto-barbero" data-id="${b.id_barbero}">Foto</button>
                <button class="btn-toggle-servicio" data-id="${b.id_barbero}" data-estado="${b.estado}">
                  ${b.estado === 'INACTIVO' ? 'Reactivar' : 'Dar de baja'}
                </button>
              </div>
            </div>
          </li>
        `).join('')
      : '<li class="col-12 listing__estado">Todavía no agregaste ningún barbero.</li>';

    lista.querySelectorAll('.btn-editar-barbero').forEach(btn => {
      btn.addEventListener('click', () => entrarModoEdicion(btn.dataset.id));
    });
    lista.querySelectorAll('.btn-subir-foto-barbero').forEach(btn => {
      btn.addEventListener('click', () => {
        lista.querySelector(`.input-foto-barbero[data-id="${btn.dataset.id}"]`).click();
      });
    });
    lista.querySelectorAll('.input-foto-barbero').forEach(input => {
      input.addEventListener('change', (e) => subirFotoBarbero(input.dataset.id, e.target.files[0]));
    });
    lista.querySelectorAll('.btn-toggle-servicio').forEach(btn => {
      btn.addEventListener('click', () => toggleEstadoBarbero(btn.dataset.id, btn.dataset.estado));
    });

  } catch (err) {
    console.error(err);
    lista.innerHTML = '<li class="col-12 listing__estado">Ocurrió un error al cargar los barberos.</li>';
  }
}

/* ── Modo edición ─────────────────────────────────────────── */
function entrarModoEdicion(id) {
  const barbero = barberosActuales.find(b => String(b.id_barbero) === String(id));
  if (!barbero) return;

  inputIdEdit.value = barbero.id_barbero;
  document.getElementById('bb-nombre').value = barbero.nombre;
  document.getElementById('bb-apellido').value = barbero.apellido;
  inputEmail.value = barbero.email;
  inputEmail.disabled = true;
  document.getElementById('bb-telefono').value = barbero.telefono || '';
  document.getElementById('bb-especialidad').value = barbero.especialidad || '';

  grupoPassword.style.display = 'none';
  tituloForm.textContent = 'Editar barbero';
  btnGuardar.textContent = 'Guardar cambios';
  btnCancelar.style.display = 'block';

  window.scrollTo({ top: 0, behavior: 'smooth' });
}

function salirModoEdicion() {
  inputIdEdit.value = '';
  document.getElementById('bb-nombre').value = '';
  document.getElementById('bb-apellido').value = '';
  inputEmail.value = '';
  inputEmail.disabled = false;
  document.getElementById('bb-password').value = '';
  document.getElementById('bb-telefono').value = '';
  document.getElementById('bb-especialidad').value = '';

  grupoPassword.style.display = 'flex';
  tituloForm.textContent = 'Agregar barbero';
  btnGuardar.textContent = 'Agregar barbero';
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

  const nombre       = document.getElementById('bb-nombre').value.trim();
  const apellido      = document.getElementById('bb-apellido').value.trim();
  const email          = inputEmail.value.trim();
  const password       = document.getElementById('bb-password').value;
  const telefono       = document.getElementById('bb-telefono').value.trim();
  const especialidad   = document.getElementById('bb-especialidad').value.trim();

  if (!nombre || !apellido || !email || !telefono) {
    mostrarAlertaForm('⚠️ Nombre, apellido, email y teléfono son obligatorios.', 'error');
    return;
  }
  if (!esEdicion && !password) {
    mostrarAlertaForm('⚠️ La contraseña es obligatoria para un barbero nuevo.', 'error');
    return;
  }

  btnGuardar.disabled = true;
  btnGuardar.textContent = esEdicion ? 'Guardando...' : 'Agregando...';

  try {
    const url = esEdicion ? API_MIS_BARBEROS + idEditando + '/' : API_MIS_BARBEROS;
    const method = esEdicion ? 'PUT' : 'POST';

    const payload = esEdicion
      ? { nombre, apellido, telefono, especialidad }
      : { nombre, apellido, email, telefono, password, especialidad };

    const resp = await fetch(url, {
      method,
      headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': getCookie('csrftoken'),
      },
      body: JSON.stringify(payload),
    });
    const datos = await resp.json();

    if (datos.ok) {
      mostrarAlertaForm(esEdicion ? '✅ Cambios guardados.' : '✅ Barbero agregado.', 'exito');
      salirModoEdicion();
      cargarBarberos();
    } else {
      mostrarAlertaForm('❌ ' + (datos.error || 'No se pudo guardar.'), 'error');
    }
  } catch (err) {
    mostrarAlertaForm('⚠️ No se pudo conectar con el servidor.', 'error');
    console.error(err);
  } finally {
    btnGuardar.disabled = false;
    btnGuardar.textContent = esEdicion ? 'Guardar cambios' : 'Agregar barbero';
  }
});

async function subirFotoBarbero(id, archivo) {
  if (!archivo) return;

  try {
    const datos = await subirArchivo(API_MIS_BARBEROS + id + '/foto/', 'foto', archivo);

    if (datos.ok) {
      cargarBarberos();
    } else {
      alert('❌ ' + (datos.error || 'No se pudo subir la foto.'));
    }
  } catch (err) {
    alert('⚠️ No se pudo conectar con el servidor.');
    console.error(err);
  }
}

/* ── Activar / dar de baja ───────────────────────────────── */
async function toggleEstadoBarbero(id, estadoActual) {
  const nuevoEstado = estadoActual === 'INACTIVO' ? 'ACTIVO' : 'INACTIVO';

  try {
    const resp = await fetch(API_MIS_BARBEROS + id + '/', {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': getCookie('csrftoken'),
      },
      body: JSON.stringify({ estado: nuevoEstado }),
    });
    const datos = await resp.json();

    if (datos.ok) {
      cargarBarberos();
    } else {
      alert('❌ ' + (datos.error || 'No se pudo cambiar el estado.'));
    }
  } catch (err) {
    alert('⚠️ No se pudo conectar con el servidor.');
    console.error(err);
  }
}

cargarBarberos();