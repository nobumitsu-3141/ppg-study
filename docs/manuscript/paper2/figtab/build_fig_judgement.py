#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""図1 判定の図 ― 表1（決定試験・4,374 名・6 層）の年齢層内 Spearman |ρ| の中央値を点で示し、規準線 0.30 を引く。

左の枠が ΔT × 大動脈脈波伝播速度、右の枠が RI × 末梢血管抵抗。縦は表1 の 6 行（表の順）。
値はすべて `data/paper2_numbers.json`（`../02_tables.md` を機械で読んだもの）から取り、手で打たない。
判定（成立・不成立）は図に書かない。段（A・C）を出すので、脚注に段の注釈を 1 行置く（CLAUDE.md §3）。

使い方
    python3 build_fig_judgement.py                 和文・英文の両方を out/ に書く
    python3 build_fig_judgement.py --lang en       英文だけ
    python3 build_fig_judgement.py --selftest      描いた値と JSON の一致・最小文字サイズ・段の注釈・禁止語を確かめる
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import re
import sys
import textwrap
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt                      # noqa: E402
from matplotlib.gridspec import GridSpec             # noqa: E402

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import common                                        # noqa: E402
from common import (PALETTE, L, STAGE_NOTE, mm, setup, save, load_numbers,   # noqa: E402
                    check_min_font, texts_of)

NAME = "fig_judgement"
REPO = HERE.parents[3]
LABELS = json.loads((HERE / "data" / "labels.json").read_text(encoding="utf-8"))

# 行の族ごとの色と記号（分解法＝円、特徴点法＝四角、早期振幅比＝三角、陽性対照＝菱形）
FAMILY = {
    "pda_frozen": ("pda", "o"),
    "pda_v2_skewgauss": ("pda", "o"),
    "pda_v2_gamma": ("pda", "o"),
    "landmark": ("landmark", "s"),
    "amp_ratio": ("amp", "^"),
    "ptt_control": ("control", "D"),
}
COLS = ("dt_pwv", "ri_pvr")

# 図の中の語（和・英）。表1 の語をそのまま使う
T = {
    "ja": {
        "tierC_only": "C 段のみ",
        "accepted": "採択 {n}",
        "tier": "{s}",
        "not_evaluated": "未検証",
        "dash": "—",
        "criterion_head": "判定規準（実行前に凍結）: ",
        "fill_note": "図は絶対値。塗りつぶし＝全層で予測の向き、白抜き＝それ以外、または表1 に層の数の記載なし。",
    },
    "en": {
        "tierC_only": "tier C only",
        "accepted": "accepted {n}",
        "tier": "{s}",
        "not_evaluated": "not evaluated",
        "dash": "—",
        "criterion_head": "Criterion, frozen before the run: ",
        "fill_note": "Magnitudes shown. Filled marker, predicted sign in every stratum; "
                     "open, otherwise or stratum count not reported in table 1.",
    },
}


def _fmt_n(n: int) -> str:
    return f"{n:,}"


def wrap_label(s: str, lang: str) -> str:
    """縦軸の行名を 2 行に折る（文字は変えない。和文は「（」の前、英文は語の切れ目）。"""
    if lang == "ja":
        if "（" in s and len(s) > 10:
            return s.replace("（", "\n（", 1)
        return s
    return "\n".join(textwrap.wrap(s, width=30, break_long_words=False))


def _wrap_ja(s: str, units: int) -> str:
    """和文を表示幅で折る（全角 2・半角 1 の単位。空白で切らない）。"""
    lines, cur, w = [], "", 0
    for ch in s:
        cw = 2 if ord(ch) > 0x2E7F else 1
        if w + cw > units:
            lines.append(cur)
            cur, w = "", 0
        cur += ch
        w += cw
    if cur:
        lines.append(cur)
    return "\n".join(lines)


def wrap_text(s: str, lang: str, width_ja: int = 102, width_en: int = 112) -> str:
    if lang == "ja":
        return _wrap_ja(s, width_ja)
    return "\n".join(textwrap.wrap(s, width=width_en, break_long_words=False, break_on_hyphens=False))


