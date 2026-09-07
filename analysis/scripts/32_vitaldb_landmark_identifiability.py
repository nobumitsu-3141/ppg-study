#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VitalDB のモニタ波形で、研究0 で成立した指標の元になる特徴点が同定できるか（20 例）。

問い（roadmap §9・checklist 段階2「次の主目標」）
------------------------------------------------
研究0（PWDB・理想波形）で成立した **早期振幅比 Am_b/Am_p1**（b 波・p1。Hellqvist 2024）と
**特徴点 ΔT**（収縮期ピーク S・切痕・拡張期ピーク D）が、実機のモニタ波形
（SNUADC/PLETH。帯域制限・AGC・雑音）で同定でき、窓間で再現するか。
同定できなければ信号鎖の問題が確定し、研究2（生波形）の根拠が立つ。同定できれば
研究1 の前提検証を Am_b/Am_p1 と特徴点 ΔT でやり直す価値がある。

事前規準（結果を見る前に固定。lab_log 追記14）
------------------------------------------------
対象  `data/target_cases.csv`（PLETH・ECG・ART と参照 CO を持つ症例。研究1 の在庫）を caseid 昇順に並べ、
      seed 0 の乱数で 20 例を無作為抽出する。結果を見て選び直さない。
窓    60 秒（研究1 と同じ）。ECG を基準に拍を切り、SQI を通った拍が **8 拍以上**ある窓を「解析できる窓」とする。
      各窓で (a) 通った拍を足で揃えて平均した 1 拍、(b) 各拍、に pda2 と同じ前処理
      （18 Hz・足→足基線・最大 1）を当て、`find_landmarks`（型・S・切痕・D）と `early_features`（b・p1・Am_b/Am_p1）を取る。
指標  ΔT_lm = D − S [ms]（型1 は切痕後の拡張期ピーク、型3 は肩。型4〜5 は NaN）、Am_b/Am_p1。
      陽性対照は同じ窓の PWTT（研究1 の窓間自己相関 +0.746）。
同定率  = 指標が有限な窓 ÷ 解析できる窓（症例ごと）。
再現性  = 隣り合う窓（60 秒差）の値の相関（lag-1 自己相関。症例ごと。対が 10 組以上）。
判定（指標ごと・結果を見る前に固定）
      **同定できる** = 同定率の症例中央値 ≥ 0.70 **かつ** 自己相関の症例中央値 ≥ 0.30
      陽性対照: PWTT の自己相関の症例中央値 ≥ 0.50。通らなければ表全体を無効とする（処理系の異常）
記述  型の分布（1/3/4/5）、切痕の顕著さ、雑音 σ、拍ごとと平均拍の同定率、症例内の変動係数、
      症例間の分離（級内相関 ICC(1)）、年齢との順位相関（20 例なので記述のみ）、
      （`data/features/case_*.csv` があれば）同じ窓の凍結版 PDA の ΔT・RI の自己相関。
書かないこと  「同定できたから実機で使える」（同定は再現性までで、妥当性は別の問い）。

使い方
------
    python3 scripts/32_vitaldb_landmark_identifiability.py --selftest
    python3 scripts/32_vitaldb_landmark_identifiability.py --run --jobs 4
    python3 scripts/32_vitaldb_landmark_identifiability.py --run --cases 17,19,...   （再実行・追試用。事前規準の 20 例は seed 0）
出力: data/vitaldb_landmark/case_{id}.csv（窓ごと）・summary.csv（症例ごと）・report.txt（表の全文）
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from src import pda2                                                     # noqa: E402
from src.beats import segment_beats, sqi, ensemble_average, estimate_noise  # noqa: E402
from src.indices import pwtt_series, detect_r_peaks, estimate_pleth_lag     # noqa: E402

FS = 500.0
WIN_S = 60.0
MIN_GOOD = 8                 # 解析できる窓の条件（研究1 と同じ）
MIN_PAIRS = 10               # 自己相関を出すのに要る隣接窓の対
N_CASES = 20
SEED = 0
GATE_ID_RATE = 0.70          # 同定率の症例中央値
GATE_AUTOCORR = 0.30         # 窓間 lag-1 自己相関の症例中央値（研究1b B-1 の可測性ゲートと同じ）
GATE_CONTROL = 0.50          # 陽性対照 PWTT の自己相関（研究1 の実測 +0.746）
DATA = ROOT / "data"
OUT = DATA / "vitaldb_landmark"
WAVE_TRACKS = ["SNUADC/PLETH", "SNUADC/ECG_II"]
INDICES = [("ens_dt_lm_ms", "特徴点 ΔT（平均拍）"), ("ens_amb", "Am_b/Am_p1（平均拍）")]
CONTROL = ("pwtt_ms", "PWTT（陽性対照）")


def vitaldb_version() -> str:
    """vitaldb の版。波形の再標本化が版で変わる（1.5.8 と 1.7.2 で拍の型と PWTT が違う。lab_log 追記22）ので必ず記録する。"""
    try:
        from importlib.metadata import version
        return version("vitaldb")
    except Exception:      # noqa: BLE001
        return "?"


