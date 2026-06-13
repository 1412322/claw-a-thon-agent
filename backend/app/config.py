from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache


class Settings(BaseSettings):
    greenode_api_key: str = ""
    greenode_endpoint: str = "https://maas-llm-aiplatform-hcm.api.vngcloud.vn/v1/chat/completions"
    greenode_model: str = "qwen/qwen3-5-27b"
    chroma_persist_dir: str = "./chroma_db"
    allowed_origins: str = "http://localhost:5173,http://localhost:3000"
    llm_provider: str = "greenode"
    llm_model: str = "qwen/qwen3-5-27b"

    # Jira Configuration
    jira_base_url: str = ""
    jira_email: str = ""
    jira_api_token: str = ""
    jira_project_key: str = ""
    jira_default_assignee: str = ""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra='ignore')

    @property
    def origins_list(self) -> list[str]:
        return [o.strip() for o in self.allowed_origins.split(",")]


@lru_cache()
def get_settings() -> Settings:
    return Settings()
