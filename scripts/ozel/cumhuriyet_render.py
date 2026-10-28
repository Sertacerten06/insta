"""29 Ekim özel bölümü: görüntü render'ı (Python + Pillow + FFmpeg).

Girdi : ozel/29ekim/senaryo.json, ozel/29ekim/ses/*.json (cumhuriyet_tts.py çıktısı)
Çıktı : ozel/29ekim/ara/zaman.json, ozel/29ekim/ara/video.mp4, ozel/29ekim/kapak.png

Sahneler kelime zamanlarına bağlıdır: anlatıcı "Samsun" dediğinde iğne Samsun'a düşer.
Arpama logosu yalnızca açılışta görünür; Haritam reklamı yoktur.

Kullanım:
  python scripts/ozel/cumhuriyet_render.py
  python scripts/ozel/cumhuriyet_render.py --kareler 3,20,45     # yalnızca önizleme kareleri
"""
import argparse
import json
import math
import random
import subprocess
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

KOK = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(KOK / "scripts"), str(KOK / "scripts" / "render"), str(KOK / "scripts" / "ozel")]
from cizim import OLCEK, SH, SW, YaziKatmani, yazi, yazi_genislik  # noqa: E402
import cumhuriyet_cizim as C  # noqa: E402
from cumhuriyet_cizim import c  # noqa: E402
from render import altyazi_ciz, altyazi_sayfalari  # noqa: E402
from sahneler import logo, sade  # noqa: E402

DIZIN = KOK / "ozel" / "29ekim"
FPS = 30
ARA = 0.45          # ses bitimi -> sonraki sahne
GECIS = 0.5         # sahneler arası dither geçişi
RX = SW * OLCEK // 2  # gerçek piksel yatay orta

H = C.Harita()
SEHIR = {
    "istanbul": (28.98, 41.01), "samsun": (36.33, 41.29), "amasya": (35.83, 40.65), "erzurum": (41.27, 39.9),
    "sivas": (37.02, 39.75), "ankara": (32.86, 39.93), "sakarya": (32.14, 39.58), "afyon": (30.45, 38.72),
    "dumlupinar": (29.98, 38.85), "izmir": (27.14, 38.42), "antalya": (30.71, 36.9), "adana": (35.32, 37.0),
    "antep": (37.38, 37.07), "urfa": (38.79, 37.16),
}
ISGAL = ["istanbul", "izmir", "antalya", "adana", "antep", "urfa"]


def hx(ad):
    return H.ixy(*SEHIR[ad])


def ease(t0, sure, t):
    if t <= t0:
        return 0.0
    if t >= t0 + sure:
        return 1.0
    u = (t - t0) / sure
    return u * u * (3 - 2 * u)


def R(v):
    return int(round(v * OLCEK))


# ------------------------------------------------------------------ yazı yardımcıları
def yaz(yk, metin, x, y, hiza="orta", boyut=67, renk="gumus", bant=None, kenar=6, ad="piksel"):
    yk.ekle(yazi(metin, ad, boyut, renk=renk, bant=bant, kenar=kenar, kenar_renk="gece1"), x, y, hiza)


def daktilo(metin, oran):
    n = int(round(len(metin) * max(0.0, min(1.0, oran))))
    return metin[:n]


def kart(d, yk, satirlar, y, t_bas, lt, renk="altin", genislik=208, ust_boyut=67, alt_boyut=50):
    """Alt bilgi kartı: tarih (altın) + açıklama (gümüş). Soldan kayarak gelir."""
    if lt < t_bas:
        return
    u = ease(t_bas, 0.35, lt)
    x0 = int((SW - genislik) / 2 - (1 - u) * 30)
    hgt = 38 if len(satirlar) > 1 else 22
    d.rectangle([x0, y, x0 + genislik, y + hgt], fill=c("gece1"), outline=c("cizgi"))
    d.rectangle([x0, y, x0 + 2, y + hgt], fill=c(renk))
    cx = R(x0 + genislik / 2 + 1)
    yaz(yk, satirlar[0], cx, R(y) + 10, boyut=ust_boyut, bant=renk, kenar=0)
    if len(satirlar) > 1:
        yaz(yk, satirlar[1], cx, R(y) + 96, boyut=alt_boyut, renk="gumus", kenar=0)


def sehir_etiketi(yk, ad, x, y, renk="beyaz", alt=False):
    yaz(yk, ad, R(x), R(y + (3 if alt else -20)), boyut=34, renk=renk, kenar=6)


# ------------------------------------------------------------------ sahne tabanı
class Sahne:
    yil = None   # zaman çizgisi göstergesi: lt -> yıl (float) ya da None

    def __init__(self, ctx):
        self.ctx = ctx
        self.k = ctx["kelimeler"]
        self.sure = ctx["sure"]

    def kt(self, parca, n=0, son=False):
        """parca ile başlayan n. kelimenin zamanı (sahne yerel)."""
        hedef = sade(parca)
        bulunan = [w for w in self.k if sade(w["k"]) == hedef] or \
            [w for w in self.k if sade(w["k"]).startswith(hedef)]
        if not bulunan:
            raise KeyError(f"{self.ctx['id']}: '{parca}' kelimesi yok")
        w = bulunan[min(n, len(bulunan) - 1)]
        return w["son"] if son else w["bas"]

    def cumle_araligi(self, ilk, son_kelime):
        return self.kt(ilk), self.kt(son_kelime, son=True)

    def olaylar(self):
        return []

    def yil_degeri(self, lt):
        return None

    def ciz(self, lt, arr):
        raise NotImplementedError


def gece_zemini(arr, ufuk=250):
    C.gradyan(arr, 0, ufuk, ["gece1", "gece1", "gece2", "gece3", "ufuk"])
    C.gradyan(arr, ufuk, SH, ["zemin2", "gece1", "gece1"])


