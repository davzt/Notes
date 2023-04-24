from pydantic import AnyHttpUrl, BaseSettings, PostgresDsn


class Settings(BaseSettings):
    DATABASE_URI: PostgresDsn
    TEST_DATABASE_URI: PostgresDsn = None

    PORT: int
    URL_PREFIX: str = '/notes/api'

    CORS_ORIGINS: list[AnyHttpUrl] = []

    USE_OAUTH2_AUTHORIZATION: bool
    SECRET_KEY: str
    ALGORITHM: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int
    REQUIRES_VERIFICATION: bool

    class Config:
        case_sensitive = True
        env_file = '.env'
        env_prefix = 'NOTES_'


settings = Settings()
