#!/usr/bin/env python3
"""Generates assets/bug-vs-dev.svg: a looping fighting-game duel (pure SVG + CSS, no JS).
One timeline (seconds) drives every element through the `ch()` channel registry."""
import math, random
random.seed(11)

L = 15.0          # loop length, seconds
EPS = 0.002       # width of an instant "hold" step
GROUND = 340

PAPER, INK, ORANGE = "#e8e6f4", "#0b0a10", "#8b86ff"; HOOD = "#3d3f99"
GREEN, DGREEN, RED, DIM, SKIN = "#e0405f", "#8a2438", "#ff4d6d", "#7d7b92", "#f2c9a0"
FONT = "ui-monospace,SFMono-Regular,Menlo,Consolas,'Liberation Mono',monospace"

# ------------------------------------------------------------------ channels
DEF = dict(x=0, y=0, r=0, sx=1, sy=1, o=1, d=1)
EASE = dict(out="cubic-bezier(.17,.84,.3,1)", i="cubic-bezier(.55,.05,.9,.4)", io="ease-in-out")
EASE["in"] = EASE["i"]
CH, ORIGIN = {}, {}


def ch(id, steps, origin=None):
    assert id not in CH, id
    merged = []
    for t, d in sorted(steps, key=lambda s: s[0]):
        if merged and abs(t - merged[-1][0]) < 1e-6:
            merged[-1][1].update(d)
        else:
            merged.append((t, dict(d)))
    CH[id] = merged
    if origin:
        ORIGIN[id] = origin


def vis(id, intervals):
    """opacity channel that is 1 inside the given (start,end) intervals and 0 outside"""
    m = []
    for a, b in sorted(intervals):
        if m and a <= m[-1][1] + 2 * EPS:
            m[-1][1] = max(m[-1][1], b)
        else:
            m.append([a, b])
    steps = []
    for a, b in m:
        steps.append((0, {"o": 1}) if a <= EPS else (a - EPS, {"o": 0}))
        if a > EPS:
            steps.append((a, {"o": 1}))
        if b < L - EPS:
            steps += [(b, {"o": 1}), (b + EPS, {"o": 0})]
        else:
            steps.append((L, {"o": 1}))
    ch(id, steps)


def frames(id):
    st = CH[id]
    used, first = set(), {}
    for t, d in st:
        for k, v in d.items():
            if k != "ease":
                used.add(k)
                first.setdefault(k, v)
    cur = dict(DEF)
    cur.update(first)
    out = []
    for t, d in st:
        cur.update({k: v for k, v in d.items() if k != "ease"})
        out.append((t, dict(cur), d.get("ease")))
    if out[0][0] > 0:
        out.insert(0, (0, dict(out[0][1]), None))
    if out[-1][0] < L:
        out.append((L, dict(out[-1][1]), None))
    return out, used


def num(v):
    s = ("%.3f" % v).rstrip("0").rstrip(".")
    return "0" if s in ("-0", "") else s


def props(v, used):
    p = []
    if used & {"x", "y", "r", "sx", "sy"}:
        p.append(f"transform:translate({num(v['x'])}px,{num(v['y'])}px) rotate({num(v['r'])}deg) scale({num(v['sx'])},{num(v['sy'])})")
    if "o" in used:
        p.append(f"opacity:{num(v['o'])}")
    if "d" in used:
        p.append(f"stroke-dashoffset:{num(v['d'])}")
    return ";".join(p)


def css_all():
    out = []
    for id in CH:
        fr, used = frames(id)
        body, last = [], -1
        for t, v, e in fr:
            pct = round(t / L * 100, 4)
            assert pct > last, (id, t)
            last = pct
            s = props(v, used) + (f";animation-timing-function:{EASE[e]}" if e else "")
            body.append(f"{pct}%{{{s}}}")
        out.append(f"@keyframes k_{id}{{{''.join(body)}}}#{id}{{animation:k_{id} {L}s linear infinite")
        if id in ORIGIN:
            out[-1] += f";transform-origin:{ORIGIN[id][0]}px {ORIGIN[id][1]}px"
        out[-1] += "}"
    return "".join(out)


# ------------------------------------------------------------------ drawing helpers
def P(x, y):
    return f"{x:.1f} {y:.1f}"


def line(pts, w, col, cap="round", extra=""):
    d = "M" + " L".join(P(*p) for p in pts)
    return f'<path d="{d}" fill="none" stroke="{col}" stroke-width="{w}" stroke-linecap="{cap}" stroke-linejoin="round"{extra}/>'


def T(content, size, fill, anchor="middle", weight=800, ls=2, stroke=None, sw=6, extra="", y=None):
    st = f' stroke="{stroke}" stroke-width="{sw}" stroke-linejoin="round" paint-order="stroke"' if stroke else ""
    yy = size * 0.35 if y is None else y
    return (f'<text text-anchor="{anchor}" y="{yy:.1f}" font-size="{size}" font-weight="{weight}" '
            f'letter-spacing="{ls}" fill="{fill}"{st} {extra}>{content}</text>')


DEV = {
 "idleA": dict(head=(3,-118), sh=(2,-98), hip=(-1,-56), ba=((-12,-84),(-18,-68)), fa=((14,-86),(26,-84)), sw=-52,
               bl=((-14,-30),(-24,0)), fl=((14,-30),(22,0)), sc=((-24,-108),(-44,-98))),
 "idleB": dict(head=(3,-116), sh=(2,-96), hip=(-1,-55), ba=((-12,-82),(-19,-66)), fa=((14,-84),(26,-83)), sw=-50,
               bl=((-15,-29),(-25,0)), fl=((15,-29),(23,0)), sc=((-24,-104),(-44,-88))),
 "runA": dict(head=(14,-112), sh=(9,-94), hip=(-3,-56), ba=((18,-82),(30,-90)), fa=((-4,-84),(-16,-72)), sw=195,
              bl=((-20,-34),(-40,-12)), fl=((24,-40),(20,-12)), sc=((-30,-100),(-72,-96))),
 "runB": dict(head=(14,-110), sh=(9,-92), hip=(-3,-54), ba=((-8,-80),(-20,-70)), fa=((0,-86),(-14,-96)), sw=190,
              bl=((16,-36),(8,-8)), fl=((-18,-32),(-38,-8)), sc=((-30,-96),(-70,-84))),
 "windup": dict(head=(-2,-114), sh=(-3,-94), hip=(-8,-52), ba=((-18,-84),(-10,-66)), fa=((4,-108),(-10,-120)), sw=-140,
                bl=((-26,-30),(-44,0)), fl=((10,-36),(22,0)), sc=((-26,-104),(-52,-90))),
 "slashF": dict(head=(24,-108), sh=(16,-90), hip=(4,-48), ba=((-2,-86),(-14,-90)), fa=((36,-92),(58,-90)), sw=-4,
                bl=((-8,-26),(-38,0)), fl=((32,-30),(40,0)), sc=((-10,-100),(-60,-110))),
 "slashD": dict(head=(20,-108), sh=(12,-92), hip=(2,-50), ba=((-6,-84),(-16,-76)), fa=((34,-110),(48,-116)), sw=38,
                bl=((-12,-28),(-34,0)), fl=((26,-32),(36,0)), sc=((-14,-100),(-56,-96))),
 "slashB": dict(head=(14,-98), sh=(10,-82), hip=(6,-42), ba=((-6,-76),(-16,-84)), fa=((28,-64),(40,-58)), sw=-38,
                bl=((-10,-22),(-30,0)), fl=((30,-24),(38,0)), sc=((-14,-90),(-50,-80))),
 "jump": dict(head=(8,-122), sh=(6,-102), hip=(2,-64), ba=((-8,-92),(-18,-104)), fa=((18,-112),(24,-128)), sw=-70,
              bl=((-12,-46),(-26,-30)), fl=((18,-50),(6,-34)), sc=((-26,-112),(-60,-130))),
 "hit": dict(head=(-14,-108), sh=(-8,-92), hip=(4,-54), ba=((-24,-98),(-36,-112)), fa=((-2,-72),(8,-60)), sw=75,
             bl=((-14,-30),(-34,-4)), fl=((18,-34),(30,-8)), sc=((-30,-92),(-48,-70))),
 "charge": dict(head=(14,-92), sh=(6,-76), hip=(-8,-42), ba=((-14,-66),(-24,-56)), fa=((2,-62),(-8,-58)), sw=2,
                bl=((-26,-24),(-44,0)), fl=((18,-26),(32,0)), sc=((-30,-82),(-62,-70))),
 "finish": dict(head=(42,-82), sh=(30,-68), hip=(10,-38), ba=((6,-62),(-8,-70)), fa=((52,-70),(72,-64)), sw=-4,
                bl=((-8,-20),(-46,0)), fl=((40,-24),(58,0)), sc=((-10,-80),(-70,-86))),
 "victory": dict(head=(3,-118), sh=(2,-98), hip=(-1,-56), ba=((-16,-82),(-24,-68)), fa=((20,-112),(24,-134)), sw=-84,
                 bl=((-14,-30),(-24,0)), fl=((14,-30),(22,0)), sc=((-26,-110),(-50,-100))),
}


