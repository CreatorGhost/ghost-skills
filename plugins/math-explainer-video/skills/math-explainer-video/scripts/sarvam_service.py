"""
Sarvam AI (Bulbul v3) TTS — Hinglish code-switching for the Hindi math channel.

Two uses in one file:
  1) Quick A/B LISTEN TEST (run it):
        SARVAM_API_KEY=your_key  python3 tools/sarvam_tts.py
        SARVAM_API_KEY=your_key  python3 tools/sarvam_tts.py Ritu     # try another voice
     -> writes /tmp/hindi_sample_sarvam.wav  (then: open /tmp/hindi_sample_sarvam.wav)
  2) Reusable manim-voiceover service for the pipeline:
        from tools.sarvam_tts import SarvamService
        self.set_speech_service(SarvamService(speaker="aditya", lang="hi-IN"))

API: POST https://api.sarvam.ai/text-to-speech  | header: api-subscription-key
     model bulbul:v3 (<=2500 chars/req) | response JSON {audios:[base64...]} (default WAV)
"""
import base64
import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path

API = "https://api.sarvam.ai/text-to-speech"


def synth(text, out_path, *, api_key=None, speaker="aditya", lang="hi-IN",
          model="bulbul:v3", rate=48000, pace=1.0, audio_format=None):
    """Raw Sarvam TTS call. lang='hi-IN' gives Hindi-primary with native English code-switching.
    ONLY tuning: pace 0.9 (slightly slower for clarity) + 48 kHz. Leave temperature at Sarvam's
    default — raising it adds hiss; default temp is crystal clear.
    audio_format=None uses Sarvam's default (WAV) — guaranteed-valid value, no casing risk."""
    key = api_key or os.environ.get("SARVAM_API_KEY", "")
    if not key:
        raise SystemExit("Set SARVAM_API_KEY first (your Sarvam free-tier key from dashboard.sarvam.ai).")
    if len(text) > 2500:
        raise SystemExit(f"Text is {len(text)} chars; Bulbul v3 limit is 2500/request — split it.")
    payload = {"text": text, "target_language_code": lang, "speaker": speaker,
               "model": model, "pace": pace, "speech_sample_rate": rate}
    if audio_format:
        payload["audio_format"] = audio_format
    req = urllib.request.Request(API, data=json.dumps(payload).encode("utf-8"), method="POST",
                                 headers={"api-subscription-key": key, "Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            data = json.load(r)
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", "ignore")
        raise SystemExit(f"Sarvam HTTP {e.code}: {body}\n"
                         f"(If this is a speaker/param error, the message lists valid values — "
                         f"rerun with a different voice, e.g. `python3 tools/sarvam_tts.py Shubh`.)")
    audio = base64.b64decode("".join(data["audios"]))
    Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "wb") as f:
        f.write(audio)
    return out_path


# -------- manim-voiceover service (used by the render pipeline) --------
try:
    from manim_voiceover.helper import remove_bookmarks
    from manim_voiceover.services.base import SpeechService, initialize_speech_service, path_to_string

    class SarvamService(SpeechService):
        def __init__(self, speaker="aditya", lang="hi-IN", model="bulbul:v3", api_key=None, **kwargs):
            initialize_speech_service(self, kwargs)
            self.speaker, self.lang, self.model = speaker, lang, model
            self.api_key = api_key or os.environ.get("SARVAM_API_KEY", "")

        def generate_from_text(self, text, cache_dir=None, path=None, **kwargs):
            if cache_dir is None:
                cache_dir = self.cache_dir
            input_text = remove_bookmarks(text)
            input_data = {"input_text": input_text, "service": "sarvam",
                          "speaker": self.speaker, "lang": self.lang, "model": self.model}
            cached = self.get_cached_result(input_data, cache_dir)
            if cached is not None:
                return cached
            audio_path = (self.get_audio_basename(input_data) + ".wav") if path is None else path_to_string(path)
            synth(input_text, str(Path(cache_dir) / audio_path), api_key=self.api_key,
                  speaker=self.speaker, lang=self.lang, model=self.model)
            return {"input_text": text, "input_data": input_data, "original_audio": audio_path}
except ImportError:
    pass  # manim_voiceover not on this interpreter; the listen-test below still works


# The exact code-switching test sentence: Hindi narration with English math terms.
SAMPLE = ("बच्चों, ये identity ऐसे काम करती है — and you have to solve this equation "
          "ताकि आपको ये चीज़ें अच्छे से समझ में आ सकें। For example, sin theta और cos theta को "
          "square करके add करो — तो answer हमेशा exactly one आता है। यही तो असली magic है!")

if __name__ == "__main__":
    speaker = sys.argv[1] if len(sys.argv) > 1 else os.environ.get("SARVAM_SPEAKER", "aditya")
    out = "/tmp/hindi_sample_sarvam.wav"
    synth(SAMPLE, out, speaker=speaker)
    cost = round(len(SAMPLE) / 10000 * 30, 3)
    print(f"\n✅ wrote {out}")
    print(f"   voice={speaker} · {len(SAMPLE)} chars · ~Rs {cost} (Rs 30 / 10K chars)")
    print(f"   listen:  open {out}")
    print(f"   other voices:  python3 tools/sarvam_tts.py Ritu   (or Shubh, Priya, Anushka, Aditya, ...)")
