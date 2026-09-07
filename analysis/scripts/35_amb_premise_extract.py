#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""早期振幅比 Am_b/Am_p1 の軽量抽出（探索的解析。設計は docs/research/sap_1_amb_exploratory_v0.md）。

何をするか
----------
研究1 で採用済みのウィンドウ（`features/case_*.csv` の t0）と**同じ時刻・同じ前処理**で、
Am_b/Am_p1（Hellqvist 2024）だけを計算する。**当てはめ（PDA）は一切行わない。**

設計上の要点（設計書 §4・§5）
--------------------------
- 指標は `src/pda2.py` の `early_features()`。研究0・32番・34番で使ったものと同一の関数である。
- 前処理は研究1（SAP §3.1）と同じ: SQI v0（振幅>0・NaN なし・同一値連続 <10%）、
  拍ごとのノイズから決める適応アンサンブル（目標 0.003・4〜16 拍・上限で未達なら棄却）。
- 採否は 32番と同じく 0 < Am_b/Am_p1 ≤ 1.5。1 ウィンドウで 2 群以上採択されたら中央値を採る。
- **研究1 が採用したウィンドウの上でのみ計算する**ので、研究1 が「PDA ok ≥ 2 区間」で
  落としたウィンドウは復元されない（設計書 §5 の但し書き。限界として報告する）。

使い方:
    python scripts/35_amb_premise_extract.py --selftest
    nohup caffeinate -i python scripts/35_amb_premise_extract.py --limit 874 --jobs 8 \
      > amb_run.log 2>&1 &
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from collections import Counter
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.beats import (segment_beats, sqi, ensemble_average,      # noqa: E402
                       estimate_noise, required_ensemble_size)
import src.pda2 as pda2                                            # noqa: E402

FS = 500.0
WIN_S = 60.0
SQI_FLAT = 0.10          # 研究1 と同じ（同一値連続の上限割合）
MIN_GOOD_BEATS = 8       # 研究1 と同じ
AMB_LO, AMB_HI = 0.0, 1.5   # 32番と同じ採択範囲
MIN_GROUPS = 2           # 1 ウィンドウで値を出すのに要する採択群数（11番の慣行）

DATA = Path(__file__).resolve().parent.parent / "data"
FEAT = DATA / "features"
AFEAT = DATA / "features_amb"
META_V = 1


# ---------------------------------------------------------------- 1 群
def amb_of_beat(y: np.ndarray, fs: float = FS) -> float:
    """平均拍 1 つから Am_b/Am_p1 を返す。求まらなければ NaN。

    32番・34番と同じ手順（pda2.preprocess → pda2.early_features）。比なので
    振幅の正規化は約分され、基線の除去だけが効く。
    """
    t = np.arange(len(y)) / fs
    ys, _amp = pda2.preprocess(t, np.asarray(y, float), fs)
    if ys is None:
        return float("nan")
    ef = pda2.early_features(t, ys)
    a = float(ef["amb_amp1"])
    return a if np.isfinite(a) and AMB_LO < a <= AMB_HI else float("nan")


# ---------------------------------------------------------------- 1 ウィンドウ
def window_amb(pleth: np.ndarray, ecg: np.ndarray, t0: float) -> dict:
    """研究1 が採用したウィンドウ t0 について Am_b/Am_p1 を計算する。

    返す列:
      amb      採択群の中央値（群が MIN_GROUPS 未満なら NaN）
      n_amb    採択された群の数
      n_group  作れた群の数（採否の前）
      n_good   SQI を通った拍数
      sigma    拍のノイズの中央値
      n_ens    そのウィンドウで使ったアンサンブル拍数
      why      値が出なかった理由（出たときは空）
    """
    i0, i1 = int(t0 * FS), int((t0 + WIN_S) * FS)
    seg_p = np.nan_to_num(np.asarray(pleth[i0:i1], float))
    seg_e = np.nan_to_num(np.asarray(ecg[i0:i1], float))
    out = {"t0": float(t0), "amb": np.nan, "n_amb": 0, "n_group": 0,
           "n_good": 0, "sigma": np.nan, "n_ens": 0, "why": ""}

    beats = segment_beats(seg_p, FS, ecg=seg_e)

    def flat_ok(a, b):
        q = sqi(seg_p[a:b], FS)
        return (q["amp"] > 0) and (q["n_nan"] == 0) and \
               (q["max_flat_run"] < SQI_FLAT * (b - a))

    good = [(a, b) for a, b in beats if flat_ok(a, b)]
    out["n_good"] = len(good)
    if len(good) < MIN_GOOD_BEATS:
        out["why"] = "sqi_beats"
        return out

    sigma = float(np.nanmedian([estimate_noise(seg_p[a:b]) for a, b in good]))
    out["sigma"] = sigma
    n_ens, ok = required_ensemble_size(sigma)
    out["n_ens"] = int(n_ens)
    if not ok:
        out["why"] = "noise_target"          # 上限拍数でも目標に届かない（研究1 と同じ棄却）
        return out
    if len(good) < 2 * n_ens:
        out["why"] = "few_groups"
        return out

    vals = []
    for k in range(0, len(good) - n_ens + 1, n_ens):
        out["n_group"] += 1
        y = ensemble_average([seg_p[a:b] for a, b in good[k:k + n_ens]])
        a = amb_of_beat(y)
        if np.isfinite(a):
            vals.append(a)
    out["n_amb"] = len(vals)
    if len(vals) >= MIN_GROUPS:
        out["amb"] = float(np.median(vals))
    else:
        out["why"] = "amb_undetected"
    return out


