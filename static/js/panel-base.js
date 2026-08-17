/* ═══════════════════════════════════════════════════════════
   panel-base.js
   Corre en las 3 páginas del panel — solo carga el nombre de
   la barbería en la sidebar, para personalizar el panel.
═══════════════════════════════════════════════════════════ */

(async function cargarNombreEnSidebar() {
  const el = document.getElementById('panel-sidebar-barberia');
  try {
    const resp = await fetch('/api/mi-barberia/');
    const datos = await resp.json();
    el.textContent = datos.ok ? datos.nombre : 'Mi barbería';
  } catch (err) {
    el.textContent = 'Mi barbería';
    console.error(err);
  }
})();