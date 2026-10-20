"""8-bit çizim yardımcıları (CLAUDE.md §3).

İki katman vardır:
  * Sanal katman (270x480): paneller, ikonlar, yıldızlar. Sadece 16 renkli palet.
    Kare sonunda nearest-neighbor ile x4 büyütülür (1080x1920).
  * Yazı katmanı (1080x1920): piksel font (Pixelify Sans, anti-aliasing kapalı) ve
    marka yazıları (Sora 700, Manrope 500). Sprite olarak önbelleğe alınır.
"""
from functools import lru_cache
import random

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

from ortak import KOK, hex_rgb, marka

MARKA = marka()
P = {k: hex_rgb(v) for k, v in MARKA["palette"].items()}
BANT = {k: [hex_rgb(c) for c in v] for k, v in MARKA["bantlar"].items()}
FONT = {k: str(KOK / v) for k, v in MARKA["font_dosyalari"].items()}

SW, SH, OLCEK = 270, 480, 4
# Instagram güvenli alanı (sanal piksel): üst 220/4, alt 380/4, sağ 140/4
GUVENLI_UST, GUVENLI_ALT, GUVENLI_SAG = 55, SH - 95, SW - 35
# İçerik ekranda ortalı dursun diye solda da sağdaki kadar boşluk bırakılır:
# sahneler x = SOL..SAG arasında, kendi yerel koordinatlarında (0..GEN) çizilir.
SOL, SAG = SW - GUVENLI_SAG, GUVENLI_SAG
GEN = SAG - SOL

# İkon karakter -> palet rengi
KAR = {
    "0": "zemin", "1": "zemin2", "2": "zemin3", "3": "cizgi", "4": "mavi_koyu", "5": "mavi",
    "6": "mavi_acik", "7": "mavi_buz", "8": "gumus", "9": "beyaz", "a": "gumus_koyu", "b": "soluk",
    "c": "altin_acik", "d": "altin", "e": "altin_koyu", "f": "kirmizi",
}


def ust(s):
    """Türkçe büyük harf (i -> İ, ı -> I)."""
    return s.replace("i", "İ").replace("ı", "I").upper()


# ------------------------------------------------------------------ sanal katman
def yeni_kare():
    im = Image.new("RGB", (SW, SH), P["zemin"])
    return im, ImageDraw.Draw(im)


def yildizlar(d, t, hiz=0.0, tohum=1, adet=70):
    rng = random.Random(tohum)
    for i in range(adet):
        x = rng.randrange(SW)
        y0 = rng.randrange(SH)
        y = int(y0 + hiz * t * (1 + i % 3)) % SH
        faz = rng.random()
        parlak = ((t * 1.5 + faz) % 1.0) < 0.82
        renk = P["mavi_buz"] if (i % 3 == 0 and parlak) else P["soluk"] if parlak else P["cizgi"]
        d.point((x, y), fill=renk)
        if i % 17 == 0 and parlak:
            d.point([(x - 1, y), (x + 1, y), (x, y - 1), (x, y + 1)], fill=P["cizgi"])


def panel(d, x, y, w, h, bant=3):
    """Kart: zemin3 üst bant + zemin2 gövde + 1px cizgi kenarlık."""
    d.rectangle([x, y, x + w - 1, y + h - 1], fill=P["zemin2"], outline=P["cizgi"])
    d.rectangle([x + 1, y + 1, x + w - 2, y + bant], fill=P["zemin3"])


def dugme(d, x, y, w, h, renk="mavi"):
    """Mavi düğme: açık üst kenar + gövde + koyu alt kenar."""
    ust_r, govde, alt_r = BANT[renk] if renk in BANT else BANT["mavi"]
    d.rectangle([x, y, x + w - 1, y + h - 1], fill=govde)
    d.rectangle([x, y, x + w - 1, y + 1], fill=ust_r)
    d.rectangle([x, y + h - 2, x + w - 1, y + h - 1], fill=alt_r)


