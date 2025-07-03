import requests
from datetime import date

# Importa le funzioni da meteo2.py
from meteo2 import get_coordinates, get_station_code, get_weather_risk

def get_weather_data(city):
    """
    Recupera i dati meteo per una città utilizzando le funzioni di meteo2.py
    e li formatta nel formato utilizzato da app.py
    """
    print(f"Recupero dati meteo per {city}...")
    
    # Ottieni le coordinate geografiche
    lat, lon = get_coordinates(city)
    if not lat or not lon:
        print(f"❌ Impossibile ottenere le coordinate per {city}, utilizzo dati simulati")
        return create_simulated_bulletin()
    
    print(f"✅ Coordinate trovate: lat={lat}, lon={lon}")
    
    # Ottieni il codice della stazione
    pgrid = get_station_code(city, lat, lon)
    if not pgrid:
        print(f"❌ Impossibile ottenere il codice stazione per {city}, utilizzo dati simulati")
        return create_simulated_bulletin()
    
    print(f"✅ Codice stazione ottenuto: {pgrid}")
    
    # Recupera i dati meteo per i prossimi 3 giorni
    giorni = {
        "Oggi": "regular",
        "Domani": "plus1",
        "Dopodomani": "plus2"
    }
    
    livello_rischio = {
        "Basso": "BASSO",
        "Moderato": "MODERATO",
        "Alto": "ALTO"
    }
    
    descrizioni = {
        "BASSO": "Poni maggiore attenzione all'idratazione e pianifica brevi pause.",
        "MODERATO": "Bevi regolarmente e fai pause in luoghi ombreggiati.",
        "ALTO": "Bevi spesso, anche poco più di 1 L/h e programma pause frequenti in luoghi ombreggiati o aree condizionate."
    }
    
    # Date fisse per il 2025 come richiesto
    date_list = ["2025-07-03", "2025-07-04", "2025-07-05"]
    
    # Crea il bollettino nel formato utilizzato da app.py
    bollettino = {}
    
    try:
        # Tenta di recuperare i dati meteo reali
        url = f"https://app.worklimate.it/osm-stazioni.php"
        headers = {
            "X-Requested-With": "XMLHttpRequest",
            "Referer": "https://app.worklimate.it/ordinanza-caldo-lavoro",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:140.0) Gecko/20100101 Firefox/140.0"
        }
        
        # Recupera i dati per ogni giorno
        for i, (nome_giorno, sys) in enumerate(giorni.items()):
            params = {
                "pgrid": pgrid,
                "sys": sys
            }
            
            response = requests.get(url, params=params, headers=headers, timeout=5)
            if response.status_code == 200:
                try:
                    data = response.json()
                    labels = []
                    
                    # Estrai i livelli di rischio
                    for key in ["g1", "g2", "g3"]:
                        label = data.get(key, {}).get("label", "")
                        if label in livello_rischio:
                            labels.append(livello_rischio[label])
                    
                    # Determina il livello di rischio massimo
                    if labels:
                        max_risk = max(labels, key=lambda x: {"BASSO": 1, "MODERATO": 2, "ALTO": 3}.get(x, 0))
                    else:
                        max_risk = "BASSO"  # Default a BASSO se non ci sono dati
                    
                    # Aggiungi al bollettino
                    day_key = f"g{i+1}"
                    bollettino[day_key] = {
                        "data": date_list[i],
                        "label": max_risk,
                        "desc": descrizioni[max_risk]
                    }
                    
                    print(f"✅ {nome_giorno}: Rischio {max_risk}")
                except Exception as e:
                    print(f"❌ Errore nell'elaborazione dei dati per {nome_giorno}: {str(e)}")
                    # Usa dati simulati per questo giorno
                    day_key = f"g{i+1}"
                    bollettino[day_key] = {
                        "data": date_list[i],
                        "label": "BASSO",
                        "desc": descrizioni["BASSO"]
                    }
            else:
                print(f"❌ Errore nella richiesta per {nome_giorno}: {response.status_code}")
                # Usa dati simulati per questo giorno
                day_key = f"g{i+1}"
                bollettino[day_key] = {
                    "data": date_list[i],
                    "label": "BASSO",
                    "desc": descrizioni["BASSO"]
                }
        
        # Verifica se abbiamo recuperato dati per tutti e 3 i giorni
        if len(bollettino) < 3:
            print(f"⚠️ Dati incompleti per {city}, integro con dati simulati")
            for i in range(1, 4):
                day_key = f"g{i}"
                if day_key not in bollettino:
                    bollettino[day_key] = {
                        "data": date_list[i-1],
                        "label": "BASSO",
                        "desc": descrizioni["BASSO"]
                    }
        
        return bollettino
    except Exception as e:
        print(f"❌ Errore generale nel recupero dei dati meteo: {str(e)}")
        return create_simulated_bulletin()

def create_simulated_bulletin():
    """
    Crea un bollettino simulato con rischio BASSO per tutti i giorni
    """
    print("⚠️ Creazione bollettino simulato con rischio BASSO")
    
    # Date fisse per il 2025 come richiesto
    date_list = ["2025-07-03", "2025-07-04", "2025-07-05"]
    
    descrizione = "Poni maggiore attenzione all'idratazione e pianifica brevi pause."
    
    bollettino = {}
    for i in range(3):
        day_key = f"g{i+1}"
        bollettino[day_key] = {
            "data": date_list[i],
            "label": "BASSO",
            "desc": descrizione
        }
    
    return bollettino

# Test della funzione
if __name__ == "__main__":
    cities = ["Viterbo", "Montalto di Castro", "Canazei"]
    for city in cities:
        print(f"\nTest per {city}:")
        bollettino = get_weather_data(city)
        print(f"Bollettino per {city}:")
        for day_key, day_data in bollettino.items():
            print(f"{day_key}: {day_data['label']} - {day_data['data']}")
            print(f"  {day_data['desc']}")