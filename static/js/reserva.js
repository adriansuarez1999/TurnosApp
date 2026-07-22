/* ═══════════════════════════════════════════════════════════
   reserva.js
   Wizard de reserva (4 pasos), con Alpine.js.
   Los mismos 3 fetch de antes (barberos, horarios disponibles,
   crear turno) siguen acá — ahora actualizan propiedades del
   componente en vez de escribir HTML a mano.
═══════════════════════════════════════════════════════════ */

function reservaApp() {
  return {
    // Estado general
    barberiaId: null,
    barberia: null,
    cargando: true,
    paso: 1,

    // Paso 1: servicio
    servicios: [],
    servicioSeleccionado: null,

    // Paso 2: barbero
    barberos: [],
    barberoSeleccionado: null,   // objeto barbero, o null si es "cualquiera"
    barberoEsCualquiera: false,
    barberoElegido: false,       // habilita "Siguiente" recién al elegir algo
    barberoLabel: 'Cualquiera disponible',

    // Paso 3: fecha y horario
    fecha: '',
    fechaMin: new Date().toISOString().split('T')[0],
    horarios: [],
    cargandoHorarios: false,
    horarioSeleccionado: null,

    // Paso 4 / confirmación
    confirmando: false,
    confirmado: false,
    estadoFinal: '',

    /* ── Inicialización ─────────────────────────────────────── */
    async init() {
      const params = new URLSearchParams(window.location.search);
      this.barberiaId = params.get('id');

      if (!this.barberiaId) {
        this.cargando = false;
        return;
      }

      try {
        const resp = await fetch(`/api/barberias/${this.barberiaId}/`);
        if (!resp.ok) throw new Error('Barbería no encontrada');
        this.barberia = await resp.json();
        this.servicios = this.barberia.servicios || [];
      } catch (err) {
        console.error(err);
        this.barberia = BARBERIAS_MOCK.find(b => String(b.id) === String(this.barberiaId)) || null;
        this.servicios = this.barberia ? (this.barberia.servicios || []) : [];
      }

      if (!this.barberia) {
        this.cargando = false;
        return;
      }

      await this.cargarBarberos();
      this.cargando = false;
},

    async cargarBarberos() {
      try {
        const resp = await fetch(`/api/barberos/?barberia=${this.barberiaId}`);
        if (!resp.ok) throw new Error('No se pudo obtener barberos');
        this.barberos = await resp.json();
      } catch (err) {
        console.error(err);
        this.barberos = BARBEROS_MOCK.filter(b => String(b.barberia) === String(this.barberiaId));
      }
    },

    /* ── Paso 1: servicio ────────────────────────────────────── */
    seleccionarServicio(s) {
      this.servicioSeleccionado = s;
    },

    /* ── Paso 2: barbero ─────────────────────────────────────── */
    seleccionarBarbero(b) {
      this.barberoElegido = true;

      if (b === 'cualquiera') {
        this.barberoSeleccionado = null;
        this.barberoEsCualquiera = true;
        this.barberoLabel = 'Cualquiera disponible';
      } else {
        this.barberoSeleccionado = b;
        this.barberoEsCualquiera = false;
        this.barberoLabel = b.nombre;
      }
    },

    /* ── Paso 3: fecha y horario ─────────────────────────────── */
    async onFechaChange() {
      this.horarioSeleccionado = null;
      this.horarios = [];
      this.cargandoHorarios = true;

      const params = new URLSearchParams({ fecha: this.fecha });
      if (this.barberoSeleccionado) {
        params.set('barbero', this.barberoSeleccionado.id);
      } else {
        params.set('barberia', this.barberiaId);
      }

      try {
        const resp = await fetch(`/api/turnos/disponibles/?${params.toString()}`);
        if (!resp.ok) throw new Error('No se pudieron obtener los horarios');
        this.horarios = await resp.json();
      } catch (err) {
        console.error(err);
        this.horarios = HORARIOS_MOCK.map(h => ({ hora: h, disponible: true }));
      } finally {
        this.cargandoHorarios = false;
      }
    },

    seleccionarHorario(h) {
      if (!h.disponible) return;
      this.horarioSeleccionado = h.hora;
    },

    /* ── Navegación ──────────────────────────────────────────── */
    irAPaso(numero) {
      this.paso = numero;
    },

    /* ── Paso 4: confirmar ───────────────────────────────────── */
    async confirmarReserva() {
      this.confirmando = true;

      const payload = {
        id_servicio: this.servicioSeleccionado.id,
        id_barbero: this.barberoSeleccionado ? this.barberoSeleccionado.id : null,
        fecha: this.fecha,
        hora_inicio: this.horarioSeleccionado,
      };

      try {
        const resp = await fetch('/api/turnos/', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCookie('csrftoken'),
          },
          body: JSON.stringify(payload),
        });
        const datos = await resp.json();

        if (datos.ok) {
          this.estadoFinal = datos.estado || 'pendiente';
          this.confirmado = true;
        } else {
          alert('❌ ' + (datos.error || 'No se pudo confirmar el turno.'));
        }
      } catch (err) {
        console.error(err);
        alert('⚠️ No se pudo conectar con el servidor.');
      } finally {
        this.confirmando = false;
      }
    },
  };
}

document.addEventListener('alpine:init', () => {
  Alpine.data('reservaApp', reservaApp);
});