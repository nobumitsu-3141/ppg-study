#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""脈波の立ち上がり系の特徴量を抽出し、ΔPWTT を説明できるかを試す（探索的）。

なぜこれを試すのか
------------------
主解析で ΔT・RI が ΔPWTT を説明できなかった一方、平均血圧は約3倍を説明した。
また心拍数を入れると説明割合が上がる。つまり PWTT の術中変動は心臓側
（前駆出期・変時性）に強く支配されている。

そこで発想を反転させる。**血管情報だけを純粋に取り出そうとするのではなく、
心臓側の影響も含む脈波形態を使う**。PWTT 自体が心臓側成分を含む以上、
心臓側も反映する指標のほうが PWTT の変動を追える可能性がある。

計算する特徴量（いずれも利得に依存しない形にする）
--------------------------------------------------
  rise_ms   立ち上がり時間（foot → 収縮期ピーク）[ms]
            純粋な時間量。振幅の正規化を受けても不変
  slope_n   最大立ち上がり勾配 ÷ 拍振幅 [1/s]
            比なので拍全体のスケーリングに不変。左室 dP/dt と動脈特性を反映
  amp_rel   拍振幅 ÷ 窓内中央振幅（症例内の相対振幅）
            利得が症例内で一定なら末梢血管トーンを反映しうる（PIの代用・要注意）
  ampbase   拍振幅 ÷ 拍の基線値（PI の粗い代用）
            **注意**: VitalDBのPLETHは0〜100の表示スケールで真のDC（組織吸光）
            ではないため、本来のPIとは異なる。参考値としてのみ扱う

位置づけ: SAP v0.3 凍結後の探索的解析。主解析には一切影響しない。
出力は data/features_slope/ に別置きする。

使い方:
    python scripts/14_slope_features.py --limit 874 --jobs 4     # 抽出＋集計
    python scripts/14_slope_features.py --stats-only             # 集計のみ
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.beats import segment_beats, sqi   # noqa: E402
from src.models import _rel                # noqa: E402

FS = 500.0
WIN_S = 60.0
DATA = Path(__file__).resolve().parent.parent / "data"
FEAT = DATA / "features"
SFEAT = DATA / "features_slope"
META_V = 1
MIN_WINDOWS = 12


def beat_shape(y: np.ndarray, fs: float) -> dict | None:
    """1拍から立ち上がり系の指標を出す。拍は foot 始まりで切られている。"""
    y = np.asarray(y, float)
    if y.size < int(0.25 * fs):
        return None
    # 収縮期ピークは前半で探す（後半の反射波ピークを拾わないため）
    half = max(int(0.6 * y.size), 5)
    ip = int(np.argmax(y[:half]))
    if ip < 2:
        return None
    amp = float(np.max(y[:half]) - y[0])
    if not np.isfinite(amp) or amp <= 0:
        return None
    d = np.diff(y[:ip + 1]) * fs           # 立ち上がり区間の勾配
    if d.size == 0:
        return None
    base = float(np.median(y))
    return {
        "rise_ms": 1000.0 * ip / fs,
        "slope_n": float(np.max(d)) / amp,       # [1/s]・利得不変
        "amp": amp,
        "ampbase": amp / base if base > 1e-6 else np.nan,
    }


def window_shape(pleth: np.ndarray, ecg: np.ndarray, t0: float) -> dict:
    i0, i1 = int(t0 * FS), int((t0 + WIN_S) * FS)
    seg_p = np.nan_to_num(np.asarray(pleth[i0:i1], float))
    seg_e = np.nan_to_num(np.asarray(ecg[i0:i1], float))
    out = {"t0": t0}
    beats = segment_beats(seg_p, FS, ecg=seg_e)
    vals = {k: [] for k in ["rise_ms", "slope_n", "amp", "ampbase"]}
    for a, b in beats:
        if not sqi(seg_p[a:b], FS)["ok"]:
            continue
        m = beat_shape(seg_p[a:b], FS)
        if m is None:
            continue
        for k in vals:
            if np.isfinite(m[k]):
                vals[k].append(m[k])
    for k, v in vals.items():
        out[k] = float(np.median(v)) if len(v) >= 5 else np.nan
    out["n_beats"] = len(vals["rise_ms"])
    return out


def extract_case(caseid: int) -> tuple:
    outp = SFEAT / f"case_{caseid}.csv"
    metap = SFEAT / f"case_{caseid}_meta.json"
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
    if len(main) < MIN_WINDOWS:
        return caseid, None, "主解析で不採用"
    import vitaldb
    wav = vitaldb.load_case(caseid, ["SNUADC/PLETH", "SNUADC/ECG_II"], 1 / FS)
    pleth = wav[:, 0].astype(np.float32)
    ecg = wav[:, 1].astype(np.float32)
    df = pd.DataFrame([window_shape(pleth, ecg, float(t)) for t in main["t0"]])
    SFEAT.mkdir(parents=True, exist_ok=True)
    df.to_csv(outp, index=False)
    metap.write_text(json.dumps({"v": META_V, "caseid": caseid, "n": len(df)}),
                     encoding="utf-8")
    return caseid, len(df), None


def _one(cid):
    try:
        return extract_case(cid)
    except Exception as e:  # noqa: BLE001
        return cid, None, f"失敗: {e}"


