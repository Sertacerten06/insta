"""10 Kasım Atatürk'ü Anma Günü Instagram postu (8-bit Arpama tarzı, 29 Ekim postuyla aynı dil).

Portre ve ay-yıldız, kullanıcının verdiği referans görselden (ozel/10kasim/post/referans.jpg)
alınır; yeniden çizilmez, sadece 8-bit'e çevrilir: sanal piksel ızgarasına küçültülür,
gümüş bantlara (4 ton) Bayer dither ile indirgenir ve nearest-neighbor ile büyütülür.

Çıktı: ozel/10kasim/post/post-4x5.png (1080x1350), post-kare.png (1080x1080), hikaye-9x16.png (1080x1920)

Kullanım:
  python scripts/ozel/ataturk_post.py
"""
import random
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

KOK = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(KOK / "scripts"), str(KOK / "scripts" / "render"), str(KOK / "scripts" / "ozel")]
import cumhuriyet_cizim as C  # noqa: E402  (P'ye gece/bayrak renklerini ekler)
from cumhuriyet_cizim import c  # noqa: E402
from cizim import OLCEK, SH, SW, YaziKatmani, yazi  # noqa: E402
from sahneler import logo  # noqa: E402

DIZIN = KOK / "ozel" / "10kasim" / "post"
REFERANS = DIZIN / "referans.jpg"
RX = SW * OLCEK // 2

# Referans görselde portre + ay-yıldız bölgesi (1024x1024 üzerinde)
KIRP = (310, 350, 760, 700)
GUMUS_TON = ["soluk", "gumus_koyu", "gumus", "beyaz"]


def R(v):
    return int(round(v * OLCEK))


def yaz(yk, metin, y, boyut=67, renk="gumus", bant=None, kenar=6, ad="piksel"):
    yk.ekle(yazi(metin, ad, boyut, renk=renk, bant=bant, kenar=kenar, kenar_renk="gece1"), RX, y, "orta")


