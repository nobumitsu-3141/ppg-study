#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""論文3（実機での同定性）― 母集団 840 例に 32番・34番の規準をそのまま当てる。

目的
----
事前登録 `docs/research/sap_3_identifiability_v0.md`（**未凍結**）の §3〜§8 を実行する。
32番（予備的検討 20 例）が結果を見る前に決めた規準

    同定できる = 同定率の症例中央値 ≥ 0.70 かつ 隣接ウィンドウの lag-1 自己相関の症例中央値 ≥ 0.30

を、母集団 840 例（874 − パイロット 20 − 研究1 の開発 15、重複 1）で当て直す。
**この台本は規準も指標の定義も決めない。**32番・34番の関数をそのまま呼び、
事前登録に書かれた閾値を当てるだけである（§13「規準とパラメータを書き直さない」）。

規約（結果を見る前に固定。括弧内は事前登録の節）
------------------------------------------------
症例   `data/target_cases.csv`（874 例）を caseid 昇順に並べ、パイロット 20 例と
       研究1 の開発 15 例（重複 caseid 97 の 1 例）を外した 840 例すべて（§3）。
       乱数種は使わない。**結果を見て症例を足したり外したりしない。**
       取得や解析に失敗した症例も分母に残し、数を報告する（§3「差し替えをしない」）。
段階1  解析できるウィンドウをすべて使う指標 ― 特徴点法の ΔT・早期振幅比 Am_b/Am_p1・
       PWTT（陽性対照）。32番の `extract_case`・`case_summary` をそのまま呼ぶ（§6）。
段階2  分解由来の 6 行 ― 34番の抜き取り規則（記録の 20%・50%・80% から連続 6 ウィンドウを
       3 ブロック、計 18 ウィンドウ）で、凍結版 2 カーネル・第2版 歪みガウス・第2版 ガンマの
       ΔT と RI（§6）。ブロックの選択は 34番の `pick_blocks` を呼ぶ。
同定率 特徴点法・早期振幅比・PWTT は「有限な値になったウィンドウ ÷ 解析できるウィンドウ」、
       分解由来は「その版の採否を通ったウィンドウ（採択率）÷ ブロックのウィンドウ」（§7）。
       分解由来の「有限な値になった割合」も併記するが、そちらは記述である（§7）。
判定   症例中央値の点推定で行う。症例を単位とした 95% 信頼区間を併記するが判定に使わない（§7）。
       陽性対照 PWTT の自己相関の症例中央値が 0.50 に達しなければ**表全体を無効**とする（§7）。
環境   Python 3.9.6・NumPy 2.0.2・SciPy 1.13.1・pandas 2.3.3・vitaldb 1.5.8（§10・`CLAUDE.md` §4）。
       一致しなければ既定で止まる。`--allow-env-mismatch` で走らせた場合、出力は別名になり
       すべて「環境依存」と記され、主要評価の判定を出さない（§8 の環境依存の行）。
凍結   母集団の症例を処理するには `--sap-tag TAG` が要る。タグが実在し、作業中の事前登録が
       そのタグの版と同一であることを確かめる。**凍結より前に新しい症例を解析しない**（§15）。
       パイロット 20 例の再現（`--pilot`）はタグを要さない。既に 32番・34番が解析した症例で、
       **新しい解析ではなく再現の確認**だからである。

データ
------
`analysis/data/target_cases.csv`（00番・01番が作る 874 例）と VitalDB の波形
（SNUADC/PLETH・SNUADC/ECG_II。32番の `_vitaldb_loader`）。`analysis/data/` は git に
入っていないので、**この台本は取得できる 1 台でしか走らない**（`CLAUDE.md` §4）。
症例ごとの結果は `analysis/data/paper3/` に置き、環境と台本の版を添えて記録する。
別の環境で作った症例が混ざるのを防ぐため、記録が食い違えば止まる（42番と同じ規則）。

計算するもの
------------
症例ごとに 段階1 と 段階2 の要約を出し、`--summarise` で症例中央値・95% 信頼区間・
事前規準の合否を組み立てる。主要評価は §5 の 8 行（特徴点法 ΔT・早期振幅比・
分解 3 条件 × ΔT と RI）と陽性対照 1 行。それ以外はすべて「参考」と記す。
34番が並べた**文献 6 本の分解は入れない**（§5「主要評価に入れない」）。必要なら 34番を回す。

出力
----
    analysis/data/paper3/cases/case_{id}.json     症例ごとの値・環境・台本の版・所要時間
    analysis/data/paper3/windows/case_{id}.csv    段階1 のウィンドウごと（32番の書式）
    analysis/data/paper3/blocks/case_{id}.csv     段階2 のウィンドウごと
    docs/research/results/44_paper3_outcome.txt   §8 の表（行ごとに 成立／不成立）
    docs/research/results/44_paper3_per_case.csv  症例ごと
    docs/research/results/44_paper3_outcome.json  合否（感度解析との突き合わせに使う）

使い方
------
自己検査（合成データのみ。ネットワークも `analysis/data/` も要らない）

    python3 analysis/scripts/44_paper3_identifiability.py --selftest

版・凍結・進み具合を見る

    python3 analysis/scripts/44_paper3_identifiability.py --check

母集団の一覧を書き出す（除外の理由つき）

    python3 analysis/scripts/44_paper3_identifiability.py --list-cases /tmp/pool.csv

パイロット 20 例で再現を確かめ、所要時間を測る（タグは要らない）

    python3 analysis/scripts/44_paper3_identifiability.py --pilot --jobs 4
    python3 analysis/scripts/44_paper3_identifiability.py --pilot --estimate

凍結後に母集団 840 例を回して集計する

    python3 analysis/scripts/44_paper3_identifiability.py --run --sap-tag sap3-v0.1 --jobs 8
    python3 analysis/scripts/44_paper3_identifiability.py --summarise

終了コード 0 = 正常、1 = 自己検査の失敗または集計に★がある、2 = 版・凍結・入力の不備、
3 = 症例ごとの記録が今の環境と食い違う（作り直しが要る）。
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import re
import subprocess
import sys
import time
import warnings
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent            # analysis/
REPO = ROOT.parent
sys.path.insert(0, str(ROOT))


def _load(stem: str, name: str):
    """数字で始まる台本を名前で読み込む（import 文では書けない）。34番・45番と同じ手口。"""
    spec = importlib.util.spec_from_file_location(name, Path(__file__).resolve().parent / stem)
    m = importlib.util.module_from_spec(spec)
    sys.modules[name] = m
    spec.loader.exec_module(m)
    return m


# 34番は読み込むときに 32番・33番を `_load` する。同じ 32番を二度読み込まないよう、
# 34番が持っているものを使う（別々に読み込むと定数の同一性の検査が意味を失う）。
M34 = _load("34_vitaldb_methods_compare.py", "m34")
M32 = M34.M32
M42 = _load("42_rebuild_on_new_mac.py", "m42")           # 版の読み取り（`modver`）
M43 = _load("43_paper3_sample_size.py", "m43")           # 信頼区間の出し方

from src import pda2                                                        # noqa: E402
from src.pda import fit_beat                                                # noqa: E402
from src.indices import si_ri_from_fit                                      # noqa: E402

DATA = ROOT / "data"
OUT = DATA / "paper3"
RESULTS = REPO / "docs" / "research" / "results"
SAP_REL = "docs/research/sap_3_identifiability_v0.md"
SAP1_REL = "docs/research/sap_v0.md"

# ---------------------------------------------------------------- 事前登録から写した値
# 主環境（§10・`CLAUDE.md` §4）。42番の REF と同じ 5 つだが、**42番は vitaldb だけを
# 止める違いとして扱うのに対し、論文3 は 5 つすべての一致を求める**（§10「1 台で回す」）。
REF = dict(M42.REF)
SOURCE_N = 874          # 抽出母集団（`data/target_cases.csv`。§3）
POOL_N = 840            # 874 − 20 − 15 ＋ 重複 1（§3）
# パイロット 20 例（32番・34番。§3 が caseid を列挙している。32番の seed 0 の抽出と一致する）
PILOT_CASES = (97, 217, 418, 1030, 1602, 1826, 3150, 3170, 3449, 3537,
               3846, 3973, 4012, 4048, 4617, 5109, 5319, 5809, 5973, 6163)
# 研究1 のパイプライン確定に使った 15 例（`sap_v0.md` §3.1。§3 が引いている）
DEV_CASES = (17, 19, 22, 25, 26, 29, 34, 38, 52, 60, 68, 70, 83, 94, 97)
WHY_PILOT = "パイロット20例"
WHY_DEV = "研究1の開発15例"

# 規準は 32番の定数をそのまま使う（書き写さない。§13）
GATE_ID = M32.GATE_ID_RATE            # 0.70
GATE_AC = M32.GATE_AUTOCORR           # 0.30
GATE_CTL = M32.GATE_CONTROL           # 0.50
MIN_GOOD = M32.MIN_GOOD               # 解析できるウィンドウの条件（SQI 通過拍 8 以上）
MIN_PAIRS_WIN = M32.MIN_PAIRS         # 段階1 の自己相関に要る隣接対（10）
# 段階2 の自己相関に要る隣接対。**34番の `summarize` が 8 を渡している**（事前登録 §3 の
# 本文は 32番の 10 を引いているが、分解由来の行は 34番の規則に従う旨が §6 にある）。
MIN_PAIRS_BLOCK = 8
N_BLOCKS = M34.N_BLOCKS               # 3
BLOCK_LEN = M34.BLOCK_LEN             # 連続 6 ウィンドウ
NAN = float("nan")
# 段階2 でブロックが取れない症例の理由。取得の失敗と違って**やり直しても変わらない**ので、
# 記録に「片づいた」と印を付けて取り直さない。数は分母つきで報告する（§3）
E_NO_BLOCK = "ブロックが取れない（連続して解析できるウィンドウが足りない）"

# 主要評価の 8 行（§5）。(列, 表示名, 段階, 採否列)
# 採否列があるものは、同定率に**採択率**を使う（§7）。無いものは有限な値になった割合。
PRIMARY_ROWS = [
    ("ens_dt_lm_ms", "特徴点法の ΔT（平均拍）",            1, None),
    ("ens_amb",      "早期振幅比 Am_b/Am_p1（平均拍）",     1, None),
    ("dt_v1_ms",     "分解 ΔT 凍結版 2 カーネル",           2, "ok_v1"),
    ("ri_v1",        "分解 RI 凍結版 2 カーネル",           2, "ok_v1"),
    ("dt_v2_ms",     "分解 ΔT 第2版 歪みガウス",            2, "ok_v2"),
    ("ri_v2",        "分解 RI 第2版 歪みガウス",            2, "ok_v2"),
    ("dt_v2g_ms",    "分解 ΔT 第2版 ガンマ",                2, "ok_v2g"),
    ("ri_v2g",       "分解 RI 第2版 ガンマ",                2, "ok_v2g"),
]
CONTROL_ROW = ("pwtt_ms", "PWTT（陽性対照）", 1, None)
# 参考（§5 で主要評価に入れないと決めた行と、§9 の記述）
REFERENCE_ROWS = [
    ("ens_dt1_ms", "型1 だけの ΔT（平均拍）",                1, None),
    ("dt_lm_ms",   "特徴点法 ΔT（ブロックのウィンドウ）",    2, None),
    ("ri_lm",      "特徴点法 RI（ブロックのウィンドウ）",    2, None),
    ("amb",        "早期振幅比（ブロックのウィンドウ）",      2, None),
    ("b_pwtt_ms",  "PWTT（ブロックのウィンドウ）",            2, None),
]
# 段階2 のウィンドウごとの表から症例ごとにまとめる列
BLOCK_COLS = ["dt_v1_ms", "ri_v1", "dt_v2_ms", "ri_v2", "dt_v2g_ms", "ri_v2g",
              "dt_lm_ms", "ri_lm", "amb", "b_pwtt_ms"]
BLOCK_OK_COLS = ["ok_v1", "ok_v2", "ok_v2g"]

# §8「結果の読み方」。合否ごとに何を書くかを事前に決めてある。表に写して出す
READING = {
    ("ens_dt_lm_ms", True): "パイロットの不合格は少数例の結果であったと書き、"
                            "「モニタ波形では特徴点を同定できない」という主張を取り下げる（§8）",
    ("ens_dt_lm_ms", False): "主張は維持する。同定率の症例中央値と 95% 信頼区間、"
                             "型4 の割合を添えて書く（§8）",
    ("ens_amb", True): "パイロットが再現したと書く。ただし自己相関はパイロットで規準の境界に"
                       "あった（1.5.8 で 0.36・1.7.2 で 0.2994）ので境界であることを併記する（§8）",
    ("ens_amb", False): "パイロットの合格は境界での結果であったと書き、研究1 の探索的解析"
                        "（35番・36番）が前提にした可測性に留保を付ける（§8）",
}
READING_DECOMP_PASS = ("予測どおりであり新しい情報ではない。分解は拡張期の特徴点が無くても"
                       "値を返すので同定性の規準では合格する。**妥当性の証拠ではない**（§8）")
