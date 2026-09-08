#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""【探索】RI は血圧とは別に全身血管抵抗（SVR）と関連するか。

問い
----
研究1c C-2 は症例内で RI × SVR の順位相関 +0.098（204例・符号検定 p=1.7e-5）を得た。
しかし RI は平均血圧とも +0.161 で相関しており、EV1000 の SVR は (MAP−CVP)×80/CO
すなわち **MAP が分子に入る量**である。したがってこの +0.098 には構造的な混入がある。

MAP ≒ CO × SVR なので SVR と MAP は解離しうる（SVR が上がっても CO が下がれば MAP は動かない）。
そこで **解離している場面で RI が SVR と MAP のどちらを追うか**を見る。これが判別試験になる。

**MAP で調整した偏相関は主解析にしない。** RI が血管収縮を測っているなら MAP はその収縮の
結果（媒介変数）であり、調整すると真の信号まで削る。同時回帰は参考として併記する。

2群
---
A群（EV1000・最大204例）
    SVR = EV1000/SVR。**構造的に MAP を含み、CO も動脈圧波形由来**。したがって
    A群の解離ウィンドウは定義上「FloTrac の CO が動いた」窓であり、
    「RI は FloTrac の CO 推定を逆に追うか」に化ける。**陽性でも証明にならない。**
    足切りとして使う。ここで SVR 方向にまったく動かなければ話は終わる。

B群（Vigilance＝肺動脈カテーテル・5例）
    VitalDB で Vigilance/CO と波形3本をすべて持つのは caseid 2174・3849・3967・4522・4897 の
    **5例のみ**（うち CVP ありは 2174・3849 の 2例）。これらの features の `co_ref` は
    **既に Vigilance/CO（熱希釈由来）**なので、SVR* = (MAP − CVP)×80/CO は
    **動脈圧波形と独立**に組める。CVP が無い症例は SVR* = MAP×80/CO とし、その旨を記す。
    **n=5 なので記述のみ。判定に使わない。**大学のガンツ症例で何が見えるかの予行である。

書かないこと
------------
- 「RI は SVR の指標である」（A群は構造的混入、B群は n=5）
- roadmap §9・§12 の判定はこの解析で動かさない

使い方
------
    python3 scripts/37_ri_svr_screen.py --selftest
    python3 scripts/37_ri_svr_screen.py --run
    python3 scripts/37_ri_svr_screen.py --run --out ../docs/research/results/37_ri_svr_screen.txt
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from src.models import _rel                                          # noqa: E402

DATA = Path(__file__).resolve().parent.parent / "data"
FEAT = DATA / "features"
VTONE = DATA / "vasotone"

MIN_WIN = 12          # 症例内解析に要求する最小ウィンドウ数（研究1 と同じ）
MIN_DISC = 10         # 解離ウィンドウでの相関に要求する最小組数
FLAT = 0.02           # 「MAP がほぼ動いていない」とみなす相対変化の幅（±2%）
N_BOOT = 2000


# ---------------------------------------------------------------- 小道具
def spearman(x: np.ndarray, y: np.ndarray) -> float:
    m = np.isfinite(x) & np.isfinite(y)
    if m.sum() < 5:
        return float("nan")
    a, b = x[m], y[m]
    if np.ptp(a) == 0 or np.ptp(b) == 0:
        return float("nan")
    ra = pd.Series(a).rank().to_numpy()
    rb = pd.Series(b).rank().to_numpy()
    return float(np.corrcoef(ra, rb)[0, 1])


def sign_test(v: np.ndarray, positive: bool = True) -> tuple[int, int, float]:
    """符号検定。返り値 (期待どおりの数, 有限な数, 両側 p)。"""
    from math import comb
    v = v[np.isfinite(v) & (v != 0)]
    n = v.size
    k = int((v > 0).sum()) if positive else int((v < 0).sum())
    if n == 0:
        return 0, 0, float("nan")
    tail = sum(comb(n, i) for i in range(k, n + 1)) / 2 ** n
    return k, n, float(min(1.0, 2 * tail))


