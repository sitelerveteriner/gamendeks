import sqlite3
import os

KLASOR = os.path.dirname(os.path.abspath(__file__))
DB_DOSYASI = os.path.join(KLASOR, "market.db")


def veritabani_olustur():
    conn = sqlite3.connect(DB_DOSYASI)
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS fiyatlar (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tarih TEXT NOT NULL,
            site TEXT NOT NULL,
            sunucu TEXT NOT NULL,
            bize_sat REAL,
            satin_al REAL
        )
    """)

    conn.commit()
    conn.close()


def fiyat_ekle(tarih, site, sunucu, bize_sat, satin_al):
    conn = sqlite3.connect(DB_DOSYASI)
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO fiyatlar
        (tarih, site, sunucu, bize_sat, satin_al)
        VALUES (?, ?, ?, ?, ?)
    """, (tarih, site, sunucu, bize_sat, satin_al))

    conn.commit()
    conn.close()


def son_fiyatlari_getir():
    conn = sqlite3.connect(DB_DOSYASI)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT tarih, site, sunucu, bize_sat, satin_al
        FROM fiyatlar
        WHERE id IN (
            SELECT MAX(id)
            FROM fiyatlar
            GROUP BY site, sunucu
        )
        ORDER BY sunucu, site
    """)

    kayitlar = cursor.fetchall()
    conn.close()

    return kayitlar


def fiyat_gecmisi_getir(sunucu, limit_saat=None):
    conn = sqlite3.connect(DB_DOSYASI)
    cursor = conn.cursor()

    if limit_saat:
        cursor.execute("""
            SELECT tarih, site, bize_sat, satin_al
            FROM fiyatlar
            WHERE sunucu = ?
            AND datetime(tarih) >= datetime('now', ?)
            ORDER BY tarih ASC
        """, (sunucu, f"-{limit_saat} hours"))
    else:
        cursor.execute("""
            SELECT tarih, site, bize_sat, satin_al
            FROM fiyatlar
            WHERE sunucu = ?
            ORDER BY tarih ASC
        """, (sunucu,))

    kayitlar = cursor.fetchall()
    conn.close()

    return kayitlar
    conn = sqlite3.connect(DB_DOSYASI)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT tarih, site, bize_sat, satin_al
        FROM fiyatlar
        WHERE sunucu = ?
        ORDER BY tarih ASC
    """, (sunucu,))

    kayitlar = cursor.fetchall()
    conn.close()

    return kayitlar


def kayitlari_goster():
    conn = sqlite3.connect(DB_DOSYASI)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, tarih, site, sunucu, bize_sat, satin_al
        FROM fiyatlar
        ORDER BY id DESC
        LIMIT 20
    """)

    for kayit in cursor.fetchall():
        print(kayit)

    conn.close()


if __name__ == "__main__":
    veritabani_olustur()
    kayitlari_goster()