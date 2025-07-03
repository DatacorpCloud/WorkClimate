from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from werkzeug.utils import secure_filename
from datetime import datetime, date
import os
from dotenv import load_dotenv
from apscheduler.schedulers.background import BackgroundScheduler
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.image import MIMEImage

# Carica le variabili d'ambiente dal file .env
load_dotenv()

# Importazione dei modelli e del database
from models import db, Client, ClientEmail, WeatherReport, MailSettings, EmailLog

# Importazione delle configurazioni
from config import DevelopmentConfig

# Inizializzazione dell'app Flask
app = Flask(__name__)
app.config.from_object(DevelopmentConfig)

# Assicurarsi che TLS sia abilitato per le email
app.config['MAIL_USE_TLS'] = True

# Inizializzazione del database con l'app
db.init_app(app)

# Importazione degli script meteo
import meteo
import meteo_integration

# Funzione per sincronizzare i dati meteo
def sync_weather():
    clients = Client.query.all()
    
    # Creiamo una cache per i bollettini meteo per località
    # Questo evita di fare richieste multiple per lo stesso luogo
    bollettini_cache = {}
    
    # Raggruppiamo i clienti per città
    clienti_per_citta = {}
    for client in clients:
        if client.city not in clienti_per_citta:
            clienti_per_citta[client.city] = []
        clienti_per_citta[client.city].append(client)
    
    # Numero totale di clienti sincronizzati
    clienti_sincronizzati = 0
    
    # Processiamo ogni città una sola volta
    for citta, clienti_citta in clienti_per_citta.items():
        print(f"Elaborazione dati meteo per {citta} ({len(clienti_citta)} clienti)")
        
        # Recupera il bollettino solo una volta per città
        if citta not in bollettini_cache:
            # Utilizziamo il nuovo modulo meteo_integration per recuperare i dati meteo
            print(f"Utilizzo meteo_integration per recuperare dati meteo per {citta}")
            bollettino = meteo_integration.get_weather_data(citta)
            
            if not bollettino:
                print(f"Nessun bollettino trovato per {citta}, utilizzo bollettino simulato")
                bollettino = meteo_integration.create_simulated_bulletin()
                if not bollettino:
                    # Se non riusciamo a creare un bollettino simulato, verifichiamo se abbiamo dati esistenti
                    existing_reports = False
                    for client in clienti_citta:
                        if WeatherReport.query.filter_by(client_id=client.id).count() > 0:
                            existing_reports = True
                            existing_client = client
                            break
                    
                    if existing_reports:
                        # Riutilizziamo i dati esistenti solo come ultima risorsa
                        print(f"Riutilizzo dati meteo esistenti per {citta} dal cliente {existing_client.company_name}")
                        existing_data = WeatherReport.query.filter_by(client_id=existing_client.id).all()
                        # Creiamo un bollettino simulato con gli stessi dati
                        bollettino = {
                            "g1": {"data": str(existing_data[0].date), "label": existing_data[0].risk, "desc": existing_data[0].description},
                            "g2": {"data": str(existing_data[1].date), "label": existing_data[1].risk, "desc": existing_data[1].description},
                            "g3": {"data": str(existing_data[2].date), "label": existing_data[2].risk, "desc": existing_data[2].description}
                        }
                    else:
                        print(f"Impossibile creare bollettino simulato per {citta}, salto tutti i clienti di questa città")
                        continue
                else:
                    print(f"Creato bollettino simulato per {citta}")
            else:
                print(f"Recuperato bollettino per {citta} con dati aggiornati")
            
            # Salva il bollettino nella cache
            bollettini_cache[citta] = bollettino
        else:
            print(f"Utilizzo bollettino dalla cache per {citta}")
            bollettino = bollettini_cache[citta]
        
        giorni = {"g1": "Oggi", "g2": "Domani", "g3": "Dopodomani"}
        
        # Verifica se il bollettino è nel formato originale
        formato_originale = any(g_key in bollettino for g_key in giorni)
        
        # Processa ogni cliente della città
        for client in clienti_citta:
            # Cancella i report precedenti per questo cliente
            WeatherReport.query.filter_by(client_id=client.id).delete()
            
            if formato_originale:
                # Formato originale
                for g_key, g_label in giorni.items():
                    giorno = bollettino.get(g_key)
                    if giorno:
                        livello = giorno.get("label", "")
                        desc = giorno.get("desc", "")
                        data_str = giorno.get("data", None)
                        
                        # Ottieni la data corrente o usa quella dal bollettino
                        if data_str:
                            try:
                                from datetime import datetime
                                today = datetime.strptime(data_str, "%Y-%m-%d").date()
                            except:
                                today = date.today()
                                # Utilizziamo l'anno 2025 come richiesto
                                if today.year != 2025:
                                    today = date(2025, today.month, today.day)
                        else:
                            today = date.today()
                            # Utilizziamo l'anno 2025 come richiesto
                            if today.year != 2025:
                                today = date(2025, today.month, today.day)
                        
                        report = WeatherReport(
                            client_id=client.id,
                            date=today,
                            day_label=g_label,
                            risk=livello,
                            description=desc
                        )
                        db.session.add(report)
            else:
                # Nuovo formato
                try:
                    # Verifica se ci sono chiavi che potrebbero contenere i dati dei giorni
                    giorni_keys = [k for k in bollettino.keys() if isinstance(bollettino[k], dict)]
                    
                    if not giorni_keys:
                        print(f"Struttura del bollettino non riconosciuta per {client.company_name}")
                        continue
                    
                    # Estrai i dati per ogni giorno disponibile
                    for i, (key, label) in enumerate(zip(giorni_keys[:3], ["Oggi", "Domani", "Dopodomani"])):
                        giorno_data = bollettino[key]
                        
                        # Cerca i campi che potrebbero contenere il livello di rischio e la descrizione
                        livello = None
                        desc = None
                        data_str = None
                        
                        # Cerca campi comuni che potrebbero contenere il livello di rischio
                        for campo in ["label", "rischio", "livello", "risk"]:
                            if campo in giorno_data:
                                livello = giorno_data[campo]
                                break
                        
                        # Cerca campi comuni che potrebbero contenere la descrizione
                        for campo in ["desc", "descrizione", "description"]:
                            if campo in giorno_data:
                                desc = giorno_data[campo]
                                break
                        
                        # Cerca campi comuni che potrebbero contenere la data
                        for campo in ["data", "date", "giorno", "day"]:
                            if campo in giorno_data:
                                data_str = giorno_data[campo]
                                break
                        
                        if livello is not None:
                            # Ottieni la data dal bollettino o usa quella corrente
                            if data_str:
                                try:
                                    from datetime import datetime
                                    today = datetime.strptime(data_str, "%Y-%m-%d").date()
                                except:
                                    today = date.today()
                                    # Utilizziamo l'anno 2025 come richiesto
                                    if today.year != 2025:
                                        today = date(2025, today.month, today.day)
                            else:
                                today = date.today()
                                # Utilizziamo l'anno 2025 come richiesto
                                if today.year != 2025:
                                    today = date(2025, today.month, today.day)
                            
                            report = WeatherReport(
                                client_id=client.id,
                                date=today,
                                day_label=label,
                                risk=livello,
                                description=desc or ""
                            )
                            db.session.add(report)
                except Exception as e:
                    print(f"Errore nell'elaborazione del nuovo formato per {client.company_name}: {str(e)}")
                    continue
            
            clienti_sincronizzati += 1
        
        # Commit dopo aver processato tutti i clienti di una città
        db.session.commit()
    
    return {"status": "success", "message": f"Sincronizzati {clienti_sincronizzati} clienti"}

