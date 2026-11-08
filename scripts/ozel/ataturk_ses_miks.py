"""10 Kasım özel bölümü: müzik, efektler ve son miks.

Müzik kodla üretilir (telif yok) ve 29 Ekim bölümünün enstrümanlarını kullanır, ama daha yavaş
(72 BPM) ve daha sakindir: re minörde müzik kutusu ve pad, "ışık" anlarında majöre açılan akorlar,
gökler bölümünde umutlu tema, kapanışta yarıya inmiş bayrakla ağır bir son akor.

Girdi : ozel/10kasim/ara/zaman.json, ozel/10kasim/ses/*.wav, ozel/10kasim/ara/video.mp4
Çıktı : ozel/10kasim/10kasim-ataturk.mp4  (--sessiz ile seslendirmesiz sürüm)
"""
import argparse
import json
import subprocess
import sys
from pathlib import Path

import numpy as np

KOK = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(KOK / "scripts"), str(KOK / "scripts" / "ozel")]
import cumhuriyet_ses_miks as CM  # noqa: E402
from cumhuriyet_ses_miks import (SR, TEMA_A, TEMA_B, akorlar, alcak, arpej, azalan, bas, ducking, ekle, gurultu,  # noqa: E402
                                 kare, kutu, lead, pad, tema, timpani, wav_yaz, yanki, yuksek, yuruyus, zarf, zil, frekans)

DIZIN = KOK / "ozel" / "10kasim"
CM.DIZIN = DIZIN
CM.VURUS = 60 / 72
CM.OLCU = 4 * CM.VURUS
RNG = np.random.default_rng(1938)


def sfx(ad):
    if ad == "tik":
        return alcak(kare(frekans(91), 0.015, 0.5) * azalan(int(0.015 * SR) + 1, 0.01)[: int(0.015 * SR)] * 0.25, 5000)
    if ad == "durak":
        return alcak(timpani(0.35, 31), 500)
    if ad == "isik":
        return pad([62, 69, 74, 78], 2.5, 0.07, atak=0.8)
    if ad == "tebesir":
        n = int(0.07 * SR)
        return yuksek(gurultu(0.07, RNG, 1)[:n], 2500) * np.sin(np.linspace(0, np.pi, n)) * 0.09
    if ad == "silgi":
        n = int(0.5 * SR)
        return alcak(gurultu(0.5, RNG, 1)[:n], 1800) * np.abs(np.sin(np.linspace(0, 12, n))) * 0.08
    if ad == "zil_okul":
        out = np.zeros(int(1.2 * SR))
        for k in range(6):
            ekle(out, kutu(88 if k % 2 else 84, 0.1), k * 0.12)
        return out
    if ad == "kalem_cizgi":
        n = int(0.35 * SR)
        return yuksek(gurultu(0.35, RNG, 1)[:n], 3500) * zarf(n, 0.05, 0.1) * 0.05
    if ad == "ucak":
        n = int(2.5 * SR)
        t = np.arange(n) / SR
        s = np.where((t * 38) % 1 < 0.5, 1.0, -1.0) * 0.5 + gurultu(2.5, RNG, 6)[:n] * 0.5
        return alcak(s, 600) * np.sin(np.linspace(0, np.pi, n)) ** 2 * 0.18
    if ad == "blip":
        return kutu(81, 0.1)
    return CM.sfx(ad)


