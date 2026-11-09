"""10 Kasım Atatürk’ü Anma Günü carousel postu (2 sayfa, 1080x1350).

Stil: hesabın 29 Ekim postuyla aynı zarif dil. Koyu zemin, ince altın çerçeve, Cinzel Decorative başlık
(gümüş geçiş), Playfair Display italik metalik altın vurgu ve rakamlar, Cinzel küçük etiketler, kırmızı elmaslı ayraç, altta Arpama logosu.

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


ALTIN_GECIS = [(255, 236, 170), (240, 200, 112), (196, 150, 64), (232, 192, 104)]
GUMUS_GECIS = [(255, 255, 255), (232, 234, 238), (190, 196, 206)]


def font(ad, boyut, agirlik=None):
    dosya = {"cinzel": "Cinzel-var.ttf", "dekor": "CinzelDecorative-Bold.ttf",
             "playfair": "PlayfairDisplay-var.ttf", "italik": "PlayfairDisplay-Italic-var.ttf"}[ad]
    f = ImageFont.truetype(str(FONT / dosya), boyut)
    if agirlik:
        f.set_variation_by_axes([agirlik])
    return f


def _gecis(h, renkler):
    t = np.linspace(0, 1, h)[:, None]
    n = len(renkler) - 1
    i = np.minimum((t * n).astype(int), n - 1)
    f = t * n - i
    rs = np.array(renkler, np.float32)
    return rs[i[:, 0]] * (1 - f) + rs[i[:, 0] + 1] * f


def yazi(d, metin, x, y, f, renk, hiza="orta", aralik=0, golge=True):
    """renk: RGB ya da üstten alta geçiş listesi (metalik). hiza: orta | sol | sag. y = üst kenar."""
    im = d._image
    harfler = list(metin) if aralik else [metin]
    gen = sum(d.textlength(ch, font=f) for ch in harfler) + aralik * (len(harfler) - 1)
    x0 = x - gen / 2 if hiza == "orta" else x - gen if hiza == "sag" else x
    maske = Image.new("L", im.size, 0)
    md = ImageDraw.Draw(maske)
    xx = x0
    for ch in harfler:
        md.text((xx, y), ch, font=f, fill=255)
        xx += d.textlength(ch, font=f) + aralik
    kutu = maske.getbbox()
    if not kutu:
        return gen
    if golge:
        g = Image.new("RGBA", im.size, (0, 0, 0, 0))
        g.putalpha(maske.point(lambda v: int(v * 0.75)).filter(ImageFilter.GaussianBlur(max(2, f.size // 22))))
        im.alpha_composite(g, (0, max(2, f.size // 30)))
    dolgu = np.zeros((im.size[1], im.size[0], 4), np.uint8)
    if isinstance(renk, list):
        x1, y1, x2, y2 = kutu
        dolgu[y1:y2, :, :3] = _gecis(y2 - y1, renk)[:, None, :].astype(np.uint8)
    else:
        dolgu[..., :3] = renk
    dolgu[..., 3] = np.array(maske)
    im.alpha_composite(Image.fromarray(dolgu, "RGBA"))
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
    yazi(d, "SAAT 09.05", W - 70, 70, ust, ALTIN_GECIS, "sag", aralik=7)

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

    yazi(d, "ATATÜRK", W / 2, 815, font("dekor", 136), GUMUS_GECIS, aralik=4)
    yazi(d, "saygıyla anıyoruz.", W / 2, 968, font("italik", 96, 500), ALTIN_GECIS)
    ayrac(d, 1125)
    yazi(d, "10 Kasım Atatürk’ü Anma Günü", W / 2, 1150, font("italik", 38, 400), GUMUS)
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
    yazi(d, "1881 – 1938", W - 70, 70, ust, ALTIN_GECIS, "sag", aralik=7)

    yazi(d, "BİR ÖMÜR", W / 2, 140, font("dekor", 108), GUMUS_GECIS, aralik=12)
    yazi(d, "bir Cumhuriyet.", W / 2, 262, font("italik", 84, 500), ALTIN_GECIS)

    cx, cy, r = W / 2, 745, 150
    hale(im, cx, cy, 230, (120, 96, 44), 0.35)
    d = ImageDraw.Draw(im)

    yil_f, gun_f, ack_f = font("playfair", 58, 700), font("cinzel", 21, 600), font("italik", 28, 400)
    y0, adim = 445, 155
    sol_x, sag_x = 345, W - 345
    for i, (yil, gun, ack) in enumerate(TARIHLER):
        sag = i >= 4
        y = y0 + (i % 4) * adim
        x = sag_x if sag else sol_x
        hiza = "sol" if sag else "sag"
        yazi(d, yil, x, y - 18, yil_f, ALTIN_GECIS, hiza, aralik=1)
        yazi(d, gun, x, y + 64, gun_f, GUMUS, hiza, aralik=4, golge=False)
        yazi(d, ack, x, y + 94, ack_f, BEYAZ, hiza, golge=False)
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
    yazi(d, "1881", cx, cy - 96, font("playfair", 118, 700), ALTIN_GECIS, aralik=1)
    d.polygon([(cx, cy + 62), (cx + 6, cy + 68), (cx, cy + 74), (cx - 6, cy + 68)], fill=KIRMIZI)
    yazi(d, "Selanik", cx, cy + 80, font("italik", 36, 400), BEYAZ)

    ayrac(d, 1125)
    yazi(d, "İzindeyiz.", W / 2, 1150, font("italik", 38, 400), GUMUS)
    logo_koy(im, 1218)
    return im.convert("RGB")


def main():
    for ad, f in (("carousel-1", sayfa1), ("carousel-2", sayfa2)):
        im = f()
        im.save(DIZIN / f"{ad}.png")
        print(ad, im.size)


if __name__ == "__main__":
    main()
