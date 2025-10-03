from typing import Mapping, Type
from materialyoucolor.hct import Hct
from materialyoucolor.blend import Blend

from materialyoucolor.dynamiccolor.material_dynamic_colors import (
    DynamicScheme,
    MaterialDynamicColors,
)

from materialyoucolor.scheme.scheme_content import SchemeContent
from materialyoucolor.scheme.scheme_expressive import SchemeExpressive
from materialyoucolor.scheme.scheme_fidelity import SchemeFidelity
from materialyoucolor.scheme.scheme_fruit_salad import SchemeFruitSalad
from materialyoucolor.scheme.scheme_monochrome import SchemeMonochrome
from materialyoucolor.scheme.scheme_neutral import SchemeNeutral
from materialyoucolor.scheme.scheme_rainbow import SchemeRainbow
from materialyoucolor.scheme.scheme_tonal_spot import SchemeTonalSpot
from materialyoucolor.scheme.scheme_vibrant import SchemeVibrant

_SCHEMES: Mapping[str, Type[DynamicScheme]] = {
    "content": SchemeContent,
    "expressive": SchemeExpressive,
    "fidelity": SchemeFidelity,
    "fruitsalad": SchemeFruitSalad,
    "monochrome": SchemeMonochrome,
    "neutral": SchemeNeutral,
    "rainbow": SchemeRainbow,
    "tonalspot": SchemeTonalSpot,
    "vibrant": SchemeVibrant,  # default
}


def get_scheme(name: str) -> Type[DynamicScheme]:
    return _SCHEMES.get(name, SchemeVibrant)


def hex_to_hct(hex: str) -> Hct:
    return Hct.from_int(int(f"0xFF{hex}", 16))


light_gruvbox = [
    hex_to_hct("FDF9F3"),
    hex_to_hct("FF6188"),
    hex_to_hct("A9DC76"),
    hex_to_hct("FC9867"),
    hex_to_hct("FFD866"),
    hex_to_hct("F47FD4"),
    hex_to_hct("78DCE8"),
    hex_to_hct("333034"),
    hex_to_hct("121212"),
    hex_to_hct("FF6188"),
    hex_to_hct("A9DC76"),
    hex_to_hct("FC9867"),
    hex_to_hct("FFD866"),
    hex_to_hct("F47FD4"),
    hex_to_hct("78DCE8"),
    hex_to_hct("333034"),
]

dark_gruvbox = [
    hex_to_hct("282828"),
    hex_to_hct("CC241D"),
    hex_to_hct("98971A"),
    hex_to_hct("D79921"),
    hex_to_hct("458588"),
    hex_to_hct("B16286"),
    hex_to_hct("689D6A"),
    hex_to_hct("A89984"),
    hex_to_hct("928374"),
    hex_to_hct("FB4934"),
    hex_to_hct("B8BB26"),
    hex_to_hct("FABD2F"),
    hex_to_hct("83A598"),
    hex_to_hct("D3869B"),
    hex_to_hct("8EC07C"),
    hex_to_hct("EBDBB2"),
]

light_catppuccin = [
    hex_to_hct("dc8a78"),
    hex_to_hct("dd7878"),
    hex_to_hct("ea76cb"),
    hex_to_hct("8839ef"),
    hex_to_hct("d20f39"),
    hex_to_hct("e64553"),
    hex_to_hct("fe640b"),
    hex_to_hct("df8e1d"),
    hex_to_hct("40a02b"),
    hex_to_hct("179299"),
    hex_to_hct("04a5e5"),
    hex_to_hct("209fb5"),
    hex_to_hct("1e66f5"),
    hex_to_hct("7287fd"),
]

dark_catppuccin = [
    hex_to_hct("f5e0dc"),
    hex_to_hct("f2cdcd"),
    hex_to_hct("f5c2e7"),
    hex_to_hct("cba6f7"),
    hex_to_hct("f38ba8"),
    hex_to_hct("eba0ac"),
    hex_to_hct("fab387"),
    hex_to_hct("f9e2af"),
    hex_to_hct("a6e3a1"),
    hex_to_hct("94e2d5"),
    hex_to_hct("89dceb"),
    hex_to_hct("74c7ec"),
    hex_to_hct("89b4fa"),
    hex_to_hct("b4befe"),
]

kcolours = [
    {"name": "klink", "hct": hex_to_hct("2980b9")},
    {"name": "kvisited", "hct": hex_to_hct("9b59b6")},
    {"name": "knegative", "hct": hex_to_hct("da4453")},
    {"name": "kneutral", "hct": hex_to_hct("f67400")},
    {"name": "kpositive", "hct": hex_to_hct("27ae60")},
]

colour_names = [
    "rosewater",
    "flamingo",
    "pink",
    "mauve",
    "red",
    "maroon",
    "peach",
    "yellow",
    "green",
    "teal",
    "sky",
    "sapphire",
    "blue",
    "lavender",
]


def _clamp(x: float, lo: float, hi: float) -> float:
    return lo if x < lo else hi if x > hi else x