# Funzione per inviare email
def send_email(to_email, subject, body, client_id=None, source='manual'):
    # Converte to_email in una lista se è una stringa
    if isinstance(to_email, str):
        recipients = [to_email]
    else:
        recipients = to_email
    
    # Prova prima a utilizzare le impostazioni dalle variabili d'ambiente
    mail_server = os.environ.get('MAIL_SERVER')
    mail_port = int(os.environ.get('MAIL_PORT', 587))
    mail_username = os.environ.get('MAIL_USERNAME')
    mail_password = os.environ.get('MAIL_PASSWORD')
    mail_default_sender = os.environ.get('MAIL_DEFAULT_SENDER')
    mail_use_tls = os.environ.get('MAIL_USE_TLS') == 'True'
    
    # Se le variabili d'ambiente non sono configurate, utilizza le impostazioni dal database
    if not mail_server or not mail_username or not mail_password:
        settings = MailSettings.query.first()
        if not settings:
            error_msg = "Impostazioni email non configurate né in .env né nel database"
            # Registra il log dell'errore
            log_email(client_id, ",".join(recipients), subject, "error", source, error_msg)
            return {"status": "error", "message": error_msg}
        mail_server = settings.smtp_server
        mail_port = settings.smtp_port
        mail_username = settings.smtp_user
        mail_password = settings.smtp_pass
        mail_default_sender = settings.from_email
        mail_use_tls = True  # Forza l'uso di TLS
    
    # Utilizza il mittente predefinito se non specificato
    from_email = mail_default_sender or mail_username
    
    try:
        print(f"Tentativo di invio email utilizzando il server {mail_server}:{mail_port}")
        
        # Imposta un timeout per evitare blocchi indefiniti
        server = smtplib.SMTP(mail_server, mail_port, timeout=10)
        # Abilita il debug per vedere i dettagli della comunicazione
        server.set_debuglevel(1)
        
        # Avvia TLS per la connessione sicura (assicurandosi che sia abilitato)
        if mail_use_tls:
            server.starttls()
            print("TLS avviato per la connessione sicura")
        
        # Login con le credenziali
        server.login(mail_username, mail_password)
        print(f"Login effettuato con l'utente {mail_username}")
        
        success_count = 0
        for recipient in recipients:
            try:
                # Crea un nuovo messaggio per ogni destinatario
                msg = MIMEMultipart()
                msg['From'] = from_email
                msg['To'] = recipient
                msg['Subject'] = subject
                
                # Aggiungi il corpo HTML dell'email
                msg.attach(MIMEText(body, 'html'))
                
                # Aggiungi il logo come allegato inline
                settings = MailSettings.query.first()
                logo_filename = settings.logo_path if settings and settings.logo_path else 'logo-base.png'
                logo_path = os.path.join(app.root_path, 'img', logo_filename)
                if os.path.exists(logo_path):
                    with open(logo_path, 'rb') as img_file:
                        img = MIMEImage(img_file.read())
                        img.add_header('Content-ID', '<logo>')
                        img.add_header('Content-Disposition', 'inline', filename=logo_filename)
                        msg.attach(img)
                
                # Invia il messaggio
                server.send_message(msg)
                print(f"Email inviata a {recipient}")
                success_count += 1
            except Exception as e:
                print(f"Errore nell'invio dell'email a {recipient}: {str(e)}")
        
        # Chiudi la connessione
        server.quit()
        
        if success_count == len(recipients):
            status = "success"
            message = f"Email inviata con successo a {success_count} destinatari"
        elif success_count > 0:
            status = "partial"
            message = f"Email inviata a {success_count} su {len(recipients)} destinatari"
        else:
            status = "error"
            message = "Nessuna email inviata"
        
        # Registra il log dell'email
        log_email(client_id, ",".join(recipients), subject, status, source, message)
        
        return {"status": status, "message": message}
    except Exception as e:
        error_msg = str(e)
        print(f"Errore nell'invio dell'email: {error_msg}")
        
        # Registra il log dell'errore
        log_email(client_id, ",".join(recipients), subject, "error", source, error_msg)
        
        return {"status": "error", "message": error_msg}

