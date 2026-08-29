#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""陽性対照: 血管指標が「既知の生理」を検出できることを確かめる。

なぜ必要か
----------
主解析（SAP §7.1）で ΔPWTT が血管指標で説明されないという陰性結果が出たとき、
査読者は必ずこう言う ――「関係が無いのではなく、指標が測れていないだけでは？」

自己相関が高いことは「白色雑音ではない」ことしか示さない。ゆっくり漂う
アーチファクトや自動利得制御の整定も自己相関は高い。VitalDB の PLETH は
研究用 PPG ではなく表示用に処理された波形であり、この疑いは正当である。

そこで、生理が既知の関係で指標が期待どおり動くかを見る。動くなら
「パイプラインは血管シグナルが存在すれば検出できる」と言える。

検証する既知の関係（いずれも症例間・横断）
  1. 加齢 → 動脈硬化 → 脈波速度上昇 → 反射波が早く戻る
     → **ΔT は年齢とともに短くなる**（したがって SI = 身長/ΔT は上昇する）
  2. 高血圧の既往がある症例は、同年齢でも ΔT が短い方向
  3. 反証用（陰性対照）: ΔT と、血管と無関係なはずの変数（例: 症例ID）は無相関

位置づけ
--------
本解析は SAP v0.3 凍結後に追加した**探索的解析**であり、事前指定の主解析では
ない。SAP の改訂履歴に日付つきで記載すること。主解析の定義には一切触れない。

使い方
------
    python scripts/06_positive_control.py
    python scripts/06_positive_control.py --min-windows 12
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

DATA = Path(__file__).resolve().parent.parent / "data"
FEAT = DATA / "features"


def load_cases(min_windows: int) -> pd.DataFrame:
    """キャッシュ済み特徴量から症例ごとの代表値を作る。

    症例内中央値を使う（時間変動ではなく、その症例の血管状態の代表値がほしい）。
    """
    demo = pd.read_csv(DATA / "cases.csv", encoding="utf-8-sig")
    demo = demo.set_index("caseid")

    rows = []
    for meta_p in sorted(FEAT.glob("case_*_meta.json")):
        try:
            meta = json.loads(meta_p.read_text(encoding="utf-8"))
        except Exception:
            continue
        if meta.get("v") != 3:
            continue
        cid = meta["caseid"]
        csv_p = FEAT / f"case_{cid}.csv"
        if not csv_p.exists():
            continue
        try:
            df = pd.read_csv(csv_p)
        except Exception:
            continue  # 本解析の実行中に書き込み途中のファイルを掴んだ場合は飛ばす
        if len(df) < min_windows or "si" not in df.columns:
            continue
        if cid not in demo.index:
            continue
        d = demo.loc[cid]
        height_m = float(d["height"]) / 100.0 if np.isfinite(d["height"]) else np.nan
        if not np.isfinite(height_m) or height_m <= 0:
            continue
        # SI = 身長[m] / ΔT[s] なので ΔT = 身長 / SI
        si_med = float(np.nanmedian(df["si"]))
        if not np.isfinite(si_med) or si_med <= 0:
            continue
        rows.append({
            "caseid": cid,
            "age": float(d["age"]) if np.isfinite(d["age"]) else np.nan,
            "sex": str(d["sex"]),
            "height_m": height_m,
            "bmi": float(d["bmi"]) if np.isfinite(d["bmi"]) else np.nan,
            "htn": float(d["preop_htn"]) if np.isfinite(d["preop_htn"]) else np.nan,
            "dm": float(d["preop_dm"]) if np.isfinite(d["preop_dm"]) else np.nan,
            "dt_ms": 1000.0 * height_m / si_med,
            "si": si_med,
            "ri": float(np.nanmedian(df["ri"])),
            "hr": float(np.nanmedian(df["hr"])),
            "map": float(np.nanmedian(df["map"])),
            "n_windows": len(df),
            "device": meta.get("device", "?"),
            # --- 症例内でのRI・ΔTの可測性（症例間のAGC正規化では壊れない量） ---
            "ri_cv": _cv(df["ri"]),
            "dt_cv": _cv(df["si"]),        # SI と ΔT の変動係数は同一
            "r_ri_map": _corr(df["ri"], df["map"]),
            "r_dt_map": _corr(df["si"], df["map"]),
        })
    return pd.DataFrame(rows)


