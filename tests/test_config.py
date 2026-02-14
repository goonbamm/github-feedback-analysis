"""Tests for configuration persistence behavior."""

from github_feedback.core.config import Config


def test_dump_creates_parent_directories_for_custom_path(tmp_path):
    """Config.dump should create missing parent directories for custom paths."""
    target_path = tmp_path / "nested" / "dir" / "config.toml"

    Config().dump(path=target_path, backup=False)

    assert target_path.exists()


def test_dump_backup_uses_same_parent_directory(tmp_path):
    """Backup files should be written alongside the target config path."""
    target_path = tmp_path / "nested" / "dir" / "config.toml"

    Config().dump(path=target_path, backup=False)
    Config().dump(path=target_path, backup=True)

    backups = list(target_path.parent.glob(f"{target_path.stem}.*.bak"))
    assert len(backups) == 1
    assert backups[0].parent == target_path.parent
