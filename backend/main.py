from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from db import create_all_tables
from app.routers import usuarios, pines, categorias, comentarios, likes

app = FastAPI(title="Visor API", lifespan=create_all_tables)

# ruta a la carpeta frontend, que es hermana de backend
# la calculo desde este archivo asi no importa desde donde corra uvicorn
FRONTEND_DIR = Path(__file__).resolve().parent.parent / "frontend"

# origenes permitidos: el front en local y el front desplegado en S3
# si todo corre desde EC2 (mismo origen) no se usa, pero lo dejo por si pruebo con live server
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://127.0.0.1:5500",
        "http://localhost:5500",
        "http://visor-frontend-prod.s3-website.us-east-2.amazonaws.com",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# cada router se encarga de un recurso, asi main queda limpio
app.include_router(usuarios.router)
app.include_router(pines.router)
app.include_router(categorias.router)
app.include_router(comentarios.router)
app.include_router(likes.router)


@app.get("/api")
def root():
    return {"message": "Visor API funcionando"}


# si abren la raiz, los mando al index del front directamente
@app.get("/")
def home():
    return RedirectResponse(url="/html/index.html")


# sirvo los assets estaticos en sus propias rutas para respetar los href relativos
# como ../estilos/ y ../js/ que ya estan dentro de los html
app.mount("/estilos", StaticFiles(directory=FRONTEND_DIR / "estilos"), name="estilos")
app.mount("/js", StaticFiles(directory=FRONTEND_DIR / "js"), name="js")
app.mount("/html", StaticFiles(directory=FRONTEND_DIR / "html", html=True), name="html")