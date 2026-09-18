"""
Builds every generated asset for the profile README:
  assets/hero-{dark,light}.svg, assets/footer-{dark,light}.svg,
  assets/cards/<repo>-{dark,light}.svg, and the "recently pushed" list in README.md.
Text is converted to vector paths, so it looks identical for every visitor.
Run locally:  GITHUB_TOKEN=... python .github/profile-kit/build.py
"""
import json, os, re, datetime, urllib.request
from pathlib import Path
from xml.sax.saxutils import escape
from fontTools.ttLib import TTFont
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen

KIT = Path(__file__).parent
ROOT = KIT.parent.parent
USER = os.environ.get("PROFILE_USER", "MukulJoshi6312")
TOKEN = os.environ.get("GITHUB_TOKEN", "")

# ---------------------------------------------------------------- type
FONTS = {k: TTFont(KIT / "fonts" / f) for k, f in {
    "display": "Bricolage-Display.ttf", "body": "Bricolage-Text.ttf",
    "bodyb": "Bricolage-TextBold.ttf", "mono": "IBMPlexMono-Medium.ttf"}.items()}

def _kern(font):
    pairs = {}
    if "GPOS" not in font: return pairs
    for lk in font["GPOS"].table.LookupList.Lookup:
        for st in lk.SubTable:
            st = getattr(st, "ExtSubTable", st)
            if getattr(st, "LookupType", 2) != 2 or getattr(st, "Format", 0) != 1: continue
            for i, first in enumerate(st.Coverage.glyphs):
                for pvr in st.PairSet[i].PairValueRecord:
                    v = pvr.Value1
                    if v is not None and getattr(v, "XAdvance", 0):
                        pairs[(first, pvr.SecondGlyph)] = v.XAdvance
    return pairs
KERN = {k: _kern(f) for k, f in FONTS.items()}

def measure(s, font, size, track=0):
    f = FONTS[font]; cmap = f.getBestCmap(); gs = f.getGlyphSet(); sc = size / f["head"].unitsPerEm
    names = [cmap.get(ord(c), ".notdef") for c in s]
    adv = [(gs[n].width + (KERN[font].get((n, names[i+1]), 0) if i+1 < len(names) else 0)) * sc + track
           for i, n in enumerate(names)]
    return names, adv, max(0, sum(adv) - track)

def text(s, font, size, x, y, fill, track=0, anchor="start", extra=""):
    names, adv, w = measure(s, font, size, track)
    f = FONTS[font]; gs = f.getGlyphSet(); sc = size / f["head"].unitsPerEm
    x -= {"start": 0, "middle": w / 2, "end": w}[anchor]
    pen = SVGPathPen(gs); cx = x
    for n, a in zip(names, adv):
        gs[n].draw(TransformPen(pen, (sc, 0, 0, -sc, cx, y))); cx += a
    return f'<path d="{pen.getCommands()}" fill="{fill}"{extra}/>', w

def wrap(s, font, size, max_w):
    lines, cur = [], ""
    for word in s.split():
        trial = (cur + " " + word).strip()
        if measure(trial, font, size)[2] <= max_w: cur = trial
        else: lines.append(cur); cur = word
    return lines + [cur] if cur else lines

# ---------------------------------------------------------------- colour
THEMES = {
    "dark":  dict(bg="#0E1726", raised="#15223A", line="#2B3D5C", text="#E8EEF6", muted="#93A6C2",
                  signal="#4C8EDA", saffron="#F2A93B", glow=".22"),
    "light": dict(bg="#F5F8FC", raised="#FFFFFF", line="#C9D5E5", text="#0E1726", muted="#4F607A",
                  signal="#2F6FBF", saffron="#B8720C", glow=".14"),
}

def svg(w, h, t, body, label, radius=22):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" '
            f'role="img" aria-label="{escape(label, {chr(34): "&quot;"})}">'
            f'<defs><radialGradient id="g" cx="0.88" cy="0.05" r="0.75"><stop offset="0" stop-color="{t["signal"]}" '
            f'stop-opacity="{t["glow"]}"/><stop offset="1" stop-color="{t["signal"]}" stop-opacity="0"/></radialGradient></defs>'
            f'<rect x=".75" y=".75" width="{w-1.5}" height="{h-1.5}" rx="{radius}" fill="{t["bg"]}" stroke="{t["line"]}" stroke-width="1.5"/>'
            f'<rect x=".75" y=".75" width="{w-1.5}" height="{h-1.5}" rx="{radius}" fill="url(#g)"/>{body}</svg>')

