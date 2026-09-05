#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""研究0: 真値既知の仮想集団（Charlton PWDB）で構成概念妥当性を検証する。

なぜこれを最初にやるのか
------------------------
測定に基づく研究の筋道は (1) 指標が測りたい量を測れているか、(2) その量が生理学的な
標的と関連するか、(3) その情報で臨床推定が改善するか、の順である。研究1は (2) を
飛ばして (2) と (3) の中間の問い（指標は ΔPWTT を説明するか）を問うたため、陰性の
解釈が繰り返し曖昧になった。本スクリプトは (2) を真値に対して直接検証する。

問い
----
  Q1  PDA由来の ΔT は、真値の大動脈脈波伝播速度（PWV_a）と関連するか
      ※ SI = 身長/ΔT は 1/ΔT の単調変換なので、順位相関では符号が反転するだけ
  Q2  PDA由来の RI は、真値の末梢血管抵抗（PVR・SVR）と関連するか
  Q3  成分対の取り方で結果が変わるか
      2カーネル 1↔2 ／ 3カーネル 1↔2 ／ 3カーネル 1↔3
      Couceiro 2015 は5ガウス分解で R1_2（前進波↔収縮後期波）0.26 に対し
      R1_d（前進波↔反射波）0.42 と正反対の成績を示した。真値で決着させる
  Q4  総動脈コンプライアンス（PVC）・心拍出量との関連
      Zc = ρ·PWV/A、PWV ∝ 1/√C という理論的な鎖が指標に現れるか

設計と判定（実行前に固定。lab_log 2026-09-03）
--------------------------------------------
PWDB は年齢6段階 × 6因子（大動脈径・心拍数・駆出時間・平均血圧・脈波伝播速度・1回拍出量）
の3水準完全要因配置（729 × 6 = 4,374 名）。末梢血管抵抗 pvr は入力ではなく、平均血圧と
心拍出量から決まる派生量である。したがって
  主判定  年齢層内の順位相関が全層で予測の向き、かつ中央値 |ρ| ≥ 0.3 なら成立
          Q1: ρ(ΔT, PWV_a) < 0    Q2: ρ(RI, pvr) > 0
  機構    因子ごとの主効果（+1 と −1 の差）で、ΔT を動かすのが脈波伝播速度、
          RI を動かすのが平均血圧（＝抵抗）であることを確かめる
  真値    pwdb_onset_times.csv の立ち上がり時刻の差 ＝ 真の伝播時間。橈骨→指尖の真値の幅を
          VitalDB の T2−T1 の症例内変動（SD ≈ 18 ms）と比べる

なぜ決定的か
------------
本研究は VitalDB で「血管指標は ΔPWTT を説明しない」「RI は妥当性を確立できない」
という結果を得ている。in silico と突き合わせると切り分けられる。

  in silico 成立 × VitalDB 不成立 → 信号鎖の問題（研究2へ）
  in silico 不成立 × VitalDB 不成立 → 概念の限界（撤退）

データ
------
Charlton P.H. et al. Modelling arterial pulse waves in healthy ageing.
Am J Physiol Heart Circ Physiol 2019. doi:10.5281/zenodo.3275625
仮想被験者 4,374名（25〜75歳）。指尖を含む13部位の圧・流速・内腔断面積・PPG。
真値として大動脈脈波伝播速度・末梢血管抵抗・総動脈コンプライアンス・1回拍出量。

使い方
------
    python scripts/20_pwdb_validity.py --pwdb ~/pwdb
        ~/pwdb は Zenodo から取得した配布物を置いたフォルダ。zip のままでも展開済みでもよく、
        必要な3ファイル（haemod_params・model_configs・Digital_PPG）を再帰的に探す
    python scripts/20_pwdb_validity.py --pwdb ~/pwdb --limit 200 --jobs 4
    python scripts/20_pwdb_validity.py --selftest
        ネットワーク不要・模擬データ
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.pda import fit_beat, skew_gaussian, component_peak, model2  # noqa: E402
from src.indices import si_ri_from_fit                               # noqa: E402

DATA = Path(__file__).resolve().parent.parent / "data"
OUT = DATA / "pwdb"

# ---------------------------------------------------------------- 読み込み
# 列は見出しの名前で引く（単位の [..] を落として小文字化）。位置対応は配布版の版差で
# 黙ってずれるので使わない。実配布版（Zenodo 2019-07-07）の model_configs には
# base・base_age の2列が age の前にあり、位置対応だと pvr の位置に density（定数 1060）が
# 入っていた。実行前の見出し確認で捕まえた。
def _norm(col) -> str:
    c = re.sub(r"\[.*?\]", "", str(col))
    c = c.strip().lower()
    return re.sub(r"[^a-z0-9]+", "_", c).strip("_")


RENAME = {"hr": "HR", "sv": "SV", "co": "CO", "pwv_a": "PWV_a", "pwv_cf": "PWV_cf"}


def _read_named(path: Path, need: tuple, prefix: str = ""):
    """見出し名で列を引く。need の列が無ければ見出しを添えて止まる。"""
    import pandas as pd
    df = pd.read_csv(path, skipinitialspace=True)
    cols = {}
    for c in df.columns:
        n = _norm(c)
        if n == "subject_number":
            n = "subj_no"
        elif prefix:
            n = prefix + n
        else:
            n = RENAME.get(n, n)
        cols[c] = n
    df = df.rename(columns=cols)
    missing = [k for k in need if k not in df.columns]
    if missing:
        raise KeyError(f"{path.name}: 必要な列がありません {missing}。"
                       f"見出し（正規化後）: {list(df.columns)[:14]} …")
    df["subj_no"] = df["subj_no"].astype(int)
    return df