def muzik(z):
    toplam = z["toplam"]
    s = {x["id"]: x for x in z["sahneler"]}
    ev = {}
    for o in z["olaylar"]:
        ev.setdefault((o["sahne"], o["efekt"]), []).append(o["t"])
    iz = {k: np.zeros(int((toplam + 4) * SR)) for k in ("pad", "bas", "lead", "kutu", "davul")}
    b = lambda a: s[a]["bas"]  # noqa: E731
    O = CM.OLCU

    # kanca: uzun re minör, "ışık"ta fa majöre açılır
    t_isik = ev[("kanca", "isik")][0]
    ekle(iz["pad"], pad([38, 45, 50, 53], t_isik + 0.5, 0.13, atak=2.5), 0)
    ekle(iz["bas"], bas(26, t_isik, 0.25), 0.3)
    ekle(iz["pad"], pad([41, 48, 53, 57, 60], b("acilis") - t_isik + 0.5, 0.15, atak=0.6), t_isik)
    # açılış: müzik kutusu motifi
    t0 = b("acilis")
    ekle(iz["pad"], pad([50, 57, 62, 65], b("ilim") - t0 + 0.4, 0.12, atak=0.5), t0)
    for k, n in enumerate((74, 77, 81, 79, 77, 74)):
        ekle(iz["kutu"], kutu(n, 0.13), t0 + 0.3 + k * CM.VURUS / 1.5)
    # ilim: müzik kutusu arpeji
    t0, t1 = b("ilim"), b("harf")
    arpej(iz, t0, t1, ["Dm", "Bb", "F", "C"], 0.09)
    akorlar(iz, t0, t1, ["Dm", "Bb", "F", "C"], 0.08, 0.22, (0,))
    # harf: daha aydınlık, Başöğretmen'de timpani + re majör
    t0, t_bas = b("harf"), ev[("harf", "muhur_buyuk")][0]
    arpej(iz, t0, t_bas - 0.2, ["F", "C", "Dm", "Bb"], 0.09)
    akorlar(iz, t0, t_bas - 0.2, ["F", "C", "Dm", "Bb"], 0.09, 0.25, (0, 2))
    ekle(iz["davul"], timpani(0.8, 38), t_bas)
    ekle(iz["davul"], zil(0.2, 2.5), t_bas)
    ekle(iz["pad"], pad([50, 54, 57, 62, 66], b("bilim") - t_bas + 0.3, 0.16, atak=0.05), t_bas)
    ekle(iz["lead"], lead(74, 2.4, 0.2), t_bas + 0.1)
    # bilim: ana tema, yumuşak
    t0, t1 = b("bilim"), b("gok")
    akorlar(iz, t0, t1, ["Dm", "Bb", "F", "A7"], 0.1, 0.3, (0, 2))
    tema(iz, t0 + O, t1 - 0.3, TEMA_A, 0.17)
    # gökler: umut teması (re majör), Çünkü'de hafif yürüyüş
    t0, t1, t_cun = b("gok"), b("kapanis"), ev[("gok", "ucak")][1]
    akorlar(iz, t0, t1, ["D", "G", "A", "D"], 0.12, 0.35, (0, 2))
    arpej(iz, t0, t_cun, ["D", "G", "A", "D"], 0.07)
    tema(iz, t_cun, t1 - 0.3, TEMA_B, 0.22)
    yuruyus(iz, t_cun, t1 - 0.3, 0.35)
    # kapanış: söz altında sadece pad, gençlerde müzik kutusu, anmada ağır son akor
    t0, t_bugun = b("kapanis"), ev[("kapanis", "blip")][0] - 1.0
    t_ulu, t_saygi = ev[("kapanis", "bayrak_acilis")][0], ev[("kapanis", "final")][0]
    ekle(iz["pad"], pad([38, 45, 50, 53], t_bugun - t0 + 0.5, 0.1, atak=1.5), t0)
    ekle(iz["bas"], bas(26, t_bugun - t0, 0.2), t0)
    arpej(iz, t_bugun, t_ulu - 0.2, ["D", "G", "Bb", "A"], 0.08)
    akorlar(iz, t_bugun, t_ulu - 0.2, ["D", "G", "Bb", "A"], 0.09, 0.25, (0,))
    ekle(iz["davul"], timpani(0.6, 38), t_ulu)
    ekle(iz["pad"], pad([38, 45, 50, 53, 57], t_saygi - t_ulu + 0.5, 0.14, atak=0.8), t_ulu)
    for v, sure, n in [(0, 1, 74), (1, 1, 72), (2, 2, 69)]:
        ekle(iz["lead"], lead(n, sure * CM.VURUS * 0.95, 0.18), t_ulu + 0.4 + v * CM.VURUS)
    son = toplam - t_saygi
    ekle(iz["pad"], pad([38, 50, 57, 62, 66, 69], son, 0.18, atak=0.3), t_saygi)
    ekle(iz["bas"], bas(26, son, 0.4), t_saygi)
    ekle(iz["lead"], lead(74, min(4.0, son - 0.5), 0.2), t_saygi + 0.3)

    karisim = (alcak(iz["pad"], 2200) + alcak(iz["lead"], 3500) * 0.85 + iz["bas"] * 0.8 +
               alcak(iz["kutu"], 6000) * 0.9 + iz["davul"] * 0.7)
    karisim = yanki(karisim, 2.4, 0.3)[: int(toplam * SR)]
    n = int(1.5 * SR)
    karisim[-n:] *= np.linspace(1, 0, n) ** 1.5
    return karisim / (np.max(np.abs(karisim)) + 1e-9) * 0.8


def efektler(z):
    iz = np.zeros(int((z["toplam"] + 3) * SR))
    kazanc = {"tik": 0.8, "tebesir": 0.8}
    for o in z["olaylar"]:
        ekle(iz, sfx(o["efekt"]), o["t"], kazanc.get(o["efekt"], 0.7))
    for sh in z["sahneler"][1:]:
        ekle(iz, sfx("gecis"), sh["bas"] - 0.6, 1.4)
    return yanki(iz, 1.2, 0.18)[: int(z["toplam"] * SR)]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--sessiz", action="store_true")
    args = ap.parse_args()
    z = json.loads((DIZIN / "ara" / "zaman.json").read_text(encoding="utf-8"))
    m = muzik(z)
    e = efektler(z)
    if args.sessiz:
        k, ad = m * 0.85 + e * 0.45, "10kasim-ataturk-seslendirmesiz.mp4"
    else:
        v = CM.konusma(z)
        v = v / (np.max(np.abs(v)) + 1e-9) * 0.9
        k, ad = v + m * ducking(v, -17, -8) + e * 0.35, "10kasim-ataturk.mp4"
    k = k / (np.max(np.abs(k)) + 1e-9) * 0.95
    miks = DIZIN / "ara" / ("miks_sessiz.wav" if args.sessiz else "miks.wav")
    wav_yaz(miks, k)
    cikti = DIZIN / ad
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", str(DIZIN / "ara" / "video.mp4"), "-i", str(miks),
                    "-af", "loudnorm=I=-14:TP=-1.5:LRA=11", "-c:v", "copy", "-c:a", "aac", "-b:a", "192k",
                    "-ar", "48000", "-shortest", "-movflags", "+faststart", str(cikti)], check=True)
    print("->", cikti)


if __name__ == "__main__":
    main()
