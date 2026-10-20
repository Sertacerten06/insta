"""Bölüm sahneleri (CLAUDE.md §4 şablonu).

Her sahne: olaylar() -> [(yerel_sn, efekt)], ciz(t, d, yk) -> sanal katman + yazı katmanı.
Animasyonlar kelime zaman damgalarına bağlanır (kt()), böylece görüntü sesle senkron kalır.
"""
import math

from cizim import (BANT, GEN, OLCEK, P, SW, bant_dikdortgen, daire, dither_maske, dugme, ikon,
                   ikon_boyut, panel, ust, xp_bar, yazi, yazi_genislik)
import ikonlar as I
from ortak import KOK

CX = GEN // 2                      # içerik alanının yatay ortası (sanal, yerel)
RCX = CX * OLCEK                   # aynı, gerçek piksel


def R(v):
    """sanal -> gerçek piksel"""
    return v * OLCEK


def adim(t, hiz=8):
    """Adımlı (stepped) animasyon için zamanı kareye yuvarla."""
    return math.floor(t * hiz) / hiz


def yanip(t, periyot=0.5, oran=0.6):
    return (t % periyot) < periyot * oran


def sade(s):
    import re
    return re.sub(r"[^\wçğıöşüâîû]", "", s.replace("İ", "i").replace("I", "ı").lower())


class Sahne:
    def __init__(self, ctx):
        self.ctx = ctx
        self.sure = ctx["sure"]
        self.kelimeler = ctx["kelimeler"]  # yerel zamanlı

    def kt(self, anahtar, n=0, tam=False, varsayilan=None):
        """anahtar ile başlayan n. kelimenin yerel başlangıç zamanı."""
        a = sade(anahtar)
        bulunan = 0
        for k in self.kelimeler:
            s = sade(k["k"])
            if (s == a) if tam else s.startswith(a):
                if bulunan == n:
                    return k["bas"]
                bulunan += 1
        if varsayilan is not None:
            return varsayilan
        raise KeyError(f"{type(self).__name__}: '{anahtar}' kelimesi bulunamadı")

    def olaylar(self):
        return []

    def ciz(self, t, d, yk):
        raise NotImplementedError


