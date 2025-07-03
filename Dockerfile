# Usa l'immagine ufficiale Ubuntu come base
FROM ubuntu:22.04

# Imposta la directory di lavoro nel container
WORKDIR /app

# Imposta le variabili d'ambiente
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    FLASK_APP=app.py \
    LANG=it_IT.UTF-8 \
    LANGUAGE=it_IT:it \
    LC_ALL=it_IT.UTF-8 \
    DEBIAN_FRONTEND=noninteractive

# Installa le dipendenze di sistema necessarie
RUN DEBIAN_FRONTEND=noninteractive apt-get update && apt-get install -y --no-install-recommends \
    python3 \
    python3-pip \
    python3-dev \
    build-essential \
    gcc \
    curl \
    locales \
    tzdata \
    && echo "it_IT.UTF-8 UTF-8" > /etc/locale.gen \
    && locale-gen \
    && update-locale LANG=it_IT.UTF-8 \
    # Configura il fuso orario per l'Italia
    && ln -fs /usr/share/zoneinfo/Europe/Rome /etc/localtime \
    && dpkg-reconfigure -f noninteractive tzdata \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Installa le dipendenze Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install gunicorn

# Copia lo script di entrypoint e rendilo eseguibile
COPY docker-entrypoint.sh .
RUN chmod +x docker-entrypoint.sh

# Copia tutto il resto del codice
COPY . .

# Crea directory necessarie
RUN mkdir -p instance logs

# Espone la porta
EXPOSE 5000

# Imposta lo script di entrypoint
ENTRYPOINT ["/app/docker-entrypoint.sh"]

# Comando di default per Gunicorn in produzione
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "4", "--timeout", "120", "app:app"]
