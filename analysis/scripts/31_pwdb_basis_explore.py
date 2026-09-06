#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""【探索・事後】基底関数を変えると PWDB の型1 の拍で何が起きるか（第3版の設計のための材料）。

**決定試験（26番・27番）の判定には使わない。** 予備実行で第2版の主経路が採用 0% だったのを受けて、
「ガウス関数なら避けられたか」「文献の基底なら PWDB でどうなるか」を、同じ拍・同じ Wang の規準で
並べて測る。閾値は動かさない。ここで良かった基底を採るなら、新しい事前登録の下で第3版として試す。

並べる基底（いずれも第2版と同じ前処理・鍵点・重み・多点起動・順序の罰則）
  歪みガウス α∈[0,8]      2・3 成分  … 第2版の凍結値（対照）
  ガウス（α=0 固定）        2〜5 成分  … Wang 2013 は 4→5 ガウス（対称）
  歪みガウス α∈[−8,8]     2・3 成分  … Basso 2024（歪みに境界を置かない）
  ガンマ（凍結の範囲）      3・4 成分  … 第2版のガンマ経路（Tigges＋到達時刻）
  ガンマ（広い範囲）        3・4 成分  … 形状 ≤ 100・立ち上がり ≤ 0.6T（27番 B 層の条件と同じ）

出すもの: 基底ごとの Wang 規準の通過率、Errx の分位、張り付き率、ΔT×大動脈PWV の年齢層内 |ρ| の中央値
（採用分と全例）。文献の手法の多くは採否規準を持たないので「全例」の列がそれに相当する。

使い方
------
    python3 scripts/31_pwdb_basis_explore.py --pwdb ~/pwdb --n 120 --jobs 8
    python3 scripts/31_pwdb_basis_explore.py --selftest
