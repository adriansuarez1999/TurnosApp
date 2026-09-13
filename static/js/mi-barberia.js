(() => {
  /* ═══════════════════════════════════════════════════════════
     mi-barberia.js
  ═══════════════════════════════════════════════════════════ */

  const API_MI_BARBERIA = "/api/mi-barberia/";

  /* ═══════════════════════════════════════════════════════════
     REFERENCIAS
  ═══════════════════════════════════════════════════════════ */

  const panelCargando = document.getElementById("panel-mi-barberia-cargando");

  const panelForm = document.getElementById("panel-mi-barberia");

  const alerta = document.getElementById("alerta-mi-barberia");

  const inputNombre = document.getElementById("mb-nombre");

  const inputDireccion = document.getElementById("mb-direccion");

  const inputZona = document.getElementById("mb-zona");

  const inputDescripcion = document.getElementById("mb-descripcion");

  const inputLogo = document.getElementById("mb-logo-archivo");

  const btnSubirLogo = document.getElementById("btn-mb-logo-subir");

  const btnGuardar = document.getElementById("btn-mi-barberia-guardar");

  const btnGuardarMobile = document.getElementById(
    "btn-mi-barberia-guardar-mobile",
  );

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
     CARGAR DATOS
  ═══════════════════════════════════════════════════════════ */

  async function cargarMiBarberia() {
    try {
      const respuesta = await fetch(API_MI_BARBERIA);

      const datos = await respuesta.json();

      if (!respuesta.ok || !datos.ok) {
        mostrarErrorCarga(datos.error || "No se pudo cargar tu barbería.");

        return;
      }

      inputNombre.value = datos.nombre || "";

      inputDireccion.value = datos.direccion || "";

      inputZona.value = datos.zona || "";

      inputDescripcion.value = datos.descripcion || "";

      mostrarPreviewLogo(datos.logo);

      actualizarResumen();

      panelCargando.classList.add("d-none");

      panelForm.classList.remove("d-none");
    } catch (error) {
      console.error(error);

      mostrarErrorCarga("Ocurrió un error al cargar tu barbería.");
    }
  }

  function mostrarErrorCarga(mensaje) {
    panelCargando.innerHTML = `

      <div
        class="alert alert-danger mb-0"
        role="alert"
      >

        ${mensaje}

      </div>

    `;
  }

  /* ═══════════════════════════════════════════════════════════
     RESUMEN
  ═══════════════════════════════════════════════════════════ */

  function actualizarResumen() {
    const nombre = inputNombre.value.trim();

    const direccion = inputDireccion.value.trim();

    const zona = inputZona.value.trim();

    document.getElementById("mb-header-nombre").textContent =
      nombre || "Mi barbería";

    document.getElementById("mb-header-ubicacion").textContent =
      construirUbicacion(direccion, zona);

    document.getElementById("mb-resumen-zona").textContent = zona || "—";

    document.getElementById("mb-resumen-direccion").textContent =
      direccion || "—";
  }

  function construirUbicacion(direccion, zona) {
    if (direccion && zona) {
      return `${direccion} · ${zona}`;
    }

    return direccion || zona || "Ubicación sin completar";
  }

  /* Actualización visual mientras escribe */

  inputNombre.addEventListener("input", actualizarResumen);

  inputDireccion.addEventListener("input", actualizarResumen);

  inputZona.addEventListener("input", actualizarResumen);

  /* ═══════════════════════════════════════════════════════════
     GUARDAR
  ═══════════════════════════════════════════════════════════ */

  async function guardarCambios() {
    limpiarAlerta();

    const payload = {
      nombre: inputNombre.value.trim(),

      direccion: inputDireccion.value.trim(),

      zona: inputZona.value.trim(),

      descripcion: inputDescripcion.value.trim(),
    };

    if (!payload.nombre || !payload.direccion || !payload.zona) {
      mostrarAlerta("Nombre, dirección y zona son obligatorios.", "warning");

      return;
    }

    cambiarEstadoBotonesGuardar(true);

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

      if (!respuesta.ok || !datos.ok) {
        mostrarAlerta(
          datos.error || "No se pudieron guardar los cambios.",
          "danger",
        );

        return;
      }

      actualizarResumen();

      mostrarAlerta("Los cambios se guardaron correctamente.", "success");

      /*
       * panel-base.js muestra el nombre de la barbería
       * en el sidebar.
       *
       * Lo actualizamos también aquí para que el cambio
       * se vea inmediatamente sin recargar.
       */

      const nombreSidebar = document.getElementById("panel-sidebar-barberia");

      if (nombreSidebar) {
        nombreSidebar.textContent = payload.nombre;
      }
    } catch (error) {
      console.error(error);

      mostrarAlerta("No se pudo conectar con el servidor.", "danger");
    } finally {
      cambiarEstadoBotonesGuardar(false);
    }
  }

  btnGuardar.addEventListener("click", guardarCambios);

  if (btnGuardarMobile) {
    btnGuardarMobile.addEventListener("click", guardarCambios);
  }

  function cambiarEstadoBotonesGuardar(guardando) {
    const botones = [btnGuardar, btnGuardarMobile].filter(Boolean);

    botones.forEach((boton) => {
      boton.disabled = guardando;

      boton.innerHTML = guardando
        ? `

              <span
                class="spinner-border spinner-border-sm me-2"
                aria-hidden="true"
              ></span>

              Guardando...

            `
        : `

              <i
                class="bi bi-floppy me-1"
              ></i>

              Guardar cambios

            `;
    });
  }

  /* ═══════════════════════════════════════════════════════════
     LOGO
  ═══════════════════════════════════════════════════════════ */

  function mostrarPreviewLogo(url) {
    const preview = document.getElementById("mb-logo-preview");

    const headerLogo = document.getElementById("mb-header-logo");

    if (url) {
      preview.innerHTML = `

        <img
          src="${url}"
          alt="Logo de la barbería"
          class="w-100 h-100 object-fit-cover"
        >

      `;

      headerLogo.innerHTML = `

        <img
          src="${url}"
          alt=""
          class="w-100 h-100 object-fit-cover"
        >

      `;

      return;
    }

    preview.innerHTML = `

      <div
        class="w-100 h-100 d-flex align-items-center justify-content-center text-primary"
      >

        <i
          class="bi bi-shop fs-1"
        ></i>

      </div>

    `;

    headerLogo.innerHTML = `

      <i
        class="bi bi-shop fs-3 text-primary"
      ></i>

    `;
  }

  btnSubirLogo.addEventListener(
    "click",

    () => {
      inputLogo.click();
    },
  );

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

        if (!datos.ok) {
          mostrarAlerta(datos.error || "No se pudo subir el logo.", "danger");

          return;
        }

        mostrarPreviewLogo(datos.logo);

        mostrarAlerta("El logo se actualizó correctamente.", "success");
      } catch (error) {
        console.error(error);

        mostrarAlerta("No se pudo conectar con el servidor.", "danger");
      } finally {
        btnSubirLogo.disabled = false;

        btnSubirLogo.innerHTML = `

          <i
            class="bi bi-image me-1"
          ></i>

          Cambiar logo

        `;

        event.target.value = "";
      }
    },
  );

  /* ═══════════════════════════════════════════════════════════
     INICIO
  ═══════════════════════════════════════════════════════════ */

  cargarMiBarberia();
})();