def _cv(s) -> float:
    """症例内の変動係数。0近傍なら「その症例では動いていない」。"""
    v = pd.to_numeric(s, errors="coerce").to_numpy(dtype=float)
    v = v[np.isfinite(v)]
    if v.size < 5:
        return np.nan
    m = np.median(v)
    return float(np.std(v) / abs(m)) if m != 0 else np.nan


def _corr(a, b) -> float:
    """症例内のSpearman相関（可測性の確認用。仮説の検証ではない）。"""
    x = pd.to_numeric(a, errors="coerce")
    y = pd.to_numeric(b, errors="coerce")
    m = x.notna() & y.notna()
    if m.sum() < 10:
        return np.nan
    return float(x[m].rank().corr(y[m].rank()))


def spearman(x: np.ndarray, y: np.ndarray):
    """Spearman の順位相関と、Fisher 変換による95%CI・両側p値。

    scipy に依存せず順位相関だけで済ませる（scipy があれば p は一致する）。
    """
    m = np.isfinite(x) & np.isfinite(y)
    x, y = x[m], y[m]
    n = x.size
    if n < 10:
        return np.nan, np.nan, np.nan, n
    rx = pd.Series(x).rank().to_numpy()
    ry = pd.Series(y).rank().to_numpy()
    r = float(np.corrcoef(rx, ry)[0, 1])
    # Fisher z
    z = np.arctanh(np.clip(r, -0.999999, 0.999999))
    se = 1.0 / np.sqrt(n - 3)
    lo, hi = np.tanh(z - 1.96 * se), np.tanh(z + 1.96 * se)
    # 両側p（正規近似）
    from math import erfc, sqrt
    p = erfc(abs(z) / (se * sqrt(2)))
    return r, (lo, hi), p, n


