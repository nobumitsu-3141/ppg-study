#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""研究0 決定試験: PDA 第2版・凍結版・ランドマーク法を、同じ真値・同じ規準で並べる。

背景
----
`20_pwdb_validity.py` で凍結版 PDA（2カーネル歪みガウス）は事前規準を満たさなかった。
`23_pwdb_landmarks.py` で、**同じ波形**から作ったランドマーク指標は規準を満たした
（ΔT×PWV 0.710 / AGI_mod×PWV 0.885 / RI×pvr 0.504）。したがって失敗は
「指尖脈波から硬さ・抵抗を読むこと」ではなく「我々の分解の作り方」に固有である。

そこで文献（Wang 2013・Tigges 2017・Couceiro 2015・Fleischhauer 2020・Lee 2011）に
基づいて `src/pda2.py` を作り直した。合成波では改善が確認できたが、合成波は
実在の交絡（心拍数・波形型の分布）を過小評価する。決定は PWDB でしかつかない。

この台本は 1 枚の表に次を並べる。**同じ被験者・同じ真値・同じ判定規準**である。
差は指標の作り方だけに帰せる。

  凍結PDA 2カーネル            src/pda.py（研究1で凍結した実装そのもの）
  PDA 第2版 二段（歪みガウス） src/pda2.py route="two_stage"
  PDA 第2版 ガンマ3            src/pda2.py route="gamma3"
  ランドマーク法               Charlton らの同梱値（Digital_RI・SI・AI・AGI_mod）
  モデル出力 PTT               配管の陽性対照

選択の効果を隠さないために、判定は 3 通り出す。
  A 各手法が自分で合格とした例だけ（20番・23番と同じ扱い）
  B 3 手法すべてが合格とした共通例だけ（分母を完全にそろえる）
  C 採否を無視して全例（合格判定そのものが選択になっていないかを見る）

A だけが通って B・C が通らないなら、それは「難しい拍を捨てたから通った」であって
指標の改善ではない。この 3 段を必ず一緒に読むこと。

使い方
------
    python3 scripts/26_pwdb_compare.py --pwdb ~/pwdb --jobs 8
    python3 scripts/26_pwdb_compare.py --pwdb ~/pwdb --limit 300 --jobs 4
    python3 scripts/26_pwdb_compare.py --selftest
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
from src.pda import fit_beat                             # noqa: E402
from src.indices import si_ri_from_fit                   # noqa: E402

DATA = ROOT / "data"
OUT = DATA / "pwdb"


def _load(stem: str, name: str):
    """数字始まりの台本を名前で読み込む（import 文では書けない）。"""
    p = Path(__file__).resolve().parent / stem
    spec = importlib.util.spec_from_file_location(name, p)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


M = _load("20_pwdb_validity.py", "m20")
L = _load("23_pwdb_landmarks.py", "m23")

# ---------------------------------------------------------------- 定義表
# (キー, 表示名, ΔT列, RI列, 採否列)
METHODS = [
    ("v1",  "凍結PDA 2カーネル",          "dt_v1_ms",  "ri_v1",      "ok_v1"),
    ("v2",  "第2版 二段(歪みガウス)",     "dt_v2_ms",  "ri_v2",      "ok_v2"),
    ("v2g", "第2版 ガンマ3",              "dt_v2g_ms", "ri_v2g",     "ok_v2g"),
    ("lm",  "ランドマーク法",             "dt_lm_ms",  "digital_ri", None),
]

# (列, 真値, 予測符号, 採否列, 表示名)
PAIRS = [
    ("dt_v1_ms",       "PWV_a", -1, "ok_v1",  "ΔT       凍結PDA 2カーネル"),
    ("dt_v2_ms",       "PWV_a", -1, "ok_v2",  "ΔT       第2版 二段(歪みガウス)"),
    ("dt_v2g_ms",      "PWV_a", -1, "ok_v2g", "ΔT       第2版 ガンマ3"),
    ("dt_lm_ms",       "PWV_a", -1, None,     "ΔT       ランドマーク法"),
    ("digital_si",     "PWV_a", +1, None,     "SI       ランドマーク法"),
    ("digital_agi_mod", "PWV_a", +1, None,    "AGI_mod  ランドマーク法"),
    ("digital_ptt",    "PWV_a", -1, None,     "PTT      モデル出力（陽性対照）"),
    ("ri_v1",          "pvr",   +1, "ok_v1",  "RI       凍結PDA 2カーネル"),
    ("ri_v2",          "pvr",   +1, "ok_v2",  "RI       第2版 二段(歪みガウス)"),
    ("ri_v2g",         "pvr",   +1, "ok_v2g", "RI       第2版 ガンマ3"),
    ("digital_ri",     "pvr",   +1, None,     "RI       ランドマーク法"),
    ("digital_ai",     "pvr",   +1, None,     "AI       ランドマーク法"),
]

