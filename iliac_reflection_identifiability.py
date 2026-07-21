# -*- coding: utf-8 -*-
"""
腸骨反射（P3）の識別性を高めた PPG 波形分解モデルと、その検証。

モデル:  y(t) = W_f(t) + Σ_{k∈{腎,腸骨}} Γ_k · W_f((t−τ_k)/β) + ε
  W_f = 単峰・非対称パルス（rise σr / fall σf）。反射は前進波の遅延・縮尺・分散コピー
  （shape-tying）。パラメータは 8 個: [A, μ, σr, σf, Γ_renal, τ_renal, Γ_iliac, τ_iliac]。

本スクリプトは合成波（真値既知）で以下を実測する:
  実験1  自由3ガウス(12) vs 形状拘束(8) … 腸骨ピーク時刻の CRLB / RMSE
  実験2  τ_iliac アンカー(身長/PWV/SDPPG)の頑健性 … 高ノイズでの gross-fail 率
  実験3  wrap-around（柔+速）… 1拍窓の切断バイアス vs 2拍窓

依存: numpy, scipy。 実行:  python3 iliac_reflection_identifiability.py
"""
import numpy as np
from scipy.optimize import least_squares

SEED = 20260721
BETA = 1.20  # 反射の分散(broadening)。まず固定

def s(t, mu, sr, sf):
    sig = np.where(t < mu, sr, sf)
    return np.exp(-((t - mu) ** 2) / (2.0 * sig ** 2))

def gen(th, t):
    """真の生成/前進波モデル（shape-tied）。"""
    A, mu, sr, sf, G1, t1, G2, t2 = th
    return (A * s(t, mu, sr, sf)
            + G1 * A * s(t, mu + t1, sr * BETA, sf * BETA)
            + G2 * A * s(t, mu + t2, sr * BETA, sf * BETA))

# ---------- 自由3ガウス（naive PDA） ----------
def pred_free(t, p):
    return p[0]*s(t,p[1],p[2],p[3]) + p[4]*s(t,p[5],p[6],p[7]) + p[8]*s(t,p[9],p[10],p[11])

def fit_free(t, y, sig):
    lb = np.array([0.4,0.08,0.02,0.04, 0.0,0.16,0.02,0.04, 0.0,0.28,0.02,0.05])
    ub = np.array([1.6,0.22,0.12,0.18, 0.9,0.34,0.14,0.24, 0.9,0.72,0.16,0.28])
    p0 = np.array([y.max(),t[np.argmax(y)],0.05,0.09, 0.3,0.25,0.05,0.10, 0.3,0.45,0.06,0.12])
    p0 = np.clip(p0, lb+1e-6, ub-1e-6)
    return least_squares(lambda p:(pred_free(t,p)-y)/sig, p0, bounds=(lb,ub),
                         method='trf', max_nfev=6000).x  # 腸骨ピーク時刻 = p[9]

# ---------- 形状拘束（改良） ----------
def fit_tied(t, y, sig, tau2_prior=None, sig_prior=None, tb=(0.16, 0.70)):
    lb = np.array([0.4,0.08,0.02,0.04,0.0,0.05,0.0,tb[0]])
    ub = np.array([1.6,0.28,0.12,0.20,0.9,0.18,0.9,tb[1]])
    th0 = np.array([y.max(),t[np.argmax(y)],0.05,0.09,0.3,0.10,0.3,
                    tau2_prior if tau2_prior is not None else 0.30])
    th0 = np.clip(th0, lb+1e-6, ub-1e-6)
    def resid(th):
        r = (gen(th, t) - y) / sig
        if tau2_prior is not None:            # τ_iliac への軟らかい事前分布（アンカー）
            r = np.append(r, (th[7] - tau2_prior) / sig_prior)
        return r
    return least_squares(resid, th0, bounds=(lb,ub), method='trf', max_nfev=6000).x

# ---------- Fisher情報 -> CRLB（腸骨ピーク時刻の下限） ----------
def _crlb(predfn, t, p, sig, idx_peak, prior=None):
    n = len(p); J = np.zeros((len(t), n)); base = predfn(t, p)
    for j in range(n):
        d = p.copy(); h = 1e-5*max(1.0, abs(p[j])); d[j] += h
        J[:, j] = (predfn(t, d) - base) / h
    F = J.T @ J / sig**2
    if prior is not None:
        F[prior[0], prior[0]] += prior[1]
    C = np.linalg.pinv(F)
    if isinstance(idx_peak, tuple):           # peak = μ + τ2
        i, k = idx_peak
        return float(np.sqrt(max(C[i,i]+C[k,k]+2*C[i,k], 0)))
    return float(np.sqrt(max(C[idx_peak, idx_peak], 0)))

def th_to_free(th):
    A,mu,sr,sf,G1,t1,G2,t2 = th
    return np.array([A,mu,sr,sf, G1*A,mu+t1,sr*BETA,sf*BETA, G2*A,mu+t2,sr*BETA,sf*BETA])

