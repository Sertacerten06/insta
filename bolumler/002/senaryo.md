# Bölüm #2 — "Ankara'ya Dev Veri Merkezi, Sunumlara Yapay Zekâ"

Seri adı: **Arpama Teknoloji Gündemi**
Süre hedefi: ~120 sn · Format: 1080×1920, 30 fps · Palet ve fontlar: `CLAUDE.md` §3
Öne çıkan Haritam özelliği: **Konu özetleri** (`data/gecmis.json` → 2. kayıt)

## Fikir

Bölümün omurgası "bilgi" teması: Türkiye veriyi saklamak için dev bir veri merkezi kuruyor, dünyada yapay zekâ
sunumu bile hazırlıyor. Ama öğrencinin asıl derdi bilginin çokluğu: hangi konuyu nereden çalışacak?
Cevap: Haritam'ın konu özetleri, haftalık programla otomatik eşleşiyor.

## Haberler ve doğrulama

| # | Haber | Kaynak 1 | Kaynak 2 | Not |
|---|---|---|---|---|
| 1 (TR) | Bakan Kacır 20 Ekim'de Ankara Temelli (Başkent OSB) veri merkezinin temelini attı. 1. aşama 450 milyon $, 22 MW; 2. aşama 900 milyon $; tüm aşamalarda toplam 4,1 milyar $. 2030'a kadar Türkiye'nin kurulu veri merkezi gücü en az 1 GW hedefi | LOG (20.10.2026) | Hürriyet (20.10.2026) | Yatırımcı şirket adı haberlerde net değil, videoda şirket adı geçmiyor |
| 2 (Dünya) | OpenAI, ChatGPT Slides'ı 16 Ekim'den itibaren yaymaya başladı: sohbetten, dosyadan, taslaktan sunum; eş zamanlı düzenleme; PowerPoint/PDF/Google Slides dışa aktarma. Şimdilik Pro, Business, Enterprise | Webtekno (20.10.2026, ChatGPT resmî X hesabına dayanarak) | Digital Applied | Plus/Go/Free planlarında yok; videoda "ücretsiz planda yok" deniyor |

Puanlama: Haber 1 = 9 (TR +3, 48 saat +2, yapay zekâ altyapısı +2, anlaşılır +2). Haber 2 = 6 (48 saat +2, öğrenci/sunum +2, genç kitle +2).
Elenenler: Google "Gemini Prompt Arena" (tek kaynak, tanıtım içerikli), YÖK Yapay Zekâ Okulu (başvuru 20 Ekim'de kapandı).

## Sahne akışı

| Sahne | Ekranda | Ses |
|---|---|---|
| Kanca | 3 piksel sunucu dolabı, yanıp sönen LED'ler; "ANKARA'YA / 4,1 MİLYAR $ / VERİ MERKEZİ!" | blip |
| Açılış | PRESS START → logo → "TEKNOLOJİ GÜNDEMİ · BÖLÜM 2" | jingle |
| Haber 1 | TR etiketi; sunucu dolapları aşama aşama çoğalır; 450 MİLYON $ / 22 MW / 4,1 MİLYAR $; veri paketleri akar; "2030 HEDEFİ: EN AZ 1 GW" çubuğu | coin, level up |
| Haber 2 | DÜNYA etiketi; SOHBET / DOSYA / TASLAK → slaytlar dizilir; iki imleç "AYNI ANDA DÜZENLE"; PPTX/PDF düğmeleri; "ŞİMDİLİK: PRO · BUSINESS · ENTERPRISE" | blip, tik, coin |
| Haritam | Kitap yığını büyür, "BİLGİ ÇOK / ZAMAN AZ" → glitch → Haritam: KONU ÖZETLERİ, TYT/AYT sekmeleri, konu kartları; "PROGRAM · BUGÜN: MAT — EŞLEŞTİ"; "EKSTRA KAYNAK / SAYFA SAYFA" üstü çizili; "CORTEX · ÇOK YAKINDA" | boss, coin, level up |
| CTA | haritam.arpama.tr, ÜCRETSİZ BAŞLA, GAME SAVED | jingle, game saved |

## Seslendirme metni (242 kelime)

Makine için tam metin: `bolumler/002/senaryo.json`. Okunuş eklemeleri (`config/okunus.json`): OpenAI → "open ey ay",
ChatGPT → "çet ci pi ti", Slides → "slayds", PowerPoint → "pavır point", PDF → "pe de fe", Business → "biznıs", Enterprise → "entırprayz".

## Ekranda geçen kaynak satırı
- Haber 1: "Kaynak: LOG, Hürriyet"
- Haber 2: "Kaynak: Webtekno, Digital Applied"

## Yayın öncesi kontrol
- haritam.arpama.tr bulut ortamından açılamadı; konu özetleri bilgisi CLAUDE.md §4.1'den alındı. Yayından önce sayfaya bakıp "programdaki konularla otomatik eşleşir" ifadesinin geçerli olduğunu doğrula.
- ChatGPT Slides plan kapsamı değişmiş olabilir; yayın günü kontrol et.
