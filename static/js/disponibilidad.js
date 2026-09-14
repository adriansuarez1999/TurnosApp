(() => {
  /* ═══════════════════════════════════════════════════════════
     disponibilidad.js

     Gestión de disponibilidad semanal de los barberos.

     GET /api/mi-barberia/barberos/
     GET /api/mi-barberia/barberos/<id>/disponibilidad/

     POST /api/mi-barberia/barberos/<id>/disponibilidad/

     PUT /api/mi-barberia/disponibilidad/<id>/
     DELETE /api/mi-barberia/disponibilidad/<id>/
  ═══════════════════════════════════════════════════════════ */

  const API_BARBEROS = "/api/mi-barberia/barberos/";

  const DIAS = [
    { codigo: "LUN", nombre: "Lunes" },
    { codigo: "MAR", nombre: "Martes" },
    { codigo: "MIE", nombre: "Miércoles" },
    { codigo: "JUE", nombre: "Jueves" },
    { codigo: "VIE", nombre: "Viernes" },
    { codigo: "SAB", nombre: "Sábado" },
    { codigo: "DOM", nombre: "Domingo" },
  ];

  let barberos = [];

  let bloquesActuales = [];

  let idBarberoSeleccionado = null;

  let idBloqueEliminar = null;

  /* ═══════════════════════════════════════════════════════════
     REFERENCIAS
  ═══════════════════════════════════════════════════════════ */

  const selectBarbero = document.getElementById(
    "select-barbero-disponibilidad",
  );

  const nombreBarberoSeleccionado = document.getElementById(
    "nombre-barbero-seleccionado",
  );

  const btnNuevoBloque = document.getElementById("btn-nuevo-bloque");

  const cantidadBloques = document.getElementById("cantidad-bloques");

  const alertaGeneral = document.getElementById("alerta-disponibilidad");

  const estadoDisponibilidad = document.getElementById("estado-disponibilidad");

  const grillaDisponibilidad = document.getElementById("grilla-disponibilidad");

  /* FORMULARIO */

  const formulario = document.getElementById("form-disponibilidad");

  const inputIdEditando = document.getElementById("disponibilidad-id-editando");

  const selectDia = document.getElementById("disponibilidad-dia");

  const inputInicio = document.getElementById("disponibilidad-inicio");

  const inputFin = document.getElementById("disponibilidad-fin");

  const alertaFormulario = document.getElementById(
    "alerta-form-disponibilidad",
  );

  const btnGuardar = document.getElementById("btn-guardar-disponibilidad");

  const modalTitulo = document.getElementById("modal-disponibilidad-titulo");

  const modalSubtitulo = document.getElementById(
    "modal-disponibilidad-subtitulo",
  );

  /* ELIMINAR */

  const textoBloqueEliminar = document.getElementById("texto-bloque-eliminar");

  const alertaEliminar = document.getElementById(
    "alerta-eliminar-disponibilidad",
  );

  const btnConfirmarEliminar = document.getElementById(
    "btn-confirmar-eliminar-disponibilidad",
  );

  /* ═══════════════════════════════════════════════════════════
     MODALES
  ═══════════════════════════════════════════════════════════ */

  const modalDisponibilidad = bootstrap.Modal.getOrCreateInstance(
    document.getElementById("modal-disponibilidad"),
  );

  const modalEliminar = bootstrap.Modal.getOrCreateInstance(
    document.getElementById("modal-eliminar-disponibilidad"),
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
     UTILIDADES
  ═══════════════════════════════════════════════════════════ */

  function nombreDia(codigo) {
    const dia = DIAS.find((item) => item.codigo === codigo);

    return dia ? dia.nombre : codigo;
  }

  function obtenerBarberoSeleccionado() {
    return barberos.find(
      (barbero) => Number(barbero.id_barbero) === Number(idBarberoSeleccionado),
    );
  }

  async function obtenerJson(respuesta) {
    try {
      return await respuesta.json();
    } catch {
      return {};
    }
  }

  /* ═══════════════════════════════════════════════════════════
     BARBEROS
  ═══════════════════════════════════════════════════════════ */

  async function cargarBarberos() {
    mostrarCargaBarberos();

    try {
      const respuesta = await fetch(API_BARBEROS);

      const datos = await obtenerJson(respuesta);

      if (!respuesta.ok || !datos.ok) {
        mostrarErrorGeneral(
          datos.error || "No se pudieron cargar los barberos.",
        );

        return;
      }

      barberos = datos.barberos || [];

      renderizarSelectorBarberos();
    } catch (error) {
      console.error(error);

      mostrarErrorGeneral("Ocurrió un error al cargar los barberos.");
    }
  }

  function mostrarCargaBarberos() {
    selectBarbero.disabled = true;

    btnNuevoBloque.disabled = true;

    selectBarbero.innerHTML = `
      <option value="">
        Cargando barberos...
      </option>
    `;
  }

  function renderizarSelectorBarberos() {
    if (barberos.length === 0) {
      selectBarbero.innerHTML = `
        <option value="">
          No hay barberos registrados
        </option>
      `;

      selectBarbero.disabled = true;

      btnNuevoBloque.disabled = true;

      nombreBarberoSeleccionado.textContent = "Ninguno";

      mostrarEstadoVacioBarberos();

      return;
    }

    selectBarbero.disabled = false;

    selectBarbero.innerHTML = `
      <option value="">
        Seleccionar barbero
      </option>

      ${barberos
        .map((barbero) => {
          const inactivo = barbero.estado === "INACTIVO";

          return `
            <option
              value="${barbero.id_barbero}"
            >
              ${barbero.nombre} ${barbero.apellido}${
                inactivo ? " — Inactivo" : ""
              }
            </option>
          `;
        })
        .join("")}
    `;

    const primerActivo =
      barberos.find((barbero) => barbero.estado !== "INACTIVO") || barberos[0];

    selectBarbero.value = primerActivo.id_barbero;

    seleccionarBarbero(primerActivo.id_barbero);
  }

  /* ═══════════════════════════════════════════════════════════
     SELECCIÓN
  ═══════════════════════════════════════════════════════════ */

  async function seleccionarBarbero(id) {
    idBarberoSeleccionado = id ? Number(id) : null;

    limpiarAlerta(alertaGeneral);

    if (!idBarberoSeleccionado) {
      nombreBarberoSeleccionado.textContent = "Ninguno";

      btnNuevoBloque.disabled = true;

      bloquesActuales = [];

      cantidadBloques.textContent = "0 bloques";

      mostrarEstadoInicial();

      return;
    }

    const barbero = obtenerBarberoSeleccionado();

    nombreBarberoSeleccionado.textContent = barbero
      ? `${barbero.nombre} ${barbero.apellido}`
      : "Barbero seleccionado";

    btnNuevoBloque.disabled = false;

    await cargarDisponibilidad();
  }

  /* ═══════════════════════════════════════════════════════════
     DISPONIBILIDAD
  ═══════════════════════════════════════════════════════════ */

  async function cargarDisponibilidad() {
    if (!idBarberoSeleccionado) {
      return;
    }

    mostrarCargaDisponibilidad();

    try {
      const respuesta = await fetch(
        `/api/mi-barberia/barberos/${idBarberoSeleccionado}/disponibilidad/`,
      );

      const datos = await obtenerJson(respuesta);

      if (!respuesta.ok || !datos.ok) {
        mostrarErrorDisponibilidad(
          datos.error || "No se pudo cargar la disponibilidad.",
        );

        return;
      }

      bloquesActuales = datos.disponibilidad || [];

      renderizarDisponibilidad();
    } catch (error) {
      console.error(error);

      mostrarErrorDisponibilidad(
        "Ocurrió un error al cargar la disponibilidad.",
      );
    }
  }

  function mostrarCargaDisponibilidad() {
    grillaDisponibilidad.classList.add("d-none");

    estadoDisponibilidad.classList.remove("d-none");

    estadoDisponibilidad.innerHTML = `
      <div
        class="d-flex justify-content-center align-items-center gap-2 text-body-secondary"
      >
        <div
          class="spinner-border spinner-border-sm"
          role="status"
        ></div>

        <span>
          Cargando disponibilidad...
        </span>
      </div>
    `;
  }

  function mostrarErrorDisponibilidad(mensaje) {
    grillaDisponibilidad.classList.add("d-none");

    estadoDisponibilidad.classList.remove("d-none");

    estadoDisponibilidad.innerHTML = `
      <div
        class="alert alert-danger mb-0"
        role="alert"
      >
        ${mensaje}
      </div>
    `;
  }

  function mostrarEstadoInicial() {
    grillaDisponibilidad.classList.add("d-none");

    estadoDisponibilidad.classList.remove("d-none");

    estadoDisponibilidad.innerHTML = `
      <div class="text-center">

        <i
          class="bi bi-calendar-week fs-1 text-body-secondary"
        ></i>

        <h3 class="h5 mt-3">
          Seleccioná un barbero
        </h3>

        <p class="text-body-secondary mb-0">
          Su disponibilidad semanal aparecerá en esta sección.
        </p>

      </div>
    `;
  }

  function mostrarEstadoVacioBarberos() {
    grillaDisponibilidad.classList.add("d-none");

    estadoDisponibilidad.classList.remove("d-none");

    estadoDisponibilidad.innerHTML = `
      <div class="text-center py-3">

        <i
          class="bi bi-people fs-1 text-body-secondary"
        ></i>

        <h3 class="h5 mt-3">
          No hay barberos registrados
        </h3>

        <p class="text-body-secondary mb-0">
          Primero agregá un barbero desde la sección
          "Mis barberos".
        </p>

      </div>
    `;
  }

  function mostrarErrorGeneral(mensaje) {
    mostrarAlerta(alertaGeneral, mensaje, "danger");

    mostrarErrorDisponibilidad(mensaje);
  }

  /* ═══════════════════════════════════════════════════════════
     RENDER GRILLA
  ═══════════════════════════════════════════════════════════ */

  function renderizarDisponibilidad() {
    estadoDisponibilidad.classList.add("d-none");

    grillaDisponibilidad.classList.remove("d-none");

    const total = bloquesActuales.length;

    cantidadBloques.textContent = total === 1 ? "1 bloque" : `${total} bloques`;

    DIAS.forEach((dia) => {
      const contenedor = document.getElementById(`bloques-${dia.codigo}`);

      const bloquesDia = bloquesActuales
        .filter((bloque) => bloque.dia_semana === dia.codigo)
        .sort((a, b) => a.hora_inicio.localeCompare(b.hora_inicio));

      if (bloquesDia.length === 0) {
        contenedor.innerHTML = `
          <span class="text-body-secondary small">
            Sin horarios configurados
          </span>
        `;

        return;
      }

      contenedor.innerHTML = `
        <div
          class="d-flex flex-column gap-2"
        >
          ${bloquesDia
            .map(
              (bloque) => `
                <div
                  class="d-flex flex-column flex-sm-row justify-content-between align-items-sm-center gap-2 border rounded-3 px-3 py-2 bg-body-tertiary"
                >

                  <div
                    class="d-flex align-items-center gap-2"
                  >
                    <i
                      class="bi bi-clock text-primary"
                    ></i>

                    <span class="fw-semibold">
                      ${bloque.hora_inicio}
                      –
                      ${bloque.hora_fin}
                    </span>
                  </div>


                  <div
                    class="d-flex gap-2"
                  >

                    <button
                      type="button"
                      class="btn btn-sm btn-outline-primary btn-editar-bloque"
                      data-id="${bloque.id}"
                    >
                      <i class="bi bi-pencil"></i>

                      <span class="d-none d-sm-inline ms-1">
                        Editar
                      </span>
                    </button>


                    <button
                      type="button"
                      class="btn btn-sm btn-outline-danger btn-eliminar-bloque"
                      data-id="${bloque.id}"
                    >
                      <i class="bi bi-trash"></i>

                      <span class="d-none d-sm-inline ms-1">
                        Eliminar
                      </span>
                    </button>

                  </div>

                </div>
              `,
            )
            .join("")}
        </div>
      `;
    });

    conectarEventosBloques();
  }

  function conectarEventosBloques() {
    document.querySelectorAll(".btn-editar-bloque").forEach((boton) => {
      boton.addEventListener("click", () => {
        abrirEditarBloque(Number(boton.dataset.id));
      });
    });

    document.querySelectorAll(".btn-eliminar-bloque").forEach((boton) => {
      boton.addEventListener("click", () => {
        abrirEliminarBloque(Number(boton.dataset.id));
      });
    });
  }

  /* ═══════════════════════════════════════════════════════════
     NUEVO BLOQUE
  ═══════════════════════════════════════════════════════════ */

  function abrirNuevoBloque() {
    if (!idBarberoSeleccionado) {
      mostrarAlerta(alertaGeneral, "Seleccioná un barbero primero.", "warning");

      return;
    }

    formulario.reset();

    inputIdEditando.value = "";

    selectDia.value = "LUN";

    inputInicio.value = "";

    inputFin.value = "";

    modalTitulo.textContent = "Agregar disponibilidad";

    modalSubtitulo.textContent = "Definí un nuevo bloque de atención.";

    btnGuardar.textContent = "Guardar bloque";

    limpiarAlerta(alertaFormulario);

    modalDisponibilidad.show();
  }

  /* ═══════════════════════════════════════════════════════════
     EDITAR
  ═══════════════════════════════════════════════════════════ */

  function abrirEditarBloque(id) {
    const bloque = bloquesActuales.find(
      (item) => Number(item.id) === Number(id),
    );

    if (!bloque) {
      return;
    }

    inputIdEditando.value = bloque.id;

    selectDia.value = bloque.dia_semana;

    inputInicio.value = bloque.hora_inicio;

    inputFin.value = bloque.hora_fin;

    modalTitulo.textContent = "Editar disponibilidad";

    modalSubtitulo.textContent =
      "Modificá el día o el rango horario del bloque.";

    btnGuardar.textContent = "Guardar cambios";

    limpiarAlerta(alertaFormulario);

    modalDisponibilidad.show();
  }

  /* ═══════════════════════════════════════════════════════════
     GUARDAR
  ═══════════════════════════════════════════════════════════ */

  async function guardarBloque(evento) {
    evento.preventDefault();

    limpiarAlerta(alertaFormulario);

    if (!idBarberoSeleccionado) {
      mostrarAlerta(alertaFormulario, "No hay un barbero seleccionado.");

      return;
    }

    const dia = selectDia.value;

    const horaInicio = inputInicio.value;

    const horaFin = inputFin.value;

    if (!dia || !horaInicio || !horaFin) {
      mostrarAlerta(alertaFormulario, "Completá todos los campos.");

      return;
    }

    if (horaFin <= horaInicio) {
      mostrarAlerta(
        alertaFormulario,
        "La hora de fin tiene que ser mayor a la hora de inicio.",
      );

      return;
    }

    const idEditando = inputIdEditando.value;

    const esEdicion = Boolean(idEditando);

    const url = esEdicion
      ? `/api/mi-barberia/disponibilidad/${idEditando}/`
      : `/api/mi-barberia/barberos/${idBarberoSeleccionado}/disponibilidad/`;

    const metodo = esEdicion ? "PUT" : "POST";

    const payload = {
      dia_semana: dia,
      hora_inicio: horaInicio,
      hora_fin: horaFin,
    };

    btnGuardar.disabled = true;

    btnGuardar.innerHTML = `
      <span
        class="spinner-border spinner-border-sm me-2"
        aria-hidden="true"
      ></span>
      Guardando...
    `;

    try {
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
        mostrarAlerta(
          alertaFormulario,
          datos.error || "No se pudo guardar el bloque.",
        );

        return;
      }

      modalDisponibilidad.hide();

      mostrarAlerta(
        alertaGeneral,
        esEdicion
          ? "La disponibilidad se actualizó correctamente."
          : "El bloque de disponibilidad se agregó correctamente.",
        "success",
      );

      await cargarDisponibilidad();
    } catch (error) {
      console.error(error);

      mostrarAlerta(
        alertaFormulario,
        "Ocurrió un error al guardar la disponibilidad.",
      );
    } finally {
      btnGuardar.disabled = false;

      btnGuardar.textContent = esEdicion ? "Guardar cambios" : "Guardar bloque";
    }
  }

  /* ═══════════════════════════════════════════════════════════
     ELIMINAR
  ═══════════════════════════════════════════════════════════ */

  function abrirEliminarBloque(id) {
    const bloque = bloquesActuales.find(
      (item) => Number(item.id) === Number(id),
    );

    if (!bloque) {
      return;
    }

    idBloqueEliminar = bloque.id;

    textoBloqueEliminar.textContent = `${nombreDia(
      bloque.dia_semana,
    )} · ${bloque.hora_inicio} – ${bloque.hora_fin}`;

    limpiarAlerta(alertaEliminar);

    modalEliminar.show();
  }

  async function eliminarBloque() {
    if (!idBloqueEliminar) {
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
        `/api/mi-barberia/disponibilidad/${idBloqueEliminar}/`,
        {
          method: "DELETE",

          headers: {
            "X-CSRFToken": getCookie("csrftoken"),
          },
        },
      );

      const datos = await obtenerJson(respuesta);

      if (!respuesta.ok || !datos.ok) {
        mostrarAlerta(
          alertaEliminar,
          datos.error || "No se pudo eliminar el bloque.",
        );

        return;
      }

      modalEliminar.hide();

      idBloqueEliminar = null;

      mostrarAlerta(
        alertaGeneral,
        "El bloque de disponibilidad se eliminó correctamente.",
        "success",
      );

      await cargarDisponibilidad();
    } catch (error) {
      console.error(error);

      mostrarAlerta(alertaEliminar, "Ocurrió un error al eliminar el bloque.");
    } finally {
      btnConfirmarEliminar.disabled = false;

      btnConfirmarEliminar.textContent = "Eliminar";
    }
  }

  /* ═══════════════════════════════════════════════════════════
     EVENTOS
  ═══════════════════════════════════════════════════════════ */

  selectBarbero.addEventListener("change", () => {
    seleccionarBarbero(selectBarbero.value);
  });

  btnNuevoBloque.addEventListener("click", abrirNuevoBloque);

  formulario.addEventListener("submit", guardarBloque);

  btnConfirmarEliminar.addEventListener("click", eliminarBloque);

  /* ═══════════════════════════════════════════════════════════
     INICIO
  ═══════════════════════════════════════════════════════════ */

  cargarBarberos();
})();
