#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""【探索】Couceiro 2015 の R1_d は VitalDB で全身血管抵抗と関連するか。血圧とはどうか。

背景
----
研究0（33番・PWDB）で、末梢血管抵抗と事前規準を満たしたのは Couceiro の R1_d だけであった
（0.585・6/6。特徴点法の RI 0.501 を上回る）。規則どおり判定表には採っていない。
一方 37番で、凍結版 PDA の RI は VitalDB で血管抵抗ではなく血圧を追っていた
（逆向きウィンドウで ρ(ΔRI%, ΔSVR%)=+0.031 [−0.023, +0.094] に対し ρ(ΔRI%, ΔMAP%)=+0.075）。

そこで R1_d を実機のモニタ波形で計算し、37番と同じ判別試験にかける。

R1_d の定義（Couceiro 2015）
--------------------------
ガウス 5 本を表 1 の初期値・境界・不等式制約のもとで当てはめ、**第4成分 g₄ の振幅を
g₁+g₂ のピーク値で除す**。第2成分ではなく g₄ を反射波とする点が凍結版と異なる。
実装は 33番の `fit_couceiro` をそのまま呼ぶ（文献条件の再現）。

2群
---
pac      Vigilance（肺動脈カテーテル）5例。features の `co_ref` が熱希釈由来なので
         SVR* = (MAP − CVP)×80/CO を**動脈圧波形と独立**に組める。**n=5 なので記述のみ。**
ev1000   EV1000/SVR を持つ症例。SVR は (MAP−CVP)×80/CO で CO が動脈圧波形由来のため
         構造的に MAP を含む。判別試験（解離ウィンドウ）で除外の判断に使う。

書かないこと
------------
- 「R1_d は血管抵抗の指標である」（pac は n=5、ev1000 は構造的混入）
- roadmap §9・§12 の判定はこの解析で動かさない

使い方
------
    python3 scripts/38_couceiro_svr.py --selftest
    python3 scripts/38_couceiro_svr.py --run --group pac --jobs 4
    python3 scripts/38_couceiro_svr.py --run --group ev1000 --limit 40 --jobs 4
    python3 scripts/38_couceiro_svr.py --stats-only --group pac
