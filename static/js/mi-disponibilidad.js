(() => {
  const API = "/api/mi-agenda/disponibilidad/";

  const API_AGENDA = "/api/mi-agenda/turnos/";

  const DIAS = [
    {
      codigo: "LUN",
      nombre: "Lunes",
      numeroJS: 1,
    },
    {
      codigo: "MAR",
      nombre: "Martes",
      numeroJS: 2,
    },
    {
      codigo: "MIE",
      nombre: "Miércoles",
      numeroJS: 3,
    },
    {
      codigo: "JUE",
      nombre: "Jueves",
      numeroJS: 4,
    },
    {
      codigo: "VIE",
      nombre: "Viernes",
      numeroJS: 5,
    },
    {
      codigo: "SAB",
      nombre: "Sábado",
      numeroJS: 6,
    },
    {
      codigo: "DOM",
      nombre: "Domingo",
      numeroJS: 0,
    },
  ];

  let bloques = [];

  let bloqueOriginalEditado = null;

  const alerta = document.getElementById("alerta-disponibilidad");

  const estado = document.getElementById("estado-disponibilidad");

  const grilla = document.getElementById("grilla-disponibilidad");

  const btnNuevo = document.getElementById("btn-nuevo-bloque");

  const form = document.getElementById("form-bloque");

  const bloqueId = document.getElementById("bloque-id");

  const bloqueDia = document.getElementById("bloque-dia");

  const bloqueInicio = document.getElementById("bloque-inicio");

  const bloqueFin = document.getElementById("bloque-fin");

  const tituloModal = document.getElementById("titulo-modal-bloque");

  const errorBloque = document.getElementById("error-bloque");

  const btnGuardar = document.getElementById("btn-guardar-bloque");

  const modal = new bootstrap.Modal(document.getElementById("modal-bloque"));

  const modalTurnosAfectados = new bootstrap.Modal(
    document.getElementById("modal-turnos-afectados"),
  );

  const listaTurnosAfectados = document.getElementById(
    "lista-turnos-afectados",
  );

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

  function mostrarAlerta(mensaje, tipo = "success") {
    alerta.className = `alert alert-${tipo}`;

    alerta.textContent = mensaje;

    alerta.classList.remove("d-none");
  }

  function ocultarAlerta() {
    alerta.className = "alert d-none";

    alerta.textContent = "";
  }

  function fechaAISO(fecha) {
    const anio = fecha.getFullYear();

    const mes = String(fecha.getMonth() + 1).padStart(2, "0");

    const dia = String(fecha.getDate()).padStart(2, "0");

    return `${anio}-${mes}-${dia}`;
  }

  function sumarDias(fecha, cantidad) {
    const copia = new Date(
      fecha.getFullYear(),
      fecha.getMonth(),
      fecha.getDate(),
    );

    copia.setDate(copia.getDate() + cantidad);

    return copia;
  }

  function fechaDesdeISO(valor) {
    const [anio, mes, dia] = valor.split("-").map(Number);

    return new Date(anio, mes - 1, dia);
  }

  function nombreDia(codigo) {
    return DIAS.find((dia) => dia.codigo === codigo)?.nombre || codigo;
  }

  function formatearFecha(fechaISO) {
    const fecha = fechaDesdeISO(fechaISO);

    return fecha.toLocaleDateString("es-AR", {
      weekday: "long",
      day: "numeric",
      month: "long",
      year: "numeric",
    });
  }

  async function cargarDisponibilidad() {
    ocultarAlerta();

    estado.classList.remove("d-none");

    grilla.classList.add("d-none");

    try {
      const respuesta = await fetch(API);

      const datos = await obtenerJson(respuesta);

      if (!respuesta.ok || !datos.ok) {
        throw new Error(datos.error || "No se pudo cargar la disponibilidad.");
      }

      bloques = datos.disponibilidad || [];

      renderizar();
    } catch (error) {
      console.error(error);

      estado.innerHTML = `
        <div
          class="alert alert-danger mb-0"
        >
          ${escaparHTML(error.message)}
        </div>
      `;
    }
  }

  function renderizar() {
    grilla.innerHTML = DIAS.map((dia) => {
      const bloquesDia = bloques.filter(
        (bloque) => bloque.dia_semana === dia.codigo,
      );

      return `
              <div
                class="col-12 col-md-6 col-xl-4"
              >

                <div
                  class="card h-100"
                >

                  <div
                    class="card-header bg-body"
                  >

                    <h3
                      class="h6 mb-0"
                    >
                      ${dia.nombre}
                    </h3>

                  </div>


                  <div class="card-body">

                    ${
                      bloquesDia.length === 0
                        ? `
                          <p
                            class="text-body-secondary small mb-0"
                          >
                            Sin disponibilidad cargada.
                          </p>
                        `
                        : `
                          <div
                            class="vstack gap-2"
                          >

                            ${bloquesDia.map(crearBloqueHTML).join("")}

                          </div>
                        `
                    }

                  </div>

                </div>

              </div>
            `;
    }).join("");

    estado.classList.add("d-none");

    grilla.classList.remove("d-none");

    configurarEventos();
  }

  function crearBloqueHTML(bloque) {
    return `
      <div
        class="border rounded-3 p-2 d-flex justify-content-between align-items-center gap-2"
      >

        <div>

          <i
            class="bi bi-clock me-1 text-body-secondary"
          ></i>

          <span class="fw-semibold">
            ${escaparHTML(bloque.hora_inicio)}
          </span>

          <span class="text-body-secondary">
            a
          </span>

          <span class="fw-semibold">
            ${escaparHTML(bloque.hora_fin)}
          </span>

        </div>


        <div
          class="btn-group btn-group-sm"
        >

          <button
            type="button"
            class="btn btn-outline-secondary"
            data-editar="${bloque.id}"
            title="Editar"
          >
            <i class="bi bi-pencil"></i>
          </button>


          <button
            type="button"
            class="btn btn-outline-danger"
            data-eliminar="${bloque.id}"
            title="Eliminar"
          >
            <i class="bi bi-trash"></i>
          </button>

        </div>

      </div>
    `;
  }

  function configurarEventos() {
    document.querySelectorAll("[data-editar]").forEach((boton) => {
      boton.addEventListener("click", () => {
        abrirEditar(Number(boton.dataset.editar));
      });
    });

    document.querySelectorAll("[data-eliminar]").forEach((boton) => {
      boton.addEventListener("click", () => {
        eliminarBloque(Number(boton.dataset.eliminar));
      });
    });
  }

  function limpiarFormulario() {
    bloqueId.value = "";

    bloqueDia.value = "";

    bloqueInicio.value = "";

    bloqueFin.value = "";

    bloqueOriginalEditado = null;

    errorBloque.classList.add("d-none");

    errorBloque.textContent = "";
  }

  function abrirNuevo() {
    limpiarFormulario();

    tituloModal.textContent = "Agregar horario";

    btnGuardar.textContent = "Guardar";

    modal.show();
  }

  function abrirEditar(id) {
    const bloque = bloques.find((item) => Number(item.id) === Number(id));

    if (!bloque) {
      return;
    }

    limpiarFormulario();

    bloqueOriginalEditado = {
      id: bloque.id,

      dia_semana: bloque.dia_semana,

      hora_inicio: bloque.hora_inicio,

      hora_fin: bloque.hora_fin,
    };

    bloqueId.value = bloque.id;

    bloqueDia.value = bloque.dia_semana;

    bloqueInicio.value = bloque.hora_inicio;

    bloqueFin.value = bloque.hora_fin;

    tituloModal.textContent = "Editar horario";

    btnGuardar.textContent = "Guardar cambios";

    modal.show();
  }

  async function guardarBloque(event) {
    event.preventDefault();

    errorBloque.classList.add("d-none");

    const id = bloqueId.value;

    const editando = Boolean(id);

    if (!bloqueDia.value || !bloqueInicio.value || !bloqueFin.value) {
      errorBloque.textContent = "Completá todos los campos.";

      errorBloque.classList.remove("d-none");

      return;
    }

    const diaOriginal = bloqueOriginalEditado?.dia_semana || null;

    const payload = {
      dia_semana: bloqueDia.value,

      hora_inicio: bloqueInicio.value,

      hora_fin: bloqueFin.value,
    };

    btnGuardar.disabled = true;

    try {
      const respuesta = await fetch(editando ? `${API}${id}/` : API, {
        method: editando ? "PUT" : "POST",

        headers: {
          "Content-Type": "application/json",

          "X-CSRFToken": getCookie("csrftoken"),
        },

        body: JSON.stringify(payload),
      });

      const datos = await obtenerJson(respuesta);

      if (!respuesta.ok || !datos.ok) {
        throw new Error(datos.error || "No se pudo guardar el horario.");
      }

      modal.hide();

      mostrarAlerta(
        editando
          ? "Horario actualizado correctamente."
          : "Horario agregado correctamente.",
      );

      await cargarDisponibilidad();

      if (editando && diaOriginal) {
        await verificarTurnosAfectados(diaOriginal);
      }
    } catch (error) {
      console.error(error);

      errorBloque.textContent = error.message;

      errorBloque.classList.remove("d-none");
    } finally {
      btnGuardar.disabled = false;
    }
  }

  async function eliminarBloque(id) {
    const bloque = bloques.find((item) => Number(item.id) === Number(id));

    if (!bloque) {
      return;
    }

    const diaAfectado = bloque.dia_semana;

    const confirmar = window.confirm(
      `¿Eliminar el horario ${bloque.hora_inicio} a ${bloque.hora_fin}?`,
    );

    if (!confirmar) {
      return;
    }

    try {
      const respuesta = await fetch(`${API}${id}/`, {
        method: "DELETE",

        headers: {
          "X-CSRFToken": getCookie("csrftoken"),
        },
      });

      const datos = await obtenerJson(respuesta);

      if (!respuesta.ok || !datos.ok) {
        throw new Error(datos.error || "No se pudo eliminar el horario.");
      }

      mostrarAlerta("Horario eliminado correctamente.");

      await cargarDisponibilidad();

      await verificarTurnosAfectados(diaAfectado);
    } catch (error) {
      console.error(error);

      mostrarAlerta(error.message, "danger");
    }
  }

  async function verificarTurnosAfectados(diaCodigo) {
    try {
      const hoy = new Date();

      const hasta = sumarDias(hoy, 365);

      const params = new URLSearchParams({
        desde: fechaAISO(hoy),

        hasta: fechaAISO(hasta),
      });

      const respuesta = await fetch(`${API_AGENDA}?${params.toString()}`);

      const datos = await obtenerJson(respuesta);

      if (!respuesta.ok || !datos.ok) {
        return;
      }

      const turnos = datos.turnos || [];

      const diaConfiguracion = DIAS.find((dia) => dia.codigo === diaCodigo);

      if (!diaConfiguracion) {
        return;
      }

      const turnosDelDia = turnos.filter((turno) => {
        if (turno.estado !== "CONFIRMADO") {
          return false;
        }

        const fecha = fechaDesdeISO(turno.fecha);

        return fecha.getDay() === diaConfiguracion.numeroJS;
      });

      const bloquesActualesDia = bloques.filter(
        (bloque) => bloque.dia_semana === diaCodigo,
      );

      const afectados = turnosDelDia.filter(
        (turno) => !turnoCubiertoPorDisponibilidad(turno, bloquesActualesDia),
      );

      if (afectados.length > 0) {
        mostrarTurnosAfectados(afectados, diaCodigo);
      }
    } catch (error) {
      console.error("No se pudieron revisar turnos afectados:", error);
    }
  }

  function turnoCubiertoPorDisponibilidad(turno, bloquesDia) {
    return bloquesDia.some((bloque) => {
      const inicioTurno = turno.hora_inicio.substring(0, 5);

      const finTurno = turno.hora_fin.substring(0, 5);

      const inicioBloque = bloque.hora_inicio.substring(0, 5);

      const finBloque = bloque.hora_fin.substring(0, 5);

      return inicioTurno >= inicioBloque && finTurno <= finBloque;
    });
  }

  function mostrarTurnosAfectados(turnos, diaCodigo) {
    listaTurnosAfectados.innerHTML = `
        <div class="mb-1">

          <strong>
            ${nombreDia(diaCodigo)}
          </strong>

          <span class="text-body-secondary">
            — ${
              turnos.length === 1
                ? "1 turno afectado"
                : `${turnos.length} turnos afectados`
            }
          </span>

        </div>
      `;

    listaTurnosAfectados.innerHTML += turnos
      .map((turno) => {
        return `
              <div
                class="border rounded-3 p-3"
              >

                <div
                  class="d-flex justify-content-between align-items-start flex-wrap gap-2"
                >

                  <div>

                    <div class="fw-semibold">
                      ${escaparHTML(turno.cliente)}
                    </div>

                    <div
                      class="small text-body-secondary"
                    >
                      ${escaparHTML(turno.servicio)}
                    </div>

                  </div>


                  <span
                    class="badge text-bg-warning"
                  >
                    Fuera de disponibilidad
                  </span>

                </div>


                <hr class="my-2">


                <div
                  class="row g-2 small"
                >

                  <div class="col-12 col-md-6">

                    <i
                      class="bi bi-calendar3 me-1"
                    ></i>

                    ${escaparHTML(formatearFecha(turno.fecha))}

                  </div>


                  <div class="col-12 col-md-6">

                    <i
                      class="bi bi-clock me-1"
                    ></i>

                    ${escaparHTML(turno.hora_inicio)}

                    a

                    ${escaparHTML(turno.hora_fin)}

                  </div>

                </div>

              </div>
            `;
      })
      .join("");

    modalTurnosAfectados.show();
  }

  btnNuevo.addEventListener("click", abrirNuevo);

  form.addEventListener("submit", guardarBloque);

  document.addEventListener("DOMContentLoaded", cargarDisponibilidad);
})();
