(() => {
  const API = {
    listar: "/api/notificaciones/",

    marcarLeida: (id) => `/api/notificaciones/${id}/leida/`,

    marcarTodas: "/api/notificaciones/leidas/",
  };

  const contenedor = document.getElementById("contenedor-notificaciones");

  const btnNotificaciones = document.getElementById("btn-notificaciones");

  const badge = document.getElementById("badge-notificaciones");

  const lista = document.getElementById("lista-notificaciones");

  const btnMarcarTodas = document.getElementById("btn-marcar-todas-leidas");

  if (
    !contenedor ||
    !btnNotificaciones ||
    !badge ||
    !lista ||
    !btnMarcarTodas
  ) {
    return;
  }

  let notificaciones = [];

  let cantidadSinLeer = 0;

  function haySesion() {
    return Boolean(sessionStorage.getItem("barberapp_usuario"));
  }

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

  function configurarVisibilidad() {
    if (haySesion()) {
      contenedor.classList.remove("d-none");

      cargarNotificaciones();
    } else {
      contenedor.classList.add("d-none");
    }
  }

  async function cargarNotificaciones() {
    if (!haySesion()) {
      return;
    }

    try {
      const respuesta = await fetch(API.listar);

      const datos = await obtenerJson(respuesta);

      if (!respuesta.ok || !datos.ok) {
        if (respuesta.status === 401) {
          contenedor.classList.add("d-none");

          return;
        }

        throw new Error(
          datos.error || "No se pudieron cargar las notificaciones.",
        );
      }

      notificaciones = datos.notificaciones || [];

      cantidadSinLeer = Number(datos.sin_leer || 0);

      actualizarBadge();

      renderizarNotificaciones();
    } catch (error) {
      console.error("Error al cargar notificaciones:", error);

      lista.innerHTML = `
        <div
          class="text-center py-4 px-3"
        >

          <i
            class="bi bi-exclamation-circle text-danger fs-4"
          ></i>

          <div
            class="small text-body-secondary mt-2"
          >
            No se pudieron cargar las notificaciones.
          </div>

        </div>
      `;
    }
  }

  function actualizarBadge() {
    if (cantidadSinLeer > 0) {
      badge.textContent =
        cantidadSinLeer > 99 ? "99+" : String(cantidadSinLeer);

      badge.classList.remove("d-none");

      btnMarcarTodas.classList.remove("d-none");
    } else {
      badge.textContent = "0";

      badge.classList.add("d-none");

      btnMarcarTodas.classList.add("d-none");
    }
  }

  function renderizarNotificaciones() {
    if (notificaciones.length === 0) {
      lista.innerHTML = `
        <div
          class="text-center py-5 px-3"
        >

          <i
            class="bi bi-bell fs-2 text-body-secondary"
          ></i>

          <div class="fw-semibold mt-2">
            Sin notificaciones
          </div>

          <div
            class="small text-body-secondary mt-1"
          >
            Los avisos de BarberApp aparecerán acá.
          </div>

        </div>
      `;

      return;
    }

    lista.innerHTML = notificaciones.map(crearNotificacionHTML).join("");

    conectarEventosNotificaciones();
  }

  function crearNotificacionHTML(notificacion) {
    const configuracion = obtenerConfiguracionTipo(notificacion.tipo);

    return `
      <button
        type="button"
        class="w-100 border-0 border-bottom text-start p-3 ${
          notificacion.leida ? "bg-body" : "bg-primary-subtle"
        } notificacion-item"
        data-notificacion-id="${notificacion.id}"
        data-leida="${notificacion.leida ? "true" : "false"}"
      >

        <div
          class="d-flex gap-3"
        >

          <div
            class="flex-shrink-0 fs-5 ${configuracion.color}"
          >
            <i
              class="bi ${configuracion.icono}"
            ></i>
          </div>


          <div
            class="flex-grow-1"
            style="min-width: 0;"
          >

            <div
              class="d-flex justify-content-between align-items-start gap-2"
            >

              <div
                class="${notificacion.leida ? "" : "fw-semibold"}"
              >
                ${configuracion.titulo}
              </div>


              ${
                !notificacion.leida
                  ? `
                    <span
                      class="badge bg-primary rounded-pill"
                      aria-label="Sin leer"
                    >
                      Nueva
                    </span>
                  `
                  : ""
              }

            </div>


            <div
              class="small mt-1"
            >
              ${escaparHTML(notificacion.mensaje)}
            </div>


            <div
              class="small text-body-secondary mt-2"
            >
              <i
                class="bi bi-clock me-1"
              ></i>

              ${formatearFecha(notificacion.fecha)}
            </div>

          </div>

        </div>

      </button>
    `;
  }

  function obtenerConfiguracionTipo(tipo) {
    const tipos = {
      TURNO_NUEVO: {
        titulo: "Nuevo turno",

        icono: "bi-calendar-plus",

        color: "text-primary",
      },

      TURNO_CANCELADO_CLIENTE: {
        titulo: "Turno cancelado",

        icono: "bi-calendar-x",

        color: "text-danger",
      },

      TURNO_CANCELADO_BARBERO: {
        titulo: "Turno cancelado",

        icono: "bi-calendar-x",

        color: "text-danger",
      },

      TURNO_FINALIZADO: {
        titulo: "Turno finalizado",

        icono: "bi-check-circle",

        color: "text-success",
      },
    };

    return (
      tipos[tipo] || {
        titulo: "Notificación",

        icono: "bi-bell",

        color: "text-secondary",
      }
    );
  }

  function formatearFecha(valor) {
    if (!valor) {
      return "";
    }

    const fecha = new Date(valor.replace(" ", "T"));

    if (Number.isNaN(fecha.getTime())) {
      return valor;
    }

    return fecha.toLocaleString("es-AR", {
      day: "2-digit",

      month: "2-digit",

      year: "numeric",

      hour: "2-digit",

      minute: "2-digit",
    });
  }

  function conectarEventosNotificaciones() {
    lista.querySelectorAll(".notificacion-item").forEach((item) => {
      item.addEventListener("click", async () => {
        const id = item.dataset.notificacionId;

        const leida = item.dataset.leida === "true";

        if (leida) {
          return;
        }

        await marcarLeida(id);
      });
    });
  }

  async function marcarLeida(id) {
    try {
      const respuesta = await fetch(API.marcarLeida(id), {
        method: "PATCH",

        headers: {
          "X-CSRFToken": getCookie("csrftoken"),
        },
      });

      const datos = await obtenerJson(respuesta);

      if (!respuesta.ok || !datos.ok) {
        throw new Error(
          datos.error || "No se pudo marcar la notificación como leída.",
        );
      }

      const indice = notificaciones.findIndex(
        (item) => String(item.id) === String(id),
      );

      if (indice !== -1 && !notificaciones[indice].leida) {
        notificaciones[indice].leida = true;

        cantidadSinLeer = Math.max(0, cantidadSinLeer - 1);
      }

      actualizarBadge();

      renderizarNotificaciones();
    } catch (error) {
      console.error(error);
    }
  }

  async function marcarTodasLeidas() {
    if (cantidadSinLeer === 0) {
      return;
    }

    btnMarcarTodas.disabled = true;

    const textoAnterior = btnMarcarTodas.textContent;

    btnMarcarTodas.textContent = "Marcando...";

    try {
      const respuesta = await fetch(API.marcarTodas, {
        method: "PATCH",

        headers: {
          "X-CSRFToken": getCookie("csrftoken"),
        },
      });

      const datos = await obtenerJson(respuesta);

      if (!respuesta.ok || !datos.ok) {
        throw new Error(
          datos.error || "No se pudieron marcar las notificaciones.",
        );
      }

      notificaciones = notificaciones.map((item) => ({
        ...item,
        leida: true,
      }));

      cantidadSinLeer = 0;

      actualizarBadge();

      renderizarNotificaciones();
    } catch (error) {
      console.error(error);
    } finally {
      btnMarcarTodas.disabled = false;

      btnMarcarTodas.textContent = textoAnterior;
    }
  }

  btnMarcarTodas.addEventListener("click", (event) => {
    event.stopPropagation();

    marcarTodasLeidas();
  });

  /*
   * La planificación pide consultar:
   * - al cargar la página
   * - al abrir el desplegable
   */

  btnNotificaciones.addEventListener("click", () => {
    cargarNotificaciones();
  });

  configurarVisibilidad();
})();
