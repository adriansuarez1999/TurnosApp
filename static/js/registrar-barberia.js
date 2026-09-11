(() => {
  /* ═══════════════════════════════════════════════════════════
     registrar-barberia.js

     Alta de una barbería.
  ═══════════════════════════════════════════════════════════ */

  const API_REGISTRAR_BARBERIA = "/api/barberias/nueva/";

  const MODO_SIMULADO_REGISTRAR_BARBERIA = false;

  /* ═══════════════════════════════════════════════════════════
     REFERENCIAS
  ═══════════════════════════════════════════════════════════ */

  const formulario = document.getElementById("form-registrar-barberia");

  const btn = document.getElementById("btn-registrar-barberia-enviar");

  const alerta = document.getElementById("alerta-registrar-barberia");

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
     REGISTRAR
  ═══════════════════════════════════════════════════════════ */

  formulario.addEventListener(
    "submit",

    async (event) => {
      event.preventDefault();

      limpiarAlerta();

      const nombre = document.getElementById("rb-nombre").value.trim();

      const direccion = document.getElementById("rb-direccion").value.trim();

      const zona = document.getElementById("rb-zona").value.trim();

      const telefono = document.getElementById("rb-telefono").value.trim();

      const descripcion = document
        .getElementById("rb-descripcion")
        .value.trim();

      if (!nombre || !direccion || !zona) {
        mostrarAlerta("Completá nombre, dirección y zona.", "warning");

        return;
      }

      btn.disabled = true;

      btn.innerHTML = `

        <span
          class="spinner-border spinner-border-sm me-2"
          aria-hidden="true"
        ></span>

        Registrando...

      `;

      try {
        let datos;

        /* ── SIMULADO ─────────────────────────────────── */

        if (MODO_SIMULADO_REGISTRAR_BARBERIA) {
          await new Promise((resolve) => setTimeout(resolve, 800));

          datos = {
            ok: true,

            id: 99,

            nombre,
          };
        } else {

        /* ── BACKEND DJANGO ───────────────────────────── */
          const respuesta = await fetch(API_REGISTRAR_BARBERIA, {
            method: "POST",

            headers: {
              "Content-Type": "application/json",

              "X-CSRFToken": getCookie("csrftoken"),
            },

            body: JSON.stringify({
              nombre,
              direccion,
              zona,
              telefono,
              descripcion,
            }),
          });

          datos = await respuesta.json();
        }

        if (datos.ok) {
          sessionStorage.setItem("barberapp_es_dueno", "true");

          mostrarAlerta(
            "Barbería registrada correctamente. Te llevamos a tu panel.",
            "success",
          );

          setTimeout(
            () => {
              window.location.href = "/paginas/mi-barberia.html";
            },

            1200,
          );
        } else {
          mostrarAlerta(
            datos.error || "No se pudo registrar la barbería.",
            "danger",
          );
        }
      } catch (error) {
        console.error(error);

        mostrarAlerta("No se pudo conectar con el servidor.", "danger");
      } finally {
        btn.disabled = false;

        btn.textContent = "Registrar barbería";
      }
    },
  );
})();
