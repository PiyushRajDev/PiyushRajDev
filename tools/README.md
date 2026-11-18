# Profile fight animation

`duel.py` is the source for `../assets/bug-vs-dev.svg`. The SVG is generated from a single synchronized 15-second playback loop and uses SVG SMIL only, so the profile image has no JavaScript runtime or external asset dependency.

## Build and validate

From the repository root:

```bash
python tools/duel.py
python tools/duel.py --check
```

The generator uses only Python's standard library. It validates XML structure, unique IDs, local SVG references, and every animation channel's `values` / `keyTimes` alignment before writing.

## Preview and scrub

```bash
python -m http.server 8000
```

Open `http://localhost:8000/tools/preview.html`. The preview page has play/pause, speed controls, a scrubber, and markers for the major fight beats.

## Choreography

| Time | Beat |
|---|---|
| 0–1s | Boot and character entrance |
| 1–3s | Boss reveal, fight banner, parry |
| 3–4s | Jump dodge |
| 4–6s | Three-hit combo and damage feedback |
| 6–7s | Boss counterattack |
| 7–9s | Charge-up |
| 9–11s | Hotfix finisher |
| 11–12s | Split, K.O. and debris |
| 12–14s | Victory state |
| 14–15s | Reset and loop |
