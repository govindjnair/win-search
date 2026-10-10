import os
import sys
import signal
import ctypes
import tkinter as tk
from .search_interface import SearchEngine
# from .mock_search import MockSearchEngine
from .c_search import CSearchEngine
from .ui import SearchUI
from .hotkey import HotkeyManager
from .tray import TrayIcon

def enable_high_dpi_awareness() -> None:
    """Make Tkinter crisp and sharp on Windows high-DPI displays."""
    if sys.platform == "win32":
        try:
            # Per-monitor DPI awareness (Windows 8.1+)
            ctypes.windll.shcore.SetProcessDpiAwareness(2)
        except Exception:
            try:
                # Fallback for Windows Vista/7/8
                ctypes.windll.user32.SetProcessDPIAware()
            except Exception:
                pass

def main() -> None:
    # 1. Enable crisp rendering before creating the Tk instance
    enable_high_dpi_awareness()

    root = tk.Tk()

    # 2. Allow Ctrl+C in terminal to instantly close Tkinter
    def check_signals() -> None:
        root.after(200, check_signals)

    def handle_sigint(*args) -> None:
        try:
            tray.stop()
        except Exception:
            pass
        root.destroy()
        sys.exit(0)

    signal.signal(signal.SIGINT, handle_sigint)
    root.after(200, check_signals)

    # 3. Initialize backend (starts with mock, we will replace this with C engine!)
    # search_engine: SearchEngine = MockSearchEngine()
    search_engine: SearchEngine = CSearchEngine()

    # 4. Initialize UI
    ui = SearchUI(root, search_engine)

    # 5. Thread-safe hotkey callback: posts a virtual event into Tkinter's queue
    def on_hotkey_pressed() -> None:
        try:
            root.event_generate("<<ToggleLauncher>>", when="tail")
        except Exception:
            pass

    # 6. Start global hotkey listener (<ctrl>+<space>)
    hotkey = HotkeyManager("<ctrl>+<space>", on_hotkey_pressed)
    hotkey.start()

    # 7. Start System Tray icon
    def on_tray_show() -> None:
        root.after(0, ui.show)

    def on_tray_refresh() -> None:
        search_engine._start_background_refresh()

    def on_tray_exit() -> None:
        root.after(0, root.destroy)

    tray = TrayIcon(on_tray_show, on_tray_refresh, on_tray_exit)
    tray.start()

    # 8. Start with the launcher visible so you can test it right away
    ui.show()

    print("🚀 Win-Search is running!")
    print("👉 Press <Ctrl>+<Space> globally to toggle the launcher.")
    print("👉 Press <Escape> to dismiss.")
    print("👉 Check the System Tray (near clock) to access the menu or exit.")
    print("👉 Press Ctrl+C in terminal to exit.")

    try:
        root.mainloop()
    except KeyboardInterrupt:
        pass
    finally:
        hotkey.stop()
        tray.stop()

if __name__ == "__main__":
    main()
