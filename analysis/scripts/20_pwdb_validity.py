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
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.pda import fit_beat, skew_gaussian, component_peak, model2  # noqa: E402
from src.indices import si_ri_from_fit                               # noqa: E402

DATA = Path(__file__).resolve().parent.parent / "data"
OUT = DATA / "pwdb"

# export_pwdb.m 由来。列は位置で対応づける（見出しは略号＋単位で書かれるため）
HAEMOD_PARAMS = ["subj_no", "age", "HR", "SV", "CO", "LVET", "dPdt", "PFT", "RFV",
                 "SBP_a", "DBP_a", "MBP_a", "PP_a", "SBP_b", "DBP_b", "MBP_b", "PP_b",
                 "PP_amp", "AP", "AIx", "Tr", "PWV_a", "PWV_cf", "PWV_br", "PWV_fa",
                 "dia_asc_a", "dia_desc_thor_a", "dia_abd_a", "dia_car", "len_prox_a",
                 "MBP_drop_finger", "MBP_drop_ankle", "svr"]
CONFIG_PARAMS = ["subj_no", "age", "hr", "sv", "t_pf", "reg_vol", "dbp", "mbp", "mu",
                 "alpha", "p_drop", "pvc", "p_out", "rho", "lvet", "pvr",
                 "gamma_b0", "gamma_b1"]


# ---------------------------------------------------------------- 読み込み
def _read_positional(path: Path, names: list[str]):
    """位置で列名を割り当てる。PWDBの見出しは略号＋単位のため名前照合ができない。"""
    import pandas as pd
    df = pd.read_csv(path, skipinitialspace=True)
    if df.shape[1] < len(names):
        # 版差で列が減ることがある。頭から対応づけ、足りない分は欠測にする
        df.columns = names[:df.shape[1]]
        for n in names[df.shape[1]:]:
            df[n] = np.nan
    else:
        df.columns = names + [f"extra_{i}" for i in range(df.shape[1] - len(names))]
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


def load_pwdb(root: Path):
    """PWDB の配布物から真値と指尖PPGを読む。root は配布物を置いた任意の親フォルダでよい。"""
    import pandas as pd
    f = locate_pwdb_files(root)
    print(f"  読み込み元: {f['haemod']}\n            {f['config']}\n            {f['ppg']}",
          flush=True)
    hae = _read_positional(f["haemod"], HAEMOD_PARAMS)
    cfg = _read_positional(f["config"], CONFIG_PARAMS)
    ppg = pd.read_csv(f["ppg"], skipinitialspace=True)
    return hae, cfg, ppg


def beat_of(ppg_row: np.ndarray, hr_bpm: float):
    """1被験者の1拍と標本化周波数を返す。

    CSVには標本化周波数が入らない（.mat のみ）。拍長 = 60/HR 秒であることから復元する。
    """
    y = np.asarray(ppg_row[1:], float)          # 先頭は Subject Number
    y = y[np.isfinite(y)]
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
def _spearman(x, y):
    from scipy.stats import rankdata
    g = np.isfinite(x) & np.isfinite(y)
    if g.sum() < 20:
        return float("nan"), int(g.sum())
    a, b = np.asarray(x)[g], np.asarray(y)[g]
    if np.ptp(a) == 0 or np.ptp(b) == 0:
        return float("nan"), int(g.sum())
    return float(np.corrcoef(rankdata(a), rankdata(b))[0, 1]), int(g.sum())


