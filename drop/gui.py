#!/usr/bin/env python3
"""
Milo Drop - Cyberpunk Native Desktop GUI (PyQt6)
The effortless local network file-sharing cockpit for Milo OS.
"""

import sys
import os
import json
import time
import socket
import threading
import subprocess
from pathlib import Path
import urllib.request
import urllib.parse

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QTabWidget, QListWidget, QListWidgetItem,
    QFileDialog, QProgressBar, QLineEdit, QFrame, QScrollArea,
    QSizePolicy, QMessageBox
)
from PyQt6.QtCore import Qt, QTimer, QThread, pyqtSignal, QSize
from PyQt6.QtGui import QFont, QIcon, QPixmap, QColor, QPainter, QBrush, QPen

from server import PORT, DOWNLOADS_DIR, get_local_ip, start_server_daemon, transfer_history, history_lock

CYBER_STYLE = """
QMainWindow {
    background-color: #070204;
}

QWidget {
    background-color: transparent;
    color: #f8f9fa;
    font-family: 'JetBrains Mono', 'Inter', -apple-system, sans-serif;
}

/* Header & Banner */
#headerFrame {
    background-color: rgba(22, 6, 13, 0.95);
    border-bottom: 2px solid #ff0838;
    padding: 12px 22px;
}

#headerTitle {
    color: #ffffff;
    font-size: 18px;
    font-weight: 800;
    letter-spacing: 2px;
}

#statusBadge {
    background-color: rgba(0, 240, 255, 0.12);
    border: 1px solid #00f0ff;
    color: #00f0ff;
    border-radius: 6px;
    padding: 5px 12px;
    font-size: 11px;
    font-weight: 700;
}

/* Tabs */
QTabWidget::pane {
    border: 1px solid rgba(255, 8, 56, 0.25);
    background-color: rgba(14, 4, 8, 0.92);
    border-radius: 8px;
    margin-top: -1px;
}

QTabBar::tab {
    background-color: rgba(25, 8, 15, 0.6);
    color: #8c8286;
    border: 1px solid rgba(255, 8, 56, 0.2);
    border-bottom: none;
    border-top-left-radius: 8px;
    border-top-right-radius: 8px;
    padding: 10px 22px;
    margin-right: 4px;
    font-size: 12px;
    font-weight: 700;
    letter-spacing: 1px;
}

QTabBar::tab:selected {
    background-color: rgba(255, 8, 56, 0.2);
    color: #ff0838;
    border: 1px solid #ff0838;
    border-bottom: none;
}

QTabBar::tab:hover:!selected {
    background-color: rgba(255, 8, 56, 0.1);
    color: #ffffff;
}

/* Buttons */
QPushButton {
    background-color: rgba(255, 8, 56, 0.15);
    color: #ff0838;
    border: 1px solid #ff0838;
    border-radius: 6px;
    padding: 7px 14px;
    font-size: 11px;
    font-weight: 700;
    letter-spacing: 0.5px;
}

QPushButton:hover {
    background-color: #ff0838;
    color: #ffffff;
}

QPushButton:pressed {
    background-color: #cc0028;
    color: #ffffff;
}

QPushButton#btnCyan {
    background-color: rgba(0, 240, 255, 0.12);
    color: #00f0ff;
    border: 1px solid #00f0ff;
}

QPushButton#btnCyan:hover {
    background-color: #00f0ff;
    color: #000000;
}

QPushButton#btnGreen {
    background-color: rgba(0, 255, 136, 0.12);
    color: #00ff88;
    border: 1px solid #00ff88;
}

QPushButton#btnGreen:hover {
    background-color: #00ff88;
    color: #000000;
}

/* Cards & Panels */
#cardFrame {
    background-color: rgba(24, 7, 14, 0.75);
    border: 1px solid rgba(255, 8, 56, 0.2);
    border-radius: 12px;
    padding: 16px;
}

#dropZone {
    background-color: rgba(30, 8, 18, 0.45);
    border: 2px dashed rgba(255, 8, 56, 0.45);
    border-radius: 12px;
    padding: 24px;
}

#dropZone:hover {
    background-color: rgba(255, 8, 56, 0.08);
    border-color: #ff0838;
}

/* List Widget */
QListWidget {
    background-color: rgba(14, 4, 8, 0.7);
    border: 1px solid rgba(255, 8, 56, 0.2);
    border-radius: 8px;
    padding: 6px;
}

QListWidget::item {
    background-color: rgba(28, 8, 17, 0.7);
    border: 1px solid rgba(255, 8, 56, 0.15);
    border-radius: 6px;
    margin-bottom: 6px;
    color: #ffffff;
}

QListWidget::item:hover {
    border-color: #ff0838;
    background-color: rgba(255, 8, 56, 0.14);
}

/* Inputs */
QLineEdit {
    background-color: rgba(20, 5, 12, 0.85);
    border: 1px solid rgba(255, 8, 56, 0.35);
    border-radius: 6px;
    padding: 8px 12px;
    color: #ffffff;
    font-size: 13px;
}

QLineEdit:focus {
    border-color: #ff0838;
}

/* Progress Bar */
QProgressBar {
    background-color: rgba(20, 5, 12, 0.85);
    border: 1px solid rgba(255, 8, 56, 0.3);
    border-radius: 6px;
    text-align: center;
    color: #ffffff;
    font-size: 11px;
    font-weight: 700;
    height: 20px;
}

QProgressBar::chunk {
    background-color: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #ff0838, stop:1 #00f0ff);
    border-radius: 5px;
}

/* Scrollbars */
QScrollBar:vertical {
    background: #0d0307;
    width: 8px;
    margin: 0;
    border-radius: 4px;
}

QScrollBar::handle:vertical {
    background: rgba(255, 8, 56, 0.4);
    min-height: 20px;
    border-radius: 4px;
}

QScrollBar::handle:vertical:hover {
    background: #ff0838;
}
"""

