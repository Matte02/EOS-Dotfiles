

def register(subparsers):
    p = subparsers.add_parser("wallpaper", help="manage the wallpapers")

    group = p.add_mutually_exclusive_group(required=False)
    group.add_argument("-p", "--print", metavar="FILE", help="print JSON colors for FILE (uses smart mode unless disabled)")
    group.add_argument("-f", "--file", metavar="FILE", help="set a specific wallpaper file")
    group.add_argument("-r","--random", action="store_true", help="set a random wallpaper")

    p.set_defaults(func=run)
    return p


def run(args):
    print(args)

    if args.print:
        print("Printing Colors")
    elif args.file:
        set_wallpaper(args.file)
        #else:
            # Set same wallpapers for all monitors
    #elif args.random:
            # Set same random wallpaper
    #else:
        # Print wallpaper path
        # Else print No wallpaper set

def set_wallpaper(wall: str) -> None:
    print("Setting Wallpaper: " + wall)