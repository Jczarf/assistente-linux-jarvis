from __future__ import annotations

import getpass
import html
import os
import platform
import shutil
from datetime import datetime
from typing import Any, Callable

import psutil
from PySide6.QtCore import QObject, QThread, QTimer, Qt, QUrl, Signal, Slot
from PySide6.QtGui import QDesktopServices, QFont, QFontDatabase
from PySide6.QtWidgets import (
    QApplication,
    QFrame,
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
from jarvis.memory import delete_fact, list_facts, save_fact
from jarvis.tools import execute_tool

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
    "warning": "#f3b74a",
    "danger": "#ff6b6b",
}


def layout_mode_for_width(width: int) -> str:
    if width < 780:
        return "compact"
    if width < 1120:
        return "medium"
    return "wide"


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


def _format_tool_result(result: dict[str, Any]) -> str:
    message = str(result.get("message", "")).strip()
    data = result.get("data")
    if isinstance(data, list):
        body = "\n".join(str(item) for item in data)
        return f"{message}\n\n{body}".strip()
    if isinstance(data, dict) and result.get("tool") == "recall":
        body = "\n".join(f"{key}: {value}" for key, value in data.items())
        return f"{message}\n\n{body}".strip()
    return message or "Sem saída."


class Card(QFrame):
    def __init__(self, parent: QWidget | None = None, *, name: str = "card") -> None:
        super().__init__(parent)
        self.setObjectName(name)


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
        except Exception as exc:
            self.failed.emit(str(exc))


