"""29 Ekim özel bölümü: kullanıcının kendi ses kayıtlarını videoya hazırlar.

ozel/29ekim/kayit/<n>-<sahne>.m4a  (sahne sırasıyla 8 kayıt)
  -> ozel/29ekim/ses/<sahne>.wav + <sahne>.json   (render ve miks bunları kullanır)

Her kayıt temizlenir (uğultu, gürültü, seviye), baştaki/sondaki sessizlik kırpılır.
Konuşma tanıma kullanmadan kelime zamanı çıkarılır: kayıttaki duraklar bulunur, senaryodaki
cümle/virgül parçaları bu duraklara dinamik programlamayla oturtulur (beklenen süre = hece sayısı
x okuma hızı), parça içindeki kelimeler sesli kısımlara hece ağırlığıyla dağıtılır.
Piper sesi ozel/29ekim/ses_piper/ altında yedek olarak kalır.

Kullanım:
  python scripts/ozel/cumhuriyet_kayit.py
"""
import json
import re
import shutil
import subprocess
import sys
import wave
from pathlib import Path

import numpy as np

KOK = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(KOK / "scripts"))
from tts import kelimeyi_oku  # noqa: E402

DIZIN = KOK / "ozel" / "29ekim"
SR = 48000
PEN = 0.01  # enerji penceresi (sn)
UNLU = set("aeıioöuüâîûAEIİOÖUÜ")


def hece(metin):
    return max(1, sum(ch in UNLU for ch in metin))


def temizle(kaynak, hedef):
    # uğultu kesme, hafif gürültü azaltma, ıslık yumuşatma, kayıtlar arası eşit seviye
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", str(kaynak), "-af",
                    "highpass=f=70,afftdn=nr=10:nf=-58:tn=1,deesser=i=0.35,loudnorm=I=-18:TP=-2:LRA=9",
                    "-ac", "1", "-ar", str(SR), str(hedef)], check=True)


def oku(yol):
    with wave.open(str(yol)) as w:
        return np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float64) / 32768


