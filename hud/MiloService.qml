import Quickshell
import Quickshell.Io
import Quickshell.Wayland
import Quickshell.Hyprland
import QtQuick
import QtQuick.Layouts
import QtQuick.Controls

Item {
  id: root

  readonly property string homeDir: Quickshell.env("HOME") || ("/home/" + (Quickshell.env("USER") || "user"))
  property bool hudVisible: true
  property string memText: "5.1 / 15.5 GB (33%)"
  property real memPercent: 0.33
  property string diskFreeText: "215G"
  property real diskPercent: 0.35
  property string cpuText: "CORE 8%"
  property string tempText: "TEMP 52°C"
  property string cpuGhzText: "3.4 GHz"
  property string mediaTitle: "Back in Black"
  property string mediaArtist: "Milo Audio · Cybernetic Vault"
  property bool isPlaying: false
  property string miloChatOutput: ""
  property string lastCameraSnapshot: ""
  property bool isThinking: false
  property var clockDate: new Date()
  property string currentMode: "✦ TACTICAL AI"
  property string promptPlaceholder: "Ask Milo, /look, dictate 🎙️, or type /dispatch <goal>, /code <goal>, /test"

  signal triggerShockwave()

  Process {
    id: soundProc
    running: false
    command: []
  }

  function playSound(name) {
    try {
      if (soundProc.running) soundProc.running = false
      soundProc.command = [root.homeDir + "/.local/bin/milo-sound", name || "chirp"]
      soundProc.running = true
    } catch(e) {}
  }

  // Hybrid Intelligence Online/Offline State
  property string intelligenceMode: "auto"
  property bool isNetworkOnline: false
  property string intelligenceLabel: "🔄 AUTO (⚡ Cortex Offline)"
  property string intelligenceColor: "#ffaa00"

  // Option B: Tactical Quick Settings / Control Center State
  property bool controlCenterOpen: false
  property int ccVolume: 50
  property bool ccMuted: false
  property int ccBrightness: 50
  property bool ccWifiEnabled: true
  property string ccWifiSSID: "JEFFY"
  property string ccWifiIp: "192.168.1.108"
  property bool ccBtEnabled: true
  property string ccBtDevice: "SPA3800B"
  property bool ccNightlightEnabled: false
  property bool ccBarOff: true
  property bool ccVoiceActive: true
  property bool ccWifiScannerOpen: false
  property bool ccBtScannerOpen: false
  property var ccWifiList: []
  property var ccBtList: []
  property bool ccIsScanningWifi: false
  property bool ccIsScanningBt: false
  property string ccWifiSelectedSSID: ""
  property string ccWifiPasswordInput: ""
  property bool ccWifiShowPasswordInput: false

  // Dynamic Persistent Milo Scratchpad & Calendar
  property bool scratchpadModalOpen: false
  property string scratchpadFilter: "all"  // "all" | "pending" | "completed"
  property string midLeftTab: "tasks"      // "tasks" | "agenda" | "mail" | "whatsapp"
  property bool tasksWrapAll: false
  property bool modalTasksWrapAll: false
  property int expandedDeskTaskIndex: -1
  property int expandedModalTaskIndex: -1
  property var mailData: ({ "unread_count": 0, "emails": [] })
  property var whatsappData: ({ "unread_count": 0, "status": "offline", "phone": "", "pushName": "", "chats": [] })
  property var agendaList: []
  property var worktimeData: ({
    start: "09:00",
    end: "18:00",
    days: ["Mon", "Tue", "Wed", "Thu", "Fri"],
    enabled: true,
    is_worktime: false,
    status: "OFF DUTY",
    status_text: "Off Duty"
  })

  function reloadAgenda() {
    try {
      var raw = agendaFile.text().trim()
      if (raw) {
        var d = JSON.parse(raw)
        if (Array.isArray(d)) root.agendaList = d
      }
      var wtRaw = worktimeFile.text().trim()
      if (wtRaw) {
        var wt = JSON.parse(wtRaw)
        if (wt && typeof wt === 'object') root.worktimeData = wt
      }
    } catch(e) {}
  }

  function addAgendaQuick(text) {
    if (!text || !text.trim()) return
    if (quickCmdProc.running) quickCmdProc.running = false
    quickCmdProc.command = [root.homeDir + "/.local/bin/milo-calendar", "quick", text.trim()]
    quickCmdProc.running = true
  }

  function setWorktime(rangeStr) {
    if (!rangeStr || !rangeStr.trim()) return
    if (quickCmdProc.running) quickCmdProc.running = false
    quickCmdProc.command = [root.homeDir + "/.local/bin/milo-calendar", "worktime", "--set", rangeStr.trim()]
    quickCmdProc.running = true
  }

  function removeAgendaEvent(id) {
    if (quickCmdProc.running) quickCmdProc.running = false
    quickCmdProc.command = [root.homeDir + "/.local/bin/milo-calendar", "rm", id.toString()]
    quickCmdProc.running = true
  }

  function mailSync() {
    if (quickCmdProc.running) quickCmdProc.running = false
    quickCmdProc.command = [root.homeDir + "/.local/bin/milo-mail", "sync"]
    quickCmdProc.running = true
  }

  function mailSummarize() {
    quickCmdProc.command = ["foot", "-a", "milo-floating", "-T", "MILO // Gmail AI Briefing", root.homeDir + "/.local/bin/milo-mail", "summarize"]
    quickCmdProc.running = true
  }

  function mailOpenWeb() {
    if (quickCmdProc.running) quickCmdProc.running = false
    quickCmdProc.command = ["xdg-open", "https://mail.google.com"]
    quickCmdProc.running = true
  }

  function whatsappSync() {
    if (quickCmdProc.running) quickCmdProc.running = false
    quickCmdProc.command = [root.homeDir + "/.local/bin/milo-wa", "sync"]
    quickCmdProc.running = true
  }

  function whatsappSummarize() {
    quickCmdProc.command = ["foot", "-a", "milo-floating", "-T", "MILO // WhatsApp AI Briefing", root.homeDir + "/.local/bin/milo-wa", "summarize"]
    quickCmdProc.running = true
  }

  function whatsappReadChat(target) {
    quickCmdProc.command = ["foot", "-a", "milo-floating", "-T", "MILO // WhatsApp Thread", root.homeDir + "/.local/bin/milo-wa", "read", target.toString()]
    quickCmdProc.running = true
  }

  function whatsappLinkQR() {
    quickCmdProc.command = ["foot", "-a", "milo-floating", "-T", "MILO // WhatsApp QR Link", root.homeDir + "/.local/bin/milo-wa", "qr"]
    quickCmdProc.running = true
  }

  // Milo Cyber Soundtrack Hotkey Actions
  function musicPlayPause() {
    if (quickCmdProc.running) quickCmdProc.running = false
    quickCmdProc.command = [root.homeDir + "/.local/bin/milo-music", "play-pause"]
    quickCmdProc.running = true
    root.triggerShockwave()
    mediaRefreshTimer.restart()
  }

  function musicNext() {
    if (quickCmdProc.running) quickCmdProc.running = false
    quickCmdProc.command = [root.homeDir + "/.local/bin/milo-music", "next"]
    quickCmdProc.running = true
    root.triggerShockwave()
    mediaRefreshTimer.restart()
  }

  function musicPrev() {
    if (quickCmdProc.running) quickCmdProc.running = false
    quickCmdProc.command = [root.homeDir + "/.local/bin/milo-music", "prev"]
    quickCmdProc.running = true
    root.triggerShockwave()
    mediaRefreshTimer.restart()
  }

  function musicPick() {
    quickCmdProc.command = ["foot", "-a", "milo-floating", "-T", "MILO // Track Picker", root.homeDir + "/.local/bin/milo-music", "pick"]
    quickCmdProc.running = true
    root.triggerShockwave()
  }

  function musicTui() {
    quickCmdProc.command = ["foot", "-a", "milo-floating", "-T", "MILO // Cyber Soundtrack", root.homeDir + "/.local/bin/milo-music", "tui"]
    quickCmdProc.running = true
    root.triggerShockwave()
  }

  Timer {
    id: mediaRefreshTimer
    interval: 350
    repeat: false
    running: false
    onTriggered: {
      if (!mediaProc.running) mediaProc.running = true
    }
  }

  // Milo Autonomous Evolution Protocol (MEP-1)
  property bool hasPendingEvolution: false

  function applyEvolution() {
    root.hudVisible = true
    root.isThinking = true
    root.miloChatOutput = "✦ Applying authorized upgrade & running sandboxed verification...\n(10s auto-rollback watchdog armed)"
    chatAutoDismissTimer.stop()
    thinkingWatchdog.restart()
    root.hasPendingEvolution = false
    if (evoProc.running) return;
    evoProc.command = ["/home/jeffy/.local/bin/milo-evolve", "approve"]
    evoProc.running = true
  }

  function deferEvolution() {
    root.miloChatOutput = "✦ Evolution proposal deferred."
    root.hasPendingEvolution = false
    if (quickCmdProc.running) quickCmdProc.running = false
    quickCmdProc.command = ["/home/jeffy/.local/bin/milo-evolve", "defer"]
    quickCmdProc.running = true
    chatAutoDismissTimer.restart()
  }

  property var todosList: [
    { "id": 1, "text": "Compile native milo-files", "done": true },
    { "id": 2, "text": "Deploy Arc Reactor HUD", "done": true },
    { "id": 3, "text": "Verify Hyprland DnD rules", "done": false },
    { "id": 4, "text": "Seed Milo Torrent swarm", "done": false }
  ]

  // Live Satellite Uplink Telemetry
  property string uplinkUptime: "6h 50m"
  property string uplinkNet: "JEFFY · 10.140.102.95"
  property string uplinkThreat: "THREAT MATRIX NOMINAL"
  property string phoneModel: "Vivo V2428"
  property string phoneBattery: "Standby"
  property string phoneStatus: "Tailscale P2P"

  // Milo Game Mode Telemetry & State
  property bool gameModeActive: false
  property string gameVramFree: "3036 MiB"
  property string gameVramUsed: "36 MiB"

  FileView {
    id: gameModeWatcher
    path: "/tmp/milo-gamemode.json"
    watchChanges: true
    printErrors: false
    onFileChanged: reload()
    onLoaded: {
      try {
        var raw = text().trim()
        if (raw) {
          var data = JSON.parse(raw)
          root.gameModeActive = !!data.active
          if (data.vram_free) root.gameVramFree = data.vram_free
          if (data.vram_used) root.gameVramUsed = data.vram_used
        }
      } catch(e) {}
    }
  }

  FileView {
    id: todosFile
    path: "/home/jeffy/.config/omarchy/todos.json"
    watchChanges: true
    atomicWrites: true
    printErrors: false
    onFileChanged: reload()
    onLoaded: {
      try {
        var raw = text().trim()
        if (raw) {
          var data = JSON.parse(raw)
          if (Array.isArray(data)) root.todosList = data
        }
      } catch(e) {}
    }
  }

  FileView {
    id: agendaFile
    path: root.homeDir + "/.local/share/milo/calendar/agenda_today.json"
    watchChanges: true
    printErrors: false
    onFileChanged: reload()
    onLoaded: {
      try {
        var raw = text().trim()
        if (raw) {
          var data = JSON.parse(raw)
          if (Array.isArray(data)) root.agendaList = data
        }
      } catch(e) {}
    }
  }

  FileView {
    id: worktimeFile
    path: root.homeDir + "/.local/share/milo/calendar/worktime.json"
    watchChanges: true
    printErrors: false
    onFileChanged: reload()
    onLoaded: {
      try {
        var raw = text().trim()
        if (raw) {
          var wt = JSON.parse(raw)
          if (wt && typeof wt === 'object') root.worktimeData = wt
        }
      } catch(e) {}
    }
  }

  FileView {
    id: mailFile
    path: root.homeDir + "/.local/share/milo/mail/inbox.json"
    watchChanges: true
    printErrors: false
    onFileChanged: reload()
    onLoaded: {
      try {
        var raw = text().trim()
        if (raw) {
          var md = JSON.parse(raw)
          if (md && typeof md === 'object') root.mailData = md
        }
      } catch(e) {}
    }
  }

  FileView {
    id: whatsappFile
    path: root.homeDir + "/.local/share/milo/whatsapp/inbox.json"
    watchChanges: true
    printErrors: false
    onFileChanged: reload()
    onLoaded: {
      try {
        var raw = text().trim()
        if (raw) {
          var wd = JSON.parse(raw)
          if (wd && typeof wd === 'object') root.whatsappData = wd
        }
      } catch(e) {}
    }
  }

  FileView {
    id: whatsappTriggerWatcher
    path: "/tmp/milo-whatsapp-trigger"
    watchChanges: true
    printErrors: false
    onFileChanged: reload()
    onLoaded: {
      try {
        whatsappFile.reload()
      } catch(e) {}
    }
  }

  // Milo Scratchpad Modal External IPC Trigger
  FileView {
    id: scratchpadTriggerWatcher
    path: "/tmp/milo-scratchpad-trigger"
    watchChanges: true
    printErrors: false
    onFileChanged: reload()
    onLoaded: {
      try {
        var raw = text().trim()
        if (raw) {
          var parts = raw.split(" ")
          var act = parts.length > 1 ? parts[1] : parts[0]
          if (act === "toggle") {
            root.scratchpadModalOpen = !root.scratchpadModalOpen
          } else if (act === "open") {
            root.scratchpadModalOpen = true
          } else if (act === "close") {
            root.scratchpadModalOpen = false
          } else if (act === "open_agenda") {
            root.midLeftTab = "agenda"
            root.scratchpadModalOpen = true
          } else if (act === "toggle_agenda") {
            if (root.scratchpadModalOpen && root.midLeftTab === "agenda") {
              root.scratchpadModalOpen = false
            } else {
              root.midLeftTab = "agenda"
              root.scratchpadModalOpen = true
            }
          } else if (act === "open_tasks") {
            root.midLeftTab = "tasks"
            root.scratchpadModalOpen = true
          } else if (act === "open_mail") {
            root.midLeftTab = "mail"
            root.scratchpadModalOpen = true
          } else if (act === "open_whatsapp" || act === "open_wa") {
            root.midLeftTab = "whatsapp"
            root.scratchpadModalOpen = true
          } else if (act === "update" || act === "update_agenda") {
            // Trigger todos reload from disk
            var rawJson = todosFile.text().trim()
            if (rawJson) {
              var d = JSON.parse(rawJson)
              if (Array.isArray(d)) root.todosList = d
            }
            var rawAgenda = agendaFile.text().trim()
            if (rawAgenda) {
              var a = JSON.parse(rawAgenda)
              if (Array.isArray(a)) root.agendaList = a
            }
            var rawWt = worktimeFile.text().trim()
            if (rawWt) {
              var wtObj = JSON.parse(rawWt)
              if (wtObj && typeof wtObj === 'object') root.worktimeData = wtObj
            }
            var rawMail = mailFile.text().trim()
            if (rawMail) {
              var mObj = JSON.parse(rawMail)
              if (mObj && typeof mObj === 'object') root.mailData = mObj
            }
            var rawWa = whatsappFile.text().trim()
            if (rawWa) {
              var wObj = JSON.parse(rawWa)
              if (wObj && typeof wObj === 'object') root.whatsappData = wObj
            }
          }
        }
      } catch(e) {}
    }
  }

  // Milo Tactical Control Center IPC Trigger
  FileView {
    id: controlCenterTriggerWatcher
    path: "/tmp/milo-control-center-trigger"
    watchChanges: true
    printErrors: false
    onLoaded: {
      try {
        var raw = text().trim()
        if (raw) {
          var parts = raw.split(" ")
          var act = parts.length > 1 ? parts[1] : parts[0]
          if (act === "toggle") {
            root.controlCenterOpen = !root.controlCenterOpen
            if (root.controlCenterOpen) root.refreshControlCenter()
          } else if (act === "open") {
            root.controlCenterOpen = true
            root.refreshControlCenter()
          } else if (act === "open_wifi") {
            root.controlCenterOpen = true
            root.ccWifiScannerOpen = true
            root.startWifiScan()
          } else if (act === "open_bt") {
            root.controlCenterOpen = true
            root.ccBtScannerOpen = true
            root.startBtScan()
          } else if (act === "close") {
            root.controlCenterOpen = false
          } else if (act === "refresh") {
            root.refreshControlCenter()
          }
        }
      } catch(e) {}
    }
  }

  // Periodic and on-demand telemetry process for Control Center
  Process {
    id: ccStatusProc
    command: [root.homeDir + "/.local/bin/milo-control-center", "status"]
    stdout: StdioCollector {
      onStreamFinished: {
        try {
          if (text && text.trim().length > 0) {
            var lines = text.trim().split("\n")
            var jsonStr = ""
            var start = false
            for (var i = 0; i < lines.length; i++) {
              if (lines[i].trim().startsWith("{")) start = true
              if (start) jsonStr += lines[i] + "\n"
            }
            if (jsonStr) {
              var st = JSON.parse(jsonStr)
              if (st) {
                if (typeof st.volume === "number") root.ccVolume = st.volume
                if (typeof st.muted === "boolean") root.ccMuted = st.muted
                if (typeof st.brightness === "number") root.ccBrightness = st.brightness
                if (typeof st.wifi_enabled === "boolean") root.ccWifiEnabled = st.wifi_enabled
                if (st.wifi_ssid) root.ccWifiSSID = st.wifi_ssid
                if (st.wifi_ip) root.ccWifiIp = st.wifi_ip
                if (typeof st.bt_enabled === "boolean") root.ccBtEnabled = st.bt_enabled
                if (st.bt_device) root.ccBtDevice = st.bt_device
                if (typeof st.nightlight_enabled === "boolean") root.ccNightlightEnabled = st.nightlight_enabled
                if (typeof st.bar_off === "boolean") root.ccBarOff = st.bar_off
              }
            }
          }
        } catch(e) {}
      }
    }
  }

  Timer {
    id: ccAutoRefreshTimer
    interval: 3000
    repeat: true
    running: root.controlCenterOpen
    onTriggered: root.refreshControlCenter()
  }

  function refreshControlCenter() {
    if (!ccStatusProc.running) ccStatusProc.running = true
  }

  function setCcVolume(val) {
    root.ccVolume = Math.max(0, Math.min(100, Math.round(val)))
    quickCmdProc.command = [root.homeDir + "/.local/bin/milo-control-center", "set-vol", "" + root.ccVolume]
    quickCmdProc.running = true
    root.playSound("tick")
  }

  function toggleCcMute() {
    root.ccMuted = !root.ccMuted
    quickCmdProc.command = [root.homeDir + "/.local/bin/milo-control-center", "toggle-mute"]
    quickCmdProc.running = true
    root.playSound("chirp")
  }

  function setCcBrightness(val) {
    root.ccBrightness = Math.max(10, Math.min(100, Math.round(val)))
    quickCmdProc.command = [root.homeDir + "/.local/bin/milo-control-center", "set-brightness", "" + root.ccBrightness]
    quickCmdProc.running = true
    root.playSound("tick")
  }

  function toggleCcWifi() {
    root.ccWifiEnabled = !root.ccWifiEnabled
    quickCmdProc.command = [root.homeDir + "/.local/bin/milo-control-center", "toggle-wifi"]
    quickCmdProc.running = true
    root.playSound("switch")
  }

  function toggleCcBluetooth() {
    root.ccBtEnabled = !root.ccBtEnabled
    quickCmdProc.command = [root.homeDir + "/.local/bin/milo-control-center", "toggle-bt"]
    quickCmdProc.running = true
    root.playSound("switch")
  }

  function toggleCcNightlight() {
    root.ccNightlightEnabled = !root.ccNightlightEnabled
    quickCmdProc.command = [root.homeDir + "/.local/bin/milo-control-center", "toggle-nightlight"]
    quickCmdProc.running = true
    root.playSound("switch")
  }

  function toggleCcTopBar() {
    root.ccBarOff = !root.ccBarOff
    quickCmdProc.command = [root.homeDir + "/.local/bin/milo-control-center", "toggle-bar"]
    quickCmdProc.running = true
    root.playSound("switch")
  }

  function openCcCommandCenter() {
    root.controlCenterOpen = false
    root.hudVisible = true
    quickCmdProc.command = [root.homeDir + "/.local/bin/milo-hud"]
    quickCmdProc.running = true
    root.playSound("activate")
  }

  Process {
    id: ccWifiScanProc
    command: [root.homeDir + "/.local/bin/milo-control-center", "wifi-scan"]
    stdout: StdioCollector {
      onStreamFinished: {
        root.ccIsScanningWifi = false
        try {
          if (text && text.trim().length > 0) {
            var lines = text.trim().split("\n")
            var jsonStr = ""
            var start = false
            for (var i = 0; i < lines.length; i++) {
              if (lines[i].trim().startsWith("[")) start = true
              if (start) jsonStr += lines[i] + "\n"
            }
            if (jsonStr) {
              var arr = JSON.parse(jsonStr)
              if (Array.isArray(arr)) root.ccWifiList = arr
            }
          }
        } catch(e) {}
      }
    }
  }

  function startWifiScan() {
    root.ccIsScanningWifi = true
    if (!ccWifiScanProc.running) ccWifiScanProc.running = true
    root.playSound("chirp")
  }

  function connectToWifi(ssid, pwd) {
    var cmd = [root.homeDir + "/.local/bin/milo-control-center", "wifi-connect", ssid]
    if (pwd) cmd.push(pwd)
    quickCmdProc.command = cmd
    quickCmdProc.running = true
    root.playSound("connect")
    root.ccWifiShowPasswordInput = false
    root.ccWifiPasswordInput = ""
    wifiRefreshTimer.restart()
  }

  Timer {
    id: wifiRefreshTimer
    interval: 2000
    repeat: false
    onTriggered: {
      root.refreshControlCenter()
      root.startWifiScan()
    }
  }

  Process {
    id: ccBtScanProc
    command: [root.homeDir + "/.local/bin/milo-control-center", "bt-scan"]
    stdout: StdioCollector {
      onStreamFinished: {
        root.ccIsScanningBt = false
        try {
          if (text && text.trim().length > 0) {
            var lines = text.trim().split("\n")
            var jsonStr = ""
            var start = false
            for (var i = 0; i < lines.length; i++) {
              if (lines[i].trim().startsWith("[")) start = true
              if (start) jsonStr += lines[i] + "\n"
            }
            if (jsonStr) {
              var arr = JSON.parse(jsonStr)
              if (Array.isArray(arr)) root.ccBtList = arr
            }
          }
        } catch(e) {}
      }
    }
  }

  function startBtScan() {
    root.ccIsScanningBt = true
    if (!ccBtScanProc.running) ccBtScanProc.running = true
    root.playSound("chirp")
  }

  function connectToBt(mac) {
    quickCmdProc.command = [root.homeDir + "/.local/bin/milo-control-center", "bt-connect", mac]
    quickCmdProc.running = true
    root.playSound("connect")
    btRefreshTimer.restart()
  }

  function disconnectFromBt(mac) {
    quickCmdProc.command = [root.homeDir + "/.local/bin/milo-control-center", "bt-disconnect", mac]
    quickCmdProc.running = true
    root.playSound("switch")
    btRefreshTimer.restart()
  }

  Timer {
    id: btRefreshTimer
    interval: 2000
    repeat: false
    onTriggered: {
      root.refreshControlCenter()
      root.startBtScan()
    }
  }

  // Voice Dictation watcher (auto-queries when Phonon-2 finishes)
  FileView {
    id: voiceDictationWatcher
    path: "/tmp/milo-dictation-last.txt"
    watchChanges: true
    printErrors: false
    onLoaded: {
      try {
        var speechText = text().trim()
        if (speechText && speechText.length > 0) {
          root.askMilo(speechText)
        }
      } catch(e) {}
    }
  }

  // Multi-Agent Task State Watcher (/tmp/milo-task.json)
  property string activeAgent: "milo"
  property string taskStage: "IDLE"
  property string taskGoal: ""
  property string taskDetails: ""
  property int taskElapsedSec: 0

  readonly property color activeAgentColor: {
    if (root.activeAgent === "claude") return "#ffaa00";  // Orange Forge
    if (root.activeAgent === "aider") return "#00ff66";   // Matrix Green QA
    if (root.activeAgent === "hermes") return "#00e5ff";  // Electric Cyan Ops
    if (root.taskStage !== "IDLE" && root.taskStage !== "DONE") return "#ff0838"; // Milo Crimson
    return "#ff0838";
  }

  function formatElapsed(sec) {
    var m = Math.floor(sec / 60)
    var s = sec % 60
    return "T+" + (m < 10 ? "0" + m : m) + ":" + (s < 10 ? "0" + s : s)
  }

  Timer {
    id: taskElapsedTimer
    interval: 1000
    repeat: true
    running: root.taskStage !== "IDLE" && root.taskStage !== "DONE"
    onRunningChanged: {
      if (running) root.taskElapsedSec = 0
    }
    onTriggered: root.taskElapsedSec += 1
  }

  FileView {
    id: activeTaskWatcher
    path: "/tmp/milo-task.json"
    watchChanges: true
    printErrors: false
    onFileChanged: reload()
    onLoaded: {
      try {
        var raw = text().trim()
        if (raw) {
          var data = JSON.parse(raw)
          root.activeAgent = data.active_agent || "milo"
          root.taskStage = data.stage || "IDLE"
          root.taskGoal = data.goal || ""
          root.taskDetails = data.details || ""
        }
      } catch(e) {}
    }
  }

  function countDoneTodos() {
    var c = 0
    for (var i = 0; i < root.todosList.length; i++) {
      if (root.todosList[i].done) c++
    }
    return c
  }

  function saveTodos() {
    todosFile.setText(JSON.stringify(root.todosList, null, 2) + "\n")
  }

  function addTodo(taskText) {
    var t = taskText.trim()
    if (!t) return
    var list = []
    for (var i = 0; i < root.todosList.length; i++) {
      list.push(root.todosList[i])
    }
    var d = new Date()
    var hours = d.getHours()
    var minutes = d.getMinutes()
    var ampm = hours >= 12 ? 'PM' : 'AM'
    hours = hours % 12
    hours = hours ? hours : 12
    var strTime = (hours < 10 ? '0' + hours : hours) + ':' + (minutes < 10 ? '0' + minutes : minutes) + ' ' + ampm
    list.push({ id: Date.now(), text: t, done: false, created_at: strTime })
    root.todosList = list
    root.saveTodos()
  }

  function toggleTodo(index) {
    var list = []
    for (var i = 0; i < root.todosList.length; i++) {
      var item = { id: root.todosList[i].id, text: root.todosList[i].text, done: root.todosList[i].done, created_at: root.todosList[i].created_at || "" }
      if (i === index) item.done = !item.done
      list.push(item)
    }
    root.todosList = list
    root.saveTodos()
  }

  function removeTodo(index) {
    var list = []
    for (var i = 0; i < root.todosList.length; i++) {
      if (i !== index) list.push(root.todosList[i])
    }
    root.todosList = list
    root.saveTodos()
  }

  // 1. Clock timer
  Timer {
    interval: 1000
    running: true
    repeat: true
    onTriggered: {
      root.clockDate = new Date()
    }
  }

  // 2. High-speed Hardware Telemetry (Native C, 5ms execution, 0% CPU)
  Timer {
    interval: 3500
    running: true
    repeat: true
    triggeredOnStart: true
    onTriggered: {
      if (!hardwareTelemProc.running) hardwareTelemProc.running = true
      if (!mediaProc.running) mediaProc.running = true
    }
  }

  // 3. Network & Satellite Uplink Polling (Low-frequency 60s interval)
  Timer {
    interval: 60000
    running: true
    repeat: true
    triggeredOnStart: true
    onTriggered: {
      if (!uplinkProc.running) uplinkProc.running = true
      if (!intelStatusProc.running) intelStatusProc.running = true
    }
  }

  Process {
    id: intelStatusProc
    command: ["/home/jeffy/.local/share/milo/venv/bin/python3", "/home/jeffy/.local/share/milo/cortex/intelligence_router.py", "status"]
    stdout: StdioCollector {
      onStreamFinished: {
        try {
          var data = JSON.parse(text.trim())
          root.intelligenceMode = data.mode
          root.isNetworkOnline = data.is_online
          root.intelligenceLabel = data.label
          root.intelligenceColor = data.color
        } catch(e) {}
      }
    }
  }

  function setIntelligenceMode(modeId) {
    quickCmdProc.command = ["/home/jeffy/.local/share/milo/venv/bin/python3", "/home/jeffy/.local/share/milo/cortex/intelligence_router.py", "set", modeId]
    quickCmdProc.running = true
    root.intelligenceMode = modeId
    if (modeId === "online") {
      root.intelligenceLabel = "🌐 ONLINE (Gemini Cloud)"
      root.intelligenceColor = root.isNetworkOnline ? "#00ffcc" : "#ff0838"
    } else if (modeId === "offline") {
      root.intelligenceLabel = "⚡ OFFLINE (Cortex 0.5B)"
      root.intelligenceColor = "#ffaa00"
    } else {
      root.intelligenceLabel = root.isNetworkOnline ? "🔄 AUTO (🌐 Gemini Cloud)" : "🔄 AUTO (⚡ Cortex Offline)"
      root.intelligenceColor = root.isNetworkOnline ? "#00ffcc" : "#ffaa00"
    }
    if (!intelStatusProc.running) intelStatusProc.running = true
  }

  function toggleIntelligenceMode() {
    quickCmdProc.command = ["/home/jeffy/.local/share/milo/venv/bin/python3", "/home/jeffy/.local/share/milo/cortex/intelligence_router.py", "toggle"]
    quickCmdProc.running = true
    if (root.intelligenceMode === "auto") root.setIntelligenceMode("online")
    else if (root.intelligenceMode === "online") root.setIntelligenceMode("offline")
    else root.setIntelligenceMode("auto")
  }

  Process {
    id: uplinkProc
    command: ["/home/jeffy/.local/bin/milo-uplink"]
    stdout: StdioCollector {
      onStreamFinished: {
        var parts = text.trim().split(":::")
        if (parts.length >= 3) {
          if (parts[0]) root.uplinkUptime = parts[0]
          if (parts[1]) root.uplinkNet = parts[1]
          if (parts[2]) root.uplinkThreat = parts[2]
        }
        if (parts.length >= 6) {
          if (parts[3]) root.phoneModel = parts[3]
          if (parts[4]) root.phoneBattery = parts[4]
          if (parts[5]) root.phoneStatus = parts[5]
        }
      }
    }
  }

  // Unified Native Hardware Telemetry Process (replaces 3 bash subshells and top -bn1)
  Process {
    id: hardwareTelemProc
    command: ["/home/jeffy/.local/bin/milo-telemetry"]
    stdout: StdioCollector {
      onStreamFinished: {
        var parts = text.trim().split(":::")
        if (parts.length >= 8) {
          var usedGb = parts[0]
          var totalGb = parts[1]
          var memPct = parseInt(parts[2]) || 0
          root.memText = usedGb + " / " + totalGb + " (" + memPct + "%)"
          root.memPercent = Math.max(0.05, Math.min(1.0, memPct / 100.0))

          root.diskFreeText = parts[3]
          var diskPct = parseInt(parts[4]) || 35
          root.diskPercent = Math.max(0.05, Math.min(1.0, diskPct / 100.0))

          root.cpuText = "CORE " + parts[5] + "%"
          root.tempText = "TEMP " + parts[6] + "°C"
          root.cpuGhzText = parts[7]
        }
      }
    }
  }

  Process {
    id: mediaProc
    command: [root.homeDir + "/.local/bin/milo-music", "status"]
    stdout: StdioCollector {
      onStreamFinished: {
        var out = text.trim()
        if (out.indexOf(":::") !== -1) {
          var p = out.split(":::")
          root.mediaTitle = p[0] || "Milo Cyber Soundtrack"
          root.mediaArtist = p[1] || "Milo Audio · Ready (736 Tracks)"
          root.isPlaying = (p[2] === "Playing")
        } else {
          root.mediaTitle = "Milo Cyber Soundtrack"
          root.mediaArtist = "Milo Audio · Ready"
          root.isPlaying = false
        }
      }
    }
  }

  // 3. Antigravity / Milo Query Process
  Process {
    id: agyProc
    running: false
    command: []
    stdout: StdioCollector {
      onStreamFinished: {
        root.isThinking = false
        var out = text ? text.trim() : ""
        if (out.length > 0) {
          if (agyProc.command && agyProc.command.length > 0 && String(agyProc.command[0]).indexOf("milo-look") !== -1) {
            root.lastCameraSnapshot = "/home/jeffy/.local/state/milo/eyes/current_camera_capture.jpg?t=" + Date.now()
          } else {
            root.lastCameraSnapshot = ""
          }
          root.miloChatOutput = out
          root.playSound("chime")
          chatAutoDismissTimer.restart()
        }
      }
    }
    onExited: function(exitCode, exitStatus) {
      if (exitCode !== 0) {
        root.isThinking = false
        root.miloChatOutput = "✦ Query exited with code " + exitCode
        root.playSound("alert")
        chatAutoDismissTimer.restart()
      }
    }
  }

  Timer {
    id: thinkingWatchdog
    interval: 60000
    repeat: false
    running: root.isThinking
    onTriggered: {
      if (root.isThinking) {
        root.isThinking = false
        if (agyProc.running) agyProc.running = false
        if (root.miloChatOutput === "✦ Neural cortex thinking..." || !root.miloChatOutput) {
          root.miloChatOutput = "✦ Neural cortex timed out. Please try again."
          chatAutoDismissTimer.restart()
        }
      }
    }
  }

  Timer {
    id: chatAutoDismissTimer
    interval: 25000
    repeat: false
    running: false
    onTriggered: {
      if (!root.isThinking && !root.hasPendingEvolution) {
        root.miloChatOutput = ""
        root.lastCameraSnapshot = ""
      }
    }
  }

  function askMilo(query) {
    if (!query || !query.trim()) return
    var q = query.trim()
    root.hudVisible = true
    root.isThinking = true
    root.miloChatOutput = "✦ Neural cortex thinking..."
    chatAutoDismissTimer.stop()
    thinkingWatchdog.restart()
    if (agyProc.running) {
      agyProc.running = false
    }
    agyProc.command = ["/usr/local/bin/milo-query", q]
    agyProc.running = true
  }

  function executeDesktopCommand(cmdText) {
    var raw = String(cmdText || "").trim()
    if (!raw) return
    root.triggerShockwave()
    root.playSound("chirp")

    var lower = raw.toLowerCase()

    // 0.0 Help & Command Matrix Intent
    if (lower === "help" || lower === "/help" || lower === "?" || lower === "cheatsheet" || lower === "shortcuts" || lower === "commands") {
      root.hudVisible = true
      root.isThinking = false
      root.playSound("chime")
      root.miloChatOutput = "✦ **MILO OS // TACTICAL COMMAND & KEYBINDING MATRIX**\n\n" +
        "⚡ **Essential Hotkeys:**\n" +
        "  • `SUPER + SHIFT + O` : Smart OCR (Snip -> Clipboard -> Action Chips)\n" +
        "  • `SUPER + ALT + O`   : OCR & Direct Ask (Snip -> Send directly to Milo)\n" +
        "  • `SUPER + V`         : High-Speed Voice Dictation (Phonon ASR)\n" +
        "  • `SUPER + I`         : Milo Eyes Optical Vision HUD\n" +
        "  • `SUPER + ESC`       : Milotop System & Process Monitor\n" +
        "  • `ESC` (on HUD)      : Instant Card & Overlay Dismissal\n\n" +
        "✦ **Direct Commands & Voice Actions:**\n" +
        "  • `doctor`            : 1-second system health diagnostic & auto-heal\n" +
        "  • `audit`             : Full codebase & daemon forensic audit\n" +
        "  • `game on / off`     : Toggle Zero-Click Gaming VRAM Dedication\n" +
        "  • `/wish <idea>`      : Thought-to-Code generator (synthesize tool)\n" +
        "  • `search <topic>`    : Instant live web grounding (DuckDuckGo 0.8s)\n" +
        "  • `install <pkg>`     : Native package & application installer\n" +
        "  • `/look`             : Webcam optical sensor check\n" +
        "  • Plain text / speech : Direct Neural Cortex conversational intelligence"
      chatAutoDismissTimer.restart()
      return
    }

    // 0.01 System Doctor Intent
    if (lower === "doctor" || lower === "/doctor" || lower === "health" || lower === "/health" || lower === "system health" || lower === "check health") {
      root.hudVisible = true
      root.isThinking = true
      root.miloChatOutput = "🧰 **[MILO SYSTEM DOCTOR ACTIVE]**\n\n✦ Running diagnostics on GPU VRAM, 15 systemd services, PipeWire sound, and Wayland bus..."
      chatAutoDismissTimer.stop()
      thinkingWatchdog.restart()
      if (evoProc.running) return;
      evoProc.command = ["/home/jeffy/.local/bin/milo-doctor"]
      evoProc.running = true
      return
    }

    // 0.02 Milo Package Manager Intent (Install / Remove / Search / Update)
    var isPkgIntent = (
      lower.startsWith("install ") || lower.startsWith("/install ") ||
      lower.startsWith("milo install ") || lower.startsWith("milo-install ") ||
      lower.startsWith("can you install ") || lower.startsWith("ccan you install ") ||
      lower.startsWith("can u install ") || lower.startsWith("could you install ") ||
      lower.startsWith("please install ") || lower.startsWith("plz install ") ||
      lower.startsWith("try installing ") || lower.startsWith("reinstall ") ||
      lower.startsWith("get ") || lower.startsWith("setup ") ||
      lower.startsWith("download and install ") ||
      lower.startsWith("uninstall ") || lower.startsWith("/uninstall ") ||
      lower.startsWith("remove ") || lower.startsWith("/remove ") ||
      lower.startsWith("search package ") || lower.startsWith("find package ") ||
      lower === "update packages" || lower === "update system" || lower === "upgrade system" ||
      lower === "upgrade packages" || lower === "update software" ||
      (lower.indexOf("install") !== -1 && (lower.indexOf("opencode") !== -1 || lower.indexOf("again") !== -1))
    )

    if (isPkgIntent) {
      var pkgAction = "install"
      var targetPkg = ""

      if (lower.startsWith("uninstall ") || lower.startsWith("/uninstall ") ||
          lower.startsWith("remove ") || lower.startsWith("/remove ")) {
        pkgAction = "remove"
        targetPkg = raw.replace(/^(?:\/uninstall|\/remove|uninstall|remove)\s+/i, "").trim()
      } else if (lower.indexOf("update") !== -1 || lower.indexOf("upgrade") !== -1) {
        pkgAction = "update"
        targetPkg = ""
      } else if (lower.startsWith("search package ") || lower.startsWith("find package ")) {
        pkgAction = "search"
        targetPkg = raw.replace(/^(?:search|find)\s+package\s+/i, "").trim()
      } else {
        pkgAction = "install"
        targetPkg = raw.replace(/^(?:\/install|milo\s+install|milo-install|c*an\s+(?:you|u)\s+install|could\s+you\s+install|please\s+install|plz\s+install|try\s+installing|reinstall|download\s+and\s+install|install|get|setup)\s+(?:for\s+me\s+)?/i, "").trim()
        targetPkg = targetPkg.replace(/\s+(?:again|for\s+me|please|plz)$/i, "").trim()
        if (!targetPkg || targetPkg === "again" || targetPkg === "it") {
          targetPkg = "opencode"
        }
      }

      root.hudVisible = true
      root.isThinking = false
      root.playSound("chirp")

      if (pkgAction === "update") {
        root.miloChatOutput = "📦 **[MILO PACKAGE MANAGER ACTIVE]**\n\n✦ Launching system upgrade console via pacman..."
        quickCmdProc.command = ["foot", "-a", "milo-floating", "-T", "MILO // System Package Upgrade", "/home/jeffy/.local/bin/milo-pkg", "update"]
      } else if (pkgAction === "remove") {
        root.miloChatOutput = "🗑️ **[MILO PACKAGE MANAGER ACTIVE]**\n\n✦ Target: `" + targetPkg + "`\n✦ Spawning package removal console..."
        quickCmdProc.command = ["foot", "-a", "milo-floating", "-T", "MILO // Remove " + targetPkg, "/home/jeffy/.local/bin/milo-pkg", "remove", targetPkg]
      } else if (pkgAction === "search") {
        root.miloChatOutput = "🔍 **[MILO PACKAGE MANAGER ACTIVE]**\n\n✦ Searching repositories for: `" + targetPkg + "`..."
        quickCmdProc.command = ["foot", "-a", "milo-floating", "-T", "MILO // Search " + targetPkg, "/home/jeffy/.local/bin/milo-pkg", "search", targetPkg]
      } else {
        root.miloChatOutput = "📦 **[MILO PACKAGE MANAGER ACTIVE]**\n\n✦ Target: `" + targetPkg + "`\n✦ Resolving repository & spawning installation console..."
        quickCmdProc.command = ["foot", "-a", "milo-floating", "-T", "MILO // Install " + targetPkg, "/home/jeffy/.local/bin/milo-pkg", "install", targetPkg]
      }
      quickCmdProc.running = true
      chatAutoDismissTimer.restart()
      return
    }

    // 0. Codebase Forensic Audit Intent Detection (Natural Language)
    if (lower === "audit" || lower === "/audit" || lower.startsWith("/audit ") ||
        lower === "audit codebase" || lower === "audit yourself" || lower === "scan codebase" ||
        lower.indexOf("weak areas") !== -1 || lower.indexOf("what needs to be improved") !== -1 ||
        lower.indexOf("codebase audit") !== -1 || lower.indexOf("scan your codebase") !== -1 ||
        lower.indexOf("what can be improved") !== -1) {
      root.hudVisible = true
      root.isThinking = true
      root.miloChatOutput = "🔍 **[MILO FORENSIC AUDITOR ACTIVE]**\n\n✦ Scanning 70+ components, background services & UI timers for weak areas...\n✦ Running syntax checks and error-trap analysis..."
      chatAutoDismissTimer.stop()
      thinkingWatchdog.restart()
      if (evoProc.running) return;
      evoProc.command = ["/home/jeffy/.local/bin/milo-evolve", "audit"]
      evoProc.running = true
      return
    }

    // 0.1 Direct Wish Mode handling (when ✨ WISH pill is active or explicit wish command)
    if (root.currentMode === "✨ WISH" || lower.startsWith("/wish ") || lower.startsWith("wish ") ||
        lower.startsWith("make a tool ") || lower.startsWith("build a tool ") ||
        lower.startsWith("create a tool ") || lower.startsWith("make a script ") ||
        lower.startsWith("build a script ") || lower.startsWith("create a script ")) {
      var wishText = raw.replace(/^(?:\/wish|wish|make\s+(?:me\s+)?(?:a\s+)?(?:tool|script)?|build\s+(?:me\s+)?(?:a\s+)?(?:tool|script)?|create\s+(?:me\s+)?(?:a\s+)?(?:tool|script)?)\s*(?:that|to|for)?\s*/i, "").trim()
      root.hudVisible = true
      root.isThinking = true
      root.miloChatOutput = "✨ **[THOUGHT-TO-CODE GENESIS ACTIVE]**\n\n✦ **Goal:** \"" + (wishText || raw) + "\"\n✦ Consulting Neural Cortex & Synthesizing Sandboxed Tool..."
      chatAutoDismissTimer.stop()
      thinkingWatchdog.restart()
      if (evoProc.running) return;
      evoProc.command = ["/home/jeffy/.local/bin/milo-evolve", "wish", (wishText || raw)]
      evoProc.running = true
      return
    }

    // 0.2 Natural Web Search Intent ("search for...", "lookup...", "google...", "find out about...")
    if (lower.startsWith("search ") || lower.startsWith("search for ") ||
        lower.startsWith("lookup ") || lower.startsWith("look up ") ||
        lower.startsWith("google ") || lower.startsWith("find out about ")) {
      var searchGoal = raw.replace(/^(?:search(?:\s+for)?|look(?:\s+)?up|google|find(?:\s+out(?:\s+about)?)?)\s+/i, "").trim()
      root.askMilo("Search the web and give me a direct factual summary: " + searchGoal)
      return
    }

    // 1. Autonomous Vision-Action Operator (strictly requires explicit /do or operate)
    if (raw.startsWith("/do ") || lower.startsWith("operate ") || lower.startsWith("/operate ")) {
      var doGoal = raw.replace(/^(?:\/do|operate|\/operate)\s+/, "")
      quickCmdProc.command = ["foot", "-a", "milo-floating", "-T", "MILO // Autonomous Operator", "/home/jeffy/.local/bin/milo-do", doGoal]
      quickCmdProc.running = true
      return
    }

    // 1.1 Autonomous Browser Agent
    if (raw.startsWith("/browse ") || raw.startsWith("browse ")) {
      var browseGoal = raw.replace(/^(?:\/browse|browse)\s+/, "")
      quickCmdProc.command = ["foot", "-a", "milo-floating", "-T", "MILO // Autonomous Browser", "/usr/local/bin/milo-browser", browseGoal]
      quickCmdProc.running = true
      return
    }

    // 1.2 Hardware Optical Camera Vision (/look, /cam, /see, /camera, /posture, /desk)
    if (lower === "/look" || lower.startsWith("/look ") ||
        lower === "/cam" || lower.startsWith("/cam ") ||
        lower === "/see" || lower.startsWith("/see ") ||
        lower === "/camera" || lower.startsWith("/camera ") ||
        lower === "look" || lower === "see" || lower === "cam" || lower === "camera" ||
        lower === "/posture" || lower === "check posture" || lower === "posture" ||
        lower === "/desk" || lower === "check desk" || lower === "desk" ||
        lower.startsWith("look at ") || lower.startsWith("can you see") || lower.startsWith("what do you see")) {

      var lookQuery = raw.replace(/^\/(?:look|cam|see|camera|posture|desk)\s*/i, "").trim()
      root.hudVisible = true
      root.isThinking = true
      root.miloChatOutput = "✦ Optical sensor scanning webcam feed..."
      chatAutoDismissTimer.stop()
      thinkingWatchdog.restart()

      var lookArgs = ["/home/jeffy/.local/bin/milo-look", "--raw"]
      if (lower.indexOf("posture") !== -1) {
        lookArgs.push("--posture")
      } else if (lower.indexOf("desk") !== -1) {
        lookArgs.push("--desk")
      } else if (lookQuery.length > 0 && lower !== "look" && lower !== "see" && lower !== "cam" && lower !== "camera") {
        lookArgs.push(lookQuery)
      }

      if (agyProc.running) agyProc.running = false
      agyProc.command = lookArgs
      agyProc.running = true
      return
    }

    // 2. Milo CEO Dispatcher
    if (raw.startsWith("/dispatch ") || raw.startsWith("/code ") || raw.startsWith("/fix ")) {
      var mission = raw.replace(/^\/(dispatch|code|fix)\s+/, "")
      quickCmdProc.command = ["foot", "-a", "milo-floating", "-T", "MILO // CEO Dispatcher", "/home/jeffy/.local/bin/milo-dispatch", mission]
      quickCmdProc.running = true
      return
    }

    // 3. Aider QA Debugger
    if (raw === "/test" || raw.startsWith("/test ")) {
      var target = raw.replace(/^\/test\s*/, "")
      quickCmdProc.command = ["foot", "-a", "milo-floating", "-T", "MILO // Aider QA Debugger", "/home/jeffy/.local/bin/milo-test", target]
      quickCmdProc.running = true
      return
    }

    // 4. Hermes Operations
    if (raw === "/ops" || raw.startsWith("/ops ")) {
      var opsGoal = raw.replace(/^\/ops\s*/, "")
      quickCmdProc.command = ["foot", "-a", "milo-floating", "-T", "MILO // Hermes Operations", "/home/jeffy/.local/bin/milo-hermes", "chat", opsGoal]
      quickCmdProc.running = true
      return
    }

    // 4.5 Milo Game Mode (/game, /gamemode)
    if (lower === "/game" || lower === "/gamemode" || lower.startsWith("/game ") || lower.startsWith("/gamemode ")) {
      var gameArgs = raw.replace(/^\/(?:game|gamemode)\s*/, "").trim()
      if (!gameArgs || gameArgs === "toggle") {
        quickCmdProc.command = ["/home/jeffy/.local/bin/milo-game", "toggle"]
      } else {
        quickCmdProc.command = ["/home/jeffy/.local/bin/milo-game", gameArgs]
      }
      quickCmdProc.running = true
      return
    }

    // 4.6 Milo Autonomous Self-Upgrade Protocol (/evolve, /upgrade)
    if (lower === "/evolve" || lower.startsWith("/evolve ") || lower === "/upgrade" || lower.startsWith("/upgrade ")) {
      var evoSub = raw.replace(/^\/(?:evolve|upgrade)\s*/i, "").trim().toLowerCase()
      if (!evoSub || evoSub === "plan") {
        quickCmdProc.command = ["/home/jeffy/.local/bin/milo-evolve", "plan"]
      } else if (evoSub === "approve" || evoSub === "apply" || evoSub === "yes") {
        quickCmdProc.command = ["/home/jeffy/.local/bin/milo-evolve", "approve"]
      } else if (evoSub === "defer" || evoSub === "dismiss" || evoSub === "no") {
        quickCmdProc.command = ["/home/jeffy/.local/bin/milo-evolve", "defer"]
      } else if (evoSub === "diff" || evoSub === "inspect") {
        quickCmdProc.command = ["foot", "-a", "milo-floating", "-T", "MILO // Upgrade Code Inspector", "/home/jeffy/.local/bin/milo-evolve", "diff"]
      } else if (evoSub === "doctor" || evoSub === "heal") {
        quickCmdProc.command = ["foot", "-a", "milo-floating", "-T", "MILO // System Doctor", "/home/jeffy/.local/bin/milo-evolve", "doctor"]
      } else if (evoSub === "bench" || evoSub === "benchmark") {
        quickCmdProc.command = ["foot", "-a", "milo-floating", "-T", "MILO // Latency Benchmark", "/home/jeffy/.local/bin/milo-evolve", "benchmark"]
      } else if (evoSub.startsWith("wish ")) {
        var wishPrompt = raw.replace(/^\/(?:evolve|upgrade)\s+wish\s+/i, "").trim()
        quickCmdProc.command = ["foot", "-a", "milo-floating", "-T", "MILO // Thought-to-Code Genesis", "/home/jeffy/.local/bin/milo-evolve", "wish", wishPrompt]
      } else if (evoSub === "rollback") {
        quickCmdProc.command = ["/home/jeffy/.local/bin/milo-evolve", "test-rollback"]
      } else if (evoSub === "status" || evoSub === "ledger") {
        quickCmdProc.command = ["foot", "-a", "milo-floating", "-T", "MILO // Evolution Ledger", "/home/jeffy/.local/bin/milo-evolve", "status"]
      } else {
        quickCmdProc.command = ["/home/jeffy/.local/bin/milo-evolve", evoSub]
      }
      quickCmdProc.running = true
      return
    }

    // 4.7 Milo Thought-to-Code Direct Genesis (/wish <idea>)
    if (lower.startsWith("/wish ") || lower.startsWith("wish ")) {
      var directWish = raw.replace(/^(?:\/wish|wish)\s+/i, "").trim()
      root.hudVisible = true
      root.isThinking = true
      root.miloChatOutput = "✨ **[THOUGHT-TO-CODE GENESIS ACTIVE]**\n\n✦ **Goal:** \"" + directWish + "\"\n✦ Consulting Neural Cortex & Synthesizing Sandboxed Tool..."
      chatAutoDismissTimer.stop()
      thinkingWatchdog.restart()
      if (evoProc.running) return;
      evoProc.command = ["/home/jeffy/.local/bin/milo-evolve", "wish", directWish]
      evoProc.running = true
      return
    }

    // 5. Shell commands in COMMANDS mode
    if (root.currentMode === "⚡ COMMANDS") {
      quickCmdProc.command = ["foot", "-a", "milo-floating", "-T", "MILO // " + raw, "-e", "bash", "-c", raw + "; echo ''; read -p 'Press Enter to dismiss...'"]
      quickCmdProc.running = true
      return
    }

    // 6. Direct AI Query to Milo Neural Cortex
    root.askMilo(raw)
  }

  // Quick Action Process (Detached execution prevents process collisions and killed transactions)
  QtObject {
    id: quickCmdProc
    property var command: []
    property bool running: false
    onRunningChanged: if (running) {
      if (command && command.length > 0) {
        Quickshell.execDetached(command);
      }
      running = false;
    }
  }

  // Autonomous Evolution & Thought-to-Code Process
  Process {
    id: evoProc
    running: false
    command: []
    stdout: StdioCollector {
      onStreamFinished: {
        root.isThinking = false
        var rawOut = text ? text.trim() : ""
        var out = rawOut.replace(/\x1b\[[0-9;]*[a-zA-Z]/g, "")
        if (out.length > 0) {
          root.hudVisible = true
          if (out.indexOf("Upgrade complete") !== -1 || out.indexOf("Assertion PASSED") !== -1) {
            root.hasPendingEvolution = false
            root.miloChatOutput = "✔ **[UPGRADE LIVE & VERIFIED]**\n\n" + out
            root.playSound("chime")
            chatAutoDismissTimer.restart()
          } else if (out.indexOf("Formulated 1-Click Fix") !== -1 || out.indexOf("Proposal formulated") !== -1 || out.indexOf("Briefing dispatched") !== -1) {
            root.hasPendingEvolution = true
            root.playSound("sweep")
            if (!root.miloChatOutput || root.miloChatOutput.indexOf("ACTIVE]") !== -1) {
              root.miloChatOutput = out
            }
          } else {
            root.miloChatOutput = out
            root.playSound("chime")
          }
        }
      }
    }
    stderr: StdioCollector {
      onStreamFinished: {
        if (text && text.trim().length > 0) {
          root.isThinking = false
          root.hudVisible = true
          root.miloChatOutput = "✘ **Evolution / Audit Error:**\n\n" + text.trim()
          root.playSound("alert")
        }
      }
    }
  }

  // 4. Stable IPC Handlers
  IpcHandler {
    target: "milo"

    function say(text: string): string {
      root.lastCameraSnapshot = ""
      root.miloChatOutput = text
      chatAutoDismissTimer.restart()
      return "ok"
    }

    function proposeEvolution(briefingText: string): string {
      root.lastCameraSnapshot = ""
      root.miloChatOutput = briefingText
      root.hasPendingEvolution = true
      root.hudVisible = true
      return "ok"
    }

    function evolve(subcmd: string): string {
      var sub = (subcmd || "plan").trim()
      quickCmdProc.command = ["/home/jeffy/.local/bin/milo-evolve", sub]
      quickCmdProc.running = true
      return "Milo evolution command dispatched: " + sub
    }

    function wish(wishPrompt: string): string {
      root.executeDesktopCommand("/wish " + (wishPrompt || ""))
      return "ok"
    }

    function audit(): string {
      root.executeDesktopCommand("audit codebase")
      return "ok"
    }

    function showCamera(text: string, imagePath: string): string {
      root.lastCameraSnapshot = imagePath || "/home/jeffy/.local/state/milo/eyes/current_camera_capture.jpg"
      root.miloChatOutput = text
      chatAutoDismissTimer.restart()
      return "ok"
    }

    function look(query: string): string {
      root.executeDesktopCommand("/look " + (query || ""))
      return "Optical sensor dispatched"
    }

    function ask(query: string): string {
      root.askMilo(query)
      return "Query sent to Milo"
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
      root.isThinking = false
      root.lastCameraSnapshot = ""
      root.miloChatOutput = ""
      chatAutoDismissTimer.stop()
      return "cleared"
    }

    function toggleScratchpad(): string {
      root.scratchpadModalOpen = !root.scratchpadModalOpen
      return root.scratchpadModalOpen ? "open" : "closed"
    }

    function openScratchpad(): string {
      root.scratchpadModalOpen = true
      return "open"
    }

    function openWhatsApp(): string {
      root.midLeftTab = "whatsapp"
      root.scratchpadModalOpen = true
      return "open"
    }

    function openMail(): string {
      root.midLeftTab = "mail"
      root.scratchpadModalOpen = true
      return "open"
    }

    function switchTab(tab: string): string {
      root.midLeftTab = tab
      return tab
    }

    function closeScratchpad(): string {
      root.scratchpadModalOpen = false
      return "closed"
    }

    function toggleControlCenter(): string {
      root.controlCenterOpen = !root.controlCenterOpen
      if (root.controlCenterOpen) root.refreshControlCenter()
      return root.controlCenterOpen ? "open" : "closed"
    }

    function openControlCenter(): string {
      root.controlCenterOpen = true
      root.refreshControlCenter()
      return "open"
    }

    function openWifiScanner(): string {
      root.controlCenterOpen = true
      root.ccWifiScannerOpen = true
      root.startWifiScan()
      return "wifi_scanner_open"
    }

    function openBtScanner(): string {
      root.controlCenterOpen = true
      root.ccBtScannerOpen = true
      root.startBtScan()
      return "bt_scanner_open"
    }

    function closeControlCenter(): string {
      root.controlCenterOpen = false
      return "closed"
    }

    function musicPlayPause(): string {
      root.musicPlayPause()
      return "toggled"
    }

    function musicNext(): string {
      root.musicNext()
      return "next"
    }

    function musicPrev(): string {
      root.musicPrev()
      return "prev"
    }

    function musicPick(): string {
      root.musicPick()
      return "pick"
    }

    function musicTui(): string {
      root.musicTui()
      return "tui"
    }
  }

  // ==========================================================================
  // 5. NATIVE WAYLAND DESKTOP WALLPAPER LAYER WINDOW
  // Lives permanently on WlrLayer.Bottom (behind all normal windows)
  // ==========================================================================
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
        left: true
        right: true
      }

      color: "transparent"

      WlrLayershell.namespace: "milo-tactical-hud"
      WlrLayershell.layer: WlrLayer.Bottom
      WlrLayershell.keyboardFocus: WlrKeyboardFocus.OnDemand
      exclusionMode: ExclusionMode.Ignore
      updatesEnabled: true

      onClosed: {
        visible = true
      }

      // 4.9 Background click dismisser for HUD modal (click anywhere on empty wallpaper to dismiss)
      MouseArea {
        anchors.fill: parent
        z: -1
        onClicked: {
          if (root.miloChatOutput && !root.isThinking && !root.hasPendingEvolution) {
            root.miloChatOutput = ""
            root.lastCameraSnapshot = ""
            chatAutoDismissTimer.stop()
          }
        }
      }

      // ----------------------------------------------------------------------
      // 5.0 TOP SYSTEM STATUS BAR (Across Screen Header)
      // ----------------------------------------------------------------------
      Rectangle {
        id: topBar
        anchors.top: parent.top
        anchors.left: parent.left
        anchors.right: parent.right
        height: 38
        color: Qt.rgba(0.04, 0.01, 0.02, 0.70)
        border.color: Qt.rgba(1.0, 0.03, 0.22, 0.25)
        border.width: 1

        RowLayout {
          anchors.fill: parent
          anchors.leftMargin: 24
          anchors.rightMargin: 24

          RowLayout {
            spacing: 12
            Text {
              text: "MILO PROTOCOL"
              color: "#ffffff"
              font.pixelSize: 12
              font.bold: true
              font.family: "system-ui, sans-serif"
              font.letterSpacing: 2
            }
            Rectangle {
              height: 18; width: 155; radius: 4
              color: Qt.rgba(1.0, 0.03, 0.22, 0.18)
              border.color: "#ff0838"; border.width: 1
              Text {
                anchors.centerIn: parent
                text: "MILO PROTOCOL // WAYLAND"
                color: "#ff2a55"
                font.pixelSize: 9
                font.bold: true
                font.family: "monospace"
              }
            }
            Text {
              text: "Hyprland OS"
              color: Qt.rgba(1, 1, 1, 0.4)
              font.pixelSize: 11
              font.family: "monospace"
            }
          }

          Item { Layout.fillWidth: true }

          RowLayout {
            spacing: 16

            // Live Hybrid Intelligence Switch & Indicator
            Rectangle {
              height: 22
              width: intelRow.implicitWidth + 20
              radius: 5
              color: Qt.rgba(0.06, 0.01, 0.02, 0.85)
              border.color: root.intelligenceColor
              border.width: 1

              RowLayout {
                id: intelRow
                anchors.centerIn: parent
                spacing: 6
                Rectangle {
                  width: 7; height: 7; radius: 3.5
                  color: root.intelligenceColor
                  SequentialAnimation on opacity {
                    loops: Animation.Infinite
                    PropertyAnimation { to: 0.3; duration: 1100 }
                    PropertyAnimation { to: 1.0; duration: 1100 }
                  }
                }
                Text {
                  text: root.intelligenceLabel
                  color: "#ffffff"
                  font.pixelSize: 10
                  font.bold: true
                  font.family: "monospace"
                }
              }

              MouseArea {
                anchors.fill: parent
                cursorShape: Qt.PointingHandCursor
                onClicked: root.toggleIntelligenceMode()
              }
            }

            Text {
              text: root.cpuText
              color: "#ff2a55"
              font.pixelSize: 11
              font.bold: true
              font.family: "monospace"
              MouseArea {
                anchors.fill: parent; cursorShape: Qt.PointingHandCursor
                onClicked: {
                  quickCmdProc.command = ["foot", "-a", "milo-floating", "-T", "MILO // Quantum Core Telemetry", "-e", "btop"]
                  quickCmdProc.running = true
                  root.triggerShockwave()
                }
              }
            }
            Text {
              text: root.tempText
              color: Qt.rgba(1, 1, 1, 0.7)
              font.pixelSize: 11
              font.family: "monospace"
              MouseArea {
                anchors.fill: parent; cursorShape: Qt.PointingHandCursor
                onClicked: {
                  quickCmdProc.command = ["foot", "-a", "milo-floating", "-T", "MILO // Thermal Diagnostics", "-e", "sh", "-c", "sensors; echo ''; read -p 'Press Enter to dismiss...'"]
                  quickCmdProc.running = true
                  root.triggerShockwave()
                }
              }
            }
            Text {
              text: Qt.formatDateTime(root.clockDate, "hh:mm:ss AP")
              color: "#ffffff"
              font.pixelSize: 12
              font.bold: true
              font.family: "monospace"
              MouseArea {
                anchors.fill: parent; cursorShape: Qt.PointingHandCursor
                onClicked: {
                  quickCmdProc.command = ["foot", "-a", "milo-floating", "-T", "MILO // Chronometer & Calendar", "-e", "sh", "-c", "cal -3; echo ''; cal -y; echo ''; read -p 'Press Enter to dismiss...'"]
                  quickCmdProc.running = true
                  root.triggerShockwave()
                }
              }
            }

            // Option B Quick Settings Summon Pill
            Rectangle {
              height: 22
              width: qsPillRow.implicitWidth + 18
              radius: 5
              color: root.controlCenterOpen ? Qt.rgba(1.0, 0.03, 0.22, 0.40) : Qt.rgba(1.0, 0.03, 0.22, 0.18)
              border.color: "#ff0838"
              border.width: 1

              RowLayout {
                id: qsPillRow
                anchors.centerIn: parent
                spacing: 5
                Text { text: "⚙"; font.pixelSize: 10 }
                Text {
                  text: "SETTINGS"
                  color: "#ffffff"
                  font.pixelSize: 10
                  font.bold: true
                  font.family: "monospace"
                }
              }

              MouseArea {
                anchors.fill: parent
                cursorShape: Qt.PointingHandCursor
                onClicked: {
                  root.controlCenterOpen = !root.controlCenterOpen
                  if (root.controlCenterOpen) root.refreshControlCenter()
                }
              }
            }
          }
        }
      }

      // ----------------------------------------------------------------------
      // 5.2 MILO TRINITY POWER REACTOR (Dead Center X: 50%, Y: 50%)
      // Perfectly aligned with the central Milo Trinity wallpaper core
      // ----------------------------------------------------------------------
      Item {
        id: arcReactorAnchor
        anchors.centerIn: parent
        width: 190; height: 190

        // Expanding Shockwave Blast Ring
        Rectangle {
          id: shockwaveRing
          anchors.centerIn: parent
          width: 50; height: 50
          radius: 25
          color: "transparent"
          border.color: "#ffffff"
          border.width: 3
          opacity: 0
          scale: 1

          function trigger() {
            shockAnim.restart()
          }

          Connections {
            target: root
            function onTriggerShockwave() {
              shockAnim.restart()
            }
          }

          SequentialAnimation {
            id: shockAnim
            ParallelAnimation {
              PropertyAnimation { target: shockwaveRing; property: "opacity"; from: 1.0; to: 0.0; duration: 750; easing.type: Easing.OutQuad }
              PropertyAnimation { target: shockwaveRing; property: "scale"; from: 1.0; to: 15.0; duration: 750; easing.type: Easing.OutQuad }
            }
            PropertyAction { target: shockwaveRing; property: "scale"; value: 1.0 }
            PropertyAction { target: shockwaveRing; property: "opacity"; value: 0.0 }
          }
        }

        // Outer CAD Rotating Ring (Dual-Tone Cyan & Crimson Telemetry)
        Rectangle {
          anchors.centerIn: parent
          width: 176; height: 176; radius: 88
          color: "transparent"
          border.color: (root.taskStage !== "IDLE" && root.taskStage !== "DONE") ? root.activeAgentColor : Qt.rgba(0, 0.95, 1, 0.5)
          border.width: (root.taskStage !== "IDLE" && root.taskStage !== "DONE") ? 2.0 : 1.5

          Behavior on border.color { ColorAnimation { duration: 400 } }

          Repeater {
            model: 12
            Rectangle {
              x: 88 - 1; y: 2
              width: 2; height: 8
              color: (index % 3 === 0) ? "#00f0ff" : ((root.taskStage !== "IDLE" && root.taskStage !== "DONE") ? root.activeAgentColor : "#ff0838")
              transformOrigin: Item.Bottom
              rotation: index * 30
            }
          }

          RotationAnimation on rotation {
            loops: Animation.Infinite
            from: 0; to: 360
            duration: (root.taskStage !== "IDLE" && root.taskStage !== "DONE") ? 4000 : 16000
          }
        }

        // Inner CAD Rotating Ring (Counter-Clockwise, 10s idle / 2.5s active)
        Rectangle {
          anchors.centerIn: parent
          width: 136; height: 136; radius: 68
          color: "transparent"
          border.color: (root.taskStage !== "IDLE" && root.taskStage !== "DONE") ? root.activeAgentColor : Qt.rgba(1, 0.03, 0.22, 0.5)
          border.width: (root.taskStage !== "IDLE" && root.taskStage !== "DONE") ? 1.8 : 1.2

          Behavior on border.color { ColorAnimation { duration: 400 } }

          Repeater {
            model: 8
            Rectangle {
              x: 68 - 1.5; y: 3
              width: 3; height: 7
              color: (root.taskStage !== "IDLE" && root.taskStage !== "DONE") ? root.activeAgentColor : "#ff2a55"
              transformOrigin: Item.Bottom
              rotation: index * 45
            }
          }

          RotationAnimation on rotation {
            loops: Animation.Infinite
            from: 360; to: 0
            duration: (root.taskStage !== "IDLE" && root.taskStage !== "DONE") ? 2500 : 10000
          }
        }

        // Active Agent Plasma Halo
        Rectangle {
          anchors.centerIn: parent
          width: 76; height: 76; radius: 38
          color: "transparent"
          border.color: root.activeAgentColor
          border.width: 1.5
          opacity: (root.taskStage !== "IDLE" && root.taskStage !== "DONE") ? 0.75 : 0.0
          Behavior on opacity { NumberAnimation { duration: 350 } }

          SequentialAnimation on scale {
            running: root.taskStage !== "IDLE" && root.taskStage !== "DONE"
            loops: Animation.Infinite
            PropertyAnimation { to: 1.25; duration: 650; easing.type: Easing.InOutQuad }
            PropertyAnimation { to: 1.0; duration: 650; easing.type: Easing.InOutQuad }
          }
        }

        // Interactive Targeting Reticle (Transparent center reveals wallpaper 12-blade aperture!)
        Rectangle {
          anchors.centerIn: parent
          width: 76; height: 76
          radius: 38
          color: (root.taskStage !== "IDLE" && root.taskStage !== "DONE") ? Qt.rgba(root.activeAgentColor.r, root.activeAgentColor.g, root.activeAgentColor.b, 0.15) : "transparent"
          border.color: (root.taskStage !== "IDLE" && root.taskStage !== "DONE") ? root.activeAgentColor : Qt.rgba(0, 0.95, 1, 0.75)
          border.width: (root.taskStage !== "IDLE" && root.taskStage !== "DONE") ? 2.5 : 1.5

          Behavior on border.color { ColorAnimation { duration: 400 } }

          // Concentric micro-crosshairs in core center
          Rectangle {
            anchors.centerIn: parent
            width: 44; height: 44; radius: 22
            color: "transparent"
            border.color: (root.taskStage !== "IDLE" && root.taskStage !== "DONE") ? root.activeAgentColor : Qt.rgba(1, 1, 1, 0.5)
            border.width: 1.0
          }

          SequentialAnimation on scale {
            loops: Animation.Infinite
            PropertyAnimation {
              to: (root.taskStage !== "IDLE" && root.taskStage !== "DONE") ? 1.18 : 1.06
              duration: (root.taskStage !== "IDLE" && root.taskStage !== "DONE") ? 750 : 2000
              easing.type: Easing.InOutQuad
            }
            PropertyAnimation {
              to: 1.0
              duration: (root.taskStage !== "IDLE" && root.taskStage !== "DONE") ? 750 : 2000
              easing.type: Easing.InOutQuad
            }
          }
        }

        // Interactive Click on Quantum Core (Launch Core Diagnostics)
        MouseArea {
          anchors.fill: parent
          cursorShape: Qt.PointingHandCursor
          onClicked: {
            quickCmdProc.command = ["foot", "-a", "milo-floating", "-T", "MILO QUANTUM CORE // SYSTEM DIAGNOSTICS", "-e", "btop"]
            quickCmdProc.running = true
            root.triggerShockwave()
          }
        }

        // ====================================================================
        // THE 3D MILO NEURAL MATRIX: ORBITAL AGENT SATELLITES (TRINITY CONFIG)
        // ====================================================================

        // 1. SATELLITE: CLAUDE CODE (The Forge / Chief Architect - Top-Left)
        Item {
          id: satelliteClaude
          x: -61; y: -10
          width: 80; height: 80

          property bool isActive: root.activeAgent === "claude"

          // Rotating CAD Ring with Glass Backdrop
          Rectangle {
            anchors.centerIn: parent
            width: 70; height: 70; radius: 35
            color: satelliteClaude.isActive ? Qt.rgba(1, 0.67, 0, 0.25) : Qt.rgba(0.03, 0.01, 0.05, 0.88)
            border.color: satelliteClaude.isActive ? "#ffaa00" : Qt.rgba(1, 0.67, 0, 0.5)
            border.width: satelliteClaude.isActive ? 2 : 1

            Repeater {
              model: 6
              Rectangle {
                x: 35 - 1; y: 2
                width: 2; height: 5
                color: satelliteClaude.isActive ? "#ffaa00" : Qt.rgba(1, 0.67, 0, 0.6)
                transformOrigin: Item.Bottom
                rotation: index * 60
              }
            }

            RotationAnimation on rotation {
              loops: Animation.Infinite
              from: 0; to: 360
              duration: satelliteClaude.isActive ? 3000 : 12000
            }
          }

          // Node Center Core & Label
          Column {
            anchors.centerIn: parent
            spacing: 2
            Text {
              anchors.horizontalCenter: parent.horizontalCenter
              text: "🏗️"
              font.pixelSize: 13
            }
            Text {
              anchors.horizontalCenter: parent.horizontalCenter
              text: "CLAUDE"
              font.pixelSize: 9
              font.bold: true
              font.letterSpacing: 1.2
              color: satelliteClaude.isActive ? "#ffaa00" : "#f8fafc"
            }
            Text {
              anchors.horizontalCenter: parent.horizontalCenter
              text: satelliteClaude.isActive ? "CODING" : "ARCHITECT"
              font.pixelSize: 7
              color: satelliteClaude.isActive ? "#ffaa00" : "#cbd5e1"
            }
          }

          MouseArea {
            anchors.fill: parent
            cursorShape: Qt.PointingHandCursor
            hoverEnabled: true
            onClicked: {
              quickCmdProc.command = ["foot", "-a", "milo-floating", "-T", "MILO // Claude Architect", "/home/jeffy/.local/bin/milo-code"]
              quickCmdProc.running = true
            }
          }
        }

        // 2. SATELLITE: HERMES AGENT (Operations Turbine - Top-Right)
        Item {
          id: satelliteHermes
          x: 181; y: -10
          width: 80; height: 80

          property bool isActive: root.activeAgent === "hermes"

          // Bladed Ion Turbine with Glass Backdrop
          Rectangle {
            anchors.centerIn: parent
            width: 70; height: 70; radius: 35
            color: satelliteHermes.isActive ? Qt.rgba(0, 0.9, 1, 0.25) : Qt.rgba(0.03, 0.01, 0.05, 0.88)
            border.color: satelliteHermes.isActive ? "#00e5ff" : Qt.rgba(0, 0.9, 1, 0.5)
            border.width: satelliteHermes.isActive ? 2 : 1

            Repeater {
              model: 8
              Rectangle {
                x: 35 - 1.5; y: 2
                width: 3; height: 6
                color: satelliteHermes.isActive ? "#00e5ff" : Qt.rgba(0, 0.9, 1, 0.6)
                transformOrigin: Item.Bottom
                rotation: index * 45
              }
            }

            RotationAnimation on rotation {
              loops: Animation.Infinite
              from: 0; to: 360
              duration: satelliteHermes.isActive ? 1800 : 10000
            }
          }

          // Node Center Core & Label
          Column {
            anchors.centerIn: parent
            spacing: 2
            Text {
              anchors.horizontalCenter: parent.horizontalCenter
              text: "⚡"
              font.pixelSize: 13
            }
            Text {
              anchors.horizontalCenter: parent.horizontalCenter
              text: "HERMES"
              font.pixelSize: 9
              font.bold: true
              font.letterSpacing: 1.2
              color: satelliteHermes.isActive ? "#00e5ff" : "#f8fafc"
            }
            Text {
              anchors.horizontalCenter: parent.horizontalCenter
              text: satelliteHermes.isActive ? "OPS RUN" : "OPERATIONS"
              font.pixelSize: 7
              color: satelliteHermes.isActive ? "#00e5ff" : "#cbd5e1"
            }
          }

          MouseArea {
            anchors.fill: parent
            cursorShape: Qt.PointingHandCursor
            hoverEnabled: true
            onClicked: {
              quickCmdProc.command = ["foot", "-a", "milo-floating", "-T", "MILO // Hermes Operations", "/home/jeffy/.local/bin/milo-hermes"]
              quickCmdProc.running = true
            }
          }
        }

        // 3. SATELLITE: AIDER + DEEPSEEK-R1 (The Threat Matrix / QA Scanner - Bottom)
        Item {
          id: satelliteAider
          x: 60; y: 200
          width: 80; height: 80

          property bool isActive: root.activeAgent === "aider"

          // Rotating Scanning Reticle with Glass Backdrop
          Rectangle {
            anchors.centerIn: parent
            width: 70; height: 70; radius: 35
            color: satelliteAider.isActive ? Qt.rgba(0, 1, 0.4, 0.25) : Qt.rgba(0.03, 0.01, 0.05, 0.88)
            border.color: satelliteAider.isActive ? "#00ff66" : Qt.rgba(0, 1, 0.4, 0.5)
            border.width: satelliteAider.isActive ? 2 : 1

            // Crosshair lines
            Rectangle { anchors.centerIn: parent; width: 62; height: 1; color: satelliteAider.isActive ? "#00ff66" : Qt.rgba(0, 1, 0.4, 0.4) }
            Rectangle { anchors.centerIn: parent; width: 1; height: 62; color: satelliteAider.isActive ? "#00ff66" : Qt.rgba(0, 1, 0.4, 0.4) }

            RotationAnimation on rotation {
              loops: Animation.Infinite
              from: 360; to: 0
              duration: satelliteAider.isActive ? 2500 : 15000
            }
          }

          // Node Center Core & Label
          Column {
            anchors.centerIn: parent
            spacing: 2
            Text {
              anchors.horizontalCenter: parent.horizontalCenter
              text: "🔍"
              font.pixelSize: 13
            }
            Text {
              anchors.horizontalCenter: parent.horizontalCenter
              text: "AIDER"
              font.pixelSize: 9
              font.bold: true
              font.letterSpacing: 1.2
              color: satelliteAider.isActive ? "#00ff66" : "#f8fafc"
            }
            Text {
              anchors.horizontalCenter: parent.horizontalCenter
              text: satelliteAider.isActive ? "TESTING" : "QA SCANNER"
              font.pixelSize: 7
              color: satelliteAider.isActive ? "#00ff66" : "#cbd5e1"
            }
          }

          MouseArea {
            anchors.fill: parent
            cursorShape: Qt.PointingHandCursor
            hoverEnabled: true
            onClicked: {
              quickCmdProc.command = ["foot", "-a", "milo-floating", "-T", "MILO // Aider QA Debugger", "/home/jeffy/.local/bin/milo-test"]
              quickCmdProc.running = true
            }
          }
        }

        // 4. LIVE MISSION TELEMETRY HUD CARD
        Rectangle {
          id: missionTelemetryCard
          visible: root.taskStage !== "IDLE" && root.taskStage !== "DONE"
          anchors.bottom: parent.top
          anchors.bottomMargin: 140
          anchors.horizontalCenter: parent.horizontalCenter
          width: Math.max(380, Math.min(620, missionContentCol.implicitWidth + 36))
          height: missionContentCol.implicitHeight + 22
          radius: 12
          color: Qt.rgba(0.06, 0.01, 0.02, 0.94)
          border.color: root.activeAgentColor
          border.width: 1.5

          Behavior on border.color { ColorAnimation { duration: 350 } }

          Column {
            id: missionContentCol
            anchors.centerIn: parent
            spacing: 5
            width: parent.width - 28

            // Top Status Line
            RowLayout {
              width: parent.width
              spacing: 8

              Rectangle {
                width: 8; height: 8; radius: 4
                color: root.activeAgentColor
                SequentialAnimation on opacity {
                  loops: Animation.Infinite
                  PropertyAnimation { to: 0.2; duration: 350 }
                  PropertyAnimation { to: 1.0; duration: 350 }
                }
              }

              Text {
                text: "TACTICAL AI RUNNER: " + root.activeAgent.toUpperCase()
                color: "#ffffff"
                font.pixelSize: 10
                font.bold: true
                font.letterSpacing: 1.2
              }

              Rectangle {
                height: 16; width: stageBadgeText.implicitWidth + 10; radius: 8
                color: Qt.rgba(root.activeAgentColor.r, root.activeAgentColor.g, root.activeAgentColor.b, 0.25)
                border.color: root.activeAgentColor
                border.width: 1
                Text {
                  id: stageBadgeText
                  anchors.centerIn: parent
                  text: root.taskStage
                  color: root.activeAgentColor
                  font.pixelSize: 8
                  font.bold: true
                }
              }

              Item { Layout.fillWidth: true }

              Text {
                text: root.formatElapsed(root.taskElapsedSec)
                color: root.activeAgentColor
                font.pixelSize: 10
                font.bold: true
                font.family: "monospace"
              }
            }

            // Mission Goal
            Text {
              width: parent.width
              visible: root.taskGoal.length > 0
              text: "MISSION // " + root.taskGoal
              color: "#f1f5f9"
              font.pixelSize: 11
              font.bold: true
              elide: Text.ElideRight
              maximumLineCount: 1
            }

            // Details / Technical Status
            Text {
              width: parent.width
              visible: root.taskDetails.length > 0
              text: "STATUS // " + root.taskDetails
              color: root.activeAgentColor
              font.pixelSize: 9
              elide: Text.ElideRight
              maximumLineCount: 1
            }
          }
        }
      }

      // ----------------------------------------------------------------------
      // 5.2.1 ARCHIVE STATUS NOTE (Subtle indicator above bottom capsule)
      // ----------------------------------------------------------------------

      // ----------------------------------------------------------------------
      // 5.3 TOP-LEFT: HYPRLAND WORKSPACE RADAR RETICLE
      // ----------------------------------------------------------------------
      Rectangle {
        id: radarCard
        x: 35; y: 52
        width: 220; height: 185
        radius: 14
        color: Qt.rgba(0.06, 0.01, 0.02, 0.85)
        border.color: Qt.rgba(1.0, 0.03, 0.22, 0.45)
        border.width: 1.2

        ColumnLayout {
          anchors.fill: parent
          anchors.margins: 12
          spacing: 8

          RowLayout {
            Layout.fillWidth: true
            Text {
              text: "✦ WORKSPACE RADAR"
              color: "#ff2a55"
              font.pixelSize: 11
              font.bold: true
              font.family: "monospace"
            }
            Item { Layout.fillWidth: true }
            Rectangle {
              height: 16; width: 44; radius: 3
              color: "#ff0838"
              Text {
                anchors.centerIn: parent
                text: "WS " + (Hyprland.focusedWorkspace ? Hyprland.focusedWorkspace.id : "1")
                color: "#ffffff"
                font.pixelSize: 9
                font.bold: true
                font.family: "monospace"
              }
              MouseArea {
                anchors.fill: parent; cursorShape: Qt.PointingHandCursor
                onClicked: {
                  quickCmdProc.command = ["hyprctl", "dispatch", "workspace", "m+1"]
                  quickCmdProc.running = true
                  root.triggerShockwave()
                }
              }
            }
          }

          Item {
            Layout.alignment: Qt.AlignHCenter
            width: 120; height: 120

            Rectangle {
              anchors.fill: parent
              radius: 60
              color: Qt.rgba(0.12, 0.01, 0.03, 0.60)
              border.color: Qt.rgba(1.0, 0.03, 0.22, 0.4)
              border.width: 1.5
            }

            Rectangle {
              anchors.centerIn: parent
              width: 70; height: 70
              radius: 35
              color: "transparent"
              border.color: Qt.rgba(1.0, 0.03, 0.22, 0.3)
              border.width: 1
            }

            // Rotating sweep
            Item {
              anchors.fill: parent
              RotationAnimation on rotation {
                loops: Animation.Infinite
                from: 0; to: 360
                duration: 4000
              }
              Rectangle {
                width: 58; height: 1.5
                x: 60; y: 60
                transformOrigin: Item.Left
                gradient: Gradient {
                  orientation: Gradient.Horizontal
                  GradientStop { position: 0.0; color: "#ff0838" }
                  GradientStop { position: 1.0; color: "transparent" }
                }
              }
            }

            // 10 Orbital Workspace Blips
            Repeater {
              model: 10
              delegate: Item {
                id: blipItem
                required property int index
                property int wsNum: index + 1
                property real angle: (wsNum - 1) * (360 / 10) * (Math.PI / 180)
                property real radius: 46
                x: 60 + radius * Math.cos(angle) - width / 2
                y: 60 + radius * Math.sin(angle) - height / 2
                width: 18; height: 18

                property bool isFocused: Hyprland.focusedWorkspace && Hyprland.focusedWorkspace.id === wsNum

                Rectangle {
                  anchors.fill: parent
                  radius: 9
                  color: blipItem.isFocused ? "#ff0838" : Qt.rgba(0.14, 0.01, 0.03, 0.85)
                  border.color: blipItem.isFocused ? "#ffffff" : Qt.rgba(1.0, 0.03, 0.22, 0.5)
                  border.width: blipItem.isFocused ? 1.5 : 1

                  Text {
                    anchors.centerIn: parent
                    text: blipItem.wsNum
                    color: blipItem.isFocused ? "#ffffff" : "#ff2a55"
                    font.pixelSize: 9
                    font.bold: true
                    font.family: "monospace"
                  }
                }

                MouseArea {
                  anchors.fill: parent
                  cursorShape: Qt.PointingHandCursor
                  onClicked: {
                    quickCmdProc.command = ["hyprctl", "dispatch", "workspace", String(blipItem.wsNum)]
                    quickCmdProc.running = true
                  }
                }
              }
            }
          }
        }
      }

      // ----------------------------------------------------------------------
      // 5.4 MID-LEFT: TACTICAL SCRATCHPAD & CALENDAR (Tasks / Agenda Dual-Tab)
      // ----------------------------------------------------------------------
      Rectangle {
        id: scratchpadCard
        x: 35
        anchors.verticalCenter: parent.verticalCenter
        width: 255; height: 245
        radius: 14
        color: Qt.rgba(0.06, 0.01, 0.02, 0.85)
        border.color: root.midLeftTab === "whatsapp" ? Qt.rgba(0.15, 0.83, 0.40, 0.45) : (root.midLeftTab === "mail" ? Qt.rgba(1.0, 0.67, 0.0, 0.45) : (root.midLeftTab === "agenda" ? Qt.rgba(0, 0.9, 1.0, 0.4) : Qt.rgba(1.0, 0.03, 0.22, 0.45)))
        border.width: 1.2

        ColumnLayout {
          anchors.fill: parent
          anchors.margins: 10
          spacing: 6

          // Header: Quad-Tab Switcher & Stats
          RowLayout {
            Layout.fillWidth: true
            Layout.alignment: Qt.AlignTop
            spacing: 4

            // Tasks Tab Button
            Rectangle {
              height: 20
              width: tasksTabLabel.implicitWidth + 10
              radius: 4
              color: root.midLeftTab === "tasks" ? "#ff0838" : Qt.rgba(1, 0.03, 0.22, 0.15)
              border.color: root.midLeftTab === "tasks" ? "#ffffff" : Qt.rgba(1, 0.03, 0.22, 0.4)
              border.width: 1

              Text {
                id: tasksTabLabel
                anchors.centerIn: parent
                text: "✦ TASKS"
                color: root.midLeftTab === "tasks" ? "#ffffff" : "#ff8899"
                font.pixelSize: 8
                font.bold: true
                font.family: "monospace"
              }

              MouseArea {
                anchors.fill: parent
                cursorShape: Qt.PointingHandCursor
                onClicked: {
                  root.midLeftTab = "tasks"
                  deskTaskInput.forceActiveFocus()
                }
              }
            }

            // Agenda Tab Button
            Rectangle {
              height: 20
              width: agendaTabLabel.implicitWidth + 10
              radius: 4
              color: root.midLeftTab === "agenda" ? "#00f0ff" : Qt.rgba(0, 0.9, 1.0, 0.15)
              border.color: root.midLeftTab === "agenda" ? "#ffffff" : Qt.rgba(0, 0.9, 1.0, 0.4)
              border.width: 1

              Text {
                id: agendaTabLabel
                anchors.centerIn: parent
                text: "📅 AGENDA"
                color: root.midLeftTab === "agenda" ? "#060102" : "#80f5ff"
                font.pixelSize: 8
                font.bold: true
                font.family: "monospace"
              }

              MouseArea {
                anchors.fill: parent
                cursorShape: Qt.PointingHandCursor
                onClicked: {
                  root.midLeftTab = "agenda"
                  deskAgendaInput.forceActiveFocus()
                }
              }
            }

            // Mail Tab Button in HUD Header
            Rectangle {
              height: 20
              width: hudMailLabel.implicitWidth + 10
              radius: 4
              color: root.midLeftTab === "mail" ? "#ffaa00" : (root.mailData && root.mailData.unread_count > 0 ? Qt.rgba(1.0, 0.67, 0.0, 0.25) : Qt.rgba(1, 1, 1, 0.08))
              border.color: root.midLeftTab === "mail" ? "#ffffff" : (root.mailData && root.mailData.unread_count > 0 ? "#ffaa00" : Qt.rgba(1, 1, 1, 0.2))
              border.width: 1

              Text {
                id: hudMailLabel
                anchors.centerIn: parent
                text: root.mailData && root.mailData.unread_count > 0 ? ("✉ " + root.mailData.unread_count) : "✉ MAIL"
                color: root.midLeftTab === "mail" ? "#060102" : (root.mailData && root.mailData.unread_count > 0 ? "#ffaa00" : Qt.rgba(1, 1, 1, 0.45))
                font.pixelSize: 8
                font.bold: true
                font.family: "monospace"
              }

              MouseArea {
                anchors.fill: parent
                cursorShape: Qt.PointingHandCursor
                onClicked: {
                  root.midLeftTab = "mail"
                  deskMailFocusScope.forceActiveFocus()
                }
              }
            }

            // WhatsApp Tab Button in HUD Header
            Rectangle {
              height: 20
              width: hudWaLabel.implicitWidth + 10
              radius: 4
              color: root.midLeftTab === "whatsapp" ? "#25d366" : (root.whatsappData && root.whatsappData.unread_count > 0 ? Qt.rgba(0.15, 0.83, 0.40, 0.25) : Qt.rgba(1, 1, 1, 0.08))
              border.color: root.midLeftTab === "whatsapp" ? "#ffffff" : (root.whatsappData && root.whatsappData.unread_count > 0 ? "#25d366" : Qt.rgba(1, 1, 1, 0.2))
              border.width: 1

              Text {
                id: hudWaLabel
                anchors.centerIn: parent
                text: root.whatsappData && root.whatsappData.unread_count > 0 ? ("💬 " + root.whatsappData.unread_count) : "💬 WA"
                color: root.midLeftTab === "whatsapp" ? "#060102" : (root.whatsappData && root.whatsappData.unread_count > 0 ? "#25d366" : Qt.rgba(1, 1, 1, 0.45))
                font.pixelSize: 8
                font.bold: true
                font.family: "monospace"
              }

              MouseArea {
                anchors.fill: parent
                cursorShape: Qt.PointingHandCursor
                onClicked: {
                  root.midLeftTab = "whatsapp"
                  deskWaFocusScope.forceActiveFocus()
                }
              }
            }

            Item { Layout.fillWidth: true }

            // Expand Modal Button
            Text {
              text: "⛶"
              color: root.midLeftTab === "whatsapp" ? "#25d366" : (root.midLeftTab === "mail" ? "#ffaa00" : (root.midLeftTab === "agenda" ? "#00f0ff" : "#ff2a55"))
              font.pixelSize: 11
              MouseArea {
                anchors.fill: parent
                cursorShape: Qt.PointingHandCursor
                onClicked: root.scratchpadModalOpen = true
              }
            }

            // Badge / Counter
            Text {
              text: {
                if (root.midLeftTab === "tasks") {
                  var doneCount = 0
                  for (var i = 0; i < root.todosList.length; i++) {
                    if (root.todosList[i].done) doneCount++
                  }
                  return doneCount + "/" + root.todosList.length + " DONE"
                } else if (root.midLeftTab === "agenda") {
                  return root.agendaList.length + " TODAY"
                } else if (root.midLeftTab === "mail") {
                  return (root.mailData && root.mailData.unread_count ? root.mailData.unread_count : 0) + " UNREAD"
                } else {
                  return (root.whatsappData && root.whatsappData.unread_count ? root.whatsappData.unread_count : 0) + " UNREAD"
                }
              }
              color: root.midLeftTab === "whatsapp" ? "#25d366" : (root.midLeftTab === "mail" ? "#ffaa00" : (root.midLeftTab === "agenda" ? Qt.rgba(0, 0.9, 1.0, 0.7) : Qt.rgba(1, 1, 1, 0.5)))
              font.pixelSize: 8
              font.family: "monospace"
              MouseArea {
                anchors.fill: parent
                cursorShape: Qt.PointingHandCursor
                onClicked: root.scratchpadModalOpen = true
              }
            }
          }

          // Worktime Status Pill (Desktop HUD - Agenda Tab)
          Rectangle {
            Layout.fillWidth: true
            height: 18
            radius: 4
            visible: root.midLeftTab === "agenda"
            color: root.worktimeData && root.worktimeData.is_worktime ? Qt.rgba(0, 0.9, 1.0, 0.15) : Qt.rgba(0.06, 0.10, 0.14, 0.6)
            border.color: root.worktimeData && root.worktimeData.is_worktime ? Qt.rgba(0, 0.9, 1.0, 0.4) : Qt.rgba(1, 1, 1, 0.12)
            border.width: 1

            RowLayout {
              anchors.fill: parent
              anchors.leftMargin: 6
              anchors.rightMargin: 6
              spacing: 4

              Text {
                text: "⏱"
                font.pixelSize: 8
              }

              Text {
                text: "WORK: " + (root.worktimeData && root.worktimeData.start ? (root.worktimeData.start + "-" + root.worktimeData.end) : "09:00-18:00")
                color: root.worktimeData && root.worktimeData.is_worktime ? "#00f0ff" : Qt.rgba(1, 1, 1, 0.6)
                font.pixelSize: 8
                font.bold: true
                font.family: "monospace"
              }

              Item { Layout.fillWidth: true }

              Text {
                text: root.worktimeData && root.worktimeData.status_text ? root.worktimeData.status_text : "Off Duty"
                color: root.worktimeData && root.worktimeData.is_worktime ? "#00ff88" : Qt.rgba(1, 1, 1, 0.45)
                font.pixelSize: 7
                font.family: "monospace"
                elide: Text.ElideRight
              }
            }

            MouseArea {
              anchors.fill: parent
              cursorShape: Qt.PointingHandCursor
              onClicked: {
                root.scratchpadModalOpen = true
                root.midLeftTab = "agenda"
              }
            }
          }

          // Tasks Mini-Toolbar & Wrap Mode Pill (Desktop HUD)
          Rectangle {
            Layout.fillWidth: true
            height: 18
            radius: 4
            visible: root.midLeftTab === "tasks"
            color: Qt.rgba(0.12, 0.01, 0.03, 0.5)
            border.color: Qt.rgba(1, 0.03, 0.22, 0.25)
            border.width: 1

            RowLayout {
              anchors.fill: parent
              anchors.leftMargin: 6
              anchors.rightMargin: 6
              spacing: 6

              Text {
                text: "📋 ACTIVE MISSIONS"
                color: Qt.rgba(1, 0.3, 0.4, 0.9)
                font.pixelSize: 8
                font.bold: true
                font.family: "monospace"
              }

              Item { Layout.fillWidth: true }

              // Wrap Toggle Pill
              Rectangle {
                height: 14
                width: wrapBadgeText.implicitWidth + 8
                radius: 3
                color: root.tasksWrapAll ? "#ff0838" : Qt.rgba(1, 0.03, 0.22, 0.2)
                border.color: root.tasksWrapAll ? "#ffffff" : Qt.rgba(1, 0.03, 0.22, 0.4)
                border.width: 1

                Text {
                  id: wrapBadgeText
                  anchors.centerIn: parent
                  text: root.tasksWrapAll ? "☰ WRAP ON" : "⋯ EXPAND"
                  color: root.tasksWrapAll ? "#ffffff" : "#ff8899"
                  font.pixelSize: 7
                  font.bold: true
                  font.family: "monospace"
                }

                MouseArea {
                  anchors.fill: parent
                  cursorShape: Qt.PointingHandCursor
                  onClicked: root.tasksWrapAll = !root.tasksWrapAll
                }
              }
            }
          }

          // Mail Mini-Toolbar (Desktop HUD - Mail Tab)
          Rectangle {
            Layout.fillWidth: true
            height: 18
            radius: 4
            visible: root.midLeftTab === "mail"
            color: Qt.rgba(0.12, 0.08, 0.02, 0.5)
            border.color: Qt.rgba(1.0, 0.67, 0.0, 0.25)
            border.width: 1

            RowLayout {
              anchors.fill: parent
              anchors.leftMargin: 6
              anchors.rightMargin: 6
              spacing: 6

              Text {
                text: "✉ GMAIL INBOX"
                color: "#ffaa00"
                font.pixelSize: 8
                font.bold: true
                font.family: "monospace"
              }

              Item { Layout.fillWidth: true }

              Text {
                text: root.mailData && root.mailData.user ? (root.mailData.user.indexOf("@") !== -1 ? root.mailData.user.split("@")[0] : root.mailData.user) : "Offline"
                color: Qt.rgba(1, 1, 1, 0.45)
                font.pixelSize: 7
                font.family: "monospace"
                elide: Text.ElideRight
                Layout.maximumWidth: 90
              }

              Text {
                text: "🔄"
                font.pixelSize: 8
                MouseArea {
                  anchors.fill: parent
                  cursorShape: Qt.PointingHandCursor
                  onClicked: root.mailSync()
                }
              }
            }
          }

          // WhatsApp Mini-Toolbar (Desktop HUD - WhatsApp Tab)
          Rectangle {
            Layout.fillWidth: true
            height: 18
            radius: 4
            visible: root.midLeftTab === "whatsapp"
            color: Qt.rgba(0.02, 0.12, 0.06, 0.5)
            border.color: Qt.rgba(0.15, 0.83, 0.40, 0.25)
            border.width: 1

            RowLayout {
              anchors.fill: parent
              anchors.leftMargin: 6
              anchors.rightMargin: 6
              spacing: 6

              Text {
                text: "💬 WHATSAPP"
                color: "#25d366"
                font.pixelSize: 8
                font.bold: true
                font.family: "monospace"
              }

              Item { Layout.fillWidth: true }

              Text {
                text: root.whatsappData && root.whatsappData.phone ? (root.whatsappData.pushName ? root.whatsappData.pushName : root.whatsappData.phone) : (root.whatsappData && root.whatsappData.status === "ready" ? "Ready" : "Offline")
                color: root.whatsappData && (root.whatsappData.status === "ready" || root.whatsappData.phone) ? "#25d366" : Qt.rgba(1, 1, 1, 0.45)
                font.pixelSize: 7
                font.family: "monospace"
                elide: Text.ElideRight
                Layout.maximumWidth: 90
              }

              Text {
                text: "🔄"
                font.pixelSize: 8
                MouseArea {
                  anchors.fill: parent
                  cursorShape: Qt.PointingHandCursor
                  onClicked: root.whatsappSync()
                }
              }
            }
          }

          // ------------------------------------------------------------------
          // VIEW 1: TASK ITEMS LIST (visible when midLeftTab === "tasks")
          // ------------------------------------------------------------------
          ScrollView {
            Layout.fillWidth: true
            Layout.fillHeight: true
            clip: true
            visible: root.midLeftTab === "tasks"

            ColumnLayout {
              width: scratchpadCard.width - 20
              spacing: 4

              Repeater {
                model: root.todosList
                delegate: Rectangle {
                  id: todoRow
                  required property var modelData
                  required property int index
                  Layout.fillWidth: true
                  property bool isLong: (modelData.text && modelData.text.length > 22)
                  property bool isExpanded: root.tasksWrapAll || (root.expandedDeskTaskIndex === index)
                  height: isExpanded ? Math.max(26, deskTaskText.contentHeight + 10) : 24
                  radius: 5
                  color: isExpanded ? Qt.rgba(1, 0.03, 0.22, modelData.done ? 0.20 : 0.12) : Qt.rgba(1, 0.03, 0.22, modelData.done ? 0.15 : 0.06)
                  border.color: isExpanded ? Qt.rgba(1, 0.03, 0.22, 0.5) : "transparent"
                  border.width: isExpanded ? 1 : 0

                  RowLayout {
                    anchors.fill: parent
                    anchors.leftMargin: 6
                    anchors.rightMargin: 6
                    spacing: 6

                    // Checkbox
                    Rectangle {
                      width: 13; height: 13; radius: 3
                      color: modelData.done ? "#ff0838" : "transparent"
                      border.color: "#ff0838"; border.width: 1
                      Layout.alignment: todoRow.isExpanded ? Qt.AlignTop : Qt.AlignVCenter
                      Layout.topMargin: todoRow.isExpanded ? 4 : 0
                      Text {
                        anchors.centerIn: parent
                        text: "✓"
                        color: "#fff"
                        font.pixelSize: 9
                        visible: modelData.done
                      }
                      MouseArea {
                        anchors.fill: parent
                        cursorShape: Qt.PointingHandCursor
                        onClicked: root.toggleTodo(index)
                      }
                    }

                    // Text
                    Text {
                      id: deskTaskText
                      Layout.fillWidth: true
                      text: modelData.text || ""
                      color: modelData.done ? Qt.rgba(1, 1, 1, 0.4) : "#ffffff"
                      font.strikeout: modelData.done
                      font.pixelSize: 10
                      font.family: "system-ui, sans-serif"
                      wrapMode: todoRow.isExpanded ? Text.Wrap : Text.NoWrap
                      elide: todoRow.isExpanded ? Text.ElideNone : Text.ElideRight

                      MouseArea {
                        anchors.fill: parent
                        cursorShape: Qt.PointingHandCursor
                        onClicked: {
                          if (todoRow.isLong) {
                            root.expandedDeskTaskIndex = (root.expandedDeskTaskIndex === index ? -1 : index)
                          } else {
                            root.toggleTodo(index)
                          }
                        }
                      }
                    }

                    // Expand indicator chevron
                    Text {
                      visible: todoRow.isLong && !root.tasksWrapAll
                      text: todoRow.isExpanded ? "▲" : "▼"
                      color: todoRow.isExpanded ? "#ff0838" : Qt.rgba(1, 1, 1, 0.45)
                      font.pixelSize: 8
                      font.bold: true
                      Layout.alignment: todoRow.isExpanded ? Qt.AlignTop : Qt.AlignVCenter
                      Layout.topMargin: todoRow.isExpanded ? 4 : 0
                      MouseArea {
                        anchors.fill: parent
                        cursorShape: Qt.PointingHandCursor
                        onClicked: {
                          root.expandedDeskTaskIndex = (root.expandedDeskTaskIndex === index ? -1 : index)
                        }
                      }
                    }

                    // Delete button
                    Text {
                      text: "×"
                      color: Qt.rgba(1, 0.2, 0.3, 0.7)
                      font.pixelSize: 12
                      font.bold: true
                      Layout.alignment: todoRow.isExpanded ? Qt.AlignTop : Qt.AlignVCenter
                      Layout.topMargin: todoRow.isExpanded ? 2 : 0
                      MouseArea {
                        anchors.fill: parent
                        cursorShape: Qt.PointingHandCursor
                        onClicked: root.removeTodo(index)
                      }
                    }
                  }
                }
              }
            }
          }

          // ------------------------------------------------------------------
          // VIEW 2: AGENDA ITEMS LIST (visible when midLeftTab === "agenda")
          // ------------------------------------------------------------------
          ScrollView {
            Layout.fillWidth: true
            Layout.fillHeight: true
            clip: true
            visible: root.midLeftTab === "agenda"

            ColumnLayout {
              width: scratchpadCard.width - 20
              spacing: 4

              // Empty state
              Item {
                Layout.fillWidth: true
                height: 48
                visible: root.agendaList.length === 0
                Text {
                  anchors.centerIn: parent
                  text: "No events today"
                  color: Qt.rgba(1, 1, 1, 0.4)
                  font.pixelSize: 9
                  font.family: "monospace"
                }
              }

              Repeater {
                model: root.agendaList
                delegate: Rectangle {
                  id: agendaRow
                  required property var modelData
                  required property int index
                  Layout.fillWidth: true
                  height: 30
                  radius: 5
                  color: modelData.is_active ? Qt.rgba(0, 0.9, 1.0, 0.22) : (modelData.is_past ? Qt.rgba(0.04, 0.06, 0.08, 0.45) : Qt.rgba(0.06, 0.12, 0.16, 0.65))
                  border.color: modelData.is_active ? "#00f0ff" : (modelData.is_past ? Qt.rgba(1, 1, 1, 0.12) : Qt.rgba(0, 0.8, 1.0, 0.22))
                  border.width: modelData.is_active ? 1.5 : 1

                  RowLayout {
                    anchors.fill: parent
                    anchors.leftMargin: 6
                    anchors.rightMargin: 6
                    spacing: 6

                    // Time badge
                    Rectangle {
                      height: 18
                      width: 40
                      radius: 3
                      color: modelData.is_past ? Qt.rgba(0, 0, 0, 0.25) : Qt.rgba(0, 0, 0, 0.45)
                      border.color: modelData.is_past ? Qt.rgba(1, 1, 1, 0.2) : (modelData.color || "#00f0ff")
                      border.width: 1

                      Text {
                        anchors.centerIn: parent
                        text: modelData.event_time || "--:--"
                        color: modelData.is_past ? Qt.rgba(1, 1, 1, 0.4) : (modelData.color || "#00f0ff")
                        font.pixelSize: 9
                        font.bold: true
                        font.family: "monospace"
                      }
                    }

                    // Title & Status
                    ColumnLayout {
                      Layout.fillWidth: true
                      spacing: 1

                      Text {
                        Layout.fillWidth: true
                        text: modelData.title || ""
                        color: modelData.is_past ? Qt.rgba(1, 1, 1, 0.4) : "#ffffff"
                        font.strikeout: modelData.is_past
                        font.pixelSize: 10
                        font.bold: !modelData.is_past
                        font.family: "system-ui, sans-serif"
                        elide: Text.ElideRight
                      }

                      Text {
                        Layout.fillWidth: true
                        text: modelData.status_text || ""
                        color: modelData.is_active ? "#00f0ff" : (modelData.is_past ? Qt.rgba(0, 1.0, 0.5, 0.6) : Qt.rgba(1, 1, 1, 0.45))
                        font.pixelSize: 8
                        font.family: "monospace"
                        elide: Text.ElideRight
                      }
                    }

                    // Delete button
                    Text {
                      text: "×"
                      color: Qt.rgba(1, 0.3, 0.4, 0.7)
                      font.pixelSize: 12
                      font.bold: true
                      MouseArea {
                        anchors.fill: parent
                        cursorShape: Qt.PointingHandCursor
                        onClicked: root.removeAgendaEvent(modelData.id)
                      }
                    }
                  }
                }
              }
            }
          }

          // ------------------------------------------------------------------
          // VIEW 3: GMAIL INBOX LIST (visible when midLeftTab === "mail")
          // ------------------------------------------------------------------
          ScrollView {
            Layout.fillWidth: true
            Layout.fillHeight: true
            clip: true
            visible: root.midLeftTab === "mail"

            ColumnLayout {
              width: scratchpadCard.width - 20
              spacing: 4

              // Empty or Not Configured State
              Item {
                Layout.fillWidth: true
                height: 54
                visible: !root.mailData || !root.mailData.emails || root.mailData.emails.length === 0

                Rectangle {
                  anchors.fill: parent
                  radius: 5
                  color: Qt.rgba(0.08, 0.05, 0.02, 0.55)
                  border.color: (!root.mailData || !root.mailData.user) ? Qt.rgba(1.0, 0.67, 0.0, 0.3) : Qt.rgba(0, 1.0, 0.5, 0.3)
                  border.width: 1

                  ColumnLayout {
                    anchors.centerIn: parent
                    spacing: 2
                    Text {
                      Layout.alignment: Qt.AlignHCenter
                      text: (!root.mailData || !root.mailData.user) ? "✉ GMAIL NOT CONFIGURED" : "✔ INBOX ZERO"
                      color: (!root.mailData || !root.mailData.user) ? "#ffaa00" : "#00ff88"
                      font.pixelSize: 8
                      font.bold: true
                      font.family: "monospace"
                    }
                    Text {
                      Layout.alignment: Qt.AlignHCenter
                      text: (!root.mailData || !root.mailData.user) ? "Click ⛶ or run 'milo-mail setup'" : "All emails read"
                      color: Qt.rgba(1, 1, 1, 0.45)
                      font.pixelSize: 7
                      font.family: "system-ui, sans-serif"
                    }
                  }
                }
              }

              // Email Cards Repeater (Desktop HUD)
              Repeater {
                model: root.mailData && root.mailData.emails ? root.mailData.emails : []
                delegate: Rectangle {
                  id: deskMailRow
                  required property var modelData
                  required property int index
                  Layout.fillWidth: true
                  height: 36
                  radius: 5
                  color: Qt.rgba(0.12, 0.08, 0.02, 0.70)
                  border.color: Qt.rgba(1.0, 0.67, 0.0, 0.25)
                  border.width: 1

                  ColumnLayout {
                    anchors.fill: parent
                    anchors.leftMargin: 6; anchors.rightMargin: 6
                    anchors.topMargin: 3; anchors.bottomMargin: 3
                    spacing: 1

                    RowLayout {
                      Layout.fillWidth: true
                      spacing: 4

                      Text {
                        text: modelData.from || "Unknown"
                        color: "#ffd480"
                        font.pixelSize: 8
                        font.bold: true
                        font.family: "system-ui, sans-serif"
                        elide: Text.ElideRight
                        Layout.maximumWidth: 135
                      }

                      Item { Layout.fillWidth: true }

                      Text {
                        text: modelData.time_rel || ""
                        color: Qt.rgba(1, 1, 1, 0.40)
                        font.pixelSize: 7
                        font.family: "monospace"
                      }
                    }

                    Text {
                      Layout.fillWidth: true
                      text: modelData.subject || "(No Subject)"
                      color: "#ffffff"
                      font.pixelSize: 8
                      font.family: "system-ui, sans-serif"
                      elide: Text.ElideRight
                    }
                  }

                  MouseArea {
                    anchors.fill: parent
                    cursorShape: Qt.PointingHandCursor
                    onClicked: {
                      quickCmdProc.command = ["foot", "-a", "milo-floating", "-T", "MILO // Email #" + modelData.id, root.homeDir + "/.local/bin/milo-mail", "read", modelData.id]
                      quickCmdProc.running = true
                    }
                  }
                }
              }
            }
          }

          // ------------------------------------------------------------------
          // VIEW 4: WHATSAPP CHATS LIST (visible when midLeftTab === "whatsapp")
          // ------------------------------------------------------------------
          ScrollView {
            Layout.fillWidth: true
            Layout.fillHeight: true
            clip: true
            visible: root.midLeftTab === "whatsapp"

            ColumnLayout {
              width: scratchpadCard.width - 20
              spacing: 4

              // Empty or Not Linked State
              Item {
                Layout.fillWidth: true
                height: 54
                visible: !root.whatsappData || !root.whatsappData.chats || root.whatsappData.chats.length === 0

                Rectangle {
                  anchors.fill: parent
                  radius: 5
                  color: Qt.rgba(0.02, 0.08, 0.04, 0.55)
                  border.color: Qt.rgba(0.15, 0.83, 0.40, 0.3)
                  border.width: 1

                  ColumnLayout {
                    anchors.centerIn: parent
                    spacing: 2
                    Text {
                      Layout.alignment: Qt.AlignHCenter
                      text: "💬 NO ACTIVE CHATS"
                      color: "#25d366"
                      font.pixelSize: 8
                      font.bold: true
                      font.family: "monospace"
                    }
                    Text {
                      Layout.alignment: Qt.AlignHCenter
                      text: "Run 'milo wa qr' to link device"
                      color: Qt.rgba(1, 1, 1, 0.45)
                      font.pixelSize: 7
                      font.family: "system-ui, sans-serif"
                    }
                  }
                }
              }

              // WhatsApp Chat Cards Repeater (Desktop HUD)
              Repeater {
                model: root.whatsappData && root.whatsappData.chats ? root.whatsappData.chats : []
                delegate: Rectangle {
                  id: deskWaRow
                  required property var modelData
                  required property int index
                  Layout.fillWidth: true
                  height: 36
                  radius: 5
                  color: Qt.rgba(0.02, 0.10, 0.05, 0.70)
                  border.color: modelData.unread > 0 ? "#25d366" : Qt.rgba(0.15, 0.83, 0.40, 0.25)
                  border.width: modelData.unread > 0 ? 1.5 : 1

                  ColumnLayout {
                    anchors.fill: parent
                    anchors.leftMargin: 6; anchors.rightMargin: 6
                    anchors.topMargin: 3; anchors.bottomMargin: 3
                    spacing: 1

                    RowLayout {
                      Layout.fillWidth: true
                      spacing: 4

                      Text {
                        text: (modelData.is_group ? "👥 " : "👤 ") + (modelData.name || "Unknown")
                        color: modelData.unread > 0 ? "#25d366" : "#a8f5c8"
                        font.pixelSize: 8
                        font.bold: true
                        font.family: "system-ui, sans-serif"
                        elide: Text.ElideRight
                        Layout.maximumWidth: 135
                      }

                      Item { Layout.fillWidth: true }

                      // Unread badge
                      Rectangle {
                        height: 12
                        width: unreadWaBadgeText.implicitWidth + 6
                        radius: 3
                        color: "#25d366"
                        visible: modelData.unread > 0
                        Text {
                          id: unreadWaBadgeText
                          anchors.centerIn: parent
                          text: modelData.unread ? modelData.unread.toString() : ""
                          color: "#060102"
                          font.pixelSize: 7
                          font.bold: true
                          font.family: "monospace"
                        }
                      }

                      Text {
                        text: modelData.time || ""
                        color: Qt.rgba(1, 1, 1, 0.40)
                        font.pixelSize: 7
                        font.family: "monospace"
                      }
                    }

                    Text {
                      Layout.fillWidth: true
                      text: modelData.snippet || "(No message content)"
                      color: "#ffffff"
                      font.pixelSize: 8
                      font.family: "system-ui, sans-serif"
                      elide: Text.ElideRight
                    }
                  }

                  MouseArea {
                    anchors.fill: parent
                    cursorShape: Qt.PointingHandCursor
                    onClicked: root.whatsappReadChat(modelData.index || (index + 1))
                  }
                }
              }
            }
          }

          // ------------------------------------------------------------------
          // INPUT 1: Add Task Row (visible when midLeftTab === "tasks")
          // ------------------------------------------------------------------
          Rectangle {
            id: deskTaskInputContainer
            Layout.fillWidth: true
            height: Math.min(56, Math.max(26, deskTaskInput.contentHeight + 8))
            radius: 5
            color: Qt.rgba(0.12, 0.01, 0.03, 0.85)
            border.color: deskTaskInput.activeFocus ? "#ff0838" : Qt.rgba(1, 0.03, 0.22, 0.4)
            border.width: 1
            visible: root.midLeftTab === "tasks"

            RowLayout {
              anchors.fill: parent
              anchors.leftMargin: 6; anchors.rightMargin: 6
              anchors.topMargin: 4; anchors.bottomMargin: 4
              spacing: 6

              Text {
                text: "+"
                color: "#ff2a55"
                font.pixelSize: 12
                font.bold: true
                Layout.alignment: Qt.AlignTop
              }

              TextEdit {
                id: deskTaskInput
                Layout.fillWidth: true
                Layout.fillHeight: true
                activeFocusOnTab: false
                color: "#ffffff"
                font.pixelSize: 9
                font.family: "system-ui, sans-serif"
                wrapMode: TextEdit.Wrap
                selectByMouse: true
                selectionColor: "#ff0838"

                Keys.priority: Keys.BeforeItem
                Keys.onPressed: function(event) {
                  if (event.key === Qt.Key_Return || event.key === Qt.Key_Enter) {
                    if (!(event.modifiers & Qt.ShiftModifier)) {
                      var val = deskTaskInput.text.trim()
                      if (val.length > 0) {
                        root.addTodo(val)
                        deskTaskInput.text = ""
                      }
                      event.accepted = true
                      return
                    }
                  } else if (event.key === Qt.Key_Escape) {
                    deskTaskInput.focus = false
                    event.accepted = true
                    return
                  } else if (event.key === Qt.Key_Tab || event.key === Qt.Key_Backtab) {
                    var isBack = (event.key === Qt.Key_Backtab || (event.modifiers & Qt.ShiftModifier))
                    if (isBack) {
                      root.midLeftTab = "whatsapp"
                      deskWaFocusScope.forceActiveFocus()
                    } else {
                      root.midLeftTab = "agenda"
                      deskAgendaInput.forceActiveFocus()
                    }
                    event.accepted = true
                    return
                  }
                }

                Text {
                  anchors.fill: parent
                  anchors.topMargin: 1
                  text: "+ Add task & hit Enter..."
                  color: Qt.rgba(1, 1, 1, 0.40)
                  font.pixelSize: 9
                  font.family: "system-ui, sans-serif"
                  visible: !deskTaskInput.text && !deskTaskInput.activeFocus
                }
              }

              // Clear button
              Text {
                text: "×"
                color: Qt.rgba(1, 1, 1, 0.5)
                font.pixelSize: 12
                font.bold: true
                visible: deskTaskInput.text.length > 0
                Layout.alignment: Qt.AlignTop
                MouseArea {
                  anchors.fill: parent
                  cursorShape: Qt.PointingHandCursor
                  onClicked: deskTaskInput.text = ""
                }
              }
            }
          }

          // ------------------------------------------------------------------
          // INPUT 2: Quick Add Agenda Row (visible when midLeftTab === "agenda")
          // ------------------------------------------------------------------
          Rectangle {
            Layout.fillWidth: true
            height: 24; radius: 5
            color: Qt.rgba(0.04, 0.12, 0.16, 0.85)
            border.color: deskAgendaInput.activeFocus ? "#00f0ff" : Qt.rgba(0, 0.8, 1.0, 0.4)
            border.width: 1
            visible: root.midLeftTab === "agenda"

            RowLayout {
              anchors.fill: parent
              anchors.leftMargin: 6; anchors.rightMargin: 6
              spacing: 6

              Text { text: "📅"; font.pixelSize: 10 }

              TextInput {
                id: deskAgendaInput
                Layout.fillWidth: true
                activeFocusOnTab: false
                color: "#ffffff"
                font.pixelSize: 9
                font.family: "system-ui, sans-serif"
                clip: true
                selectByMouse: true
                selectionColor: "#00f0ff"

                Keys.priority: Keys.BeforeItem
                Keys.onPressed: function(event) {
                  if (event.key === Qt.Key_Escape) {
                    deskAgendaInput.focus = false
                    event.accepted = true
                  } else if (event.key === Qt.Key_Tab || event.key === Qt.Key_Backtab) {
                    var isBack = (event.key === Qt.Key_Backtab || (event.modifiers & Qt.ShiftModifier))
                    if (isBack) {
                      root.midLeftTab = "tasks"
                      deskTaskInput.forceActiveFocus()
                    } else {
                      root.midLeftTab = "mail"
                      deskMailFocusScope.forceActiveFocus()
                    }
                    event.accepted = true
                  }
                }

                Text {
                  anchors.fill: parent
                  text: "+ 2pm Meeting & Enter..."
                  color: Qt.rgba(1, 1, 1, 0.40)
                  font.pixelSize: 9
                  font.family: "system-ui, sans-serif"
                  visible: !deskAgendaInput.text && !deskAgendaInput.activeFocus
                }

                onAccepted: {
                  var val = deskAgendaInput.text.trim()
                  if (val.length > 0) {
                    root.addAgendaQuick(val)
                    deskAgendaInput.text = ""
                  }
                }
              }
            }
          }

          // ------------------------------------------------------------------
          // INPUT 3: Quick Action Strip & Mail Focus Scope (visible when midLeftTab === "mail")
          // ------------------------------------------------------------------
          Rectangle {
            id: deskMailFocusScope
            Layout.fillWidth: true
            height: 24; radius: 5
            color: activeFocus ? Qt.rgba(0.14, 0.09, 0.02, 0.95) : Qt.rgba(0.08, 0.05, 0.02, 0.85)
            border.color: activeFocus ? "#ffaa00" : Qt.rgba(1.0, 0.67, 0.0, 0.4)
            border.width: activeFocus ? 1.5 : 1
            visible: root.midLeftTab === "mail"
            focus: root.midLeftTab === "mail"

            Keys.priority: Keys.BeforeItem
            Keys.onPressed: function(event) {
              if (event.key === Qt.Key_Tab || event.key === Qt.Key_Backtab) {
                var isBack = (event.key === Qt.Key_Backtab || (event.modifiers & Qt.ShiftModifier))
                if (isBack) {
                  root.midLeftTab = "agenda"
                  deskAgendaInput.forceActiveFocus()
                } else {
                  root.midLeftTab = "whatsapp"
                  deskWaFocusScope.forceActiveFocus()
                }
                event.accepted = true
              } else if (event.key === Qt.Key_Escape) {
                deskMailFocusScope.focus = false
                event.accepted = true
              } else if (event.key === Qt.Key_Return || event.key === Qt.Key_Enter) {
                root.mailSummarize()
                event.accepted = true
              } else if (event.key === Qt.Key_R && (event.modifiers & Qt.ControlModifier)) {
                root.mailSync()
                event.accepted = true
              }
            }

            RowLayout {
              anchors.fill: parent
              anchors.leftMargin: 6; anchors.rightMargin: 6
              spacing: 5

              // 🎙 AI Briefing Button
              Rectangle {
                Layout.fillWidth: true
                height: 18; radius: 3
                color: Qt.rgba(1.0, 0.67, 0.0, 0.15)
                border.color: Qt.rgba(1.0, 0.67, 0.0, 0.3)
                border.width: 1
                RowLayout {
                  anchors.centerIn: parent
                  spacing: 3
                  Text { text: "🎙"; font.pixelSize: 8 }
                  Text {
                    text: "AI BRIEF"
                    color: "#ffd480"
                    font.pixelSize: 8
                    font.bold: true
                    font.family: "monospace"
                  }
                }
                MouseArea {
                  anchors.fill: parent
                  cursorShape: Qt.PointingHandCursor
                  onClicked: root.mailSummarize()
                }
              }

              // 🔄 Sync Button
              Rectangle {
                width: 22; height: 18; radius: 3
                color: Qt.rgba(1.0, 0.67, 0.0, 0.15)
                border.color: Qt.rgba(1.0, 0.67, 0.0, 0.3)
                border.width: 1
                Text {
                  anchors.centerIn: parent
                  text: "🔄"
                  font.pixelSize: 8
                }
                MouseArea {
                  anchors.fill: parent
                  cursorShape: Qt.PointingHandCursor
                  onClicked: root.mailSync()
                }
              }

              // 🌐 Open Webmail
              Rectangle {
                width: 22; height: 18; radius: 3
                color: Qt.rgba(1.0, 0.67, 0.0, 0.15)
                border.color: Qt.rgba(1.0, 0.67, 0.0, 0.3)
                border.width: 1
                Text {
                  anchors.centerIn: parent
                  text: "🌐"
                  font.pixelSize: 8
                }
                MouseArea {
                  anchors.fill: parent
                  cursorShape: Qt.PointingHandCursor
                  onClicked: root.mailOpenWeb()
                }
              }
            }
          }

          // ------------------------------------------------------------------
          // INPUT 4: Quick Action Strip & WhatsApp Focus Scope (visible when midLeftTab === "whatsapp")
          // ------------------------------------------------------------------
          Rectangle {
            id: deskWaFocusScope
            Layout.fillWidth: true
            height: 24; radius: 5
            color: activeFocus ? Qt.rgba(0.04, 0.16, 0.08, 0.95) : Qt.rgba(0.02, 0.10, 0.05, 0.85)
            border.color: activeFocus ? "#25d366" : Qt.rgba(0.15, 0.83, 0.40, 0.4)
            border.width: activeFocus ? 1.5 : 1
            visible: root.midLeftTab === "whatsapp"
            focus: root.midLeftTab === "whatsapp"

            Keys.priority: Keys.BeforeItem
            Keys.onPressed: function(event) {
              if (event.key === Qt.Key_Tab || event.key === Qt.Key_Backtab) {
                var isBack = (event.key === Qt.Key_Backtab || (event.modifiers & Qt.ShiftModifier))
                if (isBack) {
                  root.midLeftTab = "mail"
                  deskMailFocusScope.forceActiveFocus()
                } else {
                  root.midLeftTab = "tasks"
                  deskTaskInput.forceActiveFocus()
                }
                event.accepted = true
              } else if (event.key === Qt.Key_Escape) {
                deskWaFocusScope.focus = false
                event.accepted = true
              } else if (event.key === Qt.Key_Return || event.key === Qt.Key_Enter) {
                root.whatsappSummarize()
                event.accepted = true
              } else if (event.key === Qt.Key_R && (event.modifiers & Qt.ControlModifier)) {
                root.whatsappSync()
                event.accepted = true
              }
            }

            RowLayout {
              anchors.fill: parent
              anchors.leftMargin: 6; anchors.rightMargin: 6
              spacing: 5

              // 🎙 AI Briefing Button
              Rectangle {
                Layout.fillWidth: true
                height: 18; radius: 3
                color: Qt.rgba(0.15, 0.83, 0.40, 0.15)
                border.color: Qt.rgba(0.15, 0.83, 0.40, 0.3)
                border.width: 1
                RowLayout {
                  anchors.centerIn: parent
                  spacing: 3
                  Text { text: "🎙"; font.pixelSize: 8 }
                  Text {
                    text: "AI BRIEF"
                    color: "#25d366"
                    font.pixelSize: 8
                    font.bold: true
                    font.family: "monospace"
                  }
                }
                MouseArea {
                  anchors.fill: parent
                  cursorShape: Qt.PointingHandCursor
                  onClicked: root.whatsappSummarize()
                }
              }

              // 📱 QR Link Button
              Rectangle {
                width: 48; height: 18; radius: 3
                color: Qt.rgba(1, 1, 1, 0.06)
                border.color: Qt.rgba(1, 1, 1, 0.15)
                border.width: 1
                Text {
                  anchors.centerIn: parent
                  text: "📱 QR"
                  color: Qt.rgba(1, 1, 1, 0.7)
                  font.pixelSize: 8
                  font.family: "monospace"
                }
                MouseArea {
                  anchors.fill: parent
                  cursorShape: Qt.PointingHandCursor
                  onClicked: root.whatsappLinkQR()
                }
              }

              // 🔄 Sync Button
              Rectangle {
                width: 22; height: 18; radius: 3
                color: Qt.rgba(1, 1, 1, 0.06)
                border.color: Qt.rgba(1, 1, 1, 0.15)
                border.width: 1
                Text {
                  anchors.centerIn: parent
                  text: "🔄"
                  color: "#ffffff"
                  font.pixelSize: 8
                }
                MouseArea {
                  anchors.fill: parent
                  cursorShape: Qt.PointingHandCursor
                  onClicked: root.whatsappSync()
                }
              }
            }
          }
        }

        // Floating Live Typing Preview for Long Tasks in Desktop HUD
        Rectangle {
          id: deskTaskTypingOverlay
          z: 99
          visible: root.midLeftTab === "tasks" && deskTaskInput.activeFocus && deskTaskInput.text.trim().length > 18
          anchors.bottom: parent.bottom
          anchors.bottomMargin: deskTaskInputContainer.height + 14
          anchors.left: parent.left
          anchors.leftMargin: 8
          anchors.right: parent.right
          anchors.rightMargin: 8
          height: Math.min(130, deskTypingCol.implicitHeight + 16)
          radius: 7
          color: Qt.rgba(0.07, 0.01, 0.02, 0.96)
          border.color: "#ff0838"
          border.width: 1.2
          clip: true

          ColumnLayout {
            id: deskTypingCol
            anchors.fill: parent
            anchors.margins: 8
            spacing: 4

            RowLayout {
              Layout.fillWidth: true
              Text {
                text: "✦ TYPING PREVIEW"
                color: "#ff2a55"
                font.pixelSize: 8
                font.bold: true
                font.family: "monospace"
              }
              Item { Layout.fillWidth: true }
              Text {
                text: {
                  var words = deskTaskInput.text.trim().split(/\s+/).filter(Boolean).length
                  return words + " w · " + deskTaskInput.text.length + " ch"
                }
                color: Qt.rgba(1, 1, 1, 0.6)
                font.pixelSize: 8
                font.family: "monospace"
              }
            }

            ScrollView {
              Layout.fillWidth: true
              Layout.fillHeight: true
              clip: true

              Text {
                width: deskTypingCol.width
                text: deskTaskInput.text
                color: "#ffffff"
                font.pixelSize: 10
                font.family: "system-ui, sans-serif"
                wrapMode: Text.Wrap
              }
            }

            Text {
              text: "↵ Enter to add · ⎋ Esc to unfocus"
              color: Qt.rgba(1, 1, 1, 0.35)
              font.pixelSize: 7
              font.family: "monospace"
            }
          }
        }
      }

      // ----------------------------------------------------------------------
      // 5.5 BOTTOM-LEFT: SATELLITE UPLINK & THREAT MATRIX
      // ----------------------------------------------------------------------
      Rectangle {
        id: uplinkCard
        x: 35
        anchors.bottom: parent.bottom
        anchors.bottomMargin: 35
        width: 225; height: 158
        radius: 14
        color: Qt.rgba(0.06, 0.01, 0.02, 0.85)
        border.color: Qt.rgba(1.0, 0.03, 0.22, 0.45)
        border.width: 1.2

        ColumnLayout {
          anchors.fill: parent
          anchors.margins: 12
          spacing: 5

          RowLayout {
            Layout.fillWidth: true
            Text {
              text: "✦ SATELLITE UPLINK"
              color: "#ff2a55"
              font.pixelSize: 11
              font.bold: true
              font.family: "monospace"
            }
            Item { Layout.fillWidth: true }
            Rectangle {
              width: 8; height: 8; radius: 4; color: "#00ff88"
              SequentialAnimation on opacity {
                loops: Animation.Infinite
                PropertyAnimation { to: 0.3; duration: 900; easing.type: Easing.InOutQuad }
                PropertyAnimation { to: 1.0; duration: 900; easing.type: Easing.InOutQuad }
              }
            }
          }

          Text {
            text: "NET: " + root.uplinkNet; color: "#ffffff"; font.pixelSize: 10; font.family: "monospace"; elide: Text.ElideRight; Layout.fillWidth: true
            MouseArea {
              anchors.fill: parent; cursorShape: Qt.PointingHandCursor
              onClicked: {
                quickCmdProc.command = ["foot", "-a", "milo-floating", "-T", "Satellite Uplink // Network Matrix", "-e", "nmtui"]
                quickCmdProc.running = true
                root.triggerShockwave()
              }
            }
          }
          Text {
            text: "LOC: MILO TACTICAL NODE // LOCAL SECTOR"; color: Qt.rgba(0, 0.95, 1, 0.7); font.pixelSize: 10; font.family: "monospace"
            MouseArea {
              anchors.fill: parent; cursorShape: Qt.PointingHandCursor
              onClicked: {
                quickCmdProc.command = ["foot", "-a", "milo-floating", "-T", "Satellite Uplink // IP & Route Matrix", "-e", "sh", "-c", "ip addr show scope global; echo ''; ip route; echo ''; read -p 'Press Enter to dismiss...'"]
                quickCmdProc.running = true
                root.triggerShockwave()
              }
            }
          }
          Text {
            text: "STATUS: " + root.uplinkThreat; color: "#ff0838"; font.pixelSize: 10; font.bold: true; font.family: "monospace"
            MouseArea {
              anchors.fill: parent; cursorShape: Qt.PointingHandCursor
              onClicked: {
                quickCmdProc.command = ["foot", "-a", "milo-floating", "-T", "Threat Matrix // Security Audit", "-e", "sh", "-c", "echo '=== MILO THREAT MATRIX SECURITY AUDIT ==='; ss -tuln; echo ''; ip addr show scope global; echo ''; read -p 'Press Enter to dismiss...'"]
                quickCmdProc.running = true
                root.triggerShockwave()
              }
            }
          }
          Text {
            text: "UPTIME: " + root.uplinkUptime + " · 0 ERRORS"; color: Qt.rgba(1, 1, 1, 0.5); font.pixelSize: 9; font.family: "monospace"
            MouseArea {
              anchors.fill: parent; cursorShape: Qt.PointingHandCursor
              onClicked: {
                quickCmdProc.command = ["foot", "-a", "milo-floating", "-T", "Subsystem Journal // System Errors", "-e", "journalctl", "-p", "3", "-xb"]
                quickCmdProc.running = true
                root.triggerShockwave()
              }
            }
          }
          Text {
            text: "PHONE: " + root.phoneModel + " · " + root.phoneBattery
            color: root.phoneStatus.indexOf("Active") !== -1 ? "#00ffcc" : Qt.rgba(1, 1, 1, 0.7)
            font.pixelSize: 10
            font.family: "monospace"
            elide: Text.ElideRight
            Layout.fillWidth: true
            MouseArea {
              anchors.fill: parent; cursorShape: Qt.PointingHandCursor
              onClicked: {
                quickCmdProc.command = ["foot", "-a", "milo-floating", "-T", "MILO // Phone Companion Hub", "/home/jeffy/.local/bin/milo-phone"]
                quickCmdProc.running = true
                root.triggerShockwave()
              }
            }
          }
        }
      }

      // ----------------------------------------------------------------------
      // 5.55 TOP-CENTER: FLOATING GAME MODE MATRIX BANNER
      // ----------------------------------------------------------------------
      Rectangle {
        id: gameModeBanner
        visible: root.gameModeActive
        anchors.top: parent.top
        anchors.topMargin: 52
        anchors.horizontalCenter: parent.horizontalCenter
        height: 28
        width: gameModeRow.implicitWidth + 24
        radius: 14
        color: Qt.rgba(0.01, 0.08, 0.04, 0.94)
        border.color: "#00ff88"
        border.width: 1.5

        RowLayout {
          id: gameModeRow
          anchors.centerIn: parent
          spacing: 8

          Rectangle {
            width: 8; height: 8; radius: 4
            color: "#00ff88"
            SequentialAnimation on opacity {
              running: root.gameModeActive
              loops: Animation.Infinite
              PropertyAnimation { to: 0.2; duration: 450 }
              PropertyAnimation { to: 1.0; duration: 450 }
            }
          }

          Text {
            text: "🎮 MILO GAME MODE ACTIVE // VRAM: " + root.gameVramFree + " FREE"
            color: "#00ff88"
            font.pixelSize: 10
            font.bold: true
            font.family: "monospace"
            font.letterSpacing: 1.1
          }

          Rectangle {
            height: 16; width: toggleOffText.implicitWidth + 10; radius: 8
            color: Qt.rgba(0, 1, 0.53, 0.25)
            border.color: "#00ff88"; border.width: 1
            Text {
              id: toggleOffText
              anchors.centerIn: parent
              text: "DEACTIVATE"
              color: "#ffffff"
              font.pixelSize: 8
              font.bold: true
              font.family: "monospace"
            }
          }
        }

        MouseArea {
          anchors.fill: parent; cursorShape: Qt.PointingHandCursor
          onClicked: {
            quickCmdProc.command = ["/home/jeffy/.local/bin/milo-game", "off"]
            quickCmdProc.running = true
            root.triggerShockwave()
          }
        }
      }

      // ----------------------------------------------------------------------
      // 5.6 TOP-RIGHT: MILO HARDWARE TELEMETRY GAUGES
      // ----------------------------------------------------------------------
      Rectangle {
        id: telemetryCard
        anchors.top: parent.top
        anchors.topMargin: 52
        anchors.right: parent.right
        anchors.rightMargin: 35
        width: 250; height: 215
        radius: 14
        color: Qt.rgba(0.06, 0.01, 0.02, 0.85)
        border.color: root.gameModeActive ? "#00ff88" : Qt.rgba(1.0, 0.03, 0.22, 0.45)
        border.width: 1.2

        ColumnLayout {
          anchors.fill: parent
          anchors.margins: 12
          spacing: 8

          RowLayout {
            Layout.fillWidth: true
            Text {
              text: "✦ HARDWARE TELEMETRY"
              color: "#ff2a55"
              font.pixelSize: 11
              font.bold: true
              font.family: "monospace"
            }
            Item { Layout.fillWidth: true }
            Text {
              text: root.cpuGhzText
              color: "#ffffff"
              font.pixelSize: 10
              font.bold: true
              font.family: "monospace"
              MouseArea {
                anchors.fill: parent; cursorShape: Qt.PointingHandCursor
                onClicked: {
                  quickCmdProc.command = ["foot", "-a", "milo-floating", "-T", "MILO // CPU Frequency & Topology", "-e", "sh", "-c", "lscpu; echo ''; read -p 'Press Enter to dismiss...'"]
                  quickCmdProc.running = true
                  root.triggerShockwave()
                }
              }
            }
          }

          // RAM Gauge Row
          RowLayout {
            spacing: 8
            Text { text: "RAM"; color: "#ff2a55"; font.pixelSize: 10; font.bold: true; font.family: "monospace"; Layout.preferredWidth: 32 }
            Rectangle {
              Layout.fillWidth: true
              height: 7; radius: 3.5
              color: "#180306"
              border.color: Qt.rgba(1, 0.03, 0.22, 0.4); border.width: 1
              Rectangle {
                height: parent.height
                width: Math.max(4, parent.width * root.memPercent)
                radius: 3.5
                color: "#ff0838"
              }
            }
            Text { text: root.memText; color: "#ffffff"; font.pixelSize: 10; font.family: "monospace" }
            MouseArea {
              anchors.fill: parent; cursorShape: Qt.PointingHandCursor
              onClicked: {
                quickCmdProc.command = ["foot", "-a", "milo-floating", "-T", "MILO // Memory Matrix", "-e", "btop"]
                quickCmdProc.running = true
                root.triggerShockwave()
              }
            }
          }

          // DISK Row
          RowLayout {
            spacing: 8
            Text { text: "DISK"; color: "#ff2a55"; font.pixelSize: 10; font.bold: true; font.family: "monospace"; Layout.preferredWidth: 32 }
            Rectangle {
              Layout.fillWidth: true
              height: 7; radius: 3.5
              color: "#180306"
              border.color: Qt.rgba(1, 0.03, 0.22, 0.4); border.width: 1
              Rectangle {
                height: parent.height
                width: Math.max(4, parent.width * root.diskPercent)
                radius: 3.5
                color: "#ff2a55"
              }
            }
            Text { text: root.diskFreeText + " FREE"; color: "#ffffff"; font.pixelSize: 10; font.family: "monospace" }
            MouseArea {
              anchors.fill: parent; cursorShape: Qt.PointingHandCursor
              onClicked: {
                quickCmdProc.command = ["/home/jeffy/.local/bin/milo-files"]
                quickCmdProc.running = true
                root.triggerShockwave()
              }
            }
          }

          // GPU / Game Mode Telemetry Row
          RowLayout {
            spacing: 8
            Text {
              text: "GPU"
              color: root.gameModeActive ? "#00ff88" : "#ff2a55"
              font.pixelSize: 10
              font.bold: true
              font.family: "monospace"
              Layout.preferredWidth: 32
            }
            Rectangle {
              Layout.fillWidth: true
              height: 18; radius: 4
              color: root.gameModeActive ? Qt.rgba(0, 1, 0.53, 0.15) : Qt.rgba(1, 0.03, 0.22, 0.15)
              border.color: root.gameModeActive ? "#00ff88" : Qt.rgba(1, 0.03, 0.22, 0.4)
              border.width: 1

              RowLayout {
                anchors.centerIn: parent
                spacing: 6
                Rectangle {
                  width: 6; height: 6; radius: 3
                  color: root.gameModeActive ? "#00ff88" : "#ff0838"
                  SequentialAnimation on opacity {
                    running: root.gameModeActive
                    loops: Animation.Infinite
                    PropertyAnimation { to: 0.3; duration: 500 }
                    PropertyAnimation { to: 1.0; duration: 500 }
                  }
                }
                Text {
                  text: root.gameModeActive ? "🎮 " + root.gameVramFree + " FREE" : "GTX 970M · 3GB"
                  color: root.gameModeActive ? "#00ff88" : "#ffffff"
                  font.pixelSize: 9
                  font.bold: true
                  font.family: "monospace"
                }
              }

              MouseArea {
                anchors.fill: parent; cursorShape: Qt.PointingHandCursor
                onClicked: {
                  quickCmdProc.command = ["/home/jeffy/.local/bin/milo-game", "toggle"]
                  quickCmdProc.running = true
                  root.triggerShockwave()
                }
              }
            }
          }

          // Compositor FPS
          RowLayout {
            spacing: 8
            Text { text: "COMP"; color: "#ff2a55"; font.pixelSize: 10; font.bold: true; font.family: "monospace"; Layout.preferredWidth: 32 }
            Text { text: "60 FPS WAYLAND HARDWARE RENDER"; color: "#ffffff"; font.pixelSize: 9; font.family: "monospace" }
            MouseArea {
              anchors.fill: parent; cursorShape: Qt.PointingHandCursor
              onClicked: {
                quickCmdProc.command = ["foot", "-a", "milo-floating", "-T", "MILO // Hyprland Compositor State", "-e", "sh", "-c", "hyprctl systeminfo; echo ''; hyprctl monitors; echo ''; read -p 'Press Enter to dismiss...'"]
                quickCmdProc.running = true
                root.triggerShockwave()
              }
            }
          }

          // Thermal status
          Rectangle {
            Layout.fillWidth: true; height: 22; radius: 4
            color: Qt.rgba(0.12, 0.01, 0.03, 0.85)
            border.color: "#ff0838"; border.width: 1
            RowLayout {
              anchors.centerIn: parent
              spacing: 8
              Rectangle { width: 6; height: 6; radius: 3; color: "#00ff88" }
              Text { text: "ALL SYSTEM CORES NOMINAL"; color: "#ffffff"; font.pixelSize: 9; font.bold: true; font.family: "monospace" }
            }
            MouseArea {
              anchors.fill: parent; cursorShape: Qt.PointingHandCursor
              onClicked: {
                quickCmdProc.command = ["foot", "-a", "milo-floating", "-T", "MILO // System Diagnostics", "-e", "btop"]
                quickCmdProc.running = true
                root.triggerShockwave()
              }
            }
          }
        }
      }

      // ----------------------------------------------------------------------
      // 5.7 MID-RIGHT: MILO CYBER AUDIO HUB (Spinning Disc & Keyboard Controls)
      // ----------------------------------------------------------------------
      Rectangle {
        id: mediaCard
        anchors.verticalCenter: parent.verticalCenter
        anchors.right: parent.right
        anchors.rightMargin: 35
        width: 250; height: 185
        radius: 14
        color: Qt.rgba(0.06, 0.01, 0.02, 0.85)
        border.color: mediaCard.activeFocus ? "#ff0838" : (mediaCardHover.containsMouse ? Qt.rgba(1.0, 0.25, 0.35, 0.6) : Qt.rgba(1.0, 0.03, 0.22, 0.45))
        border.width: mediaCard.activeFocus ? 1.5 : 1.2

        focus: true

        MouseArea {
          id: mediaCardHover
          anchors.fill: parent
          hoverEnabled: true
          onClicked: {
            mediaCard.forceActiveFocus()
          }
        }

        Keys.priority: Keys.BeforeItem
        Keys.onPressed: function(event) {
          if (event.key === Qt.Key_Space || event.key === Qt.Key_K) {
            root.musicPlayPause()
            event.accepted = true
          } else if (event.key === Qt.Key_Right || event.key === Qt.Key_L || event.key === Qt.Key_N) {
            root.musicNext()
            event.accepted = true
          } else if (event.key === Qt.Key_Left || event.key === Qt.Key_H || event.key === Qt.Key_P) {
            root.musicPrev()
            event.accepted = true
          } else if (event.key === Qt.Key_Return || event.key === Qt.Key_Enter || event.key === Qt.Key_M) {
            root.musicPick()
            event.accepted = true
          } else if (event.key === Qt.Key_T) {
            root.musicTui()
            event.accepted = true
          } else if (event.key === Qt.Key_S) {
            quickCmdProc.command = [root.homeDir + "/.local/bin/milo-music", "shuffle"]
            quickCmdProc.running = true
            root.triggerShockwave()
            event.accepted = true
          } else if (event.key === Qt.Key_Escape) {
            mediaCard.focus = false
            event.accepted = true
          }
        }

        ColumnLayout {
          anchors.fill: parent
          anchors.margins: 12
          spacing: 7

          RowLayout {
            Layout.fillWidth: true
            Text {
              text: "✦ MILO CYBER SOUNDTRACK"
              color: "#ff2a55"
              font.pixelSize: 11
              font.bold: true
              font.family: "monospace"
            }
            Item { Layout.fillWidth: true }
            Rectangle {
              height: 16
              width: hotkeyIndicatorText.implicitWidth + 8
              radius: 3
              color: mediaCard.activeFocus ? "#ff0838" : Qt.rgba(1, 0.03, 0.22, 0.15)
              border.color: mediaCard.activeFocus ? "#ffffff" : Qt.rgba(1, 0.03, 0.22, 0.35)
              border.width: 1
              Text {
                id: hotkeyIndicatorText
                anchors.centerIn: parent
                text: mediaCard.activeFocus ? "⌨ HOTKEYS" : "FLAC 24-BIT"
                color: mediaCard.activeFocus ? "#ffffff" : Qt.rgba(1, 1, 1, 0.45)
                font.pixelSize: 8
                font.bold: mediaCard.activeFocus
                font.family: "monospace"
              }
            }
          }

          RowLayout {
            spacing: 12
            Layout.fillWidth: true

            // Rotating Vinyl Disc (Click to open Repulsor Audio HUD)
            Item {
              width: 52; height: 52
              Rectangle {
                anchors.fill: parent; radius: 26
                color: "#110204"
                border.color: vinylMouseArea.containsMouse ? "#ff4060" : "#ff0838"; border.width: 1.5

                Repeater {
                  model: 3
                  Rectangle {
                    anchors.centerIn: parent
                    width: (index + 1) * 12; height: (index + 1) * 12
                    radius: width / 2
                    color: "transparent"
                    border.color: Qt.rgba(1, 0.03, 0.22, 0.3)
                    border.width: 1
                  }
                }

                Rectangle {
                  anchors.centerIn: parent
                  width: 12; height: 12; radius: 6
                  color: vinylMouseArea.containsMouse ? "#ffffff" : "#ff0838"
                }

                RotationAnimation on rotation {
                  loops: Animation.Infinite
                  from: 0; to: 360
                  duration: 6000
                  running: root.isPlaying
                }
              }

              MouseArea {
                id: vinylMouseArea
                anchors.fill: parent
                hoverEnabled: true
                cursorShape: Qt.PointingHandCursor
                onClicked: {
                  mediaCard.forceActiveFocus()
                  root.musicTui()
                }
              }
            }

            ColumnLayout {
              Layout.fillWidth: true
              spacing: 3

              Item {
                Layout.fillWidth: true
                Layout.preferredHeight: 34

                ColumnLayout {
                  anchors.fill: parent
                  spacing: 2
                  Text {
                    text: root.mediaTitle
                    color: titleMouseArea.containsMouse ? "#ff4060" : "#ffffff"
                    font.pixelSize: 12
                    font.bold: true
                    elide: Text.ElideRight
                    Layout.fillWidth: true
                  }
                  Text {
                    text: root.mediaArtist
                    color: titleMouseArea.containsMouse ? Qt.rgba(1, 1, 1, 0.9) : Qt.rgba(1, 1, 1, 0.6)
                    font.pixelSize: 10
                    elide: Text.ElideRight
                    Layout.fillWidth: true
                  }
                }

                MouseArea {
                  id: titleMouseArea
                  anchors.fill: parent
                  hoverEnabled: true
                  cursorShape: Qt.PointingHandCursor
                  onClicked: {
                    mediaCard.forceActiveFocus()
                    root.musicPick()
                  }
                }
              }

              // Animated Equalizer Waveform Bars & Shortcuts Hint
              RowLayout {
                Layout.fillWidth: true
                spacing: 6

                Row {
                  spacing: 3
                  Repeater {
                    model: 5
                    Rectangle {
                      width: 3
                      radius: 1.5
                      color: root.isPlaying ? "#ff0838" : Qt.rgba(1, 0.03, 0.22, 0.3)
                      height: root.isPlaying ? 10 : 4
                      SequentialAnimation on height {
                        loops: Animation.Infinite
                        running: root.isPlaying
                        PropertyAnimation { to: 4 + (index * 3); duration: 250 + (index * 80) }
                        PropertyAnimation { to: 14 - (index * 2); duration: 250 + (index * 80) }
                      }
                    }
                  }
                }

                Item { Layout.fillWidth: true }

                Text {
                  text: "⏎ Pick · T Tui · S Shuf"
                  color: Qt.rgba(1, 1, 1, 0.32)
                  font.pixelSize: 8
                  font.family: "monospace"
                }
              }
            }
          }

          // Media Controls (⏮ ⏯ ⏭) with Hotkey Indicators
          RowLayout {
            Layout.fillWidth: true
            spacing: 6

            Rectangle {
              Layout.fillWidth: true; height: 30; radius: 5
              color: prevMouseArea.containsMouse ? Qt.rgba(1, 0.03, 0.22, 0.35) : Qt.rgba(1, 0.03, 0.22, 0.15)
              border.color: Qt.rgba(1, 0.03, 0.22, 0.4); border.width: 1
              ColumnLayout {
                anchors.centerIn: parent
                spacing: 1
                Text { Layout.alignment: Qt.AlignHCenter; text: "⏮"; color: "#fff"; font.pixelSize: 10 }
                Text { Layout.alignment: Qt.AlignHCenter; text: "Alt+←"; color: Qt.rgba(1, 1, 1, 0.45); font.pixelSize: 7; font.family: "monospace" }
              }
              MouseArea {
                id: prevMouseArea
                anchors.fill: parent; cursorShape: Qt.PointingHandCursor
                hoverEnabled: true
                onClicked: {
                  mediaCard.forceActiveFocus()
                  root.musicPrev()
                }
              }
            }

            Rectangle {
              Layout.fillWidth: true; height: 30; radius: 5
              color: playMouseArea.containsMouse ? Qt.rgba(1, 0.03, 0.22, 0.45) : Qt.rgba(1, 0.03, 0.22, 0.25)
              border.color: "#ff0838"; border.width: 1
              ColumnLayout {
                anchors.centerIn: parent
                spacing: 1
                Text { Layout.alignment: Qt.AlignHCenter; text: root.isPlaying ? "⏸" : "▶"; color: "#fff"; font.pixelSize: 10 }
                Text { Layout.alignment: Qt.AlignHCenter; text: "Alt+Space"; color: Qt.rgba(1, 1, 1, 0.55); font.pixelSize: 7; font.family: "monospace" }
              }
              MouseArea {
                id: playMouseArea
                anchors.fill: parent; cursorShape: Qt.PointingHandCursor
                hoverEnabled: true
                onClicked: {
                  mediaCard.forceActiveFocus()
                  root.musicPlayPause()
                }
              }
            }

            Rectangle {
              Layout.fillWidth: true; height: 30; radius: 5
              color: nextMouseArea.containsMouse ? Qt.rgba(1, 0.03, 0.22, 0.35) : Qt.rgba(1, 0.03, 0.22, 0.15)
              border.color: Qt.rgba(1, 0.03, 0.22, 0.4); border.width: 1
              ColumnLayout {
                anchors.centerIn: parent
                spacing: 1
                Text { Layout.alignment: Qt.AlignHCenter; text: "⏭"; color: "#fff"; font.pixelSize: 10 }
                Text { Layout.alignment: Qt.AlignHCenter; text: "Alt+→"; color: Qt.rgba(1, 1, 1, 0.45); font.pixelSize: 7; font.family: "monospace" }
              }
              MouseArea {
                id: nextMouseArea
                anchors.fill: parent; cursorShape: Qt.PointingHandCursor
                hoverEnabled: true
                onClicked: {
                  mediaCard.forceActiveFocus()
                  root.musicNext()
                }
              }
            }
          }
        }
      }

      // ----------------------------------------------------------------------
      // 5.8 BOTTOM-RIGHT: HEXAGONAL MILO ARSENAL QUICK LAUNCHER
      // ----------------------------------------------------------------------
      Rectangle {
        id: arsenalCard
        anchors.bottom: parent.bottom
        anchors.bottomMargin: 35
        anchors.right: parent.right
        anchors.rightMargin: 35
        width: 250; height: 130
        radius: 14
        color: Qt.rgba(0.06, 0.01, 0.02, 0.85)
        border.color: Qt.rgba(1.0, 0.03, 0.22, 0.45)
        border.width: 1.2

        ColumnLayout {
          anchors.fill: parent
          anchors.margins: 10
          spacing: 6

          RowLayout {
            Layout.fillWidth: true
            Text {
              text: "✦ MILO ARSENAL"
              color: "#ff2a55"
              font.pixelSize: 11
              font.bold: true
              font.family: "monospace"
            }
            Item { Layout.fillWidth: true }
            Text {
              text: "QUICK LAUNCH"
              color: Qt.rgba(0, 0.95, 1, 0.7)
              font.pixelSize: 9
              font.family: "monospace"
            }
          }

          GridLayout {
            columns: 3
            Layout.fillWidth: true
            columnSpacing: 6
            rowSpacing: 6

            // Files
            Rectangle {
              Layout.fillWidth: true; height: 36; radius: 6
              color: Qt.rgba(1, 0.03, 0.22, 0.14)
              border.color: Qt.rgba(1, 0.03, 0.22, 0.4); border.width: 1
              ColumnLayout {
                anchors.centerIn: parent; spacing: 1
                Text { Layout.alignment: Qt.AlignHCenter; text: "📁"; font.pixelSize: 12 }
                Text { Layout.alignment: Qt.AlignHCenter; text: "FILES"; color: "#fff"; font.pixelSize: 8; font.bold: true }
              }
              MouseArea {
                anchors.fill: parent; cursorShape: Qt.PointingHandCursor
                onClicked: { quickCmdProc.command = ["/home/jeffy/.local/bin/milo-files"]; quickCmdProc.running = true; root.triggerShockwave() }
              }
            }

            // Terminal
            Rectangle {
              Layout.fillWidth: true; height: 36; radius: 6
              color: Qt.rgba(1, 0.03, 0.22, 0.14)
              border.color: Qt.rgba(1, 0.03, 0.22, 0.4); border.width: 1
              ColumnLayout {
                anchors.centerIn: parent; spacing: 1
                Text { Layout.alignment: Qt.AlignHCenter; text: "⚡"; font.pixelSize: 12 }
                Text { Layout.alignment: Qt.AlignHCenter; text: "TERMINAL"; color: "#fff"; font.pixelSize: 8; font.bold: true }
              }
              MouseArea {
                anchors.fill: parent; cursorShape: Qt.PointingHandCursor
                onClicked: { quickCmdProc.command = ["foot"]; quickCmdProc.running = true; root.triggerShockwave() }
              }
            }

            // Browser
            Rectangle {
              Layout.fillWidth: true; height: 36; radius: 6
              color: Qt.rgba(1, 0.03, 0.22, 0.14)
              border.color: Qt.rgba(1, 0.03, 0.22, 0.4); border.width: 1
              ColumnLayout {
                anchors.centerIn: parent; spacing: 1
                Text { Layout.alignment: Qt.AlignHCenter; text: "🌐"; font.pixelSize: 12 }
                Text { Layout.alignment: Qt.AlignHCenter; text: "BROWSER"; color: "#fff"; font.pixelSize: 8; font.bold: true }
              }
              MouseArea {
                anchors.fill: parent; cursorShape: Qt.PointingHandCursor
                onClicked: { quickCmdProc.command = ["firefox"]; quickCmdProc.running = true; root.triggerShockwave() }
              }
            }

            // Torrent
            Rectangle {
              Layout.fillWidth: true; height: 36; radius: 6
              color: Qt.rgba(1, 0.03, 0.22, 0.14)
              border.color: Qt.rgba(1, 0.03, 0.22, 0.4); border.width: 1
              ColumnLayout {
                anchors.centerIn: parent; spacing: 1
                Text { Layout.alignment: Qt.AlignHCenter; text: "🌊"; font.pixelSize: 12 }
                Text { Layout.alignment: Qt.AlignHCenter; text: "TORRENT"; color: "#fff"; font.pixelSize: 8; font.bold: true }
              }
              MouseArea {
                anchors.fill: parent; cursorShape: Qt.PointingHandCursor
                onClicked: { quickCmdProc.command = ["foot", "-T", "Milo Torrent", "-e", "milo-torrent", "swarm"]; quickCmdProc.running = true; root.triggerShockwave() }
              }
            }

            // Notes
            Rectangle {
              Layout.fillWidth: true; height: 36; radius: 6
              color: Qt.rgba(1, 0.03, 0.22, 0.14)
              border.color: Qt.rgba(1, 0.03, 0.22, 0.4); border.width: 1
              ColumnLayout {
                anchors.centerIn: parent; spacing: 1
                Text { Layout.alignment: Qt.AlignHCenter; text: "📝"; font.pixelSize: 12 }
                Text { Layout.alignment: Qt.AlignHCenter; text: "NOTES"; color: "#fff"; font.pixelSize: 8; font.bold: true }
              }
              MouseArea {
                anchors.fill: parent; cursorShape: Qt.PointingHandCursor
                onClicked: { quickCmdProc.command = ["/home/jeffy/.local/bin/milo-notes"]; quickCmdProc.running = true; root.triggerShockwave() }
              }
            }

            // MiloTop
            Rectangle {
              Layout.fillWidth: true; height: 36; radius: 6
              color: Qt.rgba(1, 0.03, 0.22, 0.14)
              border.color: Qt.rgba(1, 0.03, 0.22, 0.4); border.width: 1
              ColumnLayout {
                anchors.centerIn: parent; spacing: 1
                Text { Layout.alignment: Qt.AlignHCenter; text: "🖥️"; font.pixelSize: 12 }
                Text { Layout.alignment: Qt.AlignHCenter; text: "MILOTOP"; color: "#fff"; font.pixelSize: 8; font.bold: true }
              }
              MouseArea {
                anchors.fill: parent; cursorShape: Qt.PointingHandCursor
                onClicked: { quickCmdProc.command = ["foot", "-T", "MiloTop", "-e", "milotop"]; quickCmdProc.running = true; root.triggerShockwave() }
              }
            }
          }
        }
      }

      // ----------------------------------------------------------------------
      // 5.9 BOTTOM-CENTER: SLEEK MILO COMMAND CAPSULE
      // ----------------------------------------------------------------------
      Item {
        id: capsuleModule
        anchors.bottom: parent.bottom
        anchors.bottomMargin: 32
        anchors.horizontalCenter: parent.horizontalCenter
        width: Math.min(840, hudPanel.width - 560)
        height: 95

        // Main Glass Command Bar
        Rectangle {
          id: capsuleContainer
          anchors.fill: parent
          radius: 18
          color: Qt.rgba(0.04, 0.01, 0.03, 0.94)
          border.color: (capsuleInput.activeFocus) ? "#00f0ff" : Qt.rgba(1.0, 0.03, 0.22, 0.65)
          border.width: 1.5

          Behavior on border.color { ColorAnimation { duration: 300 } }

          // Top Neon Laser Line
          Rectangle {
            anchors.top: parent.top
            anchors.horizontalCenter: parent.horizontalCenter
            width: parent.width - 40
            height: 1.5
            gradient: Gradient {
              orientation: Gradient.Horizontal
              GradientStop { position: 0.0; color: "transparent" }
              GradientStop { position: 0.5; color: "#00f0ff" }
              GradientStop { position: 1.0; color: "transparent" }
            }
          }

          ColumnLayout {
            anchors.fill: parent
            anchors.margins: 10
            spacing: 6

            // Mode Pills Row
            RowLayout {
              spacing: 8
              Layout.fillWidth: true

              Item {
                width: 24; height: 24
                Rectangle {
                  anchors.fill: parent; radius: 12
                  color: "#031418"; border.color: "#00f0ff"; border.width: 1
                  Rectangle { anchors.centerIn: parent; width: 8; height: 8; radius: 4; color: "#00f0ff" }
                }
              }

              Text {
                text: "MILO TACTICAL INTERFACE"
                color: "#00f0ff"
                font.pixelSize: 10
                font.bold: true
                font.family: "monospace"
              }

              Item { Layout.fillWidth: true }

              // Hybrid Intelligence 3-Way Selector (Online / Offline / Auto)
              RowLayout {
                spacing: 4
                Repeater {
                  model: [
                    { "id": "auto", "label": "🔄 AUTO" },
                    { "id": "online", "label": "🌐 ONLINE" },
                    { "id": "offline", "label": "⚡ OFFLINE" }
                  ]
                  delegate: Rectangle {
                    required property var modelData
                    height: 20
                    width: intelPillText.implicitWidth + 12
                    radius: 10
                    color: root.intelligenceMode === modelData.id
                           ? (modelData.id === "online" ? "#00c896" : (modelData.id === "offline" ? "#ffaa00" : "#ff0838"))
                           : Qt.rgba(1, 0.03, 0.22, 0.12)
                    border.color: root.intelligenceMode === modelData.id ? "#ffffff" : Qt.rgba(1, 0.03, 0.22, 0.3)
                    border.width: 1

                    Text {
                      id: intelPillText
                      anchors.centerIn: parent
                      text: modelData.label
                      color: "#ffffff"
                      font.pixelSize: 9
                      font.bold: true
                      font.family: "monospace"
                    }

                    MouseArea {
                      anchors.fill: parent
                      cursorShape: Qt.PointingHandCursor
                      onClicked: root.setIntelligenceMode(modelData.id)
                    }
                  }
                }
              }

              Rectangle {
                width: 1; height: 16
                color: Qt.rgba(1, 0.03, 0.22, 0.3)
              }

              // Mode Pills
              Repeater {
                model: [
                  { "name": "✦ TACTICAL AI", "hint": "Ask Milo, dictate 🎙️, or type /dispatch, /code, /test" },
                  { "name": "✨ WISH", "hint": "✦ Tell Milo what tool to build, or type 'audit codebase'..." },
                  { "name": root.gameModeActive ? "🎮 GAME MODE: ON" : "🎮 GAME MODE", "hint": root.gameModeActive ? "Game Mode ACTIVE (3GB VRAM Dedicated) · Click to Deactivate" : "Click to activate Game Mode (dedicate 100% GPU VRAM to games)..." },
                  { "name": "⚡ COMMANDS", "hint": "Type any shell command or launch command palette (Super+Space)..." },
                  { "name": "📁 ARCHIVE", "hint": "Browse Milo Code Archive & Repositories..." },
                  { "name": "🎵 AUDIO", "hint": "Control Milo Soundtrack or open Audio Matrix..." }
                ]
                delegate: Rectangle {
                  required property var modelData
                  readonly property bool isWishPill: modelData.name.indexOf("WISH") !== -1
                  readonly property bool isGamePill: modelData.name.indexOf("GAME") !== -1
                  height: 20; width: modeText.implicitWidth + 14; radius: 10
                  color: isGamePill && root.gameModeActive ? "#00ff88" : (isWishPill ? (root.currentMode === modelData.name ? Qt.rgba(0.0, 0.94, 1.0, 0.3) : Qt.rgba(0.0, 0.94, 1.0, 0.12)) : (root.currentMode === modelData.name ? "#ff0838" : Qt.rgba(1, 0.03, 0.22, 0.12)))
                  border.color: isGamePill && root.gameModeActive ? "#ffffff" : (isWishPill ? (root.currentMode === modelData.name ? "#00f0ff" : Qt.rgba(0.0, 0.94, 1.0, 0.4)) : (root.currentMode === modelData.name ? "#ffffff" : Qt.rgba(1, 0.03, 0.22, 0.3)))
                  border.width: 1

                  Text {
                    id: modeText
                    anchors.centerIn: parent
                    text: modelData.name
                    color: isGamePill && root.gameModeActive ? "#000000" : (isWishPill ? (root.currentMode === modelData.name ? "#00f0ff" : "#ffffff") : "#ffffff")
                    font.pixelSize: 9
                    font.bold: true
                    font.family: "monospace"
                  }

                  MouseArea {
                    anchors.fill: parent; cursorShape: Qt.PointingHandCursor
                    onClicked: {
                      if (modelData.name.indexOf("GAME") !== -1) {
                        quickCmdProc.command = ["/home/jeffy/.local/bin/milo-game", "toggle"]
                        quickCmdProc.running = true
                        root.triggerShockwave()
                        return
                      }
                      root.currentMode = modelData.name
                      root.promptPlaceholder = modelData.hint
                      root.triggerShockwave()
                      if (modelData.name === "📁 ARCHIVE") {
                        quickCmdProc.command = ["/home/jeffy/.local/bin/milo-files"]
                        quickCmdProc.running = true
                      } else if (modelData.name === "🎵 AUDIO") {
                        quickCmdProc.command = ["foot", "-a", "milo-floating", "-T", "MILO // Cyber Soundtrack", "/home/jeffy/.local/bin/milo-music", "tui"]
                        quickCmdProc.running = true
                      } else if (modelData.name === "⚡ COMMANDS") {
                        quickCmdProc.command = ["/usr/bin/fuzzel"]
                        quickCmdProc.running = true
                      } else {
                        wallpaperPromptInput.forceActiveFocus()
                      }
                    }
                  }
                }
              }
            }

            // Input Bar Row — 100% Linux Native Wayland Desktop Input
            RowLayout {
              Layout.fillWidth: true
              spacing: 8

              Rectangle {
                id: wallpaperPromptBox
                Layout.fillWidth: true
                height: 38
                radius: 8
                color: wallpaperPromptInput.activeFocus ? Qt.rgba(0.20, 0.02, 0.05, 0.95) : Qt.rgba(0.10, 0.01, 0.02, 0.85)
                border.color: root.isThinking ? "#00f0ff" : (wallpaperPromptInput.activeFocus ? "#ff0838" : Qt.rgba(1, 0.03, 0.22, 0.5))
                border.width: (wallpaperPromptInput.activeFocus || root.isThinking) ? 1.5 : 1

                MouseArea {
                  anchors.fill: parent
                  cursorShape: Qt.IBeamCursor
                  onClicked: {
                    wallpaperPromptInput.forceActiveFocus()
                  }
                }

                RowLayout {
                  anchors.fill: parent
                  anchors.leftMargin: 12
                  anchors.rightMargin: 12
                  spacing: 8

                  Text {
                    text: root.isThinking ? "⚡" : "✦"
                    color: root.isThinking ? "#00f0ff" : "#ff2a55"
                    font.pixelSize: 13
                    font.bold: true
                  }

                  Text {
                    visible: root.isThinking
                    text: root.currentMode === "✨ WISH" ? "SYNTHESIZING..." : "COMPUTING..."
                    color: "#00f0ff"
                    font.pixelSize: 10
                    font.bold: true
                    font.family: "monospace"
                    SequentialAnimation on opacity {
                      running: root.isThinking
                      loops: Animation.Infinite
                      PropertyAnimation { to: 0.3; duration: 400 }
                      PropertyAnimation { to: 1.0; duration: 400 }
                    }
                  }

                  TextInput {
                    id: wallpaperPromptInput
                    Layout.fillWidth: true
                    color: "#ffffff"
                    font.pixelSize: 13
                    font.family: "system-ui, sans-serif"
                    clip: true
                    selectByMouse: true
                    activeFocusOnPress: true
                    cursorVisible: activeFocus

                    Text {
                      text: root.promptPlaceholder
                      color: Qt.rgba(1, 1, 1, 0.40)
                      font.pixelSize: 12
                      font.family: "system-ui, sans-serif"
                      visible: !wallpaperPromptInput.text && !wallpaperPromptInput.activeFocus
                      anchors.verticalCenter: parent.verticalCenter
                    }

                    Keys.priority: Keys.BeforeItem

                    Keys.onEscapePressed: function(event) {
                      focus = false
                      root.miloChatOutput = ""
                      root.lastCameraSnapshot = ""
                      root.hasPendingEvolution = false
                      chatAutoDismissTimer.stop()
                      event.accepted = true
                    }

                    Keys.onReturnPressed: function(event) {
                      var txt = wallpaperPromptInput.text.trim()
                      if (txt.length > 0) {
                        wallpaperPromptInput.text = ""
                        root.executeDesktopCommand(txt)
                        event.accepted = true
                      }
                    }

                    Keys.onEnterPressed: function(event) {
                      var txt = wallpaperPromptInput.text.trim()
                      if (txt.length > 0) {
                        wallpaperPromptInput.text = ""
                        root.executeDesktopCommand(txt)
                        event.accepted = true
                      }
                    }

                    onAccepted: {
                      var txt = wallpaperPromptInput.text.trim()
                      if (txt.length > 0) {
                        wallpaperPromptInput.text = ""
                        root.executeDesktopCommand(txt)
                      }
                    }
                  }

                  // Clear text button (visible when text entered)
                  Text {
                    visible: wallpaperPromptInput.text.length > 0
                    text: "✕"
                    color: Qt.rgba(1, 1, 1, 0.6)
                    font.pixelSize: 12
                    MouseArea {
                      anchors.fill: parent
                      cursorShape: Qt.PointingHandCursor
                      onClicked: {
                        wallpaperPromptInput.text = ""
                        wallpaperPromptInput.forceActiveFocus()
                      }
                    }
                  }
                }
              }

              // Voice Dictation Button (Phonon-2 Native)
              Rectangle {
                id: wallpaperVoiceBtn
                Layout.preferredWidth: 36
                Layout.preferredHeight: 36
                radius: 8
                color: Qt.rgba(0.15, 0.02, 0.04, 0.9)
                border.color: "#ff0838"
                border.width: 1

                Text {
                  anchors.centerIn: parent
                  text: "🎙️"
                  font.pixelSize: 14
                }

                MouseArea {
                  anchors.fill: parent
                  cursorShape: Qt.PointingHandCursor
                  onClicked: {
                    quickCmdProc.command = ["/home/jeffy/.local/bin/milo-listen"]
                    quickCmdProc.running = true
                    root.triggerShockwave()
                  }
                }
              }

              // Send Button
              Rectangle {
                Layout.preferredWidth: 36
                Layout.preferredHeight: 36
                radius: 8
                color: root.isThinking ? "#00f0ff" : "#ff0838"

                Text {
                  anchors.centerIn: parent
                  text: root.isThinking ? "⚡" : "➤"
                  color: root.isThinking ? "#000000" : "#ffffff"
                  font.pixelSize: 13
                  font.bold: true
                }

                MouseArea {
                  anchors.fill: parent
                  cursorShape: Qt.PointingHandCursor
                  onClicked: {
                    var txt = wallpaperPromptInput.text.trim()
                    if (txt.length > 0) {
                      wallpaperPromptInput.text = ""
                      root.executeDesktopCommand(txt)
                    }
                  }
                }
              }
            }

            // Quick Chips Row
            RowLayout {
              spacing: 8
              Layout.fillWidth: true

              Rectangle {
                height: 18; width: chipText1.implicitWidth + 12; radius: 4
                color: Qt.rgba(1, 0.03, 0.22, 0.12); border.color: Qt.rgba(1, 0.03, 0.22, 0.3); border.width: 1
                Text { id: chipText1; anchors.centerIn: parent; text: "📁 Browse Code Archive"; color: Qt.rgba(1, 1, 1, 0.7); font.pixelSize: 9 }
                MouseArea {
                  anchors.fill: parent; cursorShape: Qt.PointingHandCursor
                  onClicked: { quickCmdProc.command = ["/home/jeffy/.local/bin/milo-files"]; quickCmdProc.running = true; root.triggerShockwave() }
                }
              }

              Rectangle {
                height: 18; width: chipText2.implicitWidth + 12; radius: 4
                color: Qt.rgba(1, 0.03, 0.22, 0.12); border.color: Qt.rgba(1, 0.03, 0.22, 0.3); border.width: 1
                Text { id: chipText2; anchors.centerIn: parent; text: "🎵 Milo Soundtrack"; color: Qt.rgba(1, 1, 1, 0.7); font.pixelSize: 9 }
                MouseArea {
                  anchors.fill: parent; cursorShape: Qt.PointingHandCursor
                  onClicked: { quickCmdProc.command = ["/home/jeffy/.local/bin/milo-music", "play-pause"]; quickCmdProc.running = true; root.triggerShockwave(); if (!mediaProc.running) mediaProc.running = true }
                }
              }

              Rectangle {
                height: 18; width: chipText3.implicitWidth + 12; radius: 4
                color: Qt.rgba(1, 0.03, 0.22, 0.12); border.color: Qt.rgba(1, 0.03, 0.22, 0.3); border.width: 1
                Text { id: chipText3; anchors.centerIn: parent; text: "⚡ Open Terminal"; color: Qt.rgba(1, 1, 1, 0.7); font.pixelSize: 9 }
                MouseArea {
                  anchors.fill: parent; cursorShape: Qt.PointingHandCursor
                  onClicked: { quickCmdProc.command = ["foot"]; quickCmdProc.running = true; root.triggerShockwave() }
                }
              }

              Rectangle {
                height: 18; width: chipTextLook.implicitWidth + 12; radius: 4
                color: Qt.rgba(0, 0.9, 1.0, 0.15); border.color: Qt.rgba(0, 0.9, 1.0, 0.5); border.width: 1
                Text { id: chipTextLook; anchors.centerIn: parent; text: "👁️ Milo Look"; color: "#00e5ff"; font.pixelSize: 9; font.bold: true }
                MouseArea {
                  anchors.fill: parent; cursorShape: Qt.PointingHandCursor
                  onClicked: { root.executeDesktopCommand("/look") }
                }
              }

              Rectangle {
                height: 18; width: chipTextPosture.implicitWidth + 12; radius: 4
                color: Qt.rgba(0, 0.9, 1.0, 0.15); border.color: Qt.rgba(0, 0.9, 1.0, 0.5); border.width: 1
                Text { id: chipTextPosture; anchors.centerIn: parent; text: "🧘 Posture Check"; color: "#00e5ff"; font.pixelSize: 9 }
                MouseArea {
                  anchors.fill: parent; cursorShape: Qt.PointingHandCursor
                  onClicked: { root.executeDesktopCommand("/posture") }
                }
              }
            }
          }
        }
      }

      // ======================================================================
      // 5.5 IN-WALLPAPER MILO INTELLIGENCE DIRECTIVE DIALOGUE BOX
      // Embedded directly into the wallpaper layer (stays behind normal windows)
      // ======================================================================
      Rectangle {
        id: floatingChatBox
        anchors.bottom: parent.bottom
        anchors.bottomMargin: 140
        anchors.horizontalCenter: parent.horizontalCenter
        width: Math.max(500, Math.min(840, parent.width - 400))
        height: root.isThinking ? Math.min(240, Math.max(90, overlayText.implicitHeight + 56)) : (root.lastCameraSnapshot ? Math.max(124, Math.min(360, overlayText.implicitHeight + 56)) : Math.min(390, Math.max(90, overlayText.implicitHeight + 56 + (evolutionActionRow.visible ? 44 : 0))))
        radius: 14
        color: Qt.rgba(0.06, 0.01, 0.02, 0.96)
        border.color: root.isThinking ? "#00f0ff" : (root.lastCameraSnapshot ? "#00e5ff" : (root.hasPendingEvolution ? "#00f0ff" : Qt.rgba(1.0, 0.03, 0.22, 0.75)))
        border.width: 1.5
        clip: true
        visible: ((root.miloChatOutput && root.miloChatOutput.length > 0) || root.isThinking) && root.hudVisible

        Behavior on border.color { ColorAnimation { duration: 350 } }
        Behavior on height { NumberAnimation { duration: 200; easing.type: Easing.OutCubic } }

        ColumnLayout {
          anchors.fill: parent
          anchors.margins: 12
          spacing: 6

          // Header Row: Title & Close Button
          RowLayout {
            Layout.fillWidth: true
            spacing: 8

            Rectangle {
              width: 8; height: 8; radius: 4
              color: root.isThinking ? "#00f0ff" : (root.lastCameraSnapshot ? "#00e5ff" : (root.hasPendingEvolution ? "#00f0ff" : "#ff0838"))
              SequentialAnimation on opacity {
                running: root.isThinking
                loops: Animation.Infinite
                PropertyAnimation { to: 0.3; duration: 400 }
                PropertyAnimation { to: 1.0; duration: 400 }
              }
            }

            Text {
              text: root.isThinking ? (root.currentMode === "✨ WISH" ? "✦ MILO THOUGHT-TO-CODE GENESIS..." : "✦ MILO COMPUTING...") : (root.hasPendingEvolution ? (root.miloChatOutput.indexOf("AUDIT") !== -1 ? "✦ MILO CODEBASE AUDIT" : "✦ MILO EVOLUTION DIRECTIVE") : (root.lastCameraSnapshot ? "✦ MILO OPTICAL SENSOR" : "✦ MILO COGNITIVE DIRECTIVE"))
              color: root.isThinking ? "#00f0ff" : (root.lastCameraSnapshot ? "#00e5ff" : (root.hasPendingEvolution ? "#00f0ff" : "#ff0838"))
              font.pixelSize: 9
              font.bold: true
              font.letterSpacing: 1.5
            }

            Item { Layout.fillWidth: true }

            // Esc Hint Tag
            Rectangle {
              height: 18
              width: escHintText.implicitWidth + 12
              radius: 4
              color: Qt.rgba(0, 0, 0, 0.45)
              border.color: Qt.rgba(1, 1, 1, 0.15)
              border.width: 1

              Text {
                id: escHintText
                anchors.centerIn: parent
                text: "ESC TO CLOSE"
                color: Qt.rgba(1, 1, 1, 0.55)
                font.pixelSize: 8
                font.bold: true
                font.letterSpacing: 1.0
              }
            }

            // Dismiss Button (✕)
            Rectangle {
              width: 20; height: 20; radius: 10
              color: overlayCloseArea.containsMouse ? Qt.rgba(1, 0.03, 0.22, 0.4) : Qt.rgba(1, 0.03, 0.22, 0.15)
              border.color: Qt.rgba(1, 0.03, 0.22, 0.6)
              border.width: 1

              Text {
                anchors.centerIn: parent
                text: "✕"
                color: "#ffffff"
                font.pixelSize: 10
                font.bold: true
              }

              MouseArea {
                id: overlayCloseArea
                anchors.fill: parent
                hoverEnabled: true
                cursorShape: Qt.PointingHandCursor
                onClicked: {
                  root.isThinking = false
                  root.lastCameraSnapshot = ""
                  root.miloChatOutput = ""
                  chatAutoDismissTimer.stop()
                }
              }
            }
          }

          // Sleek Divider Laser Line
          Rectangle {
            Layout.fillWidth: true
            height: 1
            gradient: Gradient {
              orientation: Gradient.Horizontal
              GradientStop { position: 0.0; color: "transparent" }
              GradientStop { position: 0.2; color: root.lastCameraSnapshot ? Qt.rgba(0, 0.9, 1.0, 0.4) : Qt.rgba(1, 0.03, 0.22, 0.4) }
              GradientStop { position: 0.8; color: root.lastCameraSnapshot ? Qt.rgba(0, 0.9, 1.0, 0.4) : Qt.rgba(1, 0.03, 0.22, 0.4) }
              GradientStop { position: 1.0; color: "transparent" }
            }
          }

          // Row layout with preview and scrollable text
          RowLayout {
            Layout.fillWidth: true
            Layout.fillHeight: true
            spacing: 12

            // Camera Snapshot Preview Thumbnail (if active)
            Rectangle {
              visible: Boolean(root.lastCameraSnapshot) && !root.isThinking
              Layout.preferredWidth: 140
              Layout.preferredHeight: 88
              radius: 8
              color: "#0a0c14"
              border.color: "#00e5ff"
              border.width: 1.5
              clip: true

              Image {
                anchors.fill: parent
                source: root.lastCameraSnapshot ? ("file://" + root.lastCameraSnapshot) : ""
                fillMode: Image.PreserveAspectCrop
                asynchronous: true
                cache: false
              }

              Rectangle {
                anchors.bottom: parent.bottom
                anchors.left: parent.left
                anchors.right: parent.right
                height: 18
                color: Qt.rgba(0, 0, 0, 0.75)
                Text {
                  anchors.centerIn: parent
                  text: "🔍 Click to expand"
                  color: "#00e5ff"
                  font.pixelSize: 8
                  font.bold: true
                }
              }

              MouseArea {
                anchors.fill: parent
                cursorShape: Qt.PointingHandCursor
                onClicked: {
                  quickCmdProc.command = ["swayimg", "/home/jeffy/.local/state/milo/eyes/current_camera_capture.jpg"]
                  quickCmdProc.running = true
                }
              }
            }

            // Scrollable Rich Text Body
            ScrollView {
              id: chatScrollView
              Layout.fillWidth: true
              Layout.fillHeight: true
              Layout.preferredHeight: root.lastCameraSnapshot ? Math.max(88, Math.min(260, overlayText.implicitHeight + 8)) : Math.min(260, overlayText.implicitHeight + 8)
              clip: true
              contentWidth: availableWidth
              ScrollBar.horizontal.policy: ScrollBar.AlwaysOff
              ScrollBar.vertical.policy: overlayText.implicitHeight > 250 ? ScrollBar.AlwaysOn : ScrollBar.AsNeeded

              Text {
                id: overlayText
                width: chatScrollView.availableWidth
                text: (root.miloChatOutput && root.miloChatOutput.length > 0) ? root.miloChatOutput : (root.isThinking ? "✦ Telemetry query dispatched to neural cortex..." : "")
                textFormat: Text.MarkdownText
                color: root.isThinking ? "#00f0ff" : "#f1f5f9"
                font.pixelSize: 11
                font.family: "JetBrains Mono", "monospace"
                wrapMode: Text.Wrap
                leftPadding: 12
                rightPadding: 12
                topPadding: 4
                bottomPadding: 6
              }
            }
          }

          // Interactive Action Controls for Autonomous Self-Upgrade & Feature Proposals
          RowLayout {
            id: evolutionActionRow
            visible: root.hasPendingEvolution || (root.miloChatOutput.indexOf("EVOLUTION") !== -1) || (root.miloChatOutput.indexOf("AUTONOMOUS") !== -1) || (root.miloChatOutput.indexOf("Proposal Formulated") !== -1) || (root.miloChatOutput.indexOf("FEATURE GENESIS") !== -1) || (root.miloChatOutput.indexOf("AUDIT") !== -1)
            Layout.fillWidth: true
            Layout.topMargin: 4
            spacing: 10

            // 1. Authorize & Apply (Electric Cyan Glow)
            Rectangle {
              Layout.fillWidth: true
              Layout.preferredHeight: 32
              radius: 6
              color: authorizeArea.containsMouse ? Qt.rgba(0.0, 0.94, 1.0, 0.3) : Qt.rgba(0.0, 0.94, 1.0, 0.15)
              border.color: "#00f0ff"
              border.width: 1.5

              RowLayout {
                anchors.centerIn: parent
                spacing: 8
                Text {
                  text: "✦"
                  color: "#00f0ff"
                  font.pixelSize: 11
                  font.bold: true
                }
                Text {
                  text: root.miloChatOutput.indexOf("AUDIT") !== -1 ? "RESOLVE WEAK AREA #1" : "AUTHORIZE & APPLY UPGRADE"
                  color: "#ffffff"
                  font.pixelSize: 10
                  font.bold: true
                  font.letterSpacing: 1.0
                }
              }

              MouseArea {
                id: authorizeArea
                anchors.fill: parent
                hoverEnabled: true
                cursorShape: Qt.PointingHandCursor
                onClicked: {
                  root.applyEvolution()
                }
              }
            }

            // 2. Defer / Dismiss (Laser Crimson)
            Rectangle {
              Layout.preferredWidth: 100
              Layout.preferredHeight: 32
              radius: 6
              color: deferArea.containsMouse ? Qt.rgba(1.0, 0.03, 0.22, 0.3) : Qt.rgba(1.0, 0.03, 0.22, 0.15)
              border.color: "#ff0838"
              border.width: 1.5

              RowLayout {
                anchors.centerIn: parent
                spacing: 6
                Text {
                  text: "✕"
                  color: "#ff0838"
                  font.pixelSize: 10
                  font.bold: true
                }
                Text {
                  text: "DEFER"
                  color: "#ffffff"
                  font.pixelSize: 10
                  font.bold: true
                  font.letterSpacing: 1.0
                }
              }

              MouseArea {
                id: deferArea
                anchors.fill: parent
                hoverEnabled: true
                cursorShape: Qt.PointingHandCursor
                onClicked: {
                  root.deferEvolution()
                }
              }
            }

            // 3. Inspect Code Diff (Electric Cyan / Sky Blue)
            Rectangle {
              Layout.preferredWidth: 120
              Layout.preferredHeight: 32
              radius: 6
              color: diffArea.containsMouse ? Qt.rgba(0.22, 0.74, 0.97, 0.3) : Qt.rgba(0.22, 0.74, 0.97, 0.15)
              border.color: "#38bdf8"
              border.width: 1.5

              RowLayout {
                anchors.centerIn: parent
                spacing: 6
                Text {
                  text: "👁️"
                  font.pixelSize: 10
                }
                Text {
                  text: "VIEW DIFF"
                  color: "#38bdf8"
                  font.pixelSize: 10
                  font.bold: true
                  font.letterSpacing: 1.0
                }
              }

              MouseArea {
                id: diffArea
                anchors.fill: parent
                hoverEnabled: true
                cursorShape: Qt.PointingHandCursor
                onClicked: {
                  quickCmdProc.command = ["foot", "-H", "-a", "milo-floating", "-T", "MILO // Upgrade Code Inspector", "/home/jeffy/.local/bin/milo-evolve", "diff"]
                  quickCmdProc.running = true
                }
              }
            }
          }
        }
      }
    }
  }

  // ==========================================================================
  // 6. MILO SCRATCHPAD CENTERED MODAL OVERLAY (WlrLayer.Overlay)
  // Opens in the center of the screen on demand with interactive Milo Copilot.
  // ==========================================================================
  Variants {
    model: Quickshell.screens

    PanelWindow {
      id: scratchpadModalPanel
      required property var modelData
      screen: modelData
      visible: root.scratchpadModalOpen

      anchors {
        top: true
        bottom: true
        left: true
        right: true
      }

      color: "transparent"
      exclusionMode: ExclusionMode.Ignore
      WlrLayershell.namespace: "milo-scratchpad-modal"
      WlrLayershell.layer: WlrLayer.Overlay
      WlrLayershell.keyboardFocus: root.scratchpadModalOpen ? WlrKeyboardFocus.Exclusive : WlrKeyboardFocus.None

      onVisibleChanged: {
        if (visible) {
          if (root.midLeftTab === "tasks") {
            modalTaskInput.forceActiveFocus()
          } else if (root.midLeftTab === "agenda") {
            modalAgendaInput.forceActiveFocus()
          } else if (root.midLeftTab === "mail") {
            modalMailFocusScope.forceActiveFocus()
          } else {
            modalWaFocusScope.forceActiveFocus()
          }
        }
      }

      // Scrim background
      Rectangle {
        anchors.fill: parent
        color: Qt.rgba(0, 0, 0, 0.65)

        MouseArea {
          anchors.fill: parent
          onClicked: root.scratchpadModalOpen = false
        }
      }

      FocusScope {
        id: modalRootItem
        anchors.fill: parent
        focus: root.scratchpadModalOpen

        Keys.priority: Keys.BeforeItem
        Keys.onPressed: function(event) {
          if (event.key === Qt.Key_Escape) {
            root.scratchpadModalOpen = false
            event.accepted = true
          } else if (event.key === Qt.Key_Tab || event.key === Qt.Key_Backtab) {
            var isBack = (event.key === Qt.Key_Backtab || (event.modifiers & Qt.ShiftModifier))
            if (root.midLeftTab === "tasks") {
              if (isBack) {
                root.midLeftTab = "whatsapp"
                modalWaFocusScope.forceActiveFocus()
              } else {
                root.midLeftTab = "agenda"
                modalAgendaInput.forceActiveFocus()
              }
            } else if (root.midLeftTab === "agenda") {
              if (isBack) {
                root.midLeftTab = "tasks"
                modalTaskInput.forceActiveFocus()
              } else {
                root.midLeftTab = "mail"
                modalMailFocusScope.forceActiveFocus()
              }
            } else if (root.midLeftTab === "mail") {
              if (isBack) {
                root.midLeftTab = "agenda"
                modalAgendaInput.forceActiveFocus()
              } else {
                root.midLeftTab = "whatsapp"
                modalWaFocusScope.forceActiveFocus()
              }
            } else { // "whatsapp"
              if (isBack) {
                root.midLeftTab = "mail"
                modalMailFocusScope.forceActiveFocus()
              } else {
                root.midLeftTab = "tasks"
                modalTaskInput.forceActiveFocus()
              }
            }
            event.accepted = true
          }
        }

        // Centered Modal Window
        Rectangle {
          id: modalBox
          anchors.centerIn: parent
          width: 620
          height: 540
          radius: 14
          color: Qt.rgba(0.06, 0.01, 0.02, 0.96)
          border.color: root.midLeftTab === "whatsapp" ? "#25d366" : (root.midLeftTab === "mail" ? "#ffaa00" : (root.midLeftTab === "agenda" ? "#00f0ff" : "#ff0838"))
          border.width: 1.5

        // Prevent click-through
        MouseArea { anchors.fill: parent }

        ColumnLayout {
          anchors.fill: parent
          anchors.margins: 16
          spacing: 10

          // Top Header Row: Dual Tab Switcher & Status
          RowLayout {
            Layout.fillWidth: true
            spacing: 8

            // Tab Buttons
            RowLayout {
              spacing: 6

              Rectangle {
                height: 26
                width: modalTasksTabLabel.implicitWidth + 16
                radius: 5
                color: root.midLeftTab === "tasks" ? "#ff0838" : Qt.rgba(1, 0.03, 0.22, 0.15)
                border.color: root.midLeftTab === "tasks" ? "#ffffff" : Qt.rgba(1, 0.03, 0.22, 0.4)
                border.width: 1
                Text {
                  id: modalTasksTabLabel
                  anchors.centerIn: parent
                  text: "✦ MISSIONS & TASKS"
                  color: root.midLeftTab === "tasks" ? "#ffffff" : "#ff8899"
                  font.pixelSize: 11
                  font.bold: true
                  font.family: "monospace"
                }
                MouseArea {
                  anchors.fill: parent
                  cursorShape: Qt.PointingHandCursor
                  onClicked: {
                    root.midLeftTab = "tasks"
                    modalTaskInput.forceActiveFocus()
                  }
                }
              }

              Rectangle {
                height: 26
                width: modalAgendaTabLabel.implicitWidth + 16
                radius: 5
                color: root.midLeftTab === "agenda" ? "#00f0ff" : Qt.rgba(0, 0.9, 1.0, 0.15)
                border.color: root.midLeftTab === "agenda" ? "#ffffff" : Qt.rgba(0, 0.9, 1.0, 0.4)
                border.width: 1
                Text {
                  id: modalAgendaTabLabel
                  anchors.centerIn: parent
                  text: "📅 CALENDAR & AGENDA"
                  color: root.midLeftTab === "agenda" ? "#060102" : "#80f5ff"
                  font.pixelSize: 11
                  font.bold: true
                  font.family: "monospace"
                }
                MouseArea {
                  anchors.fill: parent
                  cursorShape: Qt.PointingHandCursor
                  onClicked: {
                    root.midLeftTab = "agenda"
                    modalAgendaInput.forceActiveFocus()
                  }
                }
              }

              // Mail Tab Button (Modal)
              Rectangle {
                height: 26
                width: modalMailTabLabel.implicitWidth + (root.mailData && root.mailData.unread_count > 0 ? 34 : 16)
                radius: 5
                color: root.midLeftTab === "mail" ? "#ffaa00" : Qt.rgba(1.0, 0.67, 0.0, 0.15)
                border.color: root.midLeftTab === "mail" ? "#ffffff" : Qt.rgba(1.0, 0.67, 0.0, 0.4)
                border.width: 1

                RowLayout {
                  anchors.centerIn: parent
                  spacing: 5
                  Text {
                    id: modalMailTabLabel
                    text: "✉ GMAIL"
                    color: root.midLeftTab === "mail" ? "#060102" : "#ffd480"
                    font.pixelSize: 11
                    font.bold: true
                    font.family: "monospace"
                  }
                  Rectangle {
                    visible: root.mailData && root.mailData.unread_count > 0
                    height: 14
                    width: mailBadgeNum.implicitWidth + 6
                    radius: 7
                    color: "#ff0838"
                    Text {
                      id: mailBadgeNum
                      anchors.centerIn: parent
                      text: root.mailData && root.mailData.unread_count ? root.mailData.unread_count.toString() : "0"
                      color: "#ffffff"
                      font.pixelSize: 8
                      font.bold: true
                      font.family: "monospace"
                    }
                  }
                }

                MouseArea {
                  anchors.fill: parent
                  cursorShape: Qt.PointingHandCursor
                  onClicked: {
                    root.midLeftTab = "mail"
                    modalMailFocusScope.forceActiveFocus()
                  }
                }
              }

              // WhatsApp Tab Button (Modal)
              Rectangle {
                height: 26
                width: modalWaTabLabel.implicitWidth + (root.whatsappData && root.whatsappData.unread_count > 0 ? 34 : 16)
                radius: 5
                color: root.midLeftTab === "whatsapp" ? "#25d366" : Qt.rgba(0.15, 0.83, 0.40, 0.15)
                border.color: root.midLeftTab === "whatsapp" ? "#ffffff" : Qt.rgba(0.15, 0.83, 0.40, 0.4)
                border.width: 1

                RowLayout {
                  anchors.centerIn: parent
                  spacing: 5
                  Text {
                    id: modalWaTabLabel
                    text: "💬 WHATSAPP"
                    color: root.midLeftTab === "whatsapp" ? "#060102" : "#25d366"
                    font.pixelSize: 11
                    font.bold: true
                    font.family: "monospace"
                  }
                  Rectangle {
                    visible: root.whatsappData && root.whatsappData.unread_count > 0
                    height: 14
                    width: waBadgeNum.implicitWidth + 6
                    radius: 7
                    color: "#ff0838"
                    Text {
                      id: waBadgeNum
                      anchors.centerIn: parent
                      text: root.whatsappData && root.whatsappData.unread_count ? root.whatsappData.unread_count.toString() : "0"
                      color: "#ffffff"
                      font.pixelSize: 8
                      font.bold: true
                      font.family: "monospace"
                    }
                  }
                }

                MouseArea {
                  anchors.fill: parent
                  cursorShape: Qt.PointingHandCursor
                  onClicked: {
                    root.midLeftTab = "whatsapp"
                    modalWaFocusScope.forceActiveFocus()
                  }
                }
              }
            }

            Item { Layout.fillWidth: true }

            // Counters badge
            Rectangle {
              height: 24
              width: counterText.implicitWidth + 16
              radius: 5
              color: root.midLeftTab === "whatsapp" ? Qt.rgba(0.15, 0.83, 0.40, 0.2) : (root.midLeftTab === "mail" ? Qt.rgba(1.0, 0.67, 0.0, 0.2) : (root.midLeftTab === "agenda" ? Qt.rgba(0, 0.9, 1.0, 0.2) : Qt.rgba(1, 0.03, 0.22, 0.2)))
              border.color: root.midLeftTab === "whatsapp" ? Qt.rgba(0.15, 0.83, 0.40, 0.5) : (root.midLeftTab === "mail" ? Qt.rgba(1.0, 0.67, 0.0, 0.5) : (root.midLeftTab === "agenda" ? Qt.rgba(0, 0.9, 1.0, 0.5) : Qt.rgba(1, 0.03, 0.22, 0.5)))
              border.width: 1
              Text {
                id: counterText
                anchors.centerIn: parent
                text: {
                  if (root.midLeftTab === "whatsapp") {
                    return (root.whatsappData && root.whatsappData.unread_count ? root.whatsappData.unread_count : 0) + " UNREAD"
                  } else if (root.midLeftTab === "mail") {
                    return (root.mailData && root.mailData.unread_count ? root.mailData.unread_count : 0) + " UNREAD"
                  } else if (root.midLeftTab === "agenda") {
                    return root.agendaList.length + " EVENTS TODAY"
                  } else {
                    return root.countDoneTodos() + "/" + root.todosList.length + " COMPLETED"
                  }
                }
                color: root.midLeftTab === "whatsapp" ? "#25d366" : (root.midLeftTab === "mail" ? "#ffd480" : (root.midLeftTab === "agenda" ? "#80f5ff" : "#ff8899"))
                font.pixelSize: 10
                font.bold: true
                font.family: "monospace"
              }
            }

            // Close button
            Rectangle {
              width: 24; height: 24; radius: 5
              color: root.midLeftTab === "whatsapp" ? Qt.rgba(0.15, 0.83, 0.40, 0.2) : (root.midLeftTab === "mail" ? Qt.rgba(1.0, 0.67, 0.0, 0.2) : (root.midLeftTab === "agenda" ? Qt.rgba(0, 0.9, 1.0, 0.2) : Qt.rgba(1, 0.03, 0.22, 0.2)))
              border.color: root.midLeftTab === "whatsapp" ? "#25d366" : (root.midLeftTab === "mail" ? "#ffaa00" : (root.midLeftTab === "agenda" ? "#00f0ff" : "#ff0838"))
              border.width: 1
              Text {
                anchors.centerIn: parent
                text: "✕"
                color: "#ffffff"
                font.pixelSize: 12
                font.bold: true
              }
              MouseArea {
                anchors.fill: parent
                cursorShape: Qt.PointingHandCursor
                onClicked: root.scratchpadModalOpen = false
              }
            }
          }

          // ==================================================================
          // MODAL VIEW 1: TASKS
          // ==================================================================
          // Filter tabs row: [ ALL (X) ] [ PENDING (Y) ] [ COMPLETED (Z) ]
          RowLayout {
            Layout.fillWidth: true
            spacing: 8
            visible: root.midLeftTab === "tasks"

            Repeater {
              model: [
                { id: "all", label: "ALL (" + root.todosList.length + ")" },
                { id: "pending", label: "PENDING (" + (root.todosList.length - root.countDoneTodos()) + ")" },
                { id: "completed", label: "COMPLETED (" + root.countDoneTodos() + ")" }
              ]

              delegate: Rectangle {
                required property var modelData
                height: 24
                width: tabLabel.implicitWidth + 18
                radius: 4
                color: root.scratchpadFilter === modelData.id ? "#ff0838" : Qt.rgba(1, 0.03, 0.22, 0.12)
                border.color: root.scratchpadFilter === modelData.id ? "#ff2a55" : Qt.rgba(1, 0.03, 0.22, 0.3)
                border.width: 1

                Text {
                  id: tabLabel
                  anchors.centerIn: parent
                  text: modelData.label
                  color: root.scratchpadFilter === modelData.id ? "#ffffff" : Qt.rgba(1, 1, 1, 0.6)
                  font.pixelSize: 10
                  font.bold: root.scratchpadFilter === modelData.id
                  font.family: "monospace"
                }

                MouseArea {
                  anchors.fill: parent
                  cursorShape: Qt.PointingHandCursor
                  onClicked: root.scratchpadFilter = modelData.id
                }
              }
            }

            Item { Layout.fillWidth: true }

            // Toggle Wrap All for Modal
            Rectangle {
              height: 24
              width: modalWrapText.implicitWidth + 14
              radius: 4
              color: root.modalTasksWrapAll ? "#ff0838" : Qt.rgba(1, 0.03, 0.22, 0.15)
              border.color: root.modalTasksWrapAll ? "#ffffff" : Qt.rgba(1, 0.03, 0.22, 0.4)
              border.width: 1

              Text {
                id: modalWrapText
                anchors.centerIn: parent
                text: root.modalTasksWrapAll ? "☰ WRAP ALL ON" : "⋯ EXPAND ALL"
                color: root.modalTasksWrapAll ? "#ffffff" : "#ff8899"
                font.pixelSize: 9
                font.bold: true
                font.family: "monospace"
              }

              MouseArea {
                anchors.fill: parent
                cursorShape: Qt.PointingHandCursor
                onClicked: root.modalTasksWrapAll = !root.modalTasksWrapAll
              }
            }

            // Clear completed button
            Rectangle {
              height: 24
              width: clearLabel.implicitWidth + 14
              radius: 4
              color: Qt.rgba(0.2, 0.05, 0.08, 0.6)
              border.color: Qt.rgba(1, 0.2, 0.3, 0.4)
              border.width: 1
              visible: {
                for (var i = 0; i < root.todosList.length; i++) {
                  if (root.todosList[i].done) return true
                }
                return false
              }
              Text {
                id: clearLabel
                anchors.centerIn: parent
                text: "🧹 Clear Completed"
                color: Qt.rgba(1, 0.6, 0.7, 0.8)
                font.pixelSize: 9
                font.family: "monospace"
              }
              MouseArea {
                anchors.fill: parent
                cursorShape: Qt.PointingHandCursor
                onClicked: {
                  var remaining = []
                  for (var i = 0; i < root.todosList.length; i++) {
                    if (!root.todosList[i].done) remaining.push(root.todosList[i])
                  }
                  root.todosList = remaining
                  root.saveTodos()
                }
              }
            }
          }

          // Task items (scrollable)
          ScrollView {
            Layout.fillWidth: true
            Layout.fillHeight: true
            clip: true
            visible: root.midLeftTab === "tasks"

            ColumnLayout {
              width: modalBox.width - 36
              spacing: 6

              Repeater {
                model: {
                  var filtered = []
                  for (var i = 0; i < root.todosList.length; i++) {
                    var item = root.todosList[i]
                    if (root.scratchpadFilter === "all") {
                      filtered.push({ origIdx: i, data: item })
                    } else if (root.scratchpadFilter === "pending" && !item.done) {
                      filtered.push({ origIdx: i, data: item })
                    } else if (root.scratchpadFilter === "completed" && item.done) {
                      filtered.push({ origIdx: i, data: item })
                    }
                  }
                  return filtered
                }

                delegate: Rectangle {
                  id: modalTaskRow
                  required property var modelData
                  Layout.fillWidth: true
                  property bool isLong: (modelData.data.text && modelData.data.text.length > 45)
                  property bool isExpanded: root.modalTasksWrapAll || (root.expandedModalTaskIndex === modelData.origIdx)
                  height: isExpanded ? Math.max(34, modalTaskText.contentHeight + 16) : 34
                  radius: 6
                  color: isExpanded ? Qt.rgba(1, 0.03, 0.22, modelData.data.done ? 0.18 : 0.12) : Qt.rgba(1, 0.03, 0.22, modelData.data.done ? 0.12 : 0.07)
                  border.color: isExpanded ? Qt.rgba(1, 0.03, 0.22, 0.6) : (modelData.data.done ? Qt.rgba(1, 0.03, 0.22, 0.2) : Qt.rgba(1, 0.03, 0.22, 0.35))
                  border.width: 1

                  RowLayout {
                    anchors.fill: parent
                    anchors.leftMargin: 10
                    anchors.rightMargin: 10
                    spacing: 10

                    // Checkbox
                    Rectangle {
                      width: 16; height: 16; radius: 4
                      color: modelData.data.done ? "#ff0838" : "transparent"
                      border.color: "#ff0838"; border.width: 1.2
                      Layout.alignment: modalTaskRow.isExpanded ? Qt.AlignTop : Qt.AlignVCenter
                      Layout.topMargin: modalTaskRow.isExpanded ? 3 : 0
                      Text {
                        anchors.centerIn: parent
                        text: "✓"
                        color: "#fff"
                        font.pixelSize: 10
                        font.bold: true
                        visible: modelData.data.done
                      }
                      MouseArea {
                        anchors.fill: parent
                        cursorShape: Qt.PointingHandCursor
                        onClicked: root.toggleTodo(modelData.origIdx)
                      }
                    }

                    // Task text
                    Text {
                      id: modalTaskText
                      Layout.fillWidth: true
                      text: modelData.data.text || ""
                      color: modelData.data.done ? Qt.rgba(1, 1, 1, 0.4) : "#ffffff"
                      font.strikeout: modelData.data.done
                      font.pixelSize: 11
                      font.family: "system-ui, sans-serif"
                      wrapMode: modalTaskRow.isExpanded ? Text.Wrap : Text.NoWrap
                      elide: modalTaskRow.isExpanded ? Text.ElideNone : Text.ElideRight

                      MouseArea {
                        anchors.fill: parent
                        cursorShape: Qt.PointingHandCursor
                        onClicked: {
                          if (modalTaskRow.isLong) {
                            root.expandedModalTaskIndex = (root.expandedModalTaskIndex === modelData.origIdx ? -1 : modelData.origIdx)
                          } else {
                            root.toggleTodo(modelData.origIdx)
                          }
                        }
                      }
                    }

                    // Expand badge pill for long tasks
                    Rectangle {
                      visible: modalTaskRow.isLong && !root.modalTasksWrapAll
                      height: 18
                      width: 50
                      radius: 3
                      color: modalTaskRow.isExpanded ? "#ff0838" : Qt.rgba(1, 0.03, 0.22, 0.2)
                      border.color: Qt.rgba(1, 0.03, 0.22, 0.5)
                      border.width: 1
                      Layout.alignment: modalTaskRow.isExpanded ? Qt.AlignTop : Qt.AlignVCenter
                      Layout.topMargin: modalTaskRow.isExpanded ? 2 : 0

                      Text {
                        anchors.centerIn: parent
                        text: modalTaskRow.isExpanded ? "▲ LESS" : "▼ MORE"
                        color: "#ffffff"
                        font.pixelSize: 8
                        font.bold: true
                        font.family: "monospace"
                      }

                      MouseArea {
                        anchors.fill: parent
                        cursorShape: Qt.PointingHandCursor
                        onClicked: {
                          root.expandedModalTaskIndex = (root.expandedModalTaskIndex === modelData.origIdx ? -1 : modelData.origIdx)
                        }
                      }
                    }

                    // Time badge
                    Text {
                      text: modelData.data.created_at || ""
                      color: Qt.rgba(1, 1, 1, 0.35)
                      font.pixelSize: 9
                      font.family: "monospace"
                      visible: !!modelData.data.created_at
                      Layout.alignment: modalTaskRow.isExpanded ? Qt.AlignTop : Qt.AlignVCenter
                      Layout.topMargin: modalTaskRow.isExpanded ? 3 : 0
                    }

                    // Delete button
                    Rectangle {
                      width: 18; height: 18; radius: 3
                      color: "transparent"
                      Layout.alignment: modalTaskRow.isExpanded ? Qt.AlignTop : Qt.AlignVCenter
                      Layout.topMargin: modalTaskRow.isExpanded ? 2 : 0
                      Text {
                        anchors.centerIn: parent
                        text: "×"
                        color: Qt.rgba(1, 0.2, 0.3, 0.8)
                        font.pixelSize: 14
                        font.bold: true
                      }
                      MouseArea {
                        anchors.fill: parent
                        cursorShape: Qt.PointingHandCursor
                        onClicked: root.removeTodo(modelData.origIdx)
                      }
                    }
                  }
                }
              }
            }
          }

          // Add Task Input Box (Auto-Expanding Multi-line with Word Wrapping)
          Rectangle {
            id: modalTaskInputContainer
            Layout.fillWidth: true
            height: Math.min(100, Math.max(38, modalTaskInput.contentHeight + 14))
            radius: 7
            color: Qt.rgba(0.12, 0.01, 0.03, 0.90)
            border.color: modalTaskInput.activeFocus ? "#ff0838" : Qt.rgba(1, 0.03, 0.22, 0.5)
            border.width: 1.2
            visible: root.midLeftTab === "tasks"

            RowLayout {
              anchors.fill: parent
              anchors.leftMargin: 10
              anchors.rightMargin: 6
              anchors.topMargin: 5
              anchors.bottomMargin: 5
              spacing: 8

              Text {
                text: "➕"
                font.pixelSize: 12
                Layout.alignment: Qt.AlignTop
                Layout.topMargin: 2
              }

              TextEdit {
                id: modalTaskInput
                Layout.fillWidth: true
                Layout.fillHeight: true
                activeFocusOnTab: false
                color: "#ffffff"
                font.pixelSize: 11
                font.family: "system-ui, sans-serif"
                wrapMode: TextEdit.Wrap
                selectByMouse: true
                selectionColor: "#ff0838"

                Keys.priority: Keys.BeforeItem
                Keys.onPressed: function(event) {
                  if (event.key === Qt.Key_Return || event.key === Qt.Key_Enter) {
                    if (!(event.modifiers & Qt.ShiftModifier)) {
                      var val = modalTaskInput.text.trim()
                      if (val.length > 0) {
                        root.addTodo(val)
                        modalTaskInput.text = ""
                      }
                      event.accepted = true
                      return
                    }
                  } else if (event.key === Qt.Key_Escape) {
                    root.scratchpadModalOpen = false
                    event.accepted = true
                    return
                  } else if (event.key === Qt.Key_Tab || event.key === Qt.Key_Backtab) {
                    var isBack = (event.key === Qt.Key_Backtab || (event.modifiers & Qt.ShiftModifier))
                    if (isBack) {
                      root.midLeftTab = "mail"
                      modalMailFocusScope.forceActiveFocus()
                    } else {
                      root.midLeftTab = "agenda"
                      modalAgendaInput.forceActiveFocus()
                    }
                    event.accepted = true
                    return
                  }
                }

                Text {
                  anchors.fill: parent
                  anchors.topMargin: 1
                  text: "Type a new mission or task and press Enter (Shift+Enter for newline)..."
                  color: Qt.rgba(1, 1, 1, 0.40)
                  font.pixelSize: 11
                  font.family: "system-ui, sans-serif"
                  visible: !modalTaskInput.text && !modalTaskInput.activeFocus
                }
              }

              // Word counter pill for long tasks
              Rectangle {
                visible: modalTaskInput.text.trim().length > 20
                height: 22
                width: modalCounterText.implicitWidth + 10
                radius: 4
                color: Qt.rgba(0.2, 0.02, 0.05, 0.8)
                border.color: Qt.rgba(1, 0.03, 0.22, 0.4)
                border.width: 1
                Layout.alignment: Qt.AlignTop

                Text {
                  id: modalCounterText
                  anchors.centerIn: parent
                  text: modalTaskInput.text.trim().split(/\s+/).filter(Boolean).length + " w · " + modalTaskInput.text.length + " ch"
                  color: "#ff8899"
                  font.pixelSize: 8
                  font.family: "monospace"
                }
              }

              // Clear button
              Rectangle {
                visible: modalTaskInput.text.length > 0
                width: 22; height: 22; radius: 4
                color: Qt.rgba(1, 1, 1, 0.08)
                Layout.alignment: Qt.AlignTop
                Text {
                  anchors.centerIn: parent
                  text: "×"
                  color: Qt.rgba(1, 1, 1, 0.6)
                  font.pixelSize: 13
                  font.bold: true
                }
                MouseArea {
                  anchors.fill: parent
                  cursorShape: Qt.PointingHandCursor
                  onClicked: modalTaskInput.text = ""
                }
              }

              // ADD button
              Rectangle {
                width: 50; height: 26; radius: 4
                color: "#ff0838"
                Layout.alignment: Qt.AlignTop
                Text {
                  anchors.centerIn: parent
                  text: "ADD"
                  color: "#ffffff"
                  font.pixelSize: 10
                  font.bold: true
                  font.family: "monospace"
                }
                MouseArea {
                  anchors.fill: parent
                  cursorShape: Qt.PointingHandCursor
                  onClicked: {
                    var val = modalTaskInput.text.trim()
                    if (val.length > 0) {
                      root.addTodo(val)
                      modalTaskInput.text = ""
                    }
                  }
                }
              }
            }
          }

          // Milo AI Neural Task Copilot Strip
          Rectangle {
            Layout.fillWidth: true
            height: 68
            radius: 8
            color: Qt.rgba(0.04, 0.08, 0.12, 0.75)
            border.color: Qt.rgba(0, 0.9, 1.0, 0.35)
            border.width: 1
            visible: root.midLeftTab === "tasks"

            ColumnLayout {
              anchors.fill: parent
              anchors.margins: 6
              spacing: 4

              RowLayout {
                Layout.fillWidth: true
                spacing: 6

                Text {
                  text: "🤖 MILO TASK COPILOT"
                  color: "#00e5ff"
                  font.pixelSize: 9
                  font.bold: true
                  font.family: "monospace"
                }

                Item { Layout.fillWidth: true }

                // Quick AI Action Chips
                Repeater {
                  model: [
                    { label: "⚡ Summarize", q: "summarize my tasks" },
                    { label: "⏳ Pending?", q: "what are my pending tasks?" },
                    { label: "✔ Completed?", q: "what did i finish?" }
                  ]
                  delegate: Rectangle {
                    required property var modelData
                    height: 18
                    width: chipText.implicitWidth + 10
                    radius: 3
                    color: Qt.rgba(0, 0.9, 1.0, 0.15)
                    border.color: Qt.rgba(0, 0.9, 1.0, 0.4)
                    border.width: 1
                    Text {
                      id: chipText
                      anchors.centerIn: parent
                      text: modelData.label
                      color: "#b0f4ff"
                      font.pixelSize: 8
                      font.family: "monospace"
                    }
                    MouseArea {
                      anchors.fill: parent
                      cursorShape: Qt.PointingHandCursor
                      onClicked: {
                        root.askMilo(modelData.q)
                      }
                    }
                  }
                }
              }

              // Milo Speech / Chat Feedback snippet
              Text {
                Layout.fillWidth: true
                text: root.miloChatOutput ? root.miloChatOutput : "Ask Milo: 'What are my pending tasks?' or click a chip above."
                color: root.miloChatOutput ? "#ffffff" : Qt.rgba(1, 1, 0.5)
                font.pixelSize: 9
                font.family: "system-ui, sans-serif"
                elide: Text.ElideRight
                wrapMode: Text.NoWrap
              }
            }
          }

          // ==================================================================
          // MODAL VIEW 2: CALENDAR & AGENDA
          // ==================================================================
          // Subheader row: Actions & Info
          RowLayout {
            Layout.fillWidth: true
            spacing: 8
            visible: root.midLeftTab === "agenda"

            Text {
              text: "SOVEREIGN LOCAL TIMELINE // SQLITE (~/.local/share/milo/calendar)"
              color: Qt.rgba(0, 0.9, 1.0, 0.7)
              font.pixelSize: 10
              font.family: "monospace"
            }

            Item { Layout.fillWidth: true }

            // Spoken Briefing Button
            Rectangle {
              height: 24
              width: briefLabel.implicitWidth + 14
              radius: 4
              color: Qt.rgba(0, 0.9, 1.0, 0.15)
              border.color: "#00f0ff"
              border.width: 1

              Text {
                id: briefLabel
                anchors.centerIn: parent
                text: "📢 Voice Briefing"
                color: "#b0f4ff"
                font.pixelSize: 9
                font.family: "monospace"
              }
              MouseArea {
                anchors.fill: parent
                cursorShape: Qt.PointingHandCursor
                onClicked: {
                  root.askMilo("give me my daily calendar briefing")
                }
              }
            }

            // Refresh Button
            Rectangle {
              height: 24
              width: refreshLabel.implicitWidth + 14
              radius: 4
              color: Qt.rgba(0.08, 0.14, 0.2, 0.6)
              border.color: Qt.rgba(0, 0.9, 1.0, 0.3)
              border.width: 1

              Text {
                id: refreshLabel
                anchors.centerIn: parent
                text: "🔄 Refresh"
                color: "#ffffff"
                font.pixelSize: 9
                font.family: "monospace"
              }
              MouseArea {
                anchors.fill: parent
                cursorShape: Qt.PointingHandCursor
                onClicked: {
                  root.reloadAgenda()
                }
              }
            }
          }

          // Worktime Management Banner (Modal)
          Rectangle {
            Layout.fillWidth: true
            height: 32
            radius: 6
            visible: root.midLeftTab === "agenda"
            color: root.worktimeData && root.worktimeData.is_worktime ? Qt.rgba(0, 0.9, 1.0, 0.12) : Qt.rgba(0.05, 0.08, 0.12, 0.7)
            border.color: root.worktimeData && root.worktimeData.is_worktime ? "#00f0ff" : Qt.rgba(0, 0.8, 1.0, 0.3)
            border.width: 1

            RowLayout {
              anchors.fill: parent
              anchors.leftMargin: 10
              anchors.rightMargin: 10
              spacing: 8

              Text {
                text: "⏱ DAILY WORKTIME:"
                color: "#80f5ff"
                font.pixelSize: 10
                font.bold: true
                font.family: "monospace"
              }

              // Work hours badge
              Rectangle {
                height: 20
                width: wtHoursLabel.implicitWidth + 12
                radius: 4
                color: root.worktimeData && root.worktimeData.is_worktime ? "#00f0ff" : Qt.rgba(0, 0.9, 1.0, 0.2)
                Text {
                  id: wtHoursLabel
                  anchors.centerIn: parent
                  text: (root.worktimeData && root.worktimeData.start ? (root.worktimeData.start + " - " + root.worktimeData.end) : "09:00 - 18:00")
                  color: root.worktimeData && root.worktimeData.is_worktime ? "#060102" : "#80f5ff"
                  font.pixelSize: 10
                  font.bold: true
                  font.family: "monospace"
                }
              }

              // Live Status Badge
              Rectangle {
                height: 20
                width: wtStatusLabel.implicitWidth + 12
                radius: 4
                color: root.worktimeData && root.worktimeData.is_worktime ? Qt.rgba(0, 1.0, 0.5, 0.2) : Qt.rgba(1, 1, 1, 0.1)
                border.color: root.worktimeData && root.worktimeData.is_worktime ? "#00ff88" : Qt.rgba(1, 1, 1, 0.2)
                border.width: 1
                Text {
                  id: wtStatusLabel
                  anchors.centerIn: parent
                  text: root.worktimeData && root.worktimeData.status_text ? root.worktimeData.status_text : "Off Duty"
                  color: root.worktimeData && root.worktimeData.is_worktime ? "#00ff88" : Qt.rgba(1, 1, 1, 0.6)
                  font.pixelSize: 9
                  font.family: "monospace"
                }
              }

              Item { Layout.fillWidth: true }

              Text {
                text: "Presets:"
                color: Qt.rgba(1, 1, 1, 0.4)
                font.pixelSize: 9
                font.family: "monospace"
              }

              // Preset chip: 09:00-18:00
              Rectangle {
                height: 20
                width: p1Label.implicitWidth + 10
                radius: 3
                color: Qt.rgba(0, 0.9, 1.0, 0.15)
                border.color: Qt.rgba(0, 0.9, 1.0, 0.4)
                border.width: 1
                Text {
                  id: p1Label
                  anchors.centerIn: parent
                  text: "09-18"
                  color: "#b0f4ff"
                  font.pixelSize: 8
                  font.family: "monospace"
                }
                MouseArea {
                  anchors.fill: parent
                  cursorShape: Qt.PointingHandCursor
                  onClicked: root.setWorktime("09:00-18:00")
                }
              }

              // Preset chip: 10:00-19:00
              Rectangle {
                height: 20
                width: p2Label.implicitWidth + 10
                radius: 3
                color: Qt.rgba(0, 0.9, 1.0, 0.15)
                border.color: Qt.rgba(0, 0.9, 1.0, 0.4)
                border.width: 1
                Text {
                  id: p2Label
                  anchors.centerIn: parent
                  text: "10-19"
                  color: "#b0f4ff"
                  font.pixelSize: 8
                  font.family: "monospace"
                }
                MouseArea {
                  anchors.fill: parent
                  cursorShape: Qt.PointingHandCursor
                  onClicked: root.setWorktime("10:00-19:00")
                }
              }

              // Preset chip: 08:00-17:00
              Rectangle {
                height: 20
                width: p3Label.implicitWidth + 10
                radius: 3
                color: Qt.rgba(0, 0.9, 1.0, 0.15)
                border.color: Qt.rgba(0, 0.9, 1.0, 0.4)
                border.width: 1
                Text {
                  id: p3Label
                  anchors.centerIn: parent
                  text: "08-17"
                  color: "#b0f4ff"
                  font.pixelSize: 8
                  font.family: "monospace"
                }
                MouseArea {
                  anchors.fill: parent
                  cursorShape: Qt.PointingHandCursor
                  onClicked: root.setWorktime("08:00-17:00")
                }
              }
            }
          }

          // Agenda items (scrollable)
          ScrollView {
            Layout.fillWidth: true
            Layout.fillHeight: true
            clip: true
            visible: root.midLeftTab === "agenda"

            ColumnLayout {
              width: modalBox.width - 36
              spacing: 6

              // Empty state
              Item {
                Layout.fillWidth: true
                height: 80
                visible: root.agendaList.length === 0
                ColumnLayout {
                  anchors.centerIn: parent
                  spacing: 4
                  Text {
                    text: "No calendar events scheduled for today."
                    color: Qt.rgba(1, 1, 1, 0.5)
                    font.pixelSize: 11
                    font.family: "monospace"
                    Layout.alignment: Qt.AlignHCenter
                  }
                  Text {
                    text: "Type below (e.g. '3pm Sync') or tell Milo to add an event."
                    color: Qt.rgba(0, 0.9, 1.0, 0.6)
                    font.pixelSize: 10
                    font.family: "monospace"
                    Layout.alignment: Qt.AlignHCenter
                  }
                }
              }

              Repeater {
                model: root.agendaList
                delegate: Rectangle {
                  required property var modelData
                  Layout.fillWidth: true
                  height: 48
                  radius: 7
                  color: modelData.is_active ? Qt.rgba(0, 0.9, 1.0, 0.18) : (modelData.is_past ? Qt.rgba(0.04, 0.06, 0.08, 0.5) : Qt.rgba(0.04, 0.10, 0.14, 0.75))
                  border.color: modelData.is_active ? "#00f0ff" : (modelData.is_past ? Qt.rgba(1, 1, 1, 0.12) : Qt.rgba(0, 0.8, 1.0, 0.3))
                  border.width: modelData.is_active ? 1.5 : 1.2

                  RowLayout {
                    anchors.fill: parent
                    anchors.leftMargin: 10
                    anchors.rightMargin: 10
                    spacing: 10

                    // Color stripe
                    Rectangle {
                      width: 4; height: 34; radius: 2
                      color: modelData.is_past ? Qt.rgba(1, 1, 1, 0.25) : (modelData.color || "#00f0ff")
                    }

                    // Time badge
                    Rectangle {
                      width: 58; height: 26; radius: 4
                      color: modelData.is_past ? Qt.rgba(0, 0, 0, 0.25) : Qt.rgba(0, 0, 0, 0.55)
                      border.color: modelData.is_past ? Qt.rgba(1, 1, 1, 0.2) : (modelData.color || "#00f0ff")
                      border.width: 1
                      Text {
                        anchors.centerIn: parent
                        text: modelData.event_time || "--:--"
                        color: modelData.is_past ? Qt.rgba(1, 1, 1, 0.4) : (modelData.color || "#00f0ff")
                        font.pixelSize: 11
                        font.bold: true
                        font.family: "monospace"
                      }
                    }

                    // Event Details
                    ColumnLayout {
                      Layout.fillWidth: true
                      spacing: 2

                      RowLayout {
                        spacing: 8
                        Text {
                          text: modelData.title || ""
                          color: modelData.is_past ? Qt.rgba(1, 1, 1, 0.4) : "#ffffff"
                          font.strikeout: modelData.is_past
                          font.pixelSize: 12
                          font.bold: !modelData.is_past
                          font.family: "system-ui, sans-serif"
                        }
                        Rectangle {
                          height: 14
                          width: catText.implicitWidth + 8
                          radius: 3
                          color: modelData.is_past ? Qt.rgba(1, 1, 1, 0.08) : Qt.rgba(0, 0.9, 1.0, 0.15)
                          Text {
                            id: catText
                            anchors.centerIn: parent
                            text: (modelData.category || "EVENT").toUpperCase()
                            color: modelData.is_past ? Qt.rgba(1, 1, 1, 0.4) : "#80f5ff"
                            font.pixelSize: 8
                            font.family: "monospace"
                          }
                        }
                      }

                      Text {
                        Layout.fillWidth: true
                        text: modelData.description ? modelData.description : ("Duration: " + (modelData.duration_min || 60) + "m")
                        color: Qt.rgba(1, 1, 1, 0.45)
                        font.pixelSize: 9
                        font.family: "system-ui, sans-serif"
                        elide: Text.ElideRight
                      }
                    }

                    // Status text pill
                    Rectangle {
                      height: 20
                      width: statusText.implicitWidth + 10
                      radius: 3
                      color: modelData.is_active ? Qt.rgba(0, 0.9, 1.0, 0.25) : (modelData.is_past ? Qt.rgba(0, 1.0, 0.5, 0.15) : Qt.rgba(1, 1, 1, 0.08))
                      border.color: modelData.is_active ? "#00f0ff" : "transparent"
                      border.width: 1
                      Text {
                        id: statusText
                        anchors.centerIn: parent
                        text: modelData.status_text || ""
                        color: modelData.is_active ? "#00f0ff" : (modelData.is_past ? Qt.rgba(0, 1.0, 0.5, 0.8) : Qt.rgba(1, 1, 1, 0.6))
                        font.pixelSize: 9
                        font.family: "monospace"
                      }
                    }

                    // Delete button
                    Rectangle {
                      width: 22; height: 22; radius: 4
                      color: Qt.rgba(1, 0.2, 0.3, 0.15)
                      border.color: Qt.rgba(1, 0.2, 0.3, 0.4)
                      border.width: 1
                      Text {
                        anchors.centerIn: parent
                        text: "×"
                        color: "#ff8899"
                        font.pixelSize: 14
                        font.bold: true
                      }
                      MouseArea {
                        anchors.fill: parent
                        cursorShape: Qt.PointingHandCursor
                        onClicked: root.removeAgendaEvent(modelData.id)
                      }
                    }
                  }
                }
              }
            }
          }

          // Add Event Input Box
          Rectangle {
            Layout.fillWidth: true
            height: 34
            radius: 7
            color: Qt.rgba(0.04, 0.12, 0.16, 0.90)
            border.color: modalAgendaInput.activeFocus ? "#00f0ff" : Qt.rgba(0, 0.8, 1.0, 0.5)
            border.width: 1.2
            visible: root.midLeftTab === "agenda"

            RowLayout {
              anchors.fill: parent
              anchors.leftMargin: 10
              anchors.rightMargin: 6
              spacing: 8

              Text { text: "📅"; font.pixelSize: 12 }

              TextInput {
                id: modalAgendaInput
                Layout.fillWidth: true
                activeFocusOnTab: false
                color: "#ffffff"
                font.pixelSize: 11
                font.family: "system-ui, sans-serif"
                clip: true
                selectByMouse: true
                selectionColor: "#00f0ff"

                Keys.priority: Keys.BeforeItem
                Keys.onPressed: function(event) {
                  if (event.key === Qt.Key_Escape) {
                    root.scratchpadModalOpen = false
                    event.accepted = true
                  } else if (event.key === Qt.Key_Tab || event.key === Qt.Key_Backtab) {
                    var isBack = (event.key === Qt.Key_Backtab || (event.modifiers & Qt.ShiftModifier))
                    if (isBack) {
                      root.midLeftTab = "tasks"
                      modalTaskInput.forceActiveFocus()
                    } else {
                      root.midLeftTab = "mail"
                      modalMailFocusScope.forceActiveFocus()
                    }
                    event.accepted = true
                  }
                }

                Text {
                  anchors.fill: parent
                  text: "Quick schedule: e.g. 'Tomorrow 2pm Code Review' or '17:00 Gym' and hit Enter..."
                  color: Qt.rgba(1, 1, 1, 0.40)
                  font.pixelSize: 11
                  font.family: "system-ui, sans-serif"
                  visible: !modalAgendaInput.text && !modalAgendaInput.activeFocus
                }

                onAccepted: {
                  var val = modalAgendaInput.text.trim()
                  if (val.length > 0) {
                    root.addAgendaQuick(val)
                    modalAgendaInput.text = ""
                  }
                }
              }

              Rectangle {
                width: 90; height: 24; radius: 4
                color: "#00f0ff"
                Text {
                  anchors.centerIn: parent
                  text: "ADD EVENT"
                  color: "#060102"
                  font.pixelSize: 10
                  font.bold: true
                  font.family: "monospace"
                }
                MouseArea {
                  anchors.fill: parent
                  cursorShape: Qt.PointingHandCursor
                  onClicked: {
                    var val = modalAgendaInput.text.trim()
                    if (val.length > 0) {
                      root.addAgendaQuick(val)
                      modalAgendaInput.text = ""
                    }
                  }
                }
              }
            }
          }

          // Milo AI Calendar Copilot Strip
          Rectangle {
            Layout.fillWidth: true
            height: 68
            radius: 8
            color: Qt.rgba(0.04, 0.08, 0.12, 0.75)
            border.color: Qt.rgba(0, 0.9, 1.0, 0.35)
            border.width: 1
            visible: root.midLeftTab === "agenda"

            ColumnLayout {
              anchors.fill: parent
              anchors.margins: 6
              spacing: 4

              RowLayout {
                Layout.fillWidth: true
                spacing: 6

                Text {
                  text: "🤖 MILO CALENDAR COPILOT"
                  color: "#00e5ff"
                  font.pixelSize: 9
                  font.bold: true
                  font.family: "monospace"
                }

                Item { Layout.fillWidth: true }

                // Quick AI Action Chips
                Repeater {
                  model: [
                    { label: "📅 Today?", q: "what is on my calendar today?" },
                    { label: "⏱ Next Event?", q: "what is my next upcoming event?" },
                    { label: "🎙 Briefing", q: "give me my daily calendar briefing" }
                  ]
                  delegate: Rectangle {
                    required property var modelData
                    height: 18
                    width: chipText2.implicitWidth + 10
                    radius: 3
                    color: Qt.rgba(0, 0.9, 1.0, 0.15)
                    border.color: Qt.rgba(0, 0.9, 1.0, 0.4)
                    border.width: 1
                    Text {
                      id: chipText2
                      anchors.centerIn: parent
                      text: modelData.label
                      color: "#b0f4ff"
                      font.pixelSize: 8
                      font.family: "monospace"
                    }
                    MouseArea {
                      anchors.fill: parent
                      cursorShape: Qt.PointingHandCursor
                      onClicked: {
                        root.askMilo(modelData.q)
                      }
                    }
                  }
                }
              }

              // Milo Speech / Chat Feedback snippet
              Text {
                Layout.fillWidth: true
                text: root.miloChatOutput ? root.miloChatOutput : "Ask Milo: 'What is on my calendar today?' or click a chip above."
                color: root.miloChatOutput ? "#ffffff" : Qt.rgba(1, 1, 1, 0.5)
                font.pixelSize: 9
                font.family: "system-ui, sans-serif"
                elide: Text.ElideRight
                wrapMode: Text.NoWrap
              }
            }
          }

          // ==================================================================
          // MODAL VIEW 3: GMAIL INBOX (visible when midLeftTab === "mail")
          // ==================================================================
          // 1. Mail Action Bar
          RowLayout {
            Layout.fillWidth: true
            spacing: 8
            visible: root.midLeftTab === "mail"

            Rectangle {
              height: 24
              width: mailUserBadge.implicitWidth + 14
              radius: 4
              color: Qt.rgba(1.0, 0.67, 0.0, 0.15)
              border.color: Qt.rgba(1.0, 0.67, 0.0, 0.4)
              border.width: 1

              Text {
                id: mailUserBadge
                anchors.centerIn: parent
                text: root.mailData && root.mailData.user ? ("👤 " + root.mailData.user) : "⚠ Gmail Not Configured"
                color: root.mailData && root.mailData.user ? "#ffd480" : "#ff8899"
                font.pixelSize: 10
                font.bold: true
                font.family: "monospace"
              }
            }

            Item { Layout.fillWidth: true }

            // Sync Button
            Rectangle {
              height: 24
              width: mailSyncLabel.implicitWidth + 14
              radius: 4
              color: Qt.rgba(0.08, 0.14, 0.2, 0.6)
              border.color: Qt.rgba(1.0, 0.67, 0.0, 0.4)
              border.width: 1

              Text {
                id: mailSyncLabel
                anchors.centerIn: parent
                text: "🔄 Sync"
                color: "#ffffff"
                font.pixelSize: 9
                font.family: "monospace"
              }
              MouseArea {
                anchors.fill: parent
                cursorShape: Qt.PointingHandCursor
                onClicked: root.mailSync()
              }
            }

            // AI Briefing Button
            Rectangle {
              height: 24
              width: mailBriefLabel.implicitWidth + 14
              radius: 4
              color: Qt.rgba(1.0, 0.67, 0.0, 0.2)
              border.color: "#ffaa00"
              border.width: 1

              Text {
                id: mailBriefLabel
                anchors.centerIn: parent
                text: "✦ AI Briefing"
                color: "#ffaa00"
                font.pixelSize: 9
                font.bold: true
                font.family: "monospace"
              }
              MouseArea {
                anchors.fill: parent
                cursorShape: Qt.PointingHandCursor
                onClicked: root.mailSummarize()
              }
            }

            // Open Webmail Button
            Rectangle {
              height: 24
              width: mailWebLabel.implicitWidth + 14
              radius: 4
              color: Qt.rgba(0.2, 0.05, 0.08, 0.6)
              border.color: Qt.rgba(1, 0.2, 0.3, 0.4)
              border.width: 1

              Text {
                id: mailWebLabel
                anchors.centerIn: parent
                text: "🌐 Webmail"
                color: Qt.rgba(1, 1, 1, 0.8)
                font.pixelSize: 9
                font.family: "monospace"
              }
              MouseArea {
                anchors.fill: parent
                cursorShape: Qt.PointingHandCursor
                onClicked: root.mailOpenWeb()
              }
            }
          }

          // 2. Email List ScrollView
          ScrollView {
            Layout.fillWidth: true
            Layout.fillHeight: true
            clip: true
            visible: root.midLeftTab === "mail"

            ColumnLayout {
              width: modalBox.width - 36
              spacing: 6

              // Empty or Not Configured State
              Item {
                Layout.fillWidth: true
                height: 240
                visible: !root.mailData || !root.mailData.user || !root.mailData.emails || root.mailData.emails.length === 0

                Rectangle {
                  anchors.centerIn: parent
                  width: Math.min(520, parent.width - 20)
                  height: 220
                  radius: 10
                  color: Qt.rgba(0.08, 0.05, 0.02, 0.8)
                  border.color: (!root.mailData || !root.mailData.user) ? Qt.rgba(1.0, 0.67, 0.0, 0.4) : Qt.rgba(0, 1.0, 0.5, 0.4)
                  border.width: 1.2

                  ColumnLayout {
                    anchors.fill: parent
                    anchors.margins: 16
                    spacing: 8

                    Text {
                      text: (!root.mailData || !root.mailData.user) ? "✉ GMAIL SETUP (Option A: 60-Second Setup)" : "✔ INBOX ZERO"
                      color: (!root.mailData || !root.mailData.user) ? "#ffaa00" : "#00ff88"
                      font.pixelSize: 13
                      font.bold: true
                      font.family: "monospace"
                    }

                    Text {
                      Layout.fillWidth: true
                      text: (!root.mailData || !root.mailData.user) ?
                        "Connect your Gmail to Milo using a Google App Password:\n\n" +
                        "1. Open https://myaccount.google.com/apppasswords\n" +
                        "2. Create an App Password for 'Milo' (16 characters)\n" +
                        "3. Save to ~/.config/milo/mail.env:\n" +
                        "     GMAIL_USER=\"youremail@gmail.com\"\n" +
                        "     GMAIL_APP_PASSWORD=\"xxxx xxxx xxxx xxxx\"\n" +
                        "4. Click [ 🔄 Sync ] above or run 'milo-mail status'" :
                        "All clear! Zero unread emails in your Gmail inbox.\n\nMilo will notify you automatically when new emails arrive."
                      color: Qt.rgba(1, 1, 1, 0.8)
                      font.pixelSize: 10
                      font.family: "system-ui, sans-serif"
                      wrapMode: Text.Wrap
                    }

                    Item { Layout.fillHeight: true }

                    RowLayout {
                      spacing: 8
                      Rectangle {
                        visible: !root.mailData || !root.mailData.user
                        height: 26
                        width: secBtnLabel.implicitWidth + 16
                        radius: 4
                        color: "#ffaa00"
                        Text {
                          id: secBtnLabel
                          anchors.centerIn: parent
                          text: "🔑 Open Google Security Settings"
                          color: "#060102"
                          font.pixelSize: 10
                          font.bold: true
                          font.family: "monospace"
                        }
                        MouseArea {
                          anchors.fill: parent
                          cursorShape: Qt.PointingHandCursor
                          onClicked: {
                            if (quickCmdProc.running) quickCmdProc.running = false
                            quickCmdProc.command = ["xdg-open", "https://myaccount.google.com/apppasswords"]
                            quickCmdProc.running = true
                          }
                        }
                      }

                      Rectangle {
                        height: 26
                        width: testBtnLabel.implicitWidth + 16
                        radius: 4
                        color: Qt.rgba(1, 1, 1, 0.12)
                        border.color: Qt.rgba(1, 1, 1, 0.3)
                        border.width: 1
                        Text {
                          id: testBtnLabel
                          anchors.centerIn: parent
                          text: "🔄 Test Connection"
                          color: "#ffffff"
                          font.pixelSize: 10
                          font.family: "monospace"
                        }
                        MouseArea {
                          anchors.fill: parent
                          cursorShape: Qt.PointingHandCursor
                          onClicked: root.mailSync()
                        }
                      }
                    }
                  }
                }
              }

              // Email Cards Repeater
              Repeater {
                model: root.mailData && root.mailData.emails ? root.mailData.emails : []
                delegate: Rectangle {
                  required property var modelData
                  required property int index
                  Layout.fillWidth: true
                  height: 56
                  radius: 7
                  color: Qt.rgba(0.12, 0.08, 0.02, 0.75)
                  border.color: Qt.rgba(1.0, 0.67, 0.0, 0.35)
                  border.width: 1

                  ColumnLayout {
                    anchors.fill: parent
                    anchors.margins: 8
                    spacing: 3

                    RowLayout {
                      Layout.fillWidth: true
                      spacing: 6

                      Text {
                        text: "✉"
                        color: "#ffaa00"
                        font.pixelSize: 10
                      }

                      Text {
                        text: modelData.from || "Unknown Sender"
                        color: "#ffd480"
                        font.pixelSize: 10
                        font.bold: true
                        font.family: "system-ui, sans-serif"
                        elide: Text.ElideRight
                        Layout.maximumWidth: 220
                      }

                      Item { Layout.fillWidth: true }

                      Text {
                        text: modelData.time_rel || ""
                        color: Qt.rgba(1, 1, 1, 0.45)
                        font.pixelSize: 9
                        font.family: "monospace"
                      }
                    }

                    Text {
                      Layout.fillWidth: true
                      text: modelData.subject || "(No Subject)"
                      color: "#ffffff"
                      font.pixelSize: 10
                      font.bold: true
                      font.family: "system-ui, sans-serif"
                      elide: Text.ElideRight
                    }

                    Text {
                      Layout.fillWidth: true
                      text: modelData.snippet || ""
                      color: Qt.rgba(1, 1, 1, 0.5)
                      font.pixelSize: 9
                      font.family: "system-ui, sans-serif"
                      elide: Text.ElideRight
                    }
                  }

                  MouseArea {
                    anchors.fill: parent
                    cursorShape: Qt.PointingHandCursor
                    onClicked: {
                      quickCmdProc.command = ["foot", "-a", "milo-floating", "-T", "MILO // Email #" + modelData.id, root.homeDir + "/.local/bin/milo-mail", "read", modelData.id]
                      quickCmdProc.running = true
                    }
                  }
                }
              }
            }
          }

          // 3. Milo AI Mail Copilot Strip & Modal Mail Focus Scope
          Rectangle {
            id: modalMailFocusScope
            Layout.fillWidth: true
            height: 68
            radius: 8
            color: activeFocus ? Qt.rgba(0.14, 0.09, 0.02, 0.95) : Qt.rgba(0.08, 0.05, 0.02, 0.75)
            border.color: activeFocus ? "#ffaa00" : Qt.rgba(1.0, 0.67, 0.0, 0.35)
            border.width: activeFocus ? 1.5 : 1
            visible: root.midLeftTab === "mail"
            focus: root.midLeftTab === "mail"

            Keys.priority: Keys.BeforeItem
            Keys.onPressed: function(event) {
              if (event.key === Qt.Key_Escape) {
                root.scratchpadModalOpen = false
                event.accepted = true
              } else if (event.key === Qt.Key_Tab || event.key === Qt.Key_Backtab) {
                var isBack = (event.key === Qt.Key_Backtab || (event.modifiers & Qt.ShiftModifier))
                if (isBack) {
                  root.midLeftTab = "agenda"
                  modalAgendaInput.forceActiveFocus()
                } else {
                  root.midLeftTab = "whatsapp"
                  modalWaFocusScope.forceActiveFocus()
                }
                event.accepted = true
              } else if (event.key === Qt.Key_Return || event.key === Qt.Key_Enter) {
                root.mailSummarize()
                event.accepted = true
              } else if (event.key === Qt.Key_R && (event.modifiers & Qt.ControlModifier)) {
                root.mailSync()
                event.accepted = true
              }
            }

            ColumnLayout {
              anchors.fill: parent
              anchors.margins: 6
              spacing: 4

              RowLayout {
                Layout.fillWidth: true
                spacing: 6

                Text {
                  text: "🤖 MILO GMAIL COPILOT"
                  color: "#ffaa00"
                  font.pixelSize: 9
                  font.bold: true
                  font.family: "monospace"
                }

                Item { Layout.fillWidth: true }

                Repeater {
                  model: [
                    { label: "🎙 AI Briefing", cmd: "summarize" },
                    { label: "🔄 Sync Now", cmd: "sync" },
                    { label: "📋 Terminal List", cmd: "list" }
                  ]
                  delegate: Rectangle {
                    required property var modelData
                    height: 18
                    width: chipMailText.implicitWidth + 10
                    radius: 3
                    color: Qt.rgba(1.0, 0.67, 0.0, 0.15)
                    border.color: Qt.rgba(1.0, 0.67, 0.0, 0.4)
                    border.width: 1
                    Text {
                      id: chipMailText
                      anchors.centerIn: parent
                      text: modelData.label
                      color: "#ffd480"
                      font.pixelSize: 8
                      font.family: "monospace"
                    }
                    MouseArea {
                      anchors.fill: parent
                      cursorShape: Qt.PointingHandCursor
                      onClicked: {
                        if (modelData.cmd === "summarize") {
                          root.mailSummarize()
                        } else if (modelData.cmd === "sync") {
                          root.mailSync()
                        } else {
                          quickCmdProc.command = ["foot", "-a", "milo-floating", "-T", "MILO // Gmail Inbox", root.homeDir + "/.local/bin/milo-mail", "list"]
                          quickCmdProc.running = true
                        }
                      }
                    }
                  }
                }
              }

              Text {
                Layout.fillWidth: true
                text: "Say: 'Milo, check my mail' or 'Milo, summarize my unread emails' for instant voice triage."
                color: Qt.rgba(1, 1, 1, 0.5)
                font.pixelSize: 9
                font.family: "system-ui, sans-serif"
                elide: Text.ElideRight
              }
            }
          }

          // ==================================================================
          // MODAL VIEW 4: WHATSAPP CHATS (visible when midLeftTab === "whatsapp")
          // ==================================================================
          // 1. WhatsApp Action Bar
          RowLayout {
            Layout.fillWidth: true
            spacing: 8
            visible: root.midLeftTab === "whatsapp"

            Rectangle {
              height: 24
              width: waUserBadge.implicitWidth + 14
              radius: 4
              color: Qt.rgba(0.15, 0.83, 0.40, 0.15)
              border.color: Qt.rgba(0.15, 0.83, 0.40, 0.4)
              border.width: 1

              Text {
                id: waUserBadge
                anchors.centerIn: parent
                text: root.whatsappData && root.whatsappData.phone ? ("● " + (root.whatsappData.pushName ? root.whatsappData.pushName + " (" + root.whatsappData.phone + ")" : root.whatsappData.phone)) : (root.whatsappData && root.whatsappData.status === "ready" ? "● Ready" : "⚠ WhatsApp Offline")
                color: root.whatsappData && (root.whatsappData.status === "ready" || root.whatsappData.phone) ? "#25d366" : "#ff8899"
                font.pixelSize: 10
                font.bold: true
                font.family: "monospace"
              }
            }

            Item { Layout.fillWidth: true }

            // Sync Button
            Rectangle {
              height: 24
              width: waSyncLabel.implicitWidth + 14
              radius: 4
              color: Qt.rgba(0.08, 0.14, 0.2, 0.6)
              border.color: Qt.rgba(0.15, 0.83, 0.40, 0.4)
              border.width: 1

              Text {
                id: waSyncLabel
                anchors.centerIn: parent
                text: "🔄 Sync"
                color: "#ffffff"
                font.pixelSize: 9
                font.family: "monospace"
              }
              MouseArea {
                anchors.fill: parent
                cursorShape: Qt.PointingHandCursor
                onClicked: root.whatsappSync()
              }
            }

            // AI Briefing Button
            Rectangle {
              height: 24
              width: waBriefLabel.implicitWidth + 14
              radius: 4
              color: Qt.rgba(0.15, 0.83, 0.40, 0.2)
              border.color: "#25d366"
              border.width: 1

              Text {
                id: waBriefLabel
                anchors.centerIn: parent
                text: "✦ AI Briefing"
                color: "#25d366"
                font.pixelSize: 9
                font.bold: true
                font.family: "monospace"
              }
              MouseArea {
                anchors.fill: parent
                cursorShape: Qt.PointingHandCursor
                onClicked: root.whatsappSummarize()
              }
            }

            // Link QR Button
            Rectangle {
              height: 24
              width: waQrLabel.implicitWidth + 14
              radius: 4
              color: Qt.rgba(0.04, 0.16, 0.08, 0.6)
              border.color: Qt.rgba(0.15, 0.83, 0.40, 0.4)
              border.width: 1

              Text {
                id: waQrLabel
                anchors.centerIn: parent
                text: "📱 Link Device"
                color: Qt.rgba(1, 1, 1, 0.8)
                font.pixelSize: 9
                font.family: "monospace"
              }
              MouseArea {
                anchors.fill: parent
                cursorShape: Qt.PointingHandCursor
                onClicked: root.whatsappLinkQR()
              }
            }
          }

          // 2. WhatsApp List ScrollView
          ScrollView {
            Layout.fillWidth: true
            Layout.fillHeight: true
            clip: true
            visible: root.midLeftTab === "whatsapp"

            ColumnLayout {
              width: modalBox.width - 36
              spacing: 6

              // Empty or Not Linked State
              Item {
                Layout.fillWidth: true
                height: 240
                visible: !root.whatsappData || !root.whatsappData.chats || root.whatsappData.chats.length === 0

                Rectangle {
                  anchors.centerIn: parent
                  width: Math.min(520, parent.width - 20)
                  height: 220
                  radius: 10
                  color: Qt.rgba(0.02, 0.08, 0.04, 0.8)
                  border.color: Qt.rgba(0.15, 0.83, 0.40, 0.4)
                  border.width: 1.2

                  ColumnLayout {
                    anchors.fill: parent
                    anchors.margins: 16
                    spacing: 8

                    Text {
                      text: "💬 WHATSAPP LINK & SETUP"
                      color: "#25d366"
                      font.pixelSize: 13
                      font.bold: true
                      font.family: "monospace"
                    }

                    Text {
                      Layout.fillWidth: true
                      text: "Link your WhatsApp to Milo using Baileys QR Code:\n\n" +
                            "1. Click [ 📱 Link Device ] above or run 'milo wa qr'\n" +
                            "2. Open WhatsApp on your phone > Linked Devices > Link a Device\n" +
                            "3. Scan the QR code displayed in the terminal\n" +
                            "4. Milo will securely maintain your private AI chat assistant and inbox cache."
                      color: Qt.rgba(1, 1, 1, 0.8)
                      font.pixelSize: 10
                      font.family: "system-ui, sans-serif"
                      wrapMode: Text.Wrap
                    }

                    Item { Layout.fillHeight: true }

                    RowLayout {
                      spacing: 8
                      Rectangle {
                        height: 26
                        width: waLinkBtnLabel.implicitWidth + 16
                        radius: 4
                        color: "#25d366"
                        Text {
                          id: waLinkBtnLabel
                          anchors.centerIn: parent
                          text: "📱 Link Device via QR"
                          color: "#060102"
                          font.pixelSize: 10
                          font.bold: true
                        }
                        MouseArea {
                          anchors.fill: parent
                          cursorShape: Qt.PointingHandCursor
                          onClicked: root.whatsappLinkQR()
                        }
                      }
                    }
                  }
                }
              }

              // WhatsApp Chat Cards Repeater
              Repeater {
                model: root.whatsappData && root.whatsappData.chats ? root.whatsappData.chats : []
                delegate: Rectangle {
                  required property var modelData
                  required property int index
                  Layout.fillWidth: true
                  height: 56
                  radius: 7
                  color: Qt.rgba(0.02, 0.10, 0.05, 0.75)
                  border.color: modelData.unread > 0 ? "#25d366" : Qt.rgba(0.15, 0.83, 0.40, 0.35)
                  border.width: modelData.unread > 0 ? 1.5 : 1

                  ColumnLayout {
                    anchors.fill: parent
                    anchors.margins: 8
                    spacing: 3

                    RowLayout {
                      Layout.fillWidth: true
                      spacing: 6

                      Text {
                        text: modelData.is_group ? "👥" : "👤"
                        color: "#25d366"
                        font.pixelSize: 10
                      }

                      Text {
                        text: modelData.name || "Unknown Contact"
                        color: modelData.unread > 0 ? "#25d366" : "#a8f5c8"
                        font.pixelSize: 10
                        font.bold: true
                        font.family: "system-ui, sans-serif"
                        elide: Text.ElideRight
                        Layout.maximumWidth: 220
                      }

                      Item { Layout.fillWidth: true }

                      // Unread badge
                      Rectangle {
                        visible: modelData.unread > 0
                        height: 14
                        width: modalWaBadgeText.implicitWidth + 8
                        radius: 3
                        color: "#25d366"
                        Text {
                          id: modalWaBadgeText
                          anchors.centerIn: parent
                          text: modelData.unread ? (modelData.unread + " NEW") : ""
                          color: "#060102"
                          font.pixelSize: 8
                          font.bold: true
                          font.family: "monospace"
                        }
                      }

                      Text {
                        text: modelData.time || ""
                        color: Qt.rgba(1, 1, 1, 0.45)
                        font.pixelSize: 9
                        font.family: "monospace"
                      }
                    }

                    Text {
                      Layout.fillWidth: true
                      text: modelData.snippet || "(No message content)"
                      color: "#ffffff"
                      font.pixelSize: 9
                      font.family: "system-ui, sans-serif"
                      elide: Text.ElideRight
                    }
                  }

                  MouseArea {
                    anchors.fill: parent
                    cursorShape: Qt.PointingHandCursor
                    onClicked: root.whatsappReadChat(modelData.index || (index + 1))
                  }
                }
              }
            }
          }

          // 3. Milo AI WhatsApp Copilot Strip & Modal WhatsApp Focus Scope
          Rectangle {
            id: modalWaFocusScope
            Layout.fillWidth: true
            height: 68
            radius: 8
            color: activeFocus ? Qt.rgba(0.04, 0.16, 0.08, 0.95) : Qt.rgba(0.02, 0.10, 0.05, 0.75)
            border.color: activeFocus ? "#25d366" : Qt.rgba(0.15, 0.83, 0.40, 0.35)
            border.width: activeFocus ? 1.5 : 1
            visible: root.midLeftTab === "whatsapp"
            focus: root.midLeftTab === "whatsapp"

            Keys.priority: Keys.BeforeItem
            Keys.onPressed: function(event) {
              if (event.key === Qt.Key_Escape) {
                root.scratchpadModalOpen = false
                event.accepted = true
              } else if (event.key === Qt.Key_Tab || event.key === Qt.Key_Backtab) {
                var isBack = (event.key === Qt.Key_Backtab || (event.modifiers & Qt.ShiftModifier))
                if (isBack) {
                  root.midLeftTab = "mail"
                  modalMailFocusScope.forceActiveFocus()
                } else {
                  root.midLeftTab = "tasks"
                  modalTaskInput.forceActiveFocus()
                }
                event.accepted = true
              } else if (event.key === Qt.Key_Return || event.key === Qt.Key_Enter) {
                root.whatsappSummarize()
                event.accepted = true
              } else if (event.key === Qt.Key_R && (event.modifiers & Qt.ControlModifier)) {
                root.whatsappSync()
                event.accepted = true
              }
            }

            ColumnLayout {
              anchors.fill: parent
              anchors.margins: 6
              spacing: 4

              RowLayout {
                Layout.fillWidth: true
                spacing: 6

                Text {
                  text: "💬 MILO WHATSAPP COPILOT"
                  color: "#25d366"
                  font.pixelSize: 9
                  font.bold: true
                  font.family: "monospace"
                }

                Item { Layout.fillWidth: true }

                Repeater {
                  model: [
                    { label: "🎙 AI Briefing", cmd: "summarize" },
                    { label: "🔄 Sync Now", cmd: "sync" },
                    { label: "📱 Link Device", cmd: "qr" },
                    { label: "📋 Terminal List", cmd: "list" }
                  ]
                  delegate: Rectangle {
                    required property var modelData
                    height: 18
                    width: chipWaText.implicitWidth + 10
                    radius: 3
                    color: Qt.rgba(0.15, 0.83, 0.40, 0.15)
                    border.color: Qt.rgba(0.15, 0.83, 0.40, 0.4)
                    border.width: 1
                    Text {
                      id: chipWaText
                      anchors.centerIn: parent
                      text: modelData.label
                      color: "#25d366"
                      font.pixelSize: 8
                      font.family: "monospace"
                    }
                    MouseArea {
                      anchors.fill: parent
                      cursorShape: Qt.PointingHandCursor
                      onClicked: {
                        if (modelData.cmd === "summarize") {
                          root.whatsappSummarize()
                        } else if (modelData.cmd === "sync") {
                          root.whatsappSync()
                        } else if (modelData.cmd === "qr") {
                          root.whatsappLinkQR()
                        } else {
                          quickCmdProc.command = ["foot", "-a", "milo-floating", "-T", "MILO // WhatsApp Inbox", root.homeDir + "/.local/bin/milo-wa", "list"]
                          quickCmdProc.running = true
                        }
                      }
                    }
                  }
                }
              }

              Text {
                Layout.fillWidth: true
                text: "Say: 'Milo, check WhatsApp' or 'Milo, summarize my WhatsApp' or 'Milo, send WhatsApp message to ...'"
                color: Qt.rgba(1, 1, 1, 0.5)
                font.pixelSize: 9
                font.family: "system-ui, sans-serif"
                elide: Text.ElideRight
              }
            }
          }
        }
      }
    }
  }
}

  // ==========================================================================
  // 7. MILO TACTICAL CONTROL CENTER OVERLAY (Option B Native Linux Overlay)
  // WlrLayer.Overlay centered glassmorphic hardware rack & telemetry hub
  // ==========================================================================
  Variants {
    model: Quickshell.screens

    PanelWindow {
      id: controlCenterPanel
      required property var modelData
      screen: modelData
      visible: root.controlCenterOpen

      anchors {
        top: true
        bottom: true
        left: true
        right: true
      }

      color: "transparent"
      exclusionMode: ExclusionMode.Ignore
      WlrLayershell.namespace: "milo-control-center"
      WlrLayershell.layer: WlrLayer.Overlay
      WlrLayershell.keyboardFocus: root.controlCenterOpen ? WlrKeyboardFocus.Exclusive : WlrKeyboardFocus.None

      onVisibleChanged: {
        if (visible) {
          root.refreshControlCenter()
          ccFocusScope.forceActiveFocus()
        }
      }

      // Background Scrim (click to dismiss)
      Rectangle {
        anchors.fill: parent
        color: Qt.rgba(0, 0, 0, 0.68)
        MouseArea {
          anchors.fill: parent
          onClicked: root.controlCenterOpen = false
        }
      }

      FocusScope {
        id: ccFocusScope
        anchors.fill: parent
        focus: root.controlCenterOpen

        Keys.priority: Keys.BeforeItem
        Keys.onPressed: function(event) {
          if (event.key === Qt.Key_Escape) {
            if (root.ccWifiScannerOpen) {
              root.ccWifiScannerOpen = false
              root.ccWifiShowPasswordInput = false
              event.accepted = true
            } else if (root.ccBtScannerOpen) {
              root.ccBtScannerOpen = false
              event.accepted = true
            } else {
              root.controlCenterOpen = false
              event.accepted = true
            }
          }
        }

        // Centered Tactical Control Capsule Box
        Rectangle {
          id: ccBox
          width: Math.min(parent.width - 60, 880)
          height: Math.min(parent.height - 60, 680)
          anchors.centerIn: parent
          radius: 16
          color: Qt.rgba(14/255, 5/255, 9/255, 0.94)
          border.color: Qt.rgba(255/255, 8/255, 56/255, 0.50)
          border.width: 1

          // Neon Red Top Accent Line
          Rectangle {
            anchors.top: parent.top
            anchors.left: parent.left
            anchors.right: parent.right
            anchors.leftMargin: 20
            anchors.rightMargin: 20
            height: 2
            color: "#ff0838"
          }

          // Corner Brackets
          Rectangle { x: 8; y: 8; width: 12; height: 2; color: "#ff0838" }
          Rectangle { x: 8; y: 8; width: 2; height: 12; color: "#ff0838" }
          Rectangle { x: parent.width - 20; y: 8; width: 12; height: 2; color: "#ff0838" }
          Rectangle { x: parent.width - 10; y: 8; width: 2; height: 12; color: "#ff0838" }
          Rectangle { x: 8; y: parent.height - 10; width: 12; height: 2; color: "#ff0838" }
          Rectangle { x: 8; y: parent.height - 20; width: 2; height: 12; color: "#ff0838" }
          Rectangle { x: parent.width - 20; y: parent.height - 10; width: 12; height: 2; color: "#ff0838" }
          Rectangle { x: parent.width - 10; y: parent.height - 20; width: 2; height: 12; color: "#ff0838" }

          ColumnLayout {
            id: ccMainView
            anchors.fill: parent
            anchors.margins: 24
            spacing: 16
            visible: !root.ccWifiScannerOpen && !root.ccBtScannerOpen

            // HEADER
            RowLayout {
              Layout.fillWidth: true
              spacing: 12

              ColumnLayout {
                spacing: 3
                RowLayout {
                  spacing: 10
                  Text {
                    text: "TACTICAL CONTROL CENTER"
                    color: "#ffffff"
                    font.pixelSize: 15
                    font.bold: true
                    font.family: "monospace"
                    font.letterSpacing: 1.5
                  }
                  Rectangle {
                    height: 18
                    width: 76
                    radius: 3
                    color: "#ff0838"
                    Text {
                      anchors.centerIn: parent
                      text: "OPTION B"
                      color: "#000000"
                      font.pixelSize: 9
                      font.bold: true
                      font.family: "monospace"
                    }
                  }
                }
                Text {
                  text: "Unified Hardware Rack & Instant Telemetry Overlay // Jeffy Protocol"
                  color: Qt.rgba(1, 1, 1, 0.5)
                  font.pixelSize: 10
                  font.family: "monospace"
                }
              }

              Item { Layout.fillWidth: true }

              // Esc to close badge & Close button
              Rectangle {
                height: 24
                width: 78
                radius: 4
                color: Qt.rgba(0, 0, 0, 0.5)
                border.color: Qt.rgba(1, 1, 1, 0.15)
                Text {
                  anchors.centerIn: parent
                  text: "ESC to close"
                  color: Qt.rgba(1, 1, 1, 0.45)
                  font.pixelSize: 9
                  font.family: "monospace"
                }
              }

              Rectangle {
                width: 30
                height: 30
                radius: 15
                color: closeCcArea.containsMouse ? "#ff0838" : Qt.rgba(1.0, 0.03, 0.22, 0.15)
                border.color: "#ff0838"
                border.width: 1

                Text {
                  anchors.centerIn: parent
                  text: "✕"
                  color: closeCcArea.containsMouse ? "#000000" : "#ff0838"
                  font.pixelSize: 12
                  font.bold: true
                }

                MouseArea {
                  id: closeCcArea
                  anchors.fill: parent
                  hoverEnabled: true
                  cursorShape: Qt.PointingHandCursor
                  onClicked: root.controlCenterOpen = false
                }
              }
            }

            // ROW 1: MASTER AUDIO & DISPLAY BRIGHTNESS SLIDERS
            RowLayout {
              Layout.fillWidth: true
              spacing: 16

              // CARD 1: MASTER AUDIO
              Rectangle {
                Layout.fillWidth: true
                Layout.preferredHeight: 185
                radius: 10
                color: Qt.rgba(26/255, 8/255, 15/255, 0.70)
                border.color: Qt.rgba(255/255, 8/255, 56/255, 0.30)
                border.width: 1

                ColumnLayout {
                  anchors.fill: parent
                  anchors.margins: 14
                  spacing: 10

                  RowLayout {
                    Layout.fillWidth: true
                    Text {
                      text: "🔊  MASTER AUDIO"
                      color: "#ffffff"
                      font.pixelSize: 12
                      font.bold: true
                      font.family: "monospace"
                    }
                    Item { Layout.fillWidth: true }
                    Rectangle {
                      height: 22
                      width: 50
                      radius: 4
                      color: Qt.rgba(1.0, 0.03, 0.22, 0.20)
                      border.color: "#ff0838"
                      Text {
                        anchors.centerIn: parent
                        text: (root.ccMuted ? "MUTED" : root.ccVolume + "%")
                        color: "#ff2a55"
                        font.pixelSize: 11
                        font.bold: true
                        font.family: "monospace"
                      }
                    }
                  }

                  RowLayout {
                    Layout.fillWidth: true
                    Text {
                      text: (root.ccMuted ? "Audio Output Silenced" : ((root.ccVolume == 0 ? "-∞" : Math.round((root.ccVolume - 100) * 0.5)) + " dB Output Level"))
                      color: Qt.rgba(1, 1, 1, 0.45)
                      font.pixelSize: 10
                      font.family: "monospace"
                    }
                    Item { Layout.fillWidth: true }
                    Text {
                      text: root.ccMuted ? "MUTED [ON]" : "MUTE [OFF]"
                      color: root.ccMuted ? Qt.rgba(1, 1, 1, 0.4) : "#ff0838"
                      font.pixelSize: 10
                      font.bold: true
                      font.family: "monospace"
                      MouseArea {
                        anchors.fill: parent
                        cursorShape: Qt.PointingHandCursor
                        onClicked: root.toggleCcMute()
                      }
                    }
                  }

                  // Custom Slider
                  Slider {
                    id: ccVolSlider
                    Layout.fillWidth: true
                    from: 0
                    to: 100
                    value: root.ccVolume
                    stepSize: 1
                    onMoved: root.setCcVolume(value)

                    background: Rectangle {
                      x: ccVolSlider.leftPadding
                      y: ccVolSlider.topPadding + ccVolSlider.availableHeight / 2 - height / 2
                      implicitWidth: 200
                      implicitHeight: 8
                      width: ccVolSlider.availableWidth
                      height: implicitHeight
                      radius: 4
                      color: Qt.rgba(1, 1, 1, 0.08)

                      Rectangle {
                        width: ccVolSlider.visualPosition * parent.width
                        height: parent.height
                        color: "#ff0838"
                        radius: 4
                      }
                    }

                    handle: Rectangle {
                      x: ccVolSlider.leftPadding + ccVolSlider.visualPosition * (ccVolSlider.availableWidth - width)
                      y: ccVolSlider.topPadding + ccVolSlider.availableHeight / 2 - height / 2
                      implicitWidth: 18
                      implicitHeight: 18
                      radius: 9
                      color: "#ffffff"
                      border.color: "#ff0838"
                      border.width: 3
                    }
                  }

                  // Equalizer animated wave
                  Row {
                    Layout.fillWidth: true
                    height: 12
                    spacing: 4
                    Repeater {
                      model: 24
                      Rectangle {
                        width: Math.max(3, (parent.width - 24 * 4) / 24)
                        height: root.ccMuted ? 3 : Math.max(3, Math.min(12, Math.floor(Math.sin((index + ccVolTimer.tick) * 0.5) * 6 + 6) * (root.ccVolume / 100)))
                        color: Qt.rgba(1.0, 0.03, 0.22, 0.65)
                        radius: 1
                        anchors.bottom: parent.bottom
                      }
                    }
                  }

                  // Preset chips
                  RowLayout {
                    Layout.fillWidth: true
                    spacing: 8
                    Repeater {
                      model: [25, 50, 75, 100]
                      Rectangle {
                        Layout.fillWidth: true
                        height: 22
                        radius: 4
                        color: root.ccVolume === modelData ? Qt.rgba(1.0, 0.03, 0.22, 0.35) : Qt.rgba(1, 1, 1, 0.05)
                        border.color: root.ccVolume === modelData ? "#ff0838" : Qt.rgba(1, 1, 1, 0.1)
                        Text {
                          anchors.centerIn: parent
                          text: modelData + "%"
                          color: root.ccVolume === modelData ? "#ff2a55" : Qt.rgba(1, 1, 1, 0.6)
                          font.pixelSize: 10
                          font.bold: true
                          font.family: "monospace"
                        }
                        MouseArea {
                          anchors.fill: parent
                          cursorShape: Qt.PointingHandCursor
                          onClicked: root.setCcVolume(modelData)
                        }
                      }
                    }
                  }
                }
              }

              // CARD 2: DISPLAY BRIGHTNESS
              Rectangle {
                Layout.fillWidth: true
                Layout.preferredHeight: 185
                radius: 10
                color: Qt.rgba(26/255, 8/255, 15/255, 0.70)
                border.color: Qt.rgba(255/255, 8/255, 56/255, 0.30)
                border.width: 1

                ColumnLayout {
                  anchors.fill: parent
                  anchors.margins: 14
                  spacing: 10

                  RowLayout {
                    Layout.fillWidth: true
                    Text {
                      text: "☀️  DISPLAY BRIGHTNESS"
                      color: "#ffffff"
                      font.pixelSize: 12
                      font.bold: true
                      font.family: "monospace"
                    }
                    Item { Layout.fillWidth: true }
                    Rectangle {
                      height: 22
                      width: 50
                      radius: 4
                      color: Qt.rgba(1.0, 0.6, 0.0, 0.20)
                      border.color: "#ffaa00"
                      Text {
                        anchors.centerIn: parent
                        text: root.ccBrightness + "%"
                        color: "#ffaa00"
                        font.pixelSize: 11
                        font.bold: true
                        font.family: "monospace"
                      }
                    }
                  }

                  RowLayout {
                    Layout.fillWidth: true
                    Text {
                      text: (root.ccBrightness * 5) + " cd/m² · QHD 240Hz"
                      color: Qt.rgba(1, 1, 1, 0.45)
                      font.pixelSize: 10
                      font.family: "monospace"
                    }
                    Item { Layout.fillWidth: true }
                    Text {
                      text: "AUTO-LUX: OFF"
                      color: "#00ff88"
                      font.pixelSize: 10
                      font.bold: true
                      font.family: "monospace"
                    }
                  }

                  // Custom Brightness Slider
                  Slider {
                    id: ccBrightSlider
                    Layout.fillWidth: true
                    from: 10
                    to: 100
                    value: root.ccBrightness
                    stepSize: 1
                    onMoved: root.setCcBrightness(value)

                    background: Rectangle {
                      x: ccBrightSlider.leftPadding
                      y: ccBrightSlider.topPadding + ccBrightSlider.availableHeight / 2 - height / 2
                      implicitWidth: 200
                      implicitHeight: 8
                      width: ccBrightSlider.availableWidth
                      height: implicitHeight
                      radius: 4
                      color: Qt.rgba(1, 1, 1, 0.08)

                      Rectangle {
                        width: ccBrightSlider.visualPosition * parent.width
                        height: parent.height
                        color: "#ffaa00"
                        radius: 4
                      }
                    }

                    handle: Rectangle {
                      x: ccBrightSlider.leftPadding + ccBrightSlider.visualPosition * (ccBrightSlider.availableWidth - width)
                      y: ccBrightSlider.topPadding + ccBrightSlider.availableHeight / 2 - height / 2
                      implicitWidth: 18
                      implicitHeight: 18
                      radius: 9
                      color: "#ffffff"
                      border.color: "#ffaa00"
                      border.width: 3
                    }
                  }

                  // Spacer to align with EQ bar
                  Item {
                    Layout.fillWidth: true
                    height: 12
                  }

                  // Preset chips
                  RowLayout {
                    Layout.fillWidth: true
                    spacing: 8
                    Repeater {
                      model: [
                        { label: "20% ECO", val: 20 },
                        { label: "50% NORM", val: 50 },
                        { label: "85% TACT", val: 85 },
                        { label: "MAX 100%", val: 100 }
                      ]
                      Rectangle {
                        Layout.fillWidth: true
                        height: 22
                        radius: 4
                        color: root.ccBrightness === modelData.val ? Qt.rgba(1.0, 0.6, 0.0, 0.35) : Qt.rgba(1, 1, 1, 0.05)
                        border.color: root.ccBrightness === modelData.val ? "#ffaa00" : Qt.rgba(1, 1, 1, 0.1)
                        Text {
                          anchors.centerIn: parent
                          text: modelData.label
                          color: root.ccBrightness === modelData.val ? "#ffaa00" : Qt.rgba(1, 1, 1, 0.6)
                          font.pixelSize: 9
                          font.bold: true
                          font.family: "monospace"
                        }
                        MouseArea {
                          anchors.fill: parent
                          cursorShape: Qt.PointingHandCursor
                          onClicked: root.setCcBrightness(modelData.val)
                        }
                      }
                    }
                  }
                }
              }
            }

            // ROW 2: WI-FI & BLUETOOTH CONNECTIVITY HUB
            RowLayout {
              Layout.fillWidth: true
              spacing: 16

              // CARD 3: WI-FI
              Rectangle {
                Layout.fillWidth: true
                Layout.preferredHeight: 155
                radius: 10
                color: Qt.rgba(26/255, 8/255, 15/255, 0.70)
                border.color: Qt.rgba(255/255, 8/255, 56/255, 0.30)
                border.width: 1

                ColumnLayout {
                  anchors.fill: parent
                  anchors.margins: 14
                  spacing: 10

                  RowLayout {
                    Layout.fillWidth: true
                    Text {
                      text: "📶  " + (root.ccWifiEnabled ? root.ccWifiSSID + " (Active)" : "Wi-Fi Disabled")
                      color: "#ffffff"
                      font.pixelSize: 12
                      font.bold: true
                      font.family: "monospace"
                    }
                    Item { Layout.fillWidth: true }

                    // Custom Switch
                    Rectangle {
                      width: 40
                      height: 20
                      radius: 10
                      color: root.ccWifiEnabled ? Qt.rgba(0, 0.94, 1.0, 0.35) : Qt.rgba(1, 1, 1, 0.1)
                      border.color: root.ccWifiEnabled ? "#00f0ff" : Qt.rgba(1, 1, 1, 0.2)

                      Rectangle {
                        width: 14
                        height: 14
                        radius: 7
                        y: 3
                        x: root.ccWifiEnabled ? 23 : 3
                        color: root.ccWifiEnabled ? "#ffffff" : Qt.rgba(1, 1, 1, 0.4)
                        Behavior on x { NumberAnimation { duration: 150 } }
                      }

                      MouseArea {
                        anchors.fill: parent
                        cursorShape: Qt.PointingHandCursor
                        onClicked: root.toggleCcWifi()
                      }
                    }
                  }

                  Text {
                    text: "5.8 GHz · WPA3 · IP: " + root.ccWifiIp
                    color: Qt.rgba(1, 1, 1, 0.45)
                    font.pixelSize: 10
                    font.family: "monospace"
                  }

                  Item { Layout.fillHeight: true }

                  Rectangle {
                    Layout.fillWidth: true
                    height: 28
                    radius: 4
                    color: wifiBtnArea.containsMouse ? Qt.rgba(0, 0.94, 1.0, 0.25) : Qt.rgba(0, 0.94, 1.0, 0.12)
                    border.color: "#00f0ff"
                    border.width: 1

                    RowLayout {
                      anchors.centerIn: parent
                      spacing: 6
                      Text {
                        text: "SCAN / CONNECT ACCESS POINTS ➔"
                        color: "#00f0ff"
                        font.pixelSize: 10
                        font.bold: true
                        font.family: "monospace"
                      }
                    }

                    MouseArea {
                      id: wifiBtnArea
                      anchors.fill: parent
                      hoverEnabled: true
                      cursorShape: Qt.PointingHandCursor
                      onClicked: {
                        root.ccWifiScannerOpen = true
                        root.startWifiScan()
                      }
                    }
                  }
                }
              }

              // CARD 4: BLUETOOTH
              Rectangle {
                Layout.fillWidth: true
                Layout.preferredHeight: 155
                radius: 10
                color: Qt.rgba(26/255, 8/255, 15/255, 0.70)
                border.color: Qt.rgba(255/255, 8/255, 56/255, 0.30)
                border.width: 1

                ColumnLayout {
                  anchors.fill: parent
                  anchors.margins: 14
                  spacing: 10

                  RowLayout {
                    Layout.fillWidth: true
                    Text {
                      text: "󰂯  BLUETOOTH 5.3"
                      color: "#ffffff"
                      font.pixelSize: 12
                      font.bold: true
                      font.family: "monospace"
                    }
                    Item { Layout.fillWidth: true }

                    // Custom Switch
                    Rectangle {
                      width: 40
                      height: 20
                      radius: 10
                      color: root.ccBtEnabled ? Qt.rgba(1.0, 0.03, 0.22, 0.35) : Qt.rgba(1, 1, 1, 0.1)
                      border.color: root.ccBtEnabled ? "#ff0838" : Qt.rgba(1, 1, 1, 0.2)

                      Rectangle {
                        width: 14
                        height: 14
                        radius: 7
                        y: 3
                        x: root.ccBtEnabled ? 23 : 3
                        color: root.ccBtEnabled ? "#ffffff" : Qt.rgba(1, 1, 1, 0.4)
                        Behavior on x { NumberAnimation { duration: 150 } }
                      }

                      MouseArea {
                        anchors.fill: parent
                        cursorShape: Qt.PointingHandCursor
                        onClicked: root.toggleCcBluetooth()
                      }
                    }
                  }

                  Text {
                    text: root.ccBtEnabled ? (root.ccBtDevice !== "None" ? "Connected: " + root.ccBtDevice : "Radio Active · Ready to Pair") : "Bluetooth Radio Disabled"
                    color: Qt.rgba(1, 1, 1, 0.45)
                    font.pixelSize: 10
                    font.family: "monospace"
                    elide: Text.ElideRight
                    Layout.fillWidth: true
                  }

                  Item { Layout.fillHeight: true }

                  Rectangle {
                    Layout.fillWidth: true
                    height: 28
                    radius: 4
                    color: btBtnArea.containsMouse ? Qt.rgba(1.0, 0.03, 0.22, 0.25) : Qt.rgba(1.0, 0.03, 0.22, 0.12)
                    border.color: "#ff0838"
                    border.width: 1

                    RowLayout {
                      anchors.centerIn: parent
                      spacing: 6
                      Text {
                        text: "+ PAIR NEW HARDWARE ➔"
                        color: "#ff2a55"
                        font.pixelSize: 10
                        font.bold: true
                        font.family: "monospace"
                      }
                    }

                    MouseArea {
                      id: btBtnArea
                      anchors.fill: parent
                      hoverEnabled: true
                      cursorShape: Qt.PointingHandCursor
                      onClicked: {
                        root.ccBtScannerOpen = true
                        root.startBtScan()
                      }
                    }
                  }
                }
              }
            }

            // ROW 3: TACTICAL MODE MATRIX (NIGHT LIGHT, COMMAND CENTER, VOICE SENTINEL, TOP BAR)
            Text {
              text: "✦ TACTICAL MODE MATRIX & QUICK TOGGLES"
              color: Qt.rgba(1, 1, 1, 0.4)
              font.pixelSize: 10
              font.bold: true
              font.family: "monospace"
              font.letterSpacing: 1
            }

            RowLayout {
              Layout.fillWidth: true
              spacing: 12

              // TILE 1: NIGHT LIGHT
              Rectangle {
                Layout.fillWidth: true
                height: 75
                radius: 8
                color: root.ccNightlightEnabled ? Qt.rgba(1.0, 0.6, 0.0, 0.25) : Qt.rgba(26/255, 8/255, 15/255, 0.70)
                border.color: root.ccNightlightEnabled ? "#ffaa00" : Qt.rgba(255/255, 8/255, 56/255, 0.25)
                border.width: 1

                ColumnLayout {
                  anchors.fill: parent
                  anchors.margins: 10
                  RowLayout {
                    Text { text: "🌙"; font.pixelSize: 16 }
                    Item { Layout.fillWidth: true }
                    Rectangle {
                      width: 7; height: 7; radius: 3.5
                      color: root.ccNightlightEnabled ? "#ffaa00" : Qt.rgba(1,1,1,0.2)
                    }
                  }
                  Item { Layout.fillHeight: true }
                  Text {
                    text: "NIGHT LIGHT"
                    color: "#ffffff"
                    font.pixelSize: 11
                    font.bold: true
                    font.family: "monospace"
                  }
                  Text {
                    text: root.ccNightlightEnabled ? "4000K Active" : "Hyprsunset 4000K"
                    color: Qt.rgba(1, 1, 1, 0.45)
                    font.pixelSize: 9
                    font.family: "monospace"
                  }
                }

                MouseArea {
                  anchors.fill: parent
                  cursorShape: Qt.PointingHandCursor
                  onClicked: root.toggleCcNightlight()
                }
              }

              // TILE 2: COMMAND CENTER (REPLACING GAME MODE!)
              Rectangle {
                Layout.fillWidth: true
                height: 75
                radius: 8
                color: Qt.rgba(1.0, 0.03, 0.22, 0.20)
                border.color: "#ff0838"
                border.width: 1

                ColumnLayout {
                  anchors.fill: parent
                  anchors.margins: 10
                  RowLayout {
                    Text { text: "🎯"; font.pixelSize: 16 }
                    Item { Layout.fillWidth: true }
                    Rectangle {
                      width: 7; height: 7; radius: 3.5
                      color: "#ff0838"
                    }
                  }
                  Item { Layout.fillHeight: true }
                  Text {
                    text: "COMMAND CENTER"
                    color: "#ffffff"
                    font.pixelSize: 11
                    font.bold: true
                    font.family: "monospace"
                  }
                  Text {
                    text: "Milo Tactical HUD"
                    color: "#ff2a55"
                    font.pixelSize: 9
                    font.bold: true
                    font.family: "monospace"
                  }
                }

                MouseArea {
                  anchors.fill: parent
                  cursorShape: Qt.PointingHandCursor
                  onClicked: root.openCcCommandCenter()
                }
              }

              // TILE 3: VOICE SENTINEL
              Rectangle {
                Layout.fillWidth: true
                height: 75
                radius: 8
                color: root.ccVoiceActive ? Qt.rgba(0, 1.0, 0.53, 0.18) : Qt.rgba(26/255, 8/255, 15/255, 0.70)
                border.color: root.ccVoiceActive ? "#00ff88" : Qt.rgba(255/255, 8/255, 56/255, 0.25)
                border.width: 1

                ColumnLayout {
                  anchors.fill: parent
                  anchors.margins: 10
                  RowLayout {
                    Text { text: "🎙"; font.pixelSize: 16 }
                    Item { Layout.fillWidth: true }
                    Rectangle {
                      width: 7; height: 7; radius: 3.5
                      color: root.ccVoiceActive ? "#00ff88" : Qt.rgba(1,1,1,0.2)
                    }
                  }
                  Item { Layout.fillHeight: true }
                  Text {
                    text: "VOICE SENTINEL"
                    color: "#ffffff"
                    font.pixelSize: 11
                    font.bold: true
                    font.family: "monospace"
                  }
                  Text {
                    text: root.ccVoiceActive ? "Active Mic" : "Mic Muted"
                    color: Qt.rgba(1, 1, 1, 0.45)
                    font.pixelSize: 9
                    font.family: "monospace"
                  }
                }

                MouseArea {
                  anchors.fill: parent
                  cursorShape: Qt.PointingHandCursor
                  onClicked: {
                    root.ccVoiceActive = !root.ccVoiceActive
                    quickCmdProc.command = [root.homeDir + "/.local/bin/milo-vol", "mic-mute"]
                    quickCmdProc.running = true
                  }
                }
              }

              // TILE 4: TOP BAR
              Rectangle {
                Layout.fillWidth: true
                height: 75
                radius: 8
                color: root.ccBarOff ? Qt.rgba(26/255, 8/255, 15/255, 0.70) : Qt.rgba(0, 0.94, 1.0, 0.18)
                border.color: root.ccBarOff ? Qt.rgba(255/255, 8/255, 56/255, 0.25) : "#00f0ff"
                border.width: 1

                ColumnLayout {
                  anchors.fill: parent
                  anchors.margins: 10
                  RowLayout {
                    Text { text: "🖥"; font.pixelSize: 16 }
                    Item { Layout.fillWidth: true }
                    Rectangle {
                      width: 7; height: 7; radius: 3.5
                      color: root.ccBarOff ? "#ff0838" : "#00ff88"
                    }
                  }
                  Item { Layout.fillHeight: true }
                  Text {
                    text: "TOP BAR"
                    color: "#ffffff"
                    font.pixelSize: 11
                    font.bold: true
                    font.family: "monospace"
                  }
                  Text {
                    text: root.ccBarOff ? "bar-off Active" : "Top Bar Visible"
                    color: Qt.rgba(1, 1, 1, 0.45)
                    font.pixelSize: 9
                    font.family: "monospace"
                  }
                }

                MouseArea {
                  anchors.fill: parent
                  cursorShape: Qt.PointingHandCursor
                  onClicked: root.toggleCcTopBar()
                }
              }
            }

            Item { Layout.fillHeight: true }

            // FOOTER
            Rectangle {
              Layout.fillWidth: true
              height: 1
              color: Qt.rgba(255/255, 8/255, 56/255, 0.2)
            }

            RowLayout {
              Layout.fillWidth: true
              Text {
                text: "HOST: ALIENWARE M16   KERNEL: 6.11-CACHYOS   COMPOSITOR: HYPRLAND"
                color: Qt.rgba(1, 1, 1, 0.4)
                font.pixelSize: 9
                font.family: "monospace"
              }
              Item { Layout.fillWidth: true }
              Rectangle {
                height: 18; width: 68; radius: 3
                color: Qt.rgba(1, 1, 1, 0.08)
                Text {
                  anchors.centerIn: parent
                  text: "SUPER + S"
                  color: "#ffffff"
                  font.pixelSize: 9
                  font.bold: true
                  font.family: "monospace"
                }
              }
            }
          }

          // ================================================================
          // CYBERPUNK WI-FI SCANNER VIEW (In-Capsule Native Scanner)
          // ================================================================
          ColumnLayout {
            id: ccWifiScannerView
            anchors.fill: parent
            anchors.margins: 24
            spacing: 16
            visible: root.ccWifiScannerOpen

            // Scanner Header
            RowLayout {
              Layout.fillWidth: true
              spacing: 12

              ColumnLayout {
                spacing: 3
                RowLayout {
                  spacing: 10
                  Text {
                    text: "📶  WI-FI NETWORK RADAR"
                    color: "#00f0ff"
                    font.pixelSize: 15
                    font.bold: true
                    font.family: "monospace"
                    font.letterSpacing: 1.5
                  }
                  Rectangle {
                    height: 18
                    width: 90
                    radius: 3
                    color: root.ccIsScanningWifi ? Qt.rgba(0, 0.94, 1.0, 0.3) : Qt.rgba(0, 1.0, 0.53, 0.2)
                    border.color: root.ccIsScanningWifi ? "#00f0ff" : "#00ff88"
                    Text {
                      anchors.centerIn: parent
                      text: root.ccIsScanningWifi ? "SCANNING..." : (root.ccWifiList.length + " FOUND")
                      color: root.ccIsScanningWifi ? "#00f0ff" : "#00ff88"
                      font.pixelSize: 9
                      font.bold: true
                      font.family: "monospace"
                    }
                  }
                }
                Text {
                  text: "Real-time Access Point Grounding via NetworkManager (nmcli)"
                  color: Qt.rgba(1, 1, 1, 0.5)
                  font.pixelSize: 10
                  font.family: "monospace"
                }
              }

              Item { Layout.fillWidth: true }

              // Rescan Button
              Rectangle {
                height: 28
                width: 100
                radius: 4
                color: rescanBtnArea.containsMouse ? Qt.rgba(0, 0.94, 1.0, 0.25) : Qt.rgba(0, 0.94, 1.0, 0.12)
                border.color: "#00f0ff"
                border.width: 1

                RowLayout {
                  anchors.centerIn: parent
                  spacing: 6
                  Text { text: "🔄"; font.pixelSize: 10 }
                  Text {
                    text: "RESCAN"
                    color: "#00f0ff"
                    font.pixelSize: 10
                    font.bold: true
                    font.family: "monospace"
                  }
                }

                MouseArea {
                  id: rescanBtnArea
                  anchors.fill: parent
                  hoverEnabled: true
                  cursorShape: Qt.PointingHandCursor
                  onClicked: root.startWifiScan()
                }
              }

              // Back Button
              Rectangle {
                height: 28
                width: 76
                radius: 4
                color: backWifiArea.containsMouse ? "#ff0838" : Qt.rgba(1.0, 0.03, 0.22, 0.15)
                border.color: "#ff0838"
                border.width: 1

                RowLayout {
                  anchors.centerIn: parent
                  spacing: 4
                  Text {
                    text: "◂ BACK"
                    color: backWifiArea.containsMouse ? "#000000" : "#ff2a55"
                    font.pixelSize: 10
                    font.bold: true
                    font.family: "monospace"
                  }
                }

                MouseArea {
                  id: backWifiArea
                  anchors.fill: parent
                  hoverEnabled: true
                  cursorShape: Qt.PointingHandCursor
                  onClicked: {
                    root.ccWifiScannerOpen = false
                    root.ccWifiShowPasswordInput = false
                  }
                }
              }
            }

            // Inline Password Prompt (if opened)
            Rectangle {
              Layout.fillWidth: true
              height: root.ccWifiShowPasswordInput ? 44 : 0
              visible: root.ccWifiShowPasswordInput
              radius: 6
              color: Qt.rgba(0.08, 0.02, 0.04, 0.95)
              border.color: "#00f0ff"
              border.width: 1
              clip: true

              RowLayout {
                anchors.fill: parent
                anchors.margins: 8
                spacing: 10

                Text {
                  text: "PASSWORD FOR '" + root.ccWifiSelectedSSID + "':"
                  color: "#00f0ff"
                  font.pixelSize: 10
                  font.bold: true
                  font.family: "monospace"
                }

                Rectangle {
                  Layout.fillWidth: true
                  height: 28
                  radius: 4
                  color: Qt.rgba(0, 0, 0, 0.6)
                  border.color: Qt.rgba(0, 0.94, 1.0, 0.4)

                  TextInput {
                    id: ccWifiPassField
                    anchors.fill: parent
                    anchors.margins: 6
                    color: "#ffffff"
                    font.pixelSize: 11
                    font.family: "monospace"
                    echoMode: TextInput.Password
                    focus: root.ccWifiShowPasswordInput
                    onAccepted: {
                      root.connectToWifi(root.ccWifiSelectedSSID, text)
                    }
                  }
                }

                Rectangle {
                  width: 80
                  height: 28
                  radius: 4
                  color: "#00f0ff"
                  Text {
                    anchors.centerIn: parent
                    text: "CONNECT"
                    color: "#000000"
                    font.pixelSize: 10
                    font.bold: true
                    font.family: "monospace"
                  }
                  MouseArea {
                    anchors.fill: parent
                    cursorShape: Qt.PointingHandCursor
                    onClicked: {
                      root.connectToWifi(root.ccWifiSelectedSSID, ccWifiPassField.text)
                    }
                  }
                }

                Rectangle {
                  width: 28
                  height: 28
                  radius: 14
                  color: Qt.rgba(1, 1, 1, 0.1)
                  Text {
                    anchors.centerIn: parent
                    text: "✕"
                    color: "#ffffff"
                    font.pixelSize: 10
                  }
                  MouseArea {
                    anchors.fill: parent
                    cursorShape: Qt.PointingHandCursor
                    onClicked: root.ccWifiShowPasswordInput = false
                  }
                }
              }
            }

            // Scrollable List of Wi-Fi Networks
            ListView {
              id: ccWifiListView
              Layout.fillWidth: true
              Layout.fillHeight: true
              clip: true
              spacing: 8
              model: root.ccWifiList

              delegate: Rectangle {
                width: ccWifiListView.width - 6
                height: 52
                radius: 6
                color: modelData.in_use ? Qt.rgba(0, 1.0, 0.53, 0.12) : (netItemArea.containsMouse ? Qt.rgba(0, 0.94, 1.0, 0.10) : Qt.rgba(1, 1, 1, 0.04))
                border.color: modelData.in_use ? "#00ff88" : (netItemArea.containsMouse ? "#00f0ff" : Qt.rgba(1, 1, 1, 0.08))
                border.width: 1

                RowLayout {
                  anchors.fill: parent
                  anchors.leftMargin: 14
                  anchors.rightMargin: 14
                  spacing: 12

                  Text {
                    text: modelData.signal >= 70 ? "📶" : (modelData.signal >= 40 ? "📶" : "📡")
                    font.pixelSize: 14
                  }

                  ColumnLayout {
                    spacing: 2
                    RowLayout {
                      spacing: 8
                      Text {
                        text: modelData.ssid
                        color: modelData.in_use ? "#00ff88" : "#ffffff"
                        font.pixelSize: 12
                        font.bold: true
                        font.family: "monospace"
                      }
                      Rectangle {
                        height: 16
                        width: secText.implicitWidth + 8
                        radius: 3
                        color: Qt.rgba(1, 1, 1, 0.08)
                        Text {
                          id: secText
                          anchors.centerIn: parent
                          text: modelData.security
                          color: Qt.rgba(1, 1, 1, 0.6)
                          font.pixelSize: 8
                          font.family: "monospace"
                        }
                      }
                    }
                    Text {
                      text: "Signal Strength: " + modelData.signal + "%"
                      color: Qt.rgba(1, 1, 1, 0.4)
                      font.pixelSize: 9
                      font.family: "monospace"
                    }
                  }

                  Item { Layout.fillWidth: true }

                  // Action Button
                  Rectangle {
                    height: 28
                    width: modelData.in_use ? 85 : 92
                    radius: 4
                    color: modelData.in_use ? Qt.rgba(0, 1.0, 0.53, 0.20) : "#00f0ff"
                    border.color: modelData.in_use ? "#00ff88" : "#00f0ff"

                    Text {
                      anchors.centerIn: parent
                      text: modelData.in_use ? "CONNECTED" : "CONNECT ➔"
                      color: modelData.in_use ? "#00ff88" : "#000000"
                      font.pixelSize: 9
                      font.bold: true
                      font.family: "monospace"
                    }

                    MouseArea {
                      anchors.fill: parent
                      cursorShape: Qt.PointingHandCursor
                      onClicked: {
                        if (modelData.in_use) return
                        if (modelData.security === "Open") {
                          root.connectToWifi(modelData.ssid)
                        } else {
                          root.ccWifiSelectedSSID = modelData.ssid
                          root.ccWifiShowPasswordInput = true
                        }
                      }
                    }
                  }
                }

                MouseArea {
                  id: netItemArea
                  anchors.fill: parent
                  hoverEnabled: true
                  z: -1
                  cursorShape: Qt.PointingHandCursor
                  onClicked: {
                    if (!modelData.in_use) {
                      root.ccWifiSelectedSSID = modelData.ssid
                      root.ccWifiShowPasswordInput = true
                    }
                  }
                }
              }
            }
          }

          // ================================================================
          // CYBERPUNK BLUETOOTH HARDWARE RACK VIEW (In-Capsule)
          // ================================================================
          ColumnLayout {
            id: ccBtScannerView
            anchors.fill: parent
            anchors.margins: 24
            spacing: 16
            visible: root.ccBtScannerOpen

            // Header
            RowLayout {
              Layout.fillWidth: true
              spacing: 12

              ColumnLayout {
                spacing: 3
                RowLayout {
                  spacing: 10
                  Text {
                    text: "󰂯  BLUETOOTH HARDWARE RACK"
                    color: "#ff2a55"
                    font.pixelSize: 15
                    font.bold: true
                    font.family: "monospace"
                    font.letterSpacing: 1.5
                  }
                  Rectangle {
                    height: 18
                    width: 90
                    radius: 3
                    color: Qt.rgba(1.0, 0.03, 0.22, 0.2)
                    border.color: "#ff0838"
                    Text {
                      anchors.centerIn: parent
                      text: (root.ccBtList.length + " REGISTERED")
                      color: "#ff2a55"
                      font.pixelSize: 9
                      font.bold: true
                      font.family: "monospace"
                    }
                  }
                }
                Text {
                  text: "Hardware Pairing & Handshake Controller (bluetoothctl)"
                  color: Qt.rgba(1, 1, 1, 0.5)
                  font.pixelSize: 10
                  font.family: "monospace"
                }
              }

              Item { Layout.fillWidth: true }

              // Rescan Button
              Rectangle {
                height: 28
                width: 100
                radius: 4
                color: rescanBtArea.containsMouse ? Qt.rgba(1.0, 0.03, 0.22, 0.35) : Qt.rgba(1.0, 0.03, 0.22, 0.15)
                border.color: "#ff0838"
                border.width: 1

                RowLayout {
                  anchors.centerIn: parent
                  spacing: 6
                  Text { text: "🔄"; font.pixelSize: 10 }
                  Text {
                    text: "REFRESH"
                    color: "#ff2a55"
                    font.pixelSize: 10
                    font.bold: true
                    font.family: "monospace"
                  }
                }

                MouseArea {
                  id: rescanBtArea
                  anchors.fill: parent
                  hoverEnabled: true
                  cursorShape: Qt.PointingHandCursor
                  onClicked: root.startBtScan()
                }
              }

              // Back Button
              Rectangle {
                height: 28
                width: 76
                radius: 4
                color: backBtArea.containsMouse ? "#ff0838" : Qt.rgba(1.0, 0.03, 0.22, 0.15)
                border.color: "#ff0838"
                border.width: 1

                RowLayout {
                  anchors.centerIn: parent
                  spacing: 4
                  Text {
                    text: "◂ BACK"
                    color: backBtArea.containsMouse ? "#000000" : "#ff2a55"
                    font.pixelSize: 10
                    font.bold: true
                    font.family: "monospace"
                  }
                }

                MouseArea {
                  id: backBtArea
                  anchors.fill: parent
                  hoverEnabled: true
                  cursorShape: Qt.PointingHandCursor
                  onClicked: root.ccBtScannerOpen = false
                }
              }
            }

            // Scrollable List of Bluetooth Devices
            ListView {
              id: ccBtListView
              Layout.fillWidth: true
              Layout.fillHeight: true
              clip: true
              spacing: 8
              model: root.ccBtList

              delegate: Rectangle {
                width: ccBtListView.width - 6
                height: 52
                radius: 6
                color: modelData.connected ? Qt.rgba(0, 1.0, 0.53, 0.12) : (btItemArea.containsMouse ? Qt.rgba(1.0, 0.03, 0.22, 0.15) : Qt.rgba(1, 1, 1, 0.04))
                border.color: modelData.connected ? "#00ff88" : (btItemArea.containsMouse ? "#ff0838" : Qt.rgba(1, 1, 1, 0.08))
                border.width: 1

                RowLayout {
                  anchors.fill: parent
                  anchors.leftMargin: 14
                  anchors.rightMargin: 14
                  spacing: 12

                  Text {
                    text: "󰂯"
                    font.pixelSize: 16
                    color: modelData.connected ? "#00ff88" : "#ff2a55"
                  }

                  ColumnLayout {
                    spacing: 2
                    RowLayout {
                      spacing: 8
                      Text {
                        text: modelData.name
                        color: modelData.connected ? "#00ff88" : "#ffffff"
                        font.pixelSize: 12
                        font.bold: true
                        font.family: "monospace"
                      }
                    }
                    Text {
                      text: "MAC: " + modelData.mac
                      color: Qt.rgba(1, 1, 1, 0.4)
                      font.pixelSize: 9
                      font.family: "monospace"
                    }
                  }

                  Item { Layout.fillWidth: true }

                  // Connect/Disconnect Button
                  Rectangle {
                    height: 28
                    width: modelData.connected ? 95 : 90
                    radius: 4
                    color: modelData.connected ? Qt.rgba(1.0, 0.03, 0.22, 0.20) : "#ff0838"
                    border.color: "#ff0838"

                    Text {
                      anchors.centerIn: parent
                      text: modelData.connected ? "DISCONNECT" : "CONNECT ➔"
                      color: modelData.connected ? "#ff2a55" : "#000000"
                      font.pixelSize: 9
                      font.bold: true
                      font.family: "monospace"
                    }

                    MouseArea {
                      anchors.fill: parent
                      cursorShape: Qt.PointingHandCursor
                      onClicked: {
                        if (modelData.connected) {
                          root.disconnectFromBt(modelData.mac)
                        } else {
                          root.connectToBt(modelData.mac)
                        }
                      }
                    }
                  }
                }

                MouseArea {
                  id: btItemArea
                  anchors.fill: parent
                  hoverEnabled: true
                  z: -1
                }
              }
            }
          }
        }
      }
    }
  }

  Timer {
    id: ccVolTimer
    interval: 80
    repeat: true
    running: root.controlCenterOpen && !root.ccMuted
    property int tick: 0
    onTriggered: tick = (tick + 1) % 1000
  }
}