# 配布物の中で探すファイル。Zenodo の zip の階層は配布版で変わりうるので、名前の
# パターンで root 以下を再帰的に探す（大文字小文字は無視）。
NEEDED = {
    "haemod": ("*haemod*param*.csv", "血行動態の真値 pwdb_haemod_params.csv"),
    "config": ("*model*config*.csv", "モデル入力 pwdb_model_configs.csv"),
    "ppg":    ("*digital*ppg*.csv",  "指尖PPG PWs_Digital_PPG.csv"),
}


def _find_one(root: Path, pattern: str):
    """root 以下で pattern に合う CSV を1つ返す（見つからなければ None）。"""
    import fnmatch
    hits = [q for q in root.rglob("*.csv") if fnmatch.fnmatch(q.name.lower(), pattern)]
    if not hits:
        return None
    # 同名が複数あるとき（例: mat 版と csv 版の展開が混在）は最も浅いものを採る
    hits.sort(key=lambda q: (len(q.parts), str(q)))
    return hits[0]


def _extract_from_zips(root: Path) -> list:
    """root 以下の zip の中に必要ファイルがあれば、その3つだけを取り出す。"""
    import fnmatch
    import zipfile
    got = []
    for z in sorted(root.rglob("*.zip")):
        try:
            with zipfile.ZipFile(z) as zf:
                for member in zf.namelist():
                    name = Path(member).name.lower()
                    if any(fnmatch.fnmatch(name, pat) for pat, _ in NEEDED.values()):
                        dest = root / "extracted"
                        dest.mkdir(parents=True, exist_ok=True)
                        zf.extract(member, dest)
                        got.append(dest / member)
        except zipfile.BadZipFile:
            continue
    return got


def locate_pwdb_files(root: Path) -> dict:
    """必要な3ファイルの実パスを返す。無ければ何があったかを添えて例外を出す。"""
    root = Path(root).expanduser()
    if not root.exists():
        raise FileNotFoundError(
            f"ディレクトリがありません: {root}\n"
            "Zenodo（doi:10.5281/zenodo.3275625）から CSV 形式の配布物を取得し、"
            "そのフォルダ（zip のままでもよい）を --pwdb に渡してください。")
    found = {k: _find_one(root, pat) for k, (pat, _) in NEEDED.items()}
    if any(v is None for v in found.values()):
        got = _extract_from_zips(root)
        if got:
            print(f"  zip から {len(got)} ファイルを取り出した: {root / 'extracted'}", flush=True)
            found = {k: _find_one(root, pat) for k, (pat, _) in NEEDED.items()}
    missing = [NEEDED[k][1] for k, v in found.items() if v is None]
    if missing:
        listing = sorted(str(q.relative_to(root)) for q in root.rglob("*")
                         if q.is_file())[:40]
        raise FileNotFoundError(
            "必要なファイルが見つかりません: " + " / ".join(missing) + "\n"
            f"{root} 以下にあるもの（先頭40件）:\n  " + "\n  ".join(listing) +
            "\n.mat 形式のみの配布物には対応していません。CSV 形式を取得してください。")
    return found


# 任意の追加ファイル（あれば使う）
EXTRA = {
    "variations": ("*model*variation*.csv", "var_",
                   ("subj_no", "var_age", "var_dia", "var_hr", "var_lvet", "var_mbp", "var_pwv", "var_sv")),
    "onsets": ("*onset*time*.csv", "on_", ("subj_no", "on_aorticroot_p", "on_digital_ppg")),
}


def load_extras(root: Path) -> dict:
    """pwdb_model_variations.csv（どの因子を振ったか）と pwdb_onset_times.csv（真の立ち上がり時刻）。"""
    out = {}
    root = Path(root).expanduser()
    for key, (pat, prefix, need) in EXTRA.items():
        q = _find_one(root, pat)
        if q is None:
            print(f"  （{key}: 見つからないので省略）", flush=True)
            continue
        try:
            out[key] = _read_named(q, need, prefix=prefix)
            print(f"  読み込み元: {q}", flush=True)
        except KeyError as e:
            print(f"  （{key}: {e} → 省略）", flush=True)
    return out


def load_pwdb(root: Path):
    """PWDB の配布物から真値・入力・指尖PPG・追加表を読む。root は配布物を置いた親フォルダでよい。"""
    import pandas as pd
    f = locate_pwdb_files(root)
    print(f"  読み込み元: {f['haemod']}\n            {f['config']}\n            {f['ppg']}",
          flush=True)
    hae = _read_named(f["haemod"], ("subj_no", "age", "HR", "SV", "CO", "PWV_a", "PWV_cf", "svr"))
    cfg = _read_named(f["config"], ("subj_no", "pvr", "pvc"))
    ppg = pd.read_csv(f["ppg"], skipinitialspace=True)
    extras = load_extras(root)
    return hae, cfg, ppg, extras