def get_wifi_ssid():
    """Detect connected Wi-Fi SSID."""
    try:
        out = subprocess.check_output(
            ["nmcli", "-t", "-f", "active,ssid", "dev", "wifi"],
            stderr=subprocess.DEVNULL
        ).decode().strip()
        for line in out.splitlines():
            if line.startswith("yes:"):
                return line.split(":", 1)[1]
    except Exception:
        pass
    return "Local Wi-Fi"

class SenderThread(QThread):
    progress_signal = pyqtSignal(int, str)
    finished_signal = pyqtSignal(bool, str)

    def __init__(self, filepath, target_ip, port=PORT):
        super().__init__()
        self.filepath = filepath
        self.target_ip = target_ip
        self.port = port

    def run(self):
        try:
            path = Path(self.filepath)
            if not path.is_file():
                self.finished_signal.emit(False, "File not found")
                return

            filesize = path.stat().st_size
            fname = path.name

            self.progress_signal.emit(5, f"Connecting to {self.target_ip}:{self.port}...")

            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(10)
            s.connect((self.target_ip, self.port))

            header = f"MILODROP {fname} {filesize}\n"
            s.sendall(header.encode("utf-8"))

            sent = 0
            with open(path, "rb") as f:
                while chunk := f.read(16384):
                    s.sendall(chunk)
                    sent += len(chunk)
                    pct = int((sent / filesize) * 90) + 5
                    self.progress_signal.emit(pct, f"Streaming: {sent // 1024} / {filesize // 1024} KB ({pct}%)")

            s.settimeout(5)
            ack = s.recv(32)
            s.close()

            self.progress_signal.emit(100, "Transfer Complete!")
            self.finished_signal.emit(True, f"Sent '{fname}' ({filesize // 1024} KB) successfully!")

        except Exception as e:
            self.finished_signal.emit(False, f"Transfer failed: {str(e)}")

class MiloDropWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setObjectName("milo-drop")
        self.setWindowTitle("MILO DROP // Local P2P AirDrop & Share")
        self.resize(960, 680)
        self.setMinimumSize(880, 600)
        self.setStyleSheet(CYBER_STYLE)

        self.selected_files = []
        self.server_ip = get_local_ip()
        self.server_url = f"http://{self.server_ip}:{PORT}"
        self.wifi_ssid = get_wifi_ssid()

        # Ensure server runs
        self.ensure_server()

        # Build UI
        self.init_ui()

        # Ensure Tab 0 (Receive) is active by default
        self.tabs.setCurrentIndex(0)
        self.clearFocus()

        # Timer to refresh history and downloads
        self.refresh_timer = QTimer(self)
        self.refresh_timer.timeout.connect(self.refresh_recent_files)
        self.refresh_timer.start(2500)

        # Initial load
        self.refresh_recent_files()

    def ensure_server(self):
        """Check if port 4242 is responding; if not, spin up daemon."""
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        result = sock.connect_ex(('127.0.0.1', PORT))
        sock.close()
        if result != 0:
            threading.Thread(target=start_server_daemon, daemon=True).start()

    def init_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(12)

        # 1. Header Frame
        header = QFrame()
        header.setObjectName("headerFrame")
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(18, 12, 18, 12)

        title_box = QVBoxLayout()
        title = QLabel("MILO DROP")
        title.setObjectName("headerTitle")
        subtitle = QLabel(f"AIRDROP & LOCAL NETWORK TRANSFER // WI-FI: {self.wifi_ssid.upper()}")
        subtitle.setStyleSheet("color: #7a6e73; font-size: 10px; font-weight: 700; letter-spacing: 1px;")
        title_box.addWidget(title)
        title_box.addWidget(subtitle)
        header_layout.addLayout(title_box)

        header_layout.addStretch()

        self.ip_badge = QLabel(f"● {self.server_url}")
        self.ip_badge.setObjectName("statusBadge")
        header_layout.addWidget(self.ip_badge)

        btn_copy = QPushButton("📋 COPY LINK")
        btn_copy.setObjectName("btnCyan")
        btn_copy.clicked.connect(self.copy_server_url)
        header_layout.addWidget(btn_copy)

        btn_browser = QPushButton("🌐 OPEN PORTAL")
        btn_browser.clicked.connect(self.open_browser)
        header_layout.addWidget(btn_browser)

        btn_folder = QPushButton("📂 DOWNLOADS")
        btn_folder.setObjectName("btnGreen")
        btn_folder.clicked.connect(self.open_downloads_folder)
        header_layout.addWidget(btn_folder)

        main_layout.addWidget(header)

        # 2. Main Content Tabs
        content_margin = QWidget()
        content_layout = QVBoxLayout(content_margin)
        content_layout.setContentsMargins(18, 0, 18, 16)

        self.tabs = QTabWidget()
        self.tab_receive = self.create_receive_tab()
        self.tab_send = self.create_send_tab()
        self.tab_clipboard = self.create_clipboard_tab()

        self.tabs.addTab(self.tab_receive, "📱 RECEIVE FROM PHONE (QR CODE)")
        self.tabs.addTab(self.tab_send, "🚀 SEND FILES (PC ➔ DEVICE)")
        self.tabs.addTab(self.tab_clipboard, "📋 CLIPBOARD TELEPORT")

        content_layout.addWidget(self.tabs)
        main_layout.addWidget(content_margin)

    # -------------------------------------------------------------
    # TAB 1: RECEIVE (QR CODE + INCOMING HISTORY)
    # -------------------------------------------------------------
    def create_receive_tab(self):
        tab = QWidget()
        layout = QHBoxLayout(tab)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(16)

        # Left Column: QR Code Card
        qr_card = QFrame()
        qr_card.setObjectName("cardFrame")
        qr_card.setFixedWidth(340)
        qr_layout = QVBoxLayout(qr_card)
        qr_layout.setContentsMargins(14, 14, 14, 14)
        qr_layout.setSpacing(10)

        qr_title = QLabel("CONNECT ANY PHONE")
        qr_title.setStyleSheet("color: #ff0838; font-size: 13px; font-weight: 800; letter-spacing: 1px;")
        qr_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        qr_layout.addWidget(qr_title)

        qr_hint = QLabel("Scan with iPhone or Android camera.\nInstant file upload with ZERO app install!")
        qr_hint.setStyleSheet("color: #9a8c92; font-size: 10px; line-height: 1.4;")
        qr_hint.setAlignment(Qt.AlignmentFlag.AlignCenter)
        qr_layout.addWidget(qr_hint)

        # Dedicated QR container
        qr_container = QWidget()
        qc_layout = QVBoxLayout(qr_container)
        qc_layout.setContentsMargins(0, 4, 0, 4)
        qc_layout.setSpacing(10)
        qc_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.qr_label = QLabel()
        self.qr_label.setFixedSize(176, 176)
        self.qr_label.setStyleSheet("border: 2px solid #ff0838; border-radius: 12px; background: #ffffff; padding: 2px;")
        self.qr_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.load_qr_image()
        qc_layout.addWidget(self.qr_label, alignment=Qt.AlignmentFlag.AlignCenter)

        self.url_display = QLabel(self.server_url)
        self.url_display.setFixedHeight(28)
        self.url_display.setStyleSheet("color: #00f0ff; font-size: 11px; font-weight: 700; background: rgba(0,240,255,0.08); padding: 4px 12px; border-radius: 6px; border: 1px solid rgba(0,240,255,0.25);")
        self.url_display.setAlignment(Qt.AlignmentFlag.AlignCenter)
        qc_layout.addWidget(self.url_display, alignment=Qt.AlignmentFlag.AlignCenter)

        qr_layout.addWidget(qr_container)

        # Quick Steps
        steps_box = QFrame()
        steps_box.setStyleSheet("background: rgba(0,0,0,0.35); border-radius: 8px; padding: 8px;")
        sb_layout = QVBoxLayout(steps_box)
        sb_layout.setSpacing(5)
        
        step1 = QLabel("1. Point camera at QR code")
        step1.setStyleSheet("color: #d1c8cb; font-size: 10px; font-weight: 600;")
        step2 = QLabel("2. Tap banner to open Milo Drop")
        step2.setStyleSheet("color: #d1c8cb; font-size: 10px; font-weight: 600;")
        step3 = QLabel("3. Select photos/files to drop")
        step3.setStyleSheet("color: #d1c8cb; font-size: 10px; font-weight: 600;")
        sb_layout.addWidget(step1)
        sb_layout.addWidget(step2)
        sb_layout.addWidget(step3)
        qr_layout.addWidget(steps_box)

        qr_layout.addStretch()

        btn_refresh_ip = QPushButton("🔄 RE-CHECK WI-FI IP")
        btn_refresh_ip.clicked.connect(self.refresh_network_ip)
        qr_layout.addWidget(btn_refresh_ip)

        layout.addWidget(qr_card)

        # Right Column: Received Files & Recent Activity
        recent_card = QFrame()
        recent_card.setObjectName("cardFrame")
        recent_layout = QVBoxLayout(recent_card)
        recent_layout.setSpacing(10)

        top_row = QHBoxLayout()
        recent_title = QLabel("📥 RECENT RECEIVED FILES (~/Downloads)")
        recent_title.setStyleSheet("color: #ffffff; font-size: 13px; font-weight: 700;")
        top_row.addWidget(recent_title)
        top_row.addStretch()

        btn_refresh_list = QPushButton("🔄 REFRESH")
        btn_refresh_list.setFixedHeight(26)
        btn_refresh_list.clicked.connect(self.refresh_recent_files)
        top_row.addWidget(btn_refresh_list)

        btn_clear = QPushButton("OPEN FOLDER")
        btn_clear.setObjectName("btnGreen")
        btn_clear.setFixedHeight(26)
        btn_clear.clicked.connect(self.open_downloads_folder)
        top_row.addWidget(btn_clear)
        recent_layout.addLayout(top_row)

        self.received_list = QListWidget()
        self.received_list.setSelectionMode(QListWidget.SelectionMode.NoSelection)
        recent_layout.addWidget(self.received_list)

        layout.addWidget(recent_card)
        return tab

    def load_qr_image(self):
        """Generate and display QR code pixmap."""
        try:
            p = subprocess.Popen(
                ["qrencode", "-s", "6", "-m", "1", "-o", "-", self.server_url],
                stdout=subprocess.PIPE, stderr=subprocess.PIPE
            )
            data, _ = p.communicate()
            pix = QPixmap()
            pix.loadFromData(data)
            self.qr_label.setPixmap(pix.scaled(176, 176, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
        except Exception:
            self.qr_label.setText("QR Error")

    def refresh_network_ip(self):
        self.server_ip = get_local_ip()
        self.server_url = f"http://{self.server_ip}:{PORT}"
        self.wifi_ssid = get_wifi_ssid()
        self.ip_badge.setText(f"● {self.server_url}")
        self.url_display.setText(self.server_url)
        self.load_qr_image()
        self.statusBar_msg(f"Network updated: {self.server_url}")

    # -------------------------------------------------------------
    # TAB 2: SEND (PC TO PHONE OR PC)
    # -------------------------------------------------------------
    def create_send_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(12)

        # Target Selector Card
        target_card = QFrame()
        target_card.setObjectName("cardFrame")
        target_layout = QHBoxLayout(target_card)
        target_layout.setContentsMargins(14, 10, 14, 10)
        target_layout.setSpacing(12)

        target_lbl = QLabel("RECEIVER IP:")
        target_lbl.setStyleSheet("color: #00f0ff; font-weight: 700; font-size: 11px;")
        target_layout.addWidget(target_lbl)

        self.target_ip_edit = QLineEdit()
        self.target_ip_edit.setPlaceholderText("e.g. 192.168.1.15 or peer IP")
        self.target_ip_edit.setText(self.server_ip)
        target_layout.addWidget(self.target_ip_edit)

        btn_share_web = QPushButton("⚡ SHARE VIA WEB PORTAL")
        btn_share_web.setObjectName("btnCyan")
        btn_share_web.setToolTip("Copies file to ~/Downloads so phone can download it immediately via browser")
        btn_share_web.clicked.connect(self.share_to_web_portal)
        target_layout.addWidget(btn_share_web)

        layout.addWidget(target_card)

        # Drop & File Selection Zone
        self.drop_card = DropZoneWidget(self)
        self.drop_card.setObjectName("dropZone")
        drop_layout = QVBoxLayout(self.drop_card)
        drop_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        drop_layout.setSpacing(8)

        drop_icon = QLabel("📤")
        drop_icon.setStyleSheet("font-size: 34px;")
        drop_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        drop_layout.addWidget(drop_icon)

        self.drop_text = QLabel("DRAG & DROP FILES HERE\nOR CLICK TO BROWSE")
        self.drop_text.setStyleSheet("color: #f8f9fa; font-weight: 700; font-size: 13px; letter-spacing: 1px; text-align: center;")
        self.drop_text.setAlignment(Qt.AlignmentFlag.AlignCenter)
        drop_layout.addWidget(self.drop_text)

        btn_row = QHBoxLayout()
        btn_row.setAlignment(Qt.AlignmentFlag.AlignCenter)
        btn_browse_file = QPushButton("📁 BROWSE FILES...")
        btn_browse_file.clicked.connect(self.browse_files)
        btn_row.addWidget(btn_browse_file)

        btn_browse_dir = QPushButton("📂 BROWSE FOLDER...")
        btn_browse_dir.clicked.connect(self.browse_folder)
        btn_row.addWidget(btn_browse_dir)
        drop_layout.addLayout(btn_row)

        layout.addWidget(self.drop_card)

        # Selected Files Queue
        queue_card = QFrame()
        queue_card.setObjectName("cardFrame")
        queue_layout = QVBoxLayout(queue_card)
        queue_layout.setContentsMargins(14, 10, 14, 10)
        queue_layout.setSpacing(8)

        q_head = QHBoxLayout()
        self.q_count_lbl = QLabel("READY TO SEND (0 FILES)")
        self.q_count_lbl.setStyleSheet("color: #ffffff; font-weight: 700; font-size: 11px;")
        q_head.addWidget(self.q_count_lbl)
        q_head.addStretch()

        btn_clear_q = QPushButton("CLEAR LIST")
        btn_clear_q.setFixedHeight(24)
        btn_clear_q.clicked.connect(self.clear_selected_files)
        q_head.addWidget(btn_clear_q)
        queue_layout.addLayout(q_head)

        self.queue_list = QListWidget()
        self.queue_list.setMaximumHeight(110)
        queue_layout.addWidget(self.queue_list)

        # Transfer Progress & Send Action
        action_row = QHBoxLayout()
        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(True)
        action_row.addWidget(self.progress_bar)

        self.btn_send_now = QPushButton("🚀 SEND TO PEER NOW")
        self.btn_send_now.setObjectName("btnGreen")
        self.btn_send_now.setMinimumWidth(160)
        self.btn_send_now.clicked.connect(self.send_to_peer)
        action_row.addWidget(self.btn_send_now)

        queue_layout.addLayout(action_row)
        layout.addWidget(queue_card)

        return tab

    # -------------------------------------------------------------
    # TAB 3: CLIPBOARD TELEPORT
    # -------------------------------------------------------------
    def create_clipboard_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(14)

        card = QFrame()
        card.setObjectName("cardFrame")
        c_layout = QVBoxLayout(card)
        c_layout.setSpacing(12)

        title = QLabel("📋 WAYLAND CLIPBOARD TELEPORT")
        title.setStyleSheet("color: #00f0ff; font-weight: 800; font-size: 13px;")
        c_layout.addWidget(title)

        hint = QLabel("Anything copied on your phone via the Milo Drop web portal can be received here, or push text to your phone instantly.")
        hint.setStyleSheet("color: #9a8c92; font-size: 11px;")
        c_layout.addWidget(hint)

        self.clip_edit = QLineEdit()
        self.clip_edit.setPlaceholderText("Type or paste text to share with your mobile device...")
        c_layout.addWidget(self.clip_edit)

        btn_row = QHBoxLayout()
        btn_paste_local = QPushButton("📥 PASTE FROM LAPTOP CLIPBOARD")
        btn_paste_local.clicked.connect(self.paste_from_local_clipboard)
        btn_row.addWidget(btn_paste_local)

        btn_copy_local = QPushButton("📋 COPY TO LAPTOP CLIPBOARD")
        btn_copy_local.setObjectName("btnCyan")
        btn_copy_local.clicked.connect(self.copy_to_local_clipboard)
        btn_row.addWidget(btn_copy_local)

        c_layout.addLayout(btn_row)
        layout.addWidget(card)
        layout.addStretch()
        return tab

    # -------------------------------------------------------------
    # UI Actions & Helpers
    # -------------------------------------------------------------
    def browse_files(self):
        files, _ = QFileDialog.getOpenFileNames(self, "Select Files to Send via Milo Drop")
        if files:
            for f in files:
                if f not in self.selected_files:
                    self.selected_files.append(f)
            self.update_queue_ui()

    def browse_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Folder to Send")
        if folder:
            for root, _, filenames in os.walk(folder):
                for name in filenames:
                    p = os.path.join(root, name)
                    if p not in self.selected_files:
                        self.selected_files.append(p)
            self.update_queue_ui()

    def add_dropped_files(self, paths):
        for p in paths:
            if os.path.isfile(p) and p not in self.selected_files:
                self.selected_files.append(p)
            elif os.path.isdir(p):
                for root, _, filenames in os.walk(p):
                    for name in filenames:
                        fp = os.path.join(root, name)
                        if fp not in self.selected_files:
                            self.selected_files.append(fp)
        self.update_queue_ui()

    def clear_selected_files(self):
        self.selected_files = []
        self.update_queue_ui()
        self.progress_bar.setValue(0)
        self.progress_bar.setFormat("Ready")

    def update_queue_ui(self):
        self.queue_list.clear()
        total_size = 0
        for f in self.selected_files:
            try:
                sz = os.path.getsize(f)
                total_size += sz
                sz_str = f"{sz / (1024*1024):.1f} MB" if sz > 1024*1024 else f"{sz / 1024:.0f} KB"
                self.queue_list.addItem(f"{Path(f).name} ({sz_str})  [{f}]")
            except Exception:
                self.queue_list.addItem(Path(f).name)

        total_mb = total_size / (1024*1024)
        self.q_count_lbl.setText(f"READY TO SEND ({len(self.selected_files)} FILES // {total_mb:.1f} MB)")

    def share_to_web_portal(self):
        """Copies selected files to ~/Downloads so phone can download them from web portal."""
        if not self.selected_files:
            QMessageBox.information(self, "Milo Drop", "Please select or drop at least one file first!")
            return

        copied = 0
        for f in self.selected_files:
            try:
                dest = DOWNLOADS_DIR / Path(f).name
                if Path(f).resolve() != dest.resolve():
                    import shutil
                    shutil.copy2(f, dest)
                copied += 1
            except Exception as e:
                print(f"Error sharing {f}: {e}")

        self.refresh_recent_files()
        QMessageBox.information(self, "Milo Drop Web Share", 
            f"✔ {copied} files are now hosted on your Milo Drop Web Portal!\n\nPhones can tap 'AVAILABLE FILES ON LAPTOP' to download them directly.")

    def send_to_peer(self):
        if not self.selected_files:
            QMessageBox.information(self, "Milo Drop", "Please select or drop files to send!")
            return

        target_ip = self.target_ip_edit.text().strip()
        if not target_ip:
            QMessageBox.warning(self, "Milo Drop", "Please enter receiver IP!")
            return

        first_file = self.selected_files[0]
        self.btn_send_now.setEnabled(False)
        self.progress_bar.setValue(0)

        self.sender_thread = SenderThread(first_file, target_ip, PORT)
        self.sender_thread.progress_signal.connect(self.on_send_progress)
        self.sender_thread.finished_signal.connect(self.on_send_finished)
        self.sender_thread.start()

    def on_send_progress(self, pct, msg):
        self.progress_bar.setValue(pct)
        self.progress_bar.setFormat(msg)

    def on_send_finished(self, success, msg):
        self.btn_send_now.setEnabled(True)
        if success:
            self.progress_bar.setValue(100)
            self.progress_bar.setFormat("Complete!")
            if self.selected_files:
                self.selected_files.pop(0)
                self.update_queue_ui()
            QMessageBox.information(self, "Milo Drop Success", msg)
        else:
            self.progress_bar.setValue(0)
            self.progress_bar.setFormat("Failed")
            QMessageBox.warning(self, "Milo Drop Error", msg)

    def refresh_recent_files(self):
        """Update received files widget with items from ~/Downloads."""
        self.received_list.clear()
        try:
            entries = []
            for entry in os.scandir(DOWNLOADS_DIR):
                if entry.is_file() and not entry.name.startswith('.'):
                    entries.append(entry)
            entries.sort(key=lambda e: e.stat().st_mtime, reverse=True)

            if not entries:
                empty_item = QListWidgetItem("No files received yet. Scan the QR code with your phone to drop files!")
                empty_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                empty_item.setForeground(QColor("#7a6e73"))
                empty_item.setSizeHint(QSize(280, 60))
                self.received_list.addItem(empty_item)
                return

            for e in entries[:20]:
                stat = e.stat()
                sz = stat.st_size
                sz_str = f"{sz / (1024*1024):.1f} MB" if sz > 1024*1024 else f"{sz / 1024:.0f} KB"
                mtime_str = time.strftime("%H:%M:%S", time.localtime(stat.st_mtime))

                item_widget = QWidget()
                item_widget.setFixedHeight(48)
                row = QHBoxLayout(item_widget)
                row.setContentsMargins(10, 4, 10, 4)
                row.setSpacing(8)

                col = QVBoxLayout()
                col.setSpacing(2)
                col.setContentsMargins(0, 0, 0, 0)

                lbl_name = QLabel(e.name)
                lbl_name.setStyleSheet("color: #ffffff; font-size: 12px; font-weight: 700;")
                
                lbl_meta = QLabel(f"{sz_str}  •  {mtime_str}")
                lbl_meta.setStyleSheet("color: #8c8286; font-size: 10px;")

                col.addWidget(lbl_name)
                col.addWidget(lbl_meta)
                row.addLayout(col)

                row.addStretch()

                btn_open = QPushButton("OPEN")
                btn_open.setFixedHeight(26)
                btn_open.clicked.connect(lambda ch, p=e.path: subprocess.Popen(["xdg-open", p]))
                row.addWidget(btn_open)

                btn_reveal = QPushButton("SHOW")
                btn_reveal.setObjectName("btnCyan")
                btn_reveal.setFixedHeight(26)
                btn_reveal.clicked.connect(lambda ch, p=DOWNLOADS_DIR: subprocess.Popen(["xdg-open", str(p)]))
                row.addWidget(btn_reveal)

                list_item = QListWidgetItem()
                list_item.setSizeHint(QSize(300, 56))
                self.received_list.addItem(list_item)
                self.received_list.setItemWidget(list_item, item_widget)

        except Exception as ex:
            print(f"Error scanning downloads: {ex}")

    def copy_server_url(self):
        try:
            p = subprocess.Popen(["wl-copy"], stdin=subprocess.PIPE)
            p.communicate(self.server_url.encode("utf-8"))
            self.statusBar_msg("Copied URL to clipboard!")
        except Exception:
            pass

    def open_browser(self):
        subprocess.Popen(["xdg-open", self.server_url])

    def open_downloads_folder(self):
        subprocess.Popen(["xdg-open", str(DOWNLOADS_DIR)])

    def paste_from_local_clipboard(self):
        try:
            txt = subprocess.check_output(["wl-paste", "--no-newline"], stderr=subprocess.DEVNULL).decode("utf-8", errors="replace")
            self.clip_edit.setText(txt)
        except Exception:
            pass

    def copy_to_local_clipboard(self):
        txt = self.clip_edit.text()
        if txt:
            try:
                p = subprocess.Popen(["wl-copy"], stdin=subprocess.PIPE)
                p.communicate(txt.encode("utf-8"))
                self.statusBar_msg("Copied to system clipboard!")
            except Exception:
                pass

    def statusBar_msg(self, msg):
        try:
            subprocess.Popen(["notify-send", "-a", "Milo Drop", msg])
        except Exception:
            pass


class DropZoneWidget(QFrame):
    """Custom Drag and Drop Area."""
    def __init__(self, parent_window):
        super().__init__()
        self.parent_window = parent_window
        self.setAcceptDrops(True)

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
            self.setStyleSheet("background-color: rgba(255, 8, 56, 0.15); border: 2px solid #ff0838;")

    def dragLeaveEvent(self, event):
        self.setStyleSheet("")

    def dropEvent(self, event):
        self.setStyleSheet("")
        paths = []
        for url in event.mimeData().urls():
            paths.append(url.toLocalFile())
        if paths:
            self.parent_window.add_dropped_files(paths)

    def mousePressEvent(self, event):
        self.parent_window.browse_files()


def main():
    os.environ.setdefault("QT_QPA_PLATFORM", "wayland;xcb")
    os.environ["QT_STYLE_OVERRIDE"] = "Fusion"

    app = QApplication(sys.argv)
    app.setApplicationName("milo-drop")
    app.setDesktopFileName("milo-drop")
    app.setWindowIcon(QIcon.fromTheme("network-wireless"))

    win = MiloDropWindow()
    win.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
