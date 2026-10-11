(() => {
  /* ═══════════════════════════════════════════════════════════
     turnos-barbero.js

     Sprint 5 - Módulo C

     Calendario semanal de turnos por barbero.

     GET
     /api/mi-barberia/barberos/

     GET
     /api/mi-barberia/barberos/<id>/turnos/
     ?desde=YYYY-MM-DD
     &hasta=YYYY-MM-DD

     El calendario es solamente de lectura.

     Al seleccionar un día NO se vuelve a consultar al backend.
     Los turnos se filtran client-side sobre los datos de la
     semana ya cargada.
  ═══════════════════════════════════════════════════════════ */

  const API_BARBEROS = "/api/mi-barberia/barberos/";

  const DIAS_SEMANA = [
    "Lunes",
    "Martes",
    "Miércoles",
    "Jueves",
    "Viernes",
    "Sábado",
    "Domingo",
  ];

  /* ═══════════════════════════════════════════════════════════
     ESTADO
  ═══════════════════════════════════════════════════════════ */

  let barberos = [];

  let turnosActuales = [];

  let idBarberoSeleccionado = null;

  let inicioSemana = obtenerInicioSemana(new Date());

  let fechaSeleccionada = null;

  /* ═══════════════════════════════════════════════════════════
     REFERENCIAS
  ═══════════════════════════════════════════════════════════ */

  const selectBarbero = document.getElementById(
    "select-barbero-turnos",
  );

  const nombreBarbero = document.getElementById(
    "nombre-barbero-turnos",
  );

  const alertaGeneral = document.getElementById(
    "alerta-turnos-barbero",
  );

  const textoRangoSemana = document.getElementById(
    "texto-rango-semana",
  );

  const estadoCalendario = document.getElementById(
    "estado-calendario-turnos",
  );

  const contenedorCalendario = document.getElementById(
    "contenedor-calendario-turnos",
  );

  const grillaSemana = document.getElementById(
    "grilla-turnos-semana",
  );

  const btnSemanaAnterior = document.getElementById(
    "btn-semana-anterior",
  );

  const btnSemanaSiguiente = document.getElementById(
    "btn-semana-siguiente",
  );

  const btnSemanaActual = document.getElementById(
    "btn-semana-actual",
  );

  const cardDetalleDia = document.getElementById(
    "card-detalle-dia",
  );

  const tituloDetalleDia = document.getElementById(
    "titulo-detalle-dia",
  );

  const subtituloDetalleDia = document.getElementById(
    "subtitulo-detalle-dia",
  );

  const cantidadTurnosDia = document.getElementById(
    "cantidad-turnos-dia",
  );

  const listaTurnosDia = document.getElementById(
    "lista-turnos-dia",
  );

  /* ═══════════════════════════════════════════════════════════
     UTILIDADES
  ═══════════════════════════════════════════════════════════ */

  function obtenerInicioSemana(fecha) {
    const copia = new Date(
      fecha.getFullYear(),
      fecha.getMonth(),
      fecha.getDate(),
    );

    const dia = copia.getDay();

    const diferencia = dia === 0 ? -6 : 1 - dia;

    copia.setDate(copia.getDate() + diferencia);

    return copia;
  }


  function sumarDias(fecha, cantidad) {
    const resultado = new Date(
      fecha.getFullYear(),
      fecha.getMonth(),
      fecha.getDate(),
    );

    resultado.setDate(resultado.getDate() + cantidad);

    return resultado;
  }


  function fechaAISO(fecha) {
    const anio = fecha.getFullYear();

    const mes = String(fecha.getMonth() + 1).padStart(2, "0");

    const dia = String(fecha.getDate()).padStart(2, "0");

    return `${anio}-${mes}-${dia}`;
  }


  function fechaDesdeISO(valor) {
    const [anio, mes, dia] = valor
      .split("-")
      .map(Number);

    return new Date(anio, mes - 1, dia);
  }


  function mismoDia(fechaA, fechaB) {
    return fechaAISO(fechaA) === fechaAISO(fechaB);
  }


  function capitalizar(texto) {
    if (!texto) {
      return "";
    }

    return texto.charAt(0).toUpperCase() + texto.slice(1);
  }


  function formatearFechaCompleta(fecha) {
    return capitalizar(
      fecha.toLocaleDateString("es-AR", {
        weekday: "long",
        day: "numeric",
        month: "long",
        year: "numeric",
      }),
    );
  }


  function formatearRangoSemana(desde, hasta) {
    const mismoMes =
      desde.getMonth() === hasta.getMonth() &&
      desde.getFullYear() === hasta.getFullYear();

    if (mismoMes) {
      return `${desde.getDate()} al ${hasta.toLocaleDateString(
        "es-AR",
        {
          day: "numeric",
          month: "long",
          year: "numeric",
        },
      )}`;
    }

    return `${desde.toLocaleDateString(
      "es-AR",
      {
        day: "numeric",
        month: "short",
      },
    )} al ${hasta.toLocaleDateString(
      "es-AR",
      {
        day: "numeric",
        month: "short",
        year: "numeric",
      },
    )}`;
  }


  function formatearDinero(valor) {
    return Number(valor || 0).toLocaleString(
      "es-AR",
      {
        style: "currency",
        currency: "ARS",
        minimumFractionDigits: 0,
        maximumFractionDigits: 2,
      },
    );
  }


  function escaparHTML(valor) {
    const div = document.createElement("div");

    div.textContent = valor ?? "";

    return div.innerHTML;
  }


  async function obtenerJson(respuesta) {
    try {
      return await respuesta.json();
    } catch {
      return {};
    }
  }


  function obtenerBarberoSeleccionado() {
    return barberos.find(
      (barbero) =>
        Number(barbero.id_barbero) ===
        Number(idBarberoSeleccionado),
    );
  }


  function obtenerTurnosDeFecha(fechaISO) {
    return turnosActuales.filter(
      (turno) => turno.fecha === fechaISO,
    );
  }

  /* ═══════════════════════════════════════════════════════════
     ALERTAS
  ═══════════════════════════════════════════════════════════ */

  function mostrarAlerta(
    mensaje,
    tipo = "danger",
  ) {
    alertaGeneral.textContent = mensaje;

    alertaGeneral.className =
      `alert alert-${tipo}`;

    alertaGeneral.classList.remove("d-none");
  }


  function limpiarAlerta() {
    alertaGeneral.textContent = "";

    alertaGeneral.className = "alert d-none";
  }

  /* ═══════════════════════════════════════════════════════════
     BARBEROS
  ═══════════════════════════════════════════════════════════ */

  async function cargarBarberos() {
    mostrarCargaBarberos();

    try {
      const respuesta = await fetch(
        API_BARBEROS,
      );

      const datos = await obtenerJson(
        respuesta,
      );

      if (!respuesta.ok || !datos.ok) {
        mostrarErrorGeneral(
          datos.error ||
            "No se pudieron cargar los barberos.",
        );

        return;
      }

      barberos = datos.barberos || [];

      renderizarSelectorBarberos();
    } catch (error) {
      console.error(error);

      mostrarErrorGeneral(
        "Ocurrió un error al cargar los barberos.",
      );
    }
  }


  function mostrarCargaBarberos() {
    selectBarbero.disabled = true;

    selectBarbero.innerHTML = `
      <option value="">
        Cargando barberos...
      </option>
    `;

    deshabilitarNavegacion();
  }


  function renderizarSelectorBarberos() {
    if (barberos.length === 0) {
      selectBarbero.innerHTML = `
        <option value="">
          No hay barberos registrados
        </option>
      `;

      selectBarbero.disabled = true;

      nombreBarbero.textContent = "Ninguno";

      mostrarEstadoSinBarberos();

      return;
    }

    selectBarbero.innerHTML = `
      <option value="">
        Seleccionar barbero
      </option>

      ${barberos
        .map((barbero) => {
          const inactivo =
            barbero.estado === "INACTIVO";

          return `
            <option
              value="${barbero.id_barbero}"
              ${inactivo ? "disabled" : ""}
            >
              ${escaparHTML(barbero.nombre)}
              ${escaparHTML(barbero.apellido)}
              ${inactivo ? " — Inactivo" : ""}
            </option>
          `;
        })
        .join("")}
    `;

    const primerActivo = barberos.find(
      (barbero) =>
        barbero.estado !== "INACTIVO",
    );

    if (!primerActivo) {
      selectBarbero.disabled = true;

      nombreBarbero.textContent = "Ninguno";

      mostrarEstadoSinBarberosActivos();

      return;
    }

    selectBarbero.disabled = false;

    selectBarbero.value =
      primerActivo.id_barbero;

    seleccionarBarbero(
      primerActivo.id_barbero,
    );
  }

  /* ═══════════════════════════════════════════════════════════
     SELECCIÓN DE BARBERO
  ═══════════════════════════════════════════════════════════ */

  async function seleccionarBarbero(id) {
    limpiarAlerta();

    idBarberoSeleccionado =
      id ? Number(id) : null;

    fechaSeleccionada = null;

    ocultarDetalleDia();

    if (!idBarberoSeleccionado) {
      nombreBarbero.textContent = "Ninguno";

      turnosActuales = [];

      deshabilitarNavegacion();

      mostrarEstadoInicial();

      return;
    }

    const barbero =
      obtenerBarberoSeleccionado();

    nombreBarbero.textContent = barbero
      ? `${barbero.nombre} ${barbero.apellido}`
      : "Barbero seleccionado";

    habilitarNavegacion();

    await cargarSemana();
  }

  /* ═══════════════════════════════════════════════════════════
     SEMANA
  ═══════════════════════════════════════════════════════════ */

  async function cargarSemana() {
    if (!idBarberoSeleccionado) {
      return;
    }

    limpiarAlerta();

    fechaSeleccionada = null;

    ocultarDetalleDia();

    mostrarCargaCalendario();

    const finSemana = sumarDias(
      inicioSemana,
      6,
    );

    const desde = fechaAISO(
      inicioSemana,
    );

    const hasta = fechaAISO(
      finSemana,
    );

    actualizarTextoSemana();

    const params = new URLSearchParams({
      desde,
      hasta,
    });

    const url =
      `/api/mi-barberia/barberos/` +
      `${idBarberoSeleccionado}/turnos/` +
      `?${params.toString()}`;

    try {
      const respuesta = await fetch(url);

      const datos = await obtenerJson(
        respuesta,
      );

      if (!respuesta.ok || !datos.ok) {
        mostrarErrorCalendario(
          datos.error ||
            "No se pudieron cargar los turnos.",
        );

        return;
      }

      turnosActuales = datos.turnos || [];

      renderizarCalendario();
    } catch (error) {
      console.error(error);

      mostrarErrorCalendario(
        "Ocurrió un error al cargar los turnos.",
      );
    }
  }


  function actualizarTextoSemana() {
    const finSemana = sumarDias(
      inicioSemana,
      6,
    );

    textoRangoSemana.textContent =
      `Semana del ${formatearRangoSemana(
        inicioSemana,
        finSemana,
      )}`;
  }


  function navegarSemana(cantidadDias) {
    inicioSemana = sumarDias(
      inicioSemana,
      cantidadDias,
    );

    cargarSemana();
  }


  function volverSemanaActual() {
    inicioSemana =
      obtenerInicioSemana(new Date());

    cargarSemana();
  }

  /* ═══════════════════════════════════════════════════════════
     RENDER CALENDARIO
  ═══════════════════════════════════════════════════════════ */

  function renderizarCalendario() {
    const hoy = new Date();

    grillaSemana.innerHTML = "";

    for (
      let indice = 0;
      indice < 7;
      indice += 1
    ) {
      const fecha = sumarDias(
        inicioSemana,
        indice,
      );

      const fechaISO = fechaAISO(fecha);

      const turnos =
        obtenerTurnosDeFecha(fechaISO);

      const cantidad = turnos.length;

      const esHoy = mismoDia(
        fecha,
        hoy,
      );

      const boton =
        document.createElement("button");

      boton.type = "button";

      boton.className =
        `calendario-dia${
          esHoy ? " hoy" : ""
        }`;

      boton.dataset.fecha =
        fechaISO;

      boton.setAttribute(
        "aria-pressed",
        "false",
      );

      boton.innerHTML = `
        <div
          class="d-flex justify-content-between align-items-start gap-2"
        >

          <div>

            <div
              class="calendario-dia-nombre"
            >
              ${DIAS_SEMANA[indice]}
            </div>

            <div
              class="calendario-dia-numero"
            >
              ${fecha.getDate()}
            </div>

          </div>


          ${
            esHoy
              ? `
                <span
                  class="badge bg-primary-subtle text-primary-emphasis border border-primary-subtle"
                >
                  Hoy
                </span>
              `
              : ""
          }

        </div>


        <div
          class="calendario-dia-turnos"
        >

          <span
            class="badge ${
              cantidad > 0
                ? "text-bg-primary"
                : "bg-body-secondary text-body border"
            }"
          >
            ${
              cantidad === 1
                ? "1 turno"
                : `${cantidad} turnos`
            }
          </span>

        </div>
      `;

      boton.addEventListener(
        "click",

        () => {
          seleccionarDia(
            fechaISO,
          );
        },
      );

      grillaSemana.appendChild(
        boton,
      );
    }

    estadoCalendario.classList.add(
      "d-none",
    );

    contenedorCalendario.classList.remove(
      "d-none",
    );
  }

  /* ═══════════════════════════════════════════════════════════
     DETALLE DE UN DÍA
  ═══════════════════════════════════════════════════════════ */

  function seleccionarDia(fechaISO) {
    fechaSeleccionada =
      fechaISO;

    grillaSemana
      .querySelectorAll(
        ".calendario-dia",
      )
      .forEach((boton) => {
        const activo =
          boton.dataset.fecha ===
          fechaISO;

        boton.classList.toggle(
          "activo",
          activo,
        );

        boton.setAttribute(
          "aria-pressed",
          activo
            ? "true"
            : "false",
        );
      });

    renderizarDetalleDia();
  }


  function renderizarDetalleDia() {
    if (!fechaSeleccionada) {
      ocultarDetalleDia();

      return;
    }

    const turnos =
      obtenerTurnosDeFecha(
        fechaSeleccionada,
      );

    const fecha =
      fechaDesdeISO(
        fechaSeleccionada,
      );

    const barbero =
      obtenerBarberoSeleccionado();

    tituloDetalleDia.textContent =
      formatearFechaCompleta(fecha);

    subtituloDetalleDia.textContent =
      barbero
        ? `Agenda de ${barbero.nombre} ${barbero.apellido}`
        : "Agenda del profesional seleccionado";

    cantidadTurnosDia.textContent =
      turnos.length === 1
        ? "1 turno"
        : `${turnos.length} turnos`;

    if (turnos.length === 0) {
      listaTurnosDia.innerHTML = `
        <div
          class="text-center py-4"
        >

          <i
            class="bi bi-calendar-check fs-1 text-body-secondary"
          ></i>


          <h3
            class="h6 mt-3 mb-1"
          >
            Sin turnos
          </h3>


          <p
            class="text-body-secondary mb-0"
          >
            Este barbero no tiene turnos agendados para este día.
          </p>

        </div>
      `;
    } else {
      listaTurnosDia.innerHTML = `
        <div
          class="vstack gap-3"
        >

          ${turnos
            .map(
              (turno) =>
                crearTurnoHTML(turno),
            )
            .join("")}

        </div>
      `;
    }

    cardDetalleDia.classList.remove(
      "d-none",
    );
  }


  function crearTurnoHTML(turno) {
    return `
      <div
        class="border rounded-3 p-3 turno-detalle-item"
      >

        <div
          class="row align-items-center g-3"
        >


          <div
            class="col-12 col-md-3"
          >

            <div
              class="text-body-secondary small"
            >
              Horario
            </div>


            <div
              class="fw-semibold"
            >
              ${escaparHTML(turno.hora_inicio)}
              -
              ${escaparHTML(turno.hora_fin)}
            </div>

          </div>



          <div
            class="col-12 col-md-3"
          >

            <div
              class="text-body-secondary small"
            >
              Cliente
            </div>


            <div
              class="fw-semibold"
            >
              ${escaparHTML(turno.cliente)}
            </div>

          </div>



          <div
            class="col-12 col-md-2"
          >

            <div
              class="text-body-secondary small"
            >
              Servicio
            </div>


            <div>
              ${escaparHTML(turno.servicio)}
            </div>

          </div>



          <div
            class="col-6 col-md-2"
          >

            <div
              class="text-body-secondary small"
            >
              Estado
            </div>


            ${crearBadgeEstado(
              turno.estado,
            )}

          </div>



          <div
            class="col-6 col-md-2 text-md-end"
          >

            <div
              class="text-body-secondary small"
            >
              Monto
            </div>


            <div
              class="fw-semibold"
            >
              ${formatearDinero(turno.monto)}
            </div>

          </div>


        </div>

      </div>
    `;
  }

  /* ═══════════════════════════════════════════════════════════
     ESTADOS DE TURNO
  ═══════════════════════════════════════════════════════════ */

  function crearBadgeEstado(estado) {
    const valor =
      String(estado || "")
        .toUpperCase();

    const configuracion = {
      PENDIENTE: {
        clase:
          "text-bg-warning",
        texto:
          "Pendiente",
      },

      RESERVADO: {
        clase:
          "text-bg-primary",
        texto:
          "Reservado",
      },

      CONFIRMADO: {
        clase:
          "text-bg-primary",
        texto:
          "Confirmado",
      },

      FINALIZADO: {
        clase:
          "text-bg-success",
        texto:
          "Finalizado",
      },

      CANCELADO: {
        clase:
          "text-bg-danger",
        texto:
          "Cancelado",
      },

      AUSENTE: {
        clase:
          "text-bg-secondary",
        texto:
          "Ausente",
      },
    };

    const config =
      configuracion[valor] || {
        clase:
          "text-bg-secondary",
        texto:
          estado || "Sin estado",
      };

    return `
      <span
        class="badge ${config.clase}"
      >
        ${escaparHTML(config.texto)}
      </span>
    `;
  }

  /* ═══════════════════════════════════════════════════════════
     ESTADOS VISUALES
  ═══════════════════════════════════════════════════════════ */

  function mostrarEstadoInicial() {
    contenedorCalendario.classList.add(
      "d-none",
    );

    estadoCalendario.classList.remove(
      "d-none",
    );

    textoRangoSemana.textContent =
      "Seleccioná un barbero para consultar su agenda.";

    estadoCalendario.innerHTML = `
      <div
        class="text-center"
      >

        <i
          class="bi bi-calendar3 fs-1 text-body-secondary"
        ></i>


        <h3
          class="h5 mt-3"
        >
          Seleccioná un barbero
        </h3>


        <p
          class="text-body-secondary mb-0"
        >
          Sus turnos de la semana aparecerán en esta sección.
        </p>

      </div>
    `;
  }


  function mostrarCargaCalendario() {
    contenedorCalendario.classList.add(
      "d-none",
    );

    estadoCalendario.classList.remove(
      "d-none",
    );

    estadoCalendario.innerHTML = `
      <div
        class="d-flex justify-content-center align-items-center gap-2 text-body-secondary"
      >

        <div
          class="spinner-border spinner-border-sm"
          role="status"
        ></div>


        <span>
          Cargando turnos...
        </span>

      </div>
    `;
  }


  function mostrarErrorCalendario(
    mensaje,
  ) {
    turnosActuales = [];

    contenedorCalendario.classList.add(
      "d-none",
    );

    estadoCalendario.classList.remove(
      "d-none",
    );

    estadoCalendario.innerHTML = `
      <div
        class="alert alert-danger mb-0"
        role="alert"
      >
        ${escaparHTML(mensaje)}
      </div>
    `;

    ocultarDetalleDia();
  }


  function mostrarErrorGeneral(
    mensaje,
  ) {
    mostrarAlerta(
      mensaje,
      "danger",
    );

    selectBarbero.disabled = true;

    nombreBarbero.textContent =
      "Ninguno";

    deshabilitarNavegacion();

    mostrarErrorCalendario(
      mensaje,
    );
  }


  function mostrarEstadoSinBarberos() {
    contenedorCalendario.classList.add(
      "d-none",
    );

    estadoCalendario.classList.remove(
      "d-none",
    );

    textoRangoSemana.textContent =
      "No hay profesionales registrados.";

    estadoCalendario.innerHTML = `
      <div
        class="text-center"
      >

        <i
          class="bi bi-people fs-1 text-body-secondary"
        ></i>


        <h3
          class="h5 mt-3"
        >
          No hay barberos registrados
        </h3>


        <p
          class="text-body-secondary mb-0"
        >
          Agregá un barbero desde la sección
          "Mis barberos" para consultar su agenda.
        </p>

      </div>
    `;

    deshabilitarNavegacion();
  }


  function mostrarEstadoSinBarberosActivos() {
    contenedorCalendario.classList.add(
      "d-none",
    );

    estadoCalendario.classList.remove(
      "d-none",
    );

    textoRangoSemana.textContent =
      "No hay profesionales activos.";

    estadoCalendario.innerHTML = `
      <div
        class="text-center"
      >

        <i
          class="bi bi-person-x fs-1 text-body-secondary"
        ></i>


        <h3
          class="h5 mt-3"
        >
          No hay barberos activos
        </h3>


        <p
          class="text-body-secondary mb-0"
        >
          Los profesionales registrados se encuentran inactivos.
        </p>

      </div>
    `;

    deshabilitarNavegacion();
  }


  function ocultarDetalleDia() {
    cardDetalleDia.classList.add(
      "d-none",
    );

    listaTurnosDia.innerHTML = "";

    cantidadTurnosDia.textContent =
      "0 turnos";
  }


  function habilitarNavegacion() {
    btnSemanaAnterior.disabled =
      false;

    btnSemanaSiguiente.disabled =
      false;

    btnSemanaActual.disabled =
      false;
  }


  function deshabilitarNavegacion() {
    btnSemanaAnterior.disabled =
      true;

    btnSemanaSiguiente.disabled =
      true;

    btnSemanaActual.disabled =
      true;
  }

  /* ═══════════════════════════════════════════════════════════
     EVENTOS
  ═══════════════════════════════════════════════════════════ */

  selectBarbero.addEventListener(
    "change",

    () => {
      seleccionarBarbero(
        selectBarbero.value,
      );
    },
  );


  btnSemanaAnterior.addEventListener(
    "click",

    () => {
      navegarSemana(-7);
    },
  );


  btnSemanaSiguiente.addEventListener(
    "click",

    () => {
      navegarSemana(7);
    },
  );


  btnSemanaActual.addEventListener(
    "click",

    () => {
      volverSemanaActual();
    },
  );

  /* ═══════════════════════════════════════════════════════════
     INICIALIZACIÓN
  ═══════════════════════════════════════════════════════════ */

  document.addEventListener(
    "DOMContentLoaded",

    () => {
      cargarBarberos();
    },
  );
})();