"""Ses + görüntü birleştirme (CLAUDE.md §6, §7, §9, §10.1).

1. Seslendirme parçalarını zaman çizelgesine yerleştirir (render.py -> ara/zaman.json).
2. Chiptune arka planı + jingle'ları ekler; konuşma varken müziği -22 dB, boşlukta -14 dB'ye çeker (ducking).
3. Efektleri (blip, coin, level up, game saved...) olay listesine göre ekler.
4. -16 LUFS'a normalize eder, H.264 videoyla AAC 48 kHz olarak birleştirir.
5. onay_modu açıksa MP4 + kapak + caption output/onay_bekleyen/ içine kopyalanır.

Kullanım:
  python scripts/birlestir.py --bolum 1
"""
import argparse
import json
import shutil
import subprocess
import sys
import wave
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from ortak import KOK, ayarlar, bolum_dizini, senaryo  # noqa: E402

SR = 48000


def oku(yol):
    """Herhangi bir ses dosyasını 48 kHz mono float diziye çevirir (ffmpeg ile)."""
    out = subprocess.run(["ffmpeg", "-v", "error", "-i", str(yol), "-f", "f32le", "-ac", "1", "-ar", str(SR), "-"],
                         capture_output=True, check=True).stdout
    return np.frombuffer(out, dtype=np.float32).astype(np.float64)


def db(x):
    return 10 ** (x / 20)


def yerlestir(iz, sinyal, t, kazanc=1.0):
    i = int(t * SR)
    if i >= len(iz) or i < 0:
        return
    j = min(len(iz), i + len(sinyal))
    iz[i:j] += sinyal[: j - i] * kazanc


def ducking_zarfi(konusma, alt_db, ust_db):
    """Konuşma enerjisine göre müzik kazancı: konuşurken alt_db, boşlukta ust_db.
    Atak 60 ms, bırakma 400 ms."""
    pencere = int(0.02 * SR)
    n = len(konusma) // pencere + 1
    enerji = np.array([np.sqrt(np.mean(konusma[k * pencere:(k + 1) * pencere] ** 2) + 1e-12) for k in range(n)])
    aktif = enerji > 0.01
    # kısa boşlukları (<300 ms) konuşma say
    bosluk = 0
    for k in range(n):
        if aktif[k]:
            if 0 < bosluk < 15:
                aktif[k - bosluk:k] = True
            bosluk = 0
        else:
            bosluk += 1
    hedef = np.where(aktif, db(alt_db), db(ust_db))
    zarf = np.empty(n)
    g = hedef[0]
    a_atak = 1 - np.exp(-0.02 / 0.06)
    a_birak = 1 - np.exp(-0.02 / 0.4)
    for k in range(n):
        a = a_atak if hedef[k] < g else a_birak
        g += (hedef[k] - g) * a
        zarf[k] = g
    return np.repeat(zarf, pencere)[: len(konusma)]


def wav_yaz(yol, sinyal):
    s = np.clip(sinyal, -1, 1)
    with wave.open(str(yol), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes((s * 32767).astype("<i2").tobytes())


def caption(sen):
    c = sen.get("caption")
    if c:
        return c
    raise SystemExit("senaryo.json içinde 'caption' yok")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--bolum", type=int, required=True)
    args = ap.parse_args()
    ayar = ayarlar()
    bd = bolum_dizini(args.bolum)
    ara = bd / "ara"
    zaman = json.loads((ara / "zaman.json").read_text(encoding="utf-8"))
    toplam = zaman["toplam"]
    n = int(toplam * SR) + 1
    muzik_dir = ara / "muzik"

    # 1) konuşma izi
    konusma = np.zeros(n)
    for s in zaman["sahneler"]:
        yerlestir(konusma, oku(bd / "ses" / f"{s['id']}.mp3"), s["ses_bas"])
    tepe = np.max(np.abs(konusma)) or 1
    konusma *= 0.7 / tepe

    # 2) müzik izi: arka plan açılış jingle'ından sonra başlar, kapanış jingle'ında biter
    muzik = np.zeros(n)
    olaylar = zaman["olaylar"]
    t_jingle1 = next(o["t"] for o in olaylar if o["efekt"] == "jingle_acilis")
    t_jingle2 = next(o["t"] for o in olaylar if o["efekt"] == "jingle_kapanis")
    j1 = oku(muzik_dir / "jingle_acilis.wav")
    j2 = oku(muzik_dir / "jingle_kapanis.wav")
    arka = oku(muzik_dir / "arkaplan.wav")
    bas = t_jingle1 + len(j1) / SR - 0.1
    parca = arka[: int((t_jingle2 - bas) * SR)]
    if len(parca) > SR:  # sonda 1 sn adımlı kısma
        k = SR
        parca[-k:] *= np.repeat(np.linspace(1, 0, 5), k // 5 + 1)[:k]
    yerlestir(muzik, parca, bas, 1.0)
    # kanca bölümünde arka planın ilk barları (davul girişi)
    yerlestir(muzik, arka[: int(t_jingle1 * SR)], 0.0, 0.8)
    jingle = np.zeros(n)
    yerlestir(jingle, j1, t_jingle1)
    yerlestir(jingle, j2, t_jingle2)

    # ducking: müzik konuşma altında -22 dB, boşlukta -14 dB (tam ölçeğe göre)
    m = ayar["muzik"]
    zarf = ducking_zarfi(konusma, m["konusma_alti_db"], m["bosluk_db"])
    muzik = muzik * zarf + jingle * zarf * db(6)  # marka melodisi müzikten 6 dB önde

    # 3) efektler
    efekt = np.zeros(n)
    cache = {}
    for o in olaylar:
        ad = o["efekt"]
        if ad.startswith("jingle"):
            continue
        if ad not in cache:
            cache[ad] = oku(muzik_dir / "sfx" / f"{ad}.wav")
        yerlestir(efekt, cache[ad], o["t"], 0.32)

    karisim = konusma + muzik + efekt
    karisim = karisim / max(1.0, np.max(np.abs(karisim)) / 0.95)
    ham = ara / "ses_karisim.wav"
    wav_yaz(ham, karisim)

    # 4) loudnorm (-16 LUFS) + mux
    hedef_lufs = ayar["tts"].get("hedef_lufs", -16)
    cikti = bd / f"bolum-{args.bolum:03d}.mp4"
    subprocess.run([
        "ffmpeg", "-y", "-v", "error", "-i", str(ara / "video.mp4"), "-i", str(ham),
        "-filter:a", f"loudnorm=I={hedef_lufs}:TP=-1.5:LRA=11", "-ar", "48000",
        "-map", "0:v", "-map", "1:a", "-c:v", "copy", "-c:a", "aac", "-b:a", "192k",
        "-movflags", "+faststart", "-shortest", str(cikti)], check=True)
    sen = senaryo(args.bolum)
    (bd / "caption.txt").write_text(caption(sen), encoding="utf-8")
    print("çıktı ->", cikti)

    # 5) onay modu
    if ayar.get("onay_modu", True):
        hedef = KOK / "output" / "onay_bekleyen" / f"bolum-{args.bolum:03d}"
        hedef.mkdir(parents=True, exist_ok=True)
        for f in (cikti, bd / "kapak.png", bd / "caption.txt"):
            shutil.copy2(f, hedef / f.name)
        print("onay_modu açık: yükleme yapılmadı ->", hedef)


if __name__ == "__main__":
    main()
