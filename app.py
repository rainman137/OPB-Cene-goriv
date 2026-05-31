from flask import Flask, render_template

from Services.goriva_service import GorivaService

# Predstavitveni nivo: Flask aplikacija, ki prikazuje podatke uporabniku.
# HTML predloge so v mapi Presentation/templates, statične datoteke v Presentation/static.
app = Flask(
    __name__,
    template_folder="Presentation/templates",
    static_folder="Presentation/static",
)

# Servis za pridobivanje podatkov (aplikacijski nivo).
service = GorivaService()


@app.route("/")
def crpalke():
    """Domača stran s seznamom črpalk."""
    return render_template("crpalke.html", crpalke=service.dobi_crpalke(), stran="crpalke")


@app.route("/cene")
def cene():
    """Stran z zadnjimi cenami goriv."""
    return render_template("cene.html", cene=service.dobi_cene(), stran="cene")


@app.route("/vrste_goriva")
def vrste_goriva():
    """Stran s seznamom vrst goriva."""
    return render_template("vrste_goriva.html", vrste_goriva=service.dobi_vrste_goriva(), stran="vrste_goriva")


if __name__ == "__main__":
    # threaded=False, ker repozitoriji uporabljajo eno samo povezavo do baze.
    app.run(host="localhost", port=8080, debug=True, threaded=False)