# Funzione per registrare i log delle email
def log_email(client_id, recipients, subject, status, source, message=None):
    try:
        email_log = EmailLog(
            client_id=client_id,
            recipients=recipients,
            subject=subject,
            status=status,
            source=source,
            message=message
        )
        db.session.add(email_log)
        db.session.commit()
        print(f"Log email registrato: {status} - {source} - {recipients}")
    except Exception as e:
        print(f"Errore nella registrazione del log email: {str(e)}")
        db.session.rollback()

# Rotte dell'applicazione
@app.route('/')
def index():
    return render_template('index.html')

# Visualizzazione dei log delle email
@app.route('/email-logs')
def email_logs():
    logs = EmailLog.query.order_by(EmailLog.timestamp.desc()).all()
    
    # Crea un dizionario con i nomi dei clienti per un accesso rapido
    clients = {}
    for client in Client.query.all():
        clients[client.id] = client.company_name
    
    return render_template('email_logs.html', logs=logs, clients=clients)

# Gestione clienti
@app.route('/clients')
def clients():
    all_clients = Client.query.all()
    return render_template('clients.html', clients=all_clients)

@app.route('/clients/add', methods=['GET', 'POST'])
def add_client():
    if request.method == 'POST':
        company_name = request.form.get('company_name')
        email = request.form.get('email')  # Email principale
        phone = request.form.get('phone')
        city = request.form.get('city')
        
        # Crea il nuovo cliente
        new_client = Client(company_name=company_name, email=email, phone=phone, city=city)
        db.session.add(new_client)
        db.session.commit()
        
        # Aggiungi l'email principale come ClientEmail con is_primary=True
        primary_email = ClientEmail(client_id=new_client.id, email=email, is_primary=True)
        db.session.add(primary_email)
        
        # Aggiungi le email aggiuntive
        additional_emails = request.form.getlist('additional_emails[]')
        for add_email in additional_emails:
            if add_email and add_email.strip():  # Verifica che l'email non sia vuota
                client_email = ClientEmail(client_id=new_client.id, email=add_email, is_primary=False)
                db.session.add(client_email)
        
        db.session.commit()
        
        flash('Cliente aggiunto con successo!', 'success')
        return redirect(url_for('clients'))
    
    return render_template('client_form.html')