"""
from __future__ import annotations

import argparse
import importlib.util
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from src import pda2                                                   # noqa: E402
from src.beats import segment_beats, sqi, ensemble_average             # noqa: E402


def _load(stem: str, name: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / "scripts" / stem)
    m = importlib.util.module_from_spec(spec)
    sys.modules[name] = m
    spec.loader.exec_module(m)
    return m


M33 = _load("33_pwdb_literature_replica.py", "m33_38")
M37 = _load("37_ri_svr_screen.py", "m37_38")
M39 = _load("39_ri_svr_standalone.py", "m39_38")   # 閾値の列と誤差率の式を共有し、食い違わせない

FS, WIN_S, MIN_GOOD = 500.0, 60.0, 8
DATA = ROOT / "data"
FEAT = DATA / "features"
VTONE = DATA / "vasotone"
OUT = DATA / "couceiro"
NAN = float("nan")


# ---------------------------------------------------------------- 1ウィンドウ
def indices_on_beat(y: np.ndarray, fs: float = FS) -> dict:
    """平均拍1拍から R1_d（Couceiro）と、比較用の特徴点RI・早期振幅比を取る。"""
    out = {"ri_cou": NAN, "dt_cou_ms": NAN, "ri_lm": NAN, "amb": NAN}
    t = np.arange(len(y)) / fs
    ys, _amp = pda2.preprocess(t, np.asarray(y, float), fs)
    if ys is None:
        return out
    lm = pda2.find_landmarks(t, ys)
    if lm is not None:
        out["klass"] = int(lm["klass"])
        if lm["klass"] in (1, 3) and np.isfinite(lm.get("dia_v", NAN)) and lm["sys_v"] > 0:
            out["ri_lm"] = float(lm["dia_v"] / lm["sys_v"])
    try:
        ef = pda2.early_features(t, ys)
        a = float(ef["amb_amp1"])
        out["amb"] = a if np.isfinite(a) and 0.0 < a <= 1.5 else NAN
    except Exception:      # noqa: BLE001
        pass
    try:
        pts = M33.couceiro_points(t, ys, lm)
        r = M33.fit_couceiro(t, ys, lm, pts)
        out["ri_cou"] = float(r.get("ri_cou", NAN))
        out["dt_cou_ms"] = float(r.get("dt_cou_ms", NAN))
    except Exception as e:      # noqa: BLE001
        out["err"] = ("EXC:" + str(e))[:60]
    return out


def _task(args):
    caseid, t0, seg_p, seg_e = args
    rec = {"caseid": int(caseid), "t0": float(t0)}
    try:
        beats = segment_beats(seg_p, FS, ecg=seg_e)
        good = [(s, e) for s, e in beats if sqi(seg_p[s:e], FS)["ok"]]
    except Exception:      # noqa: BLE001
        good = []
    rec["n_good"] = len(good)
    if len(good) < MIN_GOOD:
        return rec
    y = ensemble_average([seg_p[s:e] for s, e in good])
    rec.update(indices_on_beat(y))
    return rec


def case_windows(caseid: int) -> list:
    """研究1 と同じ t0 グリッドで全ウィンドウを切る。features がある t0 に限る。"""
    import vitaldb
    f = FEAT / f"case_{caseid}.csv"
    keep = set(np.round(pd.read_csv(f)["t0"].to_numpy(float), 6)) if f.exists() else None
    wav = vitaldb.load_case(caseid, ["SNUADC/PLETH", "SNUADC/ECG_II"], 1 / FS)
    pleth = np.nan_to_num(np.asarray(wav[:, 0], float))
    ecg = np.nan_to_num(np.asarray(wav[:, 1], float))
    dur = len(pleth) / FS
    tasks = []
    for t0 in np.arange(0, dur - WIN_S, WIN_S):
        if keep is not None and round(float(t0), 6) not in keep:
            continue
        i0, i1 = int(t0 * FS), int((t0 + WIN_S) * FS)
        sp = pleth[i0:i1]
        if sp.size < int(WIN_S * FS) * 0.9 or not np.any(sp):
            continue
        tasks.append((caseid, float(t0), sp, ecg[i0:i1]))
    return tasks


# ---------------------------------------------------------------- 症例の選択
def pick_cases(group: str, limit: int | None) -> list[int]:
    tc = pd.read_csv(DATA / "target_cases.csv")
    if group == "pac":
        ids = sorted(tc.loc[tc.get("Vigilance_CO", False) == True, "caseid"].astype(int))
    else:
        have = {int(p.stem.split("_")[1]) for p in VTONE.glob("case_*.csv")}
        ids = sorted(i for i in tc["caseid"].astype(int) if i in have)
        rng = np.random.default_rng(0)
        ids = sorted(rng.permutation(ids)[:limit].tolist()) if limit else ids
    return [i for i in ids if (FEAT / f"case_{i}.csv").exists()]


def extract(group: str, limit: int | None, jobs: int) -> None:
    from multiprocessing import Pool
    OUT.mkdir(parents=True, exist_ok=True)
    ids = pick_cases(group, limit)
    print(f"対象 {len(ids)} 例: {ids}")
    for k, cid in enumerate(ids, 1):
        p = OUT / f"case_{cid}.csv"
        if p.exists():
            print(f"  [{k}/{len(ids)}] caseid {cid}: 既にある（スキップ）")
            continue
        t = time.time()
        try:
            tasks = case_windows(cid)
        except Exception as e:      # noqa: BLE001
            print(f"  [{k}/{len(ids)}] caseid {cid}: 取得失敗 {e}")
            continue
        if not tasks:
            print(f"  [{k}/{len(ids)}] caseid {cid}: ウィンドウなし")
            continue
        with Pool(jobs) as pool:
            rows = pool.map(_task, tasks)
        pd.DataFrame(rows).to_csv(p, index=False)
        n_ok = int(np.isfinite(pd.DataFrame(rows)["ri_cou"]).sum())
        print(f"  [{k}/{len(ids)}] caseid {cid}: {len(rows)} ウィンドウ・R1_d 有限 {n_ok}"
              f"（{(time.time()-t)/60:.1f} 分）")


# ---------------------------------------------------------------- 集計
def build_frame(cid: int, group: str) -> pd.DataFrame | None:
    p = OUT / f"case_{cid}.csv"
    f = FEAT / f"case_{cid}.csv"
    if not (p.exists() and f.exists()):
        return None
    c = pd.read_csv(p)
    d = pd.read_csv(f)
    m = d.merge(c[[x for x in ("t0", "ri_cou", "ri_lm", "amb") if x in c.columns]],
                on="t0", how="inner", suffixes=("", "_c"))
    if group == "pac":
        co = m["co_ref"].to_numpy(float)
        mp = m["map"].to_numpy(float)
        cvp = m["cvp"].to_numpy(float) if "cvp" in m.columns else np.zeros_like(mp)
        with np.errstate(divide="ignore", invalid="ignore"):
            m["svr"] = np.where(co > 0, (mp - cvp) * 80.0 / co, np.nan)
    else:
        v = VTONE / f"case_{cid}.csv"
        if not v.exists():
            return None
        vt = pd.read_csv(v)
        if "svr" not in vt.columns:
            return None
        m = m.merge(vt[["t0", "svr"]], on="t0", how="inner")
    return m.sort_values("t0")


# ════════════════════════════════════════════════ 用量反応（追記57 を 203 例で）
DOSE_COLS = (("ri_lm", "特徴点法の RI"), ("ri", "凍結版 PDA の RI"),
             ("ri_cou", "Couceiro R1_d"), ("amb", "早期振幅比 Am_b/Am_p1"))


def dose_case(m: pd.DataFrame, col: str, thr: float) -> dict | None:
    """1 症例。**`|ΔSVR%|` がしきい値以上のウィンドウだけ**に絞った相関。

    39番 `--dose` と同じことを、37番・38番の 203 例のデータで行う。
    追記57 の用量反応は 39番の 40 例で走らせたもので、主指標の選択がそこから来ている。
    203 例で見直さないと指標を決められない（追記63）。
    相対変化の基準は 3 列がそろう最初のウィンドウに取る（追記54 と同じ）。
    """
    v = m[col].to_numpy(float)
    mp0 = m["map"].to_numpy(float)
    sv0 = m["svr"].to_numpy(float)
    ok = np.isfinite(v) & np.isfinite(mp0) & np.isfinite(sv0)
    if ok.sum() < M37.MIN_WIN:
        return None
    x, mp, sv = M37._rel(v[ok]), M37._rel(mp0[ok]), M37._rel(sv0[ok])
    sel = np.abs(sv) >= thr
    if sel.sum() < M37.MIN_DISC:
        return None
    return {"n": int(sel.sum()),
            "rho_svr": M37.spearman(x[sel], sv[sel]),
            "rho_map": M37.spearman(x[sel], mp[sel]),
            "rho_svr_map": M37.spearman(sv[sel], mp[sel])}


def dose(group: str) -> int:
    frames = []
    for cid in pick_cases(group, None):
        m = build_frame(cid, group)
        if m is not None and len(m):
            frames.append(m)
    out = ["=" * 92,
           f"【診断】SVR の振れ幅で絞ると相関は上がるか（38番 --dose・{group} 群・{len(frames)} 例）",
           "追記57 と同じ問いを 203 例で見る。閾値の列は 39番と共有しており、実行前に固定してある。",
           "=" * 92]
    if not frames:
        out.append("\n該当する症例がない。先に --run で抽出すること。")
        print("\n".join(out))
        return 1
    for col, name in DOSE_COLS:
        out.append(f"\n■ {name}")
        out.append(f"{'|ΔSVR%| の下限':>14s}{'例':>5s}{'ウィンドウ':>10s}"
                   f"{'ρ_SVR':>9s}{'ρ_MAP':>9s}{'ρ(SVR,MAP)':>12s}{'PE 26.9%→':>12s}")
        for thr in M39.DOSE_THR:
            rows = [r for m in frames if col in m.columns
                    for r in [dose_case(m, col, thr)] if r]
            if not rows:
                out.append(f"{thr:>13.0%} {'—':>5s}")
                continue
            t = pd.DataFrame(rows)
            rs = float(np.nanmedian(t["rho_svr"]))
            out.append(f"{thr:>13.0%}{len(t):>5d}{int(t['n'].sum()):>10,}"
                       f"{rs:>+9.3f}{float(np.nanmedian(t['rho_map'])):>+9.3f}"
                       f"{float(np.nanmedian(t['rho_svr_map'])):>+12.3f}"
                       f"{M39.pe_after(rs):>11.1f}%")
    out.append("""
  【読み方】ρ_SVR が下へ**単調に上がれば**、関連は実在して雑音で薄まっている。
  **平らなら**関連そのものが弱い。ρ_SVR と ρ_MAP のどちらが大きいかを段ごとに見ること。
  【限界】`|ΔSVR%|` は症例の最初の有効ウィンドウからの相対変化であり、隣接ウィンドウ間の
  変化ではない。値が大きいウィンドウは手術後半かつ大きな循環変動があった場面に偏る。
  参照列 ρ(SVR,MAP) が下へ上がるなら、絞るほど血圧と抵抗の分離が悪くなっている。""")
    out.append("=" * 92)
    text = "\n".join(out)
    print(text)
    dst = ROOT.parent / "docs" / "research" / "results" / f"38_dose_{group}.txt"
    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_text(text + "\n", encoding="utf-8")
    print(f"\n書き出し: {dst}", file=sys.stderr)
    return 0


def stats(group: str) -> int:
    out: list[str] = []
    out.append("=" * 84)
    out.append("【探索】Couceiro 2015 の R1_d は VitalDB で血管抵抗と関連するか（38番）")
    out.append("roadmap §9・§12 の判定は動かさない。仮説生成のための解析である。")
    out.append("=" * 84)
    label = {"pac": "肺動脈カテーテル（熱希釈由来の独立 SVR*）",
             "ev1000": "EV1000（SVR は構造的に MAP を含む）"}[group]
    out.append(f"\n群: {label}")

    frames = []
    for cid in pick_cases(group, None):
        m = build_frame(cid, group)
        if m is not None and len(m):
            frames.append((cid, m))
    if not frames:
        out.append("\n該当する症例がない。先に --run で抽出すること。")
        print("\n".join(out))
        return 1

    for col, name in (("ri_cou", "Couceiro R1_d"), ("ri", "凍結版 PDA の RI（対照）"),
                      ("ri_lm", "特徴点法の RI"), ("amb", "早期振幅比 Am_b/Am_p1")):
        rows, n_case_skip = [], 0
        for cid, m in frames:
            if col not in m.columns:
                continue
            d = m[["t0", "map", "svr"]].copy()
            d["ri"] = m[col].to_numpy(float)
            d = d[np.isfinite(d["ri"])]
            r = M37.analyse_case(d)
            if r:
                r["caseid"] = cid
                rows.append(r)
            else:
                n_case_skip += 1
        M37.summarise(rows, f"■ {name}", out)
        if n_case_skip:
            out.append(f"  （ウィンドウ不足で除外: {n_case_skip} 例）")

    out.append("""
  【読み方】判別試験は「★逆向きのみ（厳格）」の行である。SVR と MAP が逆向きに動いた
  ウィンドウで、指標が SVR と MAP のどちらを追うかを見る。SVR 側が 0 近傍で MAP 側が
  正なら、その指標は血圧を追っている。""")
    if group == "pac":
        out.append("""  【限界】n が最大 5 例であり記述のみ。さらに Vigilance の連続CO は数分の移動平均のため、
  60 秒ウィンドウでは CO がほとんど動かず SVR* が MAP の定数倍に近づく（37番で
  ρ(ΔSVR%, ΔMAP%)=+0.794）。独立性は名目的である。""")
    else:
        out.append("""  【限界】EV1000 の SVR は (MAP−CVP)×80/CO で MAP を分子に含み、CO も動脈圧波形由来。
  陽性でも証明にならない。SVR 方向にまったく動かない場合にのみ除外の判断として意味を持つ。""")
    out.append("=" * 84)

    text = "\n".join(out)
    print(text)
    dst = ROOT.parent / "docs" / "research" / "results" / f"38_couceiro_svr_{group}.txt"
    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_text(text + "\n", encoding="utf-8")
    print(f"\n書き出し: {dst}", file=sys.stderr)
    return 0


# ---------------------------------------------------------------- 自己検査
def selftest() -> int:
    ok, ng = 0, []

    def chk(name, cond):
        nonlocal ok
        if cond:
            ok += 1
            print(f"  PASS  {name}")
        else:
            ng.append(name)
            print(f"  FAIL  {name}")

    chk("33番の fit_couceiro を読める", callable(getattr(M33, "fit_couceiro", None)))
    chk("33番の couceiro_points を読める", callable(getattr(M33, "couceiro_points", None)))
    chk("37番の analyse_case を読める", callable(getattr(M37, "analyse_case", None)))
    chk("37番の summarise を読める", callable(getattr(M37, "summarise", None)))

    # 合成拍で R1_d が有限に出るか
    fs, T = FS, 1.0
    t = np.arange(0, T, 1 / fs)
    y = (1.0 * np.exp(-((t - 0.20) / 0.055) ** 2)
         + 0.45 * np.exp(-((t - 0.33) / 0.070) ** 2)
         + 0.25 * np.exp(-((t - 0.50) / 0.090) ** 2))
    r = indices_on_beat(y, fs)
    chk("合成拍で R1_d が有限", np.isfinite(r["ri_cou"]))
    chk("合成拍で早期振幅比が有限", np.isfinite(r["amb"]))

    # 振幅を2倍しても R1_d は比なので不変
    r2 = indices_on_beat(2.0 * y, fs)
    chk("R1_d は振幅倍率に不変",
        np.isfinite(r["ri_cou"]) and np.isfinite(r2["ri_cou"])
        and abs(r["ri_cou"] - r2["ri_cou"]) < 0.02)

    # 平坦な信号は NaN
    chk("平坦な信号は R1_d が NaN", not np.isfinite(indices_on_beat(np.ones(500), fs)["ri_cou"]))

    # --dose の検算。39番と閾値・誤差率の式を共有していること、絞り込みが効くこと。
    chk("閾値の列と誤差率の式を 39番と共有している",
        M39.DOSE_THR == (0.0, 0.05, 0.10, 0.20, 0.30, 0.50)
        and abs(M39.pe_after(0.67) - 20.0) < 0.1)
    _n = 60
    _sv = np.linspace(1.0, 2.0, _n)
    _d = pd.DataFrame({"svr": 1000 * _sv, "map": 80 * np.linspace(1.0, 1.2, _n),
                       "ri_lm": 0.4 * _sv})
    chk("dose_case 閾値 0 で全ウィンドウを使う", dose_case(_d, "ri_lm", 0.0)["n"] == _n)
    chk("dose_case 閾値を上げるとウィンドウが減る", dose_case(_d, "ri_lm", 0.50)["n"] < _n)
    chk("dose_case SVR に完全に従う指標は絞っても ρ=1",
        abs(dose_case(_d, "ri_lm", 0.0)["rho_svr"] - 1.0) < 1e-9)
    chk("dose_case 組数不足は None", dose_case(_d.head(5), "ri_lm", 0.0) is None)

    # 症例選択が5例（Vigilance）になる
    try:
        pac = pick_cases("pac", None)
        chk("pac 群の候補が target_cases から取れる", isinstance(pac, list))
    except Exception:      # noqa: BLE001
        chk("pac 群の候補が target_cases から取れる", False)

    print(f"\n  {ok}/{ok + len(ng)} PASS" + ("  ALL PASS" if not ng else f"  FAIL: {ng}"))
    return 0 if not ng else 1


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", action="store_true")
    ap.add_argument("--stats-only", action="store_true")
    ap.add_argument("--dose", action="store_true",
                    help="SVR の振れ幅で絞ると相関が上がるかを 203 例で見る（追記63）")
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--group", choices=["pac", "ev1000"], default="pac")
    ap.add_argument("--limit", type=int, default=None)
    ap.add_argument("--jobs", type=int, default=4)
    a = ap.parse_args()
    if a.selftest:
        sys.exit(selftest())
    if a.run:
        extract(a.group, a.limit, a.jobs)
        sys.exit(stats(a.group))
    if a.dose:
        sys.exit(dose(a.group))
    if a.stats_only:
        sys.exit(stats(a.group))
    ap.print_help()


if __name__ == "__main__":
    main()
