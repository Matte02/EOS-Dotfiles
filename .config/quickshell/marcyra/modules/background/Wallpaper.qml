pragma ComponentBehavior: Bound
import QtQuick
import qs.components

Item {
    id: root
    required property string source
    property int loadSeq: 0
    property Image current: one

    function normUrl(u) {
        return u && u.startsWith("file://") ? u : (u ? ("file://" + u) : "");
    }

    onSourceChanged: {
        const want = normUrl(source);
        loadSeq++;
        if (!want) {
            current = null;
            return;
        }
        const target = (current === one) ? two : one;
        target.update(want, loadSeq);
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
        asynchronous: true

        opacity: 0
        property int seq: -1
        property url desired: ""

        function update(url, s) {
            seq = s;
            desired = url;
            if (source === desired && status === Image.Ready) {
                // already usable, promote immediately
                root.current = img;
                return;
            }
            // keep old frame visible; start loading hidden buffer
            opacity = 0;
            source = desired;
        }

        onStatusChanged: {
            if (status === Image.Ready && seq === root.loadSeq && source === desired) {
                root.current = img;
            }
            // Optional: basic retry on transient errors for the latest request
            if (status === Image.Error && seq === root.loadSeq) {
                // Re-trigger once; a more elaborate backoff can be added if needed
                const u = desired;
                desired = "";
                source = "";
                source = u;
            }
        }

        states: State {
            name: "visible"
            when: root.current === img
            PropertyChanges {
                img.opacity: 1
            }
        }

        transitions: Transition {
            Anim {
                target: img
                properties: "opacity"
            }
        }
    }
}
