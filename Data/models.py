from dataclasses import field, dataclass

@dataclass
class Regija:
    ime: str = field(default="")
    id_regije: int = field(default=0)

@dataclass
class Ponudnik:
    naziv: str = field(default="")
    id_ponudnika: int = field(default=0)

@dataclass
class VrstaGoriva:
    naziv: str = field(default="")
    enota: str = field(default="EUR/L")
    id_goriva: int = field(default=0)

@dataclass
class Kraj:
    ime: str = field(default="")
    postna_stevilka: str = field(default="")
    id_regije: int = field(default=0)
    id_kraja: int = field(default=0)

@dataclass
class Crpalka:
    naziv: str = field(default="")
    naslov: str = field(default="")
    latitude: float = field(default=0.0)
    longitude: float = field(default=0.0)
    id_kraja: int = field(default=0)
    id_ponudnika: int = field(default=0)
    aktivna: bool = field(default=True)
    id_crpalke: int = field(default=0)

@dataclass
class Cena:
    id_crpalke: int = field(default=0)
    id_goriva: int = field(default=0)
    vrednost: float = field(default=0.0)
    valuta: str = field(default="EUR")
    datum_zajema: str = field(default="")
    id_cene: int = field(default=0)