def r2_of(X, y, keys):
    M = np.column_stack([X[k] for k in keys] + [np.ones(y.size)])
    coef, *_ = np.linalg.lstsq(M, y, rcond=None)
    sse = float(np.sum((y - M @ coef) ** 2))
    sst = float(np.sum((y - y.mean()) ** 2))
    return 1.0 - sse / max(sst, 1e-12), {k: float(coef[i]) for i, k in enumerate(keys)}


def stats() -> None:
    rows_x, rows_y = {k: [] for k in
                      ["rise", "slope", "ampbase", "dt", "ri", "map", "hr"]}, []
    n_case = 0
    for metap in sorted(SFEAT.glob("case_*_meta.json")):
        cid = json.loads(metap.read_text(encoding="utf-8"))["caseid"]
        sp, mp = SFEAT / f"case_{cid}.csv", FEAT / f"case_{cid}.csv"
        if not (sp.exists() and mp.exists()):
            continue
        try:
            s, m = pd.read_csv(sp), pd.read_csv(mp)
        except Exception:
            continue
        j = m.merge(s, on="t0", how="inner")
        j = j.dropna(subset=["pwtt", "si", "ri", "map", "hr", "rise_ms", "slope_n"])
        if len(j) < MIN_WINDOWS:
            continue
        n_case += 1
        rows_x["rise"].append(_rel(j["rise_ms"].to_numpy(float)))
        rows_x["slope"].append(_rel(j["slope_n"].to_numpy(float)))
        rows_x["ampbase"].append(_rel(j["ampbase"].to_numpy(float))
                                 if "ampbase" in j else np.zeros(len(j)))
        rows_x["dt"].append(_rel(j["si"].to_numpy(float)))
        rows_x["ri"].append(_rel(j["ri"].to_numpy(float)))
        rows_x["map"].append(_rel(j["map"].to_numpy(float)))
        rows_x["hr"].append(_rel(j["hr"].to_numpy(float)))
        rows_y.append(_rel(j["pwtt"].to_numpy(float)))
    if n_case < 10:
        print(f"症例が {n_case} 例しかありません。抽出の完了後に実行してください。")
        return
    X = {k: np.concatenate(v) for k, v in rows_x.items()}
    y = np.concatenate(rows_y)
    m = np.isfinite(y)
    for v in X.values():
        m &= np.isfinite(v)
    X = {k: v[m] for k, v in X.items()}
    y = y[m]
    print(f"\n=== 立ち上がり系特徴量による ΔPWTT の説明（探索的） ===")
    print(f"症例 {n_case}・ウィンドウ {y.size:,}\n")
    print(f"{'説明変数':<34}{'r²':>9}{'係数':>12}")
    print("-" * 56)
    singles = [
        (["dt"], "ΔSI%（主解析の指標）"),
        (["ri"], "ΔRI%（主解析の指標）"),
        (["rise"], "Δ立ち上がり時間%"),
        (["slope"], "Δ正規化立ち上がり勾配%"),
        (["ampbase"], "Δ振幅/基線%（PI代用・要注意）"),
        (["hr"], "Δ心拍数%"),
        (["map"], "Δ平均血圧%"),
    ]
    for keys, label in singles:
        r2, c = r2_of(X, y, keys)
        print(f"{label:<34}{r2:>9.4f}{c[keys[0]]:>+12.4f}")
    print()
    combos = [
        (["dt", "ri"], "血管指標のみ（主解析）"),
        (["rise", "slope"], "立ち上がり系のみ"),
        (["dt", "ri", "rise", "slope"], "血管指標 ＋ 立ち上がり系"),
        (["rise", "slope", "hr"], "立ち上がり系 ＋ 心拍数"),
        (["dt", "ri", "rise", "slope", "hr", "map"], "全部"),
    ]
    print(f"{'組み合わせ':<34}{'r²':>9}")
    print("-" * 44)
    for keys, label in combos:
        r2, _ = r2_of(X, y, keys)
        print(f"{label:<34}{r2:>9.4f}")
    print("\n読み方: 立ち上がり系が血管指標より大きな r² を示すなら、")
    print("        『心臓側も含む形態指標のほうがPWTTを追える』ことになり、")
    print("        補正の入力を選び直す根拠になる。")
    print("        ただし相関は因果ではなく、PWTTと同じ心臓側要因を")
    print("        共有しているだけの可能性がある（考察で明示すること）。")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--limit", type=int, default=874)
    ap.add_argument("--jobs", type=int, default=1)
    ap.add_argument("--stats-only", action="store_true")
    args = ap.parse_args()

    if not args.stats_only:
        tc = pd.read_csv(DATA / "target_cases.csv")
        ids = [int(c) for c in tc["caseid"] if (FEAT / f"case_{c}.csv").exists()][:args.limit]
        print(f"{len(ids)} 症例を処理します", flush=True)
        if args.jobs > 1:
            from concurrent.futures import ProcessPoolExecutor, as_completed
            with ProcessPoolExecutor(max_workers=args.jobs) as ex:
                futs = {ex.submit(_one, c): c for c in ids}
                for n, fu in enumerate(as_completed(futs), 1):
                    cid, nn, err = fu.result()
                    if n % 25 == 0 or err:
                        print(f"[{n}/{len(ids)}] caseid={cid}: "
                              + (f"skip（{err}）" if err else f"{nn} 窓"), flush=True)
        else:
            for n, c in enumerate(ids, 1):
                cid, nn, err = _one(c)
                if n % 25 == 0 or err:
                    print(f"[{n}/{len(ids)}] caseid={cid}: "
                          + (f"skip（{err}）" if err else f"{nn} 窓"), flush=True)
    stats()


if __name__ == "__main__":
    main()