# ---------------------------------------------------------------- hero
def hero(t):
    W, H, wy, CYCLE = 1200, 470, 392, 7.0
    top = [text("Full-stack developer in India", "bodyb", 19, 64, 86, t["muted"], track=0.2)[0],
           text("Mukul Joshi", "display", 118, 58, 200, t["text"], track=-3)[0],
           text("I build both ends of the wire: React on the front,", "body", 27, 64, 262, t["text"])[0],
           text("Node and MongoDB behind it.", "body", 27, 64, 298, t["muted"])[0],
           f'<line x1="150" y1="{wy}" x2="1050" y2="{wy}" stroke="{t["line"]}" stroke-width="2" stroke-dasharray="2 8" stroke-linecap="round"/>']
    def packet(color, label, x0, x1, t0, t1, above):
        lab, _ = text(label, "mono", 14, 0, wy - 34 if above else wy + 46, color, anchor="middle")
        return (f'<g opacity="0"><animate attributeName="opacity" dur="{CYCLE}s" repeatCount="indefinite" '
                f'values="0;0;1;1;0;0" keyTimes="0;{t0:.3f};{t0+.01:.3f};{t1-.01:.3f};{t1:.3f};1"/>'
                f'<animateTransform attributeName="transform" type="translate" dur="{CYCLE}s" repeatCount="indefinite" '
                f'values="{x0} 0;{x0} 0;{x1} 0;{x1} 0" keyTimes="0;{t0:.3f};{t1:.3f};1"/>'
                f'<circle cx="0" cy="{wy}" r="14" fill="{color}" opacity=".18"/><circle cx="0" cy="{wy}" r="7" fill="{color}"/>{lab}</g>')
    packets = [packet(t["saffron"], "GET /projects", 150, 1050, .05, .45, True),
               packet(t["signal"], "200 OK", 1050, 150, .55, .95, False)]
    nodes = []
    for i, (label, x) in enumerate([("React UI", 150), ("Express API", 450), ("Node.js", 750), ("MongoDB", 1050)]):
        lab, w = text(label, "mono", 16, x, wy + 6, t["text"], anchor="middle")
        bw, out, back = w + 40, .05 + .40 * i / 3, .55 + .40 * (3 - i) / 3
        kts = sorted({0, max(0, out - .03), out, out + .06, back - .03, back, min(1, back + .06), 1})
        vals = ";".join(t["saffron"] if k == out else t["signal"] if k == back else t["line"] for k in kts)
        nodes.append(f'<rect x="{x-bw/2:.1f}" y="{wy-20}" width="{bw:.1f}" height="40" rx="20" fill="{t["bg"]}" '
                     f'stroke="{t["line"]}" stroke-width="1.5"><animate attributeName="stroke" dur="{CYCLE}s" '
                     f'repeatCount="indefinite" values="{vals}" keyTimes="{";".join(f"{k:.3f}" for k in kts)}"/></rect>{lab}')
    return svg(W, H, t, "".join(top + packets + nodes),
               "Mukul Joshi, full-stack developer in India. I build both ends of the wire: React on the front, Node and MongoDB behind it.")

def footer(t):
    body = [text("Thanks for reading.", "display", 40, 64, 72, t["text"], track=-.5)[0],
            text("If something here is useful to you, a star on the repo goes a long way.", "body", 20, 64, 108, t["muted"])[0],
            text("200 OK", "mono", 15, 1136, 84, t["signal"], anchor="end")[0],
            f'<line x1="880" y1="110" x2="1096" y2="110" stroke="{t["line"]}" stroke-width="2" stroke-dasharray="2 8" stroke-linecap="round"/>',
            f'<circle cx="1110" cy="110" r="6" fill="{t["signal"]}"><animate attributeName="opacity" dur="2.4s" repeatCount="indefinite" values="1;.25;1"/></circle>']
    return svg(1200, 150, t, "".join(body), "Thanks for reading.")

# ---------------------------------------------------------------- project cards
def ago(iso, now):
    if not iso: return ""
    d = (now - datetime.datetime.fromisoformat(iso.replace("Z", "+00:00"))).days
    if d < 1: return "today"
    if d < 2: return "yesterday"
    if d < 14: return f"{d} days ago"
    if d < 60: return f"{d // 7} weeks ago"
    if d < 365: return f"{d // 30} months ago"
    y = d // 365; return f"{y} year{'s' if y > 1 else ''} ago"

