#!/usr/bin/env python3
"""
Milo Notes Native — High-Performance Wayland Markdown Knowledge Studio
Built natively with PyQt6 for MiloOS.
Features:
- Hierarchical Tree Folder Navigation (nested subdirectories)
- One-Click Daily Journaling (Ctrl+J)
- 3-Pane Studio Layout with instant search
- Interactive Force-Directed 2D Knowledge Graph (Ctrl+G)
- Obsidian-compatible [[WikiLinks]] across all folders
- Interactive checklists, auto-save, and Milo Eyes screen capture
"""

import sys
import os
os.environ["QT_STYLE_OVERRIDE"] = "Fusion"
os.environ["QT_LOGGING_RULES"] = "qt.qpa.wayland.textinput=false;qt.qpa.services=false;qt.qpa.*=false"
import re
import math
import time
import json
import random
import urllib.request
import urllib.error
import urllib.parse
import subprocess
from datetime import datetime
from pathlib import Path

from PyQt6.QtCore import (
    Qt, QSize, QRect, QRectF, QPointF, QLineF, QUrl, pyqtSignal, QTimer, QThread
)
from PyQt6.QtGui import (
    QIcon, QPixmap, QImage, QColor, QFont, QCursor, QKeySequence,
    QShortcut, QTextCursor, QPainter, QBrush, QPen, QRadialGradient,
    QPainterPath, QAction
)
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QSplitter, QListWidget, QListWidgetItem, QTreeWidget, QTreeWidgetItem,
    QLineEdit, QPushButton, QLabel, QTextBrowser, QPlainTextEdit,
    QFrame, QScrollArea, QMessageBox, QFileDialog, QInputDialog,
    QMenu, QGraphicsView, QGraphicsScene, QGraphicsItem, QStackedWidget
)

# Paths
NOTES_DIR = Path.home() / "MiloNotes"
NOTES_DIR.mkdir(parents=True, exist_ok=True)
ASSETS_DIR = NOTES_DIR / "assets"
ASSETS_DIR.mkdir(parents=True, exist_ok=True)

# Palette Constants (Obsidian Cyan Dark Theme)
BG_DARK = "#070b14"
BG_SIDEBAR = "#0c1322"
BG_LIST = "#10182b"
BG_PANEL = "#111a2e"
BG_EDITOR = "#0b1120"
BG_PREVIEW = "#080d19"
BG_HOVER = "#18243c"
BG_ACTIVE = "#1f3050"
BORDER_COLOR = "#1b2842"
ACCENT_CYAN = "#00f5ff"
ACCENT_CYAN_MUTED = "#38bdf8"
ACCENT_AMBER = "#fbbf24"
ACCENT_EMERALD = "#34d399"
ACCENT_ROSE = "#f43f5e"
TEXT_PRIMARY = "#f8fafc"
TEXT_MUTED = "#94a3b8"
TEXT_SUBTLE = "#64748b"

QSS_STYLE = f"""
QMainWindow {{
    background-color: {BG_DARK};
    border: 1px solid {BORDER_COLOR};
}}

QWidget {{
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    font-size: 13px;
    color: {TEXT_PRIMARY};
}}

/* Sidebar & Tree */
#Sidebar {{
    background-color: {BG_SIDEBAR};
    border-right: 1px solid {BORDER_COLOR};
}}

#SidebarHeader {{
    font-family: 'JetBrains Mono', monospace;
    font-size: 10.5px;
    font-weight: 700;
    color: {TEXT_SUBTLE};
    letter-spacing: 1px;
    text-transform: uppercase;
    padding: 10px 12px 4px 12px;
}}

QTreeWidget#VaultTree {{
    background-color: transparent;
    border: none;
    outline: none;
    padding: 2px 4px;
    color: {TEXT_MUTED};
    font-size: 12.5px;
}}

QTreeWidget#VaultTree::item {{
    padding: 4px 6px;
    border-radius: 4px;
    margin-bottom: 2px;
}}

QTreeWidget#VaultTree::item:hover {{
    background-color: {BG_HOVER};
    color: #ffffff;
}}

QTreeWidget#VaultTree::item:selected {{
    background-color: {BG_ACTIVE};
    color: {ACCENT_CYAN};
    font-weight: 600;
}}

/* Search & Inputs */
QLineEdit#SearchInput {{
    background-color: {BG_DARK};
    border: 1px solid {BORDER_COLOR};
    border-radius: 6px;
    padding: 7px 12px;
    color: {TEXT_PRIMARY};
    font-size: 12.5px;
}}
QLineEdit#SearchInput:focus {{
    border: 1px solid {ACCENT_CYAN};
}}

QLineEdit#TitleInput {{
    background-color: transparent;
    border: none;
    border-bottom: 1px solid transparent;
    font-size: 20px;
    font-weight: 700;
    color: #ffffff;
    padding: 4px 0;
}}
QLineEdit#TitleInput:focus {{
    border-bottom: 1px solid {ACCENT_CYAN};
}}

/* Note List */
#NoteListPane {{
    background-color: {BG_LIST};
    border-right: 1px solid {BORDER_COLOR};
}}

QListWidget#NoteList {{
    background-color: transparent;
    border: none;
    outline: none;
    padding: 4px;
}}
QListWidget#NoteList::item {{
    padding: 8px 10px;
    border-radius: 6px;
    margin-bottom: 4px;
    border: 1px solid transparent;
}}
QListWidget#NoteList::item:hover {{
    background-color: {BG_HOVER};
}}
QListWidget#NoteList::item:selected {{
    background-color: {BG_ACTIVE};
    border: 1px solid rgba(0, 245, 255, 0.4);
}}

/* Tag List */
QListWidget#TagList {{
    background-color: transparent;
    border: none;
    outline: none;
    padding: 2px 8px;
}}
QListWidget#TagList::item {{
    padding: 4px 8px;
    border-radius: 4px;
    color: {TEXT_MUTED};
    font-family: 'JetBrains Mono', monospace;
    font-size: 11px;
}}
QListWidget#TagList::item:hover {{
    background-color: {BG_HOVER};
    color: {ACCENT_CYAN};
}}
QListWidget#TagList::item:selected {{
    background-color: rgba(0, 245, 255, 0.15);
    color: {ACCENT_CYAN};
    font-weight: bold;
}}

/* Editor & Preview */
QPlainTextEdit#MarkdownEditor {{
    background-color: {BG_EDITOR};
    border: none;
    padding: 16px;
    color: #e2e8f0;
    font-family: 'JetBrains Mono', monospace;
    font-size: 13.5px;
    line-height: 1.6;
    selection-background-color: {BG_ACTIVE};
}}

QTextBrowser#MarkdownPreview {{
    background-color: {BG_PREVIEW};
    border: none;
    padding: 18px 24px;
    color: {TEXT_PRIMARY};
    font-size: 14px;
    line-height: 1.65;
    selection-background-color: {BG_ACTIVE};
}}

/* Buttons */
QPushButton {{
    background-color: rgba(0, 245, 255, 0.08);
    border: 1px solid rgba(0, 245, 255, 0.25);
    color: {ACCENT_CYAN};
    font-family: 'JetBrains Mono', monospace;
    font-size: 11px;
    font-weight: 600;
    padding: 6px 12px;
    border-radius: 4px;
    outline: none;
}}
QPushButton:hover {{
    background-color: rgba(0, 245, 255, 0.2);
    border-color: {ACCENT_CYAN};
    color: #ffffff;
}}
QPushButton:pressed {{
    background-color: rgba(0, 245, 255, 0.3);
}}

QPushButton#BtnActionSmall {{
    padding: 4px 8px;
    font-size: 10.5px;
}}

QPushButton#BtnDanger {{
    background-color: rgba(244, 63, 94, 0.1);
    border: 1px solid rgba(244, 63, 94, 0.3);
    color: {ACCENT_ROSE};
}}
QPushButton#BtnDanger:hover {{
    background-color: rgba(244, 63, 94, 0.3);
    border-color: {ACCENT_ROSE};
    color: #ffffff;
}}

/* Context Menu */
QMenu {{
    background-color: {BG_PANEL};
    border: 1px solid {BORDER_COLOR};
    padding: 4px;
}}
QMenu::item {{
    padding: 6px 20px 6px 12px;
    border-radius: 4px;
    color: {TEXT_PRIMARY};
}}
QMenu::item:selected {{
    background-color: {BG_ACTIVE};
    color: {ACCENT_CYAN};
}}

/* Scrollbars */
QScrollBar:vertical {{
    background: transparent;
    width: 6px;
    margin: 0;
}}
QScrollBar::handle:vertical {{
    background: #1e293b;
    min-height: 20px;
    border-radius: 3px;
}}
QScrollBar::handle:vertical:hover {{
    background: {ACCENT_CYAN};
}}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    height: 0px;
}}
QScrollBar:horizontal {{
    height: 0px;
}}

/* Toolbars & Status */
#TopToolbar {{
    background-color: {BG_SIDEBAR};
    border-bottom: 1px solid {BORDER_COLOR};
    padding: 6px 14px;
}}

#StatusBar {{
    background-color: {BG_DARK};
    border-top: 1px solid {BORDER_COLOR};
    padding: 4px 14px;
    font-family: 'JetBrains Mono', monospace;
    font-size: 11px;
    color: {TEXT_SUBTLE};
}}

QSplitter::handle {{
    background-color: {BORDER_COLOR};
}}
QSplitter::handle:hover {{
    background-color: {ACCENT_CYAN};
}}
"""

