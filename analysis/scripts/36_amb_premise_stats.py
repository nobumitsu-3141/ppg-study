#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""【探索・凍結後】早期振幅比による前提検証の集計（設計は docs/research/sap_1_amb_exploratory_v0.md）。

何をするか
----------
35番が出した Am_b/Am_p1 を研究1 のウィンドウに結合し、設計書 §6 の 4 行を
**すべて同じウィンドウの上で**計算する。

  ΔPWTT% を  ①ΔAm%  ②ΔAm% ＋ ΔMAP%  ③ΔSI% ＋ ΔRI%  ④ΔMAP% のみ  で説明

規約は研究1（SAP §7.1）と同じ。相対変化は `src/models.py` の `_rel` をそのまま使い、
r² は「切片なし（事前指定）」と「切片あり」の両方を出す。分母は
sum((y − mean(y))²) なので、切片なしでは負になりうる（研究1 と同じ）。

**主要評価（percentage error）は再計算しない。**参照 CO の 98% が動脈圧波形由来という
SAP §1.2 の制約と §7.6 の解釈規準は、この解析でも解けていないからである。

読み方は設計書 §7 で**結果を見る前に固定**してある。この報告の末尾に印字する。

使い方:
    python scripts/36_amb_premise_stats.py --selftest
    python scripts/36_amb_premise_stats.py --out ../docs/research/results/36_amb_premise_report.txt
