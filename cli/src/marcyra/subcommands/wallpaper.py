import json
import pprint

import random
from pathlib import Path
from typing import Iterable, Optional, Union, Dict, List

from marcyra.utils.hypr import message
from marcyra.utils.paths import (
    ensure_dirs,
    wallpapers_dir,
    wallpaper_map_path,
    output_link_path,
    atomic_dump,
)

# Register Parser and Run


def register(subparsers):
    p = subparsers.add_parser("wallpaper", help="manage the wallpapers")

    group = p.add_mutually_exclusive_group(required=False)
    group.add_argument(
        "-p", "--print", metavar="FILE", help="print JSON colors for FILE (uses smart mode unless disabled)"
    )
    group.add_argument("-f", "--file", metavar="FILE", help="set a specific wallpaper file")
    group.add_argument("-r", "--random", nargs="?", const=wallpapers_dir, metavar="DIR", help="set a random wallpaper")

    p.add_argument(
        "-o",
        "--output",
        action="append",
        metavar="OUTPUT",
        help="target output(s) (repeatable), defaults to all outputs",
    )

    p.set_defaults(func=run)
    return p


def run(args):
    if args.print:
        print("Printing Colors")
    elif args.file:
        set_wallpaper(
            args.file,
            outputs=getattr(args, "output", None),
        )
    elif args.random:
        set_random(
            args.random,
            outputs=getattr(args, "output", None),
        )
    # Set same random wallpaper
    else:
        pprint.pp(get_wallpaper(getattr(args, "output", None)))


# ---------- validation ----------

_VALID_SUFFIXES = {".jpg", ".jpeg", ".png", ".webp", ".tif", ".tiff"}


def is_valid_image(path: Path) -> bool:
    """Basic file + extension check."""
    return path.is_file() and path.suffix.lower() in _VALID_SUFFIXES


# ---------- hyprland monitors ----------


def get_monitors() -> List[dict]:
    """Return Hyprland monitors JSON via the existing IPC helper."""
    # Expected keys include: name, width, height, focused, etc.
    # See Hyprland docs for hyprctl monitors JSON fields.
    return message("monitors")  # type: ignore[no-any-return]


def list_output_names() -> List[str]:
    """All active output names (e.g., DP-1, HDMI-A-1)."""
    return [m["name"] for m in get_monitors()]


def resolve_outputs(requested: Optional[Iterable[str]]) -> List[str]:
    """If outputs are provided, validate them; otherwise target all outputs."""
    available = set(list_output_names())
    if requested:
        req = list(requested)
        unknown = [o for o in req if o not in available]
        if unknown:
            raise ValueError(f"Unknown outputs: {', '.join(unknown)}")
        return req
    return list(available)


# ---------- mapping persistence ----------


def load_outputs_map() -> Dict[str, str]:
    """Load the output->path mapping."""
    if wallpaper_map_path.is_file():
        try:
            return json.loads(wallpaper_map_path.read_text())
        except json.JSONDecodeError:
            pass
    return {}


def save_outputs_map(mapping: Dict[str, str]) -> None:
    """Atomically persist the output->path mapping."""
    atomic_dump(wallpaper_map_path, mapping)


def _iter_wallpapers(root: Path) -> List[Path]:
    # Recursive walk; filter by known image suffixes
    return [p for p in root.rglob("*") if is_valid_image(p)]


# Main Functions
def set_random(directory: Optional[Union[str, Path]] = None, outputs: Optional[Iterable[str]] = None) -> None:
    ensure_dirs()

    root = Path(directory).expanduser().resolve()
    if not root.is_dir():
        raise ValueError(f'"{root}" is not a directory')

    targets = resolve_outputs(outputs)
    if not targets:
        return

    wallpapers = _iter_wallpapers(root)
    if not wallpapers:
        raise ValueError(f'No Wallpapers found under "{root}"')
    # Deduplicate by absolute path string
    wallpapers_paths = list({str(p.resolve()): p.resolve() for p in wallpapers}.values())

    current_map = load_outputs_map()
    currently_used = set(current_map.values())

    # Prefer pool excluding anything currently used anywhere
    preferred_pool = [p for p in wallpapers if str(p) not in currently_used]

    chosen: Dict[str, Path] = {}

    # Case 1: enough unique fresh images for all outputs
    if len(preferred_pool) >= len(targets):
        picks = random.sample(preferred_pool, len(targets))
        for out, wallpaper in zip(targets, picks):
            chosen[out] = wallpaper
    else:
        # Take all fresh unique first
        remaining_targets = list(targets)
        random.shuffle(preferred_pool)
        for wallpaper in preferred_pool:
            if not remaining_targets:
                break
            out = remaining_targets.pop()
            chosen[out] = wallpaper

        # Fill the rest by relaxing constraints per-output, still avoiding its current and already chosen
        pool_all = wallpapers_paths[:]
        random.shuffle(pool_all)
        assigned = {str(p) for p in chosen.values()}
        for out in remaining_targets:
            avoid = {current_map.get(out, "")} | assigned
            options = [p for p in pool_all if str(p) not in avoid]
            pick = random.choice(options if options else pool_all)
            chosen[out] = pick
            assigned.add(str(pick))

    # Persist mapping and symlinks in a single pass
    mapping = load_outputs_map()
    for out, p in chosen.items():
        mapping[out] = str(p)
    save_outputs_map(mapping)

    for out, p in chosen.items():
        link = output_link_path(out)
        try:
            link.unlink(missing_ok=True)
        except Exception:
            pass
        link.symlink_to(p)


def get_wallpaper(output: Optional[str] = None) -> Union[None, str, Dict[str, str]]:
    """
    If output is provided, return its wallpaper path or None.
    If output is None, return the whole mapping (possibly empty).
    """
    mapping = load_outputs_map()
    if output is None:
        return mapping
    return mapping.get(output)


def set_wallpaper(wall: Path | str, outputs: list[str] | None = None) -> None:
    ensure_dirs()
    wall = Path(wall).resolve()

    if not is_valid_image(wall):
        raise ValueError(f'"{wall}" is not a valid image')

    targets = resolve_outputs(outputs)
    # Update mapping
    mapping = load_outputs_map()
    for out in targets:
        mapping[out] = str(wall)

    save_outputs_map(mapping)

    for out in targets:
        link = output_link_path(out)
        try:
            link.unlink(missing_ok=True)
        except Exception:
            pass
        link.symlink_to(wall)
