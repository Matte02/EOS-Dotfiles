import argparse
from importlib import metadata


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="marcyra",
        description="Marcyra dotfiles control CLI",
    )
    parser.add_argument(
        "-v",
        "--version",
        action="version",
        version=f"%(prog)s {metadata.version('marcyra')}",
    )

    subparsers = parser.add_subparsers(
        title="subcommands",
        description="valid subcommands",
        metavar="COMMAND",
        help="the subcommand to run",
        required=True,
    )
    from marcyra.subcommands import wallpaper, shell, scheme

    wallpaper.register(subparsers)
    shell.register(subparsers)
    scheme.register(subparsers)
    return parser