def ols2(y: np.ndarray, x1: np.ndarray, x2: np.ndarray, intercept: bool) -> tuple:
    """y ~ x1 + x2。返り値 (b1, b2, r2)。"""
    m = np.isfinite(y) & np.isfinite(x1) & np.isfinite(x2)
    if m.sum() < 5:
        return float("nan"), float("nan"), float("nan")
    X = np.column_stack([x1[m], x2[m]] + ([np.ones(m.sum())] if intercept else []))
    yy = y[m]
    try:
        beta, *_ = np.linalg.lstsq(X, yy, rcond=None)
    except np.linalg.LinAlgError:
        return float("nan"), float("nan"), float("nan")
    sse = float(((yy - X @ beta) ** 2).sum())
    sst = float(((yy - yy.mean()) ** 2).sum())
    r2 = 1.0 - sse / sst if sst > 0 else float("nan")
    return float(beta[0]), float(beta[1]), r2


def boot_ci(vals: np.ndarray, seed: int = 0) -> tuple[float, float]:
    """症例単位ブートストラップ（中央値の95%CI）。"""
    v = vals[np.isfinite(vals)]
    if v.size < 3:
        return float("nan"), float("nan")
    rng = np.random.default_rng(seed)
    meds = [float(np.median(rng.choice(v, v.size, replace=True))) for _ in range(N_BOOT)]
    return float(np.percentile(meds, 2.5)), float(np.percentile(meds, 97.5))


# ---------------------------------------------------------------- 症例ごと
def analyse_case(d: pd.DataFrame) -> dict | None:
    """d は t0 昇順で ri・map・svr を持つ。相対変化は研究1 と同じ _rel。"""
    if len(d) < MIN_WIN:
        return None
    dri = _rel(d["ri"].to_numpy(float))
    dmap = _rel(d["map"].to_numpy(float))
    dsvr = _rel(d["svr"].to_numpy(float))
    ok = np.isfinite(dri) & np.isfinite(dmap) & np.isfinite(dsvr)
    if ok.sum() < MIN_WIN:
        return None
    dri, dmap, dsvr = dri[ok], dmap[ok], dsvr[ok]

    b_svr, b_map, r2 = ols2(dri, dsvr, dmap, intercept=True)
    # 解離ウィンドウ。旧版は「逆向き」と「MAP平坦」の和を取っていたが、後者は一致集合と
    # 重なりうる（例: ΔMAP +1%・ΔSVR +5%）。重なりは解離側の相関を一致側へ引き寄せるため、
    # **純粋に逆向きだけの集合**を別に出す。
    opp = (np.sign(dsvr) * np.sign(dmap) < 0)                     # 逆向きのみ（厳格）
    flat = (np.abs(dmap) < FLAT) & (np.abs(dsvr) >= FLAT)         # MAP 平坦で SVR が動く
    disc = opp | flat                                             # 旧定義（参考）
    conc = (np.sign(dsvr) * np.sign(dmap) > 0) & ~flat            # 一致（平坦は除く）
    return {
        "n": int(ok.sum()),
        "rho_ri_svr": spearman(dri, dsvr),
        "rho_ri_map": spearman(dri, dmap),
        "rho_svr_map": spearman(dsvr, dmap),
        "b_svr": b_svr, "b_map": b_map, "r2": r2,
        "n_opp": int(opp.sum()), "n_flat": int(flat.sum()),
        "n_disc": int(disc.sum()), "n_conc": int(conc.sum()),
        "rho_opp": spearman(dri[opp], dsvr[opp]) if opp.sum() >= MIN_DISC else float("nan"),
        "rho_opp_map": spearman(dri[opp], dmap[opp]) if opp.sum() >= MIN_DISC else float("nan"),
        "rho_flat": spearman(dri[flat], dsvr[flat]) if flat.sum() >= MIN_DISC else float("nan"),
        "rho_disc": spearman(dri[disc], dsvr[disc]) if disc.sum() >= MIN_DISC else float("nan"),
        "rho_conc": spearman(dri[conc], dsvr[conc]) if conc.sum() >= MIN_DISC else float("nan"),
        "rho_disc_map": spearman(dri[disc], dmap[disc]) if disc.sum() >= MIN_DISC else float("nan"),
    }


