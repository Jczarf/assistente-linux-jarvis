from __future__ import annotations

import platform
import shutil
import threading
import tkinter as tk
from datetime import datetime
from tkinter import font as tkfont
from typing import Callable

import psutil

from jarvis.config import settings
from jarvis.core import JarvisAssistant
from jarvis.memory import list_facts


COLORS = {
    "bg": "#080d12",
    "panel": "#0d141c",
    "panel_alt": "#111a24",
    "panel_hover": "#182431",
    "border": "#22303c",
    "text": "#e8eef3",
    "muted": "#8ea0ad",
    "green": "#72f25b",
    "green_dim": "#1f6b2d",
    "cyan": "#62c6ff",
    "warning": "#f3b74a",
    "danger": "#ff6b6b",
}


def _fmt_gib(value: float) -> str:
    return f"{value / 1024**3:.1f} GiB"


def system_snapshot() -> dict[str, str]:
    vm = psutil.virtual_memory()
    disk = psutil.disk_usage("/")
    return {
        "os": f"{platform.system()} {platform.release()}",
        "uptime": _format_uptime(),
        "user": _safe_username(),
        "hostname": platform.node() or "localhost",
        "shell": _shell_name(),
        "cpu": f"{psutil.cpu_percent(interval=None):.0f}%",
        "memory": f"{_fmt_gib(vm.used)} / {_fmt_gib(vm.total)} ({vm.percent:.0f}%)",
        "disk": f"{_fmt_gib(disk.used)} / {_fmt_gib(disk.total)} ({disk.percent:.0f}%)",
    }


def _safe_username() -> str:
    import getpass

    try:
        return getpass.getuser()
    except Exception:
        return "usuário"


def _shell_name() -> str:
    import os

    shell = os.getenv("SHELL", "")
    return shell.rsplit("/", 1)[-1] or "desconhecido"


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


class RoundedCard(tk.Frame):
    """Card simples sem dependências gráficas externas."""

    def __init__(self, master: tk.Misc, **kwargs) -> None:
        bg = kwargs.pop("bg", COLORS["panel_alt"])
        super().__init__(
            master,
            bg=bg,
            highlightbackground=COLORS["border"],
            highlightthickness=1,
            bd=0,
            **kwargs,
        )


