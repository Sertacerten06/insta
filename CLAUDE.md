# Arpama Reels Otomasyonu — CLAUDE.md

Bu dosya, Claude Code'un bu projede nasıl çalışacağını tanımlar. Her oturumda önce bu dosyayı oku ve buradaki kurallara uy.

## 1. Projenin amacı

Arpama Technology'nin Instagram sayfası için **haftada 2 adet, ~2 dakikalık, 8-bit / retro tarzda dikey video (Reels)** üretmek ve otomatik yüklemek.

- Videoların **ana önceliği her zaman YKS Haritam'ın (https://haritam.arpama.tr) tanıtımıdır.**
- İçerik: gündemdeki yazılım ve teknoloji gelişmeleri. **Önce Türkiye, sonra dünya.**
- Görsel, seslendirme, arka plan müziği, efektler, altyazı, açıklama metni ve yükleme: hepsi sistem tarafından otomatik yapılır.
- Görünüm her videoda aynı mantıkta olur: Arpama renkleri, aynı açılış, aynı kapanış, aynı yerleşim.

## 2. Takvim

| İş | Sıklık | Açıklama |
|---|---|---|
| Gündem taraması | Her 2 günde bir | Haberleri topla, puanla, `data/haber_havuzu.json` dosyasına ekle |
| Video üretimi + yükleme | Haftada 2 (Salı ve Cuma, 19:00 TR saati) | Havuzdaki en güncel ve en yüksek puanlı haberlerle video üret |

- Saat dilimi: `Europe/Istanbul`.
- Kullanıcı Windows + PowerShell kullanıyor. Zamanlama için **Windows Görev Zamanlayıcı** ile `claude -p "<komut>"` (headless mod) çalıştırılır. Alternatif olarak GitHub Actions da kurulabilir.

## 3. Marka ve renk paleti

Renkler ve fontlar arpama.tr'nin kaynak kodundan ve logodan çıkarıldı. **Bu bölüm kesindir; başka renk uydurma.** Ana hava: neredeyse siyah zemin, Arpama mavisi vurgular, logodan gelen **altın ("AR")** ve **gümüş ("PAMA")** metalik tonlar.

### 3.1 Sitenin orijinal renkleri (referans)

**CSS değişkenleri**
| Değişken | Kod | Sitedeki kullanım |
|---|---|---|
| `--bg` | `#070A10` | Sayfa zemini (neredeyse siyah) |
| `--panel` | `#0E1420` | Kart ve panel zemini |
| `--line` | `#1E2D46` | Çizgiler, kenarlıklar |
| `--gold` | `#2F6FE0` | Ana vurgu rengi (adı "gold" ama mavi) |
| `--gold2` | `#7AA9F3` | Açık mavi vurgu |
| `--silver` | `#D9DDE3` | Ana yazı rengi |
| `--mut` | `#9AA0AB` | Soluk ve ikincil yazı |

**Ek renkler**
- Altın: `#F2C14E`, `#FFE38F` → `#D4A017` geçişi
- Maviler: `#6F9DF0`, `#2A5AA8`, `#A9C4EA`, `#9FB6DC`, `#CFE0FF`
- Koyu zeminler: `#080D16`, `#0A101A`, `#0F1624`, `#111B2B`, `#06101F`
- Açık tonlar: `#E9EDF5`, `#C9CED6`, `#FFFFFF`
- Uyarı/kırmızı: `#E0705C`
- Geçişler: kart `linear-gradient(145deg, #0F1624, #0A101A)`, gümüş yazı `linear-gradient(#FFF, #C9CED6)`, altın yazı `linear-gradient(#FFE38F, #D4A017)`

**Logo (resimden örneklendi, yaklaşık değerler)**
| Bölüm | Renkler (parlaktan koyuya) |
|---|---|
| "AR" işareti (altın) | `#F7E6A7`, `#DFC480`, `#B69555`, `#9A773B` |
| "PAMA" yazısı (gümüş) | `#F2F1E9`, `#E1D9C0`, `#CAC2AC`, `#979185` |
| "TECHNOLOGY" | `#B8B9BA`, `#626465` |
| Logo zemini | `#23262B` |

Logoyu videoda **yeniden çizme veya renklerini değiştirme**; `brand/arpama-logo.png` dosyasını olduğu gibi kullan (sadece nearest-neighbor ile pikselleştirilmiş bir "8-bit sürüm" ayrıca üretilebilir, ama orijinalin yerine geçmez).