SC = {  # near scythe: elbow, control, tip
 "idle": ((-62,-76), (-84,-72), (-92,-48)),
 "run": ((-52,-66), (-70,-62), (-78,-44)),
 "prep": ((-46,-92), (-40,-122), (-14,-134)),
 "strike": ((-72,-82), (-90,-98), (-106,-97)),
 "hit": ((-48,-98), (-56,-118), (-44,-128)),
 "stagger": ((-56,-90), (-70,-96), (-88,-72)),
}
BUGP = {
 "idleA": dict(gait="A", sc="idle", tilt=0, sx=1, sy=1, eye="n", mand=.3, ant=0),
 "idleB": dict(gait="B", sc="idle", tilt=0, sx=1, sy=1, eye="n", mand=.5, ant=1),
 "runA": dict(gait="SA", sc="run", tilt=-4, sx=1, sy=1, eye="n", mand=.8, ant=0),
 "runB": dict(gait="SB", sc="run", tilt=-4, sx=1, sy=1, eye="n", mand=.8, ant=1),
 "prep": dict(gait="A", sc="prep", tilt=10, sx=1, sy=1, eye="n", mand=1, ant=1),
 "strike": dict(gait="SA", sc="strike", tilt=-7, sx=1, sy=1, eye="n", mand=1, ant=0),
 "hit": dict(gait="A", sc="hit", tilt=-8, sx=1.1, sy=.86, eye="x", mand=1, ant=1),
 "stagger": dict(gait="B", sc="stagger", tilt=13, sx=1, sy=1, eye="d", mand=.6, ant=1),
}


def bug_legs(gait, far=False):
    wide = gait.startswith("S")
    out = []
    for i, bx in enumerate((-18, 12, 44)):
        ph = (i % 2 == 0) if gait in ("A", "SA") else (i % 2 == 1)
        if ph:
            kx, ky, fx, fy = bx - (26 if wide else 16), (-34 if wide else -30), bx - (30 if wide else 14), 0
        else:
            kx, ky, fx, fy = bx + (10 if wide else -4), (-38 if wide else -34), bx + (16 if wide else 4), (-8 if wide else -3)
        if far:
            kx, fx, ky = kx + 8, fx + 8, ky - 2
        out.append(f"M{bx} -18 L{kx} {ky} L{fx} {fy}")
    return " ".join(out)


# ------------------------------------------------------------------ timeline: DEV
D_INT = {
 "idle": [(0, 2.0), (3.8, 4.46), (5.1, 5.5), (8.02, 8.1), (9.75, 10.8), (13.4, L)],
 "run": [(2.0, 2.9), (6.68, 6.82)],
 "windup": [(2.9, 3.05), (5.5, 5.65), (6.45, 6.68)],
 "slashF": [(3.05, 3.2), (6.82, 7.22)],
 "hit": [(3.2, 3.8), (4.54, 5.1)],
 "hitW": [(4.46, 4.54)],
 "jump": [(5.65, 6.45), (8.1, 8.45)],
 "slashD": [(7.22, 7.62)], "slashB": [(7.62, 8.02)],
 "charge": [(8.45, 9.3)], "finish": [(9.3, 9.75)], "victory": [(10.8, 13.4)],
}
for k, v in D_INT.items():
    vis(f"d_{k}", v)

ch("dev_x", [
 (0, {"x": 250, "y": GROUND, "sx": 1}), (2.0, {"x": 250}), (2.9, {"x": 530}), (3.05, {"x": 530}), (3.10, {"x": 546}),
 (3.2, {"x": 546, "ease": "out"}), (3.8, {"x": 440}), (4.58, {"x": 440, "ease": "out"}), (5.1, {"x": 330}),
 (5.65, {"x": 330}), (6.449, {"x": 860, "sx": 1}), (6.45, {"x": 860, "sx": -1}), (6.68, {"x": 860}), (6.82, {"x": 800}),
 (7.22, {"x": 796}), (7.62, {"x": 792}), (8.02, {"x": 790}), (8.1, {"x": 790}), (8.45, {"x": 930}),
 (9.3, {"x": 930}), (9.44, {"x": 330}), (10.799, {"x": 330, "sx": -1}), (10.8, {"x": 330, "sx": 1}),
 (14.55, {"x": 330}), (14.6, {"x": 250}),
])
ch("dev_y", [
 (0, {"y": 0}), (5.65, {"y": 0, "ease": "out"}), (6.05, {"y": -62, "ease": "in"}), (6.45, {"y": 0}),
 (8.1, {"y": 0, "ease": "out"}), (8.27, {"y": -50, "ease": "in"}), (8.45, {"y": 0}),
 (10.8, {"y": 0, "ease": "out"}), (10.95, {"y": -24, "ease": "in"}), (11.1, {"y": 0}),
])

# ------------------------------------------------------------------ timeline: BUG
B_INT = {
 "idle": [(0, 2.0), (3.8, 4.1), (4.75, 6.86), (14.6, L)],
 "run": [(2.0, 2.9)],
 "prep": [(2.9, 3.05), (4.1, 4.3)],
 "strike": [(3.05, 3.2), (4.3, 4.75)],
 "stagger": [(3.2, 3.8), (8.02, 9.40)],
 "hit": [(6.94, 7.26), (7.34, 7.66), (7.74, 8.02)],
 "hitW": [(6.86, 6.94), (7.26, 7.34), (7.66, 7.74)],
}
for k, v in B_INT.items():
    vis(f"b_{k}", v)

jit = []
for i in range(22):
    jit.append((8.5 + i * 0.04, {"x": 580 + (3 if i % 2 else -3)}))
ch("bug_x", [
 (0, {"x": 860, "y": GROUND, "sx": 1}), (2.0, {"x": 860}), (2.9, {"x": 830}), (3.05, {"x": 830}), (3.10, {"x": 814}),
 (3.2, {"x": 814, "ease": "out"}), (3.8, {"x": 900}), (4.3, {"x": 900}), (4.46, {"x": 610}),
 (6.499, {"x": 610, "sx": 1}), (6.5, {"x": 610, "sx": -1}), (6.86, {"x": 610}), (6.9, {"x": 604}), (7.26, {"x": 604}),
 (7.3, {"x": 597}), (7.66, {"x": 597}), (7.7, {"x": 588}), (8.02, {"x": 588, "ease": "out"}), (8.48, {"x": 580}),
 *jit, (9.4, {"x": 580}), (14.55, {"x": 580, "sx": -1}), (14.6, {"x": 860, "sx": 1}),
])
ch("bug_root", [(0, {"o": 1}), (0.3, {"o": 1}), (0.34, {"o": .1}), (0.4, {"o": 1}), (0.46, {"o": .15}), (0.5, {"o": 1})])
# the finisher cuts the bug on the line x+y=860 (world) -> lx+ly=-40 in bug space
ch("half_a", [(0, {"x": 580, "y": GROUND, "r": 0, "o": 0}), (9.4 - EPS, {"o": 0}), (9.4, {"o": 1}), (9.9, {"x": 580, "y": GROUND, "r": 0, "o": 1}),
              (10.9, {"x": 528, "y": GROUND - 46, "r": -16, "o": 0, "ease": "out"})])
