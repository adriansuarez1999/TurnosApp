(() => {
  const navAuth = document.querySelector(".nav__auth");

  const navLogueado = document.getElementById("nav-logueado");

  const navNombre = document.getElementById("nav-nombre-usuario");

  const navPanelLink = document.getElementById("nav-panel-link");

  const btnSalir = document.getElementById("btn-salir");

  const btnAccederNav = document.getElementById("btn-acceder");

  const btnCrearCuentaNav = document.getElementById("btn-crear-cuenta");

  const MODO_ADMIN = "admin";

  const MODO_AGENDA = "agenda";

  const CLAVE_MODO = "barberapp_panel_modo";

  function obtenerDestinoPanel(esDueno, esBarbero) {
    const modoGuardado = sessionStorage.getItem(CLAVE_MODO);

    /*
     * Si tiene ambos roles,
     * respetamos la última pestaña utilizada.
     */
    if (esDueno && esBarbero) {
      if (modoGuardado === MODO_AGENDA) {
        return "/paginas/mi-agenda.html";
      }

      if (modoGuardado === MODO_ADMIN) {
        return "/paginas/mi-barberia.html";
      }

      /*
       * Primera vez:
       * por defecto abre Administración.
       */
      return "/paginas/mi-barberia.html";
    }

    /*
     * Solo dueño.
     */
    if (esDueno) {
      return "/paginas/mi-barberia.html";
    }

    /*
     * Solo barbero.
     */
    if (esBarbero) {
      return "/paginas/mi-agenda.html";
    }

    return "/";
  }

  function configurarBotonPanel(esDueno, esBarbero) {
    if (!navPanelLink) {
      return;
    }

    const tienePanel = esDueno || esBarbero;

    if (!tienePanel) {
      navPanelLink.style.display = "none";

      navPanelLink.href = "/";

      return;
    }

    navPanelLink.style.display = "inline-flex";

    navPanelLink.href = obtenerDestinoPanel(esDueno, esBarbero);
  }

  function mostrarUsuarioLogueado(nombre, esDueno, esBarbero) {
    if (!navAuth || !navLogueado || !navNombre) {
      return;
    }

    navNombre.textContent = nombre;

    navAuth.style.display = "none";

    navLogueado.style.display = "flex";

    configurarBotonPanel(esDueno, esBarbero);
  }

  function mostrarNavSinSesion() {
    if (!navAuth || !navLogueado) {
      return;
    }

    navAuth.style.display = "flex";

    navLogueado.style.display = "none";

    if (navPanelLink) {
      navPanelLink.style.display = "none";

      navPanelLink.href = "/";
    }

    if (navNombre) {
      navNombre.textContent = "";
    }
  }

  function restaurarNavbar() {
    const usuarioGuardado = sessionStorage.getItem("barberapp_usuario");

    const esDuenoGuardado =
      sessionStorage.getItem("barberapp_es_dueno") === "true";

    const esBarberoGuardado =
      sessionStorage.getItem("barberapp_es_barbero") === "true";

    if (usuarioGuardado) {
      mostrarUsuarioLogueado(
        usuarioGuardado,
        esDuenoGuardado,
        esBarberoGuardado,
      );
    } else {
      mostrarNavSinSesion();
    }
  }

  /*
   * Antes de entrar al panel,
   * recalculamos el destino por si
   * cambió la última pestaña usada.
   */

  if (navPanelLink) {
    navPanelLink.addEventListener("click", (event) => {
      const esDueno = sessionStorage.getItem("barberapp_es_dueno") === "true";

      const esBarbero =
        sessionStorage.getItem("barberapp_es_barbero") === "true";

      if (!esDueno && !esBarbero) {
        return;
      }

      event.preventDefault();

      window.location.href = obtenerDestinoPanel(esDueno, esBarbero);
    });
  }

  restaurarNavbar();

  if (btnSalir) {
    btnSalir.addEventListener("click", async () => {
      try {
        await fetch("/api/logout/", {
          method: "POST",

          headers: {
            "X-CSRFToken": getCookie("csrftoken"),
          },
        });
      } catch (error) {
        console.error("Error al cerrar sesión:", error);
      }

      sessionStorage.removeItem("barberapp_usuario");

      sessionStorage.removeItem("barberapp_es_dueno");

      sessionStorage.removeItem("barberapp_es_barbero");

      sessionStorage.removeItem("barberapp_id_barberia");

      sessionStorage.removeItem("barberapp_id_barbero");

      sessionStorage.removeItem("barberapp_panel_modo");

      mostrarNavSinSesion();

      window.location.href = "/";
    });
  }

  if (btnAccederNav) {
    btnAccederNav.addEventListener("click", () => {
      const modalLogin = document.getElementById("modal-login");

      if (modalLogin) {
        return;
      }

      window.location.href = "/?auth=login";
    });
  }

  if (btnCrearCuentaNav) {
    btnCrearCuentaNav.addEventListener("click", () => {
      const modalRegistro = document.getElementById("modal-registro");

      if (modalRegistro) {
        return;
      }

      window.location.href = "/?auth=registro";
    });
  }

  window.BarberAppNav = {
    mostrarUsuarioLogueado,
    mostrarNavSinSesion,
    restaurarNavbar,
  };
})();
