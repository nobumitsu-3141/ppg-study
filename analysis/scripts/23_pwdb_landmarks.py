#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""研究0 追試: 失敗は PDA 固有か、PPG 形態指標に共通か（真値既知の仮想集団）。

問題意識
--------
`20_pwdb_validity.py` で、PDA 由来の ΔT・RI はいずれも事前規準を満たさなかった。
ここには2通りの読みがある。

  (a) **PDA 固有の限界**  2カーネル当てはめが波を正しく分けられていない。
      であれば、カーネル数・基底関数・当てはめ方を変える余地がある
  (b) **PPG 形態指標に共通の限界**  指尖脈波の形から伝播速度・抵抗を読むこと自体が
      非特異的である。であれば分解の作り込みでは解決しない

PWDB には Charlton らが同じ仮想被験者に対して算出した**ランドマーク法**の指標が
同梱されている（`pwdb_pw_indices.csv`）。同じ真値・同じ被験者・同じ判定規準で
両者を並べれば (a)(b) を切り分けられる。**指標の作り方だけが違う対照実験**である。

比較する指標（いずれも指尖 PPG 由来）
-------------------------------------
  PDA          ΔT・RI（`data/pwdb/pwdb_indices.csv`。20 番の出力）
  ランドマーク  ΔT = PPGdia_T − PPGsys_T（拡張期ピーク時刻 − 収縮期ピーク時刻）
               SI・RI・AI・AGI_mod（Charlton らの算出値をそのまま使う）
  参照          PTT（モデルが出力する脈波到達時間。真値に近い量の陽性対照）

判定規準は 20 番と同一（年齢層内の Spearman ρ が全層で予測の向き、かつ中央値
|ρ| ≥ 0.3）。規準・年齢層・被験者集合をすべて共有するので、差は指標の作り方だけに帰せる。

使い方
------
    python scripts/23_pwdb_landmarks.py --pwdb ~/pwdb
    python scripts/23_pwdb_landmarks.py --selftest
        ネットワーク不要・模擬データ