"""
from __future__ import annotations

import argparse
import contextlib
import importlib.util
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from src import pda2  # noqa: E402

DATA = ROOT / "data"
OUT = DATA / "pwdb"

VARIANTS = [
    ("歪みガウス α∈[0,8]（凍結）", "skew", 2, (0.0, 8.0), None),
    ("歪みガウス α∈[0,8]（凍結）", "skew", 3, (0.0, 8.0), None),
    ("ガウス（α=0 固定）", "skew", 2, (0.0, 1e-6), None),
    ("ガウス（α=0 固定）", "skew", 3, (0.0, 1e-6), None),
    ("ガウス（α=0 固定）", "skew", 4, (0.0, 1e-6), None),
    ("ガウス（α=0 固定）", "skew", 5, (0.0, 1e-6), None),
    ("歪みガウス α∈[−8,8]（Basso）", "skew", 2, (-8.0, 8.0), None),
    ("歪みガウス α∈[−8,8]（Basso）", "skew", 3, (-8.0, 8.0), None),
    ("ガンマ（凍結の範囲）", "gamma", 3, None, (pda2.GAMMA_SHAPE_MAX, pda2.GAMMA_RISE_MAX)),
    ("ガンマ（凍結の範囲）", "gamma", 4, None, (pda2.GAMMA_SHAPE_MAX, pda2.GAMMA_RISE_MAX)),
    ("ガンマ（広い範囲）", "gamma", 3, None, (100.0, 0.6)),
    ("ガンマ（広い範囲）", "gamma", 4, None, (100.0, 0.6)),
]


def _load(stem: str, name: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / "scripts" / stem)
    m = importlib.util.module_from_spec(spec)
    sys.modules[name] = m
    spec.loader.exec_module(m)
    return m


@contextlib.contextmanager
def _alpha_bounds(lo_a: float, hi_a: float):
    """歪み α の探索範囲を一時的に差し替える（fit_waves は _wave_bounds をモジュールから引く）。"""
    orig = pda2._wave_bounds

    def patched(t, n_waves, min_gap=0.03, alpha_min=pda2.ALPHA_MIN):
        lo, hi, gap = orig(t, n_waves, min_gap, alpha_min)
        lo, hi = lo.copy(), hi.copy()
        lo[3::4] = lo_a
        hi[3::4] = hi_a
        return lo, hi, gap
    pda2._wave_bounds = patched
    try:
        yield
    finally:
        pda2._wave_bounds = orig


def fit_variant(t, ys, lm, w, kind, nw, arange, gbounds) -> dict:
    """1 拍 × 1 基底。Wang の規準・鍵点のずれ・役割から ΔT・張り付きを返す。"""
    nan = float("nan")
    out = {"ok": 0, "errx": nan, "nrmse": nan, "erry": nan, "nlm": 0, "dt_ms": nan, "npin": 0, "fail": 0}
    try:
        if kind == "skew":
            with _alpha_bounds(*arange):
                fit = pda2.fit_waves(t, ys, lm, n_waves=nw, w=w, alpha_min=arange[0])
        else:
            fit = pda2.fit_gamma(t, ys, lm, n_kernels=nw, w=w, shape_max=gbounds[0], rise_max=gbounds[1])
        if fit is None or not fit.get("sols"):
            out["fail"] = 1
            return out
        sol = fit["sols"][0]
        yhat = fit["model"](sol.x)
        acc = pda2.acceptance(t, ys, yhat, lm, w)
        out.update(ok=int(bool(acc["ok"])), errx=float(acc["errx_ms"]), nrmse=float(acc["nrmse"]),
                   erry=float(acc["erry"]), nlm=int(acc["n_landmark_matched"]))
        peaks, cov, step, sds, tp_pin = pda2._peaks_and_se(sol, fit["n"], fit["kind"], t, fit["lo"], fit["hi"],
                                                            n_penalty=2 * (fit["n"] - 1))
        roles = pda2.assign_roles(peaks, lm, t)
        if roles["reflected"] is not None:
            out["dt_ms"] = float((peaks[roles["reflected"]][0] - peaks[roles["forward"]][0]) * 1000.0)
        out["npin"] = len(pda2.pinned_params(sol, fit["lo"], fit["hi"], fit["kind"]))
    except Exception:      # noqa: BLE001
        out["fail"] = 1
    return out


def _one_beat(args):
    subj, age, pwv, y, fs = args
    t = np.arange(y.size) / fs
    rows = []
    try:
        ys, _amp = pda2.preprocess(t, y, fs)
        if ys is None:
            return rows
        lm = pda2.find_landmarks(t, ys)
        if lm["klass"] != 1:
            return rows
        w = pda2._weights(t, lm, pda2.W_KEY)
        for label, kind, nw, arange, gb in VARIANTS:
            r = fit_variant(t, ys, lm, w, kind, nw, arange, gb)
            rows.append({"subj_no": subj, "age": age, "PWV_a": pwv, "prom": lm.get("prom", np.nan),
                         "basis": label, "kind": kind, "n": nw, **r})
    except Exception:      # noqa: BLE001
        pass
    return rows


def collect(root: Path, n_beats: int, jobs: int) -> list:
    M = _load("20_pwdb_validity.py", "m20")
    hae, cfg, ppg, _ = M.load_pwdb(Path(root).expanduser())
    hr_by = dict(zip(hae["subj_no"].astype(int), hae["HR"].astype(float)))
    age_by = dict(zip(hae["subj_no"].astype(int), hae["age"].astype(float)))
    pwv_by = dict(zip(hae["subj_no"].astype(int), hae["PWV_a"].astype(float)))
    work = []
    stride = max(1, len(ppg) // max(n_beats * 4, 1))
    for i in range(0, len(ppg), stride):
        subj = int(ppg.iloc[i, 0])
        y, fs = M.beat_of(ppg.iloc[i].to_numpy(float), hr_by.get(subj, np.nan))
        if y is None:
            continue
        t = np.arange(y.size) / fs
        ys, _ = pda2.preprocess(t, y, fs)
        if ys is None or pda2.find_landmarks(t, ys)["klass"] != 1:
            continue
        work.append((subj, age_by.get(subj, np.nan), pwv_by.get(subj, np.nan), y, fs))
        if len(work) >= n_beats:
            break
    print(f"型1 の拍 {len(work)} を {len(VARIANTS)} 通りの基底で当てはめます（jobs={jobs}）", flush=True)
    rows = []
    if jobs > 1:
        from concurrent.futures import ProcessPoolExecutor
        with ProcessPoolExecutor(max_workers=jobs) as ex:
            for rr in ex.map(_one_beat, work, chunksize=2):
                rows.extend(rr)
    else:
        for k, wk in enumerate(work, 1):
            rows.extend(_one_beat(wk))
            if k % 10 == 0:
                print(f"  [{k}/{len(work)}]", flush=True)
    return rows


def _by_age_rho(d, col: str, tgt: str, min_n: int = 8) -> tuple:
    from scipy.stats import spearmanr
    rs = []
    for _age, g in d.groupby("age"):
        x, y = g[col].to_numpy(float), g[tgt].to_numpy(float)
        m = np.isfinite(x) & np.isfinite(y)
        if m.sum() < min_n or np.ptp(x[m]) == 0 or np.ptp(y[m]) == 0:
            continue
        rs.append(float(spearmanr(x[m], y[m]).correlation))
    if not rs:
        return float("nan"), 0, 0
    rs = np.asarray(rs)
    return float(np.median(np.abs(rs))), int((rs < 0).sum()), int(rs.size)


def report(rows: list, out_csv: Path | None) -> None:
    import pandas as pd
    d = pd.DataFrame(rows)
    if out_csv is not None:
        out_csv.parent.mkdir(parents=True, exist_ok=True)
        d.to_csv(out_csv, index=False)
    print("=" * 100)
    print("基底ごとの挙動（PWDB 型1 の拍・同じ前処理と規準）。**探索であり判定には使わない**")
    print("=" * 100)
    print(f"{'基底':<30}{'成分':>4}{'拍':>5}{'Wang通過':>9}{'Errx 10/50/90 [ms]':>22}{'NRMSE中央':>10}{'張り付き':>8}"
          f"{'ΔT×PWV |ρ| 採用分(層/負)':>26}{'全例(層/負)':>16}{'失敗':>5}")
    for (label, nw), g in d.groupby(["basis", "n"], sort=False):
        e = g["errx"].to_numpy(float)
        e = e[np.isfinite(e)]
        q = " / ".join(f"{np.percentile(e, p):.0f}" for p in (10, 50, 90)) if e.size else "—"
        acc = g[g["ok"] == 1]
        r_a, neg_a, n_a = _by_age_rho(acc, "dt_ms", "PWV_a") if len(acc) else (float("nan"), 0, 0)
        r_c, neg_c, n_c = _by_age_rho(g, "dt_ms", "PWV_a")
        ra = f"{r_a:.2f} ({neg_a}/{n_a})" if n_a else "—"
        rc = f"{r_c:.2f} ({neg_c}/{n_c})" if n_c else "—"
        print(f"{label:<30}{nw:>4}{len(g):>5}{g['ok'].mean():>9.1%}{q:>22}{np.nanmedian(g['nrmse']):>10.4f}"
              f"{(g['npin'] > 0).mean():>8.0%}{ra:>26}{rc:>16}{int(g['fail'].sum()):>5}")
    print("  読み方: 「Wang通過」は NRMSE<0.02・Errx<6 ms・Erry<0.01・鍵点 2 点以上。文献の手法の多くは採否規準を"
          "持たないので、\n  「全例」の列がそれに相当する。|ρ| は年齢層内 Spearman の中央値（層は 8 拍以上。負の層の数/層数）。"
          "\n  ここで良い基底があっても、採るのは新しい事前登録の下で第3版として。閾値は動かさない。")


def selftest() -> int:
    import tempfile
    import io
    ok = True

    def rep(name, cond, detail=""):
        nonlocal ok
        ok &= bool(cond)
        print(f"  [{'PASS' if cond else 'FAIL'}] {name}{('  ' + detail) if detail else ''}")

    print("== 31_pwdb_basis_explore 自己検証（模擬 PWDB） ==\n")
    C = _load("26_pwdb_compare.py", "m26")
    with tempfile.TemporaryDirectory() as td:
        res = C._selftest_root(Path(td), n=24)
        root = res[0] if isinstance(res, tuple) else res
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            rows = collect(root, 3, 1)
            report(rows, Path(td) / "basis.csv")
        out = buf.getvalue()
        n_var = len({(r["basis"], r["n"]) for r in rows})
        rep("型1 の拍を全基底で当てはめ、表が出る", n_var == len(VARIANTS) and "Wang通過" in out, f"基底 {n_var}")
        rep("失敗（例外）が無い", sum(r["fail"] for r in rows) == 0)
        rep("α=0 固定の基底で張り付きが数えられる（α は数えない）", all(r["npin"] >= 0 for r in rows))
        rep("CSV が書かれる", (Path(td) / "basis.csv").exists())
    # α の差し替えが元に戻っていること
    t = np.arange(0, 0.8, 1 / 500.0)
    lo, hi, _ = pda2._wave_bounds(t, 2)
    rep("α の探索範囲の差し替えが元に戻っている", hi[3] == 8.0 and lo[3] == pda2.ALPHA_MIN)
    print("\n" + ("ALL PASS" if ok else "FAIL あり"))
    return 0 if ok else 1


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--pwdb", type=str, default=None)
    ap.add_argument("--n", type=int, default=120, help="型1 の拍の数（全体から等間隔）")
    ap.add_argument("--jobs", type=int, default=1)
    ap.add_argument("--selftest", action="store_true")
    args = ap.parse_args()
    if args.selftest:
        sys.exit(selftest())
    if not args.pwdb:
        ap.error("--pwdb を指定してください（--selftest なら不要）")
    rows = collect(Path(args.pwdb), args.n, max(1, args.jobs))
    report(rows, OUT / "basis_explore.csv")


if __name__ == "__main__":
    main()