READING_DECOMP_FAIL = ("34番の探索（同定率 ≈ 1.00）が 20 例に固有だったことになるので、"
                       "その旨を書く（§8）")


# ================================================================ 版と環境
def versions() -> dict:
    """今の環境の版。読み取りは 42番の `modver`（`__version__` を当てにしない）。"""
    import platform
    got = {"python": platform.python_version()}
    for mod in ("numpy", "scipy", "pandas", "vitaldb"):
        got[mod] = M42.modver(mod)
    return got


def env_mismatch(got: dict, ref: dict | None = None) -> list:
    """主環境と違う項目。論文3 は 5 つすべての一致を求める（§10）。"""
    ref = REF if ref is None else ref
    return [(k, got.get(k) or "未導入", w) for k, w in ref.items() if got.get(k) != w]


def script_sha() -> str:
    """この台本の中身の指紋。症例ごとの記録に添え、台本が変わったら作り直す。"""
    return hashlib.sha256(Path(__file__).read_bytes()).hexdigest()[:12]


def fingerprint(got: dict | None = None) -> dict:
    got = versions() if got is None else got
    return {"env": dict(got), "pda2": pda2.code_version(), "script": script_sha()}


# ================================================================ 症例の母集団（§3）
def build_pool(table=None, target_csv: Path | None = None):
    """母集団の一覧。返り値 (DataFrame, エラー文)。乱数は使わない。

    列は caseid・included・exclude_reason。32番の `select_cases` と同じ絞り込み
    （PLETH と ECG のある症例）を当ててから caseid 昇順に並べ、除外の理由を書く。
    """
    import pandas as pd
    if table is None:
        p = Path(target_csv) if target_csv else DATA / "target_cases.csv"
        if not p.exists():
            return None, (f"{p} が無い。00番（症例一覧の取得）と 01番（対象症例の一覧）を"
                          "先に走らせること。取得できる機械でしか走らない（CLAUDE.md §4）")
        table = pd.read_csv(p)
    if "caseid" not in table:
        return None, "caseid の列が無い"
    m = np.ones(len(table), bool)
    for c in ("pleth", "ecg"):
        if c in table:
            m &= table[c].astype(str).str.lower().isin(["true", "1"]).to_numpy()
    ids = sorted(int(c) for c in table.loc[m, "caseid"].unique())
    rows = []
    for cid in ids:
        why = []
        if cid in PILOT_CASES:
            why.append(WHY_PILOT)
        if cid in DEV_CASES:
            why.append(WHY_DEV)
        rows.append({"caseid": cid, "included": not why, "exclude_reason": "・".join(why)})
    return pd.DataFrame(rows), None


def pool_counts(pool) -> dict:
    """母集団の引き算。重複（caseid 97）は 1 例として数える。"""
    ids = set(int(c) for c in pool["caseid"])
    pil = ids & set(PILOT_CASES)
    dev = ids & set(DEV_CASES)
    return {"n_source": len(ids), "n_pilot": len(pil), "n_dev": len(dev),
            "n_overlap": len(pil & dev), "n_excluded": len(pil | dev),
            "n_pool": int(pool["included"].sum())}


def pool_ids(pool) -> list:
    return [int(c) for c in pool.loc[pool["included"], "caseid"]]


def pool_arithmetic_lines(c: dict, src: Path | None = None) -> list:
    ov = sorted(set(PILOT_CASES) & set(DEV_CASES))
    src = (DATA / "target_cases.csv") if src is None else Path(src)
    return [
        f"  抽出母集団            {c['n_source']:>4d} 例（{M43.rel(src)}・caseid 昇順・§3）",
        f"  − パイロット          {c['n_pilot']:>4d} 例（32番・34番が解析した症例）",
        f"  − 研究1 の開発        {c['n_dev']:>4d} 例（sap_v0.md §3.1）",
        f"  ＋ 重複を二重に引かない {c['n_overlap']:>3d} 例（caseid {', '.join(str(x) for x in ov)}）",
        f"  = 解析対象            {c['n_pool']:>4d} 例",
    ]


def check_pilot_against_32(table=None, target_csv: Path | None = None):
    """§3 が列挙するパイロット 20 例が、32番の抽出（seed 0）と一致するかを確かめる。

    返り値 (一致したか, 説明)。入力が無ければ (None, 理由)。
    """
    import pandas as pd
    if table is None:
        p = Path(target_csv) if target_csv else DATA / "target_cases.csv"
        if not p.exists():
            return None, f"{p} が無いので照合できない"
        table = pd.read_csv(p)
    got = M32.select_cases(M32.N_CASES, M32.SEED, table=table)
    return (got == sorted(PILOT_CASES)), f"32番の抽出 {got[:5]}…"


def ids_in_document(path: Path, pattern: str):
    """文書に書かれた caseid の並びを読む（定数の写し間違いを機械で見つけるため）。"""
    if not path.exists():
        return None
    m = re.search(pattern, path.read_text(encoding="utf-8"), re.S)
    if not m:
        return None
    return sorted(int(x) for x in re.findall(r"\d+", m.group(1)))


# ================================================================ 凍結の確認（§15）
def freeze_state(tag: str | None, repo: Path = REPO, rel: str = SAP_REL) -> dict:
    """タグが実在し、作業中の事前登録がそのタグの版と同一かを見る。

    `git tag -l TAG` が空でないこと、`git diff --quiet TAG -- rel` が終了コード 0 で
    あることの 2 つで判定する。**凍結より前に新しい症例を解析しない**（事前登録 §15）。
    """
    out = {"tag": tag, "tag_exists": False, "same": False, "ok": False, "why": ""}
    if not tag:
        out["why"] = "--sap-tag が無い。事前登録を凍結し、そのタグを渡すこと"
        return out
    try:
        r = subprocess.run(["git", "tag", "-l", tag], cwd=str(repo),
                           capture_output=True, text=True, timeout=60)
    except Exception as e:      # noqa: BLE001
        out["why"] = f"git を実行できない: {e}"
        return out
    if r.returncode != 0:
        out["why"] = f"git tag が失敗した: {r.stderr.strip()[:80]}"
        return out
    out["tag_exists"] = bool(r.stdout.strip())
    if not out["tag_exists"]:
        out["why"] = f"タグ {tag} が無い（凍結の commit にタグを付けること）"
        return out
    d = subprocess.run(["git", "diff", "--quiet", tag, "--", rel], cwd=str(repo),
                       capture_output=True, text=True, timeout=60)
    out["same"] = (d.returncode == 0)
    if not out["same"]:
        out["why"] = f"作業中の {rel} がタグ {tag} の版と違う（凍結した版で回すこと）"
        return out
    out["ok"] = True
    return out


# ================================================================ 段階2 の 1 拍
def our_methods_on_beat(y, fs: float) -> dict:
    """平均拍 1 拍に、我々の 3 版の分解と特徴点法を当てる。

    **34番の `methods_on_beat` から、文献 6 本の再現（33番の呼び出し）だけを外したもの。**
    事前登録 §5 が「文献 6 本の分解は主要評価に入れない」と決めており、Wang 2013 の
    当てはめだけで 1 ウィンドウ十数秒かかるためである（文献の行が要るときは 34番を回す）。
    列名・順序・例外の扱いは 34番と同じにしてある。自己検査
    「段階2 の 1 拍が 34番の `methods_on_beat` と一致する」で毎回突き合わせる。
    """
    out = {}
    t = np.arange(len(y)) / fs
    for tag, route in (("v2", "skew"), ("v2g", "gamma")):
        try:
            r = pda2.decompose(t, y, fs, route=route)
            out[f"ok_{tag}"] = int(bool(r.get("ok")))
            out[f"dt_{tag}_ms"] = float(r.get("dt_ms", NAN))
            out[f"ri_{tag}"] = float(r.get("ri", NAN))
            out[f"why_{tag}"] = str(r.get("reason", ""))[:24]
        except Exception as e:      # noqa: BLE001
            out[f"ok_{tag}"], out[f"dt_{tag}_ms"], out[f"ri_{tag}"] = 0, NAN, NAN
            out[f"why_{tag}"] = ("EXC:" + str(e))[:24]
    try:
        fit = fit_beat(t, y)
        ix = si_ri_from_fit(fit)
        out["ok_v1"] = int(bool(fit.get("ok", False)))
        out["dt_v1_ms"] = float(ix["dt_s"] * 1000.0) if ix["dt_s"] > 0 else NAN
        out["ri_v1"] = float(ix["ri"])
    except Exception:      # noqa: BLE001
        out["ok_v1"], out["dt_v1_ms"], out["ri_v1"] = 0, NAN, NAN
    f = M32._beat_features(y, fs)
    out.update({"klass": f["klass"], "prom": f["prom"], "dt_lm_ms": f["dt_lm_ms"], "amb": f["amb"]})
    try:
        ys, _ = pda2.preprocess(t, np.asarray(y, float), fs)
        lm = pda2.find_landmarks(t, ys) if ys is not None else None
        out["ri_lm"] = (float(lm["dia_v"] / lm["sys_v"]) if lm is not None and lm["klass"] in (1, 3)
                        and np.isfinite(lm["dia_v"]) and lm["sys_v"] > 0 else NAN)
    except Exception:      # noqa: BLE001
        out["ri_lm"] = NAN
    return out


def block_window(caseid: int, t0: float, seg_p, seg_e) -> dict:
    """段階2 の 1 ウィンドウ（34番の `_window_task` と同じ流れ。平均拍は 34番の関数）。"""
    out = {"caseid": int(caseid), "t0": float(t0)}
    y, n_good = M34.ensemble_beat(seg_p, seg_e)
    out["n_good"] = int(n_good)
    if y is None:
        return out
    try:
        out.update(our_methods_on_beat(y, M32.FS))
    except Exception as e:      # noqa: BLE001
        out["err"] = ("EXC:" + str(e))[:80]
    return out


def blocks_from_stage1(df, n_blocks: int = N_BLOCKS, block_len: int = BLOCK_LEN) -> list:
    """段階1 のウィンドウごとの表からブロックを選ぶ（34番の `pick_blocks` を呼ぶ）。

    34番の `case_tasks` は解析できるウィンドウを数え直すが、その判定は 32番の
    `window_landmarks` が入れる `n_good` と同じ計算である（同じ `segment_beats`・`sqi`・
    同じ `t0` の刻み）。段階1 を先に回してあるので数え直さない。**同じブロックが選ばれる
    ことは自己検査で 34番の `case_tasks` と突き合わせる。**
    """
    ok = (df["n_good"].to_numpy(float) >= MIN_GOOD)
    return M34.pick_blocks(ok, n_blocks, block_len)


# ================================================================ 症例ごとの処理
def stage1_case(caseid: int, loader=None, win_dir: Path | None = None):
    """段階1。32番の `extract_case`（ウィンドウごと）と `case_summary`（症例ごと）。"""
    win_dir = (OUT / "windows") if win_dir is None else win_dir
    loader = M32._vitaldb_loader if loader is None else loader
    cid, df, err = M32.extract_case(caseid, loader=loader, out_dir=win_dir)
    if err:
        return None, None, err
    s = M32.case_summary(df)
    return df, s, None


def stage2_case(caseid: int, df, loader=None, blk_dir: Path | None = None,
                n_blocks: int = N_BLOCKS, block_len: int = BLOCK_LEN):
    """段階2。段階1 の表からブロックを選び、そのウィンドウに 3 版の分解を当てる。"""
    import pandas as pd
    blk_dir = (OUT / "blocks") if blk_dir is None else blk_dir
    loader = M32._vitaldb_loader if loader is None else loader
    idx = blocks_from_stage1(df, n_blocks, block_len)
    if not idx:
        return None, None, E_NO_BLOCK
    t0s = df["t0"].to_numpy(float)
    try:
        arrays = loader(caseid)
    except Exception as e:      # noqa: BLE001
        return None, None, f"取得失敗: {e}"
    pleth, ecg = arrays["pleth"], arrays["ecg"]
    fs = M32.FS
    rows = []
    for bi, block in enumerate(idx):
        for i in block:
            t0 = float(t0s[i])
            i0, i1 = int(t0 * fs), int((t0 + M32.WIN_S) * fs)
            r = block_window(caseid, t0, np.nan_to_num(np.asarray(pleth[i0:i1], float)),
                             np.nan_to_num(np.asarray(ecg[i0:i1], float)))
            r["block"] = bi
            rows.append(r)
    win = pd.DataFrame(rows)
    # PWTT は段階1 で同じウィンドウについて計算済み（32番の `window_landmarks`）。
    # 34番は `_pwtt_for` で計算し直すが、中身は同じ関数である。列名は段階1 の
    # `pwtt_ms`（解析できるウィンドウ全部）と区別するため b_ を付ける
    pw = {float(a): (b, c) for a, b, c in zip(df["t0"], df["pwtt_ms"], df["hr"])}
    win["b_pwtt_ms"] = [pw.get(float(t), (NAN, NAN))[0] for t in win["t0"]]
    win["hr"] = [pw.get(float(t), (NAN, NAN))[1] for t in win["t0"]]
    blk_dir.mkdir(parents=True, exist_ok=True)
    win.to_csv(blk_dir / f"case_{caseid}.csv", index=False)
    return win, block_summary(win), None


