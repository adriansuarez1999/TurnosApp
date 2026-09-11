/* ═══════════════════════════════════════════════════════════
   reserva.js

   Reserva de turnos sin Alpine.js.
   Bootstrap controla la interfaz.
   JavaScript controla únicamente el estado y los fetch.
═══════════════════════════════════════════════════════════ */

/* ═══════════════════════════════════════════════════════════
   ESTADO
═══════════════════════════════════════════════════════════ */

const estadoReserva = {
  barberiaId: null,

  barberia: null,

  servicios: [],

  barberos: [],

  servicioSeleccionado: null,

  barberoSeleccionado: null,

  barberoEsCualquiera: false,

  fecha: "",

  horarioSeleccionado: null,

  horarios: [],
};

/* ═══════════════════════════════════════════════════════════
   REFERENCIAS DOM
═══════════════════════════════════════════════════════════ */

const reservaEstado = document.getElementById("reserva-estado");

const reservaContenido = document.getElementById("reserva-contenido");

const listaServicios = document.getElementById("lista-servicios");

const listaBarberos = document.getElementById("lista-barberos");

const inputFecha = document.getElementById("input-fecha");

const horariosEstado = document.getElementById("horarios-estado");

const listaHorarios = document.getElementById("lista-horarios");

const btnConfirmar = document.getElementById("btn-confirmar-reserva");

const reservaAlerta = document.getElementById("reserva-alerta");

/* ═══════════════════════════════════════════════════════════
   INICIALIZACIÓN
═══════════════════════════════════════════════════════════ */

document.addEventListener(
  "DOMContentLoaded",

  () => {
    iniciarReserva();
  },
);

async function iniciarReserva() {
  const params = new URLSearchParams(window.location.search);

  estadoReserva.barberiaId = params.get("id");

  if (!estadoReserva.barberiaId) {
    mostrarErrorInicial("Falta indicar la barbería que querés reservar.");

    return;
  }

  configurarFechaMinima();

  try {
    await Promise.all([cargarBarberia(), cargarBarberos()]);

    renderizarBarberia();

    renderizarServicios();

    renderizarBarberos();

    actualizarResumen();

    reservaEstado.classList.add("d-none");

    reservaContenido.classList.remove("d-none");
  } catch (error) {
    console.error(error);

    mostrarErrorInicial("No se pudo cargar la información de la barbería.");
  }
}

/* ═══════════════════════════════════════════════════════════
   CARGAR BARBERÍA
═══════════════════════════════════════════════════════════ */

async function cargarBarberia() {
  const respuesta = await fetch(`/api/barberias/${estadoReserva.barberiaId}/`);

  if (!respuesta.ok) {
    throw new Error("Barbería no encontrada");
  }

  estadoReserva.barberia = await respuesta.json();

  estadoReserva.servicios = estadoReserva.barberia.servicios || [];
}

/* ═══════════════════════════════════════════════════════════
   CARGAR BARBEROS
═══════════════════════════════════════════════════════════ */

async function cargarBarberos() {
  const respuesta = await fetch(
    `/api/barberos/?barberia=${estadoReserva.barberiaId}`,
  );

  if (!respuesta.ok) {
    estadoReserva.barberos = [];

    return;
  }

  estadoReserva.barberos = await respuesta.json();
}

/* ═══════════════════════════════════════════════════════════
   BARBERÍA
═══════════════════════════════════════════════════════════ */

function renderizarBarberia() {
  document.getElementById("reserva-barberia-nombre").textContent =
    estadoReserva.barberia.nombre;

  document.getElementById("reserva-barberia-descripcion").textContent =
    estadoReserva.barberia.descripcion || "";

  document.title = `Reservar en ${estadoReserva.barberia.nombre} — BarberApp`;
}

/* ═══════════════════════════════════════════════════════════
   SERVICIOS
═══════════════════════════════════════════════════════════ */

