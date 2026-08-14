#!/usr/bin/env python3
"""delta_RI_measurement_robustness.py

ΔRI（反射指数の個人内変化）を術中後負荷のトレンド指標として使えるかを、
真値既知の合成 PPG で検証する。`delta_RI_afterload_protocol.md` の数値を再現する。

検証するのは「計測系が ΔRI を壊すか」であって、「ΔRI が後負荷を映すか」ではない。
後者は実患者・参照基準を要する（同文書 §6）。

  実験1  帯域制限（モニタ波形のハイパスフィルタ）は ΔRI を保存するか
  実験2  自動ゲイン制御（AGC）は ΔRI を保存するか
  実験3  心拍数（HR）は血管条件を固定しても RI を動かすか
  実験4  波形類型ごとに landmark 法と分解法はどこで破綻するか

用語：
  RI   reflection index（反射指数）＝ 拡張期ピーク高 / 収縮期ピーク高
  AGC  automatic gain control（自動ゲイン制御）
  landmark 法  原波形の極値（ピーク・切痕）を探して指標を作る方法
  分解法       波形全体を数式に当てはめて反射成分を解く方法

依存：numpy, scipy。`python3 delta_RI_measurement_robustness.py` で再現する。
"""

from __future__ import annotations

import numpy as np
from scipy import signal
from scipy.optimize import least_squares
from scipy.signal import savgol_filter

FS = 500.0          # サンプリング周波数 [Hz]（VitalDB の PLETH と同じ）
SEED = 20260814
BETA = 1.25         # 反射波の分散（dispersion）。真値・モデルとも固定

# 真値。若年〜中年の T3 型（拡張期ピークが局所最大として見える波形）を基準に置く。
TRUTH = dict(A=1.0, mu=0.16, sr=0.045, sf=0.075,
             gammas=(0.45, 0.40), taus=(0.16, 0.42))


# ---------------------------------------------------------------------------
# 1. 合成 PPG（厳密に周期的に作る）
# ---------------------------------------------------------------------------

def asym_pulse(t, sr, sf):
    """立ち上がり σr・下降 σf の非対称ガウスパルス（0 を中心とする）。

    左右対称のガウス関数では脈波の「速く上がり遅く下がる」形が表現できず、
    分解が初期値に依存しやすくなる（Basso 2024）。最小限の非対称化を行う。
    """
    return np.where(t < 0.0, np.exp(-0.5 * (t / sr) ** 2), np.exp(-0.5 * (t / sf) ** 2))


def asym_sech(t, sr, sf):
    """非対称 sech²（双曲線正割二乗）パルス。半値幅をガウスに合わせてある。

    実験4 でモデル不一致（model mismatch）を作るために使う。Nagasawa 2022 の
    sech 波分解に対応し、「真の基底関数はガウスとは限らない」状況を再現する。
    """
    w = np.where(t < 0.0, 1.335 * sr, 1.335 * sf)
    return 1.0 / np.cosh(t / w) ** 2


def beat_period(t, T, A, mu, sr, sf, gammas, taus, beta=BETA, n_wrap=2,
                basis=asym_pulse):
    """前進波＋反射波（遅延 τ・縮尺 Γ・分散 β のコピー）を位相畳み込みで生成する。

    反射波の形を前進波に縛る（shape-tying）。位相を T で折り返して隣接拍の裾を
    足し込むので、拡張期成分が次拍に回り込む wrap-around も再現される。
    """
    ph = np.mod(t, T)
    y = np.zeros_like(ph)
    for n in range(-n_wrap, n_wrap + 1):
        tt = ph - n * T
        y += A * basis(tt - mu, sr, sf)
        for g, tau in zip(gammas, taus):
            y += A * g * basis((tt - mu - tau) / beta, sr, sf)
    return y


