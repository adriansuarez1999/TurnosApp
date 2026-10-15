(() => {
  const MODO_SIMULADO_MISTURNOS = false;

  const API_MISTURNOS = {
    listar: "/api/mis-turnos/",

    cancelar: (id) => `/api/turnos/${id}/cancelar/`,

    calificar: (id) => `/api/turnos/${id}/calificar/`,
  };

  let turnosActuales = [];

  let turnoIdPendienteCancelar = null;

  let turnoPendienteCalificar = null;

  let puntuacionSeleccionada = 0;

  /* REFERENCIAS */

  const listaProximos = document.getElementById("lista-proximos");

  const listaPasados = document.getElementById("lista-pasados");

  const cantidadProximos = document.getElementById("cantidad-proximos");

  const cantidadPasados = document.getElementById("cantidad-pasados");

  const cantidadTotal = document.getElementById("cantidad-total");

  const cantidadProximosHeader = document.getElementById(
    "cantidad-proximos-header",
  );

  const cantidadPasadosHeader = document.getElementById(
    "cantidad-pasados-header",
  );

  /* CANCELAR */

  const modalCancelarElemento = document.getElementById("modal-cancelar");

  const btnCancelarSi = document.getElementById("btn-cancelar-si");

  const alertaCancelar = document.getElementById("alerta-cancelar");

  const modalCancelar = bootstrap.Modal.getOrCreateInstance(
    modalCancelarElemento,
  );

  /* CALIFICAR */

  const modalCalificarElemento = document.getElementById("modal-calificar");

  const modalCalificar = bootstrap.Modal.getOrCreateInstance(
    modalCalificarElemento,
  );

  const detalleTurnoCalificar = document.getElementById(
    "detalle-turno-calificar",
  );

  const estrellas = document.querySelectorAll(".estrella-calificacion");

  const textoPuntuacion = document.getElementById("texto-puntuacion");

  const comentarioCalificacion = document.getElementById(
    "comentario-calificacion",
  );

  const alertaCalificar = document.getElementById("alerta-calificar");

  const btnEnviarCalificacion = document.getElementById(
    "btn-enviar-calificacion",
  );

  const alertaCalificacionGlobal = document.getElementById(
    "alerta-calificacion-global",
  );

  /* CARGAR TURNOS */

  async function obtenerMisTurnos() {
    mostrarCarga();

    try {
      let turnos;

      if (MODO_SIMULADO_MISTURNOS) {
        await new Promise((resolve) => setTimeout(resolve, 300));

        turnos = obtenerTurnosGuardados();
      } else {
        const respuesta = await fetch(API_MISTURNOS.listar);

        if (!respuesta.ok) {
          throw new Error("No se pudieron obtener los turnos");
        }

        turnos = await respuesta.json();
      }

      turnosActuales = Array.isArray(turnos) ? turnos : [];

      renderizarMisTurnos(turnosActuales);
    } catch (error) {
      console.error("Error al obtener mis turnos:", error);

      listaProximos.innerHTML = `
        <div
          class="alert alert-danger mb-0"
        >
          No se pudieron cargar tus turnos.
        </div>
      `;

      listaPasados.innerHTML = "";

      cantidadProximos.textContent = "0";

      cantidadPasados.textContent = "0";

      cantidadTotal.textContent = "0";

      cantidadProximosHeader.textContent = "0";

      cantidadPasadosHeader.textContent = "0";
    }
  }

  function mostrarCarga() {
    listaProximos.innerHTML = `
      <div
        class="d-flex align-items-center gap-2 text-body-secondary"
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

    listaPasados.innerHTML = "";

    cantidadProximos.textContent = "0";

    cantidadPasados.textContent = "0";

    cantidadTotal.textContent = "0";

    cantidadProximosHeader.textContent = "0";

    cantidadPasadosHeader.textContent = "0";
  }

  /* SEPARAR TURNOS */

  function renderizarMisTurnos(turnos) {
    const hoy = obtenerFechaActual();

    const proximos = turnos
      .filter((turno) => turno.fecha >= hoy)
      .sort(compararTurnosAscendente);

    const pasados = turnos
      .filter((turno) => turno.fecha < hoy)
      .sort(compararTurnosDescendente);

    cantidadProximos.textContent = proximos.length;

    cantidadPasados.textContent = pasados.length;

    cantidadTotal.textContent = turnos.length;

    cantidadProximosHeader.textContent = proximos.length;

    cantidadPasadosHeader.textContent = pasados.length;

    renderizarProximos(proximos);

    renderizarPasados(pasados);

    conectarBotonesCancelar();

    conectarBotonesCalificar();
  }

  function obtenerFechaActual() {
    const hoy = new Date();

    const year = hoy.getFullYear();

    const month = String(hoy.getMonth() + 1).padStart(2, "0");

    const day = String(hoy.getDate()).padStart(2, "0");

    return `${year}-${month}-${day}`;
  }

  function compararTurnosAscendente(a, b) {
    return `${a.fecha}${a.hora}`.localeCompare(`${b.fecha}${b.hora}`);
  }

  function compararTurnosDescendente(a, b) {
    return `${b.fecha}${b.hora}`.localeCompare(`${a.fecha}${a.hora}`);
  }

  /* PRÓXIMOS */

  function renderizarProximos(turnos) {
    if (turnos.length === 0) {
      listaProximos.innerHTML = `
        <div class="appointments-empty">

          <span
            class="appointments-empty__icon"
          >
            <i
              class="bi bi-calendar-plus"
            ></i>
          </span>


          <div>

            <h3 class="h6 mb-1">
              No tenés turnos próximos
            </h3>

            <p
              class="text-body-secondary small mb-3"
            >
              Cuando reserves un turno aparecerá acá.
            </p>


            <a
              href="/#listado-barberias"
              class="btn btn-outline-primary btn-sm"
            >
              Buscar barbería
            </a>

          </div>

        </div>
      `;

      return;
    }

    listaProximos.innerHTML = turnos
      .map((turno) => crearTurnoHTML(turno, true))
      .join("");
  }

  /* PASADOS */

  function renderizarPasados(turnos) {
    if (turnos.length === 0) {
      listaPasados.innerHTML = `
        <div class="appointments-empty">

          <span
            class="appointments-empty__icon"
          >
            <i
              class="bi bi-clock-history"
            ></i>
          </span>


          <div>

            <h3 class="h6 mb-1">
              Todavía no hay historial
            </h3>

            <p
              class="text-body-secondary small mb-0"
            >
              Tus turnos anteriores aparecerán en esta sección.
            </p>

          </div>

        </div>
      `;

      return;
    }

    listaPasados.innerHTML = turnos
      .map((turno) => crearTurnoHTML(turno, false))
      .join("");
  }

  /* CARD TURNO */

  function crearTurnoHTML(turno, esProximo) {
    const fechaFormateada = formatearFecha(turno.fecha);

    const partesFecha = obtenerPartesFecha(turno.fecha);

    const estado = String(turno.estado || "").toUpperCase();

    const puedeCancelar =
      esProximo &&
      estado !== "CANCELADO" &&
      estado !== "FINALIZADO" &&
      estado !== "AUSENTE";

    const puedeCalificar = estado === "FINALIZADO" && !turno.calificado;

    const yaCalificado = estado === "FINALIZADO" && Boolean(turno.calificado);

    return `
      <article
        class="appointment-item"
      >

        <div
          class="appointment-date"
        >

          <span
            class="appointment-date__day"
          >
            ${partesFecha.dia}
          </span>

          <span
            class="appointment-date__month"
          >
            ${partesFecha.mes}
          </span>

        </div>


        <div
          class="appointment-item__content"
        >

          <div
            class="d-flex flex-column flex-lg-row justify-content-between gap-3"
          >


            <div class="flex-grow-1">

              <div
                class="d-flex align-items-center flex-wrap gap-2 mb-2"
              >

                <h3 class="h5 mb-0">
                  ${turno.barberia}
                </h3>

                ${crearBadgeEstado(turno.estado)}

              </div>


              <div
                class="appointment-service mb-3"
              >

                <i
                  class="bi bi-scissors me-1"
                ></i>

                ${turno.servicio}

              </div>


              <div
                class="d-flex flex-wrap gap-3 gap-md-4 small"
              >

                <span
                  class="appointment-detail"
                >

                  <i
                    class="bi bi-person"
                  ></i>

                  ${turno.barbero}

                </span>


                <span
                  class="appointment-detail"
                >

                  <i
                    class="bi bi-calendar3"
                  ></i>

                  ${fechaFormateada}

                </span>


                <span
                  class="appointment-detail"
                >

                  <i
                    class="bi bi-clock"
                  ></i>

                  ${turno.hora} hs

                </span>

              </div>

            </div>


            ${
              puedeCancelar || puedeCalificar || yaCalificado
                ? `
                  <div
                    class="d-flex align-items-start flex-wrap gap-2"
                  >

                    ${
                      puedeCancelar
                        ? `
                          <button
                            type="button"
                            class="btn btn-outline-danger btn-sm btn-cancelar-turno"
                            data-id="${turno.id}"
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
                      puedeCalificar
                        ? `
                          <button
                            type="button"
                            class="btn btn-outline-warning btn-sm btn-calificar-turno"
                            data-id="${turno.id}"
                          >
                            <i
                              class="bi bi-star me-1"
                            ></i>

                            Calificar
                          </button>
                        `
                        : ""
                    }


                    ${
                      yaCalificado
                        ? `
                          <span
                            class="badge bg-success-subtle text-success-emphasis border border-success-subtle py-2 px-3"
                          >
                            <i
                              class="bi bi-check-circle me-1"
                            ></i>

                            Calificado
                          </span>
                        `
                        : ""
                    }

                  </div>
                `
                : ""
            }

          </div>

        </div>

      </article>
    `;
  }

  /* BADGES */

  function crearBadgeEstado(estado) {
    const valor = String(estado || "").toLowerCase();

    let clase = "text-bg-secondary";

    let texto = estado || "Sin estado";

    if (valor === "confirmado") {
      clase = "text-bg-success";

      texto = "Confirmado";
    } else if (valor === "pendiente") {
      clase = "text-bg-warning";

      texto = "Pendiente";
    } else if (valor === "cancelado") {
      clase = "text-bg-danger";

      texto = "Cancelado";
    } else if (valor === "finalizado") {
      clase = "text-bg-secondary";

      texto = "Finalizado";
    } else if (valor === "ausente") {
      clase = "text-bg-dark";

      texto = "Ausente";
    }

    return `
      <span
        class="badge ${clase}"
      >
        ${texto}
      </span>
    `;
  }

  /* FECHA */

  function formatearFecha(fecha) {
    if (!fecha) {
      return "—";
    }

    return new Date(`${fecha}T00:00:00`).toLocaleDateString("es-AR", {
      day: "2-digit",

      month: "short",

      year: "numeric",
    });
  }

  function obtenerPartesFecha(fecha) {
    if (!fecha) {
      return {
        dia: "—",
        mes: "",
      };
    }

    const fechaLocal = new Date(`${fecha}T00:00:00`);

    return {
      dia: fechaLocal.toLocaleDateString("es-AR", {
        day: "2-digit",
      }),

      mes: fechaLocal
        .toLocaleDateString("es-AR", {
          month: "short",
        })
        .replace(".", "")
        .toUpperCase(),
    };
  }

  /* CANCELAR */

  function conectarBotonesCancelar() {
    document.querySelectorAll(".btn-cancelar-turno").forEach((boton) => {
      boton.addEventListener("click", () => {
        abrirModalCancelar(boton.dataset.id);
      });
    });
  }

  function abrirModalCancelar(id) {
    turnoIdPendienteCancelar = id;

    limpiarAlertaCancelar();

    modalCancelar.show();
  }

  function cerrarModalCancelar() {
    turnoIdPendienteCancelar = null;

    modalCancelar.hide();
  }

  modalCancelarElemento.addEventListener("hidden.bs.modal", () => {
    turnoIdPendienteCancelar = null;

    limpiarAlertaCancelar();
  });

  btnCancelarSi.addEventListener("click", async () => {
    const id = turnoIdPendienteCancelar;

    if (!id) {
      return;
    }

    btnCancelarSi.disabled = true;

    btnCancelarSi.innerHTML = `
          <span
            class="spinner-border spinner-border-sm me-2"
            aria-hidden="true"
          ></span>

          Cancelando...
        `;

    limpiarAlertaCancelar();

    try {
      if (MODO_SIMULADO_MISTURNOS) {
        await new Promise((resolve) => setTimeout(resolve, 500));

        const lista = obtenerTurnosGuardados();

        const turno = lista.find((item) => String(item.id) === String(id));

        if (turno) {
          turno.estado = "cancelado";
        }

        guardarTurnos(lista);
      } else {
        const respuesta = await fetch(API_MISTURNOS.cancelar(id), {
          method: "PATCH",

          headers: {
            "X-CSRFToken": getCookie("csrftoken"),
          },
        });

        if (!respuesta.ok) {
          let mensaje = "No se pudo cancelar el turno.";

          try {
            const datos = await respuesta.json();

            mensaje = datos.error || mensaje;
          } catch {}

          throw new Error(mensaje);
        }
      }

      cerrarModalCancelar();

      await obtenerMisTurnos();
    } catch (error) {
      console.error(error);

      mostrarAlertaCancelar(error.message || "No se pudo cancelar el turno.");
    } finally {
      btnCancelarSi.disabled = false;

      btnCancelarSi.textContent = "Cancelar turno";
    }
  });

  function mostrarAlertaCancelar(mensaje) {
    alertaCancelar.textContent = mensaje;

    alertaCancelar.classList.remove("d-none");
  }

  function limpiarAlertaCancelar() {
    alertaCancelar.textContent = "";

    alertaCancelar.classList.add("d-none");
  }

  /* CALIFICAR */

  function conectarBotonesCalificar() {
    document.querySelectorAll(".btn-calificar-turno").forEach((boton) => {
      boton.addEventListener("click", () => {
        abrirModalCalificar(boton.dataset.id);
      });
    });
  }

  function abrirModalCalificar(id) {
    const turno = turnosActuales.find((item) => String(item.id) === String(id));

    if (!turno) {
      return;
    }

    turnoPendienteCalificar = turno;

    puntuacionSeleccionada = 0;

    comentarioCalificacion.value = "";

    limpiarAlertaCalificar();

    actualizarEstrellas();

    textoPuntuacion.textContent = "Seleccioná de 1 a 5 estrellas.";

    detalleTurnoCalificar.textContent = `${turno.barberia} · ${turno.servicio} · ${formatearFecha(turno.fecha)}`;

    modalCalificar.show();
  }

  function seleccionarPuntuacion(puntuacion) {
    puntuacionSeleccionada = puntuacion;

    textoPuntuacion.textContent = `${puntuacion} ${
      puntuacion === 1 ? "estrella" : "estrellas"
    }`;

    actualizarEstrellas();
  }

  function actualizarEstrellas() {
    estrellas.forEach((boton) => {
      const valor = Number(boton.dataset.puntuacion);

      const icono = boton.querySelector("i");

      const seleccionada = valor <= puntuacionSeleccionada;

      boton.classList.toggle("text-warning", seleccionada);

      boton.classList.toggle("text-body-secondary", !seleccionada);

      icono.className = seleccionada ? "bi bi-star-fill" : "bi bi-star";
    });
  }

  estrellas.forEach((boton) => {
    boton.addEventListener("click", () => {
      seleccionarPuntuacion(Number(boton.dataset.puntuacion));
    });
  });

  btnEnviarCalificacion.addEventListener("click", async () => {
    if (!turnoPendienteCalificar) {
      return;
    }

    if (puntuacionSeleccionada < 1 || puntuacionSeleccionada > 5) {
      mostrarAlertaCalificar("Seleccioná una puntuación de 1 a 5 estrellas.");

      return;
    }

    const comentario = comentarioCalificacion.value.trim();

    if (comentario.length > 1000) {
      mostrarAlertaCalificar(
        "El comentario no puede superar los 1000 caracteres.",
      );

      return;
    }

    btnEnviarCalificacion.disabled = true;

    btnEnviarCalificacion.innerHTML = `
          <span
            class="spinner-border spinner-border-sm me-2"
          ></span>

          Enviando...
        `;

    limpiarAlertaCalificar();

    try {
      const respuesta = await fetch(
        API_MISTURNOS.calificar(turnoPendienteCalificar.id),
        {
          method: "POST",

          headers: {
            "Content-Type": "application/json",

            "X-CSRFToken": getCookie("csrftoken"),
          },

          body: JSON.stringify({
            puntuacion: puntuacionSeleccionada,

            comentario: comentario || null,
          }),
        },
      );

      let datos = {};

      try {
        datos = await respuesta.json();
      } catch {}

      if (!respuesta.ok || datos.ok === false) {
        throw new Error(datos.error || "No se pudo guardar la calificación.");
      }

      modalCalificar.hide();

      mostrarExitoCalificacion("Calificación enviada correctamente.");

      turnoPendienteCalificar = null;

      puntuacionSeleccionada = 0;

      await obtenerMisTurnos();
    } catch (error) {
      console.error(error);

      mostrarAlertaCalificar(
        error.message || "No se pudo guardar la calificación.",
      );
    } finally {
      btnEnviarCalificacion.disabled = false;

      btnEnviarCalificacion.innerHTML = `
            <i
              class="bi bi-star me-1"
            ></i>
            Enviar calificación
          `;
    }
  });

  modalCalificarElemento.addEventListener("hidden.bs.modal", () => {
    turnoPendienteCalificar = null;

    puntuacionSeleccionada = 0;

    comentarioCalificacion.value = "";

    limpiarAlertaCalificar();

    actualizarEstrellas();
  });

  function mostrarAlertaCalificar(mensaje) {
    alertaCalificar.textContent = mensaje;

    alertaCalificar.classList.remove("d-none");
  }

  function limpiarAlertaCalificar() {
    alertaCalificar.textContent = "";

    alertaCalificar.classList.add("d-none");
  }

  function mostrarExitoCalificacion(mensaje) {
    alertaCalificacionGlobal.textContent = mensaje;

    alertaCalificacionGlobal.classList.remove("d-none");

    window.scrollTo({
      top: 0,
      behavior: "smooth",
    });

    setTimeout(() => {
      alertaCalificacionGlobal.classList.add("d-none");
    }, 4000);
  }

  /* INICIO */

  obtenerMisTurnos();
})();
