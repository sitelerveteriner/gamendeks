# =========================
# IMPORTLAR
# =========================

from database import (
    fiyat_ekle,
    veritabani_olustur,
    son_fiyatlari_getir,
    fiyat_gecmisi_getir
)

from flask import Flask, redirect, request, render_template, jsonify
from apscheduler.schedulers.background import BackgroundScheduler
import requests
from bs4 import BeautifulSoup
from datetime import datetime
import re
import plotly.graph_objects as go

# =========================
# UYGULAMA AYARLARI
# =========================

app = Flask(__name__)

API_KEY = "gamendeks-12345"

KOPAZAR_URL = "https://www.kopazar.com/knight-online-gold-bar"
BYNOGAME_URL = "https://www.bynogame.com/tr/oyunlar/knight-online/gold-bar"


# =========================
# YARDIMCI FONKSİYONLAR
# =========================

def temiz_sunucu_adi(ad):
    if not ad:
        return ""
    return ad.replace("Gb", "").replace("GB", "").strip()


def simdi():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def fiyat_format(fiyat):
    if fiyat in ["", None]:
        return "-"
    try:
        return f"{float(str(fiyat).replace(',', '.')):.2f} TL"
    except:
        return "-"


# =========================
# VERİ ÇEKME FONKSİYONLARI
# =========================

def kopazar_guncelle():
    response = requests.get(
        KOPAZAR_URL,
        headers={"User-Agent": "Mozilla/5.0"},
        timeout=15
    )

    soup = BeautifulSoup(response.text, "html.parser")

    for item in soup.find_all("input"):
        gold_name = item.get("data-goldname")
        buy_price = item.get("data-buyprice")
        sell_price = item.get("data-sellprice")

        if gold_name and buy_price and sell_price:
            tarih = simdi()
            sunucu = temiz_sunucu_adi(gold_name)

            fiyat_ekle(
                tarih,
                "Kopazar",
                sunucu,
                float(buy_price),
                float(sell_price)
            )


def bynogame_guncelle():
    response = requests.get(
        BYNOGAME_URL,
        headers={"User-Agent": "Mozilla/5.0"},
        timeout=15
    )

    soup = BeautifulSoup(response.text, "html.parser")
    urunler = soup.select("article.itemDiv")

    for urun in urunler:
        isim_alani = urun.select_one("[ins-product-name]")
        fiyat_alani = urun.select_one("[ins-product-price]")

        if isim_alani and fiyat_alani:
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
                fiyat_ekle(
                    simdi(),
                    "ByNoGame",
                    sunucu,
                    float(bize_sat) / 10,
                    float(satin_al) / 10
                )


# =========================
# SAYFA ROUTE'LARI
# =========================

@app.route("/guncelle")
def guncelle():
    kopazar_guncelle()
    bynogame_guncelle()
    return redirect("/")


@app.route("/")
def anasayfa():
    kayitlar = son_fiyatlari_getir()

    kopazar = {}
    bynogame = {}

    for tarih, site, sunucu, bize_sat, satin_al in kayitlar:
        satir = {
            "Tarih": tarih,
            "Sunucu": sunucu,
            "Bize Sat": bize_sat,
            "Satın Al": satin_al
        }

        if site == "Kopazar":
            kopazar[sunucu] = satir
        elif site == "ByNoGame":
            bynogame[sunucu] = satir

    tum_sunucular = sorted(set(kopazar.keys()) | set(bynogame.keys()))

    son_guncelleme = "-"
    if kayitlar:
        son_guncelleme = max([k[0] for k in kayitlar])

    veriler = []

    for sunucu in tum_sunucular:
        k = kopazar.get(sunucu, {})
        b = bynogame.get(sunucu, {})

        veriler.append({
            "sunucu": sunucu,
            "bynogame_satin_al": fiyat_format(b.get("Satın Al")),
            "bynogame_bize_sat": fiyat_format(b.get("Bize Sat")),
            "kopazar_satin_al": fiyat_format(k.get("Satın Al")),
            "kopazar_bize_sat": fiyat_format(k.get("Bize Sat")),
            "son_tarih": k.get("Tarih") or b.get("Tarih") or "-"
        })

    return render_template(
        "index.html",
        veriler=veriler,
        sunucu_sayisi=len(tum_sunucular),
        son_guncelleme=son_guncelleme
    )

