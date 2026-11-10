#!/bin/sh
# Check, and fetch, what open-katana leans on. Safe to re-run.   usage: setup.sh [--library]
#   --library   also build the CC0 starter sound library and register it with real-sfx
SK="${CLAUDE_SKILLS_DIR:-$HOME/.claude/skills}"; HERE="$(cd "$(dirname "$0")" && pwd)"
REAL_SFX_REPO="https://github.com/Clipwing/skills.git"; REAL_SFX_COMMIT="edbefcbc3474869e6cc1e8a7ca583b0efd0dab7e"   # pinned: review before bumping
need() { if command -v "$1" >/dev/null 2>&1; then echo "ok       $1"; else echo "MISSING  $1  ($2)"; fi; }
need node "Node 22+"; need python3 "3.9+"; need git ""
need ffmpeg "macOS: brew install ffmpeg-full, real-sfx needs its drawtext and rubberband filters"
need whisper-cli "whisper.cpp, for word timings: brew install whisper-cpp"
[ -n "$WHISPER_MODEL" ] && [ -f "$WHISPER_MODEL" ] && echo "ok       WHISPER_MODEL" || echo "note     WHISPER_MODEL is not set: layout.py needs --model PATH to a ggml-*.bin"
[ -n "$OPENAI_API_KEY" ] && echo "ok       OPENAI_API_KEY" || echo "note     OPENAI_API_KEY is not set in this shell: vo.sh needs it (or bring your own per-line voice clips)"
[ -f "$SK/hyperframes/SKILL.md" ] && echo "ok       /hyperframes skill" || echo "MISSING  /hyperframes skill: the person installs it with  npx hyperframes skills update"

# real-sfx (Clipwing): the sound pass. Third-party, so it is downloaded at a pinned commit, never bundled here.
if [ -f "$SK/real-sfx/SKILL.md" ]; then echo "ok       /real-sfx skill"
else
  tmp="$(mktemp -d)"; echo "fetching /real-sfx at $REAL_SFX_COMMIT ..."
  if git clone -q "$REAL_SFX_REPO" "$tmp/repo" && git -C "$tmp/repo" checkout -q "$REAL_SFX_COMMIT"; then
    mkdir -p "$SK" && cp -R "$tmp/repo/skills/real-sfx" "$SK/real-sfx" && echo "ok       /real-sfx installed to $SK/real-sfx (restart the agent session to load it)"
  else echo "MISSING  /real-sfx: could not fetch $REAL_SFX_REPO"; fi
  rm -rf "$tmp"
fi

# a sound library: real-sfx ships none, and with none every hit and riser stays silent
LIB="$HOME/.claude/sfx-library/cc0-starter"
if [ "$1" = "--library" ] && [ -f "$SK/real-sfx/scripts/setup.py" ]; then
  python3 "$HERE/sfx_library.py" "$LIB" && python3 "$SK/real-sfx/scripts/setup.py" init --library cc0="$LIB" --uisfx --index
fi
if [ -f "$SK/real-sfx/scripts/setup.py" ]; then
  python3 "$SK/real-sfx/scripts/setup.py" check 2>/dev/null | grep -E "library|index" || echo "note     no sound library registered: point real-sfx at yours, or run  setup.sh --library  for a CC0 starter"
fi
