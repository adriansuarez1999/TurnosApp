(() => {
  const MODO_ADMIN = "admin";
  const MODO_AGENDA = "agenda";

  const CLAVE_MODO = "barberapp_panel_modo";

  const body = document.body;

  const modoActual = body.dataset.panelMode || MODO_ADMIN;

  const esDueno = sessionStorage.getItem("barberapp_es_dueno") === "true";

  const esBarbero = sessionStorage.getItem("barberapp_es_barbero") === "true";

  const tabAdmin = document.getElementById("panel-tab-admin");

  const tabAgenda = document.getElementById("panel-tab-agenda");

  const sidebarAdmin = document.getElementById("sidebar-admin");

  const sidebarAgenda = document.getElementById("sidebar-agenda");

  const sidebarLabel = document.getElementById("panel-sidebar-label");

  const sidebarBarberia = document.getElementById("panel-sidebar-barberia");

  /*
   * -------------------------------------------------------
   * RESTAURAR ÚLTIMA PESTAÑA
   * -------------------------------------------------------
   */

  function restaurarUltimoModo() {
    /*
     * Solo tiene sentido restaurar la última pestaña
     * cuando el usuario tiene ambos roles.
     */
    if (!esDueno || !esBarbero) {
      return false;
    }

    const modoGuardado = sessionStorage.getItem(CLAVE_MODO);

    /*
     * Si todavía no hay nada guardado,
     * dejamos que abra normalmente.
     */
    if (modoGuardado !== MODO_ADMIN && modoGuardado !== MODO_AGENDA) {
      return false;
    }

    /*
     * Ya estamos en la pestaña guardada.
     * No hace falta redirigir.
     */
    if (modoGuardado === modoActual) {
      return false;
    }

    /*
     * Estamos entrando al panel desde otra pestaña,
     * por ejemplo "Mi panel", pero la última usada
     * fue "Mi agenda".
     */
    if (modoGuardado === MODO_AGENDA) {
      window.location.replace("/paginas/mi-agenda.html");

      return true;
    }

    if (modoGuardado === MODO_ADMIN) {
      window.location.replace("/paginas/mi-barberia.html");

      return true;
    }

    return false;
  }

  /*
   * -------------------------------------------------------
   * VALIDAR ACCESO
   * -------------------------------------------------------
   */

  function validarAcceso() {
    /*
     * Está intentando entrar al modo administración
     * pero no es dueño.
     */
    if (modoActual === MODO_ADMIN && !esDueno) {
      if (esBarbero) {
        window.location.replace("/paginas/mi-agenda.html");
      } else {
        window.location.replace("/");
      }

      return false;
    }

    /*
     * Está intentando entrar a Mi agenda
     * pero no es barbero.
     */
    if (modoActual === MODO_AGENDA && !esBarbero) {
      if (esDueno) {
        window.location.replace("/paginas/mi-barberia.html");
      } else {
        window.location.replace("/");
      }

      return false;
    }

    return true;
  }

  /*
   * -------------------------------------------------------
   * MOSTRAR PESTAÑAS SEGÚN ROLES
   * -------------------------------------------------------
   */

  function configurarPestanas() {
    if (esDueno && tabAdmin) {
      tabAdmin.classList.remove("d-none");
    }

    if (esBarbero && tabAgenda) {
      tabAgenda.classList.remove("d-none");
    }

    /*
     * Marcar visualmente el modo actual.
     */

    if (tabAdmin) {
      if (modoActual === MODO_ADMIN) {
        tabAdmin.classList.remove("btn-outline-light");

        tabAdmin.classList.add("btn-light");
      } else {
        tabAdmin.classList.remove("btn-light");

        tabAdmin.classList.add("btn-outline-light");
      }
    }

    if (tabAgenda) {
      if (modoActual === MODO_AGENDA) {
        tabAgenda.classList.remove("btn-outline-light");

        tabAgenda.classList.add("btn-light");
      } else {
        tabAgenda.classList.remove("btn-light");

        tabAgenda.classList.add("btn-outline-light");
      }
    }
  }

  /*
   * -------------------------------------------------------
   * SIDEBAR
   * -------------------------------------------------------
   */

  function configurarSidebar() {
    if (sidebarAdmin) {
      sidebarAdmin.classList.add("d-none");
    }

    if (sidebarAgenda) {
      sidebarAgenda.classList.add("d-none");
    }

    if (modoActual === MODO_ADMIN) {
      if (sidebarAdmin) {
        sidebarAdmin.classList.remove("d-none");
      }

      if (sidebarLabel) {
        sidebarLabel.textContent = "Administración";
      }
    } else {
      if (sidebarAgenda) {
        sidebarAgenda.classList.remove("d-none");
      }

      if (sidebarLabel) {
        sidebarLabel.textContent = "Mi agenda";
      }
    }
  }

  /*
   * -------------------------------------------------------
   * RECORDAR ÚLTIMA PESTAÑA
   * -------------------------------------------------------
   */

  function guardarModoActual() {
    sessionStorage.setItem(CLAVE_MODO, modoActual);
  }

  function configurarCambioDeModo() {
    if (tabAdmin) {
      tabAdmin.addEventListener("click", () => {
        sessionStorage.setItem(CLAVE_MODO, MODO_ADMIN);
      });
    }

    if (tabAgenda) {
      tabAgenda.addEventListener("click", () => {
        sessionStorage.setItem(CLAVE_MODO, MODO_AGENDA);
      });
    }
  }

  /*
   * -------------------------------------------------------
   * NOMBRE EN SIDEBAR
   * -------------------------------------------------------
   */

  async function cargarNombreSidebar() {
    if (!sidebarBarberia) {
      return;
    }

    /*
     * Si es dueño podemos obtener
     * el nombre de su barbería.
     */
    if (esDueno) {
      try {
        const respuesta = await fetch("/api/mi-barberia/");

        const datos = await respuesta.json();

        if (respuesta.ok && datos.ok) {
          sidebarBarberia.textContent = datos.nombre || "Mi barbería";

          return;
        }
      } catch (error) {
        console.error("Error al cargar la barbería:", error);
      }
    }

    /*
     * Para un usuario solamente barbero
     * mostramos su nombre guardado
     * en la sesión del frontend.
     */

    const usuarioGuardado = sessionStorage.getItem("barberapp_usuario");

    if (usuarioGuardado) {
      try {
        const usuario = JSON.parse(usuarioGuardado);

        sidebarBarberia.textContent = usuario.nombre || "Mi agenda";

        return;
      } catch {
        /*
         * barberapp_usuario también puede
         * estar almacenado como texto simple.
         */

        sidebarBarberia.textContent = usuarioGuardado;
      }
    } else {
      sidebarBarberia.textContent =
        modoActual === MODO_AGENDA ? "Mi agenda" : "Mi barbería";
    }
  }

  /*
   * -------------------------------------------------------
   * INICIO
   * -------------------------------------------------------
   */

  if (!validarAcceso()) {
    return;
  }

  /*
   * Si tiene ambos roles y la última pestaña
   * usada es distinta de la actual,
   * restauramos esa pestaña.
   */
  if (restaurarUltimoModo()) {
    return;
  }

  configurarPestanas();

  configurarSidebar();

  configurarCambioDeModo();

  guardarModoActual();

  cargarNombreSidebar();
})();
