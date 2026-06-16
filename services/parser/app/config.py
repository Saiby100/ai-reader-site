from pydantic_settings import BaseSettings


class Settings(BaseSettings):
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
