import subprocess
from marcyra.utils.paths import m_cache_dir

# Register Parser and Run


def register(subparsers):
    p = subparsers.add_parser("shell", help="start or message the shell")

    p.add_argument("message", nargs="*", help="a message to send to the shell")
    p.add_argument("-d", "--daemon", action="store_true", help="start the shell detached")
    p.add_argument("-s", "--show", action="store_true", help="print all shell IPC commands")
    p.add_argument("-l", "--log", action="store_true", help="print the shell log")
    p.add_argument("-k", "--kill", action="store_true", help="kill the shell")
    p.add_argument("--log-rules", metavar="RULES", help="log rules to apply")

    p.set_defaults(func=run)
    return p


def run(args):
    if args.kill:
        shell_command("kill")
    else:
        shell_args = ["qs", "-c", "marcyra", "-n"]
        if args.daemon:
            shell_args.append("-d")
            subprocess.run(shell_args)
        else:
            shell = subprocess.Popen(shell_args, stdout=subprocess.PIPE, universal_newlines=True)
            for line in shell.stdout:
                if filter_log(line):
                    print(line, end="")


def shell_command(*shell_args: list[str]) -> str:
    return subprocess.check_output(["qs", "-c", "marcyra", *shell_args], text=True)


def filter_log(line: str) -> bool:
    return f"Cannot open: file://{m_cache_dir}/imagecache/" not in line
