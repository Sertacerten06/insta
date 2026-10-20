"""Kalite kontrol (CLAUDE.md §14). Otomatik ölçülebilenleri kontrol eder, 5 kare çıkarır.

Başarısız bir madde varsa çıkış kodu 1 olur ve neden logs/ içine yazılır (yükleme yapılmaz).
Görsel kontrol (kareler) ve içerik kontrolü (Haritam bilgileri, kaynaklar) insan/Claude tarafından yapılır.

Kullanım:
  python scripts/kalite_kontrol.py --bolum 1
"""
import argparse
import json
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from ortak import KOK, ayarlar, bolum_dizini, senaryo  # noqa: E402

KARELER = [0, 30, 60, 90, 115]


def probe(yol):
    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries",
                          "format=duration:stream=codec_type,codec_name,width,height,r_frame_rate,sample_rate",
                          "-of", "json", str(yol)], capture_output=True, text=True, check=True).stdout
    return json.loads(out)


def lufs(yol):
    out = subprocess.run(["ffmpeg", "-i", str(yol), "-af", "ebur128", "-f", "null", "-"],
                         capture_output=True, text=True).stderr
    m = re.findall(r"I:\s+(-?[\d.]+) LUFS", out)
    return float(m[-1]) if m else None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--bolum", type=int, required=True)
    args = ap.parse_args()
    ayar = ayarlar()
    bd = bolum_dizini(args.bolum)
    mp4 = bd / f"bolum-{args.bolum:03d}.mp4"
    sonuc = []

    def kontrol(ad, ok, detay=""):
        sonuc.append((ad, ok, detay))

    p = probe(mp4)
    sure = float(p["format"]["duration"])
    v = next(s for s in p["streams"] if s["codec_type"] == "video")
    a = next((s for s in p["streams"] if s["codec_type"] == "audio"), None)
    v_ayar = ayar["video"]
    kontrol("süre 110–130 sn", v_ayar["sure_min"] <= sure <= v_ayar["sure_max"], f"{sure:.1f} sn")
    kontrol("1080x1920, 30 fps, H.264", (v["width"], v["height"], v["r_frame_rate"], v["codec_name"]) ==
            (1080, 1920, "30/1", "h264"), f"{v['width']}x{v['height']} {v['r_frame_rate']} {v['codec_name']}")
    kontrol("AAC 48 kHz", a is not None and a["codec_name"] == "aac" and a["sample_rate"] == "48000",
            f"{a and a['codec_name']} {a and a['sample_rate']}")
    lu = lufs(mp4)
    kontrol("ses ~-16 LUFS", lu is not None and abs(lu - ayar["tts"].get("hedef_lufs", -16)) <= 1.5, f"{lu} LUFS")
    sen = senaryo(args.bolum)
    kontrol("Haritam bölümü var", any(b["sahne"] == "haritam" for b in sen["bolumler"]))
    cap = (bd / "caption.txt").read_text(encoding="utf-8") if (bd / "caption.txt").exists() else ""
    kontrol("caption'da kaynaklar ve haritam.arpama.tr", "Kaynaklar:" in cap and "haritam.arpama.tr" in cap)
    etiketler = re.findall(r"#\w+", cap)
    kontrol("hashtag 5–10, #arpama #haritam #yks var", 5 <= len(etiketler) <= 10 and
            {"#arpama", "#haritam", "#yks"} <= set(etiketler), f"{len(etiketler)} etiket")
    kontrol("marka sesi config ile aynı", all(
        json.loads((bd / "ses" / f"{b['id']}.json").read_text(encoding="utf-8")).get("ses") == ayar["tts"]["ses"]
        for b in sen["bolumler"]), ayar["tts"]["ses"])

    kare_dir = bd / "kontrol"
    kare_dir.mkdir(exist_ok=True)
    for s in KARELER:
        subprocess.run(["ffmpeg", "-y", "-v", "error", "-ss", str(min(s, sure - 0.1)), "-i", str(mp4),
                        "-frames:v", "1", str(kare_dir / f"kare_{s:03d}.png")], check=True)

    basarili = all(ok for _, ok, _ in sonuc)
    satirlar = [f"{'✓' if ok else '✗'} {ad} {('(' + d + ')') if d else ''}" for ad, ok, d in sonuc]
    rapor = f"Bölüm {args.bolum} kalite kontrol — {datetime.now():%Y-%m-%d %H:%M}\n" + "\n".join(satirlar)
    rapor += f"\nKareler: {kare_dir}\nSONUÇ: {'GEÇTİ' if basarili else 'KALDI (yükleme yapma)'}\n"
    (KOK / "logs").mkdir(exist_ok=True)
    (KOK / "logs" / f"kalite_bolum-{args.bolum:03d}.txt").write_text(rapor, encoding="utf-8")
    print(rapor)
    sys.exit(0 if basarili else 1)


if __name__ == "__main__":
    main()
