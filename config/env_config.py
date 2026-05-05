from pydantic_settings import BaseSettings


class EnvFile(BaseSettings):
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_DB: str
    POSTGRES_HOST: str
    POSTGRES_PORT: str
    REDIS_URL: str

    class Config:
        env_file: str = ".env"


env: EnvFile = EnvFile()
