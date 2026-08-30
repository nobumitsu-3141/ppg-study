#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""研究1b: 動脈圧波形由来の指標と PWTT の分解（SAP凍結後の探索的解析）。

なぜ必要か
----------
研究1は「末梢PPG由来の血管指標では症例内のΔPWTTを説明できない」で終わった。
残る問いは2つある。

  B-1  そもそも ΔPWTT は動脈伝播時間の現象なのか（PEPが支配していないか）
  B-2  PPGの測定限界なのか、概念そのものの限界なのか

PWTT の分解
-----------
  T1 = R波 → 橈骨動脈圧の立ち上がり        = PEP + 中枢動脈伝播
  T2 = R波 → PPG立ち上がり（主解析の pwtt） = PEP + 中枢 + 末梢 + 装置遅延
  T2 − T1                                   = 末梢動脈区間 + 装置遅延

装置遅延（中央値660ms・IQR 644–676）は症例内で定数なので **症例内Δでは相殺される**。
よって Δ(T2−T1) は PEP を一切含まない純粋な末梢動脈伝播時間の変化になる。
ΔPWTT のうち Δ(T2−T1) が説明する割合が小さければ、ΔPWTT は PEP＋中枢が支配している。

動脈圧チャネルは SNUADC が変換器出力を直接デジタル化したもので、パルスオキシメータ
モジュールのような内部処理を経ない。よって AGC・帯域制限（機構実験で RI を +61%
壊した拍内ゲイン τ≈0.25s）から自由であり、B-2 の切り分けに使える。

出力
----
data/features_art/case_{id}.csv … 主解析と同じ t0 で1行
  t1_ms      R波→動脈圧立ち上がり の中央値 [ms]        ← B-1 の核
  dpdt_max   最大上昇速度の中央値 [mmHg/s]              ← 頑健
  tau_ms     拡張期下降時定数 RC の中央値 [ms]          ← 頑健
  sbp/dbp/pp 収縮期・拡張期・脈圧 [mmHg]
  art_dt_ms / art_ri   （--pda 指定時のみ・**未検証**）動脈圧波形にPDAを当てた ΔT・RI

いまの到達点と制約
------------------
軽量モード（T1・dP/dt_max・τ・圧）は合成データで検証済み（--selftest）。
**PDAモードはまだ使えない**。凍結済みの2カーネルPDAを動脈圧波形に当てると σ が
上限に張り付き、収束検算で全滅する（合成データで確認）。貯留槽（Windkessel）成分を
カーネルが吸収しようとするためで、両端を通す指数を引く簡易な excess pressure 分離では
足りない。B-2 の「動脈圧PDAとPPG PDAの直接比較」は、駆出中に立ち上がる貯留槽成分まで
含めた分離を設計・検証してから行うこと。
それまでの B-2 は τ（=RC）と dP/dt_max で代替する。どちらも動脈圧から直接得られ、
AGC・帯域制限の影響を受けない。

使い方
------
軽量モード（PDAなし・I/O律速。変種抽出と並行して走らせても邪魔にならない）:
    nohup caffeinate -i python scripts/15_art_indices.py --limit 874 --jobs 2 \
      > art_run.log 2>&1 &

PDAあり（主解析と同程度のCPUを食う。変種抽出の完走後に走らせること）:
    python scripts/15_art_indices.py --limit 874 --jobs 8 --pda

合成データでの自己検証（ネットワーク不要・数秒）:
    python scripts/15_art_indices.py --selftest
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.beats import (segment_beats, sqi, ensemble_average,      # noqa: E402
                       estimate_noise, required_ensemble_size)
from src.indices import detect_r_peaks, pleth_onset_after, si_ri_from_fit  # noqa: E402
from src.pda import fit_beat                                      # noqa: E402

FS = 500.0
WIN_S = 60.0
DATA = Path(__file__).resolve().parent.parent / "data"
FEAT = DATA / "features"
AFEAT = DATA / "features_art"
META_V = 1