def periodic_highpass(y, fc, order=1, causal=True):
    """厳密に 1 周期分の信号に対する、ハイパスフィルタの定常応答。

    モニタが表示しているのは過渡応答ではなく定常応答なので、周期信号の各高調波に
    周波数応答 H(f) を掛けるのが厳密解になる。causal=True は実機の因果的 IIR
    （位相歪みあり、H を掛ける）、False は事後処理の filtfilt（ゼロ位相、|H|²）。
    """
    if fc is None:
        return y.copy()
    b, a = signal.butter(order, fc / (FS / 2.0), btype="highpass")
    freqs = np.fft.rfftfreq(len(y), 1.0 / FS)
    _, h = signal.freqz(b, a, worN=2.0 * np.pi * freqs / FS)
    return np.fft.irfft(np.fft.rfft(y) * (h if causal else np.abs(h) ** 2), len(y))


def make_period(hr=60.0, tone=1.0, truth=None):
    """1 拍ぶんの合成波を返す。`tone` は反射振幅の一律スケール（血管トーヌス倍率）。

    tone=1.00 がベースライン、tone=1.25 が「反射が 25% 増（血管収縮）」に相当する。
    HR はサンプル数が整数になるよう量子化する（厳密な周期性を保つため）。
    """
    tr = dict(TRUTH if truth is None else truth)
    n_per = int(round(60.0 / hr * FS))
    T = n_per / FS
    t = np.arange(n_per) / FS
    g = tuple(x * tone for x in tr["gammas"])
    y = beat_period(t, T, tr["A"], tr["mu"], tr["sr"], tr["sf"], g, tr["taus"],
                    beta=tr.get("beta", BETA), basis=tr.get("basis", asym_pulse))
    return T, n_per, y


def observe(hr=60.0, tone=1.0, fc=None, order=1, causal=True, noise=0.01,
            gain=1.0, rng=None, truth=None):
    """生成 →（帯域制限）→（AGC ゲイン）→ ノイズ付加、の観測経路を通す。

    返り値の `shift` は、拍の起点（foot）が位相原点からどれだけずれているか。
    モデル側も同じだけ回すことで、データとモデルの位相を合わせる。
    """
    T, n_per, y = make_period(hr, tone, truth)
    y = periodic_highpass(y, fc, order, causal) * gain
    shift = int(np.argmin(y))
    y = np.roll(y, -shift)
    if noise > 0 and rng is not None:
        y = y + rng.normal(0.0, noise * gain, size=y.shape)
    return T, n_per, shift, y


# ---------------------------------------------------------------------------
# 2. landmark 法による RI
# ---------------------------------------------------------------------------

def landmark_ri(y, n_per, prominence=0.02, min_gap=0.06):
    """拡張期ピークを局所最大として探し、RI = 拡張期高 / 収縮期高 を返す。

    拡張期ピークが局所最大として存在しなければ NaN（＝明示的な検出失敗）を返す。
    公平な比較のため、実装として妥当な水準の前処理を入れてある：
      * Savitzky-Golay（約 100 ms 窓）で平滑化
      * ピークに prominence（突出度）閾値＝脈波振幅の 2% を課す
      * 収縮期ピークから 60 ms 以内のピークは対象外とする
    prominence 閾値を課さないと、ノイズ由来の微小な凹凸を拡張期ピークとして
    拾ってしまい、landmark 法を不当に低く評価することになる。
    """
    win = int(0.1 * FS) | 1
    ys = savgol_filter(y, win, 3) if len(y) > win else y.copy()
    ys = ys - ys[0]
    p1 = int(np.argmax(ys))
    amp = float(ys.max() - ys.min())
    if amp <= 0:
        return np.nan, np.nan
    idx, _ = signal.find_peaks(ys, prominence=prominence * amp)
    cand = [i for i in idx if i > p1 + int(min_gap * FS)]
    if not cand:
        return np.nan, np.nan
    i = int(cand[0])
    return ys[i] / ys[p1], (i - p1) / FS