def beat_of(ppg_row: np.ndarray, hr_bpm: float):
    """1被験者の1拍と標本化周波数を返す。

    CSVには標本化周波数が入らない（.mat のみ）。拍長 = 60/HR 秒であることから復元する。
    """
    y = np.asarray(ppg_row[1:], float)          # 先頭は Subject Number
    # 末尾の詰め物だけを落とす。**途中の欠測で詰めると波形をつなぎ合わせてしまい**、
    # 標本数から復元する標本化周波数もずれる（`src/pda2.preprocess` の内部 NaN の守りは、
    # ここで詰めてしまうと二度と効かない）
    fin = np.isfinite(y)
    n_keep = int(np.argmax(~fin)) if (~fin).any() else y.size
    if n_keep == 0 or fin[n_keep:].any():
        # 欠測より後ろにまだ実データがある＝末尾の詰め物ではなく**拍の内部の欠測**。
        # 詰めると波形をつなぎ合わせ、標本数から復元する標本化周波数もずれるので落とす
        return None, np.nan
    y = y[:n_keep]
    if y.size < 40 or not np.isfinite(hr_bpm) or hr_bpm <= 0:
        return None, np.nan
    dur = 60.0 / float(hr_bpm)
    return y, y.size / dur


# ---------------------------------------------------------------- 3カーネル
def fit_beat3_all(t: np.ndarray, y: np.ndarray, seed: int = 0, n_starts: int = 6):
    """3カーネル分解。**すべての成分対**の ΔT・振幅比を返す。

    既存の `scripts/11_variants_extract.py` の `fit_beat3` は第1↔第2成分しか返さない。
    これは Couceiro の T1_2・R1_2、すなわち成績の悪かった対に相当する。
    第1↔第3（R1_d 相当）を含めて比較できるようにする。
    """
    from scipy.optimize import least_squares
    t = np.asarray(t, float)
    y0 = np.asarray(y, float) - float(np.min(y))
    ymax = float(np.max(y0))
    if ymax <= 0:
        return None
    ys = y0 / ymax
    i_pk = int(np.argmax(ys))
    t_pk = float(t[i_pk])
    #      a1    mu1              s1     al1  a2    dmu2  s2     al2  a3    dmu3  s3     al3
    lo = [0.05, 0.02,            0.015, 0.0, 0.02, 0.06, 0.015, 0.0, 0.01, 0.05, 0.015, 0.0]
    hi = [1.5, max(t_pk + .1, .3), .25, 8.0, 1.2, 0.45, 0.25, 8.0, 1.0, 0.45, 0.25, 8.0]

    def unpack(q):
        a1, m1, s1, l1, a2, d2, s2, l2, a3, d3, s3, l3 = q
        return np.array([a1, m1, s1, l1, a2, m1 + d2, s2, l2, a3, m1 + d2 + d3, s3, l3])

    def resid(q):
        p = unpack(q)
        m = np.zeros_like(t)
        for i in range(3):
            m = m + skew_gaussian(t, *p[4 * i:4 * i + 4])
        return m - ys

    rng = np.random.default_rng(seed)
    sols = []
    for _ in range(n_starts):
        x0 = np.clip(np.array([0.8, t_pk, 0.05, 2.0,
                               0.35, 0.10 + 0.25 * rng.random(), 0.07, 1.0,
                               0.15, 0.10 + 0.25 * rng.random(), 0.09, 1.0]), lo, hi)
        try:
            r = least_squares(resid, x0, bounds=(lo, hi), max_nfev=600)
        except Exception:
            continue
        sols.append((float(np.sum(r.fun ** 2)), r.x))
    if not sols:
        return None
    sols.sort(key=lambda s: s[0])
    q = sols[0][1]
    p = unpack(q)
    pk = [component_peak(tuple(p[4 * i:4 * i + 4]), t[0], t[-1]) for i in range(3)]
    (tp1, h1), (tp2, h2), (tp3, h3) = pk
    if min(h1, h2, h3) <= 0:
        return None
    # 第3成分が床に張り付く＝3つ目の波が無い正常な退化。その旨を返す
    comp3_absent = bool(q[8] <= lo[8] + 0.02)
    return {"dt3_12": (tp2 - tp1) * 1000.0, "ri3_12": h2 / h1,
            "dt3_13": (tp3 - tp1) * 1000.0, "ri3_13": h3 / h1,
            "comp3_absent": comp3_absent}


# ---------------------------------------------------------------- 1被験者
def indices_for_subject(args_tuple):
    subj, row, hr = args_tuple
    try:
        y, fs = beat_of(row, hr)
        if y is None:
            return {"subj_no": subj, "ok2": 0, "ok3": 0}
        t = np.arange(y.size) / fs
        out = {"subj_no": subj, "fs": fs, "n_samp": y.size}
        # --- 2カーネル（主解析と同一の凍結コード） ---
        try:
            fit = fit_beat(t, y)
            ix = si_ri_from_fit(fit)
            out.update({"dt2_ms": ix["dt_s"] * 1000.0, "ri2": ix["ri"],
                        "ok2": int(bool(fit.get("ok", False))),
                        "nrmse2": fit["nrmse"]})
        except Exception:
            out["ok2"] = 0
        # --- 3カーネル（成分対をすべて返す） ---
        f3 = fit_beat3_all(t, y)
        if f3:
            out.update(f3); out["ok3"] = 1
        else:
            out["ok3"] = 0
        return out
    except Exception as e:  # noqa: BLE001
        return {"subj_no": subj, "ok2": 0, "ok3": 0, "err": str(e)[:80]}


