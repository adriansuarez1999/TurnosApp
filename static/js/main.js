(() => {
  /* ═══════════════════════════════════════════════════════════
     main.js

     Funcionalidad específica del Home:
     - Login
     - Registro
     - Modales
     - Navegación de Home
     - Registrar barbería
  ═══════════════════════════════════════════════════════════ */

  const API = {
    login: "/api/login/",

    registro: "/api/registro/",
  };

  const MODO_SIMULADO = false;

  /* ═══════════════════════════════════════════════════════════
     ELEMENTOS
  ═══════════════════════════════════════════════════════════ */

  const modalLoginElemento = document.getElementById("modal-login");

  const modalRegistroElemento = document.getElementById("modal-registro");

  /*
    main.js solamente debería cargarse en index.html.

    Igual dejamos esta protección para evitar errores
    si alguna vez se carga accidentalmente en otra página.
  */

  if (!modalLoginElemento || !modalRegistroElemento) {
    return;
  }

  const alertaLogin = document.getElementById("alerta-login");

  const alertaRegistro = document.getElementById("alerta-registro");

  /* ═══════════════════════════════════════════════════════════
     MODALES BOOTSTRAP
  ═══════════════════════════════════════════════════════════ */

  const modalLogin = bootstrap.Modal.getOrCreateInstance(modalLoginElemento);

  const modalRegistro = bootstrap.Modal.getOrCreateInstance(
    modalRegistroElemento,
  );

  function abrirLogin() {
    limpiarAlerta(alertaLogin);

    modalLogin.show();
  }

  function abrirRegistro() {
    limpiarAlerta(alertaRegistro);

    modalRegistro.show();
  }

  function cerrarLogin() {
    modalLogin.hide();
  }

  function cerrarRegistro() {
    modalRegistro.hide();
  }

  /* ═══════════════════════════════════════════════════════════
     BOTONES NAVBAR
  ═══════════════════════════════════════════════════════════ */

  const btnAccederHome = document.getElementById("btn-acceder");

  const btnCrearCuentaHome = document.getElementById("btn-crear-cuenta");

  if (btnAccederHome) {
    btnAccederHome.addEventListener("click", abrirLogin);
  }

  if (btnCrearCuentaHome) {
    btnCrearCuentaHome.addEventListener("click", abrirRegistro);
  }

  /* ═══════════════════════════════════════════════════════════
     BOTONES CERRAR
  ═══════════════════════════════════════════════════════════ */

  const cerrarLoginBtn = document.getElementById("cerrar-login");

  const cerrarRegistroBtn = document.getElementById("cerrar-registro");

  if (cerrarLoginBtn) {
    cerrarLoginBtn.addEventListener("click", cerrarLogin);
  }

  if (cerrarRegistroBtn) {
    cerrarRegistroBtn.addEventListener("click", cerrarRegistro);
  }

  /* ═══════════════════════════════════════════════════════════
     CAMBIAR ENTRE LOGIN Y REGISTRO
  ═══════════════════════════════════════════════════════════ */

  const irARegistro = document.getElementById("ir-a-registro");

  const irALogin = document.getElementById("ir-a-login");

  if (irARegistro) {
    irARegistro.addEventListener(
      "click",

      () => {
        cerrarLogin();

        modalLoginElemento.addEventListener(
          "hidden.bs.modal",

          () => {
            abrirRegistro();
          },

          {
            once: true,
          },
        );
      },
    );
  }

  if (irALogin) {
    irALogin.addEventListener(
      "click",

      () => {
        cerrarRegistro();

        modalRegistroElemento.addEventListener(
          "hidden.bs.modal",

          () => {
            abrirLogin();
          },

          {
            once: true,
          },
        );
      },
    );
  }

  /* ═══════════════════════════════════════════════════════════
     ALERTAS
  ═══════════════════════════════════════════════════════════ */

  function mostrarAlerta(elemento, mensaje, tipo = "error") {
    elemento.textContent = mensaje;

    elemento.classList.remove(
      "d-none",
      "alert-danger",
      "alert-success",
      "alert-info",
    );

    if (tipo === "exito") {
      elemento.classList.add("alert-success");
    } else if (tipo === "info") {
      elemento.classList.add("alert-info");
    } else {
      elemento.classList.add("alert-danger");
    }
  }

  function limpiarAlerta(elemento) {
    elemento.textContent = "";

    elemento.classList.add("d-none");

    elemento.classList.remove("alert-danger", "alert-success", "alert-info");
  }

  /* ═══════════════════════════════════════════════════════════
     LOGIN
  ═══════════════════════════════════════════════════════════ */

  const btnLoginEnviar = document.getElementById("btn-login-enviar");

  if (btnLoginEnviar) {
    btnLoginEnviar.addEventListener(
      "click",

      async () => {
        const email = document.getElementById("login-email").value.trim();

        const password = document.getElementById("login-password").value;

        if (!email || !password) {
          mostrarAlerta(alertaLogin, "Completá todos los campos.");

          return;
        }

        btnLoginEnviar.disabled = true;

        btnLoginEnviar.textContent = "Ingresando...";

        limpiarAlerta(alertaLogin);

        try {
          let datos;

          if (MODO_SIMULADO) {
            await new Promise((resolve) => setTimeout(resolve, 700));

            datos = {
              ok: true,

              nombre: "Usuario",

              es_dueno: false,
            };
          } else {
            const respuesta = await fetch(API.login, {
              method: "POST",

              headers: {
                "Content-Type": "application/json",

                "X-CSRFToken": getCookie("csrftoken"),
              },

              body: JSON.stringify({
                email,
                password,
              }),
            });

            datos = await respuesta.json();
          }

          if (datos.ok) {
            sessionStorage.setItem("barberapp_usuario", datos.nombre);

            sessionStorage.setItem(
              "barberapp_es_dueno",

              datos.es_dueno ? "true" : "false",
            );

            cerrarLogin();

            if (window.BarberAppNav) {
              window.BarberAppNav.mostrarUsuarioLogueado(
                datos.nombre,
                datos.es_dueno,
              );
            }
          } else {
            mostrarAlerta(
              alertaLogin,

              datos.error || "Email o contraseña incorrectos.",
            );
          }
        } catch (error) {
          console.error(error);

          mostrarAlerta(
            alertaLogin,

            "No se pudo conectar con el servidor.",
          );
        } finally {
          btnLoginEnviar.disabled = false;

          btnLoginEnviar.textContent = "Ingresar";
        }
      },
    );
  }

  /* ═══════════════════════════════════════════════════════════
     LOGIN CON ENTER
  ═══════════════════════════════════════════════════════════ */

  const loginEmail = document.getElementById("login-email");

  const loginPassword = document.getElementById("login-password");

  [loginEmail, loginPassword].forEach((input) => {
    if (!input) {
      return;
    }

    input.addEventListener(
      "keydown",

      (event) => {
        if (event.key === "Enter") {
          event.preventDefault();

          btnLoginEnviar.click();
        }
      },
    );
  });

  /* ═══════════════════════════════════════════════════════════
     REGISTRO
  ═══════════════════════════════════════════════════════════ */

  const btnRegistroEnviar = document.getElementById("btn-registro-enviar");

  if (btnRegistroEnviar) {
    btnRegistroEnviar.addEventListener(
      "click",

      async () => {
        const nombre = document.getElementById("reg-nombre").value.trim();

        const apellido = document.getElementById("reg-apellido").value.trim();

        const email = document.getElementById("reg-email").value.trim();

        const telefono = document.getElementById("reg-telefono").value.trim();

        const password = document.getElementById("reg-password").value;

        if (!nombre || !apellido || !email || !password) {
          mostrarAlerta(alertaRegistro, "Completá los campos obligatorios.");

          return;
        }

        if (password.length < 6) {
          mostrarAlerta(
            alertaRegistro,
            "La contraseña debe tener al menos 6 caracteres.",
          );

          return;
        }

        if (!email.includes("@")) {
          mostrarAlerta(alertaRegistro, "Ingresá un email válido.");

          return;
        }

        btnRegistroEnviar.disabled = true;

        btnRegistroEnviar.textContent = "Creando cuenta...";

        limpiarAlerta(alertaRegistro);

        try {
          let datos;

          if (MODO_SIMULADO) {
            await new Promise((resolve) => setTimeout(resolve, 800));

            datos = {
              ok: true,

              nombre,
            };
          } else {
            const respuesta = await fetch(API.registro, {
              method: "POST",

              headers: {
                "Content-Type": "application/json",

                "X-CSRFToken": getCookie("csrftoken"),
              },

              body: JSON.stringify({
                nombre,
                apellido,
                email,
                telefono,
                password,
              }),
            });

            datos = await respuesta.json();
          }

          if (datos.ok) {
            mostrarAlerta(
              alertaRegistro,

              "¡Cuenta creada! Iniciá sesión.",

              "exito",
            );

            setTimeout(
              () => {
                cerrarRegistro();

                modalRegistroElemento.addEventListener(
                  "hidden.bs.modal",

                  () => {
                    loginEmail.value = email;

                    abrirLogin();
                  },

                  {
                    once: true,
                  },
                );
              },

              1200,
            );
          } else {
            mostrarAlerta(
              alertaRegistro,

              datos.error || "Error al crear la cuenta.",
            );
          }
        } catch (error) {
          console.error(error);

          mostrarAlerta(
            alertaRegistro,

            "No se pudo conectar con el servidor.",
          );
        } finally {
          btnRegistroEnviar.disabled = false;

          btnRegistroEnviar.textContent = "Crear mi cuenta";
        }
      },
    );
  }

  /* ═══════════════════════════════════════════════════════════
     BARBERÍAS
  ═══════════════════════════════════════════════════════════ */

  function irABarberias() {
    const listado = document.querySelector(".listing");

    if (listado) {
      listado.scrollIntoView({
        behavior: "smooth",
      });
    }
  }

  const navBarberias = document.getElementById("nav-barberias");

  if (navBarberias) {
    navBarberias.addEventListener(
      "click",

      (event) => {
        const listado = document.querySelector(".listing");

        if (!listado) {
          return;
        }

        event.preventDefault();

        irABarberias();
      },
    );
  }

  const pillBarberias = document.getElementById("pill-barberias");

  if (pillBarberias) {
    pillBarberias.addEventListener("click", irABarberias);
  }

  const pillReservar = document.getElementById("pill-reservar");

  if (pillReservar) {
    pillReservar.addEventListener("click", irABarberias);
  }

  const pillMisTurnos = document.getElementById("pill-mis-turnos");

  if (pillMisTurnos) {
    pillMisTurnos.addEventListener(
      "click",

      () => {
        window.location.href = "/paginas/misturnos.html";
      },
    );
  }

  /* ═══════════════════════════════════════════════════════════
     REGISTRAR BARBERÍA
  ═══════════════════════════════════════════════════════════ */

  const btnRegistrarBarberia = document.getElementById(
    "btn-registrar-barberia",
  );

  if (btnRegistrarBarberia) {
    btnRegistrarBarberia.addEventListener(
      "click",

      () => {
        const usuarioLogueado = sessionStorage.getItem("barberapp_usuario");

        if (!usuarioLogueado) {
          mostrarAlerta(
            alertaLogin,

            "Iniciá sesión primero para registrar tu barbería.",

            "info",
          );

          modalLogin.show();

          return;
        }

        window.location.href = "/paginas/registrar-barberia.html";
      },
    );
  }

  /* ═══════════════════════════════════════════════════════════
     ABRIR MODAL PEDIDO DESDE OTRA PÁGINA
  ═══════════════════════════════════════════════════════════ */

  const parametrosURL = new URLSearchParams(window.location.search);

  const authSolicitado = parametrosURL.get("auth");

  if (authSolicitado === "login") {
    abrirLogin();
  } else if (authSolicitado === "registro") {
    abrirRegistro();
  }
})();
