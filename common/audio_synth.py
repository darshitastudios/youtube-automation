"""Synthesized audio: music bed, ticks, dings, whooshes. 100% free/original."""
import wave
import numpy as np

SR = 44100


def _env(n, attack=0.005, release=0.05):
    a = max(1, int(attack * SR))
    r = max(1, int(release * SR))
    e = np.ones(n, dtype=np.float32)
    e[:a] = np.linspace(0, 1, a)
    e[-r:] = np.linspace(1, 0, r)
    return e


def tone(freq, dur, kind="sine", vol=0.3):
    n = int(dur * SR)
    t = np.arange(n) / SR
    if kind == "sine":
        w = np.sin(2 * np.pi * freq * t)
    elif kind == "tri":
        w = 2 * np.abs(2 * (t * freq % 1) - 1) - 1
    else:  # saw
        w = 2 * (t * freq % 1) - 1
    return (w * vol * _env(n, 0.01, min(0.12, dur / 3))).astype(np.float32)


def kick(dur=0.14, vol=0.55):
    n = int(dur * SR)
    t = np.arange(n) / SR
    f = 150 * np.exp(-t * 28) + 45
    w = np.sin(2 * np.pi * np.cumsum(f) / SR)
    return (w * vol * np.exp(-t * 22)).astype(np.float32)


def hat(dur=0.05, vol=0.10):
    n = int(dur * SR)
    w = np.random.uniform(-1, 1, n)
    w = np.diff(w, prepend=0)
    return (w * vol * _env(n, 0.001, 0.04)).astype(np.float32)


def tick(vol=0.35):
    """Clock tick for countdown."""
    n = int(0.08 * SR)
    out = np.zeros(n, dtype=np.float32)
    for f, d, v in [(2100, 0.045, vol), (3150, 0.03, vol * 0.5)]:
        seg = tone(f, d, "sine", v)
        out[: len(seg)] += seg
    return out


def ding(vol=0.5):
    """Correct-answer chime."""
    n = int(0.9 * SR)
    out = np.zeros(n, dtype=np.float32)
    for i, f in enumerate([880, 1108.7, 1318.5]):
        seg = tone(f, 0.8, "sine", vol * (0.6 - i * 0.12))
        s = int(i * 0.07 * SR)
        m = min(len(seg), n - s)
        out[s : s + m] += seg[:m]
    return out[:n]


def buzz(vol=0.4):
    """Time's-up buzz."""
    n = int(0.5 * SR)
    out = tone(196, 0.5, "saw", vol * 0.5) + tone(98, 0.5, "saw", vol * 0.35)
    return out[:n]


def whoosh(dur=0.35, vol=0.3):
    n = int(dur * SR)
    w = np.random.uniform(-1, 1, n).astype(np.float32)
    w = np.cumsum(w)  # crude lowpass
    w /= np.abs(w).max() + 1e-9
    rise = np.linspace(0, 1, n) ** 2
    fall = np.linspace(1, 0, n) ** 0.5
    return w * vol * rise * fall


def midi(m):
    return 440.0 * 2 ** ((m - 69) / 12)


def music_bed(dur, bpm=138, vol=0.5):
    """Tense upbeat loop: Am F C G arpeggio + kick/hats, game-show feel."""
    n = int(dur * SR)
    out = np.zeros(n, dtype=np.float32)
    beat = 60.0 / bpm
    chords = [[57, 60, 64], [53, 57, 60], [48, 52, 55], [55, 59, 62]]  # Am F C G
    bar = beat * 4
    pos = 0.0
    ci = 0
    while pos < dur:
        ch = chords[ci % len(chords)]
        for k in range(8):  # 8th-note arpeggio
            note = ch[k % 3] + (12 if k >= 6 else 0)
            seg = tone(midi(note), beat * 0.48, "tri", vol * 0.22)
            s = int((pos + k * beat / 2) * SR)
            if s + len(seg) <= n:
                out[s : s + len(seg)] += seg
        # bass on beat 1 and 3
        for b in (0, 2):
            seg = tone(midi(ch[0] - 12), beat * 0.9, "sine", vol * 0.5)
            s = int((pos + b * beat) * SR)
            if s + len(seg) <= n:
                out[s : s + len(seg)] += seg
        for b in range(4):
            s = int((pos + b * beat) * SR)
            seg = kick(vol=vol * 0.8)
            if s + len(seg) <= n:
                out[s : s + len(seg)] += seg
            seg = hat(vol=vol * 0.6)
            s2 = int((pos + b * beat + beat / 2) * SR)
            if s2 + len(seg) <= n:
                out[s2 : s2 + len(seg)] += seg
        pos += bar
        ci += 1
    return out


def save_wav(path, samples):
    samples = np.clip(samples, -1, 1)
    data = (samples * 32767).astype(np.int16)
    with wave.open(path, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(data.tobytes())
    return path
