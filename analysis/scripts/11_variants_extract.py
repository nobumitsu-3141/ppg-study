#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""SAP §7.5 の残り感度解析のための変種抽出（再フィットが必要な系）。

計算する変種（いずれもSAP §2.2・§7.5で事前指定）
------------------------------------------------
同一の2カーネル当てはめから導く代替定義:
  dt_onset   立ち上がり間ΔT（各成分の自ピーク高20%到達点の間隔。規約はSAP §2.2で固定）
  a_ratio    振幅パラメータ比 a2/a1
  area_ratio 成分波面積比
別の当てはめ:
  dt3, ri3   3カーネルPDA（第1↔第2成分のピーク間隔・高さ比）
アンサンブルの変種:
  dt_n2, ri_n2   ノイズ目標 0.002（主解析0.003より厳格）
  dt_n4, ri_n4   ノイズ目標 0.004（緩和）
  dt_sqi5, ri_sqi5   SQIの同一値連続閾値 10%→5%（厳格）
  dt_sqi20, ri_sqi20 同 10%→20%（緩和）

設計
----
- 主解析で採用されたウィンドウ（features/case_*.csv の t0）と同じ時刻でのみ計算する。
  PWTT・HR・MAP・CO は主解析の値をそのまま使う（12_variants_stats.py で結合）。
  → 脈波と心電図のみダウンロードすればよく、ゲート再判定も不要
- 主解析の測定パイプラインには一切触れない（このスクリプトは frozen コードを import
  して使うだけ）。結果は data/features_variants/ に別置き
- 位置づけ: SAP v0.3.1 の探索的感度解析

所要の目安: 当てはめ回数が主解析の約5〜6倍/採用ウィンドウのため、
862例で jobs 8 なら3〜5日。中断しても同じコマンドで再開できる（症例単位キャッシュ）。

使い方:
    nohup caffeinate -i python scripts/11_variants_extract.py --limit 874 --jobs 8 \
      > variants_run.log 2>&1 &
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.beats import (segment_beats, sqi, ensemble_average,  # noqa: E402
                       estimate_noise, required_ensemble_size)
from src.pda import fit_beat, skew_gaussian, component_peak   # noqa: E402
from src.indices import si_ri_from_fit                        # noqa: E402

FS = 500.0
WIN_S = 60.0
DATA = Path(__file__).resolve().parent.parent / "data"
FEAT = DATA / "features"
VFEAT = DATA / "features_variants"
META_V = 1
ONSET_FRAC = 0.20   # SAP §2.2 で固定した立ち上がり定義（自ピーク高の20%）


# ---------------------------------------------------------------- 派生指標
def _onset(comp, t0: float, t1: float, frac: float = ONSET_FRAC) -> float:
    """成分波が自ピーク高の frac に最初に到達する時刻（ピーク前）。"""
    tp, h = component_peak(comp, t0, t1)
    tt = np.linspace(t0, tp, 2000)
    y = skew_gaussian(tt, *comp)
    idx = np.flatnonzero(y >= frac * h)
    return float(tt[idx[0]]) if idx.size else float(tp)


def variant_indices_from_fit(fit: dict, t: np.ndarray) -> dict:
    """1つの2カーネル当てはめから代替定義を計算する。"""
    c1, c2 = fit["components"]
    p1 = (c1["a"], c1["mu"], c1["sigma"], c1["alpha"])
    p2 = (c2["a"], c2["mu"], c2["sigma"], c2["alpha"])
    t0f, t1f = float(t[0]), float(t[-1])
    on1, on2 = _onset(p1, t0f, t1f), _onset(p2, t0f, t1f)
    tt = np.linspace(t0f, t1f, 2000)
    a1 = float(np.trapezoid(skew_gaussian(tt, *p1), tt))
    a2 = float(np.trapezoid(skew_gaussian(tt, *p2), tt))
    return {
        "dt_onset": on2 - on1,
        "a_ratio": float(c2["a"] / max(c1["a"], 1e-12)),
        "area_ratio": a2 / max(a1, 1e-12),
    }


