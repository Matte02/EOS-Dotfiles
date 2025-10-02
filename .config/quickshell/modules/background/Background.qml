import Quickshell
import Quickshell.Wayland
import Quickshell.Io
import QtQuick
import Marcyra.Models

Loader {
    active: true
    sourceComponent: Variants {
        model: Quickshell.screens

        PanelWindow {
            id: win
            required property ShellScreen modelData

            screen: modelData
            color: "#AA000000"

            readonly property string currentNamePath: `/home/matte/.local/state/marcyra/wallpaper/outputs.json`
            property string actualCurrent

            // Convenience: the Hyprland/Quickshell output name for this window
            readonly property string outputName: (modelData && modelData.name) ? modelData.name : ""

            WlrLayershell.exclusionMode: ExclusionMode.Ignore
            WlrLayershell.layer: WlrLayershell.Background

            anchors {
                top: true
                bottom: true
                left: true
                right: true
            }

            FileView {
                id: outputsFile
                path: win.currentNamePath
                watchChanges: true
                onFileChanged: reload()
                onLoaded: win.updateFromJson()
                // If the loader didn’t trigger for some reason but text changed, still update
                onTextChanged: win.updateFromJson()
            }

            // Re-extract when this window moves to a different screen or the name changes
            onScreenChanged: updateFromJson()

            // Extractor: parse JSON and set actualCurrent based on outputName
            function updateFromJson() {
                if (!outputName || !outputsFile.path)
                    return;

                try {
                    const txt = outputsFile.text();
                    if (!txt || txt.trim().length === 0) {
                        win.actualCurrent = "";
                        return;
                    }
                    const obj = JSON.parse(txt);
                    const path = obj && obj[outputName] ? String(obj[outputName]) : "";
                    win.actualCurrent = path;
                } catch (e) {
                    console.warn("Failed to parse outputs.json:", e);
                    win.actualCurrent = "";
                }
            }

            Image {
                anchors.fill: parent
                source: win.actualCurrent ? ("file://" + win.actualCurrent) : ""
                fillMode: Image.PreserveAspectCrop
                cache: false
                visible: !!win.actualCurrent
            }
        }
    }
}
