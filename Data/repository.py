import psycopg2
from dotenv import load_dotenv
from Data.models import Regija, Ponudnik, VrstaGoriva, Kraj, Crpalka, Cena
import os

load_dotenv()


def get_connection():
    return psycopg2.connect(
        host=os.getenv("HOST"),
        dbname=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD")
    )


class RegijaRepo:
    def __init__(self):
        self.conn = get_connection()

    def dodaj(self, r: Regija):
        with self.conn.cursor() as cur:
            cur.execute(
                "INSERT INTO regija (ime) VALUES (%s) RETURNING id_regije",
                (r.ime,)
            )
            r.id_regije = cur.fetchone()[0]
        self.conn.commit()
        return r

    def vrni_vse(self) -> list[Regija]:
        with self.conn.cursor() as cur:
            cur.execute("SELECT id_regije, ime FROM regija")
            return [Regija(id_regije=row[0], ime=row[1]) for row in cur.fetchall()]


class PonudnikRepo:
    def __init__(self):
        self.conn = get_connection()

    def dodaj(self, p: Ponudnik):
        with self.conn.cursor() as cur:
            cur.execute(
                "INSERT INTO ponudnik (naziv) VALUES (%s) RETURNING id_ponudnika",
                (p.naziv,)
            )
            p.id_ponudnika = cur.fetchone()[0]
        self.conn.commit()
        return p

    def vrni_vse(self) -> list[Ponudnik]:
        with self.conn.cursor() as cur:
            cur.execute("SELECT id_ponudnika, naziv FROM ponudnik")
            return [Ponudnik(id_ponudnika=row[0], naziv=row[1]) for row in cur.fetchall()]


class VrstaGorivaRepo:
    def __init__(self):
        self.conn = get_connection()

    def dodaj(self, v: VrstaGoriva):
        with self.conn.cursor() as cur:
            cur.execute(
                "INSERT INTO vrsta_goriva (naziv, enota) VALUES (%s, %s) RETURNING id_goriva",
                (v.naziv, v.enota)
            )
            v.id_goriva = cur.fetchone()[0]
        self.conn.commit()
        return v

    def vrni_vse(self) -> list[VrstaGoriva]:
        with self.conn.cursor() as cur:
            cur.execute("SELECT id_goriva, naziv, enota FROM vrsta_goriva")
            return [VrstaGoriva(id_goriva=row[0], naziv=row[1], enota=row[2]) for row in cur.fetchall()]

    def vrni_vse_za_prikaz(self) -> list[dict]:
        # Vrste goriva za prikaz na spletni strani (vključno s kodo in opisom).
        with self.conn.cursor() as cur:
            cur.execute("SELECT koda, naziv, opis, enota FROM vrsta_goriva ORDER BY id_goriva")
            return [
                {"koda": row[0], "naziv": row[1], "opis": row[2], "enota": row[3]}
                for row in cur.fetchall()
            ]


class CrpalkaRepo:
    def __init__(self):
        self.conn = get_connection()

    def dodaj(self, c: Crpalka):
        try:
            with self.conn.cursor() as cur:
                cur.execute(
                    """INSERT INTO crpalka (naziv, naslov, latitude, longitude, id_kraja, id_ponudnika, aktivna)
                       VALUES (%s, %s, %s, %s, %s, %s, %s) RETURNING id_crpalke""",
                    (c.naziv, c.naslov, c.latitude, c.longitude, c.id_kraja, c.id_ponudnika, c.aktivna)
                )
                c.id_crpalke = cur.fetchone()[0]
            self.conn.commit()
            return c
        except Exception as e:
            self.conn.rollback()  # reset broken transaction
            raise e

    def vrni_vse(self) -> list[Crpalka]:
        try:
            with self.conn.cursor() as cur:
                cur.execute("""
                    SELECT id_crpalke, naziv, naslov, latitude, longitude,
                           id_kraja, id_ponudnika, aktivna
                    FROM crpalka WHERE aktivna = TRUE
                """)
                return [Crpalka(
                    id_crpalke=row[0], naziv=row[1], naslov=row[2],
                    latitude=row[3], longitude=row[4],
                    id_kraja=row[5], id_ponudnika=row[6], aktivna=row[7]
                ) for row in cur.fetchall()]
        except Exception as e:
            self.conn.rollback()
            raise e

    def vrni_vse_za_prikaz(self) -> list[dict]:
        # Črpalke za prikaz: namesto ID-jev pokažemo ime kraja in naziv ponudnika.
        with self.conn.cursor() as cur:
            cur.execute("""
                SELECT c.naziv, c.naslov, k.ime AS kraj, k.postna_stevilka,
                       p.naziv AS ponudnik, c.aktivna
                FROM crpalka c
                LEFT JOIN kraj k ON c.id_kraja = k.id_kraja
                LEFT JOIN ponudnik p ON c.id_ponudnika = p.id_ponudnika
                ORDER BY c.naziv, c.naslov
            """)
            return [
                {"naziv": row[0], "naslov": row[1], "kraj": row[2],
                 "postna_stevilka": row[3], "ponudnik": row[4], "aktivna": row[5]}
                for row in cur.fetchall()
            ]


class CenaRepo:
    def __init__(self):
        self.conn = get_connection()

    def dodaj(self, c: Cena):
        with self.conn.cursor() as cur:
            cur.execute(
                """INSERT INTO cena (id_crpalke, id_goriva, vrednost, valuta)
                   VALUES (%s, %s, %s, %s) RETURNING id_cene""",
                (c.id_crpalke, c.id_goriva, c.vrednost, c.valuta)
            )
            c.id_cene = cur.fetchone()[0]
        self.conn.commit()
        return c

    def vrni_zadnje_cene(self) -> list[Cena]:
        with self.conn.cursor() as cur:
            cur.execute("""
                SELECT DISTINCT ON (id_crpalke, id_goriva)
                    id_cene, id_crpalke, id_goriva, vrednost, valuta, datum_zajema
                FROM cena
                ORDER BY id_crpalke, id_goriva, datum_zajema DESC
            """)
            return [Cena(
                id_cene=row[0], id_crpalke=row[1], id_goriva=row[2],
                vrednost=row[3], valuta=row[4], datum_zajema=str(row[5])
            ) for row in cur.fetchall()]

    def vrni_zadnje_cene_za_prikaz(self) -> list[dict]:
        # Zadnja (najnovejša) cena za vsako kombinacijo črpalka + gorivo,
        # z nazivom črpalke in nazivom goriva za lepši prikaz.
        with self.conn.cursor() as cur:
            cur.execute("""
                SELECT DISTINCT ON (ce.id_crpalke, ce.id_goriva)
                    c.naziv AS crpalka, vg.naziv AS gorivo,
                    ce.vrednost, ce.valuta, ce.datum_zajema
                FROM cena ce
                LEFT JOIN crpalka c ON ce.id_crpalke = c.id_crpalke
                LEFT JOIN vrsta_goriva vg ON ce.id_goriva = vg.id_goriva
                ORDER BY ce.id_crpalke, ce.id_goriva, ce.datum_zajema DESC
            """)
            return [
                {"crpalka": row[0], "gorivo": row[1], "vrednost": float(row[2]),
                 "valuta": row[3], "datum_zajema": str(row[4])}
                for row in cur.fetchall()
            ]