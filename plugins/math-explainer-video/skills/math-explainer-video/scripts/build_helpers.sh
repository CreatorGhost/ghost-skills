#!/usr/bin/env bash
# Reusable build helpers for math-explainer videos. Source it, then call the functions.
#   source scripts/build_helpers.sh
# Assumes: run from src/; venv at ../.venv (override VENV=); SARVAM_API_KEY exported (~/.zshenv).
# The frame-critique loop (extract frames -> READ them -> fix -> re-render) is manual by design.

VENV="${VENV:-../../.venv}"
MEDIA="${MEDIA:-out}"
TEXBIN="/Library/TeX/texbin"

# render <scene.py> <SceneName> <quality: l|m|h>   (l=480p15 smoke, h=1080p60 final)
mev_render() {
  local scene="$1" name="$2" q="${3:-l}"
  PATH="$TEXBIN:$PATH" "$VENV/bin/manim" -q"$q" --media_dir "$MEDIA" "$scene" "$name"
}

# frames <video.mp4> <t1> [t2 t3 ...]   -> writes frames/f<t>.png for Claude to READ
mev_frames() {
  local vid="$1"; shift; mkdir -p frames
  for t in "$@"; do
    ffmpeg -nostdin -loglevel error -ss "$t" -i "$vid" -frames:v 1 "frames/f${t}.png" -y
  done
  echo "wrote: ${*/#/frames/f}"
}

# grid <out.png> <f1> <f2> <f3> <f4>   -> 2x2 tile so Claude Reads 4 frames per image.
# (Pass explicit args — zsh does NOT word-split unquoted vars, so "set -- $list" tricks break.)
mev_grid() {
  local outp="$1" a="$2" b="$3" c="$4" d="$5"
  ffmpeg -nostdin -loglevel error -i "$a" -i "$b" -i "$c" -i "$d" -filter_complex \
    "[0][1]hstack[t];[2][3]hstack[u];[t][u]vstack" "$outp" -y && echo "grid -> $outp"
}

# music <video.mp4> <music.wav> <out.mp4> [volume]   -> loops+fades+mixes a low bed under the narration
mev_music() {
  local vid="$1" mus="$2" outf="$3" vol="${4:-0.25}"   # ~8-10 dB under a -21 dB voice; 0.10 ships inaudible
  local dur fo
  dur=$(ffprobe -v error -show_entries format=duration -of csv=p=0 "$vid")
  fo=$(python3 -c "print(round($dur-3,2))")
  ffmpeg -nostdin -loglevel error -i "$mus" -filter_complex \
    "[0:a]aloop=loop=-1:size=4200000,atrim=0:${dur},volume=${vol},afade=t=in:st=0:d=2.5,afade=t=out:st=${fo}:d=3[m]" \
    -map "[m]" -c:a pcm_s16le /tmp/mev_bed.wav -y
  ffmpeg -nostdin -loglevel error -i "$vid" -i /tmp/mev_bed.wav -filter_complex \
    "[0:a][1:a]amix=inputs=2:duration=first:normalize=0[a]" \
    -map 0:v -map "[a]" -c:v copy -c:a aac -b:a 192k "$outf" -y
  echo "mixed -> $outf"
}

# get the free 3b1b track (Grant's Etude) for the music bed
mev_get_music() {
  local dest="${1:-out/music/grants_etude.wav}"; mkdir -p "$(dirname "$dest")"
  curl -sL --max-time 120 -o "$dest" \
    "https://www.vincentrubinetti.com/audio/3blue1brown/Vincent%20Rubinetti%20-%20The%20Music%20of%203Blue1Brown%20-%2006%20Grant%27s%20Etude.wav"
  echo "downloaded -> $dest"
}

# chapters <TrigIdentity.srt>  -> dumps each cue's start time + first words.
# Chapter lead-in phrases are video-specific, so pick the chapter-start cues from this list by eye
# (first chapter must be 0:00). manim-voiceover writes the .srt next to the rendered mp4.
mev_chapter_cues() {
  python3 - "$1" <<'PY'
import sys
for b in open(sys.argv[1]).read().strip().split("\n\n"):
    L=b.splitlines()
    if len(L)>=3 and "-->" in L[1]:
        t=L[1].split("-->")[0].strip(); h,m,r=t.split(":")
        sec=int(h)*3600+int(m)*60+int(float(r.replace(",",".")))
        print(f"{sec//60}:{sec%60:02d}  {' '.join(L[2:])[:70]}")
PY
}