IDX_FOR_FACTORS = [("dt_v1_ms", "ΔT 凍結PDA"), ("dt_v2_ms", "ΔT 第2版二段"),
                   ("dt_v2g_ms", "ΔT 第2版ガンマ"), ("dt_lm_ms", "ΔT ランドマーク"),
                   ("ri_v1", "RI 凍結PDA"), ("ri_v2", "RI 第2版二段"),
                   ("ri_v2g", "RI 第2版ガンマ"), ("digital_ri", "RI ランドマーク")]

MIN_N = 20          # これ未満の集団は表に出しても意味がないので数だけ示す
# 20番の `_by_age` は年齢層ごとに 8 名以上を要求する。全体の人数だけで門番を作ると、
# 「全体 24 名（1層 4 名）」のように、人数はあるのに判定が出ない状態を取りこぼす。
MIN_PER_AGE = 8


def _n_strata(src, col: str) -> int:
    """その指標で順位相関を出せる年齢層の数。"""
    if col not in src:
        return 0
    g = src[src[col].notna()]
    if not len(g):
        return 0
    return int((g.groupby("age").size() >= MIN_PER_AGE).sum())


def _judge_or_none(src, col: str, tgt: str, sign: int):
    if col not in src or tgt not in src or _n_strata(src, col) == 0:
        return None
    return M._judge(M._by_age(src, col, tgt), sign)


# ---------------------------------------------------------------- 1被験者
def indices_for_subject(args_tuple):
    """1 拍に 3 通りの分解を当て、それぞれの ΔT・RI・採否・当てはまりを返す。"""
    subj, row, hr = args_tuple
    out = {"subj_no": subj, "ok_v1": 0, "ok_v2": 0, "ok_v2g": 0}
    try:
        y, fs = M.beat_of(row, hr)
        if y is None:
            return out
        t = np.arange(y.size) / fs
        out["fs"] = float(fs)
        out["n_samp"] = int(y.size)

        try:                                    # --- 凍結版（研究1と同一コード）
            fit = fit_beat(t, y)
            ix = si_ri_from_fit(fit)
            out.update(dt_v1_ms=ix["dt_s"] * 1000.0, ri_v1=ix["ri"],
                       nrmse_v1=float(fit.get("nrmse", np.nan)),
                       ok_v1=int(bool(fit.get("ok", False))))
        except Exception:
            pass

        for tag, route in (("v2", "two_stage"), ("v2g", "gamma3")):
            try:                                # --- 第2版
                r = pda2.decompose(t, y, fs, route=route)
                out[f"ok_{tag}"] = int(bool(r.get("ok")))
                out[f"dt_{tag}_ms"] = r.get("dt_ms", np.nan)
                out[f"ri_{tag}"] = r.get("ri", np.nan)
                out[f"dtse_{tag}_ms"] = r.get("dt_se_ms", np.nan)
                out[f"rise_{tag}"] = r.get("ri_se", np.nan)
                out[f"nrmse_{tag}"] = r.get("nrmse", np.nan)
                out[f"errx_{tag}_ms"] = r.get("errx_ms", np.nan)
                # 閾値感度解析（27番）が当てはめ直しなしで採否を再計算できるよう、
                # 採否に使った診断量をすべて残す
                out[f"erry_{tag}"] = r.get("erry", np.nan)
                out[f"nlm_{tag}"] = r.get("n_landmark_matched", np.nan)
                out[f"amb_{tag}"] = int(bool(r.get("ambiguous")))
                out[f"noref_{tag}"] = int(r.get("role_rule") == "none")
                out[f"klass_{tag}"] = r.get("klass", np.nan)
                out[f"nw_{tag}"] = r.get("n_waves", np.nan)
                out[f"esc_{tag}"] = int(bool(r.get("escalated")))
                out[f"why_{tag}"] = str(r.get("reason", ""))[:24]
            except Exception as e:              # noqa: BLE001
                out[f"why_{tag}"] = ("EXC:" + str(e))[:24]
        return out
    except Exception as e:                      # noqa: BLE001
        out["err"] = str(e)[:80]
        return out


