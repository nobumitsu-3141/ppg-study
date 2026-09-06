#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""【探索】VitalDB のモニタ波形で、我々の関数・条件と文献の関数・条件を同じ窓・同じ平均拍で並べる。

並べるもの（同じ 60 秒窓の平均拍 1 拍に全部を当てる）
  我々    PDA 第2版 歪みガウス・ガンマ（`src/pda2.py`・決定試験と同じ条件）、凍結版 2 カーネル（研究1 と同じ `src/pda.py`）、
          ランドマーク ΔT・RI（`pda2.find_landmarks`）、早期振幅比 Am_b/Am_p1（`pda2.early_features`）
  文献    33番の再現（Goswami 2010・Tigges 2017・Wang 2013・Couceiro 2015・Fleischhauer 2020・Basso 2024。文献の条件のまま）
  対照    同じ窓の PWTT

真値が無いので、比べるのは 32番と同じ量: **同定率**（指標が有限な窓の割合）、**窓間の再現性**（隣接窓の lag-1 自己相関）、
**症例間の分離**（ICC(1)）、年齢との順位相関（20 例・記述）。

問い（探索。結果を見る前に固定。lab_log 追記19）
------------------------------------------------
  1. 実機のモニタ波形で、分解由来の ΔT・RI（我々・文献）は計測由来（ランドマーク ΔT・Am_b/Am_p1）を同定率・再現性で上回るか。
     **上回る** = 同定率と自己相関の症例中央値の**両方**が、同じ窓のランドマーク ΔT（RI ならランドマーク RI）を 0.05 以上上回る。
  2. 分解の利点「切痕・拡張期ピークが無くても動く」は実機で出るか。
     = 型4（拡張期の錨なし）の窓で分解が出した値の再現性（症例中央値を引いた値で、型4 窓と隣の窓の対を全症例で集めた
       Pearson r。対 30 組以上）が **≥ 0.30** なら「出た」と読む。
  陽性対照: PWTT の自己相関の症例中央値 ≥ 0.50（研究1 の実測 +0.746・32番 0.794）。通らなければ表全体を無効とする。
  この表は決定試験の判定（roadmap §9）を動かさない。上回る手法があっても採らず、新しい事前登録の材料にする。

窓
--
  32番と同じ 20 例（`target_cases.csv` の caseid 昇順から seed 0）。各症例で、位置 20%・50%・80% から**連続 6 窓**
  （すべて SQI 通過拍 8 以上）を 3 ブロック = 18 窓（自己相関の対 15 組）。全窓に当てると Wang（100 回当てはめ）で日単位になるため。
  Wang の重みの刻みは既定 5（33番の 624 名では選ばれた重みの中央値が 100 で刻み 1 との差は小さい。`--wang-step 1` で文献どおり）。

使い方
------
    python3 scripts/34_vitaldb_methods_compare.py --selftest
    python3 scripts/34_vitaldb_methods_compare.py --run --jobs 4