@app.route('/clients/edit/<int:client_id>', methods=['GET', 'POST'])
def edit_client(client_id):
    client = Client.query.get_or_404(client_id)
    
    if request.method == 'POST':
        client.company_name = request.form.get('company_name')
        main_email = request.form.get('email')
        client.email = main_email  # Aggiorna l'email principale nel campo legacy
        client.phone = request.form.get('phone')
        client.city = request.form.get('city')
        
        # Aggiorna o crea l'email principale
        primary_email = ClientEmail.query.filter_by(client_id=client.id, is_primary=True).first()
        if primary_email:
            primary_email.email = main_email
        else:
            primary_email = ClientEmail(client_id=client.id, email=main_email, is_primary=True)
            db.session.add(primary_email)
        
        # Elimina tutte le email aggiuntive esistenti
        ClientEmail.query.filter_by(client_id=client.id, is_primary=False).delete()
        
        # Aggiungi le nuove email aggiuntive
        additional_emails = request.form.getlist('additional_emails[]')
        for add_email in additional_emails:
            if add_email and add_email.strip():  # Verifica che l'email non sia vuota
                client_email = ClientEmail(client_id=client.id, email=add_email, is_primary=False)
                db.session.add(client_email)
        
        db.session.commit()
        
        flash('Cliente aggiornato con successo!', 'success')
        return redirect(url_for('clients'))
    
    return render_template('client_form.html', client=client)

@app.route('/clients/delete/<int:client_id>', methods=['POST'])
def delete_client(client_id):
    client = Client.query.get_or_404(client_id)
    db.session.delete(client)
    db.session.commit()
    
    flash('Cliente eliminato con successo!', 'success')
    return redirect(url_for('clients'))

# Sincronizzazione meteo
@app.route('/sync-weather', methods=['POST'])
def sync_weather_route():
    result = sync_weather()
    flash(result["message"], 'success' if result["status"] == "success" else 'danger')
    return redirect(url_for('reports'))

# Report meteo
@app.route('/reports')
def reports():
    clients_with_reports = Client.query.all()
    return render_template('reports.html', clients=clients_with_reports)

