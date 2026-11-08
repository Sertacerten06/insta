"""10 Kasım özel bölümü: cümle bazlı seslendirme (ElevenLabs, yedek Piper).

Her cümle ayrı sentezlenir (ElevenLabs'te önceki/sonraki cümle bağlam olarak verilir ki tonlama
kopmasın), baş/son sessizlik kırpılır, aralara senaryodaki duraklar konur. Kelime zamanları
ElevenLabs'in karakter hizalamasından gelir (Piper'da harf sayısına göre tahmin edilir).

Çıktı: ozel/10kasim/ses/<sahne>.wav + <sahne>.json

Kullanım:
  python scripts/ozel/ataturk_tts.py                       # ElevenLabs (ses: senaryo.json -> ses.elevenlabs)
  python scripts/ozel/ataturk_tts.py --servis piper        # yedek: Piper fahrettin (bulutta, anahtarsız)
  python scripts/ozel/ataturk_tts.py --sahne kanca         # tek sahneyi yeniden üret
"""
import argparse
import base64
import json
import os
import re
import subprocess
import sys
import wave
from pathlib import Path

import numpy as np

KOK = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(KOK / "scripts"))
from tts import kelimeyi_oku, sade  # noqa: E402

DIZIN = KOK / "ozel" / "10kasim"
SR = 44100


def wav_oku(yol):
    out = subprocess.run(["ffmpeg", "-v", "error", "-i", str(yol), "-f", "s16le", "-ac", "1", "-ar", str(SR), "-"],
                         capture_output=True, check=True).stdout
    return np.frombuffer(out, dtype=np.int16)


def kirp_sinir(x, esik=500):
    idx = np.where(np.abs(x) > esik)[0]
    if not len(idx):
        return 0, len(x)
    return max(0, idx[0] - int(0.01 * SR)), min(len(x), idx[-1] + int(0.06 * SR))


def eleven_cumle(istemci, ayar, okunan, onceki, sonraki, gecici):
    from elevenlabs import VoiceSettings
    yanit = istemci.text_to_speech.convert_with_timestamps(
        ayar["ses_id"], text=okunan, model_id=ayar.get("model", "eleven_v4"),
        language_code=ayar.get("dil", "tr"), output_format="mp3_44100_128",
        previous_text=onceki or None, next_text=sonraki or None,
        voice_settings=VoiceSettings(**ayar.get("ayarlar", {})),
    )
    gecici.write_bytes(base64.b64decode(yanit.audio_base_64))
    h = yanit.alignment
    kel, k, a, b = [], "", None, None
    for ch, s, e in zip(h.characters, h.character_start_times_seconds, h.character_end_times_seconds):
        if ch.isspace():
            if k:
                kel.append((k, a, b))
            k, a = "", None
            continue
        if a is None:
            a = s
        k, b = k + ch, e
    if k:
        kel.append((k, a, b))
    return wav_oku(gecici), kel