# ---------------------------------------------------------------- 構築
def build(root: Path, limit: int = 0, jobs: int = 1):
    """PWDB を読み、3 通りの分解を回し、ランドマーク指標・真値と結合する。"""
    import pandas as pd
    root = Path(root).expanduser()
    hae, cfg, ppg, _extras = M.load_pwdb(root)
    if limit:
        ppg = ppg.iloc[:limit]
    hr_by = dict(zip(hae["subj_no"].astype(int), hae["HR"].astype(float)))
    work = [(int(ppg.iloc[i, 0]), ppg.iloc[i].to_numpy(float),
             hr_by.get(int(ppg.iloc[i, 0]), np.nan)) for i in range(len(ppg))]
    print(f"\n{len(work)} 名に 3 通りの分解を当てます / jobs={jobs}", flush=True)

    if jobs > 1:
        from concurrent.futures import ProcessPoolExecutor
        with ProcessPoolExecutor(max_workers=jobs) as ex:
            rows = list(ex.map(indices_for_subject, work, chunksize=8))
    else:
        rows = []
        for n, w in enumerate(work, 1):
            rows.append(indices_for_subject(w))
            if n % 200 == 0:
                print(f"  [{n}/{len(work)}]", flush=True)
    pda = pd.DataFrame(rows)

    # ランドマーク側は 23 番の読み込みをそのまま使う（扱いを完全に共有する）
    d = L.load(root, pda_dir=root / "__no_pda__")
    d = d.drop(columns=[c for c in ("dt_pda_ms", "ri_pda", "ok2") if c in d.columns])
    d = d.merge(pda, on="subj_no", how="left")
    for c in ("ok_v1", "ok_v2", "ok_v2g"):
        d[c] = d[c].fillna(0).astype(int)
    d["ok_all"] = ((d["ok_v1"] == 1) & (d["ok_v2"] == 1) & (d["ok_v2g"] == 1)).astype(int)
    return d


# ---------------------------------------------------------------- 報告
def _sub(d, ok_col, mode: str):
    """判定に使う部分集合。mode は own / common / all。"""
    if mode == "all":
        return d
    if mode == "common":
        return d[d["ok_all"] == 1]
    return d if ok_col is None else d[d[ok_col] == 1]


def _fmt_j(j):
    if not j:
        return f"{'—':>9}{'—':>9}{'—':>8}"
    return f"{j['med_abs']:>9.3f}{j['n_ok']:>5}/{j['n_ages']:<3}"


