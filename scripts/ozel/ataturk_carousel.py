"""10 Kasım Atatürk’ü Anma Günü carousel postu (2 sayfa, 1080x1350).

Stil: hesabın 29 Ekim postuyla aynı zarif dil. Koyu zemin, ince altın çerçeve, Cinzel büyük harf
başlık, Cormorant Garamond italik altın vurgu, kırmızı elmaslı ayraç, altta Arpama logosu.

Sayfa 1: referans görseldeki gümüş portre + ay-yıldız, "ATATÜRK / saygıyla anıyoruz."
Sayfa 2: Cumhuriyet'in önemli tarihleri, tam ortada doğum yılı madalyonu (1881, Selanik).

Portre ve logo kullanıcının verdiği referans görselden (ozel/10kasim/post/referans.jpg) alınır.

Kullanım:
  python scripts/ozel/ataturk_carousel.py
"""
import math
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

KOK = Path(__file__).resolve().parents[2]
FONT = KOK / "brand" / "fonts"
DIZIN = KOK / "ozel" / "10kasim" / "post"
REFERANS = DIZIN / "referans.jpg"
W, H = 1080, 1350

BEYAZ = (246, 244, 238)
GUMUS = (201, 206, 214)
SOLUK = (154, 160, 171)
ALTIN = (226, 190, 110)
ALTIN_ACIK = (255, 227, 143)
ALTIN_KOYU = (178, 140, 66)
KIRMIZI = (200, 30, 40)
CERCEVE = (120, 98, 52)


def font(ad, boyut, agirlik=None):
    dosya = {"cinzel": "Cinzel-var.ttf", "serif": "CormorantGaramond-var.ttf",
             "italik": "CormorantGaramond-Italic-var.ttf"}[ad]
    f = ImageFont.truetype(str(FONT / dosya), boyut)
    if agirlik:
        f.set_variation_by_axes([agirlik])
    return f


def yazi(d, metin, x, y, f, renk, hiza="orta", aralik=0):
    """aralik: harf aralığı (px). hiza: orta | sol | sag. y = üst kenar."""
    if aralik:
        gen = sum(d.textlength(ch, font=f) for ch in metin) + aralik * (len(metin) - 1)
    else:
        gen = d.textlength(metin, font=f)
    x0 = x - gen / 2 if hiza == "orta" else x - gen if hiza == "sag" else x
    if not aralik:
        d.text((x0, y), metin, font=f, fill=renk)
        return gen
    for ch in metin:
        d.text((x0, y), ch, font=f, fill=renk)
        x0 += d.textlength(ch, font=f) + aralik
    return gen


def zemin():
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    r = np.sqrt(((xx - W / 2) / W) ** 2 + ((yy - H * 0.42) / H) ** 2)
    v = np.clip(1 - r * 1.6, 0, 1) ** 1.5
    ic, dis = np.array([30, 33, 40], np.float32), np.array([8, 9, 12], np.float32)
    arr = dis + (ic - dis) * v[..., None]
    gurultu = np.random.default_rng(10).normal(0, 2.2, (H, W, 1))
    arr = np.clip(arr + gurultu, 0, 255).astype(np.uint8)
    im = Image.fromarray(arr, "RGB").convert("RGBA")
    d = ImageDraw.Draw(im)
    d.rectangle([28, 28, W - 29, H - 29], outline=CERCEVE + (170,), width=1)
    return im


def ayrac(d, y, yari=120):
    d.line([(W / 2 - yari, y), (W / 2 - 18, y)], fill=ALTIN_KOYU, width=2)
    d.line([(W / 2 + 18, y), (W / 2 + yari, y)], fill=ALTIN_KOYU, width=2)
    d.polygon([(W / 2, y - 7), (W / 2 + 7, y), (W / 2, y + 7), (W / 2 - 7, y)], fill=KIRMIZI)


