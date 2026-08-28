# -*- coding: utf-8 -*-
"""Phase 2〜5: VitalDB実データでの本解析ランナー（v0）。

GATE P0-2（倫理委員会の該当性照会）は 2026-08-28 に通過済み（審査不要との回答）。
Macで実行する — クラウドセッションからは vitaldb.net に接続できない。

実行例:
  python3 scripts/03_run_analysis.py                 # 先頭20例でパイロット
  python3 scripts/03_run_analysis.py --limit 100     # 例数を増やす
  python3 scripts/03_run_analysis.py --device Vigileo  # 参照CO装置を固定
  python3 scripts/03_run_analysis.py --stats-only    # 抽出済み特徴量から統計だけ再計算

流れ（1症例あたり）:
  1. SNUADC/PLETH + SNUADC/ECG_II + SNUADC/ART（500Hz）と 参照CO（1s）を取得
  2. 60秒ウィンドウごとに:
       脈波→拍切り出し→SQI→適応拍数アンサンブル→PDA→ΔT・RI・SI（中央値）
       ECG＋脈波→PWTT（中央値）, R-R→HR, 動脈圧→MAP（平均）, 参照CO（中央値）
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
from src.beats import (segment_beats, sqi, ensemble_average,  # noqa: E402
                       estimate_noise, required_ensemble_size)
from src.pda import fit_beat  # noqa: E402
from src.indices import si_ri_from_fit, pwtt_series, detect_r_peaks  # noqa: E402
from src.models import crossval, premise_test, incremental_value  # noqa: E402
from src.stats import bootstrap_diff_ci, bland_altman, concordance_4q  # noqa: E402

DATA = Path(__file__).resolve().parent.parent / "data"
FEAT = DATA / "features"
FS = 500.0
WIN_S = 60.0                      # 特徴量ウィンドウ長 [s]
# 参照COの優先順: 熱希釈（Vigilance II = 肺動脈カテ）を最優先にする。
# FloTrac系（Vigileo/EV1000）のCOは動脈圧波形から導出されるため、
# 本研究が解析するのと近い信号領域に由来する。両方を持つ症例では
# 独立性の高い熱希釈を参照に採る。
DEVICE_PRIORITY = ["Vigilance", "Vigileo", "EV1000", "CardioQ"]
MIN_WINDOWS = 12                  # 症例採用に必要な有効ウィンドウ数（較正1+評価11以上）


# ---------------------------------------------------------------- 特徴量抽出
def pick_device(row, forced: str | None) -> str | None:
    """target_cases.csv の保有フラグから参照CO装置を1つ選ぶ。

    列名は 01_track_inventory.py が書く `{装置}_CO`（COトラックを実際に持つ症例）。
    CI/SV/SVI しか無い症例は解析に使えないので対象外。
    """
    if forced:
        return forced if row.get(f"{forced}_CO", False) else None
    for dev in DEVICE_PRIORITY:
        if row.get(f"{dev}_CO", False):
            return dev
    return None


def window_features(pleth: np.ndarray, ecg: np.ndarray, art: np.ndarray, co: np.ndarray,
                    co_t: np.ndarray, t0: float, height_m: float) -> dict | None:
    """1ウィンドウ分の {pwtt, si, ri, hr, map, co_ref} を返す。品質不足なら None。"""
    i0, i1 = int(t0 * FS), int((t0 + WIN_S) * FS)
    seg_p = np.nan_to_num(np.asarray(pleth[i0:i1], float))
    seg_e = np.nan_to_num(np.asarray(ecg[i0:i1], float))
    seg_a = np.asarray(art[i0:i1], float)
    if seg_p.size < int(WIN_S * FS) * 0.9 or not np.any(seg_p):
        return None

    # --- SI・RI: SQI通過拍をアンサンブル→PDA（ok解のみ採用） ---
    # 拍数はノイズから決める。収束検算は「自信を持って誤った解」を弾けないため
    # （tests/test_index_variants.py: 別解の16/17が検算通過）、実効ノイズを
    # 前処理側で目標以下に抑えることが唯一の防壁になる。
    # 心電図を基準に切る。極小値だけだと重複切痕を foot と誤検出して
    # 1心拍が2つに割れ、RI>1 などの非生理的な値が出る
    # （tests/test_beat_segmentation.py・実データ caseid=1 で確認）。
    beats = segment_beats(seg_p, FS, ecg=seg_e)
    good = [(a, b) for a, b in beats if sqi(seg_p[a:b], FS)["ok"]]
    if len(good) < 8:
        return None
    sigma = float(np.nanmedian([estimate_noise(seg_p[a:b]) for a, b in good]))
    n_ens, reachable = required_ensemble_size(sigma)
    if not reachable:                       # 上限拍数でも目標ノイズに届かない
        return None
    if len(good) < 2 * n_ens:               # 最低2アンサンブル分
        return None
    dts, ris = [], []
    for k in range(0, len(good) - n_ens + 1, n_ens):
        y = ensemble_average([seg_p[a:b] for a, b in good[k:k + n_ens]])
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

    # --- 平均血圧（SAP §7.3 用。動脈圧波形のウィンドウ平均） ---
    a = seg_a[np.isfinite(seg_a) & (seg_a > 20) & (seg_a < 300)]
    if a.size < int(0.5 * WIN_S * FS):
        return None
    mbp = float(np.mean(a))

    # --- 参照CO（ウィンドウ内中央値） ---
    m_co = (co_t >= t0) & (co_t < t0 + WIN_S) & np.isfinite(co) & (co > 0.5) & (co < 20)
    if m_co.sum() < 5:
        return None
    return {"t0": t0, "pwtt": float(np.median(pw)), "si": float(si), "ri": ri,
            "hr": hr, "map": mbp, "co_ref": float(np.median(co[m_co])),
            "sigma_rel": sigma, "n_ens": n_ens, "n_fits": len(dts)}


def extract_case(caseid: int, device: str, height_m: float):
    """1症例の特徴量CSVを作る（キャッシュ済みならスキップ）。"""
    import pandas as pd
    out = FEAT / f"case_{caseid}.csv"
    if out.exists():
        return pd.read_csv(out)
    import vitaldb  # pip install vitaldb
    wav = vitaldb.load_case(caseid, ["SNUADC/PLETH", "SNUADC/ECG_II", "SNUADC/ART"], 1 / FS)
    pleth = wav[:, 0].astype(np.float32)
    ecg = wav[:, 1].astype(np.float32)
    art = wav[:, 2].astype(np.float32)
    co = vitaldb.load_case(caseid, [f"{device}/CO"], 1).ravel().astype(np.float32)
    co_t = np.arange(co.size, dtype=np.float32)          # 1s間隔
    dur = len(pleth) / FS
    rows = []
    for t0 in np.arange(0, dur - WIN_S, WIN_S):
        f = window_features(pleth, ecg, art, co, co_t, float(t0), height_m)
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

    # --- SAP §7: 参照COの独立性への対処 ---
    pt = premise_test(cases)
    print("\n== SAP §7.1 前提検証（参照COを使わない） ==")
    print(f"ΔPWTT の変動のうち血管指標で説明される割合: r2 = {pt['r2_vasc']:.3f}"
          f"  (n={pt['n_windows']:,} ウィンドウ)")
    print(f"  係数 ΔΔT%: {pt['beta_dsi']:+.3f}  ΔRI%: {pt['beta_dri']:+.3f}")
    print("  ★ 主要評価が有意でも、ここが 0 近傍なら「参照側の性質への追随」を疑う（§7.6）")

    iv = incremental_value(cases)
    print("\n== SAP §7.3 血圧との関係（記述のみ・判別力は無い） ==")
    print(f"  PE 対照 {iv['対照']:.1f}% / +血圧 {iv['+血圧']:.1f}% / "
          f"+血管指標 {iv['+血管指標']:.1f}% / +両方 {iv['+両方']:.1f}%")

    devs = sorted({c.get("device", "?") for c in cases})
    print("\n== SAP §7.2 参照CO装置の内訳 ==")
    for d in devs:
        n = sum(c.get("device") == d for c in cases)
        kind = "熱希釈" if d == "Vigilance" else ("食道ドプラ" if d == "CardioQ" else "動脈圧由来")
        print(f"  {d:<10} {n:4d} 例  ({kind})")
    n_ind = sum(c.get("device") in ("Vigilance", "CardioQ") for c in cases)
    print(f"  → 動脈圧から独立な参照: {n_ind} 例"
          + ("（少数のため記述にとどめる）" if n_ind < 50 else ""))


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
              "（Mac上で実行すること。クラウドからは vitaldb.net に接続できない）")
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
            "windows": {k: df[k].to_numpy(float) for k in ["pwtt", "si", "ri", "hr", "map", "co_ref"]},
            "device": dev,
        })
        print(f"  ok（有効ウィンドウ {len(df)}）")

    if len(cases) < 10:
        print(f"\n解析可能な症例が {len(cases)} 例しかありません（最低10例）。--limit を増やすか基準を見直してください。")
        raise SystemExit(1)
    report(cases)


if __name__ == "__main__":
    main()