def report(d, out_dir: Path | None = None) -> dict:
    ages = sorted(d["age"].dropna().unique().tolist())
    n = len(d)
    print(f"\n{'=' * 78}")
    print("研究0 決定試験: PDA第2版・凍結版・ランドマーク法を同じ規準で比べる")
    print("=" * 78)
    print(f"\n被験者 {n} 名 / 年齢層 {[int(a) for a in ages]}")
    print(f"判定規準（20番・23番と同一）: 年齢層内 Spearman ρ が全層で予測の向き、"
          f"かつ中央値 |ρ| ≥ {M.CRIT_RHO}")

    # ---- 採択率と当てはまり
    print(f"\n{'-' * 78}\n1. 採択率と当てはまり\n{'-' * 78}")
    print(f"{'手法':<26}{'採択':>8}{'NRMSE':>9}{'Errx[ms]':>10}"
          f"{'ΔT中央値[ms]':>14}{'ΔTのSE[ms]':>12}")
    for key, lab, dtc, _ric, okc in METHODS:
        src = d if okc is None else d[d[okc] == 1]
        rate = "—" if okc is None else f"{100.0 * len(src) / max(n, 1):>7.1f}%"
        nr = d.get(f"nrmse_{key}")
        ex = d.get(f"errx_{key}_ms")
        se = d.get(f"dtse_{key}_ms")

        def _m(s):
            if s is None or not np.isfinite(np.asarray(s, float)).any():
                return "—"
            return f"{float(np.nanmedian(np.asarray(s, float))):.3f}"

        dtm = ("—" if dtc not in src or not src[dtc].notna().any()
               else f"{float(np.nanmedian(src[dtc])):.0f}")
        sem = ("—" if se is None or not np.isfinite(np.asarray(se, float)).any()
               else f"{float(np.nanmedian(np.asarray(se, float))):.1f}")
        exm = ("—" if ex is None or not np.isfinite(np.asarray(ex, float)).any()
               else f"{float(np.nanmedian(np.asarray(ex, float))):.2f}")
        print(f"{lab:<26}{rate:>8}{_m(nr):>9}{exm:>10}{dtm:>14}{sem:>12}")
    print("  採択は各手法自身の合否規準による（第2版は Wang 2013 の NRMSE<2%・Errx<6ms・"
          "Erry<0.01 かつ解が一意）。")

    # ---- A. 各手法の合格例
    print(f"\n{'-' * 78}\nA. 各手法が合格とした例だけで判定（20番・23番と同じ扱い）\n{'-' * 78}")
    hdr = (f"{'指標 × 真値':<34}" + "".join(f"{int(a):>7}" for a in ages)
           + f"{'中央値':>8}{'向き':>8}  判定")
    print(hdr)
    summary = {}
    for col, tgt, sign, okc, lab in PAIRS:
        src = _sub(d, okc, "own")
        j = _judge_or_none(src, col, tgt, sign)
        if j is None:
            n_i = 0 if col not in src else int(src[col].notna().sum())
            print(f"{lab:<34}  （判定できる年齢層がない・n={n_i}・"
                  f"8名以上の層 {_n_strata(src, col)}）")
            continue
        rows = M._by_age(src, col, tgt)
        by = {a: r for a, r, _q in rows}
        line = f"{lab:<34}"
        for a in ages:
            r = by.get(a, np.nan)
            line += f"{r:>+7.2f}" if np.isfinite(r) else f"{'—':>7}"
        if j:
            exp = {-1: "負", 1: "正", 0: "—"}[sign]
            line += f"{j['med_abs']:>8.3f}{j['n_ok']:>4}/{j['n_ages']:<3}{exp}  "
            line += ("成立" if j["pass"] else "不成立") if sign else "記述"
            summary[f"A|{col}|{tgt}"] = j
        print(line)

    # ---- B / C
    n_common = int(d["ok_all"].sum())
    print(f"\n{'-' * 78}")
    print(f"B. 3手法すべてが合格した共通例のみ（n={n_common}） / "
          f"C. 採否を無視して全例（n={n}）")
    print("-" * 78)
    print(f"{'指標 × 真値':<34}{'B 中央値':>9}{'B 向き':>9}{'B判定':>7}"
          f"{'C 中央値':>9}{'C 向き':>9}{'C判定':>7}")
    ns = _n_strata(d[d["ok_all"] == 1], "dt_v2_ms")
    if ns == 0:
        print(f"  （B: 共通例 {n_common} 名では 8 名以上の年齢層が無く、判定を出せない）")
    for col, tgt, sign, _okc, lab in PAIRS:
        line = f"{lab:<34}"
        for mode in ("common", "all"):
            src = _sub(d, None, mode)
            j = _judge_or_none(src, col, tgt, sign)
            if not j:
                line += f"{'—':>9}{'—':>9}{'—':>7}"
                continue
            summary[f"{mode}|{col}|{tgt}"] = j
            v = ("成立" if j["pass"] else "不成立") if sign else "記述"
            line += f"{j['med_abs']:>9.3f}{j['n_ok']:>5}/{j['n_ages']:<3}{v:>7}"
        print(line)
    print("  A だけ成立して B・C が不成立なら、それは難しい拍を捨てた効果であって")
    print("  指標そのものの改善ではない。3 段を必ず一緒に読むこと。")

    # ---- 波形型ごと
    if "klass_v2" in d and d["klass_v2"].notna().any():
        print(f"\n{'-' * 78}\n2. 波形型（Dawber 分類）ごとの採択率と ΔT\n{'-' * 78}")
        print(f"{'型':<6}{'n':>7}{'第2版採択':>11}{'凍結採択':>10}"
              f"{'ΔT 第2版':>11}{'ΔT ランドマーク':>16}")
        for k in sorted(d["klass_v2"].dropna().unique().tolist()):
            g = d[d["klass_v2"] == k]
            a2 = 100.0 * g["ok_v2"].mean()
            a1 = 100.0 * g["ok_v1"].mean()
            m2 = float(np.nanmedian(g["dt_v2_ms"])) if g["dt_v2_ms"].notna().any() else np.nan
            ml = float(np.nanmedian(g["dt_lm_ms"])) if g["dt_lm_ms"].notna().any() else np.nan
            print(f"{int(k):<6}{len(g):>7}{a2:>10.1f}%{a1:>9.1f}%"
                  f"{m2:>11.0f}{ml:>16.0f}")
        print("  型4（切痕なし）は合成波でも 40〜55 ms の誤差が残っている。ここが実際に")
        print("  どれだけ効いているかは、この行の n と採択率で読む。")

    # ---- 成分を増やしたかどうか
    for key, lab, dtc, ric, okc in METHODS:
        ec = f"esc_{key}"
        if ec not in d or not d[ec].notna().any() or d[ec].nunique() < 2:
            continue
        print(f"\n{'-' * 78}\n2b. 成分を増やしたかどうかで層別（{lab}）\n{'-' * 78}")
        print("  合成波では、成分を1つ増やすと波形の当てはまりは良くなるが反射波が2つに割れ、")
        print("  ΔT が真値から約 2 ms 遠ざかった。実データでも分けて読む。")
        print(f"{'':<20}{'n':>8}{'採択率':>9}{'ΔT中央値[ms]':>14}"
              f"{'ΔT×PWV 中央値|ρ|':>18}{'判定':>8}")
        for v, name in ((0, "増やさなかった"), (1, "増やした")):
            g = d[d[ec] == v]
            if len(g) < MIN_N:
                print(f"{name:<20}{len(g):>8}  （少なすぎるので判定しない）")
                continue
            go = g[g[okc] == 1]
            dtm = (f"{float(np.nanmedian(go[dtc])):.0f}"
                   if len(go) and go[dtc].notna().any() else "—")
            j = _judge_or_none(go, dtc, "PWV_a", -1)
            med = f"{j['med_abs']:.3f}" if j else "—"
            ver = (("成立" if j["pass"] else "不成立") if j else "—")
            print(f"{name:<20}{len(g):>8}{100.0 * g[okc].mean():>8.1f}%"
                  f"{dtm:>14}{med:>18}{ver:>8}")

    # ---- 因子主効果
    if "var_pwv" in d:
        print(f"\n{'-' * 78}\n3. 振った因子ごとの主効果（年齢層内。+1 と −1 の平均差 ÷ 層平均 [%]）"
              f"\n{'-' * 78}")
        print(f"{'指標':<20}" + "".join(f"{M.FACTOR_LABEL[f]:>12}" for f in M.FACTORS))
        for col, lab in IDX_FOR_FACTORS:
            if col not in d or _n_strata(d, col) == 0:
                continue
            e, _r = M._factor_effects(d, col)
            print(f"{lab:<20}" + "".join(f"{v:>+12.1f}" if np.isfinite(v) else f"{'—':>12}"
                                         for v in e))
        print("  概念どおりなら、硬さの指標は『脈波伝播速度』の列が最大になるはずである。")
        print("  『心拍数』の列が最大なら、その指標が拾っているのは主に心拍である。")

    print(f"\n{'-' * 78}\n読み方\n{'-' * 78}")
    print("  第2版が A・B・C すべてで成立 → 失敗は実装の問題だった。研究2へ進める。")
    print("  第2版が A だけ成立         → 選択の効果。改善とは言えない。")
    print("  第2版もランドマーク法に届かない → PDA という枠組みでは指尖 PPG から")
    print("    硬さ・抵抗を取り出せない。ランドマーク指標に乗り換えるか、撤退する。")
    print("  モデル出力 PTT が強い負を示さないなら、この比較自体を疑うこと（陽性対照）。")

    out_dir = OUT if out_dir is None else Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    p = out_dir / "pwdb_compare.csv"
    d.to_csv(p, index=False)
    print(f"\n被験者別の結果: {p}")
    return summary


