"""Register this checkout in the Linux application menu and Desktop."""
from pathlib import Path
import shutil
import subprocess

base = Path(__file__).resolve().parent
if not (base / "venv/bin/python").is_file():
    raise SystemExit("Buat venv dan pasang requirements.txt terlebih dahulu.")
launcher = base / "launch.sh"
launcher.chmod(launcher.stat().st_mode | 0o111)
# Escape reserved characters in Desktop Entry Exec arguments.
def quote(value):
    return '"' + str(value).replace('\\', '\\\\').replace('"', '\\"').replace('`', '\\`').replace('$', '\\$').replace('%', '%%') + '"'
entry = ("[Desktop Entry]\nVersion=1.0\nType=Application\nName=ASNkit\n"
         "Comment=Alat PDF dan konversi Markdown\n"
         f"Exec={quote(launcher)}\nIcon={base / 'asnkit.svg'}\n"
         "Terminal=false\nCategories=Office;\n")
menu = Path.home() / ".local/share/applications/ASNkit.desktop"
menu.parent.mkdir(parents=True, exist_ok=True)
menu.write_text(entry, encoding="utf-8")
if shutil.which("xdg-user-dir"):
    desktop = Path(subprocess.check_output(["xdg-user-dir", "DESKTOP"], text=True).strip())
else:
    desktop = Path.home() / "Desktop"
desktop.mkdir(parents=True, exist_ok=True)
shortcut = desktop / "ASNkit.desktop"
shortcut.write_text(entry, encoding="utf-8")
shortcut.chmod(0o755)
if shutil.which("gio"):
    subprocess.run(["gio", "set", str(shortcut), "metadata::trusted", "true"], capture_output=True)
print("Shortcut ASNkit terpasang di menu aplikasi dan Desktop.")
