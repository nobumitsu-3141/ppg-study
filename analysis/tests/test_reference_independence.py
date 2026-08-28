# -*- coding: utf-8 -*-
"""SAP §7 の検証: 参照CO（FloTrac系）の血圧依存性による「偽の改善」を見抜けるか。

背景（SAP §1.2）: 対象874例の98%は FloTrac 系（Vigileo/EV1000）が参照COで、
これは動脈圧波形から算出され、血圧変動と並行して動くことが知られている。
本研究の提案手法も血管状態に応じて動くため、一致度の改善が
「真のCO精度向上」なのか「参照側の性質への追随」なのかを見分ける必要がある。

3シナリオで各判定法を突き合わせる:
  A 真の効果   PWTTに血管状態が混入、参照COは健全
  B 偽の改善   PWTTへの混入なし、参照COが血圧と並行して動く（FloTrac系の模擬）
  C 効果なし   混入なし、参照も健全

実行: analysis/ で  python3 -m tests.test_reference_independence
"""
from __future__ import annotations

import numpy as np

from src.synth_cohort import make_cohort
from src.models import premise_test, incremental_value, crossval
from src.stats import bootstrap_diff_ci

SCEN = {
    "A 真の効果": dict(effect=True, map_artifact=0.0),
    "B 偽の改善": dict(effect=False, map_artifact=0.6),
    "C 効果なし": dict(effect=False, map_artifact=0.0),
}
SEEDS = (0, 1, 2)


def collect(kw, seed):
    cs = make_cohort(n_cases=80, n_windows=30, seed=seed, **kw)
    return (premise_test(cs),
            bootstrap_diff_ci(crossval(cs, seed=seed), seed=seed),
            incremental_value(cs, seed=seed))


def main() -> None:
    print("== 参照COの独立性: 偽の改善を見抜けるか ==")
    res = {k: [collect(kw, s) for s in SEEDS] for k, kw in SCEN.items()}
    ok = True

    print("\n[1. 主要評価だけでは区別できないこと（問題の確認）]")
    for k in SCEN:
        sig = sum(r[1]["significant_improvement"] for r in res[k])
        pe = np.mean([r[1]["diff_mean"] for r in res[k]])
        print(f"  {k}: ΔPE {pe:+.1f}%  有意 {sig}/{len(SEEDS)}")
    sig_a = sum(r[1]["significant_improvement"] for r in res["A 真の効果"])
    sig_b = sum(r[1]["significant_improvement"] for r in res["B 偽の改善"])
    confounded = (sig_a == len(SEEDS)) and (sig_b == len(SEEDS))
    print(f"  -> A も B も有意になる: {confounded}"
          f"  {'（想定どおり。主要評価だけでは不十分）' if confounded else '（想定と異なる）'}")

    print("\n[2. §7.1 前提検証 ― 参照COを使わない判定]")
    r2 = {k: np.array([r[0]["r2_vasc"] for r in res[k]]) for k in SCEN}
    for k in SCEN:
        print(f"  {k}: r2_vasc = {np.mean(r2[k]):+.3f}  "
              f"(範囲 {r2[k].min():+.3f}〜{r2[k].max():+.3f})")
    disc = bool(r2["A 真の効果"].min() > 0.30
                and r2["B 偽の改善"].max() < 0.05
                and r2["C 効果なし"].max() < 0.05)
    print(f"  -> A のみ高く B・C は 0 近傍: {'PASS' if disc else 'FAIL'}"
          f"  ★偽の改善を確実に見抜ける唯一の判定")
    ok &= disc

    print("\n[3. §7.3 血圧を超える増分 ― 判別力は無い（記述用にとどめる根拠）]")
    print(f"  {'シナリオ':<12}{'対照':>8}{'+血圧':>8}{'+血管指標':>10}{'+両方':>8}{'増分':>8}")
    inc = {}
    for k in SCEN:
        v = {key: float(np.mean([r[2][key] for r in res[k]]))
             for key in ("対照", "+血圧", "+血管指標", "+両方", "血圧を超える増分")}
        inc[k] = v
        print(f"  {k:<12}{v['対照']:>7.1f}%{v['+血圧']:>7.1f}%"
              f"{v['+血管指標']:>9.1f}%{v['+両方']:>7.1f}%{v['血圧を超える増分']:>+7.2f}")
    # 真の効果でも増分がほぼ出ない ＝ ΔMAP と血管指標が共線で、寄与を分離できない
    no_disc = inc["A 真の効果"]["血圧を超える増分"] < 0.5
    print(f"  -> 真の効果でも増分は {inc['A 真の効果']['血圧を超える増分']:+.2f}pt。"
          f"ΔMAP と血管指標は共線で寄与を分離できない。")
    print(f"     よって §7.3 は解釈の関門にせず、記述にとどめる: "
          f"{'PASS（想定どおり判別力なし）' if no_disc else 'FAIL（判別力があるなら関門に使える）'}")
    ok &= no_disc

    if ok:
        print("\nALL PASS")
        print("帰結: 偽の改善に対する防壁は §7.1 前提検証（参照COを使わない）。")
        print("      主要評価の有意性だけでは A と B を区別できず、§7.3 にも判別力は無い。")
    else:
        print("\nSOME FAILED")
        raise SystemExit(1)


if __name__ == "__main__":
    main()