def block_summary(win) -> dict:
    """段階2 の症例ごとの要約（34番の `summarize` と同じ計算を、我々の行だけで）。"""
    g = win.sort_values("t0")
    t0 = g["t0"].to_numpy(float)
    out = {"n_block_windows": int(len(g)),
           "n_blocks": int(g["block"].nunique()) if "block" in g else 0,
           "b_type4": (float(np.mean(g["klass"].to_numpy(float) >= 4))
                       if len(g) and "klass" in g else NAN)}
    for c in BLOCK_COLS:
        v = g[c].to_numpy(float) if c in g else np.full(len(g), NAN)
        out[f"id_{c}"] = float(np.isfinite(v).mean()) if v.size else NAN
        r, npair = M32.lag1_autocorr(t0, v, min_pairs=MIN_PAIRS_BLOCK)
        out[f"ac_{c}"], out[f"npair_{c}"] = r, int(npair)
        fin = v[np.isfinite(v)]
        out[f"med_{c}"] = float(np.median(fin)) if fin.size else NAN
        out[f"cv_{c}"] = (float(np.std(fin) / abs(np.mean(fin)))
                          if fin.size >= 3 and np.mean(fin) != 0 else NAN)
    for okc in BLOCK_OK_COLS:
        v = g[okc].to_numpy(float) if okc in g else np.full(len(g), NAN)
        out[f"acc_{okc}"] = float(np.nanmean(v)) if np.isfinite(v).any() else NAN
    return out


def process_case(caseid: int, stage: str = "all", loader=None, out_dir: Path | None = None,
                 n_blocks: int = N_BLOCKS, block_len: int = BLOCK_LEN, got: dict | None = None) -> dict:
    """1 症例を処理して記録を作る。失敗は理由を残す（黙って落とさない。§3）。"""
    out_dir = OUT if out_dir is None else out_dir
    rec = {"caseid": int(caseid), "stage_requested": stage, "error": None,
           "stage1": None, "stage2": None}
    rec.update(fingerprint(got))
    t0 = time.time()
    df = None
    # 波形は症例ごとに 1 度だけ取得し、段階1 と段階2 で使い回す（32番も 34番も毎回 load_case を
    # 呼ぶので、そのままだと 1 症例あたり 2 度取得することになる。lab_log 追記115）
    base = M32._vitaldb_loader if loader is None else loader
    held = {}

    def once(cid):
        if "a" not in held:
            held["a"] = base(cid)
        return held["a"]

    loader = once
    if stage in ("1", "all", "2"):
        # 段階2 だけを頼まれても段階1 のウィンドウごとの表が要る（ブロックの選択に使う）
        df, s1, err = stage1_case(caseid, loader=loader, win_dir=out_dir / "windows")
        dt = time.time() - t0
        if err:
            rec["error"] = err
            rec["stage1"] = {"ok": False, "t_s": round(dt, 2), "error": err}
            write_case(rec, out_dir)
            return rec
        rec["stage1"] = {"ok": True, "t_s": round(dt, 2), "summary": s1,
                         "n_windows": int(len(df)),
                         "n_analyzable": int((df["n_good"] >= MIN_GOOD).sum())}
    if stage in ("2", "all"):
        t1 = time.time()
        _win, s2, err2 = stage2_case(caseid, df, loader=loader, blk_dir=out_dir / "blocks",
                                     n_blocks=n_blocks, block_len=block_len)
        dt2 = time.time() - t1
        if err2:
            rec["stage2"] = {"ok": False, "t_s": round(dt2, 2), "error": err2,
                             "settled": err2 == E_NO_BLOCK}
            rec["error"] = rec["error"] or err2
        else:
            rec["stage2"] = {"ok": True, "t_s": round(dt2, 2), "summary": s2}
    write_case(rec, out_dir)
    return rec


# ================================================================ 記録の読み書き（42番の規則）
def case_path(caseid: int, out_dir: Path | None = None) -> Path:
    out_dir = OUT if out_dir is None else out_dir
    return out_dir / "cases" / f"case_{caseid}.json"


def write_case(rec: dict, out_dir: Path | None = None) -> None:
    p = case_path(rec["caseid"], out_dir)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(rec, ensure_ascii=False, allow_nan=True), encoding="utf-8")


def read_case(caseid: int, out_dir: Path | None = None):
    p = case_path(caseid, out_dir)
    if not p.exists():
        return None
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:      # noqa: BLE001
        return None


def cache_state(caseid: int, stage: str, out_dir: Path | None = None,
                got: dict | None = None) -> tuple:
    """記録の状態。返り値 (状態, 記録)。

    missing     記録が無い
    env         **今の環境と違う環境で作られている**（42番と同じ規則で止める）
    stale       台本の版が違う（作り直す）
    failed      前回失敗している（既定では取り直す）
    partial     頼まれた段階がまだ済んでいない
    done        そのまま使える
    """
    rec = read_case(caseid, out_dir)
    if rec is None:
        return "missing", None
    fp = fingerprint(got)
    if rec.get("env") != fp["env"] or rec.get("pda2") != fp["pda2"]:
        return "env", rec
    if rec.get("script") != fp["script"]:
        return "stale", rec
    if rec.get("error") and not ((rec.get("stage1") or {}).get("ok")):
        return "failed", rec
    need1 = stage in ("1", "2", "all")
    need2 = stage in ("2", "all")
    if need1 and not (rec.get("stage1") or {}).get("ok"):
        return "partial", rec
    s2 = rec.get("stage2") or {}
    if need2 and not s2.get("ok"):
        if s2.get("settled"):
            return "done", rec          # やり直しても変わらない（ブロックが取れない）
        return "failed" if s2.get("error") else "partial", rec
    return "done", rec


def clear_case(caseid: int, out_dir: Path | None = None) -> None:
    """症例の記録とウィンドウごとの表を消す（作り直すため）。"""
    out_dir = OUT if out_dir is None else out_dir
    for p in (case_path(caseid, out_dir), out_dir / "windows" / f"case_{caseid}.csv",
              out_dir / "windows" / f"case_{caseid}_meta.json",
              out_dir / "blocks" / f"case_{caseid}.csv"):
        if p.exists():
            p.unlink()


# ================================================================ 集計（§7・§8）
def median_ci(x, domain: tuple, n_boot: int | None = None, seed: int | None = None) -> tuple:
    """症例を単位とした症例中央値の 95% 信頼区間。**43番の方法A をそのまま呼ぶ**

    平滑化ブートストラップ（Silverman の幅・2,000 回・種 0）。事前登録 §7 のとおり
    併記するだけで、**判定には使わない。**
    """
    n_boot = M43.N_BOOT if n_boot is None else n_boot
    seed = M43.SEED if seed is None else seed
    x = np.asarray(x, float)
    x = x[np.isfinite(x)]
    if x.size < 2:
        return NAN, NAN
    h = M43.silverman_h(x)
    r = M43.boot_at_n(x, int(x.size), h, np.random.default_rng(seed), n_boot, domain)
    return r["a_lo"], r["a_hi"]


def _med(v) -> float:
    v = np.asarray(v, float)
    v = v[np.isfinite(v)]
    return float(np.median(v)) if v.size else NAN


def row_values(summ, col: str, acc_col: str | None, with_ci: bool = True) -> dict:
    """1 行分の同定率・自己相関とその症例数・信頼区間。"""
    idc = f"acc_{acc_col}" if acc_col else f"id_{col}"
    idv = summ[idc].to_numpy(float) if idc in summ else np.array([])
    acv = summ[f"ac_{col}"].to_numpy(float) if f"ac_{col}" in summ else np.array([])
    finv = summ[f"id_{col}"].to_numpy(float) if f"id_{col}" in summ else np.array([])
    out = {"col": col, "id_col": idc, "id": _med(idv), "ac": _med(acv),
           "n_id": int(np.isfinite(idv).sum()), "n_ac": int(np.isfinite(acv).sum()),
           "finite": _med(finv) if acc_col else NAN,
           "ci_id": (NAN, NAN), "ci_ac": (NAN, NAN)}
    if with_ci:
        out["ci_id"] = median_ci(idv, (0.0, 1.0))
        out["ci_ac"] = median_ci(acv, (-1.0, 1.0))
    return out


def apply_criteria(summ, with_ci: bool = True) -> dict:
    """事前規準（§7）を機械的に当てる。**この関数は閾値を決めない。**"""
    res = {"control": None, "primary": [], "reference": []}
    c = row_values(summ, CONTROL_ROW[0], CONTROL_ROW[3], with_ci)
    c.update({"label": CONTROL_ROW[1], "stage": CONTROL_ROW[2],
              "pass": bool(np.isfinite(c["ac"]) and c["ac"] >= GATE_CTL)})
    res["control"] = c
    for col, label, stage, acc in PRIMARY_ROWS:
        r = row_values(summ, col, acc, with_ci)
        ok_id = bool(np.isfinite(r["id"]) and r["id"] >= GATE_ID)
        ok_ac = bool(np.isfinite(r["ac"]) and r["ac"] >= GATE_AC)
        why = []
        if not ok_id:
            why.append(f"同定率 {r['id']:.3f} < {GATE_ID:.2f}" if np.isfinite(r["id"])
                       else "同定率を出せる症例がない")
        if not ok_ac:
            why.append(f"自己相関 {r['ac']:.3f} < {GATE_AC:.2f}" if np.isfinite(r["ac"])
                       else "自己相関を計算できる症例がない")
        r.update({"label": label, "stage": stage, "acc_col": acc,
                  "pass": ok_id and ok_ac, "why": "・".join(why)})
        res["primary"].append(r)
    for col, label, stage, acc in REFERENCE_ROWS:
        r = row_values(summ, col, acc, with_ci)
        r.update({"label": label, "stage": stage, "acc_col": acc})
        res["reference"].append(r)
    return res


def _f(x, d=2, signed=False) -> str:
    if x is None or not np.isfinite(x):
        return "—"
    return format(x, f"{'+' if signed else ''}.{d}f")


def _ci(t, d=2, signed=False) -> str:
    lo, hi = t
    if not (np.isfinite(lo) and np.isfinite(hi)):
        return "—"
    return f"{_f(lo, d, signed)}〜{_f(hi, d, signed)}"


