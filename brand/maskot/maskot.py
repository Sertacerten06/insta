"""Arpi — Arpama'nın 8-bit maskotu.
Arpa başaklı anteni olan küçük bir robot. Sadece CLAUDE.md 3.2'deki 16 renk kullanılır.
Çalıştır:  python maskot.py   ->  sprites/, gif/, sprite_sheet.png, arpi.json üretir.
"""
from PIL import Image
import json, os, math

PAL = {
    'K': "#070A10", 'P': "#0E1420", 'Z': "#111B2B", 'D': "#1E2D46",
    'b': "#2A5AA8", 'B': "#2F6FE0", 'L': "#7AA9F3", 'I': "#CFE0FF",
    'S': "#D9DDE3", 'W': "#FFFFFF", 'G': "#C9CED6", 'M': "#9AA0AB",
    'y': "#FFE38F", 'Y': "#F2C14E", 'O': "#D4A017", 'R': "#E0705C",
}
W, H, OY = 48, 52, 4  # sanal piksel tuval; OY: zıplama payı


def blank():
    return [['.'] * W for _ in range(H)]


def px(g, x, y, c):
    x, y = math.floor(x + 0.5), math.floor(y + 0.5)
    if 0 <= x < W and 0 <= y < H:
        g[y][x] = c


def rrect_pts(x0, y0, x1, y1, r):
    pts = []
    for y in range(y0, y1 + 1):
        for x in range(x0, x1 + 1):
            dx = max(x0 + r - x, 0, x - (x1 - r))
            dy = max(y0 + r - y, 0, y - (y1 - r))
            if dx * dx + dy * dy <= r * r + r * 0.6:
                pts.append((x, y))
    return pts


def fill(g, pts, c):
    for x, y in pts:
        px(g, x, y, c)


def banded(g, pts, bands):
    """bands: [(renk, satır_sayısı), ...]; son bant -1 = kalan; alttan bant için ayrı liste."""
    ys = sorted({y for _, y in pts}); top, bot = ys[0], ys[-1]
    for x, y in pts:
        c = bands['mid']
        if y < top + bands['top'][1]:
            c = bands['top'][0]
        elif y > bot - bands['bot'][1]:
            c = bands['bot'][0]
        px(g, x, y, c)


def ellipse_pts(cx, cy, rx, ry):
    pts = []
    for y in range(int(cy - ry - 1), int(cy + ry + 2)):
        for x in range(int(cx - rx - 1), int(cx + rx + 2)):
            if ((x - cx) / rx) ** 2 + ((y - cy) / ry) ** 2 <= 1.0:
                pts.append((x, y))
    return pts


def limb(g, x0, y0, x1, y1, c, r=1.6):
    n = int(max(abs(x1 - x0), abs(y1 - y0)) * 2) + 1
    for i in range(n + 1):
        t = i / n
        fill(g, ellipse_pts(x0 + (x1 - x0) * t, y0 + (y1 - y0) * t, r, r), c)


def outline(g, c='K'):
    out = [row[:] for row in g]
    for y in range(H):
        for x in range(W):
            if g[y][x] == '.':
                for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nx, ny = x + dx, y + dy
                    if 0 <= nx < W and 0 <= ny < H and g[ny][nx] != '.':
                        out[y][x] = c
                        break
    return out


def comp(base, layer):
    for y in range(H):
        for x in range(W):
            if layer[y][x] != '.':
                base[y][x] = layer[y][x]


# ---------------- parçalar ----------------
def antenna(dy):
    """Arpa başağı: altın sap + iki sıra tane + yukarı kılçıklar."""
    g = blank(); o = OY + dy
    for y in range(5, 12):
        px(g, 24, y + o, 'O')
    for gy in (9, 7, 5):  # sol ve sağ taneler (2x2), sağ taraf 1 piksel yukarıda
        for (x, y) in ((22, gy), (23, gy), (22, gy + 1), (23, gy + 1)):
            px(g, x, y + o, 'Y')
        for (x, y) in ((25, gy - 1), (26, gy - 1), (25, gy), (26, gy)):
            px(g, x, y + o, 'Y')
        px(g, 22, gy + o, 'y'); px(g, 25, gy - 1 + o, 'y')     # parlak üst
        px(g, 23, gy + 1 + o, 'O'); px(g, 26, gy + o, 'O')     # koyu alt
        px(g, 21, gy - 1 + o, 'y'); px(g, 27, gy - 2 + o, 'y')  # kılçık
    for y in (2, 3, 4):  # tepe tanesi
        px(g, 24, y + o, 'Y')
    px(g, 24, 2 + o, 'y'); px(g, 24, 1 + o, 'y'); px(g, 24, 0 + o, 'y')
    return outline(g)