def yaz(yol, x):
    with wave.open(str(yol), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes((np.clip(x, -1, 1) * 32767).astype("<i2").tobytes())


def aktiflik(x):
    pen = int(PEN * SR)
    e = np.array([np.sqrt(np.mean(x[i:i + pen] ** 2)) for i in range(0, len(x) - pen, pen)])
    db = 20 * np.log10(e + 1e-9)
    taban, tepe = np.percentile(db, 10), np.percentile(db, 95)
    return db > taban + 0.33 * (tepe - taban)


def parcalar(sahne):
    """Senaryodaki cümleleri TTS ile aynı şekilde virgül/iki noktadan böler."""
    out = []
    for c in sahne["cumleler"]:
        dilimler = [d for d in re.split(r"(?<=[,:])\s+", c["m"]) if d]
        for j, d in enumerate(dilimler):
            out.append({"kelimeler": d.split(), "alinti": c.get("alinti", False), "cumle_sonu": j == len(dilimler) - 1})
    return out


def hizala(akt, parcs, sozluk):
    """Parça sınırlarını duraklara oturtur. Dönüş: her parça için (bas, son) kare indisi."""
    n = len(akt)
    ilk = int(np.argmax(akt))
    son = n - int(np.argmax(akt[::-1]))
    # adaylar: 40 ms ve üstü duraklar (orta noktası + uzunluğu)
    aday = []
    i = ilk
    while i < son:
        if not akt[i]:
            j = i
            while j < son and not akt[j]:
                j += 1
            if j - i >= 4:
                aday.append(((i + j) / 2, j - i, i, j))
            i = j
        else:
            i += 1
    # durak olmadan bağlanmış parçalar için konuşmanın içinde de aday (cezalı): her 3 karede bir
    var = {int(a[0]) for a in aday}
    uzun = list(aday)
    for f in range(ilk + 3, son - 3, 3):
        if all(abs(f - v) > 3 for v in var) and not any(g[2] - 2 <= f <= g[3] + 2 for g in uzun):
            kisa = not akt[f] or not akt[f - 1] or not akt[f + 1]
            aday.append((f, -1 if kisa else -2, f, f))
    aday.sort()
    heceler = [sum(hece(kelimeyi_oku(k, sozluk)) for k in p["kelimeler"]) for p in parcs]
    birik = np.concatenate([[0], np.cumsum(akt)])
    konusma = birik[son] - birik[ilk]
    hiz = konusma / sum(heceler)  # kare / hece
    K = len(parcs)

    def maliyet(a, b, k):
        """k. parça a..b karesi arasında olursa"""
        sesli = birik[int(b)] - birik[int(a)] if b > a else 0
        bek = heceler[k] * hiz
        return ((sesli - bek) / (bek + 15)) ** 2

    # DP: durum (k, aday indeksi) = k parça bitti, son sınır bu adayda
    nok = [(ilk, 0, ilk, ilk)] + aday + [(son, 0, son, son)]
    INF = 1e18
    D = [[INF] * len(nok) for _ in range(K + 1)]
    G = [[-1] * len(nok) for _ in range(K + 1)]
    D[0][0] = 0
    for k in range(1, K + 1):
        for b in range(1, len(nok)):
            if k == K and b != len(nok) - 1:
                continue
            if k < K and b == len(nok) - 1:
                continue
            for a in range(b):
                if D[k - 1][a] >= INF:
                    continue
                c = D[k - 1][a] + maliyet(nok[a][3], nok[b][2], k - 1)
                if k < K:
                    uz = nok[b][1]
                    if uz == -1:      # 10-30 ms'lik mikro durak
                        c += 0.06
                    elif uz == -2:    # konuşmanın ortası
                        c += 0.2
                    else:             # gerçek durak: cümle sonlarında daha çok tercih et
                        c -= 0.02 * min(uz, 60) / 10 * (2.0 if parcs[k - 1]["cumle_sonu"] else 1.0)
                if c < D[k][b]:
                    D[k][b], G[k][b] = c, a
    yol, b = [], len(nok) - 1
    for k in range(K, 0, -1):
        a = G[k][b]
        yol.append((nok[a][3], nok[b][2]))
        b = a
    return yol[::-1]


def kelime_zamanlari(akt, parcs, sinirlar, sozluk, kayma):
    out = []
    for p, (a, b) in zip(parcs, sinirlar):
        kareler = [i for i in range(int(a), int(b)) if akt[i]] or list(range(int(a), max(int(a) + 1, int(b))))
        agirlik = [hece(kelimeyi_oku(k, sozluk)) + 0.4 for k in p["kelimeler"]]
        top = sum(agirlik)
        birikim = 0.0
        for k, w in zip(p["kelimeler"], agirlik):
            i0 = kareler[min(len(kareler) - 1, int(birikim / top * len(kareler)))]
            birikim += w
            i1 = kareler[min(len(kareler) - 1, int(birikim / top * len(kareler)) - 1)] + 1
            out.append({"k": k, "bas": round(i0 * PEN - kayma, 3), "son": round(max(i1, i0 + 1) * PEN - kayma, 3),
                        "alinti": p["alinti"]})
    return out


def main():
    sen = json.loads((DIZIN / "senaryo.json").read_text(encoding="utf-8"))
    sozluk = sen["okunus"]
    ses = DIZIN / "ses"
    yedek = DIZIN / "ses_piper"
    if not yedek.exists() and ses.exists():
        shutil.copytree(ses, yedek)
    ara = DIZIN / "ara" / "kayit"
    ara.mkdir(parents=True, exist_ok=True)
    for n, sahne in enumerate(sen["sahneler"], 1):
        kaynak = next((DIZIN / "kayit").glob(f"{n}-*.m4a"))
        temiz = ara / f"{sahne['id']}.wav"
        temizle(kaynak, temiz)
        x = oku(temiz)
        akt = aktiflik(x)
        ilk = max(0, int(np.argmax(akt)) - 6)                  # 60 ms nefes payı
        son = min(len(akt), len(akt) - int(np.argmax(akt[::-1])) + 25)  # 250 ms doğal kuyruk
        parcs = parcalar(sahne)
        sinirlar = hizala(akt, parcs, sozluk)
        kelimeler = kelime_zamanlari(akt, parcs, sinirlar, sozluk, ilk * PEN)
        kesik = x[int(ilk * PEN * SR): int(son * PEN * SR)]
        n_in = int(0.015 * SR)  # tık olmasın diye kısa yumuşak giriş/çıkış
        kesik[:n_in] *= np.linspace(0, 1, n_in)
        kesik[-n_in:] *= np.linspace(1, 0, n_in)
        yaz(ses / f"{sahne['id']}.wav", kesik)
        (ses / f"{sahne['id']}.json").write_text(json.dumps(
            {"kaynak": kaynak.name, "sure": round(len(kesik) / SR, 3), "kelimeler": kelimeler},
            ensure_ascii=False, indent=1), encoding="utf-8")
        print(f"[{sahne['id']}] {len(kesik) / SR:.1f} sn  " +
              " | ".join(f"{p['kelimeler'][0]}@{(a - ilk) * PEN:.2f}" for p, (a, b) in zip(parcs, sinirlar)))


if __name__ == "__main__":
    main()
