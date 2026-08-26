from __future__ import annotations

import getpass
import html
import os
import platform
import shutil
from datetime import datetime
from typing import Callable

import psutil
from PySide6.QtCore import QObject, QThread, QTimer, Qt, Signal, Slot
from PySide6.QtGui import QFont, QFontDatabase
from PySide6.QtWidgets import (
    QApplication,
    QFrame,
    QGraphicsDropShadowEffect,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QProgressBar,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QStackedWidget,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from jarvis.config import settings
from jarvis.core import JarvisAssistant
from jarvis.memory import list_facts


COLORS = {
    "bg": "#070c11",
    "sidebar": "#0a1118",
    "panel": "#0d141c",
    "panel_alt": "#111a24",
    "panel_hover": "#17232e",
    "border": "#22303c",
    "border_soft": "#17232d",
    "text": "#e8eef3",
    "muted": "#8ea0ad",
    "muted_2": "#647581",
    "green": "#72f25b",
    "green_soft": "#173c22",
    "cyan": "#62c6ff",
    "cyan_soft": "#112c3a",
    "warning": "#f3b74a",
    "danger": "#ff6b6b",
}


def _fmt_gib(value: float) -> str:
    return f"{value / 1024**3:.1f} GiB"


def _safe_username() -> str:
    try:
        return getpass.getuser()
    except Exception:
        return "usuário"


def _shell_name() -> str:
    shell = os.getenv("SHELL", "")
    return shell.rsplit("/", 1)[-1] or "desconhecido"


def _desktop_name() -> str:
    desktop = (
        os.getenv("XDG_CURRENT_DESKTOP")
        or os.getenv("DESKTOP_SESSION")
        or os.getenv("XDG_SESSION_DESKTOP")
        or "desconhecido"
    )
    session = os.getenv("XDG_SESSION_TYPE", "")
    return f"{desktop} ({session})" if session else desktop


def _format_uptime() -> str:
    seconds = max(0, int(datetime.now().timestamp() - psutil.boot_time()))
    days, remainder = divmod(seconds, 86400)
    hours, remainder = divmod(remainder, 3600)
    minutes = remainder // 60
    if days:
        return f"{days}d {hours}h {minutes}min"
    if hours:
        return f"{hours}h {minutes}min"
    return f"{minutes}min"


def system_snapshot() -> dict[str, str | int | float]:
    vm = psutil.virtual_memory()
    disk = psutil.disk_usage("/")
    cpu_percent = psutil.cpu_percent(interval=None)
    return {
        "os": f"{platform.system()} {platform.release()}",
        "uptime": _format_uptime(),
        "user": _safe_username(),
        "hostname": platform.node() or "localhost",
        "shell": _shell_name(),
        "desktop": _desktop_name(),
        "cpu": f"{cpu_percent:.0f}%",
        "cpu_percent": cpu_percent,
        "memory": f"{_fmt_gib(vm.used)} / {_fmt_gib(vm.total)} ({vm.percent:.0f}%)",
        "memory_percent": vm.percent,
        "disk": f"{_fmt_gib(disk.used)} / {_fmt_gib(disk.total)} ({disk.percent:.0f}%)",
        "disk_percent": disk.percent,
    }


def _font_family(preferred: list[str], fallback: str) -> str:
    families = set(QFontDatabase.families())
    return next((name for name in preferred if name in families), fallback)


def _shadow(widget: QWidget, blur: int = 28, y: int = 8) -> None:
    effect = QGraphicsDropShadowEffect(widget)
    effect.setBlurRadius(blur)
    effect.setOffset(0, y)
    effect.setColor(Qt.GlobalColor.black)
    widget.setGraphicsEffect(effect)


class Card(QFrame):
    def __init__(self, parent: QWidget | None = None, *, name: str = "card") -> None:
        super().__init__(parent)
        self.setObjectName(name)
        _shadow(self, 24, 7)


class AskWorker(QObject):
    finished = Signal(str)
    failed = Signal(str)

    def __init__(self, assistant: JarvisAssistant, text: str) -> None:
        super().__init__()
        self.assistant = assistant
        self.text = text

    @Slot()
    def run(self) -> None:
        try:
            self.finished.emit(self.assistant.ask(self.text))
        except Exception as exc:  # noqa: BLE001 - fronteira deliberada da UI
            self.failed.emit(str(exc))


class JarvisWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle(f"{settings.assistant_name} — Assistente Inteligente para Linux")
        self.resize(1480, 900)
        self.setMinimumSize(1120, 720)

        self.ui_font = _font_family(["Inter", "Noto Sans", "Ubuntu"], "DejaVu Sans")
        self.mono_font = _font_family(["JetBrains Mono", "Fira Code", "Cascadia Code"], "DejaVu Sans Mono")

        self.assistant: JarvisAssistant | None = None
        self.busy = False
        self.nav_buttons: dict[str, QPushButton] = {}
        self.page_index: dict[str, int] = {}
        self.system_value_labels: dict[str, QLabel] = {}
        self.system_progress: dict[str, QProgressBar] = {}
        self.system_detail_labels: dict[str, QLabel] = {}
        self.tool_status_labels: dict[str, QLabel] = {}

        self._apply_theme()
        self._build_shell()
        self._build_pages()
        self._select_page("Chat")
        self._refresh_status()

        self.timer = QTimer(self)
        self.timer.timeout.connect(self._refresh_status)
        self.timer.start(2500)

    def _apply_theme(self) -> None:
        self.setStyleSheet(
            f"""
            QMainWindow, QWidget#root {{
                background: {COLORS['bg']};
                color: {COLORS['text']};
            }}
            QLabel {{
                color: {COLORS['text']};
                background: transparent;
            }}
            QFrame#sidebar, QFrame#inspector {{
                background: {COLORS['sidebar']};
            }}
            QFrame#sidebar {{
                border-right: 1px solid {COLORS['border_soft']};
            }}
            QFrame#inspector {{
                border-left: 1px solid {COLORS['border_soft']};
            }}
            QFrame#card, QFrame#terminalCard, QFrame#inputCard, QFrame#metricCard {{
                background: {COLORS['panel_alt']};
                border: 1px solid {COLORS['border']};
                border-radius: 13px;
            }}
            QFrame#terminalCard {{
                background: #080f16;
            }}
            QFrame#inputCard {{
                background: #0a1219;
            }}
            QPushButton[nav="true"] {{
                background: transparent;
                border: none;
                border-radius: 10px;
                color: #a9b8c2;
                text-align: left;
                padding: 12px 14px;
                font-size: 13px;
            }}
            QPushButton[nav="true"]:hover {{
                background: {COLORS['panel_hover']};
                color: {COLORS['text']};
            }}
            QPushButton[nav="true"]:checked {{
                background: #192530;
                color: #f4f8fb;
                border: 1px solid #253543;
            }}
            QPushButton#sendButton {{
                background: {COLORS['green']};
                color: #07100a;
                border: none;
                border-radius: 10px;
                padding: 10px 16px;
                font-weight: 700;
            }}
            QPushButton#sendButton:hover {{ background: #8bff73; }}
            QPushButton#sendButton:disabled {{
                background: #25312b;
                color: #6f8378;
            }}
            QPushButton#ghostButton {{
                background: #121c25;
                color: {COLORS['muted']};
                border: 1px solid {COLORS['border']};
                border-radius: 9px;
                padding: 9px 12px;
            }}
            QPushButton#ghostButton:hover {{
                color: {COLORS['text']};
                border-color: #324756;
            }}
            QLineEdit#promptInput {{
                background: transparent;
                color: {COLORS['text']};
                border: none;
                padding: 12px 8px;
                selection-background-color: #25583a;
                font-size: 13px;
            }}
            QTextEdit#chatTranscript {{
                background: transparent;
                border: none;
                color: {COLORS['text']};
                selection-background-color: #245b39;
                padding: 10px;
            }}
            QProgressBar {{
                background: #0b1218;
                border: 1px solid #1b2933;
                border-radius: 4px;
                height: 7px;
                text-align: center;
                color: transparent;
            }}
            QProgressBar::chunk {{
                background: {COLORS['green']};
                border-radius: 3px;
            }}
            QScrollArea {{ border: none; background: transparent; }}
            QScrollBar:vertical {{
                background: transparent;
                width: 8px;
                margin: 3px 1px;
            }}
            QScrollBar::handle:vertical {{
                background: #253540;
                border-radius: 4px;
                min-height: 32px;
            }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0px; }}
            """
        )

    def _build_shell(self) -> None:
        root = QWidget()
        root.setObjectName("root")
        self.setCentralWidget(root)
        shell = QHBoxLayout(root)
        shell.setContentsMargins(0, 0, 0, 0)
        shell.setSpacing(0)

        self.sidebar = QFrame()
        self.sidebar.setObjectName("sidebar")
        self.sidebar.setFixedWidth(220)
        shell.addWidget(self.sidebar)

        self.stack = QStackedWidget()
        self.stack.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        shell.addWidget(self.stack, 1)

        self.inspector = QFrame()
        self.inspector.setObjectName("inspector")
        self.inspector.setFixedWidth(310)
        shell.addWidget(self.inspector)

        self._build_sidebar()
        self._build_inspector()

    def _build_sidebar(self) -> None:
        layout = QVBoxLayout(self.sidebar)
        layout.setContentsMargins(14, 18, 14, 18)
        layout.setSpacing(6)

        brand = QHBoxLayout()
        brand.setSpacing(10)
        icon = QLabel(">_")
        icon.setStyleSheet(
            f"color:{COLORS['cyan']}; font-family:'{self.mono_font}'; font-size:26px; font-weight:800;"
        )
        brand.addWidget(icon)

        brand_text = QVBoxLayout()
        brand_text.setSpacing(0)
        title = QLabel("J.A.R.V.I.S.")
        title.setStyleSheet(
            f"color:{COLORS['green']}; font-family:'{self.ui_font}'; font-size:16px; font-weight:800;"
        )
        subtitle = QLabel("LINUX ASSISTANT")
        subtitle.setStyleSheet(
            f"color:{COLORS['muted_2']}; font-family:'{self.ui_font}'; font-size:9px; font-weight:700; letter-spacing:1px;"
        )
        brand_text.addWidget(title)
        brand_text.addWidget(subtitle)
        brand.addLayout(brand_text)
        brand.addStretch()
        layout.addLayout(brand)
        layout.addSpacing(18)

        nav_items = [
            ("Chat", "●"),
            ("Ferramentas", "⌘"),
            ("Automação", "◫"),
            ("Memória", "◉"),
            ("Sistema", "▣"),
            ("Configurações", "⚙"),
        ]
        for name, glyph in nav_items:
            button = QPushButton(f"{glyph}    {name}")
            button.setProperty("nav", True)
            button.setCheckable(True)
            button.setCursor(Qt.CursorShape.PointingHandCursor)
            button.clicked.connect(lambda _checked=False, page=name: self._select_page(page))
            layout.addWidget(button)
            self.nav_buttons[name] = button

        layout.addStretch(1)

        status_wrap = QFrame()
        status_layout = QHBoxLayout(status_wrap)
        status_layout.setContentsMargins(8, 10, 8, 4)
        dot = QLabel("●")
        dot.setStyleSheet(f"color:{COLORS['green']}; font-size:12px;")
        self.local_status = QLabel("Local: ativo")
        self.local_status.setStyleSheet(
            f"color:{COLORS['green']}; font-family:'{self.ui_font}'; font-size:11px; font-weight:700;"
        )
        status_layout.addWidget(dot)
        status_layout.addWidget(self.local_status)
        status_layout.addStretch()
        layout.addWidget(status_wrap)

    def _build_inspector(self) -> None:
        scroll = QScrollArea(self.inspector)
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        host = QWidget()
        v = QVBoxLayout(host)
        v.setContentsMargins(14, 18, 14, 22)
        v.setSpacing(10)

        v.addWidget(self._section_label("INTERAÇÃO"))
        interaction = Card()
        iv = QVBoxLayout(interaction)
        iv.setContentsMargins(14, 11, 14, 11)
        iv.setSpacing(2)
        iv.addLayout(self._status_row("🎙  Voz", "não portada", COLORS["warning"]))
        iv.addLayout(self._status_row("▣  Texto", "ativo", COLORS["green"]))
        v.addWidget(interaction)

        v.addSpacing(5)
        v.addWidget(self._section_label("FERRAMENTAS LOCAIS"))
        tools = Card()
        tv = QVBoxLayout(tools)
        tv.setContentsMargins(14, 9, 14, 9)
        tv.setSpacing(1)
        tool_defs = [
            ("Terminal / shell", "shell"),
            ("Aplicativos XDG", "apps"),
            ("Informações do sistema", "system"),
            ("Memória local", "memory"),
        ]
        for label, key in tool_defs:
            row = QHBoxLayout()
            left = QLabel(label)
            left.setStyleSheet(f"color:{COLORS['text']}; font-size:11px;")
            status = QLabel("Pronto")
            status.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            status.setStyleSheet(f"color:{COLORS['green']}; font-size:10px; font-weight:700;")
            row.addWidget(left)
            row.addStretch()
            row.addWidget(status)
            tv.addLayout(row)
            tv.addSpacing(7)
            self.tool_status_labels[key] = status
        v.addWidget(tools)

        v.addSpacing(5)
        v.addWidget(self._section_label("STATUS DO SISTEMA"))
        system = Card()
        sv = QVBoxLayout(system)
        sv.setContentsMargins(14, 12, 14, 12)
        sv.setSpacing(12)
        for title, key in [("CPU", "cpu"), ("Memória", "memory"), ("Disco /", "disk")]:
            top = QHBoxLayout()
            label = QLabel(title)
            label.setStyleSheet(f"color:{COLORS['muted']}; font-size:10px;")
            value = QLabel("—")
            value.setStyleSheet(
                f"color:{COLORS['green']}; font-family:'{self.mono_font}'; font-size:10px; font-weight:700;"
            )
            value.setAlignment(Qt.AlignmentFlag.AlignRight)
            top.addWidget(label)
            top.addStretch()
            top.addWidget(value)
            bar = QProgressBar()
            bar.setRange(0, 100)
            bar.setTextVisible(False)
            sv.addLayout(top)
            sv.addWidget(bar)
            self.system_value_labels[key] = value
            self.system_progress[key] = bar
        v.addWidget(system)

        v.addSpacing(5)
        v.addWidget(self._section_label("MEMÓRIA"))
        memory = Card()
        mv = QVBoxLayout(memory)
        mv.setContentsMargins(14, 12, 14, 12)
        self.memory_summary = QLabel("Carregando…")
        self.memory_summary.setWordWrap(True)
        self.memory_summary.setStyleSheet(f"color:{COLORS['muted']}; font-size:11px; line-height:1.3;")
        mv.addWidget(self.memory_summary)
        manage_memory = QPushButton("Gerenciar memória")
        manage_memory.setObjectName("ghostButton")
        manage_memory.clicked.connect(lambda: self._select_page("Memória"))
        mv.addWidget(manage_memory)
        v.addWidget(memory)

        v.addSpacing(5)
        v.addWidget(self._section_label("AUTOMAÇÃO"))
        automation = Card()
        av = QVBoxLayout(automation)
        av.setContentsMargins(14, 12, 14, 12)
        caption = QLabel("Próximas tarefas")
        caption.setStyleSheet(f"color:{COLORS['muted']}; font-size:10px; font-weight:700;")
        av.addWidget(caption)
        placeholder = QLabel("Nenhuma automação pública configurada")
        placeholder.setWordWrap(True)
        placeholder.setStyleSheet(f"color:{COLORS['text']}; font-size:11px;")
        av.addWidget(placeholder)
        open_auto = QPushButton("Ver automação")
        open_auto.setObjectName("ghostButton")
        open_auto.clicked.connect(lambda: self._select_page("Automação"))
        av.addWidget(open_auto)
        v.addWidget(automation)

        v.addStretch(1)
        scroll.setWidget(host)

        inspector_layout = QVBoxLayout(self.inspector)
        inspector_layout.setContentsMargins(0, 0, 0, 0)
        inspector_layout.addWidget(scroll)

    def _section_label(self, text: str) -> QLabel:
        label = QLabel(text)
        label.setStyleSheet(
            f"color:{COLORS['muted_2']}; font-family:'{self.ui_font}'; font-size:9px; font-weight:800; letter-spacing:1px;"
        )
        return label

    def _status_row(self, left_text: str, right_text: str, color: str) -> QHBoxLayout:
        row = QHBoxLayout()
        left = QLabel(left_text)
        left.setStyleSheet(f"color:{COLORS['text']}; font-size:11px;")
        right = QLabel(right_text)
        right.setStyleSheet(f"color:{color}; font-size:10px; font-weight:700;")
        row.addWidget(left)
        row.addStretch()
        row.addWidget(right)
        return row

    def _build_pages(self) -> None:
        builders: list[tuple[str, Callable[[], QWidget]]] = [
            ("Chat", self._chat_page),
            ("Ferramentas", self._tools_page),
            ("Automação", self._automation_page),
            ("Memória", self._memory_page),
            ("Sistema", self._system_page),
            ("Configurações", self._settings_page),
        ]
        for name, builder in builders:
            self.page_index[name] = self.stack.addWidget(builder())

    def _page_host(self, title: str, subtitle: str) -> tuple[QWidget, QVBoxLayout]:
        host = QWidget()
        layout = QVBoxLayout(host)
        layout.setContentsMargins(26, 22, 26, 22)
        layout.setSpacing(14)

        head = QHBoxLayout()
        text = QVBoxLayout()
        text.setSpacing(2)
        title_label = QLabel(title)
        title_label.setStyleSheet(
            f"font-family:'{self.ui_font}'; font-size:21px; font-weight:800; color:{COLORS['text']};"
        )
        sub = QLabel(subtitle)
        sub.setStyleSheet(f"font-family:'{self.ui_font}'; font-size:11px; color:{COLORS['muted']};")
        text.addWidget(title_label)
        text.addWidget(sub)
        head.addLayout(text)
        head.addStretch()
        status = QLabel("●  LOCAL · ATIVO")
        status.setStyleSheet(
            f"background:{COLORS['green_soft']}; color:{COLORS['green']}; border:1px solid #255b31; border-radius:10px; padding:6px 10px; font-size:9px; font-weight:800;"
        )
        head.addWidget(status)
        layout.addLayout(head)
        return host, layout

    def _chat_page(self) -> QWidget:
        host, layout = self._page_host(
            "J.A.R.V.I.S.",
            "Assistente local para Linux · LLM + function calling + ferramentas locais",
        )

        terminal = Card(name="terminalCard")
        terminal_layout = QVBoxLayout(terminal)
        terminal_layout.setContentsMargins(16, 14, 16, 12)
        terminal_layout.setSpacing(6)

        terminal_head = QHBoxLayout()
        label = QLabel("J.A.R.V.I.S.")
        label.setStyleSheet(
            f"color:{COLORS['green']}; font-family:'{self.mono_font}'; font-size:12px; font-weight:800;"
        )
        self.clock_label = QLabel("")
        self.clock_label.setStyleSheet(f"color:{COLORS['muted_2']}; font-size:10px;")
        terminal_head.addWidget(label)
        terminal_head.addStretch()
        terminal_head.addWidget(self.clock_label)
        terminal_layout.addLayout(terminal_head)

        self.chat = QTextEdit()
        self.chat.setObjectName("chatTranscript")
        self.chat.setReadOnly(True)
        self.chat.setFont(QFont(self.mono_font, 10))
        terminal_layout.addWidget(self.chat, 1)

        layout.addWidget(terminal, 1)

        input_card = QFrame()
        input_card.setObjectName("inputCard")
        input_layout = QHBoxLayout(input_card)
        input_layout.setContentsMargins(10, 5, 7, 5)
        input_layout.setSpacing(6)
        prompt_symbol = QLabel("›")
        prompt_symbol.setStyleSheet(
            f"color:{COLORS['green']}; font-family:'{self.mono_font}'; font-size:22px; font-weight:800;"
        )
        self.prompt = QLineEdit()
        self.prompt.setObjectName("promptInput")
        self.prompt.setPlaceholderText("Mensagem para J.A.R.V.I.S…")
        self.prompt.returnPressed.connect(self._send_message)
        mic = QPushButton("🎙")
        mic.setObjectName("ghostButton")
        mic.setToolTip("Voz ainda não portada para a edição pública")
        mic.setEnabled(False)
        self.send_button = QPushButton("Enviar")
        self.send_button.setObjectName("sendButton")
        self.send_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.send_button.clicked.connect(self._send_message)
        input_layout.addWidget(prompt_symbol)
        input_layout.addWidget(self.prompt, 1)
        input_layout.addWidget(mic)
        input_layout.addWidget(self.send_button)
        layout.addWidget(input_card)

        self._seed_chat()
        return host

    def _seed_chat(self) -> None:
        snap = system_snapshot()
        self.chat.setHtml(
            f"""
            <div style="font-family:'{self.mono_font}'; font-size:10.5pt; color:{COLORS['text']}; line-height:1.45;">
              <span style="color:{COLORS['green']}; font-weight:700;">J.A.R.V.I.S. carregado e pronto.</span><br>
              <span style="color:{COLORS['text']};">Como posso ajudar você hoje?</span><br><br>
              <span style="color:{COLORS['muted']};">&gt; STATUS DO SISTEMA</span><br>
              <div style="margin-top:5px; margin-bottom:8px; padding:10px; background:#0c151d; border:1px solid #22303c; border-radius:8px;">
                <span style="color:{COLORS['green']};">SO:</span>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;{html.escape(str(snap['os']))}<br>
                <span style="color:{COLORS['green']};">Uptime:</span>&nbsp;&nbsp;&nbsp;{html.escape(str(snap['uptime']))}<br>
                <span style="color:{COLORS['green']};">Usuário:</span>&nbsp;&nbsp;{html.escape(str(snap['user']))}<br>
                <span style="color:{COLORS['green']};">Hostname:</span>&nbsp;{html.escape(str(snap['hostname']))}<br>
                <span style="color:{COLORS['green']};">Shell:</span>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;{html.escape(str(snap['shell']))}<br>
                <span style="color:{COLORS['green']};">Desktop:</span>&nbsp;&nbsp;&nbsp;{html.escape(str(snap['desktop']))}
              </div>
              <span style="color:{COLORS['muted']};">&gt; USO DE RECURSOS</span><br>
              <span style="color:{COLORS['green']};">CPU:</span>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;{html.escape(str(snap['cpu']))}<br>
              <span style="color:{COLORS['green']};">Memória:</span>&nbsp;{html.escape(str(snap['memory']))}<br>
              <span style="color:{COLORS['green']};">Disco:</span>&nbsp;&nbsp;&nbsp;{html.escape(str(snap['disk']))}<br><br>
              <span style="color:{COLORS['muted']};">Digite uma solicitação abaixo. Ações locais passam pelo dispatcher e pelas políticas da edição pública.</span>
            </div>
            """
        )
        self.chat.moveCursor(self.chat.textCursor().MoveOperation.End)

    def _tools_page(self) -> QWidget:
        host, layout = self._page_host(
            "Ferramentas",
            "Capacidades locais expostas ao modelo por function calling",
        )
        grid = QGridLayout()
        grid.setHorizontalSpacing(12)
        grid.setVerticalSpacing(12)
        items = [
            ("▣", "Informações do sistema", "CPU, RAM, disco e sistema operacional", "Ativo"),
            ("⌘", "Aplicativos XDG", "Descobre e abre aplicativos de forma portátil", "Ativo"),
            (">_", "Shell", "Execução opt-in com timeout e política de bloqueio", "Opt-in"),
            ("◉", "Memória local", "Persistência SQLite opcional e local", "Opt-in"),
        ]
        for i, (glyph, title, description, status) in enumerate(items):
            card = Card()
            cv = QVBoxLayout(card)
            cv.setContentsMargins(18, 17, 18, 17)
            icon = QLabel(glyph)
            icon.setStyleSheet(
                f"color:{COLORS['green']}; font-family:'{self.mono_font}'; font-size:24px; font-weight:800;"
            )
            t = QLabel(title)
            t.setStyleSheet(f"font-size:14px; font-weight:800; color:{COLORS['text']};")
            d = QLabel(description)
            d.setWordWrap(True)
            d.setStyleSheet(f"font-size:11px; color:{COLORS['muted']};")
            s = QLabel(status)
            status_color = COLORS["green"] if status == "Ativo" else COLORS["warning"]
            s.setStyleSheet(f"color:{status_color}; font-size:10px; font-weight:800;")
            cv.addWidget(icon)
            cv.addSpacing(4)
            cv.addWidget(t)
            cv.addWidget(d)
            cv.addSpacing(8)
            cv.addWidget(s)
            grid.addWidget(card, i // 2, i % 2)
        layout.addLayout(grid)
        layout.addStretch(1)
        return host

    def _automation_page(self) -> QWidget:
        host, layout = self._page_host(
            "Automação",
            "Área reservada para rotinas e tarefas locais controladas",
        )
        card = Card()
        cv = QVBoxLayout(card)
        cv.setContentsMargins(22, 22, 22, 22)
        icon = QLabel("◫")
        icon.setStyleSheet(f"font-size:32px; color:{COLORS['green']}; font-weight:800;")
        title = QLabel("Automação avançada ainda não foi portada")
        title.setStyleSheet(f"font-size:16px; font-weight:800; color:{COLORS['text']};")
        text = QLabel(
            "O protótipo privado possuía experimentos de automação mais amplos. Nesta edição pública, "
            "a interface preserva a área visual do mockup sem fingir que um agendador completo já existe."
        )
        text.setWordWrap(True)
        text.setStyleSheet(f"font-size:12px; color:{COLORS['muted']};")
        cv.addWidget(icon)
        cv.addWidget(title)
        cv.addWidget(text)
        layout.addWidget(card)
        layout.addStretch(1)
        return host

    def _memory_page(self) -> QWidget:
        host, layout = self._page_host(
            "Memória",
            "Fatos persistentes armazenados localmente quando o recurso está habilitado",
        )
        self.memory_page_card = Card()
        self.memory_page_layout = QVBoxLayout(self.memory_page_card)
        self.memory_page_layout.setContentsMargins(20, 18, 20, 18)
        layout.addWidget(self.memory_page_card)
        layout.addStretch(1)
        self._render_memory_page()
        return host

    def _render_memory_page(self) -> None:
        if not hasattr(self, "memory_page_layout"):
            return
        while self.memory_page_layout.count():
            item = self.memory_page_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()

        if not settings.memory_enabled:
            title = QLabel("Memória persistente desativada")
            title.setStyleSheet(f"font-size:15px; font-weight:800; color:{COLORS['warning']};")
            body = QLabel(
                "Ative JARVIS_MEMORY_ENABLED=true no arquivo .env para permitir persistência local. "
                "O recurso permanece desligado por padrão."
            )
            body.setWordWrap(True)
            body.setStyleSheet(f"color:{COLORS['muted']}; font-size:12px;")
            self.memory_page_layout.addWidget(title)
            self.memory_page_layout.addWidget(body)
            return

        facts = list_facts()
        title = QLabel(f"{len(facts)} fato(s) armazenado(s)")
        title.setStyleSheet(f"font-size:15px; font-weight:800; color:{COLORS['green']};")
        self.memory_page_layout.addWidget(title)
        if not facts:
            empty = QLabel("Nenhuma informação persistente disponível.")
            empty.setStyleSheet(f"color:{COLORS['muted']}; font-size:12px;")
            self.memory_page_layout.addWidget(empty)
            return
        for key, value in sorted(facts.items()):
            row = QFrame()
            row.setStyleSheet(
                f"background:#0c151d; border:1px solid {COLORS['border_soft']}; border-radius:9px;"
            )
            rv = QVBoxLayout(row)
            rv.setContentsMargins(12, 9, 12, 9)
            k = QLabel(str(key))
            k.setStyleSheet(f"color:{COLORS['green']}; font-size:10px; font-weight:800;")
            val = QLabel(str(value))
            val.setWordWrap(True)
            val.setStyleSheet(f"color:{COLORS['text']}; font-size:11px;")
            rv.addWidget(k)
            rv.addWidget(val)
            self.memory_page_layout.addWidget(row)

    def _system_page(self) -> QWidget:
        host, layout = self._page_host(
            "Sistema",
            "Visão local de hardware, sessão e uso de recursos",
        )
        top_grid = QGridLayout()
        top_grid.setHorizontalSpacing(12)
        top_grid.setVerticalSpacing(12)
        for i, (label, key) in enumerate(
            [("Sistema operacional", "os"), ("Uptime", "uptime"), ("Usuário", "user"), ("Hostname", "hostname"), ("Shell", "shell"), ("Desktop", "desktop")]
        ):
            card = Card(name="metricCard")
            cv = QVBoxLayout(card)
            cv.setContentsMargins(16, 13, 16, 13)
            l = QLabel(label.upper())
            l.setStyleSheet(f"color:{COLORS['muted_2']}; font-size:9px; font-weight:800;")
            value = QLabel("—")
            value.setWordWrap(True)
            value.setStyleSheet(
                f"color:{COLORS['text']}; font-family:'{self.mono_font}'; font-size:12px; font-weight:700;"
            )
            cv.addWidget(l)
            cv.addWidget(value)
            self.system_detail_labels[key] = value
            top_grid.addWidget(card, i // 3, i % 3)
        layout.addLayout(top_grid)

        resource = Card()
        rv = QVBoxLayout(resource)
        rv.setContentsMargins(18, 17, 18, 17)
        resource_title = QLabel("USO DE RECURSOS")
        resource_title.setStyleSheet(f"color:{COLORS['muted_2']}; font-size:9px; font-weight:800;")
        rv.addWidget(resource_title)
        self.system_page_resource: dict[str, tuple[QLabel, QProgressBar]] = {}
        for title, key in [("CPU", "cpu"), ("Memória", "memory"), ("Disco /", "disk")]:
            row = QHBoxLayout()
            l = QLabel(title)
            l.setStyleSheet(f"color:{COLORS['text']}; font-size:11px; font-weight:700;")
            value = QLabel("—")
            value.setStyleSheet(f"color:{COLORS['green']}; font-family:'{self.mono_font}'; font-size:10px;")
            row.addWidget(l)
            row.addStretch()
            row.addWidget(value)
            bar = QProgressBar()
            bar.setRange(0, 100)
            bar.setTextVisible(False)
            rv.addSpacing(6)
            rv.addLayout(row)
            rv.addWidget(bar)
            self.system_page_resource[key] = (value, bar)
        layout.addWidget(resource)
        layout.addStretch(1)
        return host

    def _settings_page(self) -> QWidget:
        host, layout = self._page_host(
            "Configurações",
            "Resumo das opções da edição pública — segredos nunca são exibidos",
        )
        card = Card()
        cv = QVBoxLayout(card)
        cv.setContentsMargins(20, 18, 20, 18)
        cv.setSpacing(12)
        rows = [
            ("Modelo", settings.model),
            ("Nome do assistente", settings.assistant_name),
            ("Memória persistente", "habilitada" if settings.memory_enabled else "desativada"),
            ("Shell genérico", "habilitado" if settings.allow_shell else "desativado"),
            ("Timeout do shell", f"{settings.shell_timeout}s"),
            ("Diretório de dados", str(settings.data_dir)),
            ("GEMINI_API_KEY", "configurada" if bool(settings.api_key) else "não configurada"),
        ]
        for label, value in rows:
            row = QHBoxLayout()
            l = QLabel(label)
            l.setStyleSheet(f"color:{COLORS['muted']}; font-size:11px;")
            val = QLabel(value)
            val.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
            val.setStyleSheet(
                f"color:{COLORS['text']}; font-family:'{self.mono_font}'; font-size:10px; font-weight:700;"
            )
            row.addWidget(l)
            row.addStretch()
            row.addWidget(val)
            cv.addLayout(row)
        layout.addWidget(card)
        layout.addStretch(1)
        return host

    def _select_page(self, page: str) -> None:
        index = self.page_index.get(page)
        if index is None:
            return
        self.stack.setCurrentIndex(index)
        for name, button in self.nav_buttons.items():
            button.setChecked(name == page)
        if page == "Memória":
            self._render_memory_page()
        if page == "Sistema":
            self._refresh_status()

    def _ensure_assistant(self) -> JarvisAssistant:
        if self.assistant is None:
            self.assistant = JarvisAssistant()
        return self.assistant

    @Slot()
    def _send_message(self) -> None:
        if self.busy:
            return
        text = self.prompt.text().strip()
        if not text:
            return

        self.prompt.clear()
        self._append_user(text)
        self.busy = True
        self.send_button.setEnabled(False)
        self.send_button.setText("Pensando…")
        self.prompt.setEnabled(False)

        try:
            assistant = self._ensure_assistant()
        except Exception as exc:  # noqa: BLE001
            self._append_error(str(exc))
            self._set_idle()
            return

        thread = QThread(self)
        worker = AskWorker(assistant, text)
        worker.moveToThread(thread)
        thread.started.connect(worker.run)
        worker.finished.connect(self._assistant_finished)
        worker.failed.connect(self._assistant_failed)
        worker.finished.connect(thread.quit)
        worker.failed.connect(thread.quit)
        worker.finished.connect(worker.deleteLater)
        worker.failed.connect(worker.deleteLater)
        thread.finished.connect(thread.deleteLater)
        self._active_thread = thread
        self._active_worker = worker
        thread.start()

    @Slot(str)
    def _assistant_finished(self, answer: str) -> None:
        self._append_assistant(answer)
        self._set_idle()

    @Slot(str)
    def _assistant_failed(self, error: str) -> None:
        self._append_error(error)
        self._set_idle()

    def _set_idle(self) -> None:
        self.busy = False
        self.send_button.setEnabled(True)
        self.send_button.setText("Enviar")
        self.prompt.setEnabled(True)
        self.prompt.setFocus()

    def _append_user(self, text: str) -> None:
        safe = html.escape(text).replace("\n", "<br>")
        self.chat.append(
            f"<div style='margin-top:12px;'><span style='color:{COLORS['cyan']}; font-weight:700;'>Você:</span><br>"
            f"<span style='color:{COLORS['text']};'>{safe}</span></div>"
        )
        self.chat.moveCursor(self.chat.textCursor().MoveOperation.End)

    def _append_assistant(self, text: str) -> None:
        safe = html.escape(text).replace("\n", "<br>")
        self.chat.append(
            f"<div style='margin-top:12px;'><span style='color:{COLORS['green']}; font-weight:700;'>J.A.R.V.I.S.:</span><br>"
            f"<span style='color:{COLORS['text']};'>{safe}</span></div>"
        )
        self.chat.moveCursor(self.chat.textCursor().MoveOperation.End)

    def _append_error(self, text: str) -> None:
        safe = html.escape(text).replace("\n", "<br>")
        self.chat.append(
            f"<div style='margin-top:12px;'><span style='color:{COLORS['danger']}; font-weight:700;'>Erro:</span><br>"
            f"<span style='color:{COLORS['muted']};'>{safe}</span></div>"
        )
        self.chat.moveCursor(self.chat.textCursor().MoveOperation.End)

    def _refresh_status(self) -> None:
        snap = system_snapshot()
        self.clock_label.setText(datetime.now().strftime("%a, %d %b  %H:%M"))

        values = {
            "cpu": (str(snap["cpu"]), int(float(snap["cpu_percent"]))),
            "memory": (str(snap["memory"]), int(float(snap["memory_percent"]))),
            "disk": (str(snap["disk"]), int(float(snap["disk_percent"]))),
        }
        for key, (text, percent) in values.items():
            if key in self.system_value_labels:
                self.system_value_labels[key].setText(text)
            if key in self.system_progress:
                self.system_progress[key].setValue(percent)
            if hasattr(self, "system_page_resource") and key in self.system_page_resource:
                label, bar = self.system_page_resource[key]
                label.setText(text)
                bar.setValue(percent)

        for key in ("os", "uptime", "user", "hostname", "shell", "desktop"):
            if key in self.system_detail_labels:
                self.system_detail_labels[key].setText(str(snap[key]))

        self.tool_status_labels["system"].setText("Pronto")
        self.tool_status_labels["system"].setStyleSheet(
            f"color:{COLORS['green']}; font-size:10px; font-weight:700;"
        )
        self.tool_status_labels["apps"].setText("Pronto" if shutil.which("gtk-launch") else "Parcial")
        self.tool_status_labels["apps"].setStyleSheet(
            f"color:{COLORS['green'] if shutil.which('gtk-launch') else COLORS['warning']}; font-size:10px; font-weight:700;"
        )
        self.tool_status_labels["shell"].setText("Ativo" if settings.allow_shell else "Desligado")
        self.tool_status_labels["shell"].setStyleSheet(
            f"color:{COLORS['green'] if settings.allow_shell else COLORS['warning']}; font-size:10px; font-weight:700;"
        )
        self.tool_status_labels["memory"].setText("Ativa" if settings.memory_enabled else "Desligada")
        self.tool_status_labels["memory"].setStyleSheet(
            f"color:{COLORS['green'] if settings.memory_enabled else COLORS['warning']}; font-size:10px; font-weight:700;"
        )

        if settings.memory_enabled:
            try:
                facts = list_facts()
                self.memory_summary.setText(
                    f"Fatos lembrados: {len(facts)}\nPersistência: local (SQLite)"
                )
            except Exception as exc:  # noqa: BLE001
                self.memory_summary.setText(f"Memória indisponível: {exc}")
        else:
            self.memory_summary.setText("Persistência desativada\nAtive somente se quiser memória local")


def run_gui() -> None:
    app = QApplication.instance() or QApplication([])
    app.setApplicationName("J.A.R.V.I.S.")
    app.setOrganizationName("Jczarf")
    app.setFont(QFont("Sans Serif", 10))
    window = JarvisWindow()
    window.show()
    app.exec()