"""
from __future__ import annotations

import argparse
import importlib.util
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
DATA = ROOT / "data"
OUT = DATA / "pwdb"


def _load_m20():
    """20_pwdb_validity.py を読み込む（数字始まりなので import 文では書けない）。"""
    p = Path(__file__).resolve().parent / "20_pwdb_validity.py"
    spec = importlib.util.spec_from_file_location("m20", p)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


M = _load_m20()

# (列, 対象, 予測符号, 表示名)。符号 0 は記述のみ
PAIRS = [
    ("dt_pda_ms",  "PWV_a", -1, "PDA        ΔT（2カーネル）"),
    ("dt_lm_ms",   "PWV_a", -1, "ランドマーク ΔT（拡張期−収縮期ピーク）"),
    ("digital_si", "PWV_a", +1, "ランドマーク SI（＝身長/ΔT）"),
    ("digital_agi_mod", "PWV_a", +1, "ランドマーク AGI_mod（2次微分の加齢指数）"),
    ("digital_ptt", "PWV_a", -1, "モデル出力 PTT（陽性対照。強い負を期待）"),
    ("ri_pda",     "pvr", +1, "PDA        RI（2カーネル）"),
    ("digital_ri", "pvr", +1, "ランドマーク RI（拡張期/収縮期ピーク高）"),
    ("digital_ai", "pvr", +1, "ランドマーク AI（増大係数）"),
    ("digital_ri", "PWV_a", 0, "（記述）ランドマーク RI × 大動脈PWV"),
    ("digital_ai", "PWV_a", 0, "（記述）ランドマーク AI × 大動脈PWV"),
]

IDX_FOR_FACTORS = [
    ("dt_pda_ms", "PDA ΔT"),
    ("dt_lm_ms", "ランドマーク ΔT"),
    ("digital_si", "ランドマーク SI"),
    ("ri_pda", "PDA RI"),
    ("digital_ri", "ランドマーク RI"),
    ("digital_ai", "ランドマーク AI"),
]


def _to_ms(d, cols: list[str]) -> None:
    """時刻列が秒なら ms に直す（中央値が 10 未満なら秒とみなす）。"""
    have = [c for c in cols if c in d]
    if not have:
        return
    med = float(np.nanmedian(d[have].to_numpy(float)))
    if np.isfinite(med) and med < 10:
        for c in have:
            d[c] = d[c] * 1000.0
        print("  ランドマークの時刻は秒と判断して ms に換算した", flush=True)


def load(root: Path, pda_dir: Path | None = None):
    """真値・ランドマーク指標・（あれば）PDA の結果を被験者単位で結合する。"""
    import pandas as pd
    root = Path(root).expanduser()
    f_hae = M._find_one(root, "*haemod*param*.csv")
    f_cfg = M._find_one(root, "*model*config*.csv")
    f_idx = M._find_one(root, "*pw*indice*.csv")
    missing = [n for n, q in [("pwdb_haemod_params.csv", f_hae),
                              ("pwdb_model_configs.csv", f_cfg),
                              ("pwdb_pw_indices.csv", f_idx)] if q is None]
    if missing:
        raise FileNotFoundError(f"{root} に次が見つかりません: {missing}")
    print(f"  読み込み元: {f_hae}\n            {f_cfg}\n            {f_idx}", flush=True)

    hae = M._read_named(f_hae, ("subj_no", "age", "HR", "PWV_a", "PWV_cf", "svr"))
    cfg = M._read_named(f_cfg, ("subj_no", "pvr", "pvc"))
    idx = M._read_named(f_idx, ("subj_no", "digital_si", "digital_ri"))
    idx = idx.drop(columns=[c for c in ("age",) if c in idx.columns])

    d = hae.merge(cfg[["subj_no", "pvr", "pvc"]], on="subj_no", how="left")
    d = d.merge(idx[[c for c in idx.columns if c == "subj_no" or c.startswith("digital_")]],
                on="subj_no", how="left")

    extras = M.load_extras(root)
    if "variations" in extras:
        d = d.merge(extras["variations"].drop(columns=["var_age"], errors="ignore"),
                    on="subj_no", how="left")

    _to_ms(d, ["digital_ppgsys_t", "digital_ppgdia_t", "digital_ppgdic_t", "digital_ptt"])
    if "digital_ppgdia_t" in d and "digital_ppgsys_t" in d:
        d["dt_lm_ms"] = d["digital_ppgdia_t"] - d["digital_ppgsys_t"]
    else:
        d["dt_lm_ms"] = np.nan
        print("  （拡張期／収縮期ピーク時刻の列がないため、ランドマーク ΔT は計算しない）")

    pda_p = (OUT if pda_dir is None else Path(pda_dir)) / "pwdb_indices.csv"
    if pda_p.exists():
        pda = pd.read_csv(pda_p)
        keep = {"subj_no": "subj_no", "dt2_ms": "dt_pda_ms", "ri2": "ri_pda", "ok2": "ok2"}
        have = {k: v for k, v in keep.items() if k in pda.columns}
        d = d.merge(pda[list(have)].rename(columns=have), on="subj_no", how="left")
        print(f"  PDA の結果を結合: {pda_p}", flush=True)
    else:
        for c in ("dt_pda_ms", "ri_pda", "ok2"):
            d[c] = np.nan
        print(f"  （{pda_p} がないので PDA 列は空。先に 20_pwdb_validity.py を実行すると"
              " 直接比較になる）", flush=True)
    return d


def report(d, out_dir: Path | None = None) -> dict:
    ages = sorted(d["age"].dropna().unique().tolist())
    n_lm = int(d["digital_si"].notna().sum())
    n_pda = int(d.get("ok2", 0).fillna(0).sum()) if "ok2" in d else 0
    print(f"\n{'='*78}\n研究0 追試: PDA とランドマーク法を同じ真値・同じ規準で比べる\n{'='*78}")
    print(f"\n被験者 {len(d)} 名 / ランドマーク指標あり {n_lm} / PDA 収束 {n_pda}")
    print(f"  年齢層: {ages}")
    print(f"  判定規準は 20_pwdb_validity.py と同一（全層で予測の向き、中央値 |ρ| ≥ {M.CRIT_RHO}）")

    ok2 = d[d.get("ok2", 1).fillna(0) == 1] if "ok2" in d else d
    print(f"\n{'-'*78}\n年齢層内の順位相関（Spearman ρ）\n{'-'*78}")
    hdr = f"{'指標 × 真値':<40}" + "".join(f"{int(a):>7}" for a in ages) + f"{'中央値':>8}{'向き':>8}  判定"
    print(hdr)
    summary = {}
    for col, tgt, sign, lab in PAIRS:
        src = ok2 if col in ("dt_pda_ms", "ri_pda") else d
        if col not in src or tgt not in src or src[col].notna().sum() < 20:
            print(f"{lab:<40}  （データなし）")
            continue
        rows = M._by_age(src, col, tgt)
        j = M._judge(rows, sign)
        by = {a: r for a, r, _n in rows}
        line = f"{lab:<40}"
        for a in ages:
            r = by.get(a, np.nan)
            line += f"{r:>+7.2f}" if np.isfinite(r) else f"{'—':>7}"
        if j:
            exp = {-1: "負", 1: "正", 0: "—"}[sign]
            verdict = ("成立" if j["pass"] else "不成立") if sign else "記述"
            line += f"{j['med_abs']:>8.3f}{j['n_ok']:>4}/{j['n_ages']:<3}{exp}  {verdict}"
            summary[f"{col}|{tgt}"] = j
        print(line)

    if "var_pwv" in d:
        print(f"\n{'-'*78}\n振った因子ごとの主効果（年齢層内。+1 と −1 の平均差 ÷ 層平均 [%]）\n{'-'*78}")
        print(f"{'指標':<22}" + "".join(f"{M.FACTOR_LABEL[f]:>12}" for f in M.FACTORS))
        for col, lab in IDX_FOR_FACTORS:
            src = ok2 if col in ("dt_pda_ms", "ri_pda") else d
            if col not in src or src[col].notna().sum() < 20:
                continue
            e, _r = M._factor_effects(src, col)
            print(f"{lab:<22}" + "".join(f"{v:>+12.1f}" if np.isfinite(v) else f"{'—':>12}" for v in e))
        print("  概念どおりなら、スティフネス指標は『脈波伝播速度』の列が最大になるはずである。")

    print(f"\n{'-'*78}\n読み方\n{'-'*78}")
    print("  ランドマーク法も不成立 → 失敗は PDA 固有ではなく、指尖脈波の形から")
    print("    伝播速度・抵抗を読むこと自体が非特異的。カーネル数や基底関数を変えても解決しない。")
    print("  ランドマーク法だけ成立   → 失敗は PDA 固有。分解の作り方に改善の余地がある。")
    print("  モデル出力 PTT が強い負を示さないなら、この比較自体を疑うこと（配管の陽性対照）。")

    out_dir = OUT if out_dir is None else Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    p = out_dir / "pwdb_landmarks.csv"
    d.to_csv(p, index=False)
    print(f"\n被験者別の結果: {p}")
    return summary


# ---------------------------------------------------------------- 自己検証
INDEX_HEADER = ("Subject Number, Age, Digital_SBP_V, Digital_PPGsys_V, Digital_PPGsys_T, "
                "Digital_PPGdia_V, Digital_PPGdia_T, Digital_PPGdic_T, Digital_AI, Digital_AP, "
                "Digital_RI, Digital_SI, Digital_AGI_mod, Digital_PTT")


def _make_mock(root: Path, n: int = 48, seed: int = 0):
    """実配布版と同じ見出しで、ランドマーク指標に既知の関係を仕込む。"""
    import pandas as pd
    rng = np.random.default_rng(seed)
    M._make_mock(root, n=n, seed=seed)          # haemod・configs・variations・PPG を作る
    hae = M._read_named(root / "pwdb_haemod_params.csv", ("subj_no", "age", "PWV_a"))
    cfg = M._read_named(root / "pwdb_model_configs.csv", ("subj_no", "pvr"))
    m = hae.merge(cfg[["subj_no", "pvr"]], on="subj_no")
    rows = []
    for _, r in m.iterrows():
        pwv, pvr = float(r["PWV_a"]), float(r["pvr"]) / 1e8
        dt = 0.42 - 0.022 * pwv + 0.002 * rng.standard_normal()   # 秒。PWV↑で短縮
        ri = 0.20 + 0.28 * (pvr - 0.8) / 1.4                      # 抵抗↑で上昇
        sys_t, sys_v = 0.11, 1.0
        rows.append([int(r["subj_no"]), float(r["age"]), 120, sys_v, sys_t,
                     ri, sys_t + dt, sys_t + dt * 0.6, 100 * ri * 0.5, 5.0,
                     ri, 1.75 / dt, 0.3 * pwv, 0.9 / pwv])
    with open(root / "pwdb_pw_indices.csv", "w") as f:
        f.write(INDEX_HEADER + "\n")
        for r in rows:
            f.write(",".join(f"{v:.10g}" if isinstance(v, float) else str(v) for v in r) + "\n")
    return root


def selftest() -> int:
    import tempfile
    print("== 23_pwdb_landmarks 自己検証（模擬PWDB・ネットワーク不要） ==\n")
    ok = True

    def rep(name, cond, detail=""):
        nonlocal ok
        ok &= bool(cond)
        print(f"  [{'PASS' if cond else 'FAIL'}] {name}{('  ' + detail) if detail else ''}", flush=True)

    with tempfile.TemporaryDirectory() as td:
        root = _make_mock(Path(td) / "exported_data", n=48)
        d = load(root, pda_dir=Path(td) / "nopda")
        rep("ランドマーク指標が読めた（SI・RI・AI・AGI_mod・PTT）",
            all(c in d for c in ("digital_si", "digital_ri", "digital_ai",
                                 "digital_agi_mod", "digital_ptt")))
        rep("時刻を秒→ms に換算し ΔT を作れた",
            "dt_lm_ms" in d and 100 < float(np.nanmedian(d["dt_lm_ms"])) < 400,
            f"中央値 {float(np.nanmedian(d['dt_lm_ms'])):.0f} ms")
        rep("PDA 列は無くても落ちない（20番の出力が未作成の場合）",
            "dt_pda_ms" in d and d["dt_pda_ms"].isna().all())
        s = report(d, out_dir=Path(td) / "out")
        j_dt = s.get("dt_lm_ms|PWV_a")
        j_si = s.get("digital_si|PWV_a")
        j_ri = s.get("digital_ri|pvr")
        rep("仕込んだ ランドマークΔT × PWV（負）を復元", bool(j_dt and j_dt["pass"]), f"{j_dt}")
        rep("仕込んだ ランドマークSI × PWV（正）を復元", bool(j_si and j_si["pass"]), f"{j_si}")
        rep("仕込んだ ランドマークRI × 抵抗（正）を復元", bool(j_ri and j_ri["pass"]), f"{j_ri}")
        rep("判定規準を 20 番と共有している", M.CRIT_RHO == 0.30)
    print("\n" + ("ALL PASS" if ok else "FAIL あり"))
    return 0 if ok else 1


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--pwdb", type=str, help="PWDB の配布物を置いたフォルダ")
    ap.add_argument("--selftest", action="store_true")
    args = ap.parse_args()
    if args.selftest:
        sys.exit(selftest())
    if not args.pwdb:
        ap.error("--pwdb を指定してください（--selftest なら不要）")
    report(load(Path(args.pwdb)))


if __name__ == "__main__":
    main()