def report(df, hae, cfg):
    import pandas as pd
    d = df.merge(hae, on="subj_no", how="left")
    if cfg is not None:
        d = d.merge(cfg[["subj_no", "pvr", "pvc"]], on="subj_no", how="left")
    for c in ("pvr", "pvc"):
        if c not in d:
            d[c] = np.nan

    print(f"\n{'='*74}\n研究0: 真値既知の仮想集団による構成概念妥当性\n{'='*74}")
    n2 = int(d.get("ok2", pd.Series(dtype=int)).sum())
    n3 = int(d.get("ok3", pd.Series(dtype=int)).sum())
    print(f"\n被験者 {len(d)} 名 / 2カーネル収束検算通過 {n2} ({n2/max(len(d),1):.0%})"
          f" / 3カーネル当てはめ成功 {n3} ({n3/max(len(d),1):.0%})")
    if "comp3_absent" in d:
        print(f"  うち第3成分が退化（2カーネル解に一致）: {int(d['comp3_absent'].sum())}")

    # 収束検算を通った拍のみを使う（主解析と同じ規約）
    ok2 = d[d.get("ok2", 0) == 1]
    ok3 = d[d.get("ok3", 0) == 1]

    targets = [("PWV_a", "大動脈脈波伝播速度", ok2, ok3),
               ("PWV_cf", "頸大腿脈波伝播速度", ok2, ok3),
               ("svr", "全身血管抵抗", ok2, ok3),
               ("pvr", "末梢血管抵抗（入力）", ok2, ok3),
               ("pvc", "末梢血管コンプライアンス（入力）", ok2, ok3),
               ("CO", "心拍出量", ok2, ok3),
               ("SV", "1回拍出量", ok2, ok3),
               ("age", "年齢", ok2, ok3)]
    idx = [("dt2_ms", "ΔT  2カーネル 1↔2", "2"),
           ("ri2", "RI  2カーネル 1↔2", "2"),
           ("dt3_12", "ΔT  3カーネル 1↔2", "3"),
           ("ri3_12", "RI  3カーネル 1↔2  (Couceiro R1_2 相当)", "3"),
           ("dt3_13", "ΔT  3カーネル 1↔3", "3"),
           ("ri3_13", "RI  3カーネル 1↔3  (Couceiro R1_d 相当)", "3")]

    print(f"\n{'-'*74}\n順位相関（Spearman ρ）\n{'-'*74}")
    hdr = f"{'指標':<40}" + "".join(f"{t[:9]:>11}" for t, _, _, _ in targets)
    print(hdr)
    for col, lab, which in idx:
        src = ok2 if which == "2" else ok3
        if col not in src:
            continue
        line = f"{lab:<40}"
        for tgt, _, _, _ in targets:
            r, n = _spearman(src[col].to_numpy(float), src[tgt].to_numpy(float))
            line += f"{r:>+11.3f}" if np.isfinite(r) else f"{'—':>11}"
        print(line)

    print(f"\n事前予測: 動脈が硬い（PWV大）ほど反射波の帰還が早く ΔT は短縮する → ρ(ΔT, PWV) < 0")
    print(f"          末梢が収縮（抵抗大）するほど反射が強まる → ρ(RI, PVR) > 0")
    print(f"注意: SI = 身長/ΔT は 1/ΔT の単調変換であり、順位相関では符号が反転するだけである")

    OUT.mkdir(parents=True, exist_ok=True)
    p = OUT / "pwdb_indices.csv"
    d.to_csv(p, index=False)
    print(f"\n被験者別の結果: {p}")