def parse_markdown_to_html(raw_md):
    """Render markdown into rich HTML with WikiLinks, images, tables, callouts, and interactive checklists."""
    if not raw_md:
        return ""

    html = raw_md
    html = html.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

    # 1. Code blocks (multi-line preformatted)
    def code_repl(match):
        lang = match.group(1).strip()
        code = match.group(2).strip()
        lang_badge = f'<div style="font-family:JetBrains Mono, monospace; font-size:10px; color:#64748b; text-transform:uppercase; margin-bottom:6px; letter-spacing:1px;">{lang}</div>' if lang else ''
        return f'<div style="background:#050812; border:1px solid #1e293b; border-radius:8px; padding:12px 14px; margin:12px 0;">{lang_badge}<pre style="margin:0; font-family:JetBrains Mono, monospace; color:#38bdf8; font-size:12px; line-height:1.5; white-space:pre-wrap;">{code}</pre></div>'
    html = re.sub(r'```([a-zA-Z0-9_\-\+]*)\n([\s\S]*?)```', code_repl, html)

    # 2. Inline code
    html = re.sub(r'`([^`]+)`', r'<code style="font-family:JetBrains Mono, monospace; background:rgba(0,245,255,0.08); border:1px solid rgba(0,245,255,0.25); color:#38bdf8; padding:2px 6px; border-radius:4px; font-size:12px;">\1</code>', html)

    # 3. Horizontal Rules
    html = re.sub(r'^(?:---|\*\*\*|___)\s*$', r'<hr style="border:none; border-top:1px solid #1e293b; margin:16px 0;">', html, flags=re.MULTILINE)

    # 4. Headers
    html = re.sub(r'^### (.*$)', r'<h3 style="color:#38bdf8; font-family:JetBrains Mono; margin-top:16px; margin-bottom:6px; font-size:14px; font-weight:700;">\1</h3>', html, flags=re.MULTILINE)
    html = re.sub(r'^## (.*$)', r'<h2 style="color:#fbbf24; font-family:JetBrains Mono; margin-top:20px; margin-bottom:8px; font-size:16px; font-weight:700;">\1</h2>', html, flags=re.MULTILINE)
    html = re.sub(r'^# (.*$)', r'<h1 style="color:#00f5ff; font-family:JetBrains Mono; border-bottom:1px solid rgba(0,245,255,0.25); padding-bottom:6px; margin-top:12px; margin-bottom:12px; font-size:20px; font-weight:800;">\1</h1>', html, flags=re.MULTILINE)

    # 5. Inline Images: ![alt](src)
    def img_repl(m):
        alt = m.group(1).strip()
        src = m.group(2).strip()
        if not (src.startswith("http://") or src.startswith("https://") or src.startswith("data:")):
            local_p = (NOTES_DIR / src).resolve()
            src = f"file://{local_p}"
        caption = f'<div style="color:#64748b; font-size:11px; margin-top:4px;">{alt}</div>' if alt else ''
        return f'<div style="margin:12px 0; text-align:center;"><img src="{src}" alt="{alt}" style="max-width:96%; border-radius:8px; border:1px solid #1e293b; box-shadow:0 4px 14px rgba(0,0,0,0.4);">{caption}</div>'
    html = re.sub(r'!\[([^\]]*)\]\(([^)]+)\)', img_repl, html)

    # 6. Standard Links: [title](url) (excluding images)
    def link_repl(m):
        title = m.group(1).strip()
        url = m.group(2).strip()
        return f'<a href="{url}" style="color:#00f5ff; text-decoration:underline; font-weight:600;">{title}</a>'
    html = re.sub(r'(?<!\!)\[([^\]]+)\]\(([^)]+)\)', link_repl, html)

    # 7. Interactive Tasks / Checklists
    html = re.sub(r'^\s*-\s*\[x\]\s*(.*$)', r'<div style="margin:5px 0;"><a href="toggle:\1" style="text-decoration:none; color:#10b981; font-weight:bold; font-size:14px; margin-right:6px;">☑</a> <span style="text-decoration:line-through; color:#64748b;">\1</span></div>', html, flags=re.MULTILINE)
    html = re.sub(r'^\s*-\s*\[ \]\s*(.*$)', r'<div style="margin:5px 0;"><a href="toggle:\1" style="text-decoration:none; color:#38bdf8; font-weight:bold; font-size:14px; margin-right:6px;">☐</a> <span style="color:#f8fafc;">\1</span></div>', html, flags=re.MULTILINE)

    # 8. Bullet Lists
    html = re.sub(r'^\s*[\-\*]\s+(.*$)', r'<li style="margin-bottom:4px; color:#e2e8f0;">\1</li>', html, flags=re.MULTILINE)
    html = re.sub(r'(<li>.*<\/li>)', r'<ul style="margin-left:16px; margin-bottom:10px;">\1</ul>', html, flags=re.DOTALL)

    # 9. Tables: | col | col |
    def table_repl(match):
        block = match.group(0).strip()
        lines = [l.strip() for l in block.splitlines() if l.strip()]
        if len(lines) < 2:
            return block
        headers = [c.strip() for c in lines[0].strip('|').split('|')]
        rows = [[c.strip() for c in l.strip('|').split('|')] for l in lines[2:]]
        th_html = "".join([f'<th style="border:1px solid #1e293b; padding:6px 12px; background:#0c1020; color:#00f5ff; font-weight:bold; text-align:left;">{h}</th>' for h in headers])
        tr_html = "".join(['<tr>' + "".join([f'<td style="border:1px solid #1e293b; padding:5px 12px; color:#e2e8f0;">{c}</td>' for c in r]) + '</tr>' for r in rows])
        return f'<div style="margin:12px 0; overflow-x:auto;"><table style="border-collapse:collapse; width:100%; border:1px solid #1e293b; font-size:12.5px;"><thead><tr>{th_html}</tr></thead><tbody>{tr_html}</tbody></table></div>'
    html = re.sub(r'((?:^\|.+?\|\s*$\n?){2,})', table_repl, html, flags=re.MULTILINE)

    # 10. Callout quotes & GitHub style alerts
    def callout_repl(match):
        content = match.group(1).strip()
        if content.startswith("[!NOTE]"):
            inner = content[7:].strip()
            return f'<div style="border-left:3px solid #38bdf8; background:rgba(56,189,248,0.08); padding:8px 12px; margin:10px 0; border-radius:0 6px 6px 0;"><span style="color:#38bdf8; font-weight:bold; font-size:11px;">ℹ NOTE</span><div style="color:#cbd5e1; margin-top:4px;">{inner}</div></div>'
        elif content.startswith("[!TIP]"):
            inner = content[6:].strip()
            return f'<div style="border-left:3px solid #10b981; background:rgba(16,185,129,0.08); padding:8px 12px; margin:10px 0; border-radius:0 6px 6px 0;"><span style="color:#10b981; font-weight:bold; font-size:11px;">💡 TIP</span><div style="color:#cbd5e1; margin-top:4px;">{inner}</div></div>'
        elif content.startswith("[!WARNING]"):
            inner = content[10:].strip()
            return f'<div style="border-left:3px solid #f59e0b; background:rgba(245,158,11,0.08); padding:8px 12px; margin:10px 0; border-radius:0 6px 6px 0;"><span style="color:#f59e0b; font-weight:bold; font-size:11px;">⚠️ WARNING</span><div style="color:#cbd5e1; margin-top:4px;">{inner}</div></div>'
        elif content.startswith("[!IMPORTANT]"):
            inner = content[12:].strip()
            return f'<div style="border-left:3px solid #00f5ff; background:rgba(0,245,255,0.08); padding:8px 12px; margin:10px 0; border-radius:0 6px 6px 0;"><span style="color:#00f5ff; font-weight:bold; font-size:11px;">⚡ IMPORTANT</span><div style="color:#cbd5e1; margin-top:4px;">{inner}</div></div>'
        else:
            return f'<div style="border-left:3px solid #00f5ff; background:rgba(0,245,255,0.05); padding:8px 12px; margin:10px 0; color:#94a3b8; font-style:italic; border-radius:0 4px 4px 0;">{content}</div>'
    html = re.sub(r'^\s*&gt;\s*(.*$)', callout_repl, html, flags=re.MULTILINE)

    # 11. WikiLinks: [[Target Note]]
    def wikilink_repl(m):
        target = m.group(1).strip()
        return f'<a href="wikilink:{target}" style="color:#00f5ff; text-decoration:none; font-weight:bold; background:rgba(0,245,255,0.1); padding:2px 7px; border-radius:4px; border:1px solid rgba(0,245,255,0.25);">🔗 {target}</a>'
    html = re.sub(r'\[\[([^\]]+)\]\]', wikilink_repl, html)

    # 12. Bold & Italic
    html = re.sub(r'\*\*([^*]+)\*\*', r'<strong style="color:#ffffff;">\1</strong>', html)
    html = re.sub(r'\*([^*]+)\*', r'<em style="color:#cbd5e1;">\1</em>', html)

    # 13. Paragraphs
    html = html.replace("\n\n", "</p><p style='margin-bottom:10px;'>")
    html = f"<div style='font-family:Inter, -apple-system, sans-serif; line-height:1.65; color:#f8fafc;'><p>{html}</p></div>"

    return html