def head(dy, eyes, mouth, cheeks):
    g = blank(); o = OY + dy
    # yan cıvatalar
    for x0 in (7, 38):
        fill(g, rrect_pts(x0, 17 + o, x0 + 2, 23 + o, 1), 'M')
        px(g, x0 + 1, 18 + o, 'G')
    g = outline(g)
    h = blank()
    banded(h, rrect_pts(9, 11 + o, 38, 31 + o, 5),
           {'top': ('W', 3), 'mid': 'S', 'bot': ('G', 4)})
    # yüz ekranı
    fill(h, rrect_pts(12, 14 + o, 35, 28 + o, 3), 'D')
    fill(h, rrect_pts(13, 15 + o, 34, 27 + o, 2), 'P')
    px(h, 32, 16 + o, 'D'); px(h, 33, 17 + o, 'D')  # ekran parlaması
    for side, cx in (('l', 18.5), ('r', 29.5)):
        draw_eye(h, cx, 21 + o, eyes[side] if isinstance(eyes, dict) else eyes)
    draw_mouth(h, 24, o, mouth)
    if cheeks:
        for x in (15, 16, 31, 32):
            px(h, x, 24 + o, 'R')
    comp(g, outline(h))
    return g


def draw_eye(g, cx, cy, kind):
    if kind == 'normal':
        fill(g, ellipse_pts(cx, cy, 2.2, 3.2), 'L')
        fill(g, ellipse_pts(cx, cy - 1, 1.5, 1.8), 'I')
        px(g, cx - 1, cy - 2, 'W')
    elif kind == 'buyuk':
        fill(g, ellipse_pts(cx, cy, 2.9, 3.6), 'L')
        fill(g, ellipse_pts(cx, cy - 1, 2.0, 2.2), 'I')
        px(g, cx - 1, cy - 2, 'W'); px(g, cx - 2, cy - 1, 'W')
    elif kind == 'kirp':
        for x in range(int(cx - 2), int(cx + 3)):
            px(g, x, cy + 1, 'L')
    elif kind == 'mutlu':
        for dx, dy in ((-2, 1), (-1, 0), (0, -1), (1, 0), (2, 1)):
            px(g, cx + dx, cy + dy, 'I'); px(g, cx + dx, cy + dy + 1, 'L')
    elif kind == 'yukari':  # düşünürken yukarı bakar
        fill(g, ellipse_pts(cx + 0.5, cy - 1, 2.0, 2.6), 'L')
        fill(g, ellipse_pts(cx + 0.5, cy - 2, 1.3, 1.3), 'I')


def draw_mouth(g, cx, o, kind):
    if kind == 'gulum':
        for x, y in ((-2, 25), (-1, 26), (0, 26), (1, 26), (2, 25)):
            px(g, cx + x, y + o, 'L')
    elif kind == 'acik':
        fill(g, rrect_pts(cx - 2, 25 + o, cx + 2, 27 + o, 1), 'L')
        for x in (-1, 0, 1):
            px(g, cx + x, 26 + o, 'P')
        px(g, cx, 27 + o, 'R'); px(g, cx - 1, 27 + o, 'R')
    elif kind == 'o':
        fill(g, ellipse_pts(cx, 26 + o, 1.6, 1.6), 'L')
        px(g, cx, 26 + o, 'P')
    elif kind == 'duz':
        for x in (-1, 0, 1):
            px(g, cx + x, 26 + o, 'L')


def body(dy):
    g = blank(); o = OY + dy
    banded(g, rrect_pts(14, 31 + o, 33, 42 + o, 3),
           {'top': ('L', 1), 'mid': 'B', 'bot': ('b', 2)})
    # göğüste altın harita pini (Haritam)
    fill(g, ellipse_pts(23.5, 35 + o, 2.3, 2.1), 'Y')
    px(g, 22, 34 + o, 'y'); px(g, 23, 34 + o, 'y')
    for x in (22, 23, 24, 25):
        px(g, x, 37 + o, 'O')
    px(g, 23, 38 + o, 'O'); px(g, 24, 38 + o, 'O')
    px(g, 23, 35 + o, 'P'); px(g, 24, 35 + o, 'P')
    return outline(g)


