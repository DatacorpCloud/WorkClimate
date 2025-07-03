from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime
from models import Client, WeatherReport, db

# Le funzioni sync_weather e send_email verranno importate quando setup_scheduler viene chiamato
# per evitare importazioni circolari

def setup_scheduler(app):
    # Importa le funzioni qui per evitare importazioni circolari
    from app import sync_weather
    from models import MailSettings
    
    scheduler = BackgroundScheduler()
    
    # Ottieni le impostazioni personalizzate per gli orari
    with app.app_context():
        settings = MailSettings.query.first()
        sync_hour = settings.sync_weather_hour if settings else 6
        sync_minute = settings.sync_weather_minute if settings else 0
        notify_hour = settings.send_notifications_hour if settings else 7
        notify_minute = settings.send_notifications_minute if settings else 0
    
    # Sincronizzazione meteo con orario personalizzato
    scheduler.add_job(func=sync_weather, trigger="cron", hour=sync_hour, minute=sync_minute, id="sync_weather")
    
    # Invio automatico delle notifiche con orario personalizzato
    # Passa l'app come argomento alla funzione send_daily_notifications
    scheduler.add_job(func=lambda: send_daily_notifications(app), trigger="cron", hour=notify_hour, minute=notify_minute, id="send_notifications")
    
    # Avvia lo scheduler
    scheduler.start()
    
    # Assicurati che lo scheduler si fermi quando l'applicazione si chiude
    import atexit
    atexit.register(lambda: scheduler.shutdown())
    
    return scheduler

def send_daily_notifications(app):
    """Invia notifiche giornaliere a tutti i clienti"""
    # Importa la funzione send_email qui per evitare importazioni circolari
    from app import send_email
    
    with app.app_context():
        clients = Client.query.all()
        success_count = 0
        
        for client in clients:
            reports = WeatherReport.query.filter_by(client_id=client.id).all()
            if not reports:
                continue
                
            # Costruisci il corpo dell'email
            body = f"""<h2>Report Meteo Giornaliero per {client.company_name}</h2>
            <p>Ecco il report meteo per i prossimi giorni:</p>
            <table border='1' cellpadding='5'>
                <tr>
                    <th>Giorno</th>
                    <th>Livello di Rischio</th>
                    <th>Descrizione</th>
                </tr>"""
            
            for report in reports:
                risk_color = "green"
                if report.risk and report.risk.upper() == "ALTO":
                    risk_color = "red"
                elif report.risk and report.risk.upper() == "MEDIO":
                    risk_color = "orange"
                    
                body += f"""<tr>
                    <td>{report.day_label}</td>
                    <td style='color: {risk_color};'><strong>{report.risk}</strong></td>
                    <td>{report.description}</td>
                </tr>"""
            
            body += """</table>
            <p>Questo report è generato automaticamente dal sistema <a href="https://github.com/DatacorpCloud/WorkClimate" target="_blank">Clima e Lavoro</a>
            <p>Data: {}</p>
            <p><img src="cid:logo" alt="Clima e Lavoro" style="max-width: 200px; height: auto;"></p>""".format(datetime.now().strftime("%d/%m/%Y %H:%M"))
            
            # Raccogli tutte le email associate al cliente
            emails = [client.email]  # Email principale dal campo legacy
            
            # Aggiungi le email dal modello ClientEmail
            client_emails = [ce.email for ce in client.emails if ce.email not in emails]
            if client_emails:
                emails.extend(client_emails)
            
            # Invia l'email a tutti i destinatari
            result = send_email(
                emails, 
                f"Report Meteo Giornaliero - {datetime.now().strftime('%d/%m/%Y')}", 
                body
            )
            
            if result["status"] == "success":
                success_count += 1
        
        print(f"[{datetime.now()}] Inviate {success_count} notifiche su {len(clients)} clienti")
        return {"status": "success", "message": f"Inviate {success_count} notifiche su {len(clients)} clienti"}