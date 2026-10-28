"""29 Ekim özel bölümü: film müziği, efektler ve son miks.

Müzik sahnelere göre bestelenir (kodla, telif yok): gece ve kalp atışıyla açılış, bayrakla küçük bir
fanfar, re minörde ağır bir yürüyüş (1919-1922), Erzurum defterinde müzik kutusu, İzmir'de ve
"Cumhuriyettir." cümlesinden sonra re majöre geçen ana tema. Chiptune sesleri yumuşatılır ve
hafif yankı eklenir; böylece oyun müziği değil, belgesel müziği gibi durur.

Girdi : ozel/29ekim/ara/zaman.json (render), ozel/29ekim/ses/*.wav, ozel/29ekim/ara/video.mp4
Çıktı : ozel/29ekim/29ekim-cumhuriyet.mp4 (ve --sessiz ile seslendirmesiz sürüm)

Kullanım:
  python scripts/ozel/cumhuriyet_ses_miks.py
  python scripts/ozel/cumhuriyet_ses_miks.py --sessiz      # sadece müzik + efekt
"""
import argparse
import json
import subprocess
import sys
import wave
from pathlib import Path

import numpy as np
from scipy.signal import butter, fftconvolve, sosfilt

KOK = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(KOK / "scripts"))
from muzik_uret import SR, azalan, frekans, gurultu, kare, ucgen, zarf  # noqa: E402

DIZIN = KOK / "ozel" / "29ekim"
BPM = 84
VURUS = 60 / BPM
OLCU = 4 * VURUS
RNG = np.random.default_rng(1923)

# akorlar (MIDI)
A = {"Dm": [50, 53, 57], "Bb": [46, 50, 53], "F": [53, 57, 60], "A": [45, 49, 52], "C": [48, 52, 55],
     "Gm": [43, 46, 50], "D": [50, 54, 57], "G": [43, 47, 50], "A7": [45, 49, 55]}
# ana tema (re minör) ve kurtuluş teması (re majör): (vuruş, süre, nota)
TEMA_A = [
    [(0, 1, 62), (1, .5, 65), (1.5, .5, 69), (2, 1.5, 74), (3.5, .5, 72)],
    [(0, 1, 70), (1, .5, 69), (1.5, .5, 67), (2, 2, 65)],
    [(0, 1, 69), (1, .5, 72), (1.5, .5, 69), (2, 1, 65), (3, 1, 67)],
    [(0, 1, 64), (1, 1, 67), (2, 2, 69)],
]
TEMA_B = [
    [(0, 1, 74), (1, .5, 69), (1.5, .5, 74), (2, 1.5, 78), (3.5, .5, 76)],
    [(0, 1, 74), (1, .5, 71), (1.5, .5, 74), (2, 2, 79)],
    [(0, 1, 76), (1, .5, 73), (1.5, .5, 76), (2, 1, 81), (3, 1, 79)],
    [(0, 1.5, 78), (1.5, .5, 76), (2, 2, 74)],
]
AKOR_A = ["Dm", "Bb", "F", "A7"]
AKOR_B = ["D", "G", "A", "D"]


# ---------------------------------------------------------------- enstrümanlar
def alcak(x, f, derece=2):
    return sosfilt(butter(derece, f, "low", fs=SR, output="sos"), x)


def yuksek(x, f, derece=2):
    return sosfilt(butter(derece, f, "high", fs=SR, output="sos"), x)


def ekle(iz, s, t, k=1.0):
    i = int(t * SR)
    if i < 0:
        s, i = s[-i:], 0
    if i >= len(iz):
        return
    j = min(len(iz), i + len(s))
    iz[i:j] += s[: j - i] * k


def lead(nota, sure, ses=0.3):
    n = int(sure * SR)
    t = np.arange(n) / SR
    f = frekans(nota) * (1 + 0.005 * np.sin(2 * np.pi * 5.5 * t) * np.clip((t - 0.18) * 4, 0, 1))
    faz = np.cumsum(f) / SR
    s = np.where(faz % 1 < 0.25, 1.0, -1.0) * 0.6 + (4 * np.abs(faz % 1 - 0.5) - 1) * 0.5
    return s * zarf(n, 0.012, min(0.12, sure / 3)) * ses