# ---------------------------------------------------------------- 3カーネル
def _model3(t: np.ndarray, p: np.ndarray) -> np.ndarray:
    y = np.zeros_like(t)
    for i in range(3):
        y += skew_gaussian(t, *p[4 * i:4 * i + 4])
    return y


def fit_beat3(t: np.ndarray, y: np.ndarray, seed: int = 0,
              n_starts: int = 4) -> dict | None:
    """3カーネル版の当てはめ（探索的感度解析用・pda.fit_beat を模した簡易版）。

    ok 判定は境界張り付き（α境界は除外）と振幅ゼロ、および
    「残差が拮抗する別解で ΔT が20%以上異なる」場合の曖昧判定。
    主解析の fit_beat と同一ではない（その旨を論文に明記する）。
    """
    from scipy.optimize import least_squares
    t = np.asarray(t, float)
    y0 = np.asarray(y, float) - float(np.min(y))
    ymax = float(np.max(y0))
    if ymax <= 0:
        return None
    ys = y0 / ymax
    T = float(t[-1] - t[0])
    i_pk = int(np.argmax(ys))
    t_pk = float(t[i_pk])

    #      a1    mu1              s1     al1  a2    dmu2  s2     al2  a3    dmu3  s3     al3
    lo = [0.05, 0.02,            0.015, 0.0, 0.02, 0.06, 0.015, 0.0, 0.01, 0.05, 0.015, 0.0]
    hi = [1.5,  max(t_pk + .1, .3), .25, 8.0, 1.2,  0.45, 0.25,  8.0, 1.0,  0.45, 0.25,  8.0]

    def unpack(q):
        a1, m1, s1, l1, a2, d2, s2, l2, a3, d3, s3, l3 = q
        return np.array([a1, m1, s1, l1, a2, m1 + d2, s2, l2, a3, m1 + d2 + d3, s3, l3])

    def resid(q):
        return _model3(t, unpack(q)) - ys

    rng = np.random.default_rng(seed)
    sols = []
    for k in range(n_starts):
        x0 = np.array([0.8, t_pk, 0.05, 2.0,
                       0.35, 0.10 + 0.25 * rng.random(), 0.07, 1.0,
                       0.15, 0.10 + 0.25 * rng.random(), 0.09, 1.0])
        x0 = np.clip(x0, lo, hi)
        try:
            r = least_squares(resid, x0, bounds=(lo, hi), max_nfev=200)
        except Exception:
            continue
        sols.append((float(np.sum(r.fun ** 2)), r.x))
    if not sols:
        return None
    sols.sort(key=lambda s: s[0])
    cost, q = sols[0]
    p = unpack(q)
    c1, c2 = p[0:4], p[4:8]
    tp1, h1 = component_peak(tuple(c1), t[0], t[-1])
    tp2, h2 = component_peak(tuple(c2), t[0], t[-1])
    dt = tp2 - tp1

    # 検算
    # 第3成分の振幅が床に張り付くのは「3つ目の波が無い」正常な退化
    # （2カーネル解に一致する）なので、その場合は第3成分のパラメータを
    # 境界判定から除外する。第1・第2成分の消失は従来どおり棄却する。
    eps = 1e-9
    comp3_absent = q[8] <= lo[8] + 0.02
    onb = []
    for j, v in enumerate(q):
        if j % 4 == 3:      # α境界は fit_beat と同様に除外
            continue
        if comp3_absent and j >= 8:
            continue
        onb.append(v <= lo[j] + eps * max(1, abs(lo[j])) or
                   v >= hi[j] - eps * max(1, abs(hi[j])))
    boundary = any(onb)
    amp_zero = (q[0] < 0.06) or (q[4] < 0.03)
    ambiguous = False
    for c_alt, q_alt in sols[1:]:
        if c_alt < 1.10 * cost:
            p_alt = unpack(q_alt)
            tpa1, _ = component_peak(tuple(p_alt[0:4]), t[0], t[-1])
            tpa2, _ = component_peak(tuple(p_alt[4:8]), t[0], t[-1])
            if dt > 0 and abs((tpa2 - tpa1) - dt) > 0.20 * dt:
                ambiguous = True
                break
    if boundary or amp_zero or ambiguous or dt <= 0:
        return None
    return {"dt3": float(dt), "ri3": float(h2 / max(h1, 1e-12))}


