#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""【探索・凍結後】論文1: 凍結版 PDA の ΔT と血圧、および特徴点法との比較（VitalDB 862 例）。

なぜ必要か
----------
論文1 は「血管指標は症例内の ΔPWTT% をほとんど説明しない」（前提検証の r² 0.044）で
終わった。**凍結後に残っている問いが 2 つある。**

  (1) 凍結版 PDA の ΔT は血圧と関連するか。関連するとして、それは心拍数を介した
      見かけのものではないか。20番の因子別主効果では、凍結版 ΔT を最も動かす因子は
      心拍数である（主効果 −10.9%・ρ −0.54。lab_log 2026-09-03）。45番（RI を心拍数で
      調整する）と同じ論法を、実機の症例内変動に当てる。
  (2) 陰性は「分解由来」という指標の作り方に由来するのではないか。32番は実機のモニタ
      波形で特徴点が同定できることを 20 例で示した。同じウィンドウで特徴点法
      （fiducial point analysis）の ΔT・RI を出せば、**指標の作り方の違いだけ**を
      比べられる。

**論文1 の主要評価（percentage error）も無益性の判定も再計算しない。**この台本の出力は
すべて探索的（凍結後）である。

定義
----
  ΔT_PDA [ms]   身長[m] / SI × 1000。SI は凍結版 PDA（2 カーネル）の成分波ピーク時間差
                から求めた指標で、`data/features/` の si 列（03番）。32番の
                frozen_pda_reference と同じ式である
  RI_PDA        同じ当てはめの 第2成分／第1成分 のピーク高さ比（同 ri 列）
  ΔT_LM [ms]    平均拍の収縮期ピーク S から拡張期ピーク D までの時間（32番の
                ens_dt_lm_ms）。型1 は切痕の後の拡張期ピーク、型3 は下降脚の変曲点で
                代用、型4・型5 は値なし
  RI_LM         同じ平均拍の D の高さ ÷ S の高さ（pda2.find_landmarks の dia_v / sys_v）
  SI_LM [m/s]   身長[m] / ΔT_LM
  ΔTn           ΔT[s] × HR / 60（= ΔT ÷ RR 間隔）。心周期に対する割合に直した ΔT
  Δ〜%          その集合の初回ウィンドウからの相対変化（`src.models._rel`。論文1 と同じ）
  T1・T2−T1     21番の分解。T1 = R波 → 橈骨動脈圧の立ち上がり、T2（= PWTT）= R波 →
                指尖脈波の立ち上がり、T2 − T1 = 橈骨→指尖の伝播時間（前駆出期を含まない）

問うこと
--------
  節1  ΔT_PDA% は ΔMAP% と関連するか。ΔHR% を与えても残るか（全ウィンドウ・症例内）
  節2  同じ指標（ΔT・RI）を 2 法で同じウィンドウから出したとき、相手との関連（表A・表B）・
       前提検証の回帰（表C）・両者の一致（表D）はどう違うか（共通ウィンドウ）

予測（2026-09-14、計算の前に固定。当たっても外れても成立・不成立の判定は付けない。事後・記述）:
(P1) 全ウィンドウで、ρ(ΔT_PDA%, ΔMAP%) の症例中央値は正で +0.10 以上であり、ΔHR% を与えた偏順位相関ではその大きさが調整前の半分以下になる。根拠: 陽性対照の記録（566 例）で ΔT と平均血圧の症例内相関は +0.277。PWDB で凍結版 ΔT を最も動かす因子は心拍数（主効果 −10.9%・ρ −0.54）。昇圧に伴う反射性の徐脈で ΔT が延びるという読み。
(P2) ρ(ΔT_PDA%, ΔHR%) の症例中央値は負で −0.20 以下。
(P3) 共通ウィンドウで、ρ(ΔT_LM%, ΔT1%) の症例中央値は ρ(ΔT_PDA%, ΔT1%) の症例中央値より 0.05 以上大きい。根拠: PWDB で大動脈脈波伝播速度との |ρ| は特徴点法 0.710（同梱値。自前実装 pda2.find_landmarks では 0.513）に対し凍結版 0.223。
(P4) 共通ウィンドウで、ρ(ΔT_PDA%, ΔT_LM%) の症例中央値は +0.20 以上 +0.60 未満。根拠: 分解由来と特徴点由来は構造的に別の量（Goswami 2010）で、PWDB でも一致しない。
(P5) 特徴点法の ΔSI%・ΔRI% で ΔPWTT% を回帰した切片ありの r²（全症例プール）は 0.05 未満。根拠: 論文1 の 0.044、36番（早期振幅比）の 0.0002。

前提
----
`scripts/03_run_analysis.py`（`data/features/`）と `scripts/15_art_indices.py`
（`data/features_art/`）が完走していること。段階 E（`--extract`）はさらに vitaldb と
ネットワークが要る（1 台目でしか動かない）。段階 S（統計）は `data/features_lm/` を読む。
版は確認的解析と同じにそろえる（Python 3.9.6・NumPy 2.0.2・SciPy 1.13.1・pandas 2.3.3・
**vitaldb 1.5.8**）。vitaldb 1.7.2 は波形の再標本化が変わり、拍の型が変わる（lab_log 追記22）。

限界
----
自前の特徴点実装（`pda2.find_landmarks`）は PWDB で ΔT 0.513・RI 0.236（33番。Charlton
同梱値は 0.705／0.501）なので、本台本の特徴点法の上限はこの実装の値であり、RI は PWDB でも
規準に達していない。共通ウィンドウは拡張期ピークか変曲点のある型（1・3）に限られ、全体の
約 3 分の 2（32番: 型4 が 34.9%）である。全ウィンドウでの PDA の行を並べるのはこの選択の
影響を見るためである。
さらに、**特徴点 ΔT と早期振幅比の同定率・隣接ウィンドウの自己相関は印字しない。**
これは論文3 の主要評価項目であり、その SAP は未凍結だからである（抽出は行うので
`data/features_lm/` には列として残る）。

使い方
------
    python3 scripts/47_dt_bp_landmark_compare.py --selftest
    python3 scripts/47_dt_bp_landmark_compare.py --extract --jobs 8
    python3 scripts/47_dt_bp_landmark_compare.py --stats-only
    python3 scripts/47_dt_bp_landmark_compare.py --stats-only --partial

既定（引数なし）は段階 S だけを行う。取得と抽出は `--extract` を付けたときだけ走る。
結果は print するので、残すときは tee で `docs/research/results/` に落とす。
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import sys
import time
import unicodedata
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src import pda2                                                    # noqa: E402
from src.beats import segment_beats, sqi, ensemble_average              # noqa: E402
from src.indices import estimate_pleth_lag                              # noqa: E402
from src.models import _rel                                             # noqa: E402

DATA = ROOT / "data"
FEAT = DATA / "features"          # 03番（論文1 の主解析）
AFEAT = DATA / "features_art"     # 15番（動脈圧由来の指標）
LFEAT = DATA / "features_lm"      # 本台本の段階 E（特徴点法）


def _load(stem: str, name: str):
    """数字始まりの台本を名前で読み込む（import 文では書けない）。45番・26番と同じ手口。"""
    p = Path(__file__).resolve().parent / stem
    spec = importlib.util.spec_from_file_location(name, p)
    m = importlib.util.module_from_spec(spec)
    sys.modules[name] = m
    spec.loader.exec_module(m)
    return m


# 特徴点の取り方は 32番の実物をそのまま使う（写し取ると黙ってずれる）。**32番は改変しない。**
m32 = _load("32_vitaldb_landmark_identifiability.py", "m32")

FS = m32.FS                    # 500 Hz
WIN_S = m32.WIN_S              # 60 秒
MIN_GOOD = m32.MIN_GOOD        # 解析できるウィンドウの条件（SQI を通った拍 8 以上）
MIN_WIN = 12                   # 症例採用に必要なウィンドウ数（03番の MIN_WINDOWS と同じ）
COVERAGE_MIN = 0.95            # 段階 E がここまで終わっていないと集計しない（--partial で解除）
DT_CHK_TOL_MS = 1e-9           # 再導出した ΔT と 32番の ΔT の許容差
ADULT_AGE = 18.0               # 症例間の解析は成人に限る（06番と同じ）
MIN_N_RHO = 8                  # 相関を出すのに要る対の数（21番と同じ）
K1_MIN_ROWS = 8                # 型1 限定の症例内相関に要る行数
K1_MIN_CASES = 30              # 型1 限定の行を印字する最小症例数

# 照合先として印字する既知の値（この台本は再計算しない）
PAPER1_RHO_AGE_DT = -0.197     # 06番: ρ(ΔT_PDA 症例中央値, 年齢)・成人 849 例
PAPER1_N_ADULT = 849

# 予測（2026-09-14。**計算の前に固定した。** docstring と同文）
PRED_P1_RHO_MIN = 0.10         # P1: ρ(ΔT_PDA%, ΔMAP%) の症例中央値の下限
PRED_P1_RATIO = 0.50           # P1: 偏順位相関は調整前の大きさのこの割合以下
PRED_P2_RHO_MAX = -0.20        # P2: ρ(ΔT_PDA%, ΔHR%) の症例中央値の上限
PRED_P3_GAP = 0.05             # P3: ρ(ΔT_LM%, ΔT1%) − ρ(ΔT_PDA%, ΔT1%) の下限
PRED_P4_RANGE = (0.20, 0.60)   # P4: ρ(ΔT_PDA%, ΔT_LM%) の症例中央値が入る範囲
PRED_P5_R2_MAX = 0.05          # P5: 特徴点法の前提検証（切片あり）の r² の上限

