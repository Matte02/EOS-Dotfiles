import json
import random
from collections import defaultdict
from pathlib import Path
from typing import Iterable, Optional, Union, Dict, List, Tuple

from PIL import Image
from marcyra.utils.material import get_colours_for_image
from marcyra.utils.theme import apply_colours
from materialyoucolor.hct import Hct
from materialyoucolor.utils.color_utils import argb_from_rgb

from marcyra.utils.scheme import get_scheme
from marcyra.utils.hypr import message
from marcyra.utils.paths import (
    compute_hash,
    ensure_dirs,
    wallpaper_map_path,
    thumbs_map_path,
    wallpaper_thumbnail_path,
    wallpaper_main_output_path,
    atomic_dump,
    load_json_or,
    safe_symlink,
    wallpapers_cache_dir,
    image_cache_dir,
    wallpapers_dir,
)

VALID_SUFFIXES = {".jpg", ".jpeg", ".png", ".webp", ".tif", ".tiff"}

# Register Parser and Run


def register(subparsers):
    p = subparsers.add_parser("wallpaper", help="manage the wallpapers")

    group = p.add_mutually_exclusive_group(required=False)
    group.add_argument(
        "-p", "--print", metavar="FILE", help="print JSON colors for FILE (uses smart mode unless disabled)"
    )
    group.add_argument("-f", "--file", metavar="FILE", help="set a specific wallpaper file")
    group.add_argument("-r", "--random", nargs="?", const=wallpapers_dir, metavar="DIR", help="set a random wallpaper")
    group.add_argument(
        "-smo",
        "--set-main-output",
        dest="set_main_output",
        metavar="OUTPUT",
        help="set the main output used for dynamic scheming",
    )

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
    elif args.set_main_output:
        set_main_output(args.set_main_output)
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
        print_wallpaper_report()


# -------- Files & JSON --------


def load_outputs_map() -> Dict[str, str]:
    return load_json_or(wallpaper_map_path, {})


def load_thumbs_map() -> Dict[str, str]:
    return load_json_or(thumbs_map_path, {})


def save_outputs_map(mapping: Dict[str, str]) -> None:
    atomic_dump(wallpaper_map_path, mapping)


def save_thumbs_map(mapping: Dict[str, str]) -> None:
    atomic_dump(thumbs_map_path, mapping)


# -------- Hyprland --------


def get_monitors() -> List[dict]:
    return message("monitors")  # IPC JSON


def list_output_names() -> List[str]:
    return [m["name"] for m in get_monitors()]


def resolve_outputs(requested: Optional[Iterable[str]]) -> List[str]:
    available = set(list_output_names())
    if requested:
        req = list(requested)
        unknown = [o for o in req if o not in available]
        if unknown:
            raise ValueError(f"Unknown outputs: {', '.join(unknown)}")
        return req
    return list(available)


# -------- Images & Caching --------


def is_valid_image(path: Path) -> bool:
    return path.is_file() and path.suffix.lower() in VALID_SUFFIXES


def iter_wallpapers(root: Path) -> List[Path]:
    # De-duplicate by resolved string once
    seen: Dict[str, Path] = {}
    for p in root.rglob("*"):
        if p.suffix.lower() in VALID_SUFFIXES and p.is_file():
            rp = str(p.resolve())
            if rp not in seen:
                seen[rp] = p.resolve()
    return list(seen.values())


def get_thumb(src: Path, cache: Path) -> Path:
    thumb = cache / "thumbnail.jpg"
    if not thumb.exists():
        cache.mkdir(parents=True, exist_ok=True)
        with Image.open(src) as img:
            img = img.convert("RGB")
            img.thumbnail((128, 128), Image.LANCZOS)
            img.save(thumb, "JPEG")
    return thumb


def get_smart_options(wall: Path, cache: Path) -> Dict[str, str]:
    options_cache = cache / "smart.json"
    try:
        return json.loads(options_cache.read_text(encoding="utf-8"))
    except Exception:
        pass

    from marcyra.utils.colourfulness import get_variant

    # Use the 128x128 thumb to avoid decoding full image again
    thumb = get_thumb(wall, cache)
    options: Dict[str, str] = {}
    with Image.open(thumb) as img:
        options["variant"] = get_variant(img)
        # 1x1 to probe light/dark tone cheaply
        options["mode"] = "dark"
        # tiny = img.copy()
        # tiny.thumbnail((1, 1), Image.LANCZOS)
        # hct = Hct.from_int(argb_from_rgb(*tiny.getpixel((0, 0))))
        # options["mode"] = "light" if hct.tone > 200 else "dark"

    options_cache.parent.mkdir(parents=True, exist_ok=True)
    options_cache.write_text(json.dumps(options), encoding="utf-8")
    return options


# -------- Selection policy --------


def choose_for_targets(
    targets: List[str],
    candidates: List[Path],
    current_map: Dict[str, str],
) -> Dict[str, Path]:
    # Avoid currently used images globally first
    used = set(current_map.values())
    fresh_pool = [p for p in candidates if str(p) not in used]
    chosen: Dict[str, Path] = {}

    if len(fresh_pool) >= len(targets):
        picks = random.sample(fresh_pool, len(targets))
        for out, wall in zip(targets, picks):
            chosen[out] = wall
        return chosen

    # Greedy assign all fresh first
    remaining = targets[:]
    random.shuffle(fresh_pool)
    for wall in fresh_pool:
        if not remaining:
            break
        chosen[remaining.pop()] = wall

    # Fill rest by avoiding each-output current and already-chosen
    pool_all = candidates[:]
    random.shuffle(pool_all)
    assigned = {str(p) for p in chosen.values()}
    for out in remaining:
        avoid = {current_map.get(out, "")} | assigned
        options = [p for p in pool_all if str(p) not in avoid]
        pick = random.choice(options if options else pool_all)
        chosen[out] = pick
        assigned.add(str(pick))
    return chosen


