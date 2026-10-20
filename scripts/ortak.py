"""Ortak yardımcılar: yollar, ayarlar, marka paleti."""
from pathlib import Path
import json

import yaml

KOK = Path(__file__).resolve().parent.parent


def ayarlar():
    return yaml.safe_load((KOK / "config.yaml").read_text(encoding="utf-8"))


def marka():
    return json.loads((KOK / "brand" / "brand.json").read_text(encoding="utf-8"))


def bolum_dizini(no):
    return KOK / "bolumler" / f"{int(no):03d}"


def senaryo(no):
    return json.loads((bolum_dizini(no) / "senaryo.json").read_text(encoding="utf-8"))


def hex_rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))
