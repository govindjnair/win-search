from typing import Callable
from PIL import Image, ImageDraw
import pystray
from pystray import MenuItem as item

def create_tray_image() -> Image.Image:
    """Loads bundled tray_icon.png if available, or renders a bold in-memory glyph."""
    try:
        import sys
        from pathlib import Path
        if getattr(sys, "frozen", False):
            base_dir = getattr(sys, "_MEIPASS", Path(sys.executable).parent)
        else:
            base_dir = Path(__file__).resolve().parents[2]
        icon_path = Path(base_dir) / "assets" / "tray_icon.png"
        if icon_path.exists():
            return Image.open(str(icon_path))
    except Exception:
        pass

    # High-quality supersampled fallback glyph filling the 64x64 canvas
    s = 256
    img = Image.new("RGBA", (s, s), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    coral = (255, 99, 99, 255)
    cx, cy = s * 0.40, s * 0.40
    r = s * 0.28
    lw = int(s * 0.08)
    draw.ellipse([cx - r, cy - r, cx + r, cy + r], outline=coral, width=lw)
    draw.line([(cx + r * 0.70, cy + r * 0.70), (cx + r * 1.85, cy + r * 1.85)], fill=coral, width=int(lw * 1.15))
    return img.resize((64, 64), Image.Resampling.LANCZOS)

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