# ------------------------------------------------------------------ ortak öğeler
def logo(yk, cx, y, boyut=150, oran=1.0, tohum=0):
    """Arpama logosu. brand/arpama-logo.png varsa olduğu gibi kullanılır.
    Yoksa yer tutucu: altın "AR" + gümüş "PAMA" (Sora 700) + "TECHNOLOGY"."""
    dosya = KOK / "brand" / "arpama-logo.png"
    if dosya.exists():
        sp = _logo_png(dosya, boyut * 3)
        yk.ekle(sp, cx, y, "orta", _blok_maske(sp, oran, tohum))
        return sp.height
    ar = yazi("AR", "marka", boyut, bant="altin")
    pama = yazi("PAMA", "marka", boyut, bant="gumus")
    tech = yazi("T E C H N O L O G Y", "metin", boyut // 4, renk="soluk")
    w = ar.width + pama.width + boyut // 12
    x0 = cx - w // 2
    yk.ekle(ar, x0, y, maske=_blok_maske(ar, oran, tohum))
    yk.ekle(pama, x0 + ar.width + boyut // 12, y, maske=_blok_maske(pama, oran, tohum + 1))
    yk.ekle(tech, cx, y + ar.height + boyut // 6, "orta", _blok_maske(tech, oran, tohum + 2))
    return ar.height + boyut // 6 + tech.height


_logo_onbellek = {}


def _logo_png(dosya, genislik):
    from PIL import Image
    if genislik not in _logo_onbellek:
        im = Image.open(dosya).convert("RGBA")
        h = int(im.height * genislik / im.width)
        _logo_onbellek[genislik] = im.resize((genislik, h), Image.LANCZOS)
    return _logo_onbellek[genislik]


def _blok_maske(sprite, oran, tohum):
    """Piksel piksel beliriş: 8px bloklar Bayer sırasıyla açılır."""
    if oran >= 1:
        return None
    import numpy as np
    bw, bh = sprite.width // 8 + 1, sprite.height // 8 + 1
    m = dither_maske(bw, bh, oran)
    m = np.roll(m, tohum, axis=1)
    return np.repeat(np.repeat(m, 8, axis=0), 8, axis=1)


def etiket(d, yk, metin, tarih, ikon_sablon=None, rozet=None):
    """Haber üst etiketi: [rozet] METİN ............ tarih"""
    x = 8
    if rozet:
        w = 18
        d.rectangle([x, 80, x + w - 1, 91], fill=P["kirmizi"])
        yk.yaz(rozet, R(x + w // 2), R(80) + 6, "orta", ad="piksel", boyut=39, renk="beyaz")
        x += w + 4
    if ikon_sablon:
        ikon(d, ikon_sablon, x, 81, 1)
        x += ikon_boyut(ikon_sablon)[0] + 4
    yk.yaz(metin, R(x), R(80) + 4, ad="piksel", boyut=47, bant="altin")
    yk.yaz(tarih, R(GEN - 6), R(80) + 8, "sag", ad="piksel_ince", boyut=39, renk="soluk")


def baslik_kutusu(d, yk, satirlar, y=95, h=37):
    dugme(d, 8, y, GEN - 14, h)
    for i, s in enumerate(satirlar):
        yk.yaz(s, RCX, R(y) + 14 + i * 66, "orta", ad="piksel", boyut=55, renk="beyaz")


def kaynak(yk, metin):
    yk.yaz(metin, R(8), R(283), ad="metin", boyut=30, renk="soluk")


def madde(d, yk, x, y, metin, boyut=39):
    ikon(d, I.MADDE, x, y + 1, 1)
    yk.yaz(metin, R(x + 6), R(y) - 2, ad="piksel", boyut=boyut, renk="gumus")


# ------------------------------------------------------------------ 0. KANCA
class Kanca(Sahne):
    def olaylar(self):
        return [(0.0, "blip"), (0.4, "blip"), (0.8, "blip")]

    def ciz(self, t, d, yk):
        # piksel sınav kâğıdı
        x, y, w, h = CX - 30, 92, 60, 76
        d.rectangle([x + 3, y + 3, x + w + 2, y + h + 2], fill=P["zemin3"])          # piksel gölge
        d.rectangle([x, y, x + w - 1, y + h - 1], fill=P["gumus"], outline=P["gumus_koyu"])
        d.polygon([(x + w - 12, y), (x + w - 1, y), (x + w - 1, y + 11)], fill=P["zemin"])
        d.polygon([(x + w - 12, y), (x + w - 12, y + 11), (x + w - 1, y + 11)], fill=P["gumus_koyu"])
        d.rectangle([x + 6, y + 6, x + 30, y + 8], fill=P["mavi"])
        for i in range(6):
            yy = y + 18 + i * 9
            d.rectangle([x + 6, yy, x + w - 8 - (i % 3) * 7, yy + 1], fill=P["soluk"])
        if yanip(t, 0.5):
            yk.yaz("?", R(CX), R(y + 14), "orta", ad="piksel", boyut=190, bant="altin", kenar=8)
        # başlık satırları kademeli gelir
        if t >= 0.0:
            yk.yaz("YAZILI SORULARINI", RCX, R(180), "orta", ad="piksel", boyut=55, renk="beyaz", kenar=6)
        if t >= 0.4:
            yk.yaz("YAPAY ZEKÂ", RCX, R(197), "orta", ad="piksel", boyut=95, bant="altin", kenar=6)
        if t >= 0.8:
            yk.yaz("MI HAZIRLAYACAK?", RCX, R(240), "orta", ad="piksel", boyut=55, renk="beyaz", kenar=6)


# ------------------------------------------------------------------ 1. AÇILIŞ
class Acilis(Sahne):
    LOGO_T = 1.2

    def olaylar(self):
        return [(0.0, "blip"), (0.5, "blip"), (self.LOGO_T, "jingle_acilis")]

    def ciz(self, t, d, yk):
        if t < self.LOGO_T + 0.2 and yanip(t, 0.4, 0.55):
            yk.yaz("PRESS START", RCX, R(150), "orta", ad="ingilizce_etiket", boyut=48, renk="beyaz")
        if t >= self.LOGO_T:
            oran = min(1.0, adim(t - self.LOGO_T, 10) / 1.0)
            h = logo(yk, RCX, R(112), 150, oran)
            # parıltılar
            for i, (sx, sy) in enumerate([(30, 108), (205, 118), (40, 168), (196, 160)]):
                if oran >= 1 and yanip(t + i * 0.13, 0.6, 0.35):
                    d.point([(sx, sy), (sx - 1, sy), (sx + 1, sy), (sx, sy - 1), (sx, sy + 1)], fill=P["mavi_buz"])
        if t >= self.LOGO_T + 1.2:
            yk.yaz("TEKNOLOJİ GÜNDEMİ", RCX, R(194), "orta", ad="piksel", boyut=55, bant="gumus", kenar=6)
        if t >= self.LOGO_T + 1.6:
            bolum = self.ctx["bolum"]
            yk.yaz(f"BÖLÜM {bolum}", RCX, R(220), "orta", ad="marka", boyut=120, bant="altin")
            d.rectangle([CX - 50, 250, CX + 50, 250], fill=P["cizgi"])


# ------------------------------------------------------------------ 2. HABER: MEB
class HaberMEB(Sahne):
    SINIFLAR = [("5", 0, 0), ("6", 1, 0), ("7", 2, 0), ("9", 0, 1), ("10", 1, 1), ("11", 2, 1)]

    def _acilis(self):
        return {s: self.kt(s, tam=True) for s, _, _ in self.SINIFLAR}

    def olaylar(self):
        o = [(t, "coin") for t in self._acilis().values()]
        o += [(self.kt("açık"), "tik"), (self.kt("binlerce"), "tik"), (self.kt("Peki"), "blip")]
        return o

    def ciz(self, t, d, yk):
        etiket(d, yk, "TÜRKİYE", "16 EKİM", rozet="TR")
        baslik_kutusu(d, yk, ["MEB: ORTAK YAZILI", "SINAV SİSTEMİ"])
        acilis = self._acilis()
        x0, y0, bw, bh, ara = 4, 140, 28, 24, 4
        for s, cx_, cy_ in self.SINIFLAR:
            x, y = x0 + cx_ * (bw + ara), y0 + cy_ * (bh + ara)
            self._kutu(d, yk, x, y, bw, bh, s, t >= acilis[s], t - acilis[s])
        # 12. sınıf: gri ve kilitli kalır
        x, y = x0 + (bw + ara), y0 + 2 * (bh + ara)
        self._kutu(d, yk, x, y, bw, bh, "12", False, 0)
        # sağ taraf: okul binası -> yapay zekâ robotu
        t_robot = self.kt("Peki")
        if t < t_robot:
            self._okul(d, 106, 140)
        else:
            rx = 124
            ikon(d, I.ROBOT, rx, 138, 4)
            if yanip(t - t_robot, 0.5):
                yk.yaz("?", R(rx + 52), R(130), ad="piksel", boyut=95, bant="altin", kenar=5)
            if t >= self.kt("planlanmasında", varsayilan=t_robot + 1.0) or t >= t_robot + 1.0:
                d.rectangle([rx - 18, 192, rx + 64, 205], fill=P["zemin2"], outline=P["altin_koyu"])
                if yanip(t, 0.8, 0.75):
                    yk.yaz("PLANLANIYOR", R(rx + 23), R(193) + 6, "orta", ad="piksel", boyut=39, renk="altin")
        if t >= self.kt("açık"):
            madde(d, yk, 4, 232, "AÇIK UÇLU SORULAR")
        if t >= self.kt("binlerce"):
            madde(d, yk, 4, 248, "HER DÖNEM BİNLERCE YENİ SORU")
        if t >= self.kt("Peki"):
            madde(d, yk, 4, 264, "YAPAY ZEKÂ DESTEĞİ: İLERİDE")
        kaynak(yk, self.ctx["kaynak"])

    def _kutu(self, d, yk, x, y, w, h, s, acik, ta):
        if acik:
            dugme(d, x, y, w, h)
            if ta < 0.2:
                d.rectangle([x - 1, y - 1, x + w, y + h], outline=P["mavi_buz"])
            yk.yaz(s, R(x + w // 2), R(y) + 16, "orta", ad="piksel", boyut=63, renk="beyaz")
        else:
            panel(d, x, y, w, h, bant=2)
            ikon(d, I.KILIT, x + w - 9, y + 3, 1)
            yk.yaz(s, R(x + w // 2) - 8, R(y) + 20, "orta", ad="piksel", boyut=55, renk="soluk")

    def _okul(self, d, x, y):
        w, h = 88, 58
        d.polygon([(x - 4, y + 20), (x + w // 2, y), (x + w + 3, y + 20)], fill=P["mavi_koyu"])
        d.rectangle([x, y + 20, x + w - 1, y + h + 20], fill=P["zemin3"], outline=P["cizgi"])
        for r in range(3):
            for c in range(5):
                wx, wy = x + 5 + c * 16, y + 26 + r * 14
                d.rectangle([wx, wy, wx + 9, wy + 7], fill=P["mavi_acik"] if (r + c) % 3 else P["cizgi"])
        d.rectangle([x + w // 2 - 6, y + h + 6, x + w // 2 + 5, y + h + 20], fill=P["mavi"])
        d.rectangle([x + w // 2, y - 14, x + w // 2, y], fill=P["soluk"])
        d.rectangle([x + w // 2 + 1, y - 14, x + w // 2 + 9, y - 9], fill=P["kirmizi"])


# ------------------------------------------------------------------ 3. HABER: JAXA
class HaberJAXA(Sahne):
    def olaylar(self):
        return [(self.kt("fırlattı"), "whoosh"), (self.kt("2031"), "coin"), (self.kt("Idefix"), "blip"),
                (self.kt("inecek"), "tik")]

    def ciz(self, t, d, yk):
        etiket(d, yk, "DÜNYA", "20 EKİM", ikon_sablon=I.KURE)
        baslik_kutusu(d, yk, ["JAXA: MMX GÖREVİ", "HEDEF: PHOBOS"])
        t_kalk = self.kt("fırlattı")
        t_mars = t_kalk + 2.6
        if t < t_mars:
            self._kalkis(d, yk, t, t_kalk)
        else:
            self._mars(d, yk, t, t_mars)
        kaynak(yk, self.ctx["kaynak"])

    def _kalkis(self, d, yk, t, t_kalk):
        # zemin ve rampa
        d.rectangle([-40, 268, SW, 280], fill=P["zemin3"])
        d.rectangle([-40, 268, SW, 268], fill=P["cizgi"])
        rx = CX - 5
        dt = max(0.0, adim(t - t_kalk, 15))
        yy = 252 - int(40 * dt * dt + 10 * dt)
        d.rectangle([rx - 20, 206, rx - 18, 268], fill=P["soluk"])  # kule
        for k in range(5):
            d.rectangle([rx - 20, 210 + k * 12, rx - 11, 210 + k * 12], fill=P["cizgi"])
        ikon(d, I.ROKET, rx - 11, yy - 48 + 16, 3)
        if t >= t_kalk - 0.6:
            alev = I.ALEV_1 if int(t * 12) % 2 else I.ALEV_2
            ikon(d, alev, rx - 8, yy + 16, 3)
        if t >= t_kalk:  # duman
            for i in range(10):
                sx = rx + 6 + int((i - 5) * (6 + dt * 14))
                d.rectangle([sx - 3, 262 - (i % 3) * 3, sx + 3, 267], fill=P["gumus_koyu"] if i % 2 else P["soluk"])
        if t < t_kalk:
            yk.yaz("H3", R(rx + 18), R(214), ad="piksel", boyut=55, renk="gumus")
            if yanip(t, 0.6):
                yk.yaz("3..2..1", R(rx + 18), R(234), ad="piksel_ince", boyut=39, renk="altin")
        else:
            yk.yaz("KALKIŞ!", R(rx + 22), R(216), ad="piksel", boyut=55, bant="altin", kenar=5)

    def _mars(self, d, yk, t, t_mars):
        mx, my, mr = 142, 206, 34
        # Mars: kırmızı + altın-koyu bantlar, sol kenarda dither gölge
        daire(d, mx, my, mr, P["kirmizi"])
        for (cx_, cy_, r) in [(168, 196, 5), (190, 214, 4), (176, 224, 3), (192, 190, 3)]:
            daire(d, cx_, cy_, r, P["altin_koyu"])
        for yy in range(my - mr, my + mr + 1):
            for xx in range(mx - mr, mx - mr + 14):
                if (xx - mx) ** 2 + (yy - my) ** 2 <= mr * mr and (xx + yy) % 2 == 0:
                    d.point((xx, yy), fill=P["zemin3"])
        yk.yaz("MARS", R(mx), R(my + mr + 3), "orta", ad="piksel_ince", boyut=39, renk="soluk")
        # Phobos: Mars'ın sağ üstünde, yörüngede hafif salınım
        sal = 1 if int(t * 3) % 2 else 0
        px, py = mx + 34, my - 46 + sal
        for k in range(200, 340, 10):
            a = math.radians(k)
            d.point((mx + int(48 * math.cos(a)), my + int(48 * math.sin(a))), fill=P["cizgi"])
        d.ellipse([px - 6, py - 4, px + 6, py + 4], fill=P["gumus_koyu"])
        d.point([(px - 2, py - 1), (px + 2, py + 1), (px - 3, py + 2)], fill=P["soluk"])
        yk.yaz("PHOBOS", R(px), R(py - 18), "orta", ad="piksel", boyut=39, bant="gumus", kenar=4)
        # uzay aracı Phobos'a yaklaşır
        t_in = self.kt("inecek")
        oran = min(1.0, max(0.0, adim(t - t_mars, 8) / max(0.5, t_in - t_mars)))
        ax = int(10 + (px - 20) * oran)
        ay = int(140 + (py - 140) * oran)
        if oran < 1:
            for k in range(1, 6):
                d.point((ax - k * 4, ay - k), fill=P["cizgi"])
        ikon(d, I.UZAY_ARACI, ax - 3, ay - 1, 1)
        if t >= t_in and t < t_in + 2.5 and yanip(t, 0.4):
            yk.yaz("İNİŞ + ÖRNEK", R(px - 10), R(py + 7), "orta", ad="piksel", boyut=39, renk="altin", kenar=4)
        # 2031 dönüş çubuğu
        t_2031 = self.kt("2031")
        if t >= t_2031:
            yk.yaz("DÜNYA'YA DÖNÜŞ: 2031", R(4), R(244) - 6, ad="piksel", boyut=39, renk="gumus")
            xp_bar(d, 4, 256, 110, adim(t - t_2031, 8) / 2.0, "altin")
        # Idefix gezgini
        t_id = self.kt("Idefix")
        if t >= t_id:
            ikon(d, I.GEZGIN, 4, 152, 3)
            yk.yaz("IDEFIX", R(4), R(172), ad="piksel", boyut=47, bant="gumus")
            yk.yaz("30 KG ALTI", R(4), R(185), ad="piksel_ince", boyut=39, renk="soluk")


# ------------------------------------------------------------------ 4. HARİTAM
class Haritam(Sahne):
    GUNLER = ["PZT", "SAL", "ÇAR", "PER", "CUM", "CMT", "PAZ"]
    DERSLER = [["MAT", "FİZ"], ["TÜR", "KİM", "MAT"], ["BİY", "GEO"], ["MAT", "TAR"], ["FİZ", "TÜR", "KİM"],
               ["DNM", "MAT"], ["TEK"]]

    def zamanlar(self):
        z = {
            "boss": self.kt("büyük"), "haritam": self.kt("İşte"), "excel": self.kt("Excel"),
            "kendin": self.kt("kendin"), "gorev": self.kt("görevler"), "tik": self.kt("Bitirdikçe"),
            "seri": self.kt("serini"), "gelisim": self.kt("gelişimini"), "konu": self.kt("Programındaki"),
            "cortex": self.kt("Cortex"),
        }
        return z

    def gorevler(self):
        out = []
        for g, dersler in enumerate(self.DERSLER):
            for r, ders in enumerate(dersler):
                out.append((g, r, ders))
        return out

    def olaylar(self):
        z = self.zamanlar()
        o = [(z["boss"], "boss"), (z["haritam"], "glitch"), (z["haritam"] + 0.1, "blip"), (z["excel"], "tik")]
        for i, _ in enumerate(self.gorevler()):
            if i % 2 == 0:
                o.append((z["gorev"] + i * 0.1, "tik"))
        for i in range(8):
            o.append((z["tik"] + i * 0.18, "blip"))
        o += [(z["seri"], "coin"), (z["konu"], "tik"), (z["cortex"], "coin"), (self.sure - 1.6, "levelup")]
        return o

    def ciz(self, t, d, yk):
        z = self.zamanlar()
        if t < z["boss"]:
            self._kilitli12(d, yk, t)
        elif t < z["haritam"]:
            self._boss(d, yk, t - z["boss"], t, z)
        else:
            self._uygulama(d, yk, t, z)

    def _kilitli12(self, d, yk, t):
        s = min(3, 1 + int(adim(t, 8) / 0.15))
        w, h = 30 * s, 24 * s
        x, y = CX - w // 2, 170 - h // 2
        panel(d, x, y, w, h, bant=2 * s)
        ikon(d, I.KILIT, x + w - 9 * s, y + 3 * s, s)
        yk.yaz("12", R(CX) - 10 * s, R(y + h // 2) - 14 * s, "orta", ad="piksel", boyut=40 * s, renk="soluk")
        if t > 0.5:
            yk.yaz("12. SINIF?", RCX, R(214), "orta", ad="piksel", boyut=63, renk="gumus", kenar=5)
        if t > 0.5 and yanip(t, 0.5):
            yk.yaz("YENİ SİSTEMDE YOK", RCX, R(234), "orta", ad="piksel", boyut=47, renk="soluk")

    def _boss(self, d, yk, tb, t, z):
        if tb < 0.12:
            d.rectangle([-40, 76, SW, 290], fill=P["kirmizi"])
            return
        bob = 2 if int(tb * 4) % 2 else 0
        bw, bh = ikon_boyut(I.BOSS, 4)
        ikon(d, I.BOSS, CX - bw // 2, 96 + bob, 4)
        yk.yaz("YKS", RCX, R(150 + bob), "orta", ad="piksel", boyut=71, bant="altin", kenar=5)
        yk.yaz("BÜYÜK BOSS", RCX, R(188), "orta", ad="piksel", boyut=71, renk="kirmizi", kenar=6)
        # can barı
        d.rectangle([CX - 60, 212, CX + 60, 218], fill=P["zemin2"], outline=P["cizgi"])
        d.rectangle([CX - 59, 213, CX + 59, 217], fill=P["kirmizi"])
        yk.yaz("HP", R(CX - 72), R(210), ad="piksel_ince", boyut=39, renk="soluk")
        t_harita = self.kt("haritaya", varsayilan=z["haritam"] - 1)
        if t >= t_harita and yanip(t, 0.5):
            yk.yaz("GEREKEN: HARİTA", RCX, R(232), "orta", ad="piksel", boyut=55, renk="gumus", kenar=5)

    def _uygulama(self, d, yk, t, z):
        x0, y0, w = 0, 80, GEN
        panel(d, x0, y0, w, 206)
        dugme(d, x0 + 2, y0 + 2, w - 4, 20)
        haritam_logo = KOK / "brand" / "haritam-logo.png"
        yk.yaz("YKS HARİTAM", R(CX), R(y0 + 2) + 10, "orta", ad="piksel", boyut=47, renk="beyaz")
        yk.yaz("HAFTALIK PROGRAM", R(x0 + 4), R(y0 + 25), ad="piksel", boyut=39, renk="altin")
        # Excel yükle / kendin yaz
        if t >= z["excel"]:
            dugme(d, x0 + 112, y0 + 23, 40, 12)
            yk.yaz("EXCEL", R(x0 + 132), R(y0 + 23) + 6, "orta", ad="piksel", boyut=31, renk="beyaz")
        if t >= z["kendin"]:
            d.rectangle([x0 + 156, y0 + 23, x0 + w - 5, y0 + 34], fill=P["zemin3"], outline=P["mavi_acik"])
            yk.yaz("YAZ", R(x0 + 156 + (w - 161) // 2), R(y0 + 23) + 6, "orta", ad="piksel", boyut=31, renk="mavi_acik")
        # takvim
        cw, ara, gx = 26, 2, x0 + 2
        gy = y0 + 38
        for g, ad in enumerate(self.GUNLER):
            x = gx + g * (cw + ara)
            d.rectangle([x, gy, x + cw - 1, gy + 9], fill=P["zemin3"])
            yk.yaz(ad, R(x + cw // 2), R(gy) + 6, "orta", ad="piksel_ince", boyut=31, renk="soluk")
            d.rectangle([x, gy + 10, x + cw - 1, gy + 64], outline=P["cizgi"])
        for i, (g, r, ders) in enumerate(self.gorevler()):
            ti = z["gorev"] + i * 0.1
            if t < ti:
                continue
            x = gx + g * (cw + ara) + 2
            hedef_y = gy + 13 + r * 17
            dus = adim(t - ti, 15)
            y = int(hedef_y - max(0.0, 1 - dus / 0.3) * 30)
            dugme(d, x, y, cw - 4, 14)
            yk.yaz(ders, R(x + (cw - 4) // 2), R(y) + 12, "orta", ad="piksel", boyut=31, renk="beyaz")
            tik_t = z["tik"] + (i % 8) * 0.18 if i < 8 else None
            if tik_t is not None and t >= tik_t:
                ikon(d, I.TIK, x + cw - 11, y + 1, 1)
        # seri + gelişim
        sy = y0 + 108
        if t >= z["seri"]:
            ikon(d, I.YILDIZ, x0 + 4, sy + 2, 2)
            yk.yaz("SERİ: 12 GÜN", R(x0 + 17), R(sy) + 4, ad="piksel", boyut=47, bant="altin")
        if t >= z["gelisim"]:
            xp_bar(d, x0 + 136, sy + 3, w - 142, adim(t - z["gelisim"], 8) / 1.5 * 0.8)
        # konu özetleri eşleşir
        if t >= z["konu"]:
            ky = y0 + 128
            d.rectangle([x0 + 4, ky, x0 + w - 5, ky + 14], fill=P["zemin3"], outline=P["mavi"])
            ikon(d, I.TIK, x0 + 8, ky + 4, 1)
            yk.yaz("KONU ÖZETLERİYLE EŞLEŞTİ", R(x0 + 18), R(ky) + 12, ad="piksel", boyut=39, renk="gumus")
        # Cortex rozeti
        if t >= z["cortex"]:
            cy = y0 + 150
            renk = P["altin"] if yanip(t, 0.6, 0.7) else P["altin_koyu"]
            d.rectangle([x0 + 4, cy, x0 + w - 5, cy + 26], fill=P["zemin2"], outline=renk)
            d.rectangle([x0 + 5, cy + 1, x0 + w - 6, cy + 1], fill=P["altin_koyu"])
            yk.yaz("CORTEX", R(CX), R(cy) + 10, "orta", ad="piksel", boyut=47, bant="altin")
            yk.yaz("YAPAY ZEKÂ · ÇOK YAKINDA", R(CX), R(cy) + 58, "orta", ad="piksel_ince", boyut=31, renk="gumus")
        # alt bilgi
        if t >= self.sure - 1.6:
            yk.yaz("LEVEL UP!", RCX, R(y0 + 182), "orta", ad="ingilizce_etiket", boyut=40, bant="altin")


# ------------------------------------------------------------------ 5. CTA / KAPANIŞ
class Kapanis(Sahne):
    def olaylar(self):
        return [(self.kt("ücretsiz"), "coin"), (self.ctx["ses_son"] + 0.2, "gamesaved"),
                (self.ctx["ses_son"] + 0.2, "jingle_kapanis")]

    def ciz(self, t, d, yk):
        logo(yk, RCX, R(84), 90)
        yk.yaz("haritam.arpama.tr", RCX, R(129), "orta", ad="marka", boyut=74, renk="beyaz")
        d.rectangle([CX - 80, 152, CX + 80, 152], fill=P["cizgi"])
        if t >= self.kt("ücretsiz"):
            basili = int(t * 2) % 2 == 1
            by = 160 + (1 if basili else 0)
            dugme(d, CX - 80, by, 160, 26)
            yk.yaz("ÜCRETSİZ BAŞLA", R(CX - 8), R(by) + 30, "orta", ad="marka", boyut=48, renk="beyaz")
            ikon(d, I.UCGEN_SAG, CX + 64, by + 8, 2)
        if t >= self.kt("telefonuna"):
            ikon(d, I.TELEFON, 28, 196, 2)
            yk.yaz("UYGULAMA OLARAK EKLE", R(48), R(198) + 4, ad="piksel", boyut=31, renk="gumus")
            yk.yaz("TELEFON + BİLGİSAYAR", R(48), R(207) + 6, ad="piksel_ince", boyut=31, renk="soluk")
        if t >= self.kt("takip"):
            handle = self.ctx.get("handle")
            yazi_ = f"TAKİP ET: {handle}" if handle else "ARPAMA'YI TAKİP ET"
            yk.yaz(yazi_, RCX, R(226), "orta", ad="piksel", boyut=47, renk="mavi_acik")
        if t >= self.ctx["ses_son"] + 0.2:
            yk.yaz("GAME SAVED", RCX - 30, R(250), "orta", ad="ingilizce_etiket", boyut=48, bant="altin")
            ikon(d, I.TIK, CX + 62, 251, 2)


SAHNELER = {"kanca": Kanca, "acilis": Acilis, "haber_meb": HaberMEB, "haber_jaxa": HaberJAXA,
            "haritam": Haritam, "cta": Kapanis}
