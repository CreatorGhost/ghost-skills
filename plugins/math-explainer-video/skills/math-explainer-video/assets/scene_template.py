"""
Starter template for a math-explainer video (3b1b-style, Manim CE + manim-voiceover + Sarvam).

Copy this to src/<topic>_scene.py and fill in the chapters. The channel ships HINGLISH-ONLY, voiced
by Sarvam Bulbul v3 speaker `aditya` — author the narration natively in Hinglish (see
references/hindi-hinglish-cut.md for the style + the pre-render QA gates). On-screen labels stay
ENGLISH. (Deepgram English service = legacy drafts only; code in references/manim-pipeline.md.)

Render (from src/):
  export SARVAM_API_KEY=...   # lives in ~/.zshenv
  PATH="/Library/TeX/texbin:$PATH" ../.venv/bin/manim -ql --media_dir build <topic>_scene.py Lesson   # smoke
  PATH="/Library/TeX/texbin:$PATH" ../.venv/bin/manim -qk --media_dir build <topic>_scene.py Lesson   # final 4K
Then mix music + chapters via build_helpers.sh. See SKILL.md for the full loop and gotchas.
"""
import base64
import json
import os
import urllib.request
from pathlib import Path

import numpy as np
from manim import *
from manim_voiceover import VoiceoverScene
from manim_voiceover.helper import remove_bookmarks
from manim_voiceover.services.base import SpeechService, initialize_speech_service, path_to_string

config.background_color = "#0e0e12"   # soft near-black (3b1b feel)


class SarvamService(SpeechService):
    """Sarvam Bulbul v3 — Hindi/English code-switching, speaker aditya, 48 kHz, DEFAULT pace/temp
    (overriding temperature adds hiss; overriding pace was rejected — leave both alone)."""
    def __init__(self, speaker="aditya", lang="hi-IN", model="bulbul:v3", rate=48000, api_key=None, **kwargs):
        initialize_speech_service(self, kwargs)
        self.speaker, self.lang, self.model, self.rate = speaker, lang, model, rate
        self.api_key = api_key or os.environ.get("SARVAM_API_KEY", "")

    def generate_from_text(self, text, cache_dir=None, path=None, **kwargs):
        if cache_dir is None:
            cache_dir = self.cache_dir
        input_text = remove_bookmarks(text)
        input_data = {"input_text": input_text, "service": "sarvam", "speaker": self.speaker,
                      "lang": self.lang, "model": self.model, "rate": self.rate}
        cached = self.get_cached_result(input_data, cache_dir)
        if cached is not None:
            return cached
        audio_path = (self.get_audio_basename(input_data) + ".wav") if path is None else path_to_string(path)
        payload = {"text": input_text, "target_language_code": self.lang, "speaker": self.speaker,
                   "model": self.model, "speech_sample_rate": self.rate}
        req = urllib.request.Request("https://api.sarvam.ai/text-to-speech",
            data=json.dumps(payload).encode("utf-8"), method="POST",
            headers={"api-subscription-key": self.api_key, "Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=90) as resp:
            data = json.load(resp)
        with open(str(Path(cache_dir) / audio_path), "wb") as fp:
            fp.write(base64.b64decode("".join(data["audios"])))
        return {"input_text": text, "input_data": input_data, "original_audio": audio_path}


class Lesson(VoiceoverScene, MovingCameraScene):
    def construct(self):
        self.set_speech_service(SarvamService(speaker="aditya", lang="hi-IN"))
        self.camera.frame.save_state()       # default frame to Restore after any zoom
        self.intro()
        # self.chapter_one()  ...add chapters...

    # ---------- helpers (proven; keep) ----------
    def say(self, text):
        return self.voiceover(text=text)

    def wipe(self, *keep):
        """Fade everything except `keep` (and their families — the scene holds submobjects, not VGroups)."""
        keepset = set()
        for k in keep:
            keepset.update(k.get_family())
        for m in self.mobjects:
            if m not in keepset:
                m.clear_updaters()
        gone = [m for m in self.mobjects if m not in keepset]
        if gone:
            self.play(*[FadeOut(m) for m in gone], run_time=0.6)

    def chapter_title(self, label, narration=None):
        """Spoken lead-in into each chapter — never a silent cut. Label stays ENGLISH."""
        card = Text(label, font_size=42, weight=BOLD)
        if narration:
            with self.say(narration):
                self.play(Write(card), run_time=1.2)
                b = getattr(self, "buddy", None)
                if b is not None and b in self.mobjects:
                    from root_buddy import look as _look
                    _look(self, b)     # keep the mascot alive during the chapter title
        else:
            self.play(Write(card), run_time=1.0)
            self.wait(0.4)
        self.play(card.animate.scale(0.5).to_corner(UL))
        return card

    def zoom_to(self, mob, factor=0.6, rt=1.0):
        self.play(self.camera.frame.animate.scale(factor).move_to(mob), run_time=rt)

    def reset_cam(self, rt=1.0):
        self.play(Restore(self.camera.frame), run_time=rt)

    def trace_side(self, p1, p2, color, lbl=None, rt=1.1):
        """Highlight a side as you name it. always_redraw lines can't be animated, so flash a static copy."""
        seg = Line(p1, p2, color=color, stroke_width=11)
        anims = [ShowPassingFlash(seg, time_width=0.7)]
        if lbl is not None:
            anims.append(FadeIn(lbl))
        self.play(*anims, run_time=rt)

    # ---------- example chapter (delete / adapt) ----------
    def intro(self):
        # Hook = validated confusion; spoken word == shown word (labels English, narration Hinglish);
        # travelling motion binds run_time to tracker.duration (survives any narration length).
        f = MathTex(r"\text{(your formula here)}", font_size=64)
        with self.say("ये formula दुनिया का हर student रटता है — but क्या ये actually समझ में आता है?"):
            self.play(Write(f), run_time=1.8)
        trust = Text("trust it   ✗", font_size=38, color=RED).next_to(f, DOWN, buff=0.55)
        with self.say("इस पर आपको बस भरोसा करना पड़ता है — क्योंकि WHY कोई नहीं बताता।"):
            self.play(f.animate.set_color(GREY_B), FadeIn(trust, shift=UP * 0.2))
        understand = Text("understand it   ✓", font_size=38, color=GREEN).move_to(trust)
        with self.say("आज हम इसे बदल देंगे — video के अंत तक ये आप ख़ुद बना पाओगे।") as tracker:
            self.play(f.animate.set_color(WHITE), ReplacementTransform(trust, understand),
                      run_time=max(1.0, tracker.duration * 0.5))
            self.play(Indicate(f, color=YELLOW, scale_factor=1.1), run_time=1.4)
        self.wipe()
