/* VISOR - detalle.js */
/* logica del detalle de un pin: info, like y comentarios */

// guardo el id del pin y las referencias del dom a nivel de modulo
var pinId = null;
var estadoLike = { activo: false, conteo: 0 };

var $detalle404, $detalleCard;
var $img, $titulo, $descripcion, $tags;
var $autorAvatar, $autorUsuario, $autorFecha;
var $btnLike, $likeIcono, $likeContador;
var $comentariosTitulo, $formComentario, $avisoLogin;
var $inputComentario, $btnEnviar, $contadorChars, $listaComentarios;


// convierto una fecha ISO en un texto tipo "hace 3 dias"
function fechaRelativa(iso) {
    if (!iso) {
        return "";
    }

    var fecha = new Date(iso);
    var segundos = Math.floor((new Date() - fecha) / 1000);

    if (segundos < 60) {
        return "hace un momento";
    }

    var minutos = Math.floor(segundos / 60);
    if (minutos < 60) {
        return "hace " + minutos + (minutos === 1 ? " minuto" : " minutos");
    }

    var horas = Math.floor(minutos / 60);
    if (horas < 24) {
        return "hace " + horas + (horas === 1 ? " hora" : " horas");
    }

    var dias = Math.floor(horas / 24);
    if (dias < 30) {
        return "hace " + dias + (dias === 1 ? " dia" : " dias");
    }

    var meses = Math.floor(dias / 30);
    if (meses < 12) {
        return "hace " + meses + (meses === 1 ? " mes" : " meses");
    }

    var anios = Math.floor(meses / 12);
    return "hace " + anios + (anios === 1 ? " anio" : " anios");
}


// muestro el bloque 404 y escondo la tarjeta
function mostrar404() {
    $detalleCard.prop("hidden", true);
    $detalle404.prop("hidden", false);
}


// pinto los tags como chips, tolero string separada por comas o un array
function pintarTags(pin) {
    $tags.empty();

    var tags = pin.tags;
    if (typeof tags === "string") {
        tags = tags.split(",");
    }
    if (!Array.isArray(tags)) {
        return;
    }

    tags.forEach(function (t) {
        var limpio = String(t).trim();
        if (!limpio) {
            return;
        }
        $tags.append($("<li>").text("#" + limpio));
    });
}


// refresco el boton de like segun el estado local
function refrescarLike() {
    if (estadoLike.activo) {
        $likeIcono.text("\u2665"); // corazon lleno
        $btnLike.attr("aria-pressed", "true");
    } else {
        $likeIcono.text("\u2661"); // corazon vacio
        $btnLike.attr("aria-pressed", "false");
    }
    $likeContador.text(estadoLike.conteo);
}


// pinto todo el detalle con los datos del pin
function pintarPin(pin) {
    // imagen
    $img.attr("src", pin.source || "");
    $img.attr("alt", pin.titulo || "Publicacion");

    // texto principal
    $titulo.text(pin.titulo || "");
    $descripcion.text(pin.descripcion || "");
    pintarTags(pin);

    // el autor viene anidado en pin.autor, no plano
    var autor = pin.autor || {};
    var usuario = autor.usuario || "usuario";
    var enlacePerfil = "usuario.html?id=" + (autor.id || "");
    $autorUsuario.text("@" + usuario).attr("href", enlacePerfil);
    $autorAvatar.attr("href", enlacePerfil);
    if (autor.foto_perfil) {
        $autorAvatar.css("background-image", "url('" + autor.foto_perfil + "')");
    }
    $autorFecha.text(fechaRelativa(pin.created_at));

    // like
    estadoLike.activo = pin.dio_like === true;
    estadoLike.conteo = pin.likes_count || 0;
    refrescarLike();

    // titulo de comentarios con el conteo
    $comentariosTitulo.text("Comentarios (" + (pin.comentarios_count || 0) + ")");

    // ya tengo todo, muestro la tarjeta
    $detalle404.prop("hidden", true);
    $detalleCard.prop("hidden", false);
}


// armo un comentario como nodo, sin innerHTML
function crearComentario(c) {
    // el autor del comentario viene anidado en c.autor, igual que en los pines
    // antes leia c.usuario plano y por eso siempre salia "@usuario"
    var autor = c.autor || {};
    var usuario = autor.usuario || "usuario";

    var $avatar = $("<div>").addClass("comentario-avatar");
    if (autor.foto_perfil) {
        $avatar.css("background-image", "url('" + autor.foto_perfil + "')");
    }

    var $usuario = $("<p>").addClass("comentario-usuario").text("@" + usuario);
    var $texto = $("<p>").addClass("comentario-texto").text(c.contenido || "");
    var $fecha = $("<p>").addClass("comentario-fecha").text(fechaRelativa(c.created_at));

    var $cuerpo = $("<div>")
        .addClass("comentario-cuerpo")
        .append($usuario, $texto, $fecha);

    var $articulo = $("<article>")
        .addClass("comentario")
        .append($avatar, $cuerpo);

    return $("<li>").append($articulo);
}


