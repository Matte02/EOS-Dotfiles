pragma Singleton

import Quickshell
import Quickshell.Io

Singleton {
    id: root

    property alias appearance: adapter.appearance
    JsonAdapter {
        id: adapter
        property AppearanceConfig appearance: AppearanceConfig {}
    }
}