# ---------------------------------------------------------------- 1ウィンドウ
MAX_3K_GROUPS = 6   # 3カーネルは1ウィンドウ最大6アンサンブルまで（コスト対策。中央値には十分）


def _fit_groups(seg: np.ndarray, good: list, n_ens: int, collect: dict,
                keys2: tuple, do_variants: bool = False, do_3k: bool = False,
                seed0: int = 0) -> None:
    """good 拍を n_ens 個ずつまとめて当てはめ、指標を collect に積む。"""
    for gi, k in enumerate(range(0, len(good) - n_ens + 1, n_ens)):
        y = ensemble_average([seg[a:b] for a, b in good[k:k + n_ens]])
        t = np.arange(len(y)) / FS
        try:
            fit = fit_beat(t, y)
        except Exception:
            continue
        if fit.get("ok", False):
            m = si_ri_from_fit(fit)
            if m["dt_s"] > 0:
                collect[keys2[0]].append(m["dt_s"])
                collect[keys2[1]].append(m["ri"])
                if do_variants:
                    v = variant_indices_from_fit(fit, t)
                    if v["dt_onset"] > 0:
                        collect["dt_onset"].append(v["dt_onset"])
                    collect["a_ratio"].append(v["a_ratio"])
                    collect["area_ratio"].append(v["area_ratio"])
        if do_3k and gi < MAX_3K_GROUPS:
            f3 = fit_beat3(t, y, seed=seed0 + gi)
            if f3 is not None:
                collect["dt3"].append(f3["dt3"])
                collect["ri3"].append(f3["ri3"])


def window_variants(pleth: np.ndarray, ecg: np.ndarray, t0: float) -> dict:
    """主解析で採用済みのウィンドウ t0 に対して変種指標を計算する。"""
    i0, i1 = int(t0 * FS), int((t0 + WIN_S) * FS)
    seg_p = np.nan_to_num(np.asarray(pleth[i0:i1], float))
    seg_e = np.nan_to_num(np.asarray(ecg[i0:i1], float))
    out = {"t0": t0}
    beats = segment_beats(seg_p, FS, ecg=seg_e)

    def flat_ok(a, b, thr):
        q = sqi(seg_p[a:b], FS)
        return (q["amp"] > 0) and (q["n_nan"] == 0) and (q["max_flat_run"] < thr * (b - a))

    col = {k: [] for k in ["dt", "ri", "dt_onset", "a_ratio", "area_ratio",
                           "dt3", "ri3", "dt_n2", "ri_n2", "dt_n4", "ri_n4",
                           "dt_sqi5", "ri_sqi5", "dt_sqi20", "ri_sqi20"]}

    # --- 基本セット（SQI 10%）: 主解析の再現＋派生＋3カーネル＋ノイズ目標± ---
    good = [(a, b) for a, b in beats if flat_ok(a, b, 0.10)]
    if len(good) >= 8:
        sigma = float(np.nanmedian([estimate_noise(seg_p[a:b]) for a, b in good]))
        n3, ok3 = required_ensemble_size(sigma)                    # 0.003（主解析）
        if ok3 and len(good) >= 2 * n3:
            _fit_groups(seg_p, good, n3, col, ("dt", "ri"),
                        do_variants=True, do_3k=True, seed0=int(t0))
        for target, keys in [(0.002, ("dt_n2", "ri_n2")), (0.004, ("dt_n4", "ri_n4"))]:
            n = int(np.ceil((sigma / target) ** 2))
            n = min(max(n, 4), 16)
            reachable = (sigma / np.sqrt(n)) <= target
            if reachable and len(good) >= 2 * n:
                _fit_groups(seg_p, good, n, col, keys)

    # --- SQI 変種（5% / 20%）: ノイズ目標は主解析の0.003 ---
    # 閾値がどの拍にも効かない場合は基本セットと同一なので再計算せずコピーする
    for thr, keys in [(0.05, ("dt_sqi5", "ri_sqi5")), (0.20, ("dt_sqi20", "ri_sqi20"))]:
        g = [(a, b) for a, b in beats if flat_ok(a, b, thr)]
        if g == good and col["dt"]:
            col[keys[0]] = list(col["dt"])
            col[keys[1]] = list(col["ri"])
            continue
        if len(g) < 8:
            continue
        sg = float(np.nanmedian([estimate_noise(seg_p[a:b]) for a, b in g]))
        n, ok = required_ensemble_size(sg)
        if ok and len(g) >= 2 * n:
            _fit_groups(seg_p, g, n, col, keys)

    for k, v in col.items():
        out[k] = float(np.median(v)) if len(v) >= 2 else np.nan
        out[f"n_{k}"] = len(v)
    return out