# ---------------------------------------------------------------- 自己検証
def selftest() -> int:
    import tempfile
    print("== 26_pwdb_compare 自己検証（模擬PWDB・ネットワーク不要） ==\n")
    print("  注意: 模擬波は 2 ガウスの和なので、どの手法も通って当然である。")
    print("        ここで検査するのは配管（読み込み・結合・判定の共有）であって、")
    print("        手法の優劣ではない。優劣は実 PWDB でしか決まらない。\n")
    ok = True

    def rep(name, cond, detail=""):
        nonlocal ok
        ok &= bool(cond)
        print(f"  [{'PASS' if cond else 'FAIL'}] {name}{('  ' + detail) if detail else ''}",
              flush=True)

    with tempfile.TemporaryDirectory() as td:
        root = L._make_mock(Path(td) / "exported_data", n=60)
        d = build(root, jobs=1)
        rep("3 手法すべての列が揃った",
            all(c in d for c in ("dt_v1_ms", "dt_v2_ms", "dt_v2g_ms", "dt_lm_ms",
                                 "ri_v1", "ri_v2", "ri_v2g", "digital_ri")))
        rep("被験者が重複せず結合された", len(d) == 60 and d["subj_no"].is_unique)
        rep("第2版が標準誤差を返している（凍結版にはない量）",
            "dtse_v2_ms" in d and np.isfinite(d["dtse_v2_ms"]).any(),
            f"中央値 {float(np.nanmedian(d['dtse_v2_ms'])):.2f} ms"
            if "dtse_v2_ms" in d and np.isfinite(d["dtse_v2_ms"]).any() else "")
        rep("共通合格例の列が作られた", "ok_all" in d,
            f"共通 n={int(d['ok_all'].sum())} / v1={int(d['ok_v1'].sum())}"
            f" / v2={int(d['ok_v2'].sum())} / v2g={int(d['ok_v2g'].sum())}")
        s = report(d, out_dir=Path(td) / "out")
        rep("仕込んだ ランドマークΔT × PWV（負）を復元",
            bool(s.get("A|dt_lm_ms|PWV_a", {}).get("pass")))
        rep("仕込んだ ランドマークRI × 抵抗（正）を復元",
            bool(s.get("A|digital_ri|pvr", {}).get("pass")))
        j2 = s.get("A|dt_v2_ms|PWV_a")
        rep("第2版 二段 が模擬波の ΔT × PWV を復元（配管の確認）",
            bool(j2 and j2["pass"]), f"{j2}")
        n_common = int(d["ok_all"].sum())
        ns = _n_strata(d[d["ok_all"] == 1], "dt_v2_ms")
        rep("C（全例）の判定が算出された", any(k.startswith("all|") for k in s))
        rep("B（共通例）は判定できる年齢層があるときだけ判定を出す",
            any(k.startswith("common|") for k in s) == (ns >= 1),
            f"共通 n={n_common} / 8名以上の年齢層 {ns}")
        rep("判定規準を 20 番・23 番と共有している", M.CRIT_RHO == 0.30 and L.M is not None)
        rep("結果 CSV が書かれた", (Path(td) / "out" / "pwdb_compare.csv").exists())
    print("\n" + ("ALL PASS" if ok else "FAIL あり"))
    return 0 if ok else 1


# ---------------------------------------------------------------- main
def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--pwdb", type=str, help="PWDB の配布物を置いたフォルダ")
    ap.add_argument("--limit", type=int, default=0, help="先頭N名だけ処理（0=全員）")
    ap.add_argument("--jobs", type=int, default=1)
    ap.add_argument("--selftest", action="store_true")
    args = ap.parse_args()
    if args.selftest:
        sys.exit(selftest())
    if not args.pwdb:
        ap.error("--pwdb を指定してください（--selftest なら不要）")
    report(build(Path(args.pwdb), limit=args.limit, jobs=args.jobs))


if __name__ == "__main__":
    main()
