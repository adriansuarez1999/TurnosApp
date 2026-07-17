/* ═══════════════════════════════════════════════════════════
   main.js
   Header, modales de Login/Registro y sesión.
   Se usa solo en index.html (es donde están los modales en el DOM).
═══════════════════════════════════════════════════════════ */

const API = {
  login:    '/api/login/',
  registro: '/api/registro/',
};

// Modo simulado: true = sin backend (para desarrollo)
//                false = conecta con Django real
const MODO_SIMULADO = false;

/* ── Referencias ─────────────────────────────────────────── */
const modalLogin    = document.getElementById('modal-login');
const modalRegistro  = document.getElementById('modal-registro');
const navAuth        = document.querySelector('.nav__auth');
const navLogueado    = document.getElementById('nav-logueado');
const navNombre      = document.getElementById('nav-nombre-usuario');

/* ── Abrir / cerrar modales ──────────────────────────────── */
function abrirModal(modal) {
  modal.classList.add('activo');
  document.body.style.overflow = 'hidden';
}
function cerrarModal(modal) {
  modal.classList.remove('activo');
  document.body.style.overflow = '';
  limpiarAlerta(modal);
}

[modalLogin, modalRegistro].forEach(m => {
  m.addEventListener('click', e => { if (e.target === m) cerrarModal(m); });
});
document.addEventListener('keydown', e => {
  if (e.key === 'Escape') {
    cerrarModal(modalLogin);
    cerrarModal(modalRegistro);
  }
});

document.getElementById('btn-acceder').addEventListener('click', () => abrirModal(modalLogin));
document.getElementById('btn-crear-cuenta').addEventListener('click', () => abrirModal(modalRegistro));
document.getElementById('cerrar-login').addEventListener('click', () => cerrarModal(modalLogin));
document.getElementById('cerrar-registro').addEventListener('click', () => cerrarModal(modalRegistro));

document.getElementById('ir-a-registro').addEventListener('click', () => {
  cerrarModal(modalLogin);
  abrirModal(modalRegistro);
});
document.getElementById('ir-a-login').addEventListener('click', () => {
  cerrarModal(modalRegistro);
  abrirModal(modalLogin);
});

/* ── Alertas dentro del modal ─────────────────────────────── */
function mostrarAlerta(modal, mensaje, tipo = 'error') {
  const alerta = modal.querySelector('.modal__alerta');
  alerta.textContent = mensaje;
  alerta.className = 'modal__alerta ' + tipo;
}
function limpiarAlerta(modal) {
  const alerta = modal.querySelector('.modal__alerta');
  alerta.textContent = '';
  alerta.className = 'modal__alerta';
}

/* ── Navbar logueado / sin sesión ─────────────────────────── */
function mostrarUsuarioLogueado(nombre) {
  navNombre.textContent = nombre;
  navAuth.style.display = 'none';
  navLogueado.style.display = 'flex';
}
function mostrarNavSinSesion() {
  navAuth.style.display = 'flex';
  navLogueado.style.display = 'none';
}
document.getElementById('btn-salir').addEventListener('click', () => {
  sessionStorage.removeItem('barberapp_usuario');
  mostrarNavSinSesion();
});