# 段階 S が読む列（同名列の衝突を避けるため、結合の前に必要な列だけに絞る）
COLS_MAIN = ["t0", "pwtt", "si", "ri", "hr", "map"]
COLS_ART = ["t0", "t1_ms", "sbp", "dbp"]
COLS_LM = ["t0", "ens_dt_lm_ms", "ens_ri_lm", "ens_klass", "beat_dt_med"]
NEED_FINITE = ["t1_ms", "pwtt", "si", "ri", "map", "hr"]   # 全ウィンドウの条件（21番＋map・hr）


# ================================================================ 印字と統計の部品
def _pad(s, w: int, right: bool = False) -> str:
    """表示幅で揃える（日本語は 2 文字分。f 文字列の桁指定は文字数なのでずれる）。"""
    used = sum(2 if unicodedata.east_asian_width(c) in "WF" else 1 for c in str(s))
    fill = " " * max(0, w - used)
    return (fill + str(s)) if right else (str(s) + fill)


def _f(v: float, w: int = 7, prec: int = 3, sign: bool = True) -> str:
    """欠測を「—」にして桁を揃える。"""
    if v is None or not np.isfinite(v):
        return _pad("—", w, right=True)
    return f"{v:>+{w}.{prec}f}" if sign else f"{v:>{w}.{prec}f}"


def _spearman(x, y, min_n: int = MIN_N_RHO) -> float:
    """順位相関。21番の `_spearman` と同じ規約（最少本数だけ引数にした）。"""
    from scipy.stats import rankdata
    x, y = np.asarray(x, float), np.asarray(y, float)
    g = np.isfinite(x) & np.isfinite(y)
    if g.sum() < min_n or np.ptp(x[g]) == 0 or np.ptp(y[g]) == 0:
        return float("nan")
    return float(np.corrcoef(rankdata(x[g]), rankdata(y[g]))[0, 1])


def _pearson(x, y, min_n: int = MIN_N_RHO) -> float:
    """積率相関。欠測・定数入力・最少本数の扱いは `_spearman` と同じ（21番と同じ規約）。"""
    x, y = np.asarray(x, float), np.asarray(y, float)
    g = np.isfinite(x) & np.isfinite(y)
    if g.sum() < min_n or np.ptp(x[g]) == 0 or np.ptp(y[g]) == 0:
        return float("nan")
    return float(np.corrcoef(x[g], y[g])[0, 1])


def _ols_resid(y: np.ndarray, covs: list) -> np.ndarray:
    """y を [1, covs...] に最小二乗回帰した残差。共変量が一定でも落ちない（45番と同じ）。"""
    A = np.column_stack([np.ones(y.size)] + [np.asarray(c, float) for c in covs])
    beta, *_ = np.linalg.lstsq(A, y, rcond=None)
    return y - A @ beta


def _partial_spearman(x: np.ndarray, y: np.ndarray, z: np.ndarray) -> float:
    """順位に直してからの偏相関 ρ(x, y | z)。45番の同名関数をそのまま使う。"""
    from scipy.stats import rankdata
    rx, ry, rz = rankdata(x), rankdata(y), rankdata(z)
    if min(np.ptp(rx), np.ptp(ry), np.ptp(rz)) == 0:
        return float("nan")
    rxy = float(np.corrcoef(rx, ry)[0, 1])
    rxz = float(np.corrcoef(rx, rz)[0, 1])
    ryz = float(np.corrcoef(ry, rz)[0, 1])
    den = np.sqrt(max(0.0, (1.0 - rxz ** 2) * (1.0 - ryz ** 2)))
    if den <= 1e-12:
        return float("nan")
    return float(np.clip((rxy - rxz * ryz) / den, -1.0, 1.0))


def _partial_rho(x, y, zs: list, min_n: int = MIN_N_RHO) -> float:
    """偏順位相関 ρ(x, y | zs)。欠測を落としてから 45番の規約に渡す。

    共変量が 1 つのときは `_partial_spearman` をそのまま呼ぶ。2 つ以上のときは
    順位に直してから `_ols_resid` で共変量を除いた残差どうしの Pearson を返す
    （共変量 1 つならこの 2 つは一致する。自己検証で確かめる）。
    """
    from scipy.stats import rankdata
    x, y = np.asarray(x, float), np.asarray(y, float)
    zs = [np.asarray(z, float) for z in zs]
    g = np.isfinite(x) & np.isfinite(y)
    for z in zs:
        g &= np.isfinite(z)
    if g.sum() < min_n:
        return float("nan")
    if len(zs) == 1:
        return _partial_spearman(x[g], y[g], zs[0][g])
    rx, ry = rankdata(x[g]), rankdata(y[g])
    rz = [rankdata(z[g]) for z in zs]
    return _pearson(_ols_resid(rx, rz), _ols_resid(ry, rz), min_n=min_n)


def _med_iqr(v) -> tuple:
    """有限値だけの (中央値, 第1四分位, 第3四分位, 個数)。21番と同じ。"""
    v = np.asarray(v, float)
    v = v[np.isfinite(v)]
    if v.size == 0:
        return float("nan"), float("nan"), float("nan"), 0
    return (float(np.median(v)), float(np.percentile(v, 25)),
            float(np.percentile(v, 75)), int(v.size))


def _pos_frac(v) -> float:
    """有限値のうち正の値の割合。"""
    v = np.asarray(v, float)
    v = v[np.isfinite(v)]
    return float((v > 0).mean()) if v.size else float("nan")


def _sign_p(v) -> float:
    """符号検定の両側 p（正の個数を n 回の二項検定にかける）。0 ちょうどは正に数えない。"""
    from scipy.stats import binomtest
    v = np.asarray(v, float)
    v = v[np.isfinite(v)]
    if v.size < 1:
        return float("nan")
    return float(binomtest(int((v > 0).sum()), int(v.size), 0.5).pvalue)


def _fisher_ci(r: float, n: int) -> tuple:
    """Fisher z による 95% 信頼区間（06番と同じ規約）。"""
    if not np.isfinite(r) or n < 4:
        return float("nan"), float("nan")
    z = np.arctanh(np.clip(r, -0.999999, 0.999999))
    se = 1.0 / np.sqrt(n - 3)
    return float(np.tanh(z - 1.96 * se)), float(np.tanh(z + 1.96 * se))


def _rel_of(x) -> np.ndarray:
    """`src.models._rel`（論文1 と同じ相対変化）。有限値が無い列は全 NaN を返す。"""
    x = np.asarray(x, float)
    if not np.isfinite(x).any():
        return np.full(x.shape, np.nan)
    return _rel(x)


# ================================================================ 段階 E: 特徴点法の抽出
def _ens_landmarks(seg_p: np.ndarray, seg_e: np.ndarray) -> dict:
    """1 ウィンドウの平均拍から特徴点の高さを取り直す（32番と同じ手順）。

    32番は ΔT（時間）しか残していないので、RI_LM（高さの比）を得るために同じ拍の
    切り出し・同じ平均拍・同じ前処理をもう一度当てる。**32番は改変しない。**
    `ens_dt_chk_ms` は再導出した ΔT で、呼び出し側が 32番の値と突き合わせる。
    """
    nan = float("nan")
    out = {"ens_sys_v": nan, "ens_dia_v": nan, "ens_dt_chk_ms": nan, "ens_ri_lm": nan}
    try:
        beats = segment_beats(seg_p, FS, ecg=seg_e)
        good = [(s, e) for s, e in beats if sqi(seg_p[s:e], FS)["ok"]]
        if len(good) < MIN_GOOD:
            return out
        y = ensemble_average([seg_p[s:e] for s, e in good])
        tt = np.arange(len(y)) / FS
        ys, _amp = pda2.preprocess(tt, y, FS)
        if ys is None:
            return out
        lm = pda2.find_landmarks(tt, ys)
        sv, dv = float(lm["sys_v"]), float(lm["dia_v"])
        out["ens_sys_v"], out["ens_dia_v"] = sv, dv
        if lm["klass"] in (1, 3) and np.isfinite(lm["dia_t"]) and np.isfinite(lm["sys_t"]):
            out["ens_dt_chk_ms"] = float((lm["dia_t"] - lm["sys_t"]) * 1000.0)
            if np.isfinite(sv) and np.isfinite(dv) and sv > 0:
                out["ens_ri_lm"] = dv / sv
    except Exception:      # noqa: BLE001
        return out
    return out


def window_landmarks_47(pleth, ecg, t0: float, lag: float) -> dict:
    """1 ウィンドウ分。32番の `window_landmarks` の全キーに、高さ由来の 4 列を足す。

    足す列: ens_sys_v・ens_dia_v・ens_dt_chk_ms・ens_ri_lm。
    再導出した ΔT が 32番の ΔT と食い違ったら RuntimeError で止める（黙って別の量に
    なるのを防ぐ。この検算のためだけに ens_dt_chk_ms を残している）。
    """
    out = dict(m32.window_landmarks(pleth, ecg, t0, lag))
    out.update({"ens_sys_v": float("nan"), "ens_dia_v": float("nan"),
                "ens_dt_chk_ms": float("nan"), "ens_ri_lm": float("nan")})
    if not (float(out.get("n_good", 0)) >= MIN_GOOD):
        return out
    i0, i1 = int(t0 * FS), int((t0 + WIN_S) * FS)
    seg_p = np.nan_to_num(np.asarray(pleth[i0:i1], float))
    seg_e = np.nan_to_num(np.asarray(ecg[i0:i1], float))
    out.update(_ens_landmarks(seg_p, seg_e))
    a, b = float(out["ens_dt_chk_ms"]), float(out["ens_dt_lm_ms"])
    if np.isfinite(a) and np.isfinite(b) and abs(a - b) > DT_CHK_TOL_MS:
        raise RuntimeError(f"再導出した ΔT が 32番と一致しない: t0={t0} {a} 対 {b} ms")
    return out