# R波→橈骨動脈 foot の生理的な範囲 [s]。PEP 約80–120ms＋大動脈→橈骨 約60–100ms。
# 動脈圧チャネルには装置遅延が無いはずなので、折り返し展開は行わない。
# 中央値がこの帯の外に出るようなら前提が崩れているので、集計時に警告する。
T1_RANGE = (0.04, 0.40)
T1_EXPECT = (0.10, 0.30)

# 拡張期の切り出しは拍長の固定割合にする。切痕検出は動脈硬化例で破綻するため使わない
# （DN-less の問題そのもの）。HR 50–100 拍/分ではこの範囲は拡張期に収まる。
DIAS_FRAC = (0.55, 0.90)
TAU_MIN_R2 = 0.90


# ---------------------------------------------------------------- 拍レベル
def _t1_series(seg_a: np.ndarray, seg_e: np.ndarray, fs: float) -> np.ndarray:
    """R波ごとの R→動脈圧立ち上がり [s]。"""
    out = []
    for i in detect_r_peaks(seg_e, fs):
        f = pleth_onset_after(seg_a, fs, int(i), win_s=0.5)
        if f is None:
            continue
        v = (f - int(i)) / fs
        if T1_RANGE[0] < v < T1_RANGE[1]:
            out.append(v)
    return np.asarray(out, dtype=float)


def _tau_ms(beat: np.ndarray, fs: float) -> float:
    """拡張期下降の時定数 τ=RC [ms]。P(t)=P_inf+(P0−P_inf)·exp(−t/τ) を当てる。

    P_inf を 0 に固定すると、拡張期圧の床のぶん τ が大きく出るうえ真の τ への
    感度が潰れる（合成データで確認: 真値1000/1800/3000ms が 4095/4500/5538ms に
    圧縮された）。そこで P_inf を格子探索し、対数線形の当てはまりが最良になる
    値を採る。非線形3変数の当てはめより条件がよく、拍ごとに安定する。

    拡張期の切り出しは拍長の固定割合。切痕検出は動脈硬化例で破綻するため使わない
    （DN-less の問題そのもの）。当てはまりが悪い拍（r² < 0.90）は NaN で落とす。
    """
    n = beat.size
    a, b = int(DIAS_FRAC[0] * n), int(DIAS_FRAC[1] * n)
    if b - a < 10:
        return float("nan")
    y = np.asarray(beat[a:b], float)
    if not np.all(np.isfinite(y)):
        return float("nan")
    ymin = float(np.min(y))
    if ymin <= 0.0:
        return float("nan")          # mmHg は正。負なら較正異常かゼロ点ずれ
    t = np.arange(y.size) / fs
    M = np.column_stack([t, np.ones(t.size)])
    best_tau, best_r2 = float("nan"), -np.inf
    for frac in np.linspace(0.0, 0.95, 20):
        z = y - frac * ymin
        if float(np.min(z)) <= 1e-6:
            continue
        lz = np.log(z)
        coef, *_ = np.linalg.lstsq(M, lz, rcond=None)
        slope = float(coef[0])
        if slope >= 0:
            continue
        sse = float(np.sum((lz - M @ coef) ** 2))
        sst = float(np.sum((lz - lz.mean()) ** 2))
        if sst <= 0:
            continue
        r2 = 1.0 - sse / sst
        if r2 > best_r2:
            best_r2, best_tau = r2, -1000.0 / slope
    if best_r2 < TAU_MIN_R2:
        return float("nan")
    return float(best_tau)


def _excess(beat: np.ndarray, fs: float, tau_ms: float) -> np.ndarray:
    """貯留槽成分を差し引いた excess pressure を返す。

    動脈圧は拍内に緩やかな貯留槽（Windkessel）成分を持つ。PPG は実質的に
    AC結合でこの成分を含まないため、動脈圧をそのまま2カーネルPDAに渡すと、
    表現できない緩慢な成分をカーネルが吸収しようとして σ が境界に張り付き、
    当てはめが軒並み棄却される（合成データで確認: boundary_stick=True）。

    拡張期から推定した τ を使い、拍の始端と終端を通る指数を貯留槽とみなして
    差し引く。P_res(t) = A·exp(−t/τ) + C（A, C は両端一致で一意に決まる）。
    結果は始端・終端が 0 になり、PPG拍と同じ形式で PDA に渡せる。
    τ が取れない拍は両端を結ぶ直線で代用する。
    """
    y = np.asarray(beat, float)
    n = y.size
    if n < 10:
        return y - y.min()
    t = np.arange(n) / fs
    if np.isfinite(tau_ms) and tau_ms > 0:
        e = np.exp(-t / (tau_ms / 1000.0))
        den = float(e[0] - e[-1])
        if abs(den) > 1e-9:
            a = float(y[0] - y[-1]) / den
            c = float(y[0]) - a * float(e[0])
            return y - (a * e + c)
    return y - np.linspace(float(y[0]), float(y[-1]), n)