ARMS = {
    'asagi':   [((14, 33), (11, 39), (11, 40.5)), ((33, 33), (36, 39), (36, 40.5))],
    'yukari':  [((14, 33), (8, 26), (7, 24)), ((33, 33), (39, 26), (40, 24))],
    'isaret':  [((14, 33), (11, 39), (11, 40.5)), ((33, 33), (41, 31), (43, 30.5))],
    'el_a':    [((14, 33), (11, 39), (11, 40.5)), ((33, 33), (38, 27), (39, 24.5))],
    'el_b':    [((14, 33), (11, 39), (11, 40.5)), ((33, 33), (40, 29), (42, 27))],
    'dusun':   [((14, 33), (11, 39), (11, 40.5)), ((33, 34), (36, 31), (35, 29))],
}


def arms(dy, kind):
    out = blank(); o = OY + dy
    for (sx, sy), (ex, ey), (hx, hy) in ARMS[kind]:
        g = blank()
        limb(g, sx, sy + o, ex, ey + o, 'B')
        fill(g, ellipse_pts(hx, hy + o, 1.9, 1.9), 'S')
        px(g, hx - 1, hy + o - 1, 'W')
        comp(out, outline(g))
    return out


def legs(dy):
    g = blank(); o = OY + dy
    for x0 in (17, 26):
        fill(g, rrect_pts(x0, 41 + o, x0 + 4, 45 + o, 1), 'b')
        for x in range(x0, x0 + 5):
            px(g, x, 45 + o, 'B')
    return outline(g)


def shadow(scale=1.0):
    g = blank()
    fill(g, ellipse_pts(24, 47.5 + OY - 1, 8 * scale, 1.1), 'D')
    return g


def sparkles(phase):
    g = blank()
    spots = [(5, 12, 'I'), (42, 9, 'Y'), (3, 32, 'Y'), (44, 38, 'I'), (40, 20, 'I'), (8, 6, 'Y')]
    for i, (x, y, c) in enumerate(spots):
        big = (i + phase) % 2 == 0
        px(g, x, y, 'W' if big else c)
        if big:
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                px(g, x + dx, y + dy, c)
    return g


def bubble():
    """Düşünme baloncuğu: '...'"""
    g = blank()
    fill(g, rrect_pts(36, 1, 46, 8, 2), 'S')
    for x in (38, 41, 44):
        px(g, x, 5, 'b')
    px(g, 37, 10, 'S'); px(g, 35, 12, 'S')
    return outline(g)


# ---------------- kareler ----------------
def frame(dy=0, up=0, eyes='normal', mouth='gulum', arm='asagi', cheeks=False,
          extra=None, sh=1.0):
    g = shadow(sh)
    comp(g, legs(dy))
    comp(g, body(dy + up))
    comp(g, antenna(dy + up))
    comp(g, head(dy + up, eyes, mouth, cheeks))
    comp(g, arms(dy + up, arm))
    if extra:
        comp(g, extra)
    return g


FRAMES = {
    'bekle_0':   frame(),
    'bekle_1':   frame(up=1),
    'bekle_2':   frame(eyes='kirp'),
    'konus_0':   frame(mouth='acik'),
    'konus_1':   frame(mouth='gulum'),
    'konus_2':   frame(mouth='o', up=1),
    'sevin_0':   frame(dy=1, eyes='mutlu', arm='asagi', cheeks=True),
    'sevin_1':   frame(dy=-4, eyes='mutlu', mouth='acik', arm='yukari', cheeks=True, sh=0.6),
    'isaret_0':  frame(eyes={'l': 'normal', 'r': 'mutlu'}, arm='isaret'),
    'isaret_1':  frame(eyes={'l': 'normal', 'r': 'mutlu'}, arm='isaret', up=1, mouth='acik'),
    'selam_0':   frame(eyes='mutlu', arm='el_a', cheeks=True),
    'selam_1':   frame(eyes='mutlu', arm='el_b', cheeks=True),
    'saskin_0':  frame(dy=-2, eyes='buyuk', mouth='o', arm='yukari', sh=0.8),
    'dusun_0':   frame(eyes='yukari', mouth='duz', arm='dusun', extra=bubble()),
    'levelup_0': frame(dy=-4, eyes='mutlu', mouth='acik', arm='yukari', cheeks=True, sh=0.6, extra=sparkles(0)),
    'levelup_1': frame(dy=-3, eyes='mutlu', mouth='acik', arm='yukari', cheeks=True, sh=0.7, extra=sparkles(1)),
}