# ================================================================ 症例の選択（事前規準）
def select_cases(n: int = N_CASES, seed: int = SEED, table=None) -> list:
    """target_cases.csv の caseid 昇順から seed 固定で n 例。結果を見て選び直さない。"""
    import pandas as pd
    t = pd.read_csv(DATA / "target_cases.csv") if table is None else table
    m = np.ones(len(t), bool)
    for c in ("pleth", "ecg"):
        if c in t:
            m &= t[c].astype(str).str.lower().isin(["true", "1"]).to_numpy()
    ids = sorted(int(c) for c in t.loc[m, "caseid"].unique())
    rng = np.random.default_rng(seed)
    pick = rng.choice(len(ids), size=min(n, len(ids)), replace=False)
    return sorted(int(ids[i]) for i in pick)


# ================================================================ 1 拍・1 窓
def _beat_features(y: np.ndarray, fs: float) -> dict:
    """1 拍（または平均拍）に pda2 の前処理 → 特徴点・早期特徴。失敗は NaN。"""
    nan = float("nan")
    out = {"klass": nan, "prom": nan, "S_ms": nan, "notch_ms": nan, "D_ms": nan,
           "dt_lm_ms": nan, "dt1_ms": nan, "p1_ms": nan, "b_ms": nan, "amb": nan}
    try:
        tt = np.arange(len(y)) / fs
        ys, _amp = pda2.preprocess(tt, np.asarray(y, float), fs)
        if ys is None:
            return out
        lm = pda2.find_landmarks(tt, ys)
        out["klass"] = float(lm["klass"])
        out["prom"] = float(lm.get("prom", nan))
        out["S_ms"] = float(lm["sys_t"]) * 1000.0
        out["notch_ms"] = float(lm["notch_t"]) * 1000.0
        out["D_ms"] = float(lm["dia_t"]) * 1000.0
        if lm["klass"] in (1, 3) and np.isfinite(lm["dia_t"]) and np.isfinite(lm["sys_t"]):
            out["dt_lm_ms"] = float((lm["dia_t"] - lm["sys_t"]) * 1000.0)
            if lm["klass"] == 1:
                out["dt1_ms"] = out["dt_lm_ms"]
        ef = pda2.early_features(tt, ys)
        out["p1_ms"] = float(ef["p1_t"]) * 1000.0
        out["b_ms"] = float(ef["b_t"]) * 1000.0
        a = float(ef["amb_amp1"])
        out["amb"] = a if np.isfinite(a) and 0.0 < a <= 1.5 else nan
    except Exception:      # noqa: BLE001
        pass
    return out


def window_landmarks(pleth, ecg, t0: float, lag: float) -> dict:
    """1 窓分。解析できない窓（拍 8 未満）は n_good だけ残して NaN。"""
    nan = float("nan")
    i0, i1 = int(t0 * FS), int((t0 + WIN_S) * FS)
    seg_p = np.nan_to_num(np.asarray(pleth[i0:i1], float))
    seg_e = np.nan_to_num(np.asarray(ecg[i0:i1], float))
    out = {"t0": float(t0), "n_beats": 0, "n_good": 0, "sigma": nan, "hr": nan, "pwtt_ms": nan,
           "ens_klass": nan, "ens_prom": nan, "ens_S_ms": nan, "ens_notch_ms": nan, "ens_D_ms": nan,
           "ens_dt_lm_ms": nan, "ens_dt1_ms": nan, "ens_p1_ms": nan, "ens_b_ms": nan, "ens_amb": nan,
           "beat_k1": nan, "beat_k13": nan, "beat_amb_ok": nan,
           "beat_dt_med": nan, "beat_dt_sd": nan, "beat_amb_med": nan, "beat_amb_sd": nan}
    if seg_p.size < int(WIN_S * FS) * 0.9 or not np.any(seg_p):
        return out
    try:
        beats = segment_beats(seg_p, FS, ecg=seg_e)
        good = [(s, e) for s, e in beats if sqi(seg_p[s:e], FS)["ok"]]
    except Exception:      # noqa: BLE001
        beats, good = [], []
    out["n_beats"], out["n_good"] = len(beats), len(good)
    try:
        pw = pwtt_series(seg_e, seg_p, FS, lag=lag)
        if pw.size >= 10:
            out["pwtt_ms"] = float(np.median(pw) * 1000.0)
        r = detect_r_peaks(seg_e, FS)
        if r.size >= 20:
            rr = np.diff(r) / FS
            rr = rr[(rr > 0.3) & (rr < 1.5)]
            if rr.size >= 10:
                out["hr"] = 60.0 / float(np.median(rr))
    except Exception:      # noqa: BLE001
        pass
    if len(good) < MIN_GOOD:
        return out
    out["sigma"] = float(np.nanmedian([estimate_noise(seg_p[s:e]) for s, e in good]))
    # (a) 平均拍
    try:
        y = ensemble_average([seg_p[s:e] for s, e in good])
        f = _beat_features(y, FS)
        out.update({"ens_klass": f["klass"], "ens_prom": f["prom"], "ens_S_ms": f["S_ms"],
                    "ens_notch_ms": f["notch_ms"], "ens_D_ms": f["D_ms"], "ens_dt_lm_ms": f["dt_lm_ms"],
                    "ens_dt1_ms": f["dt1_ms"], "ens_p1_ms": f["p1_ms"], "ens_b_ms": f["b_ms"], "ens_amb": f["amb"]})
    except Exception:      # noqa: BLE001
        pass
    # (b) 各拍
    ks, dts, ambs = [], [], []
    for s, e in good:
        f = _beat_features(seg_p[s:e], FS)
        ks.append(f["klass"])
        dts.append(f["dt_lm_ms"])
        ambs.append(f["amb"])
    ks = np.asarray(ks, float)
    dts = np.asarray(dts, float)
    ambs = np.asarray(ambs, float)
    out["beat_k1"] = float(np.mean(ks == 1))
    out["beat_k13"] = float(np.mean((ks == 1) | (ks == 3)))
    out["beat_amb_ok"] = float(np.mean(np.isfinite(ambs)))
    if np.isfinite(dts).sum() >= 3:
        out["beat_dt_med"], out["beat_dt_sd"] = float(np.nanmedian(dts)), float(np.nanstd(dts))
    if np.isfinite(ambs).sum() >= 3:
        out["beat_amb_med"], out["beat_amb_sd"] = float(np.nanmedian(ambs)), float(np.nanstd(ambs))
    return out


