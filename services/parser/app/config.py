from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    service_secret: str = ""
    max_file_size_mb: int = 100
    allowed_extensions: str = ".pdf,.docx,.pptx,.html,.htm,.md,.txt"
    log_level: str = "info"

    @property
    def allowed_extensions_set(self) -> set[str]:
        return {ext.strip() for ext in self.allowed_extensions.split(",")}

    @property
    def max_file_size_bytes(self) -> int:
        return self.max_file_size_mb * 1024 * 1024


settings = Settings()
