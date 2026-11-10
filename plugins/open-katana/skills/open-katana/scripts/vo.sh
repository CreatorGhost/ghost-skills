# One WAV per script line with OpenAI TTS (needs OPENAI_API_KEY: run as  zsh -ic "sh vo.sh script.txt outdir [voice]").
# usage: vo.sh SCRIPT.txt OUTDIR [VOICE=ash] [line numbers to redo...]
script="$1"; out="$2"; voice="${3:-ash}"; shift 3 2>/dev/null
mkdir -p "$out"; i=0
while IFS= read -r line; do
  [ -z "$line" ] && continue
  i=$((i+1)); n=$(printf %02d $i)
  if [ $# -gt 0 ] && ! printf '%s\n' "$@" | grep -qx "$i"; then continue; fi
  body=$(python3 -I -c 'import json,sys; print(json.dumps({"model":"gpt-4o-mini-tts","voice":sys.argv[2],"response_format":"wav","input":sys.argv[1],"instructions":"Hyped tech creator narrating a fast promo reel. Punchy, confident, energetic, slightly amazed. Crisp delivery, no long pauses."}))' "$line" "$voice")
  curl -sS --fail-with-body https://api.openai.com/v1/audio/speech -H "Authorization: Bearer $OPENAI_API_KEY" -H "Content-Type: application/json" -d "$body" -o "$out/raw_$n.wav" || { echo "FAIL $n"; continue; }
  ffmpeg -v error -y -i "$out/raw_$n.wav" -af "silenceremove=start_periods=1:start_threshold=-45dB:start_silence=0.02,areverse,silenceremove=start_periods=1:start_threshold=-45dB:start_silence=0.06,areverse" -ar 44100 -ac 1 "$out/s$n.wav"
  echo "$n $(ffprobe -v error -show_entries format=duration -of csv=p=0 "$out/s$n.wav") $line"
done < "$script"