# Invio notifiche
@app.route('/send-notification/<int:client_id>', methods=['POST'])
def send_notification(client_id):
    client = Client.query.get_or_404(client_id)
    reports = WeatherReport.query.filter_by(client_id=client.id).all()
    
    # Costruisci il corpo dell'email
    body = f"""<h2>Report Meteo per {client.company_name}</h2>
    <p>Ecco il report meteo per i prossimi giorni:</p>
    <table border='1' cellpadding='5'>
        <tr>
            <th>Giorno</th>
            <th>Livello di Rischio</th>
            <th>Descrizione</th>
        </tr>"""
    
    # Calcola le date per oggi, domani e dopodomani
    today_date = date.today()
    # Correggi l'anno se necessario
    if today_date.year == 2025:
        today_date = date(2023, today_date.month, today_date.day)
    
    # Calcola domani e dopodomani basandosi sulla data corretta
    tomorrow_date = date(today_date.year, today_date.month, today_date.day + 1)
    day_after_tomorrow_date = date(today_date.year, today_date.month, today_date.day + 2)
    
    for report in reports:
        # Determina la data in base al day_label
        if report.day_label == "Oggi":
            date_str = today_date.strftime("%d-%m-%Y")
            display_date = f"{report.day_label} {date_str}"
        elif report.day_label == "Domani":
            date_str = tomorrow_date.strftime("%d-%m-%Y")
            display_date = f"{report.day_label} {date_str}"
        elif report.day_label == "Dopodomani":
            date_str = day_after_tomorrow_date.strftime("%d-%m-%Y")
            display_date = f"{report.day_label} {date_str}"
        else:
            display_date = report.day_label
            
        body += f"""<tr>
            <td>{display_date}</td>
            <td>{report.risk}</td>
            <td>{report.description}</td>
        </tr>"""
    
    body += """</table>
    <p>Questo report è generato automaticamente dal sistema <a href="https://github.com/DatacorpCloud/WorkClimate" target="_blank">Clima e Lavoro</a>
.</p>
    <p><img src="cid:logo" alt="Clima e Lavoro" style="max-width: 200px; height: auto;"></p>"""
    
    # Raccogli tutte le email del cliente (principale e aggiuntive)
    email_list = [client.email]  # Email principale dal campo legacy
    
    # Aggiungi le email dalla tabella ClientEmail
    client_emails = ClientEmail.query.filter_by(client_id=client.id).all()
    for client_email in client_emails:
        if client_email.email not in email_list:  # Evita duplicati
            email_list.append(client_email.email)
    
    result = send_email(
        email_list, 
        "Report Meteo - Clima e Lavoro", 
        body,
        client_id=client.id,
        source='manual'
    )
    
    flash(result["message"], 'success' if result["status"] == "success" else 'danger')
    return redirect(url_for('reports'))

@app.route('/send-all-notifications', methods=['POST'])
def send_all_notifications():
    clients = Client.query.all()
    success_count = 0
    total_clients = 0
    
    for client in clients:
        reports = WeatherReport.query.filter_by(client_id=client.id).all()
        if not reports:
            continue
            
        total_clients += 1
            
        # Costruisci il corpo dell'email
        body = f"""<h2>Report Meteo per {client.company_name}</h2>
        <p>Ecco il report meteo per i prossimi giorni:</p>
        <table border='1' cellpadding='5'>
            <tr>
                <th>Giorno</th>
                <th>Livello di Rischio</th>
                <th>Descrizione</th>
            </tr>"""
        
        # Calcola le date per oggi, domani e dopodomani
        today_date = date.today()
        # Correggi l'anno se necessario
        if today_date.year == 2025:
            today_date = date(2023, today_date.month, today_date.day)
        
        # Calcola domani e dopodomani basandosi sulla data corretta
        tomorrow_date = date(today_date.year, today_date.month, today_date.day + 1)
        day_after_tomorrow_date = date(today_date.year, today_date.month, today_date.day + 2)
        
        for report in reports:
            # Determina la data in base al day_label
            if report.day_label == "Oggi":
                date_str = today_date.strftime("%d-%m-%Y")
                display_date = f"{report.day_label} {date_str}"
            elif report.day_label == "Domani":
                date_str = tomorrow_date.strftime("%d-%m-%Y")
                display_date = f"{report.day_label} {date_str}"
            elif report.day_label == "Dopodomani":
                date_str = day_after_tomorrow_date.strftime("%d-%m-%Y")
                display_date = f"{report.day_label} {date_str}"
            else:
                display_date = report.day_label
                
            body += f"""<tr>
                <td>{display_date}</td>
                <td>{report.risk}</td>
                <td>{report.description}</td>
            </tr>"""
        
        body += """</table>
        <p>Questo report è generato automaticamente dal sistema Clima e Lavoro.</p>
        <p><img src="cid:logo" alt="Clima e Lavoro" style="max-width: 200px; height: auto;"></p>"""
        
        # Raccogli tutte le email del cliente (principale e aggiuntive)
        email_list = [client.email]  # Email principale dal campo legacy
        
        # Aggiungi le email dalla tabella ClientEmail
        client_emails = ClientEmail.query.filter_by(client_id=client.id).all()
        for client_email in client_emails:
            if client_email.email not in email_list:  # Evita duplicati
                email_list.append(client_email.email)
        
        result = send_email(
            email_list, 
            "Report Meteo - Clima e Lavoro", 
            body,
            client_id=client.id,
            source='manual_all'
        )
        
        if result["status"] == "success" or result["status"] == "partial":
            success_count += 1
    
    flash(f"Inviate notifiche a {success_count} su {total_clients} clienti", 'success')
    return redirect(url_for('reports'))