### 3.2 Video için 8-bit palet (16 renk, sabit)
Retro his için videoda **sadece bu 16 renk** kullanılır. Sitedeki yumuşak gradyanlar videoda **kademeli bantlara** (2–4 adım) veya dither desenine çevrilir; yumuşak gölge ve bulanıklık yok.

| # | Ad | Hex | Kaynak | Videoda kullanım |
|---|---|---|---|---|
| 0 | `zemin` | `#070A10` | `--bg` | Ana arka plan |
| 1 | `zemin2` | `#0E1420` | `--panel` | Paneller, haber kutuları |
| 2 | `zemin3` | `#111B2B` | ek koyu | Panel üst bandı, piksel gölge |
| 3 | `cizgi` | `#1E2D46` | `--line` | Piksel kenarlıklar, ızgara, scanline |
| 4 | `mavi-koyu` | `#2A5AA8` | ek mavi | Mavi bant geçişinin koyu adımı |
| 5 | `mavi` | `#2F6FE0` | `--gold` | **Ana vurgu**: başlık kutuları, XP bar, düğmeler |
| 6 | `mavi-acik` | `#7AA9F3` | `--gold2` | İkincil vurgu, ışıltı, seçili öğe |
| 7 | `mavi-buz` | `#CFE0FF` | ek mavi | Yıldızlar, parlama pikselleri |
| 8 | `gumus` | `#D9DDE3` | `--silver` | **Ana yazı rengi** |
| 9 | `beyaz` | `#FFFFFF` | ek açık | En önemli başlıklar, gümüş bandın parlak adımı |
| 10 | `gumus-koyu` | `#C9CED6` | ek açık | Gümüş bandın koyu adımı |
| 11 | `soluk` | `#9AA0AB` | `--mut` | Kaynak adları, tarih, küçük notlar |
| 12 | `altin-acik` | `#FFE38F` | altın geçiş | Altın bandın parlak adımı |
| 13 | `altin` | `#F2C14E` | ek altın | **Dikkat çeken kelimeler**, "YENİ", yıldız, coin, ödül |
| 14 | `altin-koyu` | `#D4A017` | altın geçiş | Altın bandın koyu adımı, altın kenarlık |
| 15 | `kirmizi` | `#E0705C` | uyarı | "SON DAKİKA" etiketi, uyarı (çok az kullan) |

**Renk dengesi (her karede yaklaşık):** %65 koyu zemin (0–3), %20 mavi tonlar (4–7), %10 gümüş/beyaz yazı (8–11), %5 altın (12–14). Altın "ödül" rengidir, az kullanıldıkça değerli görünür. Kırmızı sadece gerektiğinde.

**8-bit geçiş kuralları:**
- Altın yazı/öğe: üstten alta `#FFE38F` → `#F2C14E` → `#D4A017` (3 yatay bant)
- Gümüş yazı/öğe: `#FFFFFF` → `#D9DDE3` → `#C9CED6`
- Kart/panel: `#111B2B` üst bant + `#0E1420` gövde, `#1E2D46` 1 piksellik kenarlık
- Mavi düğme/kutu: `#7AA9F3` üst kenar (ışık) + `#2F6FE0` gövde + `#2A5AA8` alt kenar (gölge)

**Haritam bölümü:** Haritam'ın kendi tema rengi `#2B44B8`. Paleti bozmamak için Haritam bölümünde de `#2F6FE0` kullan; `#2B44B8` yalnızca Haritam logosu/ekran görüntüsü içinde kendiliğinden geçiyorsa kalabilir.

`brand/brand.json`:
```json
{
  "palette": {
    "zemin": "#070A10", "zemin2": "#0E1420", "zemin3": "#111B2B", "cizgi": "#1E2D46",
    "mavi_koyu": "#2A5AA8", "mavi": "#2F6FE0", "mavi_acik": "#7AA9F3", "mavi_buz": "#CFE0FF",
    "gumus": "#D9DDE3", "beyaz": "#FFFFFF", "gumus_koyu": "#C9CED6", "soluk": "#9AA0AB",
    "altin_acik": "#FFE38F", "altin": "#F2C14E", "altin_koyu": "#D4A017", "kirmizi": "#E0705C"
  },
  "bantlar": {
    "altin": ["#FFE38F", "#F2C14E", "#D4A017"],
    "gumus": ["#FFFFFF", "#D9DDE3", "#C9CED6"],
    "mavi": ["#7AA9F3", "#2F6FE0", "#2A5AA8"]
  },
  "logo_renkleri": {
    "ar_altin": ["#F7E6A7", "#DFC480", "#B69555", "#9A773B"],
    "pama_gumus": ["#F2F1E9", "#E1D9C0", "#CAC2AC", "#979185"],
    "technology": ["#B8B9BA", "#626465"],
    "zemin": "#23262B"
  },
  "fonts": {
    "piksel": "Pixelify Sans",
    "piksel_yedek": "VT323",
    "marka": "Sora",
    "metin": "Manrope"
  },
  "logo": "brand/arpama-logo.png",
  "haritam_logo": "brand/haritam-logo.png",
  "handle": "@<instagram_kullanici_adi>",
  "cta_url": "haritam.arpama.tr"
}
```

