import re
import requests
from bs4 import BeautifulSoup

API_URL = "http://178.105.50.234/api/bynogame-ekle"
API_KEY = "gamendeks-12345"

BYNOGAME_URL = "https://www.bynogame.com/tr/oyunlar/knight-online/gold-bar"

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
    "Accept-Language": "tr-TR,tr;q=0.9,en-US;q=0.8,en;q=0.7",
}

def temiz_sunucu_adi(ad):
    if not ad:
        return ""
    return ad.replace("Gb", "").replace("GB", "").strip()

def main():
    response = requests.get(BYNOGAME_URL, headers=headers, timeout=20)
    print("ByNoGame STATUS:", response.status_code)

    soup = BeautifulSoup(response.text, "html.parser")
    urunler = soup.select("article.itemDiv")
    print("Ürün sayısı:", len(urunler))

    kayitlar = []

    for urun in urunler:
        isim_alani = urun.select_one("[ins-product-name]")
        fiyat_alani = urun.select_one("[ins-product-price]")

        if not isim_alani or not fiyat_alani:
            continue

        isim = isim_alani.get("ins-product-name")
        satin_al = fiyat_alani.get("ins-product-price")

        sunucu = (
            isim
            .replace("Knight Online", "")
            .replace("Gold Bar GB", "")
            .strip()
        )
        sunucu = temiz_sunucu_adi(sunucu)

        bize_sat = ""

        for btn in urun.find_all("button"):
            text = btn.get_text(" ", strip=True)

            if "BİZE SAT" in text.upper():
                eslesme = re.search(r"(\d+[,.]?\d*)", text)
                if eslesme:
                    bize_sat = eslesme.group(1).replace(",", ".")

        if bize_sat:
            kayitlar.append({
                "sunucu": sunucu,
                "bize_sat": float(bize_sat) / 10,
                "satin_al": float(str(satin_al).replace(",", ".")) / 10
            })

    print("Gönderilecek kayıt:", len(kayitlar))

    if not kayitlar:
        print("Kayıt bulunamadı. ByNoGame sayfa yapısı değişmiş veya erişim engellenmiş olabilir.")
        return

    r = requests.post(
        API_URL,
        json={
            "api_key": API_KEY,
            "kayitlar": kayitlar
        },
        timeout=20
    )

    print("API STATUS:", r.status_code)
    print(r.text)

if __name__ == "__main__":
    main()
