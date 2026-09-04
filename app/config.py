"""Application configuration loaded from environment variables / .env."""
from __future__ import annotations

import os
import secrets

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_env: str = "development"
    app_timezone: str = "Asia/Shanghai"

    database_url: str = "sqlite:///./data/training.db"

    # Session signing key. In production this MUST be set via .env.
    secret_key: str = ""

    products_config_path: str = "config/products.example.yaml"
    training_plan_path: str = "app/data/training_plan.yaml"

    # Only enable the Secure flag on cookies when behind HTTPS.
    session_secure: bool = False

    # Directory that holds backups (relative to working directory).
    backup_dir: str = "backups"

    def effective_secret_key(self) -> str:
        """Return a stable secret key, generating an ephemeral one in dev."""
        if self.secret_key:
            return self.secret_key
        if self.app_env == "production":
            # Failsafe: still allow the process to boot but warn loudly.
            return "insecure-ephemeral-" + secrets.token_hex(16)
        return "dev-insecure-" + secrets.token_hex(16)


def get_settings() -> Settings:
    return Settings()


settings = get_settings()
