// logica de login y registro, un solo archivo para las dos paginas

(function () {
    "use strict";

    const $formMessage = $("#formMessage");
    const $loginForm = $("#loginForm");
    const $registerForm = $("#registerForm");

    function mostrarMensaje(texto, tipo) {
        $formMessage
            .text(texto)
            .removeClass("error success")
            .addClass("form-message")
            .css("display", "block");

        if (tipo) {
            $formMessage.addClass(tipo);
        }
    }

    function limpiarMensaje() {
        $formMessage.text("").css("display", "none").removeClass("error success");
    }

    // LOGIN
    if ($loginForm.length) {
        $loginForm.on("submit", async function (e) {
            e.preventDefault();
            limpiarMensaje();

            const email = $("#email").val().trim().toLowerCase();
            const password = $("#password").val();

            if (!email) {
                mostrarMensaje("Ingresa tu correo electronico", "error");
                return;
            }

            if (password.length < 8) {
                mostrarMensaje("La contrasena debe tener al menos 8 caracteres", "error");
                return;
            }

            mostrarMensaje("Validando credenciales...", "");

            try {
                const data = await API.post("/usuarios/login", { email, password });
                API.guardarSesion(data.access_token, data.user); mostrarMensaje("Sesion iniciada correctamente", "success");
                setTimeout(function () {
                    window.location.href = "index.html";
                }, 1500);
            } catch (error) {
                const texto = error && error.message
                    ? error.message
                    : "No se pudo iniciar sesion, intenta de nuevo";
                mostrarMensaje(texto, "error");
            }
        });
    }

    // REGISTER
    if ($registerForm.length) {

        $("#password").on("input", function () {
            const val = $(this).val();
            const $bar = $("#passwordStrengthBar");
            const $text = $("#passwordStrengthText");

            if (val.length === 0) {
                $bar.css({ width: "0%", "background-color": "transparent" });
                $text.text("").css("color", "");
                return;
            }

            let nivel = 0;
            if (val.length >= 8) nivel++;
            if (/[A-Za-z]/.test(val) && /\d/.test(val)) nivel++;
            if (/[^A-Za-z0-9]/.test(val)) nivel++;

            if (val.length < 8 || nivel === 1) {
                $bar.css({ width: "33%", "background-color": "var(--color-danger)" });
                $text.text("Debil, usa al menos 8 caracteres con letras y numeros").css("color", "var(--color-danger)");
            } else if (nivel === 2) {
                $bar.css({ width: "66%", "background-color": "var(--color-warning)" });
                $text.text("Media, agrega un simbolo para mayor seguridad").css("color", "var(--color-warning)");
            } else {
                $bar.css({ width: "100%", "background-color": "var(--color-success)" });
                $text.text("Fuerte").css("color", "var(--color-success)");
            }

            if ($("#confirmPassword").val().length > 0) {
                validarConfirmacion();
            }
        });

        function validarConfirmacion() {
            const password = $("#password").val();
            const confirm = $("#confirmPassword").val();
            const $text = $("#confirmPasswordText");

            if (confirm.length === 0) {
                $text.text("").css("color", "");
                return;
            }

            if (password === confirm) {
                $text.text("Las contrasenas coinciden").css("color", "var(--color-success)");
            } else {
                $text.text("Las contrasenas no coinciden").css("color", "var(--color-danger)");
            }
        }

        $("#confirmPassword").on("input", validarConfirmacion);

        $registerForm.on("submit", async function (e) {
            e.preventDefault();
            limpiarMensaje();

            const nombre = $("#nombre").val().trim();
            const usuario = $("#usuario").val().trim();
            const email = $("#email").val().trim().toLowerCase();
            const password = $("#password").val();
            const confirmPassword = $("#confirmPassword").val();

            if (nombre.length < 3) {
                mostrarMensaje("El nombre completo debe tener al menos 3 caracteres", "error");
                return;
            }

            if (!/^[a-zA-Z0-9_]+$/.test(usuario)) {
                mostrarMensaje("El usuario solo puede tener letras, numeros y guion bajo", "error");
                return;
            }

            const passwordRegex = /^(?=.*[A-Za-z])(?=.*\d).{8,}$/;
            if (!passwordRegex.test(password)) {
                mostrarMensaje("La contrasena debe tener minimo 8 caracteres, letras y numeros", "error");
                return;
            }

            if (password !== confirmPassword) {
                mostrarMensaje("Las contrasenas no coinciden", "error");
                return;
            }

            mostrarMensaje("Creando cuenta...", "");

            const payload = { nombre, usuario, email, password };

            try {
                await API.post("/usuarios/register", payload);
                mostrarMensaje("Cuenta creada correctamente, redirigiendo al login...", "success");
                setTimeout(function () {
                    window.location.href = "login.html";
                }, 2000);
            } catch (error) {
                const texto = error && error.message
                    ? error.message
                    : "No se pudo crear la cuenta, intenta de nuevo";
                mostrarMensaje(texto, "error");
            }
        });
    }

})();