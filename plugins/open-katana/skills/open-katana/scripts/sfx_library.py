#!/usr/bin/env python3
"""Build a small CC0 starter sound library for /real-sfx from Openverse (Freesound recordings, public domain).

usage: sfx_library.py [OUT_DIR=~/.claude/sfx-library/cc0-starter] [--per 8]
Writes OUT_DIR/<role>/<role>_<id>_<title>.mp3 and OUT_DIR/LICENSES.csv (title, creator, licence, source page).
Only CC0 results are taken, so nothing here needs attribution. It is a starting point, picked by search rank and length,
not by ear: replace it with a real library (Sonniss GDC, your own packs) when you have one.
"""
import csv, json, os, re, sys, time, urllib.parse, urllib.request
out = os.path.expanduser(next((a for a in sys.argv[1:] if not a.startswith("--")), "~/.claude/sfx-library/cc0-starter"))
per = int(sys.argv[sys.argv.index("--per") + 1]) if "--per" in sys.argv else 8
ROLES = {   # role: (queries, min seconds, max seconds)
    "whoosh": (["whoosh", "swoosh", "swish fast"], 0.25, 2.5), "hit": (["impact", "cinematic hit", "boom impact"], 0.3, 4.0),
    "thump": (["thud", "thump"], 0.08, 1.5), "riser": (["riser", "rise build up"], 2.0, 10.0), "pop": (["pop", "bubble pop"], 0.04, 0.8),
    "click": (["click", "button click"], 0.02, 0.5), "typing": (["keyboard typing", "typing mechanical keyboard"], 2.0, 30.0),
    "glitch": (["glitch", "digital glitch"], 0.15, 3.0), "chime": (["chime", "bell ding", "sparkle magic"], 0.3, 4.0), "sub_drop": (["sub drop", "bass drop"], 0.5, 5.0),
}
def get(url):
    req = urllib.request.Request(url, headers={"User-Agent": "generic-client"})
    with urllib.request.urlopen(req, timeout=40) as r: return r.read()
rows = []
for role, (queries, lo, hi) in ROLES.items():
    os.makedirs(f"{out}/{role}", exist_ok=True); got = set()
    for q in queries:
        if len(got) >= per: break
        try: res = json.loads(get("https://api.openverse.org/v1/audio/?" + urllib.parse.urlencode({"q": q, "license": "cc0", "page_size": 20})))["results"]
        except Exception as e: print("search failed", q, e); time.sleep(2); continue
        for r in res:
            d = (r.get("duration") or 0) / 1000
            if len(got) >= per or r["id"] in got or not (lo <= d <= hi) or not r.get("url"): continue
            name = re.sub(r"[^a-z0-9]+", "-", (r.get("title") or "sound").lower()).strip("-")[:40]
            path = f"{out}/{role}/{role}_{r['id'][:8]}_{name}.mp3"
            try:
                if not os.path.exists(path): open(path, "wb").write(get(r["url"]))
            except Exception as e: print("skip", r.get("title"), e); continue
            got.add(r["id"]); rows.append([os.path.relpath(path, out), role, r.get("title"), r.get("creator"), "CC0", r.get("foreign_landing_url"), round(d, 2)])
        time.sleep(1)   # anonymous API: stay polite
    print(f"{role}: {len(got)}")
with open(f"{out}/LICENSES.csv", "w", newline="") as f:
    csv.writer(f).writerows([["file", "type", "title", "creator", "licence", "source", "seconds"]] + rows)
print(len(rows), "sounds ->", out)