def render_outcome(res: dict, meta: dict) -> list:
    """§8 の表を組み立てる。**引数が同じなら何度呼んでも同じ行を返す**（時刻を読まない）。"""
    lpad, rpad = M43.lpad, M43.rpad
    W = 112
    env_dep = bool(meta.get("env_dependent"))
    L = ["=" * W,
         "論文3（実機での同定性）― 事前登録 sap_3_identifiability_v0.md §7 の規準を当てた結果",
         "=" * W,
         f"  台本            analysis/scripts/{Path(__file__).name}（版 {meta.get('script', '?')}）",
         f"  事前登録        {SAP_REL}（タグ {meta.get('sap_tag') or '**未凍結**'}）",
         "  計算環境        " + " / ".join(f"{k} {v}" for k, v in meta.get("env", {}).items()),
         f"                  主環境（§10）と{'一致' if not env_dep else '**違う → 環境依存**'}",
         f"  実装の版        pda2 {meta.get('pda2', '?')}",
         f"  症例            母集団 {meta.get('n_pool', 0)} 例"
         f"（{SOURCE_N} − パイロット 20 − 研究1 の 15、重複 1。§3）",
         f"                  処理できた {meta.get('n_done', 0)} 例・失敗 {meta.get('n_failed', 0)} 例・"
         f"未処理 {meta.get('n_todo', 0)} 例（**分母は母集団の全例**。§3）",
         f"  ウィンドウ      段階1 {meta.get('n_win', 0):,}（解析できる {meta.get('n_ok_win', 0):,}）／"
         f"段階2 {meta.get('n_block_win', 0):,}（1 症例 {N_BLOCKS} ブロック × 連続 {BLOCK_LEN}）",
         f"  実行日          {meta.get('date', '?')}"]
    if env_dep:
        L += ["", "  ★ 環境依存 ― 主環境（§10）と版が違う。**この表の合否は所見にしない**（§8 の環境依存の行）。"]
    for x in meta.get("notes", []):
        L.append(f"  注 {x}")
    for x in meta.get("bad", []):
        L.append(f"  ★ {x}")

    c = res["control"]
    L += ["", "-" * W,
          f"0. {c['label']}: 自己相関の症例中央値 {_f(c['ac'], 3, True)}"
          f"（{c['n_ac']} 例・要求 ≥ {GATE_CTL:.2f}）"
          f" → {'合格' if c['pass'] else '**不合格。表全体を無効とし、指標の合否を報告しない**（§7）'}",
          "-" * W]

    L += ["", "-" * W,
          f"1. 主要評価（§5 の 8 行。同定率の症例中央値 ≥ {GATE_ID:.2f} かつ "
          f"自己相関の症例中央値 ≥ {GATE_AC:.2f}）",
          "-" * W,
          "  " + rpad("指標", 34) + lpad("同定率", 7) + lpad("95%区間", 14)
          + lpad("自己相関", 9) + lpad("95%区間", 16) + lpad("n同定", 6) + lpad("n自己相関", 10)
          + lpad("判定", 10) + "  理由"]
    for r in res["primary"]:
        if env_dep or not c["pass"]:
            verdict = "環境依存" if env_dep else "無効"
        else:
            verdict = "成立" if r["pass"] else "不成立"
        L.append("  " + rpad(r["label"], 34) + lpad(_f(r["id"]), 7) + lpad(_ci(r["ci_id"]), 14)
                 + lpad(_f(r["ac"], 2, True), 9) + lpad(_ci(r["ci_ac"], 2, True), 16)
                 + lpad(str(r["n_id"]), 6) + lpad(str(r["n_ac"]), 10)
                 + lpad(verdict, 10) + "  " + (r["why"] if verdict in ("不成立",) else ""))
    L += ["",
          "  同定率の出どころ（§7）: 特徴点法・早期振幅比は「有限な値になったウィンドウ ÷ 解析できるウィンドウ」、",
          "  分解由来は「その版の採否を通ったウィンドウ（採択率）÷ ブロックのウィンドウ」。",
          "  95% 区間は症例を単位とした平滑化ブートストラップ（43番と同じ・"
          f"{M43.N_BOOT:,} 回・種 {M43.SEED}）。**判定には使わない**（§7）。",
          "  n は中央値を計算できた症例数。分母は母集団 "
          f"{meta.get('n_pool', 0)} 例で、足りない分は値が出なかった症例である（§3）。"]

    dec = [r for r in res["primary"] if r["acc_col"]]
    if dec:
        L += ["", "  分解由来の行の併記（§7。**記述であって合否には使わない**）",
              "  " + rpad("指標", 34) + lpad("採択率", 8) + lpad("有限な値の割合", 16)]
        for r in dec:
            L.append("  " + rpad(r["label"], 34) + lpad(_f(r["id"]), 8) + lpad(_f(r["finite"]), 16))

    L += ["", "-" * W,
          "2. 参考（§5 で主要評価に入れないと決めた行・§9 の記述）。**合否を出さない**",
          "-" * W,
          "  " + rpad("指標", 38) + lpad("同定率", 8) + lpad("自己相関", 10)
          + lpad("n同定", 6) + lpad("n自己相関", 10) + lpad("段階", 6)]
    for r in res["reference"]:
        L.append("  " + rpad(r["label"], 38) + lpad(_f(r["id"]), 8) + lpad(_f(r["ac"], 2, True), 10)
                 + lpad(str(r["n_id"]), 6) + lpad(str(r["n_ac"]), 10) + lpad(f"段階{r['stage']}", 6))
    for line in meta.get("descriptive", []):
        L.append("  " + line)

    L += ["", "-" * W, "3. 結果の読み方（§8 の表から、今回の合否に当たるものだけを写した）", "-" * W]
    if env_dep:
        L.append("  環境依存なので、どの行も所見にしない。主環境（§10）で回し直すこと。")
    elif not c["pass"]:
        L.append("  陽性対照が 0.50 に達しないので、表全体を無効とする。指標の合否を報告しない（§7・§8）。")
    else:
        for r in res["primary"]:
            key = (r["col"], r["pass"])
            if key in READING:
                text = READING[key]
            else:
                text = READING_DECOMP_PASS if r["pass"] else READING_DECOMP_FAIL
            L.append("  " + lpad("成立" if r["pass"] else "不成立", 6) + f"  {r['label']}: {text}")
            # §8 の分解由来の読み方は「有限な値になった割合」を前提に書かれているが、
            # §7 は採択率で判定する。採択率で落ちて有限な値の割合が規準を超える行では
            # 前提が違うので、事実だけを添える（読み方はこの台本では決めない）
            if (r["acc_col"] and not r["pass"] and np.isfinite(r["finite"])
                    and r["finite"] >= GATE_ID and np.isfinite(r["id"]) and r["id"] < GATE_ID):
                L.append(f"          注 この行の不成立は採択率 {r['id']:.3f} による。"
                         f"有限な値になった割合は {r['finite']:.3f} である（§7 と §8 の前提の違い）")
    L += ["",
          "  いずれの場合も、論文1 の結論（roadmap_v1.md §12.1）と論文2 の判定は動かさない（§8）。",
          "  同定は再現性までで、妥当性（何を測っているか）は別の問いである（§2・§12）。",
          "=" * W]
    return L


def outcome_json(res: dict, meta: dict) -> dict:
    """感度解析（vitaldb 1.7.2）の表と突き合わせるための合否（§10）。"""
    return {"meta": {k: meta.get(k) for k in ("script", "sap_tag", "env", "pda2", "n_pool",
                                              "n_done", "n_failed", "date", "env_dependent")},
            "control": {"ac": res["control"]["ac"], "pass": res["control"]["pass"]},
            "primary": {r["col"]: {"label": r["label"], "id": r["id"], "ac": r["ac"],
                                   "pass": bool(r["pass"])} for r in res["primary"]}}


def compare_environments(res: dict, other: dict) -> list:
    """別の環境で回した合否と突き合わせ、反転した行を「環境依存」として挙げる（§10）。"""
    out = []
    op = (other or {}).get("primary", {})
    for r in res["primary"]:
        o = op.get(r["col"])
        if o is None:
            continue
        if bool(o.get("pass")) != bool(r["pass"]):
            out.append(f"{r['label']}: 主環境 {'成立' if r['pass'] else '不成立'} / "
                       f"感度解析 {'成立' if o.get('pass') else '不成立'} → **環境依存。所見にしない**（§8・§10）")
    return out


# ================================================================ 症例ごとの表を組む
def collect_summary(ids: list, out_dir: Path | None = None):
    """記録から症例ごとの表を作る。未処理・失敗の症例も行として残す（§3）。"""
    import pandas as pd
    rows, n_done, n_failed, n_todo, n_noblock = [], 0, 0, 0, 0
    for cid in ids:
        rec = read_case(cid, out_dir)
        r = {"caseid": int(cid), "state": "未処理", "error": ""}
        if rec is None:
            n_todo += 1
            rows.append(r)
            continue
        s1 = rec.get("stage1") or {}
        s2 = rec.get("stage2") or {}
        r["error"] = str(rec.get("error") or "")
        if s1.get("ok"):
            r.update(s1.get("summary") or {})
            r["n_windows"] = s1.get("n_windows", r.get("n_windows"))
            r["n_analyzable"] = s1.get("n_analyzable", r.get("n_analyzable"))
        if s2.get("ok"):
            r.update(s2.get("summary") or {})
        if s2.get("settled"):
            n_noblock += 1
        if s1.get("ok") and (s2.get("ok") or s2.get("settled") or not s2):
            r["state"] = "済み（ブロック無し）" if s2.get("settled") else "済み"
            n_done += 1
        elif s1.get("ok") or s2.get("ok"):
            r["state"] = "一部"
            n_done += 1
            n_failed += 1
        else:
            r["state"] = "失敗"
            n_failed += 1
        r["caseid"] = int(cid)
        rows.append(r)
    summ = pd.DataFrame(rows)
    return summ, {"n_pool": len(ids), "n_done": n_done, "n_failed": n_failed,
                  "n_todo": n_todo, "n_noblock": n_noblock}


def descriptive_lines(summ, out_dir: Path | None = None) -> list:
    """§9 の記述（型の分布・ICC(1)・年齢との順位相関）。**検定しない。**"""
    out_dir = OUT if out_dir is None else out_dir
    L = []
    tcols = [f"ens_type{k}" for k in (1, 3, 4, 5)]
    if all(c in summ for c in tcols):
        parts = [f"型{k} {_med(summ[f'ens_type{k}']):.2f}" for k in (1, 3, 4, 5)]
        L.append("平均拍の型の症例中央値（段階1・§9）: " + "・".join(parts))
    if "b_type4" in summ:
        L.append(f"ブロックのウィンドウの型4 以上の割合（症例中央値・§9）: {_f(_med(summ['b_type4']))}")
    icc = icc_lines(summ, out_dir)
    L += icc
    age = age_lines(summ)
    L += age
    return L


def icc_lines(summ, out_dir: Path) -> list:
    """級内相関 ICC(1)（32番の `icc1`）。ウィンドウごとの表が残っていれば出す。"""
    import pandas as pd
    L = []
    wdir = out_dir / "windows"
    if not wdir.exists():
        return L
    for col, label, stage, _acc in [PRIMARY_ROWS[0], PRIMARY_ROWS[1], CONTROL_ROW]:
        groups = []
        for cid in summ["caseid"]:
            p = wdir / f"case_{int(cid)}.csv"
            if not p.exists():
                continue
            try:
                d = pd.read_csv(p, usecols=["n_good", col])
            except Exception:      # noqa: BLE001
                continue
            d = d[d["n_good"] >= MIN_GOOD]
            groups.append(d[col].to_numpy(float))
        if len(groups) >= 2:
            L.append(f"症例間の分離 ICC(1) {label}（段階1・記述・§9）: {_f(M32.icc1(groups))}")
    return L


def age_lines(summ) -> list:
    """年齢との順位相関（症例中央値・記述のみ・§9）。"""
    import pandas as pd
    L = []
    cp = DATA / "cases.csv"
    if not cp.exists():
        return L
    try:
        demo = pd.read_csv(cp, encoding="utf-8-sig")
        ages = {int(r["caseid"]): float(r["age"]) for _, r in demo.iterrows()}
    except Exception:      # noqa: BLE001
        return L
    a = np.array([ages.get(int(c), NAN) for c in summ["caseid"]], float)
    from scipy.stats import spearmanr
    for col, label, _stage, _acc in PRIMARY_ROWS[:2]:
        mc = f"med_{col}"
        if mc not in summ:
            continue
        v = summ[mc].to_numpy(float)
        m = np.isfinite(a) & np.isfinite(v)
        if m.sum() >= 10:
            rho = float(spearmanr(a[m], v[m]).correlation)
            L.append(f"年齢との順位相関（症例中央値・記述・n={int(m.sum())}・§9）{label}: {_f(rho, 2, True)}")
    return L


# ================================================================ パイロットの再現（§13）
PILOT_REF_32 = RESULTS / "32_vitaldb_landmark_summary_v158.csv"
PILOT_REF_34 = [DATA / "vitaldb_methods_v158" / "summary.csv",
                DATA / "vitaldb_methods" / "summary.csv",
                RESULTS / "34_vitaldb_methods_summary_v158.csv"]


PILOT_REPORT_32 = RESULTS / "32_vitaldb_landmark_report_v158.txt"


def pilot_report_versions(path: Path | None = None) -> dict:
    """パイロットの report が刻んでいる版（§6「実装の版を本文に載せる」）。"""
    path = PILOT_REPORT_32 if path is None else path
    out = {}
    if not path.exists():
        return out
    txt = path.read_text(encoding="utf-8")
    for key, pat in (("pda2", r"pda2 ([0-9a-f]{6,})"), ("vitaldb", r"vitaldb ([0-9.]+)")):
        m = re.search(pat, txt)
        if m:
            out[key] = m.group(1)
    return out


def find_pilot_ref_34():
    for p in PILOT_REF_34:
        if p.exists():
            return p
    return None


