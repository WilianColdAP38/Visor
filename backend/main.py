from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware



from db import create_all_tables
from app.routers import usuarios, pines, categorias, comentarios, likes

app = FastAPI(title="Visor API", lifespan=create_all_tables)

# solo se permiten los origenes del front en local, no cualquier sitio
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://127.0.0.1:5500",
        "http://localhost:5500",
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


@app.get("/")
def root():
    return {"message": "Visor API funcionando"}