def portre(genislik):
    """Referanstaki gümüş portre + ay-yıldız, zeminden ayrılmış RGBA."""
    im = Image.open(REFERANS).convert("RGB").crop((300, 340, 770, 710))
    a = np.array(im.convert("L")).astype(np.float32)
    alfa = np.clip((a - 70) / 45, 0, 1)
    rgba = np.dstack([np.array(im), (alfa * 255).astype(np.uint8)])
    sp = Image.fromarray(rgba, "RGBA")
    h = int(sp.height * genislik / sp.width)
    return sp.resize((genislik, h), Image.LANCZOS)


def logo(genislik):
    """Referanstaki Arpama logosu (AR altın + PAMA gümüş + TECHNOLOGY), zemin saydamlaştırılır."""
    im = Image.open(REFERANS).convert("RGB").crop((338, 755, 686, 882))
    arr = np.array(im).astype(np.float32)
    zemin_rgb = np.median(arr[:6].reshape(-1, 3), axis=0)
    fark = np.abs(arr - zemin_rgb).max(axis=2)
    alfa = np.clip((fark - 18) / 60, 0, 1)
    rgb = np.clip((arr - zemin_rgb * (1 - alfa[..., None])) / np.maximum(alfa[..., None], 1e-3), 0, 255)
    sp = Image.fromarray(np.dstack([rgb, alfa * 255]).astype(np.uint8), "RGBA")
    h = int(sp.height * genislik / sp.width)
    return sp.resize((genislik, h), Image.LANCZOS)


def hale(im, cx, cy, r, renk, guc):
    k = Image.new("RGBA", im.size, (0, 0, 0, 0))
    ImageDraw.Draw(k).ellipse([cx - r, cy - r, cx + r, cy + r], fill=renk + (int(255 * guc),))
    im.alpha_composite(k.filter(ImageFilter.GaussianBlur(r * 0.45)))


def logo_koy(im, y, genislik=230):
    lg = logo(genislik)
    im.alpha_composite(lg, (int(W / 2 - lg.width / 2), y))


def sayfa1():
    im = zemin()
    d = ImageDraw.Draw(im)
    ust = font("cinzel", 26, 600)
    yazi(d, "10 KASIM 1938", 70, 70, ust, GUMUS, "sol", aralik=7)
    yazi(d, "SAAT 09.05", W - 70, 70, ust, ALTIN, "sag", aralik=7)

    sp = portre(880)
    px, py = int(W / 2 - sp.width / 2) + 10, 150
    hale(im, px + sp.width * 0.6, py + sp.height * 0.5, 300, (60, 66, 80), 0.6)
    golge = Image.new("RGBA", sp.size, (0, 0, 0, 0))
    golge.putalpha(sp.getchannel("A").point(lambda v: int(v * 0.6)))
    im.alpha_composite(golge.filter(ImageFilter.GaussianBlur(14)), (px + 10, py + 16))
    im.alpha_composite(sp, (px, py))

    # portrenin alt kenarını zemine erit
    yy = np.arange(H)[:, None]
    erit = np.clip((yy - 700) / 120, 0, 1)
    alt = np.array(zemin()).astype(np.float32)
    ust_k = np.array(im).astype(np.float32)
    im = Image.fromarray((ust_k * (1 - erit[..., None]) + alt * erit[..., None]).astype(np.uint8), "RGBA")
    d = ImageDraw.Draw(im)

    yazi(d, "ATATÜRK", W / 2, 820, font("cinzel", 132, 700), BEYAZ, aralik=6)
    yazi(d, "saygıyla anıyoruz.", W / 2, 965, font("italik", 112, 600), ALTIN)
    ayrac(d, 1125)
    yazi(d, "10 Kasım Atatürk’ü Anma Günü", W / 2, 1150, font("italik", 44, 500), GUMUS)
    logo_koy(im, 1218)
    return im.convert("RGB")


