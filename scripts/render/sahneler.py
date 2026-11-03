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

    def maskot_yol(self):
        """Arpi'nin yolu: [(t, x, ayak_y, mod)], yerel koordinat. mod: isaret/sevin/saskin/dusun/selam/levelup;
        '!' ile biten mod kalıcıdır. Varsayılan: sol kenarda başlığı gösterir, sonra alt köşede dinlenir."""
        return [(0.0, *M(113), "isaret"), (2.5, *DINLEN, None)]

    def ciz(self, t, d, yk):
        raise NotImplementedError


# ------------------------------------------------------------------ Arpi (maskot) konumları
MX = -17                           # sol kenar boşluğu (yerel x; içerik alanının solu)
DINLEN = (MX, 371)                 # alt bilgi çizgisi üstünde dinlenme yeri


def M(hedef_y):
    """Sol kenardan hedef_y yüksekliğindeki öğeyi göstermek için ayak noktası."""
    return MX, hedef_y + 26


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


def kod_penceresi(d, yk, x, y, w, h, t, catlak=False):
    """<?php kod penceresi; catlak=True iken kırmızı çatlak + uyarı."""
    panel(d, x, y, w, h)
    for i, r in enumerate(["kirmizi", "altin", "mavi_acik"]):
        d.rectangle([x + 3 + i * 5, y + 1, x + 5 + i * 5, y + 3], fill=P[r])
    yk.yaz("<?php", R(x + 4), R(y + 6), ad="piksel", boyut=39, renk="mavi_acik")
    for i in range(5):
        yy = y + 20 + i * 8
        if yy > y + h - 6:
            break
        girinti = (i % 3) * 6
        d.rectangle([x + 6 + girinti, yy, x + 6 + girinti + 18 + (i * 13) % 40, yy + 2],
                    fill=P["altin"] if i == 2 else P["gumus_koyu"])
    if catlak:
        pts = [(x + w // 2 + 4, y), (x + w // 2 - 6, y + h // 3), (x + w // 2 + 6, y + h // 2),
               (x + w // 2 - 4, y + h * 3 // 4), (x + w // 2 + 2, y + h - 1)]
        d.line(pts, fill=P["kirmizi"], width=2)


# ------------------------------------------------------------------ 0. KANCA
class Kanca(Sahne):
    """Kanca: ikon + 3 satır başlık (senaryo.json -> "kanca"). Ortadaki satır altın bantlı."""
    def maskot_yol(self):
        ikon = (self.ctx.get("kanca") or {}).get("ikon")
        x = 22 if ikon == "php" else 42 if ikon in ("uyari", "robot", "takvim", "uyku") else 30
        return [(0.0, x, 164, "dusun!"), (1.2, x, 164, "isaret"), (2.8, *DINLEN, None)]


    VARSAYILAN = {"ikon": "kagit", "satirlar": ["YAZILI SORULARINI", "YAPAY ZEKÂ", "MI HAZIRLAYACAK?"], "vurgu": 1}

    def olaylar(self):
        return [(0.0, "blip"), (0.4, "blip"), (0.8, "blip")]

    def ciz(self, t, d, yk):
        k = self.ctx.get("kanca") or self.VARSAYILAN
        if k.get("ikon") == "sunucu":
            self._sunucu(d, yk, t)
        elif k.get("ikon") == "uyari":
            self._uyari(d, yk, t)
        elif k.get("ikon") == "php":
            kod_penceresi(d, yk, CX - 50, 92, 100, 70, t, catlak=yanip(t, 0.5))
        elif k.get("ikon") == "robot":
            self._robot(d, yk, t)
        elif k.get("ikon") == "ay":
            self._ay(d, yk, t)
        elif k.get("ikon") == "bina":
            bina_ciz(d, yk, CX, 168, t)
        elif k.get("ikon") == "uyku":
            uyuyan_robot(d, yk, CX - 30, 98, 5, t, uyku=True)
        elif k.get("ikon") == "takvim":
            takvim_ciz(d, yk, CX - 36, 96, 72, 66, "19" if yanip(t, 1.0) else "20", "HAZİRAN", "YKS 2027", parla=True)
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

    def _robot(self, d, yk, t):
        # robot + etrafında düşen altın paralar
        ikon(d, I.ROBOT, CX - 30, 98, 5)
        for i in range(6):
            f = (t * 0.9 + i / 6) % 1.0
            x = CX - 60 + (i * 23) % 120
            if abs(x - CX) < 34:
                x += 70 if x >= CX else -70
            y = int(88 + f * 80)
            d.rectangle([x, y, x + 4, y + 4], fill=P["altin"], outline=P["altin_koyu"])

    def _ay(self, d, yk, t):
        # Ay + etrafında dönen roket ve arkada yerli harita rotası
        ay_ciz(d, CX + 22, 128, 26)
        a = math.radians(adim(t, 10) * 140 + 200)
        rx, ry = CX + 22 + int(math.cos(a) * 44), 128 + int(math.sin(a) * 30)
        for k in range(1, 6):
            b = a - k * 0.18
            d.point((CX + 22 + int(math.cos(b) * 44), 128 + int(math.sin(b) * 30)), fill=P["cizgi"])
        ikon(d, I.ROKET, rx - 5, ry - 8, 1)
        if t >= 0.3:
            konum_pimi(d, CX - 30, 150, yanip(t, 0.5))

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
    def maskot_yol(self):
        return [(0.0, *DINLEN, None), (self.LOGO_T + 1.6, MX, 252, "selam!")]

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
            ozel = self.ctx.get("ozel")
            yk.yaz("ÖZEL BÖLÜM" if ozel else f"BÖLÜM {bolum}", RCX, R(220), "orta", ad="marka", boyut=96 if ozel else 120,
                   bant="altin")
            d.rectangle([CX - 50, 250, CX + 50, 250], fill=P["cizgi"])
        sponsor = self.ctx.get("sponsor")
        if sponsor and t >= self.LOGO_T + 2.4:
            yk.yaz("SPONSOR", RCX, R(256), "orta", ad="piksel_ince", boyut=31, renk="soluk")
            yk.yaz(ust(sponsor), RCX, R(265), "orta", ad="piksel", boyut=55, bant="altin", kenar=4)


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
    def maskot_yol(self):
        son = self.ctx["ses_son"] + 0.2
        return [(0.0, *M(129), "isaret"), (self.kt("ücretsiz"), *M(173), "isaret"),
                (self.kt("telefon", varsayilan=1.5), *M(203), "isaret"), (self.kt("takip"), *M(230), "isaret"),
                (son, MX, 262, "selam!")]

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
                "yani": self.kt("Yani", 1)}

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
    def maskot_yol(self):
        z = self.z()
        return [(0.0, *M(113), "sevin"), (z["adi"], *M(152), "isaret"), (z["dort"], *M(185), "isaret"),
                (z["adresine"], *M(213), "isaret"), (z["Garanti"], *M(230), "isaret"),
                (z["Şifreni"], *M(247), "isaret"), (z["adımlı"], *M(264), "isaret"),
                (z["adımlı"] + 1.4, *DINLEN, "sevin")]

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
    def maskot_yol(self):
        z = self.z()
        return [(0.0, *M(113), "sevin"), (z["dijital"], *M(150), "isaret"), (z["rdj"], *M(190), "isaret"),
                (z["sonbahar"], *M(220), "isaret"), (z["fiyat"], *M(242), "saskin"), (z["ulke"], *M(262), "isaret"),
                (z["cuzdan"] + 1.5, *DINLEN, None)]

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
    def maskot_yol(self):
        z = self.z()
        return [(0.0, *M(120), "dusun"), (z["tuzak"], *M(110), "saskin"), (z["konuyu"], *M(145), "dusun"),
                (z["yks"], *M(100), "sevin"), (z["kart"], *M(150), "isaret"), (z["bildigin"], *M(182), "isaret"),
                (z["bilme"], *M(205), "isaret"), (z["zaman"], *M(242), "isaret"), (z["her"], *M(258), "isaret"),
                (self.sure - 1.6, *DINLEN, "levelup!")]

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


# ------------------------------------------------------------------ Özel bölüm · PHP: NE OLDU
class PhpNe(Sahne):
    def maskot_yol(self):
        z = self.z()
        return [(0.0, *M(113), "saskin"), (z["yama"], *M(148), "isaret"), (z["puan"], *M(175), "saskin"),
                (z["giris"], *M(209), "isaret"), (z["hol"], *M(233), "isaret"), (z["tr"], *M(251), "isaret"),
                (z["tr"] + 2.5, *DINLEN, None)]

    def z(self):
        return {"yama": self.kt("acil"), "puan": self.kt("9,2"), "giris": self.kt("giriş"),
                "hol": self.kt("Hollanda"), "tr": self.kt("Türkiye'de")}

    def olaylar(self):
        z = self.z()
        return [(z["yama"], "blip"), (z["puan"], "boss"), (z["giris"], "glitch"), (z["hol"], "tik"),
                (z["tr"], "tik")]

    def ciz(self, t, d, yk):
        z = self.z()
        etiket(d, yk, "DÜNYA + TR", "21 EKİM", ikon_sablon=I.KURE)
        baslik_kutusu(d, yk, ["PHP2SHELL:", "2 KRİTİK AÇIK"])
        kod_penceresi(d, yk, 4, 138, 92, 62, t, catlak=t >= z["giris"])
        if t >= z["yama"]:
            dugme(d, 104, 140, GEN - 108, 16)
            yk.yaz("ACİL YAMA", R(104 + (GEN - 108) // 2), R(140) + 12, "orta", ad="piksel", boyut=39, renk="beyaz")
        if t >= z["puan"]:
            yk.yaz("TEHLİKE", R(104), R(160), ad="piksel_ince", boyut=31, renk="soluk")
            yk.yaz("9,2/10", R(104), R(168), ad="piksel", boyut=71, renk="kirmizi", kenar=5)
            oran = min(0.92, adim(t - z["puan"], 8) / 1.0)
            d.rectangle([104, 190, GEN - 5, 195], fill=P["zemin2"], outline=P["cizgi"])
            d.rectangle([105, 191, 105 + int((GEN - 111) * oran), 194], fill=P["kirmizi"])
        if t >= z["giris"]:
            if yanip(t, 0.6, 0.8):
                yk.yaz("GİRİŞ YAPMADAN KOD ÇALIŞTIRMA", R(CX), R(205), "orta", ad="piksel", boyut=39, bant="altin",
                       kenar=4)
        for i, (k, metin) in enumerate([("hol", "HOLLANDA: BAZI SİTELER KAPANDI"),
                                         ("tr", "TR: SİBER GÜVENLİK BAŞKANLIĞI UYARDI")]):
            if t >= z[k]:
                y = 226 + i * 18
                d.rectangle([4, y, GEN - 5, y + 14], fill=P["zemin3"], outline=P["cizgi"])
                if k == "tr":
                    d.rectangle([5, y + 1, 18, y + 13], fill=P["kirmizi"])
                    yk.yaz("TR", R(12), R(y) + 12, "orta", ad="piksel", boyut=31, renk="beyaz")
                else:
                    ikon(d, I.KURE, 7, y + 3, 1)
                yk.yaz(metin.split(": ", 1)[1], R(22), R(y) + 12, ad="piksel", boyut=31, renk="gumus")
        kaynak(yk, self.ctx["kaynak"])


# ------------------------------------------------------------------ Özel bölüm · PHP: NEDEN
class PhpNeden(Sahne):
    def maskot_yol(self):
        z = self.z()
        return [(0.0, *M(113), "dusun"), (z["on"], *M(160), "isaret"), (z["bekle"], *M(192), "dusun"),
                (z["ai"], *M(222), "isaret"), (z["yani"], *M(264), "saskin"), (z["yani"] + 3.0, *DINLEN, None)]

    def z(self):
        return {"on": self.kt("Hatalı"), "y24": self.kt("2024"), "bekle": self.kt("aylarca"),
                "ai": self.kt("Wiz"), "yani": self.kt("Yani", 1)}

    def olaylar(self):
        z = self.z()
        return [(z["on"], "tik"), (z["y24"], "tik"), (z["bekle"], "boss"), (z["ai"], "levelup"), (z["yani"], "glitch")]

    def ciz(self, t, d, yk):
        z = self.z()
        etiket(d, yk, "NEDEN?", "21 EKİM")
        baslik_kutusu(d, yk, ["ON YILLIK HATA,", "AYLARCA BEKLEYEN YAMA"])
        # zaman çizelgesi
        x0, x1, y = 14, GEN - 14, 160
        d.rectangle([x0, y, x1, y + 1], fill=P["cizgi"])
        duraklar = [("on", 0.0, "10+ YIL", "HATA KODDA"), ("y24", 0.5, "2024", "İLK İŞARET"),
                    ("ai", 1.0, "2026", "YAMA")]
        son_x = x0
        for k, f, ust_, alt in duraklar:
            if t < z[k]:
                continue
            x = int(x0 + (x1 - x0) * f)
            d.rectangle([son_x, y, x, y + 1], fill=P["altin"])
            son_x = x
            d.rectangle([x - 3, y - 3, x + 3, y + 4], fill=P["altin"], outline=P["altin_koyu"])
            hiza = "orta" if 0 < f < 1 else ("sol" if f == 0 else "sag")
            xr = R(x) if hiza == "orta" else R(x - 4) if hiza == "sol" else R(x + 4)
            yk.yaz(ust_, xr, R(y - 18), hiza, ad="piksel", boyut=39, bant="altin", kenar=3)
            yk.yaz(alt, xr, R(y + 7), hiza, ad="piksel_ince", boyut=27, renk="gumus")
        if t >= z["bekle"]:
            # bekleyen yama: kum saati gibi yanıp sönen noktalar
            for i in range(3):
                if int(t * 3) % 3 >= i:
                    d.rectangle([CX - 8 + i * 6, 186, CX - 5 + i * 6, 189], fill=P["kirmizi"])
            yk.yaz("KÜÇÜK EKİP · AYLARCA BEKLEDİ", R(CX), R(192), "orta", ad="piksel", boyut=31, renk="kirmizi")
        if t >= z["ai"]:
            ikon(d, I.ROBOT, 8, 214, 3)
            yk.yaz("WIZ + OPENAI", R(56), R(214), ad="piksel", boyut=47, bant="altin", kenar=4)
            yk.yaz("YAPAY ZEKÂYLA AÇIĞI GÖSTERDİ", R(56), R(229), ad="piksel_ince", boyut=27, renk="gumus")
        if t >= z["yani"]:
            d.rectangle([4, 254, GEN - 5, 274], fill=P["zemin2"], outline=P["kirmizi"])
            yk.yaz("AYNI GÜÇ SALDIRGANDA DA VAR", R(CX), R(257), "orta", ad="piksel", boyut=39, renk="beyaz")
        kaynak(yk, self.ctx["kaynak"])


# ------------------------------------------------------------------ Özel bölüm · PHP: NE YAPMALI
class PhpYapilacak(Sahne):
    def maskot_yol(self):
        z = self.z()
        return [(0.0, *M(113), "dusun"), (z["sunucu"], *M(155), "isaret"), (z["sifre"], *M(211), "isaret"),
                (z["iki"], *M(229), "isaret"), (z["gelis"], *M(113), "sevin"), (z["s0"], *M(156), "isaret"),
                (z["s0"] + 1.4, *M(176), "isaret"), (z["yeniden"], *M(203), "isaret"),
                (z["eski"], *M(221), "saskin"), (z["kayit"], *M(239), "isaret"), (z["kayit"] + 2.5, *DINLEN, None)]

    SURUMLER = ["8.5.12", "8.4.27", "8.3.36", "8.2.35"]

    def z(self):
        return {"sunucu": self.kt("sitelerin"), "sifre": self.kt("farklı"), "iki": self.kt("iki"),
                "gelis": self.kt("Geliştiriciysen"), "s0": self.kt("8.5.12"), "yeniden": self.kt("yeniden"),
                "eski": self.kt("8.1"), "kayit": self.kt("Kayıtlarda")}

    def olaylar(self):
        z = self.z()
        o = [(z["sunucu"], "tik"), (z["sifre"], "blip"), (z["iki"], "blip"), (z["gelis"], "glitch"),
             (z["yeniden"], "tik"), (z["eski"], "boss"), (z["kayit"], "blip")]
        o += [(z["s0"] + i * 0.6, "coin") for i in range(4)]
        return o

    def ciz(self, t, d, yk):
        z = self.z()
        gelis = t >= z["gelis"]
        etiket(d, yk, "GELİŞTİRİCİ" if gelis else "KULLANICI", "NE YAPMALI?")
        baslik_kutusu(d, yk, ["GELİŞTİRİCİYSEN:", "HEMEN GÜNCELLE"] if gelis else ["VERİLERİN", "GÜVENDE Mİ?"])
        if not gelis:
            ikon(d, I.TELEFON, 14, 140, 4)
            ikon(d, I.TIK, 22, 186, 2)
            if t >= z["sunucu"]:
                ikon(d, I.SUNUCU, 150, 138, 3)
                if yanip(t, 0.5):
                    d.rectangle([182, 134, 192, 144], fill=P["kirmizi"])
                yk.yaz("SORUN SUNUCUDA", R(CX), R(150), "orta", ad="piksel", boyut=39, renk="gumus")
                yk.yaz("SİTELER YAMALANIYOR", R(CX), R(164), "orta", ad="piksel_ince", boyut=27, renk="soluk")
            for i, (k, metin) in enumerate([("sifre", "FARKLI ŞİFRELER KULLAN"), ("iki", "2 ADIMLI DOĞRULAMA AÇ")]):
                if t >= z[k]:
                    y = 204 + i * 18
                    d.rectangle([4, y, GEN - 5, y + 14], fill=P["zemin3"], outline=P["cizgi"])
                    ikon(d, I.TIK, 8, y + 4, 1)
                    yk.yaz(metin, R(18), R(y) + 12, ad="piksel", boyut=39, renk="gumus")
        else:
            yk.yaz("GÜVENLİ SÜRÜMLER", R(6), R(138), ad="piksel_ince", boyut=31, renk="soluk")
            for i, s in enumerate(self.SURUMLER):
                if t < z["s0"] + i * 0.6:
                    continue
                x, y = 4 + (i % 2) * 98, 148 + (i // 2) * 20
                dugme(d, x, y, 94, 16)
                yk.yaz("PHP " + s, R(x + 47), R(y) + 12, "orta", ad="piksel", boyut=39, renk="beyaz")
            satirlar = [("yeniden", "SUNUCUYU YENİDEN BAŞLAT", "gumus"), ("eski", "8.1 VE ÖNCESİ: YAMA YOK", "kirmizi"),
                        ("kayit", "KAYITLARI KONTROL ET", "gumus")]
            for i, (k, metin, r) in enumerate(satirlar):
                if t >= z[k]:
                    y = 196 + i * 18
                    d.rectangle([4, y, GEN - 5, y + 14], fill=P["zemin3"], outline=P["kirmizi"] if r == "kirmizi" else P["cizgi"])
                    ikon(d, I.MADDE, 8, y + 4, 1)
                    yk.yaz(metin, R(16), R(y) + 12, ad="piksel", boyut=39, renk=r)
        kaynak(yk, self.ctx["kaynak"])


# ------------------------------------------------------------------ HARİTAM: DENEME TAKİBİ
class HaritamDeneme(Sahne):
    def maskot_yol(self):
        z = self.z()
        return [(0.0, *M(150), "dusun"), (z["yks"], *M(100), "sevin"), (z["grafik"], *M(160), "isaret"),
                (z["puan"], *M(200), "isaret"), (z["hedef"], *M(236), "isaret"), (self.sure - 1.6, *DINLEN, "levelup!")]

    NETLER = [52, 58, 61, 67, 71, 78]

    def z(self):
        return {"sinav": self.kt("Sınavda"), "yks": self.kt("YKS"), "grafik": self.kt("grafikle"),
                "puan": self.kt("puanını"), "hedef": self.kt("hedefine")}

    def olaylar(self):
        z = self.z()
        o = [(z["yks"], "glitch"), (z["yks"] + 0.1, "blip"), (z["puan"], "coin"), (z["hedef"], "tik"),
             (self.sure - 1.6, "levelup")]
        o += [(z["grafik"] + i * 0.15, "tik") for i in range(len(self.NETLER))]
        return o

    def ciz(self, t, d, yk):
        z = self.z()
        if t < z["yks"]:
            # radar: açığı bul
            r = int((t * 30) % 40)
            d.ellipse([CX - r, 170 - r, CX + r, 170 + r], outline=P["mavi_acik"])
            daire(d, CX + 18, 160, 3, P["kirmizi"] if yanip(t, 0.4) else P["altin"])
            yk.yaz("ÖNCE NEREDE OLDUĞUNU BİL", RCX, R(110), "orta", ad="piksel", boyut=47, bant="altin", kenar=5)
            if t >= z["sinav"]:
                yk.yaz("SINAVDA DA ÖYLE", RCX, R(222), "orta", ad="piksel", boyut=55, renk="beyaz", kenar=5)
            return
        x0, y0, w = 0, 80, GEN
        panel(d, x0, y0, w, 206)
        dugme(d, x0 + 2, y0 + 2, w - 4, 20)
        yk.yaz("YKS HARİTAM", R(CX), R(y0 + 2) + 10, "orta", ad="piksel", boyut=47, renk="beyaz")
        yk.yaz("DENEME TAKİBİ", R(x0 + 4), R(y0 + 25), ad="piksel", boyut=39, renk="altin")
        # net grafiği
        gx, gy, gw, gh = x0 + 10, y0 + 42, w - 20, 70
        d.rectangle([gx, gy, gx + gw, gy + gh], fill=P["zemin"], outline=P["cizgi"])
        if t >= z["grafik"]:
            n = min(len(self.NETLER), 1 + int((t - z["grafik"]) / 0.15))
            onceki = None
            for i in range(n):
                px = gx + 8 + i * (gw - 16) // (len(self.NETLER) - 1)
                py = gy + gh - 6 - int((self.NETLER[i] - 45) / 40 * (gh - 12))
                if onceki:
                    d.line([onceki, (px, py)], fill=P["altin"], width=1)
                d.rectangle([px - 1, py - 1, px + 1, py + 1], fill=P["mavi_buz"])
                onceki = (px, py)
            yk.yaz(f"TYT NET: {self.NETLER[n - 1]}", R(gx + 4), R(gy + 3), ad="piksel_ince", boyut=27, renk="gumus")
        if t >= z["puan"]:
            yk.yaz("PUAN TAHMİNİ", R(x0 + 6), R(y0 + 120), ad="piksel_ince", boyut=31, renk="soluk")
            yk.yaz("~ 410", R(x0 + w - 8), R(y0 + 117), "sag", ad="piksel", boyut=55, bant="altin", kenar=4)
        if t >= z["hedef"]:
            yk.yaz("HEDEFE KALAN", R(x0 + 6), R(y0 + 142), ad="piksel_ince", boyut=31, renk="soluk")
            xp_bar(d, x0 + 6, y0 + 156, w - 12, min(0.78, adim(t - z["hedef"], 8) / 1.0), "altin")
            yk.yaz("%78", R(x0 + w - 8), R(y0 + 162), "sag", ad="piksel", boyut=39, renk="altin")
        if t >= self.sure - 1.6:
            yk.yaz("LEVEL UP!", RCX, R(y0 + 192), "orta", ad="ingilizce_etiket", boyut=40, bant="altin")


# ------------------------------------------------------------------ Bölüm 5 · HABER: GEMINI PROMPT ARENA
class HaberPrompt(Sahne):
    def maskot_yol(self):
        z = self.z()
        return [(0.0, *M(113), "sevin"), (z["milyon"], *M(150), "saskin"), (z["gorsel"], *M(186), "isaret"),
                (z["yazilim"], *M(208), "isaret"), (z["on8"], *M(226), "isaret"), (z["on5"], *M(244), "isaret"),
                (z["juri"], *M(142), "isaret"), (z["online"], *M(178), "isaret"), (z["yani"], *M(236), "sevin"),
                (z["yani"] + 2.0, *DINLEN, None)]

    KATEGORILER = [("gorsel", "GÖRSEL"), ("video", "VİDEO"), ("muzik", "MÜZİK"), ("kod", "KOD")]

    def z(self):
        return {"milyon": self.kt("milyon"), "gorsel": self.kt("görsel"), "video": self.kt("video"),
                "muzik": self.kt("müzik"), "kod": self.kt("kod", tam=True), "yazilim": self.kt("Yazılım"),
                "on8": self.kt("18"), "on5": self.kt("15"), "juri": self.kt("Jüride"), "online": self.kt("online"),
                "yari": self.kt("yarı"), "final": self.kt("final", 1), "yani": self.kt("Yani", 1)}

    def olaylar(self):
        z = self.z()
        o = [(z["milyon"], "coin"), (z["milyon"] + 0.2, "coin"), (z["milyon"] + 0.4, "levelup"),
             (z["yazilim"], "blip"), (z["on8"], "tik"), (z["on5"], "boss"), (z["juri"], "whoosh"),
             (z["online"], "tik"), (z["yari"], "tik"), (z["final"], "tik"), (z["yani"], "levelup")]
        o += [(z[a], "blip") for a, _ in self.KATEGORILER]
        return o

    def ciz(self, t, d, yk):
        z = self.z()
        etiket(d, yk, "TÜRKİYE", "20 EKİM", rozet="TR")
        baslik_kutusu(d, yk, ["GOOGLE'DAN", "GEMİNİ PROMPT ARENA"])
        if t < z["juri"]:
            self._odul(d, yk, t, z)
        else:
            self._yol(d, yk, t, z)
        kaynak(yk, self.ctx["kaynak"])

    def _odul(self, d, yk, t, z):
        ikon(d, I.ROBOT, 6, 140, 3)
        if t >= z["milyon"]:
            yk.yaz("BÜYÜK ÖDÜL", R(50), R(140), ad="piksel_ince", boyut=31, renk="soluk")
            yk.yaz("1 MİLYON TL", R(50), R(148), ad="piksel", boyut=71, bant="altin", kenar=5)
            for i in range(4):
                f = ((t - z["milyon"]) * 1.2 + i / 4) % 1.0
                d.rectangle([GEN - 14 + (i % 2) * 6, int(176 - f * 30), GEN - 11 + (i % 2) * 6, int(179 - f * 30)],
                            fill=P["altin"])
        w = (GEN - 8 - 9) // 4
        for i, (a, metin) in enumerate(self.KATEGORILER):
            if t < z[a]:
                continue
            x = 4 + i * (w + 3)
            dugme(d, x, 184, w, 15)
            yk.yaz(metin, R(x + w // 2), R(184) + 12, "orta", ad="piksel", boyut=31, renk="beyaz")
        satirlar = [("yazilim", "YAZILIM BİLMEK ŞART DEĞİL", "gumus"),
                    ("on8", "18+ · ÜNİVERSİTE ÖĞRENCİLERİ", "gumus"),
                    ("on5", "SON BAŞVURU: 15 KASIM", "altin")]
        for i, (k, metin, r) in enumerate(satirlar):
            if t < z[k]:
                continue
            y = 206 + i * 18
            vurgu = r == "altin"
            d.rectangle([4, y, GEN - 5, y + 14], fill=P["zemin3"],
                        outline=P["altin"] if vurgu and yanip(t, 0.6) else P["cizgi"])
            ikon(d, I.TIK if not vurgu else I.MADDE, 8, y + 4, 1)
            yk.yaz(metin, R(18), R(y) + 12, ad="piksel", boyut=39, renk=r)

    def _yol(self, d, yk, t, z):
        yk.yaz("JÜRİDE", R(6), R(138), ad="piksel_ince", boyut=31, renk="soluk")
        ikon(d, I.YILDIZ, 6, 148, 2)
        yk.yaz("OZAN SİHAY", R(24), R(146), ad="piksel", boyut=47, bant="altin", kenar=4)
        yk.yaz("ORKUN IŞITMAK", R(24), R(162), ad="piksel", boyut=47, bant="altin", kenar=4)
        # aşamalar: online -> yarı final -> final (İstanbul)
        asamalar = [("online", "ONLINE", "EVDEN"), ("yari", "YARI FİNAL", "İSTANBUL"), ("final", "FİNAL", "İSTANBUL")]
        w = 58
        for i, (k, ust_, alt) in enumerate(asamalar):
            if t < z[k]:
                continue
            x = 4 + i * (w + 9)
            if i:
                ikon(d, I.UCGEN_SAG, x - 7, 190, 1)
            renk = "altin" if i == 2 else "mavi"
            dugme(d, x, 182, w, 18, renk=renk) if renk == "mavi" else d.rectangle([x, 182, x + w - 1, 199],
                                                                                  fill=P["altin_koyu"], outline=P["altin"])
            yk.yaz(ust_, R(x + w // 2), R(182) + 14, "orta", ad="piksel", boyut=31, renk="beyaz")
            yk.yaz(alt, R(x + w // 2), R(204), "orta", ad="piksel_ince", boyut=27, renk="gumus")
        if t >= z["yani"]:
            d.rectangle([4, 232, GEN - 5, 256], fill=P["zemin2"], outline=P["altin"])
            yk.yaz("İYİ SORU SORMAK", R(CX), R(234), "orta", ad="piksel", boyut=39, renk="beyaz")
            yk.yaz("= YETENEK", R(CX), R(244), "orta", ad="piksel", boyut=39, bant="altin", kenar=3)


# ------------------------------------------------------------------ Bölüm 5 · HABER: NASA SWIFT
class HaberSwift(Sahne):
    def maskot_yol(self):
        z = self.z()
        return [(0.0, *M(113), "saskin"), (z["y2004"], *M(178), "isaret"), (z["y22"], *M(190), "sevin"),
                (z["gama"], *M(206), "isaret"), (z["sn"], *M(222), "isaret"), (z["makale"], *M(238), "isaret"),
                (z["gunes"], *M(206), "dusun"), (z["onum"], *M(238), "saskin"), (z["ama"], *M(256), "sevin"),
                (z["ama"] + 2.5, *DINLEN, None)]

    def z(self):
        return {"bitirdi": self.kt("bitirdi"), "y2004": self.kt("2004"), "y22": self.kt("22"),
                "gama": self.kt("2000"), "sn": self.kt("1400"), "makale": self.kt("7000"),
                "gunes": self.kt("Güneş"), "alcal": self.kt("alçaldı"), "onum": self.kt("Önümüzdeki"),
                "ama": self.kt("Ama", tam=True)}

    def olaylar(self):
        z = self.z()
        return [(z["bitirdi"], "tik"), (z["y2004"], "blip"), (z["y22"], "levelup"), (z["gama"], "coin"),
                (z["sn"], "coin"), (z["makale"], "coin"), (z["gunes"], "glitch"), (z["alcal"], "whoosh"),
                (z["onum"], "boss"), (z["ama"], "levelup")]

    def _uydu(self, d, x, y):
        # piksel uzay teleskobu: gövde + iki güneş paneli + ön kapak
        d.rectangle([x - 18, y - 4, x - 7, y + 4], fill=P["mavi_koyu"], outline=P["mavi_acik"])
        d.rectangle([x + 7, y - 4, x + 18, y + 4], fill=P["mavi_koyu"], outline=P["mavi_acik"])
        for k in (-15, -11, 10, 14):
            d.line([x + k, y - 3, x + k, y + 3], fill=P["mavi"])
        d.rectangle([x - 6, y - 7, x + 6, y + 7], fill=P["gumus"], outline=P["gumus_koyu"])
        d.rectangle([x - 4, y - 10, x + 4, y - 7], fill=P["altin"])
        d.rectangle([x - 2, y - 2, x + 2, y + 2], fill=P["cizgi"])

    def ciz(self, t, d, yk):
        z = self.z()
        etiket(d, yk, "DÜNYA", "23 EKİM", ikon_sablon=I.KURE)
        baslik_kutusu(d, yk, ["NASA SWIFT:", "22 YILLIK VEDA"])
        # yıldızlar
        for i in range(14):
            sx, sy = 6 + (i * 37) % (GEN - 12), 136 + (i * 23) % 36
            if yanip(t + i * 0.21, 1.2, 0.7):
                d.point((sx, sy), fill=P["gumus"])
        uy = 150
        dusus = t >= z["gunes"]
        if dusus:
            uy += min(14, int(adim(t - z["gunes"], 6) * 3))
            for x in range(4, GEN - 4, 2):
                if (x // 2 + int(t * 6)) % 3:
                    d.point((x, 172), fill=P["kirmizi"])
        titre = (1 if yanip(t, 0.25) else -1) if dusus and t >= z["alcal"] else 0
        self._uydu(d, CX + titre, uy)
        if not dusus:
            if t >= z["y2004"]:
                yk.yaz("PLAN: 2 YIL", R(6), R(174), ad="piksel_ince", boyut=31, renk="soluk")
                d.rectangle([100, 177, 100 + 9, 181], fill=P["mavi_acik"])
            if t >= z["y22"]:
                yk.yaz("GERÇEK: 22 YIL", R(6), R(186), ad="piksel", boyut=39, bant="altin", kenar=3)
                d.rectangle([100, 190, 100 + min(94, int(adim(t - z["y22"], 8) * 94)), 194], fill=P["altin"])
            satirlar = [("gama", "2.000+", "GAMA IŞINI PATLAMASI"), ("sn", "1.400+", "SÜPERNOVA"),
                        ("makale", "~7.000", "BİLİMSEL MAKALE")]
            for i, (k, sayi, metin) in enumerate(satirlar):
                if t < z[k]:
                    continue
                y = 202 + i * 18
                d.rectangle([4, y, GEN - 5, y + 14], fill=P["zemin3"], outline=P["cizgi"])
                yk.yaz(sayi, R(8), R(y) + 12, ad="piksel", boyut=39, bant="altin", kenar=3)
                yk.yaz(metin, R(54), R(y) + 12, ad="piksel", boyut=31, renk="gumus")
        else:
            satirlar = [("gunes", "GÜNEŞ ETKİNLİĞİ ARTTI", "gumus"), ("alcal", "YÖRÜNGE ALÇALDI", "gumus"),
                        ("onum", "BİRKAÇ HAFTAYA ATMOSFERDE", "kirmizi")]
            for i, (k, metin, r) in enumerate(satirlar):
                if t < z[k]:
                    continue
                y = 184 + i * 18
                d.rectangle([4, y, GEN - 5, y + 14], fill=P["zemin3"],
                            outline=P["kirmizi"] if r == "kirmizi" else P["cizgi"])
                ikon(d, I.MADDE, 8, y + 4, 1)
                yk.yaz(metin, R(16), R(y) + 12, ad="piksel", boyut=39, renk=r)
            if t >= z["ama"]:
                d.rectangle([4, 244, GEN - 5, 268], fill=P["zemin2"], outline=P["altin"])
                yk.yaz("22 YILLIK VERİ", R(CX), R(246), "orta", ad="piksel", boyut=39, bant="altin", kenar=3)
                yk.yaz("BİLİME KALIYOR", R(CX), R(256), "orta", ad="piksel", boyut=39, renk="beyaz")
        kaynak(yk, self.ctx["kaynak"])


# ------------------------------------------------------------------ Bölüm 5 · HARİTAM: YANLIŞ DEFTERİ
class HaritamYanlis(Sahne):
    def maskot_yol(self):
        z = self.z()
        return [(0.0, *M(150), "saskin"), (z["sen"], *M(200), "dusun"), (z["yks"], *M(100), "sevin"),
                (z["foto"], *M(150), "isaret"), (z["neden"], *M(200), "isaret"), (z["tekrar"], *M(230), "isaret"),
                (z["boylece"], *M(262), "sevin"), (self.sure - 1.6, *DINLEN, "levelup!")]

    def z(self):
        return {"sen": self.kt("Sen", tam=True), "yks": self.kt("YKS"), "foto": self.kt("fotoğrafını"),
                "neden": self.kt("nedenini"), "tekrar": self.kt("aralıklı"), "boylece": self.kt("Böylece")}

    def olaylar(self):
        z = self.z()
        return [(0.2, "boss"), (z["sen"], "tik"), (z["yks"], "glitch"), (z["yks"] + 0.1, "blip"),
                (z["foto"], "tik"), (z["neden"], "blip"), (z["tekrar"], "coin"), (z["tekrar"] + 0.5, "coin"),
                (z["tekrar"] + 1.0, "coin"), (z["boylece"], "tik"), (self.sure - 1.6, "levelup")]

    def ciz(self, t, d, yk):
        z = self.z()
        if t < z["yks"]:
            # piksel patlama (süpernova) -> ders: yanlışlardan öğren
            r = int(adim(t, 8) * 18) % 30 + 4
            for a in range(0, 360, 30):
                x = CX + int(math.cos(math.radians(a)) * r)
                y = 172 + int(math.sin(math.radians(a)) * r)
                d.rectangle([x - 1, y - 1, x + 1, y + 1], fill=P["altin"] if a % 60 else P["kirmizi"])
            daire(d, CX, 172, 5, P["beyaz"] if yanip(t, 0.3) else P["altin"])
            yk.yaz("PATLAMALARDAN ÖĞRENDİ", RCX, R(110), "orta", ad="piksel", boyut=47, bant="altin", kenar=5)
            if t >= z["sen"]:
                yk.yaz("SEN DE YANLIŞLARINDAN", RCX, R(222), "orta", ad="piksel", boyut=47, renk="beyaz", kenar=5)
            return
        x0, y0, w = 0, 80, GEN
        panel(d, x0, y0, w, 206)
        dugme(d, x0 + 2, y0 + 2, w - 4, 20)
        yk.yaz("YKS HARİTAM", R(CX), R(y0 + 2) + 10, "orta", ad="piksel", boyut=47, renk="beyaz")
        yk.yaz("YANLIŞ DEFTERİ", R(x0 + 4), R(y0 + 25), ad="piksel", boyut=39, renk="altin")
        # soru kartı (fotoğraf)
        kx, ky, kw, kh = x0 + 10, y0 + 42, w - 20, 50
        if t >= z["foto"]:
            d.rectangle([kx, ky, kx + kw - 1, ky + kh - 1], fill=P["gumus"], outline=P["gumus_koyu"])
            yk.yaz("SORU 14", R(kx + 4), R(ky + 3), ad="piksel_ince", boyut=27, renk="mavi_koyu")
            for i in range(4):
                d.rectangle([kx + 6, ky + 16 + i * 7, kx + kw - 20 - (i % 2) * 30, ky + 17 + i * 7], fill=P["soluk"])
            # yanlış işareti
            d.line([kx + kw - 14, ky + 6, kx + kw - 6, ky + 14], fill=P["kirmizi"], width=2)
            d.line([kx + kw - 6, ky + 6, kx + kw - 14, ky + 14], fill=P["kirmizi"], width=2)
            # flaş
            if t - z["foto"] < 0.2:
                d.rectangle([kx, ky, kx + kw - 1, ky + kh - 1], fill=P["beyaz"])
            yk.yaz("FOTOĞRAF ÇEKİLDİ", R(kx), R(ky + kh + 2), ad="piksel_ince", boyut=27, renk="soluk")
        if t >= z["neden"]:
            metin = "NEDEN: İŞLEM HATASI"
            n = min(len(metin), int((t - z["neden"]) * 18) + 1)
            d.rectangle([kx, ky + kh + 12, kx + kw - 1, ky + kh + 26], fill=P["zemin3"], outline=P["cizgi"])
            yk.yaz(metin[:n] + ("_" if n < len(metin) and yanip(t, 0.3) else ""), R(kx + 4), R(ky + kh + 12) + 12,
                   ad="piksel", boyut=39, renk="gumus")
        if t >= z["tekrar"]:
            ty = y0 + 136
            yk.yaz("ARALIKLI TEKRAR", R(x0 + 6), R(ty), ad="piksel_ince", boyut=27, renk="soluk")
            d.rectangle([x0 + 10, ty + 16, x0 + w - 10, ty + 17], fill=P["cizgi"])
            for i, f in enumerate([0.0, 0.18, 0.45, 1.0]):
                if t < z["tekrar"] + i * 0.5:
                    continue
                x = int(x0 + 10 + (w - 20) * f)
                d.rectangle([x - 3, ty + 13, x + 3, ty + 20], fill=P["altin"] if i else P["kirmizi"],
                            outline=P["altin_koyu"])
            yk.yaz("ARALAR GİDEREK AÇILIR", R(CX), R(ty + 24), "orta", ad="piksel_ince", boyut=27, renk="gumus")
        if t >= z["boylece"]:
            ikon(d, I.TIK, x0 + 30, y0 + 177, 2)
            yk.yaz("AYNI HATA SINAVDA YOK", R(x0 + 46), R(y0 + 176), ad="piksel", boyut=39, renk="mavi_acik")
        if t >= self.sure - 1.6:
            yk.yaz("LEVEL UP!", RCX, R(y0 + 194), "orta", ad="ingilizce_etiket", boyut=40, bant="altin")


def ay_ciz(d, cx, cy, r):
    """Piksel Ay: gümüş disk, kraterler, sol kenarda dither gölge."""
    daire(d, cx, cy, r, P["gumus_koyu"])
    for (dx, dy, k) in [(-8, -6, 5), (7, 5, 4), (-2, 10, 3), (9, -9, 3), (-11, 6, 2)]:
        daire(d, cx + dx * r // 26, cy + dy * r // 26, max(1, k * r // 26), P["soluk"])
    for yy in range(cy - r, cy + r + 1):
        for xx in range(cx - r, cx - r + r // 2):
            if (xx - cx) ** 2 + (yy - cy) ** 2 <= r * r and (xx + yy) % 2 == 0:
                d.point((xx, yy), fill=P["zemin3"])


def konum_pimi(d, x, y, parla=False):
    """Harita konum iğnesi (uç noktası x, y)."""
    renk = P["altin"] if parla else P["kirmizi"]
    d.ellipse([x - 5, y - 15, x + 5, y - 5], fill=renk, outline=P["zemin"])
    d.polygon([(x - 4, y - 8), (x + 4, y - 8), (x, y)], fill=renk)
    d.rectangle([x - 1, y - 11, x + 1, y - 9], fill=P["beyaz"])


# ------------------------------------------------------------------ Bölüm 6 · HABER: YERLİ NAVİGASYON + AY ARACI
class HaberNavigasyon(Sahne):
    def maskot_yol(self):
        z = self.z()
        return [(0.0, *M(113), "isaret"), (z["nav"], *M(150), "isaret"), (z["veri"], *M(190), "isaret"),
                (z["togg"], *M(208), "sevin"), (z["uzay"], *M(150), "saskin"), (z["yuzde"], *M(196), "isaret"),
                (z["hibrit"], *M(214), "isaret"), (z["ay"], *M(232), "sevin"), (z["yz"], *M(250), "isaret"),
                (z["milyon"] + 2.0, *DINLEN, None)]

    def z(self):
        return {"y2027": self.kt("2027"), "nav": self.kt("navigasyon"), "veri": self.kt("veri"),
                "togg": self.kt("Togg"), "uzay": self.kt("uzaydan"), "yuzde": self.kt("80"),
                "hibrit": self.kt("hibrit"), "ay": self.kt("Ay'a"), "yz": self.kt("yapay"),
                "milyon": self.kt("milyon")}

    def olaylar(self):
        z = self.z()
        return [(z["y2027"], "blip"), (z["nav"], "whoosh"), (z["veri"], "tik"), (z["togg"], "tik"),
                (z["uzay"], "glitch"), (z["yuzde"], "coin"), (z["hibrit"], "tik"), (z["ay"], "whoosh"),
                (z["yz"], "blip"), (z["milyon"], "levelup")]

    def ciz(self, t, d, yk):
        z = self.z()
        etiket(d, yk, "TÜRKİYE", "22 EKİM", rozet="TR")
        if t < z["uzay"]:
            baslik_kutusu(d, yk, ["YERLİ HARİTA VE", "NAVİGASYON"])
            self._harita(d, yk, t, z)
        else:
            baslik_kutusu(d, yk, ["TÜRK AY ARACI", "HEDEF: 2027"])
            self._ay(d, yk, t, z)
        kaynak(yk, self.ctx["kaynak"])

    def _harita(self, d, yk, t, z):
        x0, y0, x1, y1 = 4, 138, GEN - 5, 186
        d.rectangle([x0, y0, x1, y1], fill=P["zemin2"], outline=P["cizgi"])
        for gx in range(x0 + 18, x1, 26):          # yollar
            d.line([gx, y0 + 1, gx + 6, y1 - 1], fill=P["zemin3"], width=3)
        for gy in (y0 + 14, y0 + 33):
            d.line([x0 + 1, gy, x1 - 1, gy], fill=P["zemin3"], width=3)
        # rota: soldan sağa noktalı çizgi ilerler
        if t >= z["nav"]:
            oran = min(1.0, adim(t - z["nav"], 8) / 2.0)
            noktalar = [(x0 + 14, y1 - 10), (x0 + 60, y0 + 33), (x0 + 120, y0 + 33), (x1 - 24, y0 + 14)]
            uz = len(noktalar) - 1
            son = oran * uz
            for i in range(uz):
                if son <= i:
                    break
                (ax, ay), (bx, by) = noktalar[i], noktalar[i + 1]
                f = min(1.0, son - i)
                for k in range(0, 40):
                    g = k / 40 * f
                    if k % 3 != 2:
                        d.point((int(ax + (bx - ax) * g), int(ay + (by - ay) * g)), fill=P["mavi_acik"])
            daire(d, noktalar[0][0], noktalar[0][1], 2, P["mavi_buz"])
            if oran >= 1:
                konum_pimi(d, noktalar[-1][0], noktalar[-1][1], yanip(t, 0.5))
        if t >= z["y2027"]:
            yk.yaz("2027 BAŞI", R(x0 + 4), R(y0 + 2), ad="piksel", boyut=39, bant="altin", kenar=3)
        satirlar = [("nav", "TAMAMEN YERLİ UYGULAMA", "gumus"), ("veri", "VERİ GÜVENLİĞİ: STRATEJİK", "gumus"),
                    ("togg", "PROJEDE TOGG'UN KATKISI VAR", "gumus")]
        for i, (k, metin, r) in enumerate(satirlar):
            if t < z[k]:
                continue
            y = 192 + i * 18
            d.rectangle([4, y, GEN - 5, y + 14], fill=P["zemin3"], outline=P["cizgi"])
            ikon(d, I.TIK, 8, y + 4, 1)
            yk.yaz(metin, R(18), R(y) + 12, ad="piksel", boyut=39, renk=r)

    def _ay(self, d, yk, t, z):
        for i in range(12):
            sx, sy = 8 + (i * 41) % (GEN - 16), 138 + (i * 17) % 40
            if yanip(t + i * 0.23, 1.1, 0.7):
                d.point((sx, sy), fill=P["gumus"])
        ay_ciz(d, GEN - 34, 160, 22)
        # roket Ay'a doğru gider
        oran = min(1.0, max(0.0, adim(t - z["ay"], 8) / 2.0)) if t >= z["ay"] else 0.0
        rx, ry = int(16 + (GEN - 80) * oran), int(176 - 26 * oran)
        ikon(d, I.ROKET, rx, ry - 16, 1)
        if int(t * 12) % 2:
            d.rectangle([rx + 4, ry, rx + 6, ry + 3], fill=P["altin"])
        if t >= z["yuzde"]:
            yk.yaz("%80+ YERLİ", R(6), R(140), ad="piksel", boyut=55, bant="altin", kenar=4)
        satirlar = [("hibrit", "KENDİ HİBRİT MOTORU"), ("ay", "2027'NİN İLK AYLARINDA AY'A")]
        for i, (k, metin) in enumerate(satirlar):
            if t < z[k]:
                continue
            y = 192 + i * 18
            d.rectangle([4, y, GEN - 5, y + 14], fill=P["zemin3"], outline=P["cizgi"])
            ikon(d, I.MADDE, 8, y + 4, 1)
            yk.yaz(metin, R(16), R(y) + 12, ad="piksel", boyut=39, renk="gumus")
        if t >= z["yz"]:
            d.rectangle([4, 232, GEN - 5, 266], fill=P["zemin2"], outline=P["altin"])
            yk.yaz("YAPAY ZEKÂ HEDEFİ · 2 YIL", R(CX), R(235), "orta", ad="piksel_ince", boyut=31, renk="soluk")
            if t >= z["milyon"]:
                yk.yaz("5 MİLYON KİŞİYE", R(CX), R(245), "orta", ad="piksel", boyut=39, bant="altin", kenar=3)
                yk.yaz("YZ OKURYAZARLIĞI", R(CX), R(255), "orta", ad="piksel", boyut=39, renk="beyaz")


# ------------------------------------------------------------------ Bölüm 6 · HABER: NASA ARTEMIS 3
class HaberArtemis(Sahne):
    def maskot_yol(self):
        z = self.z()
        return [(0.0, *M(113), "saskin"), (z["inil"], *M(140), "dusun"), (z["dort"], *M(192), "isaret"),
                (z["blue"], *M(160), "isaret"), (z["spacex"], *M(160), "isaret"), (z["uc"], *M(206), "isaret"),
                (z["luca"], *M(224), "sevin"), (z["hedef"], *M(242), "isaret"), (z["y2028"], *M(254), "sevin"),
                (z["y2028"] + 2.5, *DINLEN, None)]

    def z(self):
        return {"inil": self.kt("inilmeyecek"), "dort": self.kt("Dört"), "gun": self.kt("14"),
                "kenet": self.kt("kenetlenme"), "blue": self.kt("Blue"), "spacex": self.kt("SpaceX"),
                "uc": self.kt("üç", tam=True), "luca": self.kt("Luca"), "hedef": self.kt("Hedef"),
                "y2028": self.kt("2028")}

    def olaylar(self):
        z = self.z()
        return [(z["inil"], "boss"), (z["dort"], "blip"), (z["gun"], "tik"), (z["kenet"], "whoosh"),
                (z["blue"], "coin"), (z["spacex"], "coin"), (z["uc"], "tik"), (z["luca"], "blip"),
                (z["hedef"], "tik"), (z["y2028"], "levelup")]

    def _kapsul(self, d, x, y):
        # Orion: koni gövde + servis modülü + güneş panelleri
        d.polygon([(x - 6, y + 6), (x + 6, y + 6), (x + 3, y - 3), (x - 3, y - 3)], fill=P["gumus"],
                  outline=P["gumus_koyu"])
        d.rectangle([x - 5, y + 7, x + 5, y + 13], fill=P["soluk"])
        d.rectangle([x - 16, y + 9, x - 7, y + 11], fill=P["mavi"])
        d.rectangle([x + 7, y + 9, x + 16, y + 11], fill=P["mavi"])

    def _inis_araci(self, d, x, y, ad, starship):
        if starship:
            d.rectangle([x - 4, y - 18, x + 4, y + 10], fill=P["gumus"], outline=P["gumus_koyu"])
            d.polygon([(x - 4, y - 18), (x + 4, y - 18), (x, y - 26)], fill=P["gumus"])
            d.rectangle([x - 7, y + 4, x - 5, y + 10], fill=P["gumus_koyu"])
            d.rectangle([x + 5, y + 4, x + 7, y + 10], fill=P["gumus_koyu"])
        else:
            d.rectangle([x - 6, y - 16, x + 6, y + 4], fill=P["mavi_koyu"], outline=P["mavi_acik"])
            d.rectangle([x - 3, y - 12, x + 3, y - 8], fill=P["mavi_buz"])
            d.line([x - 6, y + 4, x - 10, y + 10], fill=P["gumus_koyu"])
            d.line([x + 6, y + 4, x + 10, y + 10], fill=P["gumus_koyu"])
        return ad

    def ciz(self, t, d, yk):
        z = self.z()
        etiket(d, yk, "DÜNYA", "23 EKİM", ikon_sablon=I.KURE)
        baslik_kutusu(d, yk, ["NASA ARTEMIS 3:", "AY ÖNCESİ PROVA"])
        # Dünya yayı (alt) + yıldızlar
        for i in range(12):
            sx, sy = 6 + (i * 37) % (GEN - 12), 136 + (i * 19) % 30
            if yanip(t + i * 0.19, 1.2, 0.7):
                d.point((sx, sy), fill=P["gumus"])
        if t < z["kenet"]:
            d.ellipse([-40, 168, GEN + 40, 260], fill=P["mavi_koyu"], outline=P["mavi_acik"])
            d.rectangle([-40, 200, GEN + 40, 268], fill=P["zemin"])
            a = adim(t, 8) * 0.6
            ox, oy = CX + int(math.cos(a) * 70), 160 + int(math.sin(a) * 8)
            self._kapsul(d, ox, oy)
            if t >= z["inil"]:
                d.rectangle([4, 202, GEN - 5, 216], fill=P["zemin3"], outline=P["kirmizi"] if yanip(t, 0.6) else P["cizgi"])
                yk.yaz("BU GÖREVDE AY'A İNİŞ YOK", R(10), R(202) + 12, ad="piksel", boyut=39, renk="kirmizi")
            if t >= z["dort"]:
                yk.yaz("4 ASTRONOT", R(6), R(222), ad="piksel", boyut=47, bant="altin", kenar=3)
            if t >= z["gun"]:
                yk.yaz("~14 GÜN YÖRÜNGEDE", R(6), R(240), ad="piksel", boyut=39, renk="gumus")
        else:
            # kenetlenme provası: Orion iki iniş aracına sırayla yanaşır
            hedef = 1 if t >= z["spacex"] else 0
            ax_bm, ax_ss = 40, GEN - 40
            if t >= z["blue"]:
                self._inis_araci(d, ax_bm, 172, "BLUE MOON", False)
                yk.yaz("BLUE MOON", R(ax_bm), R(184), "orta", ad="piksel", boyut=31, renk="mavi_acik")
            if t >= z["spacex"]:
                self._inis_araci(d, ax_ss, 172, "STARSHIP", True)
                yk.yaz("STARSHIP", R(ax_ss), R(184), "orta", ad="piksel", boyut=31, renk="gumus")
            hx = (ax_bm + 18) if hedef == 0 else (ax_ss - 18)
            t0 = z["blue"] if hedef == 0 else z["spacex"]
            oran = min(1.0, max(0.0, adim(t - t0, 8) / 1.2)) if t >= z["blue"] else 0.0
            ox = int(CX + (hx - CX) * oran)
            self._kapsul(d, ox, 158)
            if oran >= 1 and yanip(t, 0.4):
                yk.yaz("KENETLENDİ", R(CX), R(140), "orta", ad="piksel", boyut=39, renk="altin")
            elif t < z["blue"]:
                yk.yaz("KENETLENME PROVASI", R(CX), R(140), "orta", ad="piksel", boyut=39, renk="gumus")
            satirlar = [("uc", "3 AYRI ROKET"), ("luca", "ESA: LUCA PARMITANO DA EKİPTE"),
                        ("hedef", "KALKIŞ HEDEFİ: 2027")]
            for i, (k, metin) in enumerate(satirlar):
                if t < z[k]:
                    continue
                y = 196 + i * 16
                d.rectangle([4, y, GEN - 5, y + 13], fill=P["zemin3"], outline=P["cizgi"])
                ikon(d, I.MADDE, 8, y + 4, 1)
                yk.yaz(metin, R(16), R(y) + 10, ad="piksel", boyut=39, renk="gumus")
            if t >= z["y2028"]:
                d.rectangle([4, 246, GEN - 5, 270], fill=P["zemin2"], outline=P["altin"])
                yk.yaz("2028: AY'IN", R(CX), R(248), "orta", ad="piksel", boyut=39, bant="altin", kenar=3)
                yk.yaz("GÜNEY KUTBUNA İNİŞ", R(CX), R(258), "orta", ad="piksel", boyut=39, renk="beyaz")
        kaynak(yk, self.ctx["kaynak"])


# ------------------------------------------------------------------ Bölüm 6 · HARİTAM: ODAK SAYACI
class HaritamOdak(Sahne):
    def maskot_yol(self):
        z = self.z()
        return [(0.0, *M(150), "dusun"), (z["yks"], *M(200), "isaret"), (z["haritam"], *M(100), "sevin"),
                (z["baslat"], *M(150), "isaret"), (z["telefon"], *M(196), "isaret"), (z["gunluk"], *M(220), "isaret"),
                (z["serin"], *M(246), "sevin"), (self.sure - 1.6, *DINLEN, "levelup!")]

    def z(self):
        return {"yks": self.kt("YKS"), "haritam": self.kt("Haritam"), "pomo": self.kt("Pomodoro"),
                "baslat": self.kt("başlatırsın"), "telefon": self.kt("telefonu"), "sadece": self.kt("sadece"),
                "gunluk": self.kt("Günlük"), "serin": self.kt("serin"), "seri": self.kt("Seriyi")}

    def olaylar(self):
        z = self.z()
        o = [(0.2, "whoosh"), (z["yks"], "tik"), (z["haritam"], "glitch"), (z["haritam"] + 0.1, "blip"),
             (z["pomo"], "blip"), (z["baslat"], "tik"), (z["telefon"], "boss"), (z["gunluk"], "coin"),
             (z["seri"], "tik"), (self.sure - 1.6, "levelup")]
        o += [(z["serin"] + i * 0.15, "coin") for i in range(4)]
        return o

    def ciz(self, t, d, yk):
        z = self.z()
        if t < z["haritam"]:
            # Ay'a giden prova rotası: adım adım ilerleyen noktalar
            ay_ciz(d, GEN - 40, 160, 18)
            n = int(adim(t, 4) * 4) % 9 + 1
            for i in range(n):
                x = 14 + i * 16
                d.rectangle([x, 176 - i * 2, x + 3, 179 - i * 2], fill=P["altin"] if i == n - 1 else P["mavi_acik"])
            yk.yaz("ÖNCE PROVA", RCX, R(110), "orta", ad="piksel", boyut=55, bant="altin", kenar=5)
            if t >= z["yks"]:
                yk.yaz("YKS DE ÖYLE:", RCX, R(200), "orta", ad="piksel", boyut=55, renk="beyaz", kenar=5)
                yk.yaz("HER GÜN KÜÇÜK ADIMLAR", RCX, R(222), "orta", ad="piksel", boyut=47, renk="gumus", kenar=5)
            return
        x0, y0, w = 0, 80, GEN
        panel(d, x0, y0, w, 206)
        dugme(d, x0 + 2, y0 + 2, w - 4, 20)
        yk.yaz("YKS HARİTAM", R(CX), R(y0 + 2) + 10, "orta", ad="piksel", boyut=47, renk="beyaz")
        yk.yaz("ODAK SAYACI", R(x0 + 4), R(y0 + 25), ad="piksel", boyut=39, renk="altin")
        if t >= z["pomo"]:
            yk.yaz("POMODORO", R(x0 + w - 6), R(y0 + 26), "sag", ad="piksel_ince", boyut=31, renk="soluk")
        # sayaç: halka + kalan süre (hızlandırılmış geri sayım)
        cx, cy, r = CX, y0 + 72, 30
        d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=P["zemin"], outline=P["cizgi"])
        kalan = 25 * 60
        if t >= z["baslat"]:
            gecen = int((t - z["baslat"]) * 40)
            kalan = max(0, kalan - gecen)
            oran = 1 - kalan / 1500
            for k in range(0, int(360 * oran), 6):
                a = math.radians(k - 90)
                d.rectangle([cx + int(math.cos(a) * (r - 3)) - 1, cy + int(math.sin(a) * (r - 3)) - 1,
                             cx + int(math.cos(a) * (r - 3)) + 1, cy + int(math.sin(a) * (r - 3)) + 1],
                            fill=P["altin"])
        yk.yaz(f"{kalan // 60:02d}:{kalan % 60:02d}", R(cx), R(cy - 7), "orta", ad="piksel", boyut=71, renk="beyaz")
        # telefon bırakıldı
        if t >= z["telefon"]:
            px, py = x0 + 14, y0 + 52
            ikon(d, I.TELEFON, px, py, 3)
            d.line([px - 2, py - 2, px + 22, py + 32], fill=P["kirmizi"], width=2)
            if t >= z["sadece"]:
                ikon(d, I.KITAP_1, x0 + w - 34, y0 + 58, 2)
                yk.yaz("DERS", R(x0 + w - 24), R(y0 + 84), "orta", ad="piksel_ince", boyut=27, renk="gumus")
        if t >= z["gunluk"]:
            yk.yaz("BUGÜNKÜ ODAK", R(x0 + 6), R(y0 + 112), ad="piksel_ince", boyut=31, renk="soluk")
            yk.yaz("2 SA 05 DK", R(x0 + w - 8), R(y0 + 109), "sag", ad="piksel", boyut=55, bant="altin", kenar=4)
        if t >= z["serin"]:
            yk.yaz("SERİ", R(x0 + 6), R(y0 + 136), ad="piksel_ince", boyut=31, renk="soluk")
            n = min(7, 3 + int((t - z["serin"]) / 0.15))
            for i in range(7):
                bx = x0 + 34 + i * 20
                dolu = i < n
                d.rectangle([bx, y0 + 134, bx + 15, y0 + 147], fill=P["altin"] if dolu else P["zemin3"],
                            outline=P["altin_koyu"] if dolu else P["cizgi"])
            yk.yaz(f"{n} GÜN", R(x0 + w - 8), R(y0 + 151), "sag", ad="piksel", boyut=39, renk="altin")
        if t >= z["seri"]:
            ikon(d, I.TIK, x0 + 24, y0 + 167, 2)
            yk.yaz("YARIN DA MASADASIN", R(x0 + 40), R(y0 + 166), ad="piksel", boyut=39, renk="mavi_acik")
        if t >= self.sure - 1.6:
            yk.yaz("LEVEL UP!", RCX, R(y0 + 194), "orta", ad="ingilizce_etiket", boyut=40, bant="altin")



def ari(d, x, y, b=1, kanat=True):
    """Piksel bal arısı (gövde ortası x, y; b = ölçek)."""
    if kanat:
        d.ellipse([x - 2 * b, y - 5 * b, x + 1 * b, y - 1 * b], fill=P["mavi_buz"])
        d.ellipse([x + 1 * b, y - 5 * b, x + 4 * b, y - 1 * b], fill=P["mavi_buz"])
    d.ellipse([x - 4 * b, y - 2 * b, x + 4 * b, y + 2 * b], fill=P["altin"])
    for k in (-1, 2):
        d.rectangle([x + k * b, y - 2 * b, x + k * b + max(0, b - 1), y + 2 * b], fill=P["zemin"])
    d.rectangle([x - 5 * b, y - 1 * b, x - 4 * b, y], fill=P["zemin"])


def petek(d, x0, y0, sutun, satir, dolu=lambda i, j: True):
    """Altıgen petek ızgarası (piksel altıgenler)."""
    for j in range(satir):
        for i in range(sutun):
            x = x0 + i * 12 + (6 if j % 2 else 0)
            y = y0 + j * 10
            renk = P["altin"] if dolu(i, j) else P["altin_koyu"]
            d.polygon([(x + 3, y), (x + 9, y), (x + 12, y + 5), (x + 9, y + 10), (x + 3, y + 10), (x, y + 5)],
                      fill=renk, outline=P["zemin"])


# ------------------------------------------------------------------ Bölüm 7 (yayın 6) · HABER: ODTÜ ROBOROYALE
class HaberAri(Sahne):
    def maskot_yol(self):
        z = self.z()
        return [(0.0, *M(113), "saskin"), (z["ulke"], *M(140), "isaret"), (z["polen"], *M(192), "isaret"),
                (z["kralice"], *M(160), "sevin"), (z["sut"], *M(196), "isaret"), (z["kamera"], *M(214), "isaret"),
                (z["hedef"], *M(236), "isaret"), (z["science"], *M(262), "sevin"), (z["science"] + 2.0, *DINLEN, None)]

    def z(self):
        return {"robo": self.kt("RoboRoyale"), "ulke": self.kt("Türkiye"), "amac": self.kt("Amaç"),
                "polen": self.kt("polen"), "ucus": self.kt("uçuyor"), "kralice": self.kt("kraliçe"),
                "sut": self.kt("sütüyle"), "kamera": self.kt("kameralar"), "hedef": self.kt("Hedef"),
                "science": self.kt("Science")}

    def olaylar(self):
        z = self.z()
        o = [(z["robo"], "blip"), (z["amac"], "tik"), (z["polen"], "tik"), (z["ucus"], "whoosh"),
             (z["kralice"], "levelup"), (z["sut"], "coin"), (z["kamera"], "blip"), (z["hedef"], "coin"),
             (z["science"], "levelup")]
        o += [(z["ulke"] + i * 0.3, "tik") for i in range(4)]
        return o

    def ciz(self, t, d, yk):
        z = self.z()
        etiket(d, yk, "TÜRKİYE", "24 EKİM", rozet="TR")
        baslik_kutusu(d, yk, ["ODTÜ: ROBOTLAR", "ARILARA YARDIMCI"])
        if t < z["kralice"]:
            self._kovan(d, yk, t, z)
        else:
            self._kralice(d, yk, t, z)
        kaynak(yk, self.ctx["kaynak"])

    def _kovan(self, d, yk, t, z):
        petek(d, 128, 156, 5, 3)
        d.rectangle([126, 186, 196, 190], fill=P["zemin3"], outline=P["cizgi"])
        n = 5 if t >= z["ucus"] else 2
        for i in range(n):
            f = (t * 0.5 + i / n) % 1.0
            ax = int(118 - f * 100)
            ay = 172 + int(math.sin(f * 9 + i) * 7)
            ari(d, ax, ay, 1, kanat=yanip(t + i * 0.1, 0.2))
        if t >= z["ulke"]:
            for i, u in enumerate(["TR", "UK", "CZ", "AT"]):
                if t < z["ulke"] + i * 0.3:
                    continue
                x = 6 + i * 26
                d.rectangle([x, 138, x + 21, 149], fill=P["kirmizi"] if u == "TR" else P["mavi_koyu"])
                yk.yaz(u, R(x + 11), R(138) + 6, "orta", ad="piksel", boyut=39, renk="beyaz")
            yk.yaz("AB DESTEKLİ · ROBOROYALE", R(6), R(152), ad="piksel_ince", boyut=27, renk="soluk")
        satirlar = [("amac", "YZ + ROBOT = DAHA ÇOK TOZLAŞMA", "gumus"),
                    ("polen", "KOVANA POLEN GİRİŞİ SINIRLI", "gumus"),
                    ("ucus", "ARILAR DAHA ÇOK UÇUYOR", "altin")]
        for i, (k, metin, r) in enumerate(satirlar):
            if t < z[k]:
                continue
            y = 196 + i * 18
            d.rectangle([4, y, GEN - 5, y + 14], fill=P["zemin3"], outline=P["cizgi"])
            ikon(d, I.MADDE, 8, y + 4, 1)
            yk.yaz(metin, R(16), R(y) + 12, ad="piksel", boyut=39, renk=r)

    def _kralice(self, d, yk, t, z):
        petek(d, 4, 140, 16, 1, dolu=lambda i, j: i % 3 != 1)
        # kraliçe arı (büyük) + taç
        kx, ky = CX - 30, 172
        ari(d, kx, ky, 3, kanat=yanip(t, 0.25))
        d.rectangle([kx - 3, ky - 13, kx + 3, ky - 11], fill=P["altin_acik"])
        d.point([(kx - 3, ky - 14), (kx, ky - 15), (kx + 3, ky - 14)], fill=P["altin_acik"])
        yk.yaz("KRALİÇE", R(kx), R(ky + 9), "orta", ad="piksel", boyut=31, renk="altin")
        if t >= z["sut"]:
            # mikro robot kol + damlalar
            rx = CX + 30
            d.rectangle([rx, 160, rx + 12, 170], fill=P["gumus"], outline=P["gumus_koyu"])
            d.line([rx, 165, kx + 14, ky - 2], fill=P["gumus_koyu"], width=2)
            for k in range(3):
                f = (t * 1.5 + k / 3) % 1.0
                d.rectangle([int(rx - f * (rx - kx - 14)), int(165 - f * 6), int(rx - f * (rx - kx - 14)) + 1,
                             int(165 - f * 6) + 1], fill=P["beyaz"])
            yk.yaz("MİKRO POMPA", R(rx + 6), R(172), "orta", ad="piksel_ince", boyut=27, renk="soluk")
        if t >= z["kamera"]:
            cx2 = GEN - 26
            d.rectangle([cx2 - 8, 156, cx2 + 8, 166], fill=P["zemin3"], outline=P["mavi_acik"])
            daire(d, cx2, 161, 3, P["kirmizi"] if yanip(t, 0.5) else P["mavi"])
            if yanip(t, 0.6):
                d.rectangle([kx - 16, ky - 14, kx + 16, ky + 8], outline=P["mavi_acik"])
        satirlar = [("sut", "KRALİÇEYE TEMİZ ARI SÜTÜ", "gumus"), ("kamera", "YZ KAMERA: KRALİÇE + PETEK", "gumus")]
        for i, (k, metin, r) in enumerate(satirlar):
            if t < z[k]:
                continue
            y = 196 + i * 18
            d.rectangle([4, y, GEN - 5, y + 14], fill=P["zemin3"], outline=P["cizgi"])
            ikon(d, I.MADDE, 8, y + 4, 1)
            yk.yaz(metin, R(16), R(y) + 12, ad="piksel", boyut=39, renk=r)
        if t >= z["hedef"]:
            d.rectangle([4, 234, GEN - 5, 258], fill=P["zemin2"], outline=P["altin"])
            yk.yaz("DAHA AZ KOLONİ", R(CX), R(236), "orta", ad="piksel", boyut=39, renk="beyaz")
            yk.yaz("DAHA ÇOK VERİM", R(CX), R(246), "orta", ad="piksel", boyut=39, bant="altin", kenar=3)
        if t >= z["science"]:
            yk.yaz("SCIENCE ROBOTICS'TE YAYIMLANDI", R(CX), R(263), "orta", ad="piksel_ince", boyut=27, renk="mavi_acik")


# ------------------------------------------------------------------ Bölüm 7 (yayın 6) · HABER: OPENAI KANIT İDDİASI
class HaberKanit(Sahne):
    def maskot_yol(self):
        z = self.z()
        return [(0.0, *M(113), "dusun"), (z["curut"], *M(160), "saskin"), (z["kakeya"], *M(210), "isaret"),
                (z["yang"], *M(228), "isaret"), (z["lean"], *M(150), "isaret"), (z["ama"], *M(200), "saskin"),
                (z["hip"], *M(222), "dusun"), (z["dogru"], *M(250), "sevin"), (z["dogru"] + 2.5, *DINLEN, None)]

    def z(self):
        return {"openai": self.kt("OpenAI"), "y1999": self.kt("1999"), "curut": self.kt("çürüttüğünü"),
                "kakeya": self.kt("Kakeya"), "yang": self.kt("Yang"), "lean": self.kt("Lean"),
                "ama": self.kt("Ama", tam=True), "hip": self.kt("Hipotezi", 1), "dogru": self.kt("Doğrulanırsa")}

    def olaylar(self):
        z = self.z()
        return [(z["openai"], "blip"), (z["y1999"], "tik"), (z["curut"], "glitch"), (z["kakeya"], "coin"),
                (z["yang"], "coin"), (z["lean"], "tik"), (z["ama"], "boss"), (z["hip"], "tik"),
                (z["dogru"], "levelup")]

    def ciz(self, t, d, yk):
        z = self.z()
        etiket(d, yk, "DÜNYA", "26 EKİM", ikon_sablon=I.KURE)
        baslik_kutusu(d, yk, ["OPENAI: BÜYÜK", "KANIT İDDİASI"])
        if t < z["lean"]:
            # kara tahta
            d.rectangle([4, 138, GEN - 5, 186], fill=P["zemin2"], outline=P["gumus_koyu"])
            yk.yaz("ÜSTEL ZAMAN HİPOTEZİ", R(10), R(141), ad="piksel", boyut=39, renk="gumus")
            if t >= z["y1999"]:
                yk.yaz("ETH · 1999'DAN BERİ", R(10), R(154), ad="piksel_ince", boyut=31, renk="soluk")
            yk.yaz("3-SAT SÜRESİ: 2^(c·n)", R(10), R(166), ad="piksel_ince", boyut=31, renk="mavi_acik")
            if t >= z["curut"]:
                d.line([8, 140, GEN - 9, 184], fill=P["kirmizi"], width=3)
                d.line([GEN - 9, 140, 8, 184], fill=P["kirmizi"], width=3)
            satirlar = [("curut", "ETH ÇÜRÜTÜLDÜ"), ("kakeya", "KAKEYA: TÜM BOYUTLARDA"),
                        ("yang", "YANG-MILLS: VARLIK KANITI")]
            for i, (k, metin) in enumerate(satirlar):
                if t < z[k]:
                    continue
                y = 194 + i * 18
                d.rectangle([4, y, GEN - 5, y + 14], fill=P["zemin3"], outline=P["cizgi"])
                yk.yaz(f"{i + 1}", R(9), R(y) + 12, ad="piksel", boyut=39, bant="altin", kenar=3)
                yk.yaz(metin, R(20), R(y) + 12, ad="piksel", boyut=39, renk="gumus")
        else:
            # Lean terminali
            d.rectangle([4, 138, GEN - 5, 180], fill=P["zemin"], outline=P["mavi_acik"])
            satirlar = ["> lean --check kanit.lean", "  derleniyor...", "  OK: kanıt doğrulandı"]
            n = min(3, 1 + int((t - z["lean"]) / 0.8))
            for i in range(n):
                yk.yaz(satirlar[i], R(10), R(142 + i * 12), ad="piksel_ince", boyut=31,
                       renk="altin" if i == 2 else "mavi_acik")
            if t >= z["ama"]:
                renk = "kirmizi" if yanip(t, 0.6) else "altin"
                d.rectangle([CX - 50, 188, CX + 50, 212], outline=P[renk], width=2)
                yk.yaz("ŞİMDİLİK İDDİA", R(CX), R(192), "orta", ad="piksel", boyut=55, renk=renk, kenar=4)
            if t >= z["hip"]:
                d.rectangle([4, 218, GEN - 5, 232], fill=P["zemin3"], outline=P["cizgi"])
                ikon(d, I.MADDE, 8, 222, 1)
                yk.yaz("UZMANLAR BAĞIMSIZ İNCELEYECEK", R(16), R(218) + 12, ad="piksel", boyut=39, renk="gumus")
            if t >= z["dogru"]:
                d.rectangle([4, 240, GEN - 5, 264], fill=P["zemin2"], outline=P["altin"])
                yk.yaz("DOĞRULANIRSA:", R(CX), R(242), "orta", ad="piksel", boyut=39, renk="beyaz")
                yk.yaz("BİLİM TARİHİNE GEÇER", R(CX), R(252), "orta", ad="piksel", boyut=39, bant="altin", kenar=3)
        kaynak(yk, self.ctx["kaynak"])


# ------------------------------------------------------------------ Bölüm 7 (yayın 6) · HARİTAM: KURUM PANELİ
class HaritamKurum(Sahne):
    def maskot_yol(self):
        z = self.z()
        return [(0.0, *M(150), "dusun"), (z["senin"], *M(200), "isaret"), (z["haritam"], *M(100), "sevin"),
                (z["davet"], *M(130), "isaret"), (z["excel"], *M(152), "isaret"), (z["gorev"], *M(180), "isaret"),
                (z["not"], *M(236), "sevin"), (self.sure - 1.6, *DINLEN, "levelup!")]

    def z(self):
        return {"senin": self.kt("Senin"), "haritam": self.kt("Haritam"), "davet": self.kt("davet"),
                "excel": self.kt("Excel"), "gorev": self.kt("görevleri"), "net": self.kt("netlerini"),
                "not": self.kt("not", tam=True), "yani": self.kt("Yani", 1)}

    def olaylar(self):
        z = self.z()
        return [(0.2, "blip"), (z["senin"], "tik"), (z["haritam"], "glitch"), (z["haritam"] + 0.1, "blip"),
                (z["davet"], "coin"), (z["excel"], "whoosh"), (z["gorev"], "tik"), (z["gorev"] + 0.3, "tik"),
                (z["net"], "coin"), (z["not"], "blip"), (z["yani"], "tik"), (self.sure - 1.6, "levelup")]

    OGRENCILER = [("ÖĞRENCİ 1", 9, 74), ("ÖĞRENCİ 2", 7, 61), ("SEN", 10, 68)]

    def ciz(self, t, d, yk):
        z = self.z()
        if t < z["haritam"]:
            # büyüteç: kontrol eden göz
            bx, by = CX, 165
            d.ellipse([bx - 16, by - 16, bx + 16, by + 16], outline=P["gumus"], width=3)
            d.line([bx + 11, by + 11, bx + 24, by + 24], fill=P["gumus_koyu"], width=4)
            ikon(d, I.TIK, bx - 5, by - 4, 2)
            yk.yaz("UZMANLAR KONTROL EDER", RCX, R(110), "orta", ad="piksel", boyut=47, bant="altin", kenar=5)
            if t >= z["senin"]:
                yk.yaz("SENİ DE DERSHANEN", RCX, R(204), "orta", ad="piksel", boyut=55, renk="beyaz", kenar=5)
                yk.yaz("TAKİP EDEBİLİR", RCX, R(222), "orta", ad="piksel", boyut=55, renk="beyaz", kenar=5)
            return
        x0, y0, w = 0, 80, GEN
        panel(d, x0, y0, w, 206)
        dugme(d, x0 + 2, y0 + 2, w - 4, 20)
        yk.yaz("YKS HARİTAM", R(CX), R(y0 + 2) + 10, "orta", ad="piksel", boyut=47, renk="beyaz")
        yk.yaz("KURUM PANELİ", R(x0 + 4), R(y0 + 25), ad="piksel", boyut=39, renk="altin")
        if t >= z["davet"]:
            d.rectangle([x0 + 6, y0 + 40, x0 + 96, y0 + 54], fill=P["zemin3"], outline=P["altin"])
            ikon(d, I.TIK, x0 + 84, y0 + 44, 1)
            yk.yaz("DAVET KODU", R(x0 + 10), R(y0 + 41), ad="piksel", boyut=39, renk="gumus")
        if t >= z["excel"]:
            ikon(d, I.DOSYA, x0 + 104, y0 + 41, 2)
            yk.yaz("PROGRAM", R(x0 + 124), R(y0 + 39), ad="piksel_ince", boyut=27, renk="soluk")
            yk.yaz("EXCEL'DEN", R(x0 + 124), R(y0 + 47), ad="piksel_ince", boyut=27, renk="mavi_acik")
        if t >= z["gorev"]:
            yk.yaz("ÖĞRENCİ", R(x0 + 8), R(y0 + 60), ad="piksel_ince", boyut=27, renk="soluk")
            yk.yaz("GÖREV", R(x0 + 110), R(y0 + 60), "orta", ad="piksel_ince", boyut=27, renk="soluk")
            if t >= z["net"]:
                yk.yaz("TYT NET", R(x0 + w - 10), R(y0 + 60), "sag", ad="piksel_ince", boyut=27, renk="soluk")
            for i, (ad, gorev, net) in enumerate(self.OGRENCILER):
                if t < z["gorev"] + i * 0.3:
                    continue
                y = y0 + 70 + i * 16
                sen = ad == "SEN"
                d.rectangle([x0 + 6, y, x0 + w - 7, y + 13], fill=P["zemin3"],
                            outline=P["altin"] if sen and yanip(t, 0.6) else P["cizgi"])
                yk.yaz(ad, R(x0 + 10), R(y) + 10, ad="piksel", boyut=39, renk="altin" if sen else "gumus")
                xp_bar(d, x0 + 88, y + 5, 40, gorev / 10, "altin" if sen else "mavi")
                if t >= z["net"]:
                    yk.yaz(str(net), R(x0 + w - 12), R(y) + 10, "sag", ad="piksel", boyut=39, renk="beyaz")
        if t >= z["not"]:
            ikon(d, I.SOHBET, x0 + 10, y0 + 124, 2)
            yk.yaz("NOT: BU HAFTA SÜPERSİN!", R(x0 + 34), R(y0 + 125), ad="piksel", boyut=39, renk="mavi_acik")
        if t >= z["yani"]:
            ikon(d, I.TIK, x0 + 24, y0 + 167, 2)
            yk.yaz("YKS'DE TEK BAŞINA DEĞİLSİN", R(x0 + 40), R(y0 + 166), ad="piksel", boyut=39, renk="beyaz")
        if t >= self.sure - 1.6:
            yk.yaz("LEVEL UP!", RCX, R(y0 + 194), "orta", ad="ingilizce_etiket", boyut=40, bant="altin")


# ------------------------------------------------------------------ Bölüm 8 (yayın 7) · ortak: teknopark binası
def bina_ciz(d, yk, cx, taban, t, parla=True, kat=5):
    """Piksel teknopark binası (taban = zemin çizgisi y). Camlar yanıp söner, çatıda bayrak."""
    w, h = 64, 13 + kat * 9
    x0, y0 = cx - w // 2, taban - h
    d.rectangle([x0 + 3, y0 + 3, x0 + w + 2, taban + 2], fill=P["zemin3"])            # piksel gölge
    d.rectangle([x0, y0, x0 + w - 1, taban - 1], fill=P["zemin2"], outline=P["cizgi"])
    d.rectangle([x0 + 1, y0 + 1, x0 + w - 2, y0 + 3], fill=P["mavi_koyu"])
    for j in range(kat):
        for i in range(6):
            x, y = x0 + 5 + i * 10, y0 + 8 + j * 9
            yanik = parla and yanip(t + (i * 7 + j * 3) * 0.11, 1.4, 0.7)
            d.rectangle([x, y, x + 5, y + 4], fill=P["mavi_acik"] if yanik else P["cizgi"])
    d.rectangle([cx - 5, taban - 10, cx + 4, taban - 1], fill=P["mavi"])                # kapı
    # çatı direği + bayrak
    d.rectangle([cx, y0 - 14, cx, y0 - 1], fill=P["gumus_koyu"])
    dalga = int(t * 4) % 2
    d.rectangle([cx + 1, y0 - 14 + dalga, cx + 10, y0 - 9 + dalga], fill=P["altin"])
    d.rectangle([-6, taban, GEN + 5, taban], fill=P["cizgi"])                           # zemin çizgisi


def konfeti(d, t, y0, y1, adet=14):
    for i in range(adet):
        f = (t * 0.8 + i / adet) % 1.0
        x = 6 + (i * 29) % (GEN - 12)
        y = int(y0 + f * (y1 - y0))
        renk = ["altin", "mavi_acik", "gumus", "altin_acik"][i % 4]
        d.rectangle([x, y, x + 2, y + 2], fill=P[renk])


# ------------------------------------------------------------------ Bölüm 8 (yayın 7) · HABER: VERTEX TEKNOPARK İSTANBUL'DA
class HaberVertex(Sahne):
    def maskot_yol(self):
        z = self.z()
        return [(0.0, *M(113), "isaret"), (z["kabul"], *M(160), "sevin"), (z["tekno"], *M(200), "isaret"),
                (z["tr"], *M(218), "isaret"), (z["cortex"], *M(236), "isaret"), (z["biz"], *M(150), "selam"),
                (z["tebrik"], *M(255), "sevin!")]

    def z(self):
        return {"vertex": self.kt("Vertex"), "kabul": self.kt("kabul"), "tekno": self.kt("Teknoparklar"),
                "tr": self.kt("Türkiye"), "cortex": self.kt("Cortex"), "adim": self.kt("adım"),
                "biz": self.kt("Biz", tam=True), "tebrik": self.kt("Tebrikler")}

    def olaylar(self):
        z = self.z()
        return [(z["vertex"], "blip"), (z["kabul"], "coin"), (z["tekno"], "tik"), (z["tr"], "tik"),
                (z["cortex"], "coin"), (z["adim"], "blip"), (z["biz"], "blip"), (z["tebrik"], "levelup")]

    def ciz(self, t, d, yk):
        z = self.z()
        etiket(d, yk, "TÜRKİYE", "BİZDEN", rozet="TR")
        baslik_kutusu(d, yk, ["VERTEX: TEKNOPARK", "İSTANBUL'DA!"])
        bina_ciz(d, yk, CX, 196, t, kat=4)
        yk.yaz("TEKNOPARK İSTANBUL", RCX, R(197) + 4, "orta", ad="piksel_ince", boyut=31, renk="soluk")
        if t >= z["kabul"]:
            renk = "altin" if yanip(t, 0.6, 0.7) else "altin_koyu"
            d.rectangle([CX + 28, 152, CX + 96, 174], fill=P["zemin"], outline=P[renk], width=2)
            yk.yaz("KABUL", R(CX + 62), R(153), "orta", ad="piksel", boyut=47, bant="altin", kenar=3)
            yk.yaz("EDİLDİ", R(CX + 62), R(163), "orta", ad="piksel", boyut=39, renk="beyaz", kenar=3)
            d.rectangle([CX - 96, 152, CX - 34, 174], fill=P["zemin"], outline=P["mavi_acik"])
            yk.yaz("VERTEX", R(CX - 65), R(153) + 4, "orta", ad="piksel", boyut=55, renk="beyaz", kenar=3)
        satirlar = [("tekno", "TEKNOPARK = AR-GE MERKEZİ", "gumus"),
                    ("tr", "ÖNEMLİ BİR TEKNOLOJİ ÜSSÜ", "gumus"),
                    ("cortex", "CORTEX BURADA GELİŞECEK", "altin")]
        for i, (k, metin, r) in enumerate(satirlar):
            if t < z[k]:
                continue
            y = 209 + i * 15
            d.rectangle([4, y, GEN - 5, y + 13], fill=P["zemin3"], outline=P["cizgi"])
            ikon(d, I.TIK, 8, y + 4, 1)
            yk.yaz(metin, R(18), R(y) + 10, ad="piksel", boyut=39, renk=r)
        if t >= z["tebrik"]:
            konfeti(d, t, 134, 254)
            d.rectangle([4, 256, GEN - 5, 279], fill=P["zemin2"], outline=P["altin"])
            yk.yaz("TEBRİKLER VERTEX!", RCX, R(258), "orta", ad="piksel", boyut=55, bant="altin", kenar=4)
        elif t >= z["adim"]:
            d.rectangle([4, 256, GEN - 5, 279], fill=P["zemin2"], outline=P["mavi"])
            yk.yaz("HARİTAM EKİBİ İÇİN", RCX, R(258), "orta", ad="piksel_ince", boyut=31, renk="soluk")
            yk.yaz("BÜYÜK BİR ADIM", RCX, R(267), "orta", ad="piksel", boyut=39, renk="beyaz")
        kaynak(yk, self.ctx["kaynak"])


# ------------------------------------------------------------------ Bölüm 8 (yayın 7) · HABER: GOOGLE SUNCATCHER
def uydu_ciz(d, x, y, t):
    """Piksel uydu: gövde (TPU çipi) + iki güneş paneli + anten."""
    for sx in (x - 22, x + 8):
        d.rectangle([sx, y - 4, sx + 13, y + 4], fill=P["mavi_koyu"], outline=P["mavi_acik"])
        for k in range(1, 3):
            d.line([sx + k * 4 + 1, y - 4, sx + k * 4 + 1, y + 4], fill=P["mavi"])
    d.rectangle([x - 8, y - 2, x + 7, y + 2], fill=P["gumus_koyu"])
    d.rectangle([x - 6, y - 7, x + 5, y + 7], fill=P["gumus"], outline=P["gumus_koyu"])
    d.rectangle([x - 3, y - 3, x + 2, y + 2], fill=P["altin"] if yanip(t, 0.5) else P["altin_koyu"])
    d.line([x, y - 7, x, y - 12], fill=P["gumus_koyu"])
    d.point((x, y - 13), fill=P["mavi_buz"])


class HaberSuncatcher(Sahne):
    HAIKU = ["Blue marble below", "Data streams in silent grace", "Starlight feeds my core"]

    def maskot_yol(self):
        z = self.z()
        return [(0.0, *M(113), "saskin"), (z["sun"], *M(150), "isaret"), (z["bir"], *M(206), "isaret"),
                (z["tpu"], *M(222), "isaret"), (z["planet"], *M(238), "isaret"), (z["gemma"], *M(254), "sevin"),
                (z["haiku"], *M(160), "dusun"), (z["svalbard"], *M(200), "isaret"), (z["sira"], *M(226), "isaret"),
                (z["y2027"], *M(244), "sevin"), (z["y2027"] + 2.5, *DINLEN, None)]

    def z(self):
        return {"sun": self.kt("Suncatcher"), "bir": self.kt("1", tam=True), "tpu": self.kt("TPU"),
                "planet": self.kt("Planet"), "gemma": self.kt("Gemma"), "haiku": self.kt("haiku"),
                "svalbard": self.kt("Svalbard"), "sira": self.kt("Sırada"), "y2027": self.kt("2027")}

    def olaylar(self):
        z = self.z()
        return [(z["sun"], "whoosh"), (z["bir"], "tik"), (z["tpu"], "coin"), (z["planet"], "tik"),
                (z["gemma"], "blip"), (z["haiku"], "glitch"), (z["haiku"] + 0.4, "blip"), (z["svalbard"], "coin"),
                (z["sira"], "tik"), (z["y2027"], "levelup")]

    def ciz(self, t, d, yk):
        z = self.z()
        etiket(d, yk, "DÜNYA", "30 EKİM", ikon_sablon=I.KURE)
        baslik_kutusu(d, yk, ["GOOGLE UYDUSU", "UZAYDAN ŞİİR!"])
        for i in range(12):
            sx, sy = 6 + (i * 37) % (GEN - 12), 136 + (i * 19) % 40
            if yanip(t + i * 0.19, 1.2, 0.7):
                d.point((sx, sy), fill=P["gumus"])
        if t < z["haiku"]:
            # Dünya yayı + yörüngede dönen uydu
            d.ellipse([-40, 176, GEN + 40, 268], fill=P["mavi_koyu"], outline=P["mavi_acik"])
            d.rectangle([-40, 198, GEN + 40, 272], fill=P["zemin"])
            a = adim(t, 8) * 0.5
            uydu_ciz(d, CX + int(math.cos(a) * 64), 158 + int(math.sin(a) * 8), t)
            if t >= z["sun"]:
                yk.yaz("SUNCATCHER", R(6), R(138), ad="piksel", boyut=39, bant="altin", kenar=3)
            satirlar = [("bir", "1 EKİM: YÖRÜNGEYE ÇIKTI"), ("tpu", "İÇİNDE TPU YAPAY ZEKÂ ÇİPİ"),
                        ("planet", "PLANET İLE BİRLİKTE ÜRETİLDİ"), ("gemma", "GEMMA 4 İLK CEVABI VERDİ")]
            for i, (k, metin) in enumerate(satirlar):
                if t < z[k]:
                    continue
                y = 202 + i * 16
                d.rectangle([4, y, GEN - 5, y + 13], fill=P["zemin3"],
                            outline=P["altin"] if k == "gemma" else P["cizgi"])
                ikon(d, I.MADDE, 8, y + 4, 1)
                yk.yaz(metin, R(16), R(y) + 10, ad="piksel", boyut=39, renk="altin" if k == "gemma" else "gumus")
        else:
            uydu_ciz(d, CX + 50, 146, t)
            # haiku paneli (uydudan gelen mesaj)
            panel(d, 4, 160, GEN - 9, 46)
            yk.yaz("HAİKU · UZAYDAN", R(10), R(163), ad="piksel_ince", boyut=31, renk="soluk")
            n = min(3, 1 + int((t - z["haiku"]) / 0.9))
            for i in range(n):
                yk.yaz(self.HAIKU[i], R(12), R(174 + i * 10), ad="piksel_ince", boyut=31, renk="mavi_acik")
            if t >= z["svalbard"]:
                # sinyal: uydudan yer istasyonuna kesik çizgi
                for k in range(0, 60, 4):
                    if (k // 4 + int(t * 8)) % 3:
                        d.point((CX + 50 - k // 6, 154 + k), fill=P["altin"])
                konum_pimi(d, CX + 40, 222, yanip(t, 0.5))
                yk.yaz("SVALBARD, NORVEÇ", R(CX + 30), R(212), "sag", ad="piksel", boyut=39, renk="gumus")
            satirlar = [("sira", "SIRADA: ISI + RADYASYON TESTİ"), ("y2027", "2027: İKİ UYDUYLA DENEME")]
            for i, (k, metin) in enumerate(satirlar):
                if t < z[k]:
                    continue
                y = 232 + i * 18
                d.rectangle([4, y, GEN - 5, y + 14], fill=P["zemin3"], outline=P["altin"] if k == "y2027" else P["cizgi"])
                ikon(d, I.MADDE, 8, y + 4, 1)
                yk.yaz(metin, R(16), R(y) + 12, ad="piksel", boyut=39, renk="gumus")
        kaynak(yk, self.ctx["kaynak"])


# ------------------------------------------------------------------ Bölüm 8 (yayın 7) · HARİTAM: SPONSOR CORTEX (çok yakında)
class HaritamCortex(Sahne):
    def maskot_yol(self):
        z = self.z()
        return [(0.0, *M(150), "sevin"), (z["vertex"], *M(190), "isaret"), (z["peki"], *M(110), "dusun"),
                (z["ozet"], *M(140), "isaret"), (z["analiz"], *M(170), "isaret"), (z["oneri"], *M(200), "isaret"),
                (z["yani"], *M(236), "sevin"), (z["tesekkur"], *M(262), "selam"), (self.sure - 1.6, *DINLEN, "levelup!")]

    def z(self):
        return {"cortex": self.kt("Cortex"), "vertex": self.kt("Vertex"), "yakin": self.kt("çok", tam=True),
                "peki": self.kt("Peki"), "ozet": self.kt("özet", tam=True), "analiz": self.kt("analiz"),
                "oneri": self.kt("önerileri"), "yani": self.kt("Yani"), "tesekkur": self.kt("teşekkürler")}

    def olaylar(self):
        z = self.z()
        return [(0.2, "blip"), (z["cortex"], "coin"), (z["vertex"], "tik"), (z["yakin"], "blip"),
                (z["peki"], "glitch"), (z["ozet"], "coin"), (z["analiz"], "coin"), (z["oneri"], "coin"),
                (z["yani"], "tik"), (z["tesekkur"], "blip"), (self.sure - 1.6, "levelup")]

    GUCLER = [("ozet", "KONU ÖZETİ", "HER KONUYA"), ("analiz", "YANLIŞ ANALİZİ", "HATANI ÇÖZ"),
              ("oneri", "KİŞİSEL ÖNERİ", "SANA ÖZEL")]

    def _beyin(self, d, cx, cy, t):
        """Piksel yapay zekâ çekirdeği: altın çip + etrafında dönen mavi düğümler."""
        d.rectangle([cx - 14, cy - 14, cx + 13, cy + 13], fill=P["zemin2"], outline=P["altin"], width=2)
        for k in range(4):
            for s in (-1, 1):
                d.rectangle([cx - 11 + k * 7, cy + s * 16 - 1, cx - 9 + k * 7, cy + s * 16 + 1], fill=P["altin_koyu"])
                d.rectangle([cx + s * 16 - 1, cy - 11 + k * 7, cx + s * 16 + 1, cy - 9 + k * 7], fill=P["altin_koyu"])
        bant_dikdortgen(d, cx - 8, cy - 8, 16, 16, BANT["altin"])
        a0 = adim(t, 8) * 1.6
        for k in range(3):
            a = a0 + k * 2.094
            daire(d, cx + int(math.cos(a) * 28), cy + int(math.sin(a) * 28), 2,
                  P["mavi_buz"] if k == int(t * 3) % 3 else P["mavi_acik"])

    def ciz(self, t, d, yk):
        z = self.z()
        if t < z["peki"]:
            yk.yaz("SPONSOR", RCX, R(100), "orta", ad="piksel_ince", boyut=39, renk="soluk")
            self._beyin(d, CX, 148, t)
            if t >= z["cortex"]:
                yk.yaz("CORTEX", RCX, R(186), "orta", ad="piksel", boyut=95, bant="altin", kenar=6)
            if t >= z["vertex"]:
                yk.yaz("VERTEX'İN YAPAY ZEKÂSI", RCX, R(214), "orta", ad="piksel", boyut=47, renk="beyaz", kenar=4)
            if t >= z["yakin"]:
                renk = P["altin"] if yanip(t, 0.6, 0.7) else P["altin_koyu"]
                d.rectangle([CX - 70, 232, CX + 70, 252], fill=P["zemin2"], outline=renk)
                yk.yaz("ÇOK YAKINDA · HARİTAM'DA", RCX, R(236), "orta", ad="piksel", boyut=39, renk="gumus")
            return
        x0, y0, w = 0, 80, GEN
        panel(d, x0, y0, w, 206)
        dugme(d, x0 + 2, y0 + 2, w - 4, 20)
        yk.yaz("YKS HARİTAM + CORTEX", R(CX), R(y0 + 2) + 10, "orta", ad="piksel", boyut=47, renk="beyaz")
        yk.yaz("YENİ GÜÇLER: ÇOK YAKINDA", R(x0 + 4), R(y0 + 25), ad="piksel", boyut=39, renk="altin")
        for i, (k, ad, alt) in enumerate(self.GUCLER):
            if t < z[k]:
                continue
            y = y0 + 40 + i * 32
            d.rectangle([x0 + 6, y, x0 + w - 7, y + 28], fill=P["zemin3"],
                        outline=P["altin"] if yanip(t - z[k], 0.5) and t - z[k] < 1.5 else P["cizgi"])
            # numaralı güç kutusu
            dugme(d, x0 + 10, y + 5, 18, 18)
            yk.yaz(str(i + 1), R(x0 + 19), R(y + 5) + 14, "orta", ad="piksel", boyut=55, renk="beyaz")
            yk.yaz(ad, R(x0 + 34), R(y) + 6, ad="piksel", boyut=47, renk="gumus")
            yk.yaz(alt, R(x0 + 34), R(y) + 70, ad="piksel_ince", boyut=31, renk="soluk")
            ikon(d, I.KILIT, x0 + w - 20, y + 11, 1)
        if t >= z["yani"]:
            ikon(d, I.TIK, x0 + 12, y0 + 141, 2)
            yk.yaz("PLAN + YAPAY ZEKÂ DESTEĞİ", R(x0 + 30), R(y0 + 140), ad="piksel", boyut=39, renk="beyaz")
        if t >= z["tesekkur"]:
            d.rectangle([x0 + 6, y0 + 158, x0 + w - 7, y0 + 182], fill=P["zemin2"], outline=P["altin"])
            yk.yaz("TEŞEKKÜRLER CORTEX!", RCX, R(y0 + 161), "orta", ad="piksel", boyut=55, bant="altin", kenar=4)
        if t >= self.sure - 1.6:
            yk.yaz("LEVEL UP!", RCX, R(y0 + 192), "orta", ad="ingilizce_etiket", boyut=40, bant="altin")



# ------------------------------------------------------------------ Bölüm 9 (yayın 8) · ortak: takvim yaprağı
def takvim_ciz(d, yk, x, y, w, h, gun, ay, alt=None, parla=False):
    """Piksel takvim yaprağı: mavi üst bant (ay) + gümüş gövde (gün) + spiral halkalar."""
    d.rectangle([x + 3, y + 3, x + w + 2, y + h + 2], fill=P["zemin3"])                # piksel gölge
    d.rectangle([x, y, x + w - 1, y + h - 1], fill=P["gumus"], outline=P["altin"] if parla else P["gumus_koyu"])
    dugme(d, x, y, w, 14)
    for k in range(3):
        hx = x + w // 4 + k * (w // 4) - 1
        d.rectangle([hx, y - 3, hx + 2, y + 3], fill=P["gumus_koyu"])
    yk.yaz(ay, R(x + w // 2), R(y) + 12, "orta", ad="piksel", boyut=31, renk="beyaz")
    yk.yaz(gun, R(x + w // 2), R(y + 15), "orta", ad="piksel", boyut=95 if h >= 50 else 71,
           renk="zemin", kenar=0)
    if alt:
        yk.yaz(alt, R(x + w // 2), R(y + h - 11), "orta", ad="piksel_ince", boyut=31, renk="mavi_koyu", kenar=0)


def laptop_ciz(d, x, y, s=1):
    """Piksel dizüstü bilgisayar (sol üst köşe x,y; 16x11 * s)."""
    d.rectangle([x + 2 * s, y, x + 14 * s - 1, y + 8 * s - 1], fill=P["cizgi"])
    d.rectangle([x + 3 * s, y + s, x + 13 * s - 1, y + 7 * s - 1], fill=P["mavi_acik"])
    d.rectangle([x + 4 * s, y + 2 * s, x + 9 * s - 1, y + 3 * s - 1], fill=P["mavi"])
    d.rectangle([x, y + 8 * s, x + 16 * s - 1, y + 10 * s - 1], fill=P["gumus_koyu"])
    d.rectangle([x + 6 * s, y + 8 * s, x + 10 * s - 1, y + 9 * s - 1], fill=P["soluk"])


# ------------------------------------------------------------------ Bölüm 9 (yayın 8) · HABER: ÖSYM 2027 TAKVİMİ
class HaberOsym(Sahne):
    def z(self):
        return {"osym": self.kt("ÖSYM"), "tyt": self.kt("TYT"), "ayt": self.kt("AYT"), "basvuru": self.kt("Başvurular"),
                "sonuc": self.kt("Sonuçların"), "geri": self.kt("Kısacası"), "ay": self.kt("yedi"),
                "hafta": self.kt("haftalara", varsayilan=1e9), "yaz": self.kt("Tarihleri")}

    def maskot_yol(self):
        z = self.z()
        return [(0.0, *M(113), "isaret"), (z["tyt"], *M(150), "isaret"), (z["ayt"], *M(170), "isaret"),
                (z["basvuru"], *M(206), "isaret"), (z["sonuc"], *M(222), "isaret"), (z["geri"], *M(240), "saskin"),
                (z["ay"], *M(258), "isaret"), (z["yaz"], *M(258), "sevin!")]

    def olaylar(self):
        z = self.z()
        return [(z["osym"], "blip"), (z["tyt"], "coin"), (z["ayt"], "coin"), (z["basvuru"], "tik"),
                (z["sonuc"], "tik"), (z["geri"], "glitch"), (z["ay"], "blip"), (z["hafta"], "tik"), (z["yaz"], "levelup")]

    def ciz(self, t, d, yk):
        z = self.z()
        etiket(d, yk, "TÜRKİYE", "28 EKİM", rozet="TR")
        baslik_kutusu(d, yk, ["ÖSYM 2027 TAKVİMİ", "YKS TARİHİ BELLİ!"])
        if t >= z["tyt"]:
            takvim_ciz(d, yk, CX - 84, 142, 70, 54, "19", "HAZİRAN", "CUMARTESİ", parla=t < z["ayt"] and yanip(t, 0.5))
            yk.yaz("TYT", R(CX - 49), R(198) + 4, "orta", ad="piksel", boyut=47, bant="altin", kenar=3)
        if t >= z["ayt"]:
            takvim_ciz(d, yk, CX + 14, 142, 70, 54, "20", "HAZİRAN", "PAZAR", parla=t < z["basvuru"] and yanip(t, 0.5))
            yk.yaz("AYT + YDT", R(CX + 49), R(198) + 4, "orta", ad="piksel", boyut=47, bant="altin", kenar=3)
        if t < z["tyt"]:
            takvim_ciz(d, yk, CX - 35, 142, 70, 54, "?", "2027", None)
        satirlar = [("basvuru", "BAŞVURU: 4 ŞUBAT - 2 MART", "gumus"),
                    ("sonuc", "SONUÇ: 21 TEMMUZ (PLAN)", "gumus"),
                    ("ay", "BÜYÜK GÜNE ~7,5 AY VAR", "altin")]
        for i, (k, metin, r) in enumerate(satirlar):
            if t < z[k]:
                continue
            y = 212 + i * 15
            d.rectangle([4, y, GEN - 5, y + 13], fill=P["zemin3"], outline=P["altin"] if k == "ay" else P["cizgi"])
            ikon(d, I.MADDE, 8, y + 4, 1)
            yk.yaz(metin, R(16), R(y) + 10, ad="piksel", boyut=39, renk=r)
        if t >= z["yaz"]:
            d.rectangle([4, 258, GEN - 5, 279], fill=P["zemin2"], outline=P["altin"])
            yk.yaz("TAKVİMİNE YAZ!", RCX, R(259), "orta", ad="piksel", boyut=55, bant="altin", kenar=4)
        elif t >= z["hafta"]:
            d.rectangle([4, 258, GEN - 5, 279], fill=P["zemin2"], outline=P["mavi"])
            yk.yaz("HAFTALARA BÖL, PLANLA", RCX, R(261), "orta", ad="piksel", boyut=39, renk="beyaz")
        elif t >= z["geri"]:
            renk = "kirmizi" if yanip(t, 0.5) else "beyaz"
            d.rectangle([4, 258, GEN - 5, 279], fill=P["zemin2"], outline=P["cizgi"])
            yk.yaz("GERİ SAYIM BAŞLADI!", RCX, R(261), "orta", ad="piksel", boyut=47, renk=renk)
        kaynak(yk, self.ctx["kaynak"])


# ------------------------------------------------------------------ Bölüm 9 (yayın 8) · HABER: GOOGLE DEEPMIND GENIE 4
class HaberGenie(Sahne):
    def z(self):
        return {"google": self.kt("Google"), "cumle": self.kt("cümle"), "olus": self.kt("oluşturuyor"),
                "klavye": self.kt("Klavyeyle"), "karakter": self.kt("karakterler"), "muzik": self.kt("Müzik"),
                "ustelik": self.kt("Üstelik"), "oyun": self.kt("oyunlar"), "simdi": self.kt("Şimdilik"),
                "uzun": self.kt("uzun")}

    def maskot_yol(self):
        z = self.z()
        return [(0.0, *M(113), "saskin"), (z["cumle"], *M(140), "isaret"), (z["olus"], *M(170), "sevin"),
                (z["klavye"], *M(180), "isaret"), (z["muzik"], *M(150), "sevin"), (z["ustelik"], *M(140), "isaret"),
                (z["oyun"], *M(212), "isaret"), (z["simdi"], *M(228), "isaret"), (z["uzun"], *M(244), "dusun"),
                (z["uzun"] + 3.0, *DINLEN, None)]

    def olaylar(self):
        z = self.z()
        o = [(z["google"], "blip"), (z["olus"], "glitch"), (z["olus"] + 0.3, "coin"), (z["klavye"], "tik"),
             (z["karakter"], "blip"), (z["muzik"], "coin"), (z["ustelik"], "glitch"), (z["oyun"], "tik"),
             (z["simdi"], "tik"), (z["uzun"], "blip")]
        for i in range(6):
            o.append((z["cumle"] + 0.2 + i * 0.12, "blip"))
        return o

    def _dunya(self, d, t, oran, yagmur):
        x0, y0, w, h = 6, 152, GEN - 12, 50
        d.rectangle([x0, y0, x0 + w - 1, y0 + h - 1], fill=P["zemin"] if yagmur else P["zemin3"], outline=P["mavi"])
        m = dither_maske(w // 2 + 1, h // 2 + 1, oran)
        # dağlar + yer + ağaçlar (dither ile beliriyor)
        for i in range(w):
            tepe = y0 + 18 + int(8 * math.sin(i * 0.09) + 4 * math.sin(i * 0.23))
            for y in range(tepe, y0 + h - 12):
                if m[(y - y0) // 2, i // 2]:
                    d.point((x0 + i, y), fill=P["mavi_koyu"] if y < tepe + 3 else P["cizgi"])
        for i in range(0, w, 2):
            if m[(h - 12) // 2, i // 2]:
                d.rectangle([x0 + i, y0 + h - 12, x0 + i + 1, y0 + h - 2], fill=P["zemin2"])
        d.rectangle([x0 + 1, y0 + h - 12, x0 + w - 2, y0 + h - 12], fill=P["mavi"] if oran >= 1 else P["cizgi"])
        if oran >= 1:
            for ax in (24, 70, 140, 172):
                d.rectangle([x0 + ax, y0 + h - 18, x0 + ax + 1, y0 + h - 13], fill=P["altin_koyu"])
                d.rectangle([x0 + ax - 3, y0 + h - 26, x0 + ax + 4, y0 + h - 18], fill=P["mavi_acik"])
            if not yagmur:
                daire(d, x0 + w - 22, y0 + 10, 4, P["altin"])
        if yagmur:
            for k in range(26):
                rx = x0 + 3 + (k * 37 + int(t * 50)) % (w - 6)
                ry = y0 + 2 + (k * 13 + int(t * 90)) % (h - 16)
                d.line([rx, ry, rx, ry + 2], fill=P["mavi_buz"])

    def ciz(self, t, d, yk):
        z = self.z()
        etiket(d, yk, "DÜNYA", "27 EKİM", ikon_sablon=I.KURE)
        baslik_kutusu(d, yk, ["GENIE 4: BİR CÜMLE YAZ,", "DÜNYA OLUŞSUN!"])
        # komut kutusu
        if t >= z["cumle"]:
            yagmur = t >= z["ustelik"]
            komut = "> yağmur yağsın" if yagmur else "> gece, dağlar, orman"
            n = int((t - (z["ustelik"] if yagmur else z["cumle"])) / 0.08)
            d.rectangle([6, 137, GEN - 7, 149], fill=P["zemin"], outline=P["altin"] if yagmur else P["mavi_acik"])
            imlec = "_" if yanip(t, 0.5) else ""
            yk.yaz(komut[:n] + imlec, R(10), R(137) + 8, ad="piksel", boyut=39, renk="altin" if yagmur else "mavi_acik")
        if t >= z["olus"]:
            oran = min(1.0, adim(t - z["olus"], 8) / 1.0)
            self._dunya(d, t, oran, t >= z["ustelik"])
            if t >= z["klavye"]:
                # klavyeyle yürüyen oyuncu
                px = 20 + int(adim(t - z["klavye"], 6) * 14) % 150
                py = 152 + 50 - 20
                d.rectangle([px, py, px + 4, py + 3], fill=P["altin"])
                d.rectangle([px, py + 4, px + 4, py + 7], fill=P["mavi"])
                d.rectangle([px + (int(t * 6) % 2), py + 8, px + 1 + (int(t * 6) % 2), py + 8], fill=P["gumus"])
                d.rectangle([px + 3 - (int(t * 6) % 2), py + 8, px + 4 - (int(t * 6) % 2), py + 8], fill=P["gumus"])
                for i, tus in enumerate(["W", "A", "S", "D"]):
                    kx = GEN - 52 + i * 11
                    d.rectangle([kx, 187, kx + 9, 196], fill=P["zemin2"], outline=P["gumus_koyu"])
                    yk.yaz(tus, R(kx + 5), R(187) + 6, "orta", ad="ingilizce_etiket", boyut=20, renk="gumus")
            if t >= z["karakter"]:
                d.rectangle([12, 158, 74, 170], fill=P["gumus"])
                yk.yaz("Merhaba!", R(43), R(158) + 6, "orta", ad="piksel", boyut=31, renk="zemin", kenar=0)
            if t >= z["muzik"]:
                for k in range(3):
                    nx = 90 + k * 14
                    ny = 160 + int(3 * math.sin(t * 6 + k))
                    d.rectangle([nx, ny, nx + 2, ny + 2], fill=P["altin"])
                    d.rectangle([nx + 2, ny - 6, nx + 2, ny], fill=P["altin"])
                yk.yaz("SES + MÜZİK", R(132), R(158) + 4, ad="piksel_ince", boyut=31, renk="altin")
        satirlar = [("oyun", "OYUN · ÖĞRENME · ROBOT", "gumus"),
                    ("simdi", "ŞİMDİLİK SADECE TEST EKİBİ", "gumus"),
                    ("uzun", "UZUN OTURUMDA DETAY KAYABİLİR", "soluk")]
        for i, (k, metin, r) in enumerate(satirlar):
            if t < z[k]:
                continue
            y = 214 + i * 15
            d.rectangle([4, y, GEN - 5, y + 13], fill=P["zemin3"], outline=P["cizgi"])
            ikon(d, I.MADDE, 8, y + 4, 1)
            yk.yaz(metin, R(16), R(y) + 10, ad="piksel", boyut=39, renk=r)
        kaynak(yk, self.ctx["kaynak"])


# ------------------------------------------------------------------ Bölüm 9 (yayın 8) · HARİTAM: ÜCRETSİZ, HER CİHAZDA
class HaritamCihaz(Sahne):
    def z(self):
        return {"bolum": self.kt("Bugünkü"), "plan": self.kt("Çünkü"), "ucret": self.kt("ücretsiz"),
                "tel": self.kt("telefonuna"), "okul": self.kt("Okul"), "ev": self.kt("Evde"),
                "aksam": self.kt("Akşam"), "hafta": self.kt("Haftalık"), "sinav": self.kt("Sınava")}

    def maskot_yol(self):
        z = self.z()
        return [(0.0, *M(130), "sevin"), (z["bolum"], *M(150), "isaret"), (z["ucret"], *M(180), "sevin"),
                (z["tel"], *M(220), "isaret"), (z["okul"], *M(130), "isaret"), (z["ev"], *M(170), "isaret"),
                (z["aksam"], *M(210), "isaret"), (z["hafta"], *M(236), "isaret"), (z["sinav"], *M(262), "sevin"),
                (self.sure - 1.6, *DINLEN, "levelup!")]

    def olaylar(self):
        z = self.z()
        return [(0.2, "blip"), (z["bolum"], "glitch"), (z["plan"], "tik"), (z["ucret"], "coin"), (z["tel"], "coin"),
                (z["okul"], "tik"), (z["ev"], "tik"), (z["aksam"], "tik"), (z["hafta"], "coin"),
                (z["sinav"], "blip"), (self.sure - 1.6, "levelup")]

    SAHNE = [("okul", "SABAH · OKUL YOLU", "BUGÜNKÜ GÖREVLER", "tel"),
             ("ev", "EVDE · BİLGİSAYAR", "DENEME NETLERİ", "pc"),
             ("aksam", "AKŞAM · TELEFON", "ODAK SAYACI", "tel")]

    def ciz(self, t, d, yk):
        z = self.z()
        if t < z["okul"]:
            yk.yaz("HARİTAM BÖLÜMÜ", RCX, R(92), "orta", ad="piksel_ince", boyut=39, renk="soluk")
            if t >= z["bolum"]:
                panel(d, 10, 104, GEN - 20, 34)
                yk.yaz("LEVEL: HER YERDE", RCX, R(108), "orta", ad="piksel", boyut=47, renk="beyaz")
                yk.yaz("HARİTAM", RCX, R(120), "orta", ad="piksel", boyut=55, bant="altin", kenar=4)
            if t >= z["ucret"]:
                yk.yaz("ÜCRETSİZ", RCX, R(146), "orta", ad="piksel", boyut=95, bant="altin", kenar=6)
            if t >= z["tel"]:
                ikon(d, I.TELEFON, CX - 52, 182, 6)
                # ana ekrana eklenen Haritam uygulama simgesi
                s = min(1.0, adim(t - z["tel"], 8) / 0.8)
                ax, ay = CX - 52 + 9, 182 + 9
                d.rectangle([ax, ay, ax + 21, ay + 21], fill=P["mavi"] if s >= 1 else P["mavi_koyu"],
                            outline=P["mavi_acik"])
                yk.yaz("YKS", R(ax + 11), R(ay + 5), "orta", ad="piksel", boyut=31, renk="beyaz")
                d.rectangle([CX - 2, 194, CX + 96, 218], fill=P["zemin2"], outline=P["altin"] if yanip(t, 0.6) else P["cizgi"])
                yk.yaz("+ UYGULAMA OLARAK", R(CX + 47), R(195) + 2, "orta", ad="piksel_ince", boyut=31, renk="gumus")
                yk.yaz("EKLE", R(CX + 47), R(205) + 2, "orta", ad="piksel", boyut=39, renk="altin")
                laptop_ciz(d, CX + 10, 226, 3)
                yk.yaz("+ BİLGİSAYAR", R(CX + 34), R(258), "orta", ad="piksel", boyut=39, renk="gumus")
            return
        x0, y0, w = 0, 80, GEN
        panel(d, x0, y0, w, 206)
        dugme(d, x0 + 2, y0 + 2, w - 4, 20)
        yk.yaz("YKS HARİTAM · HER CİHAZDA", R(CX), R(y0 + 2) + 10, "orta", ad="piksel", boyut=39, renk="beyaz")
        for i, (k, ust_, alt, cihaz) in enumerate(self.SAHNE):
            if t < z[k]:
                continue
            y = y0 + 26 + i * 34
            yeni = t - z[k] < 1.2
            d.rectangle([x0 + 6, y, x0 + w - 7, y + 30], fill=P["zemin3"],
                        outline=P["altin"] if yeni and yanip(t, 0.4) else P["cizgi"])
            if cihaz == "tel":
                ikon(d, I.TELEFON, x0 + 12, y + 5, 2)
            else:
                laptop_ciz(d, x0 + 9, y + 9, 1)
                laptop_ciz(d, x0 + 9, y + 7, 1)
            yk.yaz(ust_, R(x0 + 34), R(y) + 8, ad="piksel_ince", boyut=31, renk="soluk")
            yk.yaz(alt, R(x0 + 34), R(y) + 52, ad="piksel", boyut=47, renk="gumus")
            if not yeni:
                ikon(d, I.TIK, x0 + w - 20, y + 11, 1)
        if t >= z["hafta"]:
            cy = y0 + 132
            for j, (ad, x, ww) in enumerate([("PROGRAM", 6, 56), ("ÖZETLER", 66, 56), ("YANLIŞ DEFTERİ", 126, w - 133)]):
                if t < z["hafta"] + j * 0.6:
                    continue
                dugme(d, x0 + x, cy, ww, 14)
                yk.yaz(ad, R(x0 + x + ww // 2), R(cy) + 12, "orta", ad="piksel_ince", boyut=31, renk="beyaz")
        if t >= z["sinav"]:
            d.rectangle([x0 + 6, y0 + 154, x0 + w - 7, y0 + 180], fill=P["zemin2"], outline=P["altin"])
            yk.yaz("PLANIN CEBİNDE!", RCX, R(y0 + 158), "orta", ad="piksel", boyut=55, bant="altin", kenar=4)
        if t >= self.sure - 1.6:
            yk.yaz("LEVEL UP!", RCX, R(y0 + 190), "orta", ad="ingilizce_etiket", boyut=40, bant="altin")


# ------------------------------------------------------------------ Bölüm 10 (yayın 9) · ortak: uyuyan robot
def zzz(d, yk, x, y, t, boyut=47, yukselis=22):
    """Robotun üstünde yükselen piksel Z'ler (altın/buz)."""
    for k in range(3):
        f = (t * 0.8 + k / 3) % 1.0
        zx = x + k * 9 + int(f * 6)
        zy = y - int(f * yukselis) - k * 4
        yk.yaz("Z", R(zx), R(zy), "orta", ad="piksel", boyut=boyut - k * 8,
               renk="mavi_buz" if k % 2 else "altin", kenar=3)


def uyuyan_robot(d, yk, x, y, s, t, uyku=True, yukselis=22):
    """ROBOT ikonu; uyku=True iken gözler kapalı (çizgi) ve Z'ler çıkar."""
    ikon(d, I.ROBOT, x, y, s)
    if uyku:
        for gx in (4, 7):                      # gözleri kapat: 6 -> çizgi
            d.rectangle([x + gx * s, y + 4 * s, x + (gx + 1) * s - 1, y + 5 * s - 1], fill=P["gumus_koyu"])
            d.rectangle([x + gx * s, y + 4 * s + s // 2, x + (gx + 1) * s - 1, y + 5 * s - 1], fill=P["zemin3"])
        zzz(d, yk, x + 10 * s + 4, y + 2 * s, t, yukselis=yukselis)


# ------------------------------------------------------------------ Bölüm 10 (yayın 9) · HABER: SİRİ'YE TÜRKÇE
class HaberSiri(Sahne):
    DILLER = [("FR", 0), ("ES", 1), ("JA", 2), ("KO", 3), ("PT", 4)]

    def z(self):
        return {"apple": self.kt("Apple"), "turkce": self.kt("Türkçe"), "ilk": self.kt("açıldığında"),
                "son": self.kt("Son", tam=True), "beta": self.kt("şimdilik"), "sira": self.kt("Sıradaki"),
                "kesin": self.kt("Kesin"), "yani": self.kt("Yani", 1)}

    def maskot_yol(self):
        z = self.z()
        return [(0.0, *M(113), "isaret"), (z["ilk"], *M(146), "isaret"), (z["son"], *M(164), "isaret"),
                (z["beta"], *M(196), "dusun"), (z["sira"], *M(214), "sevin"), (z["kesin"], *M(232), "dusun"),
                (z["yani"], *M(258), "sevin!")]

    def olaylar(self):
        z = self.z()
        o = [(z["apple"], "blip"), (z["turkce"], "coin"), (z["ilk"], "tik"), (z["beta"], "tik"),
             (z["sira"], "glitch"), (z["sira"] + 0.4, "coin"), (z["kesin"], "blip"), (z["yani"], "levelup")]
        for i in range(5):
            o.append((z["son"] + 0.3 + i * 0.35, "blip"))
        return o

    def ciz(self, t, d, yk):
        z = self.z()
        etiket(d, yk, "TÜRKİYE", "27 EKİM", rozet="TR")
        baslik_kutusu(d, yk, ["YENİ SİRİ", "TÜRKÇE KONUŞACAK!"])
        # telefon + ses dalgası
        px, py = 6, 140
        ikon(d, I.TELEFON, px, py, 6)
        for k in range(5):
            hk = 2 + int(abs(math.sin(t * 7 + k * 1.3)) * 9)
            d.rectangle([px + 10 + k * 5, py + 30 - hk // 2, px + 12 + k * 5, py + 30 + hk // 2],
                        fill=P["mavi_acik"] if k % 2 else P["altin"])
        # dil çipleri
        gx, gy = 58, 142
        def cip(i, kod, renk, cerceve, yazi_renk="beyaz"):
            x = gx + (i % 4) * 35
            y = gy + (i // 4) * 18
            d.rectangle([x, y, x + 31, y + 14], fill=renk, outline=cerceve)
            yk.yaz(kod, R(x + 16), R(y) + 10, "orta", ad="piksel", boyut=47, renk=yazi_renk)
        if t >= z["ilk"]:
            cip(0, "EN", P["mavi"], P["mavi_acik"])
        for kod, i in self.DILLER:
            if t >= z["son"] + 0.3 + i * 0.35:
                cip(i + 1, kod, P["mavi_koyu"], P["cizgi"])
        if t >= z["sira"]:
            parla = yanip(t, 0.4)
            x, y = gx + 2 * 35, gy + 18
            d.rectangle([x, y, x + 66, y + 14], fill=P["zemin2"], outline=P["altin"] if parla else P["altin_koyu"])
            yk.yaz("TR · SIRADA", R(x + 33), R(y) + 10, "orta", ad="piksel", boyut=39, bant="altin")
        if t >= z["beta"]:
            d.rectangle([gx, 182, gx + 40, 193], fill=P["zemin3"], outline=P["mavi_acik"])
            yk.yaz("BETA", R(gx + 20), R(182) + 6, "orta", ad="ingilizce_etiket", boyut=24, renk="mavi_acik")
        satirlar = [("sira", "4 YENİ DİL · BİRİ TÜRKÇE", "gumus"),
                    ("kesin", "KESİN TARİH: HENÜZ YOK", "soluk")]
        for i, (k, metin, r) in enumerate(satirlar):
            if t < z[k]:
                continue
            y = 214 + i * 15
            d.rectangle([4, y, GEN - 5, y + 13], fill=P["zemin3"], outline=P["cizgi"])
            ikon(d, I.MADDE, 8, y + 4, 1)
            yk.yaz(metin, R(16), R(y) + 10, ad="piksel", boyut=39, renk=r)
        if t >= z["yani"]:
            d.rectangle([4, 248, GEN - 5, 276], fill=P["zemin2"], outline=P["altin"])
            yk.yaz("YIL SONUNA KADAR", RCX, R(250), "orta", ad="piksel_ince", boyut=39, renk="gumus")
            yk.yaz("\"MERHABA SİRİ!\"", RCX, R(261), "orta", ad="piksel", boyut=55, bant="altin", kenar=4)
        kaynak(yk, self.ctx["kaynak"])


# ------------------------------------------------------------------ Bölüm 10 (yayın 9) · HABER: YAPAY ZEKÂYA UYKU
class HaberUyku(Sahne):
    def z(self):
        return {"google": self.kt("Google"), "uyku": self.kt("uyku"), "sorun": self.kt("Sorun"),
                "unut": self.kt("unutabiliyor"), "yikici": self.kt("yıkıcı"), "cozum": self.kt("Çözüm"),
                "uyanik": self.kt("Uyanıkken"), "uykuda": self.kt("Uykuda"), "kalici": self.kt("kalıcı"),
                "alistirma": self.kt("alıştırma"), "ruya": self.kt("rüya"), "insan": self.kt("insan"),
                "test": self.kt("Testlerde")}

    def maskot_yol(self):
        z = self.z()
        return [(0.0, *M(113), "isaret"), (z["uyku"], *M(150), "saskin"), (z["unut"], *M(170), "dusun"),
                (z["uyanik"], *M(150), "isaret"), (z["uykuda"], *M(190), "isaret"), (z["alistirma"], *M(214), "isaret"),
                (z["ruya"], *M(228), "sevin"), (z["test"], *M(258), "sevin!")]

    def olaylar(self):
        z = self.z()
        return [(z["google"], "blip"), (z["uyku"], "coin"), (z["sorun"], "tik"), (z["unut"], "glitch"),
                (z["yikici"], "blip"), (z["cozum"], "tik"), (z["uyanik"], "blip"), (z["uykuda"], "coin"),
                (z["kalici"], "tik"), (z["alistirma"], "blip"), (z["ruya"], "coin"), (z["test"], "levelup")]

    def _hafiza(self, d, yk, x, y, w, etiket_, dolu, renk, baslik_renk):
        d.rectangle([x, y, x + w - 1, y + 22], fill=P["zemin3"], outline=P["cizgi"])
        yk.yaz(etiket_, R(x + w // 2), R(y) + 4, "orta", ad="piksel_ince", boyut=31, renk=baslik_renk)
        for i in range(dolu):
            bx = x + 4 + i * 8
            if bx + 6 > x + w - 3:
                break
            d.rectangle([bx, y + 12, bx + 5, y + 18], fill=P[renk])

    def ciz(self, t, d, yk):
        z = self.z()
        etiket(d, yk, "DÜNYA", "27 EKİM", ikon_sablon=I.KURE)
        baslik_kutusu(d, yk, ["YAPAY ZEKÂYA", "UYKU DÖNEMİ!"])
        if t < z["cozum"]:
            # robot + bilgiler: yeni kutu gelince eskiler dökülüp kayboluyor
            uyuyan_robot(d, yk, CX - 30, 142, 5, t, uyku=t < z["sorun"])
            if t >= z["sorun"]:
                for k in range(4):
                    f = ((t - z["sorun"]) * 0.7 + k / 4) % 1.0
                    bx = CX + 36 + k * 6
                    by = 150 + int(f * 60)
                    renk = P["altin"] if k == 0 else P["mavi_acik"]
                    if t >= z["unut"] and k > 0:
                        renk = P["cizgi"] if yanip(t + k * 0.1, 0.4) else P["mavi_koyu"]
                    d.rectangle([bx, by, bx + 4, by + 4], fill=renk)
                yk.yaz("YENİ +1", R(CX + 42), R(138), "orta", ad="piksel", boyut=39, renk="altin")
            if t >= z["unut"]:
                yk.yaz("ESKİLER -3", R(CX - 60), R(200), "orta", ad="piksel", boyut=39,
                       renk="kirmizi" if yanip(t, 0.5) else "soluk")
            if t >= z["yikici"]:
                d.rectangle([4, 214, GEN - 5, 232], fill=P["zemin2"], outline=P["kirmizi"])
                yk.yaz("YIKICI UNUTMA", RCX, R(216), "orta", ad="piksel", boyut=55, renk="beyaz", kenar=4)
        else:
            # iki aşama: UYANIK | UYKU
            uyku = t >= z["uykuda"]
            panel(d, 4, 136, 94, 74)
            panel(d, 102, 136, GEN - 106, 74)
            yk.yaz("UYANIK", R(51), R(138) + 6, "orta", ad="piksel", boyut=39, renk="mavi_acik" if not uyku else "soluk")
            yk.yaz("UYKU", R(102 + (GEN - 106) // 2), R(138) + 6, "orta", ad="piksel", boyut=39,
                   bant="altin" if uyku else None, renk="soluk")
            if t >= z["uyanik"]:
                uyuyan_robot(d, yk, 30, 152, 3, t, uyku=False)
                self._hafiza(d, yk, 8, 186, 86, "KISA SÜRELİ", 3 if not uyku else 1, "mavi_acik", "gumus")
            if uyku:
                uyuyan_robot(d, yk, 132, 152, 3, t, uyku=True)
                dolu = 2 + (int(adim(t - z["kalici"], 4) * 4) if t >= z["kalici"] else 0)
                self._hafiza(d, yk, 106, 186, GEN - 114, "KALICI", min(dolu, 10), "altin", "altin")
            satirlar = [("alistirma", "KENDİNE ALIŞTIRMA ÜRETİR", "gumus"),
                        ("ruya", "BUNA \"RÜYA\" DİYORLAR", "altin")]
            for i, (k, metin, r) in enumerate(satirlar):
                if t < z[k]:
                    continue
                y = 214 + i * 15
                d.rectangle([4, y, GEN - 5, y + 13], fill=P["zemin3"], outline=P["altin"] if k == "ruya" else P["cizgi"])
                ikon(d, I.MADDE, 8, y + 4, 1)
                yk.yaz(metin, R(16), R(y) + 10, ad="piksel", boyut=39, renk=r)
            if t >= z["test"]:
                d.rectangle([4, 248, GEN - 5, 276], fill=P["zemin2"], outline=P["altin"])
                yk.yaz("TESTLERDE", RCX, R(250), "orta", ad="piksel_ince", boyut=39, renk="gumus")
                yk.yaz("ÇOK DAHA AZ UNUTTU", RCX, R(261), "orta", ad="piksel", boyut=55, bant="altin", kenar=4)
            elif t >= z["insan"]:
                d.rectangle([4, 248, GEN - 5, 276], fill=P["zemin2"], outline=P["mavi"])
                yk.yaz("İLHAM: İNSAN UYKUSU", RCX, R(256), "orta", ad="piksel", boyut=47, renk="beyaz")
        kaynak(yk, self.ctx["kaynak"])


# ------------------------------------------------------------------ Bölüm 10 (yayın 9) · HARİTAM: HAFTALIK PROGRAM
class HaritamProgram(Haritam):
    """Bölüm 1'in haftalık program arayüzü, yeni giriş (LEVEL: HAFTANI PLANLA) ve yeni sıra."""

    def zamanlar(self):
        return {"bolum": self.kt("Bugünkü"), "yz": self.kt("Yapay"), "senin": self.kt("Senin"),
                "kayit": self.kt("Kayıt"), "excel": self.kt("Excel"), "kendin": self.kt("kendin"),
                "gorev": self.kt("Görevler"), "tik": self.kt("bitirdikçe"), "konu": self.kt("Programındaki"),
                "uyku": self.kt("uykunu")}

    def maskot_yol(self):
        z = self.zamanlar()
        return [(0.0, *M(130), "sevin"), (z["bolum"], *M(150), "isaret"), (z["yz"], *M(200), "dusun"),
                (z["senin"], *M(220), "sevin"), (z["excel"], *M(110), "isaret"), (z["gorev"], *M(150), "isaret"),
                (z["konu"], *M(214), "isaret"), (z["uyku"], *M(240), "sevin"), (self.sure - 1.6, *DINLEN, "levelup!")]

    def olaylar(self):
        z = self.zamanlar()
        o = [(0.2, "blip"), (z["bolum"], "glitch"), (z["yz"], "tik"), (z["senin"], "coin"), (z["kayit"], "tik"),
             (z["excel"], "glitch"), (z["kendin"], "tik")]
        for i, _ in enumerate(self.gorevler()):
            if i % 2 == 0:
                o.append((z["gorev"] + i * 0.1, "tik"))
        for i in range(8):
            o.append((z["tik"] + i * 0.18, "blip"))
        o += [(z["konu"], "coin"), (z["uyku"], "blip"), (self.sure - 1.6, "levelup")]
        return o

    def ciz(self, t, d, yk):
        z = self.zamanlar()
        if t < z["excel"]:
            yk.yaz("HARİTAM BÖLÜMÜ", RCX, R(92), "orta", ad="piksel_ince", boyut=39, renk="soluk")
            if t >= z["bolum"]:
                panel(d, 10, 104, GEN - 20, 34)
                yk.yaz("LEVEL: HAFTANI PLANLA", RCX, R(108), "orta", ad="piksel", boyut=47, renk="beyaz")
                yk.yaz("HARİTAM", RCX, R(120), "orta", ad="piksel", boyut=55, bant="altin", kenar=4)
            if t >= z["yz"]:
                uyuyan_robot(d, yk, CX - 18, 156, 3, t, uyku=True, yukselis=10)
                yk.yaz("UYKU + TEKRAR = KALICI", RCX, R(194), "orta", ad="piksel", boyut=39, renk="gumus")
            if t >= z["senin"]:
                d.rectangle([4, 204, GEN - 5, 224], fill=P["zemin2"], outline=P["altin"])
                yk.yaz("SENİN DÜZENİN: HARİTAM", RCX, R(207), "orta", ad="piksel", boyut=47, bant="altin", kenar=4)
            if t >= z["kayit"]:
                for j, (ad, x, w) in enumerate([("ALANIN", 8, 88), ("HEDEF PUANIN", 100, GEN - 108)]):
                    if t < z["kayit"] + j * 0.7:
                        continue
                    dugme(d, x, 232, w, 16)
                    yk.yaz(ad, R(x + w // 2), R(232) + 14, "orta", ad="piksel", boyut=39, renk="beyaz")
                yk.yaz("PLANIN BUNA GÖRE ŞEKİLLENİR", RCX, R(256), "orta", ad="piksel_ince", boyut=31, renk="soluk")
            return
        self._uygulama2(d, yk, t, z)

    def _uygulama2(self, d, yk, t, z):
        x0, y0, w = 0, 80, GEN
        panel(d, x0, y0, w, 206)
        dugme(d, x0 + 2, y0 + 2, w - 4, 20)
        yk.yaz("YKS HARİTAM", R(CX), R(y0 + 2) + 10, "orta", ad="piksel", boyut=47, renk="beyaz")
        yk.yaz("HAFTALIK PROGRAM", R(x0 + 4), R(y0 + 25), ad="piksel", boyut=39, renk="altin")
        dugme(d, x0 + 112, y0 + 23, 40, 12)
        yk.yaz("EXCEL", R(x0 + 132), R(y0 + 23) + 6, "orta", ad="piksel", boyut=31, renk="beyaz")
        if t >= z["kendin"]:
            d.rectangle([x0 + 156, y0 + 23, x0 + w - 5, y0 + 34], fill=P["zemin3"], outline=P["mavi_acik"])
            yk.yaz("YAZ", R(x0 + 156 + (w - 161) // 2), R(y0 + 23) + 6, "orta", ad="piksel", boyut=31, renk="mavi_acik")
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
        if t >= z["tik"]:
            oran = min(8, int((t - z["tik"]) / 0.18) + 1) / len(self.gorevler())
            yk.yaz("HAFTA", R(x0 + 4), R(y0 + 108) + 4, ad="piksel", boyut=39, renk="gumus")
            xp_bar(d, x0 + 40, y0 + 110, w - 46, oran)
        if t >= z["konu"]:
            ky = y0 + 128
            d.rectangle([x0 + 4, ky, x0 + w - 5, ky + 14], fill=P["zemin3"], outline=P["mavi"])
            ikon(d, I.TIK, x0 + 8, ky + 4, 1)
            yk.yaz("TYT/AYT ÖZETLERİYLE EŞLEŞTİ", R(x0 + 18), R(ky) + 12, ad="piksel", boyut=39, renk="gumus")
        if t >= z["uyku"]:
            cy = y0 + 150
            d.rectangle([x0 + 4, cy, x0 + w - 5, cy + 26], fill=P["zemin2"], outline=P["altin"])
            yk.yaz("TEKRARI HAFTAYA YAY", R(CX), R(cy) + 10, "orta", ad="piksel", boyut=47, bant="altin")
            yk.yaz("UYKUNU İHMAL ETME", R(CX), R(cy) + 58, "orta", ad="piksel_ince", boyut=31, renk="gumus")
        if t >= self.sure - 1.6:
            yk.yaz("LEVEL UP!", RCX, R(y0 + 182), "orta", ad="ingilizce_etiket", boyut=40, bant="altin")


SAHNELER = {"kanca": Kanca, "acilis": Acilis, "haber_meb": HaberMEB, "haber_jaxa": HaberJAXA,
            "haritam": Haritam, "cta": Kapanis,
            "haber_veri": HaberVeri, "haber_slides": HaberSlides, "haritam_ozet": HaritamOzet,
            "haber_dolandirici": HaberDolandirici, "haber_specs": HaberSpecs, "haritam_test": HaritamTest,
            "php_ne": PhpNe, "php_neden": PhpNeden, "php_yapilacak": PhpYapilacak, "haritam_deneme": HaritamDeneme,
            "haber_prompt": HaberPrompt, "haber_swift": HaberSwift, "haritam_yanlis": HaritamYanlis,
            "haber_navigasyon": HaberNavigasyon, "haber_artemis": HaberArtemis, "haritam_odak": HaritamOdak,
            "haber_ari": HaberAri, "haber_kanit": HaberKanit, "haritam_kurum": HaritamKurum,
            "haber_vertex": HaberVertex, "haber_suncatcher": HaberSuncatcher, "haritam_cortex": HaritamCortex,
            "haber_osym": HaberOsym, "haber_genie": HaberGenie, "haritam_cihaz": HaritamCihaz,
            "haber_siri": HaberSiri, "haber_uyku": HaberUyku, "haritam_program": HaritamProgram}