/* ── LOGIN ────────────────────────────────────────────────── */
document.getElementById('btn-login-enviar').addEventListener('click', async () => {
  const email    = document.getElementById('login-email').value.trim();
  const password = document.getElementById('login-password').value;
  const btn      = document.getElementById('btn-login-enviar');

  if (!email || !password) {
    mostrarAlerta(modalLogin, '⚠️ Completá todos los campos.');
    return;
  }

  btn.disabled = true;
  btn.textContent = 'Ingresando...';
  limpiarAlerta(modalLogin);

  try {
    let datos;

    if (MODO_SIMULADO) {
      await new Promise(r => setTimeout(r, 700));
      const usuariosSimulados = [
        { email: 'juan@gmail.com',  password: '123456', nombre: 'Juan',    apellido: 'Ramirez' },
        { email: 'julio@gmail.com', password: '123456', nombre: 'Julio',   apellido: 'Ramirez' },
        { email: 'juan@test2.com',  password: '321',    nombre: 'Alberto', apellido: 'Roca'    },
      ];
      const usuario = usuariosSimulados.find(u => u.email === email && u.password === password);
      datos = usuario
        ? { ok: true,  nombre: usuario.nombre }
        : { ok: false, error: 'Email o contraseña incorrectos.' };
    } else {
      const respuesta = await fetch(API.login, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password }),
      });
      datos = await respuesta.json();
    }

    if (datos.ok) {
      sessionStorage.setItem('barberapp_usuario', datos.nombre);
      cerrarModal(modalLogin);
      mostrarUsuarioLogueado(datos.nombre);
    } else {
      mostrarAlerta(modalLogin, '❌ ' + datos.error);
    }
  } catch (err) {
    mostrarAlerta(modalLogin, '⚠️ No se pudo conectar con el servidor.');
    console.error(err);
  } finally {
    btn.disabled = false;
    btn.textContent = 'Ingresar';
  }
});

/* ── REGISTRO ─────────────────────────────────────────────── */
document.getElementById('btn-registro-enviar').addEventListener('click', async () => {
  const nombre   = document.getElementById('reg-nombre').value.trim();
  const apellido = document.getElementById('reg-apellido').value.trim();
  const email    = document.getElementById('reg-email').value.trim();
  const telefono = document.getElementById('reg-telefono').value.trim();
  const password = document.getElementById('reg-password').value;
  const btn      = document.getElementById('btn-registro-enviar');

  if (!nombre || !apellido || !email || !password) {
    mostrarAlerta(modalRegistro, '⚠️ Completá los campos obligatorios.');
    return;
  }
  if (password.length < 6) {
    mostrarAlerta(modalRegistro, '⚠️ La contraseña debe tener al menos 6 caracteres.');
    return;
  }
  if (!email.includes('@')) {
    mostrarAlerta(modalRegistro, '⚠️ Ingresá un email válido.');
    return;
  }

  btn.disabled = true;
  btn.textContent = 'Creando cuenta...';
  limpiarAlerta(modalRegistro);

  try {
    let datos;

    if (MODO_SIMULADO) {
      await new Promise(r => setTimeout(r, 800));
      datos = { ok: true, nombre };
    } else {
      const respuesta = await fetch(API.registro, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ nombre, apellido, email, telefono, password }),
      });
      datos = await respuesta.json();
    }

    if (datos.ok) {
      mostrarAlerta(modalRegistro, '✅ ¡Cuenta creada! Iniciá sesión.', 'exito');
      setTimeout(() => {
        cerrarModal(modalRegistro);
        abrirModal(modalLogin);
        document.getElementById('login-email').value = email;
      }, 1500);
    } else {
      mostrarAlerta(modalRegistro, '❌ ' + (datos.error || 'Error al crear la cuenta.'));
    }
  } catch (err) {
    mostrarAlerta(modalRegistro, '⚠️ No se pudo conectar con el servidor.');
    console.error(err);
  } finally {
    btn.disabled = false;
    btn.textContent = 'Crear mi cuenta';
  }
});

/* ── Restaurar sesión guardada ────────────────────────────── */
const usuarioGuardado = sessionStorage.getItem('barberapp_usuario');
if (usuarioGuardado) mostrarUsuarioLogueado(usuarioGuardado);

/* ── Atajos de navegación del hero / nav ──────────────────── */
function irABarberias() {
  document.querySelector('.listing').scrollIntoView({ behavior: 'smooth' });
}
document.getElementById('nav-barberias').addEventListener('click', irABarberias);
document.getElementById('pill-barberias').addEventListener('click', irABarberias);
document.getElementById('pill-reservar').addEventListener('click', irABarberias);
document.getElementById('pill-mis-turnos').addEventListener('click', () => {
  window.location.href = 'paginas/misturnos.html';
});
