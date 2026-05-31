import csv
import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "Podatki_goriva", "data")


def get_connection():
    return psycopg2.connect(
        host=os.getenv("HOST"),
        dbname=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
    )


class UvozService:
    def __init__(self):
        self.conn = get_connection()

    def zapri(self):
        self.conn.close()

    def uvozi_ponudnike(self):
        pot = os.path.join(DATA_DIR, "franchises.csv")
        print(f"Uvažam ponudnike iz {pot} ...")

        with self.conn.cursor() as cur, open(pot, encoding="utf-8") as f:
            reader = csv.DictReader(f)

            for row in reader:
                cur.execute(
                    """
                    INSERT INTO ponudnik (zunanji_id, naziv)
                    VALUES (%s, %s)
                    ON CONFLICT (zunanji_id)
                    DO UPDATE SET naziv = EXCLUDED.naziv
                    """,
                    (int(row["id"]), row["name"]),
                )

        self.conn.commit()
        print("Ponudniki uvoženi.")

    def uvozi_vrste_goriva(self):
        pot = os.path.join(DATA_DIR, "fuel_types.csv")
        print(f"Uvažam vrste goriva iz {pot} ...")

        with self.conn.cursor() as cur, open(pot, encoding="utf-8") as f:
            reader = csv.DictReader(f)

            for row in reader:
                cur.execute(
                    """
                    INSERT INTO vrsta_goriva (koda, naziv, opis, enota)
                    VALUES (%s, %s, %s, %s)
                    ON CONFLICT (koda)
                    DO UPDATE SET
                        naziv = EXCLUDED.naziv,
                        opis = EXCLUDED.opis,
                        enota = EXCLUDED.enota
                    """,
                    (
                        row["code"],
                        row["name"],
                        row["long_name"],
                        "EUR/L",
                    ),
                )

        self.conn.commit()
        print("Vrste goriva uvožene.")

    def pridobi_neznano_regijo(self, cur):
        cur.execute(
            """
            INSERT INTO regija (ime)
            VALUES ('Neznana regija')
            ON CONFLICT (ime) DO NOTHING
            """
        )

        cur.execute("SELECT id_regije FROM regija WHERE ime = 'Neznana regija'")
        return cur.fetchone()[0]

    def pridobi_ali_ustvari_kraj(self, cur, zip_code, id_regije):
        ime = f"Pošta {zip_code}" if zip_code else "Neznan kraj"

        cur.execute(
            """
            INSERT INTO kraj (ime, postna_stevilka, id_regije)
            VALUES (%s, %s, %s)
            ON CONFLICT (ime, postna_stevilka)
            DO UPDATE SET id_regije = EXCLUDED.id_regije
            RETURNING id_kraja
            """,
            (ime, zip_code, id_regije),
        )

        return cur.fetchone()[0]

    def uvozi_crpalke(self):
        pot = os.path.join(DATA_DIR, "stations.csv")
        print(f"Uvažam črpalke iz {pot} ...")

        uvozeno = 0
        preskoceno = 0

        with self.conn.cursor() as cur, open(pot, encoding="utf-8") as f:
            id_regije = self.pridobi_neznano_regijo(cur)
            reader = csv.DictReader(f)

            for row in reader:
                try:
                    id_kraja = self.pridobi_ali_ustvari_kraj(
                        cur,
                        row.get("zip_code"),
                        id_regije,
                    )

                    cur.execute(
                        """
                        SELECT id_ponudnika
                        FROM ponudnik
                        WHERE zunanji_id = %s
                        """,
                        (int(row["franchise_id"]),),
                    )
                    ponudnik = cur.fetchone()

                    if ponudnik is None:
                        preskoceno += 1
                        continue

                    id_ponudnika = ponudnik[0]

                    cur.execute(
                        """
                        INSERT INTO crpalka (
                            zunanji_id,
                            naziv,
                            naslov,
                            latitude,
                            longitude,
                            odpiralni_cas,
                            id_kraja,
                            id_ponudnika,
                            aktivna
                        )
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, TRUE)
                        ON CONFLICT (zunanji_id)
                        DO UPDATE SET
                            naziv = EXCLUDED.naziv,
                            naslov = EXCLUDED.naslov,
                            latitude = EXCLUDED.latitude,
                            longitude = EXCLUDED.longitude,
                            odpiralni_cas = EXCLUDED.odpiralni_cas,
                            id_kraja = EXCLUDED.id_kraja,
                            id_ponudnika = EXCLUDED.id_ponudnika,
                            aktivna = TRUE
                        """,
                        (
                            int(row["id"]),
                            row["name"],
                            row["address"],
                            float(row["lat"]) if row["lat"] else None,
                            float(row["lng"]) if row["lng"] else None,
                            row.get("open_hours"),
                            id_kraja,
                            id_ponudnika,
                        ),
                    )

                    uvozeno += 1

                except Exception as e:
                    print(f"Napaka pri črpalki {row.get('name', '?')}: {e}")
                    preskoceno += 1

        self.conn.commit()
        print(f"Črpalke obdelane: {uvozeno}, preskočene: {preskoceno}.")

    def uvozi_cene(self):
        price_files = [
            filename
            for filename in os.listdir(DATA_DIR)
            if filename.startswith("prices_") and filename.endswith(".csv")
        ]

        print(f"Najdenih datotek s cenami: {len(price_files)}")

        with self.conn.cursor() as cur:
            for filename in sorted(price_files):
                pot = os.path.join(DATA_DIR, filename)
                uvozeno = 0
                preskoceno = 0

                print(f"Uvažam cene iz {filename} ...")

                with open(pot, encoding="utf-8") as f:
                    reader = csv.DictReader(f)

                    for row in reader:
                        try:
                            cur.execute(
                                """
                                SELECT id_crpalke
                                FROM crpalka
                                WHERE zunanji_id = %s
                                """,
                                (int(row["station_id"]),),
                            )
                            crpalka = cur.fetchone()

                            cur.execute(
                                """
                                SELECT id_goriva
                                FROM vrsta_goriva
                                WHERE koda = %s
                                """,
                                (row["fuel_code"],),
                            )
                            gorivo = cur.fetchone()

                            if crpalka is None or gorivo is None:
                                preskoceno += 1
                                continue

                            cur.execute(
                                """
                                INSERT INTO cena (
                                    id_crpalke,
                                    id_goriva,
                                    vrednost,
                                    valuta,
                                    datum_zajema
                                )
                                VALUES (%s, %s, %s, %s, %s)
                                ON CONFLICT (id_crpalke, id_goriva, datum_zajema)
                                DO UPDATE SET
                                    vrednost = EXCLUDED.vrednost,
                                    valuta = EXCLUDED.valuta
                                """,
                                (
                                    crpalka[0],
                                    gorivo[0],
                                    float(row["price_eur"]),
                                    "EUR",
                                    row["date"],
                                ),
                            )

                            uvozeno += 1

                        except Exception as e:
                            print(f"Napaka pri ceni {row}: {e}")
                            preskoceno += 1

                print(f"  Uvožene/posodobljene cene: {uvozeno}, preskočene: {preskoceno}")

        self.conn.commit()
        print("Cene uvožene.")

    def uvozi_vse(self):
        print("=== Začetek uvoza podatkov ===")
        self.uvozi_ponudnike()
        self.uvozi_vrste_goriva()
        self.uvozi_crpalke()
        self.uvozi_cene()
        print("=== Uvoz končan ===")


if __name__ == "__main__":
    service = UvozService()

    try:
        service.uvozi_vse()
    finally:
        service.zapri()