# ---------------------------------------------------------------- 統計
def _spearman(x, y, min_n: int = 20):
    from scipy.stats import rankdata
    g = np.isfinite(x) & np.isfinite(y)
    if g.sum() < min_n:
        return float("nan"), int(g.sum())
    a, b = np.asarray(x)[g], np.asarray(y)[g]
    if np.ptp(a) == 0 or np.ptp(b) == 0:
        return float("nan"), int(g.sum())
    return float(np.corrcoef(rankdata(a), rankdata(b))[0, 1]), int(g.sum())


FACTORS = ["dia", "hr", "lvet", "mbp", "pwv", "sv"]
FACTOR_LABEL = {"dia": "大動脈径", "hr": "心拍数", "lvet": "駆出時間", "mbp": "平均血圧",
                "pwv": "脈波伝播速度", "sv": "1回拍出量"}
# 事前規準（lab_log 2026-09-03）: 年齢層内の順位相関が全層で予測の向き、かつ中央値 |ρ| ≥ 0.3
CRIT_RHO = 0.30
PAIRS = [("dt2_ms", "PWV_a", -1, "Q1  ΔT 2k × 大動脈PWV"),
         ("dt2_ms", "PWV_cf", -1, "    ΔT 2k × 頸大腿PWV"),
         ("ri2", "pvr", +1, "Q2  RI 2k × 末梢血管抵抗"),
         ("ri2", "svr", +1, "    RI 2k × 全身血管抵抗"),
         ("ri2", "pvc", 0, "    RI 2k × 末梢コンプライアンス"),
         ("dt3_12", "PWV_a", -1, "    ΔT 3k 1↔2 × 大動脈PWV"),
         ("dt3_13", "PWV_a", -1, "    ΔT 3k 1↔3 × 大動脈PWV"),
         ("ri3_12", "pvr", +1, "    RI 3k 1↔2 × 末梢血管抵抗"),
         ("ri3_13", "pvr", +1, "    RI 3k 1↔3 × 末梢血管抵抗")]


def _by_age(d, x, y, min_n: int = 8):
    """年齢層ごとの Spearman ρ。min_n は 1 層に要る人数（既定 8）。

    26番は自分の定数 `MIN_PER_AGE` を渡し、自己検証で既定値と一致することを確かめる
    （両方に 8 が別々に書かれていて、片方だけ変えても誰も気づかない状態だった。11 巡目 S11）。
    """
    out = []
    for age, g in d.groupby("age"):
        r, n = _spearman(g[x].to_numpy(float), g[y].to_numpy(float), min_n=min_n)
        out.append((age, r, n))
    return out


def _judge(rows, sign):
    rs = np.array([r for _a, r, _n in rows if np.isfinite(r)])
    if rs.size == 0:
        return None
    n_ok = int((np.sign(rs) == sign).sum()) if sign else int(rs.size)
    med = float(np.median(np.abs(rs)))
    return {"n_ages": int(rs.size), "n_ok": n_ok, "med_abs": med,
            "pass": bool(sign) and n_ok == rs.size and med >= CRIT_RHO}


def _factor_effects(d, idx):
    """年齢層内の主効果（+1 と −1 の平均差を層平均で割った %）と順位相関。年齢層の中央値。"""
    eff, rho = [], []
    for _age, g in d.groupby("age"):
        v = g[idx].to_numpy(float)
        m = float(np.nanmean(v)) if np.isfinite(v).sum() >= 8 else np.nan
        if not np.isfinite(m) or m == 0:
            continue
        e_row, r_row = [], []
        for f in FACTORS:
            lv = g[f"var_{f}"].to_numpy(float)
            hi_, lo_ = v[lv > 0.5], v[lv < -0.5]
            e_row.append(100.0 * (np.nanmean(hi_) - np.nanmean(lo_)) / m
                         if hi_.size and lo_.size else np.nan)
            r_row.append(_spearman(v, lv, min_n=8)[0])
        eff.append(e_row)
        rho.append(r_row)
    if not eff:
        return np.full(len(FACTORS), np.nan), np.full(len(FACTORS), np.nan)
    return np.nanmedian(np.array(eff), axis=0), np.nanmedian(np.array(rho), axis=0)


def _oat_table(d, idx):
    """1因子だけ振った被験者（他は基準値）での値。年齢層の中央値を −1 / 0 / +1 で返す。"""
    lv = d[[f"var_{f}" for f in FACTORS]].to_numpy(float)
    nz = (np.abs(lv) > 0.5).sum(axis=1)
    base = d[nz == 0].groupby("age")[idx].median()
    out = {}
    for j, f in enumerate(FACTORS):
        sel = d[(nz == 1) & (np.abs(lv[:, j]) > 0.5)]
        lo_ = sel[sel[f"var_{f}"] < -0.5].groupby("age")[idx].median()
        hi_ = sel[sel[f"var_{f}"] > 0.5].groupby("age")[idx].median()
        out[f] = tuple(float(np.nanmedian(x)) if len(x) else np.nan for x in (lo_, base, hi_))
    return out


def _onsets_ms(on):
    cols = [c for c in on.columns if c.startswith("on_")]
    med = float(np.nanmedian(on[cols].to_numpy(float)))
    if np.isfinite(med) and med < 10:      # 秒なら ms に
        on = on.copy()
        on[cols] = on[cols] * 1000.0
        print("  立ち上がり時刻は秒と判断して ms に換算した", flush=True)
    return on