def _dpdt_max(beat: np.ndarray, fs: float) -> float:
    """最大上昇速度 [mmHg/s]。10ms平滑をかけ、拍の切り出し境界の前後20msは見ない。

    生の1サンプル差分は500Hzのノイズをそのまま増幅し、拍の切り出しが1サンプル
    ずれただけで非生理的な尖りを拾う（合成データで 20,057 mmHg/s の偽値を確認）。
    生理的な上昇脚は30ms程度の幅があるので平滑では潰れない。
    """
    y = np.asarray(beat, float)
    if y.size < 40:
        return float("nan")
    d = np.diff(y) * fs
    w = max(int(0.010 * fs), 3)
    d = np.convolve(d, np.ones(w) / w, mode="same")
    k = max(int(0.020 * fs), 5)
    if d.size > 2 * k + 10:
        d = d[k:-k]
    return float(np.max(d))


def _beat_stats(beat: np.ndarray, fs: float) -> dict:
    y = np.asarray(beat, float)
    return {"dpdt_max": _dpdt_max(y, fs),
            "sbp": float(np.max(y)), "dbp": float(np.min(y)),
            "tau_ms": _tau_ms(y, fs)}


# ---------------------------------------------------------------- ウィンドウ
def window_art(art: np.ndarray, ecg: np.ndarray, t0: float, with_pda: bool) -> dict:
    """1ウィンドウ分の動脈圧指標。品質不足の項目は NaN で返す（棄却はしない）。"""
    i0, i1 = int(t0 * FS), int((t0 + WIN_S) * FS)
    seg_a = np.nan_to_num(np.asarray(art[i0:i1], float))
    seg_e = np.nan_to_num(np.asarray(ecg[i0:i1], float))
    out: dict = {"t0": float(t0)}

    nan = float("nan")
    if seg_a.size < int(WIN_S * FS) * 0.9 or not np.any(seg_a):
        return {**out, "t1_ms": nan, "n_t1": 0, "dpdt_max": nan, "tau_ms": nan,
                "sbp": nan, "dbp": nan, "pp": nan, "n_beats": 0,
                **({"art_dt_ms": nan, "art_ri": nan, "n_art_pda": 0} if with_pda else {})}

    # --- B-1: R波→動脈圧立ち上がり ---
    t1 = _t1_series(seg_a, seg_e, FS)
    out["t1_ms"] = float(np.median(t1) * 1000.0) if t1.size >= 5 else nan
    out["n_t1"] = int(t1.size)

    # --- 頑健な圧指標 ---
    beats = segment_beats(seg_a, FS, ecg=seg_e)
    good = [(a, b) for a, b in beats if sqi(seg_a[a:b], FS)["ok"]]
    if good:
        st = [_beat_stats(seg_a[a:b], FS) for a, b in good]
        for k in ("dpdt_max", "sbp", "dbp", "tau_ms"):
            v = np.asarray([s[k] for s in st], float)
            v = v[np.isfinite(v)]
            out[k] = float(np.median(v)) if v.size >= 3 else nan
        out["pp"] = (out["sbp"] - out["dbp"]
                     if np.isfinite(out["sbp"]) and np.isfinite(out["dbp"]) else nan)
    else:
        out.update({"dpdt_max": nan, "sbp": nan, "dbp": nan, "tau_ms": nan, "pp": nan})
    out["n_beats"] = len(good)

    # --- B-2: 動脈圧波形に主解析と同一のPDAを当てる ---
    if with_pda:
        dts, ris = [], []
        if len(good) >= 8:
            sigma = float(np.nanmedian([estimate_noise(seg_a[a:b]) for a, b in good]))
            n_ens, reachable = required_ensemble_size(sigma)
            if reachable and len(good) >= 2 * n_ens:
                for k in range(0, len(good) - n_ens + 1, n_ens):
                    y = ensemble_average([seg_a[a:b] for a, b in good[k:k + n_ens]])
                    tt = np.arange(len(y)) / FS
                    y = _excess(y, FS, _tau_ms(y, FS))   # 貯留槽成分を外してから
                    try:
                        fit = fit_beat(tt, y)
                    except Exception:
                        continue
                    if not fit.get("ok", False):
                        continue
                    ix = si_ri_from_fit(fit)
                    dts.append(ix["dt_s"] * 1000.0)
                    ris.append(ix["ri"])
        out["art_dt_ms"] = float(np.median(dts)) if len(dts) >= 2 else nan
        out["art_ri"] = float(np.median(ris)) if len(ris) >= 2 else nan
        out["n_art_pda"] = len(dts)
    return out


