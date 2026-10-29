"""Riscatta i reward gratuiti su gemma.cards e avvisa quando i coin bastano per una busta.

Installazione (Linux, macOS, Windows):  python3 gemma.py --install   (su Windows: py gemma.py --install)
Sessione scaduta:                      python3 gemma.py --login
"""
import os
import plistlib
import re
import shutil
import subprocess
import sys
import venv
from pathlib import Path

BASE = "https://www.gemma.cards"
HERE = Path(__file__).resolve().parent
SCRIPT = HERE / "gemma.py"
PROFILE = HERE / "profile"
WIN, MAC = sys.platform == "win32", sys.platform == "darwin"
VENV_PY = HERE / ".venv" / ("Scripts/python.exe" if WIN else "bin/python")
# ponytail: prezzo busta più economica hardcoded (500 coin a ott 2026), scrapare /packs se cambia spesso
MIN_PACK = 500


def notify(msg):
    print(msg)
    if WIN:
        import ctypes
        ctypes.windll.user32.MessageBoxW(0, msg, "Gemma Cards", 0x40000)  # 0x40000 = in primo piano
    elif MAC:
        subprocess.run(["osascript", "-e", "on run argv", "-e",
                        'display notification (item 1 of argv) with title "Gemma Cards"', "-e", "end run", msg])
    else:
        subprocess.run(["notify-send", "-a", "Gemma", "Gemma Cards", msg], check=False)


def find_chrome():
    candidates = ["google-chrome", "google-chrome-stable",
                  "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
                  *(os.path.join(os.environ.get(v, ""), "Google", "Chrome", "Application", "chrome.exe")
                    for v in ("PROGRAMFILES", "PROGRAMFILES(X86)", "LOCALAPPDATA"))]
    for c in candidates:
        if found := shutil.which(c):
            return found
    sys.exit("Google Chrome non trovato: installalo e riprova.")


def login():
    # Chrome normale, non pilotato: Google blocca il login nei browser automatizzati.
    # password-store=basic (Linux) e use-mock-keychain (Mac) = stessa cifratura cookie che usa Playwright.
    print("Fai login nella finestra di Chrome, poi chiudila.")
    subprocess.run([find_chrome(), f"--user-data-dir={PROFILE}", "--password-store=basic",
                    "--use-mock-keychain", "--no-first-run", f"{BASE}/account"])


def schedule():
    """Ogni giorno alle 09:00; se a quell'ora il PC era spento, appena l'utente entra."""
    if WIN:
        pyw = VENV_PY.with_name("pythonw.exe")  # niente finestra console
        subprocess.run(["powershell", "-NoProfile", "-Command",
                        f"Register-ScheduledTask -TaskName Gemma -Force"
                        f" -Action (New-ScheduledTaskAction -Execute '{pyw}' -Argument '\"{SCRIPT}\"' -WorkingDirectory '{HERE}')"
                        f" -Trigger (New-ScheduledTaskTrigger -Daily -At 9am)"
                        f" -Settings (New-ScheduledTaskSettingsSet -StartWhenAvailable)"], check=True)
    elif MAC:
        plist = Path.home() / "Library/LaunchAgents/cards.gemma.daily.plist"
        plist.parent.mkdir(parents=True, exist_ok=True)
        # launchd non recupera i run persi a PC spento: RunAtLoad lo fa partire al login
        plist.write_bytes(plistlib.dumps({
            "Label": "cards.gemma.daily", "ProgramArguments": [str(VENV_PY), str(SCRIPT)],
            "WorkingDirectory": str(HERE), "StartCalendarInterval": {"Hour": 9, "Minute": 0}, "RunAtLoad": True}))
        subprocess.run(["launchctl", "unload", plist], capture_output=True)
        subprocess.run(["launchctl", "load", plist], check=True)
    else:
        units = Path.home() / ".config/systemd/user"
        units.mkdir(parents=True, exist_ok=True)
        (units / "gemma.service").write_text(
            "[Unit]\nDescription=Gemma Cards daily reward\n\n"
            f'[Service]\nType=oneshot\nWorkingDirectory={HERE}\nExecStart="{VENV_PY}" "{SCRIPT}"\n')
        (units / "gemma.timer").write_text(
            "[Unit]\nDescription=Gemma Cards daily reward\n\n"
            "[Timer]\nOnCalendar=*-*-* 09:00\nPersistent=true\n\n[Install]\nWantedBy=timers.target\n")
        subprocess.run(["systemctl", "--user", "daemon-reload"], check=True)
        subprocess.run(["systemctl", "--user", "enable", "--now", "gemma.timer"], check=True)


def install():
    print("Preparo l'ambiente Python...")
    if not VENV_PY.exists():
        venv.create(HERE / ".venv", with_pip=True)
    subprocess.run([VENV_PY, "-m", "pip", "install", "-q", "playwright"], check=True)
    login()
    subprocess.run([VENV_PY, SCRIPT])  # primo riscatto subito
    schedule()
    print("Fatto: gira da solo ogni giorno alle 09:00.")


def claim():
    from playwright.sync_api import sync_playwright

    with sync_playwright() as p:
        ctx = p.chromium.launch_persistent_context(PROFILE, channel="chrome", headless=True)
        page = ctx.pages[0] if ctx.pages else ctx.new_page()
        page.goto(f"{BASE}/rewards")
        # saldo mostra "—" finché non carica; da loggati compare un numero
        coins_btn = page.get_by_role("button", name=re.compile("Gemma coins")).filter(has_text=re.compile(r"\d"))
        try:
            coins_btn.wait_for(timeout=15000)
        except Exception:
            pass
        if not page.locator('header a[href="/account"]').count():
            notify("Sessione scaduta: rilancia `gemma.py --login`")
            sys.exit(1)

        # API diretta invece dei bottoni: la lista reward carica dopo il saldo, i bottoni arrivavano tardi
        claimed = 0
        for kind in ("daily", "weekly"):
            r = page.request.post(f"{BASE}/api/rewards/claim", data={"kind": kind})
            if r.ok:
                claimed += 1
                print(f"{kind}: +{r.json().get('coins')}")
            elif r.status != 409:  # 409 = già riscattato in questo periodo
                notify(f"Claim {kind} fallito: HTTP {r.status} {r.text()[:200]}")

        page.reload()
        coins_btn.wait_for()
        coins = int(re.sub(r"\D", "", coins_btn.inner_text()) or 0)
        ctx.close()

    print(f"Riscattati {claimed} reward, saldo {coins} coin")
    if coins >= MIN_PACK:
        notify(f"Puoi sbustare! Hai {coins} coin (busta da {MIN_PACK}).")


if __name__ == "__main__":
    if "--install" in sys.argv:
        install()
    elif "--login" in sys.argv:
        login()
    else:
        try:
            claim()
        except Exception as e:  # su Mac/Windows non c'è un log da guardare: meglio una notifica
            notify(f"Errore: {e}")
            raise
