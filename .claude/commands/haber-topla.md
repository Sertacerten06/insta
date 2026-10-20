---
description: Gündemi tara, puanla, havuza ekle
---
CLAUDE.md §5'e göre: önce Türkiye kaynakları, sonra dünya (RSS öncelikli, robots.txt'e uy).
Her haber için 0–10 puan + gerekçe, en az 2 bağımsız kaynak; siyaset/felaket/suç/tartışmalı konu yok.
`data/gecmis.json`'da kullanılmış haberleri atla. Sonuçları `data/haber_havuzu.json` içine
(`bolge`, `tarih`, `puan`, `gerekce`, `baslik`, `kaynaklar`, `kullanildi: null`) ekle, commit + push et.
