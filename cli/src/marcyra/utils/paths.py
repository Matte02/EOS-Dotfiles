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


# CLI Directories
cli_data_dir = Path(__file__).parent.parent / "data"


# Wallpaper state (multi-output)

wallpapers_dir = os.getenv("MARCYRA_WALLPAPERS_DIR", pictures_dir / "Wallpapers")
wallpaper_state_dir = m_state_dir / "wallpaper"
wallpaper_map_path = wallpaper_state_dir / "outputs.json"
thumbs_map_path = wallpaper_state_dir / "thumbs.json"  # NEW: output -> absolute thumbnail path

wallpaper_main_output_path = wallpaper_state_dir / "main-output.txt"
wallpaper_thumbnail_path = wallpaper_state_dir / "thumbnail.jpg"

# Wallpaper cache (per-image hash)
wallpapers_cache_dir = m_cache_dir / "wallpapers"  # each image gets a hashed subdir

# Scheme
scheme_path = m_state_dir / "scheme.json"
scheme_data_dir = cli_data_dir / "schemes"
scheme_cache_dir = m_cache_dir / "schemes"

# Themes
templates_dir = cli_data_dir / "templates"


# Utilities
def ensure_dirs() -> None:
    """Create all directories needed by the module."""
    for p in (
        m_config_dir,
        m_data_dir,
        m_state_dir,
        m_cache_dir,
        wallpaper_state_dir,
        wallpapers_cache_dir,
    ):
        p.mkdir(parents=True, exist_ok=True)


def load_json_or(path: Path, default):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return default


def safe_symlink(link: Path, target: Path) -> None:
    link.parent.mkdir(parents=True, exist_ok=True)
    try:
        link.unlink(missing_ok=True)
    except TypeError:
        try:
            link.unlink()
        except FileNotFoundError:
            pass
    link.symlink_to(target)


def atomic_dump(path: Path, content: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile("w", dir=path.parent, delete=False, encoding="utf-8") as f:
        json.dump(content, f)
        f.flush()
        os.fsync(f.fileno())
        tmp = f.name
    os.replace(tmp, path)  # atomic within same dir/filesystem
    try:
        dfd = os.open(path.parent, os.O_DIRECTORY)
        try:
            os.fsync(dfd)
        finally:
            os.close(dfd)
    except Exception:
        pass


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
