import Quickshell
import Quickshell.Io
import Quickshell.Wayland
import QtQuick
import QtQuick.Layouts
import QtQuick.Controls

Item {
  id: root

  property bool hudVisible: true
  property string greetingText: "Good evening, Jeffy 🌌"
  property string memText: "Loading..."
  property real memPercent: 0.25
  property string mediaTitle: "Ambient Desktop"
  property string mediaArtist: "Omarchy • Hyprland"
  property bool isPlaying: false
  property string miloChatOutput: "👋 Hey Jeffy! I'm Milo, your ambient AI companion on your desktop. Type any question below or press Super+A anytime!"
  property bool isThinking: false
  property var clockDate: new Date()

  // 1. Clock timer
  Timer {
    interval: 1000
    running: true
    repeat: true
    onTriggered: {
      root.clockDate = new Date()
      var hour = root.clockDate.getHours()
      if (hour < 12) root.greetingText = "Good morning, Jeffy 🌅"
      else if (hour < 17) root.greetingText = "Good afternoon, Jeffy ☀️"
      else if (hour < 22) root.greetingText = "Good evening, Jeffy 🌌"
      else root.greetingText = "Burning the midnight oil, Jeffy 🌙"
    }
  }

  // 2. Telemetry polling (Meminfo & Playerctl)
  Timer {
    interval: 3500
    running: true
    repeat: true
    triggeredOnStart: true
    onTriggered: {
      if (!memProc.running) memProc.running = true
      if (!mediaProc.running) mediaProc.running = true
    }
  }

  Process {
    id: memProc
    command: ["bash", "-c", "awk '/MemTotal/{t=$2} /MemAvailable/{a=$2} END{print t, t-a, int((t-a)/t*100)}' /proc/meminfo"]
    stdout: StdioCollector {
      onStreamFinished: {
        var parts = text.trim().split(" ")
        if (parts.length >= 3) {
          var totalGb = (parseFloat(parts[0]) / 1024 / 1024).toFixed(1)
          var usedGb = (parseFloat(parts[1]) / 1024 / 1024).toFixed(1)
          var pct = parseInt(parts[2]) || 0
          root.memText = usedGb + " / " + totalGb + " GB (" + pct + "%)"
          root.memPercent = pct / 100.0
        }
      }
    }
  }

  Process {
    id: mediaProc
    command: ["bash", "-c", "command -v playerctl >/dev/null 2>&1 && playerctl metadata --format '{{title}}:::{{artist}}:::{{status}}' 2>/dev/null || true"]
    stdout: StdioCollector {
      onStreamFinished: {
        var out = text.trim()
        if (out.indexOf(":::") !== -1) {
          var p = out.split(":::")
          root.mediaTitle = p[0] || "No Media Active"
          root.mediaArtist = p[1] || "Omarchy Audio"
          root.isPlaying = (p[2] === "Playing")
        } else {
          root.mediaTitle = "Ambient Desktop"
          root.mediaArtist = "Omarchy • Hyprland"
          root.isPlaying = false
        }
      }
    }
  }

  // 3. Antigravity CLI Execution Process
  Process {
    id: agyProc
    running: false
    command: []
    stdout: StdioCollector {
      waitForEnd: true
      onStreamFinished: {
        root.isThinking = false
        if (text && text.trim().length > 0) {
          root.miloChatOutput = text.trim()
        }
      }
    }
  }

  function askMilo(query) {
    if (!query || !query.trim() || root.isThinking) return
    var q = query.trim()
    root.isThinking = true
    root.miloChatOutput = "Thinking..."
    agyProc.command = ["/home/jeffy/.local/bin/milo-query", q]
    agyProc.running = true
  }

  // Test Harness Process
  Process {
    id: testHarnessProc
    running: false
    command: ["/home/jeffy/.local/bin/milo-harness", "all"]
    stdout: StdioCollector {
      waitForEnd: true
      onStreamFinished: {
        if (text && text.trim().length > 0) {
          var lines = text.trim().split("\n")
          var summary = []
          for (var i = 0; i < lines.length; i++) {
            var l = lines[i].replace(/\033\[[0-9;]*m/g, "").trim()
            if (l.indexOf("✔") !== -1 || l.indexOf("✖") !== -1 || l.indexOf("Results:") !== -1 || l.indexOf("ALL MILO") !== -1) {
              summary.push(l)
            }
          }
          root.miloChatOutput = summary.length > 0 ? summary.join("\n") : text.trim()
        }
      }
    }
  }

  // Quick Action Process
  Process {
    id: quickCmdProc
    property var cmdList: []
    command: cmdList
  }

  function runQuickAction(action) {
    if (action === "vault") {
      quickCmdProc.command = ["bash", "-c", "hyprctl dispatch 'hl.dsp.exec_cmd(\"obsidian\")' 2>/dev/null || gtk-launch obsidian || obsidian &"]
      quickCmdProc.running = true
      root.miloChatOutput = "📔 Opening Milo's Obsidian Vault..."
    } else if (action === "test") {
      root.miloChatOutput = "🧪 Running Milo Evaluation Harness..."
      testHarnessProc.running = true
    } else if (action === "nightlight") {
      quickCmdProc.command = ["omarchy", "toggle", "nightlight"]
      quickCmdProc.running = true
      root.miloChatOutput = "🌙 Toggled Night Light."
    } else if (action === "screenshot") {
      quickCmdProc.command = ["omarchy", "capture", "screenshot"]
      quickCmdProc.running = true
      root.miloChatOutput = "📸 Screenshot capture tool launched."
    } else if (action === "music") {
      quickCmdProc.command = ["bash", "-c", "command -v playerctl >/dev/null 2>&1 && playerctl play-pause || true"]
      quickCmdProc.running = true
      mediaProc.running = true
    } else if (action === "clear") {
      root.miloChatOutput = "🧹 Chat cleared! Standing by on desktop."
    }
  }

  IpcHandler {
    target: "milo"

    function say(text: string): string {
      root.miloChatOutput = text
      return "ok"
    }

    function notify(text: string): string {
      root.miloChatOutput = text
      return "ok"
    }

    function ask(query: string): string {
      root.askMilo(query)
      return "Query sent to Milo"
    }

    function test(): string {
      root.runQuickAction("test")
      return "running harness"
    }

    function vault(): string {
      root.runQuickAction("vault")
      return "opened"
    }

    function toggle(): string {
      root.hudVisible = !root.hudVisible
      return root.hudVisible ? "shown" : "hidden"
    }

    function show(): string {
      root.hudVisible = true
      return "shown"
    }

    function hide(): string {
      root.hudVisible = false
      return "hidden"
    }

    function clear(): string {
      root.runQuickAction("clear")
      return "cleared"
    }

    function nightlight(): string {
      root.runQuickAction("nightlight")
      return "toggled"
    }

    function screenshot(): string {
      root.runQuickAction("screenshot")
      return "launched"
    }

    function status(): string {
      return JSON.stringify({
        visible: root.hudVisible,
        isThinking: root.isThinking,
        output: root.miloChatOutput,
        mem: root.memText,
        media: root.mediaTitle + " - " + root.mediaArtist
      })
    }
  }

  // 4. Wayland Desktop Wallpaper Layer Window
  Variants {
    model: Quickshell.screens

    PanelWindow {
      id: hudPanel
      required property var modelData
      screen: modelData
      visible: root.hudVisible

      anchors {
        top: true
        bottom: true
        right: true
      }
      margins {
        top: 40
        bottom: 25
        right: 30
      }

      implicitWidth: 420
      color: "transparent"

      WlrLayershell.namespace: "milo-desktop-hud"
      WlrLayershell.layer: WlrLayer.Bottom
      WlrLayershell.keyboardFocus: WlrKeyboardFocus.OnDemand
      exclusionMode: ExclusionMode.Ignore

      // Aesthetic Glass Card
      Rectangle {
        id: card
        anchors.fill: parent
        radius: 22
        color: Qt.rgba(0.06, 0.07, 0.12, 0.90)
        border.color: Qt.rgba(0.0, 0.85, 1.0, 0.30)
        border.width: 1

        // Top Cyan Glow Line
        Rectangle {
          anchors {
            top: parent.top
            left: parent.left
            right: parent.right
          }
          height: 2
          gradient: Gradient {
            orientation: Gradient.Horizontal
            GradientStop { position: 0.0; color: "transparent" }
            GradientStop { position: 0.5; color: "#00e5ff" }
            GradientStop { position: 1.0; color: "transparent" }
          }
        }

        // Inner Padding Layout
        ColumnLayout {
          anchors {
            fill: parent
            margins: 16
          }
          spacing: 12

          // --- HEADER: Milo Orb & Online Badge ---
          RowLayout {
            Layout.fillWidth: true
            spacing: 12

            Item {
              width: 38
              height: 38

              Rectangle {
                anchors.centerIn: parent
                width: 38; height: 38
                radius: 19
                color: "#121424"
                border.color: Qt.rgba(0, 0.9, 1, 0.5)
                border.width: 1

                SequentialAnimation on scale {
                  loops: Animation.Infinite
                  PropertyAnimation { to: 1.08; duration: 2200; easing.type: Easing.InOutQuad }
                  PropertyAnimation { to: 1.0; duration: 2200; easing.type: Easing.InOutQuad }
                }

                Text {
                  anchors.centerIn: parent
                  text: "✦"
                  color: "#00f0ff"
                  font.pixelSize: 16
                }
              }
            }

            ColumnLayout {
              spacing: 1
              Layout.fillWidth: true

              RowLayout {
                spacing: 6
                Text {
                  text: "MILO CORE"
                  color: "#e2e8f0"
                  font.bold: true
                  font.pixelSize: 14
                  font.letterSpacing: 1
                }
                Rectangle {
                  radius: 8
                  color: Qt.rgba(0, 0.9, 1, 0.12)
                  border.color: Qt.rgba(0, 0.9, 1, 0.25)
                  implicitWidth: badgeText.implicitWidth + 8
                  implicitHeight: 16
                  Text {
                    id: badgeText
                    anchors.centerIn: parent
                    text: "LIVE HUD"
                    color: "#00e5ff"
                    font.pixelSize: 8
                    font.bold: true
                  }
                }
              }
              Text {
                text: "Antigravity AI Connected"
                color: "#64748b"
                font.pixelSize: 10
                font.family: "monospace"
              }
            }

            // Status Pill
            Rectangle {
              radius: 10
              color: Qt.rgba(0.05, 0.3, 0.15, 0.4)
              border.color: Qt.rgba(0.2, 0.8, 0.4, 0.4)
              implicitWidth: statusText.implicitWidth + 14
              implicitHeight: 20

              RowLayout {
                anchors.centerIn: parent
                spacing: 5
                Rectangle {
                  width: 6; height: 6
                  radius: 3
                  color: "#10b981"
                }
                Text {
                  id: statusText
                  text: "OPTIMAL"
                  color: "#34d399"
                  font.pixelSize: 9
                  font.bold: true
                }
              }
            }
          }

          // --- CLOCK & GREETING ---
          ColumnLayout {
            Layout.fillWidth: true
            Layout.alignment: Qt.AlignHCenter
            spacing: 2

            Text {
              Layout.alignment: Qt.AlignHCenter
              text: root.clockDate.toLocaleTimeString(Qt.locale(), "hh:mm:ss AP")
              color: "#f8fafc"
              font.pixelSize: 26
              font.bold: true
              font.family: "monospace"
            }
            Text {
              Layout.alignment: Qt.AlignHCenter
              text: root.clockDate.toLocaleDateString(Qt.locale(), "dddd, MMMM d").toUpperCase()
              color: "#38bdf8"
              font.pixelSize: 10
              font.letterSpacing: 1.5
            }
            Rectangle {
              Layout.alignment: Qt.AlignHCenter
              Layout.topMargin: 4
              radius: 10
              color: Qt.rgba(1, 1, 1, 0.05)
              border.color: Qt.rgba(1, 1, 1, 0.08)
              implicitWidth: greetingLabel.implicitWidth + 16
              implicitHeight: 22

              Text {
                id: greetingLabel
                anchors.centerIn: parent
                text: root.greetingText
                color: "#cbd5e1"
                font.pixelSize: 11
                font.bold: true
              }
            }
          }

          // --- SYSTEM TELEMETRY (RAM & POWER) ---
          Rectangle {
            Layout.fillWidth: true
            radius: 14
            color: Qt.rgba(0.08, 0.09, 0.16, 0.9)
            border.color: Qt.rgba(1, 1, 1, 0.06)
            implicitHeight: 64
            Layout.topMargin: 4

            ColumnLayout {
              anchors.fill: parent
              anchors.margins: 10
              spacing: 6

              RowLayout {
                Layout.fillWidth: true
                Text {
                  text: "🧠 Memory"
                  color: "#94a3b8"
                  font.pixelSize: 10
                  font.family: "monospace"
                }
                Item { Layout.fillWidth: true }
                Text {
                  text: root.memText
                  color: "#e2e8f0"
                  font.pixelSize: 10
                  font.bold: true
                  font.family: "monospace"
                }
              }

              // Progress Bar
              Rectangle {
                Layout.fillWidth: true
                height: 5
                radius: 3
                color: "#1e293b"

                Rectangle {
                  height: parent.height
                  width: Math.min(parent.width * root.memPercent, parent.width)
                  radius: 3
                  gradient: Gradient {
                    orientation: Gradient.Horizontal
                    GradientStop { position: 0.0; color: "#00e5ff" }
                    GradientStop { position: 1.0; color: "#6366f1" }
                  }
                }
              }
            }
          }

          // --- MEDIA PLAYER CAPSULE ---
          Rectangle {
            Layout.fillWidth: true
            radius: 14
            color: Qt.rgba(0.08, 0.09, 0.16, 0.9)
            border.color: Qt.rgba(1, 1, 1, 0.06)
            implicitHeight: 46

            RowLayout {
              anchors.fill: parent
              anchors.margins: 8
              spacing: 10

              Rectangle {
                width: 28; height: 28
                radius: 8
                color: Qt.rgba(0, 0.9, 1, 0.1)
                border.color: Qt.rgba(0, 0.9, 1, 0.2)
                Text {
                  anchors.centerIn: parent
                  text: "🎵"
                  font.pixelSize: 12
                }
              }

              ColumnLayout {
                Layout.fillWidth: true
                spacing: 1

                Text {
                  Layout.fillWidth: true
                  text: root.mediaTitle
                  color: "#e2e8f0"
                  font.pixelSize: 11
                  font.bold: true
                  elide: Text.ElideRight
                }
                Text {
                  Layout.fillWidth: true
                  text: root.mediaArtist
                  color: "#64748b"
                  font.pixelSize: 9
                  elide: Text.ElideRight
                }
              }

              // Play/Pause button
              Rectangle {
                width: 26; height: 26
                radius: 6
                color: playMouse.containsMouse ? Qt.rgba(1, 1, 1, 0.15) : Qt.rgba(1, 1, 1, 0.08)
                Text {
                  anchors.centerIn: parent
                  text: root.isPlaying ? "⏸" : "▶"
                  color: "#e2e8f0"
                  font.pixelSize: 11
                }
                MouseArea {
                  id: playMouse
                  anchors.fill: parent
                  hoverEnabled: true
                  onClicked: root.runQuickAction("music")
                }
              }
            }
          }

          // --- CHAT STREAM DISPLAY ---
          Rectangle {
            Layout.fillWidth: true
            Layout.fillHeight: true
            radius: 14
            color: Qt.rgba(0.07, 0.08, 0.14, 0.9)
            border.color: Qt.rgba(1, 1, 1, 0.06)
            clip: true

            Flickable {
              id: flick
              anchors.fill: parent
              anchors.margins: 12
              contentWidth: width
              contentHeight: chatLayout.implicitHeight
              clip: true
              boundsBehavior: Flickable.StopAtBounds

              ColumnLayout {
                id: chatLayout
                width: flick.width
                spacing: 8

                RowLayout {
                  Layout.fillWidth: true
                  visible: root.isThinking
                  spacing: 6
                  Rectangle {
                    width: 6; height: 6; radius: 3; color: "#00e5ff"
                    SequentialAnimation on opacity {
                      loops: Animation.Infinite
                      PropertyAnimation { to: 0.2; duration: 600 }
                      PropertyAnimation { to: 1.0; duration: 600 }
                    }
                  }
                  Text {
                    text: "Milo is generating response..."
                    color: "#00e5ff"
                    font.pixelSize: 10
                    font.italic: true
                  }
                }

                TextEdit {
                  id: chatText
                  Layout.fillWidth: true
                  width: chatLayout.width
                  text: root.miloChatOutput
                  color: "#cbd5e1"
                  font.pixelSize: 11
                  font.family: "sans-serif"
                  wrapMode: TextEdit.Wrap
                  readOnly: true
                  selectByMouse: true
                  selectionColor: "#00e5ff"
                  selectedTextColor: "#000000"
                }
              }
            }
          }

          // --- QUICK ACTION PILLS ---
          RowLayout {
            Layout.fillWidth: true
            spacing: 6

            Repeater {
              model: [
                { label: "📔 Vault", action: "vault" },
                { label: "🧪 Test", action: "test" },
                { label: "🌙 Night", action: "nightlight" },
                { label: "📸 Snip", action: "screenshot" },
                { label: "🧹 Clear", action: "clear" }
              ]

              Rectangle {
                radius: 12
                color: btnMouse.containsMouse ? Qt.rgba(0, 0.9, 1, 0.15) : Qt.rgba(1, 1, 1, 0.05)
                border.color: btnMouse.containsMouse ? Qt.rgba(0, 0.9, 1, 0.3) : Qt.rgba(1, 1, 1, 0.08)
                implicitWidth: btnText.implicitWidth + 16
                implicitHeight: 22

                Text {
                  id: btnText
                  anchors.centerIn: parent
                  text: modelData.label
                  color: btnMouse.containsMouse ? "#00e5ff" : "#94a3b8"
                  font.pixelSize: 10
                  font.bold: true
                }

                MouseArea {
                  id: btnMouse
                  anchors.fill: parent
                  hoverEnabled: true
                  onClicked: root.runQuickAction(modelData.action)
                }
              }
            }
          }

          // --- DESKTOP PROMPT INPUT BAR ---
          Rectangle {
            Layout.fillWidth: true
            height: 38
            radius: 12
            color: "#141728"
            border.color: promptEdit.activeFocus ? "#00e5ff" : Qt.rgba(1, 1, 1, 0.12)
            border.width: 1

            RowLayout {
              anchors.fill: parent
              anchors.leftMargin: 10
              anchors.rightMargin: 6
              spacing: 6

              TextInput {
                id: promptEdit
                Layout.fillWidth: true
                color: "#f8fafc"
                font.pixelSize: 11
                selectByMouse: true
                clip: true

                Text {
                  anchors.fill: parent
                  text: "Ask Milo on desktop..."
                  color: "#64748b"
                  font.pixelSize: 11
                  visible: !promptEdit.text && !promptEdit.activeFocus
                }

                onAccepted: {
                  if (text.trim().length > 0) {
                    root.askMilo(text)
                    text = ""
                  }
                }
              }

              Rectangle {
                width: 32; height: 26
                radius: 8
                color: (!root.isThinking && promptEdit.text.trim().length > 0)
                  ? "#0284c7"
                  : Qt.rgba(1, 1, 1, 0.05)

                Text {
                  anchors.centerIn: parent
                  text: "➤"
                  color: "#ffffff"
                  font.pixelSize: 11
                }

                MouseArea {
                  anchors.fill: parent
                  onClicked: {
                    if (promptEdit.text.trim().length > 0) {
                      root.askMilo(promptEdit.text)
                      promptEdit.text = ""
                    }
                  }
                }
              }
            }
          }

          // --- FOOTER NOTE ---
          RowLayout {
            Layout.fillWidth: true
            Text {
              text: "Super+A summons Spotlight modal"
              color: "#475569"
              font.pixelSize: 9
              font.family: "monospace"
            }
            Item { Layout.fillWidth: true }
            Text {
              text: "Omarchy Shell"
              color: "#475569"
              font.pixelSize: 9
              font.family: "monospace"
            }
          }

        }
      }
    }
  }
}