### 3.3 Tipografi
Sitenin fontları:
| Font | Sitede | Kalınlıklar |
|---|---|---|
| **Sora** | Başlıklar, logo yazısı, düğmeler | 500, 600, 700 |
| **Manrope** | Gövde metni, küçük etiketler | 400, 500, 600 |
| Segoe UI / Arial | Bazı dekoratif yazılarda yedek | 300, 700 |

Sitede gövde 16px/1.6 Manrope, ana başlıklar Sora 700.

Videoda kullanım (retro + marka dengesi):
- **Piksel font (`Pixelify Sans`, yedek `VT323`):** haber başlıkları, altyazılar, HUD, "PRESS START / LEVEL UP / GAME SAVED" gibi oyun etiketleri. Videonun retro havasını bu taşır.
- **Sora 700:** sadece marka anları: açılıştaki "ARPAMA TECHNOLOGY" yazısı, kapanıştaki `haritam.arpama.tr` ve "ücretsiz başla" CTA'sı. Altın veya gümüş bantlı uygulanabilir. Böylece marka sitedekiyle aynı görünür.
- **Manrope 500:** sadece küçük kaynak satırları ve tarih (çok küçük piksel font okunmaz).
- Fontların hepsi Google Fonts'tan; projeye `brand/fonts/` içine indirilip yerelden yüklensin.
- **Türkçe karakterleri (ç ğ ı İ ö ş ü Ç Ğ Ö Ş Ü) mutlaka test et.** Bir karakter eksikse o yazıda yedek fonta geç.
- `Press Start 2P` sadece Türkçe karakter içermeyen kısa İngilizce etiketlerde kullanılabilir.
- Piksel fontları tam sayı katlarında ölçekle, anti-aliasing kapalı. Sora/Manrope normal (yumuşak) render edilir.

### 3.4 Görsel dil (8-bit kuralları)
- Çözünürlük: **1080×1920 (9:16), 30 fps.** Sahneler içeride 270×480 veya 360×640 "sanal piksel" ızgarasında çizilip **nearest-neighbor** ile büyütülür.
- Hafif CRT tarama çizgisi (scanline) efekti, %10–15 opaklık. Abartma, metin okunabilir kalsın.
- Geçişler: piksel dağılma (dither), kare kare kayma, "glitch" efekti. Yumuşak fade yerine adımlı (stepped) animasyon.
- Kapak görseli ve açılış: `zemin` üzerinde altın "AR" + gümüş "PAMA" hissi; başlık Sora 700, altın bantlı.
- Tekrarlanan öğeler: piksel yıldızlı arka plan (`mavi-buz` ve `soluk` pikseller), HUD tarzı üst bar (sol: Arpama logosu, sağ: tarih), alt bilgi çubuğu, ilerleme çubuğu "XP bar" gibi.
- Başka şirketlerin logolarını, ürün fotoğraflarını veya telifli görselleri kullanma. Haberleri piksel ikonlar ve metinle anlat (ör. piksel çip, robot, telefon, bulut ikonları). İkonları kodla üret.
- Instagram arayüzü alttaki ve sağdaki alanları kapatır: önemli metinleri **üstten 220 px, alttan 380 px, sağdan 140 px** güvenli alanın içinde tut.

## 4. Video yapısı (her videoda aynı şablon, toplam ~120 sn)