class JarvisGUI:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title(f"{settings.assistant_name} — Assistente para Linux")
        self.root.geometry("1360x820")
        self.root.minsize(1040, 680)
        self.root.configure(bg=COLORS["bg"])

        self.assistant: JarvisAssistant | None = None
        self.busy = False
        self.active_page = "Chat"
        self.nav_buttons: dict[str, tk.Button] = {}
        self.page_builders: dict[str, Callable[[], None]] = {
            "Chat": self._build_chat_page,
            "Ferramentas": self._build_tools_page,
            "Automação": self._build_automation_page,
            "Memória": self._build_memory_page,
            "Sistema": self._build_system_page,
            "Configurações": self._build_settings_page,
        }

        self._configure_fonts()
        self._build_shell()
        self._show_page("Chat")
        self._tick_status()

    def _configure_fonts(self) -> None:
        families = set(tkfont.families())
        self.ui_font = "Inter" if "Inter" in families else "DejaVu Sans"
        self.mono_font = "JetBrains Mono" if "JetBrains Mono" in families else "DejaVu Sans Mono"

    def _build_shell(self) -> None:
        self.root.grid_columnconfigure(0, weight=0)
        self.root.grid_columnconfigure(1, weight=1)
        self.root.grid_columnconfigure(2, weight=0)
        self.root.grid_rowconfigure(0, weight=1)

        self.sidebar = tk.Frame(self.root, bg="#0a1118", width=208)
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        self.sidebar.grid_propagate(False)

        self.content = tk.Frame(self.root, bg=COLORS["bg"])
        self.content.grid(row=0, column=1, sticky="nsew", padx=(1, 0))
        self.content.grid_rowconfigure(0, weight=1)
        self.content.grid_columnconfigure(0, weight=1)

        self.inspector = tk.Frame(self.root, bg="#0a1118", width=292)
        self.inspector.grid(row=0, column=2, sticky="nsew")
        self.inspector.grid_propagate(False)

        self._build_sidebar()
        self._build_inspector()

    def _build_sidebar(self) -> None:
        brand = tk.Frame(self.sidebar, bg="#0a1118")
        brand.pack(fill="x", padx=18, pady=(20, 22))

        tk.Label(
            brand,
            text=">_",
            bg="#0a1118",
            fg=COLORS["cyan"],
            font=(self.mono_font, 22, "bold"),
        ).pack(side="left")
        text = tk.Frame(brand, bg="#0a1118")
        text.pack(side="left", padx=(10, 0))
        tk.Label(
            text,
            text="J.A.R.V.I.S.",
            bg="#0a1118",
            fg=COLORS["green"],
            font=(self.ui_font, 14, "bold"),
        ).pack(anchor="w")
        tk.Label(
            text,
            text="Linux Assistant",
            bg="#0a1118",
            fg=COLORS["muted"],
            font=(self.ui_font, 8),
        ).pack(anchor="w")

        items = [
            ("Chat", "●"),
            ("Ferramentas", "⌘"),
            ("Automação", "⚙"),
            ("Memória", "◉"),
            ("Sistema", "▣"),
            ("Configurações", "⚙"),
        ]
        for name, icon in items:
            button = tk.Button(
                self.sidebar,
                text=f"  {icon}   {name}",
                anchor="w",
                relief="flat",
                bd=0,
                padx=14,
                pady=11,
                bg="#0a1118",
                fg="#b8c6cf",
                activebackground=COLORS["panel_hover"],
                activeforeground=COLORS["text"],
                font=(self.ui_font, 10),
                cursor="hand2",
                command=lambda page=name: self._show_page(page),
            )
            button.pack(fill="x", padx=10, pady=2)
            self.nav_buttons[name] = button

        spacer = tk.Frame(self.sidebar, bg="#0a1118")
        spacer.pack(fill="both", expand=True)

        self.local_status = tk.Label(
            self.sidebar,
            text="●  Local: ativo",
            bg="#0a1118",
            fg=COLORS["green"],
            font=(self.ui_font, 9, "bold"),
            padx=18,
            pady=16,
            anchor="w",
        )
        self.local_status.pack(fill="x")

    def _build_inspector(self) -> None:
        title = tk.Label(
            self.inspector,
            text="INTERAÇÃO",
            bg="#0a1118",
            fg=COLORS["muted"],
            font=(self.ui_font, 8, "bold"),
            anchor="w",
        )
        title.pack(fill="x", padx=18, pady=(20, 8))

        interaction = RoundedCard(self.inspector)
        interaction.pack(fill="x", padx=14)
        self._status_row(interaction, "🎙  Voz", "não portada", COLORS["warning"])
        self._status_row(interaction, "▣  Texto", "ativo", COLORS["green"])

        tk.Label(
            self.inspector,
            text="FERRAMENTAS LOCAIS",
            bg="#0a1118",
            fg=COLORS["muted"],
            font=(self.ui_font, 8, "bold"),
            anchor="w",
        ).pack(fill="x", padx=18, pady=(18, 8))

        tools = RoundedCard(self.inspector)
        tools.pack(fill="x", padx=14)
        self.tool_rows: dict[str, tk.Label] = {}
        for label, key in [
            ("Sistema", "system"),
            ("Aplicativos XDG", "apps"),
            ("Shell", "shell"),
            ("Memória local", "memory"),
        ]:
            row = tk.Frame(tools, bg=COLORS["panel_alt"])
            row.pack(fill="x", padx=12, pady=7)
            tk.Label(
                row,
                text=label,
                bg=COLORS["panel_alt"],
                fg=COLORS["text"],
                font=(self.ui_font, 9),
            ).pack(side="left")
            status = tk.Label(
                row,
                text="pronto",
                bg=COLORS["panel_alt"],
                fg=COLORS["green"],
                font=(self.ui_font, 8, "bold"),
            )
            status.pack(side="right")
            self.tool_rows[key] = status

        tk.Label(
            self.inspector,
            text="STATUS DO SISTEMA",
            bg="#0a1118",
            fg=COLORS["muted"],
            font=(self.ui_font, 8, "bold"),
            anchor="w",
        ).pack(fill="x", padx=18, pady=(18, 8))

        system_card = RoundedCard(self.inspector)
        system_card.pack(fill="x", padx=14)
        self.system_labels: dict[str, tk.Label] = {}
        for label, key in [("CPU", "cpu"), ("Memória", "memory"), ("Disco /", "disk")]:
            row = tk.Frame(system_card, bg=COLORS["panel_alt"])
            row.pack(fill="x", padx=12, pady=8)
            tk.Label(
                row,
                text=label,
                bg=COLORS["panel_alt"],
                fg=COLORS["muted"],
                font=(self.ui_font, 8),
            ).pack(anchor="w")
            value = tk.Label(
                row,
                text="—",
                bg=COLORS["panel_alt"],
                fg=COLORS["green"],
                font=(self.mono_font, 9, "bold"),
                anchor="w",
            )
            value.pack(fill="x", pady=(2, 0))
            self.system_labels[key] = value

        tk.Label(
            self.inspector,
            text="MEMÓRIA",
            bg="#0a1118",
            fg=COLORS["muted"],
            font=(self.ui_font, 8, "bold"),
            anchor="w",
        ).pack(fill="x", padx=18, pady=(18, 8))

        memory_card = RoundedCard(self.inspector)
        memory_card.pack(fill="x", padx=14)
        self.memory_summary = tk.Label(
            memory_card,
            text="Persistência desativada",
            bg=COLORS["panel_alt"],
            fg=COLORS["muted"],
            font=(self.ui_font, 9),
            justify="left",
            anchor="w",
            padx=12,
            pady=12,
        )
        self.memory_summary.pack(fill="x")

    def _status_row(self, parent: tk.Misc, label: str, status: str, color: str) -> None:
        row = tk.Frame(parent, bg=COLORS["panel_alt"])
        row.pack(fill="x", padx=12, pady=8)
        tk.Label(
            row, text=label, bg=COLORS["panel_alt"], fg=COLORS["text"], font=(self.ui_font, 9)
        ).pack(side="left")
        tk.Label(
            row, text=status, bg=COLORS["panel_alt"], fg=color, font=(self.ui_font, 8, "bold")
        ).pack(side="right")

    def _show_page(self, page: str) -> None:
        self.active_page = page
        for name, button in self.nav_buttons.items():
            if name == page:
                button.configure(bg=COLORS["panel_hover"], fg=COLORS["text"])
            else:
                button.configure(bg="#0a1118", fg="#b8c6cf")

        for child in self.content.winfo_children():
            child.destroy()

        self.page_builders[page]()

    def _page_header(self, title: str, subtitle: str) -> tk.Frame:
        wrapper = tk.Frame(self.content, bg=COLORS["bg"])
        wrapper.grid(row=0, column=0, sticky="nsew", padx=26, pady=22)
        wrapper.grid_columnconfigure(0, weight=1)
        wrapper.grid_rowconfigure(1, weight=1)

        head = tk.Frame(wrapper, bg=COLORS["bg"])
        head.grid(row=0, column=0, sticky="ew", pady=(0, 14))
        tk.Label(
            head,
            text=title,
            bg=COLORS["bg"],
            fg=COLORS["text"],
            font=(self.ui_font, 18, "bold"),
        ).pack(anchor="w")
        tk.Label(
            head,
            text=subtitle,
            bg=COLORS["bg"],
            fg=COLORS["muted"],
            font=(self.ui_font, 9),
        ).pack(anchor="w", pady=(4, 0))
        return wrapper

    def _build_chat_page(self) -> None:
        wrapper = self._page_header(
            "J.A.R.V.I.S.",
            "Assistente local para Linux · texto + function calling",
        )

        chat_card = RoundedCard(wrapper, bg="#0a1118")
        chat_card.grid(row=1, column=0, sticky="nsew")
        chat_card.grid_columnconfigure(0, weight=1)
        chat_card.grid_rowconfigure(0, weight=1)

        self.chat = tk.Text(
            chat_card,
            bg="#0a1118",
            fg=COLORS["text"],
            insertbackground=COLORS["green"],
            relief="flat",
            bd=0,
            wrap="word",
            padx=20,
            pady=18,
            font=(self.mono_font, 10),
            selectbackground="#214f36",
        )
        self.chat.grid(row=0, column=0, sticky="nsew")
        scroll = tk.Scrollbar(chat_card, command=self.chat.yview, bg=COLORS["panel_alt"])
        scroll.grid(row=0, column=1, sticky="ns")
        self.chat.configure(yscrollcommand=scroll.set)

        self.chat.tag_configure("jarvis", foreground=COLORS["green"], font=(self.mono_font, 10, "bold"))
        self.chat.tag_configure("user", foreground=COLORS["cyan"], font=(self.mono_font, 10, "bold"))
        self.chat.tag_configure("muted", foreground=COLORS["muted"])
        self.chat.tag_configure("error", foreground=COLORS["danger"])
        self.chat.insert("end", "J.A.R.V.I.S. carregado e pronto.\n", "jarvis")
        self.chat.insert("end", "Como posso ajudar você hoje?\n\n", "muted")
        self.chat.configure(state="disabled")

        composer = tk.Frame(chat_card, bg=COLORS["panel_alt"], padx=12, pady=10)
        composer.grid(row=1, column=0, columnspan=2, sticky="ew", padx=12, pady=12)
        composer.grid_columnconfigure(0, weight=1)

        self.entry = tk.Entry(
            composer,
            bg=COLORS["panel_alt"],
            fg=COLORS["text"],
            insertbackground=COLORS["green"],
            relief="flat",
            bd=0,
            font=(self.ui_font, 10),
        )
        self.entry.grid(row=0, column=0, sticky="ew", padx=(4, 10), ipady=8)
        self.entry.bind("<Return>", lambda _event: self._submit())

        self.send_button = tk.Button(
            composer,
            text="Enviar  ➜",
            command=self._submit,
            bg=COLORS["green"],
            fg="#071008",
            activebackground="#8bff78",
            activeforeground="#071008",
            relief="flat",
            bd=0,
            padx=16,
            pady=8,
            font=(self.ui_font, 9, "bold"),
            cursor="hand2",
        )
        self.send_button.grid(row=0, column=1)

        self.entry.focus_set()

    def _append_chat(self, who: str, text: str, tag: str) -> None:
        if not hasattr(self, "chat") or not self.chat.winfo_exists():
            return
        self.chat.configure(state="normal")
        self.chat.insert("end", f"{who}\n", tag)
        self.chat.insert("end", f"{text.strip()}\n\n")
        self.chat.configure(state="disabled")
        self.chat.see("end")

    def _submit(self) -> None:
        if self.busy or not hasattr(self, "entry"):
            return
        text = self.entry.get().strip()
        if not text:
            return
        self.entry.delete(0, "end")
        self._append_chat("Você:", text, "user")
        self.busy = True
        self.send_button.configure(state="disabled", text="Processando…")

        thread = threading.Thread(target=self._ask_worker, args=(text,), daemon=True)
        thread.start()

    def _ask_worker(self, text: str) -> None:
        try:
            if self.assistant is None:
                self.assistant = JarvisAssistant()
            answer = self.assistant.ask(text)
            self.root.after(0, lambda: self._finish_answer(answer, None))
        except Exception as exc:
            self.root.after(0, lambda: self._finish_answer("", exc))

    def _finish_answer(self, answer: str, error: Exception | None) -> None:
        self.busy = False
        if hasattr(self, "send_button") and self.send_button.winfo_exists():
            self.send_button.configure(state="normal", text="Enviar  ➜")
        if error is not None:
            self._append_chat(
                "Erro:",
                f"{error}\nConfigure GEMINI_API_KEY em .env para usar o chat.",
                "error",
            )
        else:
            self._append_chat(f"{settings.assistant_name}:", answer, "jarvis")

    def _build_tools_page(self) -> None:
        wrapper = self._page_header("Ferramentas", "Capacidades locais disponíveis nesta edição pública")
        body = tk.Frame(wrapper, bg=COLORS["bg"])
        body.grid(row=1, column=0, sticky="nsew")
        body.grid_columnconfigure((0, 1), weight=1)

        items = [
            ("Informações do sistema", "CPU, RAM, disco e sistema operacional.", True),
            ("Aplicativos XDG", "Descoberta e abertura de aplicativos instalados.", True),
            ("Shell", "Execução genérica com política básica de segurança.", settings.allow_shell),
            ("Memória local", "Persistência SQLite opcional.", settings.memory_enabled),
        ]
        for index, (name, desc, enabled) in enumerate(items):
            card = RoundedCard(body)
            card.grid(row=index // 2, column=index % 2, sticky="nsew", padx=7, pady=7)
            tk.Label(
                card,
                text=name,
                bg=COLORS["panel_alt"],
                fg=COLORS["text"],
                font=(self.ui_font, 11, "bold"),
            ).pack(anchor="w", padx=16, pady=(15, 5))
            tk.Label(
                card,
                text=desc,
                bg=COLORS["panel_alt"],
                fg=COLORS["muted"],
                wraplength=320,
                justify="left",
                font=(self.ui_font, 9),
            ).pack(anchor="w", padx=16)
            tk.Label(
                card,
                text="● habilitado" if enabled else "● desativado por padrão",
                bg=COLORS["panel_alt"],
                fg=COLORS["green"] if enabled else COLORS["warning"],
                font=(self.ui_font, 8, "bold"),
            ).pack(anchor="w", padx=16, pady=(10, 15))

    def _build_automation_page(self) -> None:
        wrapper = self._page_header("Automação", "Área reservada para recursos ainda não portados")
        card = RoundedCard(wrapper)
        card.grid(row=1, column=0, sticky="new")
        tk.Label(
            card,
            text="Automação avançada ainda não faz parte da edição pública.",
            bg=COLORS["panel_alt"],
            fg=COLORS["text"],
            font=(self.ui_font, 12, "bold"),
        ).pack(anchor="w", padx=18, pady=(18, 8))
        tk.Label(
            card,
            text=(
                "O protótipo privado experimentou rotinas de desktop, navegador e voz. "
                "Esses módulos permanecem fora desta versão até serem sanitizados, revisados e testados."
            ),
            bg=COLORS["panel_alt"],
            fg=COLORS["muted"],
            wraplength=720,
            justify="left",
            font=(self.ui_font, 9),
        ).pack(anchor="w", padx=18, pady=(0, 18))

    def _build_memory_page(self) -> None:
        wrapper = self._page_header("Memória", "Informações persistentes armazenadas localmente")
        card = RoundedCard(wrapper)
        card.grid(row=1, column=0, sticky="nsew")
        if not settings.memory_enabled:
            text = "Memória persistente está desativada por padrão.\nDefina JARVIS_MEMORY_ENABLED=true para habilitar."
        else:
            facts = list_facts()
            text = "\n".join(f"• {key}: {value}" for key, value in facts.items()) or "Nenhum fato salvo."
        tk.Label(
            card,
            text=text,
            bg=COLORS["panel_alt"],
            fg=COLORS["text"],
            justify="left",
            anchor="nw",
            font=(self.mono_font, 9),
            padx=18,
            pady=18,
        ).pack(fill="both", expand=True)

    def _build_system_page(self) -> None:
        wrapper = self._page_header("Sistema", "Resumo local em tempo real")
        card = RoundedCard(wrapper)
        card.grid(row=1, column=0, sticky="new")
        snap = system_snapshot()
        for label, key in [
            ("Sistema operacional", "os"),
            ("Uptime", "uptime"),
            ("Usuário", "user"),
            ("Hostname", "hostname"),
            ("Shell", "shell"),
            ("CPU", "cpu"),
            ("Memória", "memory"),
            ("Disco /", "disk"),
        ]:
            row = tk.Frame(card, bg=COLORS["panel_alt"])
            row.pack(fill="x", padx=18, pady=8)
            tk.Label(
                row,
                text=label,
                width=20,
                anchor="w",
                bg=COLORS["panel_alt"],
                fg=COLORS["muted"],
                font=(self.ui_font, 9),
            ).pack(side="left")
            tk.Label(
                row,
                text=snap[key],
                anchor="w",
                bg=COLORS["panel_alt"],
                fg=COLORS["text"],
                font=(self.mono_font, 9),
            ).pack(side="left", fill="x", expand=True)

    def _build_settings_page(self) -> None:
        wrapper = self._page_header("Configurações", "Estado efetivo das opções locais")
        card = RoundedCard(wrapper)
        card.grid(row=1, column=0, sticky="new")
        rows = [
            ("Modelo", settings.model),
            ("Nome", settings.assistant_name),
            ("API Gemini", "configurada" if bool(settings.api_key) else "não configurada"),
            ("Memória", "habilitada" if settings.memory_enabled else "desativada"),
            ("Shell", "habilitado" if settings.allow_shell else "desativado"),
            ("Timeout shell", f"{settings.shell_timeout}s"),
        ]
        for label, value in rows:
            row = tk.Frame(card, bg=COLORS["panel_alt"])
            row.pack(fill="x", padx=18, pady=8)
            tk.Label(
                row,
                text=label,
                bg=COLORS["panel_alt"],
                fg=COLORS["muted"],
                width=18,
                anchor="w",
                font=(self.ui_font, 9),
            ).pack(side="left")
            tk.Label(
                row,
                text=value,
                bg=COLORS["panel_alt"],
                fg=COLORS["text"],
                anchor="w",
                font=(self.mono_font, 9),
            ).pack(side="left")

    def _tick_status(self) -> None:
        try:
            snap = system_snapshot()
            for key in ("cpu", "memory", "disk"):
                label = self.system_labels.get(key)
                if label and label.winfo_exists():
                    label.configure(text=snap[key])

            self.tool_rows["shell"].configure(
                text="ativo" if settings.allow_shell else "desativado",
                fg=COLORS["green"] if settings.allow_shell else COLORS["warning"],
            )
            self.tool_rows["memory"].configure(
                text="ativo" if settings.memory_enabled else "desativado",
                fg=COLORS["green"] if settings.memory_enabled else COLORS["warning"],
            )
            self.tool_rows["apps"].configure(
                text="pronto" if shutil.which("gtk-launch") else "parcial",
                fg=COLORS["green"] if shutil.which("gtk-launch") else COLORS["warning"],
            )

            if settings.memory_enabled:
                facts = list_facts()
                self.memory_summary.configure(
                    text=f"Fatos lembrados: {len(facts)}\nPersistência local: ativa",
                    fg=COLORS["text"],
                )
            else:
                self.memory_summary.configure(
                    text="Persistência desativada\n(JARVIS_MEMORY_ENABLED=false)",
                    fg=COLORS["muted"],
                )
        finally:
            self.root.after(2000, self._tick_status)


def run_gui() -> None:
    root = tk.Tk()
    JarvisGUI(root)
    root.mainloop()
