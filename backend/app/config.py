from pydantic_settings import BaseSettings, SettingsConfigDict


# carga las variables del .env al iniciar la app y las valida con tipos
# si falta una critica como SECRET_KEY, la app no arranca, no falla en runtime
class Settings(BaseSettings):
    # app
    APP_NAME: str = "Visor API"
    APP_ENV: str = "development"

    # jwt, el SECRET_KEY no tiene default a proposito, es obligatorio en el .env
    SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 180

    # aws, se llenan cuando exista el bucket S3, por eso son strings vacios validos
    AWS_REGION: str = "us-east-2"
    AWS_ACCESS_KEY_ID: str = ""
    AWS_SECRET_ACCESS_KEY: str = ""
    S3_BUCKET_NAME: str = ""

    # le dice a pydantic donde esta el .env y que ignore variables extra del sistema
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


# instancia unica, se importa desde donde haga falta como: from app.config import settings
settings = Settings()









