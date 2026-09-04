#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""研究0 追試2: 我々の PDA 実装の設計選択が、失敗の原因ではないかを検証する。

問題意識
--------
`23_pwdb_landmarks.py` で、同じ波形からランドマーク法は真値を再現し（ΔT×PWV 0.710）、
我々の凍結2カーネル PDA は再現しなかった（0.223）。失敗は抽出法に固有である。
では**我々の実装のどの選択**が効いているのか。`src/pda.py` を読むと候補は4つある。

  (1) **減衰項が無い**  モデルは skew-Gaussian 2本だけで、拡張期の下降を表す項が無い。
      拡張期は1拍の約半分を占めるので、第2カーネルが反射波ではなく**拡張期の下降全体**を
      吸収しうる。その位置は拍長（＝60/HR）に引きずられる。実際、PDA ΔT の心拍数主効果は
      −10.9% でランドマーク ΔT の −2.6% の4倍である
  (2) **歪度を正に限っている**（alpha_bounds=(0, 8)）。両成分とも「急峻に立ち上がり緩やかに減衰」
      に固定される。これは重複切痕が見えない VitalDB の処理済み波形で振幅の同定性を保つための
      選択であった。**見える波形に当てるとき妥当とは限らない**
  (3) **残差が一様重み**  拡張期の標本数が多いので、当てはめは拡張期に支配される
  (4) **カーネル2本**  Couceiro 2015 は5本のガウス関数で当てはめ、成分を同定してから
      前進波と反射波の対を選んでいる

いずれも VitalDB の信号性状に合わせた選択であり、理想波形では不利に働きうる。
本スクリプトはこれを**切り分けの実験**として測る。

前提となる留保（先に書く）
--------------------------
PWDB の波形は雑音がなく重複切痕も拡張期ピークも明瞭である。**ランドマーク法が有利な条件**で
あり、PDA が主張してきた利点（ランドマークが見えない波形でも動く・雑音に強い）は
この土俵では現れない。したがって「PWDB で PDA が負けた」ことは
「PDA がランドマーク法に劣る」ことを意味しない。本スクリプトが答えるのは
**「理想波形ですら我々の実装が真値を追えないのは、実装の選択のせいか」**である。

出力は**探索的**であり、Gate 0 の判定を動かさない。

使い方
------
    python scripts/24_pwdb_pda_ablation.py --pwdb ~/pwdb --sample 60
        各年齢層から60名を無作為抽出（計360名）。まずこれで傾向を見る
    python scripts/24_pwdb_pda_ablation.py --pwdb ~/pwdb --sample 0 --jobs 4
        全4,374名。カーネル数が多い変種があるので数時間かかる
    python scripts/24_pwdb_pda_ablation.py --selftest