def criterion_text(meta: dict, lang: str) -> str:
    c = meta["criterion"]
    if lang == "ja":
        sign = c["sign_prediction"].rstrip("。")
        return (T["ja"]["criterion_head"] + c["text"] + "（" + sign + "）。" + T["ja"]["fill_note"])
    n = c["strata_required"]
    thr = c["min_median_abs_rho"]
    return (T["en"]["criterion_head"]
            + f"predicted sign in all {n} strata and median |ρ| ≥ {thr:.2f} "
            + "(ΔT × aortic PWV negative, RI × peripheral vascular resistance positive). "
            + T["en"]["fill_note"])


def expected_points(numbers: dict) -> list[dict]:
    """表1 から描くべき点を起こす（自己検査でも同じ関数で JSON を読み直して比べる）。"""
    pts = []
    for row in numbers["tables"]["表1"]["rows"]:
        for col in COLS:
            cell = row[col]
            if cell.get("rho") is not None:
                pts.append({"id": row["id"], "col": col, "stage": None, "x": cell["rho"],
                            "filled": cell.get("strata_pass") == cell.get("strata_total")
                            and cell.get("strata_total") is not None})
            elif "stages" in cell:
                for st in ("A", "C"):
                    sc = cell["stages"].get(st)
                    if sc and sc.get("rho") is not None:
                        pts.append({"id": row["id"], "col": col, "stage": st, "x": sc["rho"],
                                    "filled": sc.get("strata_pass") is not None
                                    and sc.get("strata_pass") == sc.get("strata_total")})
    return pts


