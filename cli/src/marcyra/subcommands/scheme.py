import json
from marcyra.utils.scheme import (
    Scheme,
    get_scheme,
    get_scheme_flavours,
    get_scheme_modes,
    get_scheme_names,
    scheme_variants,
)


def register(subparsers):
    scheme_parser = subparsers.add_parser("scheme", help="manage the colour scheme")
    scheme_command_subparser = scheme_parser.add_subparsers(title="subcommands")

    # List Commands
    list_parser = scheme_command_subparser.add_parser("list", help="list available schemes")
    list_parser.add_argument("-n", "--names", action="store_true", help="list scheme names")
    list_parser.add_argument("-f", "--flavours", action="store_true", help="list scheme flavours")
    list_parser.add_argument("-m", "--modes", action="store_true", help="list scheme modes")
    list_parser.add_argument("-v", "--variants", action="store_true", help="list scheme variants")

    get_parser = scheme_command_subparser.add_parser("get", help="get scheme properties")
    get_parser.add_argument("-n", "--name", action="store_true", help="print the current scheme name")
    get_parser.add_argument("-f", "--flavour", action="store_true", help="print the current scheme flavour")
    get_parser.add_argument("-m", "--mode", action="store_true", help="print the current scheme mode")
    get_parser.add_argument("-v", "--variant", action="store_true", help="print the current scheme variant")

    set_parser = scheme_command_subparser.add_parser("set", help="set the current scheme")
    set_parser.add_argument("--notify", action="store_true", help="send a notification on error")
    set_parser.add_argument("-r", "--random", action="store_true", help="switch to a random scheme")
    set_parser.add_argument("-n", "--name", choices=get_scheme_names(), help="the name of the scheme to switch to")
    set_parser.add_argument("-f", "--flavour", help="the flavour to switch to")
    set_parser.add_argument("-m", "--mode", choices=["dark", "light"], help="the mode to switch to")
    set_parser.add_argument("-v", "--variant", choices=scheme_variants, help="the variant to switch to")

    list_parser.set_defaults(func=run_list)
    get_parser.set_defaults(func=run_get)
    set_parser.set_defaults(func=run_set)

    scheme_parser.set_defaults(func=run_list)

    return scheme_parser


def run_list(args):
    multiple = [args.names, args.flavours, args.modes, args.variants].count(True) > 1

    if args.names or args.flavours or args.modes or args.variants:
        if args.names:
            if multiple:
                print("Names:", *get_scheme_names())
            else:
                print("\n".join(get_scheme_names()))
        if args.flavours:
            if multiple:
                print("Flavours:", *get_scheme_flavours())
            else:
                print("\n".join(get_scheme_flavours()))
        if args.modes:
            if multiple:
                print("Modes:", *get_scheme_modes())
            else:
                print("\n".join(get_scheme_modes()))
        if args.variants:
            if multiple:
                print("Variants:", *scheme_variants)
            else:
                print("\n".join(scheme_variants))
    else:
        current_scheme = get_scheme()
        schemes = {}
        for scheme in get_scheme_names():
            schemes[scheme] = {}
            for flavour in get_scheme_flavours(scheme):
                s = Scheme(
                    {
                        "name": scheme,
                        "flavour": flavour,
                        "mode": current_scheme.mode,
                        "variant": current_scheme.variant,
                        "colours": current_scheme.colours,
                    }
                )
                modes = get_scheme_modes(scheme, flavour)
                if s.mode not in modes:
                    s._mode = modes[0]
                try:
                    s._update_colours()
                    schemes[scheme][flavour] = s.colours
                except ValueError:
                    pass

        print(json.dumps(schemes, indent=2))


def run_get(args):
    scheme = get_scheme()

    if args.name or args.flavour or args.mode or args.variant:
        if args.name:
            print(scheme.name)
        if args.flavour:
            print(scheme.flavour)
        if args.mode:
            print(scheme.mode)
        if args.variant:
            print(scheme.variant)
    else:
        print(scheme)


def run_set(args):
    scheme = get_scheme()

    if args.notify:
        scheme.notify = True

    if args.random:
        scheme.set_random()
        # apply_colours(scheme.colours, scheme.mode)

    elif args.name or args.flavour or args.mode or args.variant:
        if args.name:
            scheme.name = args.name
        if args.flavour:
            scheme.flavour = args.flavour
        if args.mode:
            scheme.mode = args.mode
        if args.variant:
            scheme.variant = args.variant
        # apply_colours(scheme.colours, scheme.mode)
    else:
        print("No args given. Use --name, --flavour, --mode, --variant or --random to set a scheme")
