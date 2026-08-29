#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""モニタの信号処理のうち、何が RI を壊し ΔT を残すのかを合成波形で特定する。

なぜ必要か
----------
実データ（VitalDB, 成人566例）で、ΔT は既知の生理（加齢・高血圧）を再現したのに
RI は年齢と完全に無関係だった。表示用に処理された脈波チャネルであることが原因と
考えられるが、「自動利得制御が振幅情報を壊す」という説明は雑である。

実際、**一律の利得正規化では RI は壊れない**。RI は同一拍内の2成分のピーク高さの
比なので、拍全体を同じ倍率で拡縮しても比は不変だからである。したがって
「AGCのせい」と書くなら、どの種類の処理なら犯人になりうるのかを特定せねばならない。

真値既知の合成波形に各処理をかけ、ΔT と RI の復元誤差を測って切り分ける。

位置づけ
--------
SAP v0.3 凍結後に追加した探索的解析。実データには一切触れず、主解析の定義にも
影響しない。所見と整合する機序の候補を絞るための機構実験である。

使い方
------
    python scripts/08_processing_effects.py
    python scripts/08_processing_effects.py --n 48
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.synth import make_beat            # noqa: E402
from src.pda import fit_beat               # noqa: E402
from src.indices import si_ri_from_fit     # noqa: E402

FS = 500.0
DT_BAD_MS = 10.0     # ΔT がこれ以上ずれたら「壊れた」
RI_BAD_PCT = 20.0    # RI がこれ以上ずれたら「壊れた」


def highpass(y: np.ndarray, fs: float, fc: float) -> np.ndarray:
    """1次の高域通過（位相ずれを避けるため零位相で適用）。"""
    from scipy.signal import butter, filtfilt
    b, a = butter(1, fc / (fs / 2), btype="highpass")
    return filtfilt(b, a, y)


def fast_agc(y: np.ndarray, fs: float, tau: float) -> np.ndarray:
    """時定数 tau の包絡線で割る「拍内で時変する利得制御」。

    tau が拍長に比べ十分長ければ一律利得に漸近し、短いほど拍の内部で
    利得が動く（＝成分ごとに異なる倍率がかかる）。
    """
    env = np.abs(y - np.median(y))
    k = max(int(tau * fs), 3)
    ker = np.ones(k) / k
    sm = np.convolve(np.pad(env, (k, k), mode="edge"), ker, mode="same")[k:-k]
    sm = np.maximum(sm, 1e-6 * float(np.max(sm)) + 1e-12)
    return y / sm * float(np.mean(sm))


def evaluate(fn, n: int) -> dict:
    """処理 fn をかけた合成拍から ΔT・RI を復元し、真値との誤差を返す。"""
    e_dt, e_ri, ok = [], [], 0
    for i in range(n):
        T = 0.72 + 0.015 * i
        t, y, truth = make_beat(preset="clear_notch", fs=FS, T=T,
                                noise=0.004, drift=0.004, seed=1000 + i)
        fit = fit_beat(t, fn(np.asarray(y, float)), seed=i)
        if not fit.get("ok"):
            continue
        ok += 1
        m = si_ri_from_fit(fit)
        e_dt.append(1000.0 * (m["dt_s"] - truth["dt"]))
        e_ri.append(100.0 * (m["ri"] - truth["ri"]) / truth["ri"])
    if not e_dt:
        return {"n_ok": 0, "n": n}
    return {"n_ok": ok, "n": n,
            "dt_ms": float(np.median(e_dt)), "ri_pct": float(np.median(e_ri))}


def verdict(r: dict) -> str:
    if r["n_ok"] == 0:
        return "当てはめが収束しない（誤ったRIではなく棄却として現れる）"
    if r["n_ok"] < 0.5 * r["n"]:
        return f"収束率が半減（{r['n_ok']}/{r['n']}）— 主に棄却として現れる"
    dt_bad = abs(r["dt_ms"]) > DT_BAD_MS
    ri_bad = abs(r["ri_pct"]) > RI_BAD_PCT
    if not dt_bad and not ri_bad:
        return "ΔT・RIとも保持"
    if ri_bad and not dt_bad:
        return "★ RIのみ破壊（実データの所見と一致）"
    if dt_bad and not ri_bad:
        return "ΔTのみ破壊"
    return "両方破壊"


def decimate(t: np.ndarray, y: np.ndarray, fs_new: float) -> tuple:
    """アンチエイリアス後に等間隔で間引く（実機の数値出力を模す）。"""
    from scipy.signal import butter, filtfilt
    if fs_new >= FS:
        return t, y
    b, a = butter(4, 0.4 * fs_new / (FS / 2), btype="low")
    ylp = filtfilt(b, a, y)
    step = int(round(FS / fs_new))
    return t[::step], ylp[::step]


