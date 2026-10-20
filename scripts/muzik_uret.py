"""Chiptune müzik ve efekt üretici (CLAUDE.md §7).

NES tarzı 4 kanal: 2 kare dalga (pulse), 1 üçgen (bas), 1 gürültü (davul).
Tamamen kodla üretilir, telif riski yoktur.

Çıktılar (48 kHz mono WAV):
  <hedef>/jingle_acilis.wav, jingle_kapanis.wav   marka melodisi (her videoda aynı)
  <hedef>/arkaplan.wav                            döngü (bölüm no ile küçük varyasyon)
  <hedef>/sfx/{blip,coin,levelup,gamesaved,whoosh,boss,glitch,tik}.wav

Kullanım:
  python scripts/muzik_uret.py --bolum 1 --sure 125
"""
import argparse
import sys
import wave
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from ortak import ayarlar, bolum_dizini  # noqa: E402

SR = 48000


# ---------------------------------------------------------------- kanallar
def frekans(nota):
    return 440.0 * 2 ** ((nota - 69) / 12)


def kare(f, sure, duty=0.5, faz0=0.0):
    t = np.arange(int(sure * SR)) / SR
    faz = (faz0 + f * t) % 1.0
    return np.where(faz < duty, 1.0, -1.0)


def ucgen(f, sure):
    t = np.arange(int(sure * SR)) / SR
    faz = (f * t) % 1.0
    # NES üçgeni 16 adımlıdır: basamaklı üçgen
    tri = 4 * np.abs(faz - 0.5) - 1
    return np.round(tri * 7.5) / 7.5