# ---------------------------------------------------------------- 自己検証
def _make_mock(root: Path, n: int = 60, seed: int = 0):
    """PWDB と同じCSV形式の模擬データを作る。真値と指標の関係を仕込む。"""
    import pandas as pd
    rng = np.random.default_rng(seed)
    root.mkdir(parents=True, exist_ok=True)
    (root / "PWs" / "csv").mkdir(parents=True, exist_ok=True)

    fs, rows, hae, cfg = 500.0, [], [], []
    for i in range(1, n + 1):
        hr = float(rng.uniform(55, 85))
        pwv = float(rng.uniform(4.0, 12.0))                 # 真値
        pvr = float(rng.uniform(0.8, 2.2))                  # 真値
        dur = 60.0 / hr
        m = int(dur * fs)
        tt = np.arange(m) / fs
        dt_true = 0.42 - 0.022 * pwv                        # PWVが大きいほど短縮
        ri_true = 0.20 + 0.28 * (pvr - 0.8) / 1.4           # 抵抗が大きいほど上昇
        y = (1.00 * np.exp(-0.5 * ((tt - 0.11) / 0.045) ** 2)
             + ri_true * np.exp(-0.5 * ((tt - (0.11 + dt_true)) / 0.075) ** 2))
        rows.append([i] + list(y))
        hae.append([i, 55.0, hr, 70.0, hr * 70 / 1000.0, 300.0, 900.0, 0.1, 0.0,
                    120, 80, 93, 40, 118, 79, 92, 39, 1.05, 5.0, 20.0, 140.0,
                    pwv, pwv * 0.95, 8.0, 9.0, 3.0, 2.5, 1.8, 0.7, 0.2, 5.0, 5.0, pvr])
        cfg.append([i, 55.0, hr, 70.0, 0.3, 0.0, 80, 93, 0.0025, 1.3, 0.0,
                    1.2e-8, 0.0, 1060, 300, pvr, 0.0, 0.0])

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

    pd.DataFrame(hae).to_csv(root / "pwdb_haemod_params.csv", index=False,
                             header=["Subject Number"] + [f"{c} [u]" for c in HAEMOD_PARAMS[1:]])
    pd.DataFrame(cfg).to_csv(root / "pwdb_model_configs.csv", index=False,
                             header=["Subject Number"] + [f"{c} [u]" for c in CONFIG_PARAMS[1:]])
    return root


def selftest() -> int:
    import tempfile, pandas as pd
    print("== 20_pwdb_validity 自己検証（模擬PWDB・ネットワーク不要） ==\n")
    ok = True
    with tempfile.TemporaryDirectory() as td:
        root = _make_mock(Path(td) / "exported_data", n=30)
        hae, cfg, ppg = load_pwdb(root)
        print(f"  読み込み: 血行動態 {hae.shape} / 設定 {cfg.shape} / PPG {ppg.shape}")
        load_ok = len(hae) == 30 and len(ppg) == 30 and "PWV_a" in hae and "pvr" in cfg
        ok &= load_ok
        print(f"  列の位置対応（PWV_a・pvr が引ける）  {'PASS' if load_ok else 'FAIL'}")

        rows = []
        for i in range(len(ppg)):
            rows.append(indices_for_subject((int(ppg.iloc[i, 0]), ppg.iloc[i].to_numpy(float),
                                             float(hae.iloc[i]["HR"]))))
            if (i + 1) % 10 == 0:
                print(f"    当てはめ {i+1}/{len(ppg)}", flush=True)
        df = pd.DataFrame(rows)
        conv = df["ok2"].mean()
        c_ok = conv > 0.8
        ok &= c_ok
        print(f"  2カーネルの収束率 {conv:.0%}  {'PASS' if c_ok else 'FAIL'}")

        d = df.merge(hae, on="subj_no")
        r_pwv, _ = _spearman(d["dt2_ms"].to_numpy(float), d["PWV_a"].to_numpy(float))
        r_svr, _ = _spearman(d["ri2"].to_numpy(float), d["svr"].to_numpy(float))
        p1 = np.isfinite(r_pwv) and r_pwv < -0.9
        p2 = np.isfinite(r_svr) and r_svr > 0.9
        ok &= p1 and p2
        print(f"  仕込んだ関係を復元: ρ(ΔT, PWV)={r_pwv:+.3f}（要 <−0.9）  {'PASS' if p1 else 'FAIL'}")
        print(f"                      ρ(RI, SVR)={r_svr:+.3f}（要 >+0.9）  {'PASS' if p2 else 'FAIL'}")

        f3 = df["ok3"].mean()
        f3_ok = f3 > 0.5
        ok &= f3_ok
        print(f"  3カーネルの当てはめ成功率 {f3:.0%}  {'PASS' if f3_ok else 'FAIL'}")
    print("\n" + ("ALL PASS" if ok else "FAIL あり"))
    return 0 if ok else 1


# ---------------------------------------------------------------- main
def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--pwdb", type=str, help="PWDB の exported_data ディレクトリ")
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
    hae, cfg, ppg = load_pwdb(root)
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
    report(pd.DataFrame(rows), hae, cfg)


if __name__ == "__main__":
    main()