ch("half_b", [(0, {"x": 580, "y": GROUND, "r": 0, "o": 0}), (9.4 - EPS, {"o": 0}), (9.4, {"o": 1}), (9.9, {"x": 580, "y": GROUND, "r": 0, "o": 1}),
              (10.9, {"x": 636, "y": GROUND + 34, "r": 14, "o": 0, "ease": "out"})])

# ------------------------------------------------------------------ timeline: HUD, camera, overlays
ch("hpD", [(0, {"sx": 1}), (4.46 - EPS, {"sx": 1}), (4.46, {"sx": .78}), (14.55, {"sx": .78}), (14.6, {"sx": 1})], origin=(454, 85))
ch("hpDg", [(0, {"sx": 1}), (4.9, {"sx": 1}), (5.3, {"sx": .78}), (14.55, {"sx": .78}), (14.6, {"sx": 1})], origin=(454, 85))
ch("hpB", [(0, {"sx": 1}), (6.86 - EPS, {"sx": 1}), (6.86, {"sx": .88}), (7.26 - EPS, {"sx": .88}), (7.26, {"sx": .74}),
           (7.66 - EPS, {"sx": .74}), (7.66, {"sx": .58}), (9.4 - EPS, {"sx": .58}), (9.4, {"sx": 0}), (14.55, {"sx": 0}), (14.6, {"sx": 1})], origin=(1242, 85))
ch("hpBg", [(0, {"sx": 1}), (7.2, {"sx": 1}), (7.3, {"sx": .88}), (7.6, {"sx": .88}), (7.7, {"sx": .74}), (8.0, {"sx": .74}),
            (8.1, {"sx": .58}), (9.8, {"sx": .58}), (10.3, {"sx": 0}), (14.55, {"sx": 0}), (14.6, {"sx": 1})], origin=(1242, 85))
ch("pip", [(0, {"o": 0}), (10.5 - EPS, {"o": 0}), (10.5, {"o": 1}), (14.55, {"o": 1}), (14.6, {"o": 0})])


def shake_steps(events):
    st = []
    for t0, dur, amp in events:
        n = max(2, int(dur / 0.035))
        for i in range(n):
            f = 1 - i / n
            sgn = 1 if i % 2 else -1
            st.append((t0 + i * 0.035, {"x": sgn * amp * f * (0.6 + 0.4 * random.random()), "y": -sgn * amp * f * 0.6 * random.random()}))
        st.append((t0 + dur, {"x": 0, "y": 0}))
    return st


cam = [(0, {"x": 0, "y": 0, "sx": 1, "sy": 1})]
cam += shake_steps([(3.05, .4, 7), (4.46, .45, 7), (6.86, .25, 3), (7.26, .25, 3), (7.66, .3, 5), (9.4, .7, 13), (10.4, .3, 5)])
cam += [(8.45, {"sx": 1, "sy": 1, "ease": "in"}), (9.395, {"sx": 1.05, "sy": 1.05}), (9.4, {"sx": 1, "sy": 1})]
ch("cam", cam, origin=(600, 230))

ch("flash", [(0, {"o": 0}), (1.5 - EPS, {"o": 0}), (1.5, {"o": .12}), (1.8, {"o": 0}), (3.05 - EPS, {"o": 0}), (3.05, {"o": .18}),
             (3.3, {"o": 0}), (4.46 - EPS, {"o": 0}), (4.46, {"o": .15}), (4.7, {"o": 0}), (9.4 - EPS, {"o": 0}), (9.4, {"o": .0}), (9.8, {"o": 0})])
ch("fade", [(0, {"o": 0}), (14.0, {"o": 0}), (14.55, {"o": 1}), (14.8, {"o": 1}), (15.0, {"o": 0})])
ch("dim", [(0, {"o": 0}), (8.45, {"o": 0}), (8.8, {"o": .6}), (9.395, {"o": .6}), (9.4, {"o": 0})])

# ------------------------------------------------------------------ timeline: FX & text
def pop(id, x, y, t0, dur, rise=34, s0=1.5, rot=0):
    ch(id, [(t0 - EPS, {"x": x, "y": y, "r": rot, "sx": .6, "sy": .6, "o": 0}),
            (t0, {"sx": s0, "sy": s0, "o": 1, "ease": "out"}), (t0 + .12, {"sx": 1, "sy": 1}),
            (t0 + dur * .6, {"y": y - rise * .6, "o": 1}), (t0 + dur, {"y": y - rise, "o": 0})])


def burst(id, x, y, t0, dur, s0=.2, s1=1.4):
    ch(id, [(t0 - EPS, {"x": x, "y": y, "sx": s0, "sy": s0, "o": 0}), (t0, {"o": 1, "ease": "out"}), (t0 + dur, {"sx": s1, "sy": s1, "o": 0})])


def arc(id, t0, sweep=.06, hold=.12, fade=.25):
    ch(id, [(t0 - EPS, {"d": 1, "o": 0}), (t0, {"d": 1, "o": 1}), (t0 + sweep, {"d": 0, "o": 1}),
            (t0 + sweep + hold, {"d": 0, "o": 1}), (t0 + sweep + hold + fade, {"d": -1, "o": 0})])


# title cards
ch("round", [(0.25, {"x": -240, "y": 176, "o": 0}), (0.6, {"x": 600, "o": 1, "ease": "out"}), (1.3, {"x": 600}), (1.5, {"x": 840, "o": 0})])
ch("fight", [(1.5 - EPS, {"x": 600, "y": 176, "sx": 2.2, "sy": 2.6, "o": 0}), (1.5, {"o": 1, "ease": "out"}), (1.6, {"sx": 1, "sy": 1}),
             (2.05, {"sx": 1, "sy": 1, "o": 1}), (2.35, {"sx": 1.2, "sy": 1.2, "o": 0})])
# clash
burst("sp_clash", 700, 218, 3.05, .45, .2, 1.5)
burst("ring_clash", 700, 218, 3.05, .55, .1, 2.6)
pop("t_clash", 700, 150, 3.05, .8, 14, 1.6, -6)
# bug lands the hit on dev
burst("sp_dev", 456, 252, 4.46, .4, .2, 1.3)
arc("arc_bug", 4.46)
pop("t_d22", 440, 180, 4.5, .9, 40, 1.5)
# dev's combo
burst("sp_h1", 612, 266, 6.86, .3, .2, 1.1)
burst("sp_h2", 600, 280, 7.26, .3, .2, 1.1)
burst("sp_h3", 606, 270, 7.66, .35, .2, 1.3)
arc("arc_1", 6.84)
arc("arc_2", 7.24)
arc("arc_3", 7.64)
pop("t_d12", 600, 215, 6.9, .6, 34, 1.4)
pop("t_d14", 610, 200, 7.3, .6, 34, 1.4)
pop("t_d16", 618, 185, 7.7, .8, 34, 1.6)
ch("c1", [(0, {"o": 0}), (6.86 - EPS, {"o": 0}), (6.86, {"o": 1}), (7.26, {"o": 0})])
ch("c2", [(0, {"o": 0}), (7.26 - EPS, {"o": 0}), (7.26, {"o": 1}), (7.66, {"o": 0})])
ch("c3", [(0, {"o": 0}), (7.66 - EPS, {"o": 0}), (7.66, {"o": 1}), (8.5, {"o": 1}), (8.7, {"o": 0})])
ch("alert", [(6.5 - EPS, {"x": 610, "y": 176, "sx": .5, "sy": .5, "o": 0}), (6.5, {"sx": 1.5, "sy": 1.5, "o": 1, "ease": "out"}),
             (6.62, {"sx": 1, "sy": 1}), (6.85, {"o": 1}), (6.86, {"o": 0})])
# jump / landing dust
burst("dust1", 330, GROUND - 4, 5.65, .4, .3, 1.6)
burst("dust2", 860, GROUND - 4, 6.45, .45, .3, 1.8)
burst("dust3", 930, GROUND - 4, 8.45, .4, .3, 1.5)
# finisher
ch("aura", [(8.45 - EPS, {"x": 930, "y": 270, "sx": .3, "sy": .3, "o": 0})]
   + [(8.5 + .1 * i, {"sx": 1.0 + .22 * (i % 2), "sy": 1.0 + .22 * (i % 2), "o": .85}) for i in range(8)]
   + [(9.3, {"sx": 1.4, "sy": 1.4, "o": 1}), (9.36, {"sx": 2.2, "sy": 2.2, "o": 0})])