# ================================================================ 症例
def _vitaldb_loader(caseid: int):
    import vitaldb
    wav = vitaldb.load_case(caseid, WAVE_TRACKS, 1 / FS)
    return {"pleth": wav[:, 0].astype(np.float32), "ecg": wav[:, 1].astype(np.float32)}


def extract_case(caseid: int, loader=_vitaldb_loader, out_dir: Path | None = None):
    """1 症例の窓ごとの表を out_dir に置く。返り値 (caseid, DataFrame, エラー)。"""
    import pandas as pd
    out_dir = OUT if out_dir is None else out_dir
    fp = out_dir / f"case_{caseid}.csv"
    if fp.exists():
        return caseid, pd.read_csv(fp), None
    try:
        arrays = loader(caseid)
    except Exception as e:      # noqa: BLE001
        return caseid, None, f"取得失敗: {e}"
    pleth, ecg = arrays["pleth"], arrays["ecg"]
    dur = len(pleth) / FS
    lag = estimate_pleth_lag(ecg, pleth, FS)
    rows = [window_landmarks(pleth, ecg, float(t0), lag) for t0 in np.arange(0, dur - WIN_S, WIN_S)]
    df = pd.DataFrame(rows)
    df.insert(0, "caseid", caseid)
    out_dir.mkdir(parents=True, exist_ok=True)
    df.to_csv(fp, index=False)
    (out_dir / f"case_{caseid}_meta.json").write_text(json.dumps(
        {"caseid": caseid, "vitaldb": vitaldb_version(), "duration_min": round(dur / 60, 1),
         "pleth_lag_ms": round(lag * 1000) if np.isfinite(lag) else None,
         "n_windows": len(df), "n_analyzable": int((df["n_good"] >= MIN_GOOD).sum())}, ensure_ascii=False),
        encoding="utf-8")
    return caseid, df, None


def _extract_one(caseid: int):
    try:
        return extract_case(caseid)
    except Exception as e:      # noqa: BLE001
        return caseid, None, f"失敗: {e}"


# ================================================================ 統計の部品
def lag1_autocorr(t0: np.ndarray, x: np.ndarray, step: float = WIN_S, min_pairs: int = MIN_PAIRS) -> tuple:
    """隣り合う窓（step 秒差）の値の Pearson 相関。対が min_pairs 未満なら NaN。返り値 (r, 対の数)。"""
    t0 = np.asarray(t0, float)
    x = np.asarray(x, float)
    a, b = [], []
    for i in range(len(t0) - 1):
        if abs((t0[i + 1] - t0[i]) - step) < 1e-6 and np.isfinite(x[i]) and np.isfinite(x[i + 1]):
            a.append(x[i])
            b.append(x[i + 1])
    if len(a) < min_pairs:
        return float("nan"), len(a)
    a, b = np.asarray(a), np.asarray(b)
    if np.std(a) == 0 or np.std(b) == 0:
        return float("nan"), len(a)
    return float(np.corrcoef(a, b)[0, 1]), len(a)