def extract_case_47(caseid: int, loader=None, out_dir=None):
    """1 症例のウィンドウごとの表を out_dir に置く。返り値 (caseid, DataFrame, エラー)。

    構造は 32番の `extract_case` と同じ（キャッシュ → loader → 脈波遅延 → 各 t0）。
    """
    import pandas as pd
    loader = m32._vitaldb_loader if loader is None else loader
    out_dir = LFEAT if out_dir is None else Path(out_dir)
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
    rows = [window_landmarks_47(pleth, ecg, float(t0), lag)
            for t0 in np.arange(0, dur - WIN_S, WIN_S)]
    df = pd.DataFrame(rows)
    df.insert(0, "caseid", caseid)
    out_dir.mkdir(parents=True, exist_ok=True)
    df.to_csv(fp, index=False)
    (out_dir / f"case_{caseid}_meta.json").write_text(json.dumps(
        {"caseid": int(caseid), "vitaldb": m32.vitaldb_version(),
         "duration_min": round(dur / 60, 1), "n_windows": int(len(df)),
         "n_analyzable": int((df["n_good"] >= MIN_GOOD).sum())}, ensure_ascii=False),
        encoding="utf-8")
    return caseid, df, None


def _extract_one_47(caseid: int):
    try:
        return extract_case_47(caseid)
    except Exception as e:      # noqa: BLE001
        return caseid, None, f"失敗: {e}"


def eligible_cases(limit: int = 0) -> list:
    """論文1 の採用症例（862 例）と同じ集合。返り値 [(caseid, 身長[m]), ...]。

    `src.cases.case_order(900)` の並び（主解析と同じ）から、`data/features/case_*.csv`
    があり行数が 03番の採用条件（12 ウィンドウ）以上の症例だけを取る。
    """
    import pandas as pd
    from src.cases import case_order, min_windows
    need = int(min_windows())
    out = []
    for cid, _dev, h_m in case_order(900):
        fp = FEAT / f"case_{cid}.csv"
        if not fp.exists():
            continue
        try:
            n = len(pd.read_csv(fp))
        except Exception:      # noqa: BLE001
            continue
        if n < need:
            continue
        out.append((int(cid), float(h_m)))
        if limit and len(out) >= limit:
            break
    return out


def run_extract(jobs: int = 1, limit: int = 0) -> int:
    """段階 E。論文1 の採用症例に特徴点法を当て、`data/features_lm/` に置く。"""
    ids = [c for c, _h in eligible_cases(limit)]
    print(f"段階 E: {len(ids)} 症例（論文1 の採用症例）を処理します"
          f"・vitaldb {m32.vitaldb_version()}・pda2 {pda2.code_version()}", flush=True)
    print("同定率と自己相関は論文3 の主要評価項目なので、この台本は印字しない", flush=True)
    LFEAT.mkdir(parents=True, exist_ok=True)
    t_start = time.time()
    done, n_ok, errs = 0, 0, {}

    def _note(cid, df, err):
        nonlocal done, n_ok
        done += 1
        if err:
            errs[cid] = err
        else:
            n_ok += 1
        if done % 50 == 0 or done == len(ids):
            el = time.time() - t_start
            eta = el / max(done, 1) * (len(ids) - done)
            print(f"  [{done}/{len(ids)}] 成功 {n_ok}・失敗 {len(errs)}"
                  f"　経過 {el/60:.1f} 分 / 残り {eta/60:.1f} 分", flush=True)

    if jobs > 1:
        from concurrent.futures import ProcessPoolExecutor, as_completed
        with ProcessPoolExecutor(max_workers=jobs) as ex:
            futs = {ex.submit(_extract_one_47, c): c for c in ids}
            for fu in as_completed(futs):
                _note(*fu.result())
    else:
        for c in ids:
            _note(*_extract_one_47(c))
    print(f"\n段階 E 完了: 成功 {n_ok} / 失敗 {len(errs)}"
          f"　所要 {(time.time()-t_start)/60:.1f} 分・出力 {LFEAT}", flush=True)
    for cid, err in list(errs.items())[:20]:
        print(f"  case {cid}: {err}", flush=True)
    return 0


# ================================================================ 段階 S: 結合
def _window_set(w: dict, height_m: float) -> dict:
    """1 症例・1 つのウィンドウ集合の指標と相対変化。

    相対変化はすべて `src.models._rel`（その集合の初回ウィンドウからの相対変化）。
    ΔT% は PDA では si0/si − 1 と同じになる（身長は症例内で約分される）。
    """
    dt_pda = height_m / w["si"] * 1000.0
    dt_lm = w["ens_dt_lm_ms"]
    with np.errstate(divide="ignore", invalid="ignore"):
        si_lm = height_m / (dt_lm / 1000.0)
    pwtt_ms = w["pwtt"] * 1000.0
    per_ms = pwtt_ms - w["t1_ms"]                  # T2 − T1（21番と同じ）
    dtn_pda = dt_pda / 1000.0 * w["hr"] / 60.0     # ΔT[s] ÷ RR[s]。心周期に対する割合に直した ΔT
    s = {"n": int(dt_pda.size), "t0": w["t0"], "klass": w["ens_klass"],
         "dt_pda": dt_pda, "ri_pda": w["ri"], "si_pda": w["si"],
         "dt_lm": dt_lm, "ri_lm": w["ens_ri_lm"], "si_lm": si_lm,
         "beat_dt": w["beat_dt_med"], "map": w["map"], "hr": w["hr"],
         "pwtt": w["pwtt"], "pwtt_ms": pwtt_ms, "t1_ms": w["t1_ms"], "per_ms": per_ms,
         "sbp": w["sbp"], "dbp": w["dbp"]}
    for key, arr in (("d_dt_pda", dt_pda), ("d_ri_pda", w["ri"]), ("d_si_pda", w["si"]),
                     ("d_dt_lm", dt_lm), ("d_ri_lm", w["ens_ri_lm"]), ("d_si_lm", si_lm),
                     ("d_beat_dt", w["beat_dt_med"]), ("d_dtn_pda", dtn_pda),
                     ("d_map", w["map"]), ("d_hr", w["hr"]), ("d_pwtt", w["pwtt"]),
                     ("d_t1", w["t1_ms"]), ("d_per", per_ms),
                     ("d_sbp", w["sbp"]), ("d_dbp", w["dbp"])):
        s[key] = _rel_of(arr)
    return s


def build_case(caseid: int, height_m: float, d, age: float = float("nan"),
               htn: float = float("nan")):
    """結合済みの表から 2 つのウィンドウ集合を作る。どちらも 12 行未満なら None。

    全ウィンドウ = t1_ms・pwtt・si・ri・map・hr が有限な行。
    共通ウィンドウ = そのうち ens_dt_lm_ms と ens_ri_lm が有限（型1 か型3）な行。
    """
    import pandas as pd
    cols = COLS_MAIN + COLS_ART[1:] + COLS_LM[1:]
    v = {}
    for k in cols:
        v[k] = (pd.to_numeric(d[k], errors="coerce").to_numpy(float)
                if k in d.columns else np.full(len(d), np.nan))
    g = np.ones(len(d), bool)
    for k in NEED_FINITE:
        g &= np.isfinite(v[k])
    ok_lm = np.isfinite(v["ens_dt_lm_ms"]) & np.isfinite(v["ens_ri_lm"])
    idx_all = np.flatnonzero(g)
    idx_com = np.flatnonzero(g & ok_lm)
    sets = {}
    for key, idx in (("all", idx_all), ("common", idx_com)):
        if idx.size >= MIN_WIN:
            sets[key] = _window_set({k: v[k][idx] for k in cols}, height_m)
    if not sets:
        return None
    return {"caseid": int(caseid), "height": float(height_m), "age": float(age),
            "htn": float(htn), "sets": sets, "n_merged": int(len(d)),
            "n_all": int(idx_all.size), "n_common": int(idx_com.size)}


def _demographics() -> dict:
    """cases.csv から年齢と高血圧既往を読む（BOM 付きなので utf-8-sig）。"""
    import pandas as pd
    out = {}
    fp = DATA / "cases.csv"
    if not fp.exists():
        return out
    demo = pd.read_csv(fp, encoding="utf-8-sig")
    for _i, r in demo.iterrows():
        try:
            out[int(r["caseid"])] = (float(r["age"]), float(r["preop_htn"]))
        except Exception:      # noqa: BLE001
            continue
    return out


def load_joined(limit: int = 0) -> tuple:
    """features・features_art・features_lm を症例ごとに t0 で内部結合する。

    t0 は 60 の倍数の float なので等値で結合できる（32番も同じ前提）。
    返り値: (症例のリスト, 欠損の集計)。
    """
    import pandas as pd
    demo = _demographics()
    elig = eligible_cases(limit)
    n_lm_files = sum(1 for cid, _h in elig if (LFEAT / f"case_{cid}.csv").exists())
    cases, n_main, n_join = [], 0, 0
    for cid, h_m in elig:
        try:
            m = pd.read_csv(FEAT / f"case_{cid}.csv")
            a = pd.read_csv(AFEAT / f"case_{cid}.csv")
            lm = pd.read_csv(LFEAT / f"case_{cid}.csv")
        except Exception:      # noqa: BLE001
            continue
        if any(c not in m.columns for c in COLS_MAIN) or "t0" not in a.columns \
                or any(c not in lm.columns for c in ["t0", "ens_dt_lm_ms", "ens_ri_lm"]):
            continue
        n_main += len(m)
        acol = [c for c in COLS_ART if c in a.columns]
        lcol = [c for c in COLS_LM if c in lm.columns]
        d = (m[COLS_MAIN].merge(a[acol], on="t0", how="inner")
             .merge(lm[lcol], on="t0", how="inner").sort_values("t0").reset_index(drop=True))
        n_join += len(d)
        age, htn = demo.get(cid, (float("nan"), float("nan")))
        c = build_case(cid, h_m, d, age=age, htn=htn)
        if c is not None:
            cases.append(c)
    miss = {"n_eligible": len(elig), "n_lm_files": n_lm_files,
            "coverage": n_lm_files / max(len(elig), 1),
            "n_case_used": len(cases), "n_win_main": n_main, "n_win_joined": n_join}
    for key in ("all", "common"):
        miss[f"n_case_{key}"] = sum(1 for c in cases if key in c["sets"])
        miss[f"n_win_{key}"] = sum(c["sets"][key]["n"] for c in cases if key in c["sets"])
    return cases, miss


