from bs4 import BeautifulSoup


def fiyatlari_ayristir(html):
    soup = BeautifulSoup(html, "html.parser")
    fiyatlar = []

    for urun in soup.select(
        "input[data-goldname][data-buyprice][data-sellprice]"
    ):
        sunucu = urun.get("data-goldname", "").strip()

        try:
            bize_sat = float(
                urun["data-buyprice"].replace(",", ".")
            )
            satin_al = float(
                urun["data-sellprice"].replace(",", ".")
            )
        except (ValueError, KeyError):
            continue

        if not sunucu:
            continue

        fiyatlar.append({
            "site": "Kopazar",
            "sunucu": sunucu,
            "bize_sat": bize_sat,
            "satin_al": satin_al,
        })

    return fiyatlar


if __name__ == "__main__":
    ornek_html = """
    <input
        data-goldname="Zero"
        data-buyprice="27.00"
        data-sellprice="28.50"
    >
    <input
        data-goldname="Pandora"
        data-buyprice="22.00"
        data-sellprice="24.50"
    >
    """

    for fiyat in fiyatlari_ayristir(ornek_html):
        print(
            fiyat["sunucu"],
            fiyat["bize_sat"],
            fiyat["satin_al"]
        )