# -------- Main-output helpers --------


def is_main_output(output: str) -> bool:
    if wallpaper_main_output_path.exists():
        return wallpaper_main_output_path.read_text(encoding="utf-8").strip() == output
    return False


def set_main_output(output: str) -> None:
    if output not in set(list_output_names()):
        raise ValueError(f"Unknown output: {output}")

    wallpaper_main_output_path.parent.mkdir(parents=True, exist_ok=True)
    wallpaper_main_output_path.write_text(output, encoding="utf-8")

    out_map = load_outputs_map()
    thumbs_map = load_thumbs_map()

    wall_str = out_map.get(output)
    if not wall_str:
        return  # will be set later by set_wallpaper/set_random

    wall = Path(wall_str)
    if output not in thumbs_map:
        cache = image_cache_dir(wall)
        thumb = get_thumb(wall, cache)
        thumbs_map[output] = str(thumb)
        save_thumbs_map(thumbs_map)

    safe_symlink(wallpaper_thumbnail_path, Path(thumbs_map[output]))

    scheme = get_scheme()
    if scheme.name == "dynamic":
        smart = get_smart_options(wall, image_cache_dir(wall))
        scheme.mode = smart["mode"]
        scheme.variant = smart["variant"]
    scheme.update_colours()
    apply_colours(scheme.colours, scheme.mode)


# -------- Wall application --------


def apply_wallpapers(assignments: Dict[str, Path]) -> None:
    # 1) Update both JSON maps atomically (each its own atomic write)
    out_map = load_outputs_map()
    out_map.update({out: str(p) for out, p in assignments.items()})
    save_outputs_map(out_map)

    thumbs_map = load_thumbs_map()
    for out, p in assignments.items():
        cache = wallpapers_cache_dir / compute_hash(p)
        thumb = get_thumb(p, cache)
        thumbs_map[out] = str(thumb)
    save_thumbs_map(thumbs_map)

    # 2) If main output is part of the change, update the single symlink and scheme once
    scheme = get_scheme()
    main = None
    if wallpaper_main_output_path.exists():
        main = wallpaper_main_output_path.read_text(encoding="utf-8").strip()

    if main and main in assignments:
        thumb_path = Path(thumbs_map[main])
        safe_symlink(wallpaper_thumbnail_path, thumb_path)

        if scheme.name == "dynamic":
            smart = get_smart_options(Path(out_map[main]), image_cache_dir(out_map[main]))
            scheme.mode = smart["mode"]
            scheme.variant = smart["variant"]
        scheme.update_colours()
        apply_colours(scheme.colours, scheme.mode)


# -------- Public API --------


def set_random(directory: Optional[Union[str, Path]] = None, outputs: Optional[Iterable[str]] = None) -> None:
    ensure_dirs()
    root = Path(directory or wallpapers_dir).expanduser().resolve()
    if not root.is_dir():
        raise ValueError(f'"{root}" is not a directory')

    targets = resolve_outputs(outputs)
    if not targets:
        return

    candidates = iter_wallpapers(root)
    if not candidates:
        raise ValueError(f'No wallpapers found under "{root}"')

    current_map = load_outputs_map()
    chosen = choose_for_targets(targets, candidates, current_map)
    apply_wallpapers(chosen)


def set_wallpaper(wall: Union[Path, str], outputs: Optional[Iterable[str]] = None) -> None:
    ensure_dirs()
    wall = Path(wall).resolve()
    if not is_valid_image(wall):
        raise ValueError(f'"{wall}" is not a valid image')

    targets = resolve_outputs(outputs)
    chosen = {out: wall for out in targets}
    apply_wallpapers(chosen)


# ------- Reporting -------


def rgb_from_hex(h: str) -> tuple[int, int, int]:
    s = h.lstrip("#")
    return int(s[0:2], 16), int(s[2:4], 16), int(s[4:6], 16)


def render_swatch(hexval: str, width: int = 6) -> str:
    r, g, b = rgb_from_hex(hexval)
    fg = f"\x1b[38;2;{r};{g};{b}m"
    reset = "\x1b[0m"
    block = "█" * width
    return f"{fg}{block}{reset} {fg}#{hexval.lstrip('#')}{reset}"


def print_wallpaper_report() -> None:
    mapping = load_outputs_map()
    if not mapping:
        print("No wallpapers set")
        return

    grouped: Dict[Path, List[str]] = defaultdict(list)
    for out, wall in mapping.items():
        grouped[Path(wall).expanduser().resolve()].append(out)

    for wall_path, outs in sorted(grouped.items(), key=lambda kv: str(kv[0])):
        outs_str = ", ".join(sorted(outs))
        print(f"Outputs: {outs_str}")
        print(f"Wallpaper: {wall_path}")

        scheme = get_scheme()
        cache = wallpapers_cache_dir / compute_hash(wall_path)
        smart = get_smart_options(wall_path, cache)
        print("Scheme name: dynamic")
        print("Scheme flavour: default")
        print(f"Scheme mode: {smart.get('mode', scheme.mode)}")
        print(f"Scheme variant: {smart.get('variant', scheme.variant)}")

        colours = get_colours_for_image(get_thumb(wall_path, cache), scheme)
        print("Scheme colors:")
        for name, hexval in colours.items():
            try:
                swatch = render_swatch(hexval, 6)
            except Exception:
                swatch = f"#{hexval.lstrip('#')}"
            print(f"  {name}: {swatch}")
        print("")
