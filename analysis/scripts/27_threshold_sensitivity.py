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
                          成分間隔の下限 30 ms、一意性の検査の残差許容 1.15
                          （肩の顕著さ 5% と max_nfev 1200 は数値的な守りとして 26番で監視する）

(c) が結論を左右するなら、その結論は閾値の産物である。**26番を実行する前に**
この台本を書き、振れ幅を固定しておく。結果を見てから閾値をいじれば、それは
もはや検証ではない（研究0 の第一報で、ランドマーク法を走らせる前に撤退方針を
書いてしまった失敗と同じ構図になる）。

二層に分ける
------------
  **後づけ層**（当てはめ直し不要・数秒）
      NRMSE・Errx・Erry・ΔTのSE・一意性の検査。これらは当てはめの**後**に効く
      規準なので、26番が保存した診断量から採否を再計算するだけでよい。
      ただし一点だけ限界がある。26番は規準を満たさない拍で成分を増やしており、
      保存されている診断量は**最終解**のもの。閾値を緩めれば増やさずに済んだ拍、
      厳しくすれば増やして通った拍があり得るが、後づけ層はそれを再現できない。
      成分を増やすことの影響そのものは当てはめ層の「成分を増やさない」で見る。
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
        当てはめ層も回す（歪みガウス経路。部分集合。20〜30分）
    python3 scripts/27_threshold_sensitivity.py --pwdb ~/pwdb --jobs 8 --route gamma
        ガンマ経路の当てはめ層
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
# amb_tol は曖昧判定に使う ΔT の許容 [ms]（競合解の広がりの上限・反射波の僅差の下限）。
# pda2 では SE の上限と同じ値（根拠が同じ）
FROZEN = {"nrmse": pda2.NRMSE_MAX, "errx": pda2.ERRX_MS, "erry": pda2.ERRY,
          "se": pda2.SE_DT_MAX_MS, "amb": True, "amb_tol": pda2.SE_DT_MAX_MS,
          "proxy": False}      # 型3（代用点）を採用に含めない（pda2.decompose の既定）

# 後づけ層の振れ幅（**26番を実行する前に固定した**）
POST_HOC = [
    ("nrmse", "NRMSE 上限",        [0.010, 0.015, 0.020, 0.030, 0.050, INF]),
    ("errx",  "Errx 上限 [ms]",    [3.0, 6.0, 12.0, 25.0, INF]),
    ("erry",  "Erry 上限",         [0.005, 0.010, 0.020, INF]),
    ("se",    "ΔT の SE 上限 [ms]", [5.0, 10.0, 20.0, 50.0, INF]),
    # 「なし」は曖昧判定を**すべて**外す（競合解の広がり・前進波のスロット・反射波の僅差の3つ）
    ("amb",   "曖昧判定（3種まとめて）", [True, False]),
    # pda2 は同じ 20 ms を SE の上限・競合解の広がりの上限・反射波の僅差の下限の 3 か所に使う
    # （根拠が同じ）。その値そのものを 3 か所まとめて動かす。∞ は僅差の下限として無意味
    # （すべて僅差になる）ので入れない。SE だけ ∞ は上の行にある
    ("joint", "同じ値を 3 か所まとめて [ms]", [5.0, 10.0, 20.0, 50.0]),
    # 型3（切痕なし・肩の代用点）は分解が同定できないので既定では採用しない。含めたときに
    # 結論が変わらないかを見る（合成波では含めると ΔT が +23 ms ずれた拍が通った）
    ("proxy", "型3（代用点）を採用に含める", [False, True]),
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
    # 0.9T に切ると鍵点の窓（0.65T・0.85T）と幅の尺度も 0.9 倍になる（T が短くなるため）。
    # 生理的な窓の余裕（切痕 ≤ 0.585T・拡張期ピーク ≤ 0.765T）は残るので条件として成り立つ
    ("拍の 0〜0.9T だけ当てはめ",  {"fit_frac": 0.9}),
    ("歪みの下限 −8（左歪みも許す）", {"alpha_min": -8.0}),
    # --- 6巡目: 根拠なく決めた 3 つ目の閾値（競合解とみなす残差の許容）も当てはめ層で振る
    ("一意性の残差許容 1.05",      {"tol_cost": 1.05}),
    ("一意性の残差許容 1.5",       {"tol_cost": 1.5}),
]