function renderizarServicios() {
  listaServicios.innerHTML = "";

  if (estadoReserva.servicios.length === 0) {
    listaServicios.innerHTML = `

      <div class="col-12">

        <div class="alert alert-secondary mb-0">

          Esta barbería todavía no tiene servicios disponibles.

        </div>

      </div>

    `;

    return;
  }

  estadoReserva.servicios.forEach((servicio) => {
    const col = document.createElement("div");

    col.className = "col";

    col.innerHTML = `

        <button
          type="button"
          class="btn btn-outline-primary w-100 h-100 text-start p-3"
          data-servicio-id="${servicio.id}"
        >

          <div
            class="d-flex justify-content-between align-items-center gap-3"
          >

            <span class="fw-semibold">
              ${servicio.nombre}
            </span>


            <span class="badge text-bg-primary">
              $${servicio.precio.toLocaleString("es-AR")}
            </span>

          </div>

        </button>

      `;

    listaServicios.appendChild(col);
  });

  listaServicios.querySelectorAll("[data-servicio-id]").forEach((boton) => {
    boton.addEventListener(
      "click",

      () => {
        seleccionarServicio(boton.dataset.servicioId);
      },
    );
  });
}

function seleccionarServicio(id) {
  estadoReserva.servicioSeleccionado = estadoReserva.servicios.find(
    (servicio) => String(servicio.id) === String(id),
  );

  listaServicios.querySelectorAll("[data-servicio-id]").forEach((boton) => {
    const seleccionado = String(boton.dataset.servicioId) === String(id);

    boton.classList.toggle("btn-primary", seleccionado);

    boton.classList.toggle("btn-outline-primary", !seleccionado);
  });

  limpiarHorario();

  actualizarResumen();

  intentarCargarHorarios();
}

/* ═══════════════════════════════════════════════════════════
   BARBEROS
═══════════════════════════════════════════════════════════ */

function renderizarBarberos() {
  listaBarberos.innerHTML = "";

  /* ── Cualquiera disponible ───────────────────────────── */

  const colCualquiera = document.createElement("div");

  colCualquiera.className = "col";

  colCualquiera.innerHTML = `

    <button
      type="button"
      class="btn btn-outline-primary w-100 h-100 text-start p-3"
      data-barbero-id="cualquiera"
    >

      <div class="fw-semibold">
        Cualquiera disponible
      </div>


      <small class="text-body-secondary">
        Asignación automática
      </small>

    </button>

  `;

  listaBarberos.appendChild(colCualquiera);

  /* ── Barberos cargados ───────────────────────────────── */

  estadoReserva.barberos.forEach((barbero) => {
    const col = document.createElement("div");

    col.className = "col";

    col.innerHTML = `

        <button
          type="button"
          class="btn btn-outline-primary w-100 h-100 text-start p-3"
          data-barbero-id="${barbero.id}"
        >

          <div class="fw-semibold">
            ${barbero.nombre}
          </div>

        </button>

      `;

    listaBarberos.appendChild(col);
  });

  listaBarberos.querySelectorAll("[data-barbero-id]").forEach((boton) => {
    boton.addEventListener(
      "click",

      () => {
        seleccionarBarbero(boton.dataset.barberoId);
      },
    );
  });
}

function seleccionarBarbero(id) {
  if (id === "cualquiera") {
    estadoReserva.barberoSeleccionado = null;

    estadoReserva.barberoEsCualquiera = true;
  } else {
    estadoReserva.barberoSeleccionado = estadoReserva.barberos.find(
      (barbero) => String(barbero.id) === String(id),
    );

    estadoReserva.barberoEsCualquiera = false;
  }

  listaBarberos.querySelectorAll("[data-barbero-id]").forEach((boton) => {
    let seleccionado;

    if (id === "cualquiera") {
      seleccionado = boton.dataset.barberoId === "cualquiera";
    } else {
      seleccionado = String(boton.dataset.barberoId) === String(id);
    }

    boton.classList.toggle("btn-primary", seleccionado);

    boton.classList.toggle("btn-outline-primary", !seleccionado);
  });

  limpiarHorario();

  actualizarResumen();

  intentarCargarHorarios();
}

/* ═══════════════════════════════════════════════════════════
   FECHA
═══════════════════════════════════════════════════════════ */

function configurarFechaMinima() {
  const hoy = new Date();

  const year = hoy.getFullYear();

  const month = String(hoy.getMonth() + 1).padStart(2, "0");

  const day = String(hoy.getDate()).padStart(2, "0");

  inputFecha.min = `${year}-${month}-${day}`;
}

inputFecha.addEventListener(
  "change",

  () => {
    estadoReserva.fecha = inputFecha.value;

    limpiarHorario();

    actualizarResumen();

    intentarCargarHorarios();
  },
);