# ------------------------------------------------------------------ 1. kanca: 29 Ekim 1923, 20.30
class Kanca(Sahne):
    def __init__(self, ctx):
        super().__init__(ctx)
        self.t29 = self.kt("29")
        self.tsaat = self.kt("saat")
        self.t158 = self.kt("158")
        self.tpeki = self.kt("Peki")

    def olaylar(self):
        return [(self.t29, "daktilo"), (self.tsaat, "saat"), (self.t158, "sayac"), (self.sure - 0.9, "geri_sar")]

    def ciz(self, lt, arr):
        gece_zemini(arr, 252)
        im = Image.fromarray(arr)
        d = ImageDraw.Draw(im)
        C.yildiz_ciz(d, lt, adet=70, ymax=190)
        arr[:] = np.array(im)
        isik_oran = ease(0.2, 2.5, lt)
        im = Image.fromarray(arr)
        d = ImageDraw.Draw(im)
        tepe = C.meclis_binasi(d, arr, RX // OLCEK, 252, lt, isik_oran)
        arr[:] = np.array(im)
        C.bayrak_ciz(arr, 137, tepe - 34, 16, lt * 0.8, dalga=0.8, direk_alt=tepe + 4)
        # sokak lambaları
        im = Image.fromarray(arr)
        d = ImageDraw.Draw(im)
        for x in (40, 230):
            d.rectangle([x, 222, x + 1, 252], fill=c("ahsap_koyu"))
            d.rectangle([x - 2, 218, x + 3, 222], fill=c("lamba"))
        arr[:] = np.array(im)
        for x in (40, 230):
            C.isik(arr, x + 1, 220, 18, "lamba", 0.6)
        yk = YaziKatmani()
        if lt >= self.t29 - 0.05:
            ust = daktilo("29 EKİM 1923", (lt - self.t29 + 0.05) / 1.1)
            yaz(yk, ust, RX - yazi_genislik("29 EKİM 1923", "piksel", 100) // 2, R(78), "sol", boyut=100, bant="altin", kenar=8)
        if lt >= self.tsaat:
            u = ease(self.tsaat, 0.3, lt)
            yaz(yk, "SAAT 20.30", RX, R(122 - 4 * (1 - u)), boyut=67, renk="gumus")
        if lt >= self.t158:
            u = ease(self.t158, 1.3, lt)
            n = int(round(158 * u))
            yaz(yk, f"{n}", RX, R(146), boyut=134, bant="altin", kenar=8)
            yaz(yk, "MİLLETVEKİLİ · TEK KARAR", RX, R(184), boyut=40, renk="soluk")
        # sonunda geri sarma (VHS): şeritler + ◀◀ 1918
        geri = lt - (self.sure - 0.9)
        if geri > 0:
            arr[:] = C.karart(arr, min(0.6, geri))
            rng = np.random.default_rng(int(lt * 30))
            for _ in range(6):
                y = int(rng.integers(40, SH - 40))
                arr[y:y + 2] = np.roll(arr[y:y + 2], int(rng.integers(-20, 20)), axis=1)
                arr[y, :] = (arr[y, :] * 0.5 + 120).astype(np.uint8)
            yil = int(round(1923 - 5 * min(1.0, geri / 0.7)))
            im = Image.fromarray(arr)
            d = ImageDraw.Draw(im)
            for k in range(2):
                x0 = 96 + k * 9
                d.polygon([(x0 + 8, 229), (x0, 234), (x0 + 8, 239)], fill=c("beyaz"))
            arr[:] = np.array(im)
            yaz(yk, str(yil), R(120), R(226), "sol", boyut=67, renk="beyaz")
        return yk


# ------------------------------------------------------------------ 2. açılış: Arpama + bayrak
class Acilis(Sahne):
    def olaylar(self):
        return [(0.1, "bayrak_acilis")]

    def ciz(self, lt, arr):
        C.gradyan(arr, 0, SH, ["gece1", "gece2", "gece2", "gece1"])
        C.isik(arr, 135, 200, 110, "gece3", 1.0)
        C.bayrak_ciz(arr, 60, 142, 102, lt * 0.9 + 0.5, dalga=1.0, direk_alt=300)
        yk = YaziKatmani()
        logo(yk, RX, 280, 120, oran=ease(0.1, 0.6, lt), tohum=3)
        if lt > 0.7:
            u = ease(0.7, 0.4, lt)
            yaz(yk, "29 EKİM ÖZEL", RX, 470 + int(10 * (1 - u)), boyut=47, renk="altin_acik")
        if lt > 1.0:
            yaz(yk, daktilo("CUMHURİYET'E GİDEN YOL", (lt - 1.0) / 1.0), RX - yazi_genislik("CUMHURİYET'E GİDEN YOL", "piksel", 60) // 2,
                R(262), "sol", boyut=60, bant="altin", kenar=8)
        return yk


# ------------------------------------------------------------------ zaman çizgisi (1918-1923)
def zaman_cizgisi(arr, yk, yil, gorunur=1.0):
    if yil is None or gorunur <= 0:
        return
    im = Image.fromarray(arr)
    d = ImageDraw.Draw(im)
    x0, x1, y = 45, 225, 66
    d.line([(x0, y), (x1, y)], fill=c("cizgi"))
    xs = lambda v: x0 + (x1 - x0) * (v - 1918) / 5  # noqa: E731
    xm = xs(max(1918, min(1923, yil)))
    d.line([(x0, y), (xm, y)], fill=c("altin"))
    for k in range(6):
        xk = xs(1918 + k)
        gecti = 1918 + k <= yil + 0.01
        d.rectangle([xk - 1, y - 1, xk + 1, y + 1], fill=c("altin") if gecti else c("cizgi"))
    d.rectangle([xm - 2, y - 2, xm + 2, y + 2], fill=c("altin_acik"), outline=c("gece1"))
    arr[:] = np.array(im)
    for k in range(6):
        yk_ = 1918 + k
        renk = "altin_acik" if abs(yil - yk_) < 0.5 else "soluk"
        yaz(yk, str(yk_), R(xs(yk_)), R(y - 12), boyut=34, renk=renk, kenar=4)


# ------------------------------------------------------------------ 3. 1918-1919: işgal, Samsun, Amasya
class Y1919(Sahne):
    def __init__(self, ctx):
        super().__init__(ctx)
        self.t_mondros = self.kt("Mondros'la")
        self.t_isgal = self.kt("işgal")
        self.t19 = self.kt("19")
        self.t_samsun = self.kt("Samsun'a")
        self.t_amasya = self.kt("Amasya'da")
        self.t_alinti, self.t_alinti_son = self.cumle_araligi("Milletin", "kurtaracaktır.")

    def olaylar(self):
        ev = [(self.t_mondros, "kagit")]
        ev += [(self.t_isgal + 0.15 * i, "isgal") for i in range(len(ISGAL))]
        ev += [(self.t_samsun, "pim"), (self.t_amasya, "pim"), (self.t_alinti, "alinti")]
        return ev

    def yil_degeri(self, lt):
        return 1918 + ease(self.t19 - 0.3, 0.8, lt)

    def ciz(self, lt, arr):
        C.gradyan(arr, 0, SH, ["gece1", "gece2", "gece1"])
        H.ciz(arr, lt)
        im = Image.fromarray(arr)
        d = ImageDraw.Draw(im)
        yk = YaziKatmani()
        # işgal işaretleri
        for i, ad in enumerate(ISGAL):
            if lt >= self.t_isgal + 0.15 * i:
                x, y = hx(ad)
                C.isgal_isareti(d, x, y, lt, i)
        # Bandırma: İstanbul'dan Samsun'a Karadeniz kıyısı boyunca
        rota = [H.xy(29.2, 41.35), H.xy(31.5, 41.55), H.xy(34.0, 42.15), H.xy(35.6, 41.95), H.xy(36.33, 41.45)]
        gemi_bas = self.t19 - 0.4
        if lt >= gemi_bas:
            u = ease(gemi_bas, max(0.5, self.t_samsun - gemi_bas), lt)
            C.ok_ciz(d, rota, u, "altin_koyu", lt)
            seg = u * (len(rota) - 1)
            i = min(int(seg), len(rota) - 2)
            f = seg - i
            gx = rota[i][0] + (rota[i + 1][0] - rota[i][0]) * f
            gy = rota[i][1] + (rota[i + 1][1] - rota[i][1]) * f
            if u < 1:
                C.gemi(d, int(gx), int(gy) - 4)
        if lt >= self.t_samsun:
            x, y = hx("samsun")
            C.pim(d, x, y, parla=(lt - self.t_samsun) < 0.6)
            sehir_etiketi(yk, "SAMSUN", x, y - 8)
        if lt >= self.t_amasya:
            ax, ay = hx("amasya")
            C.ok_ciz(d, [hx("samsun"), (ax, ay)], ease(self.t_amasya, 0.5, lt), "altin", lt)
            if lt >= self.t_amasya + 0.4:
                C.pim(d, ax, ay)
                sehir_etiketi(yk, "AMASYA", ax, ay + 1, alt=True)
        arr[:] = np.array(im)
        # başlık yılı
        yil = "1918" if lt < self.t19 - 0.1 else "1919"
        yaz(yk, yil, RX, R(76), boyut=100, bant="altin", kenar=8)
        im = Image.fromarray(arr)
        d = ImageDraw.Draw(im)
        if lt >= self.t_alinti - 0.2:
            pass
        elif lt < self.t19 - 0.1:
            if lt >= self.t_mondros:
                kart(d, yk, ["30 EKİM 1918", "MONDROS ATEŞKESİ"], 238, self.t_mondros, lt, renk="altin")
            if lt >= self.t_isgal:
                yaz(yk, "İŞGAL", R(hx("izmir")[0] + 6), R(hx("izmir")[1] + 6), "sol", boyut=34, renk="kirmizi")
        elif lt < self.t_amasya:
            kart(d, yk, ["19 MAYIS 1919", "SAMSUN"], 238, self.t_samsun, lt)
        else:
            kart(d, yk, ["22 HAZİRAN 1919", "AMASYA GENELGESİ"], 238, self.t_amasya, lt)
        arr[:] = np.array(im)
        # Amasya alıntısı: harita kararır, söz daktiloyla yazılır
        if lt >= self.t_alinti - 0.2:
            arr[:] = C.karart(arr, 0.75 * ease(self.t_alinti - 0.2, 0.4, lt))
            yk2 = YaziKatmani()
            satirlar = ['"MİLLETİN İSTİKLALİNİ', "YİNE MİLLETİN", "AZİM VE KARARI", 'KURTARACAKTIR."']
            toplam = sum(len(s) for s in satirlar)
            oran = (lt - self.t_alinti) / max(0.5, self.t_alinti_son - self.t_alinti)
            n = int(toplam * max(0, min(1, oran)))
            for j, s in enumerate(satirlar):
                g = s[:max(0, min(len(s), n))]
                n -= len(s)
                if g:
                    sx = RX - yazi_genislik(s, "piksel", 67) // 2
                    renk_bant = "altin" if j in (0, 3) else None
                    yaz(yk2, g, sx, R(118 + j * 24), "sol", boyut=67, bant=renk_bant, renk="beyaz", kenar=6)
            yaz(yk2, "AMASYA GENELGESİ · 22 HAZİRAN 1919", RX, R(222), boyut=34, renk="soluk")
            yk2.ops = [op for op in yk.ops if op[2] < R(100)] + yk2.ops  # yıl başlığı kalır
            return yk2
        return yk


# ------------------------------------------------------------------ 4. Erzurum: defter
class Defter(Sahne):
    SATIRLAR = ["Zaferden sonra,", "hükümet biçimi", "Cumhuriyet", "olacaktır."]

    def __init__(self, ctx):
        super().__init__(ctx)
        self.t_not = self.kt("not")
        self.t_alinti, self.t_alinti_son = self.cumle_araligi("Zaferden", "olacaktır.")
        self.t_kimse = self.kt("şimdilik")
        self.t_kongre = self.kt("Erzurum", 1)
        self.t_sivas = self.kt("Sivas")

    def olaylar(self):
        ev = [(self.t_alinti + i * 0.11, "kalem") for i in range(int((self.t_alinti_son - self.t_alinti) / 0.11))]
        return ev + [(self.t_kimse, "kapak"), (self.t_kongre + 0.1, "muhur"), (self.t_sivas, "muhur")]

    def yil_degeri(self, lt):
        return 1919.5

    def ciz(self, lt, arr):
        # duvar + masa + lamba
        C.gradyan(arr, 0, 205, ["gece1", "duvar", "duvar"])
        C.gradyan(arr, 205, SH, ["ahsap_acik", "ahsap", "ahsap_koyu", "gece1"])
        im = Image.fromarray(arr)
        d = ImageDraw.Draw(im)
        for y in range(212, 380, 9):
            d.line([(0, y), (SW, y + 2)], fill=c("ahsap_koyu"))
        d.line([(0, 205), (SW, 205)], fill=c("ahsap_acik"))
        # pencere (gece, yıldız)
        d.rectangle([180, 90, 236, 168], fill=c("gece1"), outline=c("ahsap_koyu"))
        d.line([(208, 90), (208, 168)], fill=c("ahsap_koyu"), width=2)
        d.line([(180, 128), (236, 128)], fill=c("ahsap_koyu"), width=2)
        for x, y in ((190, 100), (222, 112), (196, 146), (228, 150)):
            d.point((x, y), fill=c("soluk"))
        # lamba
        titre = 1 + 0.12 * math.sin(lt * 13) + 0.06 * math.sin(lt * 31)
        d.rectangle([22, 200, 50, 206], fill=c("ahsap_koyu"))
        d.ellipse([24, 182, 48, 202], fill=c("altin_koyu"))
        d.rectangle([31, 150, 41, 182], fill=c("gece3"), outline=c("gumus_koyu"))
        fh = int(10 * titre)
        d.ellipse([33, 176 - fh, 39, 178], fill=c("lamba"))
        d.point((36, 176 - fh + 2), fill=c("lamba_acik"))
        arr[:] = np.array(im)
        C.isik(arr, 36, 170, 95 * titre, "lamba", 0.9)
        im = Image.fromarray(arr)
        d = ImageDraw.Draw(im)
        yk = YaziKatmani()
        yaz(yk, "ERZURUM · TEMMUZ 1919", RX, R(78), boyut=67, bant="altin", kenar=8)
        # defter
        kapanis = ease(self.t_kimse, 0.7, lt)
        x0, y0, x1, y1 = 62, 132, 214, 292
        d.rectangle([x0 + 3, y0 + 3, x1 + 3, y1 + 3], fill=c("ahsap_koyu"))
        if kapanis < 1:
            d.rectangle([x0, y0, x1, y1], fill=c("kagit"), outline=c("kagit_koyu"))
            for y in range(y0 + 22, y1 - 6, 22):
                d.line([(x0 + 8, y), (x1 - 8, y)], fill=c("kagit_koyu"))
            d.line([(x0 + 14, y0 + 4), (x0 + 14, y1 - 4)], fill=c("kirmizi"))
        # yazı (daktilo yerine el yazısı hızı) + kalem
        n_top = sum(len(s) for s in self.SATIRLAR)
        oran = (lt - self.t_alinti) / max(0.5, self.t_alinti_son - self.t_alinti)
        n = int(n_top * max(0.0, min(1.0, oran)))
        kalem = None
        if kapanis < 1:
            kalan = n
            for j, s in enumerate(self.SATIRLAR):
                g = s[:max(0, min(len(s), kalan))]
                kalan -= len(s)
                if g:
                    gx, gy = R(x0 + 20), R(y0 + 10 + j * 22)
                    yk.ekle(yazi(g, "piksel", 50, renk="murekkep"), gx, gy)
                    if 0 < len(g) < len(s) or (j == len(self.SATIRLAR) - 1 and len(g) == len(s)):
                        kalem = (x0 + 20 + yazi_genislik(g, "piksel", 50) / OLCEK, y0 + 10 + j * 22 + 12)
            if lt < self.t_not:
                yk.ekle(yazi("1919", "piksel", 50, renk="kagit_koyu"), R(x1 - 30), R(y1 - 18))
        if kapanis > 0:
            # kapak soldan sağa kapanır
            xk = int(x1 - (x1 - x0) * kapanis) if kapanis < 1 else x0
            d.rectangle([xk if kapanis < 1 else x0, y0, x1, y1], fill=c("bayrak_koyu"), outline=c("ahsap_koyu"))
            if kapanis >= 1:
                d.rectangle([x0 + 6, y0 + 6, x1 - 6, y1 - 6], outline=c("altin_koyu"))
                d.rectangle([x1 - 8, y0 + 40, x1 + 2, y0 + 52], fill=c("ahsap_koyu"))
        if kalem and kapanis == 0 and lt < self.t_alinti_son + 0.5:
            kx, ky = kalem
            d.line([(kx + 1, ky), (kx + 16, ky - 22)], fill=c("gece1"), width=3)
            d.line([(kx + 1, ky), (kx + 16, ky - 22)], fill=c("altin_koyu"), width=1)
            d.point((kx, ky + 1), fill=c("murekkep"))
        arr[:] = np.array(im)
        # kongre mühürleri
        for i, (t0, ust, alt) in enumerate(((self.t_kongre + 0.1, "ERZURUM KONGRESİ", "23 TEMMUZ 1919"),
                                            (self.t_sivas, "SİVAS KONGRESİ", "4 EYLÜL 1919"))):
            if lt >= t0:
                u = ease(t0, 0.18, lt)
                im = Image.fromarray(arr)
                d = ImageDraw.Draw(im)
                y = 160 + i * 64
                bx0, bx1 = 48 - int((1 - u) * 10), 222 + int((1 - u) * 10)
                d.rectangle([bx0, y, bx1, y + 46], fill=c("kagit"), outline=c("bayrak_koyu"), width=2)
                d.rectangle([bx0 + 4, y + 4, bx1 - 4, y + 42], outline=c("bayrak"))
                arr[:] = np.array(im)
                yaz(yk, ust, RX, R(y + 6), boyut=50, renk="bayrak_koyu", kenar=0)
                yaz(yk, alt, RX, R(y + 27), boyut=40, renk="murekkep", kenar=0)
        return yk


# ------------------------------------------------------------------ 5. 1920-1922: TBMM, Sakarya, Büyük Taarruz
class Y1920(Sahne):
    def __init__(self, ctx):
        super().__init__(ctx)
        self.t23 = self.kt("23")
        self.t_meclis = self.kt("Meclisi")
        self.t_sakarya = self.kt("Sakarya'da")
        self.t26 = self.kt("26")
        self.t9 = self.kt("9")
        self.t_izmir = self.kt("İzmir'de")
        self.t_kasim = self.kt("1")

    def olaylar(self):
        return [(self.t23, "pim"), (self.t_sakarya, "kilic"), (self.t26, "taarruz"), (self.t_izmir, "zafer"),
                (self.t_kasim, "taht")]

    def yil_degeri(self, lt):
        y = 1920 + ease(self.t_sakarya - 0.2, 0.6, lt) + ease(self.t26 - 0.2, 0.6, lt)
        return y

    def ciz(self, lt, arr):
        C.gradyan(arr, 0, SH, ["gece1", "gece2", "gece1"])
        H.ciz(arr, lt)
        im = Image.fromarray(arr)
        d = ImageDraw.Draw(im)
        yk = YaziKatmani()
        # işgal izleri: İzmir'e girişle birlikte tek tek söner
        for i, ad in enumerate(ISGAL):
            if lt < self.t_izmir + 0.25 * i:
                x, y = hx(ad)
                C.isgal_isareti(d, x, y, lt, i)
        ax, ay = hx("ankara")
        if lt >= self.t23:
            C.pim(d, ax, ay, renk="altin", parla=(lt - self.t23) < 0.6)
            sehir_etiketi(yk, "ANKARA", ax, ay - 8)
        if lt >= self.t_sakarya:
            sx, sy = hx("sakarya")
            if (lt - self.t_sakarya) < 1.0 and int(lt * 8) % 2 == 0:
                d.ellipse([sx - 7, sy - 7, sx + 7, sy + 7], outline=c("kirmizi"))
            C.kilic_ciz(d, sx - 4, sy + 6)
            sehir_etiketi(yk, "SAKARYA", sx - 14, sy + 10, renk="gumus", alt=True)
        if lt >= self.t26:
            ox, oy = hx("afyon")
            dx, dy = hx("dumlupinar")
            ix, iy = hx("izmir")
            C.ok_ciz(d, [(ox + 3, oy - 1), (dx, dy), (ix + 18, iy - 2), (ix + 3, iy)],
                     ease(self.t26 + 0.2, max(0.8, self.t_izmir - self.t26 - 0.2), lt), "altin", lt)
        if lt >= self.t_izmir:
            ix, iy = hx("izmir")
            arr[:] = np.array(im)
            C.bayrak_ciz(arr, ix + 2, iy - 16, 8, lt, dalga=0.7, direk_alt=iy + 1)
            im = Image.fromarray(arr)
            d = ImageDraw.Draw(im)
            sehir_etiketi(yk, "İZMİR", ix + 4, iy + 2, renk="altin_acik", alt=True)
        arr[:] = np.array(im)
        yil = "1920" if lt < self.t_sakarya - 0.1 else "1921" if lt < self.t26 - 0.1 else "1922"
        yaz(yk, yil, RX, R(76), boyut=100, bant="altin", kenar=8)
        im = Image.fromarray(arr)
        d = ImageDraw.Draw(im)
        if lt < self.t_sakarya:
            kart(d, yk, ["23 NİSAN 1920", "BÜYÜK MİLLET MECLİSİ AÇILDI"], 238, self.t23, lt)
        elif lt < self.t26:
            kart(d, yk, ["SAKARYA · 1921", "22 GÜN 22 GECE"], 238, self.t_sakarya, lt)
        elif lt < self.t9:
            kart(d, yk, ["26 AĞUSTOS 1922", "BÜYÜK TAARRUZ"], 238, self.t26, lt)
        elif lt < self.t_kasim:
            kart(d, yk, ["9 EYLÜL 1922", "İZMİR"], 238, self.t9, lt)
        arr[:] = np.array(im)
        if lt >= self.t_kasim - 0.1:
            # saltanat kaldırılıyor: taç + çarpı
            u = ease(self.t_kasim - 0.1, 0.3, lt)
            arr[:] = C.karart(arr, 0.6 * u)
            im = Image.fromarray(arr)
            d = ImageDraw.Draw(im)
            cx, cy = 135, 165
            d.polygon([(cx - 22, cy + 12), (cx - 22, cy - 8), (cx - 11, cy + 2), (cx, cy - 14), (cx + 11, cy + 2),
                       (cx + 22, cy - 8), (cx + 22, cy + 12)], fill=c("altin_koyu"), outline=c("altin"))
            for x in (cx - 22, cx, cx + 22):
                d.rectangle([x - 2, cy - 18 if x == cx else cy - 12, x + 2, cy - 14 if x == cx else cy - 8], fill=c("kirmizi"))
            if lt >= self.t_kasim + 0.6:
                v = ease(self.t_kasim + 0.6, 0.3, lt)
                d.line([(cx - 30, cy - 24), (cx - 30 + 60 * v, cy - 24 + 48 * v)], fill=c("bayrak"), width=4)
                if v >= 1:
                    d.line([(cx + 30, cy - 24), (cx - 30, cy + 24)], fill=c("bayrak"), width=4)
            arr[:] = np.array(im)
            im = Image.fromarray(arr)
            d = ImageDraw.Draw(im)
            kart(d, yk, ["1 KASIM 1922", "SALTANAT KALDIRILDI"], 238, self.t_kasim - 0.1, lt)
            arr[:] = np.array(im)
        return yk


# ------------------------------------------------------------------ 6. 1923: Lozan, başkent, Çankaya akşamı
class Y1923(Sahne):
    def __init__(self, ctx):
        super().__init__(ctx)
        self.t24 = self.kt("24")
        self.t13 = self.kt("13")
        self.t28 = self.kt("28")
        self.t_alinti, self.t_alinti_son = self.cumle_araligi("Yarın,", "edeceğiz.")

    def olaylar(self):
        return [(self.t24, "muhur"), (self.t13, "pim"), (self.t28 - 0.1, "gecis"), (self.t_alinti, "alinti")]

    def yil_degeri(self, lt):
        return 1923

    def ciz(self, lt, arr):
        if lt < self.t28 - 0.1:
            return self._belgeler(lt, arr)
        yeni = arr.copy()
        yk = self._cankaya(lt, yeni)
        u = ease(self.t28 - 0.1, GECIS, lt)
        if u < 1:
            eski = arr.copy()
            self._belgeler(lt, eski)
            arr[:] = C.gecis(eski, yeni, u)
        else:
            arr[:] = yeni
        return yk

    def _belgeler(self, lt, arr):
        C.gradyan(arr, 0, SH, ["gece1", "gece2", "gece1"])
        yk = YaziKatmani()
        yaz(yk, "1923", RX, R(76), boyut=100, bant="altin", kenar=8)
        im = Image.fromarray(arr)
        d = ImageDraw.Draw(im)
        if lt >= self.t24:
            u = ease(self.t24, 0.35, lt)
            y = 118 + int((1 - u) * 8)
            # antlaşma belgesi
            d.rectangle([44, y, 84, y + 52], fill=c("kagit"), outline=c("kagit_koyu"))
            for k in range(6):
                d.line([(50, y + 8 + k * 6), (78 - (k % 2) * 8, y + 8 + k * 6)], fill=c("kagit_koyu"))
            d.ellipse([66, y + 38, 80, y + 52], fill=c("bayrak_koyu"))
            d.point((73, y + 45), fill=c("bayrak_acik"))
            yaz(yk, "24 TEMMUZ 1923", R(94), R(y + 8), "sol", boyut=67, bant="altin", kenar=0)
            yaz(yk, "LOZAN ANTLAŞMASI", R(94), R(y + 30), "sol", boyut=50, renk="gumus", kenar=0)
        if lt >= self.t13:
            u = ease(self.t13, 0.35, lt)
            y = 186 + int((1 - u) * 8)
            # Ankara Kalesi silueti + bayrak
            d.polygon([(40, y + 52), (46, y + 30), (54, y + 26), (58, y + 14), (70, y + 12), (74, y + 22),
                       (82, y + 28), (88, y + 52)], fill=c("tas_koyu"))
            for x in (56, 62, 68, 74):
                d.rectangle([x, y + 10, x + 2, y + 12], fill=c("tas_koyu"))
            arr[:] = np.array(im)
            C.bayrak_ciz(arr, 66, y - 4, 8, lt, dalga=0.6, direk_alt=y + 12)
            im = Image.fromarray(arr)
            d = ImageDraw.Draw(im)
            yaz(yk, "13 EKİM 1923", R(94), R(y + 14), "sol", boyut=67, bant="altin", kenar=0)
            yaz(yk, "ANKARA BAŞKENT", R(94), R(y + 36), "sol", boyut=50, renk="gumus", kenar=0)
        arr[:] = np.array(im)
        return yk

    def _cankaya(self, lt, arr):
        C.gradyan(arr, 0, 230, ["gece1", "duvar", "duvar_acik"])
        C.gradyan(arr, 230, SH, ["ahsap", "ahsap_koyu", "gece1"])
        im = Image.fromarray(arr)
        d = ImageDraw.Draw(im)
        # pencereler (gece)
        for x in (30, 196):
            d.rectangle([x, 96, x + 44, 176], fill=c("gece1"), outline=c("ahsap_koyu"), width=2)
            d.line([(x + 22, 96), (x + 22, 176)], fill=c("ahsap_koyu"), width=2)
            d.point([(x + 8, 110), (x + 34, 124), (x + 14, 150)], fill=c("soluk"))
        d.ellipse([214, 104, 222, 112], fill=c("mavi_buz"))
        # avize
        d.line([(135, 90), (135, 110)], fill=c("altin_koyu"))
        d.rectangle([122, 110, 148, 114], fill=c("altin_koyu"))
        for x in (122, 131, 139, 148):
            d.rectangle([x - 1, 106, x + 1, 109], fill=c("lamba_acik"))
        arr[:] = np.array(im)
        C.isik(arr, 135, 140, 120, "lamba", 1.0)
        im = Image.fromarray(arr)
        d = ImageDraw.Draw(im)
        # masa başındakiler (siluet) ve masa
        rng = random.Random(4)
        for i, x in enumerate((52, 84, 116, 154, 186, 218)):
            bas = 196 + rng.randint(-2, 2)
            d.rectangle([x - 11, bas + 9, x + 11, 232], fill=c("gece1"))
            d.ellipse([x - 6, bas - 4, x + 6, bas + 9], fill=c("gece1"))
            d.line([(x - 11, bas + 10), (x + 11, bas + 10)], fill=c("gece2"))
            d.point([(x, bas + 12), (x, bas + 14)], fill=c("beyaz"))
        d.rectangle([24, 228, 246, 252], fill=c("beyaz"))
        d.rectangle([24, 248, 246, 252], fill=c("gumus_koyu"))
        for x in (52, 84, 116, 154, 186, 218):
            d.ellipse([x - 7, 231, x + 7, 237], fill=c("gumus"), outline=c("gumus_koyu"))
            d.rectangle([x + 9, 224, x + 11, 233], fill=c("mavi_buz"))
        for x in (100, 170):
            d.rectangle([x, 214, x + 2, 230], fill=c("kagit"))
            d.point((x + 1, 212), fill=c("lamba_acik"))
        arr[:] = np.array(im)
        for x in (101, 171):
            C.isik(arr, x, 212, 16, "lamba", 0.8)
        yk = YaziKatmani()
        yaz(yk, "ÇANKAYA · 28 EKİM 1923", RX, R(78), boyut=60, bant="altin", kenar=8)
        if lt < self.t_alinti:
            yaz(yk, "AKŞAM YEMEĞİ", RX, R(98), boyut=40, renk="soluk")
        if lt >= self.t_alinti - 0.1:
            satirlar = ['"YARIN', "CUMHURİYET'İ", 'İLAN EDECEĞİZ."']
            toplam = sum(len(s) for s in satirlar)
            oran = (lt - self.t_alinti) / max(0.5, self.t_alinti_son - self.t_alinti)
            n = int(toplam * max(0, min(1, oran)))
            for j, s in enumerate(satirlar):
                g = s[:max(0, min(len(s), n))]
                n -= len(s)
                if g:
                    sx = RX - yazi_genislik(s, "piksel", 87) // 2
                    yaz(yk, g, sx, R(118 + j * 26), "sol", boyut=87, bant="altin" if j == 1 else None, renk="beyaz", kenar=8)
            yaz(yk, "— GAZİ MUSTAFA KEMAL", RX, R(258), boyut=47, renk="altin_acik")
        return yk


# ------------------------------------------------------------------ 7. ilan: kanun, 158 oy, 101 pare top
class Ilan(Sahne):
    SATIRLAR = ["TÜRKİYE DEVLETİNİN", "ŞEKL-İ HÜKÛMETİ", "CUMHURİYETTİR."]

    def __init__(self, ctx):
        super().__init__(ctx)
        self.t_karar = self.kt("tarihi")
        self.t_alinti, self.t_alinti_son = self.cumle_araligi("Türkiye", "Cumhuriyettir.")
        self.t_gazi = self.kt("Gazi")
        self.t_top = self.kt("Ankara'nın")
        self.toplar = [self.t_top + 0.15 + i * 0.32 for i in range(int((self.sure - self.t_top) / 0.32) + 4)]

    def olaylar(self):
        ev = [(self.t_karar, "parsomen"), (self.t_alinti_son + 0.15, "muhur_buyuk"), (self.t_gazi, "sayac")]
        ev += [(t, "top") for t in self.toplar if t < self.sure + 0.2]
        return ev

    def yil_degeri(self, lt):
        return 1923

    def ciz(self, lt, arr):
        if lt < self.t_top - 0.2:
            return self._meclis(lt, arr)
        yeni = arr.copy()
        yk = self._gece(lt, yeni)
        u = ease(self.t_top - 0.2, GECIS, lt)
        if u < 1:
            eski = arr.copy()
            self._meclis(lt, eski)
            arr[:] = C.gecis(eski, yeni, u)
        else:
            arr[:] = yeni
        return yk

    def _meclis(self, lt, arr):
        C.gradyan(arr, 0, SH, ["gece1", "duvar", "duvar_acik", "duvar", "gece1"])
        im = Image.fromarray(arr)
        d = ImageDraw.Draw(im)
        # arka duvar: kürsü + asılı bayrak
        d.rectangle([20, 92, 250, 96], fill=c("ahsap_koyu"))
        d.rectangle([105, 238, 165, 262], fill=c("ahsap"), outline=c("ahsap_koyu"))
        d.rectangle([90, 230, 180, 238], fill=c("ahsap_acik"))
        # sıralar (perspektif) + başlar
        for r, y in enumerate((300, 326, 356)):
            d.rectangle([0, y, SW, y + 8], fill=c("ahsap") if r % 2 == 0 else c("ahsap_koyu"))
            d.line([(0, y), (SW, y)], fill=c("ahsap_acik"))
            n = 7 + r * 2
            for i in range(n):
                x = 12 + i * (246 / (n - 1)) + (r % 2) * 7 - 3
                bh = 5 + r * 2
                d.rectangle([x - bh - 1, y - bh, x + bh + 1, y - 1], fill=c("gece1"))
                d.ellipse([x - bh // 2 - 1, y - bh * 2 - 2, x + bh // 2 + 1, y - bh + 1], fill=c("gece1"))
                d.point((x, y - bh * 2 - 2), fill=c("lamba_koyu"))
        arr[:] = np.array(im)
        C.bayrak_ciz(arr, 102, 108, 40, lt * 0.35, dalga=0.25, gondere=False)
        yk = YaziKatmani()
        yaz(yk, "TBMM · 29 EKİM 1923 · 20.30", RX, R(78), boyut=50, bant="altin", kenar=8)
        if self.t_karar <= lt < self.t_gazi:
            u = ease(self.t_karar, 0.5, lt)
            im = Image.fromarray(arr)
            d = ImageDraw.Draw(im)
            ust, alt = 100, 100 + int(118 * u)
            d.rectangle([30, ust, 240, alt], fill=c("kagit"), outline=c("kagit_koyu"))
            d.rectangle([26, ust - 4, 244, ust + 2], fill=c("kagit_koyu"))
            d.rectangle([26, alt - 2, 244, alt + 4], fill=c("kagit_koyu"))
            arr[:] = np.array(im)
            if u >= 1:
                yaz(yk, "TEŞKİLÂT-I ESASİYE KANUNU", RX, R(108), boyut=40, renk="bayrak_koyu", kenar=0)
                toplam = sum(len(s) for s in self.SATIRLAR)
                oran = (lt - self.t_alinti) / max(0.5, self.t_alinti_son - self.t_alinti)
                n = int(toplam * max(0, min(1, oran)))
                for j, s in enumerate(self.SATIRLAR):
                    g = s[:max(0, min(len(s), n))]
                    n -= len(s)
                    if g:
                        sx = RX - yazi_genislik(s, "piksel", 67) // 2
                        yaz(yk, g, sx, R(128 + j * 24), "sol", boyut=67,
                            renk="bayrak_koyu" if j == 2 else "murekkep", kenar=0)
            t_muhur = self.t_alinti_son + 0.15
            if lt >= t_muhur:
                v = ease(t_muhur, 0.15, lt)
                im = Image.fromarray(arr)
                d = ImageDraw.Draw(im)
                r = int(18 + (1 - v) * 10)
                d.ellipse([205 - r, 205 - r, 205 + r, 205 + r], outline=c("bayrak"), width=3)
                arr[:] = np.array(im)
                yaz(yk, "KABUL", R(205), R(199), boyut=47, renk="bayrak", kenar=0)
        if lt >= self.t_gazi:
            u = ease(self.t_gazi, 0.3, lt)
            arr[:] = C.karart(arr, 0.93 * u)
            yaz(yk, f"{int(round(158 * ease(self.t_gazi, 1.2, lt)))} OY", RX, R(132), boyut=120, bant="altin", kenar=8)
            yaz(yk, "OY BİRLİĞİYLE", RX, R(166), boyut=47, renk="gumus")
            yaz(yk, "İLK CUMHURBAŞKANI", RX, R(196), boyut=60, renk="beyaz")
            yaz(yk, "GAZİ MUSTAFA KEMAL", RX, R(214), boyut=80, bant="altin", kenar=8)
        return yk

    def _gece(self, lt, arr):
        gece_zemini(arr, 252)
        im = Image.fromarray(arr)
        d = ImageDraw.Draw(im)
        C.yildiz_ciz(d, lt, adet=50, ymax=190)
        tepe = C.meclis_binasi(d, arr, 135, 252, lt, 1.0)
        arr[:] = np.array(im)
        C.bayrak_ciz(arr, 137, tepe - 34, 16, lt * 0.8, dalga=0.9, direk_alt=tepe + 4)
        # top ateşleri: ufukta parlama + duman
        atis = [t for t in self.toplar if t <= lt]
        sayi = min(101, int(round(101 * ease(self.t_top + 0.1, self.sure - self.t_top - 0.4, lt))))
        im = Image.fromarray(arr)
        d = ImageDraw.Draw(im)
        for i, t0 in enumerate(atis[-4:]):
            k = len(atis) - len(atis[-4:]) + i
            x = (30, 236, 60, 210)[k % 4]
            g = lt - t0
            if g < 0.12:
                d.rectangle([x - 4, 240, x + 4, 248], fill=c("lamba_acik"))
            if g < 1.4:
                rr = random.Random(k)
                for p in range(6):
                    px = x + rr.randint(-6, 6) + g * rr.uniform(-6, 6)
                    py = 240 - g * rr.uniform(8, 18) + rr.randint(-3, 3)
                    pr = 1 + g * 3 * rr.uniform(0.6, 1.2)
                    d.ellipse([px - pr, py - pr, px + pr, py + pr], fill=c("gece3") if g > 0.7 else c("tas_koyu"))
        arr[:] = np.array(im)
        if atis and lt - atis[-1] < 0.1:
            C.isik(arr, (30, 236, 60, 210)[(len(atis) - 1) % 4], 244, 60, "lamba", 0.7)
        yk = YaziKatmani()
        yaz(yk, f"{sayi}", RX, R(78), boyut=134, bant="altin", kenar=8)
        yaz(yk, "PARE TOP", RX, R(114), boyut=67, renk="gumus")
        yaz(yk, "ANKARA · 29 EKİM 1923 GECESİ", RX, R(134), boyut=40, renk="soluk")
        return yk


# ------------------------------------------------------------------ 8. kapanış: defterden bayrağa, 103. yıl
class Kapanis(Sahne):
    def __init__(self, ctx):
        super().__init__(ctx)
        self.t_dort = self.kt("dört")
        self.t_son = self.kt("Cumhuriyetimizin")
        self.fisekler = []
        rng = random.Random(29)
        t = self.t_dort + 0.3
        while t < self.sure:
            self.fisekler.append((t, rng.randint(40, 230), rng.randint(70, 150), rng.randint(0, 999)))
            t += rng.uniform(0.35, 0.8)

    def olaylar(self):
        return [(self.t_dort, "bayrak_acilis"), (self.t_son, "final")] + \
               [(t + 0.6, "fisek") for t, *_ in self.fisekler]

    def ciz(self, lt, arr):
        if lt < self.t_dort - 0.2:
            return self._defter(lt, arr)
        yeni = arr.copy()
        yk = self._bayrak(lt, yeni)
        u = ease(self.t_dort - 0.2, 0.7, lt)
        if u < 1:
            eski = arr.copy()
            self._defter(lt, eski)
            arr[:] = C.gecis(eski, yeni, u)
        else:
            arr[:] = yeni
        return yk

    def _defter(self, lt, arr):
        C.gradyan(arr, 0, SH, ["gece1", "duvar", "ahsap_koyu", "gece1"])
        C.isik(arr, 60, 150, 110, "lamba", 0.6)
        im = Image.fromarray(arr)
        d = ImageDraw.Draw(im)
        x0, y0, x1, y1 = 62, 120, 214, 260
        d.rectangle([x0, y0, x1, y1], fill=c("kagit"), outline=c("kagit_koyu"))
        for y in range(y0 + 22, y1 - 6, 22):
            d.line([(x0 + 8, y), (x1 - 8, y)], fill=c("kagit_koyu"))
        d.line([(x0 + 14, y0 + 4), (x0 + 14, y1 - 4)], fill=c("kirmizi"))
        arr[:] = np.array(im)
        yk = YaziKatmani()
        parla = int(lt * 6) % 2 == 0 and lt > 1.0
        for j, s in enumerate(Defter.SATIRLAR):
            renk = "bayrak_koyu" if (j == 2 and parla) else "murekkep"
            yk.ekle(yazi(s, "piksel", 50, renk=renk), R(x0 + 20), R(y0 + 10 + j * 22))
        yaz(yk, "ERZURUM, 1919", RX, R(84), boyut=60, renk="soluk")
        return yk

    def _bayrak(self, lt, arr):
        C.gradyan(arr, 0, SH, ["gece1", "gece2", "gece3", "gece2", "gece1"])
        im = Image.fromarray(arr)
        d = ImageDraw.Draw(im)
        C.yildiz_ciz(d, lt, adet=50, ymax=260)
        for t0, x, y, s in self.fisekler:
            C.yukselen(d, lt - t0, x, y)
            C.havai_fisek(d, lt - t0 - 0.6, s, x, y)
        # Ankara silueti (kale + bugünün kenti)
        rng = random.Random(8)
        x = 0
        while x < SW:
            w = rng.randint(8, 18)
            h = rng.randint(10, 34)
            d.rectangle([x, 300 - h, x + w, 300], fill=c("gece1"))
            for wy in range(300 - h + 3, 298, 5):
                for wx in range(x + 2, x + w - 1, 4):
                    if rng.random() < 0.3:
                        d.point((wx, wy), fill=c("lamba_koyu"))
            x += w + rng.randint(0, 3)
        d.rectangle([0, 300, SW, SH], fill=c("gece1"))
        arr[:] = np.array(im)
        C.bayrak_ciz(arr, 66, 200, 64, lt * 0.9 + 1.3, dalga=1.0, direk_alt=300)
        yk = YaziKatmani()
        if lt >= self.t_son - 0.1:
            u = ease(self.t_son - 0.1, 0.5, lt)
            yaz(yk, "CUMHURİYETİMİZİN", RX, R(78), boyut=67, renk="beyaz")
            if lt >= self.t_son + 0.5:
                yaz(yk, "103. YILI", RX, R(102), boyut=134, bant="altin", kenar=10)
            if lt >= self.t_son + 1.2:
                yaz(yk, "KUTLU OLSUN", RX, R(152), boyut=100, renk="beyaz", kenar=8)
            if lt >= self.t_son + 1.9:
                yaz(yk, "29 EKİM 1923 — 29 EKİM 2026", RX, R(316), boyut=50, renk="altin_acik")
        else:
            yaz(yk, "29 EKİM", RX, R(78), boyut=100, bant="altin", kenar=8)
        return yk


SAHNELER = {"kanca": Kanca, "acilis": Acilis, "y1919": Y1919, "defter": Defter, "y1920": Y1920,
            "y1923": Y1923, "ilan": Ilan, "kapanis": Kapanis}


# ------------------------------------------------------------------ zaman çizelgesi ve kare üretimi
def zaman_cizelgesi():
    sen = json.loads((DIZIN / "senaryo.json").read_text(encoding="utf-8"))
    t, sahneler = 0.0, []
    for i, s in enumerate(sen["sahneler"]):
        ses = json.loads((DIZIN / "ses" / f"{s['id']}.json").read_text(encoding="utf-8"))
        giris = s.get("giris", 0.4)
        bitis = t + giris + ses["sure"] + s.get("kuyruk", ARA)
        sahneler.append({"id": s["id"], "sahne": s["sahne"], "bas": round(t, 3), "son": round(bitis, 3),
                         "ses_bas": round(t + giris, 3), "ses_son": round(t + giris + ses["sure"], 3),
                         "kelimeler": [dict(k, bas=k["bas"] + giris, son=k["son"] + giris) for k in ses["kelimeler"]]})
        t = bitis
    return sen, sahneler, t


class Render:
    def __init__(self):
        self.sen, self.sahneler, self.toplam = zaman_cizelgesi()
        self.nesneler = [SAHNELER[s["sahne"]]({"id": s["id"], "sure": s["son"] - s["bas"], "kelimeler": s["kelimeler"]})
                         for s in self.sahneler]
        # alıntı cümleleri ekranda büyük yazıldığı için altyazıda tekrar edilmez
        alt = [dict(s, kelimeler=[k for k in s["kelimeler"] if not k.get("alinti")]) for s in self.sahneler]
        self.sayfalar = altyazi_sayfalari(alt, self.sen.get("vurgu", []))

    def sahne_bul(self, t):
        for i, s in enumerate(self.sahneler):
            if t < s["son"] or i == len(self.sahneler) - 1:
                return i
        return len(self.sahneler) - 1

    def sanal(self, i, lt):
        arr = np.zeros((SH, SW, 3), np.uint8)
        yk = self.nesneler[i].ciz(lt, arr) or YaziKatmani()
        yil = self.nesneler[i].yil_degeri(lt)
        if yil is not None:
            zaman_cizgisi(arr, yk, yil)
        return arr, yk

    def kare(self, t):
        i = self.sahne_bul(t)
        s = self.sahneler[i]
        lt = t - s["bas"]
        arr, yk = self.sanal(i, lt)
        if i > 0 and lt < GECIS:
            onceki = self.sahneler[i - 1]
            eski, eyk = self.sanal(i - 1, onceki["son"] - onceki["bas"] + lt)
            u = lt / GECIS
            arr = C.gecis(eski, arr, u)
            if u < 0.5:
                yk = eyk
        buyuk = np.repeat(np.repeat(arr, OLCEK, axis=0), OLCEK, axis=1)
        img = Image.fromarray(np.ascontiguousarray(buyuk), "RGB")
        for sy in self.sayfalar:
            if sy["bas"] - 0.05 <= t < sy["son"]:
                altyazi_ciz(yk, sy, t)
                break
        yk.uygula(img)
        out = np.asarray(img).copy()
        out[OLCEK - 1::OLCEK] = (out[OLCEK - 1::OLCEK] * 0.9).astype(np.uint8)  # CRT tarama çizgisi
        return out

    def olaylar(self):
        out = []
        for s, n in zip(self.sahneler, self.nesneler):
            out += [{"t": round(s["bas"] + t, 3), "efekt": e, "sahne": s["id"]} for t, e in n.olaylar()]
        return sorted(out, key=lambda o: o["t"])

    def video(self, yol):
        n = int(round(self.toplam * FPS))
        cmd = ["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
               "-s", f"{SW * OLCEK}x{SH * OLCEK}", "-r", str(FPS), "-i", "-",
               "-c:v", "libx264", "-preset", "medium", "-crf", "16", "-pix_fmt", "yuv420p",
               "-colorspace", "bt709", "-color_primaries", "bt709", "-color_trc", "bt709", str(yol)]
        p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
        for f in range(n):
            p.stdin.write(self.kare(f / FPS).tobytes())
            if f % 300 == 0:
                print(f"  kare {f}/{n}", flush=True)
        p.stdin.close()
        if p.wait() != 0:
            raise RuntimeError("ffmpeg render hatası")

    def kapak(self, yol):
        arr = np.zeros((SH, SW, 3), np.uint8)
        C.gradyan(arr, 0, SH, ["gece1", "gece2", "gece3", "gece2", "gece1"])
        im = Image.fromarray(arr)
        d = ImageDraw.Draw(im)
        C.yildiz_ciz(d, 0.4, adet=60, ymax=300)
        for t0, x, y, s in ((0.5, 60, 110, 3), (0.8, 214, 96, 7), (0.6, 230, 170, 11), (0.9, 44, 180, 5)):
            C.havai_fisek(d, t0, s, x, y)
        arr[:] = np.array(im)
        C.bayrak_ciz(arr, 66, 180, 92, 1.7, dalga=1.0, direk_alt=330)
        yk = YaziKatmani()
        logo(yk, RX, 250, 110)
        yaz(yk, "29 EKİM 1923", RX, R(110), boyut=120, bant="altin", kenar=10)
        yaz(yk, "CUMHURİYET'E", RX, R(338), boyut=100, renk="beyaz", kenar=8)
        yaz(yk, "GİDEN YOL", RX, R(366), boyut=100, bant="altin", kenar=8)
        yaz(yk, "103. YIL", RX, R(400), boyut=67, renk="altin_acik")
        img = Image.fromarray(np.repeat(np.repeat(arr, OLCEK, 0), OLCEK, 1), "RGB")
        yk.uygula(img)
        img.save(yol)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--kareler", help="yalnızca bu saniyelerin karelerini PNG olarak çıkar (ör. 3,20,45)")
    args = ap.parse_args()
    r = Render()
    ara = DIZIN / "ara"
    ara.mkdir(exist_ok=True)
    (ara / "zaman.json").write_text(json.dumps({
        "toplam": r.toplam,
        "sahneler": [{k: v for k, v in s.items() if k != "kelimeler"} for s in r.sahneler],
        "olaylar": r.olaylar(),
    }, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"süre: {r.toplam:.1f} sn")
    if args.kareler:
        for s in args.kareler.split(","):
            Image.fromarray(r.kare(float(s))).save(ara / f"kare_{float(s):06.1f}.png")
        return
    r.kapak(DIZIN / "kapak.png")
    r.video(ara / "video.mp4")
    print("video ->", ara / "video.mp4")


if __name__ == "__main__":
    main()