# ---------------------------------------------------------------- 症例・並列
def extract_case_art(caseid: int, with_pda: bool) -> tuple:
    import pandas as pd
    tag = "pda" if with_pda else "base"
    outp = AFEAT / f"case_{caseid}.csv"
    metap = AFEAT / f"case_{caseid}_meta.json"
    if outp.exists() and metap.exists():
        try:
            m = json.loads(metap.read_text(encoding="utf-8"))
            if m.get("v") == META_V and m.get("mode") == tag:
                return caseid, len(pd.read_csv(outp)), None
        except Exception:
            pass
    try:
        main = pd.read_csv(FEAT / f"case_{caseid}.csv")
    except Exception:
        return caseid, None, "主解析キャッシュなし"
    if len(main) < 12:
        return caseid, None, "主解析で不採用"

    import vitaldb
    wav = vitaldb.load_case(caseid, ["SNUADC/ART", "SNUADC/ECG_II"], 1 / FS)
    art = wav[:, 0].astype(np.float32)
    ecg = wav[:, 1].astype(np.float32)
    rows = [window_art(art, ecg, float(t0), with_pda) for t0 in main["t0"]]
    df = pd.DataFrame(rows)
    AFEAT.mkdir(parents=True, exist_ok=True)
    df.to_csv(outp, index=False)
    metap.write_text(json.dumps({"v": META_V, "mode": tag, "caseid": caseid,
                                 "n_windows": len(df)}), encoding="utf-8")
    return caseid, len(df), None


def _one(args_tuple):
    caseid, with_pda = args_tuple
    try:
        return extract_case_art(caseid, with_pda)
    except Exception as e:  # noqa: BLE001
        return caseid, None, f"失敗: {e}"


# ---------------------------------------------------------------- 自己検証
def _synth_case(n_beats: int = 70, rr: float = 1.0, t1: float = 0.18,
                tau: float = 1.5, fs: float = FS):
    """既知の R→foot 遅延と時定数を持つ心電図＋動脈圧を作る。

    拍ごとの寄与を**加算**して作る（テンプレートの敷き詰めではない）。敷き詰めると
    拍の境界で貯留槽圧が不連続に跳ね、dP/dt が非生理的な値になる。実データの
    動脈圧は連続信号で切り出しは後から入るだけなので、加算のほうが忠実。
    """
    from scipy.special import erf
    n = int(n_beats * rr * fs)
    ecg = np.zeros(n)
    art = np.full(n, 60.0)                      # 拡張期の床
    idx = np.arange(n)
    for k in range(-3, n_beats + 1):            # 前後に余分な拍を置いて端を埋める
        i_r = int(k * rr * fs)
        if 0 <= i_r < n:
            ecg[i_r:i_r + 5] = 1.0
        tt = (idx - (i_r + int(t1 * fs))) / fs
        art = art + 45.0 * np.exp(-0.5 * ((tt - 0.11) / 0.055) ** 2)   # 前進波
        art = art + 18.0 * np.exp(-0.5 * ((tt - 0.29) / 0.075) ** 2)   # 反射波
        rise = 0.5 * (1.0 + erf((tt - 0.06) / (0.03 * np.sqrt(2.0))))  # 駆出（連続）
        art = art + 26.0 * rise * np.exp(-np.clip(tt, 0.0, None) / tau)
    return ecg, art


