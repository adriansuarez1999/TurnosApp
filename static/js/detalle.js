/* ═══════════════════════════════════════════════════════════
   detalle.js

   Vista de detalle de barbería.
═══════════════════════════════════════════════════════════ */

const MODO_SIMULADO_DETALLE = false;


const API_DETALLE = {

  barberia:
    id => `/api/barberias/${id}/`,

  barberos:
    id => `/api/barberos/?barberia=${id}`,

};



/* ═══════════════════════════════════════════════════════════
   OBTENER ID
═══════════════════════════════════════════════════════════ */

function obtenerIdDeURL() {

  const params =
    new URLSearchParams(
      window.location.search
    );


  return params.get('id');

}



/* ═══════════════════════════════════════════════════════════
   ESTADOS DE PANTALLA
═══════════════════════════════════════════════════════════ */

function mostrarEstado(
  mensaje,
  tipo = 'secondary'
) {

  const cont =
    document.getElementById(
      'detalle-contenido'
    );


  cont.innerHTML = `

    <section class="py-5">

      <div class="container">

        <div
          class="alert alert-${tipo}"
          role="alert"
        >
          ${mensaje}
        </div>

      </div>

    </section>

  `;

}



/* ═══════════════════════════════════════════════════════════
   CARGAR DETALLE
═══════════════════════════════════════════════════════════ */

async function cargarDetalleBarberia() {

  const id =
    obtenerIdDeURL();


  if (!id) {

    mostrarEstado(
      'No se especificó una barbería.',
      'warning'
    );

    return;

  }


  try {

    let barberia;
    let barberos;


    /* ── Simulación ─────────────────────────────────────── */

    if (MODO_SIMULADO_DETALLE) {

      await new Promise(
        resolve =>
          setTimeout(
            resolve,
            300
          )
      );


      barberia =
        BARBERIAS_MOCK.find(
          b =>
            String(b.id) ===
            String(id)
        );


      barberos =
        BARBEROS_MOCK.filter(
          b =>
            String(b.barberia) ===
            String(id)
        );

    }


    /* ── Backend Django ─────────────────────────────────── */

    else {

      const [
        respBarberia,
        respBarberos,

      ] = await Promise.all([

        fetch(
          API_DETALLE.barberia(id)
        ),

        fetch(
          API_DETALLE.barberos(id)
        ),

      ]);


      if (!respBarberia.ok) {

        throw new Error(
          'Barbería no encontrada'
        );

      }


      barberia =
        await respBarberia.json();


      barberos =
        respBarberos.ok
          ? await respBarberos.json()
          : [];

    }


    if (!barberia) {

      mostrarEstado(
        'No se encontró la barbería solicitada.',
        'warning'
      );

      return;

    }


    renderizarDetalle(
      barberia,
      barberos
    );

  }


  catch (error) {

    console.error(
      'Error al cargar el detalle:',
      error
    );


    mostrarEstado(
      'Ocurrió un error al cargar la barbería.',
      'danger'
    );

  }

}



/* ═══════════════════════════════════════════════════════════
   RENDER PRINCIPAL
═══════════════════════════════════════════════════════════ */

