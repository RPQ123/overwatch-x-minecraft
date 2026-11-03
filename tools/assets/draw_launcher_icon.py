"""绘制启动器图标：守望先锋风格的橙色断环，中间是我的世界的草方块。
输出 assets/launcher/owmc.png（1024px）与 owmc.ico（16–256 多尺寸）。"""
import math, random
from pathlib import Path
from PIL import Image, ImageDraw, ImageFilter

ROOT = Path(__file__).resolve().parents[2]
S = 1024
OUT = ROOT / 'assets/launcher'


def lerp(a, b, t):
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(len(a)))


def background():
    img = Image.new('RGBA', (S, S), (0, 0, 0, 0))
    grad = Image.new('RGBA', (S, S))
    gd = ImageDraw.Draw(grad)
    for y in range(S):
        gd.line([(0, y), (S, y)], fill=lerp((27, 38, 62, 255), (8, 12, 22, 255), y / S))
    mask = Image.new('L', (S, S), 0)
    ImageDraw.Draw(mask).rounded_rectangle([24, 24, S - 24, S - 24], radius=210, fill=255)
    img.paste(grad, (0, 0), mask)
    # 细描边
    ImageDraw.Draw(img).rounded_rectangle([24, 24, S - 24, S - 24], radius=210, outline=(60, 82, 120, 255), width=6)
    return img


def ring(img):
    """守望先锋标志的结构：10 点和 2 点方向各有一道断口；上段弧为橙色，
    下段弧为银白色（不画中间的斜杠）。"""
    layer = Image.new('RGBA', (S, S), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    c, r, width = S / 2, 430, 84
    orange, silver = (249, 158, 26, 255), (226, 232, 241, 255)
    box = [c - r, c - r, c + r, c + r]
    left, right, gap = -148, -32, 7          # 断口角度（PIL：-90 为正上方）
    d.arc(box, left + gap, right - gap, fill=orange, width=width)
    d.arc(box, right + gap, left + 360 - gap, fill=silver, width=width)
    glow = layer.filter(ImageFilter.GaussianBlur(24))
    glow.putalpha(glow.getchannel('A').point(lambda v: int(v * .5)))
    img.alpha_composite(glow)
    img.alpha_composite(layer)
    ImageDraw.Draw(img).arc([c - r + 12, c - r + 12, c + r - 12, c + r - 12], -132, -100, fill=(255, 214, 140, 255), width=10)


def block(img):
    """等距草方块，像素纹理。"""
    rnd = random.Random(7)
    c = S / 2
    w, h = 230, 133          # 顶面半宽、半高
    top_y = c - 222
    side = 260               # 侧面高度
    T = (c, top_y); R = (c + w, top_y + h); B = (c, top_y + 2 * h); L = (c - w, top_y + h)
    n = 8

    def quad(p0, u, v, colors, fn):
        d = ImageDraw.Draw(img)
        for i in range(n):
            for j in range(n):
                pts = []
                for a, b in ((i, j), (i + 1, j), (i + 1, j + 1), (i, j + 1)):
                    pts.append((p0[0] + u[0] * a / n + v[0] * b / n, p0[1] + u[1] * a / n + v[1] * b / n))
                d.polygon(pts, fill=fn(i, j, colors))

    greens = [(92, 168, 52), (104, 184, 60), (80, 150, 46), (116, 196, 70)]
    dirt = [(134, 96, 67), (120, 85, 58), (150, 108, 76), (106, 75, 52)]

    def top_fn(i, j, _):
        return greens[rnd.randrange(4)]

    def side_fn(shade):
        def f(i, j, _):
            base = greens[rnd.randrange(4)] if j < 2 or (j == 2 and rnd.random() < .45) else dirt[rnd.randrange(4)]
            return tuple(int(x * shade) for x in base) + (255,)
        return f

    # 顶面：T 为起点，u 指向 R，v 指向 L
    quad(T, (R[0] - T[0], R[1] - T[1]), (L[0] - T[0], L[1] - T[1]), None, top_fn)
    # 左侧面：L→B 为 u，向下为 v
    quad(L, (B[0] - L[0], B[1] - L[1]), (0, side), None, side_fn(.80))
    # 右侧面：B→R 为 u
    quad(B, (R[0] - B[0], R[1] - B[1]), (0, side), None, side_fn(.62))
    d = ImageDraw.Draw(img)
    edge = (20, 26, 18, 255)
    for a, b in ((T, R), (R, B), (B, L), (L, T), (L, (L[0], L[1] + side)), (B, (B[0], B[1] + side)), (R, (R[0], R[1] + side)),
                 ((L[0], L[1] + side), (B[0], B[1] + side)), ((B[0], B[1] + side), (R[0], R[1] + side))):
        d.line([a, b], fill=edge, width=6)


def main():
    img = background()
    ring(img)
    block(img)
    OUT.mkdir(parents=True, exist_ok=True)
    img.save(OUT / 'owmc.png')
    sizes = [(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)]
    img.save(OUT / 'owmc.ico', sizes=sizes)
    preview = img.resize((256, 256), Image.LANCZOS).convert('RGB')
    print('ok', OUT / 'owmc.ico')
    return preview


if __name__ == '__main__':
    main()
