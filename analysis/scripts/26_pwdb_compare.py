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
  PDA 第2版 歪みガウス        src/pda2.py route="skew"
  PDA 第2版 ガンマ            src/pda2.py route="gamma"
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
    ("v2",  "第2版 歪みガウス",     "dt_v2_ms",  "ri_v2",      "ok_v2"),
    ("v2g", "第2版 ガンマ",              "dt_v2g_ms", "ri_v2g",     "ok_v2g"),
    ("lm",  "ランドマーク法",             "dt_lm_ms",  "digital_ri", None),
    ("hq",  "早期振幅比（Hellqvist）",     "dt_p1_ms",  "amb_amp1",   None),
]

# (列, 真値, 予測符号, 採否列, 表示名)
PAIRS = [
    ("dt_v1_ms",       "PWV_a", -1, "ok_v1",  "ΔT       凍結PDA 2カーネル"),
    ("dt_v2_ms",       "PWV_a", -1, "ok_v2",  "ΔT       第2版 歪みガウス"),
    ("dt_v2g_ms",      "PWV_a", -1, "ok_v2g", "ΔT       第2版 ガンマ"),
    ("dt_lm_ms",       "PWV_a", -1, None,     "ΔT       ランドマーク法"),
    ("digital_si",     "PWV_a", +1, None,     "SI       ランドマーク法"),
    ("digital_agi_mod", "PWV_a", +1, None,    "AGI_mod  ランドマーク法"),
    ("digital_ptt",    "PWV_a", -1, None,     "PTT      モデル出力（陽性対照）"),
    ("ri_v1",          "pvr",   +1, "ok_v1",  "RI       凍結PDA 2カーネル"),
    ("ri_v2",          "pvr",   +1, "ok_v2",  "RI       第2版 歪みガウス"),
    ("ri_v2g",         "pvr",   +1, "ok_v2g", "RI       第2版 ガンマ"),
    ("digital_ri",     "pvr",   +1, None,     "RI       ランドマーク法"),
    ("digital_ai",     "pvr",   +1, None,     "AI       ランドマーク法"),
    # --- 事前指定の副次（Epstein 2014 を読んで 26番の実行前に追加した）---
    # Epstein 2014 は 1次元 75動脈モデルで、SI は**導管動脈全体**の硬さに支配され、
    # 大動脈だけを硬くすると PPT はむしろ延びる（SI は下がる）ことを示した。
    # つまり ΔT を「大動脈 PWV の代替」として検定するのは的を外しうる。
    # 主要目標（PWV_a）は凍結したまま、頸大腿 PWV を副次として並べる。
    ("dt_v2_ms",       "PWV_cf", -1, "ok_v2",  "副次 ΔT   第2版 二段 × 頸大腿PWV"),
    ("dt_lm_ms",       "PWV_cf", -1, None,     "副次 ΔT   ランドマーク × 頸大腿PWV"),
    # --- 第4の手法: 分解を使わない早期振幅比（Hellqvist 2024）---
    # 33名・頸大腿PWV 参照で r = −0.81、大動脈PWV で −0.75。硬さ指数（中枢PWV と
    # r = 0.58〜0.66）や加齢指数（0.65）、ばね定数（−0.72）のいずれより強い。
    # 同論文は「硬さ指数のように S と D のピーク間の時間に頼る指標ではなく、
    # 波形の早期部分に注目すべき」と明記している。我々の ΔT はまさにその時間である。
    ("amb_amp1",       "PWV_a",  -1, None,     "Am_b/Am_p1  早期振幅比（Hellqvist）"),
    ("amb_amp1",       "PWV_cf", -1, None,     "副次 Am_b/Am_p1 × 頸大腿PWV"),
    # Hellqvist の p1（1次微分の下降への接線の零交点）を収縮期ピークに使った ΔT。
    # p1 は「6つの波形型すべてで機能した」と報告されており、切痕の無い波形でも
    # 収縮期ピークを定義できる。我々の未解決問題（型3で ΔT 誤差 約30 ms）に効くか
    ("dt_p1_ms",       "PWV_a",  -1, None,     "ΔT  p1基準（Hellqvist の収縮期ピーク）"),
    # 同じ拡張期の錨で、収縮期の錨だけを我々の収縮期ピークにしたもの。
    # dt_p1_ms との差は収縮期の錨だけなので、p1 の寄与を交絡なく読める
    ("dt_own_ms",      "PWV_a",  -1, None,     "ΔT  自前ランドマーク（p1 との対照）"),
    # --- 記述のみ（予測の向きを事前に決めない）---
    # Goswami 2010 の差分パルス幅。健常 30歳 10 ms、高血圧 55歳 90 ms と開いたが、
    # 真値との向きの予測までは立てられないので記述にとどめる。
    ("dps_v2_ms",      "PWV_a",  0, "ok_v2",   "（記述）DPS 第2版 二段 × 大動脈PWV"),
    ("dps_v2_ms",      "pvr",    0, "ok_v2",   "（記述）DPS 第2版 二段 × 末梢血管抵抗"),
]

