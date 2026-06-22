# script que puebla la base con datos iniciales
# se corre una sola vez despues de levantar la api por primera vez
# uso: python seed.py

from sqlmodel import Session, select

from db import engine
from models import Usuarios, Pines, Rol
from app.auth import hash_password


# usuarios iniciales, el primero es admin para poder defender el rol diferenciado
USUARIOS_INICIALES = [
    {
        "nombre": "Elian Jami",
        "usuario": "elianjami",
        "email": "elian@visor.com",
        "password": "admin12345",  # se hashea antes de guardar, jamas se guarda en claro
        "bio": "Admin de Visor, estudiante de Sistemas en UIDE.",
        "rol": Rol.ADMIN,
    },
    {
        "nombre": "Ana Paisajes",
        "usuario": "ana_paisajes",
        "email": "ana@visor.com",
        "password": "ana123456",
        "bio": "Amante de los paisajes y la fotografia de naturaleza.",
        "rol": Rol.USER,
    },
    {
        "nombre": "Dario Chef",
        "usuario": "chef_dario",
        "email": "dario@visor.com",
        "password": "dario12345",
        "bio": "Cocina casera, recetas faciles y comida ecuatoriana.",
        "rol": Rol.USER,
    },
]


# pines iniciales, cada source es la CLAVE del objeto en S3 (no una url)
# el bucket es privado, GET /pines firma cada clave con presigned url en runtime
# las 30 imagenes ya estan subidas en visor-media-prod/pines/ (subida manual por consola)
PINES_INICIALES = [
    # ---------- elianjami (10) ----------
    {
        "titulo": "Trazo abstracto en azul",
        "descripcion": "Estudio de color sobre lienzo, paleta fria.",
        "tags": "arte,abstracto,pintura,azul",
        "categoria": "Arte",
        "source": "pines/art1.jpg",
        "autor_usuario": "elianjami",
    },
    {
        "titulo": "Ilustracion a tinta",
        "descripcion": "Boceto a tinta china con tramas finas.",
        "tags": "arte,tinta,ilustracion,blanco y negro",
        "categoria": "Arte",
        "source": "pines/art2.jpg",
        "autor_usuario": "elianjami",
    },
    {
        "titulo": "Monoplaza en boxes",
        "descripcion": "Monoplaza de F1 esperando salida en pit lane.",
        "tags": "f1,formula1,motor,boxes",
        "categoria": "Formula 1",
        "source": "pines/f11.jpg",
        "autor_usuario": "elianjami",
    },
    {
        "titulo": "Curva rapida a fondo",
        "descripcion": "Piloto trazando una curva de alta velocidad.",
        "tags": "f1,formula1,curva,velocidad",
        "categoria": "Formula 1",
        "source": "pines/f12.jpg",
        "autor_usuario": "elianjami",
    },
    {
        "titulo": "Tiro libre directo",
        "descripcion": "Jugador armando un tiro libre cerca del area.",
        "tags": "futbol,deporte,tiro libre,partido",
        "categoria": "Futbol",
        "source": "pines/fut1.jpg",
        "autor_usuario": "elianjami",
    },
    {
        "titulo": "Estadio a reventar",
        "descripcion": "Hinchada llenando un estadio antes del partido.",
        "tags": "futbol,estadio,hinchada,deporte",
        "categoria": "Futbol",
        "source": "pines/fut2.jpg",
        "autor_usuario": "elianjami",
    },
    {
        "titulo": "Moto deportiva en pista",
        "descripcion": "Moto deportiva inclinada en circuito.",
        "tags": "motos,deportiva,pista,velocidad",
        "categoria": "Motos",
        "source": "pines/moto1.jpg",
        "autor_usuario": "elianjami",
    },
    {
        "titulo": "Clinch en el ring",
        "descripcion": "Dos peleadores trabados en clinch.",
        "tags": "muay thai,clinch,combate,ring",
        "categoria": "Muay Thai",
        "source": "pines/muay1.jpg",
        "autor_usuario": "elianjami",
    },
    {
        "titulo": "Patada media a la guardia",
        "descripcion": "Patada circular conectando a la guardia del rival.",
        "tags": "muay thai,patada,tecnica,combate",
        "categoria": "Muay Thai",
        "source": "pines/muay2.jpg",
        "autor_usuario": "elianjami",
    },
    {
        "titulo": "Bosque al amanecer",
        "descripcion": "Niebla baja entre los arboles a primera hora.",
        "tags": "naturaleza,bosque,amanecer,niebla",
        "categoria": "Naturaleza",
        "source": "pines/nat1.jpg",
        "autor_usuario": "elianjami",
    },

    # ---------- ana_paisajes (10) ----------
    {
        "titulo": "Mural urbano colorido",
        "descripcion": "Mural callejero con tonos vivos en una pared larga.",
        "tags": "arte,mural,urbano,color",
        "categoria": "Arte",
        "source": "pines/art3.jpg",
        "autor_usuario": "ana_paisajes",
    },
    {
        "titulo": "Acuarela suave",
        "descripcion": "Composicion en acuarela con tonos pastel.",
        "tags": "arte,acuarela,pastel,pintura",
        "categoria": "Arte",
        "source": "pines/art4.jpg",
        "autor_usuario": "ana_paisajes",
    },
    {
        "titulo": "Vuelta de formacion",
        "descripcion": "Monoplazas en fila durante la vuelta previa.",
        "tags": "f1,formacion,parrilla,carrera",
        "categoria": "Formula 1",
        "source": "pines/f13.jpg",
        "autor_usuario": "ana_paisajes",
    },
    {
        "titulo": "Pase filtrado al area",
        "descripcion": "Centrocampista soltando un pase entre lineas.",
        "tags": "futbol,pase,jugada,tactica",
        "categoria": "Futbol",
        "source": "pines/fut3.jpg",
        "autor_usuario": "ana_paisajes",
    },
    {
        "titulo": "Carretera y dos ruedas",
        "descripcion": "Moto naked en carretera abierta al atardecer.",
        "tags": "motos,carretera,naked,viaje",
        "categoria": "Motos",
        "source": "pines/moto2.jpg",
        "autor_usuario": "ana_paisajes",
    },
    {
        "titulo": "Moto clasica restaurada",
        "descripcion": "Moto vintage cafe racer en exposicion.",
        "tags": "motos,clasica,cafe racer,vintage",
        "categoria": "Motos",
        "source": "pines/moto3.jpg",
        "autor_usuario": "ana_paisajes",
    },
    {
        "titulo": "Codazo en el ring",
        "descripcion": "Tecnica de codo en posicion corta.",
        "tags": "muay thai,codo,tecnica,combate",
        "categoria": "Muay Thai",
        "source": "pines/muay3.jpg",
        "autor_usuario": "ana_paisajes",
    },
    {
        "titulo": "Cascada en la selva",
        "descripcion": "Cascada alta cayendo entre vegetacion densa.",
        "tags": "naturaleza,cascada,selva,agua",
        "categoria": "Naturaleza",
        "source": "pines/nat2.jpg",
        "autor_usuario": "ana_paisajes",
    },
    {
        "titulo": "Montana nevada",
        "descripcion": "Pico nevado contra cielo despejado.",
        "tags": "naturaleza,montana,nieve,paisaje",
        "categoria": "Naturaleza",
        "source": "pines/nat3.jpg",
        "autor_usuario": "ana_paisajes",
    },
    {
        "titulo": "Lago al atardecer",
        "descripcion": "Lago tranquilo reflejando el cielo naranja.",
        "tags": "naturaleza,lago,atardecer,reflejo",
        "categoria": "Naturaleza",
        "source": "pines/nat4.jpg",
        "autor_usuario": "ana_paisajes",
    },

    # ---------- chef_dario (10) ----------
    {
        "titulo": "Escultura en metal",
        "descripcion": "Pieza escultorica moderna en metal pulido.",
        "tags": "arte,escultura,metal,moderno",
        "categoria": "Arte",
        "source": "pines/art5.jpg",
        "autor_usuario": "chef_dario",
    },
    {
        "titulo": "Pole position",
        "descripcion": "Monoplaza saliendo desde la pole en la parrilla.",
        "tags": "f1,pole,salida,carrera",
        "categoria": "Formula 1",
        "source": "pines/f14.jpg",
        "autor_usuario": "chef_dario",
    },
    {
        "titulo": "Podio de carrera",
        "descripcion": "Pilotos celebrando con champagne en el podio.",
        "tags": "f1,podio,celebracion,carrera",
        "categoria": "Formula 1",
        "source": "pines/f15.jpg",
        "autor_usuario": "chef_dario",
    },
    {
        "titulo": "Atajada a quemarropa",
        "descripcion": "Portero volando para sacar un remate cercano.",
        "tags": "futbol,portero,atajada,jugada",
        "categoria": "Futbol",
        "source": "pines/fut4.jpg",
        "autor_usuario": "chef_dario",
    },
    {
        "titulo": "Gol celebrado en grupo",
        "descripcion": "Jugadores festejando un gol en bola.",
        "tags": "futbol,gol,celebracion,equipo",
        "categoria": "Futbol",
        "source": "pines/fut5.jpg",
        "autor_usuario": "chef_dario",
    },
    {
        "titulo": "Trail por la montana",
        "descripcion": "Moto de enduro subiendo un sendero rocoso.",
        "tags": "motos,enduro,trail,montana",
        "categoria": "Motos",
        "source": "pines/moto4.jpg",
        "autor_usuario": "chef_dario",
    },
    {
        "titulo": "Moto custom en taller",
        "descripcion": "Moto custom en taller bajo luces calidas.",
        "tags": "motos,custom,taller,detalle",
        "categoria": "Motos",
        "source": "pines/moto5.jpg",
        "autor_usuario": "chef_dario",
    },
    {
        "titulo": "Rodillazo en clinch",
        "descripcion": "Rodillazo al cuerpo desde posicion de clinch.",
        "tags": "muay thai,rodilla,clinch,combate",
        "categoria": "Muay Thai",
        "source": "pines/muay4.jpg",
        "autor_usuario": "chef_dario",
    },
    {
        "titulo": "Entrenamiento en saco",
        "descripcion": "Peleador trabajando combinaciones en el saco.",
        "tags": "muay thai,entrenamiento,saco,tecnica",
        "categoria": "Muay Thai",
        "source": "pines/muay5.jpg",
        "autor_usuario": "chef_dario",
    },
    {
        "titulo": "Playa al amanecer",
        "descripcion": "Olas suaves rompiendo a primera luz del dia.",
        "tags": "naturaleza,playa,amanecer,mar",
        "categoria": "Naturaleza",
        "source": "pines/nat5.jpg",
        "autor_usuario": "chef_dario",
    },
]


