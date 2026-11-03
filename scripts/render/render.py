"""Video render (CLAUDE.md §3.4, §4, §8, §9 — Python + Pillow + FFmpeg).

Girdi : bolumler/NNN/senaryo.json, bolumler/NNN/ses/*.json (tts.py çıktısı)
Çıktı : bolumler/NNN/ara/zaman.json   (sahne zamanları + efekt olayları; birlestir.py kullanır)
        bolumler/NNN/ara/video.mp4    (sessiz görüntü)
        bolumler/NNN/kapak.png

Kullanım:
  python scripts/render/render.py --bolum 1
  python scripts/render/render.py --bolum 1 --kareler 0,30,60   # sadece önizleme kareleri
"""
import argparse
import json
import subprocess
import sys
from datetime import date
from pathlib import Path

import numpy as np
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from ortak import ayarlar, bolum_dizini, senaryo  # noqa: E402
from cizim import (SOL, SAG, Kaydir, OLCEK, P, SH, SW, YaziKatmani, dither_maske, glitch, ikon, xp_bar,  # noqa: E402
                   yeni_kare, yildizlar, yazi, yazi_genislik)
import ikonlar as I  # noqa: E402
import maskot  # noqa: E402
from sahneler import SAHNELER, logo, sade

RCX = SW * OLCEK // 2  # ekranın tam ortası (içerik simetrik boşluklu)  # noqa: E402

FPS = 30
GIRIS = {"kanca": 0.3, "acilis": 1.6}   # sahne başından sese kadar bekleme
ARA = 0.4                               # ses bitimi -> sonraki sahne
KAPANIS_KUYRUK = 4.0                    # son sesten sonra GAME SAVED + jingle
GECIS = 0.27                            # sahne geçişi (dither + glitch)


# ------------------------------------------------------------------ zaman çizelgesi
def zaman_cizelgesi(no):
    sen = senaryo(no)
    ses_dir = bolum_dizini(no) / "ses"
    t = 0.0
    sahneler = []
    for i, b in enumerate(sen["bolumler"]):
        ses = json.loads((ses_dir / f"{b['id']}.json").read_text(encoding="utf-8"))
        giris = GIRIS.get(b["id"], 0.35)
        ses_bas = t + giris
        ses_son = ses_bas + ses["sure"]
        son_mu = i == len(sen["bolumler"]) - 1
        bitis = ses_son + (KAPANIS_KUYRUK if son_mu else ARA)
        sahneler.append({
            "id": b["id"], "sahne": b["sahne"], "bas": round(t, 3), "son": round(bitis, 3),
            "ses_bas": round(ses_bas, 3), "ses_son": round(ses_son, 3),
            "kelimeler": [{"k": k["k"], "bas": k["bas"] + giris, "son": k["son"] + giris} for k in ses["kelimeler"]],
        })
        t = bitis
    return sen, sahneler, t


def sahne_nesneleri(sen, sahneler, handle):
    nesneler = []
    for s in sahneler:
        ctx = {"sure": s["son"] - s["bas"], "kelimeler": s["kelimeler"], "bolum": sen.get("yayin_no", sen["bolum"]),  # yayın sırası (özel bölümler sayılmaz)
               "ses_son": s["ses_son"] - s["bas"], "kaynak": sen.get("kaynak_satirlari", {}).get(s["id"], ""),
               "handle": handle, "kanca": sen.get("kanca"), "ozel": sen.get("ozel", False),
               "sponsor": sen.get("sponsor")}
        nesneler.append(SAHNELER[s["sahne"]](ctx))
    return nesneler


def olaylar(sahneler, nesneler):
    out = []
    for i, (s, n) in enumerate(zip(sahneler, nesneler)):
        if i > 0:
            out.append({"t": s["bas"], "efekt": "glitch"})
        for t, ef in n.olaylar():
            out.append({"t": round(s["bas"] + t, 3), "efekt": ef})
    return sorted(out, key=lambda o: o["t"])


# ------------------------------------------------------------------ altyazı (§8)
SATIR_MAX = 16
ALTYAZI_BOYUT = 67   # VT323 100px (font pikseli = 1 sanal piksel)
MASKOT_ACIK = maskot.var_mi()
# Arpi sol kenarda dolaşır; altyazı ortada kalır, sol kenara taşmayacak genişlikte kırılır
ALTYAZI_CX = RCX
ALTYAZI_MAX_G = (SAG - SOL - 20) * OLCEK


