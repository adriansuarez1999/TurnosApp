(() => {
  /* ═══════════════════════════════════════════════════════════
     nav.js

     Estado global del navbar.
     Se carga en todas las páginas mediante nav_completa.html.
  ═══════════════════════════════════════════════════════════ */

  /* REFERENCIAS */

  const navAuth = document.querySelector(".nav__auth");

  const navLogueado = document.getElementById("nav-logueado");

  const navNombre = document.getElementById("nav-nombre-usuario");

  const navPanelLink = document.getElementById("nav-panel-link");

  const btnSalir = document.getElementById("btn-salir");

  const btnAccederNav = document.getElementById("btn-acceder");

  const btnCrearCuentaNav = document.getElementById("btn-crear-cuenta");

  /* ═══════════════════════════════════════════════════════════
     USUARIO LOGUEADO
  ═══════════════════════════════════════════════════════════ */

  function mostrarUsuarioLogueado(nombre, esDueno) {
    if (!navAuth || !navLogueado || !navNombre) {
      return;
    }

    navNombre.textContent = nombre;

    navAuth.style.display = "none";

    navLogueado.style.display = "flex";

    if (navPanelLink) {
      navPanelLink.style.display = esDueno ? "inline-flex" : "none";
    }
  }

  /* ═══════════════════════════════════════════════════════════
     USUARIO SIN SESIÓN
  ═══════════════════════════════════════════════════════════ */

  function mostrarNavSinSesion() {
    if (!navAuth || !navLogueado) {
      return;
    }

    navAuth.style.display = "flex";

    navLogueado.style.display = "none";

    if (navPanelLink) {
      navPanelLink.style.display = "none";
    }

    if (navNombre) {
      navNombre.textContent = "";
    }
  }

  /* ═══════════════════════════════════════════════════════════
     RESTAURAR SESIÓN
  ═══════════════════════════════════════════════════════════ */

  function restaurarNavbar() {
    const usuarioGuardado = sessionStorage.getItem("barberapp_usuario");

    const esDuenoGuardado =
      sessionStorage.getItem("barberapp_es_dueno") === "true";

    if (usuarioGuardado) {
      mostrarUsuarioLogueado(usuarioGuardado, esDuenoGuardado);
    } else {
      mostrarNavSinSesion();
    }
  }

  restaurarNavbar();

  /* ═══════════════════════════════════════════════════════════
     LOGOUT
  ═══════════════════════════════════════════════════════════ */

  if (btnSalir) {
    btnSalir.addEventListener(
      "click",

      async () => {
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

        mostrarNavSinSesion();

        window.location.href = "/";
      },
    );
  }

  /* ═══════════════════════════════════════════════════════════
     ACCEDER DESDE PÁGINAS QUE NO SON HOME
  ═══════════════════════════════════════════════════════════ */

  if (btnAccederNav) {
    btnAccederNav.addEventListener(
      "click",

      () => {
        /*
          Si existe modal-login significa que estamos
          en el Home.

          En ese caso main.js se encarga de abrirlo.
        */

        const modalLogin = document.getElementById("modal-login");

        if (modalLogin) {
          return;
        }

        window.location.href = "/?auth=login";
      },
    );
  }

  /* ═══════════════════════════════════════════════════════════
     CREAR CUENTA DESDE OTRAS PÁGINAS
  ═══════════════════════════════════════════════════════════ */

  if (btnCrearCuentaNav) {
    btnCrearCuentaNav.addEventListener(
      "click",

      () => {
        const modalRegistro = document.getElementById("modal-registro");

        if (modalRegistro) {
          return;
        }

        window.location.href = "/?auth=registro";
      },
    );
  }

  /* ═══════════════════════════════════════════════════════════
     FUNCIONES DISPONIBLES PARA OTROS SCRIPTS
  ═══════════════════════════════════════════════════════════ */

  window.BarberAppNav = {
    mostrarUsuarioLogueado,

    mostrarNavSinSesion,

    restaurarNavbar,
  };
})();
