(() => {
  const API_PROMOCIONES = "/api/promociones/";

  const API_SERVICIOS = "/api/servicios/";

  function getCookie(nombre) {
    let cookieValue = null;

    if (document.cookie && document.cookie !== "") {
      const cookies = document.cookie.split(";");

      for (let i = 0; i < cookies.length; i += 1) {
        const cookie = cookies[i].trim();

        if (cookie.substring(0, nombre.length + 1) === `${nombre}=`) {
          cookieValue = decodeURIComponent(cookie.substring(nombre.length + 1));

          break;
        }
      }
    }

    return cookieValue;
  }

  let promociones = [];

  let servicios = [];

  let idPromocionEliminar = null;

  const alertaPromociones = document.getElementById("alerta-promociones");

  const estadoPromociones = document.getElementById("estado-promociones");

  const contenedorPromociones = document.getElementById(
    "contenedor-promociones",
  );

  const tablaPromociones = document.getElementById("tabla-promociones");

  const btnNuevaPromocion = document.getElementById("btn-nueva-promocion");

  const btnRecargarPromociones = document.getElementById(
    "btn-recargar-promociones",
  );

  const formPromocion = document.getElementById("form-promocion");

  const promocionId = document.getElementById("promocion-id");

  const promocionNombre = document.getElementById("promocion-nombre");

  const promocionServicio = document.getElementById("promocion-servicio");

  const promocionPorcentaje = document.getElementById("promocion-porcentaje");

  const promocionFechaInicio = document.getElementById(
    "promocion-fecha-inicio",
  );

  const promocionFechaFin = document.getElementById("promocion-fecha-fin");

  const promocionActiva = document.getElementById("promocion-activa");

  const tituloModalPromocion = document.getElementById(
    "titulo-modal-promocion",
  );

  const errorFormPromocion = document.getElementById("error-form-promocion");

  const btnGuardarPromocion = document.getElementById("btn-guardar-promocion");

  const textoGuardarPromocion = document.getElementById(
    "texto-guardar-promocion",
  );

  const spinnerGuardarPromocion = document.getElementById(
    "spinner-guardar-promocion",
  );

  const nombrePromocionEliminar = document.getElementById(
    "nombre-promocion-eliminar",
  );

  const errorEliminarPromocion = document.getElementById(
    "error-eliminar-promocion",
  );

  const btnConfirmarEliminar = document.getElementById(
    "btn-confirmar-eliminar-promocion",
  );

  const modalPromocion = new bootstrap.Modal(
    document.getElementById("modal-promocion"),
  );

  const modalEliminar = new bootstrap.Modal(
    document.getElementById("modal-eliminar-promocion"),
  );

  function escaparHTML(valor) {
    const div = document.createElement("div");

    div.textContent = valor ?? "";

    return div.innerHTML;
  }

  function mostrarAlerta(mensaje, tipo = "success") {
    alertaPromociones.className = `alert alert-${tipo}`;

    alertaPromociones.textContent = mensaje;

    alertaPromociones.classList.remove("d-none");
  }

  function ocultarAlerta() {
    alertaPromociones.className = "alert d-none";

    alertaPromociones.textContent = "";
  }

  async function obtenerJson(respuesta) {
    try {
      return await respuesta.json();
    } catch {
      return {};
    }
  }

  function formatearFecha(fecha) {
    if (!fecha) {
      return "—";
    }

    const [anio, mes, dia] = fecha.split("-");

    return `${dia}/${mes}/${anio}`;
  }

  function estadoPromocion(promocion) {
    if (Number(promocion.activa) !== 1) {
      return {
        texto: "Inactiva",
        clase: "text-bg-secondary",
      };
    }

    const hoy = new Date();

    hoy.setHours(0, 0, 0, 0);

    const fechaInicio = new Date(`${promocion.fecha_inicio}T00:00:00`);

    const fechaFin = new Date(`${promocion.fecha_fin}T23:59:59`);

    if (hoy < fechaInicio) {
      return {
        texto: "Programada",
        clase: "text-bg-warning",
      };
    }

    if (hoy > fechaFin) {
      return {
        texto: "Vencida",
        clase: "text-bg-danger",
      };
    }

    return {
      texto: "Activa",
      clase: "text-bg-success",
    };
  }

  async function cargarPromociones() {
    ocultarAlerta();

    estadoPromociones.classList.remove("d-none");

    contenedorPromociones.classList.add("d-none");

    estadoPromociones.innerHTML = `
      <div
        class="spinner-border spinner-border-sm me-2"
        role="status"
      ></div>

      <span
        class="text-body-secondary"
      >
        Cargando promociones...
      </span>
    `;

    try {
      const respuesta = await fetch(API_PROMOCIONES);

      const datos = await obtenerJson(respuesta);

      if (!respuesta.ok || !datos.ok) {
        throw new Error(
          datos.error || "No se pudieron cargar las promociones.",
        );
      }

      promociones = datos.promociones || [];

      renderizarPromociones();
    } catch (error) {
      console.error(error);

      estadoPromociones.innerHTML = `
        <div
          class="alert alert-danger mb-0"
        >
          ${escaparHTML(error.message)}
        </div>
      `;
    }
  }

  function renderizarPromociones() {
    estadoPromociones.classList.add("d-none");

    contenedorPromociones.classList.remove("d-none");

    if (promociones.length === 0) {
      contenedorPromociones.innerHTML = `
        <div
          class="text-center py-5"
        >

          <i
            class="bi bi-percent fs-1 text-body-secondary"
          ></i>


          <h3
            class="h5 mt-3"
          >
            Todavía no tenés promociones
          </h3>


          <p
            class="text-body-secondary mb-3"
          >
            Creá una promoción para ofrecer descuentos en tus servicios.
          </p>


          <button
            type="button"
            class="btn btn-primary"
            id="btn-vacio-nueva-promocion"
          >
            <i
              class="bi bi-plus-lg me-1"
            ></i>

            Nueva promoción
          </button>

        </div>
      `;

      document
        .getElementById("btn-vacio-nueva-promocion")
        .addEventListener("click", abrirNuevaPromocion);

      return;
    }

    contenedorPromociones.innerHTML = `
      <div
        class="table-responsive"
      >

        <table
          class="table align-middle mb-0"
        >

          <thead>

            <tr>

              <th>
                Promoción
              </th>

              <th>
                Servicio
              </th>

              <th>
                Descuento
              </th>

              <th>
                Vigencia
              </th>

              <th>
                Estado
              </th>

              <th
                class="text-end"
              >
                Acciones
              </th>

            </tr>

          </thead>


          <tbody
            id="tabla-promociones"
          >
          </tbody>

        </table>

      </div>
    `;

    const tbody = document.getElementById("tabla-promociones");

    tbody.innerHTML = promociones.map(crearFilaPromocion).join("");

    tbody.querySelectorAll("[data-accion='editar']").forEach((boton) => {
      boton.addEventListener("click", () => {
        abrirEditarPromocion(Number(boton.dataset.id));
      });
    });

    tbody.querySelectorAll("[data-accion='eliminar']").forEach((boton) => {
      boton.addEventListener("click", () => {
        abrirEliminarPromocion(Number(boton.dataset.id));
      });
    });
  }

  function crearFilaPromocion(promocion) {
    const estado = estadoPromocion(promocion);

    return `
      <tr>

        <td>

          <div
            class="fw-semibold"
          >
            ${escaparHTML(promocion.nombre)}
          </div>

        </td>


        <td>

          ${escaparHTML(promocion.servicio_nombre)}

        </td>


        <td>

          <span
            class="badge bg-primary-subtle text-primary-emphasis border border-primary-subtle"
          >
            ${Number(promocion.porcentaje_descuento)}%
          </span>

        </td>


        <td>

          <div
            class="small"
          >
            ${formatearFecha(promocion.fecha_inicio)}
          </div>

          <div
            class="small text-body-secondary"
          >
            hasta
            ${formatearFecha(promocion.fecha_fin)}
          </div>

        </td>


        <td>

          <span
            class="badge ${estado.clase}"
          >
            ${estado.texto}
          </span>

        </td>


        <td
          class="text-end"
        >

          <div
            class="btn-group btn-group-sm"
            role="group"
          >

            <button
              type="button"
              class="btn btn-outline-secondary"
              data-accion="editar"
              data-id="${promocion.id_promocion}"
              title="Editar"
            >
              <i
                class="bi bi-pencil"
              ></i>
            </button>


            <button
              type="button"
              class="btn btn-outline-danger"
              data-accion="eliminar"
              data-id="${promocion.id_promocion}"
              title="Eliminar"
            >
              <i
                class="bi bi-trash"
              ></i>
            </button>

          </div>

        </td>

      </tr>
    `;
  }

  async function cargarServicios() {
    try {
      const respuesta = await fetch(API_SERVICIOS);

      const datos = await obtenerJson(respuesta);

      if (!respuesta.ok || !datos.ok) {
        throw new Error(datos.error || "No se pudieron cargar los servicios.");
      }

      servicios = datos.servicios || [];

      renderizarServicios();
    } catch (error) {
      console.error(error);

      promocionServicio.innerHTML = `
        <option value="">
          Error al cargar servicios
        </option>
      `;

      promocionServicio.disabled = true;
    }
  }

  function renderizarServicios() {
    promocionServicio.disabled = false;

    if (servicios.length === 0) {
      promocionServicio.innerHTML = `
        <option value="">
          No hay servicios disponibles
        </option>
      `;

      promocionServicio.disabled = true;

      return;
    }

    promocionServicio.innerHTML = `
      <option value="">
        Seleccionar servicio
      </option>

      ${servicios
        .map(
          (servicio) => `
            <option
              value="${servicio.id_servicio}"
            >
              ${escaparHTML(servicio.nombre)}
            </option>
          `,
        )
        .join("")}
    `;
  }

  function limpiarFormulario() {
    promocionId.value = "";

    promocionNombre.value = "";

    promocionServicio.value = "";

    promocionPorcentaje.value = "";

    promocionFechaInicio.value = "";

    promocionFechaFin.value = "";

    promocionActiva.checked = true;

    ocultarErrorFormulario();
  }

  function abrirNuevaPromocion() {
    limpiarFormulario();

    tituloModalPromocion.textContent = "Nueva promoción";

    textoGuardarPromocion.textContent = "Guardar";

    modalPromocion.show();
  }

  function abrirEditarPromocion(id) {
    const promocion = promociones.find(
      (item) => Number(item.id_promocion) === Number(id),
    );

    if (!promocion) {
      return;
    }

    limpiarFormulario();

    promocionId.value = promocion.id_promocion;

    promocionNombre.value = promocion.nombre || "";

    promocionServicio.value = promocion.id_servicio || "";

    promocionPorcentaje.value = Number(promocion.porcentaje_descuento);

    promocionFechaInicio.value = promocion.fecha_inicio || "";

    promocionFechaFin.value = promocion.fecha_fin || "";

    promocionActiva.checked = Number(promocion.activa) === 1;

    tituloModalPromocion.textContent = "Editar promoción";

    textoGuardarPromocion.textContent = "Guardar cambios";

    modalPromocion.show();
  }

  function mostrarErrorFormulario(mensaje) {
    errorFormPromocion.textContent = mensaje;

    errorFormPromocion.classList.remove("d-none");
  }

  function ocultarErrorFormulario() {
    errorFormPromocion.textContent = "";

    errorFormPromocion.classList.add("d-none");
  }

  function validarFormulario() {
    const nombre = promocionNombre.value.trim();

    const idServicio = promocionServicio.value;

    const porcentaje = Number(promocionPorcentaje.value);

    const fechaInicio = promocionFechaInicio.value;

    const fechaFin = promocionFechaFin.value;

    if (!nombre) {
      return "Ingresá el nombre de la promoción.";
    }

    if (!idServicio) {
      return "Seleccioná un servicio.";
    }

    if (porcentaje < 1 || porcentaje > 100) {
      return "El porcentaje debe estar entre 1 y 100.";
    }

    if (!fechaInicio || !fechaFin) {
      return "Completá las fechas de vigencia.";
    }

    if (fechaFin < fechaInicio) {
      return "La fecha de fin debe ser posterior o igual a la fecha de inicio.";
    }

    return null;
  }

  async function guardarPromocion(evento) {
    evento.preventDefault();

    ocultarErrorFormulario();

    const error = validarFormulario();

    if (error) {
      mostrarErrorFormulario(error);

      return;
    }

    const id = promocionId.value;

    const editando = Boolean(id);

    const payload = {
      id_servicio: Number(promocionServicio.value),

      nombre: promocionNombre.value.trim(),

      porcentaje_descuento: Number(promocionPorcentaje.value),

      fecha_inicio: promocionFechaInicio.value,

      fecha_fin: promocionFechaFin.value,

      activa: promocionActiva.checked ? 1 : 0,
    };

    btnGuardarPromocion.disabled = true;

    spinnerGuardarPromocion.classList.remove("d-none");

    try {
      const url = editando ? `${API_PROMOCIONES}${id}/` : API_PROMOCIONES;

      const metodo = editando ? "PUT" : "POST";

      const respuesta = await fetch(url, {
        method: metodo,

        headers: {
          "Content-Type": "application/json",

          "X-CSRFToken": getCookie("csrftoken"),
        },

        body: JSON.stringify(payload),
      });

      const datos = await obtenerJson(respuesta);

      if (!respuesta.ok || !datos.ok) {
        throw new Error(datos.error || "No se pudo guardar la promoción.");
      }

      modalPromocion.hide();

      mostrarAlerta(
        editando
          ? "Promoción actualizada correctamente."
          : "Promoción creada correctamente.",
        "success",
      );

      await cargarPromociones();
    } catch (error) {
      console.error(error);

      mostrarErrorFormulario(error.message);
    } finally {
      btnGuardarPromocion.disabled = false;

      spinnerGuardarPromocion.classList.add("d-none");
    }
  }

  function abrirEliminarPromocion(id) {
    const promocion = promociones.find(
      (item) => Number(item.id_promocion) === Number(id),
    );

    if (!promocion) {
      return;
    }

    idPromocionEliminar = promocion.id_promocion;

    nombrePromocionEliminar.textContent = promocion.nombre;

    errorEliminarPromocion.textContent = "";

    errorEliminarPromocion.classList.add("d-none");

    modalEliminar.show();
  }

  async function eliminarPromocion() {
    if (!idPromocionEliminar) {
      return;
    }

    btnConfirmarEliminar.disabled = true;

    try {
      const respuesta = await fetch(
        `${API_PROMOCIONES}${idPromocionEliminar}/`,
        {
          method: "DELETE",

          headers: {
            "X-CSRFToken": getCookie("csrftoken"),
          },
        },
      );

      const datos = await obtenerJson(respuesta);

      if (!respuesta.ok || !datos.ok) {
        throw new Error(datos.error || "No se pudo eliminar la promoción.");
      }

      modalEliminar.hide();

      mostrarAlerta("Promoción eliminada correctamente.", "success");

      idPromocionEliminar = null;

      await cargarPromociones();
    } catch (error) {
      console.error(error);

      errorEliminarPromocion.textContent = error.message;

      errorEliminarPromocion.classList.remove("d-none");
    } finally {
      btnConfirmarEliminar.disabled = false;
    }
  }

  btnNuevaPromocion.addEventListener("click", abrirNuevaPromocion);

  btnRecargarPromociones.addEventListener("click", cargarPromociones);

  formPromocion.addEventListener("submit", guardarPromocion);

  btnConfirmarEliminar.addEventListener("click", eliminarPromocion);

  document.addEventListener("DOMContentLoaded", async () => {
    await cargarServicios();

    await cargarPromociones();
  });
})();