def report(df, hae, cfg, extras: dict | None = None, out_dir: Path | None = None) -> dict:
    import pandas as pd
    extras = extras or {}
    d = df.merge(hae, on="subj_no", how="left")
    d = d.merge(cfg[["subj_no", "pvr", "pvc"]], on="subj_no", how="left")
    if "variations" in extras:
        d = d.merge(extras["variations"], on="subj_no", how="left")
    if "onsets" in extras:
        on = _onsets_ms(extras["onsets"])
        d = d.merge(on, on="subj_no", how="left")
        d["ptt_root_fin_ms"] = d["on_digital_ppg"] - d["on_aorticroot_p"]
        if "on_radial_ppg" in d:
            d["ptt_rad_fin_ms"] = d["on_digital_ppg"] - d["on_radial_ppg"]
    summary = {"n": int(len(d))}

    print(f"\n{'='*74}\n研究0: 真値既知の仮想集団による構成概念妥当性\n{'='*74}")
    n2 = int(d.get("ok2", pd.Series(dtype=int)).sum())
    n3 = int(d.get("ok3", pd.Series(dtype=int)).sum())
    print(f"\n被験者 {len(d)} 名 / 2カーネル収束検算通過 {n2} ({n2/max(len(d),1):.0%})"
          f" / 3カーネル当てはめ成功 {n3} ({n3/max(len(d),1):.0%})")
    if "comp3_absent" in d:
        print(f"  うち第3成分が退化（2カーネル解に一致）: {int(d['comp3_absent'].sum())}")
    if "fs" in d:
        fs_med = float(np.nanmedian(d["fs"]))
        summary["fs"] = fs_med
        print(f"  拍長 60/HR から復元した標本化周波数 中央値 {fs_med:.0f} Hz（配布版は 500 Hz のはず）")
    ages = sorted(d["age"].dropna().unique().tolist())
    print(f"  年齢層: {ages}")

    ok2 = d[d.get("ok2", 0) == 1]
    ok3 = d[d.get("ok3", 0) == 1]

    # --- 1. 全員をプールした順位相関（年齢の効果を含むので参考） ---
    targets = [("PWV_a", "大動脈PWV"), ("PWV_cf", "頸大腿PWV"), ("svr", "全身抵抗"),
               ("pvr", "末梢抵抗"), ("pvc", "末梢ｺﾝﾌﾟﾗｲｱﾝｽ"), ("CO", "心拍出量"),
               ("SV", "1回拍出量"), ("age", "年齢")]
    idx = [("dt2_ms", "ΔT  2カーネル 1↔2", "2"),
           ("ri2", "RI  2カーネル 1↔2", "2"),
           ("dt3_12", "ΔT  3カーネル 1↔2", "3"),
           ("ri3_12", "RI  3カーネル 1↔2  (Couceiro R1_2 相当)", "3"),
           ("dt3_13", "ΔT  3カーネル 1↔3", "3"),
           ("ri3_13", "RI  3カーネル 1↔3  (Couceiro R1_d 相当)", "3")]
    print(f"\n{'-'*74}\n1. 全員プールの順位相関（Spearman ρ。年齢差を含むので参考値）\n{'-'*74}")
    print(f"{'指標':<40}" + "".join(f"{t[:9]:>11}" for _c, t in targets))
    for col, lab, which in idx:
        src = ok2 if which == "2" else ok3
        if col not in src:
            continue
        line = f"{lab:<40}"
        for tgt, _ in targets:
            r, _n = _spearman(src[col].to_numpy(float), src[tgt].to_numpy(float))
            line += f"{r:>+11.3f}" if np.isfinite(r) else f"{'—':>11}"
        print(line)

    # --- 2. 年齢層内の順位相関（主判定） ---
    print(f"\n{'-'*74}\n2. 年齢層内の順位相関（主判定。各層の ρ と中央値、予測の向きに揃った層の数）\n{'-'*74}")
    print(f"{'対':<34}" + "".join(f"{int(a):>7}" for a in ages) + f"{'中央値':>9}{'向き':>8}  判定")
    for x, y, sign, lab in PAIRS:
        src = ok2 if x in ("dt2_ms", "ri2") else ok3
        if x not in src or y not in src:
            continue
        rows = _by_age(src, x, y)
        j = _judge(rows, sign)
        line = f"{lab:<34}"
        by = {a: r for a, r, _n in rows}
        for a in ages:
            r = by.get(a, np.nan)
            line += f"{r:>+7.2f}" if np.isfinite(r) else f"{'—':>7}"
        if j:
            exp = {-1: "負", 1: "正", 0: "—"}[sign]
            verdict = ("成立" if j["pass"] else "不成立") if sign else "記述"
            line += f"{j['med_abs']:>9.3f}{j['n_ok']:>4}/{j['n_ages']:<3} {exp}  {verdict}"
            if lab.startswith("Q1"):
                summary["q1"] = j
            if lab.startswith("Q2"):
                summary["q2"] = j
        print(line)
    print(f"  規準: 全層で予測の向き かつ 中央値 |ρ| ≥ {CRIT_RHO}。事前予測は ΔT×PWV が負、RI×抵抗が正。")
    print("  注意: PWDB の pvr は入力の MBP・HR・SV から決まる派生量（MBP ≈ pvr × CO）。")
    print("        RI×pvr の関連は MBP・HR・SV の効果と混ざるので、3 の要因別の主効果で切り分ける。")

    # --- 3. 要因別の主効果（変動表がある場合） ---
    if "var_pwv" in d:
        print(f"\n{'-'*74}\n3. 振った因子ごとの主効果（年齢層内。+1 と −1 の平均差 ÷ 層平均 [%]、および順位相関）\n{'-'*74}")
        print(f"{'因子':<14}{'ΔT 主効果%':>12}{'ρ(ΔT)':>9}{'RI 主効果%':>12}{'ρ(RI)':>9}")
        e_dt, r_dt = _factor_effects(ok2, "dt2_ms")
        e_ri, r_ri = _factor_effects(ok2, "ri2")
        for k, f in enumerate(FACTORS):
            print(f"{FACTOR_LABEL[f]:<14}{e_dt[k]:>+12.1f}{r_dt[k]:>+9.2f}{e_ri[k]:>+12.1f}{r_ri[k]:>+9.2f}")
        summary["factor_dt"] = dict(zip(FACTORS, map(float, e_dt)))
        summary["factor_ri"] = dict(zip(FACTORS, map(float, e_ri)))
        print("  読み方: ΔT が主に「脈波伝播速度」で動き、RI が主に「平均血圧（＝末梢抵抗）」で動けば概念どおり。")
        print("          Epstein 2014 では導管スティフネス +200% で SI +60%、末梢抵抗 +200% で SI <2%。")

        print(f"\n{'-'*74}\n4. 1因子だけ振った被験者（他はすべて基準値）での値。年齢層の中央値\n{'-'*74}")
        print(f"{'因子':<14}{'ΔT −1':>9}{'ΔT 0':>9}{'ΔT +1':>9}{'RI −1':>9}{'RI 0':>9}{'RI +1':>9}")
        o_dt, o_ri = _oat_table(ok2, "dt2_ms"), _oat_table(ok2, "ri2")
        for f in FACTORS:
            a, b, c = o_dt[f]
            x, y, z = o_ri[f]
            print(f"{FACTOR_LABEL[f]:<14}{a:>9.1f}{b:>9.1f}{c:>9.1f}{x:>9.3f}{y:>9.3f}{z:>9.3f}")

    # --- 5. 真の伝播時間（立ち上がり時刻の表がある場合） ---
    if "ptt_root_fin_ms" in d:
        print(f"\n{'-'*74}\n5. 真の伝播時間（モデルの立ち上がり時刻の差。装置遅延も PEP も含まない）\n{'-'*74}")
        q = lambda v: np.nanpercentile(v, [5, 50, 95])  # noqa: E731
        a5, a50, a95 = q(d["ptt_root_fin_ms"].to_numpy(float))
        print(f"  大動脈起始部→指尖  中央値 {a50:.1f} ms（5–95% {a5:.1f}–{a95:.1f}）")
        if "ptt_rad_fin_ms" in d:
            b5, b50, b95 = q(d["ptt_rad_fin_ms"].to_numpy(float))
            print(f"  橈骨→指尖（VitalDB の T2−T1 の生理部分に相当） 中央値 {b50:.1f} ms（5–95% {b5:.1f}–{b95:.1f}）")
            summary["ptt_rad_fin"] = (float(b5), float(b50), float(b95))
        r_pwv = _judge(_by_age(d, "PWV_a", "ptt_root_fin_ms"), -1)
        r_dt = _judge(_by_age(ok2, "dt2_ms", "ptt_root_fin_ms"), +1)
        if r_pwv:
            print(f"  年齢層内 ρ(大動脈PWV, 起始部→指尖の伝播時間) 中央値|ρ| {r_pwv['med_abs']:.2f}"
                  f"（負の層 {r_pwv['n_ok']}/{r_pwv['n_ages']}。強く負なら真値どうしが整合）")
        if r_dt:
            print(f"  年齢層内 ρ(ΔT, 起始部→指尖の伝播時間) 中央値|ρ| {r_dt['med_abs']:.2f}"
                  f"（正の層 {r_dt['n_ok']}/{r_dt['n_ages']}。ΔT が伝播時間を追うなら正）")
        summary["ptt_root_fin_rho_pwv"] = r_pwv
        summary["ptt_root_fin_rho_dt"] = r_dt

    # --- 判定のまとめ ---
    print(f"\n{'-'*74}\n判定（事前規準）\n{'-'*74}")
    for key, lab in (("q1", "Q1 ΔT は大動脈PWV と関連する"), ("q2", "Q2 RI は末梢血管抵抗と関連する")):
        j = summary.get(key)
        if j:
            print(f"  {lab}: {'成立' if j['pass'] else '不成立'}"
                  f"（向きの揃った層 {j['n_ok']}/{j['n_ages']}、中央値 |ρ| {j['med_abs']:.3f}）")
    print("  VitalDB では不成立だったので、in silico 成立なら信号鎖の問題、不成立なら概念の限界（roadmap §3）。")

    out_dir = OUT if out_dir is None else Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    p = out_dir / "pwdb_indices.csv"
    d.to_csv(p, index=False)
    print(f"\n被験者別の結果（真値・因子・立ち上がり時刻を結合済み）: {p}")
    return summary