# ---------------------------------------------------------------------------
# 3. 分解法（shape-tied fit）
# ---------------------------------------------------------------------------
#  θ = [A, mu, sr, sf, Γ1, τ1, Γ2, τ2, c0, c1]
#  σf の上限は前進波が第 1 反射を飲み込むのを防ぐ生理的拘束（LVET 相当）。
#  τ1 < τ2 は順序拘束（Baruch の窓に対応）。c0・c1 はフィルタ由来の基線変動を吸収する。
P_LO = np.array([0.05, 0.05, 0.020, 0.030, 0.0, 0.08, 0.0, 0.25, -5.0, -20.0])
P_HI = np.array([20.0, 0.35, 0.080, 0.120, 0.9, 0.24, 0.9, 0.62, 5.0, 20.0])
P0 = np.array([1.0, 0.15, 0.045, 0.075, 0.40, 0.15, 0.35, 0.40, 0.0, 0.0])


def model(p, n_per, T, shift, filt=None):
    A, mu, sr, sf, g1, tau1, g2, tau2, c0, c1 = p
    t = np.arange(n_per) / FS
    y = beat_period(t, T, A, mu, sr, sf, (g1, g2), (tau1, tau2))
    if filt is not None:
        y = periodic_highpass(y, filt[0], filt[1], filt[2])
    y = np.roll(y, -shift)
    return y + c0 + c1 * (t - t.mean())


def fit_decomposition(y, n_per, T, shift, filt=None, n_restart=3, rng=None,
                      amp_hint=1.0):
    """拘束付き非線形最小二乗（TRF）。複数初期値から解き、最良解と初期値依存性を返す。

    `spread` は、コストが最良解の 1.05 倍以内に収まった解どうしでの τ₂ 推定値の幅
    [ms]。「この拍の推定がどれだけ決まったか」の実務的な代理指標として出力する。
    分解法は必ず値を返すので、この幅を併記しない運用は危険である。
    """
    lo, hi = P_LO.copy(), P_HI.copy()
    lo[0], hi[0] = 0.05 * amp_hint, 20.0 * amp_hint
    best, sols = None, []
    for k in range(n_restart):
        p0 = P0.copy()
        p0[0] = amp_hint
        if k > 0 and rng is not None:
            p0 = np.clip(p0 + rng.uniform(-0.25, 0.25, size=p0.shape) * (hi - lo), lo, hi)
        try:
            r = least_squares(lambda p: model(p, n_per, T, shift, filt) - y, p0,
                              bounds=(lo, hi), method="trf", x_scale="jac",
                              max_nfev=3000)
        except Exception:
            continue
        sols.append((r.cost, r.x))
        if best is None or r.cost < best[0]:
            best = (r.cost, r.x)
    if best is None:
        return None, np.nan
    near = [x for c, x in sols if c <= best[0] * 1.05]
    spread = (max(x[7] for x in near) - min(x[7] for x in near)) * 1000.0
    return best[1], spread


def amp_of(y):
    return float(y.max() - y.min())


# ---------------------------------------------------------------------------
# 実験1：帯域制限は ΔRI を保存するか
# ---------------------------------------------------------------------------