出力: data/vitaldb_methods/windows.csv（窓 × 手法）・summary.csv（症例 × 手法）・report.txt
"""
from __future__ import annotations

import argparse
import importlib.util
import io
import json
import sys
import time
import warnings
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from src import pda2                                                     # noqa: E402
from src.pda import fit_beat                                             # noqa: E402
from src.indices import si_ri_from_fit                                   # noqa: E402
from src.beats import segment_beats, sqi, ensemble_average               # noqa: E402

DATA = ROOT / "data"
OUT = DATA / "vitaldb_methods"
N_BLOCKS = 3
BLOCK_LEN = 6
BLOCK_POS = (0.2, 0.5, 0.8)
GATE_ID = 0.70
GATE_AC = 0.30
GATE_CTL = 0.50
MARGIN = 0.05
MIN_PAIRS_T4 = 30
NAN = float("nan")


def _load(stem: str, name: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / "scripts" / stem)
    m = importlib.util.module_from_spec(spec)
    sys.modules[name] = m
    spec.loader.exec_module(m)
    return m


M32 = _load("32_vitaldb_landmark_identifiability.py", "m32")
M33 = _load("33_pwdb_literature_replica.py", "m33")
FS, WIN_S, MIN_GOOD = M32.FS, M32.WIN_S, M32.MIN_GOOD

# (列, 表示名, 採否列, 群)
DT_ROWS = [
    ("dt_v2_ms",  "第2版 歪みガウス（我々・決定試験の条件）", "ok_v2",  "分解・我々"),
    ("dt_v2g_ms", "第2版 ガンマ（我々）",                    "ok_v2g", "分解・我々"),
    ("dt_v1_ms",  "凍結版 2 カーネル（研究1）",               "ok_v1",  "分解・我々"),
    ("dt_gos_ms", "Goswami 2010 Rayleigh 2",                None,     "分解・文献"),
    ("dt_tig_ms", "Tigges 2017 AICc 最良",                  None,     "分解・文献"),
    ("dt_tig3_ms", "Tigges 2017 Gamma M=3",                 None,     "分解・文献"),
    ("dt_wang_ms", "Wang 2013 4→5 ガウス（全例）",           "ok_wang", "分解・文献"),
    ("dt_cou_ms", "Couceiro 2015 5 ガウス",                 None,     "分解・文献"),
    ("dt_fl2_ms", "Fleischhauer 2020 Gamma+Gauss 2",        None,     "分解・文献"),
    ("dt_fl3_ms", "Fleischhauer 2020 Gamma+Gauss 3",        None,     "分解・文献"),
    ("dt_bas2_ms", "Basso 2024 歪みガウス L=2",              None,     "分解・文献"),
    ("dt_bas3_ms", "Basso 2024 歪みガウス L=3",              None,     "分解・文献"),
    ("dt_bas4_ms", "Basso 2024 歪みガウス L=4",              None,     "分解・文献"),
    ("dt_lm_ms",  "ランドマーク ΔT（計測・基準）",            None,     "計測"),
    ("amb",       "Am_b/Am_p1（計測）",                      None,     "計測"),
    ("pwtt_ms",   "PWTT（陽性対照）",                         None,     "対照"),
]
RI_ROWS = [
    ("ri_v2",  "第2版 歪みガウス（我々）", "ok_v2", "分解・我々"), ("ri_v2g", "第2版 ガンマ（我々）", "ok_v2g", "分解・我々"),
    ("ri_v1",  "凍結版 2 カーネル（研究1）", "ok_v1", "分解・我々"),
    ("ri_gos", "Goswami 2010", None, "分解・文献"), ("ri_tig3", "Tigges Gamma M=3", None, "分解・文献"),
    ("ri_wang", "Wang 2013（全例）", "ok_wang", "分解・文献"), ("ri_cou", "Couceiro 2015 R1_d", None, "分解・文献"),
    ("ri_fl2", "Fleischhauer 2", None, "分解・文献"), ("ri_bas2", "Basso L=2", None, "分解・文献"),
    ("ri_bas3", "Basso L=3", None, "分解・文献"),
    ("ri_lm",  "ランドマーク RI（計測・基準）", None, "計測"),
]


# ================================================================ 1 窓
def ensemble_beat(seg_p, seg_e):
    """SQI 通過拍を足で揃えて平均した 1 拍。8 拍未満なら None。"""
    try:
        beats = segment_beats(seg_p, FS, ecg=seg_e)
        good = [(s, e) for s, e in beats if sqi(seg_p[s:e], FS)["ok"]]
    except Exception:      # noqa: BLE001
        return None, 0
    if len(good) < MIN_GOOD:
        return None, len(good)
    return ensemble_average([seg_p[s:e] for s, e in good]), len(good)


def methods_on_beat(y, fs: float, wang_step: int) -> dict:
    """平均拍 1 拍に、我々の関数・条件と文献の関数・条件をすべて当てる。"""
    out = {}
    t = np.arange(len(y)) / fs
    for tag, route in (("v2", "skew"), ("v2g", "gamma")):
        try:
            r = pda2.decompose(t, y, fs, route=route)
            out[f"ok_{tag}"] = int(bool(r.get("ok")))
            out[f"dt_{tag}_ms"] = float(r.get("dt_ms", NAN))
            out[f"ri_{tag}"] = float(r.get("ri", NAN))
            out[f"why_{tag}"] = str(r.get("reason", ""))[:24]
        except Exception as e:      # noqa: BLE001
            out[f"ok_{tag}"], out[f"dt_{tag}_ms"], out[f"ri_{tag}"] = 0, NAN, NAN
            out[f"why_{tag}"] = ("EXC:" + str(e))[:24]
    try:
        fit = fit_beat(t, y)
        ix = si_ri_from_fit(fit)
        out["ok_v1"] = int(bool(fit.get("ok", False)))
        out["dt_v1_ms"] = float(ix["dt_s"] * 1000.0) if ix["dt_s"] > 0 else NAN
        out["ri_v1"] = float(ix["ri"])
    except Exception:      # noqa: BLE001
        out["ok_v1"], out["dt_v1_ms"], out["ri_v1"] = 0, NAN, NAN
    f = M32._beat_features(y, fs)
    out.update({"klass": f["klass"], "prom": f["prom"], "dt_lm_ms": f["dt_lm_ms"], "amb": f["amb"]})
    try:
        ys, _ = pda2.preprocess(t, np.asarray(y, float), fs)
        lm = pda2.find_landmarks(t, ys) if ys is not None else None
        out["ri_lm"] = (float(lm["dia_v"] / lm["sys_v"]) if lm is not None and lm["klass"] in (1, 3)
                        and np.isfinite(lm["dia_v"]) and lm["sys_v"] > 0 else NAN)
    except Exception:      # noqa: BLE001
        out["ri_lm"] = NAN
    try:
        rep = M33.replica_for_beat(t, np.asarray(y, float), fs, wang_step)
        rep.pop("klass_own", None)
        rep.pop("dt_own_ms", None)
        rep.pop("ri_own", None)
        out.update(rep)
    except Exception as e:      # noqa: BLE001
        out["err"] = ("EXC:" + str(e))[:80]
    return out


def _window_task(args):
    caseid, t0, seg_p, seg_e, wang_step = args
    out = {"caseid": int(caseid), "t0": float(t0)}
    y, n_good = ensemble_beat(seg_p, seg_e)
    out["n_good"] = int(n_good)
    if y is None:
        return out
    try:
        out.update(methods_on_beat(y, FS, wang_step))
    except Exception as e:      # noqa: BLE001
        out["err"] = ("EXC:" + str(e))[:80]
    return out


# ================================================================ 窓の選択（事前規準）
def pick_blocks(analyzable: np.ndarray, n_blocks: int = N_BLOCKS, block_len: int = BLOCK_LEN,
                positions=BLOCK_POS) -> list:
    """analyzable[i]（窓 i が解析できるか）から、位置 20/50/80% 以降で最初に見つかる連続 block_len 窓を 1 ブロックずつ。"""
    n = len(analyzable)
    chosen, used = [], set()
    for frac in positions[:n_blocks]:
        s = int(frac * max(n - block_len, 0))
        for k in range(s, n - block_len + 1):
            idx = list(range(k, k + block_len))
            if all(analyzable[i] for i in idx) and not (set(idx) & used):
                chosen.append(idx)
                used |= set(idx)
                break
    return chosen


def case_tasks(caseid: int, arrays: dict, wang_step: int, n_blocks=N_BLOCKS, block_len=BLOCK_LEN) -> list:
    """症例の全窓の解析可否（SQI 通過拍数）を数えてブロックを選び、窓ごとの仕事に切る。"""
    pleth, ecg = arrays["pleth"], arrays["ecg"]
    dur = len(pleth) / FS
    t0s = np.arange(0, dur - WIN_S, WIN_S)
    ok = np.zeros(len(t0s), bool)
    for i, t0 in enumerate(t0s):
        i0, i1 = int(t0 * FS), int((t0 + WIN_S) * FS)
        seg_p = np.nan_to_num(np.asarray(pleth[i0:i1], float))
        seg_e = np.nan_to_num(np.asarray(ecg[i0:i1], float))
        if seg_p.size < int(WIN_S * FS) * 0.9 or not np.any(seg_p):
            continue
        try:
            beats = segment_beats(seg_p, FS, ecg=seg_e)
            ok[i] = sum(1 for s, e in beats if sqi(seg_p[s:e], FS)["ok"]) >= MIN_GOOD
        except Exception:      # noqa: BLE001
            ok[i] = False
    tasks = []
    for idx in pick_blocks(ok, n_blocks, block_len):
        for i in idx:
            t0 = float(t0s[i])
            i0, i1 = int(t0 * FS), int((t0 + WIN_S) * FS)
            tasks.append((caseid, t0, np.nan_to_num(np.asarray(pleth[i0:i1], float)),
                          np.nan_to_num(np.asarray(ecg[i0:i1], float)), wang_step))
    return tasks


# ================================================================ 集計
def _pwtt_for(caseid: int, t0s, arrays: dict) -> dict:
    """同じ窓の PWTT（32番の window_landmarks と同じ計算）。"""
    from src.indices import estimate_pleth_lag
    pleth, ecg = arrays["pleth"], arrays["ecg"]
    lag = estimate_pleth_lag(ecg, pleth, FS)
    out = {}
    for t0 in t0s:
        w = M32.window_landmarks(pleth, ecg, float(t0), lag)
        out[float(t0)] = (w["pwtt_ms"], w["hr"])
    return out


def summarize(win, ages: dict | None = None):
    """症例 × 手法の同定率・自己相関・CV と、全体の ICC・年齢相関・型4 窓の再現性。"""
    import pandas as pd
    rows = []
    cols = [c for c, *_ in DT_ROWS] + [c for c, *_ in RI_ROWS]
    for cid, g in win.groupby("caseid"):
        g = g.sort_values("t0")
        r = {"caseid": int(cid), "n_windows": int(len(g)), "type4": float(np.mean(g["klass"] >= 4)) if len(g) else NAN}
        for c in cols:
            v = g[c].to_numpy(float) if c in g else np.full(len(g), NAN)
            r[f"id_{c}"] = float(np.isfinite(v).mean()) if v.size else NAN
            r[f"ac_{c}"] = M32.lag1_autocorr(g["t0"].to_numpy(float), v, min_pairs=8)[0]
            fin = v[np.isfinite(v)]
            r[f"cv_{c}"] = float(np.std(fin) / abs(np.mean(fin))) if fin.size >= 3 and np.mean(fin) != 0 else NAN
            r[f"med_{c}"] = float(np.median(fin)) if fin.size else NAN
        for okc in ("ok_v2", "ok_v2g", "ok_v1", "ok_wang"):
            r[f"acc_{okc}"] = float(np.nanmean(g[okc])) if okc in g and g[okc].notna().any() else NAN
        rows.append(r)
    summ = pd.DataFrame(rows)
    if ages:
        summ["age"] = summ["caseid"].map(lambda c: float(ages.get(int(c), NAN)))
    return summ


def type4_reproducibility(win, col: str) -> tuple:
    """型4 窓と隣の窓の対（症例中央値を引いた値）を全症例で集めた Pearson r と対の数。"""
    a, b = [], []
    for _cid, g in win.groupby("caseid"):
        g = g.sort_values("t0")
        v = g[col].to_numpy(float) if col in g else np.full(len(g), NAN)
        k = g["klass"].to_numpy(float)
        t0 = g["t0"].to_numpy(float)
        fin = v[np.isfinite(v)]
        if fin.size < 3:
            continue
        v = v - np.median(fin)
        for i in range(len(g) - 1):
            if abs((t0[i + 1] - t0[i]) - WIN_S) > 1e-6:
                continue
            if (k[i] >= 4 or k[i + 1] >= 4) and np.isfinite(v[i]) and np.isfinite(v[i + 1]):
                a.append(v[i])
                b.append(v[i + 1])
    if len(a) < MIN_PAIRS_T4 or np.std(a) == 0 or np.std(b) == 0:
        return NAN, len(a)
    return float(np.corrcoef(a, b)[0, 1]), len(a)


def report(win, summ, out_dir: Path | None = None) -> dict:
    out_dir = OUT if out_dir is None else out_dir
    out_dir.mkdir(parents=True, exist_ok=True)
    win.to_csv(out_dir / "windows.csv", index=False)
    summ.to_csv(out_dir / "summary.csv", index=False)
    res = {}
    n_case = len(summ)
    ac_ctl = float(np.nanmedian(summ["ac_pwtt_ms"])) if n_case else NAN
    ctl_ok = bool(np.isfinite(ac_ctl) and ac_ctl >= GATE_CTL)
    print("=" * 112)
    print("VitalDB モニタ波形: 我々の関数・条件 vs 文献の関数・条件 vs 計測（同じ窓・同じ平均拍）。**探索であり判定は動かさない**")
    print("=" * 112)
    t4 = float(np.mean(win["klass"] >= 4)) if len(win) else NAN
    print(f"症例 {n_case} 例・窓 {len(win)}（1 症例 {N_BLOCKS} ブロック × 連続 {BLOCK_LEN} 窓）・平均拍の型4 の割合 {t4:.0%}・"
          f"Wang の重みの刻み {int(win['wang_step'].iloc[0]) if 'wang_step' in win and len(win) else '?'}")
    print(f"\n0. 陽性対照 PWTT: 窓間自己相関の症例中央値 {ac_ctl:.3f}（要求 ≥ {GATE_CTL}）→ "
          f"{'合格' if ctl_ok else '**不合格。表全体を無効とする**'}")

    def block(rows, ref_col, title):
        ref_id = float(np.nanmedian(summ[f"id_{ref_col}"])) if n_case else NAN
        ref_ac = float(np.nanmedian(summ[f"ac_{ref_col}"])) if n_case else NAN
        print(f"\n{'-' * 112}\n{title}（基準 = 同じ窓のランドマーク: 同定率 {ref_id:.2f}・自己相関 {ref_ac:.2f}。"
              f"上回る = 両方が基準 + {MARGIN} 以上）\n{'-' * 112}")
        print(f"{'手法':<40}{'群':>8}{'採択率':>8}{'同定率':>8}{'自己相関':>9}{'ICC':>7}{'年齢ρ':>7}{'上回る':>7}"
              f"{'型4窓 同定率':>12}{'型4窓 再現性(対)':>16}")
        for col, label, okc, grp in rows:
            idr = float(np.nanmedian(summ[f"id_{col}"])) if n_case else NAN
            ac = float(np.nanmedian(summ[f"ac_{col}"])) if n_case else NAN
            groups = [g[col].to_numpy(float) for _c, g in win.groupby("caseid")] if col in win else []
            icc = M32.icc1(groups) if groups else NAN
            rho = NAN
            if "age" in summ and summ["age"].notna().sum() >= 10:
                from scipy.stats import spearmanr
                m = summ["age"].notna() & summ[f"med_{col}"].notna()
                if m.sum() >= 10:
                    rho = float(spearmanr(summ.loc[m, "age"], summ.loc[m, f"med_{col}"]).correlation)
            acc = float(np.nanmedian(summ[f"acc_{okc}"])) if okc and f"acc_{okc}" in summ else NAN
            beat = (col != ref_col and grp.startswith("分解") and np.isfinite(idr) and np.isfinite(ac)
                    and idr >= ref_id + MARGIN and ac >= ref_ac + MARGIN)
            w4 = win[win["klass"] >= 4]
            id4 = float(np.isfinite(w4[col].to_numpy(float)).mean()) if col in w4 and len(w4) else NAN
            r4, n4 = type4_reproducibility(win, col) if grp.startswith("分解") else (NAN, 0)
            f = lambda x, d=2: (f"{x:.{d}f}" if np.isfinite(x) else "—")   # noqa: E731
            print(f"{label:<40}{grp:>8}{f(acc):>8}{f(idr):>8}{f(ac):>9}{f(icc):>7}{f(rho):>7}"
                  f"{('○' if beat else ('—' if col == ref_col or not grp.startswith('分解') else '×')):>7}"
                  f"{f(id4):>12}{(f(r4) + f' ({n4})') if grp.startswith('分解') else '—':>16}")
            res[col] = {"id": idr, "ac": ac, "icc": icc, "rho_age": rho, "acc": acc, "beat": bool(beat), "id4": id4,
                        "r4": r4, "n4": n4}
        return ref_id, ref_ac

    block(DT_ROWS, "dt_lm_ms", "1. ΔT（と Am_b/Am_p1・PWTT）")
    block(RI_ROWS, "ri_lm", "2. RI")
    beats = [label for col, label, _o, grp in DT_ROWS + RI_ROWS if res.get(col, {}).get("beat")]
    shown = [label for col, label, _o, grp in DT_ROWS if grp.startswith("分解") and np.isfinite(res.get(col, {}).get("r4", NAN))
             and res[col]["r4"] >= GATE_AC]
    print(f"\n{'-' * 112}\n3. 問いへの答え（事前に決めた読み方）\n{'-' * 112}")
    print(f"  問い 1（分解が計測を同定率と再現性の両方で上回る）: {('あり → ' + '・'.join(beats)) if beats else 'なし'}")
    print(f"  問い 2（型4 窓で分解の値が再現する r ≥ {GATE_AC}・対 {MIN_PAIRS_T4} 以上）: "
          f"{('出た → ' + '・'.join(shown)) if shown else '出ない（または対が足りない）'}")
    if not ctl_ok:
        print("  ※ 陽性対照が不合格なので、上の答えは無効。")
    print(f"\n{'-' * 112}\n読み方\n{'-' * 112}")
    print("  真値が無いので、ここで分かるのは「同定できるか」「窓間で再現するか」まで。妥当性（何を測っているか）は別の問い。")
    print("  上回る手法があっても採らず、新しい事前登録の材料にする。決定試験の判定（roadmap §9）は動かさない。")
    print("  自己相関は同じ症例の隣接 60 秒窓の値の相関。生理の変化と雑音の両方を含み、高いほど『窓ごとに同じものを測っている』。")
    print("  型4 窓の再現性は、症例中央値を引いた値で型4 窓とその隣の窓の対を全症例で集めた r（分解の利点が実機で出るかを見る）。")
    print(f"  pda2 版 {pda2.code_version()}")
    return {"control": {"ac": ac_ctl, "pass": ctl_ok}, "rows": res, "beats": beats, "shown": shown}


# ================================================================ 実行
class _Tee:
    def __init__(self, *streams):
        self.streams = streams

    def write(self, s):
        for st in self.streams:
            st.write(s)

    def flush(self):
        for st in self.streams:
            st.flush()


def run(cases: list, jobs: int, wang_step: int, out_dir: Path | None = None, loader=None,
        n_blocks: int = N_BLOCKS, block_len: int = BLOCK_LEN) -> dict:
    import pandas as pd
    out_dir = OUT if out_dir is None else out_dir
    out_dir.mkdir(parents=True, exist_ok=True)
    loader = M32._vitaldb_loader if loader is None else loader
    print(f"症例（32番と同じ seed 0 の 20 例）: {cases}", flush=True)
    tasks, ctl = [], {}
    for cid in cases:
        try:
            arrays = loader(cid)
        except Exception as e:      # noqa: BLE001
            print(f"  case {cid}: 取得失敗 {e}", flush=True)
            continue
        tk = case_tasks(cid, arrays, wang_step, n_blocks, block_len)
        ctl.update({(cid, t0): v for t0, v in _pwtt_for(cid, [t[1] for t in tk], arrays).items()})
        tasks.extend(tk)
        print(f"  case {cid}: 窓 {len(tk)}", flush=True)
    print(f"窓 {len(tasks)} に全手法を当てます（jobs={jobs}・Wang の刻み {wang_step}）", flush=True)
    t_start = time.time()
    rows = []
    prog = out_dir / "progress.json"

    def tick():
        el = time.time() - t_start
        per = el / max(len(rows), 1)
        rec = {"script": "34_vitaldb_methods_compare", "done": len(rows), "total": len(tasks), "elapsed_s": round(el),
               "per_window_s": round(per, 1), "eta_s": round(per * (len(tasks) - len(rows))), "updated": time.time(),
               "state": "done" if len(rows) == len(tasks) else "running"}
        prog.write_text(json.dumps(rec), encoding="utf-8")
        if len(rows) % 10 == 0 or len(rows) == len(tasks):
            print(f"  [{len(rows)}/{len(tasks)}] 経過 {el / 60:.1f} 分・{per:.1f} 秒/窓・残り約 {rec['eta_s'] / 60:.0f} 分", flush=True)
    if jobs > 1:
        from concurrent.futures import ProcessPoolExecutor, as_completed
        with ProcessPoolExecutor(max_workers=jobs) as ex:
            futs = [ex.submit(_window_task, tk) for tk in tasks]
            for f in as_completed(futs):
                rows.append(f.result())
                tick()
    else:
        for tk in tasks:
            rows.append(_window_task(tk))
            tick()
    win = pd.DataFrame(rows)
    win["pwtt_ms"] = [ctl.get((int(c), float(t)), (NAN, NAN))[0] for c, t in zip(win["caseid"], win["t0"])]
    win["hr"] = [ctl.get((int(c), float(t)), (NAN, NAN))[1] for c, t in zip(win["caseid"], win["t0"])]
    win["wang_step"] = wang_step
    ages = {}
    cp = DATA / "cases.csv"
    if cp.exists():
        demo = pd.read_csv(cp, encoding="utf-8-sig")
        ages = {int(r["caseid"]): float(r["age"]) for _, r in demo.iterrows() if int(r["caseid"]) in set(cases)}
    summ = summarize(win, ages)
    buf = io.StringIO()
    old = sys.stdout
    sys.stdout = _Tee(old, buf)
    try:
        res = report(win, summ, out_dir=out_dir)
    finally:
        sys.stdout = old
    (out_dir / "report.txt").write_text(buf.getvalue(), encoding="utf-8")
    print(f"\n表の全文: {out_dir / 'report.txt'}")
    return res


# ================================================================ 自己検証
def selftest() -> int:
    import contextlib
    import tempfile
    import pandas as pd
    ok = True

    def rep(name, cond, detail=""):
        nonlocal ok
        ok &= bool(cond)
        print(f"  [{'PASS' if cond else 'FAIL'}] {name}{('  ' + detail) if detail else ''}", flush=True)

    print("== 34_vitaldb_methods_compare 自己検証（合成波形・ネットワーク不要） ==\n")
    an = np.array([1, 1, 0, 1, 1, 1, 1, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1], bool)
    bl = pick_blocks(an, 3, 3)
    rep("ブロックの選択: 連続して解析できる窓だけを、位置 20/50/80% から重ならずに取る",
        len(bl) == 3 and all(all(an[i] for i in b) for b in bl) and len({i for b in bl for i in b}) == 9, str(bl))
    ecg, pleth = M32._synth_case(14 * 60, seed=5, drift=True)
    arrays = {"pleth": pleth, "ecg": ecg}
    with tempfile.TemporaryDirectory() as td:
        od = Path(td)
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            res = run([9001], jobs=1, wang_step=50, out_dir=od, loader=lambda c: arrays, n_blocks=2, block_len=3)
        out = buf.getvalue()
        win = pd.read_csv(od / "windows.csv")
        rep("合成症例で 2 ブロック × 3 窓 = 6 窓が選ばれ、全手法の列が揃う",
            len(win) == 6 and all(c in win for c, *_ in DT_ROWS) and all(c in win for c, *_ in RI_ROWS), f"窓 {len(win)}")
        fin = {c: float(np.isfinite(win[c]).mean()) for c, *_ in DT_ROWS}
        rep("計測（ランドマーク ΔT・Am_b/Am_p1・PWTT）が全窓で出る", fin["dt_lm_ms"] == 1.0 and fin["amb"] == 1.0 and fin["pwtt_ms"] == 1.0,
            "・".join(f"{k} {v:.0%}" for k, v in fin.items() if k in ("dt_lm_ms", "amb", "pwtt_ms")))
        rep("我々の分解（第2版 2 経路・凍結版）と文献の分解が走り、半分以上の窓で ΔT を返す手法がある",
            sum(1 for c, *_ in DT_ROWS if fin[c] >= 0.5) >= 8, "・".join(f"{k} {v:.0%}" for k, v in fin.items()))
        rep("例外が無い", "err" not in win or win["err"].isna().all(), str(win["err"].dropna().head(2).tolist()) if "err" in win else "")
        rep("表が出て、問い 1・2 の答えと陽性対照が書かれる", "問い 1" in out and "問い 2" in out and "陽性対照" in out
            and (od / "report.txt").exists() and (od / "summary.csv").exists())
        rep("progress.json が書かれ、state が done", json.loads((od / "progress.json").read_text())["state"] == "done")
        rep("返り値に陽性対照と手法ごとの要約が入る", "control" in res and "rows" in res and "dt_lm_ms" in res["rows"])
    print("\n" + ("ALL PASS" if ok else "FAIL あり"))
    return 0 if ok else 1


def main() -> None:
    warnings.filterwarnings("ignore", message="Values in x were outside bounds")
    warnings.filterwarnings("ignore", message="All-NaN slice")
    warnings.filterwarnings("ignore", message="Mean of empty slice")
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--run", action="store_true", help="20 例を取得して表を出す（vitaldb・ネットワーク）")
    ap.add_argument("--cases", type=str, default=None, help="caseid をカンマ区切り（事前規準は 32番と同じ seed 0 の 20 例）")
    ap.add_argument("--jobs", type=int, default=1)
    ap.add_argument("--wang-step", type=int, default=5, help="Wang の重み 1..100 の刻み（文献は 1）")
    ap.add_argument("--selftest", action="store_true")
    args = ap.parse_args()
    if args.jobs < 1:
        ap.error("--jobs は 1 以上")
    if args.selftest:
        sys.exit(selftest())
    if args.run:
        cases = [int(c) for c in args.cases.split(",")] if args.cases else M32.select_cases(M32.N_CASES, M32.SEED)
        run(cases, args.jobs, max(1, args.wang_step))
    else:
        ap.print_help()


if __name__ == "__main__":
    main()
