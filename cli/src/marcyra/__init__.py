from marcyra.parser import build_parser


def main(argv=None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)
