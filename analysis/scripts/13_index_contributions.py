#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""各指標がΔPWTTの説明にどれだけ寄与しているかを分解する（探索的）。

答えたい問い
------------
1. RIが正確に測れていない可能性があるのに、RIを含む式で前提検証してよいのか。
   → RIを外した「ΔT単独」の回帰と比べ、ΔTの係数とr²が変わるかを見る。
      多重回帰では、雑音の説明変数を足しても他の係数は（相関していなければ）
      偏らず、r²もほとんど増えない。それを実測で確認する。
2. そもそもRIは今回の説明にどれだけ効いているのか。
   → 各変数の単独r²と、組み合わせたときのr²の増分を出す。
3. 「正確なRI」が入れば精度が上がる余地は残っているか。
   → 直接は答えられないが、上限を測る。血圧・心拍数という
      「よく測れている血行動態変数」でどこまで説明できるかが目安になる。
      さらにPWTTの自己相関から、そもそも説明可能な再現性成分の割合を見積もる。
4. 身長を含めた正しいSIならどうか。
   → SI = 身長/ΔT で身長は症例内で定数。ΔSI% = ΔT₀/ΔT − 1 となり
      身長は完全に約分される。SIとΔTは症例内では同一の情報しか持たない。
      これを実測でも確認する（両者のr²が一致することを示す）。

位置づけ: SAP v0.3 凍結後の探索的解析。主解析の定義には触れない。

使い方:
    python scripts/13_index_contributions.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.models import _deltas, _rel  # noqa: E402

DATA = Path(__file__).resolve().parent.parent / "data"
FEAT = DATA / "features"
MIN_WINDOWS = 12


def load_cases() -> list[dict]:
    demo = pd.read_csv(DATA / "cases.csv", encoding="utf-8-sig").set_index("caseid")
    cases = []
    for meta_p in sorted(FEAT.glob("case_*_meta.json")):
        try:
            meta = json.loads(meta_p.read_text(encoding="utf-8"))
        except Exception:
            continue
        if meta.get("v") != 3:
            continue
        cid = meta["caseid"]
        f = FEAT / f"case_{cid}.csv"
        if not f.exists():
            continue
        try:
            df = pd.read_csv(f)
        except Exception:
            continue
        if len(df) < MIN_WINDOWS or "si" not in df.columns:
            continue
        if cid not in demo.index:
            continue
        h = float(demo["height"].get(cid, np.nan))
        if not np.isfinite(h) or h < 100:
            continue
        cases.append({"caseid": cid, "height": h / 100.0,
                      "windows": {k: df[k].to_numpy(float)
                                  for k in ["pwtt", "si", "ri", "hr", "map", "co_ref"]}})
    return cases


def build_matrix(cases: list[dict]) -> tuple:
    """全症例をプールした説明変数行列と目的変数を作る。"""
    cols = {"dt": [], "ri": [], "map": [], "hr": [], "si_raw": []}
    y = []
    for c in cases:
        d = _deltas(c)
        w = c["windows"]
        # ΔT の相対変化。SI = h/ΔT なので ΔSI% と符号が逆の関係になる。
        # d["dsi"] は SI の相対変化（主解析の回帰子）。ΔT そのものの相対変化も作る。
        dt_series = c["height"] / np.maximum(w["si"], 1e-12)      # ΔT[s]
        cols["dt"].append(_rel(dt_series))
        cols["si_raw"].append(d["dsi"])
        cols["ri"].append(d["dri"])
        cols["map"].append(d["dmap"])
        cols["hr"].append(_rel(w["hr"]))
        y.append(d["dpwtt_rel"])
    X = {k: np.concatenate(v) for k, v in cols.items()}
    y = np.concatenate(y)
    m = np.isfinite(y)
    for v in X.values():
        m &= np.isfinite(v)
    return {k: v[m] for k, v in X.items()}, y[m], int(m.sum())


def r2_of(X: dict, y: np.ndarray, keys: list[str]) -> tuple:
    """指定した説明変数（＋切片）での決定係数と係数を返す。"""
    M = np.column_stack([X[k] for k in keys] + [np.ones(y.size)])
    coef, *_ = np.linalg.lstsq(M, y, rcond=None)
    sse = float(np.sum((y - M @ coef) ** 2))
    sst = float(np.sum((y - y.mean()) ** 2))
    return 1.0 - sse / max(sst, 1e-12), {k: float(coef[i]) for i, k in enumerate(keys)}


