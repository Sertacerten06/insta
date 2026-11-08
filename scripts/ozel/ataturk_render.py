"""10 Kasım özel bölümü: görüntü render'ı (29 Ekim render altyapısını kullanır).

Girdi : ozel/10kasim/senaryo.json, ozel/10kasim/ses/*.json (ataturk_tts.py çıktısı)
Çıktı : ozel/10kasim/ara/zaman.json, ozel/10kasim/ara/video.mp4, ozel/10kasim/kapak.png

Ton: saygılı ve sakin. Atatürk'ün portresi çizilmez; bilim, eğitim ve teknoloji mirası
semboller (saat 09.05, kara tahta, geometri, uçak, yarıya inmiş bayrak) ile anlatılır.
Arpama logosu yalnızca açılışta ve kapakta; Haritam reklamı yok.

Kullanım:
  python scripts/ozel/ataturk_render.py
  python scripts/ozel/ataturk_render.py --kareler 3,20,45
"""
import argparse
import json
import math
import random
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

KOK = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(KOK / "scripts"), str(KOK / "scripts" / "render"), str(KOK / "scripts" / "ozel")]
import cumhuriyet_render as CR  # noqa: E402
from cumhuriyet_render import R, RX, Sahne, daktilo, ease, kart, yaz  # noqa: E402
import cumhuriyet_cizim as C  # noqa: E402
from cumhuriyet_cizim import c  # noqa: E402
from cizim import OLCEK, SH, SW, P, YaziKatmani, yazi_genislik  # noqa: E402
from sahneler import logo  # noqa: E402

DIZIN = KOK / "ozel" / "10kasim"
P.update({"tahta": (24, 36, 34), "tahta_acik": (38, 54, 50), "tebesir": (226, 230, 222), "tebesir_koyu": (150, 160, 152)})


# ------------------------------------------------------------------ çizim parçaları
def saat_ciz(d, cx, cy, r, saat, dakika, parla=0.0):
    d.ellipse([cx - r - 3, cy - r - 3, cx + r + 3, cy + r + 3], fill=c("altin_koyu"))
    d.ellipse([cx - r - 1, cy - r - 1, cx + r + 1, cy + r + 1], fill=c("altin"))
    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=c("kagit"))
    for k in range(60):
        a = k / 60 * 2 * math.pi
        uz = 5 if k % 5 == 0 else 2
        x0, y0 = cx + (r - 2) * math.sin(a), cy - (r - 2) * math.cos(a)
        x1, y1 = cx + (r - 2 - uz) * math.sin(a), cy - (r - 2 - uz) * math.cos(a)
        if k % 5 == 0:
            d.line([(x0, y0), (x1, y1)], fill=c("murekkep"), width=2)
        elif r > 30:
            d.point((x0, y0), fill=c("kagit_koyu"))
    ad = (dakika / 60) * 2 * math.pi
    ah = ((saat % 12) / 12 + dakika / 720) * 2 * math.pi
    d.line([(cx, cy), (cx + r * 0.52 * math.sin(ah), cy - r * 0.52 * math.cos(ah))], fill=c("murekkep"), width=4)
    d.line([(cx, cy), (cx + r * 0.8 * math.sin(ad), cy - r * 0.8 * math.cos(ad))], fill=c("murekkep"), width=2)
    d.rectangle([cx - 2, cy - 2, cx + 2, cy + 2], fill=c("altin_koyu"))


def saray(d, taban, renk="gece1", pencere="gece2", isik_oran=0.0):
    """Dolmabahçe silüeti (sadeleştirilmiş): uzun iki katlı cephe, ortada yüksek tören salonu ve kubbe."""
    d.rectangle([12, taban - 30, 258, taban], fill=c(renk))
    d.rectangle([96, taban - 48, 174, taban], fill=c(renk))
    d.ellipse([112, taban - 64, 158, taban - 36], fill=c(renk))
    d.rectangle([133, taban - 70, 137, taban - 62], fill=c(renk))
    for x in (12, 246):
        d.rectangle([x, taban - 36, x + 12, taban], fill=c(renk))
    rng = random.Random(4)
    for kat, wy in enumerate((taban - 26, taban - 14)):
        for x in range(18, 252, 7):
            if 96 <= x <= 174:
                continue
            yanik = rng.random() < isik_oran
            d.rectangle([x, wy, x + 2, wy + 7], fill=c("lamba_koyu") if yanik else c(pencere))
    for x in range(102, 170, 9):
        d.rectangle([x, taban - 40, x + 4, taban - 6], fill=c(pencere))
        d.ellipse([x, taban - 42, x + 4, taban - 38], fill=c(pencere))