def experiment_1(n_rep=30):
    print("=" * 92)
    print("実験1  帯域制限（ハイパスフィルタ）と ΔRI の保存")
    print("  介入: 反射振幅 ×1.25（血管収縮相当）。回復率 = 測定Δ / 無フィルタΔ")
    print(f"  ノイズ 1% RMS、各条件 n={n_rep}。括弧内は SD。")
    print("=" * 92)
    rng = np.random.default_rng(SEED)
    cutoffs = [None, 0.05, 0.1, 0.25, 0.5, 1.0]
    rows = []
    for causal in (True, False):
        for fc in cutoffs:
            filt = None if fc is None else (fc, 1, causal)
            lm, naive, aware, fail = [], [], [], 0
            for _ in range(n_rep):
                v = {}
                for tone in (1.00, 1.25):
                    T, n_per, sh, y = observe(tone=tone, fc=fc, causal=causal,
                                              noise=0.01, rng=rng)
                    ri, _ = landmark_ri(y, n_per)
                    a = amp_of(y)
                    pn, _ = fit_decomposition(y, n_per, T, sh, None, 2, rng, a)
                    pa, _ = fit_decomposition(y, n_per, T, sh, filt, 2, rng, a)
                    v[tone] = (ri,
                               pn[6] if pn is not None else np.nan,
                               pa[6] if pa is not None else np.nan)
                d_lm = v[1.25][0] - v[1.00][0]
                fail += int(not np.isfinite(d_lm))
                lm.append(d_lm)
                naive.append(v[1.25][1] - v[1.00][1])
                aware.append(v[1.25][2] - v[1.00][2])
            rows.append([causal, fc,
                         np.nanmean(lm), np.nanstd(lm),
                         np.nanmean(naive), np.nanstd(naive),
                         np.nanmean(aware), np.nanstd(aware),
                         fail / n_rep])
    ref = {r[0]: (r[2], r[4], r[6]) for r in rows if r[1] is None}
    print(f"{'フィルタ':<9}{'遮断[Hz]':>8}{'ΔRI landmark':>20}{'回復率':>7}{'検出失敗':>9}"
          f"{'ΔΓ₂ 素朴':>18}{'回復率':>7}{'ΔΓ₂ filter-aware':>20}{'回復率':>7}")
    for causal, fc, a, asd, b, bsd, c, csd, fr in rows:
        r0 = ref[causal]
        lab = "因果的" if causal else "ゼロ位相"
        fcs = "なし" if fc is None else f"{fc:.2f}"
        av = "  n/a" if not np.isfinite(a) else f"{a:.4f}({asd:.4f})"
        ar = "  n/a" if not np.isfinite(a) else f"{a / r0[0]:.2f}"
        print(f"{lab:<9}{fcs:>8}{av:>20}{ar:>7}{fr * 100:>8.0f}%"
              f"{f'{b:.4f}({bsd:.4f})':>18}{b / r0[1]:>7.2f}"
              f"{f'{c:.4f}({csd:.4f})':>20}{c / r0[2]:>7.2f}")
    print("\n  回復率 1.00 が「無フィルタと同じ Δ が取れた」。絶対値が歪んでも Δ が保存されるなら、")
    print("  Δ 追跡という設計はモニタ波形でも成立する。filter-aware = フィルタ条件を既知として")
    print("  モデル側にも同じフィルタを通す当てはめ。")
    return rows


# ---------------------------------------------------------------------------
# 実験2：AGC は ΔRI を保存するか
# ---------------------------------------------------------------------------

def experiment_2():
    print("\n" + "=" * 84)
    print("実験2  自動ゲイン制御（AGC）と指標の不変性")
    print("=" * 84)
    rng = np.random.default_rng(SEED + 1)
    # ゲイン以外の条件を完全に揃えるため、同一のノイズ実現を全ゲインで共有する
    T, n_per, y0 = make_period()
    sh = int(np.argmin(y0))
    y0 = np.roll(y0, -sh)
    eps = rng.normal(0.0, 0.005, size=y0.shape)
    print(f"{'ゲイン':>8}{'AC 振幅(PI 相当)':>18}{'RI(landmark)':>15}"
          f"{'Γ₂(分解)':>12}{'τ₂[ms]':>10}")
    for gain in (0.5, 1.0, 2.0, 4.0):
        y = (y0 + eps) * gain
        ri, _ = landmark_ri(y, n_per)
        a = amp_of(y)
        p, _ = fit_decomposition(y, n_per, T, sh, None, 2, rng, a)
        print(f"{gain:>8.1f}{a:>18.4f}{ri:>15.4f}{p[6]:>12.4f}{p[7] * 1000:>10.1f}")
    print("\n  PI は AC の絶対量なのでゲインに比例して壊れる。RI・Γ₂・τ₂ は同一拍内の比と")
    print("  時間なので不変。＝「振幅の絶対量ではなく比と時間で Δ を作る」原則の数値的裏づけ。")


# ---------------------------------------------------------------------------
# 実験3：心拍数は RI を動かすか（血管条件は固定）
# ---------------------------------------------------------------------------

