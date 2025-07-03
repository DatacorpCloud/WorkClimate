import requests
import urllib.parse
import json

session = requests.Session()

def cerca_stazione(luogo):
    luogo_enc = urllib.parse.quote(luogo)
    url = f"https://app.worklimate.it/osm-stazioni.php?osmod=true&place={luogo_enc}"
    resp = session.get(url)
    if resp.status_code != 200:
        print(f"Errore richiesta stazione: {resp.status_code}")
        return None
    data = resp.json()
    if "dati" in data:
        pgrid = data.get("id")
        print(f"Stazione trovata con pgrid: {pgrid}")
        return pgrid
    else:
        print("Nessuna stazione trovata.")
        return None

def recupera_bollettino(pgrid):
    url = f"https://app.worklimate.it/osm-stazioni.php?pgrid={pgrid}&sys=regular"
    headers = {
        "X-Requested-With": "XMLHttpRequest",
        "Referer": "https://app.worklimate.it/ordinanza-caldo-lavoro",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:140.0) Gecko/20100101 Firefox/140.0"
    }
    resp = session.get(url, headers=headers)
    if resp.status_code != 200:
        print(f"Errore richiesta bollettino: {resp.status_code}")
        return None
    try:
        data = resp.json()
    except json.JSONDecodeError:
        print("Errore nel decodificare il JSON.")
        return None
    return data

def main():
    luogo = input("Inserisci il luogo da cercare: ").strip()
    pgrid = cerca_stazione(luogo)
    if not pgrid:
        return
    bollettino = recupera_bollettino(pgrid)
    if not bollettino:
        return
    
    giorni = {"g1": "Oggi", "g2": "Domani", "g3": "Dopodomani"}
    alert_alto = False

    for g_key, g_label in giorni.items():
        giorno = bollettino.get(g_key)
        if giorno:
            livello = giorno.get("label")
            desc = giorno.get("desc")
            print(f"{g_label} - Rischio: {livello}")
            print(f"  {desc}")
            if livello and livello.upper() == "ALTO":
                alert_alto = True
        else:
            print(f"{g_label} - Nessun dato disponibile")

    if alert_alto:
        print("⚠️ ALERT: Almeno un giorno con rischio ALTO!")
    else:
        print("✅ Nessun rischio alto rilevato nei prossimi 3 giorni.")

if __name__ == "__main__":
    main()