def compare_pilot(summ, ref_csv: Path, rename: dict | None = None) -> list:
    """症例ごとの値を出どころの表と突き合わせ、列ごとの最大の差を出す。

    **再現の確認であって新しい解析ではない。**32番・34番が既に解析した 20 例である。
    """
    import pandas as pd
    if not ref_csv.exists():
        return [f"  照合先が無い: {ref_csv}"]
    ref = pd.read_csv(ref_csv)
    if rename:
        ref = ref.rename(columns=rename)
    a = summ.set_index("caseid")
    b = ref.set_index("caseid")
    ids = sorted(set(a.index) & set(b.index))
    L = [f"  照合先 {M43.rel(ref_csv)}・共通の症例 {len(ids)} 例"]
    if not ids:
        return L
    cols = [c for c in b.columns if c in a.columns and c != "caseid"]
    worst = []
    for c in sorted(cols):
        x = pd.to_numeric(a.loc[ids, c], errors="coerce").to_numpy(float)
        y = pd.to_numeric(b.loc[ids, c], errors="coerce").to_numpy(float)
        if not (np.isfinite(x).any() or np.isfinite(y).any()):
            continue
        both = np.isfinite(x) & np.isfinite(y)
        onlyx = int((np.isfinite(x) & ~np.isfinite(y)).sum())
        onlyy = int((~np.isfinite(x) & np.isfinite(y)).sum())
        d = float(np.max(np.abs(x[both] - y[both]))) if both.any() else NAN
        worst.append((c, d, int(both.sum()), onlyx + onlyy))
    worst.sort(key=lambda r: (-(r[1] if np.isfinite(r[1]) else -1), r[0]))
    L.append("  " + M43.rpad("列", 26) + M43.lpad("最大の差", 12) + M43.lpad("比べた例数", 12)
             + M43.lpad("片方だけ欠測", 14))
    for c, d, n, na in worst:
        L.append("  " + M43.rpad(c, 26) + M43.lpad(_f(d, 6), 12) + M43.lpad(str(n), 12)
                 + M43.lpad(str(na), 14))
    return L


# ================================================================ 実行
def scan_cache(ids: list, stage: str, out_dir: Path, got: dict) -> dict:
    st = {}
    for cid in ids:
        s, _rec = cache_state(cid, stage, out_dir, got)
        st.setdefault(s, []).append(cid)
    return st


def orphan_windows(ids: list, out_dir: Path) -> list:
    """記録が無いのにウィンドウごとの表だけ残っている症例（出所が分からない）。"""
    out = []
    wdir = out_dir / "windows"
    if not wdir.exists():
        return out
    for cid in ids:
        if (wdir / f"case_{cid}.csv").exists() and not case_path(cid, out_dir).exists():
            out.append(cid)
    return out


def _work(payload: tuple) -> dict:
    """並列の子が 1 症例を処理する。**設定は値で渡す。**

    macOS の spawn では子がこのファイルを読み込み直すので、親で書いた大域変数は伝わらない
    （出力先を取り違える）。波形そのものは渡さず、症例ごとに子が取得する。
    """
    caseid, stage, out_dir, got = payload
    out_dir = Path(out_dir)
    try:
        return process_case(caseid, stage=stage, out_dir=out_dir, got=got)
    except Exception as e:      # noqa: BLE001
        rec = {"caseid": int(caseid), "error": f"失敗: {e}", "stage1": None, "stage2": None}
        rec.update(fingerprint(got))
        write_case(rec, out_dir)
        return rec


def run_cases(ids: list, stage: str, jobs: int, out_dir: Path, got: dict,
              retry_failed: bool = True, refresh_stale: bool = False) -> int:
    """症例を処理する。済んでいるものは飛ばす。環境が食い違えば止める（42番の規則）。"""
    out_dir.mkdir(parents=True, exist_ok=True)
    orph = orphan_windows(ids, out_dir)
    st = scan_cache(ids, stage, out_dir, got)
    if st.get("env") or orph:
        print("\n★ 症例ごとの記録が今の環境と食い違う（別の環境で作られたものが混ざる）。")
        if st.get("env"):
            print(f"   環境が違う記録 {len(st['env'])} 例: {st['env'][:10]}…")
        if orph:
            print(f"   記録が無いのにウィンドウの表だけある症例 {len(orph)} 例: {orph[:10]}…")
        if not refresh_stale:
            print(f"\n   作り直す:  rm -rf {out_dir}")
            print("   その症例だけ作り直す: --refresh-stale を付けてやり直す")
            return 3
        for cid in list(st.get("env", [])) + orph:
            clear_case(cid, out_dir)
        st = scan_cache(ids, stage, out_dir, got)
    todo = []
    for cid in ids:
        s, _rec = cache_state(cid, stage, out_dir, got)
        if s == "done":
            continue
        if s == "failed" and not retry_failed:
            continue
        if s == "stale":
            clear_case(cid, out_dir)
        todo.append(cid)
    print(f"\n症例 {len(ids)} 例のうち、処理するのは {len(todo)} 例"
          f"（済み {len(st.get('done', []))} 例・台本の版が古い {len(st.get('stale', []))} 例）", flush=True)
    if not todo:
        return 0
    payloads = [(c, stage, str(out_dir), got) for c in todo]
    prog = out_dir / "progress.json"
    t0 = time.time()
    done = 0
    n_err = 0

    def tick(rec):
        nonlocal done, n_err
        done += 1
        if rec.get("error"):
            n_err += 1
        el = time.time() - t0
        per = el / max(done, 1)
        rem = per * (len(todo) - done)
        prog.write_text(json.dumps(
            {"script": "44_paper3_identifiability", "stage": stage, "done": done, "total": len(todo),
             "failed": n_err, "elapsed_s": round(el), "per_case_s": round(per, 1),
             "eta_s": round(rem), "jobs": jobs, "updated": time.time(),
             "state": "done" if done == len(todo) else "running"}, ensure_ascii=False),
            encoding="utf-8")
        s1 = (rec.get("stage1") or {})
        s2 = (rec.get("stage2") or {})
        msg = (f"  case {rec['caseid']}: "
               f"段階1 {'ウィンドウ ' + str(s1.get('n_windows')) if s1.get('ok') else '×'}"
               f"（{s1.get('t_s', 0):.0f} 秒）・"
               f"段階2 {'ウィンドウ ' + str((s2.get('summary') or {}).get('n_block_windows')) if s2.get('ok') else '×'}"
               f"（{s2.get('t_s', 0):.0f} 秒）")
        if rec.get("error"):
            msg += f"  ★ {rec['error'][:60]}"
        print(f"{msg}  [{done}/{len(todo)}・経過 {el / 60:.1f} 分・"
              f"{per / 60:.1f} 分/例・残り約 {rem / 3600:.1f} 時間]", flush=True)

    if jobs > 1:
        from concurrent.futures import ProcessPoolExecutor, as_completed
        with ProcessPoolExecutor(max_workers=jobs) as ex:
            futs = [ex.submit(_work, pl) for pl in payloads]
            for f in as_completed(futs):
                tick(f.result())
    else:
        for pl in payloads:
            tick(_work(pl))
    print(f"\n処理を終えた。失敗 {n_err} 例（分母は解析対象の全例。§3）", flush=True)
    return 0


def estimate_lines(ids: list, out_dir: Path, jobs=(1, 8), n_target: int = POOL_N) -> list:
    """記録に残した所要時間から、母集団を回すのにかかる時間を見積もる。"""
    t1, t2 = [], []
    for cid in ids:
        rec = read_case(cid, out_dir)
        if not rec:
            continue
        s1, s2 = rec.get("stage1") or {}, rec.get("stage2") or {}
        if s1.get("ok"):
            t1.append(float(s1.get("t_s", NAN)))
        if s2.get("ok"):
            t2.append(float(s2.get("t_s", NAN)))
    L = [f"  実測の出どころ: {M43.rel(out_dir / 'cases')}・段階1 {len(t1)} 例・段階2 {len(t2)} 例"]
    if not t1 and not t2:
        return L + ["  ★ 所要時間の記録が無い。先に --pilot を回すこと"]
    m1 = float(np.nanmean(t1)) if t1 else NAN
    m2 = float(np.nanmean(t2)) if t2 else NAN
    tot = float(np.nansum([m1 if np.isfinite(m1) else 0.0, m2 if np.isfinite(m2) else 0.0]))
    L.append(f"  段階1（取得・ウィンドウ化・特徴点法・早期振幅比・PWTT）: "
             f"{m1:.1f} 秒/例（中央値 {np.nanmedian(t1) if t1 else NAN:.1f}）")
    L.append(f"  段階2（分解 3 版 × ブロックのウィンドウ）: "
             f"{m2:.1f} 秒/例（中央値 {np.nanmedian(t2) if t2 else NAN:.1f}）")
    L.append(f"  合計 {tot:.1f} 秒/例")
    for j in jobs:
        L.append(f"  {n_target} 例・{j} 並列の見込み: "
                 f"段階1 {m1 * n_target / j / 3600:.1f} 時間・段階2 {m2 * n_target / j / 3600:.1f} 時間・"
                 f"合計 {tot * n_target / j / 3600:.1f} 時間")
    L.append("  取得（1 例 10 秒前後）を含む実測である。回線と機械で変わる（lab_log 追記115）。")
    return L


def show_check(got: dict, bad: list, fz: dict | None, out_dir: Path, ids: list | None) -> None:
    print("== 版の照合（事前登録 §10 の主環境） ==")
    for k, want in REF.items():
        g = got.get(k) or "未導入"
        print(f"  {k:8s} {str(g):10s} （主環境 {want}）  {'一致' if g == want else '★違う'}")
    if bad:
        print("\n  ★ 主環境と違う。既定では症例を処理しない（§10「1 台で回す」）。")
        print("     合わせるか、承知のうえなら --allow-env-mismatch を付ける")
        print("     （その場合、出力はすべて環境依存と記され、主要評価の判定を出さない）")
    print(f"\n  pda2 {pda2.code_version()}・台本の版 {script_sha()}")
    print("\n== 事前登録の凍結 ==")
    if fz is None:
        print("  --sap-tag が指定されていないので確かめていない")
    elif fz["ok"]:
        print(f"  タグ {fz['tag']} があり、作業中の {SAP_REL} はその版と同一")
    else:
        print(f"  ★ {fz['why']}")
    print("\n== 進み具合 ==")
    if ids is None:
        print("  母集団の一覧を作れない（data/target_cases.csv が無い）")
    else:
        n = sum(1 for c in ids if read_case(c, out_dir) is not None)
        st = scan_cache(ids, "all", out_dir, got)
        print(f"  解析対象 {len(ids)} 例・記録のある症例 {n} 例")
        for k in ("done", "partial", "failed", "stale", "env", "missing"):
            if st.get(k):
                print(f"    {k:8s} {len(st[k]):>4d} 例")