def gurultu(sure, rng, periyot=1):
    n = int(sure * SR)
    ham = rng.choice([-1.0, 1.0], size=n // periyot + 1)
    return np.repeat(ham, periyot)[:n]


def zarf(n, atak=0.003, bırak=0.05, sus=1.0):
    e = np.full(n, sus)
    a = min(n, int(atak * SR))
    r = min(n - a, int(bırak * SR))
    if a:
        e[:a] = np.linspace(0, sus, a)
    if r > 0:
        e[n - r:] = np.linspace(sus, 0, r)
    return e


def azalan(n, sure):
    return np.exp(-np.arange(n) / (sure * SR))


def ekle(iz, sinyal, bas_sn):
    i = int(bas_sn * SR)
    if i >= len(iz):
        return
    j = min(len(iz), i + len(sinyal))
    iz[i:j] += sinyal[: j - i]


# ---------------------------------------------------------------- nota olayları
def pulse_nota(nota, sure, duty=0.25, ses=0.5, vibrato=False):
    s = kare(frekans(nota), sure, duty)
    if vibrato and sure > 0.25:
        t = np.arange(len(s)) / SR
        faz = np.cumsum(frekans(nota) * (1 + 0.006 * np.sin(2 * np.pi * 6 * t) * (t > 0.15))) / SR
        s = np.where(faz % 1 < duty, 1.0, -1.0)
    return s * zarf(len(s), bırak=min(0.04, sure / 3)) * ses


def tri_nota(nota, sure, ses=0.6):
    s = ucgen(frekans(nota), sure)
    return s * zarf(len(s), bırak=0.02) * ses


def kick(rng, ses=0.9):
    sure = 0.12
    t = np.arange(int(sure * SR)) / SR
    f = 160 * np.exp(-t * 30) + 45
    faz = np.cumsum(f) / SR
    tri = 4 * np.abs(faz % 1 - 0.5) - 1
    return np.round(tri * 7.5) / 7.5 * azalan(len(t), 0.05) * ses


def snare(rng, ses=0.45):
    n = int(0.14 * SR)
    return gurultu(0.14, rng, 3) * azalan(n, 0.045) * ses


def hat(rng, ses=0.18):
    n = int(0.04 * SR)
    return gurultu(0.04, rng, 1) * azalan(n, 0.012) * ses


# ---------------------------------------------------------------- müzik teorisi
DO = 60  # C4
# I - V - vi - IV  (C, G, Am, F)
AKORLAR = [(0, [0, 4, 7]), (7, [7, 11, 14]), (9, [9, 12, 16]), (5, [5, 9, 12])]
MAJOR = [0, 2, 4, 5, 7, 9, 11]


def melodi_bar(akor, rng, yogunluk):
    """Akor seslerine ağırlık veren 16'lık melodi (8 adım = 8'lik)."""
    kok, sesler = akor
    olaylar = []
    adim = 0
    while adim < 8:
        if rng.random() < yogunluk or adim == 0:
            if rng.random() < 0.7:
                nota = DO + 12 + rng.choice(sesler)
            else:
                nota = DO + 12 + kok + rng.choice(MAJOR)
            uzunluk = int(rng.choice([1, 1, 2, 2, 3])) if adim < 7 else 1
            uzunluk = min(uzunluk, 8 - adim)
            olaylar.append((adim, uzunluk, int(nota)))
            adim += uzunluk
        else:
            adim += 1
    return olaylar


def arkaplan(sure, bpm, tohum):
    rng = np.random.default_rng(tohum)
    sekizlik = 60 / bpm / 2
    bar = sekizlik * 8
    iz_p1 = np.zeros(int(sure * SR) + SR)
    iz_p2 = np.zeros_like(iz_p1)
    iz_tri = np.zeros_like(iz_p1)
    iz_gur = np.zeros_like(iz_p1)

    # 4 barlık iki motif üret, bölüm boyunca döndür (A A B A ...)
    motifler = [[melodi_bar(AKORLAR[i], rng, 0.55) for i in range(4)] for _ in range(2)]
    duzen = [0, 0, 1, 0]
    bar_say = int(np.ceil(sure / bar))
    for b in range(bar_say):
        t0 = b * bar
        akor = AKORLAR[b % 4]
        kok, sesler = akor
        bolum = (b // 4)
        # bas: üçgen, kök + oktav 8'likler
        for k in range(8):
            nota = DO - 24 + kok + (12 if k % 2 else 0)
            ekle(iz_tri, tri_nota(nota, sekizlik * 0.9), t0 + k * sekizlik)
        # pulse 2: arpej (12.5% duty), yumuşak
        for k in range(16):
            nota = DO + sesler[k % 3]
            ekle(iz_p2, pulse_nota(nota, sekizlik / 2 * 0.8, duty=0.125, ses=0.18), t0 + k * sekizlik / 2)
        # pulse 1: melodi (ilk 4 bar sessiz, giriş)
        if bolum >= 1:
            motif = motifler[duzen[bolum % 4]][b % 4]
            for adim, uz, nota in motif:
                ekle(iz_p1, pulse_nota(nota, uz * sekizlik * 0.92, duty=0.25, ses=0.32, vibrato=True),
                     t0 + adim * sekizlik)
        # davul
        for k in range(8):
            t = t0 + k * sekizlik
            if k in (0, 4) or (k == 6 and b % 2):
                ekle(iz_gur, kick(rng), t)
            if k in (2, 6):
                ekle(iz_gur, snare(rng), t)
            ekle(iz_gur, hat(rng), t + sekizlik / 2)
    karisim = 0.55 * iz_p1 + 0.5 * iz_p2 + 0.75 * iz_tri + 0.5 * iz_gur
    karisim = karisim[: int(sure * SR)]
    # son 1.5 sn adımlı kısma (stepped fade)
    n = int(1.5 * SR)
    karisim[-n:] *= np.repeat(np.linspace(1, 0, 6), n // 6 + 1)[:n]
    return karisim


def jingle(kapanis=False):
    """Marka melodisi: yükselen arpej + parlak bitiş. Her videoda aynı."""
    bpm = 132
    s16 = 60 / bpm / 4
    sure = 3.2 if not kapanis else 3.6
    p1 = np.zeros(int(sure * SR) + SR)
    p2 = np.zeros_like(p1)
    tri = np.zeros_like(p1)
    rng = np.random.default_rng(7)
    gur = np.zeros_like(p1)
    # A-R-PA-MA motifi: Do Mi Sol Do' | Si Sol | Do'' (uzun)
    melodi = [(0, 1, 72), (1, 1, 76), (2, 1, 79), (3, 1, 84), (4, 2, 83), (6, 2, 79), (8, 2, 81), (10, 2, 83), (12, 12, 84)]
    if kapanis:
        melodi = [(0, 2, 84), (2, 2, 79), (4, 2, 76), (6, 2, 79), (8, 2, 81), (10, 2, 83), (12, 14, 84)]
    for adim, uz, nota in melodi:
        ekle(p1, pulse_nota(nota, uz * s16 * 0.95, duty=0.25, ses=0.5, vibrato=True), adim * s16)
        ekle(p2, pulse_nota(nota - 12 + 4 if nota % 12 == 0 else nota - 12, uz * s16 * 0.95, duty=0.5, ses=0.22), adim * s16)
    for adim, nota in [(0, 36), (4, 43), (8, 41), (12, 36)]:
        ekle(tri, tri_nota(nota, (4 if adim < 12 else 12) * s16), adim * s16)
    for adim in (0, 4, 8, 12):
        ekle(gur, kick(rng), adim * s16)
    ekle(gur, snare(rng, 0.5), 10 * s16)
    ekle(gur, snare(rng, 0.5), 11 * s16)
    k = 0.6 * p1 + 0.5 * p2 + 0.8 * tri + 0.5 * gur
    return k[: int(sure * SR)]


# ---------------------------------------------------------------- efektler
def sfx_blip():
    return np.concatenate([pulse_nota(81, 0.035, 0.5, 0.5), pulse_nota(88, 0.05, 0.5, 0.5)])


def sfx_tik():
    return pulse_nota(93, 0.03, 0.25, 0.45)


def sfx_coin():
    a = pulse_nota(83, 0.07, 0.5, 0.5)
    b = kare(frekans(88), 0.35, 0.5) * azalan(int(0.35 * SR), 0.12) * 0.5
    return np.concatenate([a, b])


def sfx_levelup():
    notalar = [72, 76, 79, 84, 88, 91, 96]
    parcalar = [pulse_nota(n, 0.055, 0.25, 0.5) for n in notalar]
    son = kare(frekans(96), 0.5, 0.25) * azalan(int(0.5 * SR), 0.2) * 0.5
    return np.concatenate(parcalar + [son])


def sfx_gamesaved():
    parcalar = [pulse_nota(n, 0.09, 0.5, 0.45) for n in [79, 84, 88]]
    akor = sum(kare(frekans(n), 0.8, 0.25) for n in [84, 88, 91]) / 3
    akor = akor * azalan(len(akor), 0.3) * 0.55
    return np.concatenate(parcalar + [akor])


def sfx_whoosh():
    rng = np.random.default_rng(3)
    sure = 1.4
    n = int(sure * SR)
    # periyodu değişen gürültü: alçaktan yükseğe ve geri
    out = np.zeros(n)
    parca = n // 28
    for i in range(28):
        p = int(1 + 14 * abs(i - 14) / 14)
        out[i * parca:(i + 1) * parca] = gurultu(parca / SR + 0.01, rng, p)[:parca]
    env = np.sin(np.linspace(0, np.pi, n)) ** 1.5
    return out * env * 0.45


def sfx_boss():
    sure = 1.1
    t = np.arange(int(sure * SR)) / SR
    f = frekans(36) * (1 - 0.25 * t / sure)
    faz = np.cumsum(f) / SR
    tri = np.round((4 * np.abs(faz % 1 - 0.5) - 1) * 7.5) / 7.5
    sq = np.where(faz * 2 % 1 < 0.5, 1.0, -1.0) * 0.25
    return (tri * 0.8 + sq) * zarf(len(t), 0.005, 0.3) * 0.8


def sfx_glitch():
    rng = np.random.default_rng(11)
    return gurultu(0.12, rng, 6) * 0.35 * zarf(int(0.12 * SR), 0.001, 0.03)


EFEKTLER = {"blip": sfx_blip, "tik": sfx_tik, "coin": sfx_coin, "levelup": sfx_levelup,
            "gamesaved": sfx_gamesaved, "whoosh": sfx_whoosh, "boss": sfx_boss, "glitch": sfx_glitch}


def wav_yaz(yol, sinyal, tepe=0.89):
    s = np.asarray(sinyal, dtype=np.float64)
    m = np.max(np.abs(s)) or 1.0
    s = s / m * tepe
    yol.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(yol), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes((s * 32767).astype("<i2").tobytes())


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--bolum", type=int, required=True)
    ap.add_argument("--sure", type=float, default=125)
    args = ap.parse_args()
    bpm = ayarlar()["muzik"]["bpm"]
    hedef = bolum_dizini(args.bolum) / "ara" / "muzik"
    wav_yaz(hedef / "jingle_acilis.wav", jingle())
    wav_yaz(hedef / "jingle_kapanis.wav", jingle(kapanis=True))
    wav_yaz(hedef / "arkaplan.wav", arkaplan(args.sure, bpm, tohum=1000 + args.bolum), tepe=0.8)
    for ad, fn in EFEKTLER.items():
        wav_yaz(hedef / "sfx" / f"{ad}.wav", fn(), tepe=0.8)
    print("müzik ->", hedef)


if __name__ == "__main__":
    main()
