from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    """
    BaseSettings loads configuration from environment variables, validating them as pydantic models
    Provide default values
    Easier to declare and validate rather then using os.getenv() directly
    Removes the need of using python-dotenv as well
    A single source of truth

    NOTE: By default, Pydantic maps attribute names to env vars (case-insensitive)
    e.g database_url ->	DATABASE_URL
    """
    database_url: str
    redis_url: str
    secret_key: str
    access_token_expire_minutes: int = 60

    # Load variables from .env automatically
    # Ignore extra env variables not defined in the model
    model_config = {
        "env_file": ".env",
        "extra": "ignore"
    }

settings = Settings()