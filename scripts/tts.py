"""Seslendirme (CLAUDE.md §6).

Her senaryo bölümü için ayrı bir ses dosyası ve kelime zaman damgaları üretir:
  bolumler/NNN/ses/<id>.mp3
  bolumler/NNN/ses/<id>.json   -> {"metin", "konusma", "kelimeler": [{"k", "bas", "son"}]}

Ekranda görünen kelimeler `metin`den gelir; TTS'e `config/okunus.json` ile düzeltilmiş
`konusma` gönderilir. Zaman damgaları ekrandaki kelimelere geri eşlenir.

Servisler (config.yaml -> tts.servis):
  elevenlabs: ElevenLabs API (bulutta ve bilgisayarda çalışır, en kaliteli). Anahtar .env içinde
          ELEVENLABS_API_KEY olarak durur, koda yazılmaz. Gerçek kelime zamanları API'nin
          karakter hizalamasından gelir. Ses ve model config.yaml -> tts.elevenlabs altında.
  piper : çevrimdışı, ücretsiz, bilgisayarda çalışır (varsayılan, tr_TR-fahrettin-medium erkek sesi).
          Cümle cümle sentezlenir; kelime zamanları cümle içinde harf sayısına göre dağıtılır.
          Çıktı <id>.wav. Kurulum: pip install piper-tts ;
          python -m piper.download_voices tr_TR-fahrettin-medium --data-dir models/piper
  edge  : Microsoft edge-tts (ücretsiz ama tr-TR-AhmetNeural sunucuda çoğu zaman boş dönüyor).
  espeak: sadece test için robotik taslak.

Kullanım (PowerShell):
  python scripts/tts.py --bolum 1
"""
import argparse
import asyncio
import json
import re
import subprocess
import sys
import time
import wave

sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parent))
from ortak import KOK, ayarlar, bolum_dizini, senaryo  # noqa: E402

NOKTALAMA = ".,!?:;…\"“”()"


def okunus_sozlugu():
    d = json.loads((KOK / "config" / "okunus.json").read_text(encoding="utf-8"))
    return {k: v for k, v in d.items() if not k.startswith("_")}


def kelimeyi_oku(kelime, sozluk):
    """Tek bir ekran kelimesini okunuşa çevirir. Ekler ve noktalama korunur."""
    bas = len(kelime) - len(kelime.lstrip(NOKTALAMA))
    on, govde = kelime[:bas], kelime[bas:]
    govde_sade = govde.rstrip(NOKTALAMA)
    son = govde[len(govde_sade):]
    if govde_sade in sozluk:
        return on + sozluk[govde_sade] + son
    if "'" in govde_sade:
        kok, ek = govde_sade.split("'", 1)
        if kok in sozluk:
            return on + sozluk[kok] + "'" + ek + son
    return kelime


def sade(s):
    return re.sub(r"[^\wçğıöşüâîû]", "", s.lower().replace("İ", "i").replace("I", "ı"))


def eslestir(ekran_kelimeleri, konusma_parcalari, sinirlar, toplam_sure):
    """TTS kelime sınırlarını ekran kelimelerine sırayla eşler.

    konusma_parcalari[i]: i. ekran kelimesinin okunan kelime listesi.
    Eşleşmeyen kelimelere komşulardan oransal zaman verilir.
    """
    sonuc = [None] * len(ekran_kelimeleri)
    j = 0
    for i, parcalar in enumerate(konusma_parcalari):
        bas = son = None
        for p in parcalar:
            hedef = sade(p)
            if not hedef:
                continue
            # en fazla 3 sınır ileriye bak
            for k in range(j, min(j + 3, len(sinirlar))):
                aday = sade(sinirlar[k]["k"])
                if aday and (aday == hedef or hedef.startswith(aday) or aday.startswith(hedef)):
                    if bas is None:
                        bas = sinirlar[k]["bas"]
                    son = sinirlar[k]["son"]
                    j = k + 1
                    break
        if bas is not None:
            sonuc[i] = [bas, son]
    # boşlukları doldur
    bilinen = [(i, t) for i, t in enumerate(sonuc) if t]
    if not bilinen:
        adim = toplam_sure / max(1, len(ekran_kelimeleri))
        return [[i * adim, (i + 1) * adim] for i in range(len(ekran_kelimeleri))]
    for i, t in enumerate(sonuc):
        if t:
            continue
        onceki = max((b for b in bilinen if b[0] < i), default=None, key=lambda b: b[0])
        sonraki = min((b for b in bilinen if b[0] > i), default=None, key=lambda b: b[0])
        a = onceki[1][1] if onceki else 0.0
        b = sonraki[1][0] if sonraki else toplam_sure
        n0 = onceki[0] if onceki else -1
        n1 = sonraki[0] if sonraki else len(sonuc)
        adim = (b - a) / max(1, n1 - n0 - 1)
        sonuc[i] = [a + (i - n0 - 1) * adim, a + (i - n0) * adim]
    return sonuc


