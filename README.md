# gemma-daily

Riscatta da solo, ogni giorno, i coin gratuiti di [gemma.cards](https://www.gemma.cards/rewards) (daily e weekly) e ti manda una notifica quando ne hai abbastanza per aprire una busta (500 coin).

Funziona su **Windows**, **macOS** e **Linux**.

## Cosa serve
- **Google Chrome** installato
- **Python 3**:
  - Windows: installalo dal [Microsoft Store](https://apps.microsoft.com/search?query=python) (cerca "Python 3.12"), oppure da [python.org](https://www.python.org/downloads/) spuntando **"Add python.exe to PATH"**
  - macOS: al primo `python3` nel Terminale il Mac propone di installarlo da solo: accetta
  - Linux: di solito c'è già (su Ubuntu/Debian serve anche `sudo apt install python3-venv`)

## Installazione
1. In alto su questa pagina premi **Code → Download ZIP** ed estrai la cartella dove vuoi tenerla (es. Documenti).
2. Apri un terminale **dentro la cartella**:
   - Windows: apri la cartella, clic sulla barra dell'indirizzo, scrivi `cmd` e premi Invio
   - macOS: tasto destro sulla cartella → Servizi → **Nuovo Terminale nella cartella**
   - Linux: tasto destro → **Apri nel terminale**
3. Lancia:
   - Windows: `py gemma.py --install`
   - macOS / Linux: `python3 gemma.py --install`
4. Si apre Chrome sulla pagina di gemma.cards: **fai login** e poi **chiudi la finestra di Chrome**.

Finito. Il primo riscatto lo fa subito, poi gira da solo ogni giorno alle 09:00. Se a quell'ora il PC è spento, parte appena accedi.

## Da sapere
- **Sessione scaduta?** Arriva una notifica: rilancia il comando del punto 3 con `--login` al posto di `--install`.
- **Non spostare la cartella** dopo l'installazione. Se la sposti, rilancia `--install` dalla nuova posizione.
- **Non condividere la cartella `profile/`**: contiene il tuo login a gemma.cards.
- I coin sono tuoi, lo script fa solo quello che faresti tu premendo "Claim" ogni giorno.

## Disinstallare
- Windows: `schtasks /delete /tn Gemma /f`
- macOS: `launchctl unload ~/Library/LaunchAgents/cards.gemma.daily.plist && rm ~/Library/LaunchAgents/cards.gemma.daily.plist`
- Linux: `systemctl --user disable --now gemma.timer`

Poi cancella la cartella.
