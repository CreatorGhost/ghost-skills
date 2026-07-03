"""Reusable 'Root' mascot (the radical √ with eyes) — Lucid Science channel character.
3b1b Pi-creature usage rules: keep it in a CORNER, brief, react-then-LEAVE. Never cover the math,
never let it sit on screen the whole time. build_root() returns the mobject; blink(scene, root) reacts.
"""
from manim import *
import numpy as np

ROOT_GREEN = "#83C167"


def _eye(r=0.29, look=UP * 0.4):
    s = Circle(radius=r, color=WHITE, fill_opacity=1, stroke_width=0)
    p = Dot(radius=r * 0.5, color=BLACK).move_to(s.get_center() + look * r * 0.4)
    return VGroup(s, p)


def build_root(scale=1.0, color=ROOT_GREEN):
    # tail -> peak -> deep V -> roof corner -> vinculum  (locked design)
    pts = [np.array(p) for p in (
        (-1.30, -0.15, 0), (-0.72, 0.05, 0), (-0.35, -1.15, 0),
        (0.35, 1.00, 0), (2.30, 1.00, 0))]
    rad = VMobject(color=color, stroke_width=17)
    rad.set_points_as_corners(pts)
    try:
        rad.joint_type = LineJointType.ROUND
        rad.cap_style = CapStyleType.ROUND
    except Exception:
        pass
    eyes = VGroup(_eye().move_to([1.15, 1.58, 0]), _eye().move_to([1.85, 1.58, 0]))
    root = VGroup(rad, eyes)
    root.eyes = eyes
    root.scale(scale)
    return root


def blink(scene, root, rt=0.09):
    for e in root.eyes:
        e.save_state()
    scene.play(*[e.animate.stretch(0.14, dim=1) for e in root.eyes], run_time=rt)
    scene.play(*[Restore(e) for e in root.eyes], run_time=rt)


def look(scene, root, rt=0.4):
    """Idle life: a little HOP + glance around + blink, so he's always moving while on screen.
    Call in a block's audio slack so it adds no duration."""
    pupils = VGroup(root.eyes[0][1], root.eyes[1][1])
    scene.play(root.animate.shift(UP * 0.16), rate_func=lambda t: there_and_back(t) ** 0.7, run_time=0.38)  # hop
    scene.play(pupils.animate.shift(RIGHT * 0.05), rate_func=there_and_back, run_time=rt)
    blink(scene, root)
    scene.play(pupils.animate.shift(LEFT * 0.05), rate_func=there_and_back, run_time=rt)
