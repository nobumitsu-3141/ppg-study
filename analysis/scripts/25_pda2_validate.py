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
  T7 ランドマーク      心拍 50〜100・切痕あり／なしで鍵点が破綻しないか（dia < sys を作らないか）
  T8 減衰の担い手      合成波の指数減衰を反射波が吸収していないか（幅が膨らんでいないか）
  T9 不変性と高心拍    決定性・時間原点・切り出しずれへの不変性、高心拍での挙動
  T10 役割の割り当て   反射波の選択が僅差のとき曖昧として落ちるか（くじ引きを通さないか）
  T11 一意性の検査     競合解の対応づけ（同じ解・遠い解・ΔT の違う解・対応が潰れた解）
  T12 保護されていなかった修正  7 巡目の独立監査で「元に戻しても落ちる検査が無い」と判った
                       修正に、単体の検査を付ける（曖昧判定の配線・重みの近傍・退化入力・
                       no_se・幅の尺度化・低域通過・境界張り付き）

合成脈波
--------
    y(t) = 前進波（歪みガウス） + 反射波（歪みガウス） + 貯留槽（指数減衰）

貯留槽の時定数は生理的に固定し、**拍長だけを変える**。凍結版は第2カーネルがこれを吸収し、
その位置が拍長に引きずられるはずである。第2版は成分を1つ増やして減衰を担わせる。
**第2版に貯留槽項は無い**（機能しなかったので削除した。`pda2.fit_waves` の説明を参照）。

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


