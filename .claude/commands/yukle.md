---
description: Onay bekleyen videoyu Instagram'a yükle
---
`output/onay_bekleyen/` içindeki en eski bölümü bul. `logs/kalite_bolum-NNN.txt` "GEÇTİ" değilse yükleme.
config.yaml'da `onay_modu: true` ise kullanıcı açıkça onay vermeden `--onayla` kullanma.
Komut: `python scripts/yukle.py --bolum N --onayla`. Sonucu (link) kullanıcıya bildir, gecmis.json değişikliğini commit + push et.