def poblar():
    with Session(engine) as session:
        # revisa si ya hay usuarios para no duplicar nada si el script se corre dos veces
        existentes = session.exec(select(Usuarios)).all()
        if existentes:
            print("La base de datos ya tiene usuarios, no se hace nada.")
            return

        # crea los usuarios primero, se necesitan los ids para asignar autores a los pines
        usuarios_creados = {}
        for datos in USUARIOS_INICIALES:
            nuevo = Usuarios(
                nombre=datos["nombre"],
                usuario=datos["usuario"],
                email=datos["email"],
                password=hash_password(datos["password"]),
                bio=datos["bio"],
                rol=datos["rol"],
            )
            session.add(nuevo)
            session.commit()
            session.refresh(nuevo)
            usuarios_creados[datos["usuario"]] = nuevo.id
            print(f"Usuario creado: {datos['usuario']} ({datos['rol'].value})")

        # ahora crea los pines, cada uno asociado a su autor por usuario_id
        for datos in PINES_INICIALES:
            autor_id = usuarios_creados.get(datos["autor_usuario"])
            if autor_id is None:
                print(f"Autor no encontrado para el pin: {datos['titulo']}")
                continue

            pin = Pines(
                titulo=datos["titulo"],
                descripcion=datos["descripcion"],
                tags=datos["tags"],
                categoria=datos["categoria"],
                source=datos["source"],
                usuario_id=autor_id,
                es_publico=True,
            )
            session.add(pin)

        session.commit()
        print(f"Listo, se agregaron {len(USUARIOS_INICIALES)} usuarios y {len(PINES_INICIALES)} pines.")


if __name__ == "__main__":
    poblar()