def bant_dikdortgen(d, x, y, w, h, renkler):
    n = len(renkler)
    for i, r in enumerate(renkler):
        y0 = y + h * i // n
        y1 = y + h * (i + 1) // n - 1
        d.rectangle([x, y0, x + w - 1, y1], fill=r)


def ikon(d, sablon, x, y, olcek=1, renk_degis=None):
    satirlar = [s for s in sablon.strip("\n").split("\n")]
    for j, satir in enumerate(satirlar):
        for i, c in enumerate(satir):
            if c in (".", " "):
                continue
            ad = KAR[c]
            if renk_degis and ad in renk_degis:
                ad = renk_degis[ad]
            d.rectangle([x + i * olcek, y + j * olcek, x + (i + 1) * olcek - 1, y + (j + 1) * olcek - 1], fill=P[ad])


def ikon_boyut(sablon, olcek=1):
    s = sablon.strip("\n").split("\n")
    return max(len(r) for r in s) * olcek, len(s) * olcek


def daire(d, cx, cy, r, renk):
    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=renk)


def xp_bar(d, x, y, w, oran, renk="mavi"):
    d.rectangle([x, y, x + w - 1, y + 4], fill=P["zemin2"], outline=P["cizgi"])
    dolu = int((w - 2) * max(0.0, min(1.0, oran)))
    if dolu > 0:
        bant_dikdortgen(d, x + 1, y + 1, dolu, 3, BANT[renk])


# ------------------------------------------------------------------ geçiş efektleri
_BAYER = np.array([[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]]) / 16.0


def dither_maske(w, h, oran, blok=1):
    """oran 0..1: açılan piksel oranı (Bayer 4x4, adımlı)."""
    ky, kx = (h + 3) // 4 + 1, (w + 3) // 4 + 1
    m = np.tile(_BAYER, (ky, kx))[:h, :w]
    return m < oran


def glitch(arr, siddet, tohum):
    """Yatay şerit kaydırma (sanal piksel dizisi üzerinde)."""
    rng = np.random.default_rng(tohum)
    out = arr.copy()
    for _ in range(int(6 * siddet) + 1):
        y = rng.integers(0, arr.shape[0] - 8)
        h = rng.integers(2, 10)
        kay = int(rng.integers(-12, 12) * siddet)
        out[y:y + h] = np.roll(out[y:y + h], kay, axis=1)
    return out


# ------------------------------------------------------------------ yazı katmanı
@lru_cache(maxsize=64)
def font(ad, boyut):
    return ImageFont.truetype(FONT[ad], boyut)


PIKSEL_FONTLAR = {"piksel", "piksel_ince", "piksel_yedek", "ingilizce_etiket"}


def font_sec(metin, ad, boyut):
    """Piksel yazılar VT323 ile basılır.

    Pixelify Sans'ın statik sürümünde büyük harfler birbirine karışıyor (Z=2, B=G, C=O, 5=S);
    videoda okunmuyor. VT323 1000 birimlik em'de 40 birimlik ızgaraya oturur: boyut 25'in katı
    olunca her font pikseli tam sayı ekran pikseline denk gelir (100 -> 4px = 1 sanal piksel).
    `boyut` Pixelify ölçeğinde verilir, burada VT323 karşılığına çevrilir.
    """
    if ad in ("piksel", "piksel_ince"):
        return "piksel_yedek", max(50, int(round(boyut * 1.5 / 25)) * 25)
    return ad, boyut