# ================================================================ 統計の部品
def within(cases: list, setkey: str, xk: str, yk: str, cov=None) -> np.ndarray:
    """症例内の順位相関（cov を与えれば偏順位相関）の一覧。有限値だけ返す。"""
    out = []
    for c in cases:
        s = c["sets"].get(setkey)
        if s is None:
            continue
        r = (_spearman(s[xk], s[yk]) if cov is None
             else _partial_rho(s[xk], s[yk], [s[k] for k in cov]))
        if np.isfinite(r):
            out.append(float(r))
    return np.asarray(out, float)


def stack(cases: list, setkey: str, key: str) -> np.ndarray:
    """全症例のウィンドウを積む（症例ごとに Δ にしてから積む）。"""
    parts = [c["sets"][setkey][key] for c in cases if setkey in c["sets"]]
    return np.concatenate(parts) if parts else np.array([])


def pooled_reg(cases: list, setkey: str, ykey: str, regs: tuple) -> dict:
    """全症例プールの回帰。r² は切片なし（論文1 の事前指定）と切片ありの両方。

    規約は 36番の `pooled` と同一。分母は sum((y − mean(y))²) なので切片なしでは
    負になりうる。
    """
    Xs, ys = [], []
    for c in cases:
        s = c["sets"].get(setkey)
        if s is None:
            continue
        Xs.append(np.column_stack([s[r] for r in regs]))
        ys.append(s[ykey])
    if not ys:
        return {"n_win": 0, "r2_no_int": float("nan"), "r2_with_int": float("nan"),
                "betas": {r: float("nan") for r in regs}}
    X, y = np.vstack(Xs), np.concatenate(ys)
    g = np.isfinite(y) & np.isfinite(X).all(axis=1)
    X, y = X[g], y[g]
    if y.size < 30:
        return {"n_win": int(y.size), "r2_no_int": float("nan"),
                "r2_with_int": float("nan"), "betas": {r: float("nan") for r in regs}}
    sst = float(np.sum((y - y.mean()) ** 2))

    def r2_of(M):
        coef, *_ = np.linalg.lstsq(M, y, rcond=None)
        sse = float(np.sum((y - M @ coef) ** 2))
        return 1.0 - sse / max(sst, 1e-12), coef

    r2_ni, coef_ni = r2_of(X)
    r2_wi, coef_wi = r2_of(np.column_stack([np.ones(len(y)), X]))
    return {"n_win": int(y.size), "r2_no_int": r2_ni, "r2_with_int": r2_wi,
            "betas": {r: float(b) for r, b in zip(regs, coef_ni)},
            "betas_with_int": {r: float(b) for r, b in zip(regs, coef_wi[1:])}}


def by_case_reg(cases: list, setkey: str, ykey: str, reg: str) -> dict:
    """症例内の診断: 係数の符号の揃い・症例内 r²・順位相関の中央値（36番の `by_case`）。"""
    betas, r2s, rhos = [], [], []
    for c in cases:
        s = c["sets"].get(setkey)
        if s is None:
            continue
        y, x = np.asarray(s[ykey], float), np.asarray(s[reg], float)
        g = np.isfinite(y) & np.isfinite(x)
        y, x = y[g], x[g]
        if len(y) < MIN_N_RHO or np.std(x) < 1e-12:
            continue
        M = np.column_stack([np.ones(len(y)), x])
        coef, *_ = np.linalg.lstsq(M, y, rcond=None)
        sst = float(np.sum((y - y.mean()) ** 2))
        r2s.append(1.0 - float(np.sum((y - M @ coef) ** 2)) / max(sst, 1e-12))
        betas.append(float(coef[1]))
        r = _spearman(x, y)
        if np.isfinite(r):
            rhos.append(float(r))
    b = np.asarray(betas, float)
    return {"n_case": len(betas),
            "sign": float(max((b > 0).mean(), (b < 0).mean())) if b.size else float("nan"),
            "dir": ("負" if b.size and (b < 0).mean() >= (b > 0).mean() else "正"),
            "r2_med": float(np.median(r2s)) if r2s else float("nan"),
            "rho_med": float(np.median(rhos)) if rhos else float("nan")}


def within_reg2(cases: list, setkey: str, ykey: str, x1: str, x2: str) -> dict:
    """症例内の重回帰 y ~ 1 + x1 + x2。係数の中央値 [IQR] と符号の揃い。"""
    b1, b2, r2s = [], [], []
    for c in cases:
        s = c["sets"].get(setkey)
        if s is None:
            continue
        y = np.asarray(s[ykey], float)
        a1, a2 = np.asarray(s[x1], float), np.asarray(s[x2], float)
        g = np.isfinite(y) & np.isfinite(a1) & np.isfinite(a2)
        if g.sum() < MIN_N_RHO or np.std(a1[g]) < 1e-12 or np.std(a2[g]) < 1e-12:
            continue
        M = np.column_stack([np.ones(int(g.sum())), a1[g], a2[g]])
        coef, *_ = np.linalg.lstsq(M, y[g], rcond=None)
        sst = float(np.sum((y[g] - y[g].mean()) ** 2))
        r2s.append(1.0 - float(np.sum((y[g] - M @ coef) ** 2)) / max(sst, 1e-12))
        b1.append(float(coef[1]))
        b2.append(float(coef[2]))
    out = {"n_case": len(b1), "r2_med": float(np.median(r2s)) if r2s else float("nan")}
    for nm, v in (("b1", b1), ("b2", b2)):
        m, lo, hi, _n = _med_iqr(v)
        a = np.asarray(v, float)
        out[nm] = (m, lo, hi,
                   float(max((a > 0).mean(), (a < 0).mean())) if a.size else float("nan"))
    return out


def case_table(cases: list, setkey: str, keys: list) -> dict:
    """症例中央値の表。返り値は caseid・age・htn と各指標の症例中央値（同じ並び）。"""
    out = {k: [] for k in ["caseid", "age", "htn"] + list(keys)}
    for c in cases:
        s = c["sets"].get(setkey)
        if s is None:
            continue
        out["caseid"].append(float(c["caseid"]))
        out["age"].append(float(c["age"]))
        out["htn"].append(float(c["htn"]))
        for k in keys:
            v = np.asarray(s[k], float)
            v = v[np.isfinite(v)]
            out[k].append(float(np.median(v)) if v.size else float("nan"))
    return {k: np.asarray(v, float) for k, v in out.items()}


# ================================================================ 節1
ROWS1 = [
    ("ρ(ΔT%, ΔMAP%)", "d_dt_pda", "d_map", None),
    ("ρ(ΔT%, ΔHR%)", "d_dt_pda", "d_hr", None),
    ("ρ(ΔMAP%, ΔHR%)", "d_map", "d_hr", None),
    ("ρ(ΔT%, ΔDBP%)", "d_dt_pda", "d_dbp", None),
    ("ρ(ΔT%, ΔSBP%)", "d_dt_pda", "d_sbp", None),
    ("偏ρ(ΔT%, ΔMAP% | ΔHR%)", "d_dt_pda", "d_map", ("d_hr",)),
    ("ρ(ΔTn%, ΔMAP%)", "d_dtn_pda", "d_map", None),
]