def card(p, meta, t, now):
    W, H, pad = 600, 270, 36
    b = [text(p["title"], "display", 36, pad, 70, t["text"], track=-.6)[0]]
    stars, when = meta.get("stargazers_count", 0), ago(meta.get("pushed_at"), now)
    info = "   ".join(x for x in [f"{stars} star{'s' if stars != 1 else ''}" if stars else "", f"updated {when}" if when else ""] if x)
    if info: b.append(text(info, "mono", 13, W - pad, 64, t["muted"], anchor="end")[0])
    for i, line in enumerate(wrap(p["description"], "body", 18, W - 2 * pad)[:3]):
        b.append(text(line, "body", 18, pad, 110 + i * 26, t["text"])[0])
    x, limit = pad, W - pad - 3 * 34 - 34
    for s in p["stack"]:
        lab, w = text(s, "mono", 13, x + 12, H - pad - 7, t["muted"])
        if x + w + 24 > limit: break
        b.append(f'<rect x="{x}" y="{H-pad-27}" width="{w+24:.1f}" height="28" rx="14" fill="none" stroke="{t["line"]}" stroke-width="1.2"/>{lab}')
        x += w + 32
    # the wire motif: which layers of the stack this project covers
    layers = ["web", "app", "api", "db"]; lx0, gap, ly = W - pad - 3 * 34, 34, H - pad - 21
    b.append(f'<line x1="{lx0}" y1="{ly}" x2="{lx0 + 3*gap}" y2="{ly}" stroke="{t["line"]}" stroke-width="1.5" stroke-dasharray="2 5" stroke-linecap="round"/>')
    for i, L in enumerate(layers):
        on = L in p.get("layers", []); cx = lx0 + i * gap
        b.append(f'<circle cx="{cx}" cy="{ly}" r="5" fill="{t["saffron"] if on else t["bg"]}" stroke="{t["saffron"] if on else t["line"]}" stroke-width="1.5"/>')
        b.append(text(L, "mono", 11, cx, ly + 20, t["text"] if on else t["muted"], anchor="middle")[0])
    return svg(W, H, t, "".join(b), f'{p["title"]}: {p["description"]} Built with {", ".join(p["stack"])}.', radius=18)

# ---------------------------------------------------------------- GitHub data
def gh(url):
    req = urllib.request.Request(url, headers={"Accept": "application/vnd.github+json",
                                               **({"Authorization": f"Bearer {TOKEN}"} if TOKEN else {})})
    with urllib.request.urlopen(req, timeout=30) as r: return json.load(r)

def main():
    cfg = json.loads((KIT / "projects.json").read_text())
    now = datetime.datetime.now(datetime.timezone.utc)
    try: repos = gh(f"https://api.github.com/users/{USER}/repos?per_page=100&sort=pushed")
    except Exception as e: print("GitHub API unavailable, building without live data:", e); repos = []
    by_name = {r["name"]: r for r in repos}

    (ROOT / "assets" / "cards").mkdir(parents=True, exist_ok=True)
    for mode, t in THEMES.items():
        (ROOT / "assets" / f"hero-{mode}.svg").write_text(hero(t))
        (ROOT / "assets" / f"footer-{mode}.svg").write_text(footer(t))
        for p in cfg["featured"]:
            (ROOT / "assets" / "cards" / f'{p["repo"]}-{mode}.svg').write_text(card(p, by_name.get(p["repo"], {}), t, now))

    # cards block in README
    def pic(p):
        base = f'./assets/cards/{p["repo"]}'
        meta = by_name.get(p["repo"], {})
        return (f'<a href="https://github.com/{USER}/{p["repo"]}"><picture>'
                f'<source media="(prefers-color-scheme: dark)" srcset="{base}-dark.svg"/>'
                f'<source media="(prefers-color-scheme: light)" srcset="{base}-light.svg"/>'
                f'<img src="{base}-light.svg" width="49%" alt="{escape(p["title"])}: {escape(p["description"])}"/></picture></a>')
    cards = "\n".join(pic(p) for p in cfg["featured"])
    live = [f'[{p["title"]}]({by_name[p["repo"]]["homepage"]})' for p in cfg["featured"]
            if by_name.get(p["repo"], {}).get("homepage")]
    if live: cards += "\n\nLive: " + ", ".join(live)

    # recently pushed list
    rows = []
    for r in repos:
        if r["fork"] or r["name"] in cfg.get("recent_exclude", []): continue
        lang = f' <sub>{r["language"]}</sub>' if r.get("language") else ""
        demo = f' · [live]({r["homepage"]})' if r.get("homepage") else ""
        rows.append(f'- [**{r["name"]}**]({r["html_url"]}){lang} · pushed {ago(r["pushed_at"], now)}{demo}')
        if len(rows) == cfg.get("recent_count", 6): break
    recent = "\n".join(rows) or "_Couldn't reach GitHub this run; the list refreshes on the next one._"

    readme = (ROOT / "README.md").read_text()
    for tag, content in [("CARDS", cards), ("RECENT", recent)]:
        readme = re.sub(rf"<!-- {tag}:START -->.*?<!-- {tag}:END -->",
                        f"<!-- {tag}:START -->\n{content}\n<!-- {tag}:END -->", readme, flags=re.S)
    (ROOT / "README.md").write_text(readme)
    print(f"built hero, footer, {len(cfg['featured'])} cards x2 themes, {len(rows)} recent repos")

if __name__ == "__main__":
    main()
