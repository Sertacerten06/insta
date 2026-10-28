"""29 Ekim özel bölümü: cümle ve virgül bazlı Piper seslendirmesi.

Normal tts.py cümleleri tek parça okur. Burada her cümle virgüllerden bölünüp ayrı
sentezlenir; aralara senaryodaki duraklar konur, alıntılar daha yavaş okunur.
Böylece anlatım tek düze bir makine okuması gibi değil, belgesel anlatıcısı gibi akar.

Çıktı: ozel/29ekim/ses/<sahne>.wav + <sahne>.json  (kelime zamanları, render bunları kullanır)

Kullanım:
  python scripts/ozel/cumhuriyet_tts.py
"""
import json
import re
import sys
import wave
from pathlib import Path

import numpy as np

KOK = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(KOK / "scripts"))
from tts import NOKTALAMA, kelimeyi_oku, sade  # noqa: E402

DIZIN = KOK / "ozel" / "29ekim"


def sessizligi_kirp(x, esik=350):
    idx = np.where(np.abs(x) > esik)[0]
    if not len(idx):
        return x
    return x[max(0, idx[0] - 200): idx[-1] + 600]


def main():
    from piper import PiperVoice, SynthesisConfig
    sen = json.loads((DIZIN / "senaryo.json").read_text(encoding="utf-8"))
    ses = PiperVoice.load(str(KOK / "models" / "piper" / "tr_TR-fahrettin-medium.onnx"))
    sr = ses.config.sample_rate
    genel = sen["ses"]
    sozluk = sen["okunus"]
    hedef = DIZIN / "ses"
    hedef.mkdir(exist_ok=True)

    for sahne in sen["sahneler"]:
        parcalar, kelimeler, t = [], [], 0.0
        for c in sahne["cumleler"]:
            hiz = c.get("hiz", 1.0) * genel["hiz"]
            # virgül ve iki noktadan böl (noktalama parçada kalır)
            dilimler = [d for d in re.split(r"(?<=[,:])\s+", c["m"]) if d]
            for j, dilim in enumerate(dilimler):
                ekran = dilim.split()
                okunan = [kelimeyi_oku(k, sozluk) for k in ekran]
                cfg = SynthesisConfig(length_scale=1.0 / hiz, noise_scale=0.6, noise_w_scale=0.75)
                ham = np.concatenate([a.audio_int16_array for a in ses.synthesize(" ".join(okunan), syn_config=cfg)])
                ham = sessizligi_kirp(ham)
                sure_d = len(ham) / sr
                agirlik = [len(sade(o)) + 1.5 for o in okunan]
                top = sum(agirlik)
                a = t
                for k, w in zip(ekran, agirlik):
                    b = a + sure_d * w / top
                    kelimeler.append({"k": k, "bas": round(a, 3), "son": round(b, 3), "alinti": c.get("alinti", False)})
                    a = b
                son_dilim = j == len(dilimler) - 1
                ara = c.get("ara", genel["cumle"]) if son_dilim else genel["virgul"]
                parcalar += [ham, np.zeros(int(ara * sr), dtype=np.int16)]
                t += sure_d + ara
        veri = np.concatenate(parcalar)
        with wave.open(str(hedef / f"{sahne['id']}.wav"), "wb") as w:
            w.setnchannels(1)
            w.setsampwidth(2)
            w.setframerate(sr)
            w.writeframes(veri.tobytes())
        (hedef / f"{sahne['id']}.json").write_text(json.dumps(
            {"sure": round(len(veri) / sr, 3), "kelimeler": kelimeler}, ensure_ascii=False, indent=1), encoding="utf-8")
        print(f"[{sahne['id']}] {len(veri) / sr:.1f} sn")


if __name__ == "__main__":
    main()
