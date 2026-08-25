# -*- coding: utf-8 -*-
"""Phase 2〜5: VitalDB実データでの本解析ランナー（v0）。

★ 実行は P0-2（倫理委員会の該当性照会への回答確認）を通過してから。Macで実行する。
   クラウドセッションからは vitaldb.net に接続できない。

実行例:
  python3 scripts/03_run_analysis.py                 # 先頭20例でパイロット
  python3 scripts/03_run_analysis.py --limit 100     # 例数を増やす
  python3 scripts/03_run_analysis.py --device Vigileo  # 参照CO装置を固定
  python3 scripts/03_run_analysis.py --stats-only    # 抽出済み特徴量から統計だけ再計算

流れ（1症例あたり）:
  1. SNUADC/PLETH + SNUADC/ECG_II（500Hz）と 参照CO（1s）を取得
  2. 60秒ウィンドウごとに:
       脈波→拍切り出し→SQI→4拍アンサンブル→PDA→ΔT・RI・SI（中央値）
       ECG＋脈波→PWTT（中央値）, R-R→HR, 参照CO（中央値）
  3. data/features/case_{id}.csv にキャッシュ（再実行時はフェッチ省略）
全症例の特徴量が揃ったら:
  4. models.crossval（症例単位5-fold, 較正=各症例の初回ウィンドウ）
  5. stats: ΔPE ブートストラップCI・Bland-Altman・4象限concordance
     （tests/test_pipeline_synthetic.py と同じ機構・同じ出力形式）

注意:
  - SQI閾値・ウィンドウ採否基準は v0 仮置き。Phase 2 で実データを見て確定し、
    確定値を docs/research/sap_v0.md に固定してから本解析（Phase 5）を回す。
  - 1症例あたりメモリ数百MB（数時間×500Hz×2ch）。float32で保持する。
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from src.beats import segment_beats, sqi, ensemble_average  # noqa: E402
from src.pda import fit_beat  # noqa: E402
from src.indices import si_ri_from_fit, pwtt_series, detect_r_peaks  # noqa: E402
from src.models import crossval  # noqa: E402
from src.stats import bootstrap_diff_ci, bland_altman, concordance_4q  # noqa: E402

DATA = Path(__file__).resolve().parent.parent / "data"
FEAT = DATA / "features"
FS = 500.0
WIN_S = 60.0                      # 特徴量ウィンドウ長 [s]
DEVICE_PRIORITY = ["Vigileo", "EV1000", "Vigilance", "CardioQ"]
MIN_WINDOWS = 12                  # 症例採用に必要な有効ウィンドウ数（較正1+評価11以上）


# ---------------------------------------------------------------- 特徴量抽出
def pick_device(row, forced: str | None) -> str | None:
    """target_cases.csv の保有フラグから参照CO装置を1つ選ぶ。"""
    if forced:
        return forced if row.get(f"co_{forced}", False) else None
    for dev in DEVICE_PRIORITY:
        if row.get(f"co_{dev}", False):
            return dev
    return None


def window_features(pleth: np.ndarray, ecg: np.ndarray, co: np.ndarray,
                    co_t: np.ndarray, t0: float, height_m: float) -> dict | None:
    """1ウィンドウ分の {pwtt, si, ri, hr, co_ref} を返す。品質不足なら None。"""
    i0, i1 = int(t0 * FS), int((t0 + WIN_S) * FS)
    seg_p = np.nan_to_num(np.asarray(pleth[i0:i1], float))
    seg_e = np.nan_to_num(np.asarray(ecg[i0:i1], float))
    if seg_p.size < int(WIN_S * FS) * 0.9 or not np.any(seg_p):
        return None

    # --- SI・RI: SQI通過拍を4拍ずつアンサンブル→PDA（ok解のみ採用） ---
    beats = segment_beats(seg_p, FS)
    good = [(a, b) for a, b in beats if sqi(seg_p[a:b], FS)["ok"]]
    if len(good) < 8:                       # 最低2アンサンブル分
        return None
    dts, ris = [], []
    for k in range(0, len(good) - 3, 4):
        y = ensemble_average([seg_p[a:b] for a, b in good[k:k + 4]])
        t = np.arange(len(y)) / FS
        try:
            fit = fit_beat(t, y)
        except Exception:
            continue
        if not fit.get("ok", False):
            continue
        m = si_ri_from_fit(fit, height_m=height_m)
        if m["dt_s"] > 0:
            dts.append(m["dt_s"])
            ris.append(m["ri"])
    if len(dts) < 2:
        return None
    dt_med = float(np.median(dts))
    si = height_m / dt_med
    ri = float(np.median(ris))

    # --- PWTT・HR ---
    pw = pwtt_series(seg_e, seg_p, FS)
    if pw.size < 10:
        return None
    r = detect_r_peaks(seg_e, FS)
    if r.size < 20:
        return None
    rr = np.diff(r) / FS
    rr = rr[(rr > 0.3) & (rr < 1.5)]
    if rr.size < 10:
        return None
    hr = 60.0 / float(np.median(rr))

    # --- 参照CO（ウィンドウ内中央値） ---
    m_co = (co_t >= t0) & (co_t < t0 + WIN_S) & np.isfinite(co) & (co > 0.5) & (co < 20)
    if m_co.sum() < 5:
        return None
    return {"t0": t0, "pwtt": float(np.median(pw)), "si": float(si), "ri": ri,
            "hr": hr, "co_ref": float(np.median(co[m_co]))}


def extract_case(caseid: int, device: str, height_m: float):
    """1症例の特徴量CSVを作る（キャッシュ済みならスキップ）。"""
    import pandas as pd
    out = FEAT / f"case_{caseid}.csv"
    if out.exists():
        return pd.read_csv(out)
    import vitaldb  # pip install vitaldb
    wav = vitaldb.load_case(caseid, ["SNUADC/PLETH", "SNUADC/ECG_II"], 1 / FS)
    pleth = wav[:, 0].astype(np.float32)
    ecg = wav[:, 1].astype(np.float32)
    co = vitaldb.load_case(caseid, [f"{device}/CO"], 1).ravel().astype(np.float32)
    co_t = np.arange(co.size, dtype=np.float32)          # 1s間隔
    dur = len(pleth) / FS
    rows = []
    for t0 in np.arange(0, dur - WIN_S, WIN_S):
        f = window_features(pleth, ecg, co, co_t, float(t0), height_m)
        if f is not None:
            rows.append(f)
    df = pd.DataFrame(rows)
    FEAT.mkdir(parents=True, exist_ok=True)
    df.to_csv(out, index=False)
    return df


# ---------------------------------------------------------------- 統計
def report(cases: list[dict]) -> None:
    """合成テストと同一の機構・同一の出力形式で結果を出す。"""
    res = crossval(cases, n_folds=5, seed=0)
    s = bootstrap_diff_ci(res, seed=0)
    print("\n== 結果（症例単位5-fold CV, 較正=初回ウィンドウ） ==")
    print(f"症例数: {len(cases)}  総ウィンドウ数: {sum(len(c['windows']['co_ref']) for c in cases)}")
    print(f"PE 対照(PWTT型) 中央値 : {s['pe_ctrl_median']:.1f}%")
    print(f"PE 提案(K(SI,RI)) 中央値: {s['pe_prop_median']:.1f}%")
    print(f"ΔPE(提案−対照) 平均 {s['diff_mean']:+.1f}%  [95%CI {s['ci_low']:+.1f}, {s['ci_high']:+.1f}]"
          f"  → {'有意な改善' if s['significant_improvement'] else '有意差なし'}")
    all_ref = np.concatenate([r["co_ref"] for r in res])
    all_prop = np.concatenate([r["est_prop"] for r in res])
    ba = bland_altman(all_prop, all_ref)
    d_est = np.concatenate([np.diff(r["est_prop"]) for r in res])
    d_ref = np.concatenate([np.diff(r["co_ref"]) for r in res])
    print(f"Bland-Altman(提案): bias {ba['bias']:+.2f} L/min "
          f"(LoA {ba['loa_low']:+.2f}..{ba['loa_high']:+.2f})")
    print(f"4象限concordance(提案, 除外帯0.5 L/min): {concordance_4q(d_est, d_ref):.2f}")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=20, help="処理する症例数（先頭から）")
    ap.add_argument("--device", choices=DEVICE_PRIORITY, default=None,
                    help="参照CO装置を固定（既定: Vigileo→EV1000→…の優先順）")
    ap.add_argument("--stats-only", action="store_true",
                    help="フェッチせず data/features/ のキャッシュだけで統計を出す")
    args = ap.parse_args()

    tc_path = DATA / "target_cases.csv"
    if not tc_path.exists():
        print("data/target_cases.csv がありません。\n"
              "先に scripts/00_download_lists.py と scripts/01_track_inventory.py を実行してください。\n"
              "（P0-2: 倫理委員会の回答確認後・Mac上で）")
        raise SystemExit(1)
    import pandas as pd
    tc = pd.read_csv(tc_path)
    demo = pd.read_csv(DATA / "cases.csv")[["caseid", "height"]].set_index("caseid")

    cases = []
    n_try = 0
    for _, row in tc.iterrows():
        if n_try >= args.limit:
            break
        caseid = int(row["caseid"])
        dev = pick_device(row, args.device)
        if dev is None:
            continue
        h_cm = float(demo["height"].get(caseid, np.nan))
        if not np.isfinite(h_cm) or h_cm < 100:
            continue
        n_try += 1
        if args.stats_only:
            f = FEAT / f"case_{caseid}.csv"
            if not f.exists():
                continue
            df = pd.read_csv(f)
        else:
            print(f"[{n_try}/{args.limit}] caseid={caseid} device={dev} ...", flush=True)
            try:
                df = extract_case(caseid, dev, h_cm / 100.0)
            except Exception as e:
                print(f"  skip（取得/抽出失敗: {e}）")
                continue
        if len(df) < MIN_WINDOWS:
            print(f"  skip（有効ウィンドウ {len(df)} < {MIN_WINDOWS}）")
            continue
        cases.append({
            "caseid": caseid, "height": h_cm / 100.0,
            "windows": {k: df[k].to_numpy(float) for k in ["pwtt", "si", "ri", "hr", "co_ref"]},
            "device": dev,
        })
        print(f"  ok（有効ウィンドウ {len(df)}）")

    if len(cases) < 10:
        print(f"\n解析可能な症例が {len(cases)} 例しかありません（最低10例）。--limit を増やすか基準を見直してください。")
        raise SystemExit(1)
    report(cases)


if __name__ == "__main__":
    main()
