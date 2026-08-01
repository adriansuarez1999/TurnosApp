/* ═══════════════════════════════════════════════════════════
   registrar-barberia.js
   Alta de una barbería nueva (Sprint 3, Tarea 1).
   MODO_SIMULADO en true porque el endpoint de Facundo todavía
   no existe — apenas lo tenga, cambiamos el flag y probamos
   contra el real sin tocar el resto del archivo.
═══════════════════════════════════════════════════════════ */

const API_REGISTRAR_BARBERIA = '/api/barberias/registrar/';

// Modo simulado: true = sin backend (para desarrollo)
//                false = conecta con Django real
const MODO_SIMULADO_REGISTRAR_BARBERIA = true;

document.getElementById('btn-registrar-barberia-enviar').addEventListener('click', async () => {
  const nombre      = document.getElementById('rb-nombre').value.trim();
  const direccion   = document.getElementById('rb-direccion').value.trim();
  const zona        = document.getElementById('rb-zona').value.trim();
  const telefono    = document.getElementById('rb-telefono').value.trim();
  const descripcion = document.getElementById('rb-descripcion').value.trim();
  const btn         = document.getElementById('btn-registrar-barberia-enviar');
  const alerta      = document.getElementById('alerta-registrar-barberia');

  function mostrarAlerta(mensaje, tipo) {
    alerta.textContent = mensaje;
    alerta.className = 'modal__alerta ' + tipo;
  }

  if (!nombre || !direccion || !zona) {
    mostrarAlerta('⚠️ Completá nombre, dirección y zona.', 'error');
    return;
  }

  btn.disabled = true;
  btn.textContent = 'Registrando...';
  alerta.className = 'modal__alerta';

  try {
    let datos;

    if (MODO_SIMULADO_REGISTRAR_BARBERIA) {
      await new Promise(r => setTimeout(r, 800));
      datos = { ok: true, id: 99, nombre };
    } else {
      const resp = await fetch(API_REGISTRAR_BARBERIA, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-CSRFToken': getCookie('csrftoken'),
        },
        body: JSON.stringify({ nombre, direccion, zona, telefono, descripcion }),
      });
      datos = await resp.json();
    }

    if (datos.ok) {
      mostrarAlerta('✅ ¡Barbería registrada! Ya podés empezar a gestionarla.', 'exito');
      setTimeout(() => { window.location.href = '/'; }, 1500);
    } else {
      mostrarAlerta('❌ ' + (datos.error || 'No se pudo registrar la barbería.'), 'error');
    }
  } catch (err) {
    mostrarAlerta('⚠️ No se pudo conectar con el servidor.', 'error');
    console.error(err);
  } finally {
    btn.disabled = false;
    btn.textContent = 'Registrar barbería';
  }
});

/* Fijate que redirige a / al confirmar — como la Tarea 2 (que la sesión reconozca el rol de dueño) todavía no existe, 
por ahora no hay a dónde más mandarlo. Cuando Facundo tenga esa parte, cambiamos ese redirect por el link al panel.*/