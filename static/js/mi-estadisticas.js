(() => {
  const API = "/api/mi-agenda/estadisticas/";

  const form = document.getElementById("form-filtro-estadisticas");

  const inputDesde = document.getElementById("estadisticas-desde");

  const inputHasta = document.getElementById("estadisticas-hasta");

  const btnLimpiar = document.getElementById("btn-limpiar-filtro");

  const estado = document.getElementById("estado-estadisticas");

  const contenido = document.getElementById("contenido-estadisticas");

  const alerta = document.getElementById("alerta-estadisticas");

  function formatearDinero(valor) {
    return Number(valor || 0).toLocaleString("es-AR", {
      style: "currency",
      currency: "ARS",
      minimumFractionDigits: 0,
    });
  }

  async function obtenerJson(respuesta) {
    try {
      return await respuesta.json();
    } catch {
      return {};
    }
  }

  function mostrarError(mensaje) {
    alerta.textContent = mensaje;

    alerta.className = "alert alert-danger";

    alerta.classList.remove("d-none");
  }

  function ocultarError() {
    alerta.className = "alert d-none";

    alerta.textContent = "";
  }

  async function cargarEstadisticas() {
    ocultarError();

    estado.classList.remove("d-none");

    contenido.classList.add("d-none");

    const params = new URLSearchParams();

    if (inputDesde.value) {
      params.set("desde", inputDesde.value);
    }

    if (inputHasta.value) {
      params.set("hasta", inputHasta.value);
    }

    try {
      const url = params.toString() ? `${API}?${params.toString()}` : API;

      const respuesta = await fetch(url);

      const datos = await obtenerJson(respuesta);

      if (!respuesta.ok || !datos.ok) {
        throw new Error(
          datos.error || "No se pudieron cargar las estadísticas.",
        );
      }

      document.getElementById("stat-atendidos").textContent =
        datos.turnos_atendidos;

      document.getElementById("stat-ausencias").textContent = datos.ausencias;

      document.getElementById("stat-cancelados").textContent = datos.cancelados;

      document.getElementById("stat-ingresos").textContent = formatearDinero(
        datos.ingresos_generados,
      );

      renderizarServicios(datos.servicios_mas_pedidos || []);

      estado.classList.add("d-none");

      contenido.classList.remove("d-none");
    } catch (error) {
      console.error(error);

      estado.classList.add("d-none");

      mostrarError(error.message);
    }
  }

  function renderizarServicios(servicios) {
    const contenedor = document.getElementById("lista-servicios-estadisticas");

    if (servicios.length === 0) {
      contenedor.innerHTML = `
        <div
          class="text-center py-4 text-body-secondary"
        >
          No hay servicios finalizados en este período.
        </div>
      `;

      return;
    }

    const maximo = Math.max(...servicios.map((item) => Number(item.cantidad)));

    contenedor.innerHTML = servicios
      .map((item) => {
        const porcentaje =
          maximo > 0 ? (Number(item.cantidad) / maximo) * 100 : 0;

        return `
              <div class="mb-3">

                <div
                  class="d-flex justify-content-between mb-1"
                >

                  <span class="fw-semibold">
                    ${item.servicio}
                  </span>

                  <span class="text-body-secondary">
                    ${item.cantidad}
                  </span>

                </div>


                <div
                  class="progress"
                  style="height: 10px;"
                >

                  <div
                    class="progress-bar"
                    role="progressbar"
                    style="width: ${porcentaje}%"
                    aria-valuenow="${item.cantidad}"
                    aria-valuemin="0"
                    aria-valuemax="${maximo}"
                  ></div>

                </div>

              </div>
            `;
      })
      .join("");
  }

  form.addEventListener("submit", (event) => {
    event.preventDefault();

    cargarEstadisticas();
  });

  btnLimpiar.addEventListener("click", () => {
    inputDesde.value = "";

    inputHasta.value = "";

    cargarEstadisticas();
  });

  document.addEventListener("DOMContentLoaded", cargarEstadisticas);
})();