def pad(notalar, sure, ses=0.12, atak=0.35):
    n = int(sure * SR)
    s = np.zeros(n)
    for k, nota in enumerate(notalar):
        for det in (-0.06, 0.06):
            s += kare(frekans(nota + det), sure, duty=0.5, faz0=k * 0.13)[:n]
    s /= 2 * len(notalar)
    return s * zarf(n, atak, min(0.6, sure / 2)) * ses


def kutu(nota, ses=0.16):
    """müzik kutusu: kısa, sönümlü ince darbe"""
    sure = 0.9
    s = kare(frekans(nota), sure, duty=0.125) * 0.6 + ucgen(frekans(nota + 12), sure) * 0.4
    return s * azalan(len(s), 0.22) * zarf(len(s), 0.002, 0.05) * ses


def bas(nota, sure, ses=0.45):
    s = ucgen(frekans(nota), sure)
    return s * zarf(len(s), 0.01, 0.08) * ses


def timpani(ses=0.7, nota=38):
    sure = 1.2
    t = np.arange(int(sure * SR)) / SR
    f = frekans(nota) * (1 + 0.15 * np.exp(-t * 18))
    faz = np.cumsum(f) / SR
    s = np.sin(2 * np.pi * faz) * azalan(len(t), 0.35) + gurultu(sure, RNG, 8)[: len(t)] * azalan(len(t), 0.03) * 0.3
    return s * ses


def trampet(ses=0.22):
    n = int(0.16 * SR)
    g = yuksek(gurultu(0.16, RNG, 2)[:n], 900)
    return g * azalan(n, 0.05) * ses


def zil(ses=0.35, sure=3.0):
    n = int(sure * SR)
    g = yuksek(gurultu(sure, RNG, 1)[:n], 5000)
    return g * azalan(n, 0.9) * zarf(n, 0.003, 0.4) * ses


def kalp(ses=0.6):
    return np.concatenate([timpani(ses, 31)[: int(0.25 * SR)], np.zeros(int(0.08 * SR)), timpani(ses * 0.7, 31)[: int(0.3 * SR)]])


# ---------------------------------------------------------------- bölüm yardımcıları
def akorlar(iz, t0, t1, dizi, ses=0.12, bas_ses=0.4, bas_desen=(0, 2)):
    b = 0
    while t0 + b * OLCU < t1 - 0.1:
        ad = dizi[b % len(dizi)]
        ts = t0 + b * OLCU
        sure = min(OLCU, t1 - ts) + 0.3
        ekle(iz["pad"], pad([n + 12 for n in A[ad]], sure, ses), ts)
        for v in bas_desen:
            if ts + v * VURUS < t1:
                ekle(iz["bas"], bas(A[ad][0] - 12, VURUS * 1.8, bas_ses), ts + v * VURUS)
        b += 1


def tema(iz, t0, t1, motif, ses=0.28, oktav=0):
    b = 0
    while t0 + b * OLCU < t1 - 0.2:
        for v, s, n in motif[b % len(motif)]:
            ts = t0 + b * OLCU + v * VURUS
            if ts + 0.1 < t1:
                ekle(iz["lead"], lead(n + oktav, min(s * VURUS * 0.95, t1 - ts), ses), ts)
        b += 1


def arpej(iz, t0, t1, dizi, ses=0.14):
    b = 0
    while t0 + b * OLCU < t1 - 0.1:
        notalar = A[dizi[b % len(dizi)]]
        for k in range(8):
            ts = t0 + b * OLCU + k * VURUS / 2
            if ts < t1:
                n = notalar[[0, 1, 2, 1, 2, 0, 1, 2][k]] + 24 + (12 if k == 4 else 0)
                ekle(iz["kutu"], kutu(n, ses), ts)
        b += 1


def yuruyus(iz, t0, t1, guc=1.0):
    b = 0
    while t0 + b * OLCU < t1 - 0.1:
        ts = t0 + b * OLCU
        for k in range(8):
            t = ts + k * VURUS / 2
            if t >= t1:
                break
            if k in (0, 4):
                ekle(iz["davul"], timpani(0.35 * guc, 38), t)
            ekle(iz["davul"], trampet((0.16 if k % 2 else 0.1) * guc), t)
            if k == 7:
                for r in range(3):
                    ekle(iz["davul"], trampet(0.07 * guc), t + r * VURUS / 6)
        b += 1