ROUTES = [("v2", "第2版 歪みガウス"), ("v2g", "第2版 ガンマ")]
TARGETS = [("dt", "PWV_a", -1, "ΔT × 大動脈PWV"), ("ri", "pvr", +1, "RI × 末梢血管抵抗")]
SUBSET_MOD = 7          # 当てはめ層で使う部分集合（subj_no % 7 == 0）


def _check_version(d) -> None:
    """26番の CSV に記録された pda2 の版が現在と違えば止める（E8）。"""
    if "pda2_version" in d:
        v_csv = str(d["pda2_version"].iloc[0])
        v_now = pda2.code_version()
        if v_csv != v_now:
            raise SystemExit(
                f"pwdb_compare.csv は pda2 版 {v_csv} で作られたが、現在の pda2 は {v_now} です。\n"
                "分解のコードが変わっています。先に 26番を回し直してください:\n"
                "    python3 scripts/26_pwdb_compare.py --pwdb ~/pwdb --jobs 8")
        print(f"  pda2 版 {v_now}（CSV と一致）")
    else:
        print("  （CSV に pda2 版の記録がない。古い 26番の出力の可能性がある）")


# ---------------------------------------------------------------- 後づけ層
def recompute_amb(d, tag: str, tol_ms: float):
    """保存された材料（競合解の ΔT の広がり・反射波の僅差・前進波のスロット）から曖昧判定を
    作り直す。`pda2.decompose` の `_amb_of` と同じ論理でなければならない（27番の自己検証が
    26番の実出力で 100% 一致を検算する）。材料の列が無い古い CSV では保存値をそのまま使う。
    """
    g = lambda c: d[c].to_numpy(float) if c in d else None  # noqa: E731
    sp, marg, fwd0 = g(f"dtsp_{tag}_ms"), g(f"marg_{tag}_ms"), g(f"fwd0_{tag}")
    if sp is None or marg is None or fwd0 is None:
        stored = g(f"amb_{tag}")
        return (stored == 1) if stored is not None else np.zeros(len(d), bool)
    with np.errstate(invalid="ignore"):
        # 広がりが inf（対応づけが潰れた）や nan（反射波なし）は曖昧。僅差は有限のときだけ効く
        amb = (~np.isfinite(sp)) | (sp > tol_ms) | (np.isfinite(marg) & (marg < tol_ms)) | (fwd0 != 1)
    return amb


def recompute_ok(d, tag: str, th: dict):
    """保存された診断量から採否を作り直す。26番の判定と同じ論理でなければならない。"""
    g = lambda c: d[c].to_numpy(float) if c in d else np.full(len(d), np.nan)  # noqa: E731
    nrmse, errx = g(f"nrmse_{tag}"), g(f"errx_{tag}_ms")
    erry, nlm = g(f"erry_{tag}"), g(f"nlm_{tag}")
    se = g(f"dtse_{tag}_ms")
    noref = g(f"noref_{tag}")
    klass = g(f"klass_{tag}")
    ok = ((nrmse <= th["nrmse"]) & (errx <= th["errx"]) & (erry <= th["erry"])
          & (nlm >= 2) & np.isfinite(se) & (se <= th["se"]) & (noref != 1))
    if not th.get("proxy", False):
        ok = ok & (klass != 3)
    if th["amb"]:
        ok = ok & ~recompute_amb(d, tag, th.get("amb_tol", pda2.SE_DT_MAX_MS))
    return ok.astype(int)


