(() => {
  /* ═══════════════════════════════════════════════════════════
     mis-informes.js

     Dashboard de estadísticas.

     GET
     /api/mi-barberia/informes/
     ?desde=YYYY-MM-DD
     &hasta=YYYY-MM-DD
  ═══════════════════════════════════════════════════════════ */

  const API_INFORMES = "/api/mi-barberia/informes/";

  let graficoTurnosDia = null;

  let graficoTurnosEstado = null;

  /* ═══════════════════════════════════════════════════════════
     REFERENCIAS
  ═══════════════════════════════════════════════════════════ */

  const inputDesde = document.getElementById("inf-desde");

  const inputHasta = document.getElementById("inf-hasta");

  const btnFiltrar = document.getElementById("btn-filtrar-informes");

  const btnLimpiar = document.getElementById("btn-limpiar-filtro");

  const btnMes = document.getElementById("btn-periodo-mes");

  const btn30 = document.getElementById("btn-periodo-30");

  const btnTodo = document.getElementById("btn-periodo-todo");

  const estadoInformes = document.getElementById("estado-informes");

  const contenido = document.getElementById("informes-contenido");

  const alerta = document.getElementById("alerta-informes");

  const statIngresos = document.getElementById("stat-ingresos");

  const statTurnos = document.getElementById("stat-turnos");

  const statDias = document.getElementById("stat-dias");

  const resumenEstados = document.getElementById("resumen-estados");

  const tablaTurnos = document.getElementById("tabla-turnos-dia");

  /* ═══════════════════════════════════════════════════════════
     CARGAR INFORME
  ═══════════════════════════════════════════════════════════ */

  async function cargarInformes() {
    limpiarAlerta();

    if (
      inputDesde.value &&
      inputHasta.value &&
      inputDesde.value > inputHasta.value
    ) {
      mostrarAlerta(
        'La fecha "Desde" no puede ser posterior a la fecha "Hasta".',
        "warning",
      );

      return;
    }

    mostrarCarga();

    const params = new URLSearchParams();

    if (inputDesde.value) {
      params.set("desde", inputDesde.value);
    }

    if (inputHasta.value) {
      params.set("hasta", inputHasta.value);
    }

    let url = API_INFORMES;

    if (params.toString()) {
      url += `?${params.toString()}`;
    }

    try {
      const respuesta = await fetch(url);

      const datos = await respuesta.json();

      if (!respuesta.ok || !datos.ok) {
        throw new Error(datos.error || "No se pudieron cargar los informes.");
      }

      renderizarInforme(datos);

      estadoInformes.classList.add("d-none");

      contenido.classList.remove("d-none");
    } catch (error) {
      console.error(error);

      mostrarError(error.message || "Ocurrió un error al cargar los informes.");
    }
  }

  /* ═══════════════════════════════════════════════════════════
     CARGA
  ═══════════════════════════════════════════════════════════ */

  function mostrarCarga() {
    contenido.classList.add("d-none");

    estadoInformes.classList.remove("d-none");

    estadoInformes.innerHTML = `

      <div
        class="d-flex align-items-center gap-2 text-body-secondary"
      >

        <div
          class="spinner-border spinner-border-sm"
          role="status"
        ></div>

        <span>
          Cargando informe...
        </span>

      </div>

    `;
  }

  function mostrarError(mensaje) {
    contenido.classList.add("d-none");

    estadoInformes.classList.remove("d-none");

    estadoInformes.innerHTML = `

      <div
        class="alert alert-danger mb-0"
        role="alert"
      >
        ${mensaje}
      </div>

    `;
  }

  /* ═══════════════════════════════════════════════════════════
     RENDER GENERAL
  ═══════════════════════════════════════════════════════════ */

  function renderizarInforme(datos) {
    const totalTurnos = datos.turnos_por_estado.reduce(
      (total, item) => total + Number(item.cantidad),

      0,
    );

    const diasConTurnos = datos.turnos_por_dia.length;

    /* ── Métricas ─────────────────────────────────────── */

    statIngresos.textContent = formatearDinero(datos.ingresos_totales);

    statTurnos.textContent = totalTurnos.toLocaleString("es-AR");

    statDias.textContent = diasConTurnos.toLocaleString("es-AR");

    /* ── Estados ──────────────────────────────────────── */

    renderizarResumenEstados(datos.turnos_por_estado);

    /* ── Tabla ────────────────────────────────────────── */

    renderizarTabla(datos.turnos_por_dia);

    /* ── Charts ───────────────────────────────────────── */

    renderizarGraficoTurnosDia(datos.turnos_por_dia);

    renderizarGraficoEstados(datos.turnos_por_estado);
  }

  /* ═══════════════════════════════════════════════════════════
     TARJETAS DE ESTADO
  ═══════════════════════════════════════════════════════════ */

  function renderizarResumenEstados(estados) {
    resumenEstados.innerHTML = "";

    if (estados.length === 0) {
      resumenEstados.innerHTML = `

        <div class="col-12">

          <div
            class="alert alert-secondary mb-0"
          >
            No hay datos para el período seleccionado.
          </div>

        </div>

      `;

      return;
    }

    resumenEstados.innerHTML = estados
      .map(
        (item) => `

            <div
              class="col-sm-6 col-xl-3"
            >

              <div
                class="border rounded p-3 h-100"
              >

                <div
                  class="text-body-secondary small mb-1"
                >
                  ${formatearEstado(item.estado)}
                </div>


                <div
                  class="fs-4 fw-semibold"
                >
                  ${Number(item.cantidad).toLocaleString("es-AR")}
                </div>

              </div>

            </div>

          `,
      )
      .join("");
  }

  /* ═══════════════════════════════════════════════════════════
     TABLA
  ═══════════════════════════════════════════════════════════ */

  function renderizarTabla(dias) {
    if (dias.length === 0) {
      tablaTurnos.innerHTML = `

        <tr>

          <td
            colspan="2"
            class="text-center text-body-secondary py-4"
          >
            No hay turnos registrados en este período.
          </td>

        </tr>

      `;

      return;
    }

    tablaTurnos.innerHTML = dias
      .map(
        (dia) => `

            <tr>

              <td class="ps-4">

                ${formatearFecha(dia.fecha)}

              </td>


              <td class="text-end pe-4">

                <span class="fw-semibold">

                  ${Number(dia.cantidad).toLocaleString("es-AR")}

                </span>

              </td>

            </tr>

          `,
      )
      .join("");
  }

  /* ═══════════════════════════════════════════════════════════
     GRÁFICO TURNOS POR DÍA
  ═══════════════════════════════════════════════════════════ */

  function renderizarGraficoTurnosDia(dias) {
    const canvas = document.getElementById("grafico-turnos-dia");

    if (graficoTurnosDia) {
      graficoTurnosDia.destroy();
    }

    const etiquetas = dias.map((item) => formatearFechaCorta(item.fecha));

    const cantidades = dias.map((item) => Number(item.cantidad));

    graficoTurnosDia = new Chart(canvas, {
      type: "line",

      data: {
        labels: etiquetas,

        datasets: [
          {
            label: "Turnos",

            data: cantidades,

            tension: 0.3,

            fill: true,

            borderColor: "#62B47A",

            backgroundColor: "rgba(98, 180, 122, 0.14)",

            pointBackgroundColor: "#247345",

            pointBorderColor: "#FFFDF9",

            pointBorderWidth: 2,

            pointRadius: 4,

            pointHoverRadius: 6,
          },
        ],
      },

      options: {
        responsive: true,

        maintainAspectRatio: false,

        interaction: {
          intersect: false,

          mode: "index",
        },

        plugins: {
          legend: {
            display: false,
          },
        },

        scales: {
          y: {
            beginAtZero: true,

            ticks: {
              precision: 0,
            },
          },
        },
      },
    });
  }

  /* ═══════════════════════════════════════════════════════════
     GRÁFICO ESTADOS
  ═══════════════════════════════════════════════════════════ */

  function renderizarGraficoEstados(estados) {
    const canvas = document.getElementById("grafico-turnos-estado");

    if (graficoTurnosEstado) {
      graficoTurnosEstado.destroy();
    }

    graficoTurnosEstado = new Chart(canvas, {
      type: "doughnut",

      data: {
        labels: estados.map((item) => formatearEstado(item.estado)),

        datasets: [
          {
            data: estados.map((item) => Number(item.cantidad)),

            backgroundColor: [
              "#62B47A",
              "#BCE5C7",
              "#E9DDCB",
              "#8BCB9E",
              "#DDF2E2",
              "#247345",
            ],

            borderColor: "#FFFDF9",

            borderWidth: 3,

            hoverOffset: 6,
          },
        ],
      },

      options: {
        responsive: true,

        maintainAspectRatio: false,

        cutout: "65%",

        plugins: {
          legend: {
            position: "bottom",
          },
        },
      },
    });
  }

  /* ═══════════════════════════════════════════════════════════
     FILTRAR
  ═══════════════════════════════════════════════════════════ */

  btnFiltrar.addEventListener("click", cargarInformes);

  /* ═══════════════════════════════════════════════════════════
     LIMPIAR
  ═══════════════════════════════════════════════════════════ */

  btnLimpiar.addEventListener(
    "click",

    () => {
      inputDesde.value = "";

      inputHasta.value = "";

      cargarInformes();
    },
  );

  /* ═══════════════════════════════════════════════════════════
     ESTE MES
  ═══════════════════════════════════════════════════════════ */

  btnMes.addEventListener(
    "click",

    () => {
      const hoy = new Date();

      const inicioMes = new Date(hoy.getFullYear(), hoy.getMonth(), 1);

      inputDesde.value = fechaParaInput(inicioMes);

      inputHasta.value = fechaParaInput(hoy);

      cargarInformes();
    },
  );

  /* ═══════════════════════════════════════════════════════════
     ÚLTIMOS 30 DÍAS
  ═══════════════════════════════════════════════════════════ */

  btn30.addEventListener(
    "click",

    () => {
      const hoy = new Date();

      const hace30Dias = new Date();

      hace30Dias.setDate(hoy.getDate() - 29);

      inputDesde.value = fechaParaInput(hace30Dias);

      inputHasta.value = fechaParaInput(hoy);

      cargarInformes();
    },
  );

  /* ═══════════════════════════════════════════════════════════
     TODO
  ═══════════════════════════════════════════════════════════ */

  btnTodo.addEventListener(
    "click",

    () => {
      inputDesde.value = "";

      inputHasta.value = "";

      cargarInformes();
    },
  );

  /* ═══════════════════════════════════════════════════════════
     FORMATEADORES
  ═══════════════════════════════════════════════════════════ */

  function formatearDinero(valor) {
    return new Intl.NumberFormat("es-AR", {
      style: "currency",

      currency: "ARS",

      maximumFractionDigits: 0,
    }).format(Number(valor || 0));
  }

  function formatearFecha(fecha) {
    if (!fecha) {
      return "—";
    }

    const [anio, mes, dia] = fecha.split("-");

    return `${dia}/${mes}/${anio}`;
  }

  function formatearFechaCorta(fecha) {
    if (!fecha) {
      return "";
    }

    const [, mes, dia] = fecha.split("-");

    return `${dia}/${mes}`;
  }

  function formatearEstado(estado) {
    if (!estado) {
      return "Sin estado";
    }

    const texto = String(estado).replaceAll("_", " ").toLowerCase();

    return texto.charAt(0).toUpperCase() + texto.slice(1);
  }

  function fechaParaInput(fecha) {
    const anio = fecha.getFullYear();

    const mes = String(fecha.getMonth() + 1).padStart(2, "0");

    const dia = String(fecha.getDate()).padStart(2, "0");

    return `${anio}-${mes}-${dia}`;
  }

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
     INICIO
  ═══════════════════════════════════════════════════════════ */

  cargarInformes();
})();
