from Data.repository import CrpalkaRepo, CenaRepo, VrstaGorivaRepo


# Aplikacijski nivo za prikaz podatkov na spletni strani.
# Servis kliče repozitorije iz podatkovnega nivoja in vrne podatke,
# ki jih predstavitveni nivo (Flask) prikaže uporabniku.
# Tu ni nobenih SQL poizvedb - za to skrbijo repozitoriji.

class GorivaService:
    def __init__(self):
        self.crpalke_repo = CrpalkaRepo()
        self.cene_repo = CenaRepo()
        self.vrste_repo = VrstaGorivaRepo()

    def dobi_crpalke(self) -> list[dict]:
        return self.crpalke_repo.vrni_vse_za_prikaz()

    def dobi_cene(self) -> list[dict]:
        return self.cene_repo.vrni_zadnje_cene_za_prikaz()

    def dobi_vrste_goriva(self) -> list[dict]:
        return self.vrste_repo.vrni_vse_za_prikaz()
