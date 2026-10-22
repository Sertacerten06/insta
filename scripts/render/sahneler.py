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
    """Kanca: ikon + 3 satır başlık (senaryo.json -> "kanca"). Ortadaki satır altın bantlı."""

    VARSAYILAN = {"ikon": "kagit", "satirlar": ["YAZILI SORULARINI", "YAPAY ZEKÂ", "MI HAZIRLAYACAK?"], "vurgu": 1}

    def olaylar(self):
        return [(0.0, "blip"), (0.4, "blip"), (0.8, "blip")]

    def ciz(self, t, d, yk):
        k = self.ctx.get("kanca") or self.VARSAYILAN
        if k.get("ikon") == "sunucu":
            self._sunucu(d, yk, t)
        elif k.get("ikon") == "uyari":
            self._uyari(d, yk, t)
        else:
            self._kagit(d, yk, t)
        ys = [180, 197, 240]
        for i, satir in enumerate(k["satirlar"][:3]):
            if t < i * 0.4:
                continue
            if i == k.get("vurgu", 1):
                yk.yaz(satir, RCX, R(ys[i]), "orta", ad="piksel", boyut=95, bant="altin", kenar=6)
            else:
                yk.yaz(satir, RCX, R(ys[i]), "orta", ad="piksel", boyut=55, renk="beyaz", kenar=6)

    def _kagit(self, d, yk, t):
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

    def _uyari(self, d, yk, t):
        # telefon + ekranda "KAZANDIN!" mesajı, üstünde yanıp sönen kırmızı uyarı
        x, y = CX - 25, 92
        ikon(d, I.TELEFON, x, y, 7)
        if t >= 0.3:
            d.rectangle([x + 8, y + 10, x + 41, y + 34], fill=P["beyaz"])
            yk.yaz("Kazandın!", R(x + 24), R(y + 13), "orta", ad="marka", boyut=30, renk="mavi_koyu")
            yk.yaz("tıkla >", R(x + 24), R(y + 23), "orta", ad="metin", boyut=26, renk="kirmizi")
        if yanip(t, 0.5):
            d.rectangle([x + 40, y - 4, x + 56, y + 12], fill=P["kirmizi"])
            yk.yaz("!", R(x + 48), R(y - 4) + 2, "orta", ad="piksel", boyut=71, renk="beyaz")

    def _sunucu(self, d, yk, t):
        sw, sh = ikon_boyut(I.SUNUCU, 3)
        for k in range(3):
            x = CX - sw * 3 // 2 - 4 + k * (sw + 4)
            ikon(d, I.SUNUCU, x, 96, 3)
            # yanıp sönen LED'ler
            for j in range(3):
                if yanip(t + k * 0.17 + j * 0.29, 0.5, 0.5):
                    d.rectangle([x + 3 * 3, 96 + (2 + 4 * j) * 3, x + 3 * 3 + 2, 96 + (2 + 4 * j) * 3 + 2],
                                fill=P["mavi_buz"])


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
class Haritam(Sahne):  # Bölüm 1: haftalık program
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
        if t >= self.kt("telefon", varsayilan=1.5):
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