def section1(cases: list) -> dict:
    """節1: 凍結版 PDA の ΔT と血圧・心拍数（全ウィンドウ・症例内）。"""
    print("\n" + "-" * 96)
    print("節1. 凍結版 PDA の ΔT と血圧・心拍数（全ウィンドウ・症例内。Δ は初回ウィンドウからの相対変化）")
    print("-" * 96)
    n_case = sum(1 for c in cases if "all" in c["sets"])
    n_win = sum(c["sets"]["all"]["n"] for c in cases if "all" in c["sets"])
    print(f"  対象 {n_case} 症例・{n_win:,} ウィンドウ（症例あたり {MIN_WIN} ウィンドウ以上）")
    print(f"\n  {_pad('組み合わせ', 26)}{_pad('中央値', 9, True)}{_pad('[IQR]', 20, True)}"
          f"{_pad('正の症例', 10, True)}{_pad('符号検定 p', 12, True)}{_pad('n', 6, True)}")
    got = {}
    for lab, xk, yk, cov in ROWS1:
        v = within(cases, "all", xk, yk, cov=cov)
        m, lo, hi, n = _med_iqr(v)
        got[lab] = m
        print(f"  {_pad(lab, 26)}{_f(m, 9)}"
              f"{_pad('[' + _f(lo, 6).strip() + ', ' + _f(hi, 6).strip() + ']', 20, True)}"
              f"{_pad(f'{_pos_frac(v):.0%}' if n else '—', 10, True)}"
              f"{_pad(f'{_sign_p(v):.3g}' if n else '—', 12, True)}{_pad(n, 6, True)}")
    print("  ※ 符号検定は正の症例数の両側二項検定（scipy.stats.binomtest）。")

    w = within_reg2(cases, "all", "d_dt_pda", "d_map", "d_hr")
    print(f"\n  症例内回帰 ΔT% ~ 1 + ΔMAP% + ΔHR%（{w['n_case']} 症例）")
    for nm, lab in (("b1", "β_MAP"), ("b2", "β_HR")):
        m, lo, hi, sg = w[nm]
        print(f"    {_pad(lab, 10)}中央値 {_f(m, 8)}   [IQR {_f(lo, 7).strip()}, "
              f"{_f(hi, 7).strip()}]   符号の揃い {sg:.0%}")
    print(f"    症例内 r²（切片あり）の中央値 {w['r2_med']:.4f}")

    pr = pooled_reg(cases, "all", "d_dt_pda", ("d_map", "d_hr"))
    bs = "  ".join(f"β_{k.split('_')[1].upper()}={v:+.4f}"
                   for k, v in pr["betas_with_int"].items())
    print(f"\n  プール回帰 ΔT% ~ 1 + ΔMAP% + ΔHR%（症例ごとに Δ にしてから積む。"
          f"{pr['n_win']:,} ウィンドウ）")
    print(f"    r²（切片あり）{pr['r2_with_int']:.4f}   {bs}")
    pm = _spearman(stack(cases, "all", "d_dt_pda"), stack(cases, "all", "d_map"))
    ph = _spearman(stack(cases, "all", "d_dt_pda"), stack(cases, "all", "d_hr"))
    pp = _partial_rho(stack(cases, "all", "d_dt_pda"), stack(cases, "all", "d_map"),
                      [stack(cases, "all", "d_hr")])
    print(f"    プール Spearman  ρ(ΔT%, ΔMAP%) {_f(pm)}   ρ(ΔT%, ΔHR%) {_f(ph)}"
          f"   偏ρ(ΔT%, ΔMAP% | ΔHR%) {_f(pp)}")

    ct = case_table(cases, "all", ["dt_pda", "map", "hr"])
    ad = ct["age"] >= ADULT_AGE
    r_bw = _spearman(ct["dt_pda"][ad], ct["map"][ad], min_n=10)
    r_pt = _partial_rho(ct["dt_pda"][ad], ct["map"][ad],
                        [ct["age"][ad], ct["hr"][ad]], min_n=10)
    print(f"\n  症例間（成人 {ADULT_AGE:.0f} 歳以上・{int(np.sum(ad & np.isfinite(ct['dt_pda'])))} 例。"
          f"症例中央値どうし）")
    print(f"    ρ(ΔT_PDA, MAP) {_f(r_bw)}   年齢と HR の症例中央値を与えた偏順位相関 {_f(r_pt)}")
    got.update({"pool_rho_map": pm, "pool_rho_hr": ph, "between_rho_map": r_bw,
                "n_case": n_case, "n_win": n_win})
    return got


# ================================================================ 節2
IDX2 = [("ΔT_PDA（分解由来）", "common", "dt_pda", "d_dt_pda"),
        ("ΔT_LM（特徴点由来）", "common", "dt_lm", "d_dt_lm"),
        ("RI_PDA（分解由来）", "common", "ri_pda", "d_ri_pda"),
        ("RI_LM（特徴点由来）", "common", "ri_lm", "d_ri_lm"),
        ("参考 ΔT_PDA（全ウィンドウ）", "all", "dt_pda", "d_dt_pda"),
        ("参考 RI_PDA（全ウィンドウ）", "all", "ri_pda", "d_ri_pda")]

PARTNERS2 = [("ρ(ΔMAP%)", "d_map", None), ("ρ(ΔHR%)", "d_hr", None),
             ("偏ρ(ΔMAP%|ΔHR%)", "d_map", ("d_hr",)), ("ρ(ΔPWTT%)", "d_pwtt", None),
             ("ρ(ΔT1%)", "d_t1", None), ("ρ(Δ(T2−T1)%)", "d_per", None)]


def table_a(cases: list) -> dict:
    """表 A: 同じ指標を 2 法で出し、同じ相手との症例内順位相関の中央値を並べる。"""
    print("\n" + "-" * 96)
    print("表 A. 症例内の順位相関の中央値（共通ウィンドウ。参考の 2 行だけ全ウィンドウ）")
    print("-" * 96)
    head = (_pad("指標", 28) + _pad("n症例", 7, True) + _pad("nウィンドウ", 12, True)
            + "".join(_pad(lab, 17, True) for lab, _k, _c in PARTNERS2))
    print("  " + head)
    got = {}
    for lab, setkey, _raw, dk in IDX2:
        n_case = sum(1 for c in cases if setkey in c["sets"])
        n_win = sum(c["sets"][setkey]["n"] for c in cases if setkey in c["sets"])
        line = _pad(lab, 28) + _pad(n_case, 7, True) + _pad(f"{n_win:,}", 12, True)
        for plab, pk, cov in PARTNERS2:
            m = _med_iqr(within(cases, setkey, dk, pk, cov=cov))[0]
            got[(lab, plab)] = m
            line += _pad(_f(m, 8).strip(), 17, True)
        print("  " + line)
    print("  ※ 症例ごとに Spearman ρ を出し、その中央値を並べた。偏ρ は順位に直してからの偏相関。")
    return got


def table_b(cases: list) -> dict:
    """表 B: 症例間（成人）。症例中央値と年齢の順位相関、高血圧既往あり／なしの水準。"""
    print("\n" + "-" * 96)
    print(f"表 B. 症例間（成人 {ADULT_AGE:.0f} 歳以上）。症例中央値と年齢の Spearman ρ [95%CI は Fisher z]")
    print("-" * 96)
    print("  " + _pad("指標", 28) + _pad("n症例", 7, True) + _pad("ρ(年齢)", 10, True)
          + _pad("[95%CI]", 22, True) + _pad("高血圧既往 あり / なし（症例中央値の中央値）", 46, True))
    got = {}
    for lab, setkey, raw, _dk in IDX2:
        ct = case_table(cases, setkey, [raw])
        ad = (ct["age"] >= ADULT_AGE) & np.isfinite(ct[raw])
        r = _spearman(ct["age"][ad], ct[raw][ad], min_n=10)
        lo, hi = _fisher_ci(r, int(ad.sum()))
        h1 = ct[raw][ad & (ct["htn"] == 1)]
        h0 = ct[raw][ad & (ct["htn"] == 0)]
        fmt = "{:.1f} ms" if raw.startswith("dt") else "{:.3f}"
        hs = (f"{fmt.format(np.median(h1))} ({h1.size}) / "
              f"{fmt.format(np.median(h0))} ({h0.size})" if h1.size and h0.size else "—")
        got[lab] = r
        print("  " + _pad(lab, 28) + _pad(int(ad.sum()), 7, True) + _pad(_f(r, 8).strip(), 10, True)
              + _pad("[" + _f(lo, 6).strip() + ", " + _f(hi, 6).strip() + "]", 22, True)
              + _pad(hs, 46, True))
    print(f"  照合: 論文1 の確定値 ρ(ΔT_PDA 症例中央値, 年齢) = {PAPER1_RHO_AGE_DT:+.3f}"
          f"（06番・成人 {PAPER1_N_ADULT} 例）。")
    print("  この台本の「参考 ΔT_PDA（全ウィンドウ）」の行と突き合わせる。値がずれるのは、"
          "(a) features_art が")
    print("  ある症例に限っていること、(b) 症例中央値をウィンドウごとの ΔT の中央値で取ること"
          "（06番は 身長/中央値(SI)）による。")
    return got


PREMISE_ROWS = [("ΔSI% ＋ ΔRI%", ("si", "ri")), ("ΔSI% のみ", ("si",)), ("ΔRI% のみ", ("ri",))]


def table_c(cases: list) -> dict:
    """表 C: 前提検証（ΔPWTT% を血管指標で説明する）を 2 法で並べる。規約は 36番と同じ。"""
    print("\n" + "-" * 96)
    print("表 C. 前提検証 ΔPWTT% ~ 血管指標（共通ウィンドウ・同じ症例。規約は 36番・論文1 §7.1 と同じ）")
    print("-" * 96)
    print("  " + _pad("方法", 14) + _pad("説明変数", 20) + _pad("nウィンドウ", 12, True)
          + _pad("r² 切片なし", 13, True) + _pad("r² 切片あり", 13, True) + "   係数（切片なし）")
    got = {}
    for mlab, suf in (("凍結版 PDA", "pda"), ("特徴点法", "lm")):
        for rlab, keys in PREMISE_ROWS:
            regs = tuple(f"d_{k}_{suf}" for k in keys)
            r = pooled_reg(cases, "common", "d_pwtt", regs)
            got[(mlab, rlab)] = r
            bs = "  ".join(f"β_{k.split('_')[1].upper()}={v:+.4f}"
                           for k, v in r["betas"].items())
            print("  " + _pad(mlab, 14) + _pad(rlab, 20) + _pad(f"{r['n_win']:,}", 12, True)
                  + _pad(f"{r['r2_no_int']:.4f}", 13, True)
                  + _pad(f"{r['r2_with_int']:.4f}", 13, True) + "   " + bs)
    print("  切片なしが論文1 の事前指定の規約。分母は sum((y−mean(y))²) なので負になりうる。")
    print("\n  " + _pad("説明変数", 20) + _pad("症例", 6, True) + _pad("符号の揃い", 12, True)
          + _pad("向き", 6, True) + _pad("症例内 r² 中央値", 18, True)
          + _pad("症例内 ρ 中央値", 18, True))
    for lab, reg in (("ΔSI%（PDA）", "d_si_pda"), ("ΔRI%（PDA）", "d_ri_pda"),
                     ("ΔSI%（特徴点法）", "d_si_lm"), ("ΔRI%（特徴点法）", "d_ri_lm")):
        d = by_case_reg(cases, "common", "d_pwtt", reg)
        got[lab] = d
        print("  " + _pad(lab, 20) + _pad(d["n_case"], 6, True)
              + _pad(f"{d['sign']*100:.0f}%", 12, True) + _pad(d["dir"], 6, True)
              + _pad(f"{d['r2_med']:.4f}", 18, True) + _pad(_f(d["rho_med"], 8).strip(), 18, True))
    return got