def tremolo(iz, t0, t1, ses0=0.03, ses1=0.25):
    """timpani tremolosu (crescendo)"""
    t = t0
    while t < t1:
        u = (t - t0) / max(0.1, t1 - t0)
        ekle(iz["davul"], timpani(ses0 + (ses1 - ses0) * u ** 2, 38)[: int(0.3 * SR)], t)
        t += 0.075


# ---------------------------------------------------------------- efektler
def sfx(ad):
    if ad == "daktilo":
        out = np.zeros(int(1.2 * SR))
        for k in range(12):
            ekle(out, yuksek(gurultu(0.02, RNG, 1)[: int(0.02 * SR)], 2500) * azalan(int(0.02 * SR), 0.005) * 0.35,
                 k * 0.09 + RNG.uniform(0, 0.02))
        return out
    if ad in ("saat", "sayac"):
        out = np.zeros(int(1.4 * SR))
        n = 4 if ad == "saat" else 14
        for k in range(n):
            tik = kare(frekans(96 if k % 2 else 91), 0.012, 0.5) * 0.25
            ekle(out, alcak(tik, 6000), k * (0.35 if ad == "saat" else 0.09))
        return out
    if ad == "geri_sar":
        n = int(0.9 * SR)
        t = np.arange(n) / SR
        f = 900 * np.exp(-t * 2.2) + 80
        s = np.where((np.cumsum(f) / SR) % 1 < 0.5, 1.0, -1.0) * 0.12 + gurultu(0.9, RNG, 3)[:n] * 0.08
        return alcak(s * zarf(n, 0.02, 0.3), 4000)
    if ad in ("bayrak_acilis", "gecis"):
        n = int(1.6 * SR)
        g = alcak(gurultu(1.6, RNG, 1)[:n], 700) * np.sin(np.linspace(0, np.pi, n)) ** 2
        return g * (0.5 if ad == "bayrak_acilis" else 0.3)
    if ad in ("kagit", "parsomen"):
        n = int(0.5 * SR)
        g = yuksek(gurultu(0.5, RNG, 1)[:n], 1500) * np.abs(np.sin(np.linspace(0, 9, n))) * zarf(n, 0.05, 0.2)
        return g * 0.18
    if ad == "isgal":
        return alcak(timpani(0.25, 33), 400)
    if ad == "pim":
        return kutu(86, 0.12)
    if ad == "alinti":
        return pad([38, 45, 50], 2.0, 0.08, atak=0.6)
    if ad == "kalem":
        n = int(0.09 * SR)
        return yuksek(gurultu(0.09, RNG, 1)[:n], 3000) * np.sin(np.linspace(0, np.pi, n)) * 0.06
    if ad == "kapak":
        s = alcak(timpani(0.45, 40), 900)
        ekle(s, alcak(gurultu(0.1, RNG, 2)[: int(0.1 * SR)], 1500) * 0.25, 0)
        return s
    if ad in ("muhur", "muhur_buyuk"):
        s = alcak(timpani(0.6 if ad == "muhur" else 0.9, 36), 1200)
        if ad == "muhur_buyuk":
            s = s.copy()
            ekle(s, zil(0.25, 1.1)[: len(s)], 0)
        return s
    if ad == "kilic":
        n = int(0.6 * SR)
        s = sum(kare(frekans(n_), 0.6, 0.5)[: n] for n_ in (88, 95, 100)) / 3
        return alcak(s * azalan(n, 0.12), 5000) * 0.12
    if ad == "taarruz":
        out = np.zeros(int(1.0 * SR))
        for k in range(10):
            ekle(out, trampet(0.05 + k * 0.02), k * 0.08)
        return out
    if ad == "zafer":
        return zil(0.3, 2.5)
    if ad == "taht":
        out = np.zeros(int(1.5 * SR))
        for k, n_ in enumerate((79, 76, 72, 67)):
            ekle(out, kutu(n_, 0.12), k * 0.18)
        return out
    if ad == "top":
        n = int(1.1 * SR)
        g = alcak(gurultu(1.1, RNG, 4)[:n], 260) * azalan(n, 0.22) * 1.4
        return g + timpani(0.5, 28)[:n] * 0.6
    if ad == "fisek":
        out = np.zeros(int(1.5 * SR))
        ekle(out, alcak(gurultu(0.25, RNG, 2)[: int(0.25 * SR)], 900) * azalan(int(0.25 * SR), 0.06) * 0.5, 0)
        for k in range(14):
            ekle(out, yuksek(gurultu(0.012, RNG, 1)[: int(0.012 * SR)], 3000) * 0.12, 0.25 + RNG.uniform(0, 1.0))
        return out
    if ad == "final":
        return zil(0.2, 3.0)
    return np.zeros(10)


