(() => {
  /* ═══════════════════════════════════════════════════════════
     mis-fotos.js

     Gestión de fotos de portada de la barbería.
  ═══════════════════════════════════════════════════════════ */

  const API_MI_BARBERIA = "/api/mi-barberia/";

  let fotosActuales = [];

  let fotoPendienteEliminar = null;

  /* ═══════════════════════════════════════════════════════════
     REFERENCIAS
  ═══════════════════════════════════════════════════════════ */

  const listaFotos = document.getElementById("lista-fotos-barberia");

  const estadoFotos = document.getElementById("estado-fotos");

  const cantidadFotos = document.getElementById("cantidad-fotos");

  const alertaFotos = document.getElementById("alerta-fotos-barberia");

  const btnAgregarFoto = document.getElementById("btn-agregar-foto");

  const inputFoto = document.getElementById("nueva-foto-archivo");

  const alertaEliminar = document.getElementById("alerta-eliminar-foto");

  const btnConfirmarEliminar = document.getElementById(
    "btn-confirmar-eliminar-foto",
  );

  /* ═══════════════════════════════════════════════════════════
     MODAL
  ═══════════════════════════════════════════════════════════ */

  const modalEliminar = bootstrap.Modal.getOrCreateInstance(
    document.getElementById("modal-eliminar-foto"),
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
     CARGAR FOTOS
  ═══════════════════════════════════════════════════════════ */

  async function cargarFotos() {
    mostrarCarga();

    try {
      const respuesta = await fetch(API_MI_BARBERIA + "fotos/");

      const datos = await respuesta.json();

      if (!respuesta.ok || !datos.ok) {
        mostrarError(datos.error || "No se pudieron cargar las fotos.");

        return;
      }

      fotosActuales = datos.fotos || [];

      renderizarFotos();
    } catch (error) {
      console.error(error);

      mostrarError("Ocurrió un error al cargar las fotos.");
    }
  }

  /* ═══════════════════════════════════════════════════════════
     ESTADO CARGANDO
  ═══════════════════════════════════════════════════════════ */

  function mostrarCarga() {
    cantidadFotos.textContent = "0";

    listaFotos.classList.add("d-none");

    estadoFotos.classList.remove("d-none");

    estadoFotos.innerHTML = `

      <div
        class="d-flex align-items-center gap-2 text-body-secondary"
      >

        <div
          class="spinner-border spinner-border-sm"
          role="status"
        ></div>

        <span>
          Cargando fotos...
        </span>

      </div>

    `;
  }

  /* ═══════════════════════════════════════════════════════════
     ERROR
  ═══════════════════════════════════════════════════════════ */

  function mostrarError(mensaje) {
    listaFotos.classList.add("d-none");

    estadoFotos.classList.remove("d-none");

    estadoFotos.innerHTML = `

      <div
        class="alert alert-danger mb-0"
      >
        ${mensaje}
      </div>

    `;

    cantidadFotos.textContent = "0";
  }

  /* ═══════════════════════════════════════════════════════════
     RENDER
  ═══════════════════════════════════════════════════════════ */

  function renderizarFotos() {
    cantidadFotos.textContent = fotosActuales.length;

    listaFotos.innerHTML = "";

    if (fotosActuales.length === 0) {
      listaFotos.classList.add("d-none");

      estadoFotos.classList.remove("d-none");

      estadoFotos.innerHTML = `

        <div class="text-center py-5">

          <i
            class="bi bi-images fs-1 text-body-secondary"
          ></i>


          <h3 class="h5 mt-3">
            Todavía no cargaste fotos
          </h3>


          <p
            class="text-body-secondary mb-3"
          >
            Agregá imágenes para mostrar tu barbería a los clientes.
          </p>


          <button
            type="button"
            class="btn btn-primary"
            id="btn-primera-foto"
          >

            <i
              class="bi bi-plus-lg me-1"
            ></i>

            Agregar foto

          </button>

        </div>

      `;

      document
        .getElementById("btn-primera-foto")
        .addEventListener("click", abrirSelectorFoto);

      return;
    }

    estadoFotos.classList.add("d-none");

    listaFotos.classList.remove("d-none");

    listaFotos.innerHTML = fotosActuales
      .map((foto) => crearFotoHTML(foto))
      .join("");

    conectarBotonesEliminar();
  }

  /* ═══════════════════════════════════════════════════════════
     CARD FOTO
  ═══════════════════════════════════════════════════════════ */

  function crearFotoHTML(foto) {
    return `

      <div class="col">

        <div class="card h-100">

          <div
            class="ratio ratio-16x9 bg-body-tertiary overflow-hidden"
          >

            <img
              src="${foto.url}"
              alt="Foto de portada"
              class="w-100 h-100 object-fit-cover"
            >

          </div>


          <div
            class="card-body d-flex justify-content-between align-items-center"
          >

            <div>

              <div class="fw-semibold">
                Foto de portada
              </div>


              <div
                class="small text-body-secondary"
              >
                Visible en tu perfil
              </div>

            </div>


            <button
              type="button"
              class="btn btn-sm btn-outline-danger btn-eliminar-foto"
              data-id="${foto.id}"
              aria-label="Eliminar foto"
            >

              <i class="bi bi-trash"></i>

            </button>

          </div>

        </div>

      </div>

    `;
  }

  /* ═══════════════════════════════════════════════════════════
     AGREGAR FOTO
  ═══════════════════════════════════════════════════════════ */

  function abrirSelectorFoto() {
    inputFoto.click();
  }

  btnAgregarFoto.addEventListener("click", abrirSelectorFoto);

  inputFoto.addEventListener(
    "change",

    async (event) => {
      const archivo = event.target.files[0];

      if (!archivo) {
        return;
      }

      limpiarAlerta(alertaFotos);

      btnAgregarFoto.disabled = true;

      btnAgregarFoto.innerHTML = `

        <span
          class="spinner-border spinner-border-sm me-2"
          aria-hidden="true"
        ></span>

        Subiendo...

      `;

      try {
        const datos = await subirArchivo(
          API_MI_BARBERIA + "portada/",

          "foto",

          archivo,
        );

        if (!datos.ok) {
          mostrarAlerta(
            alertaFotos,

            datos.error || "No se pudo agregar la foto.",

            "danger",
          );

          return;
        }

        mostrarAlerta(
          alertaFotos,

          "La foto fue agregada correctamente.",

          "success",
        );

        await cargarFotos();
      } catch (error) {
        console.error(error);

        mostrarAlerta(
          alertaFotos,

          "No se pudo conectar con el servidor.",

          "danger",
        );
      } finally {
        btnAgregarFoto.disabled = false;

        btnAgregarFoto.innerHTML = `

          <i
            class="bi bi-plus-lg me-1"
          ></i>

          Agregar foto

        `;

        event.target.value = "";
      }
    },
  );

  /* ═══════════════════════════════════════════════════════════
     BOTONES ELIMINAR
  ═══════════════════════════════════════════════════════════ */

  function conectarBotonesEliminar() {
    listaFotos.querySelectorAll(".btn-eliminar-foto").forEach((boton) => {
      boton.addEventListener(
        "click",

        () => {
          fotoPendienteEliminar = boton.dataset.id;

          limpiarAlerta(alertaEliminar);

          modalEliminar.show();
        },
      );
    });
  }

  /* ═══════════════════════════════════════════════════════════
     CONFIRMAR ELIMINACIÓN
  ═══════════════════════════════════════════════════════════ */

  btnConfirmarEliminar.addEventListener(
    "click",

    async () => {
      if (!fotoPendienteEliminar) {
        return;
      }

      btnConfirmarEliminar.disabled = true;

      btnConfirmarEliminar.innerHTML = `

        <span
          class="spinner-border spinner-border-sm me-2"
          aria-hidden="true"
        ></span>

        Eliminando...

      `;

      try {
        const respuesta = await fetch(
          API_MI_BARBERIA + `fotos/${fotoPendienteEliminar}/`,

          {
            method: "DELETE",

            headers: {
              "X-CSRFToken": getCookie("csrftoken"),
            },
          },
        );

        const datos = await respuesta.json();

        if (!respuesta.ok || !datos.ok) {
          mostrarAlerta(
            alertaEliminar,

            datos.error || "No se pudo eliminar la foto.",

            "danger",
          );

          return;
        }

        modalEliminar.hide();

        mostrarAlerta(
          alertaFotos,

          "La foto fue eliminada correctamente.",

          "success",
        );

        fotoPendienteEliminar = null;

        await cargarFotos();
      } catch (error) {
        console.error(error);

        mostrarAlerta(
          alertaEliminar,

          "No se pudo conectar con el servidor.",

          "danger",
        );
      } finally {
        btnConfirmarEliminar.disabled = false;

        btnConfirmarEliminar.textContent = "Eliminar";
      }
    },
  );

  /* ═══════════════════════════════════════════════════════════
     CERRAR MODAL
  ═══════════════════════════════════════════════════════════ */

  document.getElementById("modal-eliminar-foto").addEventListener(
    "hidden.bs.modal",

    () => {
      fotoPendienteEliminar = null;

      limpiarAlerta(alertaEliminar);
    },
  );

  /* ═══════════════════════════════════════════════════════════
     INICIO
  ═══════════════════════════════════════════════════════════ */

  cargarFotos();
})();