def _with_hct(h: float, c: float, t: float) -> Hct:
    # Construct and let HCT perform gamut mapping; clamp tone preemptively.
    return Hct.from_hct(h, max(0.0, c), _clamp(t, 0.0, 100.0))


def grayscale(colour: Hct, light: bool) -> Hct:
    base_tone = colour.tone
    delta = (100.0 - base_tone) * 0.35 if light else base_tone * 0.65
    new_tone = base_tone + delta if light else base_tone - delta
    return _with_hct(colour.hue, 0.0, new_tone)


def lighten(colour: Hct, amount: float) -> Hct:
    diff = (100.0 - colour.tone) * amount
    # Avoid increasing chroma arbitrarily; clamp and let HCT handle gamut.
    return _with_hct(colour.hue, colour.chroma + diff / 5.0, colour.tone + diff)


def darken(colour: Hct, amount: float) -> Hct:
    diff = colour.tone * amount
    return _with_hct(colour.hue, colour.chroma + diff / 5.0, colour.tone - diff)


def mix(a: Hct, b: Hct, w: float) -> Hct:
    return Hct.from_int(Blend.cam16_ucs(a.to_int(), b.to_int(), w))


def harmonize(from_hct: Hct, to_hct: Hct, tone_boost: float) -> Hct:
    # Use official harmonize to move hue toward key; apply clamped tone boost.
    hct = Hct.from_int(Blend.harmonize(from_hct.to_int(), to_hct.to_int()))
    boost = 1.0 + tone_boost
    return _with_hct(hct.hue, hct.chroma, hct.tone * boost)


def gen_scheme(scheme, primary: Hct) -> dict[str, str]:
    light = scheme.mode == "light"

    colours = {}

    # Material colours
    primary_scheme = get_scheme(scheme.variant)(primary, not light, 0)
    for colour in vars(MaterialDynamicColors).keys():
        colour_name = getattr(MaterialDynamicColors, colour)
        if hasattr(colour_name, "get_hct"):
            colours[colour] = colour_name.get_hct(primary_scheme)

    # Harmonize terminal colours
    for i, hct in enumerate(light_gruvbox if light else dark_gruvbox):
        if scheme.variant == "monochrome":
            colours[f"term{i}"] = grayscale(hct, light)
        else:
            colours[f"term{i}"] = harmonize(
                hct, colours["primary_paletteKeyColor"], (0.35 if i < 8 else 0.2) * (-1 if light else 1)
            )

    # Harmonize named colours
    for i, hct in enumerate(light_catppuccin if light else dark_catppuccin):
        if scheme.variant == "monochrome":
            colours[colour_names[i]] = grayscale(hct, light)
        else:
            colours[colour_names[i]] = harmonize(hct, colours["primary_paletteKeyColor"], (-0.2 if light else 0.05))

    # KColours
    for colour in kcolours:
        colours[colour["name"]] = harmonize(colour["hct"], colours["primary"], 0.1)
        colours[f"{colour['name']}Selection"] = harmonize(colour["hct"], colours["onPrimaryFixedVariant"], 0.1)
        if scheme.variant == "monochrome":
            colours[colour["name"]] = grayscale(colours[colour["name"]], light)
            colours[f"{colour['name']}Selection"] = grayscale(colours[f"{colour['name']}Selection"], light)

    if scheme.variant == "neutral":
        for name, hct in colours.items():
            colours[name].chroma -= 15

    # FIXME: deprecated stuff
    colours["text"] = colours["onBackground"]
    colours["subtext1"] = colours["onSurfaceVariant"]
    colours["subtext0"] = colours["outline"]
    colours["overlay2"] = mix(colours["surface"], colours["outline"], 0.86)
    colours["overlay1"] = mix(colours["surface"], colours["outline"], 0.71)
    colours["overlay0"] = mix(colours["surface"], colours["outline"], 0.57)
    colours["surface2"] = mix(colours["surface"], colours["outline"], 0.43)
    colours["surface1"] = mix(colours["surface"], colours["outline"], 0.29)
    colours["surface0"] = mix(colours["surface"], colours["outline"], 0.14)
    colours["base"] = colours["surface"]
    colours["mantle"] = darken(colours["surface"], 0.03)
    colours["crust"] = darken(colours["surface"], 0.05)

    # For debugging
    # print("\n".join(["{}: \x1b[48;2;{};{};{}m   \x1b[0m".format(n, *c.to_rgba()[:3]) for n, c in colours.items()]))

    colours = {k: hex(v.to_int())[4:] for k, v in colours.items()}

    # Extended material
    if light:
        colours["success"] = "4F6354"
        colours["onSuccess"] = "FFFFFF"
        colours["successContainer"] = "D1E8D5"
        colours["onSuccessContainer"] = "0C1F13"
    else:
        colours["success"] = "B5CCBA"
        colours["onSuccess"] = "213528"
        colours["successContainer"] = "374B3E"
        colours["onSuccessContainer"] = "D1E9D6"

    return colours