# ---------------------------------------------------------------- 症例
def extract_case_amb(caseid: int) -> tuple:
    import pandas as pd
    outp = AFEAT / f"case_{caseid}.csv"
    metap = AFEAT / f"case_{caseid}_meta.json"
    if outp.exists() and metap.exists():
        try:
            if json.loads(metap.read_text(encoding="utf-8")).get("v") == META_V:
                return caseid, len(pd.read_csv(outp)), None
        except Exception:
            pass
    try:
        main = pd.read_csv(FEAT / f"case_{caseid}.csv")
    except Exception:
        return caseid, None, "主解析キャッシュなし"
    if len(main) < 12:
        return caseid, None, "主解析で不採用"

    import vitaldb
    wav = vitaldb.load_case(caseid, ["SNUADC/PLETH", "SNUADC/ECG_II"], 1 / FS)
    pleth = wav[:, 0].astype(np.float32)
    ecg = wav[:, 1].astype(np.float32)
    rows = [window_amb(pleth, ecg, float(t0)) for t0 in main["t0"]]
    df = pd.DataFrame(rows)
    AFEAT.mkdir(parents=True, exist_ok=True)
    df.to_csv(outp, index=False)
    metap.write_text(json.dumps({
        "v": META_V, "caseid": caseid, "n_windows": len(df),
        "n_amb_windows": int(df["amb"].notna().sum()),
        "pda2_version": pda2.__dict__.get("VERSION", ""),
    }), encoding="utf-8")
    return caseid, len(df), None


def _one(caseid):
    try:
        return extract_case_amb(caseid)
    except Exception as e:      # noqa: BLE001
        return caseid, None, f"失敗: {e}"


# ---------------------------------------------------------------- 自己検査
def _synth_window(fs: float = FS, n_beats: int = 20, preset: str = "clear_notch",
                  noise: float = 0.01, seed: int = 0) -> tuple:
    """合成の 60 秒ウィンドウ（脈波と、その足に合わせた矩形 ECG）を作る。"""
    from src.synth import make_beat
    rng = np.random.default_rng(seed)
    p, e = [], []
    for i in range(n_beats):
        _t, y, _tr = make_beat(preset, fs=fs, T=0.9, noise=noise, drift=0.0, seed=seed + i)
        r = np.zeros_like(y)
        r[2] = 1.0                                    # 拍頭に R 波を置く
        p.append(y)
        e.append(r)
    pleth = np.concatenate(p)
    ecg = np.concatenate(e)
    need = int(WIN_S * fs)
    if len(pleth) < need:                             # 60 秒に足りなければ繰り返す
        k = int(np.ceil(need / len(pleth)))
        pleth = np.tile(pleth, k)
        ecg = np.tile(ecg, k)
    pleth = pleth[:need] + 1e-6 * rng.standard_normal(need)
    return pleth.astype(np.float32), ecg[:need].astype(np.float32)


