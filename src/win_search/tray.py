from typing import Callable
from PIL import Image, ImageDraw
import pystray
from pystray import MenuItem as item

def create_tray_image() -> Image.Image:
    """Draws a clean 64x64 search lens in RAM matching our Raycast accent color (#ff6363)."""
    image = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    # Magnifying lens circle
    draw.ellipse((10, 10, 42, 42), outline="#ff6363", width=6)
    # Lens handle
    draw.line((35, 35, 52, 52), fill="#ff6363", width=7)
    return image

class TrayIcon:
    """
    Manages the Windows taskbar notification tray icon, double-click launch,
    and context menu actions.
    """
    def __init__(
        self,
        on_show: Callable[[], None],
        on_refresh: Callable[[], None],
        on_exit: Callable[[], None]
    ):
        self.on_show = on_show
        self.on_refresh = on_refresh
        self.on_exit = on_exit

        # default=True means double-clicking the tray icon triggers this action
        menu = (
            item("Show Win-Search", self._on_show_clicked, default=True),
            item("Refresh Index", self._on_refresh_clicked),
            pystray.Menu.SEPARATOR,
            item("Exit", self._on_exit_clicked),
        )

        self.icon = pystray.Icon(
            name="WinSearch",
            icon=create_tray_image(),
            title="Win-Search (Ctrl+Space)",
            menu=menu
        )

    def _on_show_clicked(self, icon=None, item=None) -> None:
        self.on_show()

    def _on_refresh_clicked(self, icon=None, item=None) -> None:
        self.on_refresh()

    def _on_exit_clicked(self, icon=None, item=None) -> None:
        self.stop()
        self.on_exit()

    def start(self) -> None:
        """Starts the tray icon on a background worker thread."""
        self.icon.run_detached()

    def stop(self) -> None:
        """Removes the icon from the Windows notification area."""
        self.icon.stop()