def icc1(groups: list) -> float:
    """一元配置の級内相関 ICC(1)。groups は症例ごとの値の配列（有限値のみ使う）。"""
    g = [np.asarray(v, float)[np.isfinite(np.asarray(v, float))] for v in groups]
    g = [v for v in g if v.size >= 2]
    if len(g) < 2:
        return float("nan")
    n = np.array([v.size for v in g], float)
    means = np.array([v.mean() for v in g])
    grand = float(np.concatenate(g).mean())
    ssb = float(np.sum(n * (means - grand) ** 2))
    ssw = float(sum(np.sum((v - v.mean()) ** 2) for v in g))
    k = len(g)
    N = float(n.sum())
    msb = ssb / (k - 1)
    msw = ssw / (N - k) if N > k else float("nan")
    k0 = (N - float(np.sum(n ** 2)) / N) / (k - 1)
    den = msb + (k0 - 1) * msw
    return float((msb - msw) / den) if np.isfinite(den) and den > 0 else float("nan")


def case_summary(df) -> dict:
    """1 症例の同定率・自己相関・変動係数。"""
    nan = float("nan")
    ok = df[df["n_good"] >= MIN_GOOD]
    out = {"caseid": int(df["caseid"].iloc[0]) if "caseid" in df else -1,
           "n_windows": int(len(df)), "n_analyzable": int(len(ok)),
           "frac_analyzable": float(len(ok) / max(len(df), 1)),
           "sigma_med": float(np.nanmedian(ok["sigma"])) if len(ok) else nan,
           "hr_med": float(np.nanmedian(df["hr"])) if len(df) else nan}
    for k in (1, 3, 4, 5):
        out[f"ens_type{k}"] = float(np.mean(ok["ens_klass"] == k)) if len(ok) else nan
    out["ens_prom_med"] = float(np.nanmedian(ok.loc[ok["ens_klass"] == 1, "ens_prom"])) if (ok["ens_klass"] == 1).any() else nan
    for col, _lab in INDICES + [CONTROL, ("ens_dt1_ms", "型1 だけの ΔT")]:
        v = ok[col].to_numpy(float) if len(ok) else np.array([])
        out[f"id_{col}"] = float(np.isfinite(v).mean()) if v.size else nan
        r, npair = lag1_autocorr(ok["t0"].to_numpy(float), v) if len(ok) else (nan, 0)
        out[f"ac_{col}"], out[f"npair_{col}"] = r, int(npair)
        fin = v[np.isfinite(v)]
        out[f"med_{col}"] = float(np.median(fin)) if fin.size else nan
        out[f"cv_{col}"] = float(np.std(fin) / abs(np.mean(fin))) if fin.size >= 3 and np.mean(fin) != 0 else nan
    for col in ("beat_k1", "beat_k13", "beat_amb_ok"):
        out[f"{col}_med"] = float(np.nanmedian(ok[col])) if len(ok) else nan
    for col in ("beat_dt_sd", "beat_amb_sd"):
        out[f"{col}_med"] = float(np.nanmedian(ok[col])) if len(ok) else nan
    return out


def verdict(summ, gate_id: float = GATE_ID_RATE, gate_ac: float = GATE_AUTOCORR,
            gate_ctl: float = GATE_CONTROL) -> dict:
    """事前規準を機械的に当てる。summ は症例ごとの要約の DataFrame。"""
    out = {}
    ac_ctl = float(np.nanmedian(summ[f"ac_{CONTROL[0]}"])) if len(summ) else float("nan")
    out["control"] = {"ac": ac_ctl, "pass": bool(np.isfinite(ac_ctl) and ac_ctl >= gate_ctl)}
    for col, lab in INDICES:
        idr = float(np.nanmedian(summ[f"id_{col}"])) if len(summ) else float("nan")
        ac = float(np.nanmedian(summ[f"ac_{col}"])) if len(summ) else float("nan")
        ok = bool(np.isfinite(idr) and np.isfinite(ac) and idr >= gate_id and ac >= gate_ac)
        why = []
        if not (np.isfinite(idr) and idr >= gate_id):
            why.append(f"同定率 {idr:.2f} < {gate_id}")
        if not (np.isfinite(ac) and ac >= gate_ac):
            why.append(f"自己相関 {ac:.2f} < {gate_ac}" if np.isfinite(ac) else "自己相関を計算できる症例がない")
        out[col] = {"label": lab, "id_rate": idr, "ac": ac, "pass": ok, "why": "・".join(why)}
    return out


# ================================================================ 凍結版 PDA（あれば）
def frozen_pda_reference(caseid: int, df, feat_dir: Path | None = None, cases_csv: Path | None = None) -> dict:
    """研究1 の特徴量キャッシュ（data/features/case_{id}.csv）があれば、同じ窓の凍結版 ΔT・RI の自己相関を出す。"""
    import pandas as pd
    nan = float("nan")
    feat_dir = DATA / "features" if feat_dir is None else feat_dir
    cases_csv = DATA / "cases.csv" if cases_csv is None else cases_csv
    fp = feat_dir / f"case_{caseid}.csv"
    out = {"pda_ac_dt": nan, "pda_ac_ri": nan, "pda_n": 0}
    if not fp.exists():
        return out
    try:
        f = pd.read_csv(fp)
        h = nan
        if cases_csv.exists():
            demo = pd.read_csv(cases_csv, encoding="utf-8-sig")
            row = demo[demo["caseid"] == caseid]
            if len(row):
                h = float(row["height"].iloc[0]) / 100.0
        if "si" in f and np.isfinite(h):
            f["dt_ms"] = h / f["si"] * 1000.0
        elif "dt_ms" not in f:
            return out
        m = f.merge(df[["t0"]], on="t0", how="inner")
        out["pda_n"] = int(len(m))
        out["pda_ac_dt"] = lag1_autocorr(m["t0"].to_numpy(float), m["dt_ms"].to_numpy(float))[0]
        out["pda_ac_ri"] = lag1_autocorr(m["t0"].to_numpy(float), m["ri"].to_numpy(float))[0]
    except Exception:      # noqa: BLE001
        pass
    return out


