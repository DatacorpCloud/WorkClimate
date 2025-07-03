# Worklimate - Guida Docker

Questa guida spiega come eseguire l'applicazione Worklimate utilizzando Docker.

## Prerequisiti

- [Docker](https://www.docker.com/get-started) installato sul sistema
- [Docker Compose](https://docs.docker.com/compose/install/) installato sul sistema

## Configurazione

### Variabili d'ambiente

Le variabili d'ambiente possono essere configurate nel file `docker-compose.yml` nella sezione `environment`. Le principali variabili sono:

- `SECRET_KEY`: Chiave segreta per la sicurezza dell'applicazione
- `DATABASE_URL`: URL del database (predefinito: SQLite)
- `FLASK_ENV`: Ambiente di esecuzione (`development` o `production`)

Le configurazioni email possono essere impostate tramite variabili d'ambiente o tramite l'interfaccia utente dell'applicazione:

```yaml
- MAIL_SERVER=smtp.example.com
- MAIL_PORT=587
- MAIL_USE_TLS=True
- MAIL_USERNAME=user@example.com
- MAIL_PASSWORD=password
- MAIL_DEFAULT_SENDER=noreply@example.com
```

## Avvio dell'applicazione

### Prima esecuzione

1. Clona il repository e naviga nella directory del progetto
2. Costruisci e avvia il container:

```bash
docker-compose up --build
```

### Esecuzioni successive

Per avviare l'applicazione:

```bash
docker-compose up
```

Per eseguire in background:

```bash
docker-compose up -d
```

### Accesso all'applicazione

L'applicazione sarà disponibile all'indirizzo: [http://localhost:5000](http://localhost:5000)

## Gestione del database

Il database SQLite viene salvato nella directory `instance/` che è montata come volume nel container. Questo garantisce la persistenza dei dati anche quando il container viene riavviato.

## Log

I log dell'applicazione vengono salvati nella directory `logs/` che è montata come volume nel container.

## Arresto dell'applicazione

Per arrestare l'applicazione:

```bash
docker-compose down
```

## Ricostruzione dell'immagine

Se vengono apportate modifiche al codice o alle dipendenze, è necessario ricostruire l'immagine Docker:

```bash
docker-compose build
```

o

```bash
docker-compose up --build
```

## Modalità di sviluppo

Per eseguire l'applicazione in modalità di sviluppo, modifica la variabile `FLASK_ENV` in `docker-compose.yml`:

```yaml
environment:
  - FLASK_ENV=development
```

E modifica il comando nel `docker-compose.yml` per utilizzare il server di sviluppo di Flask invece di Gunicorn:

```yaml
command: python app.py
```

## Risoluzione dei problemi

### Visualizzazione dei log

Per visualizzare i log del container:

```bash
docker-compose logs -f
```

### Accesso al container

Per accedere al container in esecuzione:

```bash
docker-compose exec app bash
```

### Problemi di permessi

Se si verificano problemi di permessi con i file nella directory `instance/` o `logs/`, eseguire:

```bash
chmod -R 777 instance/ logs/
```