(() => {
  /* ═══════════════════════════════════════════════════════════
     detalle.js

     Perfil público de una barbería.
  ═══════════════════════════════════════════════════════════ */

  const MODO_SIMULADO_DETALLE = false;

  const API_DETALLE = {
    barberia: (id) => `/api/barberias/${id}/`,

    barberos: (id) => `/api/barberos/?barberia=${id}`,
  };

  /* ═══════════════════════════════════════════════════════════
     OBTENER ID
  ═══════════════════════════════════════════════════════════ */

  function obtenerIdDeURL() {
    const params = new URLSearchParams(window.location.search);

    return params.get("id");
  }

  /* ═══════════════════════════════════════════════════════════
     ESTADOS DE PANTALLA
  ═══════════════════════════════════════════════════════════ */

  function mostrarEstado(mensaje, tipo = "secondary") {
    const cont = document.getElementById("detalle-contenido");

    cont.innerHTML = `

      <div class="container py-5">

        <div
          class="alert alert-${tipo}"
          role="alert"
        >
          ${mensaje}
        </div>

      </div>

    `;
  }

  /* ═══════════════════════════════════════════════════════════
     CARGAR DETALLE
  ═══════════════════════════════════════════════════════════ */

  async function cargarDetalleBarberia() {
    const id = obtenerIdDeURL();

    if (!id) {
      mostrarEstado("No se especificó una barbería.", "warning");

      return;
    }

    try {
      let barberia;
      let barberos;

      /* ── Simulación ─────────────────────────────────────── */

      if (MODO_SIMULADO_DETALLE) {
        await new Promise((resolve) => setTimeout(resolve, 300));

        barberia = BARBERIAS_MOCK.find((b) => String(b.id) === String(id));

        barberos = BARBEROS_MOCK.filter(
          (b) => String(b.barberia) === String(id),
        );
      } else {
        /* ── Backend Django ─────────────────────────────────── */
        const [respBarberia, respBarberos] = await Promise.all([
          fetch(API_DETALLE.barberia(id)),

          fetch(API_DETALLE.barberos(id)),
        ]);

        if (!respBarberia.ok) {
          throw new Error("Barbería no encontrada");
        }

        barberia = await respBarberia.json();

        barberos = respBarberos.ok ? await respBarberos.json() : [];
      }

      if (!barberia) {
        mostrarEstado("No se encontró la barbería solicitada.", "warning");

        return;
      }

      renderizarDetalle(barberia, barberos);
    } catch (error) {
      console.error("Error al cargar el detalle:", error);

      mostrarEstado("Ocurrió un error al cargar la barbería.", "danger");
    }
  }

  /* ═══════════════════════════════════════════════════════════
     RENDER PRINCIPAL
  ═══════════════════════════════════════════════════════════ */

  function renderizarDetalle(barberia, barberos) {
    const servicios = barberia.servicios || [];

    const fotos = barberia.fotos || [];

    /* ═════════════════════════════════════════════════════════
       INFORMACIÓN PRINCIPAL
    ═════════════════════════════════════════════════════════ */

    document.getElementById("detalle-nombre").textContent = barberia.nombre;

    document.getElementById("detalle-descripcion").textContent =
      barberia.descripcion ||
      "Conocé sus servicios y reservá tu próximo turno.";

    document.title = `${barberia.nombre} — BarberApp`;

    /* Zona */

    const zona = document.getElementById("detalle-zona");

    if (barberia.zona) {
      zona.innerHTML = `
        <i class="bi bi-geo-alt me-1"></i>
        ${barberia.zona}
      `;
    } else {
      zona.classList.add("d-none");
    }

    /* Contadores */

    document.getElementById("detalle-cantidad-servicios").textContent =
      servicios.length;

    document.getElementById("detalle-cantidad-barberos").textContent =
      barberos?.length || 0;

    /* ═════════════════════════════════════════════════════════
       LOGO
    ═════════════════════════════════════════════════════════ */

    const fotoWrap = document.getElementById("detalle-foto");

    if (barberia.foto) {
      fotoWrap.innerHTML = `

        <img
          src="${barberia.foto}"
          alt="Logo de ${barberia.nombre}"
          class="w-100 h-100 object-fit-cover"
        >

      `;
    } else {
      fotoWrap.innerHTML = `

        <i
          class="bi bi-scissors"
          aria-hidden="true"
        ></i>

      `;
    }

    /* ═════════════════════════════════════════════════════════
       PORTADA / GALERÍA
    ═════════════════════════════════════════════════════════ */

    renderizarGaleria(barberia, fotos);

    /* ═════════════════════════════════════════════════════════
       SERVICIOS
    ═════════════════════════════════════════════════════════ */

    renderizarServicios(servicios);

    /* ═════════════════════════════════════════════════════════
       BARBEROS
    ═════════════════════════════════════════════════════════ */

    renderizarBarberos(barberos);

    /* ═════════════════════════════════════════════════════════
       RESERVAR
    ═════════════════════════════════════════════════════════ */

    document
      .getElementById("btn-reservar-turno")
      .addEventListener("click", () => {
        window.location.href = `reservar.html?id=${barberia.id}`;
      });
  }

  /* ═══════════════════════════════════════════════════════════
     GALERÍA
  ═══════════════════════════════════════════════════════════ */

  function renderizarGaleria(barberia, fotos) {
    const portada = document.getElementById("detalle-portada");

    if (!fotos.length) {
      portada.innerHTML = `

        <div
          class="barber-profile__cover-empty"
        >

          <i
            class="bi bi-shop"
            aria-hidden="true"
          ></i>

          <span>
            ${barberia.nombre}
          </span>

        </div>

      `;

      return;
    }

    portada.innerHTML = `

      <div
        id="carouselBarberia"
        class="carousel slide h-100"
      >

        <div
          class="carousel-inner h-100"
        >

          ${fotos
            .map(
              (url, index) => `

              <div
                class="carousel-item h-100 ${index === 0 ? "active" : ""}"
              >

                <img
                  src="${url}"
                  class="d-block w-100 h-100 object-fit-cover"
                  alt="Foto de ${barberia.nombre}"
                >

              </div>

            `,
            )
            .join("")}

        </div>


        ${
          fotos.length > 1
            ? `

              <button
                class="carousel-control-prev"
                type="button"
                data-bs-target="#carouselBarberia"
                data-bs-slide="prev"
              >

                <span
                  class="carousel-control-prev-icon"
                  aria-hidden="true"
                ></span>

                <span class="visually-hidden">
                  Foto anterior
                </span>

              </button>


              <button
                class="carousel-control-next"
                type="button"
                data-bs-target="#carouselBarberia"
                data-bs-slide="next"
              >

                <span
                  class="carousel-control-next-icon"
                  aria-hidden="true"
                ></span>

                <span class="visually-hidden">
                  Foto siguiente
                </span>

              </button>

            `
            : ""
        }

      </div>

    `;
  }

  /* ═══════════════════════════════════════════════════════════
     SERVICIOS
  ═══════════════════════════════════════════════════════════ */

  function renderizarServicios(servicios) {
    const lista = document.getElementById("lista-servicios");

    if (!servicios.length) {
      lista.innerHTML = `
      <li
        class="list-group-item py-4 text-center text-body-secondary"
      >
        <i
          class="bi bi-info-circle me-1"
        ></i>

        Esta barbería todavía no cargó servicios.
      </li>
    `;

      return;
    }

    lista.innerHTML = servicios
      .map((servicio) => {
        const promo = servicio.promocion;

        return `
        <li
          class="list-group-item barber-profile__service"
        >

          <div
            class="d-flex justify-content-between align-items-start gap-3 flex-wrap"
          >

            <div class="flex-grow-1">

              <div
                class="d-flex align-items-center gap-2 flex-wrap"
              >

                <div class="fw-semibold">
                  ${servicio.nombre}
                </div>

                ${
                  promo
                    ? `
                      <span
                        class="badge text-bg-success"
                      >
                        -${Number(promo.porcentaje_descuento)}%
                      </span>
                    `
                    : ""
                }

              </div>

              ${
                servicio.descripcion
                  ? `
                    <div
                      class="text-body-secondary small mt-1"
                    >
                      ${servicio.descripcion}
                    </div>
                  `
                  : ""
              }

              ${
                promo
                  ? `
                    <div
                      class="mt-2"
                    >

                      <div
                        class="small fw-semibold text-success"
                      >
                        ${promo.nombre}
                      </div>

                      <div
                        class="small text-body-secondary"
                      >
                        La promoción termina en:
                      </div>

                      <div
                        class="fw-semibold text-success"
                        data-promo-contador
                        data-fecha-fin="${promo.fecha_fin_datetime}"
                      >
                        Calculando...
                      </div>

                    </div>
                  `
                  : ""
              }

            </div>


            <div class="text-end">

              ${
                promo
                  ? `
                    <div
                      class="text-body-secondary text-decoration-line-through small"
                    >
                      $${Number(promo.precio_original).toLocaleString("es-AR")}
                    </div>

                    <div
                      class="barber-profile__price text-success fw-bold"
                    >
                      $${Number(promo.precio_final).toLocaleString("es-AR")}
                    </div>
                  `
                  : `
                    <span
                      class="barber-profile__price"
                    >
                      $${Number(servicio.precio).toLocaleString("es-AR")}
                    </span>
                  `
              }

            </div>

          </div>

        </li>
      `;
      })
      .join("");

    iniciarContadoresPromociones();
  }

  function iniciarContadoresPromociones() {
    actualizarContadoresPromociones();

    if (window.intervaloPromociones) {
      clearInterval(window.intervaloPromociones);
    }

    window.intervaloPromociones = setInterval(
      actualizarContadoresPromociones,
      1000,
    );
  }

  function actualizarContadoresPromociones() {
    const contadores = document.querySelectorAll("[data-promo-contador]");

    contadores.forEach((contador) => {
      const fechaFin = new Date(contador.dataset.fechaFin);

      const ahora = new Date();

      const diferencia = fechaFin.getTime() - ahora.getTime();

      if (diferencia <= 0) {
        contador.textContent = "Promoción finalizada";

        contador.classList.add("text-body-secondary");

        return;
      }

      const dias = Math.floor(diferencia / (1000 * 60 * 60 * 24));

      const horas = Math.floor((diferencia / (1000 * 60 * 60)) % 24);

      const minutos = Math.floor((diferencia / (1000 * 60)) % 60);

      const segundos = Math.floor((diferencia / 1000) % 60);

      contador.textContent =
        `${dias}d ` +
        `${String(horas).padStart(2, "0")}h ` +
        `${String(minutos).padStart(2, "0")}m ` +
        `${String(segundos).padStart(2, "0")}s`;
    });
  }

  /* ═══════════════════════════════════════════════════════════
     BARBEROS
  ═══════════════════════════════════════════════════════════ */

  function renderizarBarberos(barberos) {
    const lista = document.getElementById("lista-barberos");

    if (!barberos || barberos.length === 0) {
      lista.innerHTML = `

        <li
          class="list-group-item py-4 text-center text-body-secondary"
        >

          <i
            class="bi bi-info-circle me-1"
          ></i>

          Todavía no hay barberos cargados.

        </li>

      `;

      return;
    }

    lista.innerHTML = barberos
      .map(
        (barbero) => `

            <li
              class="list-group-item"
            >

              <div
                class="d-flex align-items-center gap-3"
              >

                <div
                  class="barber-profile__barber-photo"
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
                          class="bi bi-person"
                          aria-hidden="true"
                        ></i>

                      `
                  }

                </div>


                <div>

                  <div class="fw-semibold">
                    ${barbero.nombre}
                  </div>

                  <div
                    class="text-body-secondary small"
                  >
                    Barbero
                  </div>

                </div>

              </div>

            </li>

          `,
      )
      .join("");
  }

  /* ═══════════════════════════════════════════════════════════
     INICIO
  ═══════════════════════════════════════════════════════════ */

  cargarDetalleBarberia();
})();