def table_d(cases: list) -> dict:
    """表 D: 2 法の一致。症例内・プール・症例間で、同じ指標どうしを突き合わせる。"""
    print("\n" + "-" * 96)
    print("表 D. 2 法の一致（共通ウィンドウ）")
    print("-" * 96)
    got = {}
    for lab, dk_a, dk_b, raw_a, raw_b, unit in (
            ("ΔT", "d_dt_pda", "d_dt_lm", "dt_pda", "dt_lm", "ms"),
            ("RI", "d_ri_pda", "d_ri_lm", "ri_pda", "ri_lm", "")):
        v = within(cases, "common", dk_a, dk_b)
        m, lo, hi, n = _med_iqr(v)
        got[lab] = m
        print(f"\n  {lab}")
        print(f"    症例内 ρ({lab}_PDA%, {lab}_LM%)   中央値 {_f(m, 8)}"
              f"   [IQR {_f(lo, 7).strip()}, {_f(hi, 7).strip()}]"
              f"   正の症例 {_pos_frac(v):.0%}   n={n}")
        pr = _spearman(stack(cases, "common", dk_a), stack(cases, "common", dk_b))
        print(f"    プール Spearman（症例ごとに Δ にしてから積む）   {_f(pr)}"
              f"   {stack(cases, 'common', dk_a).size:,} ウィンドウ")
        diff = stack(cases, "common", raw_b) - stack(cases, "common", raw_a)
        dm, dlo, dhi, dn = _med_iqr(diff)
        u = f" {unit}" if unit else ""
        print(f"    差 {lab}_LM − {lab}_PDA   プール中央値 {dm:+.3f}{u}"
              f"   [IQR {dlo:+.3f}, {dhi:+.3f}]   n={dn:,}")
        per = []
        for c in cases:
            s = c["sets"].get("common")
            if s is None:
                continue
            d2 = np.asarray(s[raw_b], float) - np.asarray(s[raw_a], float)
            d2 = d2[np.isfinite(d2)]
            if d2.size:
                per.append(float(np.median(d2)))
        pm2, plo, phi, pn = _med_iqr(per)
        print(f"    　　　　　　　　　　　症例中央値の中央値 {pm2:+.3f}{u}"
              f"   [IQR {plo:+.3f}, {phi:+.3f}]   n={pn}")
        ct = case_table(cases, "common", [raw_a, raw_b])
        rb = _spearman(ct[raw_a], ct[raw_b], min_n=10)
        print(f"    症例間 ρ（症例中央値どうし・{int(np.isfinite(ct[raw_a]).sum())} 例）   {_f(rb)}")
        got[f"{lab}_between"] = rb

    v1 = []
    for c in cases:
        s = c["sets"].get("common")
        if s is None:
            continue
        m1 = np.isfinite(s["klass"]) & (np.asarray(s["klass"], float) == 1)
        if m1.sum() < K1_MIN_ROWS:
            continue
        r = _spearman(_rel_of(np.asarray(s["dt_pda"], float)[m1]),
                      _rel_of(np.asarray(s["dt_lm"], float)[m1]), min_n=K1_MIN_ROWS)
        if np.isfinite(r):
            v1.append(float(r))
    print("")
    if len(v1) >= K1_MIN_CASES:
        m, lo, hi, n = _med_iqr(v1)
        print("  型1（明瞭な切痕と拡張期ピーク）のウィンドウだけに限った 症例内 ρ(ΔT_PDA%, ΔT_LM%)")
        print(f"    中央値 {_f(m, 8)}   [IQR {_f(lo, 7).strip()}, {_f(hi, 7).strip()}]"
              f"   正の症例 {_pos_frac(v1):.0%}   n={n}"
              f"（症例内 {K1_MIN_ROWS} 行以上の症例のみ。Δ はその部分集合の初回から取り直した）")
        got["k1"] = m
    else:
        print(f"  型1 限定の行は印字しない（症例内 {K1_MIN_ROWS} 行以上の症例が {len(v1)} 例で、"
              f"必要な {K1_MIN_CASES} 例に満たない）")
        got["k1"] = float("nan")

    vb = within(cases, "common", "d_dt_pda", "d_beat_dt")
    mb, lob, hib, nb = _med_iqr(vb)
    print(f"  拍ごとの中央値を使った 症例内 ρ(ΔT_PDA%, ΔT_beat%)   中央値 {_f(mb, 8)}"
          f"   [IQR {_f(lob, 7).strip()}, {_f(hib, 7).strip()}]   n={nb}")
    got["beat"] = mb
    return got


def section2(cases: list) -> dict:
    """節2: 同じ指標を 2 法で出して比べる（共通ウィンドウ）。"""
    print("\n" + "-" * 96)
    print("節2. 同じ指標（ΔT・RI）を 2 法で、同じウィンドウから出して比べる")
    print("-" * 96)
    n_case = sum(1 for c in cases if "common" in c["sets"])
    n_win = sum(c["sets"]["common"]["n"] for c in cases if "common" in c["sets"])
    n_all = sum(c["sets"]["all"]["n"] for c in cases if "all" in c["sets"])
    print(f"  共通ウィンドウ {n_case} 症例・{n_win:,} ウィンドウ"
          f"（全ウィンドウ {n_all:,} の {n_win/max(n_all,1):.0%}）")
    print("  共通ウィンドウ = 全ウィンドウのうち、平均拍の型が 1 か 3 で ΔT_LM と RI_LM が"
          "どちらも求まった行。")
    a = table_a(cases)
    b = table_b(cases)
    c = table_c(cases)
    d = table_d(cases)
    return {"a": a, "b": b, "c": c, "d": d, "n_case": n_case, "n_win": n_win}


# ================================================================ 予測との照合
def predictions(s1: dict, s2: dict) -> dict:
    """docstring と同文の予測に照らして「はい／いいえ」と実測値を印字する。"""
    print("\n" + "-" * 96)
    print("予測との照合（予測は 2026-09-14 に、計算の前に固定した。docstring と同文）")
    print("-" * 96)
    out = {}

    r_map = s1.get("ρ(ΔT%, ΔMAP%)", float("nan"))
    r_par = s1.get("偏ρ(ΔT%, ΔMAP% | ΔHR%)", float("nan"))
    half = bool(np.isfinite(r_map) and np.isfinite(r_par)
                and abs(r_par) <= PRED_P1_RATIO * abs(r_map))
    p1 = bool(np.isfinite(r_map) and r_map >= PRED_P1_RHO_MIN and half)
    out["P1"] = p1
    ratio = (abs(r_par) / abs(r_map)
             if np.isfinite(r_map) and np.isfinite(r_par) and abs(r_map) > 0 else float("nan"))
    print(f"  P1 ρ(ΔT_PDA%, ΔMAP%) の症例中央値が正で {PRED_P1_RHO_MIN:+.2f} 以上、"
          f"かつ ΔHR% を与えた偏順位相関がその半分以下   {'はい' if p1 else 'いいえ'}")
    print(f"     調整前 {_f(r_map)}   ΔHR% を与えた偏順位相関 {_f(r_par)}"
          f"   比 {_f(ratio, 5, 2, sign=False).strip()}（要 ≤ {PRED_P1_RATIO:.2f}）")

    r_hr = s1.get("ρ(ΔT%, ΔHR%)", float("nan"))
    p2 = bool(np.isfinite(r_hr) and r_hr <= PRED_P2_RHO_MAX)
    out["P2"] = p2
    print(f"  P2 ρ(ΔT_PDA%, ΔHR%) の症例中央値が負で {PRED_P2_RHO_MAX:+.2f} 以下"
          f"   {'はい' if p2 else 'いいえ'}")
    print(f"     実測 {_f(r_hr)}")

    a = s2.get("a", {})
    r_lm_t1 = a.get(("ΔT_LM（特徴点由来）", "ρ(ΔT1%)"), float("nan"))
    r_pda_t1 = a.get(("ΔT_PDA（分解由来）", "ρ(ΔT1%)"), float("nan"))
    gap = r_lm_t1 - r_pda_t1
    p3 = bool(np.isfinite(gap) and gap >= PRED_P3_GAP)
    out["P3"] = p3
    print(f"  P3 ρ(ΔT_LM%, ΔT1%) の症例中央値が ρ(ΔT_PDA%, ΔT1%) より {PRED_P3_GAP:+.2f} 以上大きい"
          f"   {'はい' if p3 else 'いいえ'}")
    print(f"     特徴点法 {_f(r_lm_t1)}   分解由来 {_f(r_pda_t1)}   差 {_f(gap)}")

    r_ag = s2.get("d", {}).get("ΔT", float("nan"))
    p4 = bool(np.isfinite(r_ag) and PRED_P4_RANGE[0] <= r_ag < PRED_P4_RANGE[1])
    out["P4"] = p4
    print(f"  P4 ρ(ΔT_PDA%, ΔT_LM%) の症例中央値が {PRED_P4_RANGE[0]:+.2f} 以上"
          f" {PRED_P4_RANGE[1]:+.2f} 未満   {'はい' if p4 else 'いいえ'}")
    print(f"     実測 {_f(r_ag)}")

    r5 = s2.get("c", {}).get(("特徴点法", "ΔSI% ＋ ΔRI%"), {}).get("r2_with_int", float("nan"))
    p5 = bool(np.isfinite(r5) and r5 < PRED_P5_R2_MAX)
    out["P5"] = p5
    print(f"  P5 特徴点法の ΔSI%・ΔRI% で ΔPWTT% を回帰した切片ありの r² が"
          f" {PRED_P5_R2_MAX:.2f} 未満   {'はい' if p5 else 'いいえ'}")
    r5p = s2.get("c", {}).get(("凍結版 PDA", "ΔSI% ＋ ΔRI%"), {}).get("r2_with_int", float("nan"))
    print(f"     特徴点法 {r5:.4f}（同じウィンドウの凍結版 PDA は {r5p:.4f}。"
          f"論文1 の確定値は 0.044・全ウィンドウ）")
    print("  ※ 当たっても外れても成立・不成立の判定は付けない（事後・記述）。")
    return out


