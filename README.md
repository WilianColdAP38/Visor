# Visor

Aplicacion web multimedia tipo Pinterest desarrollada como Proyecto Integrador de 4to nivel de Sistemas (UIDE), que articula tres materias: **Programacion Web**, **Gestion Cloud** y **Etica**.

Permite a los usuarios registrarse, iniciar sesion, explorar un feed en mosaico con categorias y busqueda, ver el detalle de cada pin, comentar y dar like. El contenido multimedia se almacena en **AWS S3** (bucket privado) y se sirve mediante **URLs prefirmadas**, lo que constituye el mecanismo etico-tecnico central del proyecto.

---

## Link publico de la aplicacion

**http://3.150.90.185:8000/**

La aplicacion completa (frontend + API) corre desde una instancia EC2 Ubuntu 24.04 en la region us-east-2. El bucket de medios `visor-media-prod` provee las imagenes a traves de URLs prefirmadas con expiracion de 3600 segundos.

Usuarios de prueba (sembrados):

| Usuario        | Password      | Rol   |
|----------------|---------------|-------|
| `elianjami`    | `admin12345`  | ADMIN |
| `ana_paisajes` | `ana123456`   | USER  |
| `chef_dario`   | `dario12345`  | USER  |

---

## Arquitectura desplegada

```
Navegador del usuario
        |
        v
  EC2 Ubuntu (us-east-2)  ---->  Sirve frontend estatico (HTML, CSS, JS)
  3.150.90.185:8000              Expone la API FastAPI
        |
        v  (boto3, credenciales IAM)
  S3 visor-media-prod           Almacena pines/ y avatares/
                                Privado, sin acceso publico
                                Sirve via URLs prefirmadas (3600s)
```

- **Frontend:** HTML semantico + CSS vanilla + JS vanilla + jQuery 3.7.1 local. Cero frameworks. Servido por FastAPI mediante `StaticFiles` desde las rutas `/html`, `/estilos` y `/js`.
- **Backend:** FastAPI + SQLModel + SQLite + bcrypt + JWT. Routers separados por recurso (usuarios, pines, categorias, comentarios, likes).
- **Cloud:** Bucket S3 privado `visor-media-prod` con SSE-S3 y versionado. Usuario IAM unico `wilian-visor-app-s3` con politica `VisorAppS3` (solo `s3:PutObject` y `s3:GetObject` sobre el bucket). Sin acceso a consola.
- **Persistencia:** SQLite local en `db.sqlite3` con 3 usuarios y 30 pines reales sembrados (6 categorias: Arte, Formula 1, Futbol, Motos, Muay Thai, Naturaleza).
- **Despliegue:** EC2 t3.micro con Elastic IP, security group con SSH restringido a la IP del desarrollador y puerto 8000 abierto. Proceso uvicorn corriendo dentro de `tmux` para sobrevivir al cierre de la sesion SSH.

---

## Estructura del repositorio

```
Visor/
|-- backend/
|   |-- app/
|   |   |-- routers/         # usuarios, pines, categorias, comentarios, likes
|   |   |-- auth.py          # JWT y dependencias de sesion
|   |   `-- config.py        # lee y valida variables del .env
|   |-- models.py            # modelos SQLModel
|   |-- db.py                # conexion a SQLite y lifespan
|   |-- main.py              # punto de entrada API + StaticFiles del front
|   |-- seed.py              # poblado inicial (3 usuarios + 30 pines)
|   |-- requirements.txt
|   |-- .env.example         # plantilla de variables (sin secretos)
|   `-- (.env y db.sqlite3 NO se versionan)
`-- frontend/
    |-- estilos/             # base, components, index, detalle, auth, usuario
    |-- html/                # index, login, register, detalle, usuario
    `-- js/                  # api, header, index, detalle, auth + lib/jquery
```

---



## Como replicar el proyecto en otra maquina (Windows)

### Requisitos previos

- Python 3.11 o superior
- Git
- VS Code o cualquier editor
- (Opcional) Live Server para abrir el frontend en local en el puerto 5500

### 1. Clonar el repositorio

```powershell
cd "C:\ruta\donde\quieres\el\proyecto"
git clone https://github.com/WilianColdAP38/Visor.git
cd Visor\backend
```

### 2. Crear y activar entorno virtual

```powershell
python -m venv venv
venv\Scripts\activate
```

### 3. Instalar dependencias

```powershell
pip install -r requirements.txt
```

### 4. Configurar variables de entorno

```powershell
copy .env.example .env
```

Editar `.env` y completar:

```env
SECRET_KEY=una_cadena_larga_y_aleatoria_para_jwt

AWS_REGION=us-east-2
AWS_ACCESS_KEY_ID=tu_access_key
AWS_SECRET_ACCESS_KEY=tu_secret_key
S3_BUCKET_NAME=visor-media-prod
```

Las credenciales AWS deben corresponder a un usuario IAM con permisos `s3:PutObject` y `s3:GetObject` sobre el bucket configurado.

### 5. Sembrar la base de datos

Solo la primera vez, despues de levantar la API una vez para que se creen las tablas:

