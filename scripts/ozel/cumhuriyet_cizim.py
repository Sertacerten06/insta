"""29 Ekim özel bölümü için 8-bit çizim parçaları: bayrak, harita, bina, defter, havai fişek.

Marka paletine (16 renk) bu bölüm için gerçek bayrak kırmızısı ve gece/lamba/kâğıt tonları eklenir.
Bayrak ölçüleri Türk Bayrağı Kanunu'ndaki oranlara göre çizilir (G = yükseklik).
"""
import math
import random
from functools import lru_cache

import numpy as np
from PIL import Image, ImageDraw

from cizim import P, SW, SH

EK_RENK = {
    "bayrak": (227, 10, 23), "bayrak_koyu": (158, 8, 18), "bayrak_acik": (255, 74, 74),
    "gece1": (6, 9, 22), "gece2": (14, 22, 48), "gece3": (30, 42, 82), "ufuk": (64, 58, 98),
    "lamba": (255, 196, 102), "lamba_koyu": (214, 130, 48), "lamba_acik": (255, 236, 170),
    "ahsap": (96, 60, 36), "ahsap_koyu": (56, 34, 22), "ahsap_acik": (134, 88, 52),
    "duvar": (34, 30, 40), "duvar_acik": (58, 48, 56),
    "kagit": (236, 224, 192), "kagit_koyu": (200, 182, 142), "murekkep": (36, 28, 40),
    "deniz": (12, 26, 54), "deniz_acik": (22, 44, 86), "kara": (54, 74, 104), "kara_acik": (84, 108, 140),
    "komsu": (22, 30, 44), "tas": (150, 136, 120), "tas_koyu": (104, 92, 84), "kiremit": (150, 64, 46),
}
P.update(EK_RENK)  # yazi() renkleri P'den okur