def deniz(arr, y0, lt):
    C.gradyan(arr, y0, SH, ["deniz_acik", "deniz", "gece1"])
    im = Image.fromarray(arr)
    d = ImageDraw.Draw(im)
    rng = random.Random(7)
    for k in range(70):
        x = (rng.randrange(SW) + int(lt * (4 + k % 5))) % SW
        y = y0 + 4 + rng.randrange(SH - y0 - 8)
        w = rng.randint(3, 9)
        d.line([(x, y), (x + w, y)], fill=c("gece3") if k % 3 else c("deniz_acik"))
    arr[:] = np.array(im)


def tahta(arr, x0=22, y0=96, x1=248, y1=250):
    im = Image.fromarray(arr)
    d = ImageDraw.Draw(im)
    d.rectangle([x0 - 5, y0 - 5, x1 + 5, y1 + 5], fill=c("ahsap"))
    d.rectangle([x0 - 5, y0 - 5, x1 + 5, y0 - 4], fill=c("ahsap_acik"))
    d.rectangle([x0, y0, x1, y1], fill=c("tahta"))
    rng = random.Random(11)
    for _ in range(160):  # tebeşir tozu izleri
        d.point((rng.randint(x0, x1), rng.randint(y0, y1)), fill=c("tahta_acik"))
    d.rectangle([x0 - 8, y1 + 5, x1 + 8, y1 + 9], fill=c("ahsap_koyu"))
    d.rectangle([x1 - 40, y1 + 2, x1 - 30, y1 + 5], fill=c("tebesir"))
    arr[:] = np.array(im)


def sinif_zemini(arr):
    C.gradyan(arr, 0, 270, ["gece1", "duvar", "duvar"])
    C.gradyan(arr, 270, SH, ["ahsap", "ahsap_koyu", "gece1"])


def siralar(d, y, n=5, kisi=True, lt=0.0, cocuk_buyuk=False):
    for i in range(n):
        x = 22 + i * 48
        if kisi:
            buyuk = cocuk_buyuk and i % 2 == 1
            bh = 12 if buyuk else 9
            sall = int(math.sin(lt * 2 + i) > 0.92)
            d.rectangle([x + 12, y - bh - 6, x + 24, y], fill=c("gece3"))
            d.ellipse([x + 13, y - bh - 15 - sall, x + 23, y - bh - 5 - sall], fill=c("gece3"))
        d.rectangle([x, y, x + 38, y + 4], fill=c("ahsap_acik"))
        d.rectangle([x + 2, y + 4, x + 4, y + 18], fill=c("ahsap_koyu"))
        d.rectangle([x + 34, y + 4, x + 36, y + 18], fill=c("ahsap_koyu"))


def ucak(d, x, y, egim=0.0, lt=0.0):
    """Çift kanatlı pervaneli uçak (sağa uçar)."""
    def p(px, py):
        return (x + px, y + py - px * egim)
    d.polygon([p(0, 0), p(26, -1), p(30, 2), p(26, 5), p(2, 4), p(-4, 2)], fill=c("gumus"))
    d.polygon([p(-4, 2), p(-6, -6), p(0, -5), p(2, 1)], fill=c("gumus_koyu"))
    d.polygon([p(8, -7), p(22, -7), p(22, -5), p(8, -5)], fill=c("gumus_koyu"))
    d.polygon([p(8, 5), p(22, 5), p(22, 7), p(8, 7)], fill=c("gumus_koyu"))
    d.line([p(11, -5), p(11, 5)], fill=c("soluk"))
    d.line([p(19, -5), p(19, 5)], fill=c("soluk"))
    d.point(p(18, 0), fill=c("bayrak"))
    d.point(p(17, 0), fill=c("bayrak"))
    pv = int(lt * 20) % 2
    d.line([p(31, -4 + pv), p(31, 8 - pv)], fill=c("beyaz"))
    d.rectangle([p(12, 9)[0], p(12, 9)[1], p(13, 10)[0] + 1, p(13, 10)[1] + 1], fill=c("gece1"))


