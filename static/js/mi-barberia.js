/* ═══════════════════════════════════════════════════════════
   mi-barberia.js
   Panel del dueño — ver y editar los datos de su propia
   barbería (Sprint 3, Tarea 3). Consume GET/PUT /api/mi-barberia/
   directo, sin mock.
═══════════════════════════════════════════════════════════ */

const API_MI_BARBERIA = '/api/mi-barberia/';

const panelCargando = document.getElementById('panel-mi-barberia-cargando');
const panelForm     = document.getElementById('panel-mi-barberia');
const alerta        = document.getElementById('alerta-mi-barberia');

function mostrarAlertaBarberia(mensaje, tipo) {
  alerta.textContent = mensaje;
  alerta.className = 'modal__alerta ' + tipo;
}

(async function cargarMiBarberia() {
  try {
    const resp = await fetch(API_MI_BARBERIA);
    const datos = await resp.json();

    if (!datos.ok) {
      panelCargando.innerHTML = `<p class="listing__estado">${datos.error || 'No se pudo cargar tu barbería.'}</p>`;
      return;
    }

    document.getElementById('mb-nombre').value = datos.nombre || '';
    document.getElementById('mb-direccion').value = datos.direccion || '';
    document.getElementById('mb-zona').value = datos.zona || '';
    document.getElementById('mb-descripcion').value = datos.descripcion || '';
    mostrarPreviewLogo(datos.logo);

    panelCargando.style.display = 'none';
    panelForm.style.display = 'block';

  } catch (err) {
    console.error(err);
    panelCargando.innerHTML = '<p class="listing__estado">Ocurrió un error al cargar tu barbería.</p>';
  }
})();

document.getElementById('btn-mi-barberia-guardar').addEventListener('click', async () => {
  const btn = document.getElementById('btn-mi-barberia-guardar');

  const payload = {
    nombre: document.getElementById('mb-nombre').value.trim(),
    direccion: document.getElementById('mb-direccion').value.trim(),
    zona: document.getElementById('mb-zona').value.trim(),
    descripcion: document.getElementById('mb-descripcion').value.trim(),
  };

  if (!payload.nombre || !payload.direccion || !payload.zona) {
    mostrarAlertaBarberia('⚠️ Nombre, dirección y zona son obligatorios.', 'error');
    return;
  }

  btn.disabled = true;
  btn.textContent = 'Guardando...';
  alerta.className = 'modal__alerta';

  try {
    const resp = await fetch(API_MI_BARBERIA, {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': getCookie('csrftoken'),
      },
      body: JSON.stringify(payload),
    });
    const datos = await resp.json();

    if (datos.ok) {
      mostrarAlertaBarberia('✅ Cambios guardados.', 'exito');
    } else {
      mostrarAlertaBarberia('❌ ' + (datos.error || 'No se pudieron guardar los cambios.'), 'error');
    }
  } catch (err) {
    mostrarAlertaBarberia('⚠️ No se pudo conectar con el servidor.', 'error');
    console.error(err);
  } finally {
    btn.disabled = false;
    btn.textContent = 'Guardar cambios';
  }
});

function mostrarPreviewLogo(url) {
  const preview = document.getElementById('mb-logo-preview');
  preview.innerHTML = url ? `<img src="${url}" alt="Logo actual">` : '<span>Sin logo</span>';
}

document.getElementById('btn-mb-logo-subir').addEventListener('click', () => {
  document.getElementById('mb-logo-archivo').click();
});

document.getElementById('mb-logo-archivo').addEventListener('change', async (e) => {
  const archivo = e.target.files[0];
  if (!archivo) return;

  const btn = document.getElementById('btn-mb-logo-subir');
  btn.disabled = true;
  btn.textContent = 'Subiendo...';

  try {
    const datos = await subirArchivo(API_MI_BARBERIA + 'logo/', 'logo', archivo);

    if (datos.ok) {
      mostrarPreviewLogo(datos.logo);
      mostrarAlertaBarberia('✅ Logo actualizado.', 'exito');
    } else {
      mostrarAlertaBarberia('❌ ' + (datos.error || 'No se pudo subir el logo.'), 'error');
    }
  } catch (err) {
    mostrarAlertaBarberia('⚠️ No se pudo conectar con el servidor.', 'error');
    console.error(err);
  } finally {
    btn.disabled = false;
    btn.textContent = 'Cambiar logo';
    e.target.value = '';
  }
});