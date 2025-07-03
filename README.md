# Clima e Lavoro Portal

**Clima e Lavoro** è una piattaforma web open-source per il monitoraggio delle condizioni meteo critiche legate allo stress da caldo nei luoghi di lavoro all'aperto.  
L’applicazione raccoglie dati pubblici dal portale [Worklimate](https://www.worklimate.it/) (INAIL/CNR), analizza i livelli di rischio per le località associate ai clienti e invia notifiche automatiche per segnalare condizioni critiche nelle fasce orarie più sensibili (es. 12:30–16:00).

> ⚠️ In assenza di API ufficiali, il sistema utilizza mappature dei percorsi web per ottenere i dati, fornendo un supporto proattivo alle aziende in materia di sicurezza sul lavoro.

![Python](https://img.shields.io/badge/Python-3.7%2B-blue)
![Flask](https://img.shields.io/badge/Flask-2.x-lightgrey)
![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)

---

## ✨ Caratteristiche Principali

- **Gestione Clienti**: Aggiunta, modifica ed eliminazione dei clienti con città e contatti
- **Monitoraggio Meteo**: Raccolta automatica dei dati previsionali dal sito Worklimate
- **Report Personalizzati**: Visualizzazione dei livelli di rischio per oggi, domani e dopodomani
- **Notifiche Automatiche**:
  - Email con report meteo personalizzati
  - Inoltro a più destinatari per cliente (supervisori, gruppi)
  - Logo aziendale personalizzabile nel footer del messaggio
  - Notifiche programmate giornalmente alle ore 7:00
- **Scheduler Integrato**:
  - Raccolta automatica dei dati ogni giorno alle 6:00
  - Invio notifiche alle 7:00
- **Interfaccia Web Intuitiva**: Gestione clienti, impostazioni, report e test email da browser

---

## Requisiti

- Python 3.7 o superiore
- Flask e relative dipendenze (vedi `requirements.txt`)
- Connessione internet per il recupero dei dati meteo

## Installazione

1. Clona il repository o scarica i file

2. Crea un ambiente virtuale Python (consigliato)
   ```
   python -m venv venv
   ```

3. Attiva l'ambiente virtuale
   - Windows: `venv\Scripts\activate`
   - Linux/Mac: `source venv/bin/activate`

4. Installa le dipendenze
   ```
   pip install -r requirements.txt
   ```

5. Avvia l'applicazione
   ```
   python app.py
   ```

6. Accedi all'applicazione tramite browser all'indirizzo `http://localhost:5000`

## Struttura del Progetto

```
clima-e-lavoro/
│
├── app.py                 # Applicazione Flask principale
├── meteo.py               # Script per il recupero dei dati meteo
├── meteo2.py              # Script per il recupero dei dati meteo alternativo a meteo.py dopo le mofifiche del 01/07/2025
├── models.py              # Modelli del database
├── scheduler.py           # Gestione dei job automatici
├── config.py              # Configurazioni dell'applicazione
│
├── img/                   # Immagini
│   └── logo-base.png      # Logo per email
│
├── templates/             # Template HTML
│   ├── base.html          # Template base
│   ├── index.html         # Dashboard principale
│   ├── clients.html       # Gestione clienti
│   ├── client_form.html   # Form per aggiunta/modifica clienti
│   ├── reports.html       # Visualizzazione report meteo
│   └── settings.html      # Impostazioni applicazione
│
├── static/                # File statici
│   ├── css/
│   │   └── style.css      # Stili personalizzati
│   └── js/
│       └── main.js        # JavaScript personalizzato
│
└── instance/              # Dati persistenti
    └── worklimate.db      # Database SQLite (creato automaticamente)
```

## Utilizzo

1. **Configurazione Iniziale**:
   - Accedi alla pagina "Impostazioni" e configura i parametri SMTP per l'invio delle email
   - Testa la configurazione email con la funzione "Invia Email di Test"

2. **Gestione Clienti**:
   - Aggiungi i clienti con i relativi dati di contatto e la città di riferimento
   - Aggiungi email aggiuntive per supervisori o gruppi che riceveranno le stesse notifiche
   - Modifica o elimina i clienti esistenti secondo necessità

3. **Sincronizzazione Meteo**:
   - Clicca su "Sincronizza Meteo" per aggiornare manualmente i dati
   - I dati vengono sincronizzati automaticamente ogni giorno alle 6:00

4. **Visualizzazione Report**:
   - Accedi alla pagina "Report" per visualizzare i livelli di rischio per ogni cliente
   - I report sono organizzati per cliente e suddivisi in oggi, domani e dopodomani

5. **Invio Notifiche**:
   - Invia notifiche singole a specifici clienti o a tutti i clienti contemporaneamente
   - Le notifiche vengono inviate automaticamente ogni giorno alle 7:00
   - Le email includono il logo aziendale in fondo al messaggio
   - I report mostrano le date effettive nel formato italiano (gg-mm-aaaa)
   - Le notifiche vengono inviate a tutti gli indirizzi email associati al cliente (principale e aggiuntivi)

## Personalizzazione

- Modifica i file CSS e JavaScript nella cartella `static` per personalizzare l'aspetto e il comportamento dell'applicazione
- Modifica i template HTML nella cartella `templates` per personalizzare la struttura delle pagine
- Modifica il file `config.py` per cambiare le configurazioni dell'applicazione

⚠️ Disclaimer
Questa applicazione accede a dati pubblici forniti da Worklimate tramite mappatura URL.
Non esistono API ufficiali e il progetto non è affiliato con INAIL o CNR.

I dati sono utilizzati a solo scopo informativo e non sostituiscono le comunicazioni ufficiali delle autorità competenti.
Eventuali imprecisioni nei dati previsionali derivano dai modelli meteo pubblici utilizzati da Worklimate


## Licenza
Questo progetto è rilasciato con licenza MIT. Vedi il file LICENSE per i dettagli.