"""
from __future__ import annotations

import argparse
import importlib.util
import sys
from pathlib import Path

import numpy as np
from scipy.optimize import least_squares
from scipy.special import erf

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
OUT = ROOT / "data" / "pwdb"
SQRT2 = np.sqrt(2.0)


def _load(name: str):
    p = Path(__file__).resolve().parent / f"{name}.py"
    spec = importlib.util.spec_from_file_location(name.replace("_", ""), p)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


M20 = _load("20_pwdb_validity")
M23 = _load("23_pwdb_landmarks")


# ---------------------------------------------------------------- モデル
def skew(t, a, mu, sigma, alpha):
    z = (t - mu) / sigma
    return a * np.exp(-0.5 * z * z) * (1.0 + erf(alpha * z / SQRT2))


def model(t, p, n_kernels: int, decay: bool):
    """n 本の skew-Gaussian（＋任意で指数減衰項）。

    パラメータは [a, mu, sigma, alpha] × n（muは第1成分からのオフセットで持つ）
    ＋ decay なら [d, tau]。
    """
    y = np.zeros_like(t)
    mu = p[1]
    for i in range(n_kernels):
        a, off, s, al = p[4 * i], p[4 * i + 1], p[4 * i + 2], p[4 * i + 3]
        mu = off if i == 0 else mu + off
        y = y + skew(t, a, mu, s, al)
    if decay:
        d, tau = p[4 * n_kernels], p[4 * n_kernels + 1]
        y = y + d * np.exp(-(t - t[0]) / max(tau, 1e-3))
    return y


def peaks(t, p, n_kernels: int):
    tt = np.linspace(t[0], t[-1], 4000)
    out, mu = [], p[1]
    for i in range(n_kernels):
        a, off, s, al = p[4 * i], p[4 * i + 1], p[4 * i + 2], p[4 * i + 3]
        mu = off if i == 0 else mu + off
        yy = skew(tt, a, mu, s, al)
        j = int(np.argmax(yy))
        out.append((float(tt[j]), float(yy[j])))
    return out


# 変種の定義（表示名, カーネル数, 減衰項, αの下限, 重み）
VARIANTS = [
    ("A0 凍結と同型（対照）",      2, False,  0.0, "uniform"),
    ("A1 ＋拡張期の減衰項",        2, True,   0.0, "uniform"),
    ("A2 ＋負の歪度を許す",        2, False, -8.0, "uniform"),
    ("A3 ＋収縮期側に重み",        2, False,  0.0, "systole"),
    ("A4 3カーネル",               3, False,  0.0, "uniform"),
    ("A5 5カーネル（Couceiro式）", 5, False, -8.0, "uniform"),
    ("A6 減衰項＋負歪度＋3本",     3, True,  -8.0, "uniform"),
]


def _bounds(t, n_kernels, decay, alpha_min):
    T = float(t[-1] - t[0])
    lo, hi = [], []
    for i in range(n_kernels):
        if i == 0:
            lo += [0.02, 0.02, 0.010, alpha_min]
            hi += [2.50, 0.60 * T, 0.30, 8.0]
        else:
            lo += [0.005, 0.02, 0.010, alpha_min]
            hi += [2.00, 0.85 * T, 0.40, 8.0]
    if decay:
        lo += [0.0, 0.02]
        hi += [1.5, 2.0]
    return np.array(lo, float), np.array(hi, float)


def _weights(t, ys, mode: str):
    if mode != "systole":
        return np.ones_like(t)
    # 収縮期＋早期拡張期（主ピークから拍長の55%まで）を 1、それ以降を 0.25 にする
    i_pk = int(np.argmax(ys))
    cut = t[i_pk] + 0.55 * (t[-1] - t[0])
    w = np.where(t <= cut, 1.0, 0.25)
    return w


N_STARTS = 6          # 自己検査では下げる


def fit_variant(t, y, n_kernels, decay, alpha_min, weight_mode, n_starts=None, seed=0):
    """1拍を指定の設定で当てはめ、成分ピークを返す。"""
    t = np.asarray(t, float)
    y0 = np.asarray(y, float) - float(np.min(y))
    ymax = float(np.max(y0))
    if ymax <= 0:
        return None
    ys = y0 / ymax
    n_starts = N_STARTS if n_starts is None else n_starts
    lo, hi = _bounds(t, n_kernels, decay, alpha_min)
    w = _weights(t, ys, weight_mode)

    def resid(p):
        return (model(t, p, n_kernels, decay) - ys) * w

    i_pk = int(np.argmax(ys))
    t_pk = float(t[i_pk])
    # ランドマーク由来の初期オフセット（主ピーク後の −d²y/dt² 最小点）
    d2 = np.gradient(np.gradient(ys))
    j0, j1 = i_pk + max(int(0.06 * len(t)), 3), int(0.85 * len(t))
    dmu0 = float(np.clip(t[j0 + int(np.argmin(d2[j0:j1]))] - t_pk + 0.02, 0.08, 0.45)) \
        if j0 < j1 else 0.22

    rng = np.random.default_rng(seed)
    base = []
    for i in range(n_kernels):
        if i == 0:
            base += [1.0, max(t_pk - 0.02, 0.05), 0.06, 2.0]
        elif i == 1:
            base += [0.40, dmu0, 0.09, 1.0]
        else:
            base += [0.15, 0.12, 0.10, 1.0]
    if decay:
        base += [0.15, 0.30]
    base = np.clip(np.array(base, float), lo + 1e-6, hi - 1e-6)

    starts = [base]
    for dg in (0.12, 0.20, 0.30, 0.42):
        b = base.copy()
        if n_kernels >= 2:
            b[5] = np.clip(dg, lo[5] + 1e-6, hi[5] - 1e-6)
        starts.append(b)
    while len(starts) < n_starts:
        starts.append(np.clip(base * rng.uniform(0.75, 1.25, size=base.size),
                              lo + 1e-6, hi - 1e-6))

    best = None
    for x0 in starts:
        try:
            r = least_squares(resid, x0, bounds=(lo, hi), method="trf", max_nfev=3000)
        except Exception:
            continue
        if best is None or r.cost < best.cost:
            best = r
    if best is None:
        return None
    pk = peaks(t, best.x, n_kernels)
    order = np.argsort([q[0] for q in pk])          # 時刻順に並べ替える
    pk = [pk[i] for i in order]
    (t1, h1) = pk[0]
    if h1 <= 0:
        return None
    out = {"nrmse": float(np.sqrt(np.mean((model(t, best.x, n_kernels, decay) - ys) ** 2)))}
    # 第1成分と、それ以降の各成分の対をすべて返す
    for k in range(1, n_kernels):
        tk, hk = pk[k]
        out[f"dt_1{k+1}"] = (tk - t1) * 1000.0
        out[f"ri_1{k+1}"] = hk / h1
    # 「第1成分より後で最大の成分」を反射波とみなす規則（Couceiro の成分同定を模した簡便版）
    late = [(tt, hh) for tt, hh in pk[1:] if tt - t1 > 0.05]
    if late:
        tb, hb = max(late, key=lambda q: q[1])
        out["dt_big"] = (tb - t1) * 1000.0
        out["ri_big"] = hb / h1
    return out


# ---------------------------------------------------------------- 1被験者
def one_subject(args_tuple):
    subj, row, hr = args_tuple
    try:
        y, fs = M20.beat_of(row, hr)
        if y is None:
            return {"subj_no": subj}
        t = np.arange(y.size) / fs
        rec = {"subj_no": subj}
        for vi, (lab, nk, dec, amin, wm) in enumerate(VARIANTS):
            f = fit_variant(t, y, nk, dec, amin, wm, seed=vi)
            if not f:
                continue
            for k, v in f.items():
                rec[f"v{vi}_{k}"] = v
        return rec
    except Exception as e:  # noqa: BLE001
        return {"subj_no": subj, "err": str(e)[:60]}


# ---------------------------------------------------------------- 集計
def report(d, out_dir: Path | None = None):
    ages = sorted(d["age"].dropna().unique().tolist())
    print(f"\n{'='*86}\n研究0 追試2: PDA 実装の設計選択を切り分ける（探索的）\n{'='*86}")
    print(f"\n被験者 {len(d)} 名  年齢層 {ages}")
    print(f"判定規準は 20・23 番と同一（全層で予測の向き、中央値 |ρ| ≥ {M20.CRIT_RHO}）")
    print("参考値: 凍結PDA ΔT×PWV 0.223 ／ ランドマーク ΔT×PWV 0.710")

    print(f"\n{'-'*86}\nΔT × 大動脈PWV（予測: 負）\n{'-'*86}")
    hdr = f"{'変種':<30}{'対':<10}{'当て':>6}" + "".join(f"{int(a):>7}" for a in ages) + f"{'中央値':>8}{'向き':>7}  判定"
    print(hdr)
    summary = {}
    for vi, (lab, nk, dec, amin, wm) in enumerate(VARIANTS):
        pairs = [(f"v{vi}_dt_1{k+1}", f"1↔{k+1}") for k in range(1, nk)]
        pairs.append((f"v{vi}_dt_big", "1↔最大"))
        for col, pname in pairs:
            if col not in d or d[col].notna().sum() < 30:
                continue
            rows = M20._by_age(d, col, "PWV_a")
            j = M20._judge(rows, -1)
            by = {a: r for a, r, _n in rows}
            line = f"{lab:<30}{pname:<10}{int(d[col].notna().sum()):>6}"
            for a in ages:
                r = by.get(a, np.nan)
                line += f"{r:>+7.2f}" if np.isfinite(r) else f"{'—':>7}"
            if j:
                line += f"{j['med_abs']:>8.3f}{j['n_ok']:>3}/{j['n_ages']:<3}  {'成立' if j['pass'] else '不成立'}"
                summary[f"{lab}|{pname}|dt"] = j
            print(line)

    print(f"\n{'-'*86}\nRI × 末梢血管抵抗（予測: 正）\n{'-'*86}")
    print(hdr)
    for vi, (lab, nk, dec, amin, wm) in enumerate(VARIANTS):
        pairs = [(f"v{vi}_ri_1{k+1}", f"1↔{k+1}") for k in range(1, nk)]
        pairs.append((f"v{vi}_ri_big", "1↔最大"))
        for col, pname in pairs:
            if col not in d or d[col].notna().sum() < 30:
                continue
            rows = M20._by_age(d, col, "pvr")
            j = M20._judge(rows, +1)
            by = {a: r for a, r, _n in rows}
            line = f"{lab:<30}{pname:<10}{int(d[col].notna().sum()):>6}"
            for a in ages:
                r = by.get(a, np.nan)
                line += f"{r:>+7.2f}" if np.isfinite(r) else f"{'—':>7}"
            if j:
                line += f"{j['med_abs']:>8.3f}{j['n_ok']:>3}/{j['n_ages']:<3}  {'成立' if j['pass'] else '不成立'}"
                summary[f"{lab}|{pname}|ri"] = j
            print(line)

    if "var_pwv" in d:
        print(f"\n{'-'*86}\n心拍数の交絡（ΔT 1↔2 の主効果 [%]。凍結PDA −10.9 ／ ランドマーク −2.6）\n{'-'*86}")
        print(f"{'変種':<30}{'心拍数':>10}{'脈波伝播速度':>14}{'大動脈径':>10}{'比 PWV/HR':>12}")
        for vi, (lab, nk, dec, amin, wm) in enumerate(VARIANTS):
            col = f"vi{vi}"
            c = f"v{vi}_dt_12"
            if c not in d or d[c].notna().sum() < 30:
                continue
            e, _r = M20._factor_effects(d, c)
            f = dict(zip(M20.FACTORS, e))
            ratio = abs(f["pwv"]) / max(abs(f["hr"]), 1e-9)
            print(f"{lab:<30}{f['hr']:>+10.1f}{f['pwv']:>+14.1f}{f['dia']:>+10.1f}{ratio:>12.1f}")
        print("  比が大きいほど「脈波伝播速度に特異的」。ランドマーク法は 31.2/2.6 = 12.0")

    print(f"\n{'-'*86}\n読み方\n{'-'*86}")
    print("  どれかの変種で ΔT×PWV が 0.3 以上に上がる → **我々の実装の選択が原因**。")
    print("    どの変種かで原因が分かる（減衰項・歪度・重み・カーネル数）。")
    print("  どれも上がらない → 実装の選択では説明できない。PDA という枠組みの側を疑う。")
    print("  留保: PWDB は雑音がなくランドマークが明瞭で、**PDA が有利になる条件ではない**。")
    print("        ここでの敗北は、実波形での PDA の有用性を否定しない。")

    out_dir = OUT if out_dir is None else Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    p = out_dir / "pwdb_pda_ablation.csv"
    d.to_csv(p, index=False)
    print(f"\n被験者別の結果: {p}")
    return summary


# ---------------------------------------------------------------- 自己検証
def _make_rich_mock(root: Path, n: int = 60, seed: int = 0):
    """疑っている交絡そのものを仕込んだ模擬波形を作る。

    波形 = 前進波 + 反射波（位置は PWV で決まる） + **拡張期の指数減衰**（長さは拍長に比例）

    減衰項があるので、A0（減衰項なし・2カーネル）では第2カーネルが減衰を吸収して
    ΔT が拍長＝心拍数に引きずられるはずである。A1（減衰項あり）はそれを免れるはずである。
    自己検査はこの差を検出できるかを見る。純粋な2ガウス関数の模擬では検出しようがない。
    """
    import pandas as pd
    rng = np.random.default_rng(seed)
    M20._make_mock(root, n=n, seed=seed)      # 真値・入力・変動表・（後で捨てる）波形
    hae = M20._read_named(root / "pwdb_haemod_params.csv", ("subj_no", "age", "HR", "PWV_a"))
    fs, rows = 500.0, []
    for _, r in hae.iterrows():
        hr, pwv = float(r["HR"]), float(r["PWV_a"])
        dur = 60.0 / hr
        tt = np.arange(int(dur * fs)) / fs
        dt_true = 0.42 - 0.022 * pwv                       # PWV↑ で反射波が早く戻る
        y = (1.00 * np.exp(-0.5 * ((tt - 0.11) / 0.045) ** 2)
             + 0.32 * np.exp(-0.5 * ((tt - (0.11 + dt_true)) / 0.060) ** 2)
             + 0.45 * np.exp(-(tt) / (0.42 * dur)))        # ← 拍長に比例する拡張期減衰
        rows.append([int(r["subj_no"])] + list(y))
    w = max(len(q) for q in rows)
    mat = np.full((len(rows), w), np.nan)
    for k, q in enumerate(rows):
        mat[k, :len(q)] = q
    p = root / "PWs" / "csv" / "PWs_Digital_PPG.csv"
    with open(p, "w") as f:
        f.write("Subject Number, " + ", ".join(f"pt{j}" for j in range(1, w)) + "\n")
    with open(p, "a") as f:
        np.savetxt(f, mat, delimiter=",", fmt="%.10g")
    return root


def selftest() -> int:
    import tempfile
    import pandas as pd
    global N_STARTS
    print("== 24_pwdb_pda_ablation 自己検証（模擬PWDB・ネットワーク不要） ==")
    print("   模擬波形 = 前進波 + 反射波（PWV依存） + 拡張期の指数減衰（拍長に比例）")
    print("   すなわち『第2カーネルが減衰を吸収して心拍数に引きずられる』状況を仕込んである\n")
    ok = True
    N_STARTS = 3          # 自己検査は軽くする

    def rep(name, cond, detail=""):
        nonlocal ok
        ok &= bool(cond)
        print(f"  [{'PASS' if cond else 'FAIL'}] {name}{('  ' + detail) if detail else ''}", flush=True)

    with tempfile.TemporaryDirectory() as td:
        # 年齢層あたり10名（判定に要る最低8名を満たす）
        root = _make_rich_mock(Path(td) / "exported_data", n=60)
        hae, cfg, ppg, ex = M20.load_pwdb(root)
        h = hae.set_index("subj_no")
        rows = []
        for i in range(len(ppg)):
            sid = int(ppg.iloc[i, 0])
            rows.append(one_subject((sid, ppg.iloc[i].to_numpy(float), float(h.loc[sid, "HR"]))))
            if (i + 1) % 20 == 0:
                print(f"    当てはめ {i+1}/{len(ppg)}", flush=True)
        df = pd.DataFrame(rows)

        cover = {vi: int(df.get(f"v{vi}_dt_12", pd.Series(dtype=float)).notna().sum())
                 for vi in range(len(VARIANTS))}
        rep("2カーネル系の3変種（A0・A1・A2）がほぼ全員で値を返す",
            all(cover[vi] >= 0.9 * len(df) for vi in (0, 1, 2)), f"{cover}")
        rep("多カーネル系も半数以上で値を返す",
            all(cover[vi] >= 0.5 * len(df) for vi in (4, 5, 6)), f"{cover}")

        rep("減衰項ありの変種が当てはめ誤差を下げる（仕込んだ減衰を捉える）",
            float(df["v1_nrmse"].median()) < float(df["v0_nrmse"].median()),
            f"A0 {df['v0_nrmse'].median():.4f} → A1 {df['v1_nrmse'].median():.4f}")

        d = df.merge(hae, on="subj_no").merge(cfg[["subj_no", "pvr"]], on="subj_no")
        if "variations" in ex:
            d = d.merge(ex["variations"].drop(columns=["var_age"], errors="ignore"),
                        on="subj_no", how="left")
        rep("要因表が結合できている（心拍数交絡の節が動く）", "var_pwv" in d)

        s = report(d, out_dir=Path(td) / "out")
        j0 = s.get("A0 凍結と同型（対照）|1↔2|dt")
        j1 = s.get("A1 ＋拡張期の減衰項|1↔2|dt")
        rep("対照変種について判定が計算される（年齢層あたり10名）", bool(j0), f"{j0}")
        rep("減衰項ありの変種について判定が計算される", bool(j1), f"{j1}")
        rep("**減衰項を足すと ΔT×PWV の関連が強まる**（仕込んだ交絡を検出できる）",
            bool(j0 and j1 and j1["med_abs"] > j0["med_abs"]),
            f"A0 {j0['med_abs']:.3f} → A1 {j1['med_abs']:.3f}" if (j0 and j1) else "")
        rep("結果ファイルを書き出す", (Path(td) / "out" / "pwdb_pda_ablation.csv").exists())
    N_STARTS = 6
    print("\n" + ("ALL PASS" if ok else "FAIL あり"))
    return 0 if ok else 1


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--pwdb", type=str, help="PWDB の配布物を置いたフォルダ")
    ap.add_argument("--sample", type=int, default=60,
                    help="各年齢層から無作為抽出する人数（0 で全員。既定 60）")
    ap.add_argument("--jobs", type=int, default=1)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--selftest", action="store_true")
    args = ap.parse_args()
    if args.selftest:
        sys.exit(selftest())
    if not args.pwdb:
        ap.error("--pwdb を指定してください（--selftest なら不要）")

    import pandas as pd
    root = Path(args.pwdb).expanduser()
    hae, cfg, ppg, extras = M20.load_pwdb(root)
    d0 = hae[["subj_no", "age", "HR", "PWV_a"]].merge(cfg[["subj_no", "pvr", "pvc"]], on="subj_no")
    if "variations" in extras:
        d0 = d0.merge(extras["variations"].drop(columns=["var_age"], errors="ignore"),
                      on="subj_no", how="left")
    if args.sample:
        rng = np.random.default_rng(args.seed)
        keep = []
        for _a, g in d0.groupby("age"):
            ids = g["subj_no"].to_numpy()
            keep.append(rng.choice(ids, size=min(args.sample, ids.size), replace=False))
        sel = set(np.concatenate(keep).tolist())
        print(f"  年齢層ごとに {args.sample} 名を無作為抽出 → 計 {len(sel)} 名", flush=True)
    else:
        sel = set(d0["subj_no"].tolist())

    hr_by = dict(zip(hae["subj_no"].astype(int), hae["HR"].astype(float)))
    work = [(int(ppg.iloc[i, 0]), ppg.iloc[i].to_numpy(float), hr_by.get(int(ppg.iloc[i, 0]), np.nan))
            for i in range(len(ppg)) if int(ppg.iloc[i, 0]) in sel]
    print(f"{len(work)} 名 × {len(VARIANTS)} 変種を当てはめます / jobs={args.jobs}", flush=True)

    if args.jobs > 1:
        from concurrent.futures import ProcessPoolExecutor
        with ProcessPoolExecutor(max_workers=args.jobs) as ex:
            rows = list(ex.map(one_subject, work, chunksize=4))
    else:
        rows = []
        for n, w in enumerate(work, 1):
            rows.append(one_subject(w))
            if n % 50 == 0:
                print(f"  [{n}/{len(work)}]", flush=True)
    report(pd.DataFrame(rows).merge(d0, on="subj_no", how="left"))


if __name__ == "__main__":
    main()
