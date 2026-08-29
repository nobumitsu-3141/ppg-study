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
        df = pd.read_csv(csv_p)
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
        })
    return pd.DataFrame(rows)


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
    ap.add_argument("--csv", type=str, default=None,
                    help="症例代表値をCSVに書き出す")
    args = ap.parse_args()

    df = load_cases(args.min_windows)
    if args.csv:
        df.to_csv(args.csv, index=False)
        print(f"書き出し: {args.csv}")
    report(df)


if __name__ == "__main__":
    main()