# ================================================================ 自己検査
def selftest() -> int:                    # noqa: C901
    import contextlib
    import io
    import os
    import tempfile
    import pandas as pd
    ok = True

    def rep(name, cond, detail=""):
        nonlocal ok
        ok = ok and bool(cond)
        print(f"  [{'PASS' if cond else 'FAIL'}] {name}" + (f"  {detail}" if detail else ""))

    print("44番 自己検査（合成データのみ。ネットワークも analysis/data も要らない）\n")

    # ---------------- 1. 規準・定数を書き写していないこと
    print("1. 規準と定数（32番・34番・43番のものを使っているか）")
    rep("同定率・自己相関・陽性対照の閾値が 32番の定数そのもの",
        GATE_ID is M32.GATE_ID_RATE and GATE_AC is M32.GATE_AUTOCORR and GATE_CTL is M32.GATE_CONTROL,
        f"{GATE_ID}／{GATE_AC}／{GATE_CTL}")
    rep("事前登録 §7 の値と同じ（0.70／0.30／0.50）", (GATE_ID, GATE_AC, GATE_CTL) == (0.70, 0.30, 0.50))
    rep("解析できるウィンドウの条件と段階1 の対の数が 32番と同じ",
        MIN_GOOD == M32.MIN_GOOD == 8 and MIN_PAIRS_WIN == M32.MIN_PAIRS == 10)
    rep("段階2 の対の数は 34番の summarize と同じ 8", MIN_PAIRS_BLOCK == 8,
        "34番 summarize の min_pairs=8。事前登録 §3 の本文は 32番の 10 を引いている")
    rep("ブロックの取り方が 34番と同じ（3 ブロック × 連続 6）",
        (N_BLOCKS, BLOCK_LEN) == (M34.N_BLOCKS, M34.BLOCK_LEN) == (3, 6))
    rep("主環境が 42番・CLAUDE.md §4 と同じ 5 つ",
        REF == M42.REF and REF["vitaldb"] == "1.5.8" and REF["python"] == "3.9.6", str(REF["numpy"]))
    rep("主要評価は 8 行、陽性対照 1 行（§5）", len(PRIMARY_ROWS) == 8)
    rep("分解由来の 6 行に採否列がある（同定率に採択率を使う。§7）",
        sum(1 for _c, _l, _s, a in PRIMARY_ROWS if a) == 6)
    rep("文献 6 本の分解は入れない（§5）",
        not any("Goswami" in lab or "Wang" in lab or "Basso" in lab for _c, lab, _s, _a in PRIMARY_ROWS))
    rep("信頼区間は 43番の方法A（2,000 回・種 0）", M43.N_BOOT == 2000 and M43.SEED == 0)

    # ---------------- 2. 除外する症例が文書と一致するか
    print("\n2. 除外する症例（§3・sap_v0.md §3.1）")
    rep("パイロットは 20 例・開発は 15 例・重複は caseid 97 の 1 例",
        len(PILOT_CASES) == 20 and len(DEV_CASES) == 15
        and set(PILOT_CASES) & set(DEV_CASES) == {97})
    d3 = ids_in_document(REPO / SAP_REL, r"（seed 0 で抽出された caseid([^）]*)）")
    rep("事前登録 §3 が列挙する 20 例と同じ", d3 is None or d3 == sorted(PILOT_CASES),
        "文書を読めない" if d3 is None else f"{len(d3)} 例")
    d1 = ids_in_document(REPO / SAP1_REL, r"パイロット15例（caseid([^)]*)）")
    rep("sap_v0.md §3.1 が列挙する 15 例と同じ", d1 is None or d1 == sorted(DEV_CASES),
        "文書を読めない" if d1 is None else f"{len(d1)} 例")

    # ---------------- 3. 母集団の引き算（合成の表）
    print("\n3. 母集団の引き算（874 − 20 − 15 ＋ 重複 1 = 840）")
    special = sorted(set(PILOT_CASES) | set(DEV_CASES))
    others = [c for c in range(10000, 20000) if c not in special][:SOURCE_N - len(special)]
    tab = pd.DataFrame({"caseid": sorted(special + others), "pleth": True, "ecg": True})
    pool, err = build_pool(table=tab)
    cnt = pool_counts(pool)
    rep("合成の 874 例から 840 例になる", err is None and cnt["n_pool"] == POOL_N == 840,
        f"{cnt['n_source']} − {cnt['n_pilot']} − {cnt['n_dev']} ＋ {cnt['n_overlap']} = {cnt['n_pool']}")
    rep("除外した 34 例が解析対象に入らない",
        not (set(pool_ids(pool)) & (set(PILOT_CASES) | set(DEV_CASES))),
        f"除外 {cnt['n_excluded']} 例")
    rep("caseid 97 の理由に両方が書かれる（二重に引いていない）",
        pool.loc[pool["caseid"] == 97, "exclude_reason"].iloc[0] == f"{WHY_PILOT}・{WHY_DEV}")
    rep("並びは caseid 昇順で、乱数を使っていない（二度作って同一）",
        pool_ids(pool) == sorted(pool_ids(pool))
        and build_pool(table=tab)[0].equals(pool))
    tab2 = tab.copy()
    tab2.loc[tab2["caseid"].isin(others[:5]), "pleth"] = False      # 除外の 34 例とは別の 5 例
    rep("PLETH・ECG の無い症例は 32番と同じく最初から入らない",
        pool_counts(build_pool(table=tab2)[0])["n_pool"] == POOL_N - 5,
        f"{pool_counts(build_pool(table=tab2)[0])['n_pool']} 例")
    rep("入力が無ければ理由を返して止める（exit 2 の側）",
        build_pool(target_csv=Path("/no/such/target_cases.csv"))[0] is None)

    # ---------------- 4. 版の照合
    print("\n4. 版の照合（§10）")
    rep("すべて一致なら空", env_mismatch(dict(REF)) == [])
    rep("vitaldb が違えば挙がる", [k for k, *_ in env_mismatch({**REF, "vitaldb": "1.7.2"})] == ["vitaldb"])
    rep("**42番と違い、NumPy が違うだけでも止める側に入る（§10）**",
        len(env_mismatch({**REF, "numpy": "9.9.9"})) == 1)
    rep("未導入も挙がる", env_mismatch({**REF, "scipy": None})[0][1] == "未導入")
    rep("台本の指紋が 12 桁で、同じ中身なら同じ", len(script_sha()) == 12 and script_sha() == script_sha())

    # ---------------- 5. 凍結の確認（一時の git 置き場）
    print("\n5. 凍結の確認（§15。一時の git 置き場で確かめる。本物には触れない）")
    with tempfile.TemporaryDirectory() as td:
        rp = Path(td)
        (rp / "docs" / "research").mkdir(parents=True)
        f = rp / SAP_REL
        f.write_text("事前登録 v0\n", encoding="utf-8")
        env = {**os.environ, "GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@x",
               "GIT_COMMITTER_NAME": "t", "GIT_COMMITTER_EMAIL": "t@x"}
        git_ok = True
        for cmd in (["git", "init", "-q"], ["git", "add", "-A"],
                    ["git", "commit", "-qm", "sap"], ["git", "tag", "sap3-test"]):
            r = subprocess.run(cmd, cwd=str(rp), env=env, capture_output=True, text=True)
            git_ok = git_ok and r.returncode == 0
        rep("一時の git 置き場を作れた（作れなければ以下は確かめられない）", git_ok)
        rep("タグを渡さなければ拒む", not freeze_state(None, rp)["ok"]
            and "--sap-tag" in freeze_state(None, rp)["why"])
        rep("無いタグを渡せば拒む", not freeze_state("no-such-tag", rp)["ok"])
        rep("タグがあり文書が同一なら通る", freeze_state("sap3-test", rp)["ok"])
        f.write_text("事前登録 v0（書き換えた）\n", encoding="utf-8")
        st = freeze_state("sap3-test", rp)
        rep("作業中の事前登録がタグの版と違えば拒む", not st["ok"] and "違う" in st["why"])
        rep("git のない場所では拒む（黙って通さない）",
            not freeze_state("sap3-test", Path(td) / "nowhere")["ok"])

    # ---------------- 6. 事前規準の当て方
    print("\n6. 事前規準の当て方（§7。0.70／0.30 の両側で答えの分かる値を作る）")

    def fake(n=21, **kw):
        d = {"caseid": list(range(1, n + 1)), "ac_pwtt_ms": [0.80] * n, "id_pwtt_ms": [1.0] * n}
        for c, _l, _s, acc in PRIMARY_ROWS:
            d[f"id_{c}"] = [0.99] * n
            d[f"ac_{c}"] = [0.99] * n
            if acc:
                d[f"acc_{acc}"] = [0.99] * n
        for c, _l, _s, _a in REFERENCE_ROWS:
            d[f"id_{c}"] = [0.5] * n
            d[f"ac_{c}"] = [0.5] * n
        d.update({k: [v] * n for k, v in kw.items()})
        return pd.DataFrame(d)

    # 中央値が閾値の両側にくる並び（n=21 なので 11 番目が中央値）
    hi_id = [0.71] * 11 + [0.10] * 10          # 中央値 0.71 ≥ 0.70
    lo_id = [0.69] * 11 + [0.99] * 10          # 中央値 0.69 < 0.70
    hi_ac = [0.31] * 11 + [-0.5] * 10
    lo_ac = [0.29] * 11 + [0.99] * 10
    r = apply_criteria(fake().assign(id_ens_dt_lm_ms=hi_id, ac_ens_dt_lm_ms=hi_ac), with_ci=False)
    rep("同定率 0.71・自己相関 0.31 → 成立", r["primary"][0]["pass"],
        f"{r['primary'][0]['id']:.2f}／{r['primary'][0]['ac']:+.2f}")
    r = apply_criteria(fake().assign(id_ens_dt_lm_ms=lo_id, ac_ens_dt_lm_ms=hi_ac), with_ci=False)
    rep("同定率 0.69 → 不成立（理由に同定率が出る）",
        not r["primary"][0]["pass"] and "同定率" in r["primary"][0]["why"], r["primary"][0]["why"])
    r = apply_criteria(fake().assign(id_ens_dt_lm_ms=hi_id, ac_ens_dt_lm_ms=lo_ac), with_ci=False)
    rep("自己相関 0.29 → 不成立（理由に自己相関が出る）",
        not r["primary"][0]["pass"] and "自己相関" in r["primary"][0]["why"], r["primary"][0]["why"])
    r = apply_criteria(fake().assign(id_ens_dt_lm_ms=lo_id, ac_ens_dt_lm_ms=lo_ac), with_ci=False)
    rep("両方足りなければ理由が 2 つ", r["primary"][0]["why"].count("・") == 1, r["primary"][0]["why"])
    r = apply_criteria(fake(ac_pwtt_ms=0.49), with_ci=False)
    rep("陽性対照 0.49 は不合格（0.50 に達しない）", not r["control"]["pass"])
    rep("陽性対照 0.50 ちょうどは合格", apply_criteria(fake(ac_pwtt_ms=0.50), with_ci=False)["control"]["pass"])
    # 分解由来は採択率で判定する（§7）。有限な値の割合が 1.00 でも採択率が低ければ不成立
    s = fake()
    s["acc_ok_v2"] = [0.10] * 21
    s["id_dt_v2_ms"] = [1.00] * 21
    r = apply_criteria(s, with_ci=False)
    row = [x for x in r["primary"] if x["col"] == "dt_v2_ms"][0]
    rep("分解由来は採択率で判定し、有限な値の割合は併記だけ（§7）",
        not row["pass"] and row["id"] == 0.10 and row["finite"] == 1.00,
        f"採択率 {row['id']:.2f}・有限 {row['finite']:.2f}")
    rep("参考の行には合否が付かない", all("pass" not in x for x in r["reference"]))
    # 欠測のある症例は中央値に入らないが、分母（母集団）は変わらない
    s = fake()
    s.loc[s.index[:5], "ac_ens_amb"] = np.nan
    r = apply_criteria(s, with_ci=False)
    amb = [x for x in r["primary"] if x["col"] == "ens_amb"][0]
    rep("自己相関を出せない症例はその行の集計から外れ、症例数が分かる（§3）",
        amb["n_ac"] == 16 and amb["n_id"] == 21, f"n自己相関 {amb['n_ac']}／n同定 {amb['n_id']}")

    # ---------------- 7. 信頼区間（43番の方法A）
    print("\n7. 信頼区間（§7。43番の方法A をそのまま呼ぶ）")
    x = np.clip(np.random.default_rng(0).normal(0.60, 0.10, 40), 0, 1)
    lo, hi = median_ci(x, (0.0, 1.0))
    rep("区間が中央値を挟む", lo <= float(np.median(x)) <= hi, f"{lo:.3f} ≤ {np.median(x):.3f} ≤ {hi:.3f}")
    rep("二度呼んでも 1 ビットも違わない（種 0）", median_ci(x, (0.0, 1.0)) == (lo, hi))
    lo2, hi2 = median_ci(np.clip(np.random.default_rng(1).normal(-0.5, 0.2, 40), -1, 1), (-1.0, 1.0))
    rep("自己相関は −1〜1 の範囲で丸める（0 で切らない）", lo2 < 0.0, f"{lo2:.3f}〜{hi2:.3f}")
    rep("症例が 1 例以下なら区間を出さない", not np.isfinite(median_ci([0.5], (0, 1))[0]))

    # ---------------- 8. 段階1 の計算（仕込んだ値を取り出せるか）
    print("\n8. 段階1（32番の case_summary。仕込んだ同定率・自己相関を取り出す）")
    n = 40
    rng = np.random.default_rng(3)
    v = np.zeros(n)
    for i in range(1, n):
        v[i] = 0.8 * v[i - 1] + rng.normal()
    vv = v.copy()
    vv[::4] = np.nan                       # 4 つに 1 つを欠測 → 同定率 0.75
    win = pd.DataFrame({"caseid": 9001, "t0": np.arange(n) * M32.WIN_S,
                        "n_good": 12, "sigma": 0.01, "hr": 70.0,
                        "ens_klass": 1.0, "ens_prom": 0.05, "ens_S_ms": 100.0,
                        "ens_notch_ms": 250.0, "ens_D_ms": 300.0,
                        "ens_dt_lm_ms": vv, "ens_dt1_ms": vv, "ens_p1_ms": 90.0,
                        "ens_b_ms": 60.0, "ens_amb": np.abs(v) + 0.1, "pwtt_ms": v + 10.0,
                        "beat_k1": 0.9, "beat_k13": 0.95, "beat_amb_ok": 1.0,
                        "beat_dt_med": 200.0, "beat_dt_sd": 5.0,
                        "beat_amb_med": 0.9, "beat_amb_sd": 0.02})
    s = M32.case_summary(win)
    rep("仕込んだ同定率 0.75 が出る", abs(s["id_ens_dt_lm_ms"] - 0.75) < 1e-12, f"{s['id_ens_dt_lm_ms']:.3f}")
    r_direct = M32.lag1_autocorr(win["t0"].to_numpy(float), win["pwtt_ms"].to_numpy(float))[0]
    rep("仕込んだ AR(1) φ=0.8 の自己相関が出る（0.6〜0.95）",
        0.6 < s["ac_pwtt_ms"] < 0.95 and abs(s["ac_pwtt_ms"] - r_direct) < 1e-12, f"{s['ac_pwtt_ms']:.3f}")
    rep("欠測の多い列では隣り合う対が減る（32番の対の数が出る）",
        s["npair_ens_dt_lm_ms"] < s["npair_pwtt_ms"],
        f"{s['npair_ens_dt_lm_ms']} 対 対 {s['npair_pwtt_ms']} 対")
    win2 = win.copy()
    win2["n_good"] = 3
    s2 = M32.case_summary(win2)
    rep("解析できるウィンドウが無ければ値を出さない（分母には残る）",
        s2["n_analyzable"] == 0 and not np.isfinite(s2["id_ens_dt_lm_ms"]))

    # ---------------- 9. 合成の波形で端から端まで（段階1・段階2・記録・再開）
    print("\n9. 合成の波形で端から端まで（段階1 → 段階2 → 記録 → 再開）")
    ecg, pleth = M32._synth_case(12 * 60, seed=5, drift=True)
    arrays = {"pleth": pleth, "ecg": ecg}
    calls = {"n": 0}

    def loader(_c):
        calls["n"] += 1
        return arrays

    with tempfile.TemporaryDirectory() as td:
        od = Path(td) / "paper3"
        got = versions()
        t_s = time.time()
        rec = process_case(9001, stage="all", loader=loader, out_dir=od,
                           n_blocks=1, block_len=2, got=got)
        el = time.time() - t_s
        rep("段階1 が通り、ウィンドウごとの表が書かれる",
            (rec["stage1"] or {}).get("ok") and (od / "windows" / "case_9001.csv").exists(),
            f"ウィンドウ {rec['stage1'].get('n_windows')}・段階1 {rec['stage1']['t_s']:.1f} 秒"
            f"（段階1+2 で {el:.0f} 秒）")
        rep("波形の取得は症例ごとに 1 度だけ（段階1 と段階2 で使い回す）", calls["n"] == 1,
            f"取得 {calls['n']} 回")
        s1 = rec["stage1"]["summary"]
        rep("合成の型1 波形で特徴点法 ΔT と早期振幅比が同定される（同定率 ≥ 0.9）",
            s1["id_ens_dt_lm_ms"] >= 0.9 and s1["id_ens_amb"] >= 0.9,
            f"ΔT {s1['id_ens_dt_lm_ms']:.2f}・Am {s1['id_ens_amb']:.2f}")
        s2 = (rec["stage2"] or {}).get("summary") or {}
        rep("段階2 が通り、ブロックのウィンドウに 3 版の分解が当たる",
            (rec["stage2"] or {}).get("ok") and s2.get("n_block_windows") == 2
            and (od / "blocks" / "case_9001.csv").exists(),
            f"ウィンドウ {s2.get('n_block_windows')}・{rec['stage2']['t_s']:.0f} 秒")
        blk = pd.read_csv(od / "blocks" / "case_9001.csv")
        rep("段階2 の表に 3 版の ΔT・RI・採否と特徴点法・PWTT の列がある",
            all(c in blk for c in BLOCK_COLS + BLOCK_OK_COLS),
            "・".join(c for c in BLOCK_COLS if c in blk))
        rep("PWTT は段階1 と同じ値をブロックのウィンドウに写している",
            np.isfinite(blk["b_pwtt_ms"]).all())
        rep("例外が残っていない", "err" not in blk or blk["err"].isna().all())
        # 34番の methods_on_beat と突き合わせる（文献の分だけ外して同じ拍に当てる）
        y, _ng = M34.ensemble_beat(
            np.nan_to_num(np.asarray(pleth[:int(M32.WIN_S * M32.FS)], float)),
            np.nan_to_num(np.asarray(ecg[:int(M32.WIN_S * M32.FS)], float)))
        saved = M34.M33.replica_for_beat
        M34.M33.replica_for_beat = lambda *a, **k: {}
        try:
            ref = M34.methods_on_beat(y, M32.FS, 50)
        finally:
            M34.M33.replica_for_beat = saved
        mine = our_methods_on_beat(y, M32.FS)
        shared = sorted(set(ref) & set(mine))
        diff = [k for k in shared
                if not (ref[k] == mine[k]
                        or (isinstance(ref[k], float) and isinstance(mine[k], float)
                            and np.isnan(ref[k]) and np.isnan(mine[k])))]
        rep("段階2 の 1 拍が 34番の methods_on_beat と一致する（文献の分を除いた全列）",
            len(shared) >= 12 and not diff, f"{len(shared)} 列・違う列 {diff}")
        # ブロックの選び方が 34番の case_tasks と同じか
        df1 = pd.read_csv(od / "windows" / "case_9001.csv")
        mine_idx = blocks_from_stage1(df1, 1, 2)
        t34 = M34.case_tasks(9001, arrays, 50, 1, 2)
        rep("ブロックの選び方が 34番の case_tasks と同じウィンドウを選ぶ",
            [float(df1['t0'].iloc[i]) for i in mine_idx[0]] == [t[1] for t in t34],
            f"{[float(df1['t0'].iloc[i]) for i in mine_idx[0]]}")
        # 並列の子に設定が値で渡る（spawn で出力先を取り違えないこと）。
        # 既定の取得をこの検査のあいだだけ合成に差し替える（ネットワークに出ない）
        od2 = Path(td) / "paper3b"
        saved_loader = M32._vitaldb_loader
        M32._vitaldb_loader = lambda _c: arrays
        try:
            rec_w = _work((9004, "1", str(od2), got))
        finally:
            M32._vitaldb_loader = saved_loader
        rep("並列の子は渡された出力先・段階に書く（大域変数に頼らない。spawn 対策）",
            (rec_w.get("stage1") or {}).get("ok") and case_path(9004, od2).exists()
            and not case_path(9004, od).exists() and rec_w.get("stage2") is None,
            f"{M43.rel(case_path(9004, od2)) if od2 in case_path(9004, od2).parents else case_path(9004, od2).name}")
        # 記録と再開
        before = calls["n"]
        st, _r = cache_state(9001, "all", od, got)
        rep("記録が済みと読める", st == "done")
        with contextlib.redirect_stdout(io.StringIO()):
            rc = run_cases([9001], "all", 1, od, got)
        rep("済みの症例は取り直さない（再開が効く）", rc == 0 and calls["n"] == before)
        # 環境が違う記録は拒む
        bad_got = {**got, "vitaldb": "1.7.2"}
        st2, _r2 = cache_state(9001, "all", od, bad_got)
        rep("別の環境の記録は env と判定される", st2 == "env")
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            rc2 = run_cases([9001], "all", 1, od, bad_got)
        rep("別の環境の記録があれば止まる（終了コード 3・作り直しを促す）",
            rc2 == 3 and "rm -rf" in buf.getvalue(), buf.getvalue().strip().splitlines()[-1][:60])
        # 台本の版が違えば作り直す
        rec2 = read_case(9001, od)
        rec2["script"] = "0" * 12
        write_case(rec2, od)
        st3, _r3 = cache_state(9001, "all", od, got)
        rep("台本の版が違えば stale と判定して作り直す側に回す", st3 == "stale")
        write_case(read_case(9001, od) | {"script": script_sha()}, od)
        # ブロックが取れない症例は「片づいた失敗」として取り直さない（やり直しても変わらない）
        df_low = pd.read_csv(od / "windows" / "case_9001.csv")
        df_low["n_good"] = 3
        _w, _s, e_nb = stage2_case(9001, df_low, loader=loader, blk_dir=od / "blocks",
                                   n_blocks=1, block_len=2)
        rep("連続して解析できるウィンドウが足りなければブロックを取らない", e_nb == E_NO_BLOCK, str(e_nb))
        rec_nb = read_case(9001, od)
        rec_nb["stage2"] = {"ok": False, "t_s": 0.0, "error": E_NO_BLOCK, "settled": True}
        write_case(rec_nb, od)
        st_nb, _x = cache_state(9001, "all", od, got)
        summ_nb, cnt_nb = collect_summary([9001], od)
        rep("その症例は取り直さず、ブロックの取れなかった数として数える（§3）",
            st_nb == "done" and cnt_nb["n_noblock"] == 1 and cnt_nb["n_failed"] == 0,
            f"{st_nb}・{cnt_nb}")
        write_case(rec, od)              # 元の記録に戻す

        # 失敗を記録に残す
        def bad_loader(_c):
            raise RuntimeError("取得できない")
        rec3 = process_case(9002, stage="all", loader=bad_loader, out_dir=od,
                            n_blocks=1, block_len=2, got=got)
        rep("取得に失敗した症例は理由つきで記録に残る（黙って落とさない。§3）",
            rec3["error"] and "取得" in rec3["error"] and case_path(9002, od).exists(),
            rec3["error"][:40])
        summ, cnt2 = collect_summary([9001, 9002, 9003], od)
        rep("失敗も未処理も行として残り、分母が母集団のままである（§3）",
            len(summ) == 3 and cnt2 == {"n_pool": 3, "n_done": 1, "n_failed": 1,
                                        "n_todo": 1, "n_noblock": 0},
            str(cnt2))
        rep("済みの症例の値が症例ごとの表に入る",
            np.isfinite(float(summ.loc[summ["caseid"] == 9001, "id_ens_amb"].iloc[0])))
        # 表の組み立て
        res = apply_criteria(summ, with_ci=False)
        meta = {"script": "0" * 12, "sap_tag": "sap3-test", "env": dict(REF), "pda2": "x",
                "n_pool": 3, "n_done": 1, "n_failed": 1, "n_todo": 1, "n_noblock": 0, "n_win": 11,
                "n_ok_win": 11, "n_block_win": 2, "date": "2026-09-12", "env_dependent": False}
        a = render_outcome(res, meta)
        b = render_outcome(res, meta)
        rep("表は二度組み立てても 1 行も違わない（時刻を読まない）", a == b, f"{len(a)} 行")
        rep("表に主要評価の 8 行と陽性対照と読み方が載る",
            sum(1 for ln in a if any(lab in ln for _c, lab, _s, _x in PRIMARY_ROWS)) >= 8
            and any("陽性対照" in ln for ln in a) and any("結果の読み方" in ln for ln in a))
        meta_env = dict(meta, env_dependent=True)
        c_env = render_outcome(res, meta_env)
        rep("環境依存なら判定を出さず、その旨が表に出る（§8）",
            any("環境依存" in ln for ln in c_env)
            and not any("  成立" in ln or "  不成立" in ln for ln in c_env))
        res_bad = apply_criteria(summ.assign(ac_pwtt_ms=0.1), with_ci=False)
        c_ctl = render_outcome(res_bad, meta)
        rep("陽性対照が通らなければ表全体を無効とする（§7）",
            any("表全体を無効" in ln for ln in c_ctl))
        oj = outcome_json(res, meta)
        other = json.loads(json.dumps(oj))
        first = PRIMARY_ROWS[0][0]
        other["primary"][first]["pass"] = not other["primary"][first]["pass"]
        rep("別の環境の合否と食い違う行を環境依存として挙げる（§10）",
            len(compare_environments(res, other)) == 1
            and "環境依存" in compare_environments(res, other)[0])
        # 所要時間の見積り
        el_lines = estimate_lines([9001, 9002], od, jobs=(1, 8), n_target=POOL_N)
        rep("所要時間の見積りが実測から出る（1 並列と 8 並列）",
            any("8 並列" in ln for ln in el_lines) and any("段階2" in ln for ln in el_lines),
            el_lines[-2][:70])

    # ---------------- 10. パイロットの照合の部品
    print("\n10. パイロットの再現の突き合わせ（--pilot）")
    a = pd.DataFrame({"caseid": [1, 2], "id_x": [0.5, 0.25], "ac_x": [0.1, np.nan]})
    b = pd.DataFrame({"caseid": [1, 2], "id_x": [0.5, 0.20], "ac_x": [0.1, 0.4]})
    with tempfile.TemporaryDirectory() as td:
        p = Path(td) / "ref.csv"
        b.to_csv(p, index=False)
        lines = compare_pilot(a, p)
    rep("列ごとの最大の差と、片方だけ欠測の数が出る",
        any("0.050000" in ln for ln in lines) and any("id_x" in ln for ln in lines),
        [ln.strip() for ln in lines if "id_x" in ln][0][:60])
    rep("照合先が無ければその旨を出す", "照合先が無い" in compare_pilot(a, Path("/no/such.csv"))[0])

    print("\n" + ("ALL PASS" if ok else "FAIL あり"))
    return 0 if ok else 1


