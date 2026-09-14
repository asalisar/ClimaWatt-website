# ClimaWatt — sito

Sito Flask di ClimaWatt: analisi del legame tra clima, domanda elettrica e
produzione energetica in Italia nel 2025, con dashboard e (a breve)
dashboard Tableau incorporate.

Questo repository contiene **solo il codice del sito** (l'app Flask che
lo serve), pensato per essere collegato direttamente a una piattaforma
di hosting come Render per la pubblicazione. Il database, gli script di
importazione dati (`database.py`, `insert_data.py`) e i dataset vivono
nel repository di sviluppo `ClimaWatt` (privato).

## Struttura

```
src/
  __init__.py
  app/
    __init__.py       # create_app(): configura Flask e registra le route
    db.py              # connessione al database e query helper condivisi
    utils.py           # helper per intervalli di date e gestione errori
    routes/
      main.py          # home page e /api-status
      meteo.py          # temperatura, vento, radiazione
      grafici.py        # grafici generati con matplotlib
      domanda.py        # domanda elettrica per bidding zone
      produzione.py      # produzione energetica per fonte
      capacita.py        # capacità installata
      incroci.py          # analisi incrociate meteo + energia
templates/, static/   # frontend del sito
wsgi.py                # entry point per l'esecuzione/deploy
```

## Avvio in locale

1. Installa le dipendenze:

   ```
   pip install -r requirements.txt
   ```

2. Copia `.env.example` in `.env` e inserisci le credenziali del
   database MySQL (le stesse usate per popolare i dati con il repo
   `ClimaWatt`):

   ```
   DB_HOST=...
   DB_PORT=...
   DB_USER=...
   DB_PASSWORD=...
   DB_NAME=...
   ```

   `.env` è ignorato da git: non va mai commitato.

3. Avvia il sito:

   ```
   python wsgi.py
   ```

   Il sito è disponibile su `http://127.0.0.1:5000`.

## Deploy pubblico (Render)

1. Crea un nuovo **Web Service** su [Render](https://render.com)
   collegato a questo repository GitHub.
2. Build command: `pip install -r requirements.txt`
3. Start command: `gunicorn wsgi:app`
4. Imposta le variabili d'ambiente `DB_HOST`, `DB_PORT`, `DB_USER`,
   `DB_PASSWORD`, `DB_NAME` nel pannello "Environment" di Render — mai
   nel repository.

Ogni push su questo repository aggiorna automaticamente il sito online.

## Dashboard Tableau

La sezione "Tableau" del sito (`templates/index.html`, `#tableau`) mostra
un placeholder finché non viene pubblicata una viz. Per collegarla:

1. Pubblica la dashboard su Tableau Public (o Tableau Server).
2. Copia il link "Condividi" della viz.
3. Incollalo nell'attributo `data-url` del div `#tableauViz` in
   `templates/index.html`.

`static/script.js` carica automaticamente l'embed quando `data-url` è
presente.

## Sicurezza

Le credenziali del database **non devono mai** essere scritte nel
codice: tutti i moduli in `src/app/` leggono le credenziali da variabili
d'ambiente (`.env` in locale, variabili d'ambiente della piattaforma di
hosting in produzione) — vale sia qui che nel repository privato.