# ============================= 実験1 =============================
def experiment1(rng):
    t = np.linspace(0, 0.9, 300); sig = 0.04; N = 120
    scen = {"A 明瞭な拡張期ピーク": np.array([1.0,0.15,0.045,0.085,0.35,0.10,0.42,0.33]),
            "B 硬い/融合/弱い腸骨(最難)": np.array([1.0,0.15,0.045,0.085,0.35,0.10,0.25,0.20])}
    print("\n== 実験1: 自由3ガウス vs 形状拘束（腸骨ピーク時刻の推定, noise=0.04） ==")
    for name, thT in scen.items():
        peak = thT[1] + thT[7]; ef, et = [], []
        for _ in range(N):
            y = gen(thT, t) + rng.normal(0, sig, t.size)
            ef.append(fit_free(t, y, sig)[9])
            pt = fit_tied(t, y, sig); et.append(pt[1] + pt[7])
        ef = np.array(ef); et = np.array(et)
        cF = _crlb(pred_free, t, th_to_free(thT), sig, 9)
        cT = _crlb(lambda tt, pp: gen(pp, tt), t, thT, sig, (1, 7))
        print(f"  {name} (真 {peak*1000:.0f} ms)")
        print(f"     RMSE  自由 {np.sqrt(np.mean((ef-peak)**2))*1000:5.1f} ms | 拘束 {np.sqrt(np.mean((et-peak)**2))*1000:5.1f} ms")
        print(f"     CRLB  自由 {cF*1000:5.1f} ms | 拘束 {cT*1000:5.1f} ms")

# ============================= 実験2 =============================
def experiment2(rng):
    thB = np.array([1.0,0.15,0.045,0.085,0.35,0.10,0.25,0.20])
    t = np.linspace(0, 0.9, 300); y0 = gen(thB, t); true = thB[7]; N = 250; sig = 0.06
    def run(anchor):
        errs = []
        for _ in range(N):
            y = y0 + rng.normal(0, sig, t.size)
            if anchor:
                pr = true + rng.normal(0, 0.03)
                th = fit_tied(t, y, sig, tau2_prior=pr, sig_prior=0.03, tb=(0.10, 0.45))
            else:
                th = fit_tied(t, y, sig, tb=(0.16, 0.70))
            errs.append(abs(th[7] - true))
        e = np.array(errs)
        return e.mean()*1000, np.sqrt(np.mean(e**2))*1000, (e > 0.040).mean()*100
    print("\n== 実験2: τ_iliac アンカーの頑健性（硬い/融合, noise=0.06, N=250） ==")
    for lab, an in (("アンカー無し", False), ("アンカー有り(30ms)", True)):
        mae, rmse, gf = run(an)
        print(f"  {lab:16s}: MAE {mae:5.1f} ms  RMSE {rmse:5.1f} ms  gross-fail(>40ms) {gf:4.1f}%")

# ============================= 実験3 =============================
def experiment3(rng):
    thC = np.array([1.0, 0.13, 0.040, 0.075, 0.30, 0.09, 0.42, 0.62]); cyc = 0.70
    peak = thC[1] + thC[7]                          # 0.75 = 次拍 foot(0.70) より後ろ
    t = np.linspace(0, 2*cyc, 480)
    b2 = gen(thC, t - cyc); b2[t < cyc] = 0.0
    y = gen(thC, t) + b2 + rng.normal(0, 0.03, t.size)
    m1 = t <= cyc                                    # 1拍窓(切断)
    thS = fit_tied(t[m1], y[m1], 0.03, tb=(0.30, 0.68))
    def model2(th, tt):
        c2 = gen(th, tt - cyc); c2 = np.where(tt < cyc, 0.0, c2)
        return gen(th, tt) + c2
    lb = np.array([0.4,0.08,0.02,0.04,0.0,0.05,0.0,0.30]); ub = np.array([1.6,0.28,0.12,0.20,0.9,0.18,0.9,0.68])
    th0 = np.array([1.0,0.13,0.05,0.08,0.3,0.09,0.3,0.55])
    thD = least_squares(lambda th:(model2(th,t)-y)/0.03, th0, bounds=(lb,ub),
                        method='trf', max_nfev=8000).x    # 2拍窓
    print("\n== 実験3: wrap-around（柔+速, 真の腸骨ピーク %.0f ms > 周期 %.0f ms） ==" % (peak*1000, cyc*1000))
    print(f"  1拍窓(切断):      腸骨ピーク推定 {(thS[1]+thS[7])*1000:6.1f} ms")
    print(f"  2拍窓(裾を回収):  腸骨ピーク推定 {(thD[1]+thD[7])*1000:6.1f} ms")

if __name__ == "__main__":
    rng = np.random.default_rng(SEED)
    experiment1(rng)
    experiment2(rng)
    experiment3(rng)