# ------------------------------------------------------------------ Bölüm 2 · HABER: VERİ MERKEZİ
class HaberVeri(Sahne):
    def z(self):
        return {"tesis": self.kt("450"), "mw": self.kt("22", tam=True), "toplam": self.kt("Tüm"),
                "ne": self.kt("Peki"), "saklar": self.kt("Kurumların"), "hedef": self.kt("2030")}

    def olaylar(self):
        z = self.z()
        return [(z["tesis"], "coin"), (z["mw"], "tik"), (z["toplam"], "coin"), (z["saklar"], "blip"),
                (z["hedef"], "levelup")]

    def ciz(self, t, d, yk):
        etiket(d, yk, "TÜRKİYE", "20 EKİM", rozet="TR")
        baslik_kutusu(d, yk, ["ANKARA TEMELLİ:", "YENİ VERİ MERKEZİ"])
        z = self.z()
        # sunucu dolapları: aşama aşama yükselir
        n = 2 if t < z["tesis"] else 4 if t < z["toplam"] else 6
        sw, sh = ikon_boyut(I.SUNUCU, 2)
        for k in range(n):
            x = 104 + (k % 3) * (sw + 3)
            y = 140 if k < 3 else 140 + sh + 4
            ikon(d, I.SUNUCU, x, y, 2)
            for j in range(3):
                if yanip(t + k * 0.21 + j * 0.37, 0.6, 0.5):
                    d.rectangle([x + 6, y + (2 + 4 * j) * 2, x + 7, y + (2 + 4 * j) * 2 + 1], fill=P["mavi_buz"])
        # veri paketleri sunuculara akar
        if t >= z["saklar"]:
            for i in range(6):
                f = ((t - z["saklar"]) * 1.2 + i / 6) % 1.0
                px = int(4 + f * 96)
                py = 160 + (i % 3) * 14
                d.rectangle([px, py, px + 3, py + 3], fill=P["altin"] if i % 2 else P["mavi_acik"])
        # rakamlar
        if t >= z["tesis"]:
            yk.yaz("1. AŞAMA", R(4), R(138), ad="piksel_ince", boyut=31, renk="soluk")
            yk.yaz("450 MİLYON $", R(4), R(146), ad="piksel", boyut=55, bant="altin", kenar=4)
        if t >= z["mw"]:
            yk.yaz("22 MW TESİS", R(4), R(165), ad="piksel", boyut=47, renk="gumus", kenar=4)
        if t >= z["toplam"]:
            yk.yaz("TOPLAM", R(4), R(186), ad="piksel_ince", boyut=31, renk="soluk")
            yk.yaz("4,1 MİLYAR $", R(4), R(194), ad="piksel", boyut=55, bant="altin", kenar=4)
        if t >= z["ne"]:
            madde(d, yk, 4, 222, "VERİYİ GÜVENLE SAKLAR + İŞLER")
        if t >= z["hedef"]:
            yk.yaz("2030 HEDEFİ: EN AZ 1 GW", R(4), R(240) - 4, ad="piksel", boyut=39, renk="gumus")
            xp_bar(d, 4, 254, GEN - 8, adim(t - z["hedef"], 8) / 2.0, "altin")
        kaynak(yk, self.ctx["kaynak"])