def experiment_3(n_rep=20):
    print("\n" + "=" * 92)
    print("実験3  HR 交絡（血管パラメータの真値は一切変えていない）")
    print(f"  ノイズ 1% RMS、各 HR で n={n_rep}。括弧内は SD。")
    print("=" * 92)
    rng = np.random.default_rng(SEED + 2)
    print(f"{'HR[bpm]':>8}{'RI landmark':>20}{'検出率':>8}{'Γ₂ 分解':>18}"
          f"{'τ₂[ms]':>10}{'拡張期長[ms]':>14}")
    out = []
    for hr in (50, 60, 70, 80, 90, 100, 110):
        ris, gs, ts = [], [], []
        for _ in range(n_rep):
            T, n_per, sh, y = observe(hr=hr, noise=0.01, rng=rng)
            ri, _ = landmark_ri(y, n_per)
            a = amp_of(y)
            p, _ = fit_decomposition(y, n_per, T, sh, None, 2, rng, a)
            ris.append(ri)
            gs.append(p[6])
            ts.append(p[7] * 1000)
        det = np.mean(np.isfinite(ris))
        rm, rs = np.nanmean(ris), np.nanstd(ris)
        rv = "  n/a" if not np.isfinite(rm) else f"{rm:.4f}({rs:.4f})"
        print(f"{hr:>8}{rv:>20}{det * 100:>7.0f}%"
              f"{f'{np.mean(gs):.4f}({np.std(gs):.4f})':>18}"
              f"{np.mean(ts):>10.1f}{(T - TRUTH['mu']) * 1000:>14.0f}")
        out.append((hr, rm, np.mean(gs), det))
    v = [o for o in out if np.isfinite(o[1])]
    if len(v) >= 2:
        print(f"\n  HR {v[0][0]}→{v[-1][0]} で landmark RI は {v[0][1]:.4f}→{v[-1][1]:.4f}"
              f"（{(v[-1][1] - v[0][1]) / v[0][1] * 100:+.1f}%）、"
              f"分解 Γ₂ は {out[0][2]:.4f}→{out[-1][2]:.4f}"
              f"（{(out[-1][2] - out[0][2]) / out[0][2] * 100:+.1f}%）。")
    print("  血管は何も変えていないので、この差はすべて HR による見かけの変化である。")
    print("  頻脈では拡張期が短縮し、拡張期ピークが次拍の立ち上がりに呑まれて landmark が")
    print("  検出できなくなる。フェニレフリンは後負荷を上げると同時に反射性徐脈を起こすため、")
    print("  この交絡は「昇圧薬で ΔRI が動いた」を最も汚染しやすい経路になる。")
    return out


# ---------------------------------------------------------------------------
# 実験4：波形類型ごとの破綻点
# ---------------------------------------------------------------------------

