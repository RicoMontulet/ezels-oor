from app.config import REPOSITORY_ROOT, Settings


def test_settings_resolve_repository_root_env_file():
    assert (REPOSITORY_ROOT / "backend/app/config.py").is_file()
    assert REPOSITORY_ROOT / ".env" == Settings.model_config["env_file"]
