(() => {
  /* ═══════════════════════════════════════════════════════════
     mis-barberos.js

     CRUD de barberos del panel del dueño.

     GET
     POST
     PUT

     /api/mi-barberia/barberos/
  ═══════════════════════════════════════════════════════════ */

  const API_MIS_BARBEROS = "/api/mi-barberia/barberos/";

  let barberosActuales = [];

  let barberoFotoPendiente = null;

  let cambioEstadoPendiente = null;

  /* ═══════════════════════════════════════════════════════════
     REFERENCIAS
  ═══════════════════════════════════════════════════════════ */

  const lista = document.getElementById("lista-mis-barberos");

  const estadoBarberos = document.getElementById("estado-barberos");

  const contenedorTabla = document.getElementById("contenedor-tabla-barberos");

  const cantidadBarberos = document.getElementById("cantidad-barberos");

  const alertaGeneral = document.getElementById("alerta-barberos");

  /* FORM */

  const formulario = document.getElementById("form-barbero");

  const inputIdEdit = document.getElementById("bb-id-editando");

  const inputNombre = document.getElementById("bb-nombre");

  const inputApellido = document.getElementById("bb-apellido");

  const inputEmail = document.getElementById("bb-email");

  const inputPassword = document.getElementById("bb-password");

  const inputTelefono = document.getElementById("bb-telefono");

  const inputEspecialidad = document.getElementById("bb-especialidad");

  const grupoPassword = document.getElementById("grupo-bb-password");

  const ayudaEmailEdicion = document.getElementById("ayuda-email-edicion");

  const alertaForm = document.getElementById("alerta-form-barbero");

  const btnGuardar = document.getElementById("btn-guardar-barbero");

  const btnNuevoBarbero = document.getElementById("btn-nuevo-barbero");

  const modalTitulo = document.getElementById("modal-barbero-titulo");

  const modalSubtitulo = document.getElementById("modal-barbero-subtitulo");

  /* FOTO */

  const inputFoto = document.getElementById("input-foto-barbero");

  /* ESTADO */

  const textoConfirmarEstado = document.getElementById(
    "texto-confirmar-estado",
  );

  const btnConfirmarEstado = document.getElementById("btn-confirmar-estado");

  const alertaEstado = document.getElementById("alerta-estado-barbero");

  /* ═══════════════════════════════════════════════════════════
     MODALES
  ═══════════════════════════════════════════════════════════ */

  const modalBarbero = bootstrap.Modal.getOrCreateInstance(
    document.getElementById("modal-barbero"),
  );

  const modalEstado = bootstrap.Modal.getOrCreateInstance(
    document.getElementById("modal-estado-barbero"),
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
     CARGAR BARBEROS
  ═══════════════════════════════════════════════════════════ */

  async function cargarBarberos() {
    mostrarCarga();

    try {
      const respuesta = await fetch(API_MIS_BARBEROS);

      const datos = await respuesta.json();

      if (!respuesta.ok || !datos.ok) {
        mostrarErrorListado(
          datos.error || "No se pudieron cargar los barberos.",
        );

        return;
      }

      barberosActuales = datos.barberos || [];

      renderizarBarberos();
    } catch (error) {
      console.error(error);

      mostrarErrorListado("Ocurrió un error al cargar los barberos.");
    }
  }

  /* ═══════════════════════════════════════════════════════════
     CARGA
  ═══════════════════════════════════════════════════════════ */

  function mostrarCarga() {
    cantidadBarberos.textContent = "0";

    contenedorTabla.classList.add("d-none");

    estadoBarberos.classList.remove("d-none");

    estadoBarberos.innerHTML = `

      <div
        class="d-flex align-items-center gap-2 text-body-secondary"
      >

        <div
          class="spinner-border spinner-border-sm"
          role="status"
        ></div>

        <span>
          Cargando barberos...
        </span>

      </div>

    `;
  }

  function mostrarErrorListado(mensaje) {
    cantidadBarberos.textContent = "0";

    contenedorTabla.classList.add("d-none");

    estadoBarberos.classList.remove("d-none");

    estadoBarberos.innerHTML = `

      <div
        class="alert alert-danger mb-0"
        role="alert"
      >
        ${mensaje}
      </div>

    `;
  }

  /* ═══════════════════════════════════════════════════════════
     RENDER TABLA
  ═══════════════════════════════════════════════════════════ */

  function renderizarBarberos() {
    cantidadBarberos.textContent = barberosActuales.length;

    lista.innerHTML = "";

    if (barberosActuales.length === 0) {
      contenedorTabla.classList.add("d-none");

      estadoBarberos.classList.remove("d-none");

      estadoBarberos.innerHTML = `

        <div
          class="text-center py-4"
        >

          <i
            class="bi bi-people fs-1 text-body-secondary"
          ></i>


          <h3 class="h5 mt-3">
            Todavía no agregaste barberos
          </h3>


          <p
            class="text-body-secondary mb-3"
          >
            Agregá el primer integrante de tu equipo.
          </p>


          <button
            type="button"
            class="btn btn-primary"
            id="btn-primer-barbero"
          >

            <i class="bi bi-person-plus me-1"></i>

            Agregar barbero

          </button>

        </div>

      `;

      document
        .getElementById("btn-primer-barbero")
        .addEventListener("click", abrirNuevoBarbero);

      return;
    }

    estadoBarberos.classList.add("d-none");

    contenedorTabla.classList.remove("d-none");

    lista.innerHTML = barberosActuales
      .map((barbero) => crearFilaBarbero(barbero))
      .join("");

    conectarEventosTabla();
  }

  /* ═══════════════════════════════════════════════════════════
     FILA
  ═══════════════════════════════════════════════════════════ */

  function crearFilaBarbero(barbero) {
    const activo = barbero.estado !== "INACTIVO";

    return `

      <tr>


        <!-- BARBERO -->
        <td class="ps-4">

          <div
            class="d-flex align-items-center gap-3"
          >

            <div
              class="rounded-circle border bg-body-tertiary overflow-hidden d-flex align-items-center justify-content-center flex-shrink-0"
              style="
                width: 44px;
                height: 44px;
              "
            >

              ${
                barbero.foto
                  ? `

                    <img
                      src="${barbero.foto}"
                      alt="Foto de ${barbero.nombre}"
                      class="w-100 h-100 object-fit-cover"
                    >

                  `
                  : `

                    <i
                      class="bi bi-person text-body-secondary fs-5"
                    ></i>

                  `
              }

            </div>


            <div>

              <div class="fw-semibold">

                ${barbero.nombre}
                ${barbero.apellido}

              </div>


              <div
                class="small text-body-secondary"
              >
                Barbero
              </div>

            </div>

          </div>

        </td>



        <!-- CONTACTO -->
        <td>

          <div>
            ${barbero.email}
          </div>


          <div
            class="small text-body-secondary"
          >
            ${barbero.telefono || "Sin teléfono"}
          </div>

        </td>



        <!-- ESPECIALIDAD -->
        <td>

          ${
            barbero.especialidad
              ? barbero.especialidad
              : `

                <span
                  class="text-body-secondary"
                >
                  Sin especificar
                </span>

              `
          }

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
                  class="dropdown-item btn-editar-barbero"
                  data-id="${barbero.id_barbero}"
                >

                  <i class="bi bi-pencil me-2"></i>

                  Editar

                </button>

              </li>



              <li>

                <button
                  type="button"
                  class="dropdown-item btn-foto-barbero"
                  data-id="${barbero.id_barbero}"
                >

                  <i class="bi bi-camera me-2"></i>

                  Cambiar foto

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
                  } btn-estado-barbero"
                  data-id="${barbero.id_barbero}"
                  data-estado="${barbero.estado}"
                >

                  <i
                    class="bi ${
                      activo ? "bi-person-dash" : "bi-person-check"
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
     EVENTOS DE TABLA
  ═══════════════════════════════════════════════════════════ */

  function conectarEventosTabla() {
    lista.querySelectorAll(".btn-editar-barbero").forEach((boton) => {
      boton.addEventListener(
        "click",

        () => {
          abrirEdicionBarbero(boton.dataset.id);
        },
      );
    });

    lista.querySelectorAll(".btn-foto-barbero").forEach((boton) => {
      boton.addEventListener(
        "click",

        () => {
          barberoFotoPendiente = boton.dataset.id;

          inputFoto.click();
        },
      );
    });

    lista.querySelectorAll(".btn-estado-barbero").forEach((boton) => {
      boton.addEventListener(
        "click",

        () => {
          abrirConfirmacionEstado(boton.dataset.id, boton.dataset.estado);
        },
      );
    });
  }

  /* ═══════════════════════════════════════════════════════════
     NUEVO BARBERO
  ═══════════════════════════════════════════════════════════ */

  function abrirNuevoBarbero() {
    limpiarFormulario();

    modalTitulo.textContent = "Agregar barbero";

    modalSubtitulo.textContent = "Completá los datos del nuevo integrante.";

    btnGuardar.textContent = "Agregar barbero";

    grupoPassword.classList.remove("d-none");

    inputPassword.required = true;

    inputEmail.disabled = false;

    ayudaEmailEdicion.classList.add("d-none");

    modalBarbero.show();
  }

  btnNuevoBarbero.addEventListener("click", abrirNuevoBarbero);

  /* ═══════════════════════════════════════════════════════════
     EDITAR BARBERO
  ═══════════════════════════════════════════════════════════ */

  function abrirEdicionBarbero(id) {
    const barbero = barberosActuales.find(
      (item) => String(item.id_barbero) === String(id),
    );

    if (!barbero) {
      return;
    }

    limpiarFormulario();

    inputIdEdit.value = barbero.id_barbero;

    inputNombre.value = barbero.nombre || "";

    inputApellido.value = barbero.apellido || "";

    inputEmail.value = barbero.email || "";

    inputTelefono.value = barbero.telefono || "";

    inputEspecialidad.value = barbero.especialidad || "";

    inputEmail.disabled = true;

    ayudaEmailEdicion.classList.remove("d-none");

    grupoPassword.classList.add("d-none");

    inputPassword.required = false;

    modalTitulo.textContent = "Editar barbero";

    modalSubtitulo.textContent =
      "Modificá los datos del integrante seleccionado.";

    btnGuardar.textContent = "Guardar cambios";

    modalBarbero.show();
  }

  /* ═══════════════════════════════════════════════════════════
     LIMPIAR FORM
  ═══════════════════════════════════════════════════════════ */

  function limpiarFormulario() {
    formulario.reset();

    inputIdEdit.value = "";

    inputEmail.disabled = false;

    ayudaEmailEdicion.classList.add("d-none");

    grupoPassword.classList.remove("d-none");

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

      const idEditando = inputIdEdit.value;

      const esEdicion = Boolean(idEditando);

      const nombre = inputNombre.value.trim();

      const apellido = inputApellido.value.trim();

      const email = inputEmail.value.trim();

      const password = inputPassword.value;

      const telefono = inputTelefono.value.trim();

      const especialidad = inputEspecialidad.value.trim();

      if (!nombre || !apellido || !email || !telefono) {
        mostrarAlerta(
          alertaForm,
          "Nombre, apellido, email y teléfono son obligatorios.",
          "warning",
        );

        return;
      }

      if (!esEdicion && password.length < 6) {
        mostrarAlerta(
          alertaForm,
          "La contraseña debe tener al menos 6 caracteres.",
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
          ? `${API_MIS_BARBEROS}${idEditando}/`
          : API_MIS_BARBEROS;

        const method = esEdicion ? "PUT" : "POST";

        const payload = esEdicion
          ? {
              nombre,
              apellido,
              telefono,
              especialidad,
            }
          : {
              nombre,
              apellido,
              email,
              telefono,
              password,
              especialidad,
            };

        const respuesta = await fetch(url, {
          method,

          headers: {
            "Content-Type": "application/json",

            "X-CSRFToken": getCookie("csrftoken"),
          },

          body: JSON.stringify(payload),
        });

        const datos = await respuesta.json();

        if (!respuesta.ok || !datos.ok) {
          mostrarAlerta(
            alertaForm,
            datos.error || "No se pudo guardar el barbero.",
            "danger",
          );

          return;
        }

        modalBarbero.hide();

        mostrarAlerta(
          alertaGeneral,

          esEdicion
            ? "Los datos del barbero se actualizaron correctamente."
            : "El barbero fue agregado correctamente.",

          "success",
        );

        await cargarBarberos();
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
          : "Agregar barbero";
      }
    },
  );

  /* ═══════════════════════════════════════════════════════════
     CAMBIAR FOTO
  ═══════════════════════════════════════════════════════════ */

  inputFoto.addEventListener(
    "change",

    async (event) => {
      const archivo = event.target.files[0];

      if (!archivo || !barberoFotoPendiente) {
        return;
      }

      try {
        const datos = await subirArchivo(
          `${API_MIS_BARBEROS}${barberoFotoPendiente}/foto/`,

          "foto",

          archivo,
        );

        if (!datos.ok) {
          mostrarAlerta(
            alertaGeneral,
            datos.error || "No se pudo actualizar la foto.",
            "danger",
          );

          return;
        }

        mostrarAlerta(
          alertaGeneral,
          "La foto del barbero se actualizó correctamente.",
          "success",
        );

        await cargarBarberos();
      } catch (error) {
        console.error(error);

        mostrarAlerta(
          alertaGeneral,
          "No se pudo conectar con el servidor.",
          "danger",
        );
      } finally {
        inputFoto.value = "";

        barberoFotoPendiente = null;
      }
    },
  );

  /* ═══════════════════════════════════════════════════════════
     CAMBIAR ESTADO
  ═══════════════════════════════════════════════════════════ */

  function abrirConfirmacionEstado(id, estadoActual) {
    const barbero = barberosActuales.find(
      (item) => String(item.id_barbero) === String(id),
    );

    if (!barbero) {
      return;
    }

    const estaInactivo = estadoActual === "INACTIVO";

    cambioEstadoPendiente = {
      id,

      estadoActual,
    };

    limpiarAlerta(alertaEstado);

    document.getElementById("modal-estado-barbero-titulo").textContent =
      estaInactivo ? "Reactivar barbero" : "Dar de baja barbero";

    textoConfirmarEstado.textContent = estaInactivo
      ? `¿Querés reactivar a ${barbero.nombre} ${barbero.apellido}?`
      : `¿Querés dar de baja a ${barbero.nombre} ${barbero.apellido}?`;

    btnConfirmarEstado.textContent = estaInactivo ? "Reactivar" : "Dar de baja";

    btnConfirmarEstado.className = estaInactivo
      ? "btn btn-primary"
      : "btn btn-danger";

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

      const nuevoEstado = estadoActual === "INACTIVO" ? "ACTIVO" : "INACTIVO";

      btnConfirmarEstado.disabled = true;

      const textoOriginal = btnConfirmarEstado.textContent;

      btnConfirmarEstado.innerHTML = `

        <span
          class="spinner-border spinner-border-sm me-2"
          aria-hidden="true"
        ></span>

        Procesando...

      `;

      try {
        const respuesta = await fetch(
          `${API_MIS_BARBEROS}${id}/`,

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

          nuevoEstado === "ACTIVO"
            ? "El barbero fue reactivado correctamente."
            : "El barbero fue dado de baja correctamente.",

          "success",
        );

        cambioEstadoPendiente = null;

        await cargarBarberos();
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
     LIMPIEZA DE MODALES
  ═══════════════════════════════════════════════════════════ */

  document
    .getElementById("modal-barbero")
    .addEventListener("hidden.bs.modal", limpiarFormulario);

  document.getElementById("modal-estado-barbero").addEventListener(
    "hidden.bs.modal",

    () => {
      cambioEstadoPendiente = null;

      limpiarAlerta(alertaEstado);
    },
  );

  /* ═══════════════════════════════════════════════════════════
     INICIAR
  ═══════════════════════════════════════════════════════════ */

  cargarBarberos();
})();