# ================================================================ 報告
class _Tee:
    def __init__(self, *streams):
        self.streams = streams

    def write(self, s):
        for st in self.streams:
            st.write(s)

    def flush(self):
        for st in self.streams:
            st.flush()


def report(dfs: dict, out_dir: Path | None = None, ages: dict | None = None, feat_dir: Path | None = None) -> dict:
    import pandas as pd
    out_dir = OUT if out_dir is None else out_dir
    rows = []
    for cid, df in sorted(dfs.items()):
        s = case_summary(df)
        s.update(frozen_pda_reference(cid, df, feat_dir=feat_dir))
        s["age"] = float(ages.get(cid, np.nan)) if ages else np.nan
        rows.append(s)
    summ = pd.DataFrame(rows)
    out_dir.mkdir(parents=True, exist_ok=True)
    summ.to_csv(out_dir / "summary.csv", index=False)
    v = verdict(summ)
    allw = pd.concat(list(dfs.values()), ignore_index=True) if dfs else pd.DataFrame()
    okw = allw[allw["n_good"] >= MIN_GOOD] if len(allw) else allw

    print("=" * 96)
    print("VitalDB モニタ波形での特徴点・早期振幅比の同定可能性（事前規準は本ファイル冒頭・lab_log 追記14）")
    print("=" * 96)
    print(f"症例 {len(summ)} 例・窓 {int(summ['n_windows'].sum()) if len(summ) else 0}"
          f"（解析できる窓 {int(summ['n_analyzable'].sum()) if len(summ) else 0}）・vitaldb {vitaldb_version()}・pda2 {pda2.code_version()}")
    print(f"\n0. 陽性対照 {CONTROL[1]}: 窓間自己相関の症例中央値 {v['control']['ac']:.3f}（要求 ≥ {GATE_CONTROL}）"
          f" → {'合格' if v['control']['pass'] else '**不合格。表全体を無効とする**'}")
    print(f"\n{'-' * 96}\n1. 判定（指標ごと。同定率の症例中央値 ≥ {GATE_ID_RATE} かつ 自己相関の症例中央値 ≥ {GATE_AUTOCORR}）\n{'-' * 96}")
    print(f"{'指標':<26}{'同定率 中央値':>12}{'自己相関 中央値':>14}{'判定':>10}  理由")
    for col, lab in INDICES:
        r = v[col]
        print(f"{lab:<26}{r['id_rate']:>12.2f}{r['ac']:>14.2f}{('同定できる' if r['pass'] else '同定できない'):>10}  {r['why']}")
    print(f"\n{'-' * 96}\n2. 症例ごと\n{'-' * 96}")
    print(f"{'caseid':>6}{'年齢':>5}{'窓':>5}{'解析可':>6}{'σ':>7}{'型1':>5}{'型3':>5}{'型4+':>5}"
          f"{'同定ΔT':>7}{'自己相関ΔT':>10}{'同定Am':>7}{'自己相関Am':>10}{'自己相関PWTT':>12}{'CVΔT':>6}{'CVAm':>6}"
          f"{'拍ごと型1':>8}{'凍結ΔT自己相関':>12}")
    for _, s in summ.iterrows():
        def f_(x, w=1, fmt="{:.2f}"):
            return fmt.format(x) if np.isfinite(x) else "—"
        print(f"{int(s['caseid']):>6}{f_(s['age'], fmt='{:.0f}'):>5}{int(s['n_windows']):>5}{int(s['n_analyzable']):>6}"
              f"{f_(s['sigma_med'], fmt='{:.4f}'):>7}{f_(s['ens_type1']):>5}{f_(s['ens_type3']):>5}"
              f"{f_(s['ens_type4'] + s['ens_type5']):>5}"
              f"{f_(s['id_ens_dt_lm_ms']):>7}{f_(s['ac_ens_dt_lm_ms']):>10}{f_(s['id_ens_amb']):>7}{f_(s['ac_ens_amb']):>10}"
              f"{f_(s['ac_pwtt_ms']):>12}{f_(s['cv_ens_dt_lm_ms']):>6}{f_(s['cv_ens_amb']):>6}"
              f"{f_(s['beat_k1_med']):>8}{f_(s['pda_ac_dt']):>12}")
    print(f"\n{'-' * 96}\n3. 記述\n{'-' * 96}")
    if len(okw):
        kl = okw["ens_klass"].to_numpy(float)
        print(f"  平均拍の型（解析できる窓 {len(okw)}）: 型1 {np.mean(kl == 1):.1%}・型3 {np.mean(kl == 3):.1%}・"
              f"型4 {np.mean(kl == 4):.1%}・型5 {np.mean(kl == 5):.1%}・失敗 {np.mean(~np.isfinite(kl)):.1%}")
        p1 = okw.loc[okw["ens_klass"] == 1, "ens_prom"].dropna()
        if len(p1):
            print(f"  型1 の切痕の顕著さ（拡張期ピーク−切痕）: 中央値 {p1.median():.3f}・10% 点 {p1.quantile(0.1):.3f}"
                  f"（PWDB は中央値 0.042・閾値 0.01）")
        sg = okw["sigma"].dropna()
        if len(sg):
            print(f"  拍の相対雑音 σ: 中央値 {sg.median():.4f}・90% 点 {sg.quantile(0.9):.4f}（PWDB は 0）")
        print(f"  拍ごとの同定率（窓の中央値の症例中央値）: 型1 {np.nanmedian(summ['beat_k1_med']):.2f}・"
              f"型1+3 {np.nanmedian(summ['beat_k13_med']):.2f}・Am_b/Am_p1 {np.nanmedian(summ['beat_amb_ok_med']):.2f}"
              f" ／ 平均拍: ΔT {np.nanmedian(summ['id_ens_dt_lm_ms']):.2f}・Am_b/Am_p1 {np.nanmedian(summ['id_ens_amb']):.2f}")
        print(f"  拍間の SD（窓内・症例中央値）: ΔT {np.nanmedian(summ['beat_dt_sd_med']):.1f} ms・"
              f"Am_b/Am_p1 {np.nanmedian(summ['beat_amb_sd_med']):.3f}")
        for col, lab in INDICES + [CONTROL]:
            groups = [g[col].to_numpy(float) for _c, g in okw.groupby("caseid")]
            print(f"  症例間の分離 ICC(1) {lab}: {icc1(groups):.2f}"
                  f"（症例中央値の範囲 {np.nanmin(summ['med_' + col]):.3g}〜{np.nanmax(summ['med_' + col]):.3g}）")
        if ages and summ["age"].notna().sum() >= 10:
            from scipy.stats import spearmanr
            for col, lab in INDICES:
                m = summ["age"].notna() & summ["med_" + col].notna()
                if m.sum() >= 10:
                    rr = spearmanr(summ.loc[m, "age"], summ.loc[m, "med_" + col]).correlation
                    print(f"  年齢との順位相関（症例中央値・記述のみ・n={int(m.sum())}）{lab}: {rr:+.2f}"
                          f"（研究1 の凍結版 ΔT は −0.197）")
        if summ["pda_n"].sum() > 0:
            print(f"  凍結版 PDA（研究1 のキャッシュがある {int((summ['pda_n'] > 0).sum())} 例）: 同じ窓の自己相関"
                  f" ΔT {np.nanmedian(summ['pda_ac_dt']):.2f}・RI {np.nanmedian(summ['pda_ac_ri']):.2f}")
    print(f"\n{'-' * 96}\n読み方\n{'-' * 96}")
    print("  同定できる = 同定率 ≥ 0.70 かつ 自己相関 ≥ 0.30（症例中央値）。片方だけなら「同定できるが窓間で再現しない」等と書く。")
    print("  「同定できる」は再現性まで。妥当性（何を測っているか）は別の問いで、研究1 の前提検証のやり直しで問う。")
    print("  同定できなければ信号鎖（帯域制限・AGC・雑音）の問題が確定し、研究2（生波形）の根拠が立つ。")
    return {"summary": summ, "verdict": v}


