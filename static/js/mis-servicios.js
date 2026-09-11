(() => {
  /* ═══════════════════════════════════════════════════════════
     mis-servicios.js

     CRUD de servicios del panel del dueño.

     GET    /api/servicios/
     POST   /api/servicios/
     PUT    /api/servicios/<id>/
  ═══════════════════════════════════════════════════════════ */

  const API_SERVICIOS = "/api/servicios/";

  let serviciosActuales = [];

  let cambioEstadoPendiente = null;

  /* ═══════════════════════════════════════════════════════════
     REFERENCIAS
  ═══════════════════════════════════════════════════════════ */

  const lista = document.getElementById("lista-mis-servicios");

  const estadoServicios = document.getElementById("estado-servicios");

  const contenedorTabla = document.getElementById("contenedor-tabla-servicios");

  const cantidadServicios = document.getElementById("cantidad-servicios");

  const alertaGeneral = document.getElementById("alerta-servicios");

  /* FORM */

  const formulario = document.getElementById("form-servicio");

  const inputId = document.getElementById("sv-id-editando");

  const inputNombre = document.getElementById("sv-nombre");

  const inputPrecio = document.getElementById("sv-precio");

  const inputDuracion = document.getElementById("sv-duracion");

  const inputDescripcion = document.getElementById("sv-descripcion");

  const alertaForm = document.getElementById("alerta-form-servicio");

  const btnGuardar = document.getElementById("btn-guardar-servicio");

  const btnNuevo = document.getElementById("btn-nuevo-servicio");

  const modalTitulo = document.getElementById("modal-servicio-titulo");

  const modalSubtitulo = document.getElementById("modal-servicio-subtitulo");

  /* ESTADO */

  const textoEstado = document.getElementById(
    "texto-confirmar-estado-servicio",
  );

  const alertaEstado = document.getElementById("alerta-estado-servicio");

  const btnConfirmarEstado = document.getElementById(
    "btn-confirmar-estado-servicio",
  );

  /* ═══════════════════════════════════════════════════════════
     MODALES
  ═══════════════════════════════════════════════════════════ */

  const modalServicio = bootstrap.Modal.getOrCreateInstance(
    document.getElementById("modal-servicio"),
  );

  const modalEstado = bootstrap.Modal.getOrCreateInstance(
    document.getElementById("modal-estado-servicio"),
  );

  /* ═══════════════════════════════════════════════════════════
     ALERTAS
  ═══════════════════════════════════════════════════════════ */

  function mostrarAlerta(elemento, mensaje, tipo) {
    elemento.textContent = mensaje;

    elemento.className = `alert alert-${tipo}`;

    elemento.classList.remove("d-none");
  }

  function limpiarAlerta(elemento) {
    elemento.textContent = "";

    elemento.className = "alert d-none";
  }

  /* ═══════════════════════════════════════════════════════════
     CARGAR SERVICIOS
  ═══════════════════════════════════════════════════════════ */

  async function cargarServicios() {
    mostrarCarga();

    try {
      const respuesta = await fetch(API_SERVICIOS);

      const datos = await respuesta.json();

      if (!respuesta.ok || !datos.ok) {
        mostrarErrorListado(
          datos.error || "No se pudieron cargar los servicios.",
        );

        return;
      }

      serviciosActuales = datos.servicios || [];

      renderizarServicios();
    } catch (error) {
      console.error(error);

      mostrarErrorListado("Ocurrió un error al cargar los servicios.");
    }
  }

  /* ═══════════════════════════════════════════════════════════
     CARGA
  ═══════════════════════════════════════════════════════════ */

  function mostrarCarga() {
    cantidadServicios.textContent = "0";

    contenedorTabla.classList.add("d-none");

    estadoServicios.classList.remove("d-none");

    estadoServicios.innerHTML = `

      <div
        class="d-flex align-items-center gap-2 text-body-secondary"
      >

        <div
          class="spinner-border spinner-border-sm"
          role="status"
        ></div>

        <span>
          Cargando servicios...
        </span>

      </div>

    `;
  }

  function mostrarErrorListado(mensaje) {
    cantidadServicios.textContent = "0";

    contenedorTabla.classList.add("d-none");

    estadoServicios.classList.remove("d-none");

    estadoServicios.innerHTML = `

      <div
        class="alert alert-danger mb-0"
      >
        ${mensaje}
      </div>

    `;
  }

  /* ═══════════════════════════════════════════════════════════
     RENDER
  ═══════════════════════════════════════════════════════════ */

  function renderizarServicios() {
    cantidadServicios.textContent = serviciosActuales.length;

    lista.innerHTML = "";

    if (serviciosActuales.length === 0) {
      contenedorTabla.classList.add("d-none");

      estadoServicios.classList.remove("d-none");

      estadoServicios.innerHTML = `

        <div class="text-center py-5">

          <i
            class="bi bi-scissors fs-1 text-body-secondary"
          ></i>


          <h3 class="h5 mt-3">
            Todavía no cargaste servicios
          </h3>


          <p
            class="text-body-secondary mb-3"
          >
            Agregá el primer servicio de tu barbería.
          </p>


          <button
            type="button"
            class="btn btn-primary"
            id="btn-primer-servicio"
          >

            <i
              class="bi bi-plus-lg me-1"
            ></i>

            Agregar servicio

          </button>

        </div>

      `;

      document
        .getElementById("btn-primer-servicio")
        .addEventListener("click", abrirNuevoServicio);

      return;
    }

    estadoServicios.classList.add("d-none");

    contenedorTabla.classList.remove("d-none");

    lista.innerHTML = serviciosActuales
      .map((servicio) => crearFilaServicio(servicio))
      .join("");

    conectarEventosTabla();
  }

  /* ═══════════════════════════════════════════════════════════
     FILA
  ═══════════════════════════════════════════════════════════ */

  function crearFilaServicio(servicio) {
    const activo = Number(servicio.estado) === 1;

    const precio = Number(servicio.precio).toLocaleString("es-AR", {
      minimumFractionDigits: 0,

      maximumFractionDigits: 2,
    });

    return `

      <tr>


        <!-- SERVICIO -->
        <td class="ps-4">

          <div>

            <div class="fw-semibold">

              ${servicio.nombre}

            </div>


            ${
              servicio.descripcion
                ? `

                  <div
                    class="small text-body-secondary"
                  >
                    ${servicio.descripcion}
                  </div>

                `
                : ""
            }

          </div>

        </td>



        <!-- PRECIO -->
        <td>

          <span class="fw-semibold">

            $${precio}

          </span>

        </td>



        <!-- DURACIÓN -->
        <td>

          ${servicio.duracion_minutos} min

        </td>



        <!-- ESTADO -->
        <td>

          <span
            class="badge ${activo ? "text-bg-success" : "text-bg-secondary"}"
          >

            ${activo ? "Activo" : "Inactivo"}

          </span>

        </td>



        <!-- ACCIONES -->
        <td class="text-end pe-4">

          <div class="dropdown">

            <button
              type="button"
              class="btn btn-sm btn-outline-secondary dropdown-toggle"
              data-bs-toggle="dropdown"
              aria-expanded="false"
            >
              Acciones
            </button>


            <ul
              class="dropdown-menu dropdown-menu-end"
            >


              <li>

                <button
                  type="button"
                  class="dropdown-item btn-editar-servicio"
                  data-id="${servicio.id_servicio}"
                >

                  <i
                    class="bi bi-pencil me-2"
                  ></i>

                  Editar

                </button>

              </li>



              <li>

                <hr class="dropdown-divider">

              </li>



              <li>

                <button
                  type="button"
                  class="dropdown-item ${
                    activo ? "text-danger" : ""
                  } btn-estado-servicio"
                  data-id="${servicio.id_servicio}"
                  data-estado="${servicio.estado}"
                >

                  <i
                    class="bi ${
                      activo ? "bi-x-circle" : "bi-check-circle"
                    } me-2"
                  ></i>

                  ${activo ? "Dar de baja" : "Reactivar"}

                </button>

              </li>

            </ul>

          </div>

        </td>


      </tr>

    `;
  }

  /* ═══════════════════════════════════════════════════════════
     EVENTOS TABLA
  ═══════════════════════════════════════════════════════════ */

  function conectarEventosTabla() {
    lista.querySelectorAll(".btn-editar-servicio").forEach((boton) => {
      boton.addEventListener(
        "click",

        () => {
          abrirEdicionServicio(boton.dataset.id);
        },
      );
    });

    lista.querySelectorAll(".btn-estado-servicio").forEach((boton) => {
      boton.addEventListener(
        "click",

        () => {
          abrirEstadoServicio(
            boton.dataset.id,

            boton.dataset.estado,
          );
        },
      );
    });
  }

  /* ═══════════════════════════════════════════════════════════
     NUEVO
  ═══════════════════════════════════════════════════════════ */

  function abrirNuevoServicio() {
    limpiarFormulario();

    modalTitulo.textContent = "Agregar servicio";

    modalSubtitulo.textContent = "Completá los datos del nuevo servicio.";

    btnGuardar.textContent = "Agregar servicio";

    modalServicio.show();
  }

  btnNuevo.addEventListener("click", abrirNuevoServicio);

  /* ═══════════════════════════════════════════════════════════
     EDITAR
  ═══════════════════════════════════════════════════════════ */

  function abrirEdicionServicio(id) {
    const servicio = serviciosActuales.find(
      (item) => String(item.id_servicio) === String(id),
    );

    if (!servicio) {
      return;
    }

    limpiarFormulario();

    inputId.value = servicio.id_servicio;

    inputNombre.value = servicio.nombre || "";

    inputPrecio.value = servicio.precio ?? "";

    inputDuracion.value = servicio.duracion_minutos ?? "";

    inputDescripcion.value = servicio.descripcion || "";

    modalTitulo.textContent = "Editar servicio";

    modalSubtitulo.textContent =
      "Modificá los datos del servicio seleccionado.";

    btnGuardar.textContent = "Guardar cambios";

    modalServicio.show();
  }

  /* ═══════════════════════════════════════════════════════════
     LIMPIAR FORM
  ═══════════════════════════════════════════════════════════ */

  function limpiarFormulario() {
    formulario.reset();

    inputId.value = "";

    limpiarAlerta(alertaForm);
  }

  /* ═══════════════════════════════════════════════════════════
     GUARDAR
  ═══════════════════════════════════════════════════════════ */

  formulario.addEventListener(
    "submit",

    async (event) => {
      event.preventDefault();

      limpiarAlerta(alertaForm);

      const idEditando = inputId.value;

      const esEdicion = Boolean(idEditando);

      const nombre = inputNombre.value.trim();

      const precio = inputPrecio.value;

      const duracionMinutos = inputDuracion.value;

      const descripcion = inputDescripcion.value.trim();

      if (!nombre || !precio || !duracionMinutos) {
        mostrarAlerta(
          alertaForm,

          "Nombre, precio y duración son obligatorios.",

          "warning",
        );

        return;
      }

      if (Number(precio) < 0) {
        mostrarAlerta(
          alertaForm,

          "El precio no puede ser negativo.",

          "warning",
        );

        return;
      }

      if (Number(duracionMinutos) < 5) {
        mostrarAlerta(
          alertaForm,

          "La duración mínima es de 5 minutos.",

          "warning",
        );

        return;
      }

      btnGuardar.disabled = true;

      btnGuardar.innerHTML = `

        <span
          class="spinner-border spinner-border-sm me-2"
          aria-hidden="true"
        ></span>

        ${esEdicion ? "Guardando..." : "Agregando..."}

      `;

      try {
        const url = esEdicion
          ? `${API_SERVICIOS}${idEditando}/`
          : API_SERVICIOS;

        const metodo = esEdicion ? "PUT" : "POST";

        const respuesta = await fetch(url, {
          method: metodo,

          headers: {
            "Content-Type": "application/json",

            "X-CSRFToken": getCookie("csrftoken"),
          },

          body: JSON.stringify({
            nombre,

            precio,

            duracion_minutos: duracionMinutos,

            descripcion,
          }),
        });

        const datos = await respuesta.json();

        if (!respuesta.ok || !datos.ok) {
          mostrarAlerta(
            alertaForm,

            datos.error || "No se pudo guardar el servicio.",

            "danger",
          );

          return;
        }

        modalServicio.hide();

        mostrarAlerta(
          alertaGeneral,

          esEdicion
            ? "El servicio se actualizó correctamente."
            : "El servicio fue agregado correctamente.",

          "success",
        );

        await cargarServicios();
      } catch (error) {
        console.error(error);

        mostrarAlerta(
          alertaForm,

          "No se pudo conectar con el servidor.",

          "danger",
        );
      } finally {
        btnGuardar.disabled = false;

        btnGuardar.textContent = esEdicion
          ? "Guardar cambios"
          : "Agregar servicio";
      }
    },
  );

  /* ═══════════════════════════════════════════════════════════
     ESTADO
  ═══════════════════════════════════════════════════════════ */

  function abrirEstadoServicio(id, estadoActual) {
    const servicio = serviciosActuales.find(
      (item) => String(item.id_servicio) === String(id),
    );

    if (!servicio) {
      return;
    }

    const estaActivo = Number(estadoActual) === 1;

    cambioEstadoPendiente = {
      id,

      estadoActual: Number(estadoActual),
    };

    limpiarAlerta(alertaEstado);

    document.getElementById("modal-estado-servicio-titulo").textContent =
      estaActivo ? "Dar de baja servicio" : "Reactivar servicio";

    textoEstado.textContent = estaActivo
      ? `¿Querés dar de baja "${servicio.nombre}"?`
      : `¿Querés reactivar "${servicio.nombre}"?`;

    btnConfirmarEstado.textContent = estaActivo ? "Dar de baja" : "Reactivar";

    btnConfirmarEstado.className = estaActivo
      ? "btn btn-danger"
      : "btn btn-primary";

    modalEstado.show();
  }

  /* ═══════════════════════════════════════════════════════════
     CONFIRMAR ESTADO
  ═══════════════════════════════════════════════════════════ */

  btnConfirmarEstado.addEventListener(
    "click",

    async () => {
      if (!cambioEstadoPendiente) {
        return;
      }

      const { id, estadoActual } = cambioEstadoPendiente;

      const nuevoEstado = estadoActual === 1 ? 0 : 1;

      const textoOriginal = btnConfirmarEstado.textContent;

      btnConfirmarEstado.disabled = true;

      btnConfirmarEstado.innerHTML = `

        <span
          class="spinner-border spinner-border-sm me-2"
          aria-hidden="true"
        ></span>

        Procesando...

      `;

      try {
        const respuesta = await fetch(
          `${API_SERVICIOS}${id}/`,

          {
            method: "PUT",

            headers: {
              "Content-Type": "application/json",

              "X-CSRFToken": getCookie("csrftoken"),
            },

            body: JSON.stringify({
              estado: nuevoEstado,
            }),
          },
        );

        const datos = await respuesta.json();

        if (!respuesta.ok || !datos.ok) {
          mostrarAlerta(
            alertaEstado,

            datos.error || "No se pudo cambiar el estado.",

            "danger",
          );

          return;
        }

        modalEstado.hide();

        mostrarAlerta(
          alertaGeneral,

          nuevoEstado === 1
            ? "El servicio fue reactivado correctamente."
            : "El servicio fue dado de baja correctamente.",

          "success",
        );

        cambioEstadoPendiente = null;

        await cargarServicios();
      } catch (error) {
        console.error(error);

        mostrarAlerta(
          alertaEstado,

          "No se pudo conectar con el servidor.",

          "danger",
        );
      } finally {
        btnConfirmarEstado.disabled = false;

        btnConfirmarEstado.textContent = textoOriginal;
      }
    },
  );

  /* ═══════════════════════════════════════════════════════════
     LIMPIEZA MODALES
  ═══════════════════════════════════════════════════════════ */

  document.getElementById("modal-servicio").addEventListener(
    "hidden.bs.modal",

    () => {
      limpiarFormulario();
    },
  );

  document.getElementById("modal-estado-servicio").addEventListener(
    "hidden.bs.modal",

    () => {
      cambioEstadoPendiente = null;

      limpiarAlerta(alertaEstado);
    },
  );

  /* ═══════════════════════════════════════════════════════════
     INICIO
  ═══════════════════════════════════════════════════════════ */

  cargarServicios();
})();
