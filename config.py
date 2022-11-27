from pydantic import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    DEFAULT_VAR="some default" # default value if env variable does not exist
    API_KEY: str
    APP_MAX: int=199 # default value if env variable does not exist
    ENTSOE_API_KEY: str

# specify .env file location as Config attribute
    class Config:
        env_file = ".env"

# New decorator for cache
@lru_cache()
def get_settings():
    return Settings()