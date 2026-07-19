# -*- coding: utf-8 -*-
"""Shared figure-composition helpers for the defibrillator deck. Per-chapter figure
modules do:  import figlib as F ;  from fighelp import *
Then define one function per figure code f<CC><SS> (e.g. f0402) that builds a fig
with canvas()/rbox()/txt()/ecg_in()/... and ends with F.save(fig, "f0402")."""
import numpy as np
from matplotlib.patches import FancyBboxPatch, Arc, Circle, Polygon, Rectangle, Wedge
import figlib as F

# ---------------------------------------------------------------- text/box --
def txt(ax, x, y, s, color=F.INK, fs=14, bold=False, ha="center", va="center", zorder=6):
    ax.text(x, y, s, color=color, fontsize=fs, fontweight="bold" if bold else "normal",
            ha=ha, va=va, zorder=zorder)

def canvas(w=8.6, h=5.0, W=10, H=6):
    """Standard figure canvas. Data coords default to 10 x 6 (W x H). Use ~9:5-ish
    aspect for slide figures; the deck fits the PNG into a 29.8 x 12.7 cm box."""
    fig, ax = F.newfig(w, h)
    F.clean(ax)
    ax.set_xlim(0, W); ax.set_ylim(0, H)
    return fig, ax

def rbox(ax, x, y, w, h, fc, ec, txt_lines=None, tc=F.INK, fs=13, title=None, title_color=None,
         title_fs=14, lw=1.4, round_=0.10, align="center"):
    """Rounded box with optional bold title + a stack of text lines. Each txt_line may be
    a string or a (string, color) tuple. Box sits at zorder=1 so insets drawn AFTER show on top."""
    p = FancyBboxPatch((x, y), w, h, boxstyle=f"round,pad=0.01,rounding_size={round_}",
                        fc=fc, ec=ec, lw=lw, zorder=1)
    ax.add_patch(p)
    cy = y + h - 0.32
    if title:
        n_lines = title.count("\n") + 1
        ax.text(x + w/2, cy, title, color=title_color or ec, fontsize=title_fs, fontweight="bold",
                ha="center", va="top", zorder=4, linespacing=1.3)
        cy -= 0.40 * n_lines + 0.10
    if txt_lines:
        for ln in txt_lines:
            col = tc
            if isinstance(ln, tuple):
                ln, col = ln
            ax.text(x + (w/2 if align == "center" else 0.18), cy, ln, color=col, fontsize=fs,
                    ha=align, va="top", zorder=4)
            cy -= 0.34
    return p

def table(ax, x, y, w, h, col_labels, rows, col_w=None, header_fc=F.TEAL, header_tc=F.WHITE,
          fs=12, header_fs=12.5, row_fc=("white", "#F5F7F9"), lw=1.0, ec=F.LGRAY):
    """Simple grid table. rows = list of rows; each row = list of cells; a cell is a
    string or (string, color) tuple. First column is left-aligned, rest centered."""
    ncol = len(col_labels); nrow = len(rows)
    if col_w is None:
        col_w = [w / ncol] * ncol
    xs = [x + sum(col_w[:i]) for i in range(ncol)]
    rh = h / (nrow + 1)
    # header
    for c, lab in enumerate(col_labels):
        ax.add_patch(Rectangle((xs[c], y + h - rh), col_w[c], rh, fc=header_fc, ec=ec, lw=lw, zorder=2))
        ax.text(xs[c] + col_w[c] / 2, y + h - rh / 2, lab, ha="center", va="center",
                color=header_tc, fontsize=header_fs, fontweight="bold", zorder=3)
    # body
    for r, row in enumerate(rows):
        yy = y + h - rh * (r + 2)
        for c, cell in enumerate(row):
            ax.add_patch(Rectangle((xs[c], yy), col_w[c], rh, fc=row_fc[r % len(row_fc)], ec=ec, lw=lw, zorder=2))
            s, col = (cell if isinstance(cell, tuple) else (cell, F.INK))
            ha = "left" if c == 0 else "center"
            tx = xs[c] + (0.12 if c == 0 else col_w[c] / 2)
            ax.text(tx, yy + rh / 2, s, ha=ha, va="center", color=col, fontsize=fs,
                    fontweight="bold" if c == 0 else "normal", zorder=3)
    return xs, rh

