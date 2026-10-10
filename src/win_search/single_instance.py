import sys
import threading
from typing import Callable, Optional

class SingleInstanceManager:
    """
    Guarantees that only one instance of win-search runs at any time.
    If a secondary instance is launched:
    - Signals the primary instance to wake up and show its search bar.
    - Exits immediately with exit code 0.
    """
    MUTEX_NAME = "Local\\WinSearch_Instance_Mutex"
    EVENT_NAME = "Local\\WinSearch_WakeUp_Event"

    def __init__(self):
        self._mutex_handle = None
        self._event_handle = None
        self._listener_thread: Optional[threading.Thread] = None
        self._is_running = True

    def check_or_wake_existing(self) -> bool:
        """
        Returns True if this is the primary (first) instance.
        If another instance is already running, signals it to wake up and exits immediately.
        """
        if sys.platform != "win32":
            return True

        import ctypes
        kernel32 = ctypes.windll.kernel32

        # Attempt to create the instance mutex
        self._mutex_handle = kernel32.CreateMutexW(None, True, self.MUTEX_NAME)
        last_error = kernel32.GetLastError()

        if last_error == 183:  # ERROR_ALREADY_EXISTS
            # Another instance is already running!
            EVENT_MODIFY_STATE = 0x0002
            event = kernel32.OpenEventW(EVENT_MODIFY_STATE, False, self.EVENT_NAME)
            if event:
                kernel32.SetEvent(event)
                kernel32.CloseHandle(event)

            if self._mutex_handle:
                kernel32.CloseHandle(self._mutex_handle)
                self._mutex_handle = None

            # Clean silent exit for secondary process
            sys.exit(0)

        # Primary instance: create auto-reset event for wake-up signals
        self._event_handle = kernel32.CreateEventW(None, False, False, self.EVENT_NAME)
        return True

    def start_wake_listener(self, on_wake: Callable[[], None]) -> None:
        """Starts a 0% CPU background thread listening for wake-up signals from secondary instances."""
        if sys.platform != "win32" or not self._event_handle:
            return

        import ctypes
        kernel32 = ctypes.windll.kernel32

        def _listen():
            INFINITE = 0xFFFFFFFF
            WAIT_OBJECT_0 = 0x00000000
            while self._is_running and self._event_handle:
                res = kernel32.WaitForSingleObject(self._event_handle, INFINITE)
                if not self._is_running:
                    break
                if res == WAIT_OBJECT_0:
                    try:
                        on_wake()
                    except Exception:
                        pass

        self._listener_thread = threading.Thread(target=_listen, daemon=True, name="WakeUpListener")
        self._listener_thread.start()

    def cleanup(self) -> None:
        """Releases mutex and event handles on process exit."""
        if sys.platform != "win32":
            return
        self._is_running = False
        import ctypes
        kernel32 = ctypes.windll.kernel32
        if self._event_handle:
            kernel32.SetEvent(self._event_handle)
            kernel32.CloseHandle(self._event_handle)
            self._event_handle = None
        if self._mutex_handle:
            kernel32.ReleaseMutex(self._mutex_handle)
            kernel32.CloseHandle(self._mutex_handle)
            self._mutex_handle = None
