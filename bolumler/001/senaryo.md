# Bölüm #1 — "Yazılı Sorularını Yapay Zekâ mı Hazırlayacak?"

Seri adı: **Arpama Teknoloji Gündemi**
Süre hedefi: ~120 sn · Format: 1080×1920, 30 fps · Palet ve fontlar: `CLAUDE.md` §3
Öne çıkan Haritam özelliği: **Haftalık program** (`data/gecmis.json` → ilk kayıt)

## Fikir

Bölümün omurgası şu bağlantı: MEB'in yeni Ortak Yazılı Sınav Sistemi 5–7 ve 9–11. sınıfları kapsıyor, **12. sınıflar ise yok**, çünkü onların önünde YKS var. Video bunu bir oyun benzetmesiyle kuruyor: diğer sınıflar "yeni bölüm"e geçerken 12. sınıfların karşısında **"büyük boss: YKS"** duruyor. Boss'u yenmek için gereken harita da **YKS Haritam**.

İkinci haber (Japonya'nın Phobos görevi), retro uzay görselleriyle 8-bit tarza çok iyi oturuyor ve videoya "vay be" anı katıyor.

## Haberler ve doğrulama

| # | Haber | Kaynak 1 | Kaynak 2 | Not |
|---|---|---|---|---|
| 1 (TR) | MEB, 16 Ekim'de Ortak Yazılı Sınav Sistemi'ni tanıttı. Sistem 2026–27'nin 1. dönem 1. yazılılarından başlıyor; 5, 6, 7, 9, 10 ve 11. sınıflar. Açık uçlu sorular. Yapay zekâ destekli soru yazımı ve puanlama ileride sisteme eklenecek | meb.gov.tr (resmî duyuru) | Onedio (Nefes'e dayanarak) | Bazı haberlerde "10 sorunun 8'ini yapay zekâ hazırlayacak" geçiyor, ama **resmî duyuruda bu sayı yok**, yapay zekâ "planlanıyor" deniyor. Videoda sayı kullanılmıyor |
| 2 (Dünya) | JAXA, 20 Ekim'de (04:41 JST) MMX aracını H3 roketiyle fırlattı, ayrılma başarılı. Hedef Phobos'tan örnek alıp 2031'de Dünya'ya getirmek. Görevde CNES/DLR'nin Idefix gezgini var (30 kg altı) | global.jaxa.jp (resmî basın duyurusu) | Forbes, Tech Startups, Wikipedia | Video Cuma çıkarsa "bugün" deme, "20 Ekim'de" de |

## Sahne akışı

| Zaman | Sahne | Ekranda | Renkler | Ses |
|---|---|---|---|---|
| 0–4 sn | **Kanca** | Piksel sınav kâğıdı, üstünde yanıp sönen "?" ; büyük yazı: **"YAZILI SORULARINI YAPAY ZEKÂ MI HAZIRLAYACAK?"** | `zemin` arka plan, yazı `beyaz`, "YAPAY ZEKÂ" `altin` bantlı | "blip" + müziğin ilk vuruşu |
| 4–10 sn | **Açılış** | "PRESS START" yanıp söner → Arpama logosu piksel piksel belirir → "TEKNOLOJİ GÜNDEMİ · BÖLÜM 1" | Logo orijinal; "BÖLÜM 1" Sora 700 altın bantlı | Marka jingle'ı |
| 10–42 sn | **Haber 1 · Türkiye** | Üst etiket "🇹🇷 TÜRKİYE"; piksel okul binası; sınıf numaraları 5-6-7 / 9-10-11 sırayla "kilit açıldı" gibi yanıyor, **12 gri ve kilitli kalıyor**; robot ikonu "PLANLANIYOR" etiketiyle | Panel `zemin2` + `cizgi` kenarlık; açılan sınıflar `mavi`; 12 `soluk`; etiket `altin` | Her sınıf açılışında "coin" |
| 42–70 sn | **Haber 2 · Dünya** | Üst etiket "🌍 DÜNYA"; piksel roket kalkışı, yıldızlı arka plan, Mars ve küçük Phobos; minik gezgin; "2031 → DÜNYA" geri sayım çubuğu | Yıldızlar `mavi-buz`/`soluk`; roket alevi `altin` bantları; Mars yalnızca `kirmizi` + `altin-koyu` | Kalkış için gürültü kanalı "whoosh" |
| 70–105 sn | **Haritam bölümü** | Kilitli "12" kutusu ekrana gelir → "BÜYÜK BOSS: YKS" piksel boss ekranı → Haritam arayüzünün 8-bit hali: haftalık takvim, görevler günlere düşüyor, tikleniyor, "SERİ: 12 GÜN" sayacı, XP bar doluyor → "CORTEX · ÇOK YAKINDA" rozeti | Boss ekranı `zemin` + `kirmizi` vurgu; Haritam arayüzü `mavi` tonları; tikler ve seri `altin` | Boss için alçak bas notası, tiklerde "blip", sonda "level up" |
| 105–120 sn | **CTA / Kapanış** | **"haritam.arpama.tr"** + "ÜCRETSİZ BAŞLA ▶" düğmesi; altta "Takip et: @<kullanıcı_adı>"; "GAME SAVED ✓" | URL Sora 700 `beyaz`; düğme mavi 3 bant; "GAME SAVED" `altin` | Jingle'ın kapanış hâli, "game saved" efekti |