| Zaman | Bölüm | İçerik |
|---|---|---|
| 0–4 sn | **Kanca** | Tek cümlelik merak uyandıran başlık, "PRESS START" animasyonu |
| 4–10 sn | **Açılış** | Arpama logosu piksel animasyonla belirir, "Teknoloji Gündemi #<bölüm no>" |
| 10–70 sn | **Gündem** | 2–3 haber. Her biri ~20 sn: başlık kutusu + 2–3 kısa madde + kaynak adı. Önce Türkiye haberleri |
| 70–105 sn | **Haritam bölümü** | Her videoda zorunlu. Haritam'ın bir özelliği bir "oyun bölümü" gibi anlatılır (aşağıya bak) |
| 105–120 sn | **Kapanış / CTA** | "haritam.arpama.tr — ücretsiz başla", takip et çağrısı, "GAME SAVED" animasyonu |

- Haritam'ı yalnızca sonda değil, uygun düştüğünde haber bölümünde de bağla (ör. yapay zekâ haberi → "Cortex yapay zekâ Haritam'a çok yakında geliyor").
- Seslendirme metni ~120 sn için **yaklaşık 260–300 kelime** olsun. Seslendirme bittikten sonra video süresini sese göre ayarla (110–130 sn aralığı kabul edilir).