# ================================================================ 報告
def report(cases: list, miss: dict) -> dict:
    """段階 S の全文。"""
    print("=" * 96)
    print("論文1【探索・凍結後】凍結版 PDA の ΔT と血圧、特徴点法との比較")
    print("=" * 96)
    print(f"  段階 E の被覆: 論文1 の採用症例 {miss['n_eligible']} に対し features_lm "
          f"{miss['n_lm_files']} 症例（{miss['coverage']*100:.1f}%）")
    print(f"  結合できた症例 {miss['n_case_used']}（全ウィンドウの集合 {miss['n_case_all']}・"
          f"共通ウィンドウの集合 {miss['n_case_common']}）")
    print(f"  ウィンドウ: 論文1 {miss['n_win_main']:,} → 結合後 {miss['n_win_joined']:,}"
          f" → 全ウィンドウ {miss['n_win_all']:,}・共通ウィンドウ {miss['n_win_common']:,}")
    print(f"  pda2 {pda2.code_version()}")
    print("  **論文1 の主要評価（percentage error）も無益性の判定も再計算していない。**"
          "すべて探索的（凍結後）である。")
    print("  同定率と隣接ウィンドウの自己相関は論文3 の主要評価項目なので、この台本は印字しない。")
    s1 = section1(cases)
    s2 = section2(cases)
    pr = predictions(s1, s2)
    print("\n" + "-" * 96)
    print("書かないこと")
    print("-" * 96)
    print("  「ΔT は大動脈の硬さを測る」（Epstein 2014）／「特徴点法なら esCCO が改善する」"
          "（精度を見ていない）")
    print("  「2 法が一致しないから PDA は壊れている」（分解由来と特徴点由来は別の量である。"
          "Goswami 2010）")
    print("  ΔT_PDA・ΔT_LM の絶対値を他研究と直接比べること（装置と前処理が違う）")
    print(f"\n  共通ウィンドウ: {s2['n_case']} 症例・{s2['n_win']:,} ウィンドウ")
    print(f"出典: analysis/scripts/47_dt_bp_landmark_compare.py / "
          f"{s1['n_case']} 症例・{s1['n_win']:,} ウィンドウ")
    return {"s1": s1, "s2": s2, "pred": pr}


# ================================================================ 自己検証
def _raiser(_caseid):
    raise RuntimeError("取得できない")


def _synth_joined(n_cases: int = 40, n_win: int = 40, seed: int = 0, hr_effect: float = 0.0,
                  lm_t1: float = 0.0, premise: float = 0.0, lm_nan=None,
                  height: float = 1.65) -> list:
    """合成の結合表を作り、本番と同じ `build_case` を通して症例を組み立てる。

    hr_effect  心拍数が ΔT_PDA（負）と MAP（負）を両方動かす強さ
    lm_t1      特徴点 ΔT だけが T1 を追う強さ（凍結版 ΔT は追わない）
    premise    ΔPWTT% = premise × ΔSI% + 雑音（表 C の仕込み）
    lm_nan     {症例の番号: 先頭から NaN にするウィンドウ数}
    """
    import pandas as pd
    rng = np.random.default_rng(seed)
    lm_nan = lm_nan or {}
    cases = []
    for k in range(n_cases):
        t0 = np.arange(n_win, dtype=float) * WIN_S
        u = rng.normal(0, 0.10, n_win)                 # 心拍数の変動
        v = rng.normal(0, 0.10, n_win)                 # T1 の変動（u と独立）
        hr = 70.0 * (1.0 + u)
        mapv = 80.0 * (1.0 - 0.5 * hr_effect * u) + rng.normal(0, 0.5, n_win)
        dt_pda = 250.0 * (1.0 - 0.8 * hr_effect * u) + rng.normal(0, 10.0, n_win)
        si = height / (dt_pda / 1000.0)
        ri = 0.50 + 0.02 * rng.normal(0, 1, n_win)
        t1 = 180.0 * (1.0 + 0.5 * v) + rng.normal(0, 0.5, n_win)
        dt_lm = 200.0 * (1.0 + lm_t1 * v) + rng.normal(0, 2.0, n_win)
        ri_lm = 0.45 + 0.02 * rng.normal(0, 1, n_win)
        d_si = si / si[0] - 1.0
        pwtt = 0.200 * (1.0 + premise * d_si + 0.01 * rng.normal(0, 1, n_win))
        nn = int(lm_nan.get(k, 0))
        if nn:
            dt_lm = dt_lm.copy()
            dt_lm[:nn] = np.nan
        d = pd.DataFrame({"t0": t0, "pwtt": pwtt, "si": si, "ri": ri, "hr": hr, "map": mapv,
                          "t1_ms": t1, "sbp": mapv * 1.4, "dbp": mapv * 0.8,
                          "ens_dt_lm_ms": dt_lm, "ens_ri_lm": ri_lm,
                          "ens_klass": np.where(np.arange(n_win) % 3 == 0, 3.0, 1.0),
                          "beat_dt_med": dt_lm + rng.normal(0, 2.0, n_win)})
        c = build_case(1000 + k, height, d, age=float(30 + (k * 37) % 50),
                       htn=float(k % 2))
        if c is not None:
            cases.append(c)
    return cases


def _models_form(cases: list, setkey: str = "common") -> list:
    """`src.models.premise_test` が要求する形に詰め直す（同じ配列をそのまま渡す）。"""
    out = []
    for c in cases:
        s = c["sets"].get(setkey)
        if s is None:
            continue
        out.append({"caseid": c["caseid"], "height": c["height"],
                    "windows": {"pwtt": s["pwtt"], "si": s["si_pda"], "ri": s["ri_pda"],
                                "map": s["map"], "co_ref": np.ones(s["n"])}})
    return out