async def edge_uret(metin, ses, hiz, mp3_yolu):
    import edge_tts
    iletisim = edge_tts.Communicate(metin, ses, rate=hiz, boundary="WordBoundary")
    sinirlar = []
    with open(mp3_yolu, "wb") as f:
        async for parca in iletisim.stream():
            if parca["type"] == "audio":
                f.write(parca["data"])
            elif parca["type"] == "WordBoundary":
                bas = parca["offset"] / 1e7
                sinirlar.append({"k": parca["text"], "bas": bas, "son": bas + parca["duration"] / 1e7})
    return sinirlar


def elevenlabs_uret(metin, ayar_el, mp3_yolu, onceki="", sonraki=""):
    """ElevenLabs ile sentez + karakter hizalamasından kelime sınırları.

    Anahtar .env'den (ELEVENLABS_API_KEY) okunur; koda veya loga yazılmaz.
    onceki/sonraki: parçalar arası geçiş doğal olsun diye (request stitching).
    """
    import base64
    from dotenv import load_dotenv
    from elevenlabs import ElevenLabs, VoiceSettings
    load_dotenv(KOK / ".env")
    istemci = ElevenLabs()
    ek = {}
    if onceki:
        ek["previous_text"] = onceki
    if sonraki:
        ek["next_text"] = sonraki
    ayarlar_ses = ayar_el.get("ayarlar") or {}
    if ayarlar_ses:
        ek["voice_settings"] = VoiceSettings(**ayarlar_ses)
    yanit = istemci.text_to_speech.convert_with_timestamps(
        ayar_el["ses_id"],
        text=metin,
        model_id=ayar_el.get("model", "eleven_v4"),
        language_code=ayar_el.get("dil", "tr"),
        output_format="mp3_44100_128",
        **ek,
    )
    with open(mp3_yolu, "wb") as f:
        f.write(base64.b64decode(yanit.audio_base_64))
    # karakter hizalaması -> kelime sınırları
    h = yanit.alignment
    sinirlar, kelime, bas, son = [], "", None, None
    if h:
        for ch, a, b in zip(h.characters, h.character_start_times_seconds, h.character_end_times_seconds):
            if ch.isspace():
                if kelime:
                    sinirlar.append({"k": kelime, "bas": bas, "son": son})
                kelime, bas = "", None
                continue
            if bas is None:
                bas = a
            kelime += ch
            son = b
        if kelime:
            sinirlar.append({"k": kelime, "bas": bas, "son": son})
    return sinirlar


def espeak_uret(metin, mp3_yolu):
    """Çevrimdışı TASLAK ses (robotik). Yalnızca test/önizleme içindir, yayınlanmaz."""
    wav = str(mp3_yolu).replace(".mp3", ".wav")
    subprocess.run(["espeak-ng", "-v", "tr", "-s", "165", "-w", wav, metin], check=True)
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", wav, str(mp3_yolu)], check=True)
    return []


