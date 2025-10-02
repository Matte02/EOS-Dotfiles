pragma ComponentBehavior: Bound

import Quickshell
import Quickshell.Wayland
import QtQuick

import qs.utils
import qs.services

Loader {
    active: true
    sourceComponent: Variants {
        model: Quickshell.screens

        PanelWindow {
            id: win
            required property ShellScreen modelData

            screen: modelData
            color: "#000000"

            readonly property string outputName: (modelData && modelData.name) ? modelData.name : ""
            property string sourcePath: Wallpapers.getWallpaper(outputName)

            WlrLayershell.exclusionMode: ExclusionMode.Ignore
            WlrLayershell.layer: WlrLayer.Background

            anchors {
                top: true
                bottom: true
                left: true
                right: true
            }

            Connections {
                target: Wallpapers
                function onChanged() {
                    win.sourcePath = Wallpapers.getWallpaper(win.outputName);
                }
            }

            Wallpaper {
                anchors.fill: parent
                source: win.sourcePath
            }
        }
    }
}