def _verdicts(d, tag: str, ok):
    """ある採否のもとでの、ΔT・RI の判定を返す。"""
    src = d[ok == 1]
    out = {}
    for key, tgt, sign, _lab in TARGETS:
        col = f"{key}_{tag}_ms" if key == "dt" else f"{key}_{tag}"
        out[key] = C._judge_or_none(src, col, tgt, sign)
    return out, int(ok.sum())


N_AGES_FULL = 6          # PWDB の年齢層（25〜75 の 10 歳刻み）。post_hoc は CSV の実数で上書きする


def _fmt(j, n_full: int = None):
    """中央値 |ρ| と判定。**層が揃っていなければ * を付ける**（26番と同じ規則）。

    判定は「有限の ρ を持つ層すべてで予測の向き」なので、採択率が低くて層が減った条件ほど
    通りやすい。閾値を厳しくすると層が減るので、この感度解析ではとくに効いてくる。
    """
    if n_full is None:
        n_full = N_AGES_FULL
    if not j:
        return f"{'—':>9}{'—':>8}"
    v = "成立" if j["pass"] else "不成立"
    if j["n_ages"] < n_full:
        v += "*"
    return f"{j['med_abs']:>9.3f}{v:>8}"


def post_hoc(d, out_dir: Path | None = None) -> dict:
    global N_AGES_FULL
    n = len(d)
    if "age" in d and d["age"].notna().any():
        N_AGES_FULL = int(d["age"].nunique())     # --limit で層が欠けた CSV でも * の基準を実データに合わせる
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
                th = dict(FROZEN)
                if key == "joint":
                    th["se"] = v; th["amb_tol"] = v
                else:
                    th[key] = v
                if th == FROZEN:
                    continue
                ok = recompute_ok(d, tag, th)
                vv, nn = _verdicts(d, tag, ok)
                sv = (("あり" if v else "なし") if key == "amb" else
                      ("含める" if v else "含めない") if key == "proxy" else
                      ("∞" if v == INF else f"{v:g}"))
                print(f"{lab:<22}{sv:>10}{nn / max(n, 1):>9.1%}"
                      f"{_fmt(vv['dt'])}{_fmt(vv['ri'])}")
                rows[(tag, key, v)] = (nn, vv)
        # すべて外した場合。26番の C ブロック（採否を完全に無視）とは一点だけ違い、
        # **共分散が計算できなかった拍は落とす**。標準誤差が出せない＝母数が本当に
        # 同定できていない、という意味なので、規準を外しても残すべきではない。
        allth = {"nrmse": INF, "errx": INF, "erry": INF, "se": INF, "amb": False,
                 "amb_tol": FROZEN["amb_tol"], "proxy": True}
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
            n_short = sum(1 for j in js if j["n_ages"] < N_AGES_FULL)
            if n_short:
                print(f"    （うち {n_short}/{len(js)} 条件は層不足 * ── 層が減ると通りやすくなる）")
    print(f"\n{'-' * 78}\n読み方\n{'-' * 78}")
    print("  どの閾値でも同じ判定 → 結論は閾値の産物ではない。")
    print("  閾値によって割れる     → その閾値が結論を作っている。論文には割れる範囲を書く。")
    print("  「すべて外す」の行が凍結値と違う → 採否そのものが選択になっている。")
    print("    この行は共分散が計算できた拍のみ。26番の C ブロックとは分母が少し違う。")
    print("  限界: 保存されている診断量は最終解（規準を満たさず成分を増やした拍ではその 3 波）のもの。")
    print("    閾値を変えたときに増やすかどうかまでは再現しない。それは B 層の「成分を増やさない」で見る。")
    if out_dir is not None:
        Path(out_dir).mkdir(parents=True, exist_ok=True)
    return rows


