# -*- coding: utf-8 -*-
"""合成心電図エンジン：方眼(ECGペーパー)＋P-QRS-Tモデル＋各種調律。
著作権セーフな模式波形を生成（実記録の複製ではない）。図は教育用の schematic。"""
import numpy as np
from figbase import (INK, GOLD, TEAL, RED, GRAY, LGRAY, BLUE, GREEN,
                     GRID_MINOR, GRID_MAJOR, T, arrow, clean)

# ---------- ECG graph paper ----------
def ecg_grid(ax, t0, t1, ymin, ymax, minor=True):
    """x=秒(大マス0.2s), y=mV(大マス0.5mV) の方眼。"""
    ax.set_xlim(t0, t1); ax.set_ylim(ymin, ymax)
    if minor:
        x = t0
        while x <= t1 + 1e-9:
            ax.axvline(x, color=GRID_MINOR, lw=0.5, zorder=0); x += 0.04
        y = np.floor(ymin/0.1)*0.1
        while y <= ymax + 1e-9:
            ax.axhline(y, color=GRID_MINOR, lw=0.5, zorder=0); y += 0.1
    x = np.ceil(t0/0.2)*0.2
    while x <= t1 + 1e-9:
        ax.axvline(x, color=GRID_MAJOR, lw=0.9, zorder=0.1); x += 0.2
    y = np.ceil(ymin/0.5)*0.5
    while y <= ymax + 1e-9:
        ax.axhline(y, color=GRID_MAJOR, lw=0.9, zorder=0.1); y += 0.5
    clean(ax)

def _g(t, c, a, w):
    return a*np.exp(-((t-c)**2)/(2.0*w*w))

def _plateau(t, t0, t1, level, edge=0.018):
    up = np.clip((t-t0)/edge, 0, 1); up = 0.5-0.5*np.cos(np.pi*up)
    dn = np.clip((t1-t)/edge, 0, 1); dn = 0.5-0.5*np.cos(np.pi*dn)
    w = np.minimum(up, dn); w[t < t0] = 0; w[t > t1] = 0
    return level*w

# ---------- beat spec ----------
def beat(r, **kw):
    d = dict(r=r, p=True, pr=0.16, p_amp=0.15, p_dur=0.11, p_center=None, p_inv=False,
             q=-0.05, r_amp=1.0, s=-0.20, qrs='normal', qrs_dur=0.09, qrs_gauss=None,
             st=0.0, t_amp=0.32, t_dur=0.17, t_center=0.34, t_inv=False,
             u=False, u_amp=0.06, u_center=0.50, spike=0.0, spike_at=-0.05)
    d.update(kw); return d

def _render_qrs(t, b):
    r = b['r']; v = np.zeros_like(t)
    if b['qrs_gauss'] is not None:
        for (off, amp, w) in b['qrs_gauss']:
            v += _g(t, r+off, amp, w)
        return v
    qd = b['qrs_dur']
    if b['qrs'] == 'normal':
        v += _g(t, r-0.028, b['q'], 0.008)
        v += _g(t, r,        b['r_amp'], 0.011)
        v += _g(t, r+0.030,  b['s'], 0.013)
    elif b['qrs'] in ('wide', 'pvc', 'vt'):
        # 幅広・単峰(やや2相)・不気味
        sign = 1 if b['r_amp'] >= 0 else -1
        v += _g(t, r-0.02, -0.10*sign, 0.020)
        v += _g(t, r+0.010, b['r_amp'], 0.030)
        v += _g(t, r+0.060, -0.35*sign, 0.028)
    elif b['qrs'] == 'delta':
        # δ波：緩やかな立ち上がり＋主QRS
        v += _g(t, r-0.045, 0.28, 0.028)   # slurred upstroke
        v += _g(t, r,        b['r_amp'], 0.016)
        v += _g(t, r+0.035, -0.18, 0.014)
    else:
        v += _g(t, r, b['r_amp'], 0.012)
    return v

def synth(beats, t0, t1, fs=500, base_fn=None):
    t = np.linspace(t0, t1, int((t1-t0)*fs)+1)
    v = np.zeros_like(t)
    if base_fn is not None:
        v += base_fn(t)
    for b in beats:
        r = b['r']
        if b['p']:
            pc = r + (b['p_center'] if b['p_center'] is not None else -b['pr'])
            amp = -abs(b['p_amp']) if b['p_inv'] else b['p_amp']
            v += _g(t, pc, amp, b['p_dur']/3.2)
        v += _render_qrs(t, b)
        # ST plateau
        j = r + 0.5*b['qrs_dur'] + 0.015
        t_on = r + b['t_center'] - b['t_dur']*0.9
        if b['st'] != 0.0 and t_on > j:
            v += _plateau(t, j, t_on, b['st'])
        # T wave
        tamp = -abs(b['t_amp']) if b['t_inv'] else b['t_amp']
        v += _g(t, r+b['t_center'], tamp + (b['st'] if b['st'] else 0.0)*0.0, b['t_dur']/2.4)
        # U wave
        if b['u']:
            v += _g(t, r+b['u_center'], b['u_amp'], 0.045)
        # pacing spike
        if b['spike'] != 0.0:
            st = r + b['spike_at']
            v += _g(t, st, b['spike'], 0.0016)
    return t, v

def draw(ax, t, v, color=INK, lw=2.0, ymin=-0.6, ymax=1.5, t0=None, t1=None, grid=True):
    if t0 is None: t0 = t[0]
    if t1 is None: t1 = t[-1]
    if grid: ecg_grid(ax, t0, t1, ymin, ymax)
    ax.plot(t, v, color=color, lw=lw, zorder=4, solid_capstyle="round",
            solid_joinstyle="round")
    return ax

# ---------- rhythm builders (return beats list) ----------
def _rr(rate): return 60.0/rate

def sinus(rate=72, t0=0.0, t1=4.0, first=0.35, **kw):
    rr = _rr(rate); beats = []; r = first
    while r < t1 - 0.1:
        beats.append(beat(r, **kw)); r += rr
    return beats

def af_base(amp=0.05):
    def f(t):
        y = np.zeros_like(t)
        rng = np.random.default_rng(7)
        for k in range(1, 9):
            y += (amp/k)*np.sin(2*np.pi*(4.5*k)*t + rng.uniform(0, 6.28))
        return y*np.exp(0)  # keep small
    return f

def flutter_base(rate_f=300, amp=0.14):
    """鋸歯状F波（負方向優位, 下壁誘導風）。"""
    def f(t):
        ph = (t*rate_f/60.0) % 1.0
        saw = -amp*(2*ph-1)                # ramp
        saw += -amp*0.35*np.exp(-((ph-0.02)**2)/(2*0.02**2))
        return saw
    return f

def vf_trace(t0, t1, fs=500, seed=3):
    t = np.linspace(t0, t1, int((t1-t0)*fs)+1)
    rng = np.random.default_rng(seed)
    v = np.zeros_like(t)
    for f, a in [(4.2,0.55),(6.8,0.4),(9.3,0.32),(13.1,0.22),(18.0,0.14)]:
        v += a*np.sin(2*np.pi*f*t + rng.uniform(0,6.28))
    v *= (0.8+0.3*np.sin(2*np.pi*0.8*t))
    v += rng.normal(0, 0.05, size=t.shape)
    return t, v

def asystole_trace(t0, t1, fs=500, seed=5, wander=0.03):
    t = np.linspace(t0, t1, int((t1-t0)*fs)+1)
    rng = np.random.default_rng(seed)
    v = wander*np.sin(2*np.pi*0.25*t) + rng.normal(0, 0.006, size=t.shape)
    return t, v