# ------------------------------------------------------------------ Bölüm 2 · HABER: CHATGPT SLIDES
class HaberSlides(Sahne):
    def z(self):
        return {"sohbet": self.kt("sohbetten"), "dosya": self.kt("dosyalardan"), "taslak": self.kt("taslaktan"),
                "ekip": self.kt("Ekip"), "indir": self.kt("PowerPoint"), "plan": self.kt("Şimdilik"),
                "yani": self.kt("Yani")}

    def olaylar(self):
        z = self.z()
        o = [(z["sohbet"], "blip"), (z["dosya"], "blip"), (z["taslak"], "blip"), (z["ekip"], "tik"),
             (z["indir"], "coin"), (z["plan"], "tik")]
        for i in range(4):
            o.append((z["taslak"] + 0.6 + i * 0.25, "tik"))
        return o

    def ciz(self, t, d, yk):
        etiket(d, yk, "DÜNYA", "20 EKİM", ikon_sablon=I.KURE)
        baslik_kutusu(d, yk, ["CHATGPT SLIDES:", "YAPAY ZEKÂYLA SUNUM"])
        z = self.z()
        # sol: girdiler (sohbet, dosya, taslak)
        girdiler = [("sohbet", I.SOHBET, "SOHBET"), ("dosya", I.DOSYA, "DOSYA"), ("taslak", I.DOSYA, "TASLAK")]
        for i, (k, ik, ad) in enumerate(girdiler):
            if t >= z[k]:
                y = 140 + i * 24
                ikon(d, ik, 4, y, 2)
                yk.yaz(ad, R(26), R(y) + 12, ad="piksel_ince", boyut=31, renk="gumus")
                # ok -> sunum
                for k2 in range(5):
                    if (int(t * 8) + k2) % 5 != 0:
                        d.point((62 + k2 * 4, y + 8), fill=P["mavi_acik"])
        # sağ: sunum ekranı, slaytlar dizilir
        ex, ey, ew, eh = 92, 136, GEN - 96, 74
        panel(d, ex, ey, ew, eh)
        if t >= z["taslak"] + 0.5:
            adet = min(4, 1 + int((t - z["taslak"] - 0.5) / 0.25))
            for i in range(adet):
                sx, sy = ex + 6 + (i % 2) * 49, ey + 8 + (i // 2) * 32
                d.rectangle([sx, sy, sx + 45, sy + 27], fill=P["gumus"], outline=P["gumus_koyu"])
                d.rectangle([sx + 3, sy + 3, sx + 26, sy + 5], fill=P["mavi"])
                d.rectangle([sx + 3, sy + 9, sx + 38, sy + 9], fill=P["soluk"])
                d.rectangle([sx + 3, sy + 13, sx + 32, sy + 13], fill=P["soluk"])
                if i == 1:
                    for c, hh in enumerate([6, 10, 14]):
                        d.rectangle([sx + 30 + c * 4, sy + 24 - hh, sx + 32 + c * 4, sy + 24], fill=P["altin"])
        # ekip: iki imleç aynı sunumda
        if t >= z["ekip"]:
            for i, (dx, dy) in enumerate([(30, 30), (70, 50)]):
                sal = int((t * 2 + i) % 2) * 3
                ikon(d, I.IMLEC, ex + dx + sal, ey + dy - sal, 2,
                     renk_degis={"mavi_acik": "altin" if i else "mavi_acik"})
            yk.yaz("AYNI ANDA DÜZENLE", R(ex + ew // 2), R(ey + eh + 2), "orta", ad="piksel_ince", boyut=31,
                   renk="mavi_acik")
        # indirme biçimleri
        if t >= z["indir"]:
            for i, ad in enumerate(["PPTX", "PDF"]):
                dugme(d, 4 + i * 44, 218, 40, 14)
                yk.yaz(ad, R(24 + i * 44), R(218) + 10, "orta", ad="piksel", boyut=39, renk="beyaz")
        if t >= z["plan"]:
            d.rectangle([4, 238, GEN - 5, 262], fill=P["zemin2"], outline=P["altin_koyu"])
            yk.yaz("ŞİMDİLİK: PRO · BUSINESS · ENTERPRISE", R(CX), R(241), "orta", ad="piksel_ince", boyut=31,
                   renk="altin")
            yk.yaz("ÜCRETSİZ PLANDA YOK", R(CX), R(251), "orta", ad="piksel_ince", boyut=31, renk="soluk")
        kaynak(yk, self.ctx["kaynak"])


# ------------------------------------------------------------------ Bölüm 2 · HARİTAM: KONU ÖZETLERİ
class HaritamOzet(Sahne):
    KONULAR = [("MAT", "PROBLEMLER", "TYT"), ("TÜR", "PARAGRAF", "TYT"), ("FİZ", "KUVVET VE HAREKET", "TYT"),
               ("KİM", "MODERN ATOM TEORİSİ", "AYT"), ("BİY", "HÜCRE", "TYT")]

    def z(self):
        return {"bilgi": self.kt("Bilgi"), "yoran": self.kt("yoran"), "iste": self.kt("İşte"),
                "tyt": self.kt("TYT"), "eslesir": self.kt("eşleşiyor"), "bugun": self.kt("Bugün"),
                "ekstra": self.kt("Ekstra"), "cortex": self.kt("Cortex")}

    def olaylar(self):
        z = self.z()
        o = [(z["bilgi"], "boss"), (z["iste"], "glitch"), (z["iste"] + 0.1, "blip"), (z["eslesir"], "coin"),
             (z["bugun"], "tik"), (z["ekstra"], "blip"), (z["cortex"], "coin"), (self.sure - 1.6, "levelup")]
        for i in range(len(self.KONULAR)):
            o.append((z["tyt"] + i * 0.2, "tik"))
        return o

    def ciz(self, t, d, yk):
        z = self.z()
        if t < z["iste"]:
            self._yigin(d, yk, t, z)
        else:
            self._uygulama(d, yk, t, z)

    def _yigin(self, d, yk, t, z):
        # kitap yığını büyür: bilgi çok, zaman az
        kitaplar = [I.KITAP_1, I.KITAP_2, I.KITAP_3]
        adet = 2 if t < z["bilgi"] else min(9, 2 + int((t - z["bilgi"]) * 4))
        for i in range(adet):
            kay = (i * 7) % 9 - 4
            ikon(d, kitaplar[i % 3], CX - 22 + kay, 228 - i * 7, 4)
        if t >= z["bilgi"]:
            yk.yaz("BİLGİ ÇOK", RCX, R(110), "orta", ad="piksel", boyut=71, renk="gumus", kenar=6)
            yk.yaz("ZAMAN AZ", RCX, R(132), "orta", ad="piksel", boyut=71, renk="kirmizi", kenar=6)
        if t >= z["yoran"] and yanip(t, 0.5):
            yk.yaz("HANGİ KONU? NEREDEN?", RCX, R(160), "orta", ad="piksel", boyut=47, bant="altin", kenar=5)

    def _uygulama(self, d, yk, t, z):
        x0, y0, w = 0, 80, GEN
        panel(d, x0, y0, w, 206)
        dugme(d, x0 + 2, y0 + 2, w - 4, 20)
        yk.yaz("YKS HARİTAM", R(CX), R(y0 + 2) + 10, "orta", ad="piksel", boyut=47, renk="beyaz")
        yk.yaz("KONU ÖZETLERİ", R(x0 + 4), R(y0 + 25), ad="piksel", boyut=39, renk="altin")
        # TYT / AYT sekmeleri
        if t >= z["tyt"]:
            for i, ad in enumerate(["TYT", "AYT"]):
                sx = x0 + 128 + i * 34
                if (i == 0) == (int(t * 0.8) % 2 == 0):
                    dugme(d, sx, y0 + 23, 30, 12)
                else:
                    d.rectangle([sx, y0 + 23, sx + 29, y0 + 34], fill=P["zemin3"], outline=P["mavi_acik"])
                yk.yaz(ad, R(sx + 15), R(y0 + 23) + 6, "orta", ad="piksel", boyut=31, renk="beyaz")
        # konu kartları
        for i, (ders, konu, sinav) in enumerate(self.KONULAR):
            ti = z["tyt"] + i * 0.2
            if t < ti:
                continue
            y = y0 + 40 + i * 17
            secili = t >= z["bugun"] and i == 0
            d.rectangle([x0 + 4, y, x0 + w - 5, y + 14], fill=P["zemin3"],
                        outline=P["altin"] if secili else P["cizgi"])
            d.rectangle([x0 + 5, y + 1, x0 + 26, y + 13], fill=P["mavi"])
            yk.yaz(ders, R(x0 + 16), R(y) + 12, "orta", ad="piksel", boyut=31, renk="beyaz")
            yk.yaz(konu, R(x0 + 31), R(y) + 12, ad="piksel", boyut=31, renk="gumus")
            yk.yaz(sinav, R(x0 + w - 8), R(y) + 14, "sag", ad="piksel_ince", boyut=27, renk="soluk")
        # programla eşleşme
        if t >= z["eslesir"]:
            py = y0 + 128
            d.rectangle([x0 + 4, py, x0 + w - 5, py + 16], fill=P["zemin2"], outline=P["mavi"])
            yk.yaz("PROGRAM · BUGÜN: MAT", R(x0 + 8), R(py) + 14, ad="piksel", boyut=31, renk="mavi_acik")
            if t >= z["bugun"]:
                ikon(d, I.TIK, x0 + w - 18, py + 5, 1)
                yk.yaz("EŞLEŞTİ", R(x0 + w - 22), R(py) + 14, "sag", ad="piksel", boyut=31, renk="altin")
                # bağlantı çizgisi kart <-> program
                for yy in range(y0 + 55, py, 3):
                    d.point((x0 + w - 12, yy), fill=P["altin_koyu"])
        if t >= z["ekstra"]:
            ey = y0 + 150
            for i, ad in enumerate(["EKSTRA KAYNAK", "SAYFA SAYFA"]):
                ex = x0 + 4 + i * 98
                yk.yaz(ad, R(ex + 2), R(ey) + 4, ad="piksel_ince", boyut=31, renk="soluk")
                d.line([ex, ey + 6, ex + 88, ey + 6], fill=P["kirmizi"], width=1)
        if t >= z["cortex"]:
            cy = y0 + 166
            renk = P["altin"] if yanip(t, 0.6, 0.7) else P["altin_koyu"]
            d.rectangle([x0 + 4, cy, x0 + w - 5, cy + 26], fill=P["zemin2"], outline=renk)
            yk.yaz("CORTEX", R(CX), R(cy) + 10, "orta", ad="piksel", boyut=47, bant="altin")
            yk.yaz("YAPAY ZEKÂ · ÇOK YAKINDA", R(CX), R(cy) + 58, "orta", ad="piksel_ince", boyut=31, renk="gumus")
        if t >= self.sure - 1.6:
            yk.yaz("LEVEL UP!", RCX, R(y0 + 196), "orta", ad="ingilizce_etiket", boyut=40, bant="altin")


# ------------------------------------------------------------------ Bölüm 3 · HABER: BİR DAHA BAK
class HaberDolandirici(Sahne):
    MADDELER = [("adresine", "ADRESİ KONTROL ET"), ("Garanti", "GARANTİ KAZANÇ = TUZAK"),
                ("Şifreni", "ŞİFRE + KOD PAYLAŞMA"), ("adımlı", "2 ADIMLI DOĞRULAMA AÇ")]

    def z(self):
        return {"adi": self.kt("Adı"), "dort": self.kt("Dört"), "insta": self.kt("Instagram"),
                "peki": self.kt("Peki"), **{a: self.kt(a) for a, _ in self.MADDELER}}

    def olaylar(self):
        z = self.z()
        o = [(z["adi"], "coin"), (z["dort"], "tik"), (z["peki"], "boss")]
        o += [(z[a], "blip") for a, _ in self.MADDELER]
        o.append((z["adımlı"] + 0.6, "levelup"))
        return o

    def ciz(self, t, d, yk):
        z = self.z()
        etiket(d, yk, "TÜRKİYE", "BU HAFTA", rozet="TR")
        baslik_kutusu(d, yk, ["META + SİBERAY:", "BİR DAHA BAK!"])
        # sol: telefon, sahte mesaj
        px, py = 6, 138
        ikon(d, I.TELEFON, px, py, 8)
        d.rectangle([px + 9, py + 10, px + 46, py + 44], fill=P["beyaz"])
        yk.yaz("Tebrikler!", R(px + 28), R(py + 13), "orta", ad="marka", boyut=28, renk="mavi_koyu")
        yk.yaz("Kazandın", R(px + 28), R(py + 22), "orta", ad="metin", boyut=26, renk="mavi_koyu")
        if t < z["adresine"] or yanip(t, 0.6):
            yk.yaz("hediye.xyz", R(px + 28), R(py + 33), "orta", ad="metin", boyut=24, renk="kirmizi")
        if t >= z["adresine"]:
            # büyüteç: adres kontrol
            daire(d, px + 48, py + 30, 7, P["altin"])
            daire(d, px + 48, py + 30, 5, P["zemin"])
            d.line([px + 53, py + 35, px + 58, py + 40], fill=P["altin"], width=2)
        # sağ: kampanya bilgisi
        bx = 76
        if t >= z["adi"]:
            yk.yaz("KAMPANYA", R(bx), R(140), ad="piksel_ince", boyut=31, renk="soluk")
            yk.yaz("BİR DAHA BAK,", R(bx), R(148), ad="piksel", boyut=47, bant="altin", kenar=4)
            yk.yaz("GÜVENDE KAL", R(bx), R(161), ad="piksel", boyut=47, bant="altin", kenar=4)
        if t >= z["dort"]:
            dugme(d, bx, 178, 50, 14)
            yk.yaz("4 HAFTA", R(bx + 25), R(178) + 10, "orta", ad="piksel", boyut=39, renk="beyaz")
        if t >= z["insta"]:
            yk.yaz("INSTAGRAM", R(bx + 56), R(178) - 2, ad="piksel_ince", boyut=27, renk="gumus")
            yk.yaz("FACEBOOK", R(bx + 56), R(185) + 2, ad="piksel_ince", boyut=27, renk="gumus")
        # alt: kontrol listesi
        for i, (a, metin) in enumerate(self.MADDELER):
            if t < z[a]:
                continue
            y = 206 + i * 17
            d.rectangle([4, y, GEN - 5, y + 14], fill=P["zemin3"], outline=P["cizgi"])
            ikon(d, I.TIK, 8, y + 4, 1)
            yk.yaz(metin, R(18), R(y) + 12, ad="piksel", boyut=39, renk="gumus")
        kaynak(yk, self.ctx["kaynak"])


# ------------------------------------------------------------------ Bölüm 3 · HABER: SNAP SPECS
class HaberSpecs(Sahne):
    def z(self):
        return {"rdj": self.kt("Robert"), "fahri": self.kt("fahri"), "dijital": self.kt("dijital"),
                "sonbahar": self.kt("sonbaharda"), "fiyat": self.kt("fiyatı"), "ulke": self.kt("ABD"),
                "cuzdan": self.kt("cüzdanı")}

    def olaylar(self):
        z = self.z()
        return [(z["rdj"], "levelup"), (z["fahri"], "tik"), (z["dijital"], "glitch"), (z["dijital"] + 0.3, "blip"),
                (z["sonbahar"], "tik"), (z["fiyat"], "coin"), (z["fiyat"] + 0.25, "coin"), (z["ulke"], "blip"),
                (z["cuzdan"], "boss")]

    def _gozluk(self, d, x, y, s):
        # piksel AR gözlük: iki kalın çerçeve + köprü + saplar
        for k in (0, 1):
            gx = x + k * 13 * s
            d.rectangle([gx, y, gx + 11 * s - 1, y + 7 * s - 1], fill=P["cizgi"])
            d.rectangle([gx + s, y + s, gx + 10 * s - 1, y + 6 * s - 1], fill=P["mavi_koyu"])
            d.rectangle([gx + 2 * s, y + 2 * s, gx + 4 * s - 1, y + 3 * s - 1], fill=P["mavi_buz"])
        d.rectangle([x + 11 * s, y + 2 * s, x + 13 * s - 1, y + 3 * s - 1], fill=P["cizgi"])
        d.rectangle([x - 2 * s, y + s, x - 1, y + 2 * s - 1], fill=P["cizgi"])
        d.rectangle([x + 24 * s, y + s, x + 26 * s - 1, y + 2 * s - 1], fill=P["cizgi"])

    def ciz(self, t, d, yk):
        z = self.z()
        etiket(d, yk, "DÜNYA", "21 EKİM", ikon_sablon=I.KURE)
        baslik_kutusu(d, yk, ["SNAP SPECS:", "AR GÖZLÜK"])
        s = 3
        gx, gy = CX - 13 * s + s, 146
        # AR katmanları gözlüğün üstünde süzülür
        if t >= z["dijital"]:
            for i, (dx, dy, w, h, r) in enumerate([(-96, -4, 30, 18, "mavi_acik"), (66, -6, 30, 22, "altin"),
                                                    (-92, 20, 24, 12, "gumus")]):
                kay = int(adim(t, 4) * 2 + i) % 3 - 1
                x0, y0 = CX + dx, gy + dy + kay
                d.rectangle([x0, y0, x0 + w, y0 + h], outline=P[r])
                d.rectangle([x0 + 3, y0 + 3, x0 + w - 8, y0 + 4], fill=P[r])
                d.rectangle([x0 + 3, y0 + 8, x0 + w - 12, y0 + 8], fill=P["soluk"])
        self._gozluk(d, gx, gy, s)
        if t >= z["rdj"]:
            ikon(d, I.YILDIZ, 6, 184, 2)
            yk.yaz("ROBERT DOWNEY JR.", R(20), R(184) + 4, ad="piksel", boyut=47, bant="altin", kenar=4)
        if t >= z["fahri"]:
            yk.yaz("FAHRİ YÖNETİCİ · TANITIM", R(20), R(198) + 2, ad="piksel_ince", boyut=31, renk="gumus")
        if t >= z["sonbahar"]:
            yk.yaz("ÇIKIŞ: BU SONBAHAR", R(6), R(216), ad="piksel", boyut=39, renk="mavi_acik")
        if t >= z["fiyat"]:
            d.rectangle([4, 230, GEN - 5, 254], fill=P["zemin2"], outline=P["altin_koyu"])
            yk.yaz("2.195 $", R(CX), R(231), "orta", ad="piksel", boyut=95, bant="altin", kenar=5)
        if t >= z["ulke"]:
            yk.yaz("ABD · İNGİLTERE · FRANSA", R(CX), R(258), "orta", ad="piksel_ince", boyut=31, renk="gumus")
        if t >= z["cuzdan"]:
            # cüzdandan uçan paralar
            for i in range(5):
                f = ((t - z["cuzdan"]) * 1.5 + i / 5) % 1.0
                d.rectangle([GEN - 24 + i * 3, int(250 - f * 40), GEN - 22 + i * 3, int(252 - f * 40)], fill=P["altin"])
        kaynak(yk, self.ctx["kaynak"])


# ------------------------------------------------------------------ Bölüm 3 · HARİTAM: KENDİNİ TEST ET
class HaritamTest(Sahne):
    KARTLAR = [("TYT · BİYOLOJİ", "HÜCRE ZARININ GÖREVİ?"), ("TYT · MATEMATİK", "ÜSLÜ SAYILAR"),
               ("AYT · KİMYA", "MOL KAVRAMI"), ("TYT · TARİH", "İLK TÜRK DEVLETLERİ")]

    def z(self):
        return {"tuzak": self.kt("tuzak"), "konuyu": self.kt("Konuyu"), "yks": self.kt("YKS"),
                "kart": self.kt("Kartlarla"), "bildigin": self.kt("Bildiğin"), "bilme": self.kt("bilmediklerin"),
                "zaman": self.kt("zamanını"), "her": self.kt("Her")}

    def olaylar(self):
        z = self.z()
        return [(z["tuzak"], "boss"), (z["konuyu"], "tik"), (z["yks"], "glitch"), (z["yks"] + 0.1, "blip"),
                (z["kart"], "blip"), (z["bildigin"], "coin"), (z["bilme"], "tik"), (z["bilme"] + 0.4, "whoosh"),
                (z["zaman"], "coin"), (self.sure - 1.6, "levelup")]

    def ciz(self, t, d, yk):
        z = self.z()
        if t < z["yks"]:
            self._tuzak(d, yk, t, z)
        else:
            self._uygulama(d, yk, t, z)

    def _tuzak(self, d, yk, t, z):
        ikon(d, I.KITAP_1, CX - 22, 200, 4)
        ikon(d, I.KITAP_2, CX - 20, 188, 4)
        if t >= z["tuzak"]:
            yk.yaz("EN BÜYÜK TUZAK", RCX, R(110), "orta", ad="piksel", boyut=71, renk="kirmizi", kenar=6)
        if t >= z["konuyu"]:
            yk.yaz("OKUDUM = ANLADIM ?", RCX, R(140), "orta", ad="piksel", boyut=55, bant="altin", kenar=5)
            if yanip(t, 0.5):
                d.line([CX - 70, 150, CX + 70, 160], fill=P["kirmizi"], width=2)

    def _uygulama(self, d, yk, t, z):
        x0, y0, w = 0, 80, GEN
        panel(d, x0, y0, w, 206)
        dugme(d, x0 + 2, y0 + 2, w - 4, 20)
        yk.yaz("YKS HARİTAM", R(CX), R(y0 + 2) + 10, "orta", ad="piksel", boyut=47, renk="beyaz")
        yk.yaz("KENDİNİ TEST ET", R(x0 + 4), R(y0 + 25), ad="piksel", boyut=39, renk="altin")
        # hangi kart önde: bildiğin -> geçer, bilmediğin -> desteye geri döner
        if t < z["bildigin"]:
            on = 0
        elif t < z["bilme"]:
            on = 1
        else:
            on = 2
        # deste
        kx, ky, kw, kh = x0 + 14, y0 + 44, w - 28, 54
        for i in range(3, 0, -1):
            d.rectangle([kx + i * 3, ky - i * 3, kx + kw - 1 + i * 3, ky + kh - 1 - i * 3], fill=P["zemin3"],
                        outline=P["cizgi"])
        if t >= z["kart"]:
            ust_, soru = self.KARTLAR[on]
            # geçen kart sağa kayar
            kay = 0
            if on == 1 and t - z["bildigin"] < 0.4:
                kay = int((0.4 - (t - z["bildigin"])) * -300)
            d.rectangle([kx + kay, ky, kx + kay + kw - 1, ky + kh - 1], fill=P["gumus"], outline=P["gumus_koyu"])
            d.rectangle([kx + kay, ky, kx + kay + kw - 1, ky + 12], fill=P["mavi"])
            yk.yaz(ust_, R(kx + kay + 4), R(ky) + 12, ad="piksel_ince", boyut=27, renk="beyaz")
            yk.yaz(soru, R(kx + kay + kw // 2), R(ky + 27), "orta", ad="piksel", boyut=39, renk="mavi_koyu")
            # düğmeler
            by = ky + kh + 6
            dugme(d, kx, by, kw // 2 - 3, 16)
            yk.yaz("BİLİYORUM", R(kx + kw // 4), R(by) + 12, "orta", ad="piksel", boyut=31, renk="beyaz")
            d.rectangle([kx + kw // 2 + 3, by, kx + kw - 1, by + 15], fill=P["kirmizi"])
            yk.yaz("BİLMİYORUM", R(kx + kw * 3 // 4), R(by) + 12, "orta", ad="piksel", boyut=31, renk="beyaz")
            if z["bildigin"] <= t < z["bildigin"] + 0.8:
                d.rectangle([kx - 1, by - 1, kx + kw // 2 - 2, by + 16], outline=P["altin"])
            if z["bilme"] <= t < z["bilme"] + 0.8:
                d.rectangle([kx + kw // 2 + 2, by - 1, kx + kw, by + 16], outline=P["altin"])
        if t >= z["bilme"] + 0.4:
            yk.yaz("TEKRAR: DAHA SIK GELECEK", R(CX), R(y0 + 124), "orta", ad="piksel", boyut=31, renk="kirmizi")
        if t >= z["zaman"]:
            ty = y0 + 138
            yk.yaz("ZAMANIN NEREYE GİDİYOR?", R(x0 + 6), R(ty), ad="piksel_ince", boyut=27, renk="soluk")
            yk.yaz("BİLDİKLERİN", R(x0 + 6), R(ty + 11), ad="piksel", boyut=31, renk="gumus")
            xp_bar(d, x0 + 70, ty + 14, 40, 0.5, "mavi")
            yk.yaz("EKSİKLERİN", R(x0 + 6), R(ty + 23), ad="piksel", boyut=31, renk="altin")
            xp_bar(d, x0 + 70, ty + 26, w - 80, min(1.0, adim(t - z["zaman"], 8) / 1.2), "altin")
        if t >= z["her"]:
            yk.yaz("HER GÜN BİRKAÇ DAKİKA", RCX, R(y0 + 177), "orta", ad="piksel", boyut=39, renk="mavi_acik")
        if t >= self.sure - 1.6:
            yk.yaz("LEVEL UP!", RCX, R(y0 + 194), "orta", ad="ingilizce_etiket", boyut=40, bant="altin")


SAHNELER = {"kanca": Kanca, "acilis": Acilis, "haber_meb": HaberMEB, "haber_jaxa": HaberJAXA,
            "haritam": Haritam, "cta": Kapanis,
            "haber_veri": HaberVeri, "haber_slides": HaberSlides, "haritam_ozet": HaritamOzet,
            "haber_dolandirici": HaberDolandirici, "haber_specs": HaberSpecs, "haritam_test": HaritamTest}