en = [(8.45 - EPS, {"x": 930, "y": 270, "sx": 1.9, "sy": 1.9, "o": 0})]
for k in range(3):
    t = 8.5 + .27 * k
    en += [(t, {"sx": 1.9, "sy": 1.9, "o": 0}), (t + .04, {"o": 1}), (t + .26, {"sx": .5, "sy": .5, "o": 0})]
ch("energy", en)
ch("hotfix", [(8.6 - EPS, {"x": 600, "y": 150, "sx": 1, "sy": 1, "o": 0}), (8.6, {"o": 1}), (9.3, {"o": 1}), (9.4, {"sx": 1.05, "sy": 1.05, "o": 0})])
ch("streak", [(9.3 - EPS, {"x": 930, "y": 0, "sx": 0, "o": 0}), (9.3, {"o": 1}), (9.42, {"sx": 1}), (9.75, {"sx": 1, "o": 0})])
ch("streak_bug", [(4.3 - EPS, {"x": 880, "y": 0, "sx": 0, "o": 0}), (4.3, {"o": 1}), (4.46, {"sx": 1}), (4.75, {"sx": 1, "o": 0})])
for i, xx in enumerate((850, 720, 600)):
    ch(f"after{i}", [(9.3 - EPS, {"x": xx, "y": GROUND, "sx": -1, "o": 0}), (9.3 + .035 * i + .03, {"o": .35}), (9.62, {"o": 0})])
arc("arc_fin", 9.4, sweep=.04, hold=.75, fade=.3)
burst("sp_fin", 580, 288, 9.4, .6, .3, 2.2)
pop("t_d58", 580, 176, 9.45, 1.0, 34, 1.7)
pop("t_crit", 580, 206, 9.5, 1.0, 20, 1.3)
for i in range(26):
    px, py = 520 + random.random() * 120, 230 + random.random() * 90
    vx, vy = (random.random() - .5) * 420, -random.random() * 260 - 40
    w = random.choice((5, 7, 9))
    t0 = 9.9
    pos = lambda t: (px + vx * t, py + vy * t + 0.5 * 700 * t * t)
    ch(f"pp{i}", [(t0 - EPS, {"x": px, "y": py, "r": 0, "o": 0}), (t0, {"o": 1}), (t0 + .45, {"x": pos(.45)[0], "y": pos(.45)[1], "r": 90}),
                  (t0 + 1.2, {"x": pos(1.2)[0], "y": pos(1.2)[1], "r": 220, "o": 0})])
# end cards
ch("ko", [(10.4 - EPS, {"x": 600, "y": 168, "sx": 2.0, "sy": 2.0, "o": 0}), (10.4, {"o": 1, "ease": "out"}), (10.5, {"sx": .94, "sy": .94}),
          (10.58, {"sx": 1, "sy": 1}), (13.0, {"sx": 1, "sy": 1, "o": 1}), (13.4, {"o": 0})])
ch("panel", [(11.0 - EPS, {"x": 600, "y": 284, "o": 0}), (11.2, {"y": 262, "o": 1, "ease": "out"}), (13.2, {"y": 262, "o": 1}), (13.6, {"y": 262, "o": 0})])



# =================================================================== INK PALETTE + ART (v4)
INK, PAPER, RED, STEEL, DIM, RIM = "#08080b", "#e9e5da", "#c4262e", "#9d9aa8", "#6f6d7a", "#a9a5b4"
EASE["steps"] = "steps(14,end)"
FACE = open("av_face4.b64").read()


def L2(pts, w, ink=INK, rim=RIM, tint=None, rw=2.2):
    d = "M" + " L".join(P(*p) for p in pts)
    if tint:
        return f'<path d="{d}" fill="none" stroke="{tint}" stroke-width="{w}" stroke-linecap="round" stroke-linejoin="round"/>'
    return (f'<path d="{d}" fill="none" stroke="{rim}" stroke-width="{w + rw}" stroke-linecap="round" stroke-linejoin="round"/>'
            f'<path d="{d}" fill="none" stroke="{ink}" stroke-width="{w}" stroke-linecap="round" stroke-linejoin="round"/>')


def sword(h, ang, tint=None):
    a = math.radians(ang)
    ux, uy = math.cos(a), math.sin(a)
    nx, ny = -uy, ux
    p = lambda s, n=0: (h[0] + ux * s + nx * n, h[1] + uy * s + ny * n)
    if tint:
        return line([p(-10), p(88)], 5, tint)
    return (line([p(9), p(88)], 13, RED, extra=' opacity=".22"') + line([p(-10), p(8)], 6, INK) + line([p(9, -6), p(9, 6)], 4, RIM)
            + line([p(9), p(88)], 6, INK) + line([p(10), p(87)], 2.4, "#dcd8e2"))


def dev_pose(p, tint=None):
    hx, hy = p["head"]
    sh, hip = p["sh"], p["hip"]
    ctl, end = p["sc"]
    ink = tint or INK
    back = tint or "#14141a"
    o = []
    leg = lambda l, col: L2([hip, l[0], l[1], (l[1][0] + 10, l[1][1])], 9, col, tint=tint)
    o.append(leg(p["bl"], back))
    o.append(L2([sh, *p["ba"]], 7, back, tint=tint))
    tail = (hip[0] + (end[0] - sh[0]) * .55, hip[1] + 22 + (end[1] - sh[1]) * .2)
    o.append(f'<path d="M{P(sh[0] - 5, sh[1] + 8)} Q{P(hip[0] - 10, hip[1] + 6)} {P(*tail)} L{P(hip[0] + 9, hip[1] + 14)} L{P(sh[0] + 8, sh[1] + 8)}Z" fill="{ink}" stroke="{tint or RIM}" stroke-width="1.2"/>')
    o.append(L2([sh, hip], 20, ink, tint=tint))
    o.append(f'<path d="M{P(sh[0] - 5, sh[1] - 5)} Q{P(*ctl)} {P(*end)}" fill="none" stroke="{tint or RED}" stroke-width="6" stroke-linecap="round"/>')
    o.append(leg(p["fl"], ink))
    o.append(f'<path d="M{P(sh[0] - 4, sh[1] - 3)} L{P(sh[0] + 8, sh[1] - 3)} L{P(sh[0] + 2, sh[1] + 15)}Z" fill="{tint or PAPER}"/>')
    o.append(L2([sh, (hx, hy + 10)], 8, ink, tint=tint))
    if tint:
        o.append(f'<circle cx="{hx}" cy="{hy - 2}" r="18" fill="{tint}"/>')
    else:
        o.append(f'<use href="#faceg" transform="translate({hx} {hy - 2}) scale(18)"/><circle cx="{hx}" cy="{hy - 2}" r="18" fill="none" stroke="{INK}" stroke-width="3.5"/>'
                 f'<circle cx="{hx}" cy="{hy - 2}" r="19.8" fill="none" stroke="{RIM}" stroke-width=".8"/>')
    o.append(L2([sh, *p["fa"]], 7, ink, tint=tint))
    o.append(sword(p["fa"][1], p["sw"], tint))
    return "".join(o)


def scythe(sc, dx, dy, tint, dim):
    e, ct, tp = [(a + dx, b + dy) for a, b in sc]
    s = (-30 + dx, -52 + dy)
    q = f"M{P(*e)} Q{P(*ct)} {P(*tp)}"
    if tint:
        return line([s, e], 8, tint) + f'<path d="{q}" fill="none" stroke="{tint}" stroke-width="8" stroke-linecap="round"/>'
    return (line([s, e], 9, INK) + f'<path d="{q}" fill="none" stroke="{RED}" stroke-width="15" stroke-linecap="round" opacity=".18"/>'
            + f'<path d="{q}" fill="none" stroke="{INK}" stroke-width="9" stroke-linecap="round"/>'
            + f'<path d="{q}" fill="none" stroke="{"#4a4856" if dim else "#dcd8e2"}" stroke-width="3" stroke-linecap="round"/>'
            + line([s, e], 3, "#5c5a68" if dim else RIM))


