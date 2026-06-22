// wrapper centralizado para las llamadas al backend de Visor
// expongo un objeto API global con metodos get, post, del y helpers de sesion

(function (window) {
    "use strict";

    const BASE_URL = "http://localhost:8000";

    const KEY_TOKEN = "visor_token";
    const KEY_USUARIO = "visor_usuario";

    function getToken() {
        return localStorage.getItem(KEY_TOKEN);
    }

    function limpiarSesion() {
        localStorage.removeItem(KEY_TOKEN);
        localStorage.removeItem(KEY_USUARIO);
    }

    function request(metodo, ruta, datos, esFormData) {
        const headers = {};
        const token = getToken();

        if (token) {
            headers["Authorization"] = "Bearer " + token;
        }

        const config = {
            url: BASE_URL + ruta,
            method: metodo,
            headers: headers
        };

        if (datos !== undefined && datos !== null) {
            if (esFormData) {
                config.data = datos;
                config.processData = false;
                config.contentType = false;
            } else {
                config.data = JSON.stringify(datos);
                config.contentType = "application/json";
            }
        }

        return new Promise(function (resolve, reject) {
            $.ajax(config)
                .done(function (respuesta) {
                    resolve(respuesta);
                })
                .fail(function (xhr) {
                    // 401 con sesion previa significa que el token expiro
                    // 401 sin sesion (caso login con credenciales malas) solo propaga el error
                    if (xhr.status === 401 && getToken()) {
                        limpiarSesion();
                        window.location.href = "login.html";
                        return;
                    }

                    // FastAPI puede mandar detail como string o como array (errores 422 de Pydantic)
                    let mensaje = "No se pudo completar la solicitud";
                    if (xhr.responseJSON && xhr.responseJSON.detail) {
                        const detail = xhr.responseJSON.detail;
                        if (typeof detail === "string") {
                            mensaje = detail;
                        } else if (Array.isArray(detail) && detail.length > 0) {
                            mensaje = detail[0].msg || mensaje;
                        }
                    }
                    reject(new Error(mensaje));
                });
        });
    }

    window.API = {
        get: function (ruta) {
            return request("GET", ruta);
        },
        post: function (ruta, datos) {
            return request("POST", ruta, datos, false);
        },
        postFile: function (ruta, formData) {
            return request("POST", ruta, formData, true);
        },
        del: function (ruta) {
            return request("DELETE", ruta);
        },

        guardarSesion: function (token, usuario) {
            localStorage.setItem(KEY_TOKEN, token);
            localStorage.setItem(KEY_USUARIO, JSON.stringify(usuario));
        },
        cerrarSesion: function () {
            limpiarSesion();
            window.location.href = "login.html";
        },
        haySesion: function () {
            return getToken() !== null;
        },
        getUsuarioActual: function () {
            const raw = localStorage.getItem(KEY_USUARIO);
            if (!raw) {
                return null;
            }
            try {
                return JSON.parse(raw);
            } catch (e) {
                return null;
            }
        }
    };

})(window);