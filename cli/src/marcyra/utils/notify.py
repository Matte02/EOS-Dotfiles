import subprocess


def notify(*args: list[str]) -> str:
    return subprocess.check_output(["notify-send", "-a", "marcyra-cli", *args], text=True).strip()


# TODO: Dubble check this
def close_notification(id: str) -> None:
    subprocess.run(
        [
            "gdbus",
            "call",
            "--session",
            "--dest=org.freedesktop.Notifications",
            "--object-path=/org/freedesktop/Notifications",
            "--method=org.freedesktop.Notifications.CloseNotification",
            id,
        ],
        stdout=subprocess.DEVNULL,
    )