# ---------------------------------------------------------------- 当てはめ層
def _one(args_tuple):
    subj, row, hr, opts = args_tuple
    out = {"subj_no": subj, "ok": 0, "why": ""}
    try:
        y, fs = M.beat_of(row, hr)
        if y is None:
            out["why"] = "no_beat"
            return out
        t = np.arange(y.size) / fs
        r = pda2.decompose(t, y, fs, route=opts.pop("route", "skew"), **opts)
        out.update(ok=int(bool(r.get("ok"))), dt_ms=r.get("dt_ms", np.nan),
                   ri=r.get("ri", np.nan), nrmse=r.get("nrmse", np.nan),
                   why=str(r.get("reason", "")), klass=r.get("klass", np.nan),
                   n_waves=r.get("n_waves", np.nan))
        return out
    except Exception as e:                      # noqa: BLE001
        out["why"] = ("EXC:" + str(e))[:40]
        return out


def _refit_csv_name(route: str, lab: str) -> str:
    """条件ごとの CSV 名。ラベルの英数字以外を _ にする（条件間で衝突しないことを自己検証で確かめる）。"""
    safe = "".join(c if c.isalnum() else "_" for c in lab)[:32]
    return f"refit_{route}_{safe}.csv"


def refit(root: Path, jobs: int = 1, route: str = "skew", out_dir=None,
          conditions=None) -> dict:
    """当てはめそのものを変える閾値を、固定した部分集合で回し直す。

    conditions は REFIT の部分列（自己検証が短く回すために使う）。既定は REFIT 全部。
    """
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
    if out_dir is not None:
        Path(out_dir).mkdir(parents=True, exist_ok=True)
    rows = {}
    for lab, opts in (REFIT if conditions is None else conditions):
        work = [(s, r, h, dict(opts, route=route)) for s, r, h in base]
        if jobs > 1:
            from concurrent.futures import ProcessPoolExecutor
            with ProcessPoolExecutor(max_workers=jobs) as ex:
                res = list(ex.map(_one, work, chunksize=8))
        else:
            res = [_one(x) for x in work]
        d = truth.merge(pd.DataFrame(res), on="subj_no", how="inner")
        if out_dir is not None:                 # 驚く結果が出たときに中身を見られるように残す
            od = Path(out_dir); od.mkdir(parents=True, exist_ok=True)
            d.to_csv(od / _refit_csv_name(route, lab), index=False)
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
        # 曖昧判定の材料。q > 0.9 の拍だけ競合解の広がりが 20 ms を超えるようにする
        "dtsp_v2_ms": np.where(q > 0.9, 30.0, 2.0), "marg_v2_ms": INF, "fwd0_v2": 1,
        # 10 名に 1 名を型3 にして「含める」の行が動くようにする（当てはまりとは独立に割り当てる。
        # 当てはまりの悪い拍だけを型3 にすると、含めても他の規準で落ちて行が空振りになる）
        "klass_v2": np.where(np.arange(n) % 10 == 0, 3, 1),
    })
    d["ok_v2"] = recompute_ok(d, "v2", FROZEN)
    rep("採否を診断量から作り直せる", d["ok_v2"].sum() > 20, f"採択 {int(d['ok_v2'].sum())}/{n}")

    rows = post_hoc(d, out_dir=None)
    rep("凍結値の行が出た", ("v2", "frozen", None) in rows)
    rep("層不足の判定に * が付く（H1: B 層も同じ規則）",
        _fmt({"pass": True, "n_ages": 2, "med_abs": 0.9}, 6).endswith("成立*")
        and _fmt({"pass": True, "n_ages": 6, "med_abs": 0.9}, 6).endswith("成立")
        and not _fmt({"pass": True, "n_ages": 6, "med_abs": 0.9}, 6).endswith("*"))
    stale = pd.DataFrame({"pda2_version": ["000000000000"]})
    try:
        _check_version(stale)
        stopped = False
    except SystemExit:
        stopped = True
    rep("pda2 の版が CSV と違えば止まる（E8）", stopped)
    rep("曖昧判定を材料から作り直せる（合成データで保存値と一致）",
        bool(np.all(recompute_amb(d, "v2", FROZEN["amb_tol"]) == (d["amb_v2"].to_numpy(int) == 1))))
    rep("3 か所まとめての行が出た", ("v2", "joint", 5.0) in rows and ("v2", "joint", 50.0) in rows)
    rep("型3 を含める行が出て、含めると採択が増える",
        ("v2", "proxy", True) in rows and rows[("v2", "proxy", True)][0] > rows[("v2", "frozen", None)][0],
        f"{rows[('v2', 'frozen', None)][0]} → {rows.get(('v2', 'proxy', True), (None,))[0]}")
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

    # 26番の自己検証が残した模擬 CSV があれば、採否の再計算が保存値と一致するかを通しで検算する。
    # これが 100% でなければ、A 層の表は 26番と論理がずれており信用できない
    e2e = OUT / "_selftest_pwdb_compare.csv"
    same = False
    if e2e.exists():
        dd = pd.read_csv(e2e)
        agree = []
        for tag in ("v2", "v2g"):
            if f"ok_{tag}" in dd and f"nrmse_{tag}" in dd:
                agree.append(float(np.mean(recompute_ok(dd, tag, FROZEN) == dd[f"ok_{tag}"].to_numpy(int))))
        rep("26番の実出力で採否の再計算が保存値と 100% 一致（通し検算）",
            bool(agree) and min(agree) >= 0.999999,
            f"一致率 {[f'{a:.4%}' for a in agree]}" if agree else "列が無い")
        agree_amb = []
        for tag in ("v2", "v2g"):
            if f"amb_{tag}" in dd and f"dtsp_{tag}_ms" in dd:
                agree_amb.append(float(np.mean(recompute_amb(dd, tag, FROZEN["amb_tol"])
                                               == (dd[f"amb_{tag}"].to_numpy(int) == 1))))
        rep("26番の実出力で曖昧判定の再計算が保存値と 100% 一致（材料から作り直せる）",
            bool(agree_amb) and min(agree_amb) >= 0.999999,
            f"一致率 {[f'{a:.4%}' for a in agree_amb]}" if agree_amb else "材料の列が無い")
        n_amb = int(sum(int((dd[f"amb_{t}"] == 1).sum()) for t in ("v2", "v2g") if f"amb_{t}" in dd))
        print(f"      （曖昧と判定された拍 {n_amb} 例を含む。0 なら一致の検算は空振りである）")
        same = ("pda2_version" in dd and str(dd["pda2_version"].iloc[0]) == pda2.code_version())
        rep("26番の出力に pda2 の版が記録され、現在の版と一致する", same,
            f"CSV {dd['pda2_version'].iloc[0] if 'pda2_version' in dd else '—'} / 現在 {pda2.code_version()}")
    else:
        print("  （26番の自己検証の出力が無いので通し検算は省略。先に 26番 --selftest を回すと検算できる）")
    rep("凍結値が pda2 の定数と一致している",
        FROZEN["nrmse"] == pda2.NRMSE_MAX and FROZEN["errx"] == pda2.ERRX_MS
        and FROZEN["erry"] == pda2.ERRY and FROZEN["se"] == pda2.SE_DT_MAX_MS
        and FROZEN["amb_tol"] == pda2.SE_DT_MAX_MS)
    names = [_refit_csv_name("skew", lab) for lab, _o in REFIT]
    rep("B 層の条件ごとの CSV 名が衝突しない", len(set(names)) == len(names))
    rep("B 層の条件に、根拠なく決めた 3 つの閾値（重み・間隔・残差許容）がすべて入っている",
        any("w_key" in o for _l, o in REFIT) and any("min_gap" in o for _l, o in REFIT)
        and any("tol_cost" in o for _l, o in REFIT))

    # 当てはめ層が decompose に閾値を渡せること（1拍だけ）
    with tempfile.TemporaryDirectory() as _td:
        t = np.arange(0, 0.857, 1 / 500.0)
        y = (np.exp(-0.5 * ((t - 0.12) / 0.045) ** 2)
             + 0.45 * np.exp(-0.5 * ((t - 0.40) / 0.065) ** 2))
        r1 = pda2.decompose(t, y, 500.0, route="skew", escalate=False)
        r2 = pda2.decompose(t, y, 500.0, route="skew", escalate=False,
                            lowpass_hz=10.0, min_gap=0.06, w_key=1.0)
        rep("当てはめ層の引数が decompose に届いている（結果が変わる）",
            np.isfinite(r1.get("dt_ms", np.nan)) and np.isfinite(r2.get("dt_ms", np.nan))
            and abs(r1["dt_ms"] - r2["dt_ms"]) > 1e-9,
            f"{r1['dt_ms']:.1f} 対 {r2['dt_ms']:.1f} ms")
        r3 = pda2.decompose(t, y, 500.0, route="skew", escalate=False,
                            nrmse_max=INF, errx_ms=INF, erry_max=INF, se_dt_max_ms=INF)
        rep("採否の閾値も decompose に届いている", bool(r3.get("ok")))
        r4 = pda2.decompose(t, y, 500.0, route="skew", escalate=False, tol_cost=1.5)
        rep("一意性の残差許容 tol_cost が decompose に届いている（結果が返る）",
            np.isfinite(r4.get("dt_ms", np.nan)))

    # --- B 層の通し検算: 26番と同じ模擬 PWDB を作り、部分集合で 2 条件だけ当てはめ直す。
    # 「凍結値」の条件は 26番の自己検証の出力（同じ模擬・同じ版）と ΔT・採否が一致しなければならない。
    # ここがずれていれば、B 層の配管（_one）が 26番の配管（indices_for_subject）と別の前処理をしている
    if e2e.exists() and same:
        with tempfile.TemporaryDirectory() as td:
            root, _kinds = C._selftest_root(Path(td))
            conds = [REFIT[0], ("成分を増やさない", {"escalate": False}),
                     ("歪みの下限 −8（左歪みも許す）", {"alpha_min": -8.0})]
            rows_b = refit(root, jobs=1, route="skew", out_dir=Path(td) / "out", conditions=conds)
            rep("B 層が模擬 PWDB で通しで動く（部分集合・3 条件。歪みの下限 −8 を含む）", len(rows_b) == 3)
            import pandas as pd
            fz_p = Path(td) / "out" / _refit_csv_name("skew", REFIT[0][0])
            fz = pd.read_csv(fz_p) if fz_p.exists() else None
            if fz is not None:
                m_ = fz.merge(dd[["subj_no", "ok_v2", "dt_v2_ms"]], on="subj_no", how="inner")
                same_ok = bool((m_["ok"].astype(int) == m_["ok_v2"].astype(int)).all())
                both = m_[np.isfinite(m_["dt_ms"]) & np.isfinite(m_["dt_v2_ms"])]
                same_dt = bool(np.allclose(both["dt_ms"], both["dt_v2_ms"], atol=1e-6)) if len(both) else True
                rep("B 層の「凍結値」が 26番の同じ被験者と採否・ΔT で一致（配管が同一）",
                    len(m_) > 0 and same_ok and same_dt,
                    f"n={len(m_)} 採否一致 {same_ok} ΔT一致 {same_dt}")
            else:
                rep("B 層が条件ごとの CSV を残す", False)
    else:
        print("  （26番の自己検証の出力が無い／版が違うので B 層の通し検算は省略）")
    print("\n" + ("ALL PASS" if ok else "FAIL あり"))
    return 0 if ok else 1


# ---------------------------------------------------------------- main
def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--csv", type=str, default=str(OUT / "pwdb_compare.csv"),
                    help="26番の出力")
    ap.add_argument("--pwdb", type=str, help="指定すると当てはめ層も回す")
    ap.add_argument("--route", type=str, default="skew",
                    choices=["skew", "gamma"])
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
    d = pd.read_csv(p)
    _check_version(d)
    post_hoc(d, out_dir=OUT)
    if args.pwdb:
        refit(Path(args.pwdb), jobs=args.jobs, route=args.route, out_dir=OUT)


if __name__ == "__main__":
    main()