# ---- ECG / rhythm drawing wrappers (clinically load-bearing; keep correct) ----
def ecg_in(ax, x0, x1, ymid, yscale, beats=4, narrow=True, twave=0.25,
           color=F.INK, lw=2.2, zorder=4, mark_r=False, mark_t=False, mark_color=F.TEAL):
    """Draw a sinus ECG train into window [x0,x1] centered at ymid, half-height yscale.
    mark_r places SYNC markers on R waves; mark_t places red markers on T-wave peaks
    (the vulnerable period). Returns the list of on-canvas R-wave x positions."""
    X, Y, rpos = F.ecg_train(beats=beats, narrow=narrow, twave=twave)
    span = X.max() - X.min()
    def mapx(v): return x0 + (v - X.min()) / span * (x1 - x0)
    ax.plot(mapx(X), ymid + Y * yscale, color=color, lw=lw, zorder=zorder,
            solid_joinstyle="round", solid_capstyle="round")
    rx = [mapx(r) for r in rpos]
    if mark_r:
        for xr in rx:
            F.sync_marker(ax, xr, ymid + yscale * 1.30, ymid + yscale * 1.05, color=mark_color)
    if mark_t:
        for tp in F.t_peak_positions(beats):
            F.sync_marker(ax, mapx(tp), ymid + yscale * 1.18, ymid + yscale * 0.92, color=F.RED)
    return rx

def wave_in(ax, X, Y, x0, x1, ymid, yscale, color=F.INK, lw=2.2, zorder=4):
    """Map any (X,Y) model waveform (vf/vt/torsades/asystole/pea) into window [x0,x1]."""
    return F.draw_ecg(ax, X, Y, x0, x1, ymid, yscale, color=color, lw=lw, zorder=zorder)

def pacing_in(ax, x0, x1, ymid, yscale, beats=5, capture=True, false_capture=False,
              color=F.INK, lw=2.2, spike_color=F.TEAL, zorder=4):
    """Draw a transcutaneous-pacing strip with pacer spikes into [x0,x1]. Spikes are tall
    thin vertical ticks; capture/false_capture control the ventricular response."""
    X, Y, spikes = F.pacing_ecg(beats=beats, capture=capture, false_capture=false_capture)
    span = X.max() - X.min()
    def mapx(v): return x0 + (v - X.min()) / span * (x1 - x0)
    ax.plot(mapx(X), ymid + Y * yscale, color=color, lw=lw, zorder=zorder, solid_joinstyle="round")
    for sx in spikes:
        ax.plot([mapx(sx), mapx(sx)], [ymid - yscale * 0.25, ymid + yscale * 1.25],
                color=spike_color, lw=1.6, zorder=zorder + 1)
    return [mapx(s) for s in spikes]

def shock_bolt(ax, x, y, size=0.5, color=F.RED, zorder=8):
    """A lightning-bolt glyph marking a delivered shock."""
    pts = [(x, y+size), (x-0.18*size, y+0.15*size), (x+0.05*size, y+0.15*size),
           (x-0.10*size, y-size), (x+0.20*size, y-0.05*size), (x-0.02*size, y-0.05*size)]
    ax.add_patch(Polygon(pts, closed=True, fc=color, ec="none", zorder=zorder))

def big_x(ax, x, y, size=0.35, color=F.RED, lw=4):
    """A bold red X (wrong / non-indication)."""
    ax.plot([x-size, x+size], [y-size, y+size], color=color, lw=lw, zorder=8, solid_capstyle="round")
    ax.plot([x-size, x+size], [y+size, y-size], color=color, lw=lw, zorder=8, solid_capstyle="round")

def check(ax, x, y, size=0.35, color=F.GREEN, lw=4):
    """A bold green check (right / correct)."""
    ax.plot([x-size, x-size*0.2, x+size], [y, y-size*0.8, y+size*0.9],
            color=color, lw=lw, zorder=8, solid_capstyle="round", solid_joinstyle="round")