def summarise(rows: list[dict], label: str, out: list) -> None:
    if not rows:
        out.append(f"\n{label}: 該当症例なし")
        return
    df = pd.DataFrame(rows)
    out.append(f"\n{label}（{len(df)} 例・ウィンドウ計 {int(df['n'].sum()):,}）")
    out.append(f"{'量':38s}{'中央値':>9s}{'95%CI':>22s}{'符号一致':>10s}{'p':>10s}")

    def line(name, col, positive=True):
        v = df[col].to_numpy(float)
        lo, hi = boot_ci(v)
        k, n, p = sign_test(v, positive)
        med = float(np.nanmedian(v)) if np.isfinite(v).any() else float("nan")
        ci = f"[{lo:+.3f}, {hi:+.3f}]" if np.isfinite(lo) else "—"
        out.append(f"{name:38s}{med:>+9.3f}{ci:>22s}{f'{k}/{n}':>10s}{p:>10.2g}")

    line("ρ(ΔRI%, ΔSVR%)  症例内", "rho_ri_svr")
    line("ρ(ΔRI%, ΔMAP%)  症例内（参考）", "rho_ri_map")
    line("ρ(ΔSVR%, ΔMAP%) 症例内（解離の程度）", "rho_svr_map")
    line("β_SVR  同時回帰（切片あり）", "b_svr")
    line("β_MAP  同時回帰（切片あり）", "b_map")
    out.append("")
    line("ρ(ΔRI%, ΔSVR%)  ★逆向きのみ（厳格）", "rho_opp")
    line("ρ(ΔRI%, ΔMAP%)  ★逆向きのみ（厳格）", "rho_opp_map")
    line("ρ(ΔRI%, ΔSVR%)  MAP平坦でSVRが動く窓", "rho_flat")
    line("ρ(ΔRI%, ΔSVR%)  一致ウィンドウのみ", "rho_conc")
    line("ρ(ΔRI%, ΔSVR%)  解離（逆向き＋平坦・旧定義）", "rho_disc")
    tot = int(df["n"].sum())
    no, nf, nc = df["n_opp"].sum(), df["n_flat"].sum(), df["n_conc"].sum()
    out.append(f"\n  逆向き {int(no):,}（{no/tot:.1%}）・MAP平坦 {int(nf):,}（{nf/tot:.1%}）"
               f"・一致 {int(nc):,}（{nc/tot:.1%}）")
    out.append(f"  {MIN_DISC} 組以上ある症例: 逆向き {int((df['n_opp'] >= MIN_DISC).sum())}"
               f"・平坦 {int((df['n_flat'] >= MIN_DISC).sum())}")


# ---------------------------------------------------------------- 本体
def load_feat(cid: int) -> pd.DataFrame | None:
    p = FEAT / f"case_{cid}.csv"
    if not p.exists():
        return None
    d = pd.read_csv(p)
    return d if {"t0", "ri", "map"} <= set(d.columns) else None