# ---------------------------------------------------------------- 自己検証
HAEMOD_HEADER = ("Subject Number, age [years], HR [bpm], SV [ml], CO [l/min], LVET [ms], dp/dt [mmHg/s], "
                 "PFT [ms], RFV [ml], SBP_a [mmHg], DBP_a [mmHg], MAP_a [mmHg], PP_a [mmHg], SBP_b [mmHg], "
                 "DBP_b [mmHg], MBP_b [mmHg], PP_b [mmHg], PP_amp [ratio], AP [mmHg], AIx [%], Tr [ms], "
                 "PWV_a [m/s], PWV_cf [m/s], PWV_br [m/s], PWV_fa [m/s], dia_asca [mm], dia_dta [mm], "
                 "dia_abda [mm], dia_car [mm], Len [mm], drop fin [mmHg], drop ankle [mmHg], SVR [10^6 Pa s / m3]")
CONFIG_HEADER = ("Subject Number, base, base_age, age [years], hr [bpm], sv [ml], pft [ms], rfv [ml], dbp [mmHg], "
                 "mbp [mmHg], viscosity [Pa s], alpha [-], p_drop [mmHg], pvc [scaling factor], p_out [mmHg], "
                 "density [kg /m^3], lvet [ms], pvr [Pa s/m^3], b0 [g/s], b1 [g cm/s], k1 [g/s^2/cm], k2 [/cm], "
                 "k3 [g/s^2/cm]")
