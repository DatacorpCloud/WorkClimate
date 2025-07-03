import requests

def get_coordinates(city):
    url = "https://nominatim.openstreetmap.org/search"
    params = {
        "q": city,
        "format": "json",
        "limit": 1,
        "countrycodes": "it"
    }
    headers = {
        "User-Agent": "worklimate-client/1.0"
    }
    response = requests.get(url, params=params, headers=headers)
    if response.status_code == 200 and response.json():
        data = response.json()[0]
        return float(data["lat"]), float(data["lon"])
    else:
        print("❌ Impossibile ottenere le coordinate.")
        return None, None

def get_station_code(city, lat, lon):
    url = "https://app.worklimate.it/osm-stazioni.php"
    params = {
        "osmod": "true",
        "place": city,
        "latx": lat,
        "lonx": lon
    }
    response = requests.get(url, params=params)
    if response.status_code == 200:
        try:
            data = response.json()
            if "q" in data.get("dati", {}):
                return data["dati"]["q"]
            elif "q" in data:
                return data["q"]
            else:
                print("⚠️ Nessun codice numerico restituito.")
                print("📦 Risposta:", response.text)
                return None
        except Exception as e:
            print("❌ Errore nel parsing JSON:", e)
            print("📦 Risposta:", response.text)
            return None
    else:
        print("❌ Errore HTTP nel recupero codice stazione.")
        return None

def get_weather_risk(pgrid):
    giorni = {
        "Oggi": "regular",
        "Domani": "plus1",
        "Dopodomani": "plus2"
    }

    livello_rischio = {
        "Basso": 1,
        "Moderato": 2,
        "Alto": 3
    }

    rischio_label = {
        1: "🟢 Basso",
        2: "🟡 Moderato",
        3: "🔴 Alto"
    }

    for nome_giorno, sys in giorni.items():
        url = "https://app.worklimate.it/osm-stazioni.php"
        params = {
            "pgrid": pgrid,
            "sys": sys
        }
        response = requests.get(url, params=params)
        if response.status_code == 200:
            try:
                data = response.json()
                labels = []
                for key in ["g1", "g2", "g3"]:
                    label = data.get(key, {}).get("label", "")
                    labels.append(livello_rischio.get(label, 0))

                max_risk = max(labels) if labels else 0
                rischio = rischio_label.get(max_risk, "❌ N/A")
                print(f"{nome_giorno} ☀️ Rischio caldo: {rischio}")
            except Exception as e:
                print(f"{nome_giorno} ❌ Errore nel parsing JSON: {e}")
        else:
            print(f"{nome_giorno} ❌ Errore HTTP: {response.status_code}")



if __name__ == "__main__":
    city = input("Inserisci la città: ")
    lat, lon = get_coordinates(city)
    if lat and lon:
        print(f"Coordinate trovate: lat={lat}, lon={lon}")
        pgrid = get_station_code(city, lat, lon)
        if pgrid:
            print(f"✅ Codice stazione ottenuto: {pgrid}")
            get_weather_risk(pgrid)