@app.route("/sunucu/<sunucu>")
def sunucu_detay(sunucu):
    aralik = request.args.get("aralik", "tum")

    if aralik == "24s":
        kayitlar = fiyat_gecmisi_getir(sunucu, 24)
    elif aralik == "7g":
        kayitlar = fiyat_gecmisi_getir(sunucu, 24 * 7)
    elif aralik == "30g":
        kayitlar = fiyat_gecmisi_getir(sunucu, 24 * 30)
    else:
        kayitlar = fiyat_gecmisi_getir(sunucu)

    if not kayitlar:
        return f"""
        <h1>{sunucu} için veri bulunamadı.</h1>
        <a href="/">Ana sayfaya dön</a>
        """

    tarihler_kopazar = []
    kopazar_satin_al = []
    kopazar_bize_sat = []

    tarihler_bynogame = []
    bynogame_satin_al = []
    bynogame_bize_sat = []

    for tarih, site, bize_sat, satin_al in kayitlar:
        if site == "Kopazar":
            tarihler_kopazar.append(tarih)
            kopazar_satin_al.append(satin_al)
            kopazar_bize_sat.append(bize_sat)

        elif site == "ByNoGame":
            tarihler_bynogame.append(tarih)
            bynogame_satin_al.append(satin_al)
            bynogame_bize_sat.append(bize_sat)

    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=tarihler_kopazar,
        y=kopazar_satin_al,
        mode="lines+markers",
        name="Kopazar Satın Al"
    ))

    fig.add_trace(go.Scatter(
        x=tarihler_kopazar,
        y=kopazar_bize_sat,
        mode="lines+markers",
        name="Kopazar Bize Sat"
    ))

    fig.add_trace(go.Scatter(
        x=tarihler_bynogame,
        y=bynogame_satin_al,
        mode="lines+markers",
        name="ByNoGame Satın Al"
    ))

    fig.add_trace(go.Scatter(
        x=tarihler_bynogame,
        y=bynogame_bize_sat,
        mode="lines+markers",
        name="ByNoGame Bize Sat"
    ))

    fig.update_layout(
        title=f"{sunucu} GB Fiyat Geçmişi",
        xaxis_title="Tarih",
        yaxis_title="Fiyat TL",
        template="plotly_dark",
        paper_bgcolor="#0f172a",
        plot_bgcolor="#111827",
        font=dict(color="#e5e7eb"),
        height=600
    )

    grafik_html = fig.to_html(full_html=False, config={"responsive": True})

    html = f"""
    <!DOCTYPE html>
    <html lang="tr">
    <head>
        <meta charset="UTF-8">
        <title>{sunucu} Fiyat Grafiği</title>
        <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet">
        <style>
            body {{
                margin: 0;
                font-family: 'Inter', sans-serif;
                background: #0f172a;
                color: #e5e7eb;
            }}

            .container {{
                max-width: 1300px;
                margin: 40px auto;
                padding: 20px;
            }}

            a {{
                color: #facc15;
                text-decoration: none;
                font-weight: 800;
            }}

            h1 {{
                text-align: center;
                font-size: 36px;
                letter-spacing: -0.03em;
            }}

            .filter-wrap {{
                text-align: center;
                margin: 25px 0;
            }}

            .filter-btn {{
                background: #1f2937;
                color: #facc15;
                padding: 10px 16px;
                border-radius: 8px;
                margin: 4px;
                display: inline-block;
            }}

            .filter-btn:hover {{
                background: #374151;
            }}

            @media (max-width: 600px) {{
                .container {{
                    margin: 16px auto;
                    padding: 12px;
                }}

                h1 {{
                    font-size: 27px;
                }}

                .filter-btn {{
                    padding: 9px 12px;
                    font-size: 13px;
                }}
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <a href="/">← Ana sayfa</a>

            <h1>{sunucu} GB Fiyat Grafiği</h1>

            <div class="filter-wrap">
                <a class="filter-btn" href="/sunucu/{sunucu}?aralik=24s">24 Saat</a>
                <a class="filter-btn" href="/sunucu/{sunucu}?aralik=7g">7 Gün</a>
                <a class="filter-btn" href="/sunucu/{sunucu}?aralik=30g">30 Gün</a>
                <a class="filter-btn" href="/sunucu/{sunucu}?aralik=tum">Tümü</a>
            </div>

            {grafik_html}
        </div>
    </body>
    </html>
    """

    return render_template(
    "sunucu.html",
    sunucu=sunucu,
    grafik_html=grafik_html,
    aralik_adi=aralik
)


# =========================
# BYNOGAME API
# =========================

@app.route("/api/bynogame-ekle", methods=["POST"])
def api_bynogame_ekle():
    data = request.get_json()

    if not data:
        return jsonify({"hata": "Veri gelmedi"}), 400

    if data.get("api_key") != API_KEY:
        return jsonify({"hata": "Yetkisiz"}), 403

    kayitlar = data.get("kayitlar", [])
    eklenen = 0

    for item in kayitlar:
        try:
            sunucu = temiz_sunucu_adi(item.get("sunucu", ""))

            fiyat_ekle(
                simdi(),
                "ByNoGame",
                sunucu,
                float(item.get("bize_sat")),
                float(item.get("satin_al"))
            )

            eklenen += 1

        except Exception as e:
            print("ByNoGame API kayıt hatası:", e)

    return jsonify({
        "durum": "ok",
        "eklenen": eklenen
    })


# =========================
# OTOMATİK GÜNCELLEME
# =========================

def otomatik_guncelle():
    try:
        print("Otomatik güncelleme başladı...")

        kopazar_guncelle()
        bynogame_guncelle()

        print("Otomatik güncelleme tamamlandı.")

    except Exception as e:
        print("Otomatik güncelleme hatası:", e)


# =========================
# UYGULAMA BAŞLATMA
# =========================

veritabani_olustur()

scheduler = BackgroundScheduler()

scheduler.add_job(
    otomatik_guncelle,
    "interval",
    minutes=60
)

scheduler.start()


if __name__ == "__main__":
    app.run(debug=True, use_reloader=False)