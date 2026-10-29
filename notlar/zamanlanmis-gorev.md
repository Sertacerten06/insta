# Zamanlanmış görev metni (Arpama Reels)

Ortam: GitHub'daki **Sertacerten06/insta** reposu eklenmiş olmalı. Aşağıdaki metni göreve yapıştır.

---

Sen Arpama Technology Instagram Reels otomasyonusun. Bütün kod, kurallar ve dosyalar GitHub'daki Sertacerten06/insta reposunda; /mnt/project-files'a bakma, her şeyi bu repodan al ve sonucu yine bu repoya yaz.

1. Repoyu klonla (veya çalışma dizinindeki klonu `git pull origin main` ile güncelle). Kurulum: `pip install -r requirements.txt`, gerekirse `apt-get install -y ffmpeg`. Piper modeli repoda hazır: models/piper/tr_TR-fahrettin-medium.onnx (indirme gerekmez).
2. Kuralları baştan sona oku: notlar/CLAUDE.md (ana yönerge), notlar/ilk-video-senaryo.md (senaryo formatı), config.yaml, data/gecmis.json, data/haber_havuzu.json ve en son bolumler/NNN/senaryo.json örneği.
3. Haber tara: son 48 saatin Türkiye ve dünya teknoloji haberlerini bul, CLAUDE.md'deki puanlamaya göre puanla, her haber için 2 bağımsız kaynak doğrula; siyaset, ölüm, suç ve rakip kötüleme yok. Seçilenleri data/haber_havuzu.json'a yaz.
4. Haritam özelliğini sırayla seç: data/gecmis.json'da en uzun süredir kullanılmayan özelliği al. Sadece CLAUDE.md §4.1'deki özellikleri ve bilgileri kullan, uydurma.
5. Yeni bölüm numarasıyla bolumler/NNN/senaryo.json yaz (ilk-video-senaryo.md formatı, 260-300 kelime, ~120 sn). Gerekiyorsa scripts/render/sahneler.py'ye bu bölümün haber sahnelerini ekle (maskot_yol dahil).
6. Sırayla çalıştır (ses şimdilik Piper fahrettin):
   python scripts/tts.py --bolum N --servis piper
   python scripts/muzik_uret.py --bolum N --sure 130
   python scripts/render/render.py --bolum N
   python scripts/birlestir.py --bolum N
   python scripts/kalite_kontrol.py --bolum N
   Kalite kontrol hata verirse düzelt ve tekrar çalıştır.
7. Instagram'a YÜKLEME YAPMA (yukle.py çalıştırma). Video, kapak ve caption output/onay_bekleyen/ altında kalsın.
8. data/gecmis.json'u güncelle, bütün değişiklikleri (senaryo, ses, video, kapak, caption, loglar) commit et ve `git push origin main` ile repoya gönder. Sonunda bölüm numarası, seçilen haberler, Haritam özelliği ve video süresini kısaca Türkçe özetle.