def portre_sprite(genislik):
    """Referanstaki gümüş portreyi sanal piksel ölçeğinde 8-bit sprite'a çevirir (RGBA, sanal px)."""
    im = Image.open(REFERANS).convert("L").crop(KIRP)
    a = np.array(im).astype(np.float32)
    maske = (a > 105).astype(np.float32)
    h = int(round(im.height * genislik / im.width))
    kapsama = np.array(Image.fromarray((maske * 255).astype(np.uint8)).resize((genislik, h), Image.BOX)) / 255.0
    # Parlaklık sadece portre pikselleri üzerinden (zemin karışmasın)
    pay = np.array(Image.fromarray(a * maske).resize((genislik, h), Image.BOX))
    payda = np.maximum(kapsama, 1e-3)
    lum = pay / payda
    v = np.clip((lum - 112) / (150 - 112), 0, 1)
    by = np.tile(C.BAYER, (h // 4 + 1, genislik // 4 + 1))[:h, :genislik]
    n = len(GUMUS_TON) - 1
    seviye = np.clip(np.floor(v * n + by * 0.9), 0, n).astype(int)
    tonlar = np.array([c(t) for t in GUMUS_TON], np.uint8)
    rgba = np.zeros((h, genislik, 4), np.uint8)
    rgba[..., :3] = tonlar[seviye]
    rgba[..., 3] = np.where(kapsama > 0.5, 255, 0)
    return rgba


def koy(arr, sp, x0, y0):
    h, w = sp.shape[:2]
    m = sp[..., 3] > 0
    arr[y0:y0 + h, x0:x0 + w][m] = sp[..., :3][m]


def golge(arr, sp, x0, y0, renk="gece1", dx=2, dy=2):
    """Piksel gölge: sprite'ın silüeti sağ-alta kaydırılmış koyu tonla."""
    h, w = sp.shape[:2]
    m = sp[..., 3] > 0
    arr[y0 + dy:y0 + dy + h, x0 + dx:x0 + dx + w][m] = c(renk)


def ayrac(d, cx, y, yari=70):
    """Altın yıldızlı ince piksel ayraç."""
    d.line([(cx - yari, y), (cx - 7, y)], fill=c("altin_koyu"))
    d.line([(cx + 7, y), (cx + yari, y)], fill=c("altin_koyu"))
    for k in range(0, yari - 10, 6):
        d.point((cx - yari + k, y - 1), fill=c("gece3"))
        d.point((cx + yari - k, y - 1), fill=c("gece3"))
    d.point((cx, y - 3), fill=c("altin_acik"))
    d.line([(cx - 1, y - 2), (cx + 1, y - 2)], fill=c("altin_acik"))
    d.line([(cx - 4, y - 1), (cx + 4, y - 1)], fill=c("altin"))
    d.line([(cx - 2, y), (cx + 2, y)], fill=c("altin"))
    d.point([(cx - 2, y + 1), (cx + 2, y + 1)], fill=c("altin_koyu"))
    d.point([(cx - 3, y + 2), (cx + 3, y + 2)], fill=c("altin_koyu"))


def tarama(img):
    """Hafif CRT tarama çizgisi (%12): her sanal pikselin son gerçek satırı biraz koyulur."""
    a = np.array(img).astype(np.float32)
    a[OLCEK - 1::OLCEK] *= 0.88
    return Image.fromarray(a.astype(np.uint8), "RGB")


def ciz(yuk, duzen):
    """yuk: sanal piksel yüksekliği. duzen: y konumları (sanal px) sözlüğü."""
    arr = np.zeros((SH, SW, 3), np.uint8)
    C.gradyan(arr, 0, yuk, ["gece1", "gece2", "gece3", "gece2", "gece1"])
    im = Image.fromarray(arr)
    d = ImageDraw.Draw(im)
    rng = random.Random(10)
    for i in range(70):
        x, y = rng.randrange(SW), rng.randrange(yuk)
        d.point((x, y), fill=c("mavi_buz") if i % 4 == 0 else c("soluk") if i % 3 else c("gece3"))
        if i % 17 == 0:
            d.point([(x - 1, y), (x + 1, y), (x, y - 1), (x, y + 1)], fill=c("gece3"))
    arr[:] = np.array(im)

    sp = portre_sprite(duzen["portre_w"])
    ph, pw = sp.shape[:2]
    px, py = (SW - pw) // 2 + 4, duzen["portre_y"]
    C.isik(arr, px + pw * 0.62, py + ph * 0.5, pw * 0.62, "gece3", 1.0)
    C.isik(arr, px + pw * 0.62, py + ph * 0.5, pw * 0.40, "altin_koyu", 0.35)
    golge(arr, sp, px, py)
    koy(arr, sp, px, py)

    im = Image.fromarray(arr)
    d = ImageDraw.Draw(im)
    ayrac(d, SW // 2, duzen["ayrac1"])
    ayrac(d, SW // 2, duzen["ayrac2"], yari=60)
    arr[:] = np.array(im)

    yk = YaziKatmani()
    yaz(yk, "10 KASIM 1938", R(duzen["baslik"]), boyut=100, bant="altin", kenar=10)
    yaz(yk, "ATATÜRK'Ü ANMA GÜNÜ", R(duzen["alt_baslik"]), boyut=67, renk="beyaz", kenar=8)
    yaz(yk, "SONSUZA KADAR...", R(duzen["soz1"]), boyut=67, bant="altin", kenar=8)
    yaz(yk, "SAYGI VE MİNNETLE ANIYORUZ", R(duzen["soz2"]), boyut=50, renk="gumus", kenar=6)
    logo(yk, RX, R(duzen["logo"]), duzen.get("logo_boyut", 90))

    img = Image.fromarray(np.repeat(np.repeat(arr[:yuk], OLCEK, 0), OLCEK, 1), "RGB")
    img = tarama(img)
    yk.uygula(img)
    return img


DUZENLER = {
    # 1080x1350 (4:5) — feed için en çok alan kaplayan oran
    "post-4x5": (338, 1350, dict(baslik=22, alt_baslik=52, ayrac1=78, portre_w=200, portre_y=90,
                           ayrac2=250, soz1=255, soz2=274, logo=297, logo_boyut=80)),
    # 1080x1080 kare (referansla aynı oran)
    "post-kare": (270, 1080, dict(baslik=12, alt_baslik=38, ayrac1=64, portre_w=150, portre_y=72,
                                  ayrac2=192, soz1=196, soz2=213, logo=233, logo_boyut=60)),
    # 1080x1920 hikâye; IG güvenli alanı (üst 220, alt 380 gerçek px) içinde
    "hikaye-9x16": (480, 1920, dict(baslik=58, alt_baslik=87, ayrac1=114, portre_w=210, portre_y=130,
                                    ayrac2=302, soz1=308, soz2=326, logo=344, logo_boyut=85)),
}


def main():
    for ad, (yuk, gercek_h, duzen) in DUZENLER.items():
        img = ciz(yuk, duzen).crop((0, 0, SW * OLCEK, gercek_h))
        img.save(DIZIN / f"{ad}.png")
        print(ad, img.size)


if __name__ == "__main__":
    main()