def selftest() -> int:
    """合成データでの自己検証。

    合否は**軽量モード（T1・dP/dt_max・τ・圧）だけ**で決める。PDAモードは
    まだ検証を通っていないため、参考として結果を表示するのみ（下の注記を参照）。
    """
    print("== 15_art_indices 自己検証（合成データ・ネットワーク不要） ==\n")
    print("-- 必須: 軽量モード --")
    ok = True

    # T1 は絶対値ではなく「オフセットが一定か」が要件。解析は症例内Δしか使わないので、
    # 立ち上がり定義に由来する固定バイアスは差分で消える。
    offs = []
    for t1_true in (0.14, 0.18, 0.24):
        ecg, art = _synth_case(t1=t1_true)
        r = window_art(art, ecg, 0.0, with_pda=False)
        offs.append(r["t1_ms"] - t1_true * 1000.0)
        print(f"  T1 真値 {t1_true*1000:5.0f} ms → 推定 {r['t1_ms']:6.1f} ms "
              f"(オフセット {offs[-1]:+5.1f} ms, 拍 {r['n_t1']})")
    spread = float(np.max(offs) - np.min(offs))
    t1_ok = spread < 3.0 and abs(float(np.mean(offs))) < 60.0
    ok &= t1_ok
    print(f"  → オフセットのばらつき {spread:.1f} ms（要件 <3 ms・症例内Δで相殺）"
          f"  {'PASS' if t1_ok else 'FAIL'}\n")

    taus = []
    for tau_true in (1.0, 1.8, 3.0):
        ecg, art = _synth_case(tau=tau_true)
        taus.append(window_art(art, ecg, 0.0, with_pda=False)["tau_ms"])
        print(f"  τ 真値 {tau_true*1000:5.0f} ms → 推定 {taus[-1]:7.0f} ms")
    tau_ok = (all(np.isfinite(v) for v in taus) and taus[0] < taus[1] < taus[2]
              and all(0.6 < e / (t * 1000.0) < 1.4
                      for e, t in zip(taus, (1.0, 1.8, 3.0))))
    ok &= tau_ok
    print(f"  → 単調かつ真値の ±40% 以内  {'PASS' if tau_ok else 'FAIL'}\n")

    ecg, art = _synth_case()
    r = window_art(art, ecg, 0.0, with_pda=False)
    dpdt_ok = np.isfinite(r["dpdt_max"]) and 200.0 < r["dpdt_max"] < 3000.0
    pp_ok = np.isfinite(r["pp"]) and 20.0 < r["pp"] < 120.0
    ok &= dpdt_ok and pp_ok
    print(f"  dP/dt_max {r['dpdt_max']:.0f} mmHg/s（生理域 200–3000）"
          f"  {'PASS' if dpdt_ok else 'FAIL'}")
    print(f"  SBP {r['sbp']:.0f} / DBP {r['dbp']:.0f} / PP {r['pp']:.0f} mmHg"
          f"  {'PASS' if pp_ok else 'FAIL'}")

    ecg0 = np.zeros(int(60 * FS))
    r0 = window_art(np.zeros(int(60 * FS)), ecg0, 0.0, with_pda=False)
    flat_ok = not np.isfinite(r0["t1_ms"]) and r0["n_beats"] == 0
    ok &= flat_ok
    print(f"  平坦な入力で例外を出さず NaN を返す  {'PASS' if flat_ok else 'FAIL'}")

    print("\n-- 参考: PDAモード（未検証・合否に含めない） --")
    rp = window_art(art, ecg, 0.0, with_pda=True)
    print(f"  ΔT {rp['art_dt_ms']} / RI {rp['art_ri']} / 採用当てはめ {rp['n_art_pda']}")
    print("  既知の問題: 凍結済みの2カーネルPDAは動脈圧波形に対して σ が上限に張り付き、")
    print("  収束検算で棄却される（boundary_stick=True）。貯留槽（Windkessel）成分を")
    print("  カーネルが吸収しようとするため。両端を通す指数を引く簡易な excess pressure")
    print("  分離では足りず、駆出中に立ち上がる貯留槽成分まで分離する必要がある。")
    print("  → B-2 の『動脈圧PDA』は、この分離を設計・検証してから走らせること。")
    print("     いま使えるのは軽量モードの T1・dP/dt_max・τ・圧だけ。")

    print("\n" + ("ALL PASS（軽量モード）" if ok else "FAIL あり"))
    return 0 if ok else 1