"""
from __future__ import annotations

import argparse
import sys
import unicodedata
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.models import _rel                                    # noqa: E402

DATA = Path(__file__).resolve().parent.parent / "data"
FEAT = DATA / "features"
AFEAT = DATA / "features_amb"
MIN_WIN = 12          # 研究1 と同じ症例採用条件
COVERAGE_MIN = 0.95   # 35番がこの割合まで終わっていないと集計しない（--partial で解除）

# 設計書 §6 の 4 行。(表示名, 説明変数の並び)
ROWS = [
    ("① ΔAm%（早期振幅比）",            ("dam",)),
    ("② ΔAm% ＋ ΔMAP%",                ("dam", "dmap")),
    ("③ ΔSI% ＋ ΔRI%（研究1 の主解析）", ("dsi", "dri")),
    ("④ ΔMAP% のみ",                    ("dmap",)),
]

_OUT = []


def say(msg: str = "") -> None:
    print(msg, flush=True)
    _OUT.append(msg)


def _w(s: str) -> int:
    return sum(2 if unicodedata.east_asian_width(c) in "WFA" else 1 for c in s)


def _pad(s: str, width: int) -> str:
    return s + " " * max(width - _w(s), 0)


# ---------------------------------------------------------------- 読み込み
def load_joined(limit: int | None = None) -> tuple[list[dict], dict]:
    """研究1 の features と 35番の features_amb を t0 で結合する。

    返り値: (症例のリスト, 欠損の集計)
    各症例は {"caseid", "n_main", "n_joined", "w": {列名: 配列}}。
    Am_b/Am_p1 が欠損したウィンドウは落とす（**4 行すべてが同じ窓になる**）。
    """
    import pandas as pd
    cases, tot_main, tot_join, n_amb_all = [], 0, 0, []
    files = sorted(FEAT.glob("case_*.csv"))
    for fp in files:
        if limit is not None and len(cases) >= limit:
            break
        try:
            cid = int(fp.stem.split("_")[1])
        except Exception:
            continue
        ap = AFEAT / f"case_{cid}.csv"
        if not ap.exists():
            continue
        m = pd.read_csv(fp)
        a = pd.read_csv(ap)
        if "t0" not in m.columns or "t0" not in a.columns:
            continue
        tot_main += len(m)
        j = m.merge(a[["t0", "amb", "n_amb", "n_group"]], on="t0", how="inner")
        need = ["pwtt", "si", "ri", "map", "amb"]
        if any(c not in j.columns for c in need):
            continue
        j = j.dropna(subset=need)
        tot_join += len(j)
        if "n_amb" in j.columns:
            n_amb_all.extend(j["n_amb"].tolist())
        if len(j) < MIN_WIN:
            continue
        j = j.sort_values("t0").reset_index(drop=True)
        cases.append({
            "caseid": cid, "n_main": len(m), "n_joined": len(j),
            "w": {c: j[c].to_numpy(float) for c in ["pwtt", "si", "ri", "map", "amb"]},
        })
    n_amb_files = len(list(AFEAT.glob("case_*.csv")))
    miss = {
        "n_case_main": len(files),
        "n_case_amb_files": n_amb_files,
        "coverage": n_amb_files / max(len(files), 1),
        "n_case_used": len(cases),
        "n_win_main": tot_main,
        "n_win_joined": tot_join,
        "drop_rate": 1.0 - tot_join / max(tot_main, 1),
        "n_amb_median": float(np.median(n_amb_all)) if n_amb_all else float("nan"),
    }
    return cases, miss


def deltas(case: dict) -> dict:
    """研究1 と同じ規約（src.models._rel）で相対変化を作る。"""
    w = case["w"]
    return {
        "y":    _rel(w["pwtt"]),
        "dsi":  _rel(w["si"]),
        "dri":  _rel(w["ri"]),
        "dmap": _rel(w["map"]),
        "dam":  _rel(w["amb"]),
    }


# ---------------------------------------------------------------- 回帰
def pooled(cases: list[dict], regs: tuple[str, ...]) -> dict:
    """全症例プールの回帰。r² は切片なし（事前指定）と切片ありの両方。"""
    Xs, ys = [], []
    for c in cases:
        d = deltas(c)
        Xs.append(np.column_stack([d[r] for r in regs]))
        ys.append(d["y"])
    X, y = np.vstack(Xs), np.concatenate(ys)
    g = np.isfinite(y) & np.isfinite(X).all(axis=1)
    X, y = X[g], y[g]
    sst = float(np.sum((y - y.mean()) ** 2))

    def r2_of(M):
        coef, *_ = np.linalg.lstsq(M, y, rcond=None)
        sse = float(np.sum((y - M @ coef) ** 2))
        return 1.0 - sse / max(sst, 1e-12), coef

    r2_ni, coef_ni = r2_of(X)
    r2_wi, _ = r2_of(np.column_stack([np.ones(len(y)), X]))
    return {"n_win": int(y.size), "r2_no_int": r2_ni, "r2_with_int": r2_wi,
            "betas": {r: float(b) for r, b in zip(regs, coef_ni)}}


def by_case(cases: list[dict], reg: str) -> dict:
    """症例内の診断: 係数の符号の揃い・症例内 r²・順位相関の中央値。"""
    from scipy.stats import spearmanr
    betas, r2s, rhos = [], [], []
    for c in cases:
        d = deltas(c)
        y, x = d["y"], d[reg]
        g = np.isfinite(y) & np.isfinite(x)
        y, x = y[g], x[g]
        if len(y) < 8 or np.std(x) < 1e-12:
            continue
        M = np.column_stack([np.ones(len(y)), x])
        coef, *_ = np.linalg.lstsq(M, y, rcond=None)
        sst = float(np.sum((y - y.mean()) ** 2))
        r2s.append(1.0 - float(np.sum((y - M @ coef) ** 2)) / max(sst, 1e-12))
        betas.append(float(coef[1]))
        rho = spearmanr(x, y).statistic
        if np.isfinite(rho):
            rhos.append(float(rho))
    b = np.array(betas)
    return {
        "n_case": len(betas),
        "sign_consistency": float(max((b > 0).mean(), (b < 0).mean())) if b.size else float("nan"),
        "sign_dir": ("負" if b.size and (b < 0).mean() >= (b > 0).mean() else "正"),
        "r2_within_median": float(np.median(r2s)) if r2s else float("nan"),
        "rho_median": float(np.median(rhos)) if rhos else float("nan"),
    }


def autocorr1(cases: list[dict], col: str) -> float:
    """隣接ウィンドウの lag-1 自己相関の症例中央値（測定の再現性の目安）。"""
    vals = []
    for c in cases:
        x = c["w"][col]
        x = x[np.isfinite(x)]
        if len(x) < 3 or np.std(x) < 1e-12:
            continue
        r = float(np.corrcoef(x[:-1], x[1:])[0, 1])
        if np.isfinite(r):
            vals.append(r)
    return float(np.median(vals)) if vals else float("nan")


# ---------------------------------------------------------------- 報告
def report(cases: list[dict], miss: dict, label: str = "") -> None:
    say("=" * 92)
    if label:
        say(f"★★ {label} ★★")
        say("=" * 92)
    say("研究1 の前提検証を早期振幅比でやり直す（探索的解析）")
    say("設計: docs/research/sap_1_amb_exploratory_v0.md（結果を見る前に凍結）")
    say("=" * 92)
    say("")
    say(f"抽出の網羅率: 研究1 のキャッシュ {miss['n_case_main']} 症例に対し "
        f"35番の出力 {miss['n_case_amb_files']} 症例（{miss['coverage']*100:.1f}%）")
    say(f"症例: 研究1 のキャッシュ {miss['n_case_main']} → 本解析で採用 {miss['n_case_used']}"
        f"（結合後 {MIN_WIN} ウィンドウ以上）")
    say(f"ウィンドウ: 研究1 {miss['n_win_main']:,} → 本解析 {miss['n_win_joined']:,}"
        f"（欠損率 {miss['drop_rate']*100:.1f}%）")
    say(f"1 ウィンドウあたりの採択群数 n_amb の中央値: {miss['n_amb_median']:.1f}")
    say("")
    say("**研究1 が採用したウィンドウの上でのみ計算している。**"
        "「PDA ok ≥ 2 区間」で研究1 が落とした窓は復元されない（設計書 §5）。")
    say("")

    say("-" * 92)
    say("1. 前提検証（被説明変数はいずれも ΔPWTT%。4 行はすべて同じウィンドウ）")
    say("-" * 92)
    say(f"{_pad('説明変数', 34)}{'窓数':>10}{'r² 切片なし':>13}{'r² 切片あり':>13}   係数")
    results = {}
    for label, regs in ROWS:
        r = pooled(cases, regs)
        results[label] = r
        bs = " ".join(f"{k}={v:+.4f}" for k, v in r["betas"].items())
        say(f"{_pad(label, 34)}{r['n_win']:>10,}{r['r2_no_int']:>13.4f}"
            f"{r['r2_with_int']:>13.4f}   {bs}")
    say("")
    say("  切片なしが事前指定の規約（SAP §7.1）。分母は sum((y−mean)²) なので負になりうる。")
    say("")

    say("-" * 92)
    say("2. 症例内の診断")
    say("-" * 92)
    say(f"{_pad('説明変数', 16)}{'症例':>6}{'符号の揃い':>12}{'向き':>6}"
        f"{'症例内 r² 中央値':>18}{'順位相関 中央値':>18}")
    for reg, lab in [("dam", "ΔAm%"), ("dsi", "ΔSI%"), ("dri", "ΔRI%"), ("dmap", "ΔMAP%")]:
        d = by_case(cases, reg)
        say(f"{_pad(lab, 16)}{d['n_case']:>6}{d['sign_consistency']*100:>11.0f}%"
            f"{d['sign_dir']:>6}{d['r2_within_median']:>18.4f}{d['rho_median']:>18.4f}")
    say("")

    say("-" * 92)
    say("3. 測定の再現性（隣接ウィンドウの lag-1 自己相関・症例中央値）")
    say("-" * 92)
    for col, lab in [("amb", "Am_b/Am_p1"), ("pwtt", "PWTT（陽性対照）"),
                     ("si", "SI"), ("ri", "RI"), ("map", "平均血圧")]:
        say(f"  {_pad(lab, 22)}{autocorr1(cases, col):>8.3f}")
    say("")

    say("-" * 92)
    say("4. 事前に決めた読み方（設計書 §7。結果を見る前に固定した）")
    say("-" * 92)
    r1 = results[ROWS[0][0]]["r2_with_int"]
    sc = by_case(cases, "dam")["sign_consistency"]
    say(f"  ① の r²（切片あり）= {r1:.4f}　符号の揃い = {sc*100:.0f}%")
    if r1 >= 0.10 and sc >= 0.70:
        verdict = ("r² ≥ 0.10 かつ 符号の揃い ≥ 70% → "
                   "「分解由来の指標では説明できなかったが、構成概念妥当性のある指標では "
                   "ΔPWTT% の一部を説明する」と書ける。"
                   "ただし ΔMAP% 単独を超えない限り「血圧を超えて説明する」とは書かない。")
    elif r1 >= 0.05:
        verdict = ("0.05 ≤ r² < 0.10 → 記述にとどめる。"
                   "向きと大きさを数値で書き、結論には使わない。")
    else:
        verdict = ("r² < 0.05 → 「**指標を替えても ΔPWTT% は説明できない**」。"
                   "研究1 の結論（この形の補正は臨床段階へ進めない）は変わらず、むしろ補強される。")
    say(f"  → {verdict}")
    r4 = results[ROWS[3][0]]["r2_with_int"]
    say(f"  参考: ④ ΔMAP% 単独の r²（切片あり）= {r4:.4f}"
        f"　① はこれを{'超える' if r1 > r4 else '超えない'}")
    say("")
    say("  いずれの場合も、研究1 の主要評価・無益性の判定は動かさない。")
    say("  **主要評価（percentage error）は再計算していない**（参照 CO の非独立性は解けていない）。")
    say("")
    say("  書かないこと（設計書 §8）: 「早期振幅比なら esCCO が改善する」"
        "（精度を見ていない）／「Am_b/Am_p1 は血管トーヌスを測る」"
        "（示したのは大動脈脈波伝播速度との関連）／「実機で同定できたから妥当である」"
        "（再現性は妥当性を含意しない）。")
    say("=" * 92)


# ---------------------------------------------------------------- 自己検査
def _synth_cases(n_cases=40, n_win=40, effect=0.0, seed=0) -> list[dict]:
    """ΔPWTT% と ΔAm% に既知の関係 effect を仕込んだ合成症例。

    effect=0 なら関係なし（陰性対照）、effect<0 なら仕込みあり（陽性対照）。
    ΔSI%・ΔRI%・ΔMAP% は独立な雑音とする。
    """
    rng = np.random.default_rng(seed)
    out = []
    for k in range(n_cases):
        amb = 0.90 + 0.05 * rng.standard_normal(n_win)
        d_am = amb / amb[0] - 1.0
        base = 200.0
        pwtt = base * (1.0 + effect * d_am + 0.01 * rng.standard_normal(n_win))
        out.append({"caseid": k, "n_main": n_win, "n_joined": n_win, "w": {
            "pwtt": pwtt,
            "si": 3.0 + 0.2 * rng.standard_normal(n_win),
            "ri": 0.5 + 0.05 * rng.standard_normal(n_win),
            "map": 80.0 + 8.0 * rng.standard_normal(n_win),
            "amb": amb,
        }})
    return out


def selftest() -> int:
    ok = [0, 0]

    def rep(name, cond, detail=""):
        ok[1] += 1
        ok[0] += bool(cond)
        print(f"  [{'PASS' if cond else 'FAIL'}] {name}" + (f"  {detail}" if detail else ""))

    print("36番 自己検査")
    print("-" * 74)

    # 陽性対照: 仕込んだ関係を復元できるか
    pos = _synth_cases(effect=-0.6, seed=1)
    rp = pooled(pos, ("dam",))
    rep("陽性対照: 仕込んだ関係を復元する（r² 切片あり ≥ 0.5）",
        rp["r2_with_int"] >= 0.5, f"r²={rp['r2_with_int']:.3f} β={rp['betas']['dam']:+.3f}")
    rep("陽性対照: 係数の符号が仕込みと同じ（負）",
        rp["betas"]["dam"] < 0, f"β={rp['betas']['dam']:+.3f}")
    dp = by_case(pos, "dam")
    rep("陽性対照: 症例内の符号がほぼ揃う（≥ 90%）",
        dp["sign_consistency"] >= 0.90, f"{dp['sign_consistency']*100:.0f}% ({dp['sign_dir']})")

    # 陰性対照: 関係が無ければ 0 近傍
    neg = _synth_cases(effect=0.0, seed=2)
    rn = pooled(neg, ("dam",))
    rep("陰性対照: 関係が無ければ r²（切片あり）が 0 近傍",
        abs(rn["r2_with_int"]) < 0.02, f"r²={rn['r2_with_int']:.4f}")
    dn = by_case(neg, "dam")
    rep("陰性対照: 症例内の符号が揃わない（< 75%）",
        dn["sign_consistency"] < 0.75, f"{dn['sign_consistency']*100:.0f}%")

    # 無関係な説明変数では陽性対照でも上がらない
    rep("陽性対照でも無関係な説明変数（ΔSI%＋ΔRI%）では上がらない",
        abs(pooled(pos, ("dsi", "dri"))["r2_with_int"]) < 0.02,
        f"r²={pooled(pos, ('dsi','dri'))['r2_with_int']:.4f}")

    # 規約の検算
    r_ni = pooled(pos, ("dam",))["r2_no_int"]
    r_wi = pooled(pos, ("dam",))["r2_with_int"]
    rep("切片ありの r² は切片なし以上（同じ分母なので）", r_wi >= r_ni - 1e-12,
        f"{r_ni:.4f} → {r_wi:.4f}")

    # 相対変化の規約が src.models._rel と一致すること
    c = pos[0]
    rep("ΔPWTT% が src.models._rel と一致する",
        np.allclose(deltas(c)["y"], _rel(c["w"]["pwtt"])))

    # 自己相関: 平滑な系列は高く、白色雑音は 0 近傍
    smooth = [{"caseid": 0, "w": {"amb": np.cumsum(np.random.default_rng(3).standard_normal(50))}}]
    white = [{"caseid": 0, "w": {"amb": np.random.default_rng(4).standard_normal(50)}}]
    rep("自己相関: 平滑な系列で高く、白色雑音で 0 近傍",
        autocorr1(smooth, "amb") > 0.7 and abs(autocorr1(white, "amb")) < 0.35,
        f"{autocorr1(smooth,'amb'):.3f} 対 {autocorr1(white,'amb'):.3f}")

    # 症例採用条件
    short = _synth_cases(n_cases=3, n_win=5, seed=5)
    rep("ウィンドウ数が足りない症例は by_case から外れる",
        by_case(short, "dam")["n_case"] == 0)

    print("-" * 74)
    print(f"{ok[0]}/{ok[1]} " + ("ALL PASS" if ok[0] == ok[1] else "**FAIL あり**"))
    return 0 if ok[0] == ok[1] else 1


# ---------------------------------------------------------------- main
def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--limit", type=int, default=None)
    ap.add_argument("--out", type=str, default=None)
    ap.add_argument("--partial", action="store_true",
                    help="35番の抽出が未完でも集計する（判定には使えない）")
    ap.add_argument("--label", type=str, default="",
                    help="報告の先頭に出す注記（例: 雲・15例・処理系の確認であって判定ではない）")
    ap.add_argument("--selftest", action="store_true")
    args = ap.parse_args()
    if args.selftest:
        return selftest()

    cases, miss = load_joined(args.limit)
    if not cases:
        print("結合できる症例がありません。先に 35_amb_premise_extract.py を回してください。")
        return 1

    # --- 番人: 35番が走り終わる前に集計してしまう事故を防ぐ ---
    # 部分集計は症例の偏りで値が大きく動く（比較行 ③ が研究1 の確定値から外れることで気づける）。
    if args.limit is None and miss["coverage"] < COVERAGE_MIN and not args.partial:
        print("=" * 92)
        print("★★ 中止: 35番の抽出が終わっていません ★★")
        print("=" * 92)
        print(f"  研究1 のキャッシュ {miss['n_case_main']} 症例に対し、"
              f"35番の出力は {miss['n_case_amb_files']} 症例（{miss['coverage']*100:.1f}%）しかありません。")
        print(f"  部分集計は症例の偏りで値が大きく動くので、判定には使えません"
              f"（{COVERAGE_MIN*100:.0f}% 未満では出しません）。")
        print()
        print("  35番の進捗:  python3 scripts/status.py     の「早期振幅比抽出」")
        print("               tail -f amb_run.log            の「完了:」行を待つ")
        print()
        print("  途中経過をどうしても見たいときだけ --partial を付けてください"
              "（--label で「判定ではない」と明記すること）。")
        print("=" * 92)
        return 2
    if miss["coverage"] < COVERAGE_MIN and not args.label:
        args.label = (f"部分集計（35番の網羅率 {miss['coverage']*100:.1f}%）。"
                      "判定ではない。抽出の完走後に必ず取り直すこと")
    report(cases, miss, args.label)
    if args.out:
        p = Path(args.out)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text("\n".join(_OUT) + "\n", encoding="utf-8")
        print(f"\n報告を書き出しました: {p}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
