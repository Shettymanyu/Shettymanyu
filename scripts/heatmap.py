"""Daily: scrape the public contributions fragment -> animated contrib-heatmap.svg. Stdlib only.
Usage: python scripts/heatmap.py [username]      Self-check: python scripts/heatmap.py --test"""
import re
import sys
import urllib.request
from datetime import date, timedelta

W, CELL, GAP, LEFT, TOP = 800, 11, 3, 40, 58
COLORS = ["#161b22", "#0e4429", "#006d32", "#26a641", "#39d353"]
MONTHS = "Jan Feb Mar Apr May Jun Jul Aug Sep Oct Nov Dec".split()


def fetch(user):
    req = urllib.request.Request(f"https://github.com/users/{user}/contributions", headers={"User-Agent": "heatmap"})
    return urllib.request.urlopen(req, timeout=30).read().decode()


def parse(html):
    """-> sorted [(date, level, count)]"""
    cells = re.findall(r'data-date="(\d{4}-\d\d-\d\d)" id="([^"]+)" data-level="(\d)"', html)
    counts = {m[0]: 0 if m[1] == "No" else int(m[1])
              for m in re.findall(r'<tool-tip[^>]*for="([^"]+)"[^>]*>(No|\d+) contribution', html)}
    return sorted((date.fromisoformat(d), int(lvl), counts.get(cid, 0)) for d, cid, lvl in cells)


def stats(days):
    total = sum(c for _, _, c in days)
    longest = run = 0
    for _, _, c in days:
        run = run + 1 if c else 0
        longest = max(longest, run)
    current = 0
    for i, (_, _, c) in enumerate(reversed(days)):
        if c:
            current += 1
        elif i:          # today with 0 doesn't break the streak yet
            break
    best = max(days, key=lambda d: d[2])
    return total, current, longest, best


def render(days, user):
    start = days[0][0] - timedelta(days=(days[0][0].weekday() + 1) % 7)  # Sunday of first week
    total, current, longest, best = stats(days)
    rects, months, seen = [], [], set()
    for d, lvl, c in days:
        col, row = (d - start).days // 7, (d.weekday() + 1) % 7
        x, y = LEFT + col * (CELL + GAP), TOP + row * (CELL + GAP)
        rects.append(f'<rect x="{x}" y="{y}" width="{CELL}" height="{CELL}" rx="2" fill="{COLORS[lvl]}" '
                     f'style="animation-delay:{(col + row) * 18}ms"><title>{c} on {d}</title></rect>')
        if d.day <= 7 and row == 0 and (d.year, d.month) not in seen:
            seen.add((d.year, d.month))
            months.append(f'<text class="m" x="{x}" y="{TOP - 8}">{MONTHS[d.month - 1]}</text>')
    gy = TOP + 7 * (CELL + GAP) + 22
    legend = "".join(f'<rect x="{W - 150 + i * 15}" y="{gy - 10}" width="{CELL}" height="{CELL}" rx="2" fill="{c}"/>'
                     for i, c in enumerate(COLORS))
    H = gy + 22
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">
<style>
text{{font:12px ui-monospace,SFMono-Regular,Menlo,Consolas,monospace;fill:#8b949e}}
.m{{font-size:10px}} .s{{fill:#c9d1d9}} .g{{fill:#39d353}}
rect[style]{{opacity:0;animation:pop .35s ease-out forwards;transform-box:fill-box;transform-origin:center}}
@keyframes pop{{from{{opacity:0;transform:translate(-6px,-6px) scale(.4)}}to{{opacity:1;transform:none}}}}
</style>
<rect width="{W}" height="{H}" rx="10" fill="#0d1117" stroke="#30363d"/>
<circle cx="18" cy="14" r="5" fill="#ff5f56"/><circle cx="34" cy="14" r="5" fill="#ffbd2e"/><circle cx="50" cy="14" r="5" fill="#27c93f"/>
<text x="{W / 2}" y="18" text-anchor="middle">{user}@github: ~/contributions</text>
<text class="m" x="8" y="{TOP + 1 * (CELL + GAP) + 9}">Mon</text>
<text class="m" x="8" y="{TOP + 3 * (CELL + GAP) + 9}">Wed</text>
<text class="m" x="8" y="{TOP + 5 * (CELL + GAP) + 9}">Fri</text>
{"".join(months)}
{"".join(rects)}
<text x="{LEFT}" y="{gy}"><tspan class="g">$</tspan> <tspan class="s">{total}</tspan> contributions · streak <tspan class="s">{current}d</tspan> · longest <tspan class="s">{longest}d</tspan> · best <tspan class="s">{best[2]}</tspan> on {best[0]:%b %d}</text>
<text x="{W - 185}" y="{gy}">Less</text>{legend}<text x="{W - 72}" y="{gy}">More</text>
</svg>'''


def test():
    html = ('<td data-date="2026-01-04" id="a" data-level="1"></td><td data-date="2026-01-05" id="b" data-level="0"></td>'
            '<td data-date="2026-01-06" id="c" data-level="4"></td><td data-date="2026-01-07" id="d" data-level="2"></td>'
            '<tool-tip for="a">3 contributions on</tool-tip><tool-tip for="b">No contributions on</tool-tip>'
            '<tool-tip for="c">9 contributions on</tool-tip><tool-tip for="d">1 contribution on</tool-tip>')
    days = parse(html)
    assert [c for _, _, c in days] == [3, 0, 9, 1], days
    total, current, longest, best = stats(days)
    assert (total, current, longest, best[2]) == (13, 2, 2, 9)
    assert stats(days + [(date(2026, 1, 8), 0, 0)])[1] == 2  # empty today keeps streak
    assert "<svg" in render(days, "x")
    print("ok")


if __name__ == "__main__":
    if sys.argv[1:] == ["--test"]:
        test()
    else:
        user = sys.argv[1] if len(sys.argv) > 1 else "Shettymanyu"
        open("contrib-heatmap.svg", "w", encoding="utf-8").write(render(parse(fetch(user)), user))
