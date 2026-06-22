// Logica del perfil de usuario: lee ?id=N, pinta los datos y la grilla de sus pines
// Sin id asume "mi perfil" y usa la sesion. Cero innerHTML, todo con jQuery.

$(function () {

    // Referencias al DOM
    const $estadoCargando = $('#estado-cargando');
    const $perfil404 = $('#perfil-404');
    const $perfilContenido = $('#perfil-contenido');
    const $avatar = $('#perfil-avatar');
    const $nombre = $('#perfil-nombre');
    const $handle = $('#perfil-handle');
    const $bio = $('#perfil-bio');
    const $metricaPines = $('#metrica-pines');
    const $metricaLikes = $('#metrica-likes');
    const $estadoVacio = $('#estado-vacio');
    const $grillaPines = $('#grilla-pines');

    // Muestra el estado de carga y oculta el resto
    function mostrarCargando() {
        $estadoCargando.removeAttr('hidden');
        $perfil404.attr('hidden', true);
        $perfilContenido.attr('hidden', true);
    }

    // Muestra el 404 cuando el usuario no existe
    function mostrar404() {
        $estadoCargando.attr('hidden', true);
        $perfilContenido.attr('hidden', true);
        $perfil404.removeAttr('hidden');
    }

    // Pinta avatar, nombre, handle y bio del usuario
    function pintarCabecera(user) {
        $avatar.empty();
        if (user.foto_perfil) {
            $avatar.append(
                $('<img>').attr('src', user.foto_perfil).attr('alt', user.nombre)
            );
        } else {
            $avatar.text(user.nombre.charAt(0).toUpperCase());
        }

        $nombre.text(user.nombre);
        $handle.text('@' + user.usuario);

        // la bio es opcional, si no hay la oculto para no dejar un hueco
        if (user.bio) {
            $bio.text(user.bio).removeAttr('hidden');
        } else {
            $bio.attr('hidden', true);
        }

        // ya tengo los datos, muestro el contenido y escondo el cargando
        $estadoCargando.attr('hidden', true);
        $perfil404.attr('hidden', true);
        $perfilContenido.removeAttr('hidden');
    }

    // Crea el avatar pequeno de la tarjeta, igual que en el feed
    function construirAvatarPequeno(autor) {
        const $mini = $('<span>').addClass('tarjeta-pin-autor-avatar');
        if (autor.foto_perfil) {
            $mini.append($('<img>').attr('src', autor.foto_perfil).attr('alt', autor.nombre));
        } else {
            $mini.text(autor.nombre.charAt(0).toUpperCase());
        }
        return $mini;
    }

    // Construye una tarjeta de pin reutilizando los estilos del feed
    function construirTarjetaPin(pin) {
        const $li = $('<li>');
        const $article = $('<article>').addClass('tarjeta-pin');

        const $enlace = $('<a>')
            .attr('href', 'detalle.html?id=' + pin.id)
            .addClass('tarjeta-pin-enlace');

        const $imagen = $('<img>')
            .addClass('tarjeta-pin-imagen')
            .attr('src', pin.source)
            .attr('alt', pin.titulo)
            .attr('loading', 'lazy');

        const $header = $('<header>').addClass('tarjeta-pin-header');
        $header.append($('<h3>').text(pin.titulo));

        $enlace.append($imagen).append($header);

        const $footer = $('<footer>').addClass('tarjeta-pin-footer');

        const $bloqueAutor = $('<div>').addClass('tarjeta-pin-autor');
        $bloqueAutor.append(construirAvatarPequeno(pin.autor));
        $bloqueAutor.append(
            $('<span>').addClass('tarjeta-pin-autor-nombre').text('@' + pin.autor.usuario)
        );

        const $contadores = $('<div>').addClass('tarjeta-pin-contadores');
        $contadores.append(
            $('<span>').attr('aria-label', 'Cantidad de likes').text('♥ ' + (pin.likes_count || 0))
        );
        $contadores.append(
            $('<span>').attr('aria-label', 'Cantidad de comentarios').text('💬 ' + (pin.comentarios_count || 0))
        );

        $footer.append($bloqueAutor).append($contadores);
        $article.append($enlace).append($footer);
        $li.append($article);
        return $li;
    }

    // Pinta la grilla y calcula las metricas reales
    function pintarGrilla(pines) {
        $grillaPines.empty();

        const lista = pines || [];

        // metricas: cantidad de pines y suma de likes recibidos
        $metricaPines.text(lista.length);
        let totalLikes = 0;
        lista.forEach(function (pin) {
            totalLikes += (pin.likes_count || 0);
        });
        $metricaLikes.text(totalLikes);

        if (lista.length === 0) {
            $estadoVacio.removeAttr('hidden');
            return;
        }

        $estadoVacio.attr('hidden', true);
        lista.forEach(function (pin) {
            $grillaPines.append(construirTarjetaPin(pin));
        });
    }

    // Trae los pines del usuario por su handle y los pinta
    function cargarPines(handle) {
        API.get('/pines/?usuario=' + encodeURIComponent(handle))
            .then(pintarGrilla)
            .catch(function () {
                // si fallan los pines dejo la cabecera y muestro grilla vacia
                pintarGrilla([]);
            });
    }

    // Carga el perfil de cualquier usuario a partir de su id
    function cargarPerfilPorId(id) {
        API.get('/usuarios/' + id)
            .then(function (user) {
                pintarCabecera(user);
                cargarPines(user.usuario);
            })
            .catch(mostrar404);
    }

    // Carga mi propio perfil usando la sesion
    function cargarMiPerfil() {
        API.get('/usuarios/me')
            .then(function (user) {
                pintarCabecera(user);
                cargarPines(user.usuario);
            })
            .catch(mostrar404);
    }

    // INIT
    mostrarCargando();

    const params = new URLSearchParams(window.location.search);
    const id = params.get('id');

    if (id) {
        // perfil de cualquier usuario, viene del enlace del autor en el detalle
        cargarPerfilPorId(id);
    } else if (API.haySesion()) {
        // sin id pero con sesion: es mi perfil, viene del dropdown del header
        cargarMiPerfil();
    } else {
        // sin id y sin sesion no hay a quien mostrar, mando al login
        window.location.href = 'login.html';
    }
});