def run(cases: list, jobs: int, out_dir: Path | None = None) -> None:
    import pandas as pd
    out_dir = OUT if out_dir is None else out_dir
    out_dir.mkdir(parents=True, exist_ok=True)
    print(f"症例（事前規準: target_cases.csv の caseid 昇順から seed {SEED}）: {cases}", flush=True)
    dfs, errs = {}, {}
    if jobs > 1:
        from concurrent.futures import ProcessPoolExecutor, as_completed
        with ProcessPoolExecutor(max_workers=jobs) as ex:
            futs = {ex.submit(_extract_one, c): c for c in cases}
            for f in as_completed(futs):
                cid, df, err = f.result()
                if err:
                    errs[cid] = err
                    print(f"  case {cid}: {err}", flush=True)
                else:
                    dfs[cid] = df
                    print(f"  case {cid}: 窓 {len(df)}・解析できる窓 {int((df['n_good'] >= MIN_GOOD).sum())}", flush=True)
    else:
        for c in cases:
            cid, df, err = _extract_one(c)
            if err:
                errs[cid] = err
                print(f"  case {cid}: {err}", flush=True)
            else:
                dfs[cid] = df
                print(f"  case {cid}: 窓 {len(df)}・解析できる窓 {int((df['n_good'] >= MIN_GOOD).sum())}", flush=True)
    ages = {}
    cp = DATA / "cases.csv"
    if cp.exists():
        demo = pd.read_csv(cp, encoding="utf-8-sig")
        ages = {int(r["caseid"]): float(r["age"]) for _, r in demo.iterrows() if int(r["caseid"]) in dfs}
    import io
    buf = io.StringIO()
    old = sys.stdout
    sys.stdout = _Tee(old, buf)
    try:
        report(dfs, out_dir=out_dir, ages=ages)
        if errs:
            print(f"\n取得できなかった症例 {len(errs)}: {errs}")
    finally:
        sys.stdout = old
    (out_dir / "report.txt").write_text(buf.getvalue(), encoding="utf-8")
    print(f"\n表の全文: {out_dir / 'report.txt'}・症例ごと: {out_dir / 'summary.csv'}")