def altyazi_sayfalari(sahneler, vurgu):
    vurgu_s = {sade(v) for v in vurgu}
    sayfalar = []
    for s in sahneler:
        kel = [dict(k, abs_bas=k["bas"] + s["bas"], abs_son=k["son"] + s["bas"]) for k in s["kelimeler"]]
        satirlar, satir = [], []
        sayfa = []

        def satir_kapat():
            nonlocal satir
            if satir:
                sayfa.append(satir)
            satir = []

        for k in kel:
            metin = " ".join(x["k"] for x in satir + [k])
            if satir and (len(metin) > SATIR_MAX or yazi_genislik(metin, "piksel", ALTYAZI_BOYUT) > ALTYAZI_MAX_G):
                satir_kapat()
                if len(sayfa) == 2:
                    sayfalar.append(sayfa)
                    sayfa = []
            satir.append(k)
            # cümle sonunda sayfayı kapat
            if k["k"][-1] in ".?!" and len(" ".join(x["k"] for x in sum(sayfa, []) + satir)) > 12:
                satir_kapat()
                sayfalar.append(sayfa)
                sayfa = []
        satir_kapat()
        if sayfa:
            sayfalar.append(sayfa)
    out = []
    for i, sy in enumerate(sayfalar):
        ilk = sy[0][0]["abs_bas"]
        son = sy[-1][-1]["abs_son"]
        out.append({"bas": ilk, "son": son,
                    "satirlar": [[(k["k"], sade(k["k"]) in vurgu_s, k["abs_bas"]) for k in st] for st in sy]})
    for i in range(len(out) - 1):  # kısa boşluklarda sayfa ekranda kalsın
        if out[i + 1]["bas"] - out[i]["son"] < 0.6:
            out[i]["son"] = out[i + 1]["bas"]
        else:
            out[i]["son"] += 0.3
    return out


def altyazi_ciz(yk, sayfa, t):
    # sprite'lar kenar için her yanda 7px pay taşır
    bosluk = yazi_genislik("a a", "piksel", ALTYAZI_BOYUT) - 2 * yazi_genislik("a", "piksel", ALTYAZI_BOYUT) + 4 - 14
    y0 = 1196 if len(sayfa["satirlar"]) == 2 else 1240
    for j, satir in enumerate(sayfa["satirlar"]):
        sprite = [yazi(k, "piksel", ALTYAZI_BOYUT, renk="altin" if v else "gumus", kenar=6) for k, v, _ in satir]
        toplam = sum(s.width for s in sprite) + bosluk * (len(sprite) - 1)
        x = ALTYAZI_CX - toplam // 2
        for s, (_, _, kb) in zip(sprite, satir):
            if t >= kb - 0.05:  # kelime söylenince belirir
                yk.ekle(s, x, y0 + j * 92)
            x += s.width + bosluk


# ------------------------------------------------------------------ HUD ve alt bilgi
def hud(d, yk, t, toplam, tarih):
    d.rectangle([SOL, 56, SAG - 1, 70], fill=P["zemin2"], outline=P["cizgi"])
    logo_mini(yk)
    yk.yaz(tarih, (SAG - 4) * OLCEK, 56 * OLCEK + 18, "sag", ad="piksel_ince", boyut=35, renk="soluk")
    yk.yaz("XP", SOL * OLCEK, 72 * OLCEK - 4, ad="piksel_ince", boyut=27, renk="mavi_acik")
    xp_bar(d, SOL + 10, 72, SAG - SOL - 10, t / toplam)


def logo_mini(yk):
    logo_dosya = Path(__file__).resolve().parents[2] / "brand" / "arpama-logo.png"
    if logo_dosya.exists():
        logo(yk, (SOL + 4) * OLCEK + 120, 57 * OLCEK, 40)
        return
    yk.yaz("AR", (SOL + 4) * OLCEK, 56 * OLCEK + 14, ad="marka", boyut=34, bant="altin")
    yk.yaz("PAMA", (SOL + 4) * OLCEK + yazi("AR", "marka", 34, bant="altin").width + 2, 56 * OLCEK + 14,
           ad="marka", boyut=34, bant="gumus")


def alt_bilgi(d, yk):
    d.rectangle([SOL, 372, SAG - 1, 372], fill=P["cizgi"])
    yk.yaz("haritam.arpama.tr", RCX, 374 * OLCEK + 4, "orta", ad="piksel_ince", boyut=31, renk="mavi_acik")