# ---------------------------------------------------------------- yankı
def yanki(x, sure=1.8, islak=0.22):
    n = int(sure * SR)
    ir = RNG.standard_normal(n) * np.exp(-np.arange(n) / (0.32 * SR))
    ir = alcak(ir, 5000)
    ir /= np.sqrt(np.sum(ir ** 2))
    return x * (1 - islak) + fftconvolve(x, ir)[: len(x)] * islak * 1.6


# ---------------------------------------------------------------- ana
def oku_wav(yol):
    out = subprocess.run(["ffmpeg", "-v", "error", "-i", str(yol), "-f", "f32le", "-ac", "1", "-ar", str(SR), "-"],
                         capture_output=True, check=True).stdout
    return np.frombuffer(out, dtype=np.float32).astype(np.float64)


def wav_yaz(yol, s):
    s = np.clip(s, -1, 1)
    with wave.open(str(yol), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes((s * 32767).astype("<i2").tobytes())


def muzik(z):
    toplam = z["toplam"]
    s = {x["id"]: x for x in z["sahneler"]}
    ev = {}
    for o in z["olaylar"]:
        ev.setdefault((o["sahne"], o["efekt"]), []).append(o["t"])
    iz = {k: np.zeros(int((toplam + 4) * SR)) for k in ("pad", "bas", "lead", "kutu", "davul")}
    bas_ = lambda a: s[a]["bas"]  # noqa: E731

    # 1. kanca: gece, kalp atışı, uzun re minör
    ekle(iz["pad"], pad([38, 45, 50, 53], bas_("acilis") + 0.4, 0.16, atak=2.5), 0)
    t = 0.6
    while t < bas_("acilis") - 1.2:
        ekle(iz["davul"], kalp(0.5), t)
        t += 2 * VURUS * 1.2
    # 2. açılış: küçük fanfar (re majör)
    t0 = bas_("acilis")
    ekle(iz["davul"], timpani(0.6, 38), t0)
    ekle(iz["pad"], pad([62, 66, 69, 74], bas_("y1919") - t0, 0.15, atak=0.05), t0)
    for v, sure, n in [(0, .5, 62), (.5, .5, 69), (1, 1, 74), (2, 2.5, 78)]:
        ekle(iz["lead"], lead(n, sure * VURUS, 0.26), t0 + 0.15 + v * VURUS)
    ekle(iz["bas"], bas(38, 3.5, 0.4), t0)
    # 3. 1918-1919: re minör yürüyüş, Amasya sözünde müzik durur
    t0, t_al = bas_("y1919"), ev[("y1919", "alinti")][0]
    akorlar(iz, t0, t_al - 0.3, AKOR_A, 0.11, 0.35)
    yuruyus(iz, t0 + OLCU, t_al - 0.3, 0.55)
    tema(iz, t0 + 2 * OLCU, t_al - 0.3, TEMA_A, 0.22)
    ekle(iz["pad"], pad([50, 57, 62, 65], bas_("defter") - t_al + 0.8, 0.14, atak=1.2), t_al - 0.3)
    ekle(iz["bas"], bas(38, bas_("defter") - t_al, 0.3), t_al - 0.3)
    # 4. Erzurum defteri: müzik kutusu
    t0 = bas_("defter")
    arpej(iz, t0, bas_("y1920"), ["Dm", "Bb", "Gm", "A"], 0.12)
    akorlar(iz, t0, bas_("y1920"), ["Dm", "Bb", "Gm", "A"], 0.07, 0.22, (0,))
    # 5. 1920-1922: yürüyüş, İzmir'de re majör
    t0, t_iz, t_taht = bas_("y1920"), ev[("y1920", "zafer")][0], ev[("y1920", "taht")][0]
    akorlar(iz, t0, t_iz, ["Dm", "Bb", "C", "A"], 0.12, 0.42, (0, 1, 2, 3))
    yuruyus(iz, t0, t_iz, 0.9)
    tema(iz, t0 + OLCU, t_iz, TEMA_A, 0.26)
    ekle(iz["davul"], timpani(0.8, 38), t_iz)
    akorlar(iz, t_iz, t_taht, ["D", "G"], 0.15, 0.45, (0, 2))
    tema(iz, t_iz, t_taht, TEMA_B, 0.28)
    ekle(iz["pad"], pad([58, 62, 65], bas_("y1923") - t_taht + 0.6, 0.12, atak=0.4), t_taht)
    # 6. 1923: umut (fa majör), Çankaya'da sessizleşir, sözde neredeyse susar
    t0, t_gec, t_al = bas_("y1923"), ev[("y1923", "gecis")][0], ev[("y1923", "alinti")][0]
    akorlar(iz, t0, t_gec, ["F", "C", "Dm", "Bb"], 0.11, 0.3)
    arpej(iz, t0 + OLCU, t_gec, ["F", "C", "Dm", "Bb"], 0.09)
    akorlar(iz, t_gec, t_al - 0.4, ["Dm", "Bb", "C", "A"], 0.08, 0.2, (0,))
    arpej(iz, t_gec, t_al - 0.4, ["Dm", "Bb", "C", "A"], 0.06)
    ekle(iz["bas"], bas(26, bas_("ilan") - t_al + 0.6, 0.25), t_al - 0.2)
    # 7. ilan: timpani kreşendosu -> "Cumhuriyettir." -> ana tema, toplar
    t0, t_muhur = bas_("ilan"), ev[("ilan", "muhur_buyuk")][0]
    tremolo(iz, t0 + 0.3, t_muhur, 0.02, 0.3)
    ekle(iz["pad"], pad([50, 57, 62], t_muhur - t0, 0.1, atak=2.0), t0)
    ekle(iz["davul"], timpani(1.0, 38), t_muhur)
    ekle(iz["davul"], zil(0.35, 3.5), t_muhur)
    akorlar(iz, t_muhur, bas_("kapanis"), AKOR_B, 0.15, 0.45, (0, 2))
    tema(iz, t_muhur + 0.05, bas_("kapanis"), TEMA_B, 0.3)
    yuruyus(iz, t_muhur + OLCU, bas_("kapanis"), 0.6)
    # 8. kapanış: önce sakin, "dört yıl sonra"dan itibaren tam tema, son akor
    t0, t_b, t_f = bas_("kapanis"), ev[("kapanis", "bayrak_acilis")][0], ev[("kapanis", "final")][0]
    ekle(iz["pad"], pad([50, 57, 62, 66], t_b - t0 + 0.3, 0.1, atak=0.8), t0)
    for k, n in enumerate((74, 69, 74, 78)):
        ekle(iz["kutu"], kutu(n + 12, 0.12), t0 + 0.4 + k * VURUS)
    akorlar(iz, t_b, toplam - 3.5, AKOR_B, 0.16, 0.5, (0, 2))
    tema(iz, t_b, toplam - 3.5, TEMA_B, 0.32)
    yuruyus(iz, t_b, toplam - 3.5, 1.0)
    ekle(iz["davul"], timpani(1.0, 38), toplam - 3.5)
    ekle(iz["pad"], pad([38, 50, 57, 62, 66, 69], 3.8, 0.22, atak=0.02), toplam - 3.5)
    ekle(iz["lead"], lead(74, 3.2, 0.3), toplam - 3.5)
    ekle(iz["bas"], bas(26, 3.5, 0.5), toplam - 3.5)
    ekle(iz["davul"], zil(0.3, 3.0), toplam - 3.5)

    karisim = (alcak(iz["pad"], 2200) * 1.0 + alcak(iz["lead"], 3800) * 0.9 + iz["bas"] * 0.85 +
               alcak(iz["kutu"], 6000) * 0.9 + iz["davul"] * 0.8)
    karisim = yanki(karisim, 2.2, 0.28)[: int(toplam * SR)]
    n = int(1.2 * SR)
    karisim[-n:] *= np.linspace(1, 0, n) ** 1.5
    return karisim / (np.max(np.abs(karisim)) + 1e-9) * 0.8


def efektler(z):
    iz = np.zeros(int((z["toplam"] + 3) * SR))
    kazanc = {"kalem": 0.6, "top": 0.9, "fisek": 0.5}
    for o in z["olaylar"]:
        ekle(iz, sfx(o["efekt"]), o["t"], kazanc.get(o["efekt"], 0.7))
    for sh in z["sahneler"][1:]:  # sahne geçişlerinde yumuşak rüzgâr: müzik bölümleri arasında boşluk kalmasın
        ekle(iz, sfx("gecis"), sh["bas"] - 0.6, 1.6)
    return yanki(iz, 1.2, 0.18)[: int(z["toplam"] * SR)]


def konusma(z):
    iz = np.zeros(int(z["toplam"] * SR) + SR)
    gecici = DIZIN / "ara" / "ses_islenmis"
    gecici.mkdir(parents=True, exist_ok=True)
    for s in z["sahneler"]:
        kaynak = DIZIN / "ses" / f"{s['id']}.wav"
        hedef = gecici / f"{s['id']}.wav"
        # belgesel anlatıcısı rengi: gövde, netlik, hafif sıkıştırma
        subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", str(kaynak), "-af",
                        "aresample=48000:resampler=soxr,highpass=f=75,equalizer=f=180:t=q:w=1.2:g=2,"
                        "equalizer=f=3200:t=q:w=1.5:g=2.5,equalizer=f=7500:t=q:w=2:g=-3,"
                        "acompressor=threshold=-22dB:ratio=3:attack=8:release=120:makeup=2",
                        "-ac", "1", "-ar", str(SR), str(hedef)], check=True)
        ekle(iz, oku_wav(hedef), s["ses_bas"])
    iz = iz[: int(z["toplam"] * SR)]
    return yanki(iz, 0.9, 0.09)


