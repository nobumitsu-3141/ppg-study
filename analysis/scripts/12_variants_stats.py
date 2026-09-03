#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""変種抽出（11_variants_extract.py）の結果を集計し、主解析と比較する（SAP §7.5・Table 5）。

各変種について前提検証（ΔPWTT% ~ Δ指標%）と精度評価（対照 vs 補正）を
主解析と同じ機構（src.models）で再計算する。PWTT・HR・MAP・CO は
主解析キャッシュの値を (caseid, t0) で結合して使う。

使い方（zsh は行末の # をコメントと見なさないので、説明は別行に置く）:
    python scripts/12_variants_stats.py --check
        データの点検だけ（数秒）
    python scripts/12_variants_stats.py
        集計（862例で1分前後）
    python scripts/12_variants_stats.py --selftest
        合成データで配管を検算

出力は画面に加えて data/variants_table.csv にも書く。
`| tail` で受けると tail が全入力を読み終えるまで何も表示されないので、
途中経過を見たいときはパイプせずそのまま実行する。

列名の注意: 変種ファイルの dt・ri は主解析ファイルの ri と名前が衝突するため、
結合時に dt_rep・ri_rep に改名する（改名しないと「再現」行が主解析の RI を
読んでしまう）。
"""
from __future__ import annotations

import argparse
import faulthandler
import json
import sys
import unicodedata
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.models import crossval, premise_test, premise_by_case  # noqa: E402
from src.stats import bootstrap_diff_ci                        # noqa: E402

DATA = Path(__file__).resolve().parent.parent / "data"
MIN_WINDOWS = 12
MIN_CASES = 10

# 変種ファイルの列名 → 結合後の列名（主解析の ri と衝突するものだけ改名）
RENAME = {"dt": "dt_rep", "ri": "ri_rep", "n_dt": "n_dt_rep", "n_ri": "n_ri_rep"}

# (ΔT系の列, RI系の列, 表示名)。ΔT系の列が "si" のときは主解析の SI をそのまま使う
VARIANTS = [
    ("si",       "ri",         "主解析（同一ウィンドウで再計算）"),
    ("dt_rep",   "ri_rep",     "再現（同一定義・当てはめ再実行）"),
    ("dt_onset", "ri_rep",     "立ち上がり間ΔT（20%規約）"),
    ("dt_rep",   "a_ratio",    "振幅パラメータ比 a2/a1"),
    ("dt_rep",   "area_ratio", "成分波面積比"),
    ("dt3",      "ri3",        "3カーネルPDA"),
    ("dt_n2",    "ri_n2",      "ノイズ目標 0.002（厳格）"),
    ("dt_n4",    "ri_n4",      "ノイズ目標 0.004（緩和）"),
    ("dt_sqi5",  "ri_sqi5",    "SQI 同一値連続 <5%（厳格）"),
    ("dt_sqi20", "ri_sqi20",   "SQI 同一値連続 <20%（緩和）"),
]


def _w(s: str) -> int:
    """表示幅（全角=2）。"""
    return sum(2 if unicodedata.east_asian_width(ch) in "FW" else 1 for ch in s)


def _pad(s: str, width: int) -> str:
    return s + " " * max(width - _w(s), 0)


def say(msg: str = "") -> None:
    print(msg, flush=True)


# ---------------------------------------------------------------- 読み込み
def load_joined(data: Path) -> tuple[dict[int, pd.DataFrame], dict]:
    """主解析と変種のウィンドウを t0 で結合し、症例ごとの DataFrame を返す。"""
    feat, vfeat = data / "features", data / "features_variants"
    inv = {"meta": 0, "meta_bad": 0, "csv_missing": 0, "read_error": 0,
           "short": 0, "no_height": 0, "joined": 0}
    demo = pd.read_csv(data / "cases.csv", encoding="utf-8-sig").set_index("caseid")
    out: dict[int, pd.DataFrame] = {}
    for meta_p in sorted(vfeat.glob("case_*_meta.json")):
        inv["meta"] += 1
        try:
            cid = int(json.loads(meta_p.read_text(encoding="utf-8"))["caseid"])
        except Exception:
            inv["meta_bad"] += 1
            continue
        vp, mp = vfeat / f"case_{cid}.csv", feat / f"case_{cid}.csv"
        if not (vp.exists() and mp.exists()):
            inv["csv_missing"] += 1
            continue
        try:
            v = pd.read_csv(vp).rename(columns=RENAME)
            m = pd.read_csv(mp)
        except Exception:
            inv["read_error"] += 1
            continue
        j = m.merge(v, on="t0", how="inner")
        if len(j) < MIN_WINDOWS:
            inv["short"] += 1
            continue
        h = float(demo["height"].get(cid, np.nan)) if cid in demo.index else np.nan
        if not np.isfinite(h) or h < 100:
            inv["no_height"] += 1
            continue
        j.attrs["height_m"] = h / 100.0
        out[cid] = j
    inv["joined"] = len(out)
    return out, inv


def build_cases(joined: dict, dt_col: str, ri_col: str) -> list[dict]:
    """変種の (ΔT, RI) で主解析と同じ形の症例辞書を作る。

    si は 身長/ΔT に組み直す（premise_test の回帰子 ΔSI% の定義を保つ）。
    dt_col が "si" のときは主解析の SI 列をそのまま使う（参照行）。
    変種が欠損のウィンドウは落とし、残り≥12の症例のみ採用する。
    """
    cases = []
    for cid, j in joined.items():
        if dt_col not in j.columns or ri_col not in j.columns:
            continue
        d = j.dropna(subset=["pwtt", "hr", "map", "co_ref", dt_col, ri_col])
        d = d[d[dt_col].to_numpy(float) > 0]
        if len(d) < MIN_WINDOWS:
            continue
        h = j.attrs["height_m"]
        si = d["si"].to_numpy(float) if dt_col == "si" else h / d[dt_col].to_numpy(float)
        cases.append({"caseid": cid, "height": h, "windows": {
            "pwtt": d["pwtt"].to_numpy(float),
            "si": si,
            "ri": d[ri_col].to_numpy(float),
            "hr": d["hr"].to_numpy(float),
            "map": d["map"].to_numpy(float),
            "co_ref": d["co_ref"].to_numpy(float),
        }})
    return cases


# ---------------------------------------------------------------- 点検
def check(joined: dict, inv: dict) -> None:
    say(f"メタ {inv['meta']} 件: 結合できた症例 {inv['joined']}"
        f"（メタ不良 {inv['meta_bad']} / CSV欠落 {inv['csv_missing']} / 読込失敗 {inv['read_error']}"
        f" / 結合後<{MIN_WINDOWS}窓 {inv['short']} / 身長なし {inv['no_height']}）")
    if not joined:
        return
    n_tot = sum(len(j) for j in joined.values())
    say(f"結合ウィンドウ総数 {n_tot:,}")
    say()
    say(f"{_pad('変種', 34)}{'症例≥12窓':>10}{'窓数':>9}{'欠損率':>8}")
    say("-" * 61)
    for dt_col, ri_col, label in VARIANTS:
        cases = build_cases(joined, dt_col, ri_col)
        n_win = sum(len(c["windows"]["pwtt"]) for c in cases)
        say(f"{_pad(label, 34)}{len(cases):>10}{n_win:>9,}{1 - n_win / max(n_tot, 1):>8.0%}")
    say()
    say("欠損率は「結合ウィンドウのうち、その変種が計算できなかった割合」。")
    say("3カーネルとノイズ目標0.002は計算条件が厳しいので高めになる。")


# ---------------------------------------------------------------- 集計
def run(joined: dict, out_csv: Path | None) -> pd.DataFrame:
    say()
    say("== 変種ごとの前提検証と精度（主解析と同じ機構で再計算） ==")
    hdr = (f"{_pad('変種', 34)}{'症例':>5}{'窓数':>9}{'r²':>8}{'βΔSI%':>9}{'βΔRI%':>9}"
           f"{'符号揃い':>9}{'PE対照':>8}{'PE補正':>8}{'ΔPE [95%CI]':>22}")
    say(hdr)
    say("-" * _w(hdr))
    rows = []
    for dt_col, ri_col, label in VARIANTS:
        cases = build_cases(joined, dt_col, ri_col)
        n_win = sum(len(c["windows"]["pwtt"]) for c in cases)
        row = {"variant": label, "dt_col": dt_col, "ri_col": ri_col,
               "n_cases": len(cases), "n_windows": n_win}
        if len(cases) < MIN_CASES:
            say(f"{_pad(label, 34)}{len(cases):>5}{n_win:>9,}   （症例不足）")
            rows.append(row)
            continue
        pt = premise_test(cases, with_map=False)
        diag = premise_by_case(cases)
        ci = bootstrap_diff_ci(crossval(cases))
        row.update({
            "r2_vasc": pt["r2_vasc"], "beta_dsi": pt["beta_dsi"], "beta_dri": pt["beta_dri"],
            "sign_consistency": diag["sign_consistency"], "r2_within_median": diag["r2_median"],
            "pe_ctrl_median": ci["pe_ctrl_median"], "pe_prop_median": ci["pe_prop_median"],
            "dpe_mean": ci["diff_mean"], "ci_low": ci["ci_low"], "ci_high": ci["ci_high"],
        })
        rows.append(row)
        say(f"{_pad(label, 34)}{len(cases):>5}{n_win:>9,}{pt['r2_vasc']:>8.3f}"
            f"{pt['beta_dsi']:>+9.3f}{pt['beta_dri']:>+9.3f}"
            f"{diag['sign_consistency']:>8.0%}"
            f"{ci['pe_ctrl_median']:>7.1f}%{ci['pe_prop_median']:>7.1f}%"
            f"  {ci['diff_mean']:+.1f} [{ci['ci_low']:+.1f}, {ci['ci_high']:+.1f}]")
    df = pd.DataFrame(rows)
    if out_csv is not None:
        out_csv.parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(out_csv, index=False)
        say()
        say(f"表を書き出した: {out_csv}")
    say()
    say("読み方: 1行目は主解析の値を同じウィンドウ集合で再計算した参照。")
    say("        どの変種でも r² が 0 近傍のままなら、主結論（前提の弱さ）は")
    say("        指標定義・カーネル数・前処理閾値の選択に依存しない。")
    return df


# ---------------------------------------------------------------- 自己検査
def _make_synthetic(data: Path, n_cases: int = 30, n_win: int = 40, seed: int = 0) -> None:
    """11_variants_extract.py / 03_run_analysis.py と同じ書式の合成データを作る。"""
    rng = np.random.default_rng(seed)
    feat, vfeat = data / "features", data / "features_variants"
    feat.mkdir(parents=True, exist_ok=True)
    vfeat.mkdir(parents=True, exist_ok=True)
    keys = ["dt", "ri", "dt_onset", "a_ratio", "area_ratio", "dt3", "ri3",
            "dt_n2", "ri_n2", "dt_n4", "ri_n4", "dt_sqi5", "ri_sqi5", "dt_sqi20", "ri_sqi20"]
    demo = []
    for i in range(n_cases):
        cid, h = 9000 + i, 160.0 + float(rng.normal(0, 8))
        demo.append({"caseid": cid, "height": h})
        t0 = np.arange(n_win) * 60.0
        dt = np.clip(0.20 + 0.02 * rng.standard_normal(n_win), 0.08, 0.4)
        ri = np.clip(0.5 + 0.1 * rng.standard_normal(n_win), 0.05, 1.5)
        m = pd.DataFrame({"t0": t0, "pwtt": 0.25 + 0.01 * rng.standard_normal(n_win),
                          "si": (h / 100) / dt, "ri": ri,
                          "hr": 70 + 8 * rng.standard_normal(n_win),
                          "map": 80 + 10 * rng.standard_normal(n_win),
                          "co_ref": np.clip(5 + 0.3 * rng.standard_normal(n_win), 2, 9)})
        m.to_csv(feat / f"case_{cid}.csv", index=False)
        v = {"t0": t0}
        v["dt"] = dt * 1.05                     # 再当てはめは主解析と少し違う
        v["ri"] = ri * 2.0                      # 主解析 ri と明確に区別できる値
        v["dt_onset"], v["a_ratio"], v["area_ratio"] = v["dt"] * 0.9, ri * 1.1, ri * 1.3
        miss = rng.random(n_win) < 0.3
        v["dt3"], v["ri3"] = np.where(miss, np.nan, v["dt"]), np.where(miss, np.nan, ri)
        for k in ["n2", "n4", "sqi5", "sqi20"]:
            v[f"dt_{k}"], v[f"ri_{k}"] = v["dt"], ri
        if i < 3:                               # 3カーネルが全滅の症例
            v["dt3"], v["ri3"] = np.full(n_win, np.nan), np.full(n_win, np.nan)
        df = pd.DataFrame(v)
        for k in keys:
            df[f"n_{k}"] = df[k].notna().astype(int) * 4
        df.to_csv(vfeat / f"case_{cid}.csv", index=False)
        (vfeat / f"case_{cid}_meta.json").write_text(
            json.dumps({"v": 1, "caseid": cid, "n_windows": n_win}), encoding="utf-8")
    pd.DataFrame(demo).to_csv(data / "cases.csv", index=False, encoding="utf-8-sig")


def selftest() -> int:
    import tempfile
    ok = True

    def rep(name, cond, detail=""):
        nonlocal ok
        ok &= bool(cond)
        say(f"  [{'PASS' if cond else 'FAIL'}] {name}{('  ' + detail) if detail else ''}")

    with tempfile.TemporaryDirectory() as td:
        data = Path(td)
        _make_synthetic(data)
        joined, inv = load_joined(data)
        rep("全症例が結合できる", inv["joined"] == 30, f"{inv}")

        cid, j = next(iter(joined.items()))
        m = pd.read_csv(data / "features" / f"case_{cid}.csv")
        v = pd.read_csv(data / "features_variants" / f"case_{cid}.csv")
        rep("結合後の ri は主解析ファイルの ri", np.allclose(j["ri"], m["ri"]))
        rep("結合後の ri_rep は変種ファイルの ri（列名衝突なし）",
            np.allclose(j["ri_rep"], v["ri"]) and not np.allclose(j["ri_rep"], m["ri"]))

        c_main = build_cases(joined, "si", "ri")
        c_rep = build_cases(joined, "dt_rep", "ri_rep")
        rep("参照行の SI は主解析の si をそのまま使う",
            np.allclose(c_main[0]["windows"]["si"], m["si"]))
        rep("再現行の RI は変種の ri を使う",
            np.allclose(c_rep[0]["windows"]["ri"], v["ri"]))
        rep("再現行の SI は 身長/変種ΔT",
            np.allclose(c_rep[0]["windows"]["si"], j.attrs["height_m"] / v["dt"]))

        c_3k = build_cases(joined, "dt3", "ri3")
        rep("3カーネルが全滅の症例は落ちる", len(c_3k) == 27, f"{len(c_3k)} 症例")

        out_csv = data / "variants_table.csv"
        df = run(joined, out_csv)
        rep("表が全変種ぶん書き出される", out_csv.exists() and len(df) == len(VARIANTS))
        pt = premise_test(c_main, with_map=False)
        rep("参照行の r² は src.models の直接計算と一致",
            abs(float(df.loc[0, "r2_vasc"]) - pt["r2_vasc"]) < 1e-12)
    say("ALL PASS" if ok else "FAILED")
    return 0 if ok else 1


# ---------------------------------------------------------------- 入口
def main() -> None:
    faulthandler.enable()
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--check", action="store_true", help="データの点検だけ行い集計しない")
    ap.add_argument("--selftest", action="store_true", help="合成データで配管を検算する")
    ap.add_argument("--out", type=Path, default=DATA / "variants_table.csv",
                    help="表の書き出し先（既定: data/variants_table.csv）")
    args = ap.parse_args()
    if args.selftest:
        sys.exit(selftest())

    say("変種キャッシュを読み込み中 …")
    joined, inv = load_joined(DATA)
    check(joined, inv)
    if args.check:
        return
    if len(joined) < MIN_CASES:
        say("11_variants_extract.py の完走後に実行してください。")
        return
    run(joined, args.out)


if __name__ == "__main__":
    main()