def piper_uret(ekran, okunan, model, hiz, wav_yolu):
    """Cümle cümle Piper sentezi. Dönüş: ekran kelimesi başına [bas, son] listesi."""
    import numpy as np
    from piper import PiperVoice
    ses = PiperVoice.load(str(model))
    oran = ses.config.sample_rate
    length_scale = 1.0 / (1.0 + float(str(hiz).strip("%+")) / 100.0) if hiz else 1.0
    # ekran kelimelerini cümlelere böl
    cumleler, cumle = [], []
    for i, k in enumerate(ekran):
        cumle.append(i)
        if k.rstrip("\"”'")[-1:] in ".!?":
            cumleler.append(cumle)
            cumle = []
    if cumle:
        cumleler.append(cumle)
    parcalar, zamanlar, t = [], [None] * len(ekran), 0.0
    bosluk = np.zeros(int(0.22 * oran), dtype=np.int16)
    for c in cumleler:
        metin = " ".join(okunan[i] for i in c)
        ham = _piper_sentez(ses, metin, length_scale)
        sure_c = len(ham) / oran
        agirlik = [len(sade(okunan[i])) + 1 for i in c]
        toplam = sum(agirlik)
        a = t
        for i, w in zip(c, agirlik):
            b = a + sure_c * w / toplam
            zamanlar[i] = [round(a, 3), round(b, 3)]
            a = b
        parcalar += [ham, bosluk]
        t += sure_c + len(bosluk) / oran
    veri = np.concatenate(parcalar)
    with wave.open(str(wav_yolu), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(oran)
        w.writeframes(veri.tobytes())
    return zamanlar, len(veri) / oran


def _piper_sentez(ses, metin, length_scale):
    """piper-tts 1.3+ (synthesize -> AudioChunk) ve eski sürümler (synthesize_stream_raw) için."""
    import numpy as np
    try:
        from piper import SynthesisConfig
        cfg = SynthesisConfig(length_scale=length_scale)
        return np.concatenate([c.audio_int16_array for c in ses.synthesize(metin, syn_config=cfg)])
    except ImportError:
        ham = b"".join(ses.synthesize_stream_raw(metin, length_scale=length_scale))
        return np.frombuffer(ham, dtype=np.int16)


def sure(yol, sinirlar=()):
    try:
        out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                          "-of", "csv=p=0", str(yol)], capture_output=True, text=True, check=True)
        return float(out.stdout.strip())
    except (OSError, subprocess.CalledProcessError, ValueError):
        # ffprobe yoksa (Windows'ta kurulu olmayabilir) son kelimenin bitişini kullan
        return (sinirlar[-1]["son"] + 0.3) if sinirlar else 0.0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--bolum", type=int, required=True)
    ap.add_argument("--servis", choices=["elevenlabs", "piper", "edge", "espeak"])
    ap.add_argument("--yeniden", action="store_true", help="hazır parçaları da baştan üret")
    args = ap.parse_args()

    ayar = ayarlar()["tts"]
    servis = args.servis or ayar["servis"]
    sozluk = okunus_sozlugu()
    hedef = bolum_dizini(args.bolum) / "ses"
    hedef.mkdir(parents=True, exist_ok=True)

    ayar_el = ayar.get("elevenlabs") or {}
    parcalar = senaryo(args.bolum)["bolumler"]
    konusmalar = [" ".join(kelimeyi_oku(k, sozluk) for k in p["metin"].split()) for p in parcalar]
    for sira, parca in enumerate(parcalar):
        ekran = parca["metin"].split()
        okunan = [kelimeyi_oku(k, sozluk) for k in ekran]
        konusma = " ".join(okunan)
        mp3 = hedef / f"{parca['id']}.mp3"
        wav = hedef / f"{parca['id']}.wav"
        js = hedef / f"{parca['id']}.json"
        ses_adi = {"edge": ayar["ses"], "piper": ayar.get("piper_ses", "tr_TR-fahrettin-medium"),
                   "elevenlabs": f"elevenlabs:{ayar_el.get('ses_adi', ayar_el.get('ses_id'))}"}.get(servis, "espeak-ng tr")
        cikti = wav if servis == "piper" else mp3
        # aynı metin ve sesle üretilmiş parça varsa atla
        if not args.yeniden and cikti.exists() and cikti.stat().st_size > 0 and js.exists():
            try:
                eski = json.loads(js.read_text(encoding="utf-8"))
            except ValueError:
                eski = {}
            if eski.get("konusma") == konusma and eski.get("ses") == ses_adi:
                print(f"[{parca['id']}] hazır, atlandı")
                continue
        if servis == "piper":
            model = KOK / "models" / "piper" / f"{ses_adi}.onnx"
            zamanlar, toplam = piper_uret(ekran, okunan, model, ayar.get("hiz", "+0%"), wav)
            mp3.unlink(missing_ok=True)  # eski edge sesi karışmasın
            kayit = {"metin": parca["metin"], "konusma": konusma, "servis": servis, "ses": ses_adi,
                     "sure": toplam, "kelimeler": [{"k": k, "bas": z[0], "son": z[1]} for k, z in zip(ekran, zamanlar)]}
            js.write_text(json.dumps(kayit, ensure_ascii=False, indent=1), encoding="utf-8")
            print(f"[{parca['id']}] {toplam:.1f} sn (piper)")
            continue
        # önce geçici dosyaya yaz; boş ses iyi bir mp3'ün üzerine yazılmasın
        gecici = hedef / f"{parca['id']}.tmp.mp3"
        for deneme in range(3):  # §15: en fazla 2 yeniden deneme
            try:
                if servis == "elevenlabs":
                    sinirlar = elevenlabs_uret(konusma, ayar_el, gecici,
                                               konusmalar[sira - 1] if sira > 0 else "",
                                               konusmalar[sira + 1] if sira + 1 < len(konusmalar) else "")
                elif servis == "edge":
                    sinirlar = asyncio.run(edge_uret(konusma, ayar["ses"], ayar["hiz"], gecici))
                else:
                    sinirlar = espeak_uret(konusma, gecici)
                if not gecici.exists() or gecici.stat().st_size == 0:
                    raise RuntimeError("boş ses dosyası (0 bayt)")
                break
            except Exception as e:  # noqa: BLE001
                print(f"[{parca['id']}] deneme {deneme + 1} başarısız: {e}")
                if deneme == 2:
                    gecici.unlink(missing_ok=True)
                    raise
                time.sleep(3 * (deneme + 1))
        gecici.replace(mp3)
        wav.unlink(missing_ok=True)  # eski piper sesi birleştirmede öne geçmesin
        toplam = sure(mp3, sinirlar)
        zamanlar = eslestir(ekran, [o.split() for o in okunan], sinirlar, toplam)
        kayit = {
            "metin": parca["metin"], "konusma": konusma, "servis": servis,
            "ses": ses_adi,
            "kadin": bool(ayar_el.get("kadin")) if servis == "elevenlabs" else None,
            "sure": toplam,
            "kelimeler": [{"k": k, "bas": round(t[0], 3), "son": round(t[1], 3)} for k, t in zip(ekran, zamanlar)],
        }
        js.write_text(json.dumps(kayit, ensure_ascii=False, indent=1), encoding="utf-8")
        print(f"[{parca['id']}] {toplam:.1f} sn, {len(sinirlar)} sınır")


if __name__ == "__main__":
    main()