def ac1_median(cases: list[dict], key: str) -> float:
    vals = []
    for c in cases:
        x = np.asarray(c["windows"][key], float)
        x = x[np.isfinite(x)]
        if len(x) < 3 or np.std(x) < 1e-12:
            continue
        vals.append(float(np.corrcoef(x[:-1], x[1:])[0, 1]))
    return float(np.nanmedian(vals)) if vals else float("nan")


LABEL = {"dt": "ΔT", "si_raw": "ΔSI（身長込み）", "ri": "RI", "map": "平均血圧", "hr": "心拍数"}


def main() -> None:
    cases = load_cases()
    print(f"症例数 {len(cases)}")
    if len(cases) < 10:
        print("本解析の完走後に実行してください。")
        return
    X, y, n = build_matrix(cases)
    print(f"ウィンドウ数 {n:,}\n")

    print("=== 問1・問2: RIを外すとΔTの係数と説明力は変わるか ===")
    r2_dt, c_dt = r2_of(X, y, ["si_raw"])
    r2_ri, c_ri = r2_of(X, y, ["ri"])
    r2_both, c_both = r2_of(X, y, ["si_raw", "ri"])
    print(f"  ΔSI% のみ          : r² {r2_dt:.4f}   β_ΔSI% {c_dt['si_raw']:+.4f}")
    print(f"  ΔRI% のみ          : r² {r2_ri:.4f}   β_ΔRI% {c_ri['ri']:+.4f}")
    print(f"  ΔSI% ＋ ΔRI%（主解析）: r² {r2_both:.4f}   "
          f"β_ΔSI% {c_both['si_raw']:+.4f}   β_ΔRI% {c_both['ri']:+.4f}")
    print(f"  → RI追加によるr²の増分 {r2_both - r2_dt:+.4f}")
    print(f"  → RI追加によるΔSI%係数の変化 {c_both['si_raw'] - c_dt['si_raw']:+.4f}")
    print("  読み方: 増分と係数変化がともに0近傍なら、RIは主解析の結論に")
    print("          影響していない（RIを外しても同じ結論になる）。")

    print("\n=== 問4: 身長を含むSIと、身長を含まないΔTは同じ情報か ===")
    r2_dtraw, c_dtraw = r2_of(X, y, ["dt"])
    print(f"  ΔT%（身長なし）のみ : r² {r2_dtraw:.4f}   β {c_dtraw['dt']:+.4f}")
    print(f"  ΔSI%（身長込み）のみ: r² {r2_dt:.4f}   β {c_dt['si_raw']:+.4f}")
    print(f"  → r²の差 {abs(r2_dtraw - r2_dt):.6f}")
    print("  数式: SI = 身長/ΔT、身長は症例内で定数なので ΔSI% = ΔT₀/ΔT − 1。")
    print("        身長は完全に約分され、症例内では同一の情報しか持たない。")
    print("        （r²が一致することがその実測による確認）")

    print("\n=== 問3: 説明力の上限はどこにあるか ===")
    r2_map, _ = r2_of(X, y, ["map"])
    r2_hr, _ = r2_of(X, y, ["hr"])
    r2_vm, c_vm = r2_of(X, y, ["si_raw", "ri", "map"])
    r2_all, c_all = r2_of(X, y, ["si_raw", "ri", "map", "hr"])
    print(f"  平均血圧のみ                : r² {r2_map:.4f}")
    print(f"  心拍数のみ                  : r² {r2_hr:.4f}")
    print(f"  血管指標 ＋ 血圧            : r² {r2_vm:.4f}"
          f"   （血管指標のみからの増分 {r2_vm - r2_both:+.4f}）")
    print(f"  血管指標 ＋ 血圧 ＋ 心拍数  : r² {r2_all:.4f}")
    print(f"    係数 ΔSI% {c_all['si_raw']:+.4f} / ΔRI% {c_all['ri']:+.4f} / "
          f"血圧 {c_all['map']:+.4f} / 心拍数 {c_all['hr']:+.4f}")
    ac = ac1_median(cases, "pwtt")
    print(f"\n  PWTTの隣接ウィンドウ自己相関（中央値） {ac:+.3f}")
    print(f"  → 系列が1次自己回帰に従うと仮定した場合の再現可能成分の目安 "
          f"{max(ac, 0) ** 2 * 100:.0f}〜{max(ac, 0) * 100:.0f}%")
    print("  読み方: よく測れている血行動態変数（血圧・心拍数）を総動員しても")
    print("          説明できる割合がこの程度なら、指標の精度を上げても")
    print("          伸びしろは限られる。逆に大きな未説明分が残るなら、")
    print("          より良い血管指標に余地がありうる。")


if __name__ == "__main__":
    main()
