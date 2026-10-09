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

    # 6. Start global hotkey listener (<alt>+<space>)
    hotkey = HotkeyManager("<ctrl>+<space>", on_hotkey_pressed)
    hotkey.start()

    # 7. Start with the launcher visible so you can test it right away
    ui.show()

    print("🚀 Win-Search is running!")
    print("👉 Press <Ctrl>+<Space> globally to toggle the launcher.")
    print("👉 Press <Escape> to dismiss.")
    print("👉 Press Ctrl+C in terminal to exit.")

    try:
        root.mainloop()
    except KeyboardInterrupt:
        pass
    finally:
        hotkey.stop()

if __name__ == "__main__":
    main()