def tempo_uygula(x, tempo, gecici):
    if abs(tempo - 1.0) < 1e-3:
        return x
    g1, g2 = gecici.with_suffix(".in.wav"), gecici.with_suffix(".out.wav")
    with wave.open(str(g1), "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR); w.writeframes(x.tobytes())
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", str(g1), "-filter:a", f"atempo={tempo}", str(g2)], check=True)
    return wav_oku(g2)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--servis", choices=["elevenlabs", "piper"], default="elevenlabs")
    ap.add_argument("--sahne", help="yalnızca bu sahne(ler), virgülle")
    ap.add_argument("--ses-id", help="ElevenLabs voice_id (senaryodakini ezer)")
    args = ap.parse_args()
    sen = json.loads((DIZIN / "senaryo.json").read_text(encoding="utf-8"))
    genel = sen["ses"]
    sozluk = sen.get("okunus", {})
    hedef = DIZIN / "ses"
    hedef.mkdir(exist_ok=True)
    gecici = hedef / "_gecici.mp3"
    secili = set(args.sahne.split(",")) if args.sahne else None

    # tüm cümleler sırayla (bağlam için)
    tum = [c for s in sen["sahneler"] for c in s["cumleler"]]

    if args.servis == "elevenlabs":
        from dotenv import load_dotenv
        load_dotenv(KOK / ".env")
        from elevenlabs import ElevenLabs
        if not os.environ.get("ELEVENLABS_API_KEY"):
            sys.exit("ELEVENLABS_API_KEY yok: .env dosyasına ekle (ya da --servis piper)")
        istemci = ElevenLabs(api_key=os.environ["ELEVENLABS_API_KEY"])
        ayar = dict(genel["elevenlabs"])
        if args.ses_id:
            ayar["ses_id"] = args.ses_id
        tempo = float(ayar.get("tempo", 1.0))
    else:
        from piper import PiperVoice, SynthesisConfig
        pses = PiperVoice.load(str(KOK / "models" / "piper" / "tr_TR-fahrettin-medium.onnx"))
        tempo = 1.0

    for sahne in sen["sahneler"]:
        if secili and sahne["id"] not in secili:
            continue
        parcalar, kelimeler, t = [], [], 0.0
        for c in sahne["cumleler"]:
            ekran = c["m"].split()
            okunan = [kelimeyi_oku(k, sozluk) for k in ekran]
            i = tum.index(c)
            if args.servis == "elevenlabs":
                onceki = " ".join(x["m"] for x in tum[max(0, i - 2):i])
                sonraki = tum[i + 1]["m"] if i + 1 < len(tum) else ""
                ham, hiz_kel = eleven_cumle(istemci, ayar, " ".join(okunan), onceki, sonraki, gecici)
                a0, a1 = kirp_sinir(ham)
                ham = ham[a0:a1]
                ofs = a0 / SR
                # okunan kelimeler -> ekran kelimeleri (okunuş birden çok kelime olabilir)
                zam, j = [], 0
                for o in okunan:
                    n = len(o.split())
                    grup = hiz_kel[j:j + n] or hiz_kel[-1:]
                    zam.append((grup[0][1] - ofs, grup[-1][2] - ofs))
                    j += n
                ham = tempo_uygula(ham, tempo, gecici)
                zam = [(max(0, a) / tempo, max(0, b) / tempo) for a, b in zam]
            else:
                hiz = c.get("hiz", 1.0) * genel.get("hiz", 1.0) * (0.9 if c.get("alinti") else 1.0)
                cfg = SynthesisConfig(length_scale=1.0 / hiz, noise_scale=0.6, noise_w_scale=0.75)
                ham = np.concatenate([a.audio_int16_array for a in pses.synthesize(" ".join(okunan), syn_config=cfg)])
                sr0 = pses.config.sample_rate
                if sr0 != SR:  # 22050 -> 44100
                    ham = np.repeat(ham, SR // sr0)
                a0, a1 = kirp_sinir(ham, 350)
                ham = ham[a0:a1]
                sure_d = len(ham) / SR
                ag = [len(sade(o)) + 1.5 for o in okunan]
                top, a = sum(ag), 0.0
                zam = []
                for w in ag:
                    zam.append((a, a + sure_d * w / top))
                    a += sure_d * w / top
            for k, (a, b) in zip(ekran, zam):
                kelimeler.append({"k": k, "bas": round(t + a, 3), "son": round(t + b, 3), "alinti": c.get("alinti", False)})
            ara = c.get("ara", genel["cumle"])
            parcalar += [ham, np.zeros(int(ara * SR), dtype=np.int16)]
            t += len(ham) / SR + ara
        veri = np.concatenate(parcalar)
        with wave.open(str(hedef / f"{sahne['id']}.wav"), "wb") as w:
            w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR); w.writeframes(veri.tobytes())
        (hedef / f"{sahne['id']}.json").write_text(json.dumps(
            {"sure": round(len(veri) / SR, 3), "servis": args.servis, "kelimeler": kelimeler},
            ensure_ascii=False, indent=1), encoding="utf-8")
        print(f"[{sahne['id']}] {len(veri) / SR:.1f} sn")
    for g in hedef.glob("_gecici*"):
        g.unlink()


if __name__ == "__main__":
    main()