# ---------------------------------------------------------------- main
def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--limit", type=int, default=874)
    ap.add_argument("--jobs", type=int, default=1)
    ap.add_argument("--pda", action="store_true",
                    help="動脈圧波形にPDAを当てて ΔT・RI も出す（CPUを主解析並みに食う）")
    ap.add_argument("--selftest", action="store_true")
    args = ap.parse_args()

    if args.selftest:
        sys.exit(selftest())

    import pandas as pd
    tc = pd.read_csv(DATA / "target_cases.csv")
    ids = []
    for cid in tc["caseid"].astype(int):
        if len(ids) >= args.limit:
            break
        if (FEAT / f"case_{cid}.csv").exists():
            ids.append(cid)
    if args.pda:
        print("警告: PDAモードは未検証です。動脈圧波形では収束検算で棄却され、"
              "art_dt_ms・art_ri が全て NaN になる可能性が高い。"
              "--selftest の『参考』節を読んでから使うこと。\n", flush=True)
    mode = "PDAあり（未検証・重い）" if args.pda else "軽量（PDAなし）"
    print(f"{len(ids)} 症例を処理します / モード: {mode} / jobs={args.jobs}", flush=True)

    tally = Counter()
    work = [(c, args.pda) for c in ids]
    if args.jobs > 1:
        from concurrent.futures import ProcessPoolExecutor, as_completed
        with ProcessPoolExecutor(max_workers=args.jobs) as ex:
            futs = {ex.submit(_one, w): w[0] for w in work}
            for n, fu in enumerate(as_completed(futs), 1):
                cid, nn, err = fu.result()
                tally["ok" if err is None else "skip"] += 1
                print(f"[{n}/{len(ids)}] caseid={cid}: "
                      + (f"skip（{err}）" if err else f"動脈圧 {nn} ウィンドウ"), flush=True)
    else:
        for n, w in enumerate(work, 1):
            cid, nn, err = _one(w)
            tally["ok" if err is None else "skip"] += 1
            print(f"[{n}/{len(ids)}] caseid={cid}: "
                  + (f"skip（{err}）" if err else f"動脈圧 {nn} ウィンドウ"), flush=True)

    print(f"\n完了: ok {tally['ok']} / skip {tally['skip']}")

    # --- 健全性チェック: T1 の中央値が生理的な帯に入っているか ---
    vals = []
    for p in sorted(AFEAT.glob("case_*.csv")):
        try:
            v = pd.read_csv(p)["t1_ms"].dropna()
        except Exception:
            continue
        if len(v):
            vals.append(float(v.median()))
    if vals:
        med = float(np.median(vals))
        lo, hi = np.percentile(vals, [25, 75])
        print(f"\nT1（R波→動脈圧立ち上がり）症例中央値: {med:.0f} ms "
              f"[IQR {lo:.0f}–{hi:.0f}]（n={len(vals)}症例）")
        if not (T1_EXPECT[0] * 1000 <= med <= T1_EXPECT[1] * 1000):
            print(f"  警告: 生理的な想定帯 {T1_EXPECT[0]*1000:.0f}–{T1_EXPECT[1]*1000:.0f} ms "
                  "から外れています。動脈圧チャネルにも装置遅延がある可能性を疑うこと。")
        else:
            print("  想定帯の中。動脈圧チャネルに装置遅延は無いという前提と整合します。")
    print("\n次: 主解析の pwtt と結合して Δ(T2−T1) の説明力を見る（B-1）")


if __name__ == "__main__":
    main()