# ==============================================================================
# Knowledge Graph View Components
# ==============================================================================

class GraphNodeItem(QGraphicsItem):
    def __init__(self, name, path, graph_view, is_current=False):
        super().__init__()
        self.name = name
        self.path = Path(path)
        self.graph_view = graph_view
        self.is_current = is_current
        self.is_hovered = False
        self.edges = []
        self.velocity = QPointF(0, 0)
        self.radius = 12.0
        self.press_pos = None

        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemSendsGeometryChanges)
        self.setAcceptHoverEvents(True)
        self.setZValue(2)

    def update_radius_by_links(self):
        links = len(self.edges)
        if links >= 4: self.radius = 18.0
        elif links >= 2: self.radius = 14.0
        else: self.radius = 11.0

    def boundingRect(self):
        r = self.radius + 6
        return QRectF(-r - 85, -r - 10, 2 * r + 170, 2 * r + 45)

    def shape(self):
        path = QPainterPath()
        path.addEllipse(-self.radius, -self.radius, 2 * self.radius, 2 * self.radius)
        return path

    def paint(self, painter, option, widget=None):
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        r = self.radius

        if self.is_current or self.is_hovered:
            glow_col = QColor(0, 245, 255, 200) if self.is_current else QColor(251, 191, 36, 220)
            glow_pen = QPen(glow_col, 2.5)
            painter.setPen(glow_pen)
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawEllipse(QRectF(-r - 4, -r - 4, 2 * (r + 4), 2 * (r + 4)))

        grad = QRadialGradient(-r * 0.3, -r * 0.3, r * 1.4)
        if self.is_current:
            grad.setColorAt(0.0, QColor("#38bdf8"))
            grad.setColorAt(1.0, QColor("#0284c7"))
            border_col = QColor("#00f5ff")
        elif len(self.edges) >= 3:
            grad.setColorAt(0.0, QColor("#fbbf24"))
            grad.setColorAt(1.0, QColor("#d97706"))
            border_col = QColor("#fde68a")
        elif len(self.edges) > 0:
            grad.setColorAt(0.0, QColor("#38bdf8"))
            grad.setColorAt(1.0, QColor("#0f172a"))
            border_col = QColor("#00f5ff")
        else:
            grad.setColorAt(0.0, QColor("#64748b"))
            grad.setColorAt(1.0, QColor("#1e293b"))
            border_col = QColor("#94a3b8")

        painter.setBrush(QBrush(grad))
        painter.setPen(QPen(border_col, 1.5))
        painter.drawEllipse(QRectF(-r, -r, 2 * r, 2 * r))

        painter.setBrush(QBrush(QColor("#ffffff")))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(QRectF(-2.5, -2.5, 5, 5))

        font = QFont("JetBrains Mono", 8)
        font.setBold(self.is_current or self.is_hovered)
        painter.setFont(font)
        painter.setPen(QColor("#ffffff") if (self.is_hovered or self.is_current) else QColor("#94a3b8"))

        clean_name = self.name.replace("_", " ")
        if len(clean_name) > 22: clean_name = clean_name[:20] + ".."
        painter.drawText(QRectF(-80, r + 4, 160, 20), Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignTop, clean_name)

    def hoverEnterEvent(self, event):
        self.is_hovered = True
        for e in self.edges: e.set_highlighted(True)
        self.update()
        super().hoverEnterEvent(event)

    def hoverLeaveEvent(self, event):
        self.is_hovered = False
        for e in self.edges: e.set_highlighted(False)
        self.update()
        super().hoverLeaveEvent(event)

    def mousePressEvent(self, event):
        self.press_pos = event.pos()
        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        super().mouseReleaseEvent(event)
        if self.press_pos:
            dist = (event.pos() - self.press_pos).manhattanLength()
            if dist < 5:
                self.graph_view.node_selected.emit(str(self.path))

    def itemChange(self, change, value):
        if change == QGraphicsItem.GraphicsItemChange.ItemPositionHasChanged:
            for e in self.edges: e.adjust()
            self.graph_view.start_simulation()
        return super().itemChange(change, value)


class GraphEdgeItem(QGraphicsItem):
    def __init__(self, source_node, dest_node):
        super().__init__()
        self.source = source_node
        self.dest = dest_node
        self.source.edges.append(self)
        self.dest.edges.append(self)
        self.is_highlighted = False
        self.setZValue(1)
        self.adjust()

    def adjust(self):
        self.prepareGeometryChange()

    def set_highlighted(self, hl):
        self.is_highlighted = hl
        self.update()

    def boundingRect(self):
        p1 = self.source.pos()
        p2 = self.dest.pos()
        extra = 6
        return QRectF(p1, p2).normalized().adjusted(-extra, -extra, extra, extra)

    def paint(self, painter, option, widget=None):
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        p1 = self.source.pos()
        p2 = self.dest.pos()
        pen = QPen(QColor(0, 245, 255, 220), 2.2) if self.is_highlighted else QPen(QColor(56, 189, 248, 70), 1.2)
        painter.setPen(pen)
        painter.drawLine(p1, p2)


