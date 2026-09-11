(() => {
  /* ═══════════════════════════════════════════════════════════
     mi-barberia.js

     Panel del dueño.
     GET / PUT /api/mi-barberia/
  ═══════════════════════════════════════════════════════════ */

  const API_MI_BARBERIA = "/api/mi-barberia/";

  /* ═══════════════════════════════════════════════════════════
     REFERENCIAS
  ═══════════════════════════════════════════════════════════ */

  const panelCargando = document.getElementById("panel-mi-barberia-cargando");

  const panelForm = document.getElementById("panel-mi-barberia");

  const formulario = document.getElementById("form-mi-barberia");

  const alerta = document.getElementById("alerta-mi-barberia");

  const btnGuardar = document.getElementById("btn-mi-barberia-guardar");

  const btnSubirLogo = document.getElementById("btn-mb-logo-subir");

  const inputLogo = document.getElementById("mb-logo-archivo");

  const previewLogo = document.getElementById("mb-logo-preview");

  /* ═══════════════════════════════════════════════════════════
     ALERTAS
  ═══════════════════════════════════════════════════════════ */

  function mostrarAlerta(mensaje, tipo) {
    alerta.textContent = mensaje;

    alerta.className = `alert alert-${tipo}`;

    alerta.classList.remove("d-none");
  }

  function limpiarAlerta() {
    alerta.textContent = "";

    alerta.className = "alert d-none";
  }

  /* ═══════════════════════════════════════════════════════════
     CARGAR BARBERÍA
  ═══════════════════════════════════════════════════════════ */

  async function cargarMiBarberia() {
    try {
      const respuesta = await fetch(API_MI_BARBERIA);

      const datos = await respuesta.json();

      if (!respuesta.ok || !datos.ok) {
        mostrarErrorCarga(datos.error || "No se pudo cargar tu barbería.");

        return;
      }

      document.getElementById("mb-nombre").value = datos.nombre || "";

      document.getElementById("mb-direccion").value = datos.direccion || "";

      document.getElementById("mb-zona").value = datos.zona || "";

      document.getElementById("mb-descripcion").value = datos.descripcion || "";

      mostrarPreviewLogo(datos.logo);

      panelCargando.classList.add("d-none");

      panelForm.classList.remove("d-none");
    } catch (error) {
      console.error(error);

      mostrarErrorCarga("Ocurrió un error al cargar tu barbería.");
    }
  }

  /* ═══════════════════════════════════════════════════════════
     ERROR DE CARGA
  ═══════════════════════════════════════════════════════════ */

  function mostrarErrorCarga(mensaje) {
    panelCargando.innerHTML = `

      <div class="card-body">

        <div
          class="alert alert-danger mb-0"
          role="alert"
        >
          ${mensaje}
        </div>

      </div>

    `;
  }

  /* ═══════════════════════════════════════════════════════════
     GUARDAR DATOS
  ═══════════════════════════════════════════════════════════ */

  formulario.addEventListener(
    "submit",

    async (event) => {
      event.preventDefault();

      limpiarAlerta();

      const payload = {
        nombre: document.getElementById("mb-nombre").value.trim(),

        direccion: document.getElementById("mb-direccion").value.trim(),

        zona: document.getElementById("mb-zona").value.trim(),

        descripcion: document.getElementById("mb-descripcion").value.trim(),
      };

      if (!payload.nombre || !payload.direccion || !payload.zona) {
        mostrarAlerta("Nombre, dirección y zona son obligatorios.", "warning");

        return;
      }

      btnGuardar.disabled = true;

      btnGuardar.innerHTML = `

        <span
          class="spinner-border spinner-border-sm me-2"
          aria-hidden="true"
        ></span>

        Guardando...

      `;

      try {
        const respuesta = await fetch(API_MI_BARBERIA, {
          method: "PUT",

          headers: {
            "Content-Type": "application/json",

            "X-CSRFToken": getCookie("csrftoken"),
          },

          body: JSON.stringify(payload),
        });

        const datos = await respuesta.json();

        if (respuesta.ok && datos.ok) {
          mostrarAlerta("Los cambios se guardaron correctamente.", "success");

          actualizarNombreSidebar(payload.nombre);
        } else {
          mostrarAlerta(
            datos.error || "No se pudieron guardar los cambios.",
            "danger",
          );
        }
      } catch (error) {
        console.error(error);

        mostrarAlerta("No se pudo conectar con el servidor.", "danger");
      } finally {
        btnGuardar.disabled = false;

        btnGuardar.textContent = "Guardar cambios";
      }
    },
  );

  /* ═══════════════════════════════════════════════════════════
     PREVIEW LOGO
  ═══════════════════════════════════════════════════════════ */

  function mostrarPreviewLogo(url) {
    if (!url) {
      previewLogo.innerHTML = `

        <span
          class="text-body-secondary"
        >
          Sin logo
        </span>

      `;

      return;
    }

    previewLogo.innerHTML = `

      <img
        src="${url}"
        alt="Logo de la barbería"
        class="w-100 h-100 object-fit-cover"
      >

    `;
  }

  /* ═══════════════════════════════════════════════════════════
     ABRIR SELECTOR DE ARCHIVO
  ═══════════════════════════════════════════════════════════ */

  btnSubirLogo.addEventListener(
    "click",

    () => {
      inputLogo.click();
    },
  );

  /* ═══════════════════════════════════════════════════════════
     SUBIR LOGO
  ═══════════════════════════════════════════════════════════ */

  inputLogo.addEventListener(
    "change",

    async (event) => {
      const archivo = event.target.files[0];

      if (!archivo) {
        return;
      }

      limpiarAlerta();

      btnSubirLogo.disabled = true;

      btnSubirLogo.innerHTML = `

        <span
          class="spinner-border spinner-border-sm me-2"
          aria-hidden="true"
        ></span>

        Subiendo...

      `;

      try {
        const datos = await subirArchivo(
          API_MI_BARBERIA + "logo/",

          "logo",

          archivo,
        );

        if (datos.ok) {
          mostrarPreviewLogo(datos.logo);

          mostrarAlerta("El logo se actualizó correctamente.", "success");
        } else {
          mostrarAlerta(datos.error || "No se pudo subir el logo.", "danger");
        }
      } catch (error) {
        console.error(error);

        mostrarAlerta("No se pudo conectar con el servidor.", "danger");
      } finally {
        btnSubirLogo.disabled = false;

        btnSubirLogo.textContent = "Cambiar logo";

        event.target.value = "";
      }
    },
  );

  /* ═══════════════════════════════════════════════════════════
     ACTUALIZAR SIDEBAR
  ═══════════════════════════════════════════════════════════ */

  function actualizarNombreSidebar(nombre) {
    const escritorio = document.getElementById("panel-sidebar-barberia");

    const mobile = document.getElementById("panel-sidebar-barberia-mobile");

    if (escritorio) {
      escritorio.textContent = nombre;
    }

    if (mobile) {
      mobile.textContent = nombre;
    }
  }

  /* ═══════════════════════════════════════════════════════════
     INICIAR
  ═══════════════════════════════════════════════════════════ */

  cargarMiBarberia();
})();