@lru_cache(maxsize=2048)
def yazi(metin, ad="piksel", boyut=63, renk="gumus", bant=None, kenar=0, kenar_renk="zemin"):
    """Yazıyı RGBA sprite olarak döndürür.

    renk: palet adı. bant: 'altin' | 'gumus' | 'mavi' (yatay 3 bant).
    kenar: kenar çizgisi kalınlığı (gerçek piksel).
    """
    ad, boyut = font_sec(metin, ad, boyut)
    f = font(ad, boyut)
    piksel = ad in PIKSEL_FONTLAR
    sol, ust_, sag, alt = f.getbbox(metin)
    w, h = sag - sol + 2 * kenar + 2, alt - ust_ + 2 * kenar + 2
    maske = Image.new("L", (w, h), 0)
    md = ImageDraw.Draw(maske)
    md.fontmode = "1" if piksel else "L"
    md.text((kenar + 1 - sol, kenar + 1 - ust_), metin, font=f, fill=255)
    renkli = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    if bant:
        renkler = BANT[bant]
        dolu = np.array(maske) > 0
        satirlar = np.where(dolu.any(axis=1))[0]
        y0, y1 = (satirlar[0], satirlar[-1] + 1) if len(satirlar) else (0, h)
        katman = np.zeros((h, w, 4), dtype=np.uint8)
        for i, r in enumerate(renkler):
            a = y0 + (y1 - y0) * i // len(renkler)
            b = y0 + (y1 - y0) * (i + 1) // len(renkler)
            if i == len(renkler) - 1:
                b = h
            if i == 0:
                a = 0
            # bant sınırlarını 4px'e (sanal piksel) yuvarla
            katman[a:b, :, :3] = r
        katman[..., 3] = np.array(maske)
        renkli = Image.fromarray(katman, "RGBA")
    else:
        renkli.paste(Image.new("RGBA", (w, h), P[renk] + (255,)), (0, 0), maske)
    if kenar:
        dis = maske.filter(ImageFilter.MaxFilter(2 * kenar + 1))
        if piksel:
            dis = dis.point(lambda v: 255 if v > 0 else 0)
        taban = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        taban.paste(Image.new("RGBA", (w, h), P[kenar_renk] + (255,)), (0, 0), dis)
        taban.alpha_composite(renkli)
        renkli = taban
    return renkli


def yazi_genislik(metin, ad="piksel", boyut=63):
    ad, boyut = font_sec(metin, ad, boyut)
    s, _, e, _ = font(ad, boyut).getbbox(metin)
    return e - s


class Kaydir:
    """ImageDraw sarmalayıcı: tüm x koordinatlarını dx kadar kaydırır (sahne yerel koordinatı)."""

    def __init__(self, d, dx):
        self._d, self._dx = d, dx

    def _xy(self, xy):
        if xy and isinstance(xy[0], (tuple, list)):
            return [(x + self._dx, y) for x, y in xy]
        if isinstance(xy, tuple) and len(xy) == 2:
            return (xy[0] + self._dx, xy[1])
        return [v + self._dx if i % 2 == 0 else v for i, v in enumerate(xy)]

    def rectangle(self, xy, **kw):
        return self._d.rectangle(self._xy(xy), **kw)

    def ellipse(self, xy, **kw):
        return self._d.ellipse(self._xy(xy), **kw)

    def polygon(self, xy, **kw):
        return self._d.polygon(self._xy(xy), **kw)

    def point(self, xy, **kw):
        return self._d.point(self._xy(xy) if not isinstance(xy, tuple) else self._xy(xy), **kw)

    def line(self, xy, **kw):
        return self._d.line(self._xy(xy), **kw)


class YaziKatmani:
    """Bir karede çizilecek yazı sprite'larının listesi (gerçek piksel koordinatı)."""

    def __init__(self, dx=0):
        self.ops = []
        self.dx = dx

    def ekle(self, sprite, x, y, hiza="sol", maske=None):
        x += self.dx
        if hiza == "orta":
            x -= sprite.width // 2
        elif hiza == "sag":
            x -= sprite.width
        self.ops.append((sprite, int(x), int(y), maske))

    def yaz(self, metin, x, y, hiza="sol", **kw):
        self.ekle(yazi(metin, **kw), x, y, hiza)

    def uygula(self, im):
        for sprite, x, y, maske in self.ops:
            if maske is not None:
                a = np.array(sprite.getchannel("A"))
                a = np.where(maske[: a.shape[0], : a.shape[1]], a, 0).astype(np.uint8)
                sprite = sprite.copy()
                sprite.putalpha(Image.fromarray(a))
            im.alpha_composite(sprite, (x, y)) if im.mode == "RGBA" else im.paste(sprite, (x, y), sprite)