def bug_pose(pz, tint=None):
    sc = SC[pz["sc"]]
    ink = tint or "#0a0a0d"
    rim = tint or RIM
    o = [f'<path d="{bug_legs(pz["gait"], True)}" fill="none" stroke="{tint or "#2a2833"}" stroke-width="5" stroke-linecap="round" stroke-linejoin="round"/>',
         scythe(sc, 10, -6, tint, True),
         f'<path d="{bug_legs(pz["gait"])}" fill="none" stroke="{ink}" stroke-width="9" stroke-linecap="round" stroke-linejoin="round"/>',
         f'<path d="{bug_legs(pz["gait"])}" fill="none" stroke="{tint or "#8a8796"}" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"/>',
         f'<ellipse cx="28" cy="-48" rx="46" ry="32" fill="{ink}" stroke="{rim}" stroke-width="2.2"/>',
         f'<path d="M28 -78 L28 -18 M-2 -70 Q10 -48 -2 -24 M58 -70 Q46 -48 58 -24" fill="none" stroke="{tint or "#3b3946"}" stroke-width="2.5"/>',
         f'<path d="M-2 -68 Q28 -92 62 -66" fill="none" stroke="{rim}" stroke-width="2" opacity=".6"/>',
         f'<ellipse cx="-34" cy="-46" rx="22" ry="19" fill="{ink}" stroke="{rim}" stroke-width="2.2"/>']
    ex, ey = -44, -52
    if pz["eye"] == "n":
        o.append(f'<circle cx="{ex}" cy="{ey}" r="12" fill="{tint or RED}" opacity=".3"/><circle cx="{ex}" cy="{ey}" r="6" fill="{tint or RED}"/><circle cx="{ex - 1.5}" cy="{ey - 1.5}" r="2" fill="{tint or PAPER}"/>')
    elif pz["eye"] == "x":
        o.append(line([(ex - 5, ey - 5), (ex + 5, ey + 5)], 3, tint or PAPER) + line([(ex - 5, ey + 5), (ex + 5, ey - 5)], 3, tint or PAPER))
    else:
        o.append(f'<circle cx="{ex}" cy="{ey}" r="6" fill="none" stroke="{tint or RED}" stroke-width="2.5"/><circle cx="{ex}" cy="{ey}" r="1.8" fill="{tint or RED}"/>')
    m = pz["mand"]
    o.append(f'<path d="M-54 -42 Q-66 -46 -76 {-44 - 12 * m:.1f} M-54 -36 Q-66 -30 -76 {-34 + 10 * m:.1f}" fill="none" stroke="{rim}" stroke-width="4" stroke-linecap="round"/>')
    a1, a2 = ((-70, -94), (-36, -100)) if pz["ant"] == 0 else ((-62, -104), (-26, -96))
    o.append(f'<path d="M-40 -62 Q-52 -88 {P(*a1)} M-30 -64 Q-34 -86 {P(*a2)}" fill="none" stroke="{rim}" stroke-width="2.6" stroke-linecap="round"/>')
    o.append(f'<circle cx="{a1[0]}" cy="{a1[1]}" r="3.4" fill="{tint or RED}"/><circle cx="{a2[0]}" cy="{a2[1]}" r="3.4" fill="{tint or RED}"/>')
    o.append(scythe(sc, 0, 0, tint, False))
    return f'<g transform="scale(1.3)"><g transform="rotate({pz["tilt"]} 50 0) scale({pz["sx"]} {pz["sy"]})">{"".join(o)}</g></g>'


def dev_fn(n, tint=None):
    p = dev_pose(DEV["hit"], "#ffffff") if n == "hitW" else dev_pose(DEV[n], tint)
    return f'<g transform="scale(1.25)">{p}</g>'


def bug_fn(n, tint=None):
    return bug_pose(BUGP[n if n != "hitW" else "hit"], tint)


def pose_stack(prefix, fn, names, flips):
    out = []
    for n in names:
        if n in flips:
            sp = flips[n]
            out.append(f'<g id="{prefix}_{n}" class="h"><g class="fA{sp}">{fn(n + "A")}</g><g class="fB{sp}" opacity="0">{fn(n + "B")}</g></g>')
        else:
            out.append(f'<g id="{prefix}_{n}" class="h">{fn(n, "#ffffff" if n.endswith("W") else None)}</g>')
    return "".join(out)


dev_stack = pose_stack("d", dev_fn, ["idle", "run", "windup", "slashF", "hit", "hitW", "jump", "slashD", "slashB", "charge", "finish", "victory"], {"idle": "8", "run": "2"})
bug_stack = pose_stack("b", bug_fn, ["idle", "run", "prep", "strike", "stagger", "hit", "hitW"], {"idle": "8", "run": "2"})
after = "".join(f'<g id="after{i}" class="h"><g transform="scale(1.25)">{dev_pose(DEV["finish"], "#7a1c22")}</g></g>' for i in range(3))
stag = BUGP["stagger"]
halves = (f'<g id="half_a" class="h"><g clip-path="url(#cutA)"><g transform="scale(-1 1)">{bug_pose(stag)}</g></g></g>'
          f'<g id="half_b" class="h"><g clip-path="url(#cutB)"><g transform="scale(-1 1)">{bug_pose(stag)}</g></g></g>')
bug_cut = ('<clipPath id="cutA"><polygon points="-220,-260 198,-260 -162,100 -220,100"/></clipPath>'
           '<clipPath id="cutB"><polygon points="198,-260 220,-260 220,100 -162,100"/></clipPath>')


# ------------------------------------------------------------------ world backdrop: moon, pylons, skyline, water
def pylon(x, h, w):
    c = "#1c1c24"
    o = [f'<path d="M{x - w} {GROUND}L{x - 4} {GROUND - h}M{x + w} {GROUND}L{x + 4} {GROUND - h}" stroke="{c}" stroke-width="3" fill="none"/>']
    n = int(h / 22)
    for i in range(n):
        y0, y1 = GROUND - i * 22, GROUND - (i + 1) * 22
        w0, w1 = w - (w - 4) * i / n, w - (w - 4) * (i + 1) / n
        o.append(f'<path d="M{x - w0:.1f} {y0}L{x + w1:.1f} {y1}M{x + w0:.1f} {y0}L{x - w1:.1f} {y1}" stroke="{c}" stroke-width="1.6" fill="none"/>')
    for k, f in ((0, 30), (1, 20)):
        o.append(f'<path d="M{x - f} {GROUND - h + 12 + k * 22}H{x + f}" stroke="{c}" stroke-width="3"/>')
    return "".join(o)