def build(lang: str, numbers: dict):
    """図を組む。戻り値は (fig, 描いた点の一覧, 規準線の x)。"""
    setup(lang)
    plt.rcParams.update({"xtick.labelsize": 8, "ytick.labelsize": 8, "legend.fontsize": 8,
                         "font.family": list(plt.rcParams["font.family"]) + ["DejaVu Sans"]})
    t1 = numbers["tables"]["表1"]
    meta = numbers["meta"]
    crit = meta["criterion"]["min_median_abs_rho"]
    rows = t1["rows"]
    n = len(rows)
    tx = T[lang]
    stage_name = {k: v[lang] for k, v in LABELS["stages"].items()}

    fig = plt.figure(figsize=(mm(150), mm(88)))
    bottom = 0.35
    gs = GridSpec(1, 2, figure=fig, left=0.29, right=0.985, top=0.91, bottom=bottom, wspace=0.14)
    axes = [fig.add_subplot(gs[0, 0]), fig.add_subplot(gs[0, 1], sharey=None)]
    titles = {"dt_pwv": "(a) " + L[lang]["dt_pwv"], "ri_pvr": "(b) " + L[lang]["ri_pvr"]}
    drawn = []
    for ax, col in zip(axes, COLS):
        ax.set_xlim(0, 1.06)
        ax.set_ylim(n - 0.4, -0.6)
        ax.set_xticks([0, 0.2, 0.4, 0.6, 0.8, 1.0])
        ax.set_xticklabels(["0", "0.2", "0.4", "0.6", "0.8", "1.0"])
        ax.set_yticks(range(n))
        if col == COLS[0]:
            ax.set_yticklabels([wrap_label(LABELS["methods"][r["id"]][lang], lang) for r in rows])
        else:
            ax.set_yticklabels([])
            ax.tick_params(axis="y", length=0)
        ax.set_title(titles[col], loc="center", fontsize=8)
        ax.axvline(crit, color=PALETTE["grey"], lw=0.8, ls=(0, (4, 2)), zorder=1)
        ax.text(crit + 0.03, n - 0.55, L[lang]["criterion"], ha="left", va="center",
                fontsize=8, color=PALETTE["grey"])
        for i, row in enumerate(rows):
            color = PALETTE[FAMILY[row["id"]][0]]
            marker = FAMILY[row["id"]][1]
            cell = row[col]

            def put(x, filled, stage=None, ms=5.5):
                ln, = ax.plot([x], [i], marker=marker, ms=ms, ls="none",
                              mfc=color if filled else "white", mec=color, mew=1.0, zorder=3)
                drawn.append({"id": row["id"], "col": col, "stage": stage, "x": float(ln.get_xdata()[0]),
                              "filled": filled})
                return ln

            if cell.get("rho") is not None:
                filled = cell.get("strata_total") is not None and cell["strata_pass"] == cell["strata_total"]
                put(cell["rho"], filled)
                ax.annotate(cell["strata"], (cell["rho"], i), xytext=(5, 0), textcoords="offset points",
                            ha="left", va="center", fontsize=8, color=PALETTE["ink"])
            elif "stages" in cell:
                st = cell["stages"]
                has_a = st.get("A", {}).get("rho") is not None
                xa = st["A"]["rho"] if has_a else None
                xc = st["C"]["rho"]
                if has_a:
                    # A 段と C 段を細線で結ぶ
                    ax.plot([xa, xc], [i, i], color=PALETTE["light"], lw=0.8, zorder=2)
                    fa = st["A"].get("strata_pass") is not None and st["A"]["strata_pass"] == st["A"]["strata_total"]
                    put(xa, fa, "A")
                    ax.annotate(f"A {st['A']['strata']}", (xa, i), xytext=(5, 0), textcoords="offset points",
                                ha="left", va="center", fontsize=8, color=PALETTE["ink"])
                fc = st["C"].get("strata_pass") is not None and st["C"]["strata_pass"] == st["C"]["strata_total"]
                put(xc, fc, "C")
                if has_a:
                    ax.annotate("C", (xc, i), xytext=(5, 0), textcoords="offset points",
                                ha="left", va="center", fontsize=8, color=PALETTE["ink"])
                    if cell.get("adopted"):
                        ax.annotate(tx["accepted"].format(n=_fmt_n(cell["adopted"]["n"])), (xc, i),
                                    xytext=(-6, 0), textcoords="offset points",
                                    ha="right", va="center", fontsize=8, color=PALETTE["ink"])
                else:
                    # 第2版 歪みガウス: C 段のみ。採択数（ΔT の欄）か層の数（RI の欄）を添える
                    if cell.get("adopted"):
                        a = cell["adopted"]
                        s = tx["tierC_only"] + "\n" + tx["accepted"].format(n=f"{_fmt_n(a['n'])}/{_fmt_n(a['of'])}")
                    elif st["C"].get("strata"):
                        s = tx["tierC_only"] + ("・" if lang == "ja" else "; ") + st["C"]["strata"]
                    else:
                        s = tx["tierC_only"]
                    ax.annotate(s, (xc, i), xytext=(5, 0), textcoords="offset points",
                                ha="left", va="center", fontsize=8, color=PALETTE["ink"], linespacing=1.1)
            elif cell.get("dash"):
                ax.text(0.02, i, tx["dash"], ha="left", va="center", fontsize=8, color=PALETTE["grey"])
            elif cell.get("note"):
                ax.text(0.02, i, tx["not_evaluated"], ha="left", va="center", fontsize=8, color=PALETTE["grey"])
    fig.text((0.29 + 0.985) / 2, bottom - 0.075, L[lang]["rho"], ha="center", va="top", fontsize=8)
    footer = wrap_text(criterion_text(meta, lang), lang) + "\n" + wrap_text(STAGE_NOTE[lang], lang)
    fig.text(0.01, 0.012, footer, ha="left", va="bottom", fontsize=8, color=PALETTE["ink"], linespacing=1.3)
    return fig, drawn, crit


