# Arpama Reels Otomasyonu

Arpama Technology Instagram sayfası için haftada 2 adet, ~2 dakikalık, 8-bit tarzda dikey video (Reels).
Kurallar ve marka rehberi: [CLAUDE.md](CLAUDE.md). Bölüm senaryoları: `bolumler/NNN/`.

## Kurulum (Windows + PowerShell)

```powershell
python -m pip install -r requirements.txt
# FFmpeg gerekli: winget install Gyan.FFmpeg
Copy-Item .env.example .env   # Instagram ve R2 anahtarlarını doldur (git'e girmez)
```

## Bir bölüm üretmek

```powershell
python scripts/tts.py --bolum 1                    # seslendirme (edge-tts, kelime zaman damgalı)
python scripts/muzik_uret.py --bolum 1 --sure 130  # chiptune müzik + efektler (kodla üretilir)
python scripts/render/render.py --bolum 1          # 8-bit görüntü + kapak
python scripts/birlestir.py --bolum 1              # ducking, -16 LUFS, MP4; onay modunda output/onay_bekleyen/
python scripts/kalite_kontrol.py --bolum 1         # CLAUDE.md §14, 5 kare + rapor (logs/)
python scripts/yukle.py --bolum 1 --onayla         # sadece onay verince: R2 + Instagram Graph API
```

Claude Code içinden: `/video-uret`, `/yukle`, `/tam-dongu`, `/onizle`, `/haber-topla` (`.claude/commands/`).

## Yapı

| Yol | İçerik |
|---|---|
| `config.yaml` | onay_modu, ses, takvim, video ayarları |
| `brand/` | `brand.json` (16 renk palet), fontlar; logolar buraya (`arpama-logo.png`, `haritam-logo.png`) |
| `config/okunus.json` | TTS okunuş sözlüğü (JAXA → jaksa ...) |
| `scripts/render/` | Python + Pillow renderer: `cizim.py` (palet, panel, yazı), `ikonlar.py` (piksel ikonlar), `sahneler.py` (kanca, açılış, haberler, Haritam, kapanış) |
| `bolumler/NNN/` | senaryo (md + json), ses, kapak, MP4, kontrol kareleri |
| `data/` | haber havuzu, geçmiş (bölüm no, Haritam özelliği rotasyonu) |
| `output/onay_bekleyen/` | onay bekleyen video + kapak + caption |

## Notlar

- **Piksel font:** Pixelify Sans'ın statik sürümünde büyük harfler karışıyor (Z=2, B=G, C=O, 5=S);
  videoda okunmadığı için tüm piksel yazılar yedek font VT323 ile basılıyor (25'in katı boyutlarda tam piksel).
  Marka anları (logo yazısı, BÖLÜM N, haritam.arpama.tr, ÜCRETSİZ BAŞLA) Sora 700, kaynak satırı Manrope 500.
- **Logo:** `brand/arpama-logo.png` yoksa yer tutucu olarak Sora 700 ile altın "AR" + gümüş "PAMA" yazılır.
  Dosya eklenince render otomatik olarak gerçek logoyu kullanır.
- **TTS:** edge-tts, Microsoft'un websocket servisine bağlanır; bu yüzden ses kullanıcının bilgisayarında üretilir.
