#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Defibrillator/DC deck — figure runner. Imports the per-group figure modules
(make_figs_g1..g4, each: import figlib as F; from fighelp import *) and runs every
figure function named f<digits...> (e.g. f00_hero, f0402). Writes PNGs to figlib.OUTDIR."""
import re, importlib
import figlib as F

GROUP_MODULES = ["make_figs_g1", "make_figs_g2", "make_figs_g3", "make_figs_g4"]

def _run():
    made, missing = [], []
    for modname in GROUP_MODULES:
        try:
            mod = importlib.import_module(modname)
        except ModuleNotFoundError:
            missing.append(modname); continue
        for name in sorted(dir(mod)):
            obj = getattr(mod, name)
            if callable(obj) and re.match(r"^f\d|^f00", name):
                obj(); made.append(name)
    return made, missing

if __name__ == "__main__":
    made, missing = _run()
    if missing:
        print("NOTE: modules not found (skipped):", ", ".join(missing))
    print(f"generated {len(made)} figures -> {F.OUTDIR}")
    for n in made:
        print("  ", n)
