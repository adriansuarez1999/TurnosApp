(() => {
  /* ═══════════════════════════════════════════════════════════
     clientes.js

     Sprint 4 - Módulo B

     GET
     /api/mi-barberia/clientes/

     PATCH
     /api/mi-barberia/clientes/<id>/bloquear/

     PATCH
     /api/mi-barberia/clientes/<id>/desbloquear/
  ═══════════════════════════════════════════════════════════ */

  const API_CLIENTES = "/api/mi-barberia/clientes/";

  let clientesActuales = [];

  let accionPendiente = null;

  /* ═══════════════════════════════════════════════════════════
     REFERENCIAS
  ═══════════════════════════════════════════════════════════ */

  const alertaGeneral = document.getElementById("alerta-clientes");

  const estadoClientes = document.getElementById("estado-clientes");

  const contenedorTabla = document.getElementById("contenedor-tabla-clientes");

  const listaClientes = document.getElementById("lista-clientes");

  const cantidadClientes = document.getElementById("cantidad-clientes");

  const statTotal = document.getElementById("stat-total-clientes");

  const statAusencias = document.getElementById("stat-clientes-ausencias");

  const statBloqueados = document.getElementById("stat-clientes-bloqueados");

  /* MODAL */

  const tituloModal = document.getElementById("modal-estado-cliente-titulo");

  const textoConfirmacion = document.getElementById(
    "texto-confirmacion-cliente",
  );

  const avisoBloqueo = document.getElementById("aviso-bloqueo-global");

  const alertaModal = document.getElementById("alerta-estado-cliente");

  const btnConfirmar = document.getElementById("btn-confirmar-estado-cliente");

  const modalEstado = bootstrap.Modal.getOrCreateInstance(
    document.getElementById("modal-estado-cliente"),
  );

  /* ═══════════════════════════════════════════════════════════
     ALERTAS
  ═══════════════════════════════════════════════════════════ */

  function mostrarAlerta(elemento, mensaje, tipo = "danger") {
    elemento.textContent = mensaje;

    elemento.className = `alert alert-${tipo}`;

    elemento.classList.remove("d-none");
  }

  function limpiarAlerta(elemento) {
    elemento.textContent = "";

    elemento.className = "alert d-none";
  }

  /* ═══════════════════════════════════════════════════════════
     SEGURIDAD HTML
  ═══════════════════════════════════════════════════════════ */

  function escaparHtml(valor) {
    if (valor === null || valor === undefined) {
      return "";
    }

    return String(valor)
      .replaceAll("&", "&amp;")
      .replaceAll("<", "&lt;")
      .replaceAll(">", "&gt;")
      .replaceAll('"', "&quot;")
      .replaceAll("'", "&#039;");
  }

  /* ═══════════════════════════════════════════════════════════
     CARGAR CLIENTES
  ═══════════════════════════════════════════════════════════ */

  async function cargarClientes() {
    limpiarAlerta(alertaGeneral);

    mostrarCarga();

    try {
      const respuesta = await fetch(API_CLIENTES);

      const datos = await respuesta.json();

      if (!respuesta.ok || !datos.ok) {
        mostrarError(datos.error || "No se pudieron cargar los clientes.");

        return;
      }

      clientesActuales = datos.clientes || [];

      renderizarClientes();
    } catch (error) {
      console.error(error);

      mostrarError("No se pudo conectar con el servidor.");
    }
  }

  /* ═══════════════════════════════════════════════════════════
     ESTADOS DE PANTALLA
  ═══════════════════════════════════════════════════════════ */

  function mostrarCarga() {
    contenedorTabla.classList.add("d-none");

    estadoClientes.classList.remove("d-none");

    estadoClientes.innerHTML = `
      <div
        class="d-flex justify-content-center align-items-center gap-2 text-body-secondary"
      >

        <div
          class="spinner-border spinner-border-sm"
          role="status"
        ></div>

        <span>
          Cargando clientes...
        </span>

      </div>
    `;
  }

  function mostrarError(mensaje) {
    contenedorTabla.classList.add("d-none");

    estadoClientes.classList.remove("d-none");

    estadoClientes.innerHTML = `
      <div
        class="alert alert-danger mb-0"
        role="alert"
      >
        ${escaparHtml(mensaje)}
      </div>
    `;
  }

  /* ═══════════════════════════════════════════════════════════
     RENDER
  ═══════════════════════════════════════════════════════════ */

  function renderizarClientes() {
    actualizarResumen();

    listaClientes.innerHTML = "";

    if (clientesActuales.length === 0) {
      contenedorTabla.classList.add("d-none");

      estadoClientes.classList.remove("d-none");

      estadoClientes.innerHTML = `
        <div class="text-center py-4">

          <i
            class="bi bi-people fs-1 text-body-secondary"
          ></i>

          <h3 class="h5 mt-3">
            Todavía no hay clientes
          </h3>

          <p
            class="text-body-secondary mb-0"
          >
            Los usuarios aparecerán acá cuando realicen
            una reserva en tu barbería.
          </p>

        </div>
      `;

      return;
    }

    estadoClientes.classList.add("d-none");

    contenedorTabla.classList.remove("d-none");

    listaClientes.innerHTML = clientesActuales
      .map((cliente) => crearFilaCliente(cliente))
      .join("");

    conectarEventos();
  }

  /* ═══════════════════════════════════════════════════════════
     RESUMEN
  ═══════════════════════════════════════════════════════════ */

  function actualizarResumen() {
    const total = clientesActuales.length;

    const conAusencias = clientesActuales.filter(
      (cliente) => Number(cliente.ausencias) > 0,
    ).length;

    const bloqueados = clientesActuales.filter(
      (cliente) => cliente.estado === "BLOQUEADO",
    ).length;

    statTotal.textContent = total;

    statAusencias.textContent = conAusencias;

    statBloqueados.textContent = bloqueados;

    cantidadClientes.textContent =
      total === 1 ? "1 cliente" : `${total} clientes`;
  }

  /* ═══════════════════════════════════════════════════════════
     FILA CLIENTE
  ═══════════════════════════════════════════════════════════ */

  function crearFilaCliente(cliente) {
    const bloqueado = cliente.estado === "BLOQUEADO";

    const inactivo = cliente.estado === "INACTIVO";

    const ausencias = Number(cliente.ausencias) || 0;

    const totalTurnos = Number(cliente.total_turnos) || 0;

    let badgeEstado = "text-bg-success";

    let textoEstado = "Activo";

    if (bloqueado) {
      badgeEstado = "text-bg-danger";

      textoEstado = "Bloqueado";
    } else if (inactivo) {
      badgeEstado = "text-bg-secondary";

      textoEstado = "Inactivo";
    }

    let badgeAusencias = "text-bg-light border text-body";

    if (ausencias > 0) {
      badgeAusencias = "text-bg-warning";
    }

    const telefono = cliente.telefono
      ? escaparHtml(cliente.telefono)
      : "Sin teléfono";

    const email = cliente.email ? escaparHtml(cliente.email) : "Sin email";

    return `
      <tr>

        <!-- CLIENTE -->
        <td class="ps-4">

          <div
            class="d-flex align-items-center gap-3"
          >

            <div
              class="rounded-circle bg-primary-subtle text-primary-emphasis d-flex align-items-center justify-content-center flex-shrink-0"
              style="
                width: 40px;
                height: 40px;
              "
            >

              <i class="bi bi-person"></i>

            </div>


            <div>

              <div class="fw-semibold">

                ${escaparHtml(cliente.nombre)}

                ${escaparHtml(cliente.apellido)}

              </div>


              <div
                class="small text-body-secondary"
              >
                ID ${cliente.id_usuario}
              </div>

            </div>

          </div>

        </td>


        <!-- CONTACTO -->
        <td>

          <div class="small">

            <div>

              <i
                class="bi bi-envelope me-1 text-body-secondary"
              ></i>

              ${email}

            </div>


            <div
              class="text-body-secondary mt-1"
            >

              <i
                class="bi bi-telephone me-1"
              ></i>

              ${telefono}

            </div>

          </div>

        </td>


        <!-- TOTAL TURNOS -->
        <td class="text-center">

          <span
            class="badge text-bg-light border text-body"
          >
            ${totalTurnos}
          </span>

        </td>


        <!-- AUSENCIAS -->
        <td class="text-center">

          <span
            class="badge ${badgeAusencias}"
          >

            ${ausencias}

          </span>

        </td>


        <!-- ESTADO -->
        <td>

          <span
            class="badge ${badgeEstado}"
          >

            ${textoEstado}

          </span>

        </td>


        <!-- ACCIONES -->
        <td class="text-end pe-4">

          ${
            inactivo
              ? `
                <button
                  type="button"
                  class="btn btn-sm btn-outline-secondary"
                  disabled
                >

                  No disponible

                </button>
              `
              : `
                <button
                  type="button"
                  class="btn btn-sm ${
                    bloqueado ? "btn-outline-success" : "btn-outline-danger"
                  } btn-estado-cliente"
                  data-id="${cliente.id_usuario}"
                >

                  <i
                    class="bi ${bloqueado ? "bi-unlock" : "bi-lock"} me-1"
                  ></i>

                  ${bloqueado ? "Desbloquear" : "Bloquear"}

                </button>
              `
          }

        </td>

      </tr>
    `;
  }

  /* ═══════════════════════════════════════════════════════════
     EVENTOS DE TABLA
  ═══════════════════════════════════════════════════════════ */

  function conectarEventos() {
    document.querySelectorAll(".btn-estado-cliente").forEach((boton) => {
      boton.addEventListener("click", () => {
        abrirConfirmacion(Number(boton.dataset.id));
      });
    });
  }

  /* ═══════════════════════════════════════════════════════════
     MODAL CONFIRMACIÓN
  ═══════════════════════════════════════════════════════════ */

  function abrirConfirmacion(id) {
    const cliente = clientesActuales.find(
      (item) => Number(item.id_usuario) === Number(id),
    );

    if (!cliente) {
      return;
    }

    const bloqueado = cliente.estado === "BLOQUEADO";

    accionPendiente = {
      id: cliente.id_usuario,

      accion: bloqueado ? "desbloquear" : "bloquear",
    };

    limpiarAlerta(alertaModal);

    const nombreCompleto = `${cliente.nombre} ${cliente.apellido}`;

    if (bloqueado) {
      tituloModal.textContent = "Desbloquear cliente";

      textoConfirmacion.textContent = `¿Querés desbloquear a ${nombreCompleto}? El cliente podrá volver a realizar reservas.`;

      avisoBloqueo.classList.add("d-none");

      btnConfirmar.className = "btn btn-success";

      btnConfirmar.textContent = "Desbloquear";
    } else {
      tituloModal.textContent = "Bloquear cliente";

      textoConfirmacion.textContent = `¿Querés bloquear a ${nombreCompleto}?`;

      avisoBloqueo.classList.remove("d-none");

      btnConfirmar.className = "btn btn-danger";

      btnConfirmar.textContent = "Bloquear";
    }

    modalEstado.show();
  }

  /* ═══════════════════════════════════════════════════════════
     EJECUTAR BLOQUEO / DESBLOQUEO
  ═══════════════════════════════════════════════════════════ */

  async function cambiarEstadoCliente() {
    if (!accionPendiente) {
      return;
    }

    const { id, accion } = accionPendiente;

    const textoOriginal = btnConfirmar.textContent;

    btnConfirmar.disabled = true;

    btnConfirmar.innerHTML = `
      <span
        class="spinner-border spinner-border-sm me-2"
        aria-hidden="true"
      ></span>

      Procesando...
    `;

    try {
      const respuesta = await fetch(
        `/api/mi-barberia/clientes/${id}/${accion}/`,
        {
          method: "PATCH",

          headers: {
            "X-CSRFToken": getCookie("csrftoken"),
          },
        },
      );

      const datos = await respuesta.json();

      if (!respuesta.ok || !datos.ok) {
        mostrarAlerta(
          alertaModal,
          datos.error || "No se pudo modificar el estado del cliente.",
          "danger",
        );

        return;
      }

      modalEstado.hide();

      mostrarAlerta(
        alertaGeneral,
        accion === "bloquear"
          ? "El cliente fue bloqueado correctamente."
          : "El cliente fue desbloqueado correctamente.",
        "success",
      );

      accionPendiente = null;

      await cargarClientes();
    } catch (error) {
      console.error(error);

      mostrarAlerta(
        alertaModal,
        "No se pudo conectar con el servidor.",
        "danger",
      );
    } finally {
      btnConfirmar.disabled = false;

      btnConfirmar.textContent = textoOriginal;
    }
  }

  /* ═══════════════════════════════════════════════════════════
     EVENTOS
  ═══════════════════════════════════════════════════════════ */

  btnConfirmar.addEventListener("click", cambiarEstadoCliente);

  document
    .getElementById("modal-estado-cliente")
    .addEventListener("hidden.bs.modal", () => {
      accionPendiente = null;

      limpiarAlerta(alertaModal);
    });

  /* ═══════════════════════════════════════════════════════════
     INICIO
  ═══════════════════════════════════════════════════════════ */

  cargarClientes();
})();