def report(df: pd.DataFrame) -> None:
    print(f"\n=== 陽性対照（探索的・SAP凍結後の追加解析） ===")
    print(f"症例数: {len(df)}")
    if len(df) < 10:
        print("症例数が不足しているため判定できません（10例以上必要）。")
        print("本解析は 03_run_analysis.py の完走後に実行してください。")
        return

    print(f"年齢 中央値 {df['age'].median():.0f} 歳 "
          f"(範囲 {df['age'].min():.0f}–{df['age'].max():.0f})")
    print(f"ΔT   中央値 {df['dt_ms'].median():.0f} ms "
          f"(IQR {df['dt_ms'].quantile(.25):.0f}–{df['dt_ms'].quantile(.75):.0f})")
    print(f"RI   中央値 {df['ri'].median():.2f} "
          f"(IQR {df['ri'].quantile(.25):.2f}–{df['ri'].quantile(.75):.2f})")

    print("\n--- 主たる陽性対照: 加齢と ΔT ---")
    print("期待: 加齢で動脈硬化 → 反射波が早く戻る → ΔT は【短く】なる（r は負）")
    for name, col, expect in [("ΔT [ms]", "dt_ms", "負"),
                              ("SI [m/s]", "si", "正"),
                              ("RI", "ri", "正（弱い想定）")]:
        r, ci, p, n = spearman(df["age"].to_numpy(), df[col].to_numpy())
        if np.isfinite(r):
            print(f"  年齢 vs {name:9s}: rho {r:+.3f} "
                  f"[95%CI {ci[0]:+.3f}, {ci[1]:+.3f}]  p={p:.4f}  n={n}"
                  f"   期待符号={expect}")

    print("\n--- 補助的な陽性対照 ---")
    for label, key in [("高血圧既往", "htn"), ("糖尿病既往", "dm")]:
        g1 = df.loc[df[key] == 1, "dt_ms"].dropna()
        g0 = df.loc[df[key] == 0, "dt_ms"].dropna()
        if len(g1) >= 5 and len(g0) >= 5:
            print(f"  {label}あり ΔT 中央値 {g1.median():.0f} ms (n={len(g1)}) / "
                  f"なし {g0.median():.0f} ms (n={len(g0)})   期待: ありの方が短い")

    print("\n--- 症例内でのRIの可測性（症例間のAGC正規化とは独立の確認） ---")
    print("  自動利得制御は症例ごとに振幅を正規化するため、症例間の比較を壊しても")
    print("  症例内の相対変化は保ちうる。主解析が使うのは症例内のΔRI%である。")
    for label, cv_col, r_col in [("RI", "ri_cv", "r_ri_map"), ("ΔT", "dt_cv", "r_dt_map")]:
        cv = df[cv_col].dropna()
        rr = df[r_col].dropna()
        if len(cv) >= 10:
            print(f"  {label:3s}: 症例内変動係数 中央値 {cv.median():.3f} "
                  f"(IQR {cv.quantile(.25):.3f}–{cv.quantile(.75):.3f})   "
                  f"平均血圧との症例内相関 中央値 {rr.median():+.3f} "
                  f"(|r|>0.3 の症例 {100 * (rr.abs() > 0.3).mean():.0f}%)")
    print("  読み方: 変動係数が0近傍なら症例内でも動いていない（可測性なし）。")
    print("          十分に動き、血圧と一定の相関を示すなら症例内では可測である")
    print("          （相関の存在は仮説の支持ではない。共線性のため §7.3 参照）")

    print("\n--- 陰性対照（無関係であるべき） ---")
    r, ci, p, n = spearman(df["caseid"].to_numpy().astype(float),
                           df["dt_ms"].to_numpy())
    if np.isfinite(r):
        print(f"  症例ID vs ΔT: rho {r:+.3f} [95%CI {ci[0]:+.3f}, {ci[1]:+.3f}] "
              f"p={p:.4f}   期待: 0近傍")

    print("\n--- 読み方（事前に決めておく） ---")
    print("  加齢とΔTに期待どおりの負の相関があり、陰性対照が0近傍")
    print("    → パイプラインは血管シグナルを検出できている。")
    print("       主解析の陰性は【測定失敗ではなく実勢】と主張できる")
    print("  加齢との関係も出ない")
    print("    → 指標がこのチャネルで測れていない可能性が高い。論文の主張を")
    print("       「PWTTは血管指標で説明されない」から")
    print("       「VitalDBのPPGチャネルではこれらの指標を信頼して測れない」に")
    print("       変更する（データセット健全性の報告としての価値は残る）")
    print("  RIだけ関係が出ない（ΔTは出る）")
    print("    → 自動利得制御で振幅情報が失われている疑い。")
    print("       RIに基づく結論はタイミングのみに格下げする")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--min-windows", type=int, default=12,
                    help="症例採用に必要な有効ウィンドウ数（主解析と同じ既定12）")
    ap.add_argument("--min-age", type=float, default=None,
                    help="この年齢未満の症例を除く（例: 18 で成人限定。小児の影響を確認）")
    ap.add_argument("--csv", type=str, default=None,
                    help="症例代表値をCSVに書き出す")
    args = ap.parse_args()

    df = load_cases(args.min_windows)
    if args.min_age is not None:
        n0 = len(df)
        df = df[df["age"] >= args.min_age]
        print(f"年齢 {args.min_age:.0f} 歳以上に限定: {n0} → {len(df)} 例")
    if args.csv:
        df.to_csv(args.csv, index=False)
        print(f"書き出し: {args.csv}")
    report(df)


if __name__ == "__main__":
    main()
