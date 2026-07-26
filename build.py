#!/usr/bin/env python3
"""Rewrite the <main> block of index.html from essay.txt.

essay.txt is the source of truth for the prose. Run this after editing it:
    python3 build.py
"""
import re, sys, html, pathlib

HERE = pathlib.Path(__file__).parent
essay = (HERE / "essay.txt").read_text(encoding="utf-8")
page = (HERE / "index.html").read_text(encoding="utf-8")

# everything below the notes rule is for the author, not the page
essay = essay.split("---------------------------------------------------------------")[0]

# ---- parse [label] blocks into paragraphs -------------------------------
sections, label, buf = [], None, []
for line in essay.splitlines():
    m = re.match(r"^\s*\[([a-z]+)\]\s*$", line)
    if m:
        if label:
            sections.append((label, buf))
        label, buf = m.group(1), []
    elif label is not None:
        buf.append(line)
if label:
    sections.append((label, buf))

def paras(lines):
    out, cur = [], []
    for ln in lines:
        if ln.strip():
            cur.append(ln.strip())
        elif cur:
            out.append(" ".join(cur)); cur = []
    if cur:
        out.append(" ".join(cur))
    return out

def typo(t):
    """Straight quotes to curly, plus a couple of mechanical fixes."""
    t = re.sub(r"\s+", " ", t).strip()
    t = t.replace("&", "&amp;")
    t = re.sub(r'"([^"]*)"', lambda m: "“" + m.group(1) + "”", t)
    t = t.replace("'", "’")
    t = re.sub(r"\bmy my\b", "my", t)
    t = re.sub(r"\beveryday\b(?= [a-z])", "every day", t)
    t = t.replace("miss him everyday", "miss him every day")
    return t

CUES = ["rise", "wake", "wind"]
def cues(t):
    """*starred* phrases become the three cues the pond performs."""
    i = [0]
    def sub(m):
        sign = CUES[min(i[0], len(CUES) - 1)]; i[0] += 1
        return f'<em class="cue" data-sign="{sign}">{m.group(1)}</em>'
    return re.sub(r"\*([^*]+)\*", sub, t)

# ---- emit -----------------------------------------------------------------
out = ["<main>"]
first_beat = True
for label, lines in sections:
    ps = [typo(p) for p in paras(lines)]
    if not ps:
        continue

    if label == "dawn":
        out.append(f'''  <section class="hero" data-mood="dawn">
    <div class="wrap">
      <div class="kicker">A Morning at the Water&rsquo;s Edge</div>
      <h1>Fishing,<br><em>Not Catching</em></h1>
      <p class="dek">{ps[0]}</p>
    </div>
  </section>''')
        continue

    if label == "closing":
        body = f'      <p>{ps[0]}</p>'
        if len(ps) > 1:
            body += '\n      <div class="rule"></div>\n' + "\n".join(f"      <p>{p}</p>" for p in ps[1:])
        out.append(f'''  <section class="closing" data-mood="closing">
    <div class="wrap rv">
{body}
    </div>
  </section>''')
        continue

    body = []
    for p in ps:
        if p.startswith("“"):                      # the pull quote
            body.append(f'''      <blockquote>
        {p}
      </blockquote>''')
        else:
            cls = ""
            if first_beat:
                cls = ' class="lede"'; first_beat = False
            pid = ' id="signsText"' if label == "signs" else ""
            body.append(f'      <p{pid}{cls}>{cues(p) if label == "signs" else p}</p>')
    out.append(f'''  <section class="beat" data-mood="{label}">
    <div class="wrap plate rv">
{chr(10).join(body)}
    </div>
  </section>''')

out.append('''  <div class="colophon">
    <div class="dedic">My Grandfather (RIP)</div>
    Wood thrush &middot; dawn &middot; still water
  </div>
</main>''')
new_main = "\n\n".join(out)

updated = re.sub(r"<main>.*?</main>", lambda m: new_main, page, flags=re.S)
if updated == page:
    sys.exit("ERROR: <main> block not found in index.html")
(HERE / "index.html").write_text(updated, encoding="utf-8")

moods = re.findall(r'data-mood="([^"]+)"', new_main)
n_cues = new_main.count('class="cue"')
print(f"rebuilt {len(moods)} sections: {', '.join(moods)}")
print(f"cues: {n_cues}  |  pull quotes: {new_main.count('<blockquote>')}")
