import os
import sys
import ctypes
import subprocess
import tkinter as tk
from tkinter import font
from typing import List, Optional, Callable
from .search_interface import SearchResult, SearchEngine

class SearchUI:
    """
    Frameless, dark-mode search bar UI with live results and arrow-key navigation.
    """
    def __init__(self, root: tk.Tk, search_engine: SearchEngine):
        self.root = root
        self.search_engine = search_engine
        self.is_visible = False
        self.current_results: List[SearchResult] = []

        # Color Palette (Dark Theme / Catppuccin inspired)
        self.BG_COLOR = "#1e1e2e"
        self.INPUT_BG = "#2b2b3b"
        self.FG_COLOR = "#cdd6f4"
        self.MUTED_COLOR = "#a6adc8"
        self.ACCENT_COLOR = "#89b4fa"
        self.SEL_BG = "#45475a"
        self.SEL_FG = "#ffffff"
        self.BORDER_COLOR = "#313244"

        self._configure_window()
        self._create_widgets()
        self._bind_events()

        # Initial search with empty query to preload defaults
        self._update_results("")

    def _get_dpi_scale(self) -> float:
        if sys.platform == "win32":
            try:
                dpi = ctypes.windll.user32.GetDpiForSystem()
                return dpi / 96.0
            except Exception:
                try:
                    hdc = ctypes.windll.user32.GetDC(0)
                    dpi = ctypes.windll.gdi32.GetDeviceCaps(hdc, 88)
                    ctypes.windll.user32.ReleaseDC(0, hdc)
                    return dpi / 96.0
                except Exception:
                    pass
        return 1.0

    def _configure_window(self) -> None:
        self.scale = self._get_dpi_scale()
        self.root.overrideredirect(True)          # Frameless (no titlebar/borders)
        self.root.attributes("-topmost", True)     # Float above all windows
        self.root.attributes("-alpha", 0.94)       # Sleek semi-transparency (0.0 invisible, 1.0 opaque)
        self.root.configure(bg=self.BG_COLOR)

        self.width = int(1050 * self.scale)
        self.compact_height = int(70 * self.scale)
        self.expanded_height = int(470 * self.scale)

        screen_w = self.root.winfo_screenwidth()
        screen_h = self.root.winfo_screenheight()
        self.win_x = (screen_w - self.width) // 2
        self.win_y = int(screen_h * 0.18)

        # Start in compact single-bar mode
        self.is_expanded = False
        self.root.geometry(f"{self.width}x{self.compact_height}+{self.win_x}+{self.win_y}")

    def _create_widgets(self) -> None:
        self.pad_x = int(14 * self.scale)
        self.pad_y = int(10 * self.scale)
        border_w = max(2, int(2 * self.scale))

        # Outer Border Frame
        self.outer_frame = tk.Frame(
            self.root,
            bg=self.BG_COLOR,
            highlightbackground=self.BORDER_COLOR,
            highlightthickness=border_w
        )
        self.outer_frame.pack(fill=tk.BOTH, expand=True)

        # Search Input Container
        search_container = tk.Frame(self.outer_frame, bg=self.INPUT_BG, padx=self.pad_x, pady=int(8 * self.scale))
        search_container.pack(fill=tk.X, padx=self.pad_x, pady=self.pad_y)

        # Search Icon Label
        self.icon_label = tk.Label(
            search_container,
            text="🔍",
            font=("Segoe UI", max(10, int(11 * self.scale))),
            bg=self.INPUT_BG,
            fg=self.MUTED_COLOR
        )
        self.icon_label.pack(side=tk.LEFT, padx=(0, int(8 * self.scale)))

        # Search Query Entry
        self.query_var = tk.StringVar()
        self.query_var.trace_add("write", self._on_query_changed)

        self.entry = tk.Entry(
            search_container,
            textvariable=self.query_var,
            font=("Segoe UI", max(12, int(13 * self.scale))),
            bg=self.INPUT_BG,
            fg=self.FG_COLOR,
            insertbackground=self.ACCENT_COLOR,
            relief="flat",
            borderwidth=0
        )
        self.entry.pack(side=tk.LEFT, fill=tk.X, expand=True)

        # Divider line (packed dynamically when expanded)
        self.divider = tk.Frame(self.outer_frame, bg=self.BORDER_COLOR, height=1)

        # Results Listbox (packed dynamically when expanded)
        self.results_listbox = tk.Listbox(
            self.outer_frame,
            font=("Segoe UI", max(9, int(10 * self.scale))),
            bg=self.BG_COLOR,
            fg=self.FG_COLOR,
            selectbackground=self.SEL_BG,
            selectforeground=self.SEL_FG,
            selectborderwidth=0,
            relief="flat",
            borderwidth=0,
            highlightthickness=0,
            activestyle="none"
        )

        # Bottom Hint Bar (packed dynamically when expanded)
        self.hint_bar = tk.Frame(self.outer_frame, bg=self.BG_COLOR, padx=self.pad_x, pady=int(6 * self.scale))

        hint_label = tk.Label(
            self.hint_bar,
            text="↑ / ↓ navigate   •   ↵ launch   •   esc dismiss",
            font=("Segoe UI", max(8, int(9 * self.scale))),
            bg=self.BG_COLOR,
            fg=self.MUTED_COLOR
        )
        hint_label.pack(side=tk.RIGHT)

    def _set_expanded(self, expand: bool) -> None:
        """Expands window to show results or collapses to a single search bar."""
        if self.is_expanded == expand:
            return
        self.is_expanded = expand

        if expand:
            self.root.geometry(f"{self.width}x{self.expanded_height}+{self.win_x}+{self.win_y}")
            self.divider.pack(fill=tk.X, padx=self.pad_x, pady=int(6 * self.scale))
            self.hint_bar.pack(fill=tk.X, side=tk.BOTTOM, padx=self.pad_x, pady=int(6 * self.scale))
            self.results_listbox.pack(fill=tk.BOTH, expand=True, padx=self.pad_x, pady=(0, int(6 * self.scale)))
        else:
            self.results_listbox.pack_forget()
            self.divider.pack_forget()
            self.hint_bar.pack_forget()
            self.root.geometry(f"{self.width}x{self.compact_height}+{self.win_x}+{self.win_y}")

    def _bind_events(self) -> None:
        # Virtual event for thread-safe hotkey toggle
        self.root.bind("<<ToggleLauncher>>", lambda e: self.toggle())

        # Keyboard shortcuts
        self.root.bind("<Escape>", lambda e: self.hide())

        # Arrow navigation intercepted directly in the Entry widget
        self.entry.bind("<Down>", self._on_arrow_down)
        self.entry.bind("<Up>", self._on_arrow_up)
        self.entry.bind("<Return>", self._on_enter_pressed)

        # Double click on item launches it
        self.results_listbox.bind("<Double-Button-1>", lambda e: self.launch_selected())

    def _on_query_changed(self, *args) -> None:
        query = self.query_var.get()
        self._update_results(query)

    def _update_results(self, query: str) -> None:
        trimmed = query.strip()
        if not trimmed:
            self.current_results = []
            self.results_listbox.delete(0, tk.END)
            self._set_expanded(False)
            return

        self.current_results = self.search_engine.search(trimmed, limit=7)
        self.results_listbox.delete(0, tk.END)

        if not self.current_results:
            self._set_expanded(False)
            return

        self._set_expanded(True)
        for res in self.current_results:
            self.results_listbox.insert(tk.END, f"  {res.display_text()}")

        self.results_listbox.selection_clear(0, tk.END)
        self.results_listbox.selection_set(0)
        self.results_listbox.activate(0)


    def _on_arrow_down(self, event) -> str:
        count = self.results_listbox.size()
        if count == 0:
            return "break"
        selected = self.results_listbox.curselection()
        next_idx = (selected[0] + 1) if selected else 0
        if next_idx >= count:
            next_idx = count - 1

        self.results_listbox.selection_clear(0, tk.END)
        self.results_listbox.selection_set(next_idx)
        self.results_listbox.see(next_idx)
        return "break"

    def _on_arrow_up(self, event) -> str:
        count = self.results_listbox.size()
        if count == 0:
            return "break"
        selected = self.results_listbox.curselection()
        prev_idx = (selected[0] - 1) if selected else 0
        if prev_idx < 0:
            prev_idx = 0

        self.results_listbox.selection_clear(0, tk.END)
        self.results_listbox.selection_set(prev_idx)
        self.results_listbox.see(prev_idx)
        return "break"

    def _on_enter_pressed(self, event) -> str:
        self.launch_selected()
        return "break"

    def launch_selected(self) -> None:
        selected = self.results_listbox.curselection()
        if not selected or selected[0] >= len(self.current_results):
            return

        item = self.current_results[selected[0]]
        self.hide()

        try:
            # On Windows: os.startfile natively launches executables, files, and folders
            if hasattr(os, "startfile"):
                os.startfile(item.path)
            else:
                # Fallback for Linux/WSL testing
                subprocess.Popen(["xdg-open", item.path])
        except Exception as e:
            print(f"Error launching '{item.path}': {e}")

    def show(self) -> None:
        self.root.deiconify()
        self.root.lift()
        self.root.focus_force()
        self.entry.focus_set()
        self.entry.select_range(0, tk.END)
        self.is_visible = True

    def hide(self) -> None:
        self.root.withdraw()
        self.is_visible = False
        self.query_var.set("")

    def toggle(self) -> None:
        if self.is_visible:
            self.hide()
        else:
            self.show()