def selftest() -> int:
    ok = [0, 0]

    def rep(name, cond, detail=""):
        ok[1] += 1
        ok[0] += bool(cond)
        print(f"  [{'PASS' if cond else 'FAIL'}] {name}" + (f"  {detail}" if detail else ""))

    print("35番 自己検査")
    print("-" * 74)

    # --- 1拍レベル ---
    from src.synth import make_beat
    _t, y, _tr = make_beat("clear_notch", fs=FS, T=0.9, noise=0.0, drift=0.0, seed=0)
    a = amb_of_beat(y)
    rep("合成拍から Am_b/Am_p1 が求まり、0 と 1.5 の間に入る", np.isfinite(a) and 0 < a <= 1.5, f"amb={a:.4f}")

    a_scaled = amb_of_beat(3.7 * y)
    rep("振幅を定数倍しても値が変わらない（比なので約分される）",
        np.isfinite(a_scaled) and abs(a_scaled - a) < 1e-9, f"{a:.6f} 対 {a_scaled:.6f}")

    a_offset = amb_of_beat(y + 5.0)
    rep("基線を平行移動しても値が変わらない（前処理で除去される）",
        np.isfinite(a_offset) and abs(a_offset - a) < 1e-6, f"{a:.6f} 対 {a_offset:.6f}")

    rep("定数波形では値が出ない", not np.isfinite(amb_of_beat(np.full(450, 2.0))))
    rep("NaN を含む波形では値が出ない",
        not np.isfinite(amb_of_beat(np.concatenate([y[:100], [np.nan], y[101:]]))))

    # 型による向き: dn_less（切痕が浅い＝より硬い側）のほうが比が小さい
    _t2, y2, _ = make_beat("dn_less", fs=FS, T=0.9, noise=0.0, drift=0.0, seed=0)
    a2 = amb_of_beat(y2)
    rep("切痕の浅い波形のほうが早期振幅比が小さい（Hellqvist の向き）",
        np.isfinite(a2) and a2 < a, f"clear_notch={a:.4f} 対 dn_less={a2:.4f}")

    # --- ウィンドウレベル ---
    pleth, ecg = _synth_window(seed=1)
    w = window_amb(pleth, ecg, 0.0)
    rep("合成ウィンドウで値が出る", np.isfinite(w["amb"]),
        f"amb={w['amb']:.4f} n_amb={w['n_amb']}/{w['n_group']} n_good={w['n_good']} n_ens={w['n_ens']}")
    rep("採択群数が要求（2 群）以上", w["n_amb"] >= MIN_GROUPS, f"n_amb={w['n_amb']}")
    rep("値が出たウィンドウでは why が空", w["why"] == "", f"why='{w['why']}'")

    flat = np.zeros(int(WIN_S * FS), dtype=np.float32)
    wf = window_amb(flat, ecg, 0.0)
    rep("定数ウィンドウは棄却され、理由が残る",
        (not np.isfinite(wf["amb"])) and wf["why"] != "", f"why='{wf['why']}'")

    noisy, ecg2 = _synth_window(noise=0.35, seed=2)
    wn = window_amb(noisy, ecg2, 0.0)
    rep("雑音の大きいウィンドウは棄却されるか、拍数が増える（研究1 と同じ適応則）",
        (not np.isfinite(wn["amb"])) or wn["n_ens"] > w["n_ens"],
        f"why='{wn['why']}' n_ens={wn['n_ens']}（対照 {w['n_ens']}）")

    # 硬さを振ったウィンドウで、ウィンドウ中央値が拍の向きを保つ
    p_soft, e_soft = _synth_window(preset="clear_notch", seed=3)
    p_stiff, e_stiff = _synth_window(preset="dn_less", seed=3)
    ws = window_amb(p_soft, e_soft, 0.0)["amb"]
    wh = window_amb(p_stiff, e_stiff, 0.0)["amb"]
    rep("ウィンドウ中央値でも硬い側のほうが小さい",
        np.isfinite(ws) and np.isfinite(wh) and wh < ws, f"{ws:.4f} 対 {wh:.4f}")

    print("-" * 74)
    print(f"{ok[0]}/{ok[1]} " + ("ALL PASS" if ok[0] == ok[1] else "**FAIL あり**"))
    return 0 if ok[0] == ok[1] else 1


# ---------------------------------------------------------------- main
def main() -> int:
    import pandas as pd
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--limit", type=int, default=874)
    ap.add_argument("--jobs", type=int, default=1)
    ap.add_argument("--selftest", action="store_true")
    args = ap.parse_args()
    if args.selftest:
        return selftest()

    tc = pd.read_csv(DATA / "target_cases.csv")
    ids = []
    for cid in tc["caseid"].astype(int):
        if len(ids) >= args.limit:
            break
        if (FEAT / f"case_{cid}.csv").exists():
            ids.append(cid)
    print(f"{len(ids)} 症例（研究1 のキャッシュあり）を処理します", flush=True)
    print("当てはめは行いません（I/O 律速）", flush=True)

    t_start = time.time()
    tally = Counter()
    done = 0
    if args.jobs > 1:
        from concurrent.futures import ProcessPoolExecutor, as_completed
        with ProcessPoolExecutor(max_workers=args.jobs) as ex:
            futs = {ex.submit(_one, c): c for c in ids}
            for fu in as_completed(futs):
                cid, nn, err = fu.result()
                done += 1
                tally["ok" if err is None else "skip"] += 1
                el = time.time() - t_start
                eta = el / done * (len(ids) - done)
                print(f"[{done}/{len(ids)}] caseid={cid}: "
                      + (f"skip（{err}）" if err else f"{nn} ウィンドウ")
                      + f"　経過 {el/60:.1f} 分 / 残り {eta/60:.1f} 分", flush=True)
    else:
        for c in ids:
            cid, nn, err = _one(c)
            done += 1
            tally["ok" if err is None else "skip"] += 1
            el = time.time() - t_start
            eta = el / done * (len(ids) - done)
            print(f"[{done}/{len(ids)}] caseid={cid}: "
                  + (f"skip（{err}）" if err else f"{nn} ウィンドウ")
                  + f"　経過 {el/60:.1f} 分 / 残り {eta/60:.1f} 分", flush=True)

    print(f"\n完了: ok {tally['ok']} / skip {tally['skip']}　"
          f"所要 {(time.time()-t_start)/60:.1f} 分", flush=True)
    print(f"出力: {AFEAT}", flush=True)
    print("次は 36_amb_premise_stats.py で集計する", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