# Impostazioni email
@app.route('/settings', methods=['GET', 'POST'])
def settings():
    settings = MailSettings.query.first()
    
    if request.method == 'POST':
        # Gestione del caricamento del logo
        logo_file = request.files.get('logo_file')
        logo_path = request.form.get('logo_path')
        
        if logo_file and logo_file.filename:
            # Salva il nuovo logo nella cartella static/img
            filename = secure_filename(logo_file.filename)
            logo_path = filename
            logo_file.save(os.path.join(app.root_path, 'static', 'img', filename))
        
        if settings:
            settings.smtp_server = request.form.get('smtp_server')
            settings.smtp_port = int(request.form.get('smtp_port'))
            settings.smtp_user = request.form.get('smtp_user')
            settings.smtp_pass = request.form.get('smtp_pass')
            settings.from_email = request.form.get('from_email')
            settings.logo_path = logo_path
            
            # Salva le impostazioni dello scheduler
            settings.sync_weather_hour = int(request.form.get('sync_weather_hour'))
            settings.sync_weather_minute = int(request.form.get('sync_weather_minute'))
            settings.send_notifications_hour = int(request.form.get('send_notifications_hour'))
            settings.send_notifications_minute = int(request.form.get('send_notifications_minute'))
        else:
            settings = MailSettings(
                smtp_server=request.form.get('smtp_server'),
                smtp_port=int(request.form.get('smtp_port')),
                smtp_user=request.form.get('smtp_user'),
                smtp_pass=request.form.get('smtp_pass'),
                from_email=request.form.get('from_email'),
                logo_path=logo_path,
                sync_weather_hour=int(request.form.get('sync_weather_hour')),
                sync_weather_minute=int(request.form.get('sync_weather_minute')),
                send_notifications_hour=int(request.form.get('send_notifications_hour')),
                send_notifications_minute=int(request.form.get('send_notifications_minute'))
            )
            db.session.add(settings)
        
        db.session.commit()
        
        # Riavvia lo scheduler con i nuovi orari
        from scheduler import setup_scheduler
        scheduler = setup_scheduler(app)
        
        flash('Impostazioni salvate con successo!', 'success')
        return redirect(url_for('settings'))
    
    return render_template('settings.html', settings=settings)

@app.route('/test-email', methods=['POST'])
def test_email():
    test_email = request.form.get('test_email')
    
    result = send_email(
        test_email,
        "Test Email - Clima e Lavoro",
        "<h1>Test Email</h1><p>Questa è un'email di test dal sistema Clima e Lavoro.</p><p><img src='cid:logo' alt='Clima e Lavoro' style='max-width: 200px; height: auto;'></p>",
        client_id=None,
        source='test'
    )
    
    flash(result["message"], 'success' if result["status"] == "success" else 'danger')
    return redirect(url_for('settings'))

# Importazione dello scheduler e datetime
from scheduler import setup_scheduler
import datetime

# Creazione delle tabelle del database e avvio dello scheduler
# NOTA: Lo scheduler viene avviato automaticamente alla prima richiesta
# Non è necessario avviare scheduler.py separatamente, basta lanciare app.py
# e lo scheduler verrà inizializzato e avviato automaticamente
@app.before_first_request
def initialize():
    with app.app_context():
        db.create_all()
        # Avvia lo scheduler con gli orari configurati nelle impostazioni
        setup_scheduler(app)

# Aggiunge la variabile now a tutti i template
@app.context_processor
def inject_now():
    return {'now': datetime.datetime.now()}

if __name__ == '__main__':
    app.run(debug=True)