def ducking(ses, alt_db=-14, ust_db=-6):
    pen = int(0.02 * SR)
    n = len(ses) // pen + 1
    enerji = np.array([np.sqrt(np.mean(ses[k * pen:(k + 1) * pen] ** 2) + 1e-12) for k in range(n)])
    aktif = enerji > 0.004
    bosluk = 0
    for k in range(n):  # 300 ms'den kısa boşlukları konuşma say (müzik nefes arasında kabarmasın)
        if aktif[k]:
            if 0 < bosluk < 15:
                aktif[k - bosluk:k] = True
            bosluk = 0
        else:
            bosluk += 1
    hedef = np.where(aktif, 10 ** (alt_db / 20), 10 ** (ust_db / 20))
    yum = np.copy(hedef)
    for k in range(1, n):
        a = 0.35 if hedef[k] < yum[k - 1] else 0.04
        yum[k] = yum[k - 1] + (hedef[k] - yum[k - 1]) * a
    return np.repeat(yum, pen)[: len(ses)]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--sessiz", action="store_true", help="seslendirmesiz sürüm (müzik + efekt)")
    args = ap.parse_args()
    z = json.loads((DIZIN / "ara" / "zaman.json").read_text(encoding="utf-8"))
    m = muzik(z)
    e = efektler(z)
    if args.sessiz:
        k = m * 0.85 + e * 0.45
        ad = "29ekim-cumhuriyet-seslendirmesiz.mp4"
    else:
        v = konusma(z)
        v = v / (np.max(np.abs(v)) + 1e-9) * 0.9
        k = v + m * ducking(v) + e * 0.35
        ad = "29ekim-cumhuriyet.mp4"
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