function renderizarDetalle(
  barberia,
  barberos
) {

  /* ── Datos principales ───────────────────────────────── */

  document
    .getElementById(
      'detalle-nombre'
    )
    .textContent =
      barberia.nombre;


  const zona =
    document.getElementById(
      'detalle-zona'
    );


  if (barberia.zona) {

    zona.textContent =
      barberia.zona;

  }

  else {

    zona.classList.add(
      'd-none'
    );

  }


  document
    .getElementById(
      'detalle-descripcion'
    )
    .textContent =
      barberia.descripcion || '';


  document.title =
    `${barberia.nombre} — BarberApp`;



  /* ═══════════════════════════════════════════════════════════
     FOTO PRINCIPAL
  ═══════════════════════════════════════════════════════════ */

  const fotoWrap =
    document.getElementById(
      'detalle-foto'
    );


  if (barberia.foto) {

    fotoWrap.innerHTML = `

      <img
        src="${barberia.foto}"
        alt="Foto de ${barberia.nombre}"
        class="w-100 h-100 object-fit-cover"
      >

    `;

  }

  else {

    fotoWrap.innerHTML = `

      <svg
        width="48"
        height="48"
        viewBox="0 0 24 24"
        fill="none"
        stroke="currentColor"
        stroke-width="1.5"
        class="text-primary"
      >

        <path d="M6 3v12"></path>

        <path
          d="M18 9a3 3 0 1 0 0-6"
        ></path>

        <path
          d="M6 21a3 3 0 1 0 0-6"
        ></path>

        <path
          d="M15 6l-9 9"
        ></path>

        <path
          d="M18 15l-3-3"
        ></path>

      </svg>

    `;

  }



  /* ═══════════════════════════════════════════════════════════
     PORTADA / GALERÍA
  ═══════════════════════════════════════════════════════════ */

  const portada =
    document.getElementById(
      'detalle-portada'
    );


  const seccionPortada =
    document.getElementById(
      'seccion-portada'
    );


  const fotos =
    barberia.fotos || [];


  if (fotos.length > 0) {

    portada.innerHTML = `

      <div
        id="carouselBarberia"
        class="carousel slide w-100 h-100"
        data-bs-ride="carousel"
      >

        <div
          class="carousel-inner w-100 h-100"
        >

          ${fotos.map(
            (url, index) => `

              <div
                class="carousel-item h-100
                ${index === 0 ? 'active' : ''}"
              >

                <img
                  src="${url}"
                  class="d-block w-100 h-100 object-fit-cover"
                  alt="Imagen de ${barberia.nombre}"
                >

              </div>

            `
          ).join('')}

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
                  Anterior
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
                  Siguiente
                </span>

              </button>

            `

            : ''
        }

      </div>

    `;

  }

  else {

    seccionPortada.classList.add(
      'd-none'
    );

  }



  /* ═══════════════════════════════════════════════════════════
     SERVICIOS
  ═══════════════════════════════════════════════════════════ */

  const listaServicios =
    document.getElementById(
      'lista-servicios'
    );


  const servicios =
    barberia.servicios || [];


  if (servicios.length === 0) {

    listaServicios.innerHTML = `

      <li class="col-12">

        <div
          class="alert alert-secondary mb-0"
        >
          Esta barbería todavía no cargó servicios.
        </div>

      </li>

    `;

  }

  else {

    listaServicios.innerHTML =
      servicios.map(

        servicio => `

          <li class="col">

            <div class="card h-100">

              <div
                class="card-body d-flex align-items-center justify-content-between gap-3"
              >

                <div>

                  <h3
                    class="h6 card-title mb-0"
                  >
                    ${servicio.nombre}
                  </h3>

                </div>


                <span
                  class="badge text-bg-primary fs-6"
                >
                  $${servicio.precio.toLocaleString('es-AR')}
                </span>

              </div>

            </div>

          </li>

        `

      ).join('');

  }



  /* ═══════════════════════════════════════════════════════════
     BARBEROS
  ═══════════════════════════════════════════════════════════ */

  const listaBarberos =
    document.getElementById(
      'lista-barberos'
    );


  if (!barberos || barberos.length === 0) {

    listaBarberos.innerHTML = `

      <li class="col-12">

        <div
          class="alert alert-secondary mb-0"
        >
          Todavía no hay barberos cargados.
        </div>

      </li>

    `;

  }

  else {

    listaBarberos.innerHTML =
      barberos.map(

        barbero => `

          <li class="col">

            <div class="card h-100">

              <div
                class="card-body d-flex align-items-center gap-3"
              >

                <div
                  class="rounded-circle overflow-hidden bg-body-tertiary border d-flex align-items-center justify-content-center flex-shrink-0"
                  style="width: 64px; height: 64px;"
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

                        <svg
                          width="28"
                          height="28"
                          viewBox="0 0 24 24"
                          fill="none"
                          stroke="currentColor"
                          stroke-width="2"
                          class="text-body-secondary"
                        >

                          <path
                            d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"
                          ></path>

                          <circle
                            cx="12"
                            cy="7"
                            r="4"
                          ></circle>

                        </svg>

                      `
                  }

                </div>


                <div>

                  <h3
                    class="h6 card-title mb-0"
                  >
                    ${barbero.nombre}
                  </h3>

                  <span
                    class="text-body-secondary small"
                  >
                    Barbero
                  </span>

                </div>

              </div>

            </div>

          </li>

        `

      ).join('');

  }



  /* ═══════════════════════════════════════════════════════════
     RESERVAR
  ═══════════════════════════════════════════════════════════ */

  document
    .getElementById(
      'btn-reservar-turno'
    )
    .addEventListener(
      'click',

      () => {

        window.location.href =
          `reservar.html?id=${barberia.id}`;

      }
    );

}



/* ═══════════════════════════════════════════════════════════
   INICIO
═══════════════════════════════════════════════════════════ */

cargarDetalleBarberia();