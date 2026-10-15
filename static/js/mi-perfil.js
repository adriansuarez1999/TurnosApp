(() => {
  const API_PERFIL = "/api/mi-agenda/perfil/";

  const API_FOTO = "/api/mi-agenda/perfil/foto/";

  const API_PASSWORD = "/api/mi-agenda/perfil/password/";

  let perfilActual = null;

  const estadoPerfil = document.getElementById("estado-perfil");

  const contenidoPerfil = document.getElementById("contenido-perfil");

  const alertaPerfil = document.getElementById("alerta-perfil");

  const formPerfil = document.getElementById("form-perfil");

  const perfilNombre = document.getElementById("perfil-nombre");

  const perfilApellido = document.getElementById("perfil-apellido");

  const perfilEmail = document.getElementById("perfil-email");

  const perfilTelefono = document.getElementById("perfil-telefono");

  const perfilEspecialidad = document.getElementById("perfil-especialidad");

  const errorPerfil = document.getElementById("error-perfil");

  const btnGuardarPerfil = document.getElementById("btn-guardar-perfil");

  const fotoPerfil = document.getElementById("foto-perfil");

  const fotoPlaceholder = document.getElementById("foto-placeholder");

  const nombreLateral = document.getElementById("nombre-perfil-lateral");

  const especialidadLateral = document.getElementById(
    "especialidad-perfil-lateral",
  );

  const promedioCalificacion = document.getElementById("promedio-calificacion");

  const formFoto = document.getElementById("form-foto");

  const inputFoto = document.getElementById("input-foto");

  const errorFoto = document.getElementById("error-foto");

  const btnSubirFoto = document.getElementById("btn-subir-foto");

  const formPassword = document.getElementById("form-password");

  const passwordActual = document.getElementById("password-actual");

  const passwordNueva = document.getElementById("password-nueva");

  const passwordConfirmar = document.getElementById("password-confirmar");

  const errorPassword = document.getElementById("error-password");

  const btnCambiarPassword = document.getElementById("btn-cambiar-password");

  function getCookie(nombre) {
    let valor = null;

    if (document.cookie && document.cookie !== "") {
      const cookies = document.cookie.split(";");

      for (let i = 0; i < cookies.length; i += 1) {
        const cookie = cookies[i].trim();

        if (cookie.startsWith(`${nombre}=`)) {
          valor = decodeURIComponent(cookie.substring(nombre.length + 1));

          break;
        }
      }
    }

    return valor;
  }

  async function obtenerJson(respuesta) {
    try {
      return await respuesta.json();
    } catch {
      return {};
    }
  }

  function mostrarAlerta(mensaje, tipo = "success") {
    alertaPerfil.className = `alert alert-${tipo}`;

    alertaPerfil.textContent = mensaje;

    alertaPerfil.classList.remove("d-none");

    window.scrollTo({
      top: 0,
      behavior: "smooth",
    });
  }

  function ocultarAlerta() {
    alertaPerfil.className = "alert d-none";

    alertaPerfil.textContent = "";
  }

  function mostrarError(elemento, mensaje) {
    elemento.textContent = mensaje;

    elemento.classList.remove("d-none");
  }

  function ocultarError(elemento) {
    elemento.textContent = "";

    elemento.classList.add("d-none");
  }

  function resolverFoto(ruta) {
    if (!ruta) {
      return null;
    }

    if (
      ruta.startsWith("http://") ||
      ruta.startsWith("https://") ||
      ruta.startsWith("/")
    ) {
      return ruta;
    }

    return `/media/${ruta}`;
  }

  async function cargarPerfil() {
    ocultarAlerta();

    try {
      const respuesta = await fetch(API_PERFIL);

      const datos = await obtenerJson(respuesta);

      if (!respuesta.ok || !datos.ok) {
        throw new Error(datos.error || "No se pudo cargar el perfil.");
      }

      perfilActual = datos.perfil;

      renderizarPerfil();

      estadoPerfil.classList.add("d-none");

      contenidoPerfil.classList.remove("d-none");
    } catch (error) {
      console.error(error);

      estadoPerfil.innerHTML = `
        <div
          class="alert alert-danger"
        >
          ${error.message}
        </div>
      `;
    }
  }

  function renderizarPerfil() {
    if (!perfilActual) {
      return;
    }

    perfilNombre.value = perfilActual.nombre || "";

    perfilApellido.value = perfilActual.apellido || "";

    perfilEmail.value = perfilActual.email || "";

    perfilTelefono.value = perfilActual.telefono || "";

    perfilEspecialidad.value = perfilActual.especialidad || "";

    nombreLateral.textContent =
      `${perfilActual.nombre || ""} ${perfilActual.apellido || ""}`.trim();

    especialidadLateral.textContent =
      perfilActual.especialidad || "Sin especialidad cargada";

    promedioCalificacion.textContent = Number(
      perfilActual.promedio_calificacion || 0,
    ).toFixed(1);

    actualizarFoto(perfilActual.foto);
  }

  function actualizarFoto(ruta) {
    const url = resolverFoto(ruta);

    if (!url) {
      fotoPerfil.classList.add("d-none");

      fotoPlaceholder.classList.remove("d-none");

      fotoPerfil.removeAttribute("src");

      return;
    }

    fotoPerfil.src = `${url}?v=${Date.now()}`;

    fotoPerfil.classList.remove("d-none");

    fotoPlaceholder.classList.add("d-none");
  }

  async function guardarPerfil(event) {
    event.preventDefault();

    ocultarError(errorPerfil);

    const telefono = perfilTelefono.value.trim();

    const especialidad = perfilEspecialidad.value.trim();

    if (!telefono) {
      mostrarError(errorPerfil, "El teléfono no puede estar vacío.");

      return;
    }

    if (telefono.length > 20) {
      mostrarError(
        errorPerfil,
        "El teléfono no puede superar los 20 caracteres.",
      );

      return;
    }

    if (especialidad.length > 100) {
      mostrarError(
        errorPerfil,
        "La especialidad no puede superar los 100 caracteres.",
      );

      return;
    }

    btnGuardarPerfil.disabled = true;

    try {
      const respuesta = await fetch(API_PERFIL, {
        method: "PUT",

        headers: {
          "Content-Type": "application/json",

          "X-CSRFToken": getCookie("csrftoken"),
        },

        body: JSON.stringify({
          telefono,
          especialidad,
        }),
      });

      const datos = await obtenerJson(respuesta);

      if (!respuesta.ok || !datos.ok) {
        throw new Error(datos.error || "No se pudo guardar el perfil.");
      }

      perfilActual = datos.perfil;

      renderizarPerfil();

      mostrarAlerta("Perfil actualizado correctamente.");
    } catch (error) {
      console.error(error);

      mostrarError(errorPerfil, error.message);
    } finally {
      btnGuardarPerfil.disabled = false;
    }
  }

  async function subirFoto(event) {
    event.preventDefault();

    ocultarError(errorFoto);

    const archivo = inputFoto.files[0];

    if (!archivo) {
      mostrarError(errorFoto, "Seleccioná una imagen.");

      return;
    }

    if (!archivo.type.startsWith("image/")) {
      mostrarError(errorFoto, "El archivo debe ser una imagen.");

      return;
    }

    if (archivo.size > 5 * 1024 * 1024) {
      mostrarError(errorFoto, "La imagen no puede superar los 5 MB.");

      return;
    }

    const formData = new FormData();

    formData.append("foto", archivo);

    btnSubirFoto.disabled = true;

    try {
      const respuesta = await fetch(API_FOTO, {
        method: "POST",

        headers: {
          "X-CSRFToken": getCookie("csrftoken"),
        },

        body: formData,
      });

      const datos = await obtenerJson(respuesta);

      if (!respuesta.ok || !datos.ok) {
        throw new Error(datos.error || "No se pudo actualizar la foto.");
      }

      perfilActual.foto = datos.foto;

      actualizarFoto(datos.foto);

      inputFoto.value = "";

      mostrarAlerta("Foto actualizada correctamente.");
    } catch (error) {
      console.error(error);

      mostrarError(errorFoto, error.message);
    } finally {
      btnSubirFoto.disabled = false;
    }
  }

  async function cambiarPassword(event) {
    event.preventDefault();

    ocultarError(errorPassword);

    const actual = passwordActual.value;

    const nueva = passwordNueva.value;

    const confirmar = passwordConfirmar.value;

    if (!actual || !nueva || !confirmar) {
      mostrarError(errorPassword, "Completá todos los campos.");

      return;
    }

    if (nueva.length < 6) {
      mostrarError(
        errorPassword,
        "La nueva contraseña debe tener al menos 6 caracteres.",
      );

      return;
    }

    if (nueva !== confirmar) {
      mostrarError(errorPassword, "Las nuevas contraseñas no coinciden.");

      return;
    }

    if (nueva === actual) {
      mostrarError(
        errorPassword,
        "La nueva contraseña debe ser distinta de la actual.",
      );

      return;
    }

    btnCambiarPassword.disabled = true;

    try {
      const respuesta = await fetch(API_PASSWORD, {
        method: "POST",

        headers: {
          "Content-Type": "application/json",

          "X-CSRFToken": getCookie("csrftoken"),
        },

        body: JSON.stringify({
          password_actual: actual,

          password_nueva: nueva,
        }),
      });

      const datos = await obtenerJson(respuesta);

      if (!respuesta.ok || !datos.ok) {
        throw new Error(datos.error || "No se pudo cambiar la contraseña.");
      }

      formPassword.reset();

      mostrarAlerta("Contraseña actualizada correctamente.");
    } catch (error) {
      console.error(error);

      mostrarError(errorPassword, error.message);
    } finally {
      btnCambiarPassword.disabled = false;
    }
  }

  formPerfil.addEventListener("submit", guardarPerfil);

  formFoto.addEventListener("submit", subirFoto);

  formPassword.addEventListener("submit", cambiarPassword);

  document.addEventListener("DOMContentLoaded", cargarPerfil);
})();
