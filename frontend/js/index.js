// Logica del feed principal: categorias, busqueda y pintado de pines
// Cero innerHTML, todo se construye con jQuery createElement equivalente

$(function () {

    // Estado local del feed
    let categoriaActual = '';
    let busquedaActual = '';
    let temporizadorBusqueda = null;

    // Referencias al DOM
    const $listaCategorias = $('#lista-categorias');
    const $listaPines = $('#lista-pines');
    const $estadoCargando = $('#estado-cargando');
    const $estadoVacio = $('#estado-vacio');
    const $campoBusqueda = $('#campo-busqueda');

    // Arma una ruta con query string a partir de un objeto de parametros
    // Lo necesito porque API.get solo recibe la ruta
    function construirRuta(base, parametros) {
        const filtrados = Object.entries(parametros).filter(function (par) {
            return par[1] !== '' && par[1] !== null && par[1] !== undefined;
        });

        if (filtrados.length === 0) return base;

        const query = new URLSearchParams(filtrados).toString();
        return base + '?' + query;
    }

    // CATEGORIAS

    function cargarCategorias() {
        API.get('/categorias/')
            .then(function (categorias) {
                pintarChipsCategorias(categorias);
            })
            .catch(function () {
                console.warn('No se pudieron cargar las categorias');
            });
    }

    function pintarChipsCategorias(categorias) {
        $listaCategorias.empty();

        // Chip de "Todas" siempre primero y activo por defecto
        $listaCategorias.append(construirChip('', 'Todas', true));

        categorias.forEach(function (nombreCategoria) {
            $listaCategorias.append(construirChip(nombreCategoria, nombreCategoria, false));
        });
    }

    // Crea un <li> con un <button> de chip de categoria
    function construirChip(valor, etiqueta, esActivo) {
        const $li = $('<li>');

        const $boton = $('<button>')
            .attr('type', 'button')
            .addClass('chip-categoria')
            .attr('data-categoria', valor)
            .attr('aria-pressed', esActivo ? 'true' : 'false')
            .text(etiqueta);

        $boton.on('click', function () {
            seleccionarCategoria(valor, $boton);
        });

        $li.append($boton);
        return $li;
    }

    function seleccionarCategoria(valor, $botonClickeado) {
        $listaCategorias.find('.chip-categoria').attr('aria-pressed', 'false');
        $botonClickeado.attr('aria-pressed', 'true');

        categoriaActual = valor;
        cargarFeed();
    }

    // BUSQUEDA con debounce de 350ms

    $campoBusqueda.on('input', function () {
        const valor = $(this).val().trim();

        if (temporizadorBusqueda) {
            clearTimeout(temporizadorBusqueda);
        }

        temporizadorBusqueda = setTimeout(function () {
            busquedaActual = valor;
            cargarFeed();
        }, 350);
    });

    // FEED

    function cargarFeed() {
        mostrarCargando();

        const ruta = construirRuta('/pines/', {
            categoria: categoriaActual,
            buscar: busquedaActual
        });

        API.get(ruta)
            .then(function (pines) {
                pintarPines(pines);
            })
            .catch(function () {
                $estadoCargando.text('Error al cargar el feed. Intenta de nuevo.').removeAttr('hidden');
            });
    }

    function mostrarCargando() {
        $estadoCargando.text('Cargando pines...').removeAttr('hidden');
        $estadoVacio.attr('hidden', true);
        $listaPines.empty();
    }

    function pintarPines(pines) {
        $estadoCargando.attr('hidden', true);
        $listaPines.empty();

        if (!pines || pines.length === 0) {
            $estadoVacio.removeAttr('hidden');
            return;
        }

        $estadoVacio.attr('hidden', true);

        pines.forEach(function (pin) {
            $listaPines.append(construirTarjetaPin(pin));
        });
    }

    // Construye una tarjeta completa: <li><article>...</article></li>
    function construirTarjetaPin(pin) {
        const $li = $('<li>');
        const $article = $('<article>').addClass('tarjeta-pin');

        // El enlace envuelve imagen y titulo, va al detalle del pin
        const $enlace = $('<a>')
            .attr('href', 'detalle.html?id=' + pin.id)
            .addClass('tarjeta-pin-enlace');

        const $imagen = $('<img>')
            .addClass('tarjeta-pin-imagen')
            .attr('src', pin.source)
            .attr('alt', pin.titulo)
            .attr('loading', 'lazy');

        const $header = $('<header>').addClass('tarjeta-pin-header');
        $header.append($('<h2>').text(pin.titulo));

        $enlace.append($imagen).append($header);

        // Footer interno con autor y contadores
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

    function construirAvatarPequeno(autor) {
        const $avatar = $('<span>').addClass('tarjeta-pin-autor-avatar');

        if (autor.foto_perfil) {
            const $img = $('<img>')
                .attr('src', autor.foto_perfil)
                .attr('alt', autor.nombre);
            $avatar.append($img);
        } else {
            $avatar.text(autor.nombre.charAt(0).toUpperCase());
        }

        return $avatar;
    }

    // INIT
    cargarCategorias();
    cargarFeed();
});