```powershell
python seed.py
```

Esto crea 3 usuarios y 10 pines de ejemplo. Los 30 pines reales con keys de S3 forman parte del `db.sqlite3` de produccion y no se replican con `seed.py` (es esperado: el seed publico usa URLs de placeholder).

### 6. Levantar la API

```powershell
$env:PYTHONIOENCODING="utf-8"; uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

### 7. Abrir la aplicacion

En el navegador: **http://localhost:8000/**

La raiz redirige automaticamente a `/html/index.html` y se carga el feed. Tambien estan disponibles:

- `http://localhost:8000/docs` — Swagger UI con todos los endpoints.
- `http://localhost:8000/api` — ping de verificacion.
- `http://localhost:8000/pines/` — JSON con los pines del feed.

---

## Como replicar el despliegue en AWS (EC2 + S3)

### A. Bucket S3 de medios

1. Crear bucket `visor-media-prod` en `us-east-2`.
2. Mantener bloqueado el acceso publico (Block all public access activado).
3. Habilitar SSE-S3 y versionado.
4. Crear los prefijos (carpetas) `pines/` y `avatares/`.

### B. Usuario IAM

1. Crear politica `VisorAppS3` con el JSON minimo:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": ["s3:PutObject", "s3:GetObject"],
      "Resource": "arn:aws:s3:::visor-media-prod/*"
    }
  ]
}
```

2. Crear usuario IAM `wilian-visor-app-s3` sin acceso a consola.
3. Adjuntar la politica `VisorAppS3`.
4. Generar par de claves de acceso (Access Key ID + Secret) tipo "Outside AWS".

### C. Instancia EC2

1. Lanzar instancia Ubuntu 24.04 LTS, tipo `t3.micro` en `us-east-2`.
2. Security group: SSH (22) desde la IP del desarrollador, TCP personalizado (8000) desde `0.0.0.0/0`.
3. Asignar y asociar una Elastic IP a la instancia.
4. Conectarse por SSH con el `.pem` descargado:

```powershell
ssh -i visor-key.pem ubuntu@TU_IP_ELASTICA
```

5. Dentro de la EC2:

```bash
sudo apt update
sudo apt install -y python3-venv python3-pip git tmux
git clone https://github.com/WilianColdAP38/Visor.git
cd Visor/backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

6. Copiar `.env` y `db.sqlite3` desde la maquina local (en otra ventana de PowerShell):

```powershell
scp -i visor-key.pem .env ubuntu@TU_IP_ELASTICA:~/Visor/backend/.env
scp -i visor-key.pem db.sqlite3 ubuntu@TU_IP_ELASTICA:~/Visor/backend/db.sqlite3
```

7. Levantar la API dentro de tmux para que sobreviva al cierre de SSH:

```bash
tmux new -s visor
source venv/bin/activate
PYTHONIOENCODING=utf-8 uvicorn main:app --host 0.0.0.0 --port 8000
```

Luego `Ctrl+B` y `D` para detachar. Para reconectarse: `tmux attach -t visor`.

8. La aplicacion queda disponible en `http://TU_IP_ELASTICA:8000/`.

---

## Endpoints principales

| Metodo | Ruta                              | Descripcion                                |
|--------|-----------------------------------|--------------------------------------------|
| POST   | `/usuarios/register`              | Registrar nuevo usuario                    |
| POST   | `/usuarios/login`                 | Login JSON, devuelve JWT                   |
| POST   | `/usuarios/token`                 | Login OAuth2 para Swagger Authorize        |
| GET    | `/usuarios/me`                    | Datos del usuario autenticado              |
| GET    | `/pines/`                         | Feed con URLs prefirmadas de S3            |
| POST   | `/pines/`                         | Crear pin (sube imagen a S3 via boto3)     |
| GET    | `/pines/{id}`                     | Detalle de un pin                          |
| GET    | `/categorias/`                    | Lista de categorias                        |
| GET    | `/pines/{id}/comentarios`         | Comentarios de un pin                      |
| POST   | `/pines/{id}/comentarios`         | Crear comentario (requiere sesion)         |
| POST   | `/pines/{id}/like`                | Dar/quitar like (requiere sesion)          |

Documentacion interactiva: `/docs`.

---

## Stack

| Capa            | Tecnologia                                                    |
|-----------------|---------------------------------------------------------------|
| Frontend        | HTML5 semantico, CSS vanilla, JS vanilla, jQuery 3.7.1 local  |
| Backend         | FastAPI, SQLModel, Pydantic                                   |
| Base de datos   | SQLite                                                        |
| Autenticacion   | bcrypt + JWT (python-jose)                                    |
| Almacenamiento  | AWS S3 (boto3) con URLs prefirmadas                           |
| Servidor        | Uvicorn en EC2 Ubuntu 24.04                                   |
| Region AWS      | us-east-2                                                     |

---

## Equipo

- **Wilian Elian Jami** 
- **Omar Pacheco** 
- **Erick Gualli** 

Proyecto Integrador 4to semestre, Universidad Internacional del Ecuador (UIDE), 2026.
