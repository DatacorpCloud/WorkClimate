#!/bin/bash
set -e

# Crea la directory per i log se non esiste
mkdir -p /app/logs

# Crea la directory per il database se non esiste
mkdir -p /app/instance

# Inizializza il database se non esiste
if [ ! -f /app/instance/worklimate.db ]; then
    echo "Inizializzazione del database..."
    python -c "from app import app, db; app.app_context().push(); db.create_all()"
    echo "Database inizializzato."
fi

# Esegui eventuali migrazioni del database
# Se in futuro si implementa Flask-Migrate, decommentare la riga seguente
# python -c "from app import app; from flask_migrate import upgrade; app.app_context().push(); upgrade()"

# Esegui il comando fornito (default: gunicorn)
exec "$@"