def backdrop():
    o = [f'<rect x="-60" y="20" width="1320" height="400" fill="#0b0b10"/>',
         '<g mask="url(#htm)"><rect x="-60" y="40" width="1320" height="300" fill="url(#ht)" opacity=".3"/></g>']
    for _ in range(60):
        o.append(f'<rect class="{random.choice(("bk1", "bk2", "bk3", "", ""))}" x="{random.randint(-40, 1240)}" y="{random.randint(46, 200)}" width="2" height="2" fill="{PAPER}" opacity="{random.choice((.2, .35, .55))}"/>')
    o.append(f'<circle cx="610" cy="232" r="214" fill="none" stroke="{PAPER}" stroke-opacity=".07"/><circle cx="610" cy="232" r="196" fill="none" stroke="{PAPER}" stroke-opacity=".12"/>')
    o.append(f'<circle cx="610" cy="232" r="178" fill="{PAPER}"/>')
    for cx, cy, r in ((560, 190, 30), (655, 262, 22), (610, 130, 14), (700, 170, 11), (545, 280, 16)):
        o.append(f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="#cfcabd" opacity=".55"/>')
    o.append(f'<circle cx="610" cy="232" r="178" fill="url(#ht2)" opacity=".18"/>')
    o.append(pylon(330, 190, 34) + pylon(900, 220, 38))
    o.append('<path d="M330 150Q480 190 630 120M630 120Q770 80 900 120M350 172Q500 205 640 142M640 142Q780 105 920 140" stroke="#1c1c24" stroke-width="1.5" fill="none"/>')
    x = -20
    while x < 1240:
        w, h = random.choice((34, 44, 56, 70)), random.randint(26, 92)
        o.append(f'<rect x="{x}" y="{GROUND - h}" width="{w}" height="{h}" fill="#050507"/>')
        for r in range(6, h - 6, 11):
            for cx in range(x + 6, x + w - 6, 9):
                if random.random() < .15:
                    col = RED if random.random() < .16 else PAPER
                    o.append(f'<rect class="{random.choice(("bk1", "bk2", "bk3", ""))}" x="{cx}" y="{GROUND - h + r}" width="3" height="2" fill="{col}" opacity=".55"/>')
        x += w + random.randint(0, 14)
    o.append(f'<rect x="-60" y="{GROUND}" width="1320" height="80" fill="#060609"/>')
    for k in range(10):
        w = 300 - k * 22 + random.randint(-10, 10)
        o.append(f'<rect class="{"bk2" if k % 3 else "bk1"}" x="{610 - w / 2:.0f}" y="{GROUND + 4 + k * 6.2:.1f}" width="{w}" height="{1.8 - k * .1:.1f}" fill="{PAPER}" opacity="{.55 - k * .04:.2f}"/>')
    o.append(f'<path d="M-60 {GROUND}H1260" stroke="{PAPER}" stroke-opacity=".55" stroke-width="1.5"/>')
    for lab, xx in (("LATENCY", 300), ("STATE", 500), ("CONCURRENCY", 720), ("FAILURE", 920)):
        o.append(f'<text x="{xx}" y="392" text-anchor="middle" font-size="9" letter-spacing="3" fill="{DIM}">{lab}</text>')
    return "".join(o)


def rain(n, ln, op, cls):
    return f'<g class="{cls}" stroke="{PAPER}" stroke-opacity="{op}" stroke-width="1">' + "".join(
        f'<path d="M{random.randint(150, 1080)} {random.randint(0, 460) - 60}l-{ln * .35:.1f} {ln}"/>' for _ in range(n)) + "</g>"


def ripple_el(id):
    return f'<g id="{id}" class="h"><ellipse rx="34" ry="7" fill="none" stroke="{PAPER}" stroke-width="1.6"/><ellipse rx="20" ry="4" fill="none" stroke="{PAPER}" stroke-opacity=".6"/></g>'


def fx_lines(n, r1, r2, w, cols):
    return "".join(f'<path d="M{math.cos(i * 2 * math.pi / n + .2) * r1:.1f} {math.sin(i * 2 * math.pi / n + .2) * r1:.1f}L{math.cos(i * 2 * math.pi / n + .2) * r2:.1f} {math.sin(i * 2 * math.pi / n + .2) * r2:.1f}" stroke="{cols[i % len(cols)]}" stroke-width="{w}" stroke-linecap="round"/>' for i in range(n))


def burst_el(id, n, r1, r2, w, cols):
    return f'<g id="{id}" class="h">{fx_lines(n, r1, r2, w, cols)}</g>'


def arc_el(id, d, c1, c2, w1=14, w2=5):
    return (f'<g id="{id}" class="ag h"><path pathLength="1" d="{d}" fill="none" stroke="{c1}" stroke-width="{w1}" stroke-linecap="round" opacity=".55"/>'
            f'<path pathLength="1" d="{d}" fill="none" stroke="{c2}" stroke-width="{w2}" stroke-linecap="round"/></g>')


def label(id, inner):
    return f'<g id="{id}" class="h">{inner}</g>'


# new ripples at feet on every impact / landing
for i, (x, t) in enumerate(((330, 5.65), (860, 6.45), (930, 8.45), (440, 4.46), (610, 6.86), (606, 7.26), (598, 7.66), (580, 9.4), (546, 3.05), (814, 3.05))):
    burst(f"rp{i}", x, GROUND + 8, t, .8, .3, 3.2)
ripples = "".join(ripple_el(f"rp{i}") for i in range(10))

fx = "".join([
    burst_el("sp_clash", 14, 14, 70, 3, (PAPER, RED)), burst_el("sp_dev", 10, 10, 46, 3, (PAPER, RED)),
    burst_el("sp_h1", 8, 8, 34, 3, (PAPER, RED)), burst_el("sp_h2", 8, 8, 34, 3, (PAPER, RED)), burst_el("sp_h3", 10, 10, 46, 3, (PAPER, RED)),
    burst_el("sp_fin", 16, 18, 100, 4, (PAPER, RED, "#fff")),
    f'<g id="ring_clash" class="h"><circle r="46" fill="none" stroke="{PAPER}" stroke-width="2.5"/></g>',
    "".join(f'<g id="dust{i}" class="h">{fx_lines(5, 8, 22, 4, (DIM,))}</g>' for i in (1, 2, 3)),
    arc_el("arc_bug", "M380 196 Q462 226 500 312", RED, PAPER), arc_el("arc_1", "M712 238 Q640 232 546 288", RED, PAPER),
    arc_el("arc_2", "M700 196 Q650 252 556 318", RED, PAPER), arc_el("arc_3", "M546 320 Q634 292 714 212", RED, PAPER),
    arc_el("arc_fin", "M690 168 L470 388", RED, "#ffffff", 24, 8),
])
aura = (f'<g id="aura" class="h"><circle r="120" fill="url(#aura_g)"/></g><g id="energy" class="h">{fx_lines(10, 44, 78, 2.5, (RED, PAPER))}</g>')
streak = ('<g id="streak" class="h">' + "".join(f'<path d="M0 {y}H-{ln}" stroke="{c}" stroke-width="{w}" stroke-linecap="round" opacity=".85"/>'
          for y, ln, c, w in ((236, 520, PAPER, 2), (260, 470, RED, 4), (284, 560, PAPER, 1.5), (308, 430, RED, 3), (248, 380, PAPER, 1.5))) + '</g>')
streak_bug = ('<g id="streak_bug" class="h">' + "".join(f'<path d="M0 {y}H-{ln}" stroke="{c}" stroke-width="{w}" stroke-linecap="round" opacity=".85"/>'
              for y, ln, c, w in ((240, 300, PAPER, 2), (270, 320, RED, 3), (300, 280, PAPER, 1.5))) + '</g>')
pix = "".join(f'<rect id="pp{i}" class="h" x="-4" y="-4" width="{random.choice((4, 6, 8))}" height="{random.choice((4, 6, 8))}" fill="{random.choice((PAPER, PAPER, RED, STEEL, INK))}" stroke="{PAPER}" stroke-width=".6" shape-rendering="crispEdges"/>' for i in range(26))
glitch = (f'<g class="gl"><rect x="62" y="-62" width="18" height="3" fill="{RED}"/><rect x="-24" y="-30" width="22" height="3" fill="{PAPER}"/>'
          f'<rect x="-70" y="-112" width="14" height="3" fill="{RED}"/><rect x="40" y="-96" width="8" height="8" fill="{PAPER}"/></g>')

# ------------------------------------------------------------------ captions, meters, cinematic layers
def cap(id, txt, x, y, t0, dur, col):
    pop(id, x, y, t0, dur, 12, 1.1)
    return label(id, T(txt, 12, col, stroke=INK, sw=4, ls=3, weight=700))


caps = "".join([cap("cap_null", "NULL DEREF", 560, 252, 4.3, 1.1, PAPER), cap("cap_c1", "CACHE HIT", 590, 266, 6.86, .5, PAPER),
                cap("cap_c2", "BATCH WRITE", 600, 266, 7.26, .5, PAPER), cap("cap_c3", "RETRY x3", 610, 266, 7.66, .6, PAPER),
                cap("cap_race", "RACE CONDITION", 700, 186, 3.05, 1.0, PAPER)])
XP = [("LATENCY", 368, [(3.05, .25), (3.4, .6), (9.4, .6), (9.8, 1)], .25), ("STATE", 388, [(6.86, .2), (7.3, .4), (7.7, .6), (9.4, .6), (9.8, 1)], .2),
      ("CONCURRENCY", 408, [(6.0, .15), (6.5, .5), (9.4, .5), (9.8, 1)], .15), ("FAILURE", 428, [(4.46, .3), (4.8, .55), (9.4, .55), (9.8, 1)], .3)]
meters = ""
for i, (nm, yy, pts, base) in enumerate(XP):
    st = [(0, {"sx": base})] + [(t, {"sx": v}) for t, v in pts] + [(14.55, {"sx": 1}), (14.6, {"sx": base})]
    ch(f"xp{i}", st, origin=(170, yy + 4))
    meters += (f'<text x="40" y="{yy + 8}" font-size="10" letter-spacing="2.5" fill="{STEEL}">{nm}</text><rect x="170" y="{yy + 2}" width="230" height="4" fill="#1b1b22"/>'
               f'<rect id="xp{i}" x="170" y="{yy + 2}" width="230" height="4" fill="{PAPER}"/>')
ch("lvl", [(0, {"o": 0}), (10.5 - EPS, {"o": 0}), (10.5, {"o": 1}), (10.7, {"o": .2}), (10.9, {"o": 1}), (14.55, {"o": 1}), (14.6, {"o": 0})])
ch("lb_t", [(0, {"y": 0, "o": 1}), (1.5, {"y": 0}), (1.9, {"y": -34}), (2.95, {"y": -34}), (2.95 + EPS, {"o": 1}), (8.45 - EPS, {"y": -34}), (8.45, {"y": 0, "ease": "out"}), (8.7, {"y": 0}),
              (10.4, {"y": 0}), (10.8, {"y": -34}), (14.55, {"y": -34}), (14.6, {"y": 0, "o": 1})])
ch("lb_b", [(0, {"y": 0, "o": 1}), (1.5, {"y": 0}), (1.9, {"y": 34}), (8.45 - EPS, {"y": 34}), (8.45, {"y": 0, "ease": "out"}), (10.4, {"y": 0}), (10.8, {"y": 34}), (14.55, {"y": 34}), (14.6, {"y": 0})])
ch("imp_c", [(0, {"o": 0}), (3.05 - EPS, {"o": 0}), (3.05, {"o": 1}), (3.1, {"o": 1}), (3.1 + EPS, {"o": 0})])
ch("imp_f", [(0, {"o": 0}), (9.4 - EPS, {"o": 0}), (9.4, {"o": 1}), (9.46, {"o": 1}), (9.46 + EPS, {"o": 0})])
ch("imp_w", [(0, {"o": 0}), (9.46, {"o": 0}), (9.46 + EPS, {"o": 1}), (9.52, {"o": 1}), (9.52 + EPS, {"o": 0})])
ch("typecover", [(8.6 - EPS, {"sx": 1}), (8.75, {"sx": 1, "ease": "steps"}), (9.2, {"sx": 0})], origin=(62, 0))


def impact(id, cx, cy, bg, fg, n=70):
    ls = "".join(f'<path d="M{cx + math.cos(a) * r1:.0f} {cy + math.sin(a) * r1:.0f}L{cx + math.cos(a) * (r1 + 200 + random.random() * 500):.0f} {cy + math.sin(a) * (r1 + 200 + random.random() * 500):.0f}" stroke="{fg}" stroke-width="{.8 + random.random() * 3.6:.1f}"/>'
                 for a, r1 in ((random.random() * 6.283, 40 + random.random() * 90) for _ in range(n)))
    return f'<g id="{id}" class="h"><rect x="440" y="116" width="816" height="354" fill="{bg}"/>{ls}</g>'


impacts = impact("imp_c", 948, 288, INK, PAPER, 56) + impact("imp_f", 828, 358, INK, PAPER, 90) + impact("imp_w", 828, 358, PAPER, INK, 90)


def tx(content, size, fill, anchor="middle", ls=3, sw=7, weight=900, skew=-8):
    return f'<g transform="skewX({skew})">{T(content, size, fill, anchor, weight, ls, INK, sw)}</g>'


texts = "".join([
    label("round", tx("INCIDENT #4041", 40, PAPER, ls=7)), label("fight", tx("DEBUG.", 96, PAPER, ls=6, sw=10)),
    label("t_clash", tx("CLANG", 46, PAPER, ls=4)), label("t_d22", tx("-22", 36, RED, sw=7)),
    label("t_d12", tx("-12", 26, PAPER, sw=6)), label("t_d14", tx("-14", 28, PAPER, sw=6)), label("t_d16", tx("-16", 32, PAPER, sw=6)),
    label("t_d58", tx("-58", 50, RED, sw=8)), label("t_crit", tx("SIGKILL", 16, PAPER, ls=7, sw=5)),
    label("alert", tx("!", 54, RED, sw=7)),
    label("hotfix", f'<rect x="-150" y="-24" width="300" height="48" fill="{INK}" stroke="{PAPER}" stroke-width="1.5"/>'
          f'<text x="-134" y="7" font-size="20" font-weight="700" letter-spacing="1" fill="{PAPER}">$ kill -9 4041</text>'
          f'<rect id="typecover" x="-134" y="-13" width="196" height="28" fill="{INK}"/>'),
    f'<g id="c1" class="h" transform="translate(215 118)">{tx("1 HIT", 30, PAPER, "start", sw=6)}</g>',
    f'<g id="c2" class="h" transform="translate(215 118)">{tx("2 HIT", 36, PAPER, "start", sw=6)}</g>',
    f'<g id="c3" class="h" transform="translate(215 118)">{tx("3 HIT", 44, RED, "start", sw=7)}</g>',
    label("ko", tx("EXIT 0", 104, PAPER, ls=8, sw=12) + f'<rect x="-210" y="52" width="420" height="5" fill="{RED}"/>'),
    label("panel", f'<rect x="-190" y="-34" width="380" height="68" fill="{INK}" stroke="{PAPER}" stroke-width="1.5"/>'
          + T("BUG_4041 / SEV-2 RESOLVED", 11, STEEL, ls=4, weight=700, y=-12) + T("SYSTEMS ONLINE", 26, PAPER, ls=5, y=14)),
]) + caps

hud = f"""
<defs><clipPath id="cL"><polygon points="460,80 800,80 794,90 454,90"/></clipPath><clipPath id="cR"><polygon points="896,80 1236,80 1242,90 902,90"/></clipPath></defs>
<text x="460" y="72" font-size="14" font-weight="800" letter-spacing="4" fill="{PAPER}">PIYUSH RAJ</text>
<g clip-path="url(#cL)"><rect x="454" y="80" width="346" height="10" fill="#1b1b22"/><rect id="hpDg" x="454" y="80" width="346" height="10" fill="{DIM}"/><rect id="hpD" x="454" y="80" width="346" height="10" fill="{PAPER}"/></g>
<text x="460" y="108" font-size="9" letter-spacing="2" fill="{STEEL}">p99 &lt; 40ms  /  UPTIME 99.9%</text>
<text x="1236" y="72" text-anchor="end" font-size="14" font-weight="800" letter-spacing="4" fill="{PAPER}">BUG_4041</text>
<g clip-path="url(#cR)"><rect x="896" y="80" width="346" height="10" fill="#1b1b22"/><rect id="hpBg" x="896" y="80" width="346" height="10" fill="{DIM}"/><rect id="hpB" x="896" y="80" width="346" height="10" fill="{RED}"/></g>
<text x="1236" y="108" text-anchor="end" font-size="9" letter-spacing="2" fill="{RED}">SEV-2  /  NOT REPRODUCIBLE</text>
<text x="848" y="76" text-anchor="middle" font-size="10" letter-spacing="4" fill="{STEEL}">SEV-2</text>
<circle cx="834" cy="88" r="3.5" fill="none" stroke="{STEEL}"/><circle id="pip" class="h" cx="834" cy="88" r="3.5" fill="{PAPER}"/><circle cx="862" cy="88" r="3.5" fill="none" stroke="{STEEL}"/>
"""

panel = f"""
<rect x="24" y="52" width="400" height="418" fill="none" stroke="{PAPER}" stroke-opacity=".4"/>
<text x="40" y="76" font-size="10" letter-spacing="3" fill="{DIM}">ROLE: BACKEND ENGINEER</text>
<text x="36" y="148" font-size="74" font-weight="900" letter-spacing="-3" fill="{PAPER}">PIYUSH</text>
<text x="36" y="214" font-size="74" font-weight="900" letter-spacing="-3" fill="none" stroke="{PAPER}" stroke-width="1.6">RAJ</text>
<g transform="translate(366 108) rotate(-5)"><rect x="-30" y="-30" width="60" height="60" fill="{RED}" opacity=".92"/><rect x="-25" y="-25" width="50" height="50" fill="none" stroke="{INK}" stroke-width="2"/>
<text text-anchor="middle" y="12" font-size="34" font-weight="900" fill="{INK}">PR</text></g>
<rect x="40" y="234" width="6" height="6" fill="{RED}"/><text x="54" y="241" font-size="11" font-weight="700" letter-spacing="2.5" fill="{PAPER}">BACKEND / REAL-TIME / SYSTEMS</text>
<text font-size="14" fill="{STEEL}"><tspan x="40" y="278">Building systems where latency,</tspan><tspan x="40" y="299">state, concurrency and failure</tspan><tspan x="40" y="320">are part of the design.</tspan></text>
<path d="M40 340H408" stroke="{PAPER}" stroke-opacity=".25"/>
<text x="40" y="358" font-size="9" letter-spacing="3" fill="{DIM}">SKILL XP</text>
<g id="lvl" class="h"><text x="408" y="358" text-anchor="end" font-size="10" font-weight="800" letter-spacing="3" fill="{RED}">LEVEL UP</text></g>
{meters}
<rect x="40" y="446" width="176" height="24" fill="{PAPER}"/><circle cx="56" cy="458" r="4.5" fill="{RED}"><animate attributeName="opacity" values="1;.2;1" dur="1.6s" repeatCount="indefinite"/></circle>
<text x="70" y="463" font-size="11" font-weight="800" letter-spacing="2" fill="{INK}">OPEN TO ROLES</text>
<text x="408" y="463" text-anchor="end" font-size="9" letter-spacing="2" fill="{DIM}">BACKEND / PLATFORM / SWE</text>
"""

BASE_CSS = f"""
.h{{opacity:0}}
#d_idle,#b_idle,#bug_root{{opacity:1}}
#dev_x{{transform:translate(250px,{GROUND}px)}} #bug_x{{transform:translate(860px,{GROUND}px)}}
.ag{{stroke-dasharray:1;stroke-dashoffset:1}}
@keyframes fA8{{0%,49.99%{{opacity:1}}50%,100%{{opacity:0}}}} @keyframes fB8{{0%,49.99%{{opacity:0}}50%,100%{{opacity:1}}}}
@keyframes fA2{{0%,49.99%{{opacity:1}}50%,100%{{opacity:0}}}} @keyframes fB2{{0%,49.99%{{opacity:0}}50%,100%{{opacity:1}}}}
.fA8{{animation:fA8 .8s linear infinite}} .fB8{{animation:fB8 .8s linear infinite}}
.fA2{{animation:fA2 .22s linear infinite}} .fB2{{animation:fB2 .22s linear infinite}}
@keyframes gl{{0%,9%{{opacity:0}}10%,13%{{opacity:1}}14%,45%{{opacity:0}}46%,49%{{opacity:1}}50%,81%{{opacity:0}}82%,85%{{opacity:1}}86%,100%{{opacity:0}}}}
.gl{{opacity:0;animation:gl 1.6s linear infinite}}
@keyframes bk{{0%,60%{{opacity:.85}}61%,100%{{opacity:.1}}}}
.bk1{{animation:bk 1.7s linear infinite}} .bk2{{animation:bk 2.3s linear -.8s infinite}} .bk3{{animation:bk 3.1s linear -1.4s infinite}}
@keyframes rn{{from{{transform:translate(0,-60px)}}to{{transform:translate(-21px,60px)}}}}
.rn1{{animation:rn .5s linear infinite}} .rn2{{animation:rn .72s linear -.3s infinite}}
@media (prefers-reduced-motion:reduce){{*{{animation:none!important}}}}
"""

svg = f"""<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" viewBox="0 0 1280 520" width="1280" height="520" role="img" aria-labelledby="ttl desc" font-family="{FONT}">
<title id="ttl">Piyush Raj versus BUG_4041</title>
<desc id="desc">A looping ink-and-moonlight duel beside Piyush Raj's profile card. A suited swordsman wearing Piyush's face clashes with a glitch bug in the rain, takes one hit, leaps over it, lands a three-hit combo and ends it with kill -9. Exit code 0. Open to backend, platform and software engineering roles.</desc>
<style>{BASE_CSS}{css_all()}</style>
<defs>
<clipPath id="hc" clipPathUnits="objectBoundingBox"><circle cx=".5" cy=".5" r=".5"/></clipPath>
<g id="faceg"><image href="data:image/png;base64,{FACE}" xlink:href="data:image/png;base64,{FACE}" x="-1" y="-1" width="2" height="2" clip-path="url(#hc)"/></g>
<radialGradient id="aura_g"><stop offset="0" stop-color="{RED}" stop-opacity=".55"/><stop offset="1" stop-color="{RED}" stop-opacity="0"/></radialGradient>
<pattern id="ht" width="6" height="6" patternUnits="userSpaceOnUse"><circle cx="3" cy="3" r="1.1" fill="#fff"/></pattern>
<pattern id="ht2" width="5" height="5" patternUnits="userSpaceOnUse" patternTransform="rotate(30)"><circle cx="2.5" cy="2.5" r="1.2" fill="#000"/></pattern>
<linearGradient id="htg" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#fff"/><stop offset="1" stop-color="#000"/></linearGradient>
<mask id="htm"><rect x="-60" y="40" width="1320" height="300" fill="url(#htg)"/></mask>
<pattern id="scan" width="4" height="4" patternUnits="userSpaceOnUse"><rect width="4" height="1" fill="#fff" opacity=".03"/></pattern>
<clipPath id="stage"><rect x="440" y="116" width="816" height="354"/></clipPath>
{bug_cut}
</defs>
<rect width="1280" height="520" fill="{INK}"/>
<text x="24" y="31" font-size="11" letter-spacing="2.5" fill="{PAPER}">piyush@raj:~$ ./debug --incident 4041</text><text x="1256" y="31" text-anchor="end" font-size="11" letter-spacing="3" fill="{PAPER}">BUILD 2026.11 / PASSING</text>
<path d="M24 40H1256" stroke="{PAPER}" stroke-opacity=".6"/>
{panel}
<rect x="440" y="52" width="816" height="418" fill="none" stroke="{PAPER}" stroke-opacity=".4"/>
<g clip-path="url(#stage)"><g transform="translate(248 70)">
<g id="cam">
{backdrop()}
<rect id="dim" class="h" x="-60" y="20" width="1320" height="400" fill="#000"/>
{aura}
<g id="bug_x"><g id="bug_root">{bug_stack}{glitch}</g></g>
{halves}{after}{streak}{streak_bug}
<g id="dev_x"><g id="dev_y">{dev_stack}</g></g>
{ripples}{fx}{pix}{rain(70, 16, .3, "rn1")}{rain(40, 24, .18, "rn2")}
</g>
{texts}
</g>
{impacts}
<rect id="lb_t" class="h" x="440" y="116" width="816" height="34" fill="{INK}"/><rect id="lb_b" class="h" x="440" y="436" width="816" height="34" fill="{INK}"/>
</g>
{hud}
<rect id="flash" class="h" x="440" y="116" width="816" height="354" fill="#fff"/>
<rect id="fade" class="h" x="440" y="52" width="816" height="418" fill="#000"/>
<rect width="1280" height="520" fill="url(#scan)"/>
<path d="M24 480H1256" stroke="{PAPER}" stroke-opacity=".6"/>
<text x="24" y="500" font-size="10" letter-spacing="2" fill="{DIM}">BUILD / MEASURE / BREAK / REBUILD</text>
<text x="1256" y="500" text-anchor="end" font-size="10" letter-spacing="2" fill="{DIM}">CSE ’27 / CHANDIGARH UNIVERSITY</text>
<rect x="8" y="8" width="1264" height="504" fill="none" stroke="{PAPER}" stroke-width="2"/>
</svg>"""

for cid in CH:
    assert f'id="{cid}"' in svg, f"channel {cid} has no element"
open("../assets/bug-vs-dev.svg", "w").write(svg)
print(len(svg), "bytes,", len(CH), "channels")
