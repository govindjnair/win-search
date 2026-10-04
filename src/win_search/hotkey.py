import threading
from typing import Callable, Optional
from pynput import keyboard

class HotkeyManager:
    """
    Manages a global hotkey listener running on a background daemon thread.
    Invokes a callback whenever the specified hotkey combo is pressed.
    """
    def __init__(self, hotkey_str: str, on_triggered: Callable[[], None]):
        self.hotkey_str = hotkey_str
        self.on_triggered = on_triggered
        self._listener: Optional[keyboard.GlobalHotKeys] = None

    def start(self) -> None:
        if self._listener is not None:
            return

        self._listener = keyboard.GlobalHotKeys({
            self.hotkey_str: self.on_triggered
        })
        self._listener.daemon = True
        self._listener.start()

    def stop(self) -> None:
        if self._listener:
            self._listener.stop()
            self._listener = None
