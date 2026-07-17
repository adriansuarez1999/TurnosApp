/* ═══════════════════════════════════════════════════════════
   mock-data.js
   Datos de prueba compartidos por barberias.js, detalle.js y
   reserva.js mientras los endpoints reales de Gonzalo/Facundo
   no están disponibles.

   Cuando el backend esté listo, estos arrays dejan de usarse:
   cada archivo ya tiene el fetch real comentado / listo, solo
   hay que poner MODO_SIMULADO = false en cada uno.
═══════════════════════════════════════════════════════════ */

const BARBERIAS_MOCK = [
  {
    id: 1,
    nombre: 'La Navaja de Oro',
    descripcion: 'Especialistas en cortes clásicos',
    zona: 'Centro',
    foto: '',
    servicios: [
      { id: 101, nombre: 'Corte clásico',    precio: 4500 },
      { id: 102, nombre: 'Corte + Barba',     precio: 7000 },
      { id: 103, nombre: 'Afeitado a navaja', precio: 3800 },
    ],
  },
  {
    id: 2,
    nombre: 'Estilo Clásico',
    descripcion: 'Barbería tradicional',
    zona: 'Zona Norte',
    foto: '',
    servicios: [
      { id: 201, nombre: 'Corte tradicional', precio: 4000 },
      { id: 202, nombre: 'Coloración',        precio: 9000 },
      { id: 203, nombre: 'Corte + Barba',      precio: 6800 },
      { id: 204, nombre: 'Perfilado de barba', precio: 3000 },
    ],
  },
  {
    id: 3,
    nombre: 'El Barbero del Sur',
    descripcion: 'Fade y Barba',
    zona: 'Zona Sur',
    foto: '',
    servicios: [
      { id: 301, nombre: 'Fade',             precio: 5000 },
      { id: 302, nombre: 'Diseño de barba',  precio: 3500 },
      { id: 303, nombre: 'Fade + Barba',     precio: 7500 },
    ],
  },
  {
    id: 4,
    nombre: 'Tijeras & Talento',
    descripcion: 'Cortes modernos',
    zona: 'Zona Este',
    foto: '',
    servicios: [
      { id: 401, nombre: 'Corte moderno',   precio: 4800 },
      { id: 402, nombre: 'Diseño a tijera',  precio: 5200 },
    ],
  },
];

const BARBEROS_MOCK = [
  { id: 11, nombre: 'Martín Gómez',  foto: '', barberia: 1 },
  { id: 12, nombre: 'Facundo Ríos',  foto: '', barberia: 1 },
  { id: 21, nombre: 'Lucas Peralta', foto: '', barberia: 2 },
  { id: 22, nombre: 'Diego Sosa',    foto: '', barberia: 2 },
  { id: 23, nombre: 'Nahuel Torres', foto: '', barberia: 2 },
  { id: 31, nombre: 'Bruno Acosta',  foto: '', barberia: 3 },
  { id: 41, nombre: 'Ezequiel Luna', foto: '', barberia: 4 },
];

// Horarios de ejemplo. En la versión real esto lo devuelve
// GET /turnos/disponibles/?barbero=<id>&fecha=<fecha> (Facundo).
const HORARIOS_MOCK = ['09:00', '09:30', '10:00', '10:30', '11:00', '11:30', '14:00', '14:30', '15:00', '15:30', '16:00', '16:30'];

// Turnos de ejemplo del cliente logueado. En la versión real esto lo
// devuelve GET /mis-turnos/ (Facundo), ya ordenado próximos primero.
// Se guardan en sessionStorage para que los turnos reservados en
// reserva.js aparezcan acá también durante la prueba end-to-end.
const TURNOS_STORAGE_KEY = 'barberapp_turnos';

// Devuelve la lista de turnos guardada en sessionStorage. La primera vez
// la inicializa con TURNOS_MOCK_INICIALES (definidos más abajo).
function obtenerTurnosGuardados() {
  const guardado = sessionStorage.getItem(TURNOS_STORAGE_KEY);
  if (guardado) return JSON.parse(guardado);

  sessionStorage.setItem(TURNOS_STORAGE_KEY, JSON.stringify(TURNOS_MOCK_INICIALES));
  return TURNOS_MOCK_INICIALES;
}

function guardarTurnos(lista) {
  sessionStorage.setItem(TURNOS_STORAGE_KEY, JSON.stringify(lista));
}

// Usado por reserva.js al confirmar un turno nuevo, para que aparezca
// enseguida en Mis Turnos sin necesidad de backend real.
function agregarTurnoGuardado(turno) {
  const lista = obtenerTurnosGuardados();
  lista.unshift(turno);
  guardarTurnos(lista);
}

const TURNOS_MOCK_INICIALES = [
  {
    id: 501,
    barberia: 'La Navaja de Oro',
    barbero: 'Martín Gómez',
    servicio: 'Corte + Barba',
    fecha: '2026-07-10',
    hora: '10:30',
    estado: 'confirmado',
  },
  {
    id: 502,
    barberia: 'Estilo Clásico',
    barbero: 'Lucas Peralta',
    servicio: 'Corte tradicional',
    fecha: '2026-07-12',
    hora: '15:00',
    estado: 'pendiente',
  },
  {
    id: 503,
    barberia: 'El Barbero del Sur',
    barbero: 'Bruno Acosta',
    servicio: 'Fade',
    fecha: '2026-06-20',
    hora: '11:00',
    estado: 'cancelado',
  },
  {
    id: 504,
    barberia: 'La Navaja de Oro',
    barbero: 'Facundo Ríos',
    servicio: 'Afeitado a navaja',
    fecha: '2026-06-15',
    hora: '09:30',
    estado: 'confirmado',
  },
];
