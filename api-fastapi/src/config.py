import os
import tomllib
from pydantic import Field
from pydantic_settings import BaseSettings

def load_toml_project():
    with open("pyproject.toml", "rb") as f:
        data = tomllib.load(f)
    return data["project"]

mode = os.getenv('APP_ENV', 'development')

class Settings(BaseSettings):
    project: dict = Field(default_factory=load_toml_project)

    uvicorn_host: str
    uvicorn_port: int

    keycloak_openid_host: str
    keycloak_openid_realm: str
    keycloak_openid_scope: str

    keycloak_client_id: str
    keycloak_client_secret: str

    url_backend: str
    url_frontend: str

    url_tfnexus: str

    class Config:
        env_file=('.env', f'{mode}.env') # if 'dev' in sys.argv else 'production.env' )

settings = Settings()
