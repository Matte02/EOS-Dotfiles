pragma Singleton

import Marcyra
import Quickshell

Singleton {
    id: root

    readonly property string home: Quickshell.env("HOME")
    readonly property string pictures: Quickshell.env("XDG_PICTURES_DIR") || `${home}/Pictures`
    readonly property string videos: Quickshell.env("XDG_VIDEOS_DIR") || `${home}/Videos`

    readonly property string data: `${Quickshell.env("XDG_DATA_HOME") || `${home}/.local/share`}/marcyra`
    readonly property string state: `${Quickshell.env("XDG_STATE_HOME") || `${home}/.local/state`}/marcyra`
    readonly property string cache: `${Quickshell.env("XDG_CACHE_HOME") || `${home}/.cache`}/marcyra`
    readonly property string config: `${Quickshell.env("XDG_CONFIG_HOME") || `${home}/.config`}/marcyra`

    readonly property string imagecache: `${cache}/imagecache`
    readonly property string notifimagecache: `${imagecache}/notifs`
    readonly property string wallsdir: Quickshell.env("MARCYRA_WALLPAPERS_DIR") || `${pictures}/Wallpapers`
    readonly property string recsdir: Quickshell.env("MARCYRA_RECORDINGS_DIR") || `${videos}/Recordings`
    readonly property string libdir: Quickshell.env("MARCYRA_LIB_DIR") || "/usr/lib/marcyra"

    function toLocalFile(path: url): string {
        path = Qt.resolvedUrl(path);
        return path.toString() ? CUtils.toLocalFile(path) : "";
    }

    function absolutePath(path: string): string {
        return toLocalFile(path.replace("~", home));
    }

    function shortenHome(path: string): string {
        return path.replace(home, "~");
    }
}
