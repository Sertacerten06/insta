"""Instagram'a yükleme (CLAUDE.md §10).

Akış: MP4 + kapak -> Cloudflare R2 (herkese açık URL) -> Graph API REELS container
-> durum FINISHED olana kadar bekle -> media_publish -> data/gecmis.json + logs/.

onay_modu: true iken sadece --onayla verilirse yükler (kullanıcı onayı).
Anahtarlar .env içindedir; asla loga veya koda yazılmaz.

Kullanım (PowerShell):
  python scripts/yukle.py --bolum 1              # onay modu açıksa sadece durumu söyler
  python scripts/yukle.py --bolum 1 --onayla     # kullanıcı onay verdi, yükle
"""
import argparse
import json
import os
import shutil
import sys
import time
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from ortak import KOK, ayarlar  # noqa: E402

GEREKLI = ["IG_USER_ID", "IG_ACCESS_TOKEN", "R2_ACCOUNT_ID", "R2_ACCESS_KEY_ID",
           "R2_SECRET_ACCESS_KEY", "R2_BUCKET", "R2_PUBLIC_BASE_URL"]


def log(mesaj):
    (KOK / "logs").mkdir(exist_ok=True)
    with open(KOK / "logs" / "yukleme.log", "a", encoding="utf-8") as f:
        f.write(f"{datetime.now():%Y-%m-%d %H:%M:%S} {mesaj}\n")
    print(mesaj)


def env_yukle():
    from dotenv import load_dotenv
    load_dotenv(KOK / ".env")
    eksik = [k for k in GEREKLI if not os.getenv(k)]
    if eksik:
        raise SystemExit(f".env eksik: {', '.join(eksik)} (bkz. .env.example)")


def r2_yukle(yol, anahtar):
    import boto3
    s3 = boto3.client("s3", endpoint_url=f"https://{os.environ['R2_ACCOUNT_ID']}.r2.cloudflarestorage.com",
                      aws_access_key_id=os.environ["R2_ACCESS_KEY_ID"],
                      aws_secret_access_key=os.environ["R2_SECRET_ACCESS_KEY"], region_name="auto")
    tur = "video/mp4" if yol.suffix == ".mp4" else "image/png"
    s3.upload_file(str(yol), os.environ["R2_BUCKET"], anahtar, ExtraArgs={"ContentType": tur})
    return f"{os.environ['R2_PUBLIC_BASE_URL'].rstrip('/')}/{anahtar}"


def graph(yontem, yol, **params):
    import httpx
    surum = os.getenv("IG_GRAPH_VERSION", "v21.0")
    params["access_token"] = os.environ["IG_ACCESS_TOKEN"]
    url = f"https://graph.facebook.com/{surum}/{yol}"
    for deneme in range(3):  # §15: en fazla 2 yeniden deneme
        try:
            r = httpx.request(yontem, url, params=params, timeout=60)
            r.raise_for_status()
            return r.json()
        except httpx.HTTPError as e:
            # token içeren URL'yi loglama
            log(f"Graph API hatası ({yol}, deneme {deneme + 1}): {type(e).__name__}")
            if deneme == 2:
                raise
            time.sleep(5 * (deneme + 1))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--bolum", type=int, required=True)
    ap.add_argument("--onayla", action="store_true", help="onay modunda kullanıcı onayı")
    args = ap.parse_args()
    ad = f"bolum-{args.bolum:03d}"
    klasor = KOK / "output" / "onay_bekleyen" / ad
    if not klasor.exists():
        raise SystemExit(f"{klasor} yok. Önce /video-uret çalıştır.")
    kalite = KOK / "logs" / f"kalite_{ad}.txt"
    if not kalite.exists() or "SONUÇ: GEÇTİ" not in kalite.read_text(encoding="utf-8"):
        log(f"{ad}: kalite kontrol geçmedi veya yapılmadı, yükleme iptal")
        raise SystemExit(1)
    if ayarlar().get("onay_modu", True) and not args.onayla:
        print(f"onay_modu açık. {klasor} içindeki videoyu izle; onaylıyorsan --onayla ile tekrar çalıştır.")
        return

    env_yukle()
    caption = (klasor / "caption.txt").read_text(encoding="utf-8")
    video_url = r2_yukle(klasor / f"{ad}.mp4", f"reels/{ad}.mp4")
    kapak_url = r2_yukle(klasor / "kapak.png", f"reels/{ad}-kapak.png")
    log(f"{ad}: R2'ye yüklendi")

    ig = os.environ["IG_USER_ID"]
    kap = graph("POST", f"{ig}/media", media_type="REELS", video_url=video_url, caption=caption,
                cover_url=kapak_url, share_to_feed="true")
    cid = kap["id"]
    for _ in range(60):  # en fazla ~10 dk
        durum = graph("GET", cid, fields="status_code").get("status_code")
        if durum == "FINISHED":
            break
        if durum == "ERROR":
            log(f"{ad}: container ERROR, yükleme durdu")
            raise SystemExit(1)
        time.sleep(10)
    else:
        log(f"{ad}: container zaman aşımı")
        raise SystemExit(1)
    yayin = graph("POST", f"{ig}/media_publish", creation_id=cid)
    link = graph("GET", yayin["id"], fields="permalink").get("permalink")
    log(f"{ad}: yayınlandı {link}")

    gp = KOK / "data" / "gecmis.json"
    g = json.loads(gp.read_text(encoding="utf-8"))
    for b in g["bolumler"]:
        if b["no"] == args.bolum:
            b.update(durum="yayinlandi", yayin_tarihi=datetime.now().strftime("%Y-%m-%d"), instagram_link=link)
    gp.write_text(json.dumps(g, ensure_ascii=False, indent=2), encoding="utf-8")
    shutil.move(str(klasor), str(KOK / "output" / "yayinlanan" / ad))


if __name__ == "__main__":
    main()