// pinto la lista de comentarios
function pintarComentarios(lista) {
    $listaComentarios.empty();

    if (!lista || lista.length === 0) {
        $listaComentarios.append(
            $("<li>").addClass("comentarios-vacio").text("Todavia no hay comentarios. Se el primero.")
        );
        return;
    }

    lista.forEach(function (c) {
        $listaComentarios.append(crearComentario(c));
    });
}


// traigo el pin del backend
function cargarPin() {
    API.get("/pines/" + pinId)
        .then(pintarPin)
        .catch(mostrar404);
}


// traigo los comentarios del backend
function cargarComentarios() {
    API.get("/pines/" + pinId + "/comentarios")
        .then(pintarComentarios)
        .catch(function () {
            // si fallan los comentarios no rompo la pagina
        });
}


// muestro u oculto el form segun haya sesion
function configurarFormulario() {
    if (API.haySesion()) {
        $formComentario.prop("hidden", false);
        $avisoLogin.prop("hidden", true);
    } else {
        $formComentario.prop("hidden", true);
        $avisoLogin.prop("hidden", false);
    }
}


$(function () {
    // cacheo todas las referencias del dom
    $detalle404 = $("#detalle-404");
    $detalleCard = $("#detalle-card");
    $img = $("#detalle-img");
    $titulo = $("#detalle-titulo");
    $descripcion = $("#detalle-descripcion");
    $tags = $("#detalle-tags");
    $autorAvatar = $("#autor-avatar");
    $autorUsuario = $("#autor-usuario");
    $autorFecha = $("#autor-fecha");
    $btnLike = $("#btn-like");
    $likeIcono = $("#like-icono");
    $likeContador = $("#like-contador");
    $comentariosTitulo = $("#comentarios-titulo");
    $formComentario = $("#form-comentario");
    $avisoLogin = $("#aviso-login");
    $inputComentario = $("#input-comentario");
    $btnEnviar = $("#btn-enviar-comentario");
    $contadorChars = $("#contador-chars");
    $listaComentarios = $("#lista-comentarios");

    // leo el id del pin de la url, si no hay muestro 404 y corto
    var params = new URLSearchParams(window.location.search);
    pinId = params.get("id");
    if (!pinId) {
        mostrar404();
        return;
    }

    configurarFormulario();

    // click en like: sin sesion mando al login, con sesion hago toggle
    $btnLike.on("click", function () {
        if (!API.haySesion()) {
            window.location.href = "login.html";
            return;
        }

        // evito doble click mientras va la peticion
        $btnLike.prop("disabled", true);

        var peticion = estadoLike.activo
            ? API.del("/pines/" + pinId + "/like")
            : API.post("/pines/" + pinId + "/like");

        peticion
            .then(function () {
                // actualizo el estado local sin recargar la pagina
                if (estadoLike.activo) {
                    estadoLike.activo = false;
                    estadoLike.conteo = Math.max(0, estadoLike.conteo - 1);
                } else {
                    estadoLike.activo = true;
                    estadoLike.conteo = estadoLike.conteo + 1;
                }
                refrescarLike();
            })
            .catch(function () {
                // si falla dejo el estado como estaba
            })
            .then(function () {
                // reactivo el boton pase lo que pase
                $btnLike.prop("disabled", false);
            });
    });

    // valido en vivo el largo del comentario, entre 1 y 300
    $inputComentario.on("input", function () {
        var largo = $inputComentario.val().trim().length;
        $contadorChars.text(largo + " / 300");
        $btnEnviar.prop("disabled", largo < 1 || largo > 300);
    });

    // envio el comentario y recargo la lista desde el backend
    $formComentario.on("submit", function (e) {
        e.preventDefault();

        var contenido = $inputComentario.val().trim();
        if (contenido.length < 1 || contenido.length > 300) {
            return;
        }

        $btnEnviar.prop("disabled", true);

        API.post("/pines/" + pinId + "/comentarios", { contenido: contenido })
            .then(function () {
                $inputComentario.val("");
                $contadorChars.text("0 / 300");
                cargarComentarios();
            })
            .catch(function () {
                // si falla dejo el texto para no perderlo
            })
            .then(function () {
                // recalculo el estado del boton segun lo que quede escrito
                var largo = $inputComentario.val().trim().length;
                $btnEnviar.prop("disabled", largo < 1 || largo > 300);
            });
    });

    // carga inicial
    cargarPin();
    cargarComentarios();
});