def run(out_path: str | None) -> int:
    out: list[str] = []
    out.append("=" * 84)
    out.append("【探索】RI は血圧とは別に全身血管抵抗と関連するか（37番）")
    out.append("roadmap §9・§12 の判定は動かさない。仮説生成のための解析である。")
    out.append("=" * 84)

    # ---- A群: EV1000 -------------------------------------------------
    rows_a = []
    for p in sorted(VTONE.glob("case_*.csv")):
        cid = int(p.stem.split("_")[1])
        f = load_feat(cid)
        if f is None:
            continue
        v = pd.read_csv(p)
        if "svr" not in v.columns:
            continue
        d = f.merge(v[["t0", "svr"]], on="t0", how="inner").sort_values("t0")
        d = d[np.isfinite(d["svr"])]
        r = analyse_case(d)
        if r:
            rows_a.append(r)
    summarise(rows_a, "A群  EV1000 の SVR", out)
    out.append("""
  【A群の限界】EV1000 の SVR は (MAP−CVP)×80/CO で、**MAP が分子に入り、CO は動脈圧波形由来**。
  よって ρ(ΔRI%, ΔSVR%) には構造的な混入がある。さらに解離ウィンドウは定義上
  「FloTrac の CO が動いた窓」であり、そこでの相関は「RI が FloTrac の CO 推定を
  逆に追うか」に化ける。**陽性でも RI が SVR を測る証拠にはならない。**
  ここで SVR 方向にまったく動かない場合にのみ、足切りとして意味を持つ。""")

    # ---- B群: Vigilance（肺動脈カテーテル） ---------------------------
    tc = DATA / "target_cases.csv"
    rows_b, notes = [], []
    if tc.exists():
        t = pd.read_csv(tc)
        col = "Vigilance_CO"
        pac = sorted(t.loc[t.get(col, False) == True, "caseid"].astype(int)) if col in t.columns else []
        out.append(f"\nB群  Vigilance（肺動脈カテーテル）該当 caseid: {pac}")
        for cid in pac:
            f = load_feat(cid)
            if f is None:
                notes.append(f"    caseid {cid}: features なし（未抽出）")
                continue
            if "co_ref" not in f.columns:
                notes.append(f"    caseid {cid}: co_ref 列なし")
                continue
            d = f.sort_values("t0").copy()
            co = d["co_ref"].to_numpy(float)
            mp = d["map"].to_numpy(float)
            cvp = d["cvp"].to_numpy(float) if "cvp" in d.columns else np.zeros_like(mp)
            src = "MAP−CVP" if "cvp" in d.columns else "MAP のみ（CVP 未取得）"
            with np.errstate(divide="ignore", invalid="ignore"):
                d["svr"] = np.where(co > 0, (mp - cvp) * 80.0 / co, np.nan)
            r = analyse_case(d)
            if r:
                r["caseid"] = cid
                rows_b.append(r)
                notes.append(f"    caseid {cid}: n={r['n']:4d}  ρ(RI,SVR*)={r['rho_ri_svr']:+.3f}  "
                             f"ρ(RI,MAP)={r['rho_ri_map']:+.3f}  分子={src}")
            else:
                notes.append(f"    caseid {cid}: ウィンドウ不足（<{MIN_WIN}）")
        out.append("  SVR* = (MAP − CVP) × 80 / CO。CO は Vigilance（熱希釈由来）なので"
                   "**動脈圧波形と独立**。")
        out.extend(notes)
        summarise(rows_b, "B群  熱希釈由来の独立 SVR*", out)
        out.append("""
  【B群の限界】**n が最大 5 例であり、記述のみ。判定にも仮説検定にも使わない。**
  5 例すべてが予測の向き（正）でも符号検定の両側 p は 0.063 が下限であり、有意にならない。
  CVP が取れない症例では SVR* = MAP×80/CO とした。症例内で CVP がほぼ一定なら
  この省略は主に尺度を変えるだけだが、CVP が動く症例では誤差になる。
  この群の意義は、**大学のガンツ症例で何が見えるかの予行**である。""")
    else:
        out.append("\nB群: data/target_cases.csv が無いため実行できない")

    out.append("\n" + "=" * 84)
    out.append("読み方: A群で β_SVR が 0 近傍かつ解離ウィンドウでも動かない → RI に SVR 情報は無い。")
    out.append("        A群で動く → 構造的混入と区別できないため、独立な SVR（ガンツ）が要る。")
    out.append("        B群は方向の目安のみ。大学データの中核群 40 例で検定する。")
    out.append("=" * 84)

    text = "\n".join(out)
    print(text)
    if out_path:
        Path(out_path).parent.mkdir(parents=True, exist_ok=True)
        Path(out_path).write_text(text + "\n", encoding="utf-8")
        print(f"\n書き出し: {out_path}", file=sys.stderr)
    return 0


