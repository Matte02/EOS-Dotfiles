pragma ComponentBehavior: Bound
import QtQuick
import qs.components

Item {
    id: root
    required property string source
    property Image current: one

    onSourceChanged: {
        if (!source)
            current = null;
        else if (current === one)
            two.update();
        else
            one.update();
    }

    anchors.fill: parent

    Img {
        id: one
    }

    Img {
        id: two
    }

    component Img: Image {
        id: img
        anchors.fill: parent
        fillMode: Image.PreserveAspectCrop
        cache: false
        asynchronous: true

        // Visual defaults; animated to 1.0 in the "visible" state
        opacity: 0

        // Normalize to file:// to satisfy Image URL expectations
        function normUrl(u) {
            return u && u.startsWith("file://") ? u : (u ? ("file://" + u) : "");
        }

        function update(): void {
            const want = normUrl(root.source);
            if (source === want) {
                // Already showing desired image: promote immediately
                root.current = this;
                return;
            }
            // Reset visuals and trigger async decode on the hidden buffer
            opacity = 0;
            source = want;
        }
        // Promote to active only after decode completes for a flicker-free fade
        onStatusChanged: {
            if (status === Image.Ready)
                root.current = img;
        }
        // Becomes "visible" when this buffer is the active one
        states: State {
            name: "visible"
            when: root.current === img

            PropertyChanges {
                img.opacity: 1
            }
        }
        // Opacity crossfade; uses shared Anim defaults
        transitions: Transition {
            Anim {
                target: img
                properties: "opacity"
            }
        }
    }
}