TARIHLER = [
    ("1919", "19 MAYIS", "Samsun’a çıkış"),
    ("1920", "23 NİSAN", "TBMM açıldı"),
    ("1922", "30 AĞUSTOS", "Büyük Zafer"),
    ("1923", "29 EKİM", "Cumhuriyet ilan edildi"),
    ("1924", "3 MART", "Eğitim birliği"),
    ("1928", "1 KASIM", "Harf Devrimi"),
    ("1934", "5 ARALIK", "Kadınlara seçme hakkı"),
    ("1938", "10 KASIM", "Sonsuzluğa yürüdü"),
]


def sayfa2():
    im = zemin()
    d = ImageDraw.Draw(im)
    ust = font("cinzel", 26, 600)
    yazi(d, "MUSTAFA KEMAL", 70, 70, ust, GUMUS, "sol", aralik=7)
    yazi(d, "1881 – 1938", W - 70, 70, ust, ALTIN, "sag", aralik=7)

    yazi(d, "BİR ÖMÜR", W / 2, 150, font("cinzel", 104, 700), BEYAZ, aralik=6)
    yazi(d, "bir Cumhuriyet.", W / 2, 262, font("italik", 96, 600), ALTIN)

    cx, cy, r = W / 2, 745, 150
    hale(im, cx, cy, 230, (120, 96, 44), 0.35)
    d = ImageDraw.Draw(im)

    yil_f, gun_f, ack_f = font("cinzel", 50, 700), font("cinzel", 21, 600), font("italik", 31, 500)
    y0, adim = 445, 155
    sol_x, sag_x = 345, W - 345
    for i, (yil, gun, ack) in enumerate(TARIHLER):
        sag = i >= 4
        y = y0 + (i % 4) * adim
        x = sag_x if sag else sol_x
        hiza = "sol" if sag else "sag"
        yazi(d, yil, x, y, yil_f, ALTIN, hiza, aralik=2)
        yazi(d, gun, x, y + 64, gun_f, GUMUS, hiza, aralik=4)
        yazi(d, ack, x, y + 92, ack_f, BEYAZ, hiza)
        # madalyona bağlanan ince çizgi
        ny = y + 40
        bx = x + 18 if not sag else x - 18
        aci = math.atan2(ny - cy, bx - cx)
        ex, ey = cx + (r + 14) * math.cos(aci), cy + (r + 14) * math.sin(aci)
        d.line([(bx, ny), (ex, ey)], fill=CERCEVE, width=1)
        d.ellipse([bx - 4, ny - 4, bx + 4, ny + 4], fill=ALTIN_KOYU)

    # doğum madalyonu
    d.ellipse([cx - r - 12, cy - r - 12, cx + r + 12, cy + r + 12], outline=ALTIN_KOYU, width=2)
    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(14, 15, 20), outline=ALTIN, width=4)
    d.ellipse([cx - r + 10, cy - r + 10, cx + r - 10, cy + r - 10], outline=CERCEVE, width=1)
    yazi(d, "DOĞUM", cx, cy - 98, font("cinzel", 24, 600), GUMUS, aralik=6)
    yazi(d, "1881", cx, cy - 66, font("cinzel", 108, 700), ALTIN_ACIK, aralik=2)
    d.polygon([(cx, cy + 58), (cx + 6, cy + 64), (cx, cy + 70), (cx - 6, cy + 64)], fill=KIRMIZI)
    yazi(d, "Selanik", cx, cy + 74, font("italik", 40, 600), BEYAZ)

    ayrac(d, 1125)
    yazi(d, "İzindeyiz.", W / 2, 1150, font("italik", 44, 500), GUMUS)
    logo_koy(im, 1218)
    return im.convert("RGB")


def main():
    for ad, f in (("carousel-1", sayfa1), ("carousel-2", sayfa2)):
        im = f()
        im.save(DIZIN / f"{ad}.png")
        print(ad, im.size)


if __name__ == "__main__":
    main()