def sampling_sweep(n: int) -> None:
    """実機から取り出せる間隔で ΔT・RI が復元できるかを調べる。

    実機（日本光電）からは生波形ではなくフィルタ後の数値列しか出せない。
    間隔が 0.004 秒なら 250 Hz、0.04 秒なら 25 Hz であり、後者では
    1拍あたり約20点しかない。2カーネル(8パラメータ)を同定できるかを確かめる。
    """
    print("\n=== サンプリング間隔の影響（実機からの数値出力を想定） ===")
    print(f"{'fs [Hz]':>8}{'間隔':>10}{'1拍の点数':>10}{'ΔT誤差':>12}"
          f"{'ΔT のばらつき':>14}{'RI誤差':>10}{'収束':>9}")
    print("-" * 76)
    for fs_new in (500, 250, 125, 100, 50, 25):
        e_dt, e_ri, ok, npts = [], [], 0, []
        for i in range(n):
            T = 0.72 + 0.012 * i
            t_, y_, truth = make_beat(preset="clear_notch", fs=FS, T=T,
                                      noise=0.004, drift=0.004, seed=2000 + i)
            td, yd = decimate(np.asarray(t_, float), np.asarray(y_, float), fs_new)
            npts.append(len(td))
            try:
                fit = fit_beat(td, yd, seed=i)
            except Exception:
                continue
            if not fit.get("ok"):
                continue
            ok += 1
            m = si_ri_from_fit(fit)
            e_dt.append(1000.0 * (m["dt_s"] - truth["dt"]))
            e_ri.append(100.0 * (m["ri"] - truth["ri"]) / truth["ri"])
        if not e_dt:
            print(f"{fs_new:>8}{1/fs_new:>9.3f}s{int(np.mean(npts)):>10}"
                  f"{'収束せず':>12}{'':>14}{'':>10}{ok:>4}/{n}")
            continue
        dt = np.array(e_dt)
        iqr = float(np.percentile(dt, 75) - np.percentile(dt, 25))
        print(f"{fs_new:>8}{1/fs_new:>9.3f}s{int(np.mean(npts)):>10}"
              f"{np.median(dt):>+9.1f}ms{iqr:>11.1f}ms"
              f"{np.median(e_ri):>+8.1f}%{ok:>4}/{n}")
    print("\n  読み方: ΔT誤差が一定の偏り（ばらつきが小さい）なら、本研究は症例内の")
    print("  変化量しか使わないので較正点との差で相殺される。装置遅延と同じ扱いになる。")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--n", type=int, default=32, help="条件あたりの拍数")
    ap.add_argument("--sampling", action="store_true",
                    help="サンプリング間隔の影響のみを調べる")
    args = ap.parse_args()

    if args.sampling:
        sampling_sweep(args.n)
        return

    conds = [
        ("生波形（対照）", lambda y: y),
        ("一律の利得正規化", lambda y: (y - y.min()) / max(float(np.ptp(y)), 1e-12)),
        ("高域通過 0.3 Hz", lambda y: highpass(y, FS, 0.3)),
        ("高域通過 0.5 Hz", lambda y: highpass(y, FS, 0.5)),
        ("高域通過 1.0 Hz", lambda y: highpass(y, FS, 1.0)),
    ]
    for tau in (1.00, 0.50, 0.25, 0.10):
        conds.append((f"拍内AGC τ={tau:.2f}s", lambda y, tau=tau: fast_agc(y, FS, tau)))

    print("\n=== モニタ処理が脈波分解指標に与える影響（合成波形・真値既知） ===")
    print(f"条件あたり {args.n} 拍。判定基準: |ΔT誤差|>{DT_BAD_MS:.0f}ms または "
          f"|RI誤差|>{RI_BAD_PCT:.0f}%\n")
    print(f"{'条件':<22}{'ΔT誤差':>10}{'RI誤差':>10}{'収束':>9}   判定")
    print("-" * 80)
    for name, fn in conds:
        r = evaluate(fn, args.n)
        if r["n_ok"] == 0:
            print(f"{name:<22}{'—':>10}{'—':>10}{0:>5}/{r['n']:<3}   {verdict(r)}")
            continue
        print(f"{name:<22}{r['dt_ms']:>+8.1f}ms{r['ri_pct']:>+8.1f}%"
              f"{r['n_ok']:>5}/{r['n']:<3}   {verdict(r)}")

    print("\n--- 読み方 ---")
    print("  一律の利得正規化で RI が保たれるのは、RI が同一拍内の2成分の比であり")
    print("  拍全体を同じ倍率で拡縮しても不変だからである。よって実データで観察された")
    print("  『ΔTは妥当だがRIだけ生理と無関係』を説明できるのは、拍の内部で利得が")
    print("  時間変化する処理に限られる。高域通過は強くかけると当てはめ自体が収束せず、")
    print("  誤ったRIではなく棄却として現れるため、今回の所見の説明にはならない。")
    print("\n  注意: これは所見と整合する機序を絞り込む機構実験であり、")
    print("        VitalDB が実際にこの処理を行っている証拠ではない。")

    sampling_sweep(args.n)


if __name__ == "__main__":
    main()
