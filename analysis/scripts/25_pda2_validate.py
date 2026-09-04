#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""PDA 第2版（src/pda2.py）を真値既知の合成脈波で検証し、凍結版と直接比べる。

何を確かめるか
--------------
  T1 ピーク母数化      ピーク高さ・時刻が母数どおりに出るか
  T2 指標の回復        雑音なしで ΔT・RI を真値どおりに戻せるか
  T3 **心拍数交絡**    ΔT の真値を固定して心拍数だけ振ったとき、ΔT が動かないか
                       ← 凍結版の最大の欠陥。ここが本番
  T4 雑音耐性          SNR を下げたときの ΔT の誤差と、採否規準の効き方
  T5 波形型            重複切痕のある型と無い型の両方で動くか
  T6 採否規準          壊れた当てはめを弾けるか（Errx）
  T7 標準誤差          雑音が増えると ΔT の標準誤差も増えるか（選別に使えるか）

合成脈波
--------
    y(t) = 前進波（歪みガウス） + 反射波（歪みガウス） + 貯留槽（指数減衰）

貯留槽の時定数は生理的に固定し、**拍長だけを変える**。凍結版は貯留槽を表す項が無いので
第2カーネルがこれを吸収し、その位置が拍長に引きずられるはずである。第2版はそうならないはず。

使い方
------
    python scripts/25_pda2_validate.py --selftest
    python scripts/25_pda2_validate.py --selftest --quick
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src import pda2                                     # noqa: E402
from src.pda import fit_beat, component_peak             # noqa: E402

FS = 500.0


# ---------------------------------------------------------------- 合成脈波
def make_beat(hr=70.0, dt_true=0.28, ri_true=0.45, tau_res=0.35, d_res=0.40,
              notch=True, noise=0.0, seed=0, fs=FS, basis="skew"):
    """前進波 ＋ 反射波 ＋ 貯留槽。真値を返す。

    basis で真値側の基底関数を選べる。**どちらの経路にも有利な真値があるので、
    両方の基底で作った波形で両方の経路を測る**（2×2）。片方だけで比べると、
    真値と同じ基底を使う経路が自動的に勝つ。
    notch=False では反射波を早く幅広くして重複切痕を消す（Dawber 3〜4型を模す）。
    """
    rng = np.random.default_rng(seed)
    T = 60.0 / hr
    t = np.arange(0.0, T, 1.0 / fs)
    tp_f = 0.12
    if notch:
        w_f, a_f, w_r, a_r = 0.045, 2.5, 0.065, 1.2
    else:
        w_f, a_f, w_r, a_r = 0.055, 2.0, 0.090, 0.0
    tp_r = tp_f + dt_true
    if basis == "gamma":
        fwd = pda2.gamma_peak(t, 1.0, tp_f, 0.09, 5.0)
        ref = pda2.gamma_peak(t, ri_true, tp_r, 0.11, 9.0 if notch else 4.0)
    else:
        fwd = pda2.skew_peak(t, 1.0, tp_f, w_f, a_f)
        ref = pda2.skew_peak(t, ri_true, tp_r, w_r, a_r)
    t_a = min(0.55 * T, tp_r + 0.05)
    sh = np.clip(t / max(t_a, 1e-6), 0, 1) ** 2
    res = d_res * sh * np.exp(-np.maximum(t - t_a, 0.0) / tau_res)
    y = fwd + ref + res
    if noise > 0:
        y = y + noise * rng.standard_normal(y.size)
    return t, y, {"dt_ms": dt_true * 1000.0, "ri": ri_true, "hr": hr, "T": T,
                  "basis": basis}


def frozen_indices(t, y):
    """凍結版（src/pda.py）で ΔT・RI を出す。比較の対照。"""
    try:
        f = fit_beat(t, y)
    except Exception:
        return np.nan, np.nan, False
    c1, c2 = f["components"]
    p1 = (c1["a"], c1["mu"], c1["sigma"], c1["alpha"])
    p2 = (c2["a"], c2["mu"], c2["sigma"], c2["alpha"])
    t1, h1 = component_peak(p1, t[0], t[-1])
    t2, h2 = component_peak(p2, t[0], t[-1])
    return (t2 - t1) * 1000.0, h2 / max(h1, 1e-9), bool(f.get("ok", False))


