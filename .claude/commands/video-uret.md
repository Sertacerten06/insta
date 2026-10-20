---
description: Havuzdan haber seç, senaryo yaz, ses + müzik + görsel üret, MP4 ve kapağı çıkar
---
CLAUDE.md'yi oku ve şu sırayla ilerle (PowerShell, proje kökünde):

1. `data/gecmis.json` → son bölüm no + 1 = N. Sıradaki Haritam özelliğini `haritam_ozellik_sirasi` listesinden döndür.
2. haritam.arpama.tr sayfasını oku; §4.1 ile fark varsa kullanıcıya bildir, yeni özellik uydurma.
3. `data/haber_havuzu.json` içinden kullanılmamış, 2 kaynakla doğrulanmış, en yüksek puanlı 2–3 haberi seç (önce Türkiye).
4. `bolumler/NNN/senaryo.md` (insan için, `bolumler/001/senaryo.md` formatında) ve `bolumler/NNN/senaryo.json` (makine için, `bolumler/001/senaryo.json` yapısında) yaz: 260–300 kelime, caption, kaynak satırları, kapak.
   Yeni bir sahne tipi gerekiyorsa `scripts/render/sahneler.py` içine ekle (haber sahneleri habere özeldir).
5. `python scripts/tts.py --bolum N`
6. `python scripts/muzik_uret.py --bolum N --sure 130`
7. `python scripts/render/render.py --bolum N --kareler 0,30,60,90,115` → kareleri incele, sorun varsa düzelt.
8. `python scripts/render/render.py --bolum N`
9. `python scripts/birlestir.py --bolum N`
10. `python scripts/kalite_kontrol.py --bolum N` → geçmezse dur, logs/ içine yaz.
11. `data/gecmis.json` ve `data/haber_havuzu.json` güncelle, değişiklikleri GitHub'a commit + push et.