def legend_text(lang: str, numbers: dict) -> str:
    t1 = numbers["tables"]["表1"]
    meta = numbers["meta"]
    n_subj = _fmt_n(meta["n_subjects_decision_test"])
    thr = meta["criterion"]["min_median_abs_rho"]
    if lang == "ja":
        return "\n".join([
            f"図1　判定の図 ― 表1 の年齢層内 Spearman |ρ| の中央値と規準線 {thr:.2f}",
            "",
            f"何を示すか: 決定試験（PWDB {n_subj} 名・6 層）で、表1 の 6 通りの指標の作り方ごとに、"
            "ΔT × 大動脈脈波伝播速度（a）と RI × 末梢血管抵抗（b）の年齢層内 Spearman 順位相関の絶対値の中央値を点で示す。"
            f"破線は実行前に凍結した規準（{meta['criterion']['text']}）。{meta['criterion']['sign_prediction']}"
            "塗りつぶしは全層で予測の向き、白抜きはそれ以外か表1 に層の数の記載がないもの。点の横の x/6 は予測の向きを持った層の数。"
            "第2版 歪みガウスは採択 2/4,374 で A・B 段が判定できないので C 段のみ、第2版 ガンマは A 段（採択 103）と C 段を細線で結んだ。"
            "陽性対照に RI の欄は無く（—）、早期振幅比の RI は未検証。判定の札は図に書かず表に任せる。",
            "",
            "出典: `02_tables.md` 表1（`docs/research/roadmap_v1.md` §9）。"
            "凍結版は 20番 `20_pwdb_validity.py`（`data/pwdb/pwdb_indices.csv`。lab_log 2026-09-03「研究0 の結果」）、"
            "特徴点法と陽性対照は 23番 `23_pwdb_landmarks.py`（lab_log 2026-09-03「判定の訂正」）、"
            "第2版と早期振幅比は 26番 `26_pwdb_compare.py`・27番 `27_threshold_sensitivity.py`"
            "（`data/pwdb/pwdb_compare.csv`・`pwdb_compare_report.txt`。lab_log 追記11・12）。"
            "数値は `data/paper2_numbers.json` から台本 `build_fig_judgement.py` が読む。",
            "",
            "段の注釈: " + STAGE_NOTE["ja"],
            "",
            f"表1 の出所（02_tables.md の記載）: {t1['source']}",
        ])
    return "\n".join([
        f"Figure 1. Decision figure: median within-age-stratum Spearman |ρ| of table 1 against the criterion line {thr:.2f}.",
        "",
        f"What is shown: for the decision test (PWDB, {n_subj} virtual subjects, six age strata) and each of the six index "
        "constructions of table 1, the median across strata of the absolute within-stratum Spearman rank correlation of "
        "ΔT with aortic PWV (a) and of RI with peripheral vascular resistance (b). The dashed line is the criterion frozen "
        f"before the run (predicted sign in all {meta['criterion']['strata_required']} strata and median |ρ| ≥ {thr:.2f}; "
        "ΔT × aortic PWV negative, RI × peripheral vascular resistance positive; magnitudes shown). Filled markers have the "
        "predicted sign in every stratum; open markers do not, or table 1 does not report the stratum count. The x/6 beside "
        "a marker is the number of strata with the predicted sign. The rebuilt skew-Gaussian route accepted 2 of 4,374 "
        "subjects, so tiers A and B could not be evaluated and only tier C is plotted; for the rebuilt gamma route tier A "
        "(accepted 103) and tier C are joined by a thin line. The positive control has no RI entry (—) and the RI of the "
        "early amplitude ratio was not evaluated. Verdicts are not written in the figure; they are given in the table.",
        "",
        "Source: table 1 of `02_tables.md` (`docs/research/roadmap_v1.md` §9). Frozen version: script 20 "
        "`20_pwdb_validity.py` (`data/pwdb/pwdb_indices.csv`; lab_log 2026-09-03, results of study 0). Fiducial-point "
        "analysis and positive control: script 23 `23_pwdb_landmarks.py` (lab_log 2026-09-03, correction of the verdict). "
        "Rebuilt version and early amplitude ratio: scripts 26 `26_pwdb_compare.py` and 27 `27_threshold_sensitivity.py` "
        "(`data/pwdb/pwdb_compare.csv`, `pwdb_compare_report.txt`; lab_log entries 11 and 12). All numbers are read from "
        "`data/paper2_numbers.json` by `build_fig_judgement.py`.",
        "",
        "Tier note: " + STAGE_NOTE["en"],
    ])


# ---------------------------------------------------------------- 自己検査