VARIATION_HEADER = "SUBJECT NUMBER, AGE, DIA, HR, LVET, MBP, PWV, SV"
ONSET_HEADER = ("Subject Number, AorticRoot_P, AorticRoot_U, AorticRoot_A, AorticRoot_PPG, Radial_P, Radial_U, "
                "Radial_A, Radial_PPG, Digital_P, Digital_U, Digital_A, Digital_PPG")


def _make_mock(root: Path, n: int = 48, seed: int = 0):
    """実配布版と同じ見出しの模擬データを作る。真値と指標の関係を仕込む。"""
    rng = np.random.default_rng(seed)
    root.mkdir(parents=True, exist_ok=True)
    (root / "PWs" / "csv").mkdir(parents=True, exist_ok=True)
    ages = [25, 35, 45, 55, 65, 75]
    fs, rows, hae, cfg, var, ons, truth = 500.0, [], [], [], [], [], {}
    for i in range(1, n + 1):
        age = ages[(i - 1) % 6]
        lv = rng.integers(-1, 2, size=6)                   # DIA, HR, LVET, MBP, PWV, SV
        hr = float(rng.uniform(55, 85))
        pwv = 5.0 + 0.09 * (age - 25) + 1.2 * lv[4] + float(rng.uniform(-0.3, 0.3))   # 真値
        pvr = float(rng.uniform(0.8, 2.2)) * 1e8                                          # 真値
        dur = 60.0 / hr
        m = int(dur * fs)
        tt = np.arange(m) / fs
        dt_true = 0.42 - 0.022 * pwv                        # PWVが大きいほど短縮
        ri_true = 0.20 + 0.28 * (pvr / 1e8 - 0.8) / 1.4     # 抵抗が大きいほど上昇
        y = (1.00 * np.exp(-0.5 * ((tt - 0.11) / 0.045) ** 2)
             + ri_true * np.exp(-0.5 * ((tt - (0.11 + dt_true)) / 0.075) ** 2))
        rows.append([i] + list(y))
        hae.append([i, age, hr, 70.0, hr * 70 / 1000.0, 300.0, 900.0, 0.1, 0.0,
                    120, 80, 93, 40, 118, 79, 92, 39, 1.05, 5.0, 20.0, 140.0,
                    pwv, pwv * 0.95, 8.0, 9.0, 3.0, 2.5, 1.8, 0.7, 0.2, 5.0, 5.0, pvr * 1.6 / 1e6])
        cfg.append([i, int(lv.sum() == 0), 1, age, hr, 70.0, 79, 0.73, 75, 89, 0.0025, 1.3333, 0,
                    1.0, 33.2, 1060, 282, pvr, 600, 150, 3e6, -13.5, 5.4e5])
        var.append([i, age] + lv.tolist())
        t_fin = 0.05 + 1.2 / pwv                            # 秒（換算の検査用）
        ons.append([i, 0.0, 0.0, 0.0, 0.01, t_fin - 0.06, t_fin - 0.06, t_fin - 0.06, t_fin - 0.02,
                    t_fin - 0.01, t_fin - 0.01, t_fin - 0.01, t_fin])
        truth[i] = {"pwv": pwv, "pvr": pvr, "fs": fs}

    w = max(len(r) for r in rows)
    mat = np.full((len(rows), w), np.nan)
    for k, r in enumerate(rows):
        mat[k, :len(r)] = r
    hdr = "Subject Number, " + ", ".join(f"pt{j}" for j in range(1, w))
    p = root / "PWs" / "csv" / "PWs_Digital_PPG.csv"
    with open(p, "w") as f:
        f.write(hdr + "\n")
    with open(p, "a") as f:
        np.savetxt(f, mat, delimiter=",", fmt="%.10g")

    def _write(name, header, table):
        with open(root / name, "w") as f:
            f.write(header + "\n")
            for r in table:
                f.write(",".join(f"{v:.15g}" if isinstance(v, float) else str(v) for v in r) + "\n")

    _write("pwdb_haemod_params.csv", HAEMOD_HEADER, hae)
    _write("pwdb_model_configs.csv", CONFIG_HEADER, cfg)
    _write("pwdb_model_variations.csv", VARIATION_HEADER, var)
    _write("pwdb_onset_times.csv", ONSET_HEADER, ons)
    return root, truth