# ================================================================ 自己検証
def _synth_case(dur_s: float = 20 * 60, seed: int = 0, drift: bool = True, noise: float = 0.15):
    """合成の心電図と脈波。drift=True で反射波の位置・立ち上がりの幅・脈波の遅延をゆっくり（周期 10 分）動かす。"""
    from scipy.special import erf
    rng = np.random.default_rng(seed)
    n = int(dur_s * FS)
    ecg = np.zeros(n)
    pleth = np.full(n, 50.0)
    t_r = 0.0
    L = int(1.6 * FS)
    while t_r < dur_s + 2:
        i_r = int(t_r * FS)
        if 0 <= i_r < n:
            ecg[i_r:i_r + 5] = 1.0
        ph = 2 * np.pi * t_r / 600.0
        d_ref = 0.30 + (0.04 * np.sin(ph) if drift else 0.0)
        w_rise = 0.02 + (0.006 * np.sin(ph + 1.0) if drift else 0.0)
        tau = 0.35 + (0.10 * np.sin(ph + 1.0) if drift else 0.0)      # 減衰が速いほど Am_b/Am_p1 は大きい
        delay = 0.18 + 0.03 + 0.66 + (0.006 * np.sin(ph + 2.0) if drift else 0.0)
        j0 = i_r + int(round(delay * FS))
        j1 = min(j0 + L, n)
        if j0 < n:
            tp = np.arange(j1 - j0) / FS
            pleth[j0:j1] += 40.0 * (0.5 * (1 + erf((tp - 0.05) / (w_rise * np.sqrt(2))))
                                   * np.exp(-tp / tau) + 0.25 * np.exp(-0.5 * ((tp - d_ref) / 0.07) ** 2))
        t_r += float(rng.uniform(0.85, 1.05))
    pleth = pleth + rng.normal(0, noise, n)
    return ecg.astype(np.float32), pleth.astype(np.float32)


