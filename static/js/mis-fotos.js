/* ═══════════════════════════════════════════════════════════
   mis-fotos.js
   Fotos de portada de la barbería propia (Sprint 3, Tarea 3).
   Consume /api/mi-barberia/fotos/ real, sin mock.
═══════════════════════════════════════════════════════════ */

const API_MI_BARBERIA = '/api/mi-barberia/';

const listaFotos  = document.getElementById('lista-fotos-barberia');
const alertaFotos = document.getElementById('alerta-fotos-barberia');

function mostrarAlertaFotos(mensaje, tipo) {
  alertaFotos.textContent = mensaje;
  alertaFotos.className = 'modal__alerta ' + tipo;
}

async function cargarFotos() {
  try {
    const resp = await fetch(API_MI_BARBERIA + 'fotos/');
    const datos = await resp.json();

    if (!datos.ok) {
      mostrarAlertaFotos('❌ ' + (datos.error || 'No se pudieron cargar las fotos.'), 'error');
      return;
    }

    renderizarFotos(datos.fotos);

  } catch (err) {
    console.error(err);
    mostrarAlertaFotos('⚠️ Ocurrió un error al cargar las fotos.', 'error');
  }
}

function renderizarFotos(fotos) {
  listaFotos.innerHTML = fotos.length
    ? fotos.map(f => `
        <li class="col">
          <div class="galeria-item">
            <img src="${f.url}" alt="Foto de portada">
            <button class="galeria-item__eliminar" data-id="${f.id}" aria-label="Eliminar foto">✕</button>
          </div>
        </li>
      `).join('')
    : '<li class="col-12 listing__estado">Todavía no cargaste fotos de portada.</li>';

  listaFotos.querySelectorAll('.galeria-item__eliminar').forEach(btn => {
    btn.addEventListener('click', () => eliminarFoto(btn.dataset.id));
  });
}

// ANTES: (todo el bloque desde "document.getElementById('btn-agregar-foto').addEventListener" hasta el "});" que lo cierra)

// DESPUÉS:
document.getElementById('btn-agregar-foto').addEventListener('click', () => {
  document.getElementById('nueva-foto-archivo').click();
});

document.getElementById('nueva-foto-archivo').addEventListener('change', async (e) => {
  const archivo = e.target.files[0];
  if (!archivo) return;

  const btn = document.getElementById('btn-agregar-foto');
  btn.disabled = true;
  btn.textContent = 'Subiendo...';

  try {
    const datos = await subirArchivo(API_MI_BARBERIA + 'portada/', 'foto', archivo);

    if (datos.ok) {
      mostrarAlertaFotos('✅ Foto agregada.', 'exito');
      cargarFotos();
    } else {
      mostrarAlertaFotos('❌ ' + (datos.error || 'No se pudo agregar la foto.'), 'error');
    }
  } catch (err) {
    mostrarAlertaFotos('⚠️ No se pudo conectar con el servidor.', 'error');
    console.error(err);
  } finally {
    btn.disabled = false;
    btn.textContent = 'Elegir foto';
    e.target.value = '';
  }
});

async function eliminarFoto(id) {
  if (!confirm('¿Eliminar esta foto?')) return;

  try {
    const resp = await fetch(API_MI_BARBERIA + `fotos/${id}/`, {
      method: 'DELETE',
      headers: { 'X-CSRFToken': getCookie('csrftoken') },
    });
    const datos = await resp.json();

    if (datos.ok) {
      cargarFotos();
    } else {
      mostrarAlertaFotos('❌ ' + (datos.error || 'No se pudo eliminar la foto.'), 'error');
    }
  } catch (err) {
    mostrarAlertaFotos('⚠️ No se pudo conectar con el servidor.', 'error');
    console.error(err);
  }
}

cargarFotos();