# ------------------------------------------------------------------ kare üretimi
def tr_tarih(gun):
    return gun.strftime("%d.%m.%Y")


class Render:
    def __init__(self, no, tarih=None):
        self.ayar = ayarlar()
        handle = self.ayar.get("instagram", {}).get("handle", "")
        handle = handle if handle and "<" not in handle else None
        self.sen, self.sahneler, self.toplam = zaman_cizelgesi(no)
        ses_json = next(iter(sorted((bolum_dizini(no) / "ses").glob("*.json"))), None)
        maskot.ayarla(json.loads(ses_json.read_text(encoding="utf-8")).get("ses") if ses_json else None)
        self.nesneler = sahne_nesneleri(self.sen, self.sahneler, handle)
        self.sayfalar = altyazi_sayfalari(self.sahneler, self.sen.get("vurgu_kelimeleri", []))
        self.tarih = tarih or tr_tarih(date.today())
        self.scan = float(self.ayar["video"].get("scanline_opaklik", 0.12))

    def sahne_bul(self, t):
        for i, s in enumerate(self.sahneler):
            if t < s["son"] or i == len(self.sahneler) - 1:
                return i, s
        return len(self.sahneler) - 1, self.sahneler[-1]

    def kare(self, t):
        i, s = self.sahne_bul(t)
        lt = t - s["bas"]
        im, d = yeni_kare()
        yildizlar(d, t, hiz=6 if s["sahne"] == "haber_jaxa" else 1.5, tohum=7)
        yk = YaziKatmani()
        hud(d, yk, t, self.toplam, self.tarih)
        yk_sahne = YaziKatmani(dx=SOL * OLCEK)
        self.nesneler[i].ciz(lt, Kaydir(d, SOL), yk_sahne)
        if not (i > 0 and lt < GECIS / 2):  # geçişin ilk yarısında sahne yazıları gizli
            yk.ops += yk_sahne.ops
        alt_bilgi(d, yk)
        if MASKOT_ACIK:
            konusuyor = any(k["bas"] - 0.02 <= lt < k["son"] for k in s["kelimeler"])
            mx, my, anim = maskot.yol_durumu(self.nesneler[i].maskot_yol(), lt, konusuyor)
            maskot.ciz(im, SOL + mx, my, anim, t)
        for sy in self.sayfalar:
            if sy["bas"] - 0.05 <= t < sy["son"]:
                altyazi_ciz(yk, sy, t)
                break
        arr = np.asarray(im)
        if i > 0 and lt < GECIS:
            oran = lt / GECIS
            arr = glitch(arr, 1 - oran, int(t * FPS))
            m = dither_maske(SW, SH, oran)
            arr = np.where(m[..., None], arr, np.array(P["zemin"], dtype=np.uint8))
        buyuk = np.repeat(np.repeat(arr, OLCEK, axis=0), OLCEK, axis=1)
        img = Image.fromarray(np.ascontiguousarray(buyuk), "RGB")
        yk.uygula(img)
        out = np.asarray(img).copy()
        out[OLCEK - 1::OLCEK] = (out[OLCEK - 1::OLCEK] * (1 - self.scan)).astype(np.uint8)  # CRT scanline
        return out

    def video(self, yol):
        n = int(round(self.toplam * FPS))
        cmd = ["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
               "-s", f"{SW * OLCEK}x{SH * OLCEK}", "-r", str(FPS), "-i", "-",
               "-c:v", "libx264", "-preset", "medium", "-crf", "17", "-pix_fmt", "yuv420p",
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
        """1080x1920 kapak: logo + başlık + roket + bölüm etiketi (profil ızgarası için orta 3:4 alanda)."""
        k = self.sen.get("kapak", {})
        im, d = yeni_kare()
        yildizlar(d, 0.3, tohum=7, adet=110)
        d.rectangle([10, 66, SW - 11, 413], outline=P["cizgi"])
        d.rectangle([12, 68, SW - 13, 70], fill=P["mavi"])
        if k.get("ikon") == "sunucu":
            for j in range(3):
                ikon(d, I.SUNUCU, SW // 2 - 37 + j * 26, 296, 2)
        elif k.get("ikon") == "php":
            d.rectangle([SW // 2 - 40, 290, SW // 2 + 40, 342], fill=P["zemin2"], outline=P["cizgi"])
            for i in range(4):
                d.rectangle([SW // 2 - 32 + (i % 2) * 6, 302 + i * 9, SW // 2 - 32 + (i % 2) * 6 + 20 + i * 9, 304 + i * 9],
                            fill=P["altin"] if i == 1 else P["gumus_koyu"])
            d.line([(SW // 2 + 4, 290), (SW // 2 - 6, 308), (SW // 2 + 6, 318), (SW // 2 - 2, 342)], fill=P["kirmizi"], width=2)
        elif k.get("ikon") == "robot":
            ikon(d, I.ROBOT, SW // 2 - 24, 290, 4)
            for j, (dx, dy) in enumerate([(-44, 300), (36, 294), (-38, 330), (40, 326)]):
                d.rectangle([SW // 2 + dx, dy, SW // 2 + dx + 5, dy + 5], fill=P["altin"], outline=P["altin_koyu"])
        elif k.get("ikon") == "uyku":
            ikon(d, I.ROBOT, SW // 2 - 24, 290, 4)
            for gx in (4, 7):
                d.rectangle([SW // 2 - 24 + gx * 4, 306, SW // 2 - 24 + gx * 4 + 3, 309], fill=P["zemin3"])
                d.rectangle([SW // 2 - 24 + gx * 4, 306, SW // 2 - 24 + gx * 4 + 3, 307], fill=P["gumus_koyu"])
            for j, (dx, dy, r) in enumerate([(30, 292, "altin"), (40, 282, "mavi_buz"), (50, 272, "altin")]):
                zx, zy, zs = SW // 2 + dx, dy, 6 - j
                d.line([(zx, zy), (zx + zs, zy), (zx, zy + zs), (zx + zs, zy + zs)], fill=P[r], width=2)
        elif k.get("ikon") == "telefon":
            ikon(d, I.TELEFON, SW // 2 - 14, 292, 4)
            d.rectangle([SW // 2 + 10, 286, SW // 2 + 21, 297], fill=P["kirmizi"])
        else:
            ikon(d, I.ROKET, SW // 2 - 11, 300, 2)
            ikon(d, I.ALEV_2, SW // 2 - 9, 332, 2)
        yk = YaziKatmani()
        cx = SW * OLCEK // 2
        logo(yk, cx, 330, 150)
        ust_boyut = 150
        while ust_boyut > 60 and yazi_genislik(k.get("ust", ""), "piksel", ust_boyut) > 900:
            ust_boyut -= 10
        yk.yaz(k.get("ust", ""), cx, 650, "orta", ad="piksel", boyut=ust_boyut, bant="altin", kenar=8)
        for j, satir in enumerate(k.get("alt_satirlar", [])):
            yk.yaz(satir, cx, 930 + j * 115, "orta", ad="piksel", boyut=71, renk="beyaz", kenar=8)
        yk.yaz(k.get("bolum_etiketi", ""), cx, 1450, "orta", ad="marka", boyut=110, bant="altin")
        yk.yaz("ARPAMA TEKNOLOJİ GÜNDEMİ", cx, 1590, "orta", ad="piksel", boyut=47, renk="soluk")
        arr = np.asarray(im)
        img = Image.fromarray(np.repeat(np.repeat(arr, OLCEK, 0), OLCEK, 1), "RGB")
        yk.uygula(img)
        img.save(yol)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--bolum", type=int, required=True)
    ap.add_argument("--tarih", help="HUD tarihi (GG.AA.YYYY), varsayılan bugün")
    ap.add_argument("--kareler", help="sadece bu saniyelerin karelerini PNG olarak çıkar (ör. 0,30,60)")
    args = ap.parse_args()
    r = Render(args.bolum, args.tarih)
    hedef = bolum_dizini(args.bolum)
    ara = hedef / "ara"
    ara.mkdir(parents=True, exist_ok=True)
    (ara / "zaman.json").write_text(json.dumps({
        "toplam": r.toplam,
        "sahneler": [{k: v for k, v in s.items() if k != "kelimeler"} for s in r.sahneler],
        "olaylar": olaylar(r.sahneler, r.nesneler),
    }, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"süre: {r.toplam:.1f} sn")
    if args.kareler:
        for s in args.kareler.split(","):
            Image.fromarray(r.kare(float(s))).save(ara / f"kare_{float(s):06.1f}.png")
        return
    r.kapak(hedef / "kapak.png")
    r.video(ara / "video.mp4")
    print("video ->", ara / "video.mp4")


if __name__ == "__main__":
    main()