def selftest() -> int:
    import contextlib
    import io
    import tempfile
    from src.models import premise_test

    fails = []

    def rep(name: str, cond, detail: str = "") -> None:
        ok = bool(cond)
        if not ok:
            fails.append(name)
        print(f"  [{'PASS' if ok else 'FAIL'}] {name}" + (f"  {detail}" if detail else ""),
              flush=True)

    print("== 47_dt_bp_landmark_compare 自己検証（合成データのみ・ネットワーク不要） ==\n")

    # ------------------------------------------------ 1. 段階 E
    print("1. 段階 E: 特徴点法の抽出")
    ecg, pleth = m32._synth_case(20 * 60, seed=3, drift=True)

    def loader(_cid):
        return {"pleth": pleth, "ecg": ecg}

    with tempfile.TemporaryDirectory() as td:
        od, od32 = Path(td) / "lm", Path(td) / "v32"
        _cid, df, err = extract_case_47(9001, loader=loader, out_dir=od)
        rep("抽出が通り、ウィンドウごとの表が出る",
            err is None and df is not None and len(df) >= 18,
            f"ウィンドウ {0 if df is None else len(df)}")
        _c2, df32, err32 = m32.extract_case(9001, loader=loader, out_dir=od32)
        a = df["ens_dt_lm_ms"].to_numpy(float)
        b = df32["ens_dt_lm_ms"].to_numpy(float)
        rep("32番の ens_dt_lm_ms と全ウィンドウで一致（NaN の位置も含む）",
            err32 is None and a.shape == b.shape and np.array_equal(a, b, equal_nan=True),
            f"{np.isfinite(a).sum()}/{a.size} 個が有限")
        okw = df[df["n_good"] >= MIN_GOOD]
        ri = okw["ens_ri_lm"].to_numpy(float)
        fin = ri[np.isfinite(ri)]
        frac = float(np.isfinite(ri).mean()) if ri.size else 0.0
        rep("RI_LM が解析できるウィンドウの 90% 以上で有限、かつ (0, 1.5) に入る",
            frac >= 0.90 and fin.size > 0 and bool(np.all((fin > 0) & (fin < 1.5))),
            f"{frac:.0%}・範囲 {fin.min():.3f}〜{fin.max():.3f}" if fin.size else "値なし")
        chk = df["ens_dt_chk_ms"].to_numpy(float)
        m = np.isfinite(chk) & np.isfinite(a)
        rep("再導出した ΔT が 32番の ΔT と一致する（1e-9 ms 以内）",
            m.sum() > 0 and float(np.max(np.abs(chk[m] - a[m]))) <= DT_CHK_TOL_MS,
            f"最大差 {float(np.max(np.abs(chk[m]-a[m]))):.3e} ms・{int(m.sum())} ウィンドウ")
        mp = od / "case_9001_meta.json"
        meta = json.loads(mp.read_text(encoding="utf-8")) if mp.exists() else {}
        rep("meta.json が書かれ、caseid・vitaldb 版・ウィンドウ数が入る",
            mp.exists() and {"caseid", "vitaldb", "duration_min", "n_windows",
                             "n_analyzable"} <= set(meta),
            f"n_windows={meta.get('n_windows')}・n_analyzable={meta.get('n_analyzable')}")
        _c3, df2, err2 = extract_case_47(9001, loader=_raiser, out_dir=od)
        rep("キャッシュがあれば再計算しない", err2 is None and df2 is not None
            and len(df2) == len(df))
        _c4, df3, err3 = extract_case_47(9099, loader=_raiser, out_dir=od)
        rep("loader が例外なら err を返す（止まらない）", df3 is None and bool(err3),
            str(err3)[:40])
        bad = df.copy()
        bad.loc[0, "ens_dt_lm_ms"] = 1.0
        rep("検算の対象列がそろっている（ens_sys_v・ens_dia_v・ens_dt_chk_ms・ens_ri_lm）",
            {"ens_sys_v", "ens_dia_v", "ens_dt_chk_ms", "ens_ri_lm"} <= set(df.columns))

    # ------------------------------------------------ 2. 統計の部品
    print("\n2. 段階 S: 統計の部品（合成の結合表。40 症例 × 40 ウィンドウ）")
    x = np.random.default_rng(7).normal(0, 1, 200)
    z = np.random.default_rng(8).normal(0, 1, 200)
    y = 0.7 * z + np.random.default_rng(9).normal(0, 1, 200)
    rep("偏順位相関: 共変量 1 つなら 45番の式と残差法が一致する",
        abs(_partial_rho(x, y, [z]) - _partial_spearman(x, y, z)) < 1e-12,
        f"{_partial_rho(x, y, [z]):+.6f}")

    hr_cases = _synth_joined(hr_effect=1.0, seed=11)
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        s1 = section1(hr_cases)
    r_map = s1["ρ(ΔT%, ΔMAP%)"]
    r_par = s1["偏ρ(ΔT%, ΔMAP% | ΔHR%)"]
    rep("心拍数が ΔT と MAP を両方動かすとき、調整前の ρ(ΔT%, ΔMAP%) は正",
        np.isfinite(r_map) and r_map > 0.2, f"{r_map:+.3f}")
    rep("ΔHR% を与えた偏順位相関は調整前の半分以下になる（節1 の計算経路を通した）",
        np.isfinite(r_par) and abs(r_par) <= PRED_P1_RATIO * abs(r_map),
        f"{r_par:+.3f}（調整前 {r_map:+.3f}）")
    rep("心拍数と ΔT の症例内相関は負", s1["ρ(ΔT%, ΔHR%)"] < -0.2,
        f"{s1['ρ(ΔT%, ΔHR%)']:+.3f}")

    t1_cases = _synth_joined(lm_t1=0.8, seed=12)
    a_lm = _med_iqr(within(t1_cases, "common", "d_dt_lm", "d_t1"))[0]
    a_pda = _med_iqr(within(t1_cases, "common", "d_dt_pda", "d_t1"))[0]
    rep("T1 を特徴点 ΔT だけが追う仕込みで、P3 の差が規準を超える",
        np.isfinite(a_lm - a_pda) and (a_lm - a_pda) >= PRED_P3_GAP,
        f"特徴点 {a_lm:+.3f} − 分解 {a_pda:+.3f} = {a_lm-a_pda:+.3f}（要 ≥ {PRED_P3_GAP}）")

    null_cases = _synth_joined(seed=13)
    r_null = pooled_reg(null_cases, "common", "d_pwtt", ("d_si_pda", "d_ri_pda"))
    rep("仕込みなしなら 表 C の r²（切片あり）は 0.05 未満",
        abs(r_null["r2_with_int"]) < PRED_P5_R2_MAX, f"r²={r_null['r2_with_int']:.4f}")
    pos_cases = _synth_joined(premise=0.5, seed=14)
    r_pos = pooled_reg(pos_cases, "common", "d_pwtt", ("d_si_pda", "d_ri_pda"))
    rep("仕込みあり（ΔPWTT% = 0.5·ΔSI% ＋ 雑音）なら r²（切片あり）は 0.3 以上",
        r_pos["r2_with_int"] >= 0.3,
        f"r²={r_pos['r2_with_int']:.4f} β_SI={r_pos['betas']['d_si_pda']:+.3f}")
    pt = premise_test(_models_form(pos_cases), with_map=False)
    rep("pooled の r²（切片なし）が src.models.premise_test と一致する",
        abs(pt["r2_vasc"] - r_pos["r2_no_int"]) < 1e-9
        and pt["n_windows"] == r_pos["n_win"],
        f"{pt['r2_vasc']:.6f} 対 {r_pos['r2_no_int']:.6f}・{pt['n_windows']:,} ウィンドウ")
    rep("切片ありの r² は切片なし以上（分母が同じなので）",
        r_pos["r2_with_int"] >= r_pos["r2_no_int"] - 1e-12,
        f"{r_pos['r2_no_int']:.4f} → {r_pos['r2_with_int']:.4f}")

    join_cases = _synth_joined(seed=15, lm_nan={0: 30, 1: 10})
    n_all = sum(1 for c in join_cases if "all" in c["sets"])
    n_com = sum(1 for c in join_cases if "common" in c["sets"])
    c0 = [c for c in join_cases if c["caseid"] == 1000][0]
    c1 = [c for c in join_cases if c["caseid"] == 1001][0]
    rep("ΔT_LM が欠けたウィンドウは共通ウィンドウから落ちる",
        c1["sets"]["common"]["n"] == 30 and c1["sets"]["all"]["n"] == 40,
        f"全 {c1['sets']['all']['n']} → 共通 {c1['sets']['common']['n']}")
    rep("共通ウィンドウが 12 未満の症例は共通の集合から外れる（全ウィンドウには残る）",
        ("common" not in c0["sets"]) and ("all" in c0["sets"]) and n_all == 40 and n_com == 39,
        f"全 {n_all} 症例・共通 {n_com} 症例")
    short = _synth_joined(n_cases=3, n_win=8, seed=16)
    rep("ウィンドウが 12 未満の症例は採用しない", len(short) == 0, f"{len(short)} 症例")

    # ------------------------------------------------ 3. 報告の全文
    print("\n3. 報告の全文と予測との照合")
    full = _synth_joined(hr_effect=1.0, lm_t1=0.8, premise=0.0, seed=17, lm_nan={0: 30})
    miss = {"n_eligible": 40, "n_lm_files": 40, "coverage": 1.0,
            "n_case_used": len(full), "n_win_main": 1600, "n_win_joined": 1600}
    for key in ("all", "common"):
        miss[f"n_case_{key}"] = sum(1 for c in full if key in c["sets"])
        miss[f"n_win_{key}"] = sum(c["sets"][key]["n"] for c in full if key in c["sets"])
    buf2 = io.StringIO()
    err_report = None
    try:
        with contextlib.redirect_stdout(buf2):
            res = report(full, miss)
    except Exception as e:      # noqa: BLE001
        res, err_report = None, e
    txt = buf2.getvalue()
    rep("報告が例外なく最後まで出る", err_report is None, str(err_report)[:70] if err_report else "")
    pl = [ln for ln in txt.splitlines() if ln.strip().startswith(("P1 ", "P2 ", "P3 ", "P4 ", "P5 "))]
    rep("予測の照合が 5 行あり、すべて はい／いいえ が付く",
        len(pl) == 5 and all(("はい" in ln) or ("いいえ" in ln) for ln in pl),
        f"{len(pl)} 行")
    rep("表 A〜表 D と節1・節2 の見出しが出る",
        all(k in txt for k in ("節1.", "節2.", "表 A.", "表 B.", "表 C.", "表 D.")))
    rep("最後の行が出典である",
        txt.strip().splitlines()[-1].startswith("出典: analysis/scripts/47_dt_bp_landmark_compare.py"),
        txt.strip().splitlines()[-1][:70])
    rep("同定率と自己相関は印字しない（論文3 の主要評価項目）",
        ("同定率" in txt) and ("同定率 中央値" not in txt) and ("自己相関 中央値" not in txt))
    if res is not None:
        rep("仕込みどおり P1・P2・P3 が はい になる",
            res["pred"]["P1"] and res["pred"]["P2"] and res["pred"]["P3"],
            f"P1={res['pred']['P1']}・P2={res['pred']['P2']}・P3={res['pred']['P3']}")

    print("\n" + "-" * 74)
    if fails:
        print(f"自己検証: 失敗 {len(fails)} 件")
        for f in fails:
            print(f"  - {f}")
        return 1
    print("自己検証: 通過")
    return 0


# ================================================================ main
def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--extract", action="store_true",
                    help="段階 E: 特徴点法を抽出する（vitaldb・ネットワークが要る）")
    ap.add_argument("--stats-only", action="store_true", help="段階 E を飛ばして集計だけ行う")
    ap.add_argument("--jobs", type=int, default=1, help="段階 E の並列数")
    ap.add_argument("--limit", type=int, default=0, help="対象症例数の上限（0 は全部）")
    ap.add_argument("--partial", action="store_true",
                    help="段階 E が未完でも集計する（判定には使えない）")
    ap.add_argument("--selftest", action="store_true")
    args = ap.parse_args()
    if args.jobs < 1:
        ap.error("--jobs は 1 以上")
    if args.selftest:
        return selftest()
    if args.extract:
        run_extract(jobs=args.jobs, limit=args.limit)
        print("")

    cases, miss = load_joined(args.limit)
    if not cases:
        print("結合できる症例がありません。03番・15番の完走と、この台本の --extract を確認してください。")
        return 1
    if miss["coverage"] < COVERAGE_MIN and not args.partial and not args.limit:
        print("=" * 96)
        print("★★ 中止: 段階 E（特徴点法の抽出）が終わっていません ★★")
        print("=" * 96)
        print(f"  論文1 の採用症例 {miss['n_eligible']} に対し、features_lm は "
              f"{miss['n_lm_files']} 症例（{miss['coverage']*100:.1f}%）しかありません。")
        print(f"  部分集計は症例の偏りで値が大きく動くので、判定には使えません"
              f"（{COVERAGE_MIN*100:.0f}% 未満では出しません）。")
        print("")
        print("  抽出:  python3 scripts/47_dt_bp_landmark_compare.py --extract --jobs 8")
        print("  途中経過をどうしても見たいときだけ --partial を付けてください。")
        print("=" * 96)
        return 2
    if miss["coverage"] < COVERAGE_MIN:
        print(f"★ 部分集計（段階 E の被覆 {miss['coverage']*100:.1f}%）。判定ではない。"
              "抽出の完走後に取り直すこと\n")
    report(cases, miss)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
