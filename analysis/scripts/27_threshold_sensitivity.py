#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""研究0 事前指定: PDA第2版の結論が閾値の選び方に依存しないかを確かめる。

なぜ要るのか
------------
`src/pda2.py` の閾値には3つの層がある。

  (a) 文献から借りたもの   Errx<6ms・Erry<0.01・NRMSE<2%（Wang 2013）、
                          低域通過 18 Hz（Tigges 2017・Couceiro 2015）
  (b) 自分のデータで理由づけたもの
                          ΔT の標準誤差の上限 20 ms（研究1の症例内 ΔPWTT の
                          標準偏差 18 ms より大きい誤差の拍は問いに寄与しない）
  (c) **根拠なく私が決めたもの**
                          鍵点の重み 20（Wang は 1〜100 を探索、その中間を取っただけ）、
                          成分間隔の下限 30 ms、貯留槽の窓 0.62T、立ち上がりの次数 2、
                          貯留槽カーネルの判定 0.60T、境界近傍の許容 0.1%、
                          一意性の検査 1.15 / 0.20

(c) が結論を左右するなら、その結論は閾値の産物である。**26番を実行する前に**
この台本を書き、振れ幅を固定しておく。結果を見てから閾値をいじれば、それは
もはや検証ではない（研究0 の第一報で、ランドマーク法を走らせる前に撤退方針を
書いてしまった失敗と同じ構図になる）。

二層に分ける
------------
  **後づけ層**（当てはめ直し不要・数秒）
      NRMSE・Errx・Erry・ΔTのSE・一意性の検査。これらは当てはめの**後**に効く
      規準なので、26番が保存した診断量から採否を再計算するだけでよい。
  **当てはめ層**（当てはめ直しが要る・部分集合で実施）
      鍵点の重み・低域通過・成分間隔の下限・成分を増やすか。これらは当てはめ
      そのものを変えるので回し直す。全例では時間がかかるので、**被験者番号を
      7 で割った余りが 0** の集団（約 625 名、年齢層は均等に入る）に固定する。

判定は 20番・23番・26番と同一（年齢層内 Spearman ρ が全層で予測の向き、かつ
中央値 |ρ| ≥ 0.30）。

使い方
------
    python3 scripts/27_threshold_sensitivity.py
        後づけ層のみ（data/pwdb/pwdb_compare.csv が要る。数秒）
    python3 scripts/27_threshold_sensitivity.py --pwdb ~/pwdb --jobs 8
        当てはめ層も回す（部分集合。20〜30分）
    python3 scripts/27_threshold_sensitivity.py --selftest
