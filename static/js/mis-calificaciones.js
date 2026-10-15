(() => {
  const API = "/api/mi-agenda/calificaciones/";

  const estado = document.getElementById("estado-calificaciones");

  const contenido = document.getElementById("contenido-calificaciones");

  const lista = document.getElementById("lista-calificaciones");

  async function obtenerJson(respuesta) {
    try {
      return await respuesta.json();
    } catch {
      return {};
    }
  }

  function estrellas(puntuacion) {
    let html = "";

    for (let i = 1; i <= 5; i += 1) {
      html += `
        <i
          class="bi ${
            i <= puntuacion
              ? "bi-star-fill text-warning"
              : "bi-star text-body-secondary"
          }"
        ></i>
      `;
    }

    return html;
  }

  function formatearFecha(valor) {
    if (!valor) {
      return "";
    }

    const [anio, mes, dia] = valor.split("-").map(Number);

    const fecha = new Date(anio, mes - 1, dia);

    return fecha.toLocaleDateString("es-AR", {
      day: "numeric",
      month: "long",
      year: "numeric",
    });
  }

  async function cargarCalificaciones() {
    try {
      const respuesta = await fetch(API);

      const datos = await obtenerJson(respuesta);

      if (!respuesta.ok || !datos.ok) {
        throw new Error(
          datos.error || "No se pudieron cargar las calificaciones.",
        );
      }

      document.getElementById("promedio-calificaciones").textContent = Number(
        datos.promedio || 0,
      ).toFixed(2);

      document.getElementById("cantidad-calificaciones").textContent =
        datos.cantidad || 0;

      renderizarCalificaciones(datos.calificaciones || []);

      estado.classList.add("d-none");

      contenido.classList.remove("d-none");
    } catch (error) {
      console.error(error);

      estado.innerHTML = `
        <div
          class="alert alert-danger"
        >
          ${error.message}
        </div>
      `;
    }
  }

  function renderizarCalificaciones(calificaciones) {
    if (calificaciones.length === 0) {
      lista.innerHTML = `
        <div
          class="text-center py-5"
        >

          <i
            class="bi bi-star fs-1 text-body-secondary"
          ></i>

          <h3 class="h6 mt-3">
            Todavía no recibiste calificaciones
          </h3>

          <p
            class="text-body-secondary mb-0"
          >
            Las opiniones aparecerán acá cuando tus clientes califiquen turnos finalizados.
          </p>

        </div>
      `;

      return;
    }

    lista.innerHTML = calificaciones
      .map((item) => {
        return `
              <div
                class="border rounded-3 p-3"
              >

                <div
                  class="d-flex justify-content-between align-items-start gap-3 flex-wrap"
                >

                  <div>

                    <div class="fw-semibold">
                      ${item.cliente}
                    </div>

                    <div class="mt-1">
                      ${estrellas(Number(item.puntuacion))}
                    </div>

                  </div>


                  <div
                    class="small text-body-secondary"
                  >
                    ${formatearFecha(item.fecha)}
                  </div>

                </div>


                ${
                  item.comentario
                    ? `
                      <p class="mb-0 mt-3">
                        ${item.comentario}
                      </p>
                    `
                    : `
                      <p
                        class="mb-0 mt-3 text-body-secondary fst-italic"
                      >
                        Sin comentario.
                      </p>
                    `
                }

              </div>
            `;
      })
      .join("");
  }

  document.addEventListener("DOMContentLoaded", cargarCalificaciones);
})();