def selftest() -> int:
    import tempfile, pandas as pd
    print("== 20_pwdb_validity 自己検証（模擬PWDB・実配布版の見出し・ネットワーク不要） ==\n")
    ok = True

    def rep(name, cond, detail=""):
        nonlocal ok
        ok &= bool(cond)
        print(f"  [{'PASS' if cond else 'FAIL'}] {name}{('  ' + detail) if detail else ''}", flush=True)

    with tempfile.TemporaryDirectory() as td:
        root, truth = _make_mock(Path(td) / "exported_data", n=48)
        hae, cfg, ppg, extras = load_pwdb(root)
        rep("見出し名で読めた（haemod 33列・configs 23列）",
            len(hae) == 48 and "PWV_a" in hae and "svr" in hae and "pvr" in cfg and "pvc" in cfg)
        c = cfg.set_index("subj_no")
        rep("configs の pvr が仕込んだ真値と一致（density 1060 ではない）",
            all(abs(c.loc[i, "pvr"] - truth[i]["pvr"]) <= 1e-6 * truth[i]["pvr"] for i in truth))
        h = hae.set_index("subj_no")
        rep("haemod の PWV_a が仕込んだ真値と一致",
            all(abs(h.loc[i, "PWV_a"] - truth[i]["pwv"]) < 1e-6 for i in truth))
        rep("追加表（variations・onsets）が読めた", "variations" in extras and "onsets" in extras)

        rows = []
        for i in range(len(ppg)):
            rows.append(indices_for_subject((int(ppg.iloc[i, 0]), ppg.iloc[i].to_numpy(float),
                                             float(h.loc[int(ppg.iloc[i, 0]), "HR"]))))
            if (i + 1) % 12 == 0:
                print(f"    当てはめ {i+1}/{len(ppg)}", flush=True)
        df = pd.DataFrame(rows)
        rep("2カーネルの収束率 > 80%", df["ok2"].mean() > 0.8, f"{df['ok2'].mean():.0%}")
        rep("拍長から復元した fs ≈ 500 Hz", abs(float(np.nanmedian(df["fs"])) - 500) < 10,
            f"{float(np.nanmedian(df['fs'])):.0f} Hz")
        rep("3カーネルの当てはめ成功率 > 50%", df["ok3"].mean() > 0.5, f"{df['ok3'].mean():.0%}")

        summ = report(df, hae, cfg, extras, out_dir=Path(td) / "out")
        q1, q2 = summ.get("q1"), summ.get("q2")
        rep("Q1 仕込んだ ΔT×PWV の関係を年齢層内で復元（成立判定）",
            bool(q1 and q1["pass"]), f"{q1}" if q1 else "None")
        rep("Q2 仕込んだ RI×pvr の関係を年齢層内で復元（成立判定）",
            bool(q2 and q2["pass"]), f"{q2}" if q2 else "None")
        rp = summ.get("ptt_root_fin_rho_pwv")
        rep("立ち上がり時刻を秒→ms に換算し、真の伝播時間が PWV と負に相関",
            bool(rp and rp["pass"]), f"{rp}" if rp else "None")
        rep("要因別の主効果が計算できた", "factor_dt" in summ)
    print("\n" + ("ALL PASS" if ok else "FAIL あり"))
    return 0 if ok else 1


# ---------------------------------------------------------------- main
def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--pwdb", type=str, help="PWDB の配布物を置いたフォルダ（zip のままでも可）")
    ap.add_argument("--limit", type=int, default=0, help="先頭N名だけ処理（0=全員）")
    ap.add_argument("--jobs", type=int, default=1)
    ap.add_argument("--selftest", action="store_true")
    args = ap.parse_args()

    if args.selftest:
        sys.exit(selftest())
    if not args.pwdb:
        ap.error("--pwdb を指定してください（--selftest なら不要）")

    import pandas as pd
    root = Path(args.pwdb).expanduser()
    hae, cfg, ppg, extras = load_pwdb(root)
    if args.limit:
        ppg = ppg.iloc[:args.limit]
    hr_by = dict(zip(hae["subj_no"].astype(int), hae["HR"].astype(float)))
    work = [(int(ppg.iloc[i, 0]), ppg.iloc[i].to_numpy(float),
             hr_by.get(int(ppg.iloc[i, 0]), np.nan)) for i in range(len(ppg))]
    print(f"{len(work)} 名を処理します / jobs={args.jobs}", flush=True)

    if args.jobs > 1:
        from concurrent.futures import ProcessPoolExecutor
        with ProcessPoolExecutor(max_workers=args.jobs) as ex:
            rows = list(ex.map(indices_for_subject, work, chunksize=8))
    else:
        rows = []
        for n, w in enumerate(work, 1):
            rows.append(indices_for_subject(w))
            if n % 200 == 0:
                print(f"  [{n}/{len(work)}]", flush=True)
    report(pd.DataFrame(rows), hae, cfg, extras)


if __name__ == "__main__":
    main()