"""
from __future__ import annotations

import argparse
import importlib.util
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src import pda2                                    # noqa: E402

DATA = ROOT / "data"
OUT = DATA / "pwdb"
INF = float("inf")


def _load(stem: str, name: str):
    p = Path(__file__).resolve().parent / stem
    spec = importlib.util.spec_from_file_location(name, p)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


M = _load("20_pwdb_validity.py", "m20")
C = _load("26_pwdb_compare.py", "m26")

# 凍結値。ここを動かすときは lab_log に理由を書くこと
FROZEN = {"nrmse": pda2.NRMSE_MAX, "errx": pda2.ERRX_MS, "erry": pda2.ERRY,
          "se": pda2.SE_DT_MAX_MS, "amb": True}

# 後づけ層の振れ幅（**26番を実行する前に固定した**）
POST_HOC = [
    ("nrmse", "NRMSE 上限",        [0.010, 0.015, 0.020, 0.030, 0.050, INF]),
    ("errx",  "Errx 上限 [ms]",    [3.0, 6.0, 12.0, 25.0, INF]),
    ("erry",  "Erry 上限",         [0.005, 0.010, 0.020, INF]),
    ("se",    "ΔT の SE 上限 [ms]", [5.0, 10.0, 20.0, 50.0, INF]),
    ("amb",   "一意性の検査",       [True, False]),
]

# 当てはめ層（当てはめ直しが要る）
REFIT = [
    ("凍結値",                    {}),
    ("鍵点の重み 1（重みなし）",   {"w_key": 1.0}),
    ("鍵点の重み 100（Wang 上限）", {"w_key": 100.0}),
    ("低域通過 10 Hz",            {"lowpass_hz": 10.0}),
    ("低域通過 25 Hz",            {"lowpass_hz": 25.0}),
    ("成分間隔の下限 15 ms",       {"min_gap": 0.015}),
    ("成分間隔の下限 60 ms",       {"min_gap": 0.060}),
    ("成分を増やさない",           {"escalate": False}),
    # --- Basso 2024 / Tigges 2017 / Goswami 2010 を読んで 26番の実行前に追加 ---
    ("40 Hz へ落として当てはめ",   {"resample_hz": 40.0}),
    ("拍の 0〜0.9T だけ当てはめ",  {"fit_frac": 0.9}),
    ("歪みの下限 −8（左歪みも許す）", {"alpha_min": -8.0}),
]

ROUTES = [("v2", "第2版 二段(歪みガウス)"), ("v2g", "第2版 ガンマ3")]
TARGETS = [("dt", "PWV_a", -1, "ΔT × 大動脈PWV"), ("ri", "pvr", +1, "RI × 末梢血管抵抗")]
SUBSET_MOD = 7          # 当てはめ層で使う部分集合（subj_no % 7 == 0）


# ---------------------------------------------------------------- 後づけ層
def recompute_ok(d, tag: str, th: dict):
    """保存された診断量から採否を作り直す。26番の判定と同じ論理でなければならない。"""
    g = lambda c: d[c].to_numpy(float) if c in d else np.full(len(d), np.nan)  # noqa: E731
    nrmse, errx = g(f"nrmse_{tag}"), g(f"errx_{tag}_ms")
    erry, nlm = g(f"erry_{tag}"), g(f"nlm_{tag}")
    se, amb = g(f"dtse_{tag}_ms"), g(f"amb_{tag}")
    noref = g(f"noref_{tag}")
    ok = ((nrmse <= th["nrmse"]) & (errx <= th["errx"]) & (erry <= th["erry"])
          & (nlm >= 2) & np.isfinite(se) & (se <= th["se"]) & (noref != 1))
    if th["amb"]:
        ok = ok & (amb != 1)
    return ok.astype(int)


def _verdicts(d, tag: str, ok):
    """ある採否のもとでの、ΔT・RI の判定を返す。"""
    src = d[ok == 1]
    out = {}
    for key, tgt, sign, _lab in TARGETS:
        col = f"{key}_{tag}_ms" if key == "dt" else f"{key}_{tag}"
        out[key] = C._judge_or_none(src, col, tgt, sign)
    return out, int(ok.sum())


def _fmt(j):
    if not j:
        return f"{'—':>9}{'—':>8}"
    return f"{j['med_abs']:>9.3f}{('成立' if j['pass'] else '不成立'):>8}"


def post_hoc(d, out_dir: Path | None = None) -> dict:
    n = len(d)
    print(f"\n{'=' * 78}\n閾値感度解析 A: 当てはめ後に効く規準（当てはめ直し不要）\n{'=' * 78}")
    print(f"\n被験者 {n} 名。**26番を実行する前に振れ幅を固定してある。**")
    print(f"判定規準は 20・23・26番と同一（全層で予測の向き、中央値 |ρ| ≥ {M.CRIT_RHO}）")

    rows = {}
    for tag, rlab in ROUTES:
        if f"nrmse_{tag}" not in d:
            print(f"\n（{rlab}: 診断量が保存されていない。26番を新しい版で回し直すこと）")
            continue
        base = recompute_ok(d, tag, FROZEN)
        stored = d.get(f"ok_{tag}")
        agree = (np.mean(base == stored.to_numpy(int)) if stored is not None else np.nan)
        print(f"\n{'-' * 78}\n{rlab}\n{'-' * 78}")
        print(f"  再計算した採否が 26番の保存値と一致する割合: {agree:.4%}")
        if np.isfinite(agree) and agree < 0.999:
            print("  **一致しない。この表は信用してはいけない。26番と論理がずれている。**")
        print(f"{'規準':<22}{'値':>10}{'採択率':>9}"
              f"{'ΔT×PWV |ρ|':>12}{'判定':>8}{'RI×pvr |ρ|':>12}{'判定':>8}")
        v0, n0 = _verdicts(d, tag, base)
        print(f"{'（凍結値）':<22}{'—':>10}{n0 / max(n, 1):>9.1%}"
              f"{_fmt(v0['dt'])}{_fmt(v0['ri'])}")
        rows[(tag, "frozen", None)] = (n0, v0)
        for key, lab, vals in POST_HOC:
            for v in vals:
                th = dict(FROZEN); th[key] = v
                if th == FROZEN:
                    continue
                ok = recompute_ok(d, tag, th)
                vv, nn = _verdicts(d, tag, ok)
                sv = ("あり" if v else "なし") if key == "amb" else (
                    "∞" if v == INF else f"{v:g}")
                print(f"{lab:<22}{sv:>10}{nn / max(n, 1):>9.1%}"
                      f"{_fmt(vv['dt'])}{_fmt(vv['ri'])}")
                rows[(tag, key, v)] = (nn, vv)
        # すべて外した場合。26番の C ブロック（採否を完全に無視）とは一点だけ違い、
        # **共分散が計算できなかった拍は落とす**。標準誤差が出せない＝母数が本当に
        # 同定できていない、という意味なので、規準を外しても残すべきではない。
        allth = {"nrmse": INF, "errx": INF, "erry": INF, "se": INF, "amb": False}
        ok = recompute_ok(d, tag, allth)
        vv, nn = _verdicts(d, tag, ok)
        print(f"{'すべて外す(SE可算のみ)':<22}{'—':>10}{nn / max(n, 1):>9.1%}"
              f"{_fmt(vv['dt'])}{_fmt(vv['ri'])}")
        rows[(tag, "none", None)] = (nn, vv)

        # 判定が一つでも割れたか
        vs = {k: v for k, v in rows.items() if k[0] == tag}
        for key, _tgt, _sg, lab in TARGETS:
            js = [j[1][key] for j in vs.values() if j[1][key]]
            if not js:
                continue
            ps = {bool(j["pass"]) for j in js}
            print(f"  {lab}: 判定は" + ("**閾値によって割れる**" if len(ps) > 1
                                        else f"どの閾値でも {'成立' if ps.pop() else '不成立'}"))
    print(f"\n{'-' * 78}\n読み方\n{'-' * 78}")
    print("  どの閾値でも同じ判定 → 結論は閾値の産物ではない。")
    print("  閾値によって割れる     → その閾値が結論を作っている。論文には割れる範囲を書く。")
    print("  「すべて外す」の行が凍結値と違う → 採否そのものが選択になっている。")
    print("    この行は共分散が計算できた拍のみ。26番の C ブロックとは分母が少し違う。")
    if out_dir is not None:
        Path(out_dir).mkdir(parents=True, exist_ok=True)
    return rows


# ---------------------------------------------------------------- 当てはめ層
def _one(args_tuple):
    subj, row, hr, opts = args_tuple
    out = {"subj_no": subj, "ok": 0}
    try:
        y, fs = M.beat_of(row, hr)
        if y is None:
            return out
        t = np.arange(y.size) / fs
        r = pda2.decompose(t, y, fs, route=opts.pop("route", "two_stage"), **opts)
        out.update(ok=int(bool(r.get("ok"))), dt_ms=r.get("dt_ms", np.nan),
                   ri=r.get("ri", np.nan), nrmse=r.get("nrmse", np.nan))
        return out
    except Exception:
        return out


def refit(root: Path, jobs: int = 1, route: str = "two_stage", out_dir=None) -> dict:
    """当てはめそのものを変える閾値を、固定した部分集合で回し直す。"""
    import pandas as pd
    hae, cfg, ppg, _ = M.load_pwdb(Path(root).expanduser())
    keep = ppg.iloc[:, 0].astype(int) % SUBSET_MOD == 0
    ppg = ppg[keep]
    hr_by = dict(zip(hae["subj_no"].astype(int), hae["HR"].astype(float)))
    base = [(int(ppg.iloc[i, 0]), ppg.iloc[i].to_numpy(float),
             hr_by.get(int(ppg.iloc[i, 0]), np.nan)) for i in range(len(ppg))]
    truth = hae.merge(cfg[["subj_no", "pvr"]], on="subj_no", how="left")
    print(f"\n{'=' * 78}\n閾値感度解析 B: 当てはめ自体を変える規準（部分集合 {len(base)} 名）\n{'=' * 78}")
    print(f"  部分集合は subj_no %% {SUBSET_MOD} == 0 に固定（結果を見て選び直さない）")
    print(f"  経路: {route}")
    print(f"\n{'条件':<26}{'採択率':>9}{'ΔT中央値[ms]':>14}"
          f"{'ΔT×PWV |ρ|':>12}{'判定':>8}{'RI×pvr |ρ|':>12}{'判定':>8}")
    rows = {}
    for lab, opts in REFIT:
        work = [(s, r, h, dict(opts, route=route)) for s, r, h in base]
        if jobs > 1:
            from concurrent.futures import ProcessPoolExecutor
            with ProcessPoolExecutor(max_workers=jobs) as ex:
                res = list(ex.map(_one, work, chunksize=8))
        else:
            res = [_one(x) for x in work]
        d = truth.merge(pd.DataFrame(res), on="subj_no", how="inner")
        go = d[d["ok"] == 1]
        jd = C._judge_or_none(go, "dt_ms", "PWV_a", -1)
        jr = C._judge_or_none(go, "ri", "pvr", +1)
        dtm = f"{float(np.nanmedian(go['dt_ms'])):.0f}" if len(go) else "—"
        print(f"{lab:<26}{d['ok'].mean():>9.1%}{dtm:>14}{_fmt(jd)}{_fmt(jr)}", flush=True)
        rows[lab] = (float(d["ok"].mean()), jd, jr)
    ps = {bool(j["pass"]) for _r, j, _q in rows.values() if j}
    print("\n  ΔT × 大動脈PWV: 判定は" + ("**条件によって割れる**" if len(ps) > 1
                                        else f"どの条件でも {'成立' if ps.pop() else '不成立'}"
                                        if ps else "判定できず"))
    if out_dir is not None:
        Path(out_dir).mkdir(parents=True, exist_ok=True)
    return rows


# ---------------------------------------------------------------- 自己検証
def selftest() -> int:
    import tempfile
    import pandas as pd
    print("== 27_threshold_sensitivity 自己検証（模擬データ・ネットワーク不要） ==\n")
    ok = True

    def rep(name, cond, detail=""):
        nonlocal ok
        ok &= bool(cond)
        print(f"  [{'PASS' if cond else 'FAIL'}] {name}{('  ' + detail) if detail else ''}",
              flush=True)

    rng = np.random.default_rng(0)
    n = 240
    ages = np.array([25, 35, 45, 55, 65, 75])[np.arange(n) % 6]
    pwv = 5.0 + 0.09 * (ages - 25) + rng.uniform(-0.5, 0.5, n)
    pvr = rng.uniform(0.8, 2.2, n) * 1e8
    # 当てはまりの良い拍ほど真の関係が強い、という構造をわざと仕込む
    q = rng.uniform(0, 1, n)
    d = pd.DataFrame({
        "subj_no": np.arange(1, n + 1), "age": ages, "PWV_a": pwv, "pvr": pvr,
        "dt_v2_ms": 420 - 22 * pwv + 40 * q * rng.standard_normal(n),
        "ri_v2": 0.20 + 0.28 * (pvr / 1e8 - 0.8) / 1.4 + 0.30 * q * rng.standard_normal(n),
        "nrmse_v2": 0.004 + 0.05 * q, "errx_v2_ms": 1.0 + 30.0 * q,
        "erry_v2": 0.002 + 0.03 * q, "nlm_v2": 3, "dtse_v2_ms": 0.3 + 60.0 * q,
        "amb_v2": (q > 0.9).astype(int), "noref_v2": 0,
    })
    d["ok_v2"] = recompute_ok(d, "v2", FROZEN)
    rep("採否を診断量から作り直せる", d["ok_v2"].sum() > 20, f"採択 {int(d['ok_v2'].sum())}/{n}")

    rows = post_hoc(d, out_dir=None)
    rep("凍結値の行が出た", ("v2", "frozen", None) in rows)
    n_fro = rows[("v2", "frozen", None)][0]
    n_none = rows[("v2", "none", None)][0]
    rep("規準をすべて外すと採択が増える", n_none > n_fro, f"{n_fro} → {n_none}")
    n_tight = rows[("v2", "nrmse", 0.010)][0]
    rep("NRMSE を厳しくすると採択が減る", n_tight < n_fro, f"{n_fro} → {n_tight}")
    j_fro = rows[("v2", "frozen", None)][1]["dt"]
    j_none = rows[("v2", "none", None)][1]["dt"]
    rep("仕込んだ「当てはまりが良い拍ほど関係が強い」を検出できる",
        bool(j_fro and j_none and j_fro["med_abs"] > j_none["med_abs"]),
        f"凍結 {j_fro['med_abs']:.3f} 対 すべて外す {j_none['med_abs']:.3f}"
        if j_fro and j_none else "判定できず")
    rep("判定規準を 20・26番と共有している", M.CRIT_RHO == 0.30 and C.MIN_PER_AGE == 8)
    rep("凍結値が pda2 の定数と一致している",
        FROZEN["nrmse"] == pda2.NRMSE_MAX and FROZEN["errx"] == pda2.ERRX_MS
        and FROZEN["erry"] == pda2.ERRY and FROZEN["se"] == pda2.SE_DT_MAX_MS)

    # 当てはめ層が decompose に閾値を渡せること（1拍だけ）
    with tempfile.TemporaryDirectory() as _td:
        t = np.arange(0, 0.857, 1 / 500.0)
        y = (np.exp(-0.5 * ((t - 0.12) / 0.045) ** 2)
             + 0.45 * np.exp(-0.5 * ((t - 0.40) / 0.065) ** 2))
        r1 = pda2.decompose(t, y, 500.0, route="two_stage", escalate=False)
        r2 = pda2.decompose(t, y, 500.0, route="two_stage", escalate=False,
                            lowpass_hz=10.0, min_gap=0.06, w_key=1.0)
        rep("当てはめ層の引数が decompose に届いている（結果が変わる）",
            np.isfinite(r1.get("dt_ms", np.nan)) and np.isfinite(r2.get("dt_ms", np.nan))
            and abs(r1["dt_ms"] - r2["dt_ms"]) > 1e-9,
            f"{r1['dt_ms']:.1f} 対 {r2['dt_ms']:.1f} ms")
        r3 = pda2.decompose(t, y, 500.0, route="two_stage", escalate=False,
                            nrmse_max=INF, errx_ms=INF, erry_max=INF, se_dt_max_ms=INF)
        rep("採否の閾値も decompose に届いている", bool(r3.get("ok")))
    print("\n" + ("ALL PASS" if ok else "FAIL あり"))
    return 0 if ok else 1


# ---------------------------------------------------------------- main
def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--csv", type=str, default=str(OUT / "pwdb_compare.csv"),
                    help="26番の出力")
    ap.add_argument("--pwdb", type=str, help="指定すると当てはめ層も回す")
    ap.add_argument("--route", type=str, default="two_stage",
                    choices=["two_stage", "gamma3"])
    ap.add_argument("--jobs", type=int, default=1)
    ap.add_argument("--selftest", action="store_true")
    args = ap.parse_args()
    if args.selftest:
        sys.exit(selftest())

    import pandas as pd
    p = Path(args.csv).expanduser()
    if not p.exists():
        raise FileNotFoundError(
            f"{p} がありません。先に 26番を実行してください:\n"
            "    python3 scripts/26_pwdb_compare.py --pwdb ~/pwdb --jobs 8")
    post_hoc(pd.read_csv(p), out_dir=OUT)
    if args.pwdb:
        refit(Path(args.pwdb), jobs=args.jobs, route=args.route, out_dir=OUT)


if __name__ == "__main__":
    main()