BAYER = np.array([[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]]) / 16.0
_BY = np.tile(BAYER, (SH // 4 + 1, SW // 4 + 1))[:SH, :SW]


def c(ad):
    return P[ad]


# ------------------------------------------------------------------ dither yardımcıları
def gradyan(arr, y0, y1, renkler, x0=0, x1=SW):
    """arr[y0:y1, x0:x1] bölgesini renkler arasında Bayer dither'lı dikey geçişle doldurur."""
    n = len(renkler) - 1
    rs = np.array([c(r) if isinstance(r, str) else r for r in renkler], dtype=np.uint8)
    ys = np.arange(y0, y1)
    v = (ys - y0) / max(1, (y1 - y0 - 1)) * n
    i = np.clip(np.floor(v).astype(int), 0, n - 1)
    f = v - i
    esik = _BY[y0:y1, x0:x1]
    ust = esik < f[:, None]
    idx = i[:, None] + ust
    arr[y0:y1, x0:x1] = rs[idx]


def isik(arr, cx, cy, r, renk, guc=1.0, bayer=True):
    """Yuvarlak ışık halesi: merkeze yakın pikseller dither ile renge çekilir (yarı saydam his)."""
    y0, y1 = max(0, int(cy - r)), min(SH, int(cy + r) + 1)
    x0, x1 = max(0, int(cx - r)), min(SW, int(cx + r) + 1)
    if y0 >= y1 or x0 >= x1:
        return
    yy, xx = np.mgrid[y0:y1, x0:x1]
    d = np.sqrt((xx - cx) ** 2 + (yy - cy) ** 2) / r
    oran = np.clip(1 - d, 0, 1) ** 1.6 * guc
    m = _BY[y0:y1, x0:x1] < oran * 0.55
    hedef = np.array(c(renk) if isinstance(renk, str) else renk, dtype=np.float32)
    bolge = arr[y0:y1, x0:x1].astype(np.float32)
    karisim = bolge * 0.55 + hedef * 0.45
    arr[y0:y1, x0:x1] = np.where(m[..., None], karisim, bolge).astype(np.uint8)


def karart(arr, oran):
    """Bayer deseniyle karartma (0 = değişmez, 1 = tamamen zemin)."""
    if oran <= 0:
        return arr
    m = _BY < oran
    return np.where(m[..., None], np.array(c("gece1"), dtype=np.uint8), arr)


def gecis(eski, yeni, oran, blok=2):
    """İki kare arasında blok blok dither geçişi."""
    by = np.repeat(np.repeat(BAYER, blok, 0), blok, 1)
    m = np.tile(by, (SH // (4 * blok) + 1, SW // (4 * blok) + 1))[:SH, :SW] < oran
    return np.where(m[..., None], yeni, eski)


# ------------------------------------------------------------------ gökyüzü
def yildiz_ciz(d, t, tohum=3, adet=60, ymax=200):
    rng = random.Random(tohum)
    for i in range(adet):
        x, y = rng.randrange(SW), rng.randrange(ymax)
        faz = rng.random()
        parlak = ((t * 0.7 + faz) % 1.0) < 0.85
        renk = c("mavi_buz") if i % 4 == 0 and parlak else c("soluk") if parlak else c("gece3")
        d.point((x, y), fill=renk)
        if i % 13 == 0 and parlak:
            d.point([(x - 1, y), (x + 1, y), (x, y - 1), (x, y + 1)], fill=c("gece3"))


# ------------------------------------------------------------------ bayrak
@lru_cache(maxsize=8)
def bayrak_maskesi(h):
    """Türk bayrağı (oran 2:3). 0 = kırmızı, 1 = beyaz. Kanun ölçüleri:
    ay dış çember merkezi göndere 1/2 G, çapı 1/2 G; iç çember merkezi 1/16 G ileride, çapı 0,4 G;
    yıldız çevrel çember çapı 1/4 G, iç çemberden 1/3 G uzakta; yıldızın bir ucu göndere bakar."""
    o = 4  # süper örnekleme
    G = h * o
    W = int(round(1.5 * G))
    yy, xx = np.mgrid[0:G, 0:W] + 0.5
    cy = G / 2
    dis = (xx - 0.5 * G) ** 2 + (yy - cy) ** 2 <= (0.25 * G) ** 2
    ic = (xx - (0.5 + 0.0625) * G) ** 2 + (yy - cy) ** 2 <= (0.2 * G) ** 2
    ay = dis & ~ic
    # yıldız: iç çemberin sol kenarından 1/3 G sonra başlayan 1/4 G çaplı çemberin içinde
    ic_sol = (0.5 + 0.0625 - 0.2) * G
    sx = ic_sol + G / 3 + 0.125 * G
    r_dis, r_ic = 0.125 * G, 0.125 * G * 0.382
    kose = []
    for k in range(10):
        a = math.pi + k * math.pi / 5  # ilk uç sola (göndere) bakar
        r = r_dis if k % 2 == 0 else r_ic
        kose.append((sx + r * math.cos(a), cy + r * math.sin(a)))
    yim = Image.new("L", (W, G), 0)
    ImageDraw.Draw(yim).polygon(kose, fill=255)
    yildiz = np.array(yim) > 0
    beyaz = (ay | yildiz).astype(np.float32)
    kucuk = beyaz.reshape(h, o, W // o, o).mean(axis=(1, 3))
    return (kucuk > 0.45).astype(np.uint8)


def bayrak_ciz(arr, x0, y0, h, t, dalga=1.0, gondere=True, direk_alt=None):
    """Dalgalanan bayrak. Göndere bağlı kenar sabit, uca doğru dalga büyür; eğime göre 3 ton gölge."""
    m = bayrak_maskesi(h)
    H, W = m.shape
    renk = {0: [c("bayrak_koyu"), c("bayrak"), c("bayrak_acik")],
            1: [c("gumus_koyu"), c("gumus"), c("beyaz")]}
    lam = W * 0.85
    for x in range(W):
        u = x / W
        faz = 2 * math.pi * (x / lam - 0.9 * t)
        genlik = dalga * (0.5 + 2.6 * u) * h / 26
        dy = genlik * math.sin(faz)
        egim = math.cos(faz) * dalga * (0.3 + u)
        ton = 1 + (1 if egim > 0.45 else -1 if egim < -0.45 else 0)
        # yatay sıkışma: dalga tepesinde sütunlar hafif kayar
        for y in range(H):
            yy = int(round(y0 + y + dy))
            xx = x0 + x
            if 0 <= yy < SH and 0 <= xx < SW:
                tt = ton
                if tt == 1 and ((x + y) % 2 == 0) and abs(egim) > 0.3:
                    tt = 2 if egim > 0 else 0
                arr[yy, xx] = renk[int(m[y, x])][tt]
    if gondere:
        alt = direk_alt if direk_alt is not None else y0 + H + h
        arr[y0 - 3:alt, x0 - 3:x0 - 1] = c("gumus_koyu")
        arr[y0 - 3:alt, x0 - 3] = c("beyaz")
        arr[y0 - 6:y0 - 3, x0 - 4:x0] = c("altin")
        arr[y0 - 7, x0 - 3:x0 - 1] = c("altin_acik")


# ------------------------------------------------------------------ harita (Türkiye kıyı ve sınır hattı, yaklaşık)
LON0, LON1, LAT0, LAT1 = 25.6, 45.2, 35.6, 42.3
ANADOLU = [
    (29.05, 41.2), (29.9, 41.15), (30.5, 41.2), (31.4, 41.3), (32.3, 41.73), (33.3, 42.0), (34.2, 41.95),
    (35.0, 42.08), (35.2, 41.7), (36.0, 41.7), (36.4, 41.25), (37.0, 41.15), (37.7, 41.05), (38.4, 40.93),
    (39.7, 41.03), (40.6, 41.03), (41.4, 41.4), (41.55, 41.53), (42.5, 41.45), (42.8, 41.58), (43.45, 41.18),
    (43.7, 40.75), (43.6, 40.45), (43.9, 40.0), (44.6, 39.75), (44.82, 39.65), (44.35, 39.4), (44.45, 38.95),
    (44.3, 38.4), (44.45, 38.0), (44.25, 37.95), (44.8, 37.3), (44.79, 37.15), (44.3, 37.05), (43.4, 37.3),
    (42.8, 37.35), (42.35, 37.1), (41.2, 37.07), (40.2, 36.95), (39.0, 36.7), (38.2, 36.85), (37.6, 36.75),
    (37.0, 36.65), (36.7, 36.82), (36.6, 36.25), (36.4, 35.95), (36.15, 35.82), (35.9, 35.92), (35.95, 36.15),
    (35.8, 36.32), (36.17, 36.58), (36.2, 36.85), (35.7, 36.62), (35.5, 36.58), (34.9, 36.75), (34.63, 36.8),
    (34.0, 36.3), (33.5, 36.15), (32.8, 36.03), (32.0, 36.5), (31.3, 36.8), (30.7, 36.88), (30.55, 36.5),
    (30.4, 36.2), (29.7, 36.15), (29.1, 36.6), (28.6, 36.8), (28.0, 36.6), (27.5, 36.95), (27.25, 37.05),
    (27.3, 37.5), (27.25, 37.85), (26.6, 38.1), (26.3, 38.3), (26.4, 38.5), (26.9, 38.45), (27.1, 38.42),
    (26.8, 38.75), (26.85, 39.05), (26.6, 39.3), (26.1, 39.47), (26.2, 39.95), (26.4, 40.15), (26.7, 40.4),
    (27.3, 40.4), (27.9, 40.4), (28.4, 40.4), (28.9, 40.42), (29.1, 40.45), (29.95, 40.73), (29.4, 40.8),
    (29.05, 41.0),
]
TRAKYA = [
    (26.05, 40.73), (26.6, 40.62), (26.8, 40.55), (26.5, 40.3), (26.18, 40.05), (26.4, 40.2), (26.7, 40.42),
    (27.3, 40.65), (27.5, 40.97), (28.0, 41.05), (28.6, 41.0), (29.0, 41.02), (29.05, 41.22), (28.6, 41.4),
    (28.1, 41.6), (27.95, 41.98), (27.4, 42.0), (26.6, 41.85), (26.35, 41.75), (26.6, 41.35), (26.3, 40.95),
]
KARADENIZ = [(25.6, 42.3), (45.2, 42.3), (41.75, 42.3), (41.6, 41.6), (41.55, 41.53)]
VAN = [(42.35, 38.6), (42.8, 38.95), (43.3, 38.95), (43.6, 38.6), (43.1, 38.35), (42.6, 38.35)]
TUZ = [(33.25, 39.0), (33.55, 38.95), (33.6, 38.6), (33.35, 38.62)]


class Harita:
    """Türkiye haritası. Kıyı ve sınırlar sade (8-bit) çizim içindir, ölçek temsilidir."""

    def __init__(self, x0=17, x1=253, y0=118):
        self.x0, self.x1, self.y0 = x0, x1, y0
        self.k = (x1 - x0) / ((LON1 - LON0) * 0.777)
        self.y1 = y0 + (LAT1 - LAT0) * self.k
        self._taban = None

    def xy(self, lon, lat):
        return (self.x0 + (lon - LON0) * 0.777 * self.k, self.y0 + (LAT1 - lat) * self.k)

    def ixy(self, lon, lat):
        x, y = self.xy(lon, lat)
        return int(round(x)), int(round(y))

    def taban(self):
        if self._taban is not None:
            return self._taban
        im = Image.new("RGB", (SW, SH), c("deniz"))
        d = ImageDraw.Draw(im)
        y0, y1 = self.y0 - 6, int(self.y1) + 6
        # komşu kara parçaları: Balkanlar, Kafkasya, İran, Irak, Suriye (koyu)
        komsu = [self.xy(*p) for p in [(25.6, 42.3), (27.9, 42.3), (28.0, 41.95), (27.4, 42.0), (26.6, 41.85),
                                       (26.35, 41.75), (26.6, 41.35), (26.3, 40.95), (26.05, 40.73), (25.6, 40.85)]]
        d.polygon(komsu, fill=c("komsu"))
        dogu = [self.xy(*p) for p in [(41.6, 41.6), (41.75, 42.3), (45.2, 42.3), (45.2, 35.6), (35.85, 35.6),
                                      (35.9, 35.92), (36.15, 35.82), (36.4, 35.95), (36.6, 36.25), (36.7, 36.82),
                                      (37.0, 36.65), (39.0, 36.7), (41.2, 37.07), (42.35, 37.1), (44.3, 37.05),
                                      (44.79, 37.15), (44.8, 37.3), (44.25, 37.95), (44.45, 38.0), (44.3, 38.4),
                                      (44.45, 38.95), (44.35, 39.4), (44.82, 39.65), (44.6, 39.75), (43.9, 40.0),
                                      (43.6, 40.45), (43.7, 40.75), (43.45, 41.18), (42.8, 41.58), (42.5, 41.45),
                                      (41.55, 41.53)]]
        d.polygon(dogu, fill=c("komsu"))
        for poly in (ANADOLU, TRAKYA):
            d.polygon([self.xy(*p) for p in poly], fill=c("kara"))
        for poly in (VAN, TUZ):
            d.polygon([self.xy(*p) for p in poly], fill=c("deniz_acik"))
        arr = np.array(im)
        # kara dokusu: seyrek açık noktalar (piksel sanat dokusu)
        kara = np.all(arr == c("kara"), axis=-1)
        doku = (_BY < 0.07) & kara
        arr[doku] = c("kara_acik")
        # kıyı çizgisi: kara pikselinin denize komşu olduğu yerler
        deniz = np.all(arr == c("deniz"), axis=-1) | np.all(arr == c("deniz_acik"), axis=-1)
        komsu_m = np.all(arr == c("komsu"), axis=-1)
        kara = np.all(arr == c("kara"), axis=-1) | np.all(arr == c("kara_acik"), axis=-1)
        kenar = np.zeros_like(kara)
        for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            kenar |= np.roll(np.roll(deniz, dy, 0), dx, 1)
        arr[kara & kenar] = c("kara_acik")
        sinir = np.zeros_like(kara)
        for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            sinir |= np.roll(np.roll(komsu_m, dy, 0), dx, 1)
        arr[kara & sinir & ~kenar] = c("mavi_acik")
        # haritanın dışını sahne zeminine bırak (üst/alt yumuşak kesim)
        maske = np.zeros(arr.shape[:2], bool)
        maske[max(0, y0):min(SH, y1)] = True
        self._taban = (arr, maske)
        return self._taban

    def ciz(self, arr, t, parlaklik=1.0):
        taban, maske = self.taban()
        out = np.where(maske[..., None], taban, arr)
        # deniz parıltısı
        deniz = maske & np.all(taban == c("deniz"), axis=-1)
        dalga = (np.roll(_BY, int(t * 3) % 4, axis=1) < 0.04) & deniz
        out[dalga] = c("deniz_acik")
        arr[:] = out
        # üst/alt kenarı dither ile eriterek sahneye bağla
        for k in range(6):
            for yb in (int(self.y0) - 6 + k, int(self.y1) + 6 - k - 1):
                if 0 <= yb < SH:
                    sat = _BY[yb] < (1 - k / 6)
                    arr[yb][sat] = c("gece1")


# ------------------------------------------------------------------ küçük sprite'lar
def pim(d, x, y, renk="altin", parla=False):
    """Harita iğnesi: ucu (x, y)."""
    r, k = c(renk), c("gece1")
    d.rectangle([x - 2, y - 7, x + 2, y - 3], fill=r, outline=k)
    d.point([(x, y - 2), (x, y - 1), (x, y)], fill=r)
    d.point((x - 1, y - 6), fill=c("beyaz"))
    if parla:
        d.point([(x - 4, y - 5), (x + 4, y - 5), (x, y - 10)], fill=c("altin_acik"))


def isgal_isareti(d, x, y, t, faz=0.0):
    """İşgal bölgesi: kırmızı çapraz taramalı küçük leke, yavaş nabız."""
    r = 4 + int((math.sin(t * 4 + faz) + 1) * 0.8)
    for yy in range(y - r, y + r + 1):
        for xx in range(x - r, x + r + 1):
            if (xx - x) ** 2 + (yy - y) ** 2 <= r * r and (xx + yy) % 3 == 0:
                d.point((xx, yy), fill=c("kirmizi"))
    d.point((x, y), fill=c("bayrak_acik"))


def gemi(d, x, y):
    """Küçük buharlı gemi (sağa bakar)."""
    k = c("gece1")
    d.polygon([(x - 8, y), (x + 8, y), (x + 6, y + 3), (x - 6, y + 3)], fill=c("gumus_koyu"), outline=k)
    d.rectangle([x - 4, y - 3, x + 3, y - 1], fill=c("gumus"), outline=k)
    d.rectangle([x - 1, y - 7, x + 1, y - 4], fill=c("bayrak_koyu"))
    d.point([(x - 2, y - 9), (x - 3, y - 10), (x - 5, y - 11)], fill=c("soluk"))


def kilic_ciz(d, x, y):
    for s in (1, -1):
        d.line([(x - 5 * s, y - 5), (x + 5 * s, y + 5)], fill=c("gumus"))
        d.point((x + 5 * s, y + 5), fill=c("beyaz"))
        d.line([(x - 6 * s, y - 2), (x - 2 * s, y - 6)], fill=c("altin"))


def ok_ciz(d, noktalar, oran, renk="altin", t=0.0):
    """Kesikli ilerleyen ok. noktalar: [(x, y)], oran 0..1 çizilen kısım."""
    toplam = sum(math.dist(a, b) for a, b in zip(noktalar, noktalar[1:]))
    hedef = toplam * max(0.0, min(1.0, oran))
    gidilen, son = 0.0, noktalar[0]
    for a, b in zip(noktalar, noktalar[1:]):
        L = math.dist(a, b)
        n = max(1, int(L))
        for i in range(n):
            if gidilen + i > hedef:
                break
            p = (a[0] + (b[0] - a[0]) * i / n, a[1] + (b[1] - a[1]) * i / n)
            if int(gidilen + i - t * 8) % 5 < 3:
                d.rectangle([p[0] - 1, p[1] - 1, p[0], p[1]], fill=c(renk))
            son = p
        gidilen += L
        if gidilen > hedef:
            break
    if oran > 0.05:
        # ok ucu
        a, b = noktalar[-2], noktalar[-1]
        if oran < 1:
            b = son
        ang = math.atan2(b[1] - a[1], b[0] - a[0])
        uc = [(b[0] + 4 * math.cos(ang), b[1] + 4 * math.sin(ang)),
              (b[0] + 4 * math.cos(ang + 2.4), b[1] + 4 * math.sin(ang + 2.4)),
              (b[0] + 4 * math.cos(ang - 2.4), b[1] + 4 * math.sin(ang - 2.4))]
        d.polygon(uc, fill=c(renk))


def meclis_binasi(d, arr, cx, taban_y, t, isik_oran=1.0):
    """Birinci TBMM binası (Ulus): iki katlı taş bina, kemerli pencereler, kiremit çatı, ortada giriş."""
    w, h = 150, 54
    x0, x1 = cx - w // 2, cx + w // 2
    y0 = taban_y - h
    d.rectangle([x0, y0, x1, taban_y], fill=c("tas_koyu"))
    # taş sıraları
    for yy in range(y0 + 3, taban_y, 4):
        d.line([(x0, yy), (x1, yy)], fill=c("duvar_acik"))
    # kat silmesi
    d.rectangle([x0 - 2, y0 + 25, x1 + 2, y0 + 27], fill=c("tas"))
    d.rectangle([x0 - 2, y0 - 1, x1 + 2, y0 + 1], fill=c("tas"))
    # çatı
    d.polygon([(x0 - 6, y0 - 1), (x1 + 6, y0 - 1), (x1 - 8, y0 - 12), (x0 + 8, y0 - 12)], fill=c("kiremit"))
    d.line([(x0 - 6, y0 - 1), (x1 + 6, y0 - 1)], fill=c("ahsap_koyu"))
    # orta çıkıntı (giriş)
    d.rectangle([cx - 16, y0 - 4, cx + 16, taban_y], fill=c("tas"))
    d.polygon([(cx - 19, y0 - 4), (cx + 19, y0 - 4), (cx, y0 - 14)], fill=c("kiremit"))
    d.rectangle([cx - 5, taban_y - 14, cx + 5, taban_y], fill=c("ahsap_koyu"))
    d.rectangle([cx - 4, taban_y - 18, cx + 4, taban_y - 15], fill=c("ahsap_koyu"))
    rng = random.Random(5)
    for kat, wy in enumerate((y0 + 7, y0 + 32)):
        for i in range(10):
            wx = x0 + 8 + i * 14
            if cx - 20 < wx + 3 and wx < cx + 20:
                continue
            yanik = rng.random() < isik_oran + 0.2 and (rng.random() + 0.0) < isik_oran * 1.1
            renk = c("lamba") if yanik else c("gece2")
            d.rectangle([wx, wy + 2, wx + 6, wy + 13], fill=renk)
            d.rectangle([wx + 1, wy, wx + 5, wy + 1], fill=renk)
            d.line([(wx + 3, wy + 1), (wx + 3, wy + 13)], fill=c("tas_koyu"))
            if yanik:
                isik(arr, wx + 3, wy + 8, 9, "lamba_koyu", 0.35)
    # orta pencereler (üst kat)
    for wx in (cx - 11, cx + 5):
        d.rectangle([wx, y0 + 9, wx + 6, y0 + 20], fill=c("lamba") if isik_oran > 0.3 else c("gece2"))
    return y0 - 14  # çatı tepesi


def havai_fisek(d, t, tohum, cx, cy, renkler=("bayrak_acik", "beyaz", "altin_acik"), r=24):
    """t: patlamadan beri geçen süre. 1,8 sn'de söner."""
    if t < 0 or t > 1.8:
        return
    rng = random.Random(tohum)
    renk = c(rng.choice(renkler))
    n = 22
    yayil = r * (1 - math.exp(-t * 3.2))
    dus = 6 * t * t
    for i in range(n):
        a = 2 * math.pi * i / n + rng.random() * 0.2
        rr = yayil * (0.75 + 0.25 * rng.random())
        x, y = cx + rr * math.cos(a), cy + rr * math.sin(a) + dus
        if t > 1.2 and (i + int(t * 20)) % 3 == 0:
            continue
        d.point((x, y), fill=renk)
        if t < 0.9:
            x2, y2 = cx + rr * 0.8 * math.cos(a), cy + rr * 0.8 * math.sin(a) + dus * 0.8
            d.point((x2, y2), fill=c("gece3") if t > 0.5 else renk)
    if t < 0.15:
        d.rectangle([cx - 2, cy - 2, cx + 2, cy + 2], fill=c("beyaz"))


def yukselen(d, t, x, hedef_y, taban_y=300, sure=0.6):
    """Havai fişeğin yükselen izi (t: 0..sure)."""
    if 0 <= t < sure:
        y = taban_y + (hedef_y - taban_y) * (t / sure)
        d.point([(x, y), (x, y + 2)], fill=c("altin_acik"))
        d.point((x, y + 4), fill=c("lamba_koyu"))