# ================================================================ 入口
def main() -> None:                       # noqa: C901
    warnings.filterwarnings("ignore", message="All-NaN slice")
    warnings.filterwarnings("ignore", message="Mean of empty slice")
    warnings.filterwarnings("ignore", message="Values in x were outside bounds")
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--selftest", action="store_true", help="合成データで筋道を検算する（既定の入口）")
    ap.add_argument("--check", action="store_true", help="版・凍結・進み具合だけ見る")
    ap.add_argument("--list-cases", type=str, default=None, metavar="OUT.csv",
                    help="母集団の一覧を書き出す（除外の理由つき）")
    ap.add_argument("--run", action="store_true", help="母集団の症例を処理する（--sap-tag が要る）")
    ap.add_argument("--pilot", action="store_true",
                    help="パイロット 20 例で再現を確かめる（タグは要らない。新しい解析ではない）")
    ap.add_argument("--summarise", action="store_true", help="記録から §8 の表を組み立てる")
    ap.add_argument("--estimate", action="store_true", help="実測から母集団の所要時間を見積もる")
    ap.add_argument("--stage", choices=["1", "2", "all"], default="all", help="処理する段階")
    ap.add_argument("--jobs", type=int, default=1, help="並列に処理する症例数（既定 1）")
    ap.add_argument("--limit", type=int, default=None, help="先頭から何例だけ処理するか（動作確認用）")
    ap.add_argument("--sap-tag", type=str, default=None, help="凍結した事前登録の git タグ")
    ap.add_argument("--allow-env-mismatch", action="store_true",
                    help="主環境と版が違っても走らせる（出力はすべて環境依存と記す）")
    ap.add_argument("--refresh-stale", action="store_true",
                    help="環境が食い違う記録を消して作り直す（既定は止まる）")
    ap.add_argument("--no-retry-failed", action="store_true", help="前回失敗した症例を取り直さない")
    ap.add_argument("--target-csv", type=str, default=None, help="母集団の元の表（既定 data/target_cases.csv）")
    ap.add_argument("--out", type=str, default=None, help="症例ごとの記録の置き場（既定 data/paper3）")
    ap.add_argument("--results-dir", type=str, default=None, help="表の書き出し先（既定 docs/research/results）")
    ap.add_argument("--sensitivity-json", type=str, default=None,
                    help="感度解析（vitaldb 1.7.2）の 44_paper3_outcome.json。合否が反転した行を環境依存と記す")
    ap.add_argument("--date", type=str, default=None, help="表に載せる実行日（既定は今日）")
    args = ap.parse_args()

    if args.selftest:
        sys.exit(selftest())
    if args.jobs < 1:
        ap.error("--jobs は 1 以上")

    out_dir = Path(args.out) if args.out else (OUT / "pilot" if args.pilot else OUT)
    res_dir = Path(args.results_dir) if args.results_dir else RESULTS
    got = versions()
    bad_env = env_mismatch(got)
    env_dep = bool(bad_env)

    if args.list_cases:
        pool, err = build_pool(target_csv=args.target_csv)
        if err:
            print(f"★ {err}")
            sys.exit(2)
        cnt = pool_counts(pool)
        src = Path(args.target_csv) if args.target_csv else DATA / "target_cases.csv"
        print("母集団の作り方（事前登録 §3。乱数種は使わない）")
        for ln in pool_arithmetic_lines(cnt, src):
            print(ln)
        same, note = check_pilot_against_32(target_csv=args.target_csv)
        if same is None:
            print(f"  注 {note}")
        elif same:
            print(f"  パイロット 20 例と 32番の抽出（seed 0）の照合: 一致  {note}")
        else:
            print(f"  ★ §3 のパイロット 20 例が 32番の抽出（seed 0）と一致しない。{note}")
            print("     入力が事前登録の前提とする表ではない。この一覧で解析を始めないこと")
        p = Path(args.list_cases)
        p.parent.mkdir(parents=True, exist_ok=True)
        pool.to_csv(p, index=False)
        print(f"\n{p} に書き出した（{len(pool)} 行・解析対象 {cnt['n_pool']} 例）")
        if cnt["n_pool"] != POOL_N:
            print(f"★ 解析対象が {POOL_N} 例にならない。入力が事前登録の前提と違う")
            sys.exit(2)
        if same is False:
            sys.exit(2)
        sys.exit(0)

    pool, perr = build_pool(target_csv=args.target_csv)
    ids = None if pool is None else (sorted(PILOT_CASES) if args.pilot else pool_ids(pool))
    if args.pilot:
        ids = sorted(PILOT_CASES)

    if args.check:
        fz = freeze_state(args.sap_tag) if args.sap_tag else None
        show_check(got, bad_env, fz, out_dir, ids)
        if perr:
            print(f"\n  注 {perr}")
        sys.exit(2 if bad_env else 0)

    if args.estimate and not (args.run or args.pilot):
        if ids is None:
            print(f"★ {perr}")
            sys.exit(2)
        print("所要時間の見積り（実測。事前登録 §10・lab_log 追記115）")
        for ln in estimate_lines(ids, out_dir):
            print(ln)
        sys.exit(0)

    if args.run or args.pilot:
        if bad_env and not args.allow_env_mismatch:
            print("★ 主環境（事前登録 §10）と版が違う。症例を処理しない。")
            for k, g, w in bad_env:
                print(f"   {k}: {g} → {w} に合わせること")
            print("   承知のうえで走らせるなら --allow-env-mismatch"
                  "（出力は環境依存と記し、主要評価の判定を出さない）")
            sys.exit(2)
        if args.run:
            if pool is None:
                print(f"★ {perr}")
                sys.exit(2)
            cnt = pool_counts(pool)
            if cnt["n_pool"] != POOL_N:
                print(f"★ 解析対象が {cnt['n_pool']} 例で、事前登録の {POOL_N} 例と違う")
                sys.exit(2)
            same, note = check_pilot_against_32(target_csv=args.target_csv)
            if same is False:
                print(f"★ §3 のパイロット 20 例が 32番の抽出と一致しない。{note}")
                sys.exit(2)
            fz = freeze_state(args.sap_tag)
            if not fz["ok"]:
                print("★ 事前登録が凍結されていない。母集団の症例を処理しない（§15）。")
                print(f"   {fz['why']}")
                print("   手順: 内容を確定して commit → git tag → Zenodo で DOI（§冒頭）")
                print("   パイロット 20 例の再現だけなら --pilot（タグは要らない）")
                sys.exit(2)
            print("母集団の作り方（事前登録 §3）")
            for ln in pool_arithmetic_lines(cnt, Path(args.target_csv) if args.target_csv
                                            else DATA / "target_cases.csv"):
                print(ln)
        work = list(ids)
        if args.limit:
            work = work[:args.limit]
            print(f"\n★ --limit {args.limit} なので先頭 {len(work)} 例だけ処理する（動作確認用。集計は不完全）")
        rc = run_cases(work, args.stage, args.jobs, out_dir, got,
                       retry_failed=not args.no_retry_failed, refresh_stale=args.refresh_stale)
        if rc:
            sys.exit(rc)
        if args.pilot:
            summ, cnt2 = collect_summary(work, out_dir)
            print("\n" + "=" * 96)
            print("パイロット 20 例の再現の確認（32番・34番が既に解析した症例。**新しい解析ではない**）")
            print("=" * 96)
            print(f"  処理できた {cnt2['n_done']} 例・失敗 {cnt2['n_failed']} 例")
            was = pilot_report_versions()
            now = {"pda2": pda2.code_version(), "vitaldb": got.get("vitaldb")}
            if was:
                for k in ("vitaldb", "pda2"):
                    if k in was:
                        print(f"  {k}: 今 {now.get(k)} ／ パイロットの report {was[k]}"
                              f"  {'一致' if was[k] == now.get(k) else '★違う（§6 の識別子）'}")
            print("\n段階1（32番）")
            for ln in compare_pilot(summ, PILOT_REF_32):
                print(ln)
            ref34 = find_pilot_ref_34()
            print("\n段階2（34番）")
            if ref34 is None:
                print("  照合先が無い（34番の症例ごとの表が見つからない）")
            else:
                # 34番の表の列名をこちらの名前に合わせる（段階1 の同名の列と取り違えないため）
                ren = {"n_windows": "n_block_windows", "type4": "b_type4"}
                ren.update({f"{k}pwtt_ms": f"{k}b_pwtt_ms"
                            for k in ("", "id_", "ac_", "med_", "cv_", "npair_")})
                for ln in compare_pilot(summ, ref34, rename=ren):
                    print(ln)
        if args.estimate:
            print("\n所要時間の見積り（実測。lab_log 追記115 の見積りと比べる）")
            for ln in estimate_lines(work, out_dir, n_target=POOL_N):
                print(ln)
        sys.exit(0)

    if args.summarise:
        if ids is None:
            print(f"★ {perr}")
            sys.exit(2)
        summ, cnt2 = collect_summary(ids, out_dir)
        notes, bad = [], []
        # 記録の環境がそろっているかを見る（混ざっていれば判定しない）
        envs = set()
        for cid in ids:
            rec = read_case(cid, out_dir)
            if rec:
                envs.add(json.dumps(rec.get("env"), sort_keys=True, ensure_ascii=False))
        if len(envs) > 1:
            bad.append(f"症例ごとの記録に {len(envs)} 通りの環境が混ざっている。作り直すこと")
            env_dep = True
        rec_env = json.loads(list(envs)[0]) if len(envs) == 1 else dict(got)
        if env_mismatch(rec_env):
            env_dep = True
            bad.append("症例を処理した環境が主環境（§10）と違う。**合否を所見にしない**")
        if cnt2["n_todo"]:
            bad.append(f"未処理が {cnt2['n_todo']} 例ある。母集団の全例を処理してから集計すること（§3）")
        if cnt2["n_failed"]:
            notes.append(f"取得または解析に失敗した症例 {cnt2['n_failed']} 例。"
                         "差し替えはしない。分母は母集団の全例である（§3）")
        if cnt2["n_noblock"]:
            notes.append(f"段階2 のブロックが取れなかった症例 {cnt2['n_noblock']} 例"
                         f"／{cnt2['n_pool']} 例（§3。差し替えはしない）")
        res = apply_criteria(summ)
        other = None
        if args.sensitivity_json:
            try:
                other = json.loads(Path(args.sensitivity_json).read_text(encoding="utf-8"))
            except Exception as e:      # noqa: BLE001
                bad.append(f"感度解析の合否を読めない: {e}")
        flips = compare_environments(res, other) if other else []
        meta = {"script": script_sha(), "sap_tag": args.sap_tag, "env": rec_env,
                "pda2": pda2.code_version(), "date": args.date or time.strftime("%Y-%m-%d"),
                "env_dependent": env_dep, "notes": notes + flips, "bad": bad}
        meta.update(cnt2)
        for k, c in (("n_win", "n_windows"), ("n_ok_win", "n_analyzable"),
                     ("n_block_win", "n_block_windows")):
            meta[k] = int(np.nansum(summ[c].to_numpy(float))) if c in summ else 0
        meta["descriptive"] = descriptive_lines(summ, out_dir)
        lines = render_outcome(res, meta)
        print("\n".join(lines))
        res_dir.mkdir(parents=True, exist_ok=True)
        tail = "_env_mismatch" if env_dep else ""
        (res_dir / f"44_paper3_outcome{tail}.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")
        summ.to_csv(res_dir / f"44_paper3_per_case{tail}.csv", index=False)
        (res_dir / f"44_paper3_outcome{tail}.json").write_text(
            json.dumps(outcome_json(res, meta), ensure_ascii=False, indent=1), encoding="utf-8")
        print(f"\n書き出した: {M43.rel(res_dir / f'44_paper3_outcome{tail}.txt')}・"
              f"{M43.rel(res_dir / f'44_paper3_per_case{tail}.csv')}・"
              f"{M43.rel(res_dir / f'44_paper3_outcome{tail}.json')}")
        sys.exit(1 if bad else 0)

    ap.print_help()
    sys.exit(0)


if __name__ == "__main__":
    main()
