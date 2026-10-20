---
description: Video üret + (onay modu kapalıysa) yükle
---
Önce `/video-uret` adımlarını uygula. Kalite kontrol geçtiyse ve config.yaml'da `onay_modu: false` ise
`python scripts/yukle.py --bolum N --onayla` çalıştır. Onay modu açıksa yükleme yapma; videonun
`output/onay_bekleyen/` içinde beklediğini kullanıcıya bildir.