# (列, 表示名, 採否列)。因子主効果は各手法が合格とした例で計算する
IDX_FOR_FACTORS = [("dt_v1_ms", "ΔT 凍結PDA", "ok_v1"), ("dt_v2_ms", "ΔT 第2版歪み", "ok_v2"),
                   ("dt_v2g_ms", "ΔT 第2版ガンマ", "ok_v2g"), ("dt_lm_ms", "ΔT ランドマーク", None),
                   ("ri_v1", "RI 凍結PDA", "ok_v1"), ("ri_v2", "RI 第2版歪み", "ok_v2"),
                   ("ri_v2g", "RI 第2版ガンマ", "ok_v2g"), ("digital_ri", "RI ランドマーク", None),
                   ("dps_v2_ms", "DPS 第2版歪み", "ok_v2"), ("amb_amp1", "Am_b/Am_p1", None),
                   ("dt_p1_ms", "ΔT p1基準", None), ("dt_own_ms", "ΔT 自前ランドマーク", None)]

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


def _verdict(j, sign: int, n_ages_full: int) -> str:
    """判定の文字列。**層が揃っていなければ印を付ける。**

    事前規準は「年齢層内の順位相関が**全層で**予測の向き」である。`_judge` の実装は
    「有限の ρ を持つ層すべて」で判定するので、採択率が低くて層が減った手法ほど
    通りやすくなる（2層なら 2/2 で足りる）。規準そのものは凍結したまま動かさないが、
    **層が揃っていない判定は揃っている判定と同列に読んではいけない**ので印で区別する。
    """
    if not j:
        return "—"
    if not sign:
        return "記述"
    v = "成立" if j["pass"] else "不成立"
    if j["n_ages"] < n_ages_full:
        v += "*"          # 層不足。* の付いた「成立」は層が揃った「成立」より弱い
    return v


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

        # --- 波形そのものから取る指標（分解を要しない）
        try:
            ys, _amp = pda2.preprocess(t, y, fs)
            if ys is not None:
                lmo = pda2.find_landmarks(t, ys)
                ef = pda2.early_features(t, ys)
                out["klass_own"] = lmo["klass"]
                out["sys_own_ms"] = lmo["sys_t"] * 1000.0
                out["dia_own_ms"] = lmo["dia_t"] * 1000.0
                out["p1_t_ms"] = ef["p1_t"] * 1000.0
                out["amb_amp1"] = ef["amb_amp1"]          # Hellqvist 2024 の早期振幅比
                # Hellqvist の p1 を収縮期ピークに使った ΔT。切痕の無い波形でも
                # 収縮期ピークが定義できるので、我々の未解決問題に効くかを見る
                out["dt_p1_ms"] = (lmo["dia_t"] - ef["p1_t"]) * 1000.0
                # 自前のランドマークだけで作った ΔT。dt_p1_ms との差は**収縮期の錨だけ**に
                # なるので、「p1 が切痕なし波形を救うか」を交絡なく見られる。
                # dt_lm_ms（Charlton 同梱値）とは拡張期の錨も違うので直接は比べられない
                out["dt_own_ms"] = (lmo["dia_t"] - lmo["sys_t"]) * 1000.0
                # 拍が足で切り出されているか（前処理の足→足基線の前提）を実データで確かめる
                out["edge_lo"] = float(min(ys[0], ys[-1]))
                out["edge_hi"] = float(max(ys[0], ys[-1]))
        except Exception as e:                  # noqa: BLE001
            out["why_lm"] = ("EXC:" + str(e))[:40]

        try:                                    # --- 凍結版（研究1と同一コード）
            fit = fit_beat(t, y)
            ix = si_ri_from_fit(fit)
            out.update(dt_v1_ms=ix["dt_s"] * 1000.0, ri_v1=ix["ri"],
                       nrmse_v1=float(fit.get("nrmse", np.nan)),
                       ok_v1=int(bool(fit.get("ok", False))))
        except Exception as e:                  # noqa: BLE001
            out["why_v1"] = ("EXC:" + str(e))[:40]

        for tag, route in (("v2", "skew"), ("v2g", "gamma")):
            try:                                # --- 第2版
                r = pda2.decompose(t, y, fs, route=route)
                out[f"ok_{tag}"] = int(bool(r.get("ok")))
                out[f"dt_{tag}_ms"] = r.get("dt_ms", np.nan)
                out[f"ri_{tag}"] = r.get("ri", np.nan)
                out[f"dtse_{tag}_ms"] = r.get("dt_se_ms", np.nan)
                out[f"dps_{tag}_ms"] = r.get("dps_ms", np.nan)   # Goswami 2010
                out[f"dtsp_{tag}_ms"] = r.get("dt_spread_ms", np.nan)   # 競合解の ΔT の広がり
                # 成分ピークの絶対時刻・高さ（役割の割り当てを事後に検算できるように）
                pk = r.get("peaks") or []
                lmr = r.get("landmarks") or {}
                out[f"tf_{tag}_ms"] = np.nan
                out[f"tr_{tag}_ms"] = np.nan
                if pk and r.get("dt_ms") is not None and np.isfinite(r.get("dt_ms", np.nan)):
                    # 反射波 = 前進波 + ΔT。前進波はピーク時刻が最小の成分
                    tf = min(p_[0] for p_ in pk)
                    out[f"tf_{tag}_ms"] = tf * 1000.0
                    out[f"tr_{tag}_ms"] = tf * 1000.0 + r["dt_ms"]
                out[f"sys_lm_{tag}_ms"] = float(lmr.get("sys_t", np.nan)) * 1000.0
                out[f"gap_{tag}_ms"] = r.get("ref_gap_ms", np.nan)      # 反射波と拡張期鍵点の距離
                out[f"marg_{tag}_ms"] = r.get("ref_margin_ms", np.nan)  # 2番目の候補との差
                out[f"rise_{tag}"] = r.get("ri_se", np.nan)   # RI の標準誤差（ガンマの rise 母数ではない）
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
    if limit and limit < len(ppg):
        # 先頭 N 名ではなく等間隔に N 名。PWDB は被験者が年齢順に並んでいる可能性があり、
        # 先頭だけ取ると 1 つの年齢層に偏る。年齢層内の順位相関が判定なので全層が要る
        step = max(1, len(ppg) // limit)
        ppg = ppg.iloc[::step].iloc[:limit]
        print(f"  --limit: {step} 名おきに {len(ppg)} 名を取る（全年齢層を含めるため）", flush=True)
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
    d["pda2_version"] = pda2.code_version()      # 27番が照合する
    # 環境も記録する。scipy の版が違うと最適化の最終桁が変わり、閾値際の採否が数例で入れ替わりうる。
    # 論文の再現性の記述と、Mac と雲で結果が違ったときの切り分けに使う
    import platform, scipy
    d["python_version"] = platform.python_version()
    d["numpy_version"] = np.__version__
    d["scipy_version"] = scipy.__version__
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
    n_ages_full = len(ages)
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

    # ---- 拍の切り出しの前提
    if "edge_lo" in d and d["edge_lo"].notna().any():
        lo_ = float(np.nanmedian(d["edge_lo"])); hi_ = float(np.nanmedian(d["edge_hi"]))
        print(f"\n{'-' * 78}\n1a. 拍の切り出し（前処理の足→足基線の前提）\n{'-' * 78}")
        print(f"  正規化後の波形の両端の値（中央値）: 低い側 {lo_:.4f} / 高い側 {hi_:.4f}")
        print("  どちらも 0 に近ければ、拍は足で切り出されており基線の前提が成り立つ。")
        if hi_ > 0.15:
            print("  **高い側が 0.15 を超えている。拍が足で切り出されていない疑いがある。**")
            print("  この場合 RI（振幅の比）が基線の傾きに引きずられる。ΔT は時刻の差なので影響は小さい。")

    # ---- 不採用の理由
    print(f"\n{'-' * 78}\n1b. 不採用の理由（第2版）\n{'-' * 78}")
    print("  採択率が低いとき最初に見る表。no_landmarks はデータ側に鍵点が無い（型4〜5）拍で、")
    print("  分解の失敗ではない。landmark_or_fit は Wang の規準（NRMSE・Errx・Erry）の不合格。")
    for key, lab, _dtc, _ric, okc in METHODS:
        wc = f"why_{key}"
        if wc not in d or okc is None:
            continue
        g = d[d[okc] != 1]
        if not len(g):
            print(f"{lab:<26} 不採用なし")
            continue
        vc = g[wc].fillna("").replace("", "(記録なし)").value_counts()
        line = "  ".join(f"{k} {v}（{100.0 * v / max(n, 1):.1f}%）" for k, v in vc.items())
        print(f"{lab:<26} {line}")

    # ---- A. 各手法の合格例
    print(f"\n{'-' * 78}\nA. 各手法が合格とした例だけで判定（20番・23番と同じ扱い）\n{'-' * 78}")
    print("  行の役割: 「副次」「（記述）」と書いていない行が事前指定の主要比較（12 行）。")
    print("  多重性の調整はしない。**主要行のうち一つでも通れば良い、という読み方をしない**こと。")
    print("  読み方は docs/research/gate0_rules_v2.md の表に従う（結果を見る前に固定してある）。")
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
            line += _verdict(j, sign, n_ages_full)
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
            v = _verdict(j, sign, n_ages_full)
            line += f"{j['med_abs']:>9.3f}{j['n_ok']:>5}/{j['n_ages']:<3}{v:>7}"
        print(line)
    print("  A だけ成立して B・C が不成立なら、それは難しい拍を捨てた効果であって")
    print("  指標そのものの改善ではない。3 段を必ず一緒に読むこと。")
    short = [(k, v) for k, v in summary.items() if v and v["n_ages"] < n_ages_full]
    if short:
        print(f"\n  **層不足（* 印）**: 判定は「有限の ρ を持つ層すべて」で下している。層が減った手法は")
        print(f"  少ない層で全一致すればよいので**通りやすくなる**（全 {n_ages_full} 層）。")
        for k, v in short:
            print(f"    {k}  {v['n_ok']}/{v['n_ages']} 層")
        print("  * の付いた「成立」を、層が揃った「成立」と同列に読んではいけない。")

    # ---- 波形型ごと
    if "klass_own" in d and d["klass_own"].notna().any():
        print(f"\n{'-' * 78}\n2a. 波形型ごとの p1 と収縮期ピークの一致\n{'-' * 78}")
        print("  Hellqvist の p1 は『6つの波形型すべてで機能した』とされる。切痕の無い型でも")
        print("  収縮期ピークを定義できるなら、我々の未解決問題（型3で ΔT 誤差 約30 ms）に効く。")
        print(f"{'型':<6}{'n':>7}{'p1が取れた率':>13}{'|p1 − S| 中央値':>16}"
              f"{'Am_b/Am_p1 中央値':>18}{'ΔT p1基準 中央値':>17}")
        for k in sorted(d["klass_own"].dropna().unique().tolist()):
            g = d[d["klass_own"] == k]
            got = float(g["p1_t_ms"].notna().mean()) if "p1_t_ms" in g else np.nan
            gap = (float(np.nanmedian(np.abs(g["p1_t_ms"] - g["sys_own_ms"])))
                   if "p1_t_ms" in g and g["p1_t_ms"].notna().any() else np.nan)
            r_ = (float(np.nanmedian(g["amb_amp1"])) if g["amb_amp1"].notna().any() else np.nan)
            dp = (float(np.nanmedian(g["dt_p1_ms"])) if g["dt_p1_ms"].notna().any() else np.nan)
            print(f"{int(k):<6}{len(g):>7}{got:>12.1%}{gap:>14.1f} ms"
                  f"{r_:>18.4f}{dp:>14.0f} ms")

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
        print("  型3（切痕なし・肩で代用）は合成波でも 30 ms 前後の誤差が残る。ここが実際に")
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
            ver = _verdict(j, -1, n_ages_full)
            print(f"{name:<20}{len(g):>8}{100.0 * g[okc].mean():>8.1f}%"
                  f"{dtm:>14}{med:>18}{ver:>8}")

    # ---- 因子主効果
    if "var_pwv" in d:
        print(f"\n{'-' * 78}\n3. 振った因子ごとの主効果（年齢層内。+1 と −1 の平均差 ÷ 層平均 [%]）"
              f"\n{'-' * 78}")
        print(f"{'指標':<20}" + "".join(f"{M.FACTOR_LABEL[f]:>12}" for f in M.FACTORS))
        skipped = []
        for col, lab, okc in IDX_FOR_FACTORS:
            src = _sub(d, okc, "own")
            if col not in src or _n_strata(src, col) == 0:
                continue
            # 主効果は「層平均で割った %」なので、0 をまたぐ量では発散して意味を持たない
            # （DPS = σ_reflected − σ_forward は符号が変わりうる）。比を出さずに飛ばす
            v_ = src[col].to_numpy(float)
            v_ = v_[np.isfinite(v_)]
            if v_.size and abs(np.mean(v_)) < 0.5 * np.std(v_):
                skipped.append(lab)
                continue
            e, _r = M._factor_effects(src, col)
            print(f"{lab:<20}" + "".join(f"{v:>+12.1f}" if np.isfinite(v) else f"{'—':>12}"
                                         for v in e))
        if skipped:
            print(f"  （{'・'.join(skipped)}: 平均が 0 に近く符号が変わりうる量なので、")
            print("    層平均で割った % は定義できない。飛ばした）")
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
    print(f"\n被験者別の結果: {p}（pda2 版 {pda2.code_version()}）")
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
        # 27番の通し検算用に、模擬の被験者別 CSV を残す（実データの CSV とは別名）
        OUT.mkdir(parents=True, exist_ok=True)
        d.to_csv(OUT / "_selftest_pwdb_compare.csv", index=False)
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
