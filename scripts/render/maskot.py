"""Arpi: Arpama'nın 8-bit maskotu (brand/maskot/, 48x52 sanal piksel sprite'lar).

Sahnenin sağ altında, alt bilgi çizgisinin üstünde durur. Durum sahne türüne ve
seslendirmenin kelime zamanlarına göre seçilir: konuşurken ağzı oynar, boşlukta bekler.
"""
import json
from functools import lru_cache

from PIL import Image

from ortak import KOK

DIZIN = KOK / "brand" / "maskot"


@lru_cache(maxsize=1)
def _veri():
    return json.loads((DIZIN / "arpi.json").read_text(encoding="utf-8"))


def var_mi():
    return (DIZIN / "arpi.json").exists()


@lru_cache(maxsize=64)
def _kare(ad):
    return Image.open(DIZIN / _veri()["kareler"][ad]["dosya"]).convert("RGBA")


def kare_sec(anim, t):
    """anim adındaki animasyonun t saniyesindeki karesi (döngülü)."""
    kareler = _veri()["animasyonlar"][anim]["kareler"]
    toplam = sum(k["ms"] for k in kareler) / 1000
    u = (t % toplam) * 1000
    for k in kareler:
        if u < k["ms"]:
            return _kare(k["kare"])
        u -= k["ms"]
    return _kare(kareler[-1]["kare"])


HABER = {"haber_meb", "haber_jaxa", "haber_veri", "haber_slides", "haber_dolandirici", "haber_specs",
         "php_ne", "php_neden", "php_yapilacak"}


def durum(sahne, lt, sure, ses_son, kelimeler):
    """Sahne türü + yerel zaman -> animasyon adı."""
    konusuyor = any(k["bas"] - 0.02 <= lt < k["son"] for k in kelimeler)
    if sahne == "kanca":
        return "dusun" if lt < 1.2 else ("konus" if konusuyor else "saskin")
    if sahne == "acilis":
        return "selam"
    if sahne == "cta":
        if lt >= ses_son + 0.2:
            return "selam"
        return "isaret" if not konusuyor else "konus"
    if sahne.startswith("haritam"):
        if lt >= sure - 1.6:
            return "levelup"
        return "konus" if konusuyor else "bekle"
    if sahne in HABER and lt < 0.8:
        return "saskin" if sahne == "php_ne" else "sevin"
    return "konus" if konusuyor else "bekle"


def ciz(im, x, ayak_y, anim, t):
    """im: sanal kare (RGB). Arpi'nin ayak noktası (x, ayak_y)'ye gelir."""
    sp = kare_sec(anim, t)
    ax, ay = _veri()["ayak_noktasi"]["x"], _veri()["ayak_noktasi"]["y"]
    im.paste(sp, (x - ax, ayak_y - ay), sp)