def selftest() -> int:
    import contextlib
    import io
    import tempfile
    import pandas as pd
    ok = True

    def rep(name, cond, detail=""):
        nonlocal ok
        ok &= bool(cond)
        print(f"  [{'PASS' if cond else 'FAIL'}] {name}{('  ' + detail) if detail else ''}", flush=True)

    print("== 32_vitaldb_landmark_identifiability 自己検証（合成データ・ネットワーク不要） ==\n")
    # 1. 症例の選択が決定的
    tab = pd.DataFrame({"caseid": np.arange(1, 201), "pleth": True, "ecg": True})
    a, b = select_cases(20, 0, table=tab), select_cases(20, 0, table=tab)
    rep("症例の選択が seed で決定的（20 例・重複なし・昇順）", a == b and len(set(a)) == 20 and a == sorted(a), str(a[:6]) + "…")
    rep("seed を変えると別の 20 例", select_cases(20, 1, table=tab) != a)
    # 2. 自己相関・ICC の部品
    rng = np.random.default_rng(0)
    x = np.zeros(200)
    for i in range(1, 200):
        x[i] = 0.8 * x[i - 1] + rng.normal()
    r, npair = lag1_autocorr(np.arange(200) * WIN_S, x)
    rep("lag-1 自己相関（AR(1) φ=0.8 → 0.6〜0.9）", 0.6 < r < 0.9 and npair == 199, f"r={r:.2f}")
    r2, _ = lag1_autocorr(np.arange(200) * WIN_S * 2, x)
    rep("窓が隣接していなければ対を作らない（NaN）", not np.isfinite(r2))
    hi = [rng.normal(m, 1, 30) for m in (0, 5, 10, 15)]
    lo = [rng.normal(0, 1, 30) for _ in range(4)]
    rep("ICC(1): 症例で平均が違えば高く、同じ分布なら低い", icc1(hi) > 0.8 and icc1(lo) < 0.3,
        f"{icc1(hi):.2f} / {icc1(lo):.2f}")
    # 3. 判定の規則（単体）
    s_ok = pd.DataFrame({"ac_pwtt_ms": [0.8] * 5, "id_ens_dt_lm_ms": [0.9] * 5, "ac_ens_dt_lm_ms": [0.5] * 5,
                         "id_ens_amb": [0.95] * 5, "ac_ens_amb": [0.2] * 5})
    v = verdict(s_ok)
    rep("判定: ΔT は同定できる、Am は自己相関不足で同定できない、陽性対照 合格",
        v["control"]["pass"] and v["ens_dt_lm_ms"]["pass"] and not v["ens_amb"]["pass"] and "自己相関" in v["ens_amb"]["why"])
    s_bad = s_ok.copy()
    s_bad["ac_pwtt_ms"] = 0.1
    rep("判定: 陽性対照が通らなければ不合格になる", not verdict(s_bad)["control"]["pass"])
    # 4. 合成症例（ゆっくり動く反射波・立ち上がり・遅延）→ 同定と再現性
    ecg, pleth = _synth_case(20 * 60, seed=3, drift=True)
    with tempfile.TemporaryDirectory() as td:
        od = Path(td)
        cid, df, err = extract_case(9001, loader=lambda c: {"pleth": pleth, "ecg": ecg}, out_dir=od)
        rep("抽出が通り、窓ごとに平均拍と拍ごとの特徴が出る", err is None and len(df) >= 18
            and (df["n_good"] >= MIN_GOOD).mean() > 0.9, f"窓 {len(df)}")
        s = case_summary(df)
        rep("合成の型1 波形で ΔT と Am_b/Am_p1 が同定される（同定率 ≥ 0.9）",
            s["id_ens_dt_lm_ms"] >= 0.9 and s["id_ens_amb"] >= 0.9,
            f"ΔT {s['id_ens_dt_lm_ms']:.2f}・Am {s['id_ens_amb']:.2f}・型1 {s['ens_type1']:.2f}")
        rep("仕込んだゆっくりした変動が窓間の自己相関に出る（ΔT・Am・PWTT ≥ 0.3）",
            s["ac_ens_dt_lm_ms"] >= 0.3 and s["ac_ens_amb"] >= 0.3 and s["ac_pwtt_ms"] >= 0.3,
            f"ΔT {s['ac_ens_dt_lm_ms']:.2f}・Am {s['ac_ens_amb']:.2f}・PWTT {s['ac_pwtt_ms']:.2f}")
        dt_med = s["med_ens_dt_lm_ms"]
        rep("ΔT の値が仕込み（拡張期ピーク 0.30 s − 収縮期ピーク ≈ 0.10 s ≈ 200 ms）に近い（150〜260）",
            150 <= dt_med <= 260, f"{dt_med:.0f} ms")
        rep("拍ごとの同定率も出る（型1 ≥ 0.8）", s["beat_k1_med"] >= 0.8, f"{s['beat_k1_med']:.2f}")
        ecg0, pleth0 = _synth_case(12 * 60, seed=4, drift=False)
        cid0, df0, _ = extract_case(9002, loader=lambda c: {"pleth": pleth0, "ecg": ecg0}, out_dir=od)
        s0 = case_summary(df0)
        rep("変動を仕込まなければ自己相関は低い（< 0.3。雑音だけ）", not (s0["ac_ens_dt_lm_ms"] >= 0.3),
            f"ΔT {s0['ac_ens_dt_lm_ms']:.2f}")
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            res = report({9001: df, 9002: df0}, out_dir=od / "out", ages={9001: 50, 9002: 60})
        out = buf.getvalue()
        rep("表が出て summary.csv が書かれる", (od / "out" / "summary.csv").exists() and "判定" in out and len(res["summary"]) == 2)
        cid2, df2, err2 = extract_case(9001, loader=lambda c: (_ for _ in ()).throw(RuntimeError("no")), out_dir=od)
        rep("キャッシュがあれば再取得しない", err2 is None and len(df2) == len(df))
    print("\n" + ("ALL PASS" if ok else "FAIL あり"))
    return 0 if ok else 1


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--run", action="store_true", help="20 例を取得して表を出す（vitaldb・ネットワーク）")
    ap.add_argument("--cases", type=str, default=None, help="caseid をカンマ区切りで指定（事前規準の 20 例は seed 0）")
    ap.add_argument("--n", type=int, default=N_CASES)
    ap.add_argument("--jobs", type=int, default=1)
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--out", type=str, default=None, help="出力先（既定 data/vitaldb_landmark。vitaldb の版ごとに分けるとき）")
    args = ap.parse_args()
    if args.jobs < 1:
        ap.error("--jobs は 1 以上")
    if args.selftest:
        sys.exit(selftest())
    if args.run:
        cases = ([int(c) for c in args.cases.split(",")] if args.cases else select_cases(args.n, SEED))
        global OUT
        if args.out:
            OUT = Path(args.out)
        run(cases, args.jobs, out_dir=OUT)
    else:
        ap.print_help()


if __name__ == "__main__":
    main()