### 4.1 Haritam hakkında doğru bilgiler (sadece bunları kullan)
YKS Haritam, YKS'ye hazırlanan öğrenciler için bir çalışma uygulamasıdır. Arpama Technology × Vertex iş birliğiyle geliştirildi.
- Haftalık program (koçun Excel programını yükleme ya da kendin yazma)
- TYT/AYT konu özetleri (programdaki konularla otomatik eşleşir)
- Kendini test et: kartlarla tekrar, bilinmeyenler daha sık gelir
- Deneme takibi: net grafiği, puan tahmini, hedefe kalan mesafe
- Yanlış defteri: soru fotoğrafı + neden, aralıklı tekrar
- Odak sayacı (Pomodoro), günlük odak süresi ve seri
- Dershaneler/kurumlar için öğrenci takip paneli (görev tamamlama, netler, Excel'den program yükleme, öğrenciye not/bildirim, davet kodu, CSV dışa aktarma)
- Vertex'in yapay zekâsı **Cortex** "çok yakında": konu özetleri, yanlış analizi, kişisel öneriler
- Ücretsiz, telefona uygulama olarak eklenir, telefon ve bilgisayarda çalışır

Bu listede olmayan bir özellik, sayı, kullanıcı rakamı veya vaat **uydurma**. Yeni özellik eklendiğinde bu bölüm güncellenecek; her üretimden önce haritam.arpama.tr sayfasını tekrar okuyup değişiklik var mı kontrol et.

Her videoda Haritam özelliklerinden **farklı birini** öne çıkar; hangi özelliğin kullanıldığını `data/gecmis.json` dosyasına yaz ve sırayla döndür.

## 5. Gündem toplama

### 5.1 Kaynaklar (önce Türkiye)
- Türkiye: Webrazzi, ShiftDelete.Net, DonanımHaber, LOG, Teknoloji haberleri yapan büyük gazetelerin teknoloji bölümleri, TÜBİTAK / BTK / Sanayi ve Teknoloji Bakanlığı duyuruları, TEKNOFEST duyuruları
- Dünya: The Verge, TechCrunch, Ars Technica, Hacker News (ön sayfa), GitHub Blog, büyük yapay zekâ şirketlerinin resmî blogları
- Mümkün olduğunda RSS kullan; site taramadan önce `robots.txt` kurallarına uy.

### 5.2 Seçim ve puanlama
Her haber için 0–10 puan ver ve gerekçesini yaz:
- Türkiye ile ilgiliyse +3
- Son 48 saat içindeyse +2
- Öğrencileri, eğitimi, sınavları, yapay zekâ ile öğrenmeyi ilgilendiriyorsa +2 (Haritam'a bağlanabilir)
- Genç kitle için anlaşılır ve ilginçse +2
- Sadece söylenti, tek kaynaklı veya doğrulanamıyorsa −5 (kullanma)

Kurallar:
- **Her haber en az 2 bağımsız kaynakla doğrulanmalı.** Doğrulanamayan haber videoya girmez.
- Siyasi, ölüm/felaket, suç ve tartışmalı konuları seçme. Rakip şirketleri kötüleme.
- Haber metinlerini kopyalama; kendi cümlelerinle, kısa ve sade anlat. Kaynak adlarını videoda ve açıklamada belirt.
- Aynı haberi iki kez kullanma (`data/gecmis.json` ile kontrol et).

## 6. Seslendirme (TTS)

- Dil: Türkçe, enerjik ama abartısız, genç kitleye hitap eden "sen" dili.
- Başlangıç seçeneği: `edge-tts` (ücretsiz), ses: `tr-TR-AhmetNeural` veya `tr-TR-EmelNeural`. Kelime zaman damgalarını kaydet (altyazı senkronu için).
- Daha kaliteli seçenek: ElevenLabs (çok dilli model) veya Azure TTS. API anahtarı `.env` içinde.
- Her videoda **aynı ses** kullanılsın (marka tutarlılığı). Ses `config.yaml` içinde ayarlanır.
- Kısaltmaları ve İngilizce terimleri okunuşa göre düzelt (ör. "API" → "ey-pi-ay", "GPU" → "ci-pi-yu"). Sözlüğü `config/okunus.json` dosyasında tut.
- Ses seviyesi: -16 LUFS civarına normalize et.

## 7. Müzik ve efektler (tamamen kendi üretimimiz)

- Telif riski olmaması için **arka plan müziğini kod ile üret**: Python + numpy ile kare dalga, üçgen dalga ve gürültü kanallarından oluşan chiptune (NES tarzı 4 kanal) synth yaz.
- Her videoda aynı "marka melodisi" (jingle) açılış ve kapanışta çalsın; arka plan döngüsü videodan videoya küçük varyasyonlarla değişebilir (tempo 110–130 BPM, majör ton, pozitif hava).
- Efektler de kodla: geçiş "blip", madde çıkınca "coin", Haritam bölümünde "level up", kapanışta "game saved".
- Seslendirme konuşurken müzik otomatik kısılsın (ducking): müzik konuşma altında yaklaşık -22 dB, boşluklarda -14 dB. FFmpeg `sidechaincompress` veya mixing kodu ile.

## 8. Altyazı

- Seslendirme ile senkron, büyük piksel fontlu altyazı videoya gömülü (burned-in).
- Aynı anda en fazla 2 satır, satır başına ~20 karakter. Önemli kelime `altin` (`#F2C14E`) renginde, normal metin `gumus` (`#D9DDE3`), 2 piksel `zemin` (`#070A10`) kenar çizgisiyle.
- Zaman damgası TTS'ten gelmiyorsa `whisper` (Türkçe) ile hizala.

## 9. Teknik yığın (öneri)

- **Video render:** Remotion (React/TypeScript) — şablon tabanlı, her videoda aynı tasarım için ideal. Alternatif: Python (Pillow ile kare üretimi + FFmpeg).
- **Ses:** Python (edge-tts, numpy, pydub), FFmpeg
- **Haber toplama:** Python (feedparser, httpx)
- **Metin yazımı:** Claude Code'un kendisi (senaryo, açıklama, hashtag)
- **Dosya barındırma:** Cloudflare R2 (Instagram API videoyu herkese açık bir URL'den çeker)
- **Yükleme:** Instagram Graph API

Çıktı formatı: MP4, H.264, AAC 48 kHz, 1080×1920, 30 fps. Ayrıca bir kapak görseli (1080×1920, PNG) üret: başlık + Arpama logosu, palet renkleriyle.

## 10. Instagram'a yükleme

Gereksinimler (kullanıcı bir kere kuracak):
1. Instagram hesabı **Profesyonel (İşletme veya İçerik Üreticisi)** olmalı ve bir Facebook Sayfasına bağlı olmalı.
2. developers.facebook.com üzerinde bir Meta uygulaması, Instagram içerik yayınlama izinleri ve uzun ömürlü erişim token'ı.
3. `.env` içinde: `IG_USER_ID`, `IG_ACCESS_TOKEN`, `R2_*` anahtarları.

Akış:
1. MP4'ü R2'ye yükle, herkese açık URL al.
2. `POST /{ig-user-id}/media` ile `media_type=REELS`, `video_url`, `caption`, (opsiyonel) `cover_url` gönder → container id.
3. Container durumu `FINISHED` olana kadar bekle (periyodik kontrol).
4. `POST /{ig-user-id}/media_publish` ile yayınla.
5. Sonucu ve gönderi linkini `data/gecmis.json` ve `logs/` içine yaz.

Notlar:
- Güncel limitleri (video süresi, günlük gönderi sayısı, dosya boyutu) her kurulumda Meta'nın resmi dokümanından kontrol et.
- Token süresi dolmadan yenile; dolmak üzereyse kullanıcıya uyarı bırak.
- Token ve anahtarları asla koda, loga veya commit'e yazma. `.env` mutlaka `.gitignore` içinde.

### 10.1 Onay modu
`config.yaml` içinde `onay_modu: true` iken video üretilir, `output/onay_bekleyen/` klasörüne konur ve yükleme yapılmaz; kullanıcı onay verince yüklenir. İlk birkaç hafta bu mod açık kalsın. Kullanıcı açıkça `onay_modu: false` yapınca tam otomatik yükleme başlar.

## 11. Açıklama metni (caption) ve hashtag

Şablon:
```
<Kanca cümlesi> 🕹️

Bu bölümde:
▸ <haber 1 kısa başlık>
▸ <haber 2 kısa başlık>
▸ Haritam: <öne çıkan özellik>

YKS'ye planlı hazırlanmak için ➜ haritam.arpama.tr (ücretsiz)

Kaynaklar: <kaynak adları>

#yks #yks2027 #teknoloji #yazılım #yapayzeka #teknolojihaberleri #arpama #haritam
```
- Hashtag sayısı 5–10 arası. Değişmeyenler: `#arpama #haritam #yks`.
- Emoji az ve retro temalı (🕹️ 👾 ⭐ 🎮).

## 12. Klasör yapısı

```
arpama-reels/
├── CLAUDE.md
├── config.yaml            # ses, takvim, onay_modu, video süresi
├── .env                   # anahtarlar (git'e girmez)
├── brand/                 # brand.json, logolar, fontlar
├── config/okunus.json     # TTS okunuş sözlüğü
├── scripts/
│   ├── haber_topla.py
│   ├── senaryo_uret.py    # Claude ile senaryo + caption
│   ├── tts.py
│   ├── muzik_uret.py      # chiptune synth
│   ├── render/            # Remotion projesi
│   ├── birlestir.py       # ses + video + altyazı (FFmpeg)
│   └── yukle.py           # R2 + Instagram Graph API
├── data/
│   ├── haber_havuzu.json
│   └── gecmis.json        # kullanılan haberler, Haritam özellikleri, bölüm no
├── output/
│   ├── onay_bekleyen/
│   └── yayinlanan/
└── logs/
```

## 13. Komutlar (slash command olarak `.claude/commands/` içine)

- `/haber-topla` — gündemi tara, puanla, havuza ekle
- `/video-uret` — havuzdan haber seç, senaryo yaz, ses + müzik + görsel üret, MP4 ve kapağı çıkar
- `/yukle` — onay bekleyen veya yeni üretilen videoyu Instagram'a yükle
- `/tam-dongu` — üret + (onay modu kapalıysa) yükle
- `/onizle` — son videonun özetini, senaryosunu ve kare örneklerini göster

## 14. Kalite kontrol (her videodan önce zorunlu)

Yayına çıkmadan önce şunları kontrol et, biri başarısızsa yükleme yapma ve `logs/` içine nedenini yaz:
- [ ] Süre 110–130 sn, çözünürlük 1080×1920, ses ve görüntü senkron
- [ ] Haritam bölümü var ve sadece 4.1'deki doğru bilgileri içeriyor
- [ ] Her haber en az 2 kaynakla doğrulandı, kaynaklar caption'da yazıyor
- [ ] Türkçe karakterler doğru görünüyor, yazım hatası yok
- [ ] Metinler güvenli alanın içinde
- [ ] Sadece marka paletindeki renkler kullanıldı
- [ ] Telifli görsel, logo veya müzik yok
- [ ] Müzik konuşmayı bastırmıyor
- Videodan 5 kare (0, 30, 60, 90, 115. saniye) çıkarıp bak; görsel bir sorun varsa düzelt.

## 15. Genel davranış kuralları

- Önceliği unutma: **Haritam tanıtımı > Türkiye teknoloji gündemi > dünya teknoloji gündemi.**
- Emin olmadığın bilgiyi videoya koyma.
- Bir adım hata verirse (API, render, TTS) en fazla 2 kez yeniden dene, sonra dur ve log bırak; yarım video yükleme.
- Yeni kütüphane eklerken `requirements.txt` / `package.json` güncelle.
- Kullanıcı Windows kullanıyor: komutları PowerShell uyumlu yaz, yol ayırıcılarına dikkat et.

## 16. Eklenecekler (kullanıcı dolduracak)

- [ ] Instagram kullanıcı adı
- [ ] Arpama logosu ve Haritam logosu dosyaları (`brand/`)
- [ ] Tercih edilen seslendirme sesi (kadın/erkek, servis)
- [ ] Sabit bir maskot/karakter olacak mı? (ör. piksel robot)
- [ ] Yayın günleri/saatleri değişikliği
- [ ] Diğer ek istekler
