// Logica del header dinamico segun sesion
// Si hay token pido GET /usuarios/me y pinto avatar + dropdown
// Si no hay token pinto botones de login y registro
// Uso <details>/<summary> nativo para el dropdown, sin JS para abrir y cerrar

$(function () {

    const $accionesAuth = $('#acciones-auth');
    const $menuUsuario = $('#menu-usuario');

    // Pinta los botones de login y registro cuando no hay sesion
    function pintarAcciones() {

        $accionesAuth.empty();
        $menuUsuario.empty().attr('hidden', true);

        const $liLogin = $('<li>');
        const $aLogin = $('<a>')
            .attr('href', 'login.html')
            .addClass('btn-secundario')
            .text('Iniciar sesion');

        const $liRegistro = $('<li>');
        const $aRegistro = $('<a>')
            .attr('href', 'register.html')
            .addClass('btn-primario')
            .text('Registrarse');

        $liLogin.append($aLogin);
        $liRegistro.append($aRegistro);
        $accionesAuth.append($liLogin).append($liRegistro).removeAttr('hidden');
    }

    // Pinta el avatar y el dropdown cuando hay sesion
    function pintarMenuUsuario(user) {

        $accionesAuth.empty().attr('hidden', true);
        $menuUsuario.empty();

        // Uso <details> y <summary> nativos: accesible y sin logica de abrir/cerrar
        const $details = $('<details>').addClass('dropdown-usuario');
        const $summary = $('<summary>').addClass('dropdown-summary');

        const $avatar = $('<span>')
            .addClass('avatar-header')
            .attr('aria-label', 'Menu de usuario');

        if (user.foto_perfil) {
            const $img = $('<img>')
                .attr('src', user.foto_perfil)
                .attr('alt', user.nombre);
            $avatar.append($img);
        } else {
            $avatar.text(user.nombre.charAt(0).toUpperCase());
        }

        $summary.append($avatar);

        // Lista del menu desplegable
        const $listaDropdown = $('<ul>').addClass('lista-dropdown');

        // Cabecera con nombre completo y arroba
        const $cabecera = $('<li>').addClass('dropdown-cabecera');
        $cabecera.append($('<strong>').text(user.nombre));
        $cabecera.append($('<span>').addClass('dropdown-usuario-handle').text('@' + user.usuario));

        // Separador semantico con <hr>
        const $separador = $('<li>').attr('role', 'separator').append($('<hr>'));

        const $liPerfil = $('<li>').append(
            $('<a>').attr('href', 'usuario.html').text('Mi perfil')
        );

        const $liSalir = $('<li>').append(
            $('<button>')
                .attr('type', 'button')
                .addClass('btn-salir')
                .text('Cerrar sesion')
                .on('click', cerrarSesion)
        );

        $listaDropdown.append($cabecera).append($separador).append($liPerfil).append($liSalir);

        $details.append($summary).append($listaDropdown);
        $menuUsuario.append($details).removeAttr('hidden');
    }

    // Cierra sesion usando el helper del wrapper, que ya redirige al login
    function cerrarSesion() {
        API.cerrarSesion();
    }

    // Cierra el dropdown si el usuario hace click fuera de el
    $(document).on('click', function (evento) {
        const $detailsAbierto = $('details.dropdown-usuario[open]');
        if ($detailsAbierto.length === 0) return;

        if (!$(evento.target).closest('details.dropdown-usuario').length) {
            $detailsAbierto.removeAttr('open');
        }
    });

    // Punto de entrada: si hay sesion, traigo el user fresco del backend
    function iniciar() {
        if (!API.haySesion()) {
            pintarAcciones();
            return;
        }

        API.get('/usuarios/me')
            .then(function (user) {
                pintarMenuUsuario(user);
            })
            .catch(function () {
                // Si el GET falla por red, uso el user guardado en localStorage como fallback
                const userLocal = API.getUsuarioActual();
                if (userLocal) {
                    pintarMenuUsuario(userLocal);
                } else {
                    pintarAcciones();
                }
            });
    }

    iniciar();
});