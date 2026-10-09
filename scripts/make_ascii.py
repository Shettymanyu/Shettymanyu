"""One-off: photo -> animated ASCII portrait SVG.  Usage: python scripts/make_ascii.py photo.jpg
Needs Pillow (local only, not used by the daily workflow)."""
import sys
from html import escape
from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageOps

COLS, CW, LH, FS = 48, 7.0, 12.6, 11.6   # columns, char width, line height, font size
RAMP = " .'`:-=+*#%@"                    # dark -> bright (light text on dark bg)
CROP = (120, 10, 280, 240)               # head + shoulders in the 400x400 avatar
PAD, BAR = 16, 28

img = ImageOps.grayscale(Image.open(sys.argv[1]).convert("RGB")).resize((400, 400)).crop(CROP)
img = ImageOps.equalize(img)
# ponytail: elliptical vignette instead of rembg background removal; swap in rembg if the backdrop still competes
mask = Image.new("L", img.size, 0)
ImageDraw.Draw(mask).ellipse((img.width * .12, -img.height * .05, img.width * .88, img.height * 1.1), fill=255)
img = ImageChops.multiply(img, mask.filter(ImageFilter.GaussianBlur(img.width / 10)))
rows = round(COLS * img.height / img.width * CW / LH)
img = img.resize((COLS, rows))
px = img.load()
lines = ["".join(RAMP[px[x, y] * (len(RAMP) - 1) // 255] for x in range(COLS)) for y in range(rows)]

W = round(COLS * CW + PAD * 2)
H = round(BAR + PAD + rows * LH + PAD)
out = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">',
       '<style>text{font:%spx ui-monospace,SFMono-Regular,Menlo,Consolas,monospace;fill:#c9d1d9;white-space:pre}'
       '.t{fill:#8b949e;font-size:12px}</style>' % FS,
       f'<rect width="{W}" height="{H}" rx="10" fill="#0d1117" stroke="#30363d"/>',
       '<circle cx="18" cy="14" r="5" fill="#ff5f56"/><circle cx="34" cy="14" r="5" fill="#ffbd2e"/>'
       '<circle cx="50" cy="14" r="5" fill="#27c93f"/>',
       f'<text class="t" x="{W/2}" y="18" text-anchor="middle">manyu@github: ~/portrait</text>',
       '<defs>']
for i in range(rows):
    y = BAR + PAD + i * LH
    out.append(f'<clipPath id="c{i}"><rect x="0" y="{y-LH:.1f}" height="{LH+2}" width="0">'
               f'<animate attributeName="width" from="0" to="{W}" begin="{i*0.06:.2f}s" dur="0.5s" fill="freeze"/>'
               '</rect></clipPath>')
out.append('</defs>')
for i, line in enumerate(lines):
    y = BAR + PAD + i * LH
    out.append(f'<text x="{PAD}" y="{y:.1f}" clip-path="url(#c{i})" textLength="{COLS*CW}" lengthAdjust="spacingAndGlyphs" xml:space="preserve">{escape(line)}</text>')
out.append('</svg>')
open("avi-ascii.svg", "w", encoding="utf-8").write("\n".join(out))
print("\n".join(lines))
print(f"avi-ascii.svg {W}x{H}")
