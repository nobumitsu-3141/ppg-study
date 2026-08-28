# -*- coding: utf-8 -*-
"""P0-3: VitalDB から1症例をダウンロードし、波形とPDA・PWTTの動作を確認する。

実行例:  python3 scripts/02_fetch_case.py 1
（引数=caseid。省略時は data/target_cases.csv の先頭症例）

やること:
 1. SNUADC/PLETH, SNUADC/ECG_II を 500Hz で取得
 2. 脈波を拍に切り、SQI 通過拍に PDA を適用して SI・RI を数拍分表示
 3. PWTT（R波→脈波立ち上がり）を数拍分表示
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from src.beats import (segment_beats, sqi, ensemble_average,  # noqa: E402
                       estimate_noise, required_ensemble_size)
from src.pda import fit_beat  # noqa: E402
from src.indices import si_ri_from_fit, pwtt_series, estimate_pleth_lag  # noqa: E402

FS = 500.0
TRACKS = ["SNUADC/PLETH", "SNUADC/ECG_II"]


def load(caseid: int) -> np.ndarray:
    import vitaldb  # pip install vitaldb
    return vitaldb.load_case(caseid, TRACKS, 1 / FS)


def main() -> None:
    if len(sys.argv) > 1:
        caseid = int(sys.argv[1])
    else:
        import pandas as pd
        tc = pd.read_csv(Path(__file__).resolve().parent.parent / "data" / "target_cases.csv")
        caseid = int(tc["caseid"].iloc[0])
    print(f"caseid = {caseid}, tracks = {TRACKS}")
    vals = load(caseid)
    pleth, ecg = vals[:, 0], vals[:, 1]
    print(f"samples: {len(pleth)} ({len(pleth)/FS/60:.1f} min), "
          f"pleth NaN率 {np.mean(np.isnan(pleth)):.1%}")

    # 波形が安定している10分目以降から5分を使う（要調整）
    i0 = int(10 * 60 * FS)
    seg_p = np.nan_to_num(pleth[i0:i0 + int(5 * 60 * FS)])
    seg_e = np.nan_to_num(ecg[i0:i0 + int(5 * 60 * FS)])

    # 心電図を基準に切る（極小値のみだと重複切痕を foot と誤検出して2倍に割れる）
    beats = segment_beats(seg_p, FS, ecg=seg_e)
    good = [(a, b) for a, b in beats if sqi(seg_p[a:b], FS)["ok"]]
    dur_min = len(seg_p) / FS / 60
    print(f"beats: {len(beats)} ({len(beats)/dur_min:.0f} 拍/分), "
          f"SQI通過: {len(good)} ({len(good)/max(len(beats),1):.0%})")
    from src.indices import detect_r_peaks
    n_r = len(detect_r_peaks(seg_e, FS))
    print(f"  心電図R波: {n_r} ({n_r/dur_min:.0f} 拍/分)  "
          f"→ 拍数の比 {len(beats)/max(n_r,1):.2f}（1.0付近なら健全）")
    sig = float(np.median([estimate_noise(seg_p[a:b]) for a, b in good[:60]])) if good else float("nan")
    n_ens, reachable = required_ensemble_size(sig)
    print(f"  相対ノイズ {sig:.4f} → アンサンブル {n_ens} 拍"
          f"{'' if reachable else '（★目標未達。本解析ではこのウィンドウを棄却）'}")

    # ノイズに応じた拍数で平均 → PDA。
    # 本解析(03)は60秒ウィンドウ内の全区間の中央値を使うので、ここでも全区間を集計する。
    dts, ris, n_try, n_ok = [], [], 0, 0
    for k in range(0, len(good) - n_ens + 1, n_ens):
        n_try += 1
        y = ensemble_average([seg_p[a:b] for a, b in good[k:k + n_ens]])
        t = np.arange(len(y)) / FS
        try:
            fit = fit_beat(t, y)
        except Exception:
            continue
        if not fit.get("ok", False):
            continue
        n_ok += 1
        m = si_ri_from_fit(fit, height_m=None)
        dts.append(m["dt_s"] * 1000)
        ris.append(m["ri"])
    print(f"  PDA: {n_try} 区間中 {n_ok} 区間が収束検算を通過 ({n_ok/max(n_try,1):.0%})")
    if dts:
        d, r = np.array(dts), np.array(ris)
        print(f"    ΔT 中央値 {np.median(d):.0f} ms "
              f"(IQR {np.percentile(d,25):.0f}–{np.percentile(d,75):.0f})")
        print(f"    RI 中央値 {np.median(r):.2f} "
              f"(IQR {np.percentile(r,25):.2f}–{np.percentile(r,75):.2f})"
              f"  → 本解析はこの中央値をウィンドウの値として使う")
        print(f"    先頭4区間: " + ", ".join(f"ΔT{a:.0f}/RI{b:.2f}" for a, b in zip(d[:4], r[:4])))
        if np.median(r) < 0.1 or np.median(r) > 1.0:
            print("    ★ RI が生理的範囲(0.1–1.0)の外。この症例は要検討")
    else:
        print("    ★ 収束した区間なし。この症例は解析対象から外す候補")

    lag = estimate_pleth_lag(ecg, pleth, FS)
    print(f"脈波チャネル遅延（症例全体から推定）: {lag*1000:.0f} ms"
          "  ※PWTTはこの遅延を含む。症例内Δでは相殺される")
    pw = pwtt_series(seg_e, seg_p, FS, lag=lag)
    if pw.size:
        print(f"PWTT: n={pw.size}, median={np.median(pw)*1000:.0f} ms "
              f"(IQR {np.percentile(pw,25)*1000:.0f}–{np.percentile(pw,75)*1000:.0f})")
    else:
        print("PWTT: 検出できず（R波検出パラメータの調整が必要）")


if __name__ == "__main__":
    main()
