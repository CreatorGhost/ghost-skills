#!/usr/bin/env python3
"""Sound cue list for the film: the same word timings and scene starts the scenes use, so the two cannot drift.

  python3 cues.py           -> docs/cues.json   typed events (t, type, g, len, n) for /real-sfx to voice with real recordings
  python3 cues.py --stem    -> also assets/sfx.wav, a fallback stem from the sounds in assets/sfx/ (peak lands a frame after the picture)
Run from the project root. Edit EVENTS for your own film; the time is the frame where something STARTS to happen.
"""
import json, os, re, subprocess, sys, array
VO = json.loads(open("assets/timing.js").read().split("window.VO = ")[1].rstrip(";\n"))
G = {k: float(v) for k, v in re.findall(r"(\w+): ([\d.]+)", open("assets/grid.js").read())}
w = lambda s, n: VO["W"][s - 1][n - 1][1]          # when word n of sentence s is spoken
EVENTS = []
def ev(t, kind, g=1.0, length=None, n=None):
    EVENTS.append({k: v for k, v in {"t": round(t, 3), "type": kind, "g": g, "len": length, "n": n}.items() if v is not None})

# hero words: a whoosh into the light ones, a hit on the ones that land hard
for t in [w(1, 1), w(4, 2), w(13, 1) + .14, w(18, 1)]: ev(t - .1, "whoosh", .8, .35)
for t in [w(1, 2) + .12, w(5, 3), w(10, 5), w(13, 2), w(18, 2)]: ev(t, "hit", .5)   # under the voice: a full-level hit masks the word it lands on
# blade cuts, the zoom through the O, whips and the three tunnel flights
for t in [w(3, 10) + .04, w(4, 9) + .3, G["s13"] + 1.12, G["s15"] + 6.02]: ev(t - .08, "whoosh", 1.0, .45)
ev(w(2, 6) + .36, "whoosh", .3, .5)
for t in [G["s03"] + 1.44, G["s14"] + 1.12, G["s12"] + .02, w(11, 3) - .16, w(11, 4) - .16]: ev(t, "wipe", .7)
# things landing: boxes, the engine, checklist ticks, stack rows, pipeline pills
for t in [w(4, 6), w(4, 8), w(7, 1) + .08, w(15, 2)]: ev(t, "pop", .8)
for i in range(6): ev(w(7, 1) + .7 + i * .16, "tick", .45)
for n in [6, 8, 9, 10, 12]: ev(w(14, n) + .14, "thump", .8)
for n in [3, 4, 5]: ev(w(15, n) + .05, "pop")
ev(w(17, 8) + .02, "magic", .8)
# typing follows the voice; Enter is a click
ev(w(6, 1) + .75, "key", .7, w(6, 10) - w(6, 1) - .8, 77)
ev(w(9, 1), "key", .7, w(9, 16) + .4 - w(9, 1), 109)
ev(w(6, 10) + .06, "click"); ev(G["s10"] + min(w(9, 16) - G["s10"] + .55, 8.8), "click")
# glitch exits, one build into the payoff
for t in [G["s06"] + 2.76, G["s09"] + 2.0, w(16, 3) - .1]: ev(t, "glitch", .8, .4)
ev(w(18, 1) - 6.0, "riser", .7, 6.0)

os.makedirs("docs", exist_ok=True)
json.dump(sorted(EVENTS, key=lambda e: e["t"]), open("docs/cues.json", "w"), indent=1)
print(len(EVENTS), "events -> docs/cues.json")

if "--stem" in sys.argv:   # fallback when /real-sfx is not installed: one stem from the bundled files
    D = "assets/sfx/"; FILE = {"whoosh": "whoosh-short", "wipe": "whoosh-short", "hit": "impact-bass-1", "thump": "pop", "pop": "pop", "tick": "pop",
        "magic": "sparkle", "click": "key-press", "key": "typing", "glitch": "glitch-1", "riser": "riser"}
    VOL = {"whoosh": .6, "wipe": .35, "hit": .6, "thump": .5, "pop": .45, "tick": .3, "magic": .4, "click": .7, "key": .28, "glitch": .4, "riser": .22}
    def peak(name):
        a = array.array("h", subprocess.check_output(["ffmpeg", "-v", "error", "-i", D + name + ".mp3", "-f", "s16le", "-ac", "1", "-ar", "8000", "-"]))
        return max(range(len(a)), key=lambda i: abs(a[i])) / 8000
    PK = {n: peak(n) for n in set(FILE.values()) - {"typing", "riser", "glitch-1"}}
    ins, f = [], []
    def add(name, start, vol, trim=None):
        i = len(ins) // 2; ins.extend(["-i", D + name + ".mp3"])
        f.append(f"[{i}:a]" + (f"atrim=0:{trim:.2f},afade=t=out:st={max(0, trim - .08):.2f}:d=0.08," if trim else "") + f"volume={vol},adelay={int(max(0, start) * 1000)}:all=1[a{i}]")
    for e in EVENTS:
        name, vol = FILE[e["type"]], VOL[e["type"]] * e.get("g", 1)
        if e["type"] == "key":       # loop the 1.5 s typing burst across the stretch
            t = e["t"]
            while t < e["t"] + e["len"] - .2: add(name, t, vol, min(1.5, e["t"] + e["len"] - t)); t += 1.5
        elif e["type"] == "riser": add(name, e["t"] + e["len"] - 10.0, vol)          # the file peaks at its end
        elif e["type"] == "glitch": add(name, e["t"], vol, .5)
        else: add(name, e["t"] + (.08 if e["type"] in ("whoosh",) else 0) + 1 / 30 - PK.get(name, 0), vol)
    n = len(f); mix = ";".join(f) + ";" + "".join(f"[a{i}]" for i in range(n)) + f"amix=inputs={n}:normalize=0,alimiter=limit=0.89[o]"
    subprocess.run(["ffmpeg", "-v", "error", "-y", *ins, "-filter_complex", mix, "-map", "[o]", "-ar", "48000", "-ac", "2", "assets/sfx.wav"], check=True)
    print(n, "clips -> assets/sfx.wav")