# ---------------------------------------------------------------- 症例・並列
def extract_case_variants(caseid: int) -> tuple:
    import pandas as pd
    outp = VFEAT / f"case_{caseid}.csv"
    metap = VFEAT / f"case_{caseid}_meta.json"
    if outp.exists() and metap.exists():
        try:
            if json.loads(metap.read_text(encoding="utf-8")).get("v") == META_V:
                return caseid, len(pd.read_csv(outp)), None
        except Exception:
            pass
    mainp = FEAT / f"case_{caseid}.csv"
    try:
        main = pd.read_csv(mainp)
    except Exception:
        return caseid, None, "主解析キャッシュなし"
    if len(main) < 12:
        return caseid, None, "主解析で不採用"
    import vitaldb
    wav = vitaldb.load_case(caseid, ["SNUADC/PLETH", "SNUADC/ECG_II"], 1 / FS)
    pleth = wav[:, 0].astype(np.float32)
    ecg = wav[:, 1].astype(np.float32)
    rows = [window_variants(pleth, ecg, float(t0)) for t0 in main["t0"]]
    df = pd.DataFrame(rows)
    VFEAT.mkdir(parents=True, exist_ok=True)
    df.to_csv(outp, index=False)
    metap.write_text(json.dumps({"v": META_V, "caseid": caseid,
                                 "n_windows": len(df)}), encoding="utf-8")
    return caseid, len(df), None


def _one(caseid):
    try:
        return extract_case_variants(caseid)
    except Exception as e:  # noqa: BLE001
        return caseid, None, f"失敗: {e}"


def main() -> None:
    import pandas as pd
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--limit", type=int, default=874)
    ap.add_argument("--jobs", type=int, default=1)
    args = ap.parse_args()

    tc = pd.read_csv(DATA / "target_cases.csv")
    ids = []
    for cid in tc["caseid"].astype(int):
        if len(ids) >= args.limit:
            break
        if (FEAT / f"case_{cid}.csv").exists():
            ids.append(cid)
    print(f"{len(ids)} 症例（主解析キャッシュあり）を処理します", flush=True)

    tally = Counter()
    if args.jobs > 1:
        from concurrent.futures import ProcessPoolExecutor, as_completed
        with ProcessPoolExecutor(max_workers=args.jobs) as ex:
            futs = {ex.submit(_one, c): c for c in ids}
            for n, fu in enumerate(as_completed(futs), 1):
                cid, nn, err = fu.result()
                tally["ok" if err is None else "skip"] += 1
                print(f"[{n}/{len(ids)}] caseid={cid}: "
                      + (f"skip（{err}）" if err else f"変種 {nn} ウィンドウ"), flush=True)
    else:
        for n, c in enumerate(ids, 1):
            cid, nn, err = _one(c)
            tally["ok" if err is None else "skip"] += 1
            print(f"[{n}/{len(ids)}] caseid={cid}: "
                  + (f"skip（{err}）" if err else f"変種 {nn} ウィンドウ"), flush=True)
    print(f"\n完了: ok {tally['ok']} / skip {tally['skip']}")
    print("次: python scripts/12_variants_stats.py")


if __name__ == "__main__":
    main()