def _banned_terms():
    """用語検査器（analysis/scripts/check_terminology.py）の禁止語の表を読む。写さない。"""
    path = REPO / "analysis" / "scripts" / "check_terminology.py"
    if not path.exists():
        return None
    spec = importlib.util.spec_from_file_location("check_terminology", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.BANNED


def _banned_hits(banned, strings) -> list[str]:
    hits = []
    for s in strings:
        for line in s.split("\n"):
            for term, _alt, allow in banned:
                if term in line and not (allow and re.sub(allow, "", line).find(term) < 0):
                    hits.append(f"{term}: {line[:40]}")
    return hits


def selftest() -> int:
    ok_all = True

    def rep(name, ok, detail=""):
        nonlocal ok_all
        ok_all &= bool(ok)
        print(f"  {'PASS' if ok else 'FAIL'}  {name}" + (f"  ({detail})" if detail and not ok else ""))

    banned = _banned_terms()
    for lang in ("ja", "en"):
        print(f"[{lang}]")
        fig, drawn, crit = build(lang, load_numbers())
        fresh = load_numbers()
        exp = expected_points(fresh)
        key = lambda p: (p["id"], p["col"], p["stage"] or "")   # noqa: E731
        d = {key(p): (p["x"], p["filled"]) for p in drawn}
        e = {key(p): (p["x"], p["filled"]) for p in exp}
        rep("描いた点の数が表1 から起こした数と同じ", len(drawn) == len(exp) == len(d),
            f"描いた {len(drawn)}・期待 {len(exp)}")
        diff = [k for k in e if k not in d or abs(d[k][0] - e[k][0]) > 1e-12 or d[k][1] != e[k][1]]
        rep("描いた |ρ| と塗りつぶしが JSON と一致（全点）", not diff, f"差 {diff}")
        rep("規準線が meta.criterion の値", abs(crit - fresh["meta"]["criterion"]["min_median_abs_rho"]) < 1e-12)
        texts = texts_of(fig)
        joined = "\n".join(texts)
        bad_font = check_min_font(fig)
        rep(f"文字はすべて {common.MIN_FONT_PT:g} pt 以上", not bad_font, f"{bad_font[:3]}")
        rep("段の注釈が脚注にある", STAGE_NOTE[lang] in joined.replace("\n", "") or
            STAGE_NOTE[lang].replace(" ", "") in joined.replace("\n", "").replace(" ", ""))
        rep("規準線の札がある", L[lang]["criterion"] in texts)
        verdict_words = ["成立", "合格", " pass", "fail"]
        rep("判定の語（成立・不成立・pass・fail）を図に書いていない",
            not any(w in joined for w in verdict_words))
        # 行名が labels.json と一字一句同じ（折り返しの改行を除く）
        ylabs = [t.get_text() for t in fig.axes[0].get_yticklabels()]
        want = [LABELS["methods"][r["id"]][lang] for r in fresh["tables"]["表1"]["rows"]]
        got = [s.replace("\n", "" if lang == "ja" else " ") for s in ylabs]
        rep("縦軸の行名が labels.json と同じ（表の順）", got == want, f"{got} != {want}")
        # 採択数が JSON の値
        sk = next(r for r in fresh["tables"]["表1"]["rows"] if r["id"] == "pda_v2_skewgauss")["dt_pwv"]["adopted"]
        gm = next(r for r in fresh["tables"]["表1"]["rows"] if r["id"] == "pda_v2_gamma")["dt_pwv"]["adopted"]
        rep("採択数の注釈が JSON の値", f"{sk['n']:,}/{sk['of']:,}" in joined and f"{gm['n']:,}" in joined)
        leg = legend_text(lang, fresh)
        if banned is None:
            print("  （用語検査器が無いので禁止語の確認は飛ばした）")
        else:
            hits = _banned_hits(banned, texts + [leg])
            rep("図と凡例文に禁止語が無い（検査器の表）", not hits, f"{hits[:3]}")
        plt.close(fig)
    print("RESULT", "PASS" if ok_all else "FAIL")
    return 0 if ok_all else 1


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--lang", choices=["ja", "en"], default=None, help="省略すると両方")
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--out-dir", default=str(common.OUT))
    a = ap.parse_args()
    if a.selftest:
        return selftest()
    common.OUT = Path(a.out_dir)
    common.OUT.mkdir(parents=True, exist_ok=True)
    numbers = load_numbers()
    for lang in ([a.lang] if a.lang else ["ja", "en"]):
        fig, _drawn, _crit = build(lang, numbers)
        paths = save(fig, NAME, lang)
        plt.close(fig)
        lp = common.OUT / f"{NAME}_legend_{lang}.txt"
        lp.write_text(legend_text(lang, numbers) + "\n", encoding="utf-8")
        for p in paths + [lp]:
            print(p)
    return 0


if __name__ == "__main__":
    sys.exit(main())
