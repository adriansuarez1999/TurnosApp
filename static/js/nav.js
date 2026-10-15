(() => {
  const navAuth = document.querySelector(".nav__auth");

  const navLogueado = document.getElementById("nav-logueado");

  const navNombre = document.getElementById("nav-nombre-usuario");

  const navPanelLink = document.getElementById("nav-panel-link");

  const navAgendaLink = document.getElementById("nav-agenda-link");

  const btnSalir = document.getElementById("btn-salir");

  const btnAccederNav = document.getElementById("btn-acceder");

  const btnCrearCuentaNav = document.getElementById("btn-crear-cuenta");

  function mostrarUsuarioLogueado(nombre, esDueno, esBarbero) {
    if (!navAuth || !navLogueado || !navNombre) {
      return;
    }

    navNombre.textContent = nombre;

    navAuth.style.display = "none";

    navLogueado.style.display = "flex";

    if (navPanelLink) {
      navPanelLink.style.display = esDueno ? "inline-flex" : "none";
    }

    if (navAgendaLink) {
      navAgendaLink.style.display = esBarbero ? "inline-flex" : "none";
    }
  }

  function mostrarNavSinSesion() {
    if (!navAuth || !navLogueado) {
      return;
    }

    navAuth.style.display = "flex";

    navLogueado.style.display = "none";

    if (navPanelLink) {
      navPanelLink.style.display = "none";
    }

    if (navAgendaLink) {
      navAgendaLink.style.display = "none";
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