class JarvisWindow(QMainWindow):
    NAV_ITEMS = [
        ("Chat", "●"),
        ("Ferramentas", "⌘"),
        ("Memória", "◉"),
        ("Sistema", "▣"),
        ("Configurações", "⚙"),
    ]

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle(
            f"{settings.assistant_name} — Assistente Inteligente para Linux"
        )
        self.resize(1320, 820)
        self.setMinimumSize(680, 520)

        self.ui_font = _font_family(
            ["Inter", "Noto Sans", "Ubuntu"], "DejaVu Sans"
        )
        self.mono_font = _font_family(
            ["JetBrains Mono", "Fira Code", "Cascadia Code"],
            "DejaVu Sans Mono",
        )

        self.assistant: JarvisAssistant | None = None
        self.busy = False
        self.nav_buttons: dict[str, QPushButton] = {}
        self.page_index: dict[str, int] = {}
        self.page_layouts: list[QVBoxLayout] = []
        self.system_value_labels: dict[str, QLabel] = {}
        self.system_progress: dict[str, QProgressBar] = {}
        self.system_detail_labels: dict[str, QLabel] = {}
        self.tool_status_labels: dict[str, QLabel] = {}
        self._active_thread: QThread | None = None
        self._active_worker: AskWorker | None = None
        self._layout_mode = ""

        self._apply_theme()
        self._build_shell()
        self._build_pages()
        self._select_page("Chat")
        self._refresh_status()
        self._apply_responsive_layout(force=True)

        self.timer = QTimer(self)
        self.timer.timeout.connect(self._refresh_status)
        self.timer.start(2500)

    def _apply_theme(self) -> None:
        self.setStyleSheet(
            f"""
            QMainWindow, QWidget#root {{ background: {COLORS['bg']}; color: {COLORS['text']}; }}
            QLabel {{ color: {COLORS['text']}; background: transparent; }}
            QFrame#sidebar, QFrame#inspector {{ background: {COLORS['sidebar']}; }}
            QFrame#sidebar {{ border-right: 1px solid {COLORS['border_soft']}; }}
            QFrame#inspector {{ border-left: 1px solid {COLORS['border_soft']}; }}
            QFrame#card, QFrame#terminalCard, QFrame#inputCard, QFrame#metricCard {{
                background: {COLORS['panel_alt']}; border: 1px solid {COLORS['border']}; border-radius: 13px;
            }}
            QFrame#terminalCard {{ background: #080f16; }}
            QFrame#inputCard {{ background: #0a1219; }}
            QPushButton[nav="true"] {{
                background: transparent; border: none; border-radius: 10px; color: #a9b8c2;
                text-align: left; padding: 12px 14px; font-size: 13px;
            }}
            QPushButton[nav="true"]:hover {{ background: {COLORS['panel_hover']}; color: {COLORS['text']}; }}
            QPushButton[nav="true"]:checked {{ background: #192530; color: #f4f8fb; border: 1px solid #253543; }}
            QPushButton#primaryButton, QPushButton#sendButton {{
                background: {COLORS['green']}; color: #07100a; border: none; border-radius: 9px;
                padding: 9px 13px; font-weight: 700;
            }}
            QPushButton#primaryButton:hover, QPushButton#sendButton:hover {{ background: #8bff73; }}
            QPushButton#primaryButton:disabled, QPushButton#sendButton:disabled {{ background: #25312b; color: #6f8378; }}
            QPushButton#ghostButton {{
                background: #121c25; color: {COLORS['muted']}; border: 1px solid {COLORS['border']};
                border-radius: 9px; padding: 9px 12px;
            }}
            QPushButton#ghostButton:hover {{ color: {COLORS['text']}; border-color: #324756; }}
            QLineEdit {{
                background: #0b131a; color: {COLORS['text']}; border: 1px solid {COLORS['border']};
                border-radius: 8px; padding: 9px 10px; selection-background-color: #25583a;
            }}
            QLineEdit#promptInput {{ background: transparent; border: none; padding: 12px 8px; font-size: 13px; }}
            QTextEdit {{
                background: #081018; border: 1px solid {COLORS['border_soft']}; border-radius: 9px;
                color: {COLORS['text']}; padding: 8px; selection-background-color: #245b39;
            }}
            QTextEdit#chatTranscript {{ background: transparent; border: none; padding: 10px; }}
            QProgressBar {{
                background: #0b1218; border: 1px solid #1b2933; border-radius: 4px; height: 7px; color: transparent;
            }}
            QProgressBar::chunk {{ background: {COLORS['green']}; border-radius: 3px; }}
            QScrollArea {{ border: none; background: transparent; }}
            QScrollBar:vertical {{ background: transparent; width: 8px; margin: 3px 1px; }}
            QScrollBar::handle:vertical {{ background: #253540; border-radius: 4px; min-height: 32px; }}
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
        shell.addWidget(self.sidebar)

        self.stack = QStackedWidget()
        self.stack.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        shell.addWidget(self.stack, 1)

        self.inspector = QFrame()
        self.inspector.setObjectName("inspector")
        shell.addWidget(self.inspector)

        self._build_sidebar()
        self._build_inspector()

    def _build_sidebar(self) -> None:
        layout = QVBoxLayout(self.sidebar)
        layout.setContentsMargins(14, 18, 14, 18)
        layout.setSpacing(6)
        self.sidebar_layout = layout

        brand = QHBoxLayout()
        brand.setSpacing(10)
        self.brand_icon = QLabel(">_")
        self.brand_icon.setStyleSheet(
            f"color:{COLORS['cyan']}; font-family:'{self.mono_font}'; font-size:26px; font-weight:800;"
        )
        brand.addWidget(self.brand_icon)

        brand_text = QVBoxLayout()
        brand_text.setSpacing(0)
        self.brand_title = QLabel("J.A.R.V.I.S.")
        self.brand_title.setStyleSheet(
            f"color:{COLORS['green']}; font-family:'{self.ui_font}'; font-size:16px; font-weight:800;"
        )
        self.brand_subtitle = QLabel("LINUX ASSISTANT")
        self.brand_subtitle.setStyleSheet(
            f"color:{COLORS['muted_2']}; font-family:'{self.ui_font}'; font-size:9px; font-weight:700;"
        )
        brand_text.addWidget(self.brand_title)
        brand_text.addWidget(self.brand_subtitle)
        brand.addLayout(brand_text)
        brand.addStretch()
        layout.addLayout(brand)
        layout.addSpacing(18)

        for name, glyph in self.NAV_ITEMS:
            button = QPushButton(f"{glyph}    {name}")
            button.setProperty("nav", True)
            button.setCheckable(True)
            button.setCursor(Qt.CursorShape.PointingHandCursor)
            button.setToolTip(name)
            button.clicked.connect(lambda _checked=False, page=name: self._select_page(page))
            layout.addWidget(button)
            self.nav_buttons[name] = button

        layout.addStretch(1)
        status_wrap = QFrame()
        status_layout = QHBoxLayout(status_wrap)
        status_layout.setContentsMargins(8, 10, 8, 4)
        self.local_dot = QLabel("●")
        self.local_dot.setStyleSheet(f"color:{COLORS['green']}; font-size:12px;")
        self.local_status = QLabel("Local: ativo")
        self.local_status.setStyleSheet(
            f"color:{COLORS['green']}; font-family:'{self.ui_font}'; font-size:11px; font-weight:700;"
        )
        status_layout.addWidget(self.local_dot)
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

        v.addWidget(self._section_label("CAPACIDADES ATIVAS"))
        tools = Card()
        tv = QVBoxLayout(tools)
        tv.setContentsMargins(14, 10, 14, 10)
        tool_defs = [
            ("Texto + LLM", "llm"),
            ("Aplicativos XDG", "apps"),
            ("Informações do sistema", "system"),
            ("Shell", "shell"),
            ("Memória local", "memory"),
        ]
        for label, key in tool_defs:
            row = QHBoxLayout()
            left = QLabel(label)
            left.setStyleSheet(f"color:{COLORS['text']}; font-size:11px;")
            status = QLabel("—")
            status.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            row.addWidget(left)
            row.addStretch()
            row.addWidget(status)
            tv.addLayout(row)
            tv.addSpacing(6)
            self.tool_status_labels[key] = status
        v.addWidget(tools)

        v.addSpacing(4)
        v.addWidget(self._section_label("STATUS DO SISTEMA"))
        system = Card()
        sv = QVBoxLayout(system)
        sv.setContentsMargins(14, 12, 14, 12)
        sv.setSpacing(10)
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

        v.addSpacing(4)
        v.addWidget(self._section_label("MEMÓRIA"))
        memory = Card()
        mv = QVBoxLayout(memory)
        mv.setContentsMargins(14, 12, 14, 12)
        self.memory_summary = QLabel("Carregando…")
        self.memory_summary.setWordWrap(True)
        self.memory_summary.setStyleSheet(f"color:{COLORS['muted']}; font-size:11px;")
        mv.addWidget(self.memory_summary)
        manage_memory = QPushButton("Gerenciar memória")
        manage_memory.setObjectName("ghostButton")
        manage_memory.clicked.connect(lambda: self._select_page("Memória"))
        mv.addWidget(manage_memory)
        v.addWidget(memory)
        v.addStretch(1)
        scroll.setWidget(host)

        inspector_layout = QVBoxLayout(self.inspector)
        inspector_layout.setContentsMargins(0, 0, 0, 0)
        inspector_layout.addWidget(scroll)

    def _section_label(self, text: str) -> QLabel:
        label = QLabel(text)
        label.setStyleSheet(
            f"color:{COLORS['muted_2']}; font-family:'{self.ui_font}'; font-size:9px; font-weight:800;"
        )
        return label

    def _build_pages(self) -> None:
        builders: list[tuple[str, Callable[[], QWidget]]] = [
            ("Chat", self._chat_page),
            ("Ferramentas", self._tools_page),
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
        self.page_layouts.append(layout)

        head = QHBoxLayout()
        text = QVBoxLayout()
        text.setSpacing(2)
        title_label = QLabel(title)
        title_label.setStyleSheet(
            f"font-family:'{self.ui_font}'; font-size:21px; font-weight:800; color:{COLORS['text']};"
        )
        sub = QLabel(subtitle)
        sub.setWordWrap(True)
        sub.setStyleSheet(
            f"font-family:'{self.ui_font}'; font-size:11px; color:{COLORS['muted']};"
        )
        text.addWidget(title_label)
        text.addWidget(sub)
        head.addLayout(text)
        head.addStretch()
        status = QLabel("●  LOCAL")
        status.setStyleSheet(
            f"background:{COLORS['green_soft']}; color:{COLORS['green']}; border:1px solid #255b31; "
            "border-radius:10px; padding:6px 10px; font-size:9px; font-weight:800;"
        )
        head.addWidget(status)
        layout.addLayout(head)
        return host, layout

    def _chat_page(self) -> QWidget:
        host, layout = self._page_host(
            "J.A.R.V.I.S.",
            "Chat real com Gemini, function calling e ferramentas locais verificáveis",
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
        self.send_button = QPushButton("Enviar")
        self.send_button.setObjectName("sendButton")
        self.send_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.send_button.clicked.connect(self._send_message)
        input_layout.addWidget(prompt_symbol)
        input_layout.addWidget(self.prompt, 1)
        input_layout.addWidget(self.send_button)
        layout.addWidget(input_card)

        self._seed_chat()
        return host

    def _seed_chat(self) -> None:
        snap = system_snapshot()
        self.chat.setHtml(
            f"""
            <div style="font-family:'{self.mono_font}'; font-size:10.5pt; color:{COLORS['text']}; line-height:1.45;">
              <span style="color:{COLORS['green']}; font-weight:700;">J.A.R.V.I.S. pronto.</span><br>
              <span>As ações abaixo usam estado real do computador.</span><br><br>
              <span style="color:{COLORS['muted']};">&gt; SISTEMA</span><br>
              <span style="color:{COLORS['green']};">SO:</span> {html.escape(str(snap['os']))}<br>
              <span style="color:{COLORS['green']};">CPU:</span> {html.escape(str(snap['cpu']))}<br>
              <span style="color:{COLORS['green']};">Memória:</span> {html.escape(str(snap['memory']))}<br>
              <span style="color:{COLORS['green']};">Disco:</span> {html.escape(str(snap['disk']))}<br><br>
              <span style="color:{COLORS['muted']};">O agente bloqueia repetição idêntica de ferramentas e não declara sucesso sem retorno ok=true.</span>
            </div>
            """
        )
        self.chat.moveCursor(self.chat.textCursor().MoveOperation.End)

    def _tools_page(self) -> QWidget:
        host, layout = self._page_host(
            "Ferramentas",
            "Controles diretos sobre as mesmas ferramentas disponíveis ao agente",
        )
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        body = QWidget()
        self.tools_grid = QGridLayout(body)
        self.tools_grid.setHorizontalSpacing(12)
        self.tools_grid.setVerticalSpacing(12)
        self.tool_cards: list[QWidget] = []

        self.tool_cards.append(self._system_tool_card())
        self.tool_cards.append(self._apps_tool_card())
        self.tool_cards.append(self._shell_tool_card())
        self.tool_cards.append(self._memory_tool_card())

        scroll.setWidget(body)
        layout.addWidget(scroll, 1)
        return host

    def _tool_card_base(self, title: str, description: str) -> tuple[Card, QVBoxLayout]:
        card = Card()
        card.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        cv = QVBoxLayout(card)
        cv.setContentsMargins(18, 16, 18, 16)
        cv.setSpacing(9)
        t = QLabel(title)
        t.setStyleSheet(f"font-size:14px; font-weight:800; color:{COLORS['text']};")
        d = QLabel(description)
        d.setWordWrap(True)
        d.setStyleSheet(f"font-size:11px; color:{COLORS['muted']};")
        cv.addWidget(t)
        cv.addWidget(d)
        return card, cv

    def _system_tool_card(self) -> QWidget:
        card, cv = self._tool_card_base("Informações do sistema", "Lê CPU, RAM, disco e kernel neste computador.")
        self.system_tool_output = QTextEdit()
        self.system_tool_output.setReadOnly(True)
        self.system_tool_output.setMaximumHeight(115)
        button = QPushButton("Atualizar agora")
        button.setObjectName("primaryButton")
        button.clicked.connect(self._run_system_tool)
        cv.addWidget(self.system_tool_output)
        cv.addWidget(button)
        self._run_system_tool()
        return card

    def _apps_tool_card(self) -> QWidget:
        card, cv = self._tool_card_base(
            "Aplicativos XDG",
            "Pesquisa aplicativos instalados e abre um nome exato quando solicitado.",
        )
        self.apps_query = QLineEdit()
        self.apps_query.setPlaceholderText("Ex.: Firefox")
        buttons = QHBoxLayout()
        search = QPushButton("Buscar")
        search.setObjectName("ghostButton")
        search.clicked.connect(self._search_apps)
        open_button = QPushButton("Abrir")
        open_button.setObjectName("primaryButton")
        open_button.clicked.connect(self._open_app)
        buttons.addWidget(search)
        buttons.addWidget(open_button)
        self.apps_output = QTextEdit()
        self.apps_output.setReadOnly(True)
        self.apps_output.setMaximumHeight(150)
        cv.addWidget(self.apps_query)
        cv.addLayout(buttons)
        cv.addWidget(self.apps_output)
        return card

    def _shell_tool_card(self) -> QWidget:
        card, cv = self._tool_card_base(
            "Shell",
            "Execução direta com timeout e política de bloqueio. Desativado por padrão.",
        )
        self.shell_input = QLineEdit()
        self.shell_input.setPlaceholderText("Ex.: uname -a")
        self.shell_run = QPushButton("Executar comando")
        self.shell_run.setObjectName("primaryButton")
        self.shell_run.setEnabled(settings.allow_shell)
        self.shell_run.clicked.connect(self._run_shell_tool)
        self.shell_output = QTextEdit()
        self.shell_output.setReadOnly(True)
        self.shell_output.setMaximumHeight(150)
        if not settings.allow_shell:
            self.shell_output.setPlainText(
                "Shell desativado. Ative JARVIS_ALLOW_SHELL=true e reinicie o aplicativo."
            )
        cv.addWidget(self.shell_input)
        cv.addWidget(self.shell_run)
        cv.addWidget(self.shell_output)
        return card

    def _memory_tool_card(self) -> QWidget:
        card, cv = self._tool_card_base(
            "Memória local",
            "Gerencie os fatos realmente persistidos no SQLite local.",
        )
        status = QLabel("Habilitada" if settings.memory_enabled else "Desativada")
        status.setStyleSheet(
            f"color:{COLORS['green'] if settings.memory_enabled else COLORS['warning']}; font-size:11px; font-weight:800;"
        )
        button = QPushButton("Abrir memória")
        button.setObjectName("ghostButton")
        button.clicked.connect(lambda: self._select_page("Memória"))
        cv.addWidget(status)
        cv.addWidget(button)
        return card

    def _run_system_tool(self) -> None:
        result = execute_tool("system_info")
        if hasattr(self, "system_tool_output"):
            self.system_tool_output.setPlainText(_format_tool_result(result))

    def _search_apps(self) -> None:
        result = execute_tool("list_apps", {"query": self.apps_query.text()})
        self.apps_output.setPlainText(_format_tool_result(result))

    def _open_app(self) -> None:
        result = execute_tool("open_app", {"app": self.apps_query.text()})
        self.apps_output.setPlainText(_format_tool_result(result))

    def _run_shell_tool(self) -> None:
        result = execute_tool("run_command", {"command": self.shell_input.text()})
        self.shell_output.setPlainText(_format_tool_result(result))

    def _memory_page(self) -> QWidget:
        host, layout = self._page_host(
            "Memória",
            "Fatos persistentes locais; adicione e remova somente quando o recurso estiver habilitado",
        )
        editor = Card()
        ev = QVBoxLayout(editor)
        ev.setContentsMargins(18, 16, 18, 16)
        ev.setSpacing(8)
        title = QLabel("Adicionar ou atualizar")
        title.setStyleSheet(f"font-size:14px; font-weight:800; color:{COLORS['text']};")
        self.memory_key = QLineEdit()
        self.memory_key.setPlaceholderText("Chave")
        self.memory_value = QLineEdit()
        self.memory_value.setPlaceholderText("Valor")
        self.memory_save = QPushButton("Salvar na memória")
        self.memory_save.setObjectName("primaryButton")
        self.memory_save.setEnabled(settings.memory_enabled)
        self.memory_save.clicked.connect(self._save_memory_from_ui)
        self.memory_feedback = QLabel("")
        self.memory_feedback.setWordWrap(True)
        self.memory_feedback.setStyleSheet(f"color:{COLORS['muted']}; font-size:11px;")
        if not settings.memory_enabled:
            self.memory_feedback.setText(
                "Memória desativada. Ative JARVIS_MEMORY_ENABLED=true no .env e reinicie."
            )
        ev.addWidget(title)
        ev.addWidget(self.memory_key)
        ev.addWidget(self.memory_value)
        ev.addWidget(self.memory_save)
        ev.addWidget(self.memory_feedback)
        layout.addWidget(editor)

        self.memory_page_card = Card()
        self.memory_page_layout = QVBoxLayout(self.memory_page_card)
        self.memory_page_layout.setContentsMargins(18, 16, 18, 16)
        layout.addWidget(self.memory_page_card, 1)
        self._render_memory_page()
        return host

    def _save_memory_from_ui(self) -> None:
        message = save_fact(self.memory_key.text(), self.memory_value.text())
        self.memory_feedback.setText(message)
        if message.startswith("Informação '"):
            self.memory_key.clear()
            self.memory_value.clear()
        self._render_memory_page()
        self._refresh_status()

    def _delete_memory_from_ui(self, key: str) -> None:
        self.memory_feedback.setText(delete_fact(key))
        self._render_memory_page()
        self._refresh_status()

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
            self.memory_page_layout.addWidget(title)
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
            rh = QHBoxLayout(row)
            rh.setContentsMargins(12, 9, 12, 9)
            text = QVBoxLayout()
            k = QLabel(str(key))
            k.setStyleSheet(f"color:{COLORS['green']}; font-size:10px; font-weight:800;")
            val = QLabel(str(value))
            val.setWordWrap(True)
            val.setStyleSheet(f"color:{COLORS['text']}; font-size:11px;")
            text.addWidget(k)
            text.addWidget(val)
            remove = QPushButton("Remover")
            remove.setObjectName("ghostButton")
            remove.clicked.connect(
                lambda _checked=False, fact_key=key: self._delete_memory_from_ui(fact_key)
            )
            rh.addLayout(text, 1)
            rh.addWidget(remove)
            self.memory_page_layout.addWidget(row)

    def _system_page(self) -> QWidget:
        host, layout = self._page_host(
            "Sistema",
            "Visão local de hardware, sessão e uso de recursos",
        )
        self.system_grid = QGridLayout()
        self.system_grid.setHorizontalSpacing(12)
        self.system_grid.setVerticalSpacing(12)
        self.system_cards: list[QWidget] = []

        for label, key in [
            ("Sistema operacional", "os"),
            ("Uptime", "uptime"),
            ("Usuário", "user"),
            ("Hostname", "hostname"),
            ("Shell", "shell"),
            ("Desktop", "desktop"),
        ]:
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
            self.system_cards.append(card)
        layout.addLayout(self.system_grid)

        resource = Card()
        rv = QVBoxLayout(resource)
        rv.setContentsMargins(18, 17, 18, 17)
        self.system_page_resource: dict[str, tuple[QLabel, QProgressBar]] = {}
        for title, key in [("CPU", "cpu"), ("Memória", "memory"), ("Disco /", "disk")]:
            row = QHBoxLayout()
            l = QLabel(title)
            value = QLabel("—")
            value.setStyleSheet(
                f"color:{COLORS['green']}; font-family:'{self.mono_font}'; font-size:10px;"
            )
            row.addWidget(l)
            row.addStretch()
            row.addWidget(value)
            bar = QProgressBar()
            bar.setRange(0, 100)
            bar.setTextVisible(False)
            rv.addLayout(row)
            rv.addWidget(bar)
            self.system_page_resource[key] = (value, bar)
        layout.addWidget(resource)
        layout.addStretch(1)
        return host

    def _settings_page(self) -> QWidget:
        host, layout = self._page_host(
            "Configurações",
            "Estado efetivo carregado do ambiente; segredos nunca são exibidos",
        )
        card = Card()
        cv = QVBoxLayout(card)
        cv.setContentsMargins(20, 18, 20, 18)
        cv.setSpacing(12)
        rows = [
            ("Modelo", settings.model),
            ("Nome do assistente", settings.assistant_name),
            ("Memória persistente", "habilitada" if settings.memory_enabled else "desativada"),
            ("Shell", "habilitado" if settings.allow_shell else "desativado"),
            ("Timeout shell", f"{settings.shell_timeout}s"),
            ("Timeout modelo", f"{settings.request_timeout_seconds}s"),
            ("Máximo de etapas do agente", str(settings.max_agent_steps)),
            ("Repetição idêntica de ferramenta", f"até {settings.tool_repeat_limit}x"),
            ("Diretório de dados", str(settings.data_dir)),
            ("GEMINI_API_KEY", "configurada" if bool(settings.api_key) else "não configurada"),
        ]
        for label, value in rows:
            row = QHBoxLayout()
            l = QLabel(label)
            l.setStyleSheet(f"color:{COLORS['muted']}; font-size:11px;")
            val = QLabel(value)
            val.setWordWrap(True)
            val.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
            val.setStyleSheet(
                f"color:{COLORS['text']}; font-family:'{self.mono_font}'; font-size:10px; font-weight:700;"
            )
            row.addWidget(l)
            row.addStretch()
            row.addWidget(val)
            cv.addLayout(row)

        note = QLabel("Alterações no .env são aplicadas ao reiniciar o aplicativo.")
        note.setWordWrap(True)
        note.setStyleSheet(f"color:{COLORS['warning']}; font-size:11px;")
        cv.addWidget(note)

        actions = QHBoxLayout()
        open_data = QPushButton("Abrir pasta de dados")
        open_data.setObjectName("ghostButton")
        open_data.clicked.connect(self._open_data_dir)
        copy_diag = QPushButton("Copiar diagnóstico")
        copy_diag.setObjectName("primaryButton")
        copy_diag.clicked.connect(self._copy_diagnostics)
        actions.addWidget(open_data)
        actions.addWidget(copy_diag)
        cv.addLayout(actions)
        self.settings_feedback = QLabel("")
        self.settings_feedback.setStyleSheet(f"color:{COLORS['muted']}; font-size:11px;")
        cv.addWidget(self.settings_feedback)
        layout.addWidget(card)
        layout.addStretch(1)
        return host

    def _open_data_dir(self) -> None:
        try:
            settings.data_dir.mkdir(parents=True, exist_ok=True)
            ok = QDesktopServices.openUrl(QUrl.fromLocalFile(str(settings.data_dir)))
            self.settings_feedback.setText(
                "Diretório aberto." if ok else "O ambiente gráfico não conseguiu abrir o diretório."
            )
        except OSError as exc:
            self.settings_feedback.setText(f"Falha ao preparar diretório: {exc}")

    def _copy_diagnostics(self) -> None:
        snap = system_snapshot()
        text = "\n".join(
            [
                f"JARVIS model={settings.model}",
                f"os={snap['os']}",
                f"desktop={snap['desktop']}",
                f"shell={snap['shell']}",
                f"memory_enabled={settings.memory_enabled}",
                f"shell_enabled={settings.allow_shell}",
                f"request_timeout={settings.request_timeout_seconds}s",
                f"max_agent_steps={settings.max_agent_steps}",
            ]
        )
        QApplication.clipboard().setText(text)
        self.settings_feedback.setText("Diagnóstico não sensível copiado.")

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
        self.send_button.setText("Processando…")
        self.prompt.setEnabled(False)

        try:
            assistant = self._ensure_assistant()
        except Exception as exc:
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
        thread.finished.connect(self._clear_thread_refs)
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

    @Slot()
    def _clear_thread_refs(self) -> None:
        self._active_thread = None
        self._active_worker = None

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

    def _set_status_label(self, key: str, text: str, color: str) -> None:
        label = self.tool_status_labels.get(key)
        if label is None:
            return
        label.setText(text)
        label.setStyleSheet(f"color:{color}; font-size:10px; font-weight:700;")

    def _refresh_status(self) -> None:
        snap = system_snapshot()
        self.clock_label.setText(datetime.now().strftime("%d/%m/%Y  %H:%M"))
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

        self._set_status_label(
            "llm",
            "Configurado" if settings.api_key else "Sem chave",
            COLORS["green"] if settings.api_key else COLORS["warning"],
        )
        gtk = bool(shutil.which("gtk-launch"))
        self._set_status_label(
            "apps",
            "Pronto" if gtk else "Parcial",
            COLORS["green"] if gtk else COLORS["warning"],
        )
        self._set_status_label("system", "Pronto", COLORS["green"])
        self._set_status_label(
            "shell",
            "Ativo" if settings.allow_shell else "Desligado",
            COLORS["green"] if settings.allow_shell else COLORS["warning"],
        )
        self._set_status_label(
            "memory",
            "Ativa" if settings.memory_enabled else "Desligada",
            COLORS["green"] if settings.memory_enabled else COLORS["warning"],
        )

        if settings.memory_enabled:
            try:
                facts = list_facts()
                self.memory_summary.setText(
                    f"Fatos lembrados: {len(facts)}\nPersistência: SQLite local"
                )
            except Exception as exc:
                self.memory_summary.setText(f"Memória indisponível: {exc}")
        else:
            self.memory_summary.setText("Persistência desativada\nSem simulação de memória")

    @staticmethod
    def _reflow_grid(grid: QGridLayout, widgets: list[QWidget], columns: int) -> None:
        while grid.count():
            grid.takeAt(0)
        for index, widget in enumerate(widgets):
            grid.addWidget(widget, index // columns, index % columns)

    def _apply_responsive_layout(self, *, force: bool = False) -> None:
        mode = layout_mode_for_width(self.width())
        if mode == self._layout_mode and not force:
            return
        self._layout_mode = mode
        compact = mode == "compact"
        medium = mode == "medium"

        if compact:
            self.sidebar.setFixedWidth(72)
            self.inspector.hide()
            self.brand_title.hide()
            self.brand_subtitle.hide()
            self.local_status.hide()
            self.sidebar_layout.setContentsMargins(8, 14, 8, 14)
            for name, glyph in self.NAV_ITEMS:
                button = self.nav_buttons[name]
                button.setText(glyph)
                button.setStyleSheet("text-align:center; padding:12px 4px;")
        else:
            self.sidebar.setFixedWidth(190 if medium else 220)
            self.inspector.setVisible(not medium)
            if not medium:
                self.inspector.setFixedWidth(300)
            self.brand_title.show()
            self.brand_subtitle.show()
            self.local_status.show()
            self.sidebar_layout.setContentsMargins(12 if medium else 14, 18, 12 if medium else 14, 18)
            for name, glyph in self.NAV_ITEMS:
                button = self.nav_buttons[name]
                button.setText(f"{glyph}    {name}")
                button.setStyleSheet("")

        margin = 12 if compact else 18 if medium else 26
        for layout in self.page_layouts:
            layout.setContentsMargins(margin, 16 if compact else 22, margin, 18)

        if hasattr(self, "tools_grid"):
            self._reflow_grid(self.tools_grid, self.tool_cards, 1 if mode != "wide" else 2)
        if hasattr(self, "system_grid"):
            system_columns = 1 if compact else 2 if medium else 3
            self._reflow_grid(self.system_grid, self.system_cards, system_columns)

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        if hasattr(self, "_layout_mode"):
            self._apply_responsive_layout()


def run_gui() -> None:
    app = QApplication.instance() or QApplication([])
    app.setApplicationName("J.A.R.V.I.S.")
    app.setOrganizationName("Jczarf")
    app.setFont(QFont("Sans Serif", 10))
    window = JarvisWindow()
    window.show()
    app.exec()