def bulut(d, x, y, w, renk="gece3"):
    d.rectangle([x, y, x + w, y + 5], fill=c(renk))
    d.rectangle([x + w // 5, y - 4, x + w * 3 // 5, y], fill=c(renk))
    d.rectangle([x + w // 2, y - 7, x + w * 4 // 5, y], fill=c(renk))


def tebesir_yazi(yk, satirlar, oran, x, y0, satir_h=20, boyut=50, altin=(), hiza="orta"):
    toplam = sum(len(s) for s in satirlar)
    n = int(toplam * max(0, min(1, oran)))
    for j, s in enumerate(satirlar):
        g = s[:max(0, min(len(s), n))]
        n -= len(s)
        if g:
            sx = x - yazi_genislik(s, "piksel", boyut) // 2 if hiza == "orta" else x
            yaz(yk, g, sx, R(y0 + j * satir_h), "sol", boyut=boyut,
                renk="altin_acik" if j in altin else "tebesir", kenar=0)


# ------------------------------------------------------------------ 1. kanca: 10 Kasım 1938, 09.05
class Kanca(Sahne):
    def __init__(self, ctx):
        super().__init__(ctx)
        self.t10 = self.kt("10")
        self.t_dokuz = self.kt("dokuzu")
        self.t_dur = self.kt("duruyor.")
        self.t_isik = self.kt("ışık,")

    def olaylar(self):
        ev = [(self.t10, "daktilo")]
        t = 0.3
        while t < self.t_dur + 0.1:
            ev.append((t, "tik"))
            t += 1.0
        return ev + [(self.t_dur + 0.15, "durak"), (self.t_isik, "isik")]

    def ciz(self, lt, arr):
        sabah = ease(self.t_isik - 0.3, 2.5, lt)
        C.gradyan(arr, 0, 285, ["gece1", "gece1", "gece2", "gece3", "ufuk"] if sabah < 0.5 else
                  ["gece1", "gece2", "gece3", "ufuk", "lamba_koyu"])
        im = Image.fromarray(arr)
        d = ImageDraw.Draw(im)
        C.yildiz_ciz(d, lt, adet=int(60 * (1 - sabah * 0.7)), ymax=200)
        arr[:] = np.array(im)
        if sabah > 0:
            C.isik(arr, 135, 286, 40 + 90 * sabah, "lamba", 0.9 * sabah)
        deniz(arr, 285, lt)
        im = Image.fromarray(arr)
        d = ImageDraw.Draw(im)
        saray(d, 286, isik_oran=0.25)
        # saat: 08.58'den 09.05'e ilerler, "duruyor"da durur
        u = ease(0.0, max(0.5, self.t_dur - 0.2), lt)
        dakika_top = 8 * 60 + 58 + 7 * u
        saat_ciz(d, 135, 150, 46, dakika_top // 60, dakika_top % 60)
        arr[:] = np.array(im)
        if lt >= self.t_isik:
            C.isik(arr, 135, 150, 75 * ease(self.t_isik, 1.0, lt), "lamba_acik", 0.6)
        yk = YaziKatmani()
        if lt >= self.t10 - 0.05:
            yaz(yk, daktilo("10 KASIM 1938", (lt - self.t10 + 0.05) / 1.0),
                RX - yazi_genislik("10 KASIM 1938", "piksel", 100) // 2, R(62), "sol", boyut=100, bant="altin", kenar=8)
        if lt >= self.t_dokuz:
            u = ease(self.t_dokuz, 0.3, lt)
            yaz(yk, "09.05", RX, R(208 - 4 * (1 - u)), boyut=80, renk="beyaz", kenar=8)
        if lt >= self.t_dur + 0.1:
            yaz(yk, "DOLMABAHÇE", RX, R(234), boyut=47, renk="soluk", kenar=6)
        return yk


# ------------------------------------------------------------------ 2. açılış: Arpama + yarıya inmiş bayrak
class Acilis(Sahne):
    def olaylar(self):
        return [(0.1, "bayrak_acilis")]

    def ciz(self, lt, arr):
        C.gradyan(arr, 0, SH, ["gece1", "gece2", "gece2", "gece1"])
        C.isik(arr, 135, 190, 110, "gece3", 1.0)
        im = Image.fromarray(arr)
        d = ImageDraw.Draw(im)
        C.yildiz_ciz(d, lt, adet=40, ymax=300, tohum=9)
        arr[:] = np.array(im)
        # gönder 120'de başlar, bayrak yarıda
        arr[140:246, 103:105] = c("gumus_koyu")
        arr[140:246, 103] = c("beyaz")
        arr[136:140, 102:106] = c("altin")
        C.bayrak_ciz(arr, 106, 178, 40, lt * 0.6 + 0.5, dalga=0.7, gondere=False)
        yk = YaziKatmani()
        logo(yk, RX, 260, 110, oran=ease(0.1, 0.6, lt), tohum=3)
        if lt > 0.7:
            u = ease(0.7, 0.4, lt)
            yaz(yk, "10 KASIM ÖZEL", RX, 440 + int(10 * (1 - u)), boyut=47, renk="altin_acik")
        if lt > 1.0:
            yaz(yk, daktilo("BİLİMİN IŞIĞINDA", (lt - 1.0) / 1.0), RX - yazi_genislik("BİLİMİN IŞIĞINDA", "piksel", 80) // 2,
                R(262), "sol", boyut=80, bant="altin", kenar=8)
        return yk


# ------------------------------------------------------------------ 3. Samsun 1924: ilim
class Ilim(Sahne):
    SOZ = ['"DÜNYADA HER ŞEY İÇİN,', "MEDENİYET İÇİN,", "HAYAT İÇİN,", "MUVAFFAKİYET İÇİN,", "EN HAKİKİ MÜRŞİT",
           'İLİMDİR, FENDİR."']

    def __init__(self, ctx):
        super().__init__(ctx)
        self.t_ogr = self.kt("öğretmenlerle")
        self.t_a, self.t_a_son = self.cumle_araligi("Dünyada", "fendir.")
        self.t_mursit = self.kt("Mürşit,")
        self.t_isik = self.kt("ışığında")

    def olaylar(self):
        ev = [(self.t_a + i * 0.16, "tebesir") for i in range(int((self.t_a_son - self.t_a) / 0.16))]
        return ev + [(self.t_mursit, "silgi"), (self.t_isik, "isik")]

    def ciz(self, lt, arr):
        sinif_zemini(arr)
        tahta(arr)
        im = Image.fromarray(arr)
        d = ImageDraw.Draw(im)
        if lt >= self.t_ogr:
            siralar(d, 300, lt=lt)
        arr[:] = np.array(im)
        yk = YaziKatmani()
        yaz(yk, "SAMSUN · 22 EYLÜL 1924", RX, R(66), boyut=60, bant="altin", kenar=8)
        if lt < self.t_a - 0.2:
            yaz(yk, "22.9.1924", R(220), R(104), "sag", boyut=40, renk="tebesir_koyu", kenar=0)
            if lt >= self.t_ogr:
                yaz(yk, "ÖĞRETMENLERLE", RX, R(160), boyut=67, renk="tebesir", kenar=0)
        elif lt < self.t_mursit - 0.15:
            tebesir_yazi(yk, self.SOZ, (lt - self.t_a) / max(0.5, self.t_a_son - self.t_a), RX, 108, 22, 50, altin=(4, 5))
            if lt > self.t_a_son:
                yaz(yk, "ATATÜRK", R(232), R(232), "sag", boyut=40, renk="tebesir_koyu", kenar=0)
        else:
            yaz(yk, "MÜRŞİT", RX, R(118), boyut=100, renk="altin_acik", kenar=0)
            yaz(yk, "=", RX, R(152), boyut=67, renk="tebesir", kenar=0)
            yaz(yk, "YOL GÖSTEREN", RX, R(176), boyut=80, renk="tebesir", kenar=0)
            if lt >= self.t_isik:
                im = Image.fromarray(arr)
                d = ImageDraw.Draw(im)
                # yıldız/pusula
                cx, cy, r = 135, 226, 9
                d.polygon([(cx, cy - r), (cx + 3, cy - 3), (cx + r, cy), (cx + 3, cy + 3), (cx, cy + r),
                           (cx - 3, cy + 3), (cx - r, cy), (cx - 3, cy - 3)], fill=c("altin"))
                arr[:] = np.array(im)
                C.isik(arr, 135, 226, 60 * ease(self.t_isik, 0.8, lt), "lamba_acik", 0.7)
        return yk


# ------------------------------------------------------------------ 4. 1928: harfler, Başöğretmen
class Harf(Sahne):
    ALFABE = "A B C Ç D E F G Ğ H I İ J K L M N O Ö P R S Ş T U Ü V Y Z".split()

    def __init__(self, ctx):
        super().__init__(ctx)
        self.t1928 = self.kt("1928'de")
        self.t_teb = self.kt("tebeşiri")
        self.t_millet = self.kt("Millet")
        self.t_bas = self.kt("Başöğretmen")
        self.t_gun = self.kt("O")

    def olaylar(self):
        ev = []
        t0, t1 = self.t1928 + 0.4, self.t_millet - 0.3
        for i in range(len(self.ALFABE)):
            ev.append((t0 + (t1 - t0) * i / len(self.ALFABE), "tebesir"))
        return ev + [(self.t_millet, "zil_okul"), (self.t_bas, "muhur_buyuk")]

    def ciz(self, lt, arr):
        sinif_zemini(arr)
        tahta(arr)
        im = Image.fromarray(arr)
        d = ImageDraw.Draw(im)
        if lt >= self.t_millet:
            siralar(d, 300, lt=lt, cocuk_buyuk=True)
        arr[:] = np.array(im)
        yk = YaziKatmani()
        yaz(yk, "1928 · YENİ TÜRK HARFLERİ", RX, R(66), boyut=60, bant="altin", kenar=8)
        t0, t1 = self.t1928 + 0.4, self.t_millet - 0.3
        n = int(len(self.ALFABE) * ease(t0, t1 - t0, lt) + (0.999 if lt >= t1 else 0)) if lt >= t0 else 0
        if lt < self.t_gun - 0.2:
            for i, h in enumerate(self.ALFABE[:n]):
                sat, sut = divmod(i, 8)
                x = 46 + sut * 25
                y = 106 + sat * 30
                renk = "altin_acik" if h in ("Ç", "Ğ", "İ", "Ö", "Ş", "Ü") else "tebesir"
                yaz(yk, h, R(x), R(y), boyut=100, renk=renk, kenar=0)
            if lt >= self.t_millet:
                im = Image.fromarray(arr)
                d = ImageDraw.Draw(im)
                kart(d, yk, ["1 OCAK 1929", "MİLLET MEKTEPLERİ"], 346, self.t_millet, lt)
                arr[:] = np.array(im)
        else:
            u = ease(self.t_gun - 0.2, 0.4, lt)
            arr[:] = C.karart(arr, 0.85 * u)
            if lt >= self.t_bas - 0.05:
                yaz(yk, "BAŞÖĞRETMEN", RX, R(150), boyut=134, bant="altin", kenar=10)
                yaz(yk, "MUSTAFA KEMAL ATATÜRK", RX, R(200), boyut=60, renk="beyaz")
                yaz(yk, "24 KASIM 1928", RX, R(222), boyut=47, renk="soluk")
        return yk


# ------------------------------------------------------------------ 5. 1933 üniversite + Geometri kitabı
class Bilim(Sahne):
    def __init__(self, ctx):
        super().__init__(ctx)
        self.t1933 = self.kt("1933'te")
        self.t_avr = self.kt("Avrupa'dan")
        self.t_geo = self.kt("Atatürk")
        self.t_aci = self.kt("Açı,")
        self.t_ucg = self.kt("üçgen,")
        self.t_ken = self.kt("kenar,")
        self.t_cap = self.kt("çap,")
        self.t_yar = self.kt("yarıçap.")
        self.t_bugun = self.kt("Bugün")

    def olaylar(self):
        return [(self.t1933, "muhur"), (self.t_geo, "kagit"), (self.t_aci, "kalem_cizgi"), (self.t_ucg, "kalem_cizgi"),
                (self.t_ken, "pim"), (self.t_cap, "kalem_cizgi"), (self.t_yar, "pim"), (self.t_bugun, "isik")]

    def ciz(self, lt, arr):
        if lt < self.t_geo - 0.2:
            return self._universite(lt, arr)
        yeni = arr.copy()
        yk = self._geometri(lt, yeni)
        u = ease(self.t_geo - 0.2, 0.6, lt)
        if u < 1:
            eski = arr.copy()
            self._universite(lt, eski)
            arr[:] = C.gecis(eski, yeni, u)
        else:
            arr[:] = yeni
        return yk

    def _universite(self, lt, arr):
        C.gradyan(arr, 0, 280, ["gece1", "gece2", "gece3"])
        C.gradyan(arr, 280, SH, ["tas_koyu", "duvar", "gece1"])
        im = Image.fromarray(arr)
        d = ImageDraw.Draw(im)
        C.yildiz_ciz(d, lt, adet=40, ymax=150, tohum=5)
        # kapı (kemerli, iki kuleli)
        d.rectangle([60, 170, 210, 280], fill=c("tas"))
        for x in (52, 196):
            d.rectangle([x, 150, x + 22, 280], fill=c("tas"))
            d.polygon([(x - 2, 150), (x + 24, 150), (x + 11, 132)], fill=c("tas_koyu"))
        d.rectangle([100, 200, 170, 280], fill=c("gece1"))
        d.ellipse([100, 180, 170, 220], fill=c("gece1"))
        d.rectangle([60, 166, 210, 172], fill=c("tas_koyu"))
        for x in range(68, 205, 12):
            if not 96 < x < 172:
                d.rectangle([x, 186, x + 5, 200], fill=c("lamba") if (x // 12) % 2 else c("lamba_koyu"))
        arr[:] = np.array(im)
        C.isik(arr, 135, 240, 50, "lamba", 0.5)
        im = Image.fromarray(arr)
        d = ImageDraw.Draw(im)
        # gelen bilim insanları: kitaplı küçük figürler kapıya yürür
        if lt >= self.t_avr:
            for k in range(6):
                g = lt - self.t_avr - k * 0.35
                if g < 0:
                    continue
                yon = -1 if k % 2 else 1
                x = 135 + yon * max(0, 120 - g * 28) + (k - 3) * 2
                y = 300 + (k % 3) * 6
                d.rectangle([x - 2, y - 8, x + 2, y], fill=c("gece3"))
                d.ellipse([x - 2, y - 13, x + 2, y - 9], fill=c("gece3"))
                d.rectangle([min(x + 2 * yon, x + 4 * yon), y - 6, max(x + 2 * yon, x + 4 * yon), y - 3], fill=c("altin_koyu"))
        arr[:] = np.array(im)
        yk = YaziKatmani()
        if lt >= self.t1933:
            yaz(yk, "1933", RX, R(66), boyut=100, bant="altin", kenar=8)
            yaz(yk, "ÜNİVERSİTE REFORMU", RX, R(100), boyut=60, renk="gumus")
        if lt >= self.t_avr:
            im = Image.fromarray(arr)
            d = ImageDraw.Draw(im)
            kart(d, yk, ["İSTANBUL ÜNİVERSİTESİ", "AVRUPA'DAN BİLİM İNSANLARI"], 346, self.t_avr, lt, ust_boyut=50, alt_boyut=40)
            arr[:] = np.array(im)
        return yk

    def _geometri(self, lt, arr):
        C.gradyan(arr, 0, SH, ["gece1", "ahsap_koyu", "gece1"])
        im = Image.fromarray(arr)
        d = ImageDraw.Draw(im)
        x0, y0, x1, y1 = 20, 92, 250, 330
        d.rectangle([x0 + 3, y0 + 3, x1 + 3, y1 + 3], fill=c("gece1"))
        d.rectangle([x0, y0, x1, y1], fill=c("kagit"))
        for x in range(x0 + 10, x1, 10):
            d.line([(x, y0), (x, y1)], fill=c("kagit_koyu"))
        for y in range(y0 + 10, y1, 10):
            d.line([(x0, y), (x1, y)], fill=c("kagit_koyu"))
        mur, alt = c("murekkep"), c("bayrak_koyu")
        # AÇI
        if lt >= self.t_aci:
            u = ease(self.t_aci, 0.4, lt)
            o = (40, 175)
            d.line([o, (o[0] + 75 * u, o[1])], fill=mur, width=2)
            d.line([o, (o[0] + 55 * u, o[1] - 50 * u)], fill=mur, width=2)
            if u >= 1:
                d.arc([o[0] - 18, o[1] - 18, o[0] + 18, o[1] + 18], 318, 360, fill=alt, width=2)
        # ÜÇGEN + KENAR
        A, B, Cc = (150, 180), (232, 180), (180, 112)
        if lt >= self.t_ucg:
            u = ease(self.t_ucg, 0.5, lt)
            pts = [A, Cc, B, A]
            seg = u * 3
            for i in range(3):
                f = max(0, min(1, seg - i))
                if f > 0:
                    a, b = pts[i], pts[i + 1]
                    d.line([a, (a[0] + (b[0] - a[0]) * f, a[1] + (b[1] - a[1]) * f)], fill=mur, width=2)
        if lt >= self.t_ken:
            d.line([A, B], fill=c("altin_koyu"), width=4)
        # ÇAP + YARIÇAP
        O, r = (135, 262), 44
        if lt >= self.t_cap:
            u = ease(self.t_cap, 0.5, lt)
            d.arc([O[0] - r, O[1] - r, O[0] + r, O[1] + r], 0, 360 * u, fill=mur, width=2)
            if u >= 1:
                d.line([(O[0] - r, O[1]), (O[0] + r, O[1])], fill=alt, width=2)
        if lt >= self.t_yar:
            a = math.radians(-50)
            d.line([O, (O[0] + r * math.cos(a), O[1] + r * math.sin(a))], fill=c("altin_koyu"), width=3)
            d.rectangle([O[0] - 1, O[1] - 1, O[0] + 1, O[1] + 1], fill=mur)
        arr[:] = np.array(im)
        yk = YaziKatmani()
        yaz(yk, "GEOMETRİ · 1936-37", RX, R(66), boyut=60, bant="altin", kenar=8)
        if lt < self.t_aci:
            yaz(yk, "GEOMETRİ", RX, R(170), boyut=134, renk="murekkep", kenar=0)
            yaz(yk, "ATATÜRK'ÜN KALEMİNDEN", RX, R(214), boyut=50, renk="bayrak_koyu", kenar=0)
        etiketler = [(self.t_aci, "AÇI", 82, 186), (self.t_ucg, "ÜÇGEN", 190, 100), (self.t_ken, "KENAR", 191, 186),
                     (self.t_cap, "ÇAP", 72, 256), (self.t_yar, "YARIÇAP", 212, 220)]
        for t0, ad, x, y in etiketler:
            if lt >= t0:
                yaz(yk, ad, R(x), R(y), boyut=50, renk="bayrak_koyu" if ad in ("AÇI", "ÇAP") else "murekkep", kenar=0)
        if lt >= self.t_bugun:
            im = Image.fromarray(arr)
            d = ImageDraw.Draw(im)
            kart(d, yk, ["BUGÜN DE", "MATEMATİK DERSİNDE"], 346, self.t_bugun, lt)
            arr[:] = np.array(im)
        return yk


# ------------------------------------------------------------------ 6. gökler: Türk Tayyare Cemiyeti, Sabiha Gökçen
class Gok(Sahne):
    def __init__(self, ctx):
        super().__init__(ctx)
        self.t1925 = self.kt("1925'te")
        self.t_sab = self.kt("Sabiha")
        self.t_cun = self.kt("Çünkü")
        self.t_zor = self.kt("zorunluluk.")

    def olaylar(self):
        return [(self.t1925, "ucak"), (self.t_sab, "pim"), (self.t_cun, "ucak"), (self.t_zor, "isik")]

    def ciz(self, lt, arr):
        C.gradyan(arr, 0, SH, ["gece1", "gece2", "gece3", "ufuk", "lamba_koyu", "gece1"])
        im = Image.fromarray(arr)
        d = ImageDraw.Draw(im)
        C.yildiz_ciz(d, lt, adet=50, ymax=170, tohum=12)
        rng = random.Random(3)
        for k in range(9):
            hiz = 3 + k % 4
            w = rng.randint(24, 50)
            x = (rng.randint(0, SW + 60) - lt * hiz) % (SW + 80) - 60
            bulut(d, int(x), rng.randint(130, 320), w, "gece3" if k % 2 else "ufuk")
        # uçak: 1925'ten itibaren soldan girer, sonra ortada süzülür, "Çünkü"de yükselir
        if lt >= self.t1925 - 0.3:
            g = lt - (self.t1925 - 0.3)
            x = min(118, -40 + g * 55)
            y = 238 + 4 * math.sin(lt * 1.6)
            egim = 0.0
            if lt >= self.t_cun:
                h = ease(self.t_cun, 3.0, lt)
                x += h * 80
                y -= h * 120
                egim = 0.35 * min(1, (lt - self.t_cun) * 2)
            for k in range(1, 6):  # duman izi
                d.point((x - 6 - k * 5, y + 2 + k * egim * 5), fill=c("gumus_koyu") if k < 3 else c("gece3"))
            ucak(d, int(x), int(y), egim, lt)
        arr[:] = np.array(im)
        yk = YaziKatmani()
        if lt < self.t1925:
            yaz(yk, "GELECEK GÖKLERDE", RX, R(66), boyut=60, bant="altin", kenar=8)
        else:
            yaz(yk, "1925", RX, R(66), boyut=100, bant="altin", kenar=8)
            yaz(yk, "TÜRK TAYYARE CEMİYETİ", RX, R(100), boyut=60, renk="gumus")
            yaz(yk, "BUGÜNKÜ TÜRK HAVA KURUMU", RX, R(120), boyut=40, renk="soluk")
        im = Image.fromarray(arr)
        d = ImageDraw.Draw(im)
        if self.t_sab <= lt < self.t_cun - 0.1:
            kart(d, yk, ["SABİHA GÖKÇEN", "İLK TÜRK KADIN ASKERİ PİLOT"], 346, self.t_sab, lt, ust_boyut=67, alt_boyut=40)
        arr[:] = np.array(im)
        if lt >= self.t_cun + 0.6:
            yaz(yk, "BİLİM + TEKNOLOJİ", RX, R(168), boyut=67, renk="beyaz")
        if lt >= self.t_zor - 0.1:
            yaz(yk, "TERCİH DEĞİL, ZORUNLULUK", RX, R(192), boyut=50, bant="altin", kenar=6)
        return yk


# ------------------------------------------------------------------ 7. kapanış: söz, gençler, saygıyla anma
class Kapanis(Sahne):
    SOZ1 = ['"BENİ GÖRMEK DEMEK', "MUTLAKA YÜZÜMÜ", 'GÖRMEK DEĞİLDİR."']
    SOZ2 = ['"BENİM FİKİRLERİMİ,', "BENİM DUYGULARIMI", "ANLIYORSANIZ VE", "HİSSEDİYORSANIZ,", 'BU KÂFİDİR."']

    def __init__(self, ctx):
        super().__init__(ctx)
        self.t1, self.t1_son = self.cumle_araligi("Beni", "değildir.")
        self.t2, self.t2_son = self.cumle_araligi("Benim", "kâfidir.")
        self.t_bugun = self.kt("Bugün")
        self.t_prob = self.kt("problemi")
        self.t_kod = self.kt("kod")
        self.t_den = self.kt("deneyi")
        self.t_ulu = self.kt("Ulu")
        self.t_88 = self.kt("88.")
        self.t_saygi = self.kt("saygı,")

    def olaylar(self):
        ev = [(self.t1, "alinti"), (self.t2, "alinti"), (self.t_prob, "blip"), (self.t_kod, "blip"), (self.t_den, "blip"),
              (self.t_ulu, "bayrak_acilis"), (self.t_saygi, "final")]
        return ev

    def ciz(self, lt, arr):
        C.gradyan(arr, 0, SH, ["gece1", "gece2", "gece3", "gece2", "gece1"])
        im = Image.fromarray(arr)
        d = ImageDraw.Draw(im)
        C.yildiz_ciz(d, lt, adet=80, ymax=SH, tohum=19)
        arr[:] = np.array(im)
        yk = YaziKatmani()
        if lt < self.t_bugun - 0.2:
            if lt >= self.t1 - 0.1:
                tebesir_yazi(yk, self.SOZ1, (lt - self.t1) / max(0.5, self.t1_son - self.t1), RX, 96, 24, 67)
            if lt >= self.t2 - 0.1:
                tebesir_yazi(yk, self.SOZ2, (lt - self.t2) / max(0.5, self.t2_son - self.t2), RX, 186, 24, 67, altin=(0, 4))
            if lt > self.t2_son + 0.2:
                yaz(yk, "— ATATÜRK", R(225), R(312), "sag", boyut=47, renk="soluk")
            for op in yk.ops:
                pass
            # tebesir rengi yerine gece için beyaz/gümüş
            return yk
        if lt < self.t_ulu - 0.2:
            ikonlar = [(self.t_prob, "PROBLEM", "x+y=?"), (self.t_kod, "KOD", "</>"), (self.t_den, "DENEY", None)]
            im = Image.fromarray(arr)
            d = ImageDraw.Draw(im)
            for i, (t0, ad, sembol) in enumerate(ikonlar):
                if lt < t0:
                    continue
                u = ease(t0, 0.3, lt)
                y = 120 + i * 62 - int((1 - u) * 10)
                d.rectangle([50, y, 220, y + 48], fill=c("gece1"), outline=c("mavi"))
                d.rectangle([50, y, 220, y + 3], fill=c("mavi_acik"))
                if sembol is None:  # deney şişesi
                    fx, fy = 82, y + 8
                    d.rectangle([fx - 3, fy, fx + 3, fy + 12], outline=c("gumus"))
                    d.polygon([(fx - 3, fy + 12), (fx + 3, fy + 12), (fx + 12, fy + 34), (fx - 12, fy + 34)], fill=c("gumus"))
                    d.polygon([(fx - 7, fy + 24), (fx + 7, fy + 24), (fx + 11, fy + 32), (fx - 11, fy + 32)], fill=c("mavi_acik"))
                    if int(lt * 4) % 2:
                        d.point((fx + 1, fy - 3), fill=c("mavi_buz"))
                else:
                    yaz(yk, sembol, R(82), R(y + 10), boyut=67, renk="altin" if ad == "KOD" else "mavi_buz")
                yaz(yk, ad, R(160), R(y + 14), boyut=67, renk="beyaz")
            arr[:] = np.array(im)
            yaz(yk, "O FİKİRLER YAŞIYOR", RX, R(72), boyut=67, bant="altin", kenar=8)
            return yk
        # saygıyla anma: yarıya inmiş bayrak
        u = ease(self.t_ulu - 0.2, 0.6, lt)
        arr[130:200, 103:105] = c("gumus_koyu")
        arr[130:200, 103] = c("beyaz")
        arr[126:130, 102:106] = c("altin")
        C.bayrak_ciz(arr, 106, 154, 32, lt * 0.6, dalga=0.7, gondere=False)
        if u < 1:
            arr[:] = C.karart(arr, 1 - u)
        yaz(yk, "MUSTAFA KEMAL", RX, R(214), boyut=80, renk="beyaz", kenar=8)
        yaz(yk, "ATATÜRK", RX, R(238), boyut=134, bant="altin", kenar=10)
        yaz(yk, "1881 — 1938", RX, R(276), boyut=60, renk="gumus")
        if lt >= self.t_88:
            yaz(yk, "AYRILIŞININ 88. YILINDA", RX, R(72), boyut=60, renk="gumus")
        if lt >= self.t_saygi:
            yaz(yk, "SAYGI, MİNNET VE ÖZLEMLE", RX, R(96), boyut=60, bant="altin", kenar=8)
        return yk


SAHNELER = {"kanca": Kanca, "acilis": Acilis, "ilim": Ilim, "harf": Harf, "bilim": Bilim, "gok": Gok, "kapanis": Kapanis}


class Render(CR.Render):
    def kapak(self, yol):
        arr = np.zeros((SH, SW, 3), np.uint8)
        C.gradyan(arr, 0, 300, ["gece1", "gece2", "gece3", "ufuk"])
        im = Image.fromarray(arr)
        d = ImageDraw.Draw(im)
        C.yildiz_ciz(d, 0.4, adet=60, ymax=260)
        arr[:] = np.array(im)
        deniz(arr, 300, 0.0)
        im = Image.fromarray(arr)
        d = ImageDraw.Draw(im)
        saray(d, 301, isik_oran=0.3)
        saat_ciz(d, 135, 182, 50, 9, 5)
        arr[:] = np.array(im)
        C.isik(arr, 135, 182, 80, "lamba_acik", 0.4)
        yk = YaziKatmani()
        logo(yk, RX, 1700, 100)
        yaz(yk, "10 KASIM 1938", RX, R(66), boyut=100, bant="altin", kenar=10)
        yaz(yk, "09.05", RX, R(98), boyut=67, renk="beyaz")
        yaz(yk, "BİLİMİN", RX, R(318), boyut=120, renk="beyaz", kenar=8)
        yaz(yk, "IŞIĞINDA", RX, R(350), boyut=120, bant="altin", kenar=8)
        yaz(yk, "SAYGI VE ÖZLEMLE", RX, R(352 + 44), boyut=50, renk="gumus")
        img = Image.fromarray(np.repeat(np.repeat(arr, OLCEK, 0), OLCEK, 1), "RGB")
        yk.uygula(img)
        img.save(yol)


def main():
    CR.DIZIN = DIZIN
    CR.SAHNELER = SAHNELER
    ap = argparse.ArgumentParser()
    ap.add_argument("--kareler")
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
