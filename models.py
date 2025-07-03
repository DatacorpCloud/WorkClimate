from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, date

# Inizializzazione del database (verrà configurato in app.py)
db = SQLAlchemy()

class Client(db.Model):
    __tablename__ = 'clients'
    
    id = db.Column(db.Integer, primary_key=True)
    company_name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), nullable=False)  # Manteniamo questo campo per retrocompatibilità
    phone = db.Column(db.String(20))
    city = db.Column(db.String(100), nullable=False)
    
    # Relazione con i report meteo
    weather_reports = db.relationship('WeatherReport', backref='client', lazy=True, cascade='all, delete-orphan')
    
    # Relazione con le email aggiuntive
    emails = db.relationship('ClientEmail', backref='client', lazy=True, cascade='all, delete-orphan')
    
    def __repr__(self):
        return f"<Client {self.company_name}>"

class ClientEmail(db.Model):
    __tablename__ = 'client_emails'
    
    id = db.Column(db.Integer, primary_key=True)
    client_id = db.Column(db.Integer, db.ForeignKey('clients.id'), nullable=False)
    email = db.Column(db.String(100), nullable=False)
    is_primary = db.Column(db.Boolean, default=False)  # Indica se è l'email principale
    
    def __repr__(self):
        return f"<ClientEmail {self.email}>"

class WeatherReport(db.Model):
    __tablename__ = 'weather_reports'
    
    id = db.Column(db.Integer, primary_key=True)
    client_id = db.Column(db.Integer, db.ForeignKey('clients.id'), nullable=False)
    # Funzione per ottenere la data corrente con l'anno 2025
    def get_corrected_date():
        today = date.today()
        # Utilizziamo l'anno 2025 come richiesto
        if today.year != 2025:
            return date(2025, today.month, today.day)
        return today
    
    date = db.Column(db.Date, nullable=False, default=get_corrected_date)
    day_label = db.Column(db.String(20), nullable=False)  # oggi, domani, dopodomani
    risk = db.Column(db.String(20))
    description = db.Column(db.Text)
    
    def __repr__(self):
        return f"<WeatherReport {self.day_label} for client {self.client_id}>"

class MailSettings(db.Model):
    __tablename__ = 'mail_settings'
    
    id = db.Column(db.Integer, primary_key=True)
    smtp_server = db.Column(db.String(100), nullable=False)
    smtp_port = db.Column(db.Integer, nullable=False)
    smtp_user = db.Column(db.String(100), nullable=False)
    smtp_pass = db.Column(db.String(100), nullable=False)
    from_email = db.Column(db.String(100), nullable=False)
    logo_path = db.Column(db.String(255), default='logo-base.png')  # Percorso del logo personalizzato
    sync_weather_hour = db.Column(db.Integer, default=6)  # Ora per la sincronizzazione meteo
    sync_weather_minute = db.Column(db.Integer, default=0)  # Minuto per la sincronizzazione meteo
    send_notifications_hour = db.Column(db.Integer, default=7)  # Ora per l'invio delle notifiche
    send_notifications_minute = db.Column(db.Integer, default=0)  # Minuto per l'invio delle notifiche
    
    def __repr__(self):
        return f"<MailSettings {self.smtp_server}:{self.smtp_port}>"

class EmailLog(db.Model):
    __tablename__ = 'email_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, default=datetime.now)
    client_id = db.Column(db.Integer, db.ForeignKey('clients.id'), nullable=True)  # Può essere null per email di test
    recipients = db.Column(db.Text, nullable=False)  # Lista di destinatari separati da virgola
    subject = db.Column(db.String(255), nullable=False)
    status = db.Column(db.String(20), nullable=False)  # success, partial, error
    source = db.Column(db.String(20), nullable=False)  # scheduler, manual, manual_all, test
    message = db.Column(db.Text, nullable=True)  # Messaggio di errore o successo
    
    def __repr__(self):
        return f"<EmailLog {self.timestamp} to {self.recipients}>"