ROUTES = ("skew", "gamma")


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
    rep("ガンマ真値では gamma 経路が skew より良い（2×2 が働いている）",
        abs(t2[("gamma", "gamma")][0]) < abs(t2[("gamma", "skew")][0]),
        f"gamma {t2[('gamma','gamma')][0]:+.1f} 対 skew {t2[('gamma','skew')][0]:+.1f}")
    print("       注: ガンマ基底には Tigges 2017 の定義に無い到達時刻の母数を足してある。")
    print("           これが無いと全成分が拍の先頭から立ち上がり、遅れて届く反射波を表せない。")
    print("       注: ガンマ真値の波は成分の裾が速く（時定数 20〜45 ms）、貯留槽の緩い下降を")
    print("           どちらの経路も表しきれない。両経路とも Errx で不採用になるのが正しい。")
    print("           採否規準そのものが基底の当てはめやすさに依存することを意味する。")
    t, y, tr = make_beat()
    dtf, rif, _ = frozen_indices(t, y)
    rep("**RI の誤差が凍結版より小さい**（歪みガウス真値で比較）",
        abs(t2[("skew", "skew")][1]) < abs(rif - tr["ri"]),
        f"skew {t2[('skew','skew')][1]:+.3f} 対 凍結版 {rif - tr['ri']:+.3f}")

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
    rep("skew の心拍数交絡が凍結版以下",
        np.isfinite(spread["skew"]) and spread["skew"] <= spread["frozen"],
        f"skew {spread['skew']:.1f} ms 対 凍結版 {spread['frozen']:.1f} ms")
    # 7 巡目: gamma の交絡は表示されるだけで合否が無く、到達時刻の母数（rise）を外しても
    # 落ちる検査が無かった。外すと 155 ms に戻るので、凍結版の 2 倍未満を要求する
    rep("gamma の心拍数交絡が凍結版の 2 倍未満（到達時刻の母数が効いている）",
        np.isfinite(spread["gamma"]) and spread["gamma"] < 2.0 * spread["frozen"],
        f"gamma {spread['gamma']:.1f} ms 対 凍結版 {spread['frozen']:.1f} ms")
    print("       注: 本合成では凍結版の交絡が 15 ms 程度にしか出ない。PWDB では ΔT の心拍数主効果が")
    print("           −10.9%（≒38 ms）であり、**合成データは交絡を過小に再現している**。")
    print("           改善の可否を決めるのは PWDB での実測であって、この表ではない。")
    print("       注: gamma の交絡は skew より大きい。到達時刻の母数を足す前は幅 155 ms で")
    print("           完全に破綻していた（足した直後は 55 ms、監査後は 19 ms）。ガンマの裾は形状母数")
    print("           ひとつで立ち上がりと下降の両方を決めるため、拍が短いと下降を優先して形が歪む。")

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
    # 低雑音での系統誤差（skew は雑音ゼロでも +5.9 ms ずれる）と高雑音での偶然誤差を
    # 比べることになり、交絡する。採否は真値を見ていないので、固定水準での比較は循環しない。
    nz_sel = 0.02
    n_sel = 12 if quick else 30
    print(f"\n       選別と標準誤差の較正（雑音 {nz_sel} に固定・{n_sel} 回）")
    print(f"       {'経路':<12}{'採択率':>8}{'採用のΔT誤差':>14}{'不採用のΔT誤差':>16}"
          f"{'採用のSE中央値':>16}{'採用のΔTのσ':>15}{'成分を増やした割合':>19}")
    for route in ROUTES:
        eo, en, vo, se_o, esc = [], [], [], [], []
        sat_all, sat_best = [], []
        for k in range(n_sel):
            t, y, tr = make_beat(noise=nz_sel, seed=300 + k)
            r = _run(t, y, route)
            if "n_starts" in r:
                sat_all.append((r["n_saturated"], r["n_starts"])); sat_best.append(bool(r["best_saturated"]))
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
        if sat_all:
            tot = sum(a for a, _b in sat_all); nst = sum(b for _a, b in sat_all)
            print(f"       {route}: 多点起動の飽和率（max_nfev 到達） 全起動 {tot / max(nst, 1):.1%} / "
                  f"最良解 {np.mean(sat_best):.1%}（監視のみ。採否には使わない）")
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
    # 切痕なし波形の分解は**同定できない**。Errx・Erry を外して 3 波を採用させると ΔT が
    # +50 ms（歪みガウス）／+20 ms（ガンマ）ずれる（当てはまりは NRMSE 0.003 と良い）。
    # 採否規準はこれを正しく落としている。1巡目の「+3.3 ms で採用」は Errx 5.8 ms の際どい通過で、
    # 2巡目の基線の変更で解の盆地が変わり +65 ms になった（6巡目の二分探索で判明。文書を訂正した）。
    # 不変条件は「**採用するなら ΔT 誤差 15 ms 未満**」。不採用であることは要求しない
    # 6巡目の検査で、ガンマ経路が心拍 70 の切痕なし波形を「規準をすべて通して」採用し、ΔT が
    # +23 ms ずれていた（Wald SE 9 ms・競合解の広がり 15 ms で、どちらも誤差を過小に見積もる）。
    # 型3 の分解は同定できないので、規則で採用しない（accept_proxy=False が既定、理由 proxy_landmarks）。
    # 「含める」ときの挙動も並べて、規則が何を落としているかを見えるようにする。
    # 不変条件の閾値は SE_DT_MAX_MS（20 ms）: 採用した ΔT の誤差が、採用の根拠にした不確かさの
    # 上限を超えてはならない（28番の乱数検査 I4 と同じ原則・同じ値）
    print(f"       切痕なし・心拍を振る（既定: 型3 は採用しない。含めた場合と、Errx・Erry も外した場合を併記。"
          f"採用するなら誤差 {pda2.SE_DT_MAX_MS:.0f} ms 未満）")
    print(f"       {'HR':>5} {'経路':<7}{'採用':<6}{'理由':<17}| 型3を含める: 採用   誤差  | Errx・Erry も外す: 成分 採用   誤差")
    inv_ok = True
    proxy_rejected = True
    for hr in ((70,) if quick else (55, 70, 85, 100)):
        t, y, tr = make_beat(hr=hr, notch=False, dt_true=0.08, ri_true=0.60)
        for route in ROUTES:
            r = _run(t, y, route)
            rp = pda2.decompose(t, y, FS, route=route, accept_proxy=True)
            rx = pda2.decompose(t, y, FS, route=route, accept_proxy=True,
                                errx_ms=np.inf, erry_max=np.inf)
            ep = rp["dt_ms"] - tr["dt_ms"]
            ex = rx["dt_ms"] - tr["dt_ms"]
            if r["ok"] and abs(r["dt_ms"] - tr["dt_ms"]) >= pda2.SE_DT_MAX_MS:
                inv_ok = False
            if r["ok"] or r["reason"] != "proxy_landmarks":
                proxy_rejected = False
            print(f"       {hr:>5} {route:<7}{str(r['ok']):<6}{r['reason']:<17}| "
                  f"{str(rp['ok']):<6}{ep:>+7.1f}  | {rx['n_waves']:>4} {str(rx['ok']):<6}{ex:>+7.1f}")
    rep("型3（切痕なし）は理由 proxy_landmarks で採用されない", proxy_rejected)
    rep(f"採用された ΔT は誤差 {pda2.SE_DT_MAX_MS:.0f} ms 未満（誤った ΔT を黙って通さない）", inv_ok)
    print("       注: 型3 を含めると、規準をすべて通った当てはめでも ΔT が +20 ms 以上ずれる拍がある。")
    print("           型3 で PDA の ΔT が得られないことは第2版の限界として先に書いておく。")

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
    # 7 巡目: データが型1（極値）なのに模型側に極値が無い場合、代用点で合わせてはいけない（E3）。
    # 模型側の鍵点が消えたことを Errx の罰則で落とす
    t3, y3, _ = make_beat(notch=False, dt_true=0.08, ri_true=0.60)
    y3s = pda2.preprocess(t3, y3, FS)[0]
    yhat3 = np.interp(t, t3, y3s, right=0.0)                 # 切痕の無い波形を模型側に置く
    mis = pda2.acceptance(t, ys, yhat3, lm)
    rep("データが型1で模型に極値が無ければ鍵点は一致せず不合格（代用点で合わせない: E3）",
        (not mis["ok"]) and mis["n_landmark_matched"] < 3, f"一致 {mis['n_landmark_matched']}/3")
    # 切痕の振幅が Erry に入っている（E2）: 切痕の値だけ 0.02 上げた波形は Erry で落ちる
    yb = ys.copy()
    i_n = int(np.argmin(np.abs(t - lm["notch_t"])))
    yb[max(0, i_n - 8): i_n + 9] += 0.02
    e2 = pda2.acceptance(t, ys, yb, lm)
    rep("切痕の振幅のずれ 0.02 は Erry で不合格（E2: Erry に切痕を含む）",
        (not e2["ok"]) and e2["erry"] > pda2.ERRY, f"Erry {e2['erry']:.3f}")

    # ---- T7 ランドマーク
    print("\nT7 ランドマーク（心拍 50〜100・切痕あり／なし）")
    print(f"       {'HR':>4}{'切痕':>6}{'型':>4}{'S[ms]':>8}{'notch':>8}{'dia':>8}{'真dia':>8}{'誤差':>8}")
    bad_order = 0
    err_notch, err_plain = [], []
    for notch in (True, False):
        for hr in (50, 70, 85, 100):
            dt_true = 0.28 if notch else 0.08
            t, y, tr = make_beat(hr=hr, notch=notch, dt_true=dt_true,
                                 ri_true=0.45 if notch else 0.60)
            ys, _ = pda2.preprocess(t, y, FS)
            lm = pda2.find_landmarks(t, ys)
            true_dia = (0.12 + dt_true) * 1000.0
            e = (lm["dia_t"] * 1000.0 - true_dia) if np.isfinite(lm["dia_t"]) else np.nan
            (err_notch if notch else err_plain).append(abs(e))
            if np.isfinite(lm["dia_t"]) and lm["dia_t"] <= lm["sys_t"]:
                bad_order += 1
            print(f"       {hr:>4}{'あり' if notch else 'なし':>6}{lm['klass']:>4}"
                  f"{lm['sys_t'] * 1000:>8.1f}{lm['notch_t'] * 1000:>8.1f}"
                  f"{lm['dia_t'] * 1000:>8.1f}{true_dia:>8.0f}{e:>+8.1f}")
    rep("拡張期の鍵点が収縮期ピークより前に来ることがない（旧・型4の欠陥）", bad_order == 0)
    rep("切痕ありの波形で拡張期ピークの誤差が 15 ms 未満（心拍 50〜100）",
        all(np.isfinite(err_notch)) and max(err_notch) < 15.0, f"最大 {max(err_notch):.1f} ms")
    rep("切痕なしの波形でも代用点が定義でき、誤差が 40 ms 未満",
        all(np.isfinite(err_plain)) and max(err_plain) < 40.0,
        f"最大 {max(err_plain):.1f} ms（肩は構造的に真のピークより遅れる）")
    # 反射波が無く単調に減衰する波形は肩を持たない。肩の顕著さを片側で測っていたときは、
    # 平坦になった裾の微小な揺らぎが「肩」に化けて型3になっていた（6巡目 K8）
    k4 = []
    for hr in (55, 85):
        t, y, tr = make_beat(hr=hr, ri_true=0.0, d_res=0.0)
        lm = pda2.find_landmarks(t, pda2.preprocess(t, y, FS)[0])
        k4.append((lm["klass"], lm["prom"]))
    rep("反射波の無い単調減衰は肩（型3）に化けず型4になる",
        all(k == 4 for k, _p in k4), f"型 {[k for k, _p in k4]} 顕著さ {[round(p_, 3) for _k, p_ in k4]}")

    # ---- T8 減衰の担い手
    print("\nT8 減衰の担い手（合成波の指数減衰 d=0.40, τ=0.35 を反射波が吸収していないか）")
    t, y, tr = make_beat(tau_res=0.35, d_res=0.40)
    r = _run(t, y, "skew")
    ys, _ = pda2.preprocess(t, y, FS)
    lm = pda2.find_landmarks(t, ys)
    # 反射波の真の幅: skew_peak(w=0.065, α=1.2) → σ = ω·sqrt(1−2δ²/π)
    sd_true = pda2.component_sd("skew", 0.065, 1.2) * 1000.0
    sd_ref = np.nan
    if r.get("peaks") is not None and r.get("ok") is not None:
        rr = pda2.decompose(t, y, FS, route="skew")
        # indices() は幅を返さないので、分解をやり直して成分の幅を読む
        fit = pda2.fit_waves(t, ys, lm, n_waves=rr["n_waves"], w=pda2._weights(t, lm))
        x = fit["sols"][0].x
        peaks = [(x[4 * k + 1], x[4 * k]) for k in range(rr["n_waves"])]
        roles = pda2.assign_roles(peaks, lm, has_reservoir_kernel=True, t=t)
        k = roles["reflected"]
        if k is not None:
            sd_ref = pda2.component_sd("skew", x[4 * k + 2], x[4 * k + 3]) * 1000.0
    print(f"       採用 {r.get('ok')}  成分 {r.get('n_waves')}  増やした {r.get('escalated')}  "
          f"ΔT {r.get('dt_ms', float('nan')):.1f}（真 {tr['dt_ms']:.0f}）  "
          f"反射波の幅 σ {sd_ref:.1f} ms（真 {sd_true:.1f}）")
    rep("減衰を含む合成波でも採用される", bool(r.get("ok")))
    rep("反射波の幅が真値の 2 倍未満（減衰を反射波が吸収していない）",
        np.isfinite(sd_ref) and sd_ref < 2.0 * sd_true, f"{sd_ref:.1f} 対 {sd_true:.1f} ms")

    # ---- T9 不変性と高心拍
    print("\nT9 不変性と高心拍")
    t, y, tr = make_beat(hr=70, noise=0.01, seed=7)
    r1 = _run(t, y, "skew"); r2 = _run(t, y, "skew"); r3 = pda2.decompose(t + 5.0, y, FS, route="skew")
    rep("同じ入力で同じ出力（決定性）", r1["dt_ms"] == r2["dt_ms"] and r1["ri"] == r2["ri"])
    # ランドマーク・初期値・境界は原点に対して厳密に不変。残るのは最適化の丸め（4e-6 ms 程度）なので
    # 許容は 1e-3 ms / 1e-6 とする（生理的な尺度より 1000 倍厳しい）
    rep("時間軸の原点に依存しない（最適化の丸めを除く）",
        abs(r1["dt_ms"] - r3["dt_ms"]) < 1e-3 and abs(r1["ri"] - r3["ri"]) < 1e-6,
        f"|ΔΔT| {abs(r1['dt_ms'] - r3['dt_ms']):.1e} ms, |ΔRI| {abs(r1['ri'] - r3['ri']):.1e}")
    # 切り出し位置のずれ（onset が 0〜8 ms 遅い）。ΔT は時刻の差なので不変、RI は基線に依存する。
    # 前方のずれだけを検査する。合成波は周期的でない（末尾が足に戻らない）ので、前に継ぎ足すと
    # 継ぎ目に段差が出て検査側の人工物になる。onset が遅れる方向が実際の切り出し誤差でも多い
    dts, ris = [], []
    for sh in (0, 2, 4):
        seg = y[sh:]
        r = pda2.decompose(np.arange(len(seg)) / FS, seg, FS, route="skew")
        dts.append(r["dt_ms"]); ris.append(r["ri"])
    rep("切り出しが 0〜8 ms 遅れても ΔT は 1 ms 以内", np.ptp(dts) < 1.0, f"幅 {np.ptp(dts):.2f} ms")
    rep("切り出しが 0〜8 ms 遅れても RI は 0.05 以内（足→足の基線）", np.ptp(ris) < 0.05, f"幅 {np.ptp(ris):.3f}")
    # 高心拍: 成分が重なって分解が同定できなくなる。黙って採用せず、理由つきで落とすこと
    print(f"       {'HR':>5}{'ΔT':>8}{'真':>6}{'Wald SE':>9}{'競合広がり':>11}{'採用':>6}  理由")
    hi_ok = True
    for hr in (100, 120, 130, 150):
        tt, yy, trr = make_beat(hr=hr, dt_true=min(0.28, 0.45 * 60 / hr), ri_true=0.45)
        r = pda2.decompose(tt, yy, 1 / (tt[1] - tt[0]), route="skew")
        print(f"       {hr:>5}{r['dt_ms']:>8.1f}{trr['dt_ms']:>6.0f}{r['dt_se_ms']:>9.1f}"
              f"{r['dt_spread_ms']:>11.1f}{str(r['ok']):>6}  {r['reason']}")
        if hr >= 130 and r["ok"]:
            hi_ok = False
    rep("心拍 130 以上（成分が重なる）では理由つきで不採用になる", hi_ok)
    print("       注: 心拍 130 では Wald の標準誤差が桁違いに膨らむ（ブートストラップ 15 ms に対し 709 ms）。")
    print("           条件数は採用例でも 1e5 に達し良否を分けない。競合解の広がりを併記して判定する。")

    # ---- T10 役割の割り当て
    print("\nT10 役割の割り当て（反射波の選択がくじ引きになっていないか）")
    t, y, tr = make_beat(hr=70, dt_true=0.28, ri_true=0.45)
    ys, _ = pda2.preprocess(t, y, FS)
    lm = pda2.find_landmarks(t, ys)
    # 拡張期の鍵点からほぼ等距離に2つの成分がある場合、選択は実質くじ引きで ΔT はその差だけ動く
    dia = lm["dia_t"]
    peaks_tie = [(0.12, 1.0), (dia - 0.005, 0.5), (dia + 0.005, 0.48)]
    peaks_clear = [(0.12, 1.0), (dia - 0.002, 0.5), (dia + 0.15, 0.2)]
    r_tie = pda2.assign_roles(peaks_tie, lm, has_reservoir_kernel=True, t=t)
    r_clear = pda2.assign_roles(peaks_clear, lm, has_reservoir_kernel=True, t=t)
    print(f"       僅差:   規則 {r_tie['rule']:>9}  gap {r_tie['ref_gap_ms']:5.1f} ms  "
          f"余裕 {r_tie['ref_margin_ms']:6.1f} ms")
    print(f"       明瞭:   規則 {r_clear['rule']:>9}  gap {r_clear['ref_gap_ms']:5.1f} ms  "
          f"余裕 {r_clear['ref_margin_ms']:6.1f} ms")
    rep("僅差の割り当ては ΔT の SE 上限より小さい余裕として記録される",
        np.isfinite(r_tie["ref_margin_ms"]) and r_tie["ref_margin_ms"] < pda2.SE_DT_MAX_MS,
        f"{r_tie['ref_margin_ms']:.1f} ms < {pda2.SE_DT_MAX_MS:.0f} ms")
    rep("明瞭な割り当ては余裕が十分に大きい",
        r_clear["ref_margin_ms"] >= pda2.SE_DT_MAX_MS, f"{r_clear['ref_margin_ms']:.1f} ms")
    rep("成分が2つのときは規則が single になり、余裕は無限大",
        pda2.assign_roles([(0.12, 1.0), (0.40, 0.5)], lm,
                          has_reservoir_kernel=True, t=t)["rule"] == "single")
    # 前進波が第0スロットでない解は曖昧に倒れる
    bad = pda2.assign_roles([(0.40, 0.5), (0.12, 1.0)], lm, has_reservoir_kernel=True, t=t)
    rep("ピーク時刻が最小の成分が前進波（スロット順ではなく時刻順）", bad["forward"] == 1)

    # ---- T11 一意性の検査（競合解の対応づけ）
    print("\nT11 一意性の検査（競合解の対応づけ）")
    from types import SimpleNamespace as NS
    x0 = np.array([1.0, 0.12, 0.05, 2.0, 0.45, 0.40, 0.07, 1.0])   # 2 成分 (h, tp, w, α) × 2
    best = NS(x=x0, cost=1.0)
    same = NS(x=x0.copy(), cost=1.05)
    far = NS(x=x0.copy(), cost=2.0); far.x[5] = 0.30              # 残差が大きい → 競合ではない
    near = NS(x=x0.copy(), cost=1.10); near.x[5] = 0.43            # 競合で ΔT が 30 ms 違う
    coll = NS(x=x0.copy(), cost=1.10); coll.x[1] = 0.40; coll.x[5] = 0.41   # 両成分が反射波の位置に潰れた
    roles = {"forward": 0, "reflected": 1}
    rep("同じ解しか無ければ曖昧でない", not pda2._ambiguous([best, same], 4, roles))
    rep("残差が許容（1.15 倍）を超える解は競合とみなさない", not pda2._ambiguous([best, far], 4, roles))
    rep("競合解の ΔT が 20 ms 以上違えば曖昧", pda2._ambiguous([best, near], 4, roles),
        f"広がり {pda2.competing_spread_ms([best, near], 4, roles):.0f} ms")
    rep("対応づけが潰れた競合解（広がり inf）は曖昧（6巡目 K5: 以前は inf を曖昧でないと扱っていた）",
        pda2._ambiguous([best, coll], 4, roles) and np.isinf(pda2.competing_spread_ms([best, coll], 4, roles)))
    rep("残差許容を緩めると遠い解も競合になる（tol_cost が効く）",
        pda2._ambiguous([best, far], 4, roles, tol_cost=2.5))
    rep("ΔT の許容を広げると曖昧でなくなる（tol_dt_ms が効く）",
        not pda2._ambiguous([best, near], 4, roles, tol_dt_ms=50.0))

    # ---- T12 保護されていなかった修正（7 巡目の独立監査で見つかった検査の穴）
    print("\nT12 保護されていなかった修正の検査")
    # 曖昧判定の合成（decompose の配線）: 僅差の反射波・前進波がスロット 0 でない → 曖昧（G1・R2）
    roles_ok = {"forward": 0, "reflected": 1, "ref_margin_ms": np.inf}
    rep("曖昧判定の合成: 明瞭な解は曖昧でない",
        not pda2.ambiguity_flags([best], 4, roles_ok))
    rep("曖昧判定の合成: 反射波の候補が僅差（5 ms）なら曖昧（G1 の配線）",
        pda2.ambiguity_flags([best], 4, {"forward": 0, "reflected": 1, "ref_margin_ms": 5.0}))
    rep("曖昧判定の合成: 前進波がスロット 0 でなければ曖昧（R2 の配線）",
        pda2.ambiguity_flags([best], 4, {"forward": 1, "reflected": 0, "ref_margin_ms": np.inf}))
    rep("曖昧判定の合成: 僅差の下限は tol_dt_ms で動く（3 か所同じ値: K4）",
        not pda2.ambiguity_flags([best], 4, {"forward": 0, "reflected": 1, "ref_margin_ms": 5.0},
                                 tol_dt_ms=3.0))
    # 鍵点の重みの近傍は時間で指定（B2）: 40 Hz でも近傍が数十 ms に収まる
    t, y, tr = make_beat()
    ys, _ = pda2.preprocess(t, y, FS)
    lm = pda2.find_landmarks(t, ys)
    t40 = np.arange(0, t[-1], 1 / 40.0)
    y40 = np.interp(t40, t, ys)
    lm40 = pda2.find_landmarks(t40, y40)
    w40 = pda2._weights(t40, lm40)
    i_s = int(np.argmax(y40))
    blk = np.flatnonzero(w40 > 1)
    seg = blk[(blk >= i_s - 10) & (blk <= i_s + 10)]
    width_s = (seg.max() - seg.min() + 1) / 40.0 if seg.size else np.nan
    rep("鍵点の重みの近傍は 40 Hz でも 0.1 s 未満（標本数ではなく時間で指定: B2）",
        np.isfinite(width_s) and width_s < 0.10, f"{width_s * 1000:.0f} ms")
    # 退化した入力は例外を出さず理由 amplitude（R1）
    bad_inputs = {"全 NaN": np.full_like(t, np.nan), "定数": np.ones_like(t),
                  "内部 NaN": np.where(np.arange(t.size) == 100, np.nan, y),
                  "inf": np.where(np.arange(t.size) == 100, np.inf, y)}
    r1_ok = True
    for name, yy in bad_inputs.items():
        try:
            r = pda2.decompose(t, yy, FS, route="skew")
            if r.get("reason") != "amplitude" or r.get("ok"):
                r1_ok = False
        except Exception:                                # noqa: BLE001
            r1_ok = False
    try:
        r = pda2.decompose(t[:5], y[:5], FS, route="skew")
        r1_ok &= (r.get("reason") == "amplitude")
    except Exception:                                    # noqa: BLE001
        r1_ok = False
    rep("退化した入力（NaN・定数・内部 NaN・inf・5 標本）は例外を出さず理由 amplitude（R1）", r1_ok)
    # 7 巡目の独立監査: fs=inf で例外、fs=0・NaN で低域通過が黙って外れていた。
    # fs・t の検証で理由 bad_input になること、t を ms で渡す誤りも bad_input で止まること
    bad_fs = True
    for fs_bad in (np.inf, 0.0, np.nan, -500.0):
        try:
            r = pda2.decompose(t, y, fs_bad, route="skew")
            bad_fs &= (r.get("reason") == "bad_input") and not r.get("ok")
        except Exception:                                # noqa: BLE001
            bad_fs = False
    try:
        r = pda2.decompose(t * 1000.0, y, FS, route="skew")
        bad_fs &= (r.get("reason") == "bad_input")
        r = pda2.decompose(t[::-1], y, FS, route="skew")
        bad_fs &= (r.get("reason") == "bad_input")
    except Exception:                                    # noqa: BLE001
        bad_fs = False
    rep("fs が inf・0・NaN・負、t が ms や逆順なら例外を出さず理由 bad_input", bad_fs)
    # 内部の標本化周波数を 500 Hz にそろえる: 100 Hz の拍でも型・採否・ΔT が 500 Hz と一致する
    t100 = np.arange(0, t[-1], 1 / 100.0)
    y100 = np.interp(t100, t, y)
    r500 = pda2.decompose(t, y, FS, route="skew")
    r100 = pda2.decompose(t100, y100, 100.0, route="skew")
    rep("100 Hz の拍は内部で 500 Hz に再標本化され、採否と ΔT（2 ms 以内）が 500 Hz と一致する",
        r100.get("ok") == r500.get("ok") and r100.get("klass") == r500.get("klass")
        and abs(r100.get("dt_ms", np.nan) - r500.get("dt_ms", np.nan)) < 2.0,
        f"ΔT {r500.get('dt_ms', np.nan):.1f} 対 {r100.get('dt_ms', np.nan):.1f} ms")
    # 共分散が計算できない拍は no_se（K6）: 共分散を None にして配線を確かめる
    orig = pda2._peaks_and_se

    def _no_cov(*a, **k):
        pk, cov, step, sds = orig(*a, **k)
        return pk, None, step, sds
    pda2._peaks_and_se = _no_cov
    try:
        r = pda2.decompose(t, y, FS, route="skew")
    finally:
        pda2._peaks_and_se = orig
    rep("共分散が計算できない拍は理由 no_se で不採用（K6）",
        (not r["ok"]) and r["reason"] == "no_se" and not np.isfinite(r["dt_se_ms"]))
    # 幅の探索範囲は拍長で尺度化（D4）
    lo1, hi1, _ = pda2._wave_bounds(np.arange(0, 0.6, 1 / FS), 2)
    lo2, hi2, _ = pda2._wave_bounds(np.arange(0, 1.2, 1 / FS), 2)
    rep("幅の探索範囲が拍長に比例する（D4: T/T_REF で尺度化）",
        np.isclose(hi2[2] / hi1[2], 2.0, rtol=0.02) and np.isclose(lo2[2] / lo1[2], 2.0, rtol=0.02),
        f"上限 {hi1[2] * 1000:.0f} → {hi2[2] * 1000:.0f} ms")
    # 18 Hz 低域通過が効いている
    y_hf = y + 0.05 * np.sin(2 * np.pi * 40.0 * t)
    d_hf = float(np.max(np.abs(pda2.preprocess(t, y_hf, FS)[0] - ys)))
    rep("40 Hz の成分（振幅 0.05）は前処理で 0.01 未満に落ちる（18 Hz 低域通過）", d_hf < 0.01,
        f"残差 {d_hf:.4f}")
    # 境界張り付きの検出（1c の探索範囲が解を決めていないかの監視）
    lo, hi, _ = pda2._wave_bounds(t, 2)
    xp = (lo + hi) / 2.0
    xp[2] = hi[2]                       # 幅を上限に張り付ける
    xp[3] = lo[3]                       # α=0 は正当（数えない）
    pins = pda2.pinned_params(NS(x=xp), lo, hi, "skew")
    rep("境界に張り付いた母数を検出し、α=0 は数えない", pins == ["0:w:hi"], f"{pins}")
    r = pda2.decompose(t, y, FS, route="skew")
    rep("decompose が張り付きの数と内訳を返す", "n_pinned" in r and "pinned" in r,
        f"n_pinned={r.get('n_pinned')} {r.get('pinned')!r}")

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