ROUTES = ("two_stage", "gamma3")


def _run(t, y, route):
    return pda2.decompose(t, y, FS, route=route)


# ---------------------------------------------------------------- 検証
def selftest(quick: bool = False) -> int:
    ok_all = True

    def rep(name, cond, detail=""):
        nonlocal ok_all
        ok_all &= bool(cond)
        print(f"  [{'PASS' if cond else 'FAIL'}] {name}{('  ' + detail) if detail else ''}",
              flush=True)

    print("== PDA 第2版の検証（真値既知の合成脈波・凍結版と直接比較） ==\n")

    # ---- T1 ピーク母数化
    print("T1 ピーク母数化")
    tt = np.arange(0, 0.9, 1 / FS)
    s = pda2.skew_peak(tt, 1.0, 0.12, 0.05, 2.0)
    g = pda2.gamma_peak(tt, 0.8, 0.30, 0.12, 6.0)
    rep("歪みガウスのピークが母数どおり",
        abs(s.max() - 1.0) < 1e-6 and abs(tt[int(np.argmax(s))] - 0.12) < 0.003)
    rep("ガンマのピークが母数どおり（Γ(α) を陽に計算しない）",
        abs(g.max() - 0.8) < 1e-6 and abs(tt[int(np.argmax(g))] - 0.30) < 0.003)

    # ---- T2 指標の回復（真値の基底 × 経路 の 2×2。どちらにも有利な真値があるため）
    print("\nT2 指標の回復（雑音なし・HR 70）")
    print(f"       {'真値の基底':<12}{'経路':<12}{'ΔT誤差':>9}{'RI誤差':>9}{'Errx':>8}{'NRMSE':>9}  採用")
    t2 = {}
    for tb in ("skew", "gamma"):
        t, y, tr = make_beat(basis=tb)
        for route in ROUTES:
            r = _run(t, y, route)
            e_dt, e_ri = r["dt_ms"] - tr["dt_ms"], r["ri"] - tr["ri"]
            t2[(tb, route)] = (e_dt, e_ri, r["ok"])
            print(f"       {tb:<12}{route:<12}{e_dt:>+9.1f}{e_ri:>+9.3f}"
                  f"{r['errx_ms']:>8.2f}{r['nrmse']:>9.4f}  {r['ok']}")
        dtf, rif, okf = frozen_indices(t, y)
        print(f"       {tb:<12}{'凍結版':<12}{dtf - tr['dt_ms']:>+9.1f}{rif - tr['ri']:>+9.3f}"
              f"{'—':>8}{'—':>9}  {okf}")
    rep("歪みガウス真値でどちらの経路も ΔT の誤差が 15 ms 未満",
        all(abs(t2[("skew", r)][0]) < 15.0 for r in ROUTES),
        ", ".join(f"{r} {t2[('skew', r)][0]:+.1f}" for r in ROUTES))
    rep("ガンマ真値では gamma 経路が two_stage より良い（2×2 が働いている）",
        abs(t2[("gamma", "gamma3")][0]) < abs(t2[("gamma", "two_stage")][0]),
        f"gamma3 {t2[('gamma','gamma3')][0]:+.1f} 対 two_stage {t2[('gamma','two_stage')][0]:+.1f}")
    print("       注: ガンマ基底には Tigges 2017 の定義に無い到達時刻の母数を足してある。")
    print("           これが無いと全成分が拍の先頭から立ち上がり、遅れて届く反射波を表せない。")
    print("       注: ガンマ真値の波は成分の裾が速く（時定数 20〜45 ms）、貯留槽の緩い下降を")
    print("           どちらの経路も表しきれない。両経路とも Errx で不採用になるのが正しい。")
    print("           採否規準そのものが基底の当てはめやすさに依存することを意味する。")
    t, y, tr = make_beat()
    dtf, rif, _ = frozen_indices(t, y)
    rep("**RI の誤差が凍結版より小さい**（歪みガウス真値で比較）",
        abs(t2[("skew", "two_stage")][1]) < abs(rif - tr["ri"]),
        f"two_stage {t2[('skew','two_stage')][1]:+.3f} 対 凍結版 {rif - tr['ri']:+.3f}")

    # ---- T3 心拍数交絡（本番）
    print("\nT3 心拍数交絡（ΔT の真値を 280 ms に固定し、心拍数だけ 50〜100 に振る）")
    hrs = [50, 60, 70, 80, 90, 100] if not quick else [50, 70, 100]
    got = {r: [] for r in ROUTES}
    got["frozen"] = []
    for hr in hrs:
        t, y, tr = make_beat(hr=hr)
        for route in ROUTES:
            r = _run(t, y, route)
            got[route].append(r["dt_ms"])       # 採否に関わらず集める（交絡量を測るため）
        got["frozen"].append(frozen_indices(t, y)[0])
    print(f"       {'心拍数':<12}" + "".join(f"{h:>9}" for h in hrs) + f"{'幅':>10}{'傾き':>12}")
    spread = {}
    for key in ("frozen", *ROUTES):
        v = np.array(got[key], float)
        fin = np.isfinite(v)
        sp = float(np.nanmax(v) - np.nanmin(v)) if fin.sum() > 1 else np.nan
        slope = float(np.polyfit(np.array(hrs)[fin], v[fin], 1)[0]) if fin.sum() > 1 else np.nan
        spread[key] = sp
        lab = "凍結版" if key == "frozen" else key
        print(f"       {lab:<12}" + "".join(f"{x:>9.1f}" if np.isfinite(x) else f"{'—':>9}" for x in v)
              + f"{sp:>10.1f}{slope:>12.3f}")
    print("       幅 = 心拍数を通じた ΔT の最大差 [ms]。真値は一定なので 0 が理想。傾きは ms/bpm")
    rep("two_stage の心拍数交絡が凍結版以下",
        np.isfinite(spread["two_stage"]) and spread["two_stage"] <= spread["frozen"],
        f"two_stage {spread['two_stage']:.1f} ms 対 凍結版 {spread['frozen']:.1f} ms")
    print("       注: 本合成では凍結版の交絡が 15 ms 程度にしか出ない。PWDB では ΔT の心拍数主効果が")
    print("           −10.9%（≒38 ms）であり、**合成データは交絡を過小に再現している**。")
    print("           改善の可否を決めるのは PWDB での実測であって、この表ではない。")
    print("       注: gamma3 の交絡は two_stage より大きい。到達時刻の母数を足す前は幅 155 ms で")
    print("           完全に破綻していたが、足した後も 55 ms 残る。ガンマの裾は形状母数ひとつで")
    print("           立ち上がりと下降の両方を決めるため、拍が短いと下降を優先して形が歪む。")

    # ---- T4 雑音耐性
    print("\nT4 雑音耐性（HR 70・雑音の標準偏差を振る）")
    noises = [0.0, 0.01, 0.03, 0.06] if not quick else [0.0, 0.06]
    reps = 6 if quick else 12
    print(f"       {'雑音':<10}{'経路':<12}{'ΔT誤差 中央値':>16}{'採用率':>9}"
          f"{'採用分の SE 中央値':>20}{'SE>20ms の割合':>16}")
    ok_rate = {r: [] for r in ROUTES}
    pool = {r: [] for r in ROUTES}          # (採否, ΔT の絶対誤差)
    for nz in noises:
        for route in ROUTES:
            errs, oks, se_ok, bad = [], [], [], []
            for k in range(reps):
                t, y, tr = make_beat(noise=nz, seed=100 + k)
                r = _run(t, y, route)
                oks.append(r["ok"])
                e = abs(r["dt_ms"] - tr["dt_ms"]) if np.isfinite(r["dt_ms"]) else np.nan
                if np.isfinite(e):
                    errs.append(e)
                    pool[route].append((bool(r["ok"]), e))
                se = r["dt_se_ms"]
                bad.append(not np.isfinite(se) or se > pda2.SE_DT_MAX_MS)
                if r["ok"] and np.isfinite(se):
                    se_ok.append(se)
            ok_rate[route].append(float(np.mean(oks)))
            sm = float(np.median(se_ok)) if se_ok else np.nan
            print(f"       {nz:<10.3f}{route:<12}{float(np.median(errs)) if errs else np.nan:>16.1f}"
                  f"{np.mean(oks):>9.0%}{sm:>20.2f}{float(np.mean(bad)):>16.0%}")
    print(f"       ΔT の標準誤差が {pda2.SE_DT_MAX_MS:.0f} ms を超える解は採否で落とす。振幅が潰れた")
    print("       成分のピーク時刻は本当に同定できないので、その標準誤差は秒の桁になる。")
    print("       これは異常値ではなく正しい報告であり、当てはまりの規準だけでは落とせない。")
    for route in ROUTES:
        v = ok_rate[route]
        rep(f"{route}: 雑音が増えると採択率が下がる", len(v) >= 2 and v[-1] < v[0],
            f"{v[0]:.0%} → {v[-1]:.0%}")

    # 選別が効いているかは**雑音を固定して**見る。水準をまたいで採用・不採用を比べると、
    # 低雑音での系統誤差（two_stage は雑音ゼロでも +5.9 ms ずれる）と高雑音での偶然誤差を
    # 比べることになり、交絡する。採否は真値を見ていないので、固定水準での比較は循環しない。
    nz_sel = 0.02
    n_sel = 12 if quick else 30
    print(f"\n       選別と標準誤差の較正（雑音 {nz_sel} に固定・{n_sel} 回）")
    print(f"       {'経路':<12}{'採択率':>8}{'採用のΔT誤差':>14}{'不採用のΔT誤差':>16}"
          f"{'採用のSE中央値':>16}{'採用のΔTのσ':>15}{'成分を増やした割合':>19}")
    for route in ROUTES:
        eo, en, vo, se_o, esc = [], [], [], [], []
        for k in range(n_sel):
            t, y, tr = make_beat(noise=nz_sel, seed=300 + k)
            r = _run(t, y, route)
            if not np.isfinite(r["dt_ms"]):
                continue
            e = abs(r["dt_ms"] - tr["dt_ms"])
            if r["ok"]:
                eo.append(e); vo.append(r["dt_ms"]); esc.append(bool(r["escalated"]))
                if np.isfinite(r["dt_se_ms"]):
                    se_o.append(r["dt_se_ms"])
            else:
                en.append(e)
        mo = float(np.median(eo)) if eo else np.nan
        mn = float(np.median(en)) if en else np.nan
        sm = float(np.median(se_o)) if se_o else np.nan
        # 拍間のばらつきの頑健推定（四分位範囲 ÷ 1.349）。SE がこれと同じ桁なら較正できている
        sig = (float(np.subtract(*np.percentile(vo, [75, 25]))) / 1.349
               if len(vo) >= 4 else np.nan)
        print(f"       {route:<12}{len(eo) / max(len(eo) + len(en), 1):>8.0%}"
              f"{mo:>11.1f} ms{mn:>13.1f} ms{sm:>13.2f} ms{sig:>12.2f} ms"
              f"{np.mean(esc) if esc else np.nan:>19.0%}")
        # 較正の検査。壊れた共分散は 10^5〜10^6 ms を返していたので、この検査は空でない
        rep(f"{route}: ΔT の標準誤差が拍間のばらつきと同じ桁（共分散が壊れていない）",
            np.isfinite(sm) and np.isfinite(sig) and 0.2 <= sm / max(sig, 1e-9) <= 5.0,
            f"SE {sm:.2f} ms 対 拍間σ {sig:.2f} ms（比 {sm / sig:.2f}）"
            if np.isfinite(sm) and np.isfinite(sig) else "推定できず")
    print("       ΔT 誤差の 2 列は**合否にしない**。採否規準は当てはまりを見ており、")
    print("       当てはまりが足りない拍では成分を1つ増やす。増やすと波形は良く合うが")
    print("       反射波が2つに割れ、ΔT は真値から 2 ms ほど遠ざかる。だから採用側のほうが")
    print("       ΔT 誤差が大きくなりうる。系統誤差が偶然誤差より大きいということでもある。")
    print("       症例内の変化を見る本研究では一定の偏りは相殺されるが、**ΔT の絶対値を")
    print("       他研究と比べてはならない**。下流では必ず『成分を増やしたか』で層別すること。")

    # ---- T5 波形型
    print("\nT5 波形型（重複切痕あり／なし）")
    for notch, name in ((True, "切痕あり"), (False, "切痕なし")):
        t, y, tr = make_beat(notch=notch, dt_true=0.28 if notch else 0.08,
                             ri_true=0.45 if notch else 0.60)
        for route in ROUTES:
            r = _run(t, y, route)
            print(f"       {name:<10}{route:<12}型{r['klass']}  ΔT {r['dt_ms']:>7.1f}  "
                  f"誤差 {r['dt_ms'] - tr['dt_ms']:>+7.1f}  Errx {r['errx_ms']:>5.1f}  "
                  f"採用 {r['ok']}  規則 {r['role_rule']}  成分 {r['n_components']}"
                  f"{'（増やした）' if r['escalated'] else ''}")
    t, y, tr = make_beat(notch=False, dt_true=0.08, ri_true=0.60)
    ks = [pda2.find_landmarks(t, pda2.preprocess(t, y, FS)[0])["klass"]]
    rep("切痕の無い波形が型1（明瞭な切痕）と判定されない", ks[0] != 1, f"型 {ks[0]}")

    # ---- T6 採否規準
    print("\nT6 採否規準（Errx）が壊れた当てはめを弾くか")
    t, y, tr = make_beat()
    lm = pda2.find_landmarks(t, pda2.preprocess(t, y, FS)[0])
    ys = pda2.preprocess(t, y, FS)[0]
    good = pda2.acceptance(t, ys, ys, lm)
    shifted = np.interp(t, t + 0.030, ys, left=ys[0], right=ys[-1])   # 30 ms ずらす
    bad = pda2.acceptance(t, ys, shifted, lm)
    rep("同じ波形なら合格", good["ok"], f"Errx {good['errx_ms']:.2f} ms")
    rep("30 ms ずれた波形は不合格", not bad["ok"], f"Errx {bad['errx_ms']:.1f} ms")

    # ---- T7 貯留槽（前処理で線形成分を引くため、植えた τ とは一致しない。役割で検査する）
    print("\nT7 貯留槽（拡張期後半で錨づけ、収縮期を食わないか）")
    t, y, tr = make_beat(tau_res=0.35, d_res=0.40)
    ys, _ = pda2.preprocess(t, y, FS)
    lm = pda2.find_landmarks(t, ys)
    rp = pda2.estimate_reservoir_tau(t, ys, lm)
    rep("時定数の推定窓が拡張期ピークより後にある",
        rp["ok"] and rp["t_a"] > lm["dia_t"],
        f"t_a {rp['t_a']:.3f} s / 拡張期ピーク {lm['dia_t']:.3f} s / τ {rp['tau']:.3f} s")
    r = _run(t, y, "two_stage")
    shape = pda2.reservoir_shape(t, rp["t_a"], rp["tau"])
    d = r["reservoir"].get("d", 0.0)
    rep("貯留槽が収縮期ピークを食っていない",
        d * float(shape[lm["i_sys"]]) < 0.35 * float(ys[lm["i_sys"]]),
        f"収縮期ピークでの割合 {d * shape[lm['i_sys']] / max(ys[lm['i_sys']], 1e-9):.2f}")
    rep("貯留槽の振幅が過大でない（差し引きすぎない）", 0.0 <= d <= 1.0, f"d {d:.3f}")

    print("\n" + ("ALL PASS" if ok_all else "FAIL あり"))
    return 0 if ok_all else 1


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--quick", action="store_true", help="点数を減らして速く回す")
    args = ap.parse_args()
    if args.selftest:
        sys.exit(selftest(quick=args.quick))
    ap.error("--selftest を指定してください")


if __name__ == "__main__":
    main()
