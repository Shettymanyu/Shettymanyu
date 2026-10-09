"""One-off: photo -> animated ASCII portrait SVG.  Usage: python scripts/make_ascii.py photo.jpg
Needs Pillow (local only, not used by the daily workflow). Expects a portrait on a plain light backdrop.
Each character's glyph density AND its grey shade come from the photo, so tones read like the real picture."""
import sys
from html import escape
from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageOps

COLS, CW, LH, FS = 96, 3.5, 6.35, 5.85   # columns, char width, line height, font size (CW/LH ~ glyph aspect)
RAMP = " .'`^,:;Il!i><~+_-?][}{1)(|/tfjrxnuvczXYUJCLQ0OZmwqpdbkhao*#MW&8%B@$"  # dark -> bright (light text on dark bg)
SHADES = 16                               # grey levels for per-character fill
FLOOR = 46                                # min brightness on the person, so black hair/suit stay visible
PAD, BAR = 16, 28
BG_TOL = 30                               # flood-fill tolerance for the backdrop
KEY = (255, 0, 255)

img = Image.open(sys.argv[1]).convert("RGB")
w, h = img.size
d = ImageDraw.Draw(img)
d.rectangle((w - 90, h - 90, w, h), fill=img.getpixel((w - 120, h - 60)))  # paint over corner watermark
for y in range(0, h, 40):                                                  # flood backdrop from both edges
    for x in (0, w - 1):
        if sum(img.getpixel((x, y))) > 450:
            ImageDraw.floodfill(img, (x, y), KEY, thresh=BG_TOL)

bg = Image.frombytes("L", img.size, bytes(255 if p == KEY else 0 for p in img.get_flattened_data()))
person = ImageOps.invert(bg)
g = ImageOps.grayscale(img).filter(ImageFilter.UnsharpMask(radius=25, percent=160, threshold=2))  # local contrast (CLAHE-ish)
g = ImageOps.autocontrast(g, cutoff=1, mask=person)                        # stretch tones over the person only
g = ImageChops.lighter(g, Image.new("L", g.size, FLOOR))                   # lift shadows to the floor...
g.paste(0, mask=bg.filter(ImageFilter.GaussianBlur(2)))                    # ...then blank the backdrop
rows = round(COLS * h / w * CW / LH)
g = g.resize((COLS, rows), Image.LANCZOS)
px = g.load()


def shade(v):  # brightness -> grey hex, quantised so neighbouring chars merge into one <tspan>
    q = min(v * SHADES // 256, SHADES - 1)
    c = round(70 + q * (255 - 70) / (SHADES - 1))
    return f"#{c:02x}{c:02x}{c:02x}"


rendered = []  # (row, text length, tspans markup)
for y in range(rows):
    vals = [px[x, y] for x in range(COLS)]
    chars = [RAMP[v * (len(RAMP) - 1) // 255] for v in vals]
    n = len("".join(chars).rstrip())
    if not n:
        continue
    spans, run, cur = [], "", None
    for ch, v in zip(chars[:n], vals[:n]):
        s = shade(v)
        if s != cur and run:
            spans.append(f'<tspan fill="{cur}">{escape(run)}</tspan>')
            run = ""
        run, cur = run + ch, s
    spans.append(f'<tspan fill="{cur}">{escape(run)}</tspan>')
    rendered.append((y, n, "".join(spans)))

W = round(COLS * CW + PAD * 2)
H = round(BAR + PAD + rows * LH + PAD)
out = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">',
       '<style>text{font:%spx ui-monospace,SFMono-Regular,Menlo,Consolas,monospace;white-space:pre}'
       '.t{fill:#8b949e;font-size:12px}</style>' % FS,
       f'<rect width="{W}" height="{H}" rx="10" fill="#0d1117" stroke="#30363d"/>',
       '<circle cx="18" cy="14" r="5" fill="#ff5f56"/><circle cx="34" cy="14" r="5" fill="#ffbd2e"/>'
       '<circle cx="50" cy="14" r="5" fill="#27c93f"/>',
       f'<text class="t" x="{W/2}" y="18" text-anchor="middle">manyu@github: ~/portrait</text>',
       '<defs>']
for i, *_ in rendered:
    y = BAR + PAD + i * LH
    out.append(f'<clipPath id="c{i}"><rect x="0" y="{y-LH:.1f}" height="{LH+2}" width="0">'
               f'<animate attributeName="width" from="0" to="{W}" begin="{i*0.035:.2f}s" dur="0.5s" fill="freeze"/>'
               '</rect></clipPath>')
out.append('</defs>')
for i, n, spans in rendered:
    y = BAR + PAD + i * LH
    out.append(f'<text x="{PAD}" y="{y:.2f}" clip-path="url(#c{i})" textLength="{n*CW:.2f}" '
               f'lengthAdjust="spacingAndGlyphs" xml:space="preserve">{spans}</text>')
out.append('</svg>')
open("portrait.svg", "w", encoding="utf-8").write("\n".join(out))
print(f"portrait.svg {W}x{H}, {rows} rows")
