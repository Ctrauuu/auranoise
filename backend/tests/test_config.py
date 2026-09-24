from app.core.config import Settings


def test_neon_url_is_normalized_for_asyncpg() -> None:
    settings = Settings(
        database_url="postgresql://user:pass@example.neon.tech/db?sslmode=require&channel_binding=require",
        _env_file=None,
    )
    assert settings.database_url == "postgresql+asyncpg://user:pass@example.neon.tech/db?ssl=require"