# ---------------------------------------------------------------- 自己検査
def selftest() -> int:
    rng = np.random.default_rng(0)
    ok, ng = 0, []

    def chk(name, cond):
        nonlocal ok
        if cond:
            ok += 1
            print(f"  PASS  {name}")
        else:
            ng.append(name)
            print(f"  FAIL  {name}")

    # 1-2. spearman
    x = np.arange(50.0)
    chk("spearman 単調増加=+1", abs(spearman(x, 2 * x + 1) - 1.0) < 1e-9)
    chk("spearman 単調減少=−1", abs(spearman(x, -x) + 1.0) < 1e-9)
    chk("spearman 定数はNaN", not np.isfinite(spearman(x, np.ones(50))))

    # 4-5. 符号検定
    k, n, p = sign_test(np.array([1.0, 1, 1, 1, 1]))
    chk("符号検定 5/5 で p=0.0625", k == 5 and n == 5 and abs(p - 0.0625) < 1e-9)
    k, n, p = sign_test(np.array([1.0, -1, 1, -1]))
    chk("符号検定 2/4 で p=1.0", k == 2 and abs(p - 1.0) < 1e-9)

    # 6-7. 陽性統制: RI が SVR に従い MAP に従わない
    n_w = 300
    dsvr = rng.normal(0, 0.2, n_w)
    dmap = rng.normal(0, 0.2, n_w)                 # SVR と独立にする
    dri = 0.5 * dsvr + rng.normal(0, 0.02, n_w)
    b1, b2, _ = ols2(dri, dsvr, dmap, intercept=True)
    chk("陽性統制 β_SVR≈0.5", abs(b1 - 0.5) < 0.05)
    chk("陽性統制 β_MAP≈0", abs(b2) < 0.05)

    # 8-9. 陰性統制: RI が MAP にのみ従う
    dri2 = 0.5 * dmap + rng.normal(0, 0.02, n_w)
    b1, b2, _ = ols2(dri2, dsvr, dmap, intercept=True)
    chk("陰性統制 β_SVR≈0", abs(b1) < 0.05)
    chk("陰性統制 β_MAP≈0.5", abs(b2 - 0.5) < 0.05)

    # 10. 解離ウィンドウの抽出
    a = np.array([+0.1, -0.1, +0.1, +0.005, +0.1])
    b = np.array([+0.1, +0.1, -0.1, +0.100, +0.005])
    disc = ((np.sign(a) * np.sign(b) < 0) | ((np.abs(b) < FLAT) & (np.abs(a) >= FLAT)))
    chk("解離ウィンドウ抽出 = [F,T,T,F,T]", list(disc) == [False, True, True, False, True])

    # 11. analyse_case が研究1 と同じ相対変化を使う
    d = pd.DataFrame({"t0": np.arange(30.0), "ri": np.linspace(0.3, 0.5, 30),
                      "map": np.linspace(70, 90, 30), "svr": np.linspace(800, 1200, 30)})
    r = analyse_case(d)
    chk("analyse_case 単調同方向で ρ(RI,SVR)=+1", r is not None and abs(r["rho_ri_svr"] - 1.0) < 1e-6)

    # 12. ウィンドウ不足は None
    chk("ウィンドウ不足で None", analyse_case(d.head(5)) is None)

    # 13. _rel が研究1 と同一（先頭0・分母に床）
    v = _rel(np.array([2.0, 3.0, 4.0]))
    chk("_rel 先頭は0", abs(v[0]) < 1e-12 and abs(v[1] - 0.5) < 1e-12)

    print(f"\n  {ok}/{ok + len(ng)} PASS" + ("  ALL PASS" if not ng else f"  FAIL: {ng}"))
    return 0 if not ng else 1


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", action="store_true")
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--out", default=None)
    a = ap.parse_args()
    if a.selftest:
        sys.exit(selftest())
    if a.run:
        sys.exit(run(a.out))
    ap.print_help()


if __name__ == "__main__":
    main()
