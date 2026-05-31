#ta skripta je namenjena tedenskemu zajemu cen goriv s spletne strani goriva.si in pol vpisu teh cen v SQL bazo. Uporabila sem task scheduler, ki bo skripto zagnal vsak torek ob 00.10 ko se cene goriv posodobijo
import requests
import psycopg2
from datetime import date

BASE = "https://goriva.si/api/v1"
TODAY = date.today().isoformat()

# NASTAVITVE ZA POVEZAVO (Najprej nujno preizkusi na svoji bazi, pol spremen na aljazevo!)
DB_HOST = "baza.fmf.uni-lj.si"
DB_NAME = "sem2026_dezmal"  
DB_USER = "pikavi"          
DB_PASS = "geslo"        

def fetch_and_insert_weekly_prices():
    print("Zagon tedenskega zajema: Pobiram trenutne cene iz goriva.si API...")
    page = 1
    vsi_novi_zapisi = []

    # 1. DEL: Pobiranje trenutno veljavnih cen s spleta (od Ane)
    while True:
        r = requests.get(f"{BASE}/search/", params={
            "format": "json", "page": page,
            "franchise": "", "name": "", "o": "", "position": "", "radius": ""
        })
        data = r.json()

        for s in data["results"]:
            station_id = int(s["pk"])
            for fuel_code, price in s["prices"].items():
                if price and price > 0.01:
                    try:
                        # Pripravimo podatke za tabelo 'cena'
                        vsi_novi_zapisi.append({
                            "id_crpalke": station_id,
                            "id_goriva": int(fuel_code), # API vrne npr. '1' ali '2'
                            "vrednost": float(price)
                        })
                    except ValueError:
                        # Če je koda goriva slučajno tekst (npr. 'lpg'), jo preskočimo
                        continue

        if data["next"] is None:
            break
        page += 1

    print(f"Zajetih {len(vsi_novi_zapisi)} trenutnih cen. Vpisujem v bazo '{DB_NAME}'...")

    # 2. DEL: Vpis v SQL tabelo 'cena'
    povezava = None
    kurzor = None
    try:
        povezava = psycopg2.connect(
            host=DB_HOST,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASS
        )
        kurzor = povezava.cursor()

        # SQL ukaz, prilagojen točnim stolpcem, ki jih ima Aljaz v tabeli cena
        sql_ukaz = """
            INSERT INTO cena (id_crpalke, id_goriva, vrednost, valuta, datum_zajema)
            VALUES (%s, %s, %s, 'EUR', %s);
        """

        # Vstavimo vse vrstice, ki smo jih pravkar pobrali z interneta
        for z in vsi_novi_zapisi:
            kurzor.execute(sql_ukaz, (z["id_crpalke"], z["id_goriva"], z["vrednost"], TODAY))
        
        povezava.commit()
        print(f"\n--- USPEH! ---")
        print(f"Vseh {len(vsi_novi_zapisi)} najnovejših cen je uspešno dodanih v tabelo!")

    except Exception as e:
        print(f"\n--- NAPAKA PRI VPISU ---")
        print(e)
        if povezava:
            povezava.rollback()
    finally:
        if kurzor: kurzor.close()
        if povezava: granite = povezava.close()

if __name__ == "__main__":
    fetch_and_insert_weekly_prices()