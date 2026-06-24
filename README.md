# Visor · Aplicación web multimedia (estilo Pinterest)

Visor es una aplicación web donde los usuarios se registran, inician sesión, suben imágenes y exploran un feed en mosaico. El **backend** (FastAPI + SQLite) expone una API; el **frontend** (HTML, CSS y JavaScript con jQuery) la consume. Las imágenes **no** se guardan en la base de datos: viven en un bucket privado de **Amazon S3** y se sirven con **URLs prefirmadas** temporales.

> Proyecto Integrador · 4to Semestre · Gestión de Servicios Cloud (AWS) · UIDE
> Autores: Wilian Jami, Omar Pacheco, Erick Gualli — Quito, 2026

---

## Stack

| Capa | Tecnologías |
|---|---|
| Backend | FastAPI, SQLModel, SQLite, bcrypt, python-jose (JWT HS256), boto3, uvicorn |
| Frontend | HTML, CSS y JavaScript con jQuery 3.7.1 (local) |
| Nube | Amazon S3 (`us-east-2`) e IAM |

---

## Estructura del repositorio

```
Visor/
├── backend/
│   ├── app/
│   │   ├── routers/        # usuarios, pines, categorias, comentarios, likes
│   │   ├── auth.py         # JWT y dependencias de sesión
│   │   └── config.py       # lee y valida las variables del .env
│   ├── models.py           # modelos de datos (SQLModel)
│   ├── db.py               # conexión a SQLite
│   ├── main.py             # punto de entrada de la API + CORS
│   ├── seed.py             # poblado inicial (3 usuarios + 30 pines)
│   ├── requirements.txt    # dependencias
│   ├── .env                # credenciales (NO se versiona)
│   ├── .env.example        # plantilla de variables
│   └── db.sqlite3          # base local (NO se versiona)
└── frontend/
    ├── estilos/            # hojas de estilo CSS
    ├── html/               # index, login, register, detalle, usuario
    └── js/                 # scripts + js/lib/ (jQuery)
```

El `.gitignore` excluye `.env`, `venv/` y `db.sqlite3`. **Ninguna clave secreta llega al repositorio.**

---

## Requisitos previos

- **Python 3.11 o superior**
- **Git**
- Un servidor estático para el frontend (la extensión **Live Server** de VS Code, puerto `5500`, es la usada en el proyecto)
- Credenciales del usuario IAM `wilian-visor-app-s3` (Access Key ID y Secret Access Key). La infraestructura AWS —bucket `visor-media-prod`, política de mínimo privilegio, etc.— debe estar creada según el Manual Técnico Cloud.

---

## Puesta en marcha local

### 1. Clonar el repositorio

```bash
git clone https://github.com/WilianColdAP38/Visor
cd Visor/backend
```

### 2. Entorno virtual e instalación de dependencias

```bash
python -m venv venv

# Activar el entorno
venv\Scripts\activate        # Windows
# source venv/bin/activate   # Linux / macOS

pip install -r requirements.txt
```

### 3. Configurar el `.env`

Copia `.env.example` como `.env` y rellena los valores reales del usuario `wilian-visor-app-s3`:

```bash
copy .env.example .env       # Windows
# cp .env.example .env       # Linux / macOS
```

Contenido de `.env.example`:

```env
# --- App ---
APP_NAME=Visor API
APP_ENV=development

# --- Seguridad / JWT ---
SECRET_KEY=<genera_una_clave_larga_y_aleatoria>
JWT_ALGORITHM=HS256
JWT_EXPIRE_MINUTES=180

# --- AWS (usuario wilian-visor-app-s3) ---
AWS_REGION=us-east-2
AWS_ACCESS_KEY_ID=AKIA...
AWS_SECRET_ACCESS_KEY=<clave_secreta_generada_en_IAM>

# nombre del bucket privado de imágenes
S3_BUCKET_NAME=visor-media-prod
```

> ⚠️ El `.env` **nunca** se sube al repositorio. La región debe coincidir con la del bucket (`us-east-2`).
> ⚠️ El `.env` se lee **solo al arrancar**. Si lo editas con el servidor encendido, reinícialo a mano: `--reload` recarga el código, no las variables de entorno.

### 4. Poblar la base de datos

El script crea las tablas e inserta datos de ejemplo (3 usuarios y 30 pines reales con sus claves de S3). Se ejecuta **una sola vez**:

```bash
python seed.py
```

Usuarios que crea el seed: **`elianjami`** (admin), **`ana_paisajes`** y **`chef_dario`**. La contraseña está definida dentro de `seed.py` (revísala ahí para iniciar sesión).

> Si la base ya tiene usuarios, el seed se detiene. Para re-sembrar desde cero, borra `db.sqlite3` de la carpeta `backend/` y vuelve a ejecutarlo.

### 5. Levantar el backend (FastAPI)

```bash
set PYTHONIOENCODING=utf-8                 # Windows: evita errores de acentos en consola
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

Espera el mensaje `Application startup complete`. La documentación interactiva queda en **http://127.0.0.1:8000/docs**.

### 6. Servir el frontend y probar

Con el backend en el puerto **8000**, sirve la carpeta `frontend/` con **Live Server** (puerto `5500`). El backend ya autoriza ese origen en su configuración de **CORS**.

Abre `frontend/html/index.html` desde Live Server, inicia sesión con `elianjami` y comprueba que el feed carga las imágenes servidas desde S3.

Flujo de prueba completo: registrar usuario → iniciar sesión → publicar un pin con imagen → verlo aparecer en el feed.

---

## Cómo funciona la integración con S3 (resumen)

- **Subida** (`POST /pines`): el backend valida sesión (JWT) y archivo (solo `jpg/png/webp`, máx. 5 MB), sube el objeto con boto3 al prefijo `pines/{uuid}-{archivo}` y guarda en SQLite **la clave del objeto**, no una URL.
- **Lectura** (`GET /pines`): por cada clave, el backend genera una **URL prefirmada** de solo lectura con caducidad corta (1 h). El navegador carga la imagen por ese enlace temporal.
- **Privacidad verificable**: abrir la URL directa del objeto, sin firmar, devuelve **Access Denied**. Esa es la prueba de que el bucket es privado.

---

## Problemas frecuentes

| Síntoma | Causa probable | Solución |
|---|---|---|
| `InvalidAccessKeyId` | Quedaron los `<...>` de la plantilla en el `.env` | Pega las claves reales sin los signos `<>` |
| El feed no muestra imágenes | Faltan credenciales en `.env` o región incorrecta | Revisa `AWS_*` y que `AWS_REGION=us-east-2` |
| Cambié el `.env` y no surte efecto | El `.env` solo se lee al arrancar | Reinicia uvicorn manualmente |
| El frontend carga sin estilos | Rutas relativas rotas al servir | Sirve respetando la estructura de carpetas (`html/`, `estilos/`, `js/`) |
| Acentos rotos en consola (Windows) | Codificación | `set PYTHONIOENCODING=utf-8` antes de uvicorn |

---

## Despliegue en línea

El frontend se publica como sitio estático en un **segundo bucket público** (p. ej. `visor-frontend-prod`) con hosting estático y política de lectura pública. El bucket de imágenes (`visor-media-prod`) sigue privado. El procedimiento completo está en el **Capítulo 7** del Manual Técnico Cloud.

## Ramas

`main` (estable) · `develop` (en curso) · `feature/programacion-web` · `feature/cloud` · `feature/etica`
