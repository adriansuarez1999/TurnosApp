(() => {
  const API_AGENDA = "/api/mi-agenda/turnos/";

  const DIAS_SEMANA = [
    "Lunes",
    "Martes",
    "Miércoles",
    "Jueves",
    "Viernes",
    "Sábado",
    "Domingo",
  ];

  let inicioSemana = obtenerInicioSemana(new Date());

  let turnosSemana = [];

  let fechaSeleccionada = null;

  let turnoAccion = null;

  let accionActual = null;

  let turnoCobro = null;

  const alertaAgenda = document.getElementById("alerta-agenda");

  const textoRangoSemana = document.getElementById("texto-rango-semana");

  const estadoAgenda = document.getElementById("estado-agenda");

  const contenedorAgenda = document.getElementById("contenedor-agenda");

  const grillaAgenda = document.getElementById("grilla-agenda");

  const btnSemanaAnterior = document.getElementById("btn-semana-anterior");

  const btnSemanaSiguiente = document.getElementById("btn-semana-siguiente");

  const btnSemanaActual = document.getElementById("btn-semana-actual");

  const cardDetalleDia = document.getElementById("card-detalle-dia");

  const tituloDetalleDia = document.getElementById("titulo-detalle-dia");

  const subtituloDetalleDia = document.getElementById("subtitulo-detalle-dia");

  const cantidadTurnosDia = document.getElementById("cantidad-turnos-dia");

  const listaTurnosDia = document.getElementById("lista-turnos-dia");

  const modalAccion = new bootstrap.Modal(
    document.getElementById("modal-accion-turno"),
  );

  const tituloModalAccion = document.getElementById("titulo-modal-accion");

  const textoModalAccion = document.getElementById("texto-modal-accion");

  const contenedorMotivo = document.getElementById(
    "contenedor-motivo-cancelacion",
  );

  const motivoCancelacion = document.getElementById("motivo-cancelacion");

  const errorAccionTurno = document.getElementById("error-accion-turno");

  const btnConfirmarAccion = document.getElementById("btn-confirmar-accion");

  const modalHistorial = new bootstrap.Modal(
    document.getElementById("modal-historial-cliente"),
  );

  const nombreClienteHistorial = document.getElementById(
    "nombre-cliente-historial",
  );

  const estadoHistorial = document.getElementById("estado-historial");

  const datosHistorial = document.getElementById("datos-historial");

  const modalCobro = new bootstrap.Modal(
    document.getElementById("modal-cobro"),
  );

  const montoCobro = document.getElementById("monto-cobro");

  const metodoCobro = document.getElementById("metodo-cobro");

  const errorCobro = document.getElementById("error-cobro");

  const btnConfirmarCobro = document.getElementById("btn-confirmar-cobro");

  function getCookie(nombre) {
    let valor = null;

    if (document.cookie && document.cookie !== "") {
      const cookies = document.cookie.split(";");

      for (let i = 0; i < cookies.length; i += 1) {
        const cookie = cookies[i].trim();

        if (cookie.startsWith(`${nombre}=`)) {
          valor = decodeURIComponent(cookie.substring(nombre.length + 1));

          break;
        }
      }
    }

    return valor;
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
    const [anio, mes, dia] = valor.split("-").map(Number);

    return new Date(anio, mes - 1, dia);
  }

  function formatearFecha(fecha) {
    return fecha.toLocaleDateString("es-AR", {
      weekday: "long",
      day: "numeric",
      month: "long",
      year: "numeric",
    });
  }

  function formatearDinero(valor) {
    return Number(valor || 0).toLocaleString("es-AR", {
      style: "currency",
      currency: "ARS",
      minimumFractionDigits: 0,
      maximumFractionDigits: 2,
    });
  }

  function mismoDia(fechaA, fechaB) {
    return fechaAISO(fechaA) === fechaAISO(fechaB);
  }

  function obtenerTurnosFecha(fechaISO) {
    return turnosSemana.filter((turno) => turno.fecha === fechaISO);
  }

  function mostrarAlerta(mensaje, tipo = "success") {
    alertaAgenda.className = `alert alert-${tipo}`;

    alertaAgenda.textContent = mensaje;

    alertaAgenda.classList.remove("d-none");
  }

  function ocultarAlerta() {
    alertaAgenda.className = "alert d-none";

    alertaAgenda.textContent = "";
  }

  function turnoYaEmpezo(turno) {
    const inicio = new Date(`${turno.fecha}T${turno.hora_inicio}:00`);

    return inicio.getTime() <= Date.now();
  }

  function obtenerEstadoVisual(estado) {
    const estados = {
      CONFIRMADO: {
        texto: "Confirmado",

        clase: "text-bg-primary",
      },

      FINALIZADO: {
        texto: "Finalizado",

        clase: "text-bg-success",
      },

      AUSENTE: {
        texto: "Ausente",

        clase: "text-bg-warning",
      },

      CANCELADO: {
        texto: "Cancelado",

        clase: "text-bg-danger",
      },

      PENDIENTE: {
        texto: "Pendiente",

        clase: "text-bg-secondary",
      },
    };

    return (
      estados[estado] || {
        texto: estado,

        clase: "text-bg-secondary",
      }
    );
  }

  async function cargarSemana() {
    ocultarAlerta();

    fechaSeleccionada = null;

    cardDetalleDia.classList.add("d-none");

    contenedorAgenda.classList.add("d-none");

    estadoAgenda.classList.remove("d-none");

    estadoAgenda.innerHTML = `
      <div
        class="spinner-border spinner-border-sm me-2"
        role="status"
      ></div>

      <span
        class="text-body-secondary"
      >
        Cargando turnos...
      </span>
    `;

    const finSemana = sumarDias(inicioSemana, 6);

    const desde = fechaAISO(inicioSemana);

    const hasta = fechaAISO(finSemana);

    textoRangoSemana.textContent = `${inicioSemana.toLocaleDateString("es-AR", {
      day: "numeric",
      month: "short",
    })} al ${finSemana.toLocaleDateString("es-AR", {
      day: "numeric",
      month: "short",
      year: "numeric",
    })}`;

    try {
      const params = new URLSearchParams({
        desde,
        hasta,
      });

      const respuesta = await fetch(`${API_AGENDA}?${params.toString()}`);

      const datos = await obtenerJson(respuesta);

      if (!respuesta.ok || !datos.ok) {
        throw new Error(datos.error || "No se pudo cargar la agenda.");
      }

      turnosSemana = datos.turnos || [];

      renderizarSemana();
    } catch (error) {
      console.error(error);

      estadoAgenda.innerHTML = `
        <div
          class="alert alert-danger mb-0"
        >
          ${escaparHTML(error.message)}
        </div>
      `;
    }
  }

  function renderizarSemana() {
    const hoy = new Date();

    grillaAgenda.innerHTML = "";

    for (let i = 0; i < 7; i += 1) {
      const fecha = sumarDias(inicioSemana, i);

      const fechaISO = fechaAISO(fecha);

      const turnos = obtenerTurnosFecha(fechaISO);

      const boton = document.createElement("button");

      boton.type = "button";

      boton.className = `agenda-dia${mismoDia(fecha, hoy) ? " hoy" : ""}`;

      boton.dataset.fecha = fechaISO;

      boton.innerHTML = `
        <div
          class="d-flex justify-content-between align-items-start gap-2"
        >

          <div>

            <div
              class="agenda-dia-nombre"
            >
              ${DIAS_SEMANA[i]}
            </div>

            <div
              class="agenda-dia-numero"
            >
              ${fecha.getDate()}
            </div>

          </div>


          ${
            mismoDia(fecha, hoy)
              ? `
                <span
                  class="badge bg-primary-subtle text-primary-emphasis"
                >
                  Hoy
                </span>
              `
              : ""
          }

        </div>


        <div
          class="agenda-dia-turnos"
        >

          <span
            class="badge ${
              turnos.length > 0 ? "text-bg-primary" : "text-bg-light border"
            }"
          >
            ${turnos.length === 1 ? "1 turno" : `${turnos.length} turnos`}
          </span>

        </div>
      `;

      boton.addEventListener("click", () => {
        seleccionarDia(fechaISO);
      });

      grillaAgenda.appendChild(boton);
    }

    estadoAgenda.classList.add("d-none");

    contenedorAgenda.classList.remove("d-none");

    const hoyISO = fechaAISO(new Date());

    const dentroDeSemana =
      hoyISO >= fechaAISO(inicioSemana) &&
      hoyISO <= fechaAISO(sumarDias(inicioSemana, 6));

    if (dentroDeSemana) {
      seleccionarDia(hoyISO);
    }
  }

  function seleccionarDia(fechaISO) {
    fechaSeleccionada = fechaISO;

    grillaAgenda.querySelectorAll(".agenda-dia").forEach((boton) => {
      boton.classList.toggle("activo", boton.dataset.fecha === fechaISO);
    });

    renderizarDetalleDia();
  }

  function renderizarDetalleDia() {
    const turnos = obtenerTurnosFecha(fechaSeleccionada);

    const fecha = fechaDesdeISO(fechaSeleccionada);

    tituloDetalleDia.textContent = formatearFecha(fecha);

    subtituloDetalleDia.textContent = "Tus turnos de este día.";

    cantidadTurnosDia.textContent =
      turnos.length === 1 ? "1 turno" : `${turnos.length} turnos`;

    if (turnos.length === 0) {
      listaTurnosDia.innerHTML = `
        <div
          class="text-center py-4"
        >

          <i
            class="bi bi-calendar-check fs-1 text-body-secondary"
          ></i>

          <h3
            class="h6 mt-3"
          >
            No tenés turnos
          </h3>

          <p
            class="text-body-secondary mb-0"
          >
            No hay turnos agendados para este día.
          </p>

        </div>
      `;
    } else {
      listaTurnosDia.innerHTML = turnos.map(crearTurnoHTML).join("");
    }

    cardDetalleDia.classList.remove("d-none");

    configurarEventosTurnos();
  }

  function crearTurnoHTML(turno) {
    const estado = obtenerEstadoVisual(turno.estado);

    const empezo = turnoYaEmpezo(turno);

    const puedeCerrar = turno.estado === "CONFIRMADO" && empezo;

    const puedeCancelar = turno.estado === "CONFIRMADO" && !empezo;

    const puedeCobrar = turno.estado === "FINALIZADO";

    return `
      <div
        class="turno-agenda"
      >

        <div
          class="d-flex justify-content-between align-items-start gap-3 flex-wrap"
        >

          <div>

            <div
              class="fs-5 fw-semibold"
            >
              ${escaparHTML(turno.hora_inicio)}
              -
              ${escaparHTML(turno.hora_fin)}
            </div>

            <div
              class="text-body-secondary small"
            >
              ${escaparHTML(turno.servicio)}
            </div>

          </div>


          <span
            class="badge ${estado.clase}"
          >
            ${estado.texto}
          </span>

        </div>


        <hr>


        <div
          class="row g-3"
        >

          <div
            class="col-12 col-md-4"
          >

            <div
              class="small text-body-secondary"
            >
              Cliente
            </div>


            <button
              type="button"
              class="cliente-link"
              data-historial-cliente="${turno.id_cliente}"
              data-nombre-cliente="${escaparHTML(turno.cliente)}"
            >
              ${escaparHTML(turno.cliente)}
            </button>

          </div>


          <div
            class="col-6 col-md-4"
          >

            <div
              class="small text-body-secondary"
            >
              Servicio
            </div>

            <div>
              ${escaparHTML(turno.servicio)}
            </div>

          </div>


          <div
            class="col-6 col-md-4"
          >

            <div
              class="small text-body-secondary"
            >
              Monto
            </div>

            <div class="fw-semibold">
              ${formatearDinero(turno.monto)}
            </div>

          </div>

        </div>


        ${
          puedeCerrar || puedeCancelar || puedeCobrar
            ? `
              <div
                class="d-flex flex-wrap gap-2 mt-3 pt-3 border-top"
              >

                ${
                  puedeCerrar
                    ? `
                      <button
                        type="button"
                        class="btn btn-success btn-sm"
                        data-accion-turno="finalizar"
                        data-turno-id="${turno.id}"
                      >
                        <i
                          class="bi bi-check-circle me-1"
                        ></i>
                        Finalizar
                      </button>


                      <button
                        type="button"
                        class="btn btn-outline-warning btn-sm"
                        data-accion-turno="ausente"
                        data-turno-id="${turno.id}"
                      >
                        <i
                          class="bi bi-person-x me-1"
                        ></i>
                        Ausente
                      </button>
                    `
                    : ""
                }


                ${
                  puedeCancelar
                    ? `
                      <button
                        type="button"
                        class="btn btn-outline-danger btn-sm"
                        data-accion-turno="cancelar"
                        data-turno-id="${turno.id}"
                      >
                        <i
                          class="bi bi-x-circle me-1"
                        ></i>
                        Cancelar
                      </button>
                    `
                    : ""
                }


                ${
                  puedeCobrar
                    ? `
                      <button
                        type="button"
                        class="btn btn-primary btn-sm"
                        data-cobro-turno="${turno.id}"
                      >
                        <i
                          class="bi bi-cash-coin me-1"
                        ></i>
                        Registrar cobro
                      </button>
                    `
                    : ""
                }

              </div>
            `
            : ""
        }

      </div>
    `;
  }

  function configurarEventosTurnos() {
    document.querySelectorAll("[data-accion-turno]").forEach((boton) => {
      boton.addEventListener("click", () => {
        abrirAccionTurno(
          Number(boton.dataset.turnoId),
          boton.dataset.accionTurno,
        );
      });
    });

    document.querySelectorAll("[data-historial-cliente]").forEach((boton) => {
      boton.addEventListener("click", () => {
        abrirHistorial(
          Number(boton.dataset.historialCliente),
          boton.dataset.nombreCliente,
        );
      });
    });

    document.querySelectorAll("[data-cobro-turno]").forEach((boton) => {
      boton.addEventListener("click", () => {
        abrirCobro(Number(boton.dataset.cobroTurno));
      });
    });
  }

  function abrirAccionTurno(idTurno, accion) {
    turnoAccion = turnosSemana.find(
      (turno) => Number(turno.id) === Number(idTurno),
    );

    accionActual = accion;

    if (!turnoAccion) {
      return;
    }

    errorAccionTurno.classList.add("d-none");

    motivoCancelacion.value = "";

    contenedorMotivo.classList.toggle("d-none", accion !== "cancelar");

    if (accion === "finalizar") {
      tituloModalAccion.textContent = "Finalizar turno";

      textoModalAccion.textContent = `¿Confirmás que el turno de ${turnoAccion.cliente} fue finalizado?`;

      btnConfirmarAccion.className = "btn btn-success";

      btnConfirmarAccion.textContent = "Finalizar";
    } else if (accion === "ausente") {
      tituloModalAccion.textContent = "Marcar ausencia";

      textoModalAccion.textContent = `¿Confirmás que ${turnoAccion.cliente} no asistió al turno?`;

      btnConfirmarAccion.className = "btn btn-warning";

      btnConfirmarAccion.textContent = "Marcar ausente";
    } else {
      tituloModalAccion.textContent = "Cancelar turno";

      textoModalAccion.textContent = `¿Confirmás que no vas a poder atender el turno de ${turnoAccion.cliente}?`;

      btnConfirmarAccion.className = "btn btn-danger";

      btnConfirmarAccion.textContent = "Cancelar turno";
    }

    modalAccion.show();
  }

  async function ejecutarAccionTurno() {
    if (!turnoAccion || !accionActual) {
      return;
    }

    btnConfirmarAccion.disabled = true;

    errorAccionTurno.classList.add("d-none");

    const url = `${API_AGENDA}${turnoAccion.id}/${accionActual}/`;

    const opciones = {
      method: "PATCH",

      headers: {
        "X-CSRFToken": getCookie("csrftoken"),
      },
    };

    if (accionActual === "cancelar") {
      opciones.headers["Content-Type"] = "application/json";

      opciones.body = JSON.stringify({
        motivo: motivoCancelacion.value.trim(),
      });
    }

    try {
      const respuesta = await fetch(url, opciones);

      const datos = await obtenerJson(respuesta);

      if (!respuesta.ok || !datos.ok) {
        throw new Error(datos.error || "No se pudo modificar el turno.");
      }

      const turnoActualizado = datos.turno;

      const indice = turnosSemana.findIndex(
        (turno) => Number(turno.id) === Number(turnoActualizado.id),
      );

      if (indice !== -1) {
        turnosSemana[indice] = turnoActualizado;
      }

      modalAccion.hide();

      mostrarAlerta("Turno actualizado correctamente.");

      renderizarSemana();

      seleccionarDia(turnoActualizado.fecha);

      if (accionActual === "finalizar") {
        setTimeout(() => {
          abrirCobro(turnoActualizado.id);
        }, 300);
      }
    } catch (error) {
      console.error(error);

      errorAccionTurno.textContent = error.message;

      errorAccionTurno.classList.remove("d-none");
    } finally {
      btnConfirmarAccion.disabled = false;
    }
  }

  async function abrirHistorial(idCliente, nombre) {
    nombreClienteHistorial.textContent = nombre;

    estadoHistorial.classList.remove("d-none");

    datosHistorial.classList.add("d-none");

    estadoHistorial.innerHTML = `
      <div
        class="spinner-border spinner-border-sm me-2"
      ></div>
      Cargando...
    `;

    modalHistorial.show();

    try {
      const respuesta = await fetch(
        `/api/mi-agenda/clientes/${idCliente}/historial/`,
      );

      const datos = await obtenerJson(respuesta);

      if (!respuesta.ok || !datos.ok) {
        throw new Error(datos.error || "No se pudo cargar el historial.");
      }

      document.getElementById("historial-total").textContent =
        datos.turnos_totales;

      document.getElementById("historial-finalizados").textContent =
        datos.turnos_finalizados;

      document.getElementById("historial-ausencias").textContent =
        datos.turnos_ausente;

      document.getElementById("historial-cancelados").textContent =
        datos.turnos_cancelados;

      estadoHistorial.classList.add("d-none");

      datosHistorial.classList.remove("d-none");
    } catch (error) {
      estadoHistorial.innerHTML = `
        <div
          class="alert alert-danger mb-0"
        >
          ${escaparHTML(error.message)}
        </div>
      `;
    }
  }

  function abrirCobro(idTurno) {
    turnoCobro = turnosSemana.find(
      (turno) => Number(turno.id) === Number(idTurno),
    );

    if (!turnoCobro) {
      return;
    }

    montoCobro.value = formatearDinero(turnoCobro.monto);

    metodoCobro.value = "EFECTIVO";

    errorCobro.classList.add("d-none");

    modalCobro.show();
  }

  async function registrarCobro() {
    if (!turnoCobro) {
      return;
    }

    btnConfirmarCobro.disabled = true;

    errorCobro.classList.add("d-none");

    try {
      const respuesta = await fetch(`${API_AGENDA}${turnoCobro.id}/cobro/`, {
        method: "POST",

        headers: {
          "Content-Type": "application/json",

          "X-CSRFToken": getCookie("csrftoken"),
        },

        body: JSON.stringify({
          metodo_pago: metodoCobro.value,
        }),
      });

      const datos = await obtenerJson(respuesta);

      if (!respuesta.ok || !datos.ok) {
        throw new Error(datos.error || "No se pudo registrar el cobro.");
      }

      modalCobro.hide();

      mostrarAlerta("Cobro registrado correctamente.");

      turnoCobro = null;
    } catch (error) {
      console.error(error);

      errorCobro.textContent = error.message;

      errorCobro.classList.remove("d-none");
    } finally {
      btnConfirmarCobro.disabled = false;
    }
  }

  btnSemanaAnterior.addEventListener("click", () => {
    inicioSemana = sumarDias(inicioSemana, -7);

    cargarSemana();
  });

  btnSemanaSiguiente.addEventListener("click", () => {
    inicioSemana = sumarDias(inicioSemana, 7);

    cargarSemana();
  });

  btnSemanaActual.addEventListener("click", () => {
    inicioSemana = obtenerInicioSemana(new Date());

    cargarSemana();
  });

  btnConfirmarAccion.addEventListener("click", ejecutarAccionTurno);

  btnConfirmarCobro.addEventListener("click", registrarCobro);

  document.addEventListener("DOMContentLoaded", cargarSemana);
})();