/* ═══════════════════════════════════════════════════════════
   HORARIOS
═══════════════════════════════════════════════════════════ */

function puedeCargarHorarios() {
  const tieneServicio = Boolean(estadoReserva.servicioSeleccionado);

  const tieneBarbero =
    estadoReserva.barberoEsCualquiera ||
    Boolean(estadoReserva.barberoSeleccionado);

  const tieneFecha = Boolean(estadoReserva.fecha);

  return tieneServicio && tieneBarbero && tieneFecha;
}

async function intentarCargarHorarios() {
  if (!puedeCargarHorarios()) {
    horariosEstado.classList.remove("d-none");

    horariosEstado.className = "alert alert-secondary mb-0";

    horariosEstado.textContent = "Elegí primero servicio, barbero y fecha.";

    listaHorarios.classList.add("d-none");

    return;
  }

  await cargarHorarios();
}

async function cargarHorarios() {
  horariosEstado.classList.remove("d-none");

  horariosEstado.className = "alert alert-info";

  horariosEstado.innerHTML = `

    <div class="d-flex align-items-center gap-2">

      <div
        class="spinner-border spinner-border-sm"
        role="status"
      ></div>

      <span>
        Buscando horarios disponibles...
      </span>

    </div>

  `;

  listaHorarios.classList.add("d-none");

  const params = new URLSearchParams({
    fecha: estadoReserva.fecha,
  });

  if (estadoReserva.barberoSeleccionado) {
    params.set("barbero", estadoReserva.barberoSeleccionado.id);
  } else {
    params.set("barberia", estadoReserva.barberiaId);
  }

  try {
    const respuesta = await fetch(
      `/api/turnos/disponibles/?${params.toString()}`,
    );

    if (!respuesta.ok) {
      throw new Error("No se pudieron obtener los horarios");
    }

    estadoReserva.horarios = await respuesta.json();

    renderizarHorarios();
  } catch (error) {
    console.error(error);

    horariosEstado.className = "alert alert-danger";

    horariosEstado.textContent =
      "No se pudieron cargar los horarios disponibles.";
  }
}

function renderizarHorarios() {
  listaHorarios.innerHTML = "";

  const disponibles = estadoReserva.horarios.filter(
    (horario) => horario.disponible,
  );

  if (disponibles.length === 0) {
    horariosEstado.className = "alert alert-warning";

    horariosEstado.textContent = "No hay horarios disponibles para esa fecha.";

    listaHorarios.classList.add("d-none");

    return;
  }

  horariosEstado.classList.add("d-none");

  listaHorarios.classList.remove("d-none");

  estadoReserva.horarios.forEach((horario) => {
    const col = document.createElement("div");

    col.className = "col";

    col.innerHTML = `

        <button
          type="button"
          class="btn btn-outline-primary w-100"
          data-hora="${horario.hora}"
          ${horario.disponible ? "" : "disabled"}
        >

          ${horario.hora}

        </button>

      `;

    listaHorarios.appendChild(col);
  });

  listaHorarios.querySelectorAll("[data-hora]").forEach((boton) => {
    boton.addEventListener(
      "click",

      () => {
        seleccionarHorario(boton.dataset.hora);
      },
    );
  });
}

function seleccionarHorario(hora) {
  estadoReserva.horarioSeleccionado = hora;

  listaHorarios.querySelectorAll("[data-hora]").forEach((boton) => {
    const seleccionado = boton.dataset.hora === hora;

    boton.classList.toggle("btn-primary", seleccionado);

    boton.classList.toggle("btn-outline-primary", !seleccionado);
  });

  actualizarResumen();
}

/* ═══════════════════════════════════════════════════════════
   LIMPIAR HORARIO
═══════════════════════════════════════════════════════════ */

function limpiarHorario() {
  estadoReserva.horarioSeleccionado = null;

  estadoReserva.horarios = [];

  listaHorarios.innerHTML = "";

  listaHorarios.classList.add("d-none");
}

/* ═══════════════════════════════════════════════════════════
   RESUMEN
═══════════════════════════════════════════════════════════ */

function actualizarResumen() {
  document.getElementById("resumen-barberia").textContent =
    estadoReserva.barberia ? estadoReserva.barberia.nombre : "—";

  document.getElementById("resumen-servicio").textContent =
    estadoReserva.servicioSeleccionado
      ? estadoReserva.servicioSeleccionado.nombre
      : "—";

  document.getElementById("resumen-barbero").textContent =
    obtenerNombreBarbero();

  document.getElementById("resumen-fecha").textContent = formatearFecha(
    estadoReserva.fecha,
  );

  document.getElementById("resumen-horario").textContent =
    estadoReserva.horarioSeleccionado || "—";

  document.getElementById("resumen-total").textContent =
    estadoReserva.servicioSeleccionado
      ? `$${estadoReserva.servicioSeleccionado.precio.toLocaleString("es-AR")}`
      : "—";

  actualizarBotonConfirmar();
}

function obtenerNombreBarbero() {
  if (estadoReserva.barberoEsCualquiera) {
    return "Cualquiera disponible";
  }

  if (estadoReserva.barberoSeleccionado) {
    return estadoReserva.barberoSeleccionado.nombre;
  }

  return "—";
}

function formatearFecha(fecha) {
  if (!fecha) {
    return "—";
  }

  const [year, month, day] = fecha.split("-");

  return `${day}/${month}/${year}`;
}

/* ═══════════════════════════════════════════════════════════
   CONFIRMAR
═══════════════════════════════════════════════════════════ */

function reservaCompleta() {
  const barberoElegido =
    estadoReserva.barberoEsCualquiera ||
    Boolean(estadoReserva.barberoSeleccionado);

  return Boolean(
    estadoReserva.servicioSeleccionado &&
    barberoElegido &&
    estadoReserva.fecha &&
    estadoReserva.horarioSeleccionado,
  );
}

function actualizarBotonConfirmar() {
  btnConfirmar.disabled = !reservaCompleta();
}

btnConfirmar.addEventListener(
  "click",

  async () => {
    limpiarAlerta();

    if (!reservaCompleta()) {
      mostrarAlerta("Completá todos los datos antes de confirmar.", "warning");

      return;
    }

    btnConfirmar.disabled = true;

    btnConfirmar.innerHTML = `

      <span
        class="spinner-border spinner-border-sm me-2"
        aria-hidden="true"
      ></span>

      Confirmando...

    `;

    const payload = {
      id_servicio: estadoReserva.servicioSeleccionado.id,

      id_barbero: estadoReserva.barberoSeleccionado
        ? estadoReserva.barberoSeleccionado.id
        : null,

      fecha: estadoReserva.fecha,

      hora_inicio: estadoReserva.horarioSeleccionado,
    };

    try {
      const respuesta = await fetch("/api/turnos/", {
        method: "POST",

        headers: {
          "Content-Type": "application/json",

          "X-CSRFToken": getCookie("csrftoken"),
        },

        body: JSON.stringify(payload),
      });

      const datos = await respuesta.json();

      if (!respuesta.ok || !datos.ok) {
        mostrarAlerta(
          datos.error || "No se pudo confirmar el turno.",
          "danger",
        );

        return;
      }

      const modal = bootstrap.Modal.getOrCreateInstance(
        document.getElementById("modal-reserva-confirmada"),
      );

      modal.show();
    } catch (error) {
      console.error(error);

      mostrarAlerta("No se pudo conectar con el servidor.", "danger");
    } finally {
      btnConfirmar.innerHTML = "Confirmar reserva";

      actualizarBotonConfirmar();
    }
  },
);

/* ═══════════════════════════════════════════════════════════
   ALERTAS
═══════════════════════════════════════════════════════════ */

function mostrarAlerta(mensaje, tipo) {
  reservaAlerta.className = `alert alert-${tipo}`;

  reservaAlerta.textContent = mensaje;

  reservaAlerta.classList.remove("d-none");
}

function limpiarAlerta() {
  reservaAlerta.textContent = "";

  reservaAlerta.classList.add("d-none");
}

/* ═══════════════════════════════════════════════════════════
   ERROR INICIAL
═══════════════════════════════════════════════════════════ */

function mostrarErrorInicial(mensaje) {
  reservaEstado.className = "alert alert-danger";

  reservaEstado.textContent = mensaje;

  reservaContenido.classList.add("d-none");
}

/* ═══════════════════════════════════════════════════════════
   VOLVER
═══════════════════════════════════════════════════════════ */

document.getElementById("btn-volver").addEventListener(
  "click",

  () => {
    history.back();
  },
);