def experiment_4(n_rep=15):
    print("\n" + "=" * 92)
    print("実験4  波形類型・モデル不一致と識別可能性")
    print("  真値は sech² 基底・3 反射・分散 β=1.5 で生成し、当てはめは非対称ガウス基底・")
    print("  2 反射・β=1.25 固定で行う（＝基底も成分数も分散も間違えた状態）。")
    print("  Γ₂・τ₂ の誤差は第 2 反射（最遠位）の真値に対する絶対誤差。")
    print("=" * 92)
    rng = np.random.default_rng(SEED + 3)
    # 3 番目の反射（弱い再反射）を混ぜ、基底と β も真値と当てはめでずらす
    def case(taus, gammas, beta):
        return dict(TRUTH, taus=taus, gammas=gammas, beta=beta, basis=asym_sech)
    cases = {
        "T3 型 τ₂=420ms 明瞭": case((0.16, 0.42, 0.68), (0.45, 0.40, 0.10), 1.5),
        "T2 型 τ₂=340ms 浅い": case((0.15, 0.34, 0.58), (0.45, 0.32, 0.08), 1.5),
        "T1 型 τ₂=260ms 融合": case((0.13, 0.26, 0.46), (0.40, 0.24, 0.06), 1.5),
        "T0 型 τ₂=180ms 単峰": case((0.10, 0.18, 0.32), (0.30, 0.12, 0.03), 2.2),
    }
    # 無ノイズの真の波形で拡張期ピークが検出できるか（既定 prominence 2% での判定）
    for label, tr in cases.items():
        _, n_c, y_c = make_period(60.0, 1.0, tr)
        y_c = np.roll(y_c, -int(np.argmin(y_c)))
        vis = np.isfinite(landmark_ri(y_c, n_c)[0])
        print(f"    {label}: 無ノイズ・prominence 2% での拡張期ピーク "
              f"= {'検出可' if vis else '検出不可（退化）'}")
    print()
    print(f"{'波形類型':<24}{'ノイズ':>7}{'landmark 検出率':>16}{'うち妥当':>10}"
          f"{'Γ₂ 誤差':>10}{'τ₂ 誤差[ms]':>13}{'初期値ばらつき[ms]':>20}")
    for label, tr in cases.items():
        for noise in (0.01, 0.03):
            ok, valid, ge, te, sp = 0, 0, [], [], []
            for _ in range(n_rep):
                T, n_per, sh, y = observe(noise=noise, rng=rng, truth=tr)
                ri, dt = landmark_ri(y, n_per)
                if np.isfinite(ri):
                    ok += 1
                    # 検出した拡張期ピークが真の第 2 反射の時刻と ±50 ms 以内で一致するか
                    valid += int(abs(dt - tr["taus"][1]) <= 0.05)
                a = amp_of(y)
                p, spread = fit_decomposition(y, n_per, T, sh, None, 4, rng, a)
                if p is not None:
                    ge.append(abs(p[6] - tr["gammas"][1]))
                    te.append(abs(p[7] - tr["taus"][1]) * 1000)
                    sp.append(spread)
            vr = f"{valid / ok * 100:.0f}%" if ok else "n/a"
            print(f"{label:<24}{noise:>7.2f}{ok / n_rep * 100:>15.0f}%{vr:>10}"
                  f"{np.mean(ge):>10.3f}{np.mean(te):>13.1f}{np.mean(sp):>20.1f}")
    print("\n  「検出率」は landmark 法が値を返した割合、「うち妥当」はその値が真の第 2 反射")
    print("  時刻と ±50 ms 以内で一致した割合。")
    print("  landmark 法は T1・T0 で明示的に落ちる（検出率 0%）。一方で分解法は全類型で値を")
    print("  返すが、T1・T0 では τ₂ 誤差が 200 ms 前後・Γ₂ 誤差が真値の 4 割超に達する。")
    print("  しかも初期値ばらつきはほぼ 0 ms のまま——最適化は「決まって」いるのに答えは")
    print("  間違っている。モデル不一致由来の偏りは初期値ばらつきでは検出できない。")
    print("  ＝ 不確実性の出力は必要条件であって十分条件ではない。")

    # 検出可否の境界（T2 付近）が prominence 閾値という実装上の任意選択に依存すること
    print("\n  補足：検出の境界は prominence（突出度）閾値という実装上の任意選択に依存する。")
    print(f"  {'prominence 閾値':<18}{'T2 検出率':>12}{'T1 検出率':>12}")
    for prom in (0.005, 0.01, 0.02, 0.04):
        res = []
        for key in ("T2 型 τ₂=340ms 浅い", "T1 型 τ₂=260ms 融合"):
            tr = cases[key]
            ok = 0
            for _ in range(n_rep):
                T, n_per, sh, y = observe(noise=0.01, rng=rng, truth=tr)
                ok += int(np.isfinite(landmark_ri(y, n_per, prominence=prom)[0]))
            res.append(ok / n_rep * 100)
        print(f"  {prom * 100:>6.1f}%{'':<11}{res[0]:>11.0f}%{res[1]:>11.0f}%")
    print("  同じ波形でも閾値ひとつで「見えた／見えない」が反転する。研究設計で検出本数を")
    print("  一次アウトカムにしてはならない理由がここにある。")


def main():
    experiment_1()
    experiment_2()
    experiment_3()
    experiment_4()
    print("\n" + "=" * 84)
    print("注意：本スクリプトは合成波（真値既知）による計測系の検証である。")
    print("      実 PPG・実患者で ΔRI が後負荷を映すかは、これとは別に検証を要する。")
    print("=" * 84)


if __name__ == "__main__":
    main()