ANIMS = {  # [(kare, ms), ...]
    'bekle':   [('bekle_0', 500), ('bekle_1', 300), ('bekle_0', 900), ('bekle_2', 120)],
    'konus':   [('konus_0', 110), ('konus_1', 110), ('konus_2', 110), ('konus_1', 110)],
    'sevin':   [('sevin_0', 160), ('sevin_1', 320)],
    'isaret':  [('isaret_0', 300), ('isaret_1', 200)],
    'selam':   [('selam_0', 220), ('selam_1', 220)],
    'saskin':  [('saskin_0', 400), ('bekle_0', 200)],
    'dusun':   [('dusun_0', 600)],
    'levelup': [('levelup_0', 160), ('levelup_1', 160)],
}

USAGE = {
    'bekle': 'Varsayılan; sahne boşken nefes alır, ara ara göz kırpar',
    'konus': 'Seslendirme konuşurken (TTS kelime zamanlarına göre ağız açılır)',
    'sevin': 'Haber başlığı çıkınca / iyi haber',
    'isaret': 'Ekrandaki madde veya haritam.arpama.tr yazısını gösterir (sağa bakar)',
    'selam': 'Açılış ve kapanış (GAME SAVED)',
    'saskin': 'SON DAKİKA veya şaşırtıcı haber',
    'dusun': 'Soru sorarken / kanca cümlesi',
    'levelup': 'Haritam bölümü, LEVEL UP anı',
}


def to_img(g, scale, bg=None):
    im = Image.new('RGBA', (W, H), (0, 0, 0, 0) if bg is None else bg)
    p = im.load()
    for y in range(H):
        for x in range(W):
            c = g[y][x]
            if c != '.':
                h = PAL[c]
                p[x, y] = (int(h[1:3], 16), int(h[3:5], 16), int(h[5:7], 16), 255)
    return im.resize((W * scale, H * scale), Image.NEAREST)


def main():
    os.makedirs('sprites', exist_ok=True); os.makedirs('gif', exist_ok=True)
    names = list(FRAMES)
    for n in names:
        to_img(FRAMES[n], 1).save(f'sprites/{n}.png')
        to_img(FRAMES[n], 10).save(f'sprites/{n}@10x.png')
    # sprite sheet (1x, 8 sütun)
    cols = 8; rows = math.ceil(len(names) / cols)
    sheet = Image.new('RGBA', (W * cols, H * rows), (0, 0, 0, 0))
    for i, n in enumerate(names):
        sheet.paste(to_img(FRAMES[n], 1), ((i % cols) * W, (i // cols) * H))
    sheet.save('sprite_sheet.png')
    # önizleme GIF'leri (marka zemini üzerinde)
    bg = (7, 10, 16, 255)
    for a, seq in ANIMS.items():
        ims = [to_img(FRAMES[f], 6, bg).convert('P', palette=Image.ADAPTIVE) for f, _ in seq]
        ims[0].save(f'gif/{a}.gif', save_all=True, append_images=ims[1:],
                    duration=[d for _, d in seq], loop=0, disposal=2)
    meta = {
        'ad': 'Arpi',
        'tuval': {'w': W, 'h': H, 'not': 'Nearest-neighbor ile tam sayı katında büyüt (ör. 10x = 480x520)'},
        'ayak_noktasi': {'x': 24, 'y': 49},
        'kareler': {n: {'dosya': f'sprites/{n}.png', 'sheet_x': (i % cols) * W, 'sheet_y': (i // cols) * H}
                    for i, n in enumerate(names)},
        'animasyonlar': {a: {'kullanim': USAGE[a], 'kareler': [{'kare': f, 'ms': d} for f, d in s]}
                         for a, s in ANIMS.items()},
        'palet': PAL,
    }
    json.dump(meta, open('arpi.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
    # karakter kartı
    show = ['bekle_0', 'konus_0', 'sevin_1', 'isaret_0', 'selam_0', 'saskin_0', 'dusun_0', 'levelup_0']
    sc = 6; card = Image.new('RGBA', (W * sc * 4 + 50, H * sc * 2 + 30), bg)
    for i, n in enumerate(show):
        card.paste(to_img(FRAMES[n], sc), (10 + (i % 4) * (W * sc + 10), 10 + (i // 4) * (H * sc + 10)),
                   to_img(FRAMES[n], sc))
    card.save('arpi_kart.png')


if __name__ == '__main__':
    main()
