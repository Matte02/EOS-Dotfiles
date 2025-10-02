import hashlib
import json
import os
import shutil
import tempfile
from pathlib import Path

config_dir = Path(os.getenv("XDG_CONFIG_HOME", Path.home() / ".config"))
data_dir = Path(os.getenv("XDG_DATA_HOME", Path.home() / ".local/share"))
state_dir = Path(os.getenv("XDG_STATE_HOME", Path.home() / ".local/state"))
cache_dir = Path(os.getenv("XDG_CACHE_HOME", Path.home() / ".cache"))
pictures_dir = Path(os.getenv("XDG_PICTURES_DIR", Path.home() / "Pictures"))
videos_dir = Path(os.getenv("XDG_VIDEOS_DIR", Path.home() / "Videos"))


m_config_dir = config_dir / "marcyra"
m_data_dir = data_dir / "marcyra"
m_state_dir = state_dir / "marcyra"
m_cache_dir = cache_dir / "marcyra"

# Wallpaper state (multi-output)

wallpapers_dir = os.getenv("MARCYRA_WALLPAPERS_DIR", pictures_dir / "Wallpapers")
wallpaper_state_dir = m_state_dir / "wallpaper"
wallpaper_outputs_dir = wallpaper_state_dir / "outputs"  # per-output symlinks
wallpaper_map_path = wallpaper_state_dir / "outputs.json"  # mapping: output -> absolute path

# Wallpaper cache (per-image hash)
wallpapers_cache_dir = m_cache_dir / "wallpapers"  # each image gets a hashed subdir

# Utilities


def ensure_dirs() -> None:
    """Create all directories needed by the module."""
    for p in (
        m_config_dir,
        m_data_dir,
        m_state_dir,
        m_cache_dir,
        wallpaper_state_dir,
        wallpaper_outputs_dir,
        wallpapers_cache_dir,
    ):
        p.mkdir(parents=True, exist_ok=True)


def output_link_path(output: str) -> Path:
    """Symlink target used by QuickShell/consumers to detect changes for a given output."""
    return wallpaper_outputs_dir / output


def output_thumb_link_path(output: str) -> Path:
    """Optional per-output thumbnail symlink for UI surfaces."""
    return wallpaper_outputs_dir / f"{output}.thumb.jpg"


def image_cache_dir(image_path: Path | str) -> Path:
    """Return the cache directory for a specific image (by SHA-256 of its content)."""
    return wallpapers_cache_dir / compute_hash(image_path)


def image_thumb_cache_path(image_path: Path | str) -> Path:
    """Thumbnail location for a specific image inside its cache directory."""
    return image_cache_dir(image_path) / "thumbnail.jpg"


def compute_hash(path: Path | str) -> str:
    sha = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(8192):
            sha.update(chunk)
    return sha.hexdigest()


def atomic_dump(path: Path, content: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile("w", delete=False) as f:
        json.dump(content, f)
        f.flush()
        os.fsync(f.fileno())
        tempname = f.name
    shutil.move(tempname, path)