## Seslendirme metni (~280 kelime)

> **[Kanca]**
> Okuldaki yazılı sorularını yakında yapay zekâ mı hazırlayacak? Hazırsan başlıyoruz!
>
> **[Açılış]**
> Arpama Teknoloji Gündemi'ne hoş geldin, bu ilk bölümümüz. Yazılım ve teknoloji dünyasından en önemli gelişmeler, iki dakikada.
>
> **[Haber 1]**
> İlk durağımız Türkiye. Millî Eğitim Bakanlığı, 16 Ekim'de yeni Ortak Yazılı Sınav Sistemi'ni tanıttı. Sistem bu dönemin ilk yazılılarından itibaren 5, 6 ve 7 ile 9, 10 ve 11. sınıflarda kullanılacak. Sorular açık uçlu olacak ve her sınav döneminde binlerce yeni soru sisteme eklenecek. Peki yapay zekâ nerede? Bakanlık, soru yazımında ve açık uçlu cevapların puanlanmasında yapay zekâ desteğini ilerleyen aşamada sisteme katmayı planlıyor. Yani şimdilik bir plan, ama yön belli.
>
> **[Haber 2]**
> Şimdi rotamızı uzaya çeviriyoruz. Japonya Uzay Ajansı JAXA, 20 Ekim'de MMX aracını H3 roketiyle fırlattı. Hedef, Mars'ın küçük uydusu Phobos. Araç Phobos'a inecek, yüzeyden örnek toplayacak ve bu örnekleri 2031'de Dünya'ya getirecek. Yanında Fransa ve Almanya'nın geliştirdiği, otuz kilodan hafif Idefix adında minik bir gezgin de var.
>
> **[Haritam]**
> Bir şey fark ettin mi? Yeni sınav sisteminde 12. sınıflar yok. Çünkü onların karşısında büyük boss duruyor: YKS. Boss'u yenmek için bir haritaya ihtiyacın var. İşte YKS Haritam! Koçunun Excel programını yükle ya da kendin yaz, görevler günlere otomatik yerleşsin. Bitirdikçe işaretle, serini koru, gelişimini gör. Programındaki konular, konu özetleriyle kendiliğinden eşleşir. Üstelik Vertex'in yapay zekâsı Cortex de çok yakında Haritam'a geliyor.
>
> **[CTA]**
> Haritam tamamen ücretsiz ve telefonuna uygulama olarak eklenir. haritam nokta arpama nokta tr adresinden hemen başla. Arpama'yı takip etmeyi unutma, gelecek bölümde görüşürüz!

Okunuş notları (`config/okunus.json`): "JAXA" → "jaksa", "MMX" → "em em iks", "H3" → "ha üç", "YKS" → "ye ka se".

## Ekranda geçen kaynak satırı (Manrope 500, `soluk`)
- Haber 1: "Kaynak: MEB, Onedio"
- Haber 2: "Kaynak: JAXA, Forbes"

## Açıklama metni (caption)

```
Yazılı sorularını yapay zekâ mı hazırlayacak? 🕹️

Bu bölümde:
▸ MEB'in yeni Ortak Yazılı Sınav Sistemi
▸ Japonya Mars'ın uydusu Phobos'a yola çıktı
▸ Haritam: haftalık programın tek yerde

YKS'ye planlı hazırlanmak için ➜ haritam.arpama.tr (ücretsiz)

Kaynaklar: MEB, Onedio, JAXA, Forbes

#yks #yks2027 #teknoloji #yapayzeka #eğitim #uzay #teknolojihaberleri #arpama #haritam
```

## Kapak görseli
`zemin` arka plan, üstte Arpama logosu, ortada büyük piksel yazı "YAPAY ZEKÂ SORU MU HAZIRLAYACAK?" ("YAPAY ZEKÂ" altın bantlı), altta küçük piksel roket ve "BÖLÜM 1".

## Yayın öncesi kontrol
- Video Cuma (23 Ekim) çıkacaksa haber 1 bir haftalık olur. Kontrol et: MEB'den yeni bir açıklama geldi mi, yapay zekâ kısmı netleşti mi?
- Haritam sayfasını tekrar oku; haftalık program özelliği aynı şekilde duruyor mu?
