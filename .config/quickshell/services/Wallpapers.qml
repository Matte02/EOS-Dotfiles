// qs/services/Wallpapers.qml
pragma Singleton
import Quickshell.Io
import qs.utils
import Quickshell

Singleton {
    id: svc

    // Path to the outputs mapping
    // Prefer central config/paths; falls back to XDG/state integration in your app
    property string outputsJsonPath: `${Paths.state}/wallpaper/outputs.json`

    // Reactive data
    property var map: ({})
    readonly property var keys: Object.keys(map)

    signal changed

    FileView {
        id: fv
        path: svc.outputsJsonPath
        watchChanges: true
        onFileChanged: reload()
        onLoaded: svc._updateFromText()
    }

    function _updateFromText() {
        try {
            const t = fv.text();
            const obj = t && t.trim().length ? JSON.parse(t) : {};
            svc.map = obj || {};
            svc.changed();
        } catch (e) {
            console.warn("Wallpapers: parse error", e);
            svc.map = {};
            svc.changed();
        }
    }

    // Convenience accessor; returns "" if missing
    function getWallpaper(outputName) {
        return (svc.map && outputName in svc.map) ? String(svc.map[outputName]) : "";
    }
}
