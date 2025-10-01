from marcyra.parser import build_parser

def main(argv=None) -> None:
    print("START")
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)