class KnowledgeGraphView(QGraphicsView):
    node_selected = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.scene = QGraphicsScene(self)
        self.setScene(self.scene)
        self.scene.setSceneRect(-600, -500, 1200, 1000)

        self.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.ViewportAnchor.AnchorViewCenter)
        self.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)
        self.setStyleSheet(f"background-color: {BG_DARK}; border: none;")

        self.nodes = {}
        self.edges = []
        self.current_active_path = None

        self.physics_timer = QTimer(self)
        self.physics_timer.timeout.connect(self.run_physics_step)
        self.sim_iterations = 0

    def drawBackground(self, painter, rect):
        painter.fillRect(rect, QColor("#060a14"))
        grid_pen = QPen(QColor(0, 245, 255, 18), 1)
        painter.setPen(grid_pen)
        left = int(rect.left()) - (int(rect.left()) % 40)
        top = int(rect.top()) - (int(rect.top()) % 40)
        for x in range(left, int(rect.right()), 40):
            for y in range(top, int(rect.bottom()), 40):
                painter.drawPoint(x, y)

    def wheelEvent(self, event):
        factor = 1.15 if event.angleDelta().y() > 0 else 0.87
        self.scale(factor, factor)

    def start_simulation(self):
        self.sim_iterations = 0
        if not self.physics_timer.isActive():
            self.physics_timer.start(16)

    def run_physics_step(self):
        self.sim_iterations += 1
        node_list = list(self.nodes.values())
        if not node_list:
            self.physics_timer.stop()
            return

        total_kinetic_energy = 0.0

        for i in range(len(node_list)):
            n1 = node_list[i]
            for j in range(i + 1, len(node_list)):
                n2 = node_list[j]
                dx = n1.x() - n2.x()
                dy = n1.y() - n2.y()
                dist = math.sqrt(dx * dx + dy * dy) + 0.1
                if dist < 350:
                    force = 5000.0 / (dist * dist)
                    fx = (dx / dist) * force
                    fy = (dy / dist) * force
                    n1.velocity += QPointF(fx, fy)
                    n2.velocity -= QPointF(fx, fy)

        for edge in self.edges:
            p1 = edge.source.pos()
            p2 = edge.dest.pos()
            dx = p2.x() - p1.x()
            dy = p2.y() - p1.y()
            dist = math.sqrt(dx * dx + dy * dy)
            target_dist = 140.0
            force = 0.04 * (dist - target_dist)
            if dist > 0.1:
                fx = (dx / dist) * force
                fy = (dy / dist) * force
                edge.source.velocity += QPointF(fx, fy)
                edge.dest.velocity -= QPointF(fx, fy)

        for node in node_list:
            node.velocity += QPointF(-0.007 * node.x(), -0.007 * node.y())
            node.velocity *= 0.80
            speed = math.sqrt(node.velocity.x()**2 + node.velocity.y()**2)
            if speed > 15.0:
                node.velocity = (node.velocity / speed) * 15.0
            total_kinetic_energy += speed
            node.setPos(node.pos() + node.velocity)

        if total_kinetic_energy < 0.25 or self.sim_iterations > 300:
            self.physics_timer.stop()

    def build_graph(self, notes_data, current_path=None):
        self.scene.clear()
        self.nodes = {}
        self.edges = []
        self.current_active_path = str(current_path) if current_path else None

        if not notes_data:
            return

        angle_step = (2 * math.pi) / len(notes_data)
        radius = min(220, max(80, len(notes_data) * 28))

        for idx, n in enumerate(notes_data):
            p = n["path"]
            name = p.stem
            is_active = (str(p) == self.current_active_path)
            
            node = GraphNodeItem(name, p, self, is_current=is_active)
            angle = idx * angle_step + random.uniform(-0.1, 0.1)
            node.setPos(radius * math.cos(angle), radius * math.sin(angle))
            self.scene.addItem(node)
            self.nodes[name] = node

        added_edges = set()
        for n in notes_data:
            src_name = n["path"].stem
            src_node = self.nodes.get(src_name)
            if not src_node:
                continue

            try:
                with open(n["path"], "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read()
                
                targets = re.findall(r'\[\[([^\]]+)\]\]', content)
                for t in targets:
                    dest_name = t.strip().replace(" ", "_")
                    dest_node = self.nodes.get(dest_name)
                    if dest_node and dest_node != src_node:
                        edge_key = tuple(sorted([src_name, dest_name]))
                        if edge_key not in added_edges:
                            added_edges.add(edge_key)
                            edge = GraphEdgeItem(src_node, dest_node)
                            self.scene.addItem(edge)
                            self.edges.append(edge)
            except Exception:
                pass

        for node in self.nodes.values():
            node.update_radius_by_links()

        self.start_simulation()

    def reset_view(self):
        self.resetTransform()
        self.centerOn(0, 0)


# ==============================================================================
# Enhanced Markdown Editor with Image Paste, Indentation & Auto-Pairing
# ==============================================================================

class MiloMarkdownEditor(QPlainTextEdit):
    image_pasted = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("MarkdownEditor")

    def keyPressEvent(self, event):
        # 1. Clipboard image paste on Ctrl+V
        if event.key() == Qt.Key.Key_V and (event.modifiers() & Qt.KeyboardModifier.ControlModifier):
            clipboard = QApplication.clipboard()
            mime = clipboard.mimeData()
            if mime.hasImage():
                img = clipboard.image()
                if not img.isNull():
                    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
                    filename = f"paste_{ts}.png"
                    filepath = ASSETS_DIR / filename
                    img.save(str(filepath), "PNG")
                    cursor = self.textCursor()
                    cursor.insertText(f"\n![Image](assets/{filename})\n")
                    self.image_pasted.emit(str(filepath))
                    event.accept()
                    return

        # 2. Indent with Tab / Unindent with Shift+Tab
        if event.key() == Qt.Key.Key_Tab:
            cursor = self.textCursor()
            cursor.insertText("  ")
            event.accept()
            return
        elif event.key() == Qt.Key.Key_Backtab:
            cursor = self.textCursor()
            cursor.movePosition(QTextCursor.MoveOperation.StartOfLine)
            cursor.movePosition(QTextCursor.MoveOperation.Right, QTextCursor.MoveMode.KeepAnchor, 2)
            if cursor.selectedText() == "  ":
                cursor.removeSelectedText()
            event.accept()
            return

        # 3. Ctrl+D or Ctrl+Return to toggle checkbox on current line
        if (event.key() == Qt.Key.Key_D or event.key() == Qt.Key.Key_Return) and (event.modifiers() & Qt.KeyboardModifier.ControlModifier):
            cursor = self.textCursor()
            cursor.select(QTextCursor.SelectionType.LineUnderCursor)
            line = cursor.selectedText()
            if "- [ ] " in line:
                new_line = line.replace("- [ ] ", "- [x] ", 1)
            elif "- [x] " in line:
                new_line = line.replace("- [x] ", "- [ ] ", 1)
            elif line.strip().startswith("- "):
                new_line = line.replace("- ", "- [ ] ", 1)
            else:
                new_line = "- [ ] " + line.lstrip()
            cursor.insertText(new_line)
            event.accept()
            return

        # 4. Smart bracket / quote auto-pairing with selection wrapping
        cursor = self.textCursor()
        if cursor.hasSelection():
            sel = cursor.selectedText()
            char = event.text()
            if char == "[":
                cursor.insertText(f"[[{sel}]]" if sel.startswith("[") and sel.endswith("]") else f"[{sel}]")
                event.accept()
                return
            elif char == "*":
                cursor.insertText(f"**{sel}**")
                event.accept()
                return
            elif char == "`":
                cursor.insertText(f"`{sel}`")
                event.accept()
                return
            elif char == "(":
                cursor.insertText(f"({sel})")
                event.accept()
                return
            elif char == '"':
                cursor.insertText(f'"{sel}"')
                event.accept()
                return

        super().keyPressEvent(event)


# ==============================================================================
# Main Studio Window (Hierarchical Tree + 3-Pane + Graph)
# ==============================================================================

class MiloNotesNativeWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.current_file = None
        self.active_folder = NOTES_DIR
        self.auto_save_timer = QTimer(self)
        self.auto_save_timer.setSingleShot(True)
        self.auto_save_timer.timeout.connect(self.save_current_note)

        self.all_notes = []
        self.current_filter_tag = None
        self.current_filter_folder = None
        self.view_mode = "split"

        self.init_ui()
        self.setup_shortcuts()
        self.setStyleSheet(QSS_STYLE)

        self.reload_vault()

    def init_ui(self):
        self.setWindowTitle("Milo Notes — Markdown Studio")
        self.resize(1200, 750)

        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # 1. Top Global Studio Toolbar
        topbar = QWidget()
        topbar.setObjectName("TopToolbar")
        topbar.setFixedHeight(46)
        tb_layout = QHBoxLayout(topbar)
        tb_layout.setContentsMargins(12, 6, 12, 6)
        tb_layout.setSpacing(8)

        brand_lbl = QLabel("📝 MILO NOTES")
        brand_lbl.setStyleSheet(f"font-family: 'JetBrains Mono'; font-weight: bold; font-size: 13px; color: {ACCENT_CYAN};")
        
        self.vault_badge = QLabel(f"VAULT: {NOTES_DIR.name}")
        self.vault_badge.setStyleSheet(f"font-family: 'JetBrains Mono'; font-size: 11px; color: {TEXT_MUTED}; background: {BG_DARK}; padding: 3px 8px; border-radius: 4px; border: 1px solid {BORDER_COLOR};")

        tb_layout.addWidget(brand_lbl)
        tb_layout.addWidget(self.vault_badge)
        tb_layout.addStretch()

        # View Mode Toggle Buttons
        self.btn_mode_split = QPushButton("◫ SPLIT")
        self.btn_mode_split.clicked.connect(lambda: self.set_view_mode("split"))
        
        self.btn_mode_edit = QPushButton("✎ EDIT")
        self.btn_mode_edit.clicked.connect(lambda: self.set_view_mode("editor"))
        
        self.btn_mode_view = QPushButton("👁 VIEW")
        self.btn_mode_view.clicked.connect(lambda: self.set_view_mode("preview"))

        self.btn_mode_graph = QPushButton("🕸 GRAPH")
        self.btn_mode_graph.setToolTip("Interactive 2D Knowledge Graph (Ctrl+G)")
        self.btn_mode_graph.clicked.connect(lambda: self.set_view_mode("graph"))

        tb_layout.addWidget(self.btn_mode_split)
        tb_layout.addWidget(self.btn_mode_edit)
        tb_layout.addWidget(self.btn_mode_view)
        tb_layout.addWidget(self.btn_mode_graph)

        # Action Buttons
        self.btn_daily = QPushButton("📅 DAILY")
        self.btn_daily.setToolTip("Create / Open Today's Journal Note (Ctrl+J)")
        self.btn_daily.clicked.connect(self.open_daily_note)
        tb_layout.addWidget(self.btn_daily)

        self.btn_snap = QPushButton("📸 SNAP SCREEN")
        self.btn_snap.setToolTip("Capture screen region via Milo Eyes and insert image (Ctrl+Shift+I)")
        self.btn_snap.clicked.connect(self.trigger_milo_eyes_snap)
        tb_layout.addWidget(self.btn_snap)

        self.btn_ai = QPushButton("✨ AI ASSIST")
        self.btn_ai.clicked.connect(self.trigger_ai_assist)
        tb_layout.addWidget(self.btn_ai)

        self.btn_export = QPushButton("📤 EXPORT")
        self.btn_export.clicked.connect(self.show_export_menu)
        tb_layout.addWidget(self.btn_export)

        main_layout.addWidget(topbar)

        # 2. Main 3-Pane Splitter
        self.main_splitter = QSplitter(Qt.Orientation.Horizontal)

        # --- Pane 1: Hierarchical Vault Tree & Tags Sidebar ---
        sidebar = QWidget()
        sidebar.setObjectName("Sidebar")
        sidebar.setFixedWidth(240)
        sb_layout = QVBoxLayout(sidebar)
        sb_layout.setContentsMargins(0, 0, 0, 0)
        sb_layout.setSpacing(4)

        # Explorer Toolbar
        tree_toolbar = QHBoxLayout()
        tree_toolbar.setContentsMargins(12, 10, 10, 4)
        
        sb_lbl_vault = QLabel("VAULT EXPLORER")
        sb_lbl_vault.setObjectName("SidebarHeader")
        sb_lbl_vault.setStyleSheet("padding: 0;")
        
        btn_add_folder = QPushButton("📁+")
        btn_add_folder.setObjectName("BtnActionSmall")
        btn_add_folder.setToolTip("New Subfolder")
        btn_add_folder.clicked.connect(self.create_new_folder)

        btn_refresh = QPushButton("⟲")
        btn_refresh.setObjectName("BtnActionSmall")
        btn_refresh.setToolTip("Reload Vault")
        btn_refresh.clicked.connect(self.reload_vault)

        tree_toolbar.addWidget(sb_lbl_vault)
        tree_toolbar.addStretch()
        tree_toolbar.addWidget(btn_add_folder)
        tree_toolbar.addWidget(btn_refresh)
        sb_layout.addLayout(tree_toolbar)

        # Hierarchical Vault QTreeWidget
        self.vault_tree = QTreeWidget()
        self.vault_tree.setObjectName("VaultTree")
        self.vault_tree.setHeaderHidden(True)
        self.vault_tree.itemClicked.connect(self.on_tree_item_clicked)
        self.vault_tree.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.vault_tree.customContextMenuRequested.connect(self.show_tree_context_menu)
        sb_layout.addWidget(self.vault_tree, stretch=3)

        # Tags Section
        sb_lbl_tags = QLabel("TAG CLOUD")
        sb_lbl_tags.setObjectName("SidebarHeader")
        sb_layout.addWidget(sb_lbl_tags)

        self.tag_list = QListWidget()
        self.tag_list.setObjectName("TagList")
        self.tag_list.itemClicked.connect(self.on_tag_selected)
        sb_layout.addWidget(self.tag_list, stretch=1)

        # Bottom stats
        self.note_count_lbl = QLabel("0 notes in vault")
        self.note_count_lbl.setStyleSheet(f"font-family: 'JetBrains Mono'; font-size: 11px; color: {TEXT_SUBTLE}; padding: 10px 14px;")
        sb_layout.addWidget(self.note_count_lbl)

        self.main_splitter.addWidget(sidebar)

        # --- Pane 2: Note List Stream Pane ---
        note_list_pane = QWidget()
        note_list_pane.setObjectName("NoteListPane")
        note_list_pane.setFixedWidth(270)
        nlp_layout = QVBoxLayout(note_list_pane)
        nlp_layout.setContentsMargins(10, 10, 10, 10)
        nlp_layout.setSpacing(8)

        search_row = QHBoxLayout()
        search_row.setSpacing(6)
        self.search_input = QLineEdit()
        self.search_input.setObjectName("SearchInput")
        self.search_input.setPlaceholderText("Search all notes (Ctrl+F)...")
        self.search_input.textChanged.connect(self.filter_notes)
        
        self.btn_new_note = QPushButton("+ Note")
        self.btn_new_note.setObjectName("BtnNewNote")
        self.btn_new_note.setToolTip("Create Note in active folder (Ctrl+N)")
        self.btn_new_note.clicked.connect(self.create_new_note)

        search_row.addWidget(self.search_input)
        search_row.addWidget(self.btn_new_note)
        nlp_layout.addLayout(search_row)

        self.current_folder_lbl = QLabel("📂 ~/MiloNotes")
        self.current_folder_lbl.setStyleSheet(f"font-family: 'JetBrains Mono'; font-size: 10.5px; color: {ACCENT_CYAN_MUTED}; padding: 2px 4px;")
        nlp_layout.addWidget(self.current_folder_lbl)

        self.note_list = QListWidget()
        self.note_list.setObjectName("NoteList")
        self.note_list.itemClicked.connect(self.on_note_selected)
        nlp_layout.addWidget(self.note_list)

        self.main_splitter.addWidget(note_list_pane)

        # --- Pane 3: Right Stack (Studio vs Knowledge Graph) ---
        self.right_stack = QStackedWidget()

        # Page 0: Editor & Preview Studio
        editor_studio = QWidget()
        es_layout = QVBoxLayout(editor_studio)
        es_layout.setContentsMargins(0, 0, 0, 0)
        es_layout.setSpacing(0)

        # Note Header
        note_header = QWidget()
        note_header.setFixedHeight(50)
        note_header.setStyleSheet(f"background-color: {BG_DARK}; border-bottom: 1px solid {BORDER_COLOR}; padding: 10px 16px;")
        nh_layout = QHBoxLayout(note_header)
        nh_layout.setContentsMargins(0, 0, 0, 0)
        nh_layout.setSpacing(10)

        self.title_input = QLineEdit()
        self.title_input.setObjectName("TitleInput")
        self.title_input.setPlaceholderText("Untitled Note...")
        self.title_input.textChanged.connect(self.on_title_changed)
        nh_layout.addWidget(self.title_input)

        self.path_badge = QLabel("root")
        self.path_badge.setStyleSheet(f"font-family: 'JetBrains Mono'; font-size: 11px; color: {TEXT_SUBTLE}; background: #0c1424; padding: 4px 8px; border-radius: 4px;")
        nh_layout.addWidget(self.path_badge)

        self.btn_delete_note = QPushButton("🗑")
        self.btn_delete_note.setObjectName("BtnDanger")
        self.btn_delete_note.setToolTip("Delete Note")
        self.btn_delete_note.clicked.connect(self.delete_current_note)
        nh_layout.addWidget(self.btn_delete_note)

        es_layout.addWidget(note_header)

        # Splitter between Editor and Preview
        self.editor_preview_splitter = QSplitter(Qt.Orientation.Horizontal)

        self.editor = MiloMarkdownEditor()
        self.editor.setObjectName("MarkdownEditor")
        self.editor.textChanged.connect(self.on_editor_text_changed)
        self.editor.image_pasted.connect(lambda p: (self.update_preview(), self.save_current_note()))
        self.editor_preview_splitter.addWidget(self.editor)

        self.preview = QTextBrowser()
        self.preview.setObjectName("MarkdownPreview")
        self.preview.setOpenLinks(False)
        self.preview.anchorClicked.connect(self.on_preview_link_clicked)
        self.editor_preview_splitter.addWidget(self.preview)

        es_layout.addWidget(self.editor_preview_splitter)

        # Status Bar
        statusbar = QWidget()
        statusbar.setObjectName("StatusBar")
        statusbar.setFixedHeight(28)
        sb_bar_layout = QHBoxLayout(statusbar)
        sb_bar_layout.setContentsMargins(12, 4, 12, 4)

        self.lbl_stats = QLabel("0 words  |  0 chars  |  0 min read")
        self.lbl_save_status = QLabel("● Saved")
        self.lbl_save_status.setStyleSheet(f"color: {ACCENT_EMERALD}; font-weight: bold;")

        sb_bar_layout.addWidget(self.lbl_stats)
        sb_bar_layout.addStretch()
        sb_bar_layout.addWidget(self.lbl_save_status)
        es_layout.addWidget(statusbar)

        self.right_stack.addWidget(editor_studio)

        # Page 1: Knowledge Graph Studio
        graph_studio = QWidget()
        gs_layout = QVBoxLayout(graph_studio)
        gs_layout.setContentsMargins(0, 0, 0, 0)
        gs_layout.setSpacing(0)

        graph_header = QWidget()
        graph_header.setFixedHeight(46)
        graph_header.setStyleSheet(f"background-color: {BG_DARK}; border-bottom: 1px solid {BORDER_COLOR}; padding: 8px 16px;")
        gh_layout = QHBoxLayout(graph_header)
        gh_layout.setContentsMargins(0, 0, 0, 0)
        gh_layout.setSpacing(10)

        gh_title = QLabel("🕸 KNOWLEDGE GRAPH EXPLORER")
        gh_title.setStyleSheet(f"font-family: 'JetBrains Mono'; font-weight: bold; font-size: 12px; color: {ACCENT_CYAN};")
        gh_layout.addWidget(gh_title)

        gh_legend = QLabel("🟡 Hub  |  🔵 Connected  |  🟢 Active Note")
        gh_legend.setStyleSheet(f"font-family: 'JetBrains Mono'; font-size: 11px; color: {TEXT_MUTED};")
        gh_layout.addWidget(gh_legend)
        gh_layout.addStretch()

        btn_recenter = QPushButton("⟲ RE-CENTER")
        btn_recenter.clicked.connect(lambda: self.graph_view.reset_view())
        
        btn_shake = QPushButton("⚡ RELAX GRAPH")
        btn_shake.clicked.connect(lambda: self.graph_view.start_simulation())

        gh_layout.addWidget(btn_recenter)
        gh_layout.addWidget(btn_shake)
        gs_layout.addWidget(graph_header)

        self.graph_view = KnowledgeGraphView()
        self.graph_view.node_selected.connect(self.on_graph_node_selected)
        gs_layout.addWidget(self.graph_view)

        self.right_stack.addWidget(graph_studio)

        self.main_splitter.addWidget(self.right_stack)

        self.main_splitter.setSizes([230, 260, 710])
        self.editor_preview_splitter.setSizes([355, 355])

        main_layout.addWidget(self.main_splitter)

    def setup_shortcuts(self):
        QShortcut(QKeySequence("Ctrl+N"), self, self.create_new_note)
        QShortcut(QKeySequence("Ctrl+J"), self, self.open_daily_note)
        QShortcut(QKeySequence("Ctrl+F"), self, lambda: self.search_input.setFocus())
        QShortcut(QKeySequence("Ctrl+S"), self, self.save_current_note)
        QShortcut(QKeySequence("Ctrl+G"), self, self.toggle_graph_view)
        QShortcut(QKeySequence("Ctrl+Shift+I"), self, self.trigger_milo_eyes_snap)
        QShortcut(QKeySequence("Escape"), self, self.close)

    def toggle_graph_view(self):
        if self.right_stack.currentIndex() == 0:
            self.set_view_mode("graph")
        else:
            self.set_view_mode("split")

    def reload_vault(self, select_filepath=None):
        """Recursively scan ~/MiloNotes, rebuild Tree, Notes List, and Tags."""
        self.all_notes = []
        tags_set = set()

        # 1. Recursive scan for all .md files
        for p in NOTES_DIR.glob("**/*.md"):
            if "assets" in p.parts:
                continue
            try:
                stat = p.stat()
                mtime = stat.st_mtime
                with open(p, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read()

                title = p.stem.replace("_", " ")
                lines = content.strip().splitlines()
                snippet = lines[0] if lines else "Empty note"
                if lines and lines[0].startswith("# "):
                    title = lines[0][2:].strip()
                    snippet = lines[1] if len(lines) > 1 else ""

                rel_folder = p.parent.relative_to(NOTES_DIR)
                rel_str = str(rel_folder) if str(rel_folder) != "." else ""

                found_tags = re.findall(r'#([a-zA-Z0-9_\-]+)', content)
                for t in found_tags:
                    tags_set.add(t)

                self.all_notes.append({
                    "path": p,
                    "filename": p.name,
                    "rel_folder": rel_str,
                    "title": title,
                    "snippet": snippet[:60],
                    "mtime": mtime,
                    "tags": found_tags
                })
            except Exception:
                pass

        self.all_notes.sort(key=lambda x: x["mtime"], reverse=True)

        # 2. Populate Hierarchical QTreeWidget
        self.vault_tree.clear()
        vault_root = QTreeWidgetItem(self.vault_tree)
        vault_root.setText(0, f"📂 {NOTES_DIR.name} ({len(self.all_notes)})")
        vault_root.setData(0, Qt.ItemDataRole.UserRole, str(NOTES_DIR))
        vault_root.setData(0, Qt.ItemDataRole.UserRole + 1, "folder")
        vault_root.setExpanded(True)

        self._populate_tree_recursive(vault_root, NOTES_DIR)

        # 3. Populate Tag list
        self.tag_list.clear()
        for t in sorted(tags_set):
            item = QListWidgetItem(f"#{t}")
            item.setData(Qt.ItemDataRole.UserRole, t)
            self.tag_list.addItem(item)

        self.note_count_lbl.setText(f"{len(self.all_notes)} notes across vault")
        self.filter_notes(select_filepath=select_filepath)

        # 4. Update Knowledge Graph
        self.graph_view.build_graph(self.all_notes, self.current_file)

    def _populate_tree_recursive(self, parent_item, current_dir):
        try:
            entries = sorted(current_dir.iterdir(), key=lambda p: (not p.is_dir(), p.name.lower()))
            for entry in entries:
                if entry.name.startswith(".") or entry.name == "assets":
                    continue
                if entry.is_dir():
                    count = len([f for f in entry.glob("**/*.md") if "assets" not in f.parts])
                    folder_item = QTreeWidgetItem(parent_item)
                    folder_item.setText(0, f"📁 {entry.name} ({count})")
                    folder_item.setData(0, Qt.ItemDataRole.UserRole, str(entry))
                    folder_item.setData(0, Qt.ItemDataRole.UserRole + 1, "folder")
                    folder_item.setExpanded(True)
                    self._populate_tree_recursive(folder_item, entry)
                elif entry.suffix == ".md":
                    file_item = QTreeWidgetItem(parent_item)
                    title = entry.stem.replace("_", " ")
                    file_item.setText(0, f"📄 {title}")
                    file_item.setData(0, Qt.ItemDataRole.UserRole, str(entry))
                    file_item.setData(0, Qt.ItemDataRole.UserRole + 1, "file")
        except Exception:
            pass

    def on_tree_item_clicked(self, item, column):
        path_str = item.data(0, Qt.ItemDataRole.UserRole)
        item_type = item.data(0, Qt.ItemDataRole.UserRole + 1)
        
        if not path_str:
            return
        p = Path(path_str)

        if item_type == "folder":
            self.active_folder = p
            self.current_filter_folder = p
            self.current_filter_tag = None
            rel_name = p.relative_to(NOTES_DIR)
            self.current_folder_lbl.setText(f"📁 ~/{NOTES_DIR.name}/{rel_name}" if str(rel_name) != "." else f"📂 ~/{NOTES_DIR.name}")
            self.filter_notes()
        elif item_type == "file":
            self.active_folder = p.parent
            self.load_note_file(p)
            if self.right_stack.currentIndex() == 1:
                self.set_view_mode("split")

    def show_tree_context_menu(self, pos):
        item = self.vault_tree.itemAt(pos)
        menu = QMenu(self)

        if item:
            path_str = item.data(0, Qt.ItemDataRole.UserRole)
            item_type = item.data(0, Qt.ItemDataRole.UserRole + 1)
            target_path = Path(path_str)

            if item_type == "folder":
                act_new_note = menu.addAction("📄 New Note Here")
                act_new_sub = menu.addAction("📁 New Subfolder")
                menu.addSeparator()
                act_rename = menu.addAction("✏️ Rename Folder")
                act_del = menu.addAction("🗑️ Delete Folder")

                action = menu.exec(self.vault_tree.viewport().mapToGlobal(pos))
                if action == act_new_note:
                    self.active_folder = target_path
                    self.create_new_note()
                elif action == act_new_sub:
                    self.create_new_folder(parent_dir=target_path)
                elif action == act_rename:
                    self.rename_folder(target_path)
                elif action == act_del:
                    self.delete_folder(target_path)
            elif item_type == "file":
                act_open = menu.addAction("👁 Open Note")
                act_del = menu.addAction("🗑️ Delete Note")
                action = menu.exec(self.vault_tree.viewport().mapToGlobal(pos))
                if action == act_open:
                    self.load_note_file(target_path)
                elif action == act_del:
                    self.current_file = target_path
                    self.delete_current_note()
        else:
            act_new_folder = menu.addAction("📁 New Root Folder")
            act_refresh = menu.addAction("⟲ Refresh Vault")
            action = menu.exec(self.vault_tree.viewport().mapToGlobal(pos))
            if action == act_new_folder:
                self.create_new_folder()
            elif action == act_refresh:
                self.reload_vault()

    def filter_notes(self, query=None, select_filepath=None):
        self.note_list.clear()
        search_q = (self.search_input.text() if query is None else query).lower().strip()

        matched = []
        for n in self.all_notes:
            # Folder filter
            if self.current_filter_folder:
                try:
                    n["path"].relative_to(self.current_filter_folder)
                except ValueError:
                    continue

            # Tag filter
            if self.current_filter_tag and self.current_filter_tag not in n["tags"]:
                continue

            # Search query
            if search_q:
                if search_q not in n["title"].lower() and search_q not in n["snippet"].lower() and search_q not in n["rel_folder"].lower():
                    continue
            matched.append(n)

        target_idx = 0
        for i, n in enumerate(matched):
            dt_str = datetime.fromtimestamp(n["mtime"]).strftime("%b %d")
            folder_badge = f"📁 {n['rel_folder']}" if n['rel_folder'] else "📄 root"
            item = QListWidgetItem(f"{n['title']}\n{folder_badge}  •  {dt_str}")
            item.setData(Qt.ItemDataRole.UserRole, str(n["path"]))
            self.note_list.addItem(item)
            if select_filepath and str(n["path"]) == str(select_filepath):
                target_idx = i

        if matched:
            self.note_list.setCurrentRow(target_idx)
            self.load_note_file(matched[target_idx]["path"])
        else:
            self.title_input.clear()
            self.editor.clear()
            self.preview.clear()

    def show_all_notes(self):
        self.current_filter_tag = None
        self.current_filter_folder = None
        self.active_folder = NOTES_DIR
        self.current_folder_lbl.setText(f"📂 ~/{NOTES_DIR.name}")
        self.tag_list.clearSelection()
        self.vault_tree.clearSelection()
        self.filter_notes()
        self.set_view_mode("split")

    def on_tag_selected(self, item):
        self.current_filter_tag = item.data(Qt.ItemDataRole.UserRole)
        self.current_filter_folder = None
        self.filter_notes()

    def on_note_selected(self, item):
        path_str = item.data(Qt.ItemDataRole.UserRole)
        if path_str:
            self.load_note_file(Path(path_str))
            if self.right_stack.currentIndex() == 1:
                self.set_view_mode("split")

    def on_graph_node_selected(self, path_str):
        p = Path(path_str)
        if p.exists():
            self.load_note_file(p)
            self.set_view_mode("split")

    def load_note_file(self, path, line_number=None):
        if not path.exists():
            return
        self.current_file = path
        self.active_folder = path.parent
        try:
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()
        except Exception:
            content = ""

        # Set title input
        self.title_input.blockSignals(True)
        title = path.stem.replace("_", " ")
        lines = content.strip().splitlines()
        if lines and lines[0].startswith("# "):
            title = lines[0][2:].strip()
        self.title_input.setText(title)
        self.title_input.blockSignals(False)

        # Update path badge
        try:
            rel = path.parent.relative_to(NOTES_DIR)
            badge_text = str(rel) if str(rel) != "." else "vault root"
        except Exception:
            badge_text = "root"
        self.path_badge.setText(f"📁 {badge_text}")

        # Set editor content
        self.editor.blockSignals(True)
        self.editor.setPlainText(content)
        self.editor.blockSignals(False)

        if line_number and line_number > 0:
            cursor = self.editor.textCursor()
            cursor.movePosition(QTextCursor.MoveOperation.Start)
            for _ in range(line_number - 1):
                cursor.movePosition(QTextCursor.MoveOperation.Down)
            cursor.movePosition(QTextCursor.MoveOperation.EndOfLine, QTextCursor.MoveMode.KeepAnchor)
            self.editor.setTextCursor(cursor)
            self.editor.ensureCursorVisible()

        self.update_preview()
        self.update_stats()
        self.lbl_save_status.setText("● Saved")
        self.lbl_save_status.setStyleSheet(f"color: {ACCENT_EMERALD}; font-weight: bold;")

    def on_editor_text_changed(self):
        self.lbl_save_status.setText("○ Editing...")
        self.lbl_save_status.setStyleSheet(f"color: {ACCENT_AMBER};")
        self.update_preview()
        self.update_stats()
        self.auto_save_timer.start(400)

    def on_title_changed(self, new_title):
        if not self.current_file:
            return
        clean_name = re.sub(r'[^a-zA-Z0-9_\- ]', '', new_title).strip().replace(" ", "_")
        if clean_name and clean_name != self.current_file.stem:
            new_path = self.current_file.parent / f"{clean_name}.md"
            if not new_path.exists():
                self.current_file.rename(new_path)
                self.current_file = new_path
                self.auto_save_timer.start(400)

    def update_preview(self):
        text = self.editor.toPlainText()
        html = parse_markdown_to_html(text)
        self.preview.setHtml(html)

    def update_stats(self):
        text = self.editor.toPlainText()
        words = len(text.split()) if text.strip() else 0
        chars = len(text)
        read_min = max(1, words // 200) if words > 100 else 1
        self.lbl_stats.setText(f"{words} words  |  {chars} chars  |  {read_min} min read")

    def save_current_note(self):
        if not self.current_file:
            return
        text = self.editor.toPlainText()
        try:
            with open(self.current_file, "w", encoding="utf-8") as f:
                f.write(text)
            self.lbl_save_status.setText("● Saved")
            self.lbl_save_status.setStyleSheet(f"color: {ACCENT_EMERALD}; font-weight: bold;")
        except Exception as e:
            self.lbl_save_status.setText(f"Save error: {e}")
            self.lbl_save_status.setStyleSheet(f"color: {ACCENT_ROSE};")

    def create_new_note(self):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"Note_{timestamp}.md"
        target_dir = self.active_folder if self.active_folder.exists() else NOTES_DIR
        p = target_dir / filename
        initial_content = f"# New Note\n\n- Write your thoughts here\n- Connects via [[WikiLinks]]\n\n#ideas\n"
        with open(p, "w", encoding="utf-8") as f:
            f.write(initial_content)
        self.reload_vault(select_filepath=p)
        self.set_view_mode("split")
        self.title_input.setFocus()
        self.title_input.selectAll()

    def open_daily_note(self):
        """Open or create today's daily log (Daily/YYYY-MM-DD.md)."""
        daily_dir = NOTES_DIR / "Daily"
        daily_dir.mkdir(parents=True, exist_ok=True)
        today_str = datetime.now().strftime("%Y-%m-%d")
        daily_path = daily_dir / f"{today_str}.md"

        if not daily_path.exists():
            template = (
                f"# Daily Log — {today_str}\n\n"
                f"> Daily focus, goals, and scratchpad for MiloOS.\n\n"
                f"## Priorities\n"
                f"- [ ] Priority item 1\n"
                f"- [ ] Priority item 2\n\n"
                f"## Notes & Thoughts\n\n"
                f"- Log your notes here\n\n"
                f"#daily #journal #focus\n"
            )
            with open(daily_path, "w", encoding="utf-8") as f:
                f.write(template)

        self.reload_vault(select_filepath=daily_path)
        self.set_view_mode("split")

    def create_new_folder(self, parent_dir=None):
        base_dir = parent_dir or self.active_folder or NOTES_DIR
        name, ok = QInputDialog.getText(self, "New Folder", f"Create folder inside '{base_dir.name}':")
        if ok and name.strip():
            clean = re.sub(r'[^a-zA-Z0-9_\- ]', '', name.strip()).replace(" ", "_")
            new_f = base_dir / clean
            new_f.mkdir(parents=True, exist_ok=True)
            self.active_folder = new_f
            self.reload_vault()

    def rename_folder(self, folder_path):
        name, ok = QInputDialog.getText(self, "Rename Folder", "Enter new name:", text=folder_path.name)
        if ok and name.strip() and name.strip() != folder_path.name:
            clean = re.sub(r'[^a-zA-Z0-9_\- ]', '', name.strip()).replace(" ", "_")
            dest = folder_path.parent / clean
            if not dest.exists():
                folder_path.rename(dest)
                self.reload_vault()

    def delete_folder(self, folder_path):
        reply = QMessageBox.question(
            self, "Delete Folder",
            f"Are you sure you want to delete folder '{folder_path.name}' and all its notes?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            import shutil
            shutil.rmtree(folder_path, ignore_errors=True)
            self.active_folder = NOTES_DIR
            self.reload_vault()

    def delete_current_note(self):
        if not self.current_file or not self.current_file.exists():
            return
        reply = QMessageBox.question(
            self, "Delete Note",
            f"Are you sure you want to delete '{self.current_file.name}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.current_file.unlink()
            self.current_file = None
            self.reload_vault()

    def on_preview_link_clicked(self, url: QUrl):
        s = url.toString()
        if s.startswith("http://") or s.startswith("https://"):
            try:
                subprocess.Popen(["xdg-open", s])
            except Exception:
                pass
            return

        if s.startswith("toggle:"):
            target_text = urllib.parse.unquote(s[7:])
            raw = self.editor.toPlainText()
            patt_unchecked = f"- [ ] {target_text}"
            patt_checked = f"- [x] {target_text}"
            if patt_unchecked in raw:
                raw = raw.replace(patt_unchecked, patt_checked, 1)
            elif patt_checked in raw:
                raw = raw.replace(patt_checked, patt_unchecked, 1)
            self.editor.setPlainText(raw)
            return

        if s.startswith("wikilink:"):
            target = urllib.parse.unquote(s[9:]).strip()
            target_clean = target.replace(" ", "_")

            # Recursive lookup across any subfolder in vault
            found = None
            for p in NOTES_DIR.glob("**/*.md"):
                if p.stem.lower() == target.lower() or p.stem.lower() == target_clean.lower():
                    found = p
                    break

            if not found:
                # Create note in active folder
                target_dir = self.active_folder if self.active_folder.exists() else NOTES_DIR
                found = target_dir / f"{target_clean}.md"
                with open(found, "w", encoding="utf-8") as f:
                    f.write(f"# {target}\n\n> Auto-created via [[{target}]] WikiLink.\n\n")
                self.reload_vault(select_filepath=found)
            else:
                self.load_note_file(found)
            return

    def set_view_mode(self, mode):
        self.view_mode = mode
        if mode == "graph":
            self.right_stack.setCurrentIndex(1)
            self.graph_view.build_graph(self.all_notes, self.current_file)
            return

        self.right_stack.setCurrentIndex(0)
        if mode == "split":
            self.editor.show()
            self.preview.show()
            self.editor_preview_splitter.setSizes([355, 355])
        elif mode == "editor":
            self.editor.show()
            self.preview.hide()
        elif mode == "preview":
            self.editor.hide()
            self.preview.show()

    def trigger_milo_eyes_snap(self):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        target_img = ASSETS_DIR / f"snap_{timestamp}.png"

        slurp_cmd = ["slurp", "-b", "00000066", "-c", "00f5ffee", "-s", "00f5ff22", "-w", "2"]
        try:
            res = subprocess.run(slurp_cmd, capture_output=True, text=True)
            sel = res.stdout.strip()
            if not sel:
                return
            subprocess.run(["grim", "-g", sel, str(target_img)], check=True)
            
            # Use relative path from current note to image
            try:
                rel_path = os.path.relpath(target_img, self.current_file.parent if self.current_file else NOTES_DIR)
            except Exception:
                rel_path = f"assets/{target_img.name}"

            embed_md = f"\n\n![Screen Snapshot]({rel_path})\n\n"
            
            cursor = self.editor.textCursor()
            cursor.insertText(embed_md)
            self.save_current_note()
        except Exception as e:
            QMessageBox.warning(self, "Milo Eyes Snap", f"Could not capture screen: {e}")

    def show_export_menu(self):
        text = self.editor.toPlainText()
        if not text.strip():
            QMessageBox.information(self, "Export", "Note is empty.")
            return

        menu = QMenu(self)
        act_html_clip = menu.addAction("📋 Copy Formatted HTML to Clipboard")
        act_md_clip = menu.addAction("📄 Copy Raw Markdown to Clipboard")
        menu.addSeparator()
        act_save_html = menu.addAction("🌐 Export as Standalone HTML File...")
        
        chosen = menu.exec(self.btn_export.mapToGlobal(QPointF(0, self.btn_export.height()).toPoint()))
        if chosen == act_html_clip:
            html = parse_markdown_to_html(text)
            QApplication.clipboard().setText(html)
            self.lbl_save_status.setText("● Copied HTML")
            self.lbl_save_status.setStyleSheet(f"color: {ACCENT_CYAN};")
        elif chosen == act_md_clip:
            QApplication.clipboard().setText(text)
            self.lbl_save_status.setText("● Copied Markdown")
            self.lbl_save_status.setStyleSheet(f"color: {ACCENT_CYAN};")
        elif chosen == act_save_html:
            default_name = f"{self.current_file.stem}.html" if self.current_file else "Note.html"
            save_path, _ = QFileDialog.getSaveFileName(self, "Export HTML", str(Path.home() / "Downloads" / default_name), "HTML Files (*.html)")
            if save_path:
                html = parse_markdown_to_html(text)
                title = self.title_input.text() or "Milo Note"
                doc = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<title>{title}</title>
<style>
body {{ background: #080914; color: #f8fafc; font-family: 'Inter', -apple-system, sans-serif; max-width: 800px; margin: 40px auto; padding: 0 20px; line-height: 1.6; }}
h1, h2, h3 {{ font-family: 'JetBrains Mono', monospace; }}
table {{ border-collapse: collapse; width: 100%; }}
th, td {{ border: 1px solid #1e293b; padding: 8px 12px; }}
th {{ background: #0c1020; color: #00f5ff; }}
code {{ font-family: 'JetBrains Mono', monospace; }}
</style>
</head>
<body>
{html}
</body>
</html>"""
                with open(save_path, "w", encoding="utf-8") as f:
                    f.write(doc)
                self.lbl_save_status.setText(f"● Exported: {Path(save_path).name}")
                self.lbl_save_status.setStyleSheet(f"color: {ACCENT_EMERALD};")

    def trigger_ai_assist(self):
        text = self.editor.toPlainText().strip()
        if not text:
            QMessageBox.information(self, "AI Assist", "Note is empty. Write some text first.")
            return

        api_key = os.environ.get("GEMINI_API_KEY")
        if not api_key:
            for env_path in [
                Path.home() / ".config" / "milo" / "keys.env",
                Path.home() / ".config" / "milo" / "eyes.env",
                Path.home() / "Projects" / "milo-os" / "config" / "keys.env",
            ]:
                if env_path.exists():
                    try:
                        with open(env_path) as f:
                            for l in f:
                                l_str = l.strip()
                                if l_str.startswith("GEMINI_API_KEY="):
                                    api_key = l_str.split("=", 1)[1].strip().strip('"').strip("'")
                                    break
                    except Exception:
                        pass
                if api_key:
                    break

        if not api_key:
            QMessageBox.warning(self, "AI Assist", "No GEMINI_API_KEY found in ~/.config/milo/keys.env.")
            return

        # Prompt selection menu
        menu = QMenu(self)
        act_summary = menu.addAction("📋 Executive Summary & Checklist")
        act_polish = menu.addAction("✍ Polish Writing & Fix Grammar")
        act_brainstorm = menu.addAction("💡 Brainstorm Next Ideas & Gaps")
        act_action_items = menu.addAction("☑ Convert into Action Checklist")

        chosen = menu.exec(self.btn_ai.mapToGlobal(QPointF(0, self.btn_ai.height()).toPoint()))
        if not chosen:
            return

        if chosen == act_summary:
            instruction = "Analyze this markdown note and generate an executive summary callout block followed by actionable checklist items (- [ ] Task). Return ONLY clean markdown without preamble:"
            section_title = "## ✨ Executive Summary & Tasks"
        elif chosen == act_polish:
            instruction = "Carefully polish and improve the writing, flow, and grammar of this text while preserving all markdown tags, code blocks, and meaning. Return ONLY the polished markdown:"
            section_title = "## ✍ Polished Version"
        elif chosen == act_brainstorm:
            instruction = "Brainstorm creative next ideas, expansion opportunities, and critical questions based on this note. Return formatted markdown with bullet points and bold highlights:"
            section_title = "## 💡 Brainstorm & Next Ideas"
        else:
            instruction = "Extract all actionable tasks, to-dos, and responsibilities from this note into a clean interactive markdown checklist (- [ ] Task):"
            section_title = "## ☑ Action Checklist"

        self.lbl_save_status.setText("● AI Thinking...")
        self.lbl_save_status.setStyleSheet(f"color: {ACCENT_AMBER};")
        QApplication.processEvents()

        prompt = f"{instruction}\n\n{text}"
        payload = {"contents": [{"parts": [{"text": prompt}]}]}

        # Try models in order of capability and speed
        models_to_try = ["gemini-2.5-flash", "gemini-2.0-flash", "gemini-1.5-flash"]
        ai_text = None
        last_err = None

        for model in models_to_try:
            try:
                url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
                req = urllib.request.Request(url, data=json.dumps(payload).encode("utf-8"), headers={"Content-Type": "application/json"}, method="POST")
                with urllib.request.urlopen(req, timeout=18) as r:
                    res = json.loads(r.read())
                    ai_text = res["candidates"][0]["content"]["parts"][0]["text"].strip()
                    break
            except Exception as e:
                last_err = e

        if ai_text:
            updated = text + f"\n\n---\n{section_title}\n\n{ai_text}\n"
            self.editor.setPlainText(updated)
            self.save_current_note()
            self.lbl_save_status.setText("● AI Completed")
            self.lbl_save_status.setStyleSheet(f"color: {ACCENT_EMERALD}; font-weight: bold;")
        else:
            QMessageBox.warning(self, "AI Assist", f"AI Assist error: {last_err}")
            self.lbl_save_status.setText("● Saved")
            self.lbl_save_status.setStyleSheet(f"color: {ACCENT_EMERALD};")


def main():
    os.environ.setdefault("QT_QPA_PLATFORM", "wayland")
    app = QApplication(sys.argv)
    app.setApplicationName("milo-notes")
    app.setDesktopFileName("milo-notes")

    win = MiloNotesNativeWindow()

    # Handle file path and optional line number from arguments
    target_path = None
    target_line = None
    if len(sys.argv) > 1:
        arg = sys.argv[1]
        if ":" in arg:
            parts = arg.split(":")
            target_path = Path(parts[0]).expanduser().resolve()
            try:
                target_line = int(parts[1])
            except ValueError:
                pass
        else:
            target_path = Path(arg).expanduser().resolve()
            if len(sys.argv) > 2 and sys.argv[2] in ["--line", "-l"] and len(sys.argv) > 3:
                try:
                    target_line = int(sys.argv[3])
                except ValueError:
                    pass

    if target_path and target_path.exists() and target_path.is_file():
        win.load_note_file(target_path, target_line)

    win.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
