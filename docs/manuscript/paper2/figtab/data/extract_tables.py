#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""`docs/manuscript/paper2/02_tables.md`（論文2 の表）を機械で読み、`paper2_numbers.json` に書く。

図表の台本（`../build_*.py`）は数値をこの JSON からだけ取り、手で打たない。
表の行は `|` で区切った行を正規表現で読む。セルの文字列は `raw` にそのまま残し、
数値はそこから機械で取り出す。太字（`**`）は `bold` に、`<br>` と全角の記号は数値を読むときだけ半角に直す。
行の見出し（和文）は `label_ja` にそのまま残し、表6・表6b・表6c のように同じ案が複数の表に出る表には
機械用の `id`（fb・trunc065・deriv など）を付ける。

読めなかったセルは落とさず `issues` に表・行・列・文字列を記録し、`raw` だけのセル（`unparsed: true`）として残す。

使い方
------
    JSON を書く
        python3 docs/manuscript/paper2/figtab/data/extract_tables.py
    既知の値と照合する（落ちたら終了コード 1）
        python3 docs/manuscript/paper2/figtab/data/extract_tables.py --selftest

出力は決定的である（日時を入れない。同じ markdown からは同じ JSON が出る）。
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]
SRC = HERE.parents[1] / "02_tables.md"
OUT = HERE / "paper2_numbers.json"


class ParseError(ValueError):
    pass


# ---------------------------------------------------------------------------
# 文字の正規化
# ---------------------------------------------------------------------------

_FW = {
    "（": "(", "）": ")", "／": "/", "−": "-", "－": "-", "〜": "~", "～": "~",
    "　": " ", "．": ".", "，": ",", "＋": "+", "＝": "=",
}
_FW.update({chr(0xFF10 + i): str(i) for i in range(10)})
FW = str.maketrans(_FW)
SUP = str.maketrans("⁰¹²³⁴⁵⁶⁷⁸⁹", "0123456789")
DASH = {"—", "–", "-", "―"}

NUM = r"[+-]?\d{1,3}(?:,\d{3})+(?:\.\d+)?|[+-]?\d+(?:\.\d+)?"


def unbold(raw: str) -> tuple[str, bool]:
    """セル全体を囲む `**` を外し、太字だったかを返す。"""
    s = raw.strip()
    m = re.fullmatch(r"\*\*((?:(?!\*\*).)+)\*\*", s)
    if m:
        return m.group(1).strip(), True
    return s, False


def norm(s: str) -> str:
    """数値を読むための正規化（全角 → 半角、`<br>` → 空白、空白の圧縮）。"""
    s = s.replace("<br>", " ").translate(FW)
    return re.sub(r"\s+", " ", s).strip()


def to_float(s: str) -> float:
    return float(s.replace(",", ""))


def to_int(s: str) -> int:
    return int(s.replace(",", ""))


def header_text(raw: str) -> str:
    s, _ = unbold(raw)
    return re.sub(r"\s+", " ", s.replace("<br>", " ")).strip()


# ---------------------------------------------------------------------------
# セルの読み方（列の種類ごと）
# ---------------------------------------------------------------------------

def parse_rho(s: str) -> dict:
    """`0.223(6/6)`・`R1_d 0.585(6/6)`・`0.798(3/4 層)`・`0.705`・`—`・`未検証`、
    および 表1 の「採択 2/4,374。A・B は判定不能、C 0.167」のような段ごとの記述。"""
    if s in DASH:
        return {"rho": None, "strata": None, "dash": True}
    if s == "未検証":
        return {"rho": None, "strata": None, "note": s}
    if "採択" in s or "判定不能" in s or re.search(r"(?<![A-Za-z0-9_])[ABC] \d+\.\d+", s):
        return parse_stage_text(s)
    m = re.fullmatch(
        r"(?:(?P<prefix>[A-Za-z][A-Za-z0-9_]*) )?(?P<v>\d+\.\d+)"
        r"(?: ?\((?P<a>\d+)/(?P<b>\d+)(?: 層)?\))?", s)
    if m:
        out = {"rho": float(m.group("v")), "strata": None}
        if m.group("a"):
            out["strata"] = f"{m.group('a')}/{m.group('b')}"
            out["strata_pass"] = int(m.group("a"))
            out["strata_total"] = int(m.group("b"))
        if m.group("prefix"):
            out["prefix"] = m.group("prefix")
        return out
    raise ParseError("相関のセルとして読めない")


def parse_stage_text(s: str) -> dict:
    out: dict = {"rho": None, "strata": None, "stages": {}}
    rest = s
    m = re.search(r"採択 (\d[\d,]*)(?:/(\d[\d,]*))?", rest)
    if m:
        out["adopted"] = {"n": to_int(m.group(1)), "of": to_int(m.group(2)) if m.group(2) else None}
        rest = rest.replace(m.group(0), " ")
    for m in re.finditer(r"([ABC])(?:・([ABC]))? は判定不能", rest):
        for letter in (m.group(1), m.group(2)):
            if letter:
                out["stages"][letter] = {"rho": None, "strata": None, "note": "判定不能"}
    rest = re.sub(r"([ABC])(?:・([ABC]))? は判定不能", " ", rest)
    pat = re.compile(r"(?<![A-Za-z0-9_])([ABC]) (\d+\.\d+)(?: ?\((\d+)/(\d+)(?: 層)?\))?")
    for m in pat.finditer(rest):
        st = {"rho": float(m.group(2)), "strata": None}
        if m.group(3):
            st["strata"] = f"{m.group(3)}/{m.group(4)}"
            st["strata_pass"] = int(m.group(3))
            st["strata_total"] = int(m.group(4))
        out["stages"][m.group(1)] = st
    rest = pat.sub(" ", rest)
    if re.search(r"\d", rest):
        raise ParseError(f"段ごとの記述に読めない数値が残った: {rest.strip()!r}")
    out["stages"] = dict(sorted(out["stages"].items()))
    return out


def parse_effect(s: str) -> dict:
    """表2: `−12.6（−0.37）` → 主効果 % と年齢層内 Spearman。"""
    m = re.fullmatch(r"(?P<v>[+-]?\d+(?:\.\d+)?)(?: ?\((?P<r>[+-]?\d+\.\d+)\))?", s)
    if not m:
        raise ParseError("主効果のセルとして読めない")
    out = {"effect_pct": float(m.group("v")), "rho": None}
    if m.group("r"):
        out["rho"] = float(m.group("r"))
    return out


def parse_num(s: str) -> dict:
    if s in DASH:
        return {"value": None, "dash": True}
    if re.fullmatch(NUM, s):
        return {"value": to_float(s)}
    raise ParseError("数値として読めない")


def parse_int(s: str) -> dict:
    if s in DASH:
        return {"value": None, "dash": True}
    if re.fullmatch(r"\d{1,3}(?:,\d{3})+|\d+", s):
        return {"value": to_int(s)}
    raise ParseError("整数として読めない")


def parse_pct(s: str) -> dict:
    if s in DASH:
        return {"value": None, "fraction": None, "unit": "%", "dash": True}
    m = re.fullmatch(r"(\d+(?:\.\d+)?) ?%", s)
    if not m:
        raise ParseError("百分率として読めない")
    v = float(m.group(1))
    return {"value": v, "fraction": round(v / 100.0, 6), "unit": "%"}


def parse_ms(s: str) -> dict:
    if s in DASH:
        return {"value": None, "unit": "ms", "dash": True}
    m = re.fullmatch(r"([+-]?\d+(?:\.\d+)?) ?ms", s)
    if m:
        return {"value": float(m.group(1)), "unit": "ms"}
    m = re.fullmatch(r"([+-]?\d+(?:\.\d+)?) ?\((.+)\)", s)
    if m:
        return {"value": float(m.group(1)), "unit": "ms", "note": m.group(2)}
    raise ParseError("ms の値として読めない")


def parse_range_ms(s: str) -> dict:
    m = re.fullmatch(r"(\d+(?:\.\d+)?) ?~ ?(\d+(?:\.\d+)?) ?ms", s)
    if not m:
        raise ParseError("範囲（ms）として読めない")
    return {"lo": float(m.group(1)), "hi": float(m.group(2)), "unit": "ms"}


def parse_sci(s: str) -> dict:
    """`3.71×10⁷` または通常の数値。"""
    if s in DASH:
        return {"value": None, "dash": True}
    m = re.fullmatch(r"(\d+(?:\.\d+)?)×10([⁰¹²³⁴⁵⁶⁷⁸⁹]+)", s)
    if m:
        exp = m.group(2).translate(SUP)
        return {"value": float(f"{m.group(1)}e{exp}"), "mantissa": float(m.group(1)), "exponent": int(exp)}
    if re.fullmatch(NUM, s):
        return {"value": to_float(s)}
    raise ParseError("指数表記として読めない")


def parse_frac(s: str) -> dict:
    if s in DASH:
        return {"num": None, "den": None, "dash": True}
    m = re.fullmatch(r"(\d+) ?/ ?(\d+)", s)
    if not m:
        raise ParseError("分数として読めない")
    return {"num": int(m.group(1)), "den": int(m.group(2))}


def parse_triple(s: str) -> dict:
    if s == "" or s in DASH:
        return {"values": None, "dash": s in DASH}
    m = re.fullmatch(r"(\d+\.\d+)/(\d+\.\d+)/(\d+\.\d+)", s)
    if not m:
        raise ParseError("3 つ組として読めない")
    return {"values": [float(m.group(i)) for i in (1, 2, 3)]}


def parse_breakdown(raw: str) -> dict:
    """表6b の内訳: `**g:hi 0.61**・**τ:lo 0.21**`、`α1:hi 0.25・μ1:lo 0.02（τ:lo 0.00）`。"""
    items = []
    for part in raw.split("・"):
        part = part.strip()
        paren = None
        m = re.fullmatch(r"(.*?)（(.*)）", part)
        if m:
            part, paren = m.group(1).strip(), m.group(2).strip()
        for txt, is_paren in ((part, False), (paren, True)):
            if txt is None:
                continue
            t, bold = unbold(txt)
            m2 = re.fullmatch(r"(?P<p>[^\s:]+):(?P<b>lo|hi) (?P<f>\d+\.\d+)", t)
            if not m2:
                raise ParseError(f"内訳の項目として読めない: {txt!r}")
            items.append({"param": m2.group("p"), "bound": m2.group("b"), "fraction": float(m2.group("f")),
                          "bold": bold, "parenthetical": is_paren, "raw": txt})
    return {"items": items}


def parse_stage(s: str) -> dict:
    if not re.fullmatch(r"[ABC]", s):
        raise ParseError("段として読めない")
    return {"stage": s}


def parse_verdict(s: str) -> dict:
    if s not in ("成立", "不成立", "合格", "不合格"):
        raise ParseError("判定として読めない")
    return {"verdict": s}


def parse_label_n(label: str) -> dict:
    """表5: `型4　いずれも無し（105・3 層）` → n と層数。"""
    m = re.search(r"\((\d[\d,]*)(?:・(\d+) 層)?\)$", norm(label))
    out = {"n": None, "strata_count": None}
    if m:
        out["n"] = to_int(m.group(1))
        if m.group(2):
            out["strata_count"] = int(m.group(2))
    return out


PARSERS = {
    "rho": parse_rho, "effect": parse_effect, "num": parse_num, "int": parse_int, "pct": parse_pct,
    "ms": parse_ms, "range_ms": parse_range_ms, "sci": parse_sci, "frac": parse_frac, "triple": parse_triple,
    "stage": parse_stage, "verdict": parse_verdict,
}


def parse_cell(kind: str, raw: str) -> dict:
    """1 セルを読む。戻り値は必ず `raw` と `bold` を持つ。"""
    inner, bold = unbold(raw)
    cell: dict = {"raw": raw}
    if kind == "text":
        cell.update({"text": inner, "bold": bold})
        return cell
    if kind == "breakdown":
        # セル全体が太字（`**τ:lo 0.33**`）なら、項目ごとの太字と同じ意味なので各項目に写す
        cell.update(parse_breakdown(inner))
        if bold:
            for it in cell["items"]:
                it["bold"] = True
        cell["bold"] = bold
        return cell
    s = norm(inner)
    if s == "":
        cell.update({"empty": True, "bold": False})
        if kind == "triple":
            cell["values"] = None
        else:
            cell["value"] = None
        return cell
    cell.update(PARSERS[kind](s))
    cell["bold"] = bold
    return cell


# ---------------------------------------------------------------------------
# 表ごとの列の意味と、行の機械用 id
# ---------------------------------------------------------------------------

FACTORS = [
    ("aortic_diameter", r"^大動脈径"), ("heart_rate", r"^心拍数"), ("ejection_time", r"^駆出時間"),
    ("map", r"^平均血圧"), ("pwv", r"^脈波伝播速度"), ("stroke_volume", r"^1回拍出量"),
]
METHODS_7A = [("pda_ppg", r"^分解（PPG）"), ("pda_pressure", r"^分解（圧）"), ("landmark", r"^特徴点法")]
TYPES = [("type1", r"^型1"), ("type3", r"^型3"), ("type4", r"^型4")]
BASES_3 = [
    ("skewgauss_a08", r"^歪みガウス α∈\[0,8\]"), ("gauss", r"^ガウス（歪みなし）"),
    ("skewgauss_pm8", r"^歪みガウス α∈\[−8,8\]"), ("gamma_frozen", r"^ガンマ（凍結"),
    ("gamma_wide", r"^ガンマ（広い"),
]

SPEC: dict[str, dict] = {
    "表1": dict(keys=["label_ja", "dt_pwv", "ri_pvr", "verdict"],
               kinds=["label", "rho", "rho", "verdict"],
               ids=[("pda_frozen", r"^分解法・凍結版"), ("pda_v2_skewgauss", r"^分解法・第2版 歪みガウス"),
                    ("pda_v2_gamma", r"^分解法・第2版 ガンマ"), ("landmark", r"^特徴点法"),
                    ("amp_ratio", r"^早期振幅比"), ("ptt_control", r"陽性対照")]),
    "表2": dict(keys=["label_ja", "landmark_dt", "pda_dt", "pda_ri", "amp_ratio"],
               kinds=["label", "effect", "effect", "effect", "effect"], ids=FACTORS),
    "表2b": dict(keys=["label_ja", "dt_minus1sd", "dt_base", "dt_plus1sd", "ri_minus1sd", "ri_base", "ri_plus1sd"],
                kinds=["label", "num", "num", "num", "num", "num", "num"], ids=FACTORS),
    "表2c": dict(keys=["label_ja", "median", "p5_p95"], kinds=["label", "ms", "range_ms"],
                ids=[("aorta_to_finger", r"^大動脈起始部"), ("radial_to_finger", r"^橈骨")]),
    "表3": dict(keys=["label_ja", "n_components", "wang_pass", "errx_median_ms", "nrmse_median",
                     "boundary_fraction", "dt_pwv"],
               kinds=["label", "int", "pct", "num", "num", "pct", "rho"], ids=BASES_3, carry="same"),
    "表4": dict(keys=["label_ja", "dt_pwv", "ri_pvr"], kinds=["label", "rho", "rho"],
               ids=[("tigges2017", r"^Tigges"), ("fleischhauer2020", r"^Fleischhauer"), ("couceiro2015", r"^Couceiro"),
                    ("wang2013", r"^Wang"), ("basso2024", r"^Basso"), ("goswami2010", r"^Goswami"),
                    ("landmark_ref", r"^参照")]),
    "表4_逸脱表": dict(keys=["label_ja", "deviation_ja"], kinds=["label", "text"],
                   ids=[("all", r"^全条件"), ("wang2013", r"^Wang"), ("couceiro2015", r"^Couceiro"),
                        ("tigges2017", r"^Tigges"), ("common", r"^共通")]),
    "表5": dict(keys=["label_ja", "landmark_dt_C", "pda_frozen_dt_A", "amp_ratio_C", "landmark_ri_C", "pda_frozen_ri_A"],
               kinds=["label_n", "rho", "rho", "rho", "rho", "rho"],
               ids=[("type1", r"^型1"), ("type3", r"^型3"), ("type4", r"^型4"), ("all", r"^全例")]),
    "表5b": dict(keys=["label_ja", "pwv_iqr_width_m_s", "pvr_iqr_width", "strata_ge8", "min_stratum_n"],
                kinds=["label", "num", "sci", "frac", "int"],
                ids=[("ratio_type1_type3", r"^型1 ÷ 型3"), ("type1", r"^型1"), ("type3", r"^型3"), ("type4", r"^型4")]),
    "表6": dict(keys=["label_ja", "dt_pwv_A", "dt_pwv_C", "ri_pvr_A", "ri_pvr_C", "pass_rate", "dt_offset_vs_landmark_ms_A"],
               kinds=["label", "rho", "rho", "rho", "rho", "num", "ms"],
               ids=[("fb", r"^凍結版"), ("dmu001", r"0\.08 → 0\.01"), ("reservoir", r"^貯留槽の項を足す"),
                    ("reservoir_tau015", r"0\.05 → 0\.15"), ("decay", r"指数減衰"), ("conv", r"^出力側の畳み込み"),
                    ("twostage", r"^2 段階"), ("trunc065", r"^当てはめを拍長の 0\.65 倍"), ("trunc055", r"^同 0\.55 倍"),
                    ("trunc075", r"^同 0\.75 倍"), ("trunc_abs045", r"^絶対時間 0\.45"), ("deriv", r"1 次微分"),
                    ("landmark", r"特徴点法")]),
    "表6b": dict(keys=["label_ja", "boundary_fraction", "breakdown"], kinds=["label", "num", "breakdown"],
                ids=[("fb", r"^凍結版"), ("reservoir_tau015", r"^貯留槽の項（同 0\.15 s）"),
                     ("reservoir", r"^貯留槽の項（時定数の下限 0\.05 s）"), ("decay", r"指数減衰"),
                     ("conv", r"^出力側の畳み込み"), ("twostage", r"^2 段階"), ("trunc065", r"^拍長の 0\.65 倍"),
                     ("trunc_abs045", r"^絶対時間 0\.45"), ("deriv", r"1 次微分")]),
    "表6c": dict(keys=["label_ja", "stage", "dt_pwv_0", "dt_pwv_001", "dt_pwv_002",
                      "ri_pvr_0", "ri_pvr_001", "ri_pvr_002", "pass_rate"],
                kinds=["label", "stage", "rho", "rho", "rho", "rho", "rho", "rho", "triple"],
                ids=[("fb", r"^凍結版"), ("trunc065", r"^拍長の 0\.65 倍"), ("deriv", r"1 次微分"),
                     ("landmark", r"特徴点法")],
                carry="empty", multi=True),
    "表6d": dict(keys=["label_ja", "stage", "type1", "type3", "type4", "all"],
                kinds=["label", "stage", "rho", "rho", "rho", "rho"],
                ids=[("dt_fb", r"^ΔT×PWV 凍結版"), ("dt_trunc065_dmu001", r"^ΔT×PWV 0\.65 倍"),
                     ("dt_landmark", r"^ΔT×PWV （参考）"), ("ri_fb", r"^RI×抵抗 凍結版"),
                     ("ri_deriv", r"^RI×抵抗 1 次微分"), ("ri_landmark", r"^RI×抵抗 （参考）")],
                multi=True),
    "表6e": dict(keys=["label_ja", "rule", "fb", "trunc065", "deriv", "landmark", "outcome"],
                kinds=["label", "text", "text", "text", "text", "text", "text"],
                ids=[("c6", r"^C6"), ("c7a", r"^C7a"), ("c7b", r"^C7b"), ("c8_dt", r"^C8 ΔT"), ("c8_ri", r"^C8 RI")]),
    "表7a": dict(keys=["type_ja", "method_ja", "n", "dt_diff_ms", "rho_pooled"],
                kinds=["label", "label", "int", "ms", "num"], ids=None),
    "表7b": dict(keys=["label_ja", "dt_pwv_A", "dt_pwv_C", "ri_pvr_A", "ri_pvr_C", "adoption_rate"],
                kinds=["label", "rho", "rho", "rho", "rho", "pct"],
                ids=[("ppg", r"^PPG"), ("pressure", r"^圧波形"), ("landmark", r"特徴点法")]),
}
EXPECTED_TABLES = list(SPEC)
NOISE_LEVELS = ["0", "0.01", "0.02"]

CRITERION_RE = re.compile(r"全6層で予測の符号を持ち、かつ中央値 \|ρ\| ≥ 0\.30")
SIGN_RE = re.compile(r"予測の符号は[^。]*。")
BOLD_RULE_RE = re.compile(r"太字は規準（([^）]*)）を満たす")
STAGE_DEF_RE = re.compile(r"(?:\*\*)?([ABC]) 段(?:\*\*)? ＝ ")
HEADING_RE = re.compile(r"^(#{1,6})\s+(.*?)\s*$")
SEP_RE = re.compile(r"^\|?\s*:?-{3,}:?\s*(\|\s*:?-{3,}:?\s*)*\|?\s*$")


# ---------------------------------------------------------------------------
# markdown の構造
# ---------------------------------------------------------------------------

def split_row(line: str) -> list[str]:
    s = line.strip()
    if s.startswith("|"):
        s = s[1:]
    if s.endswith("|") and not s.endswith("\\|"):
        s = s[:-1]
    return [c.replace("\\|", "|").strip() for c in re.split(r"(?<!\\)\|", s)]


def paragraphs(lines: list[str], start: int, end: int) -> list[dict]:
    """[start, end]（1 始まり・両端含む）の段落。空行と `---` で区切る。"""
    out, cur, cur_start = [], [], None
    for i in range(start, end + 1):
        s = lines[i - 1].strip()
        if s == "" or s == "---":
            if cur:
                out.append({"line_start": cur_start, "line_end": i - 1, "text": "\n".join(cur)})
                cur = []
            continue
        if not cur:
            cur_start = i
        cur.append(s)
    if cur:
        out.append({"line_start": cur_start, "line_end": end, "text": "\n".join(cur)})
    return out


def flat(text: str) -> str:
    return text.replace("\n", "")


def first_sentence(text: str) -> str:
    """括弧の深さ 0 にある最初の `。` までを返す。"""
    depth = 0
    for j, ch in enumerate(text):
        if ch in "（(":
            depth += 1
        elif ch in "）)":
            depth = max(0, depth - 1)
        elif ch == "。" and depth == 0:
            return text[:j + 1]
    return text


def extract_stage_defs(paras: list[dict]) -> list[dict]:
    occ = []
    for p in paras:
        text = flat(p["text"])
        ms = list(STAGE_DEF_RE.finditer(text))
        for k, m in enumerate(ms):
            start = m.end()
            limit = ms[k + 1].start() if k + 1 < len(ms) else len(text)
            depth0 = text[:m.start()].count("（") + text[:m.start()].count("(") \
                - text[:m.start()].count("）") - text[:m.start()].count(")")
            depth, end = depth0, limit
            for j in range(start, limit):
                ch = text[j]
                if ch in "（(":
                    depth += 1
                elif ch in "）)":
                    if depth == depth0:
                        end = j
                        break
                    depth -= 1
                elif ch == "。" and depth == depth0:
                    end = j
                    break
            occ.append({"stage": m.group(1), "text": text[start:end].rstrip("、。 "), "line": p["line_start"]})
    return occ


def match_id(rules, label: str):
    for rid, pat in rules:
        if re.search(pat, label):
            return rid
    return None


def build_rows(name: str, spec: dict, header: list[str], body: list[tuple[int, list[str]]], issues: list) -> dict:
    keys, kinds = spec["keys"], spec["kinds"]
    if len(header) != len(keys):
        issues.append({"table": name, "line": None, "col": None, "raw": " | ".join(header),
                       "problem": f"列数が仕様と違う（markdown {len(header)} 列・仕様 {len(keys)} 列）"})
    rows, groups = [], []
    group = None
    last_label = None
    for ln, cells in body:
        if all(c == "" for c in cells):
            continue
        if cells[0] != "" and all(c == "" for c in cells[1:]):
            group, _ = unbold(cells[0])
            groups.append(group)
            continue
        if len(cells) != len(keys):
            issues.append({"table": name, "line": ln, "col": None, "raw": " | ".join(cells),
                           "problem": f"セル数が仕様と違う（{len(cells)} 対 {len(keys)}）"})
        row: dict = {"id": None, "line": ln}
        if group is not None:
            row["group"] = group
        prev = None
        for i, (key, kind) in enumerate(zip(keys, kinds)):
            raw = cells[i] if i < len(cells) else ""
            if kind in ("label", "label_n"):
                label, bold = unbold(raw)
                row[key] = label
                row[key.replace("_ja", "") + "_bold"] = bold
                if spec.get("carry") == "empty" and label == "" and last_label is not None:
                    row[key] = last_label
                    row["label_carried"] = True
                elif spec.get("carry") == "same" and label == "同" and last_label is not None:
                    row["basis_ja"] = last_label
                elif i == 0:
                    last_label = label
                if kind == "label_n":
                    row.update(parse_label_n(label))
                continue
            try:
                if norm(unbold(raw)[0]) == "(同左)":
                    if prev is None:
                        raise ParseError("左のセルが無い")
                    cell = {k: v for k, v in prev.items()}
                    cell["raw"] = raw
                    cell["same_as_left"] = True
                else:
                    cell = parse_cell(kind, raw)
            except (ParseError, KeyError) as e:
                issues.append({"table": name, "line": ln, "col": key, "raw": raw, "problem": str(e)})
                cell = {"raw": raw, "bold": unbold(raw)[1], "unparsed": True}
            row[key] = cell
            prev = cell
        if spec.get("carry") == "same" and "basis_ja" not in row:
            row["basis_ja"] = row["label_ja"]
        # 参考・参照の行は比較の基準であり、直前の群見出しには属さない
        first_label = row.get(keys[0], "")
        row["reference"] = first_label.startswith("（参考）") or first_label.startswith("参照")
        if row["reference"] and "group" in row:
            row["group"] = None
        rows.append(row)
    # 機械用 id
    if name == "表3":
        for r in rows:
            b = match_id(BASES_3, r["basis_ja"])
            n = r["n_components"].get("value")
            r["id"] = f"{b}_m{n}" if b and n is not None else None
            r["basis_id"] = b
    elif name == "表7a":
        for r in rows:
            t, mth = match_id(TYPES, r["type_ja"]), match_id(METHODS_7A, r["method_ja"])
            r["type_id"], r["method_id"] = t, mth
            r["id"] = f"{t}_{mth}" if t and mth else None
    else:
        for r in rows:
            r["id"] = match_id(spec["ids"], r["label_ja"])
    seen = set()
    for r in rows:
        if r["id"] is None:
            issues.append({"table": name, "line": r["line"], "col": "id", "raw": r.get("label_ja", ""),
                           "problem": "機械用 id の規則に一致する行の見出しが無い"})
        elif not spec.get("multi") and r["id"] in seen:
            issues.append({"table": name, "line": r["line"], "col": "id", "raw": r.get("label_ja", ""),
                           "problem": f"id が重複した: {r['id']}"})
        seen.add(r["id"])
    return {"rows": rows, "groups": groups}


def post_6c(table: dict) -> None:
    table["noise_levels"] = NOISE_LEVELS
    methods: dict = {}
    for r in table["rows"]:
        r["stage"] = r["stage"]["stage"] if isinstance(r["stage"], dict) else r["stage"]
        for base in ("dt_pwv", "ri_pvr"):
            r[base] = {lvl: r.pop(f"{base}_{suffix}") for lvl, suffix in zip(NOISE_LEVELS, ("0", "001", "002"))}
        tr = r.pop("pass_rate")
        vals = tr.get("values")
        r["pass_rate"] = None if vals is None else {"raw": tr["raw"], **{lvl: v for lvl, v in zip(NOISE_LEVELS, vals)}}
        if r["pass_rate"] is not None and r["id"]:
            methods[r["id"]] = {"label_ja": r["label_ja"], "pass_rate": r["pass_rate"]}
    table["methods"] = methods


def parse_document(path: Path = SRC) -> dict:
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()
    n = len(lines)
    issues: list[dict] = []

    headings = [(i, len(m.group(1)), m.group(2)) for i, ln in enumerate(lines, 1) if (m := HEADING_RE.match(ln))]

    # 表のブロック（`|` で始まる連続行で、2 行目が区切り行）
    blocks = []
    i = 1
    while i <= n:
        if lines[i - 1].lstrip().startswith("|") and i < n and SEP_RE.match(lines[i]):
            j = i
            while j + 1 <= n and lines[j].lstrip().startswith("|"):
                j += 1
            blocks.append((i, j))
            i = j + 1
        else:
            i += 1

    def heading_before(line):
        h = [x for x in headings if x[0] < line]
        return h[-1] if h else None

    def next_heading_line(line, max_level=6):
        for ln, lv, _ in headings:
            if ln > line and lv <= max_level:
                return ln
        return n + 1

    def name_of(title):
        m = re.match(r"(表\d+[a-z]?)", title)
        return m.group(1) if m else title.split("（")[0].strip()

    all_paras = paragraphs(lines, 1, n)
    src_paras = []
    for p in all_paras:
        t = flat(p["text"])
        if t.startswith("出典"):
            m = re.match(r"出典（(.+?)）", t)
            scope = [x.strip().replace(" とも", "").replace("とも", "") for x in m.group(1).split("・")] if m else None
            src_paras.append({**p, "flat": t, "scope": scope})

    # 文書の冒頭（出どころの文）
    head = all_paras[1] if len(all_paras) > 1 else all_paras[0]
    doc_sources = None
    hs = flat(head["text"])
    k = hs.find("出どころは")
    if k >= 0:
        doc_sources = first_sentence(hs[k:])
    segments = re.findall(r"[^（）、]+?（[^）]*）", doc_sources or "")

    tables: dict[str, dict] = {}
    for (b, e) in blocks:
        h = heading_before(b)
        if h is None:
            issues.append({"table": None, "line": b, "col": None, "raw": lines[b - 1], "problem": "見出しの無い表"})
            continue
        h_line, h_level, h_title = h
        name = name_of(h_title)
        parent = None
        if h_level >= 3:
            ph = [x for x in headings if x[0] < h_line and x[1] == 2]
            parent = name_of(ph[-1][2]) if ph else None
        key = name if name.startswith("表") else f"{parent}_{name}"
        if key not in SPEC:
            issues.append({"table": key, "line": b, "col": None, "raw": h_title, "problem": "仕様に無い表"})
            continue
        spec = SPEC[key]
        own_end = next_heading_line(h_line) - 1
        sec_start = h_line
        if parent is not None:
            sec_start = [x for x in headings if x[0] < h_line and x[1] == 2][-1][0]
        sec_end = next_heading_line(sec_start, 2) - 1

        header = split_row(lines[b - 1])
        body = [(ln, split_row(lines[ln - 1])) for ln in range(b + 2, e + 1)]
        built = build_rows(key, spec, header, body, issues)

        # 出典: 明示の範囲 → 自分の節 → 上位の節 → 文書の冒頭
        src, src_kind = None, None
        base_name = re.match(r"表\d+", name).group(0) if name.startswith("表") else parent
        for sp in src_paras:
            if sp["scope"] and name in sp["scope"]:
                src, src_kind = sp, "出典（明示）"
                break
        if src is None:
            for sp in src_paras:
                if h_line <= sp["line_start"] <= own_end:
                    src, src_kind = sp, "出典（同じ節）"
                    break
        if src is None:
            for sp in src_paras:
                if sec_start <= sp["line_start"] <= sec_end and not sp["scope"]:
                    src, src_kind = sp, "出典（上位の節）"
                    break
        if src is not None:
            source = {"source": first_sentence(src["flat"]), "source_kind": src_kind,
                      "source_lines": [src["line_start"], src["line_end"]], "source_paragraph": src["flat"]}
        else:
            segs = [s.lstrip("出どころは、・ ").strip() for s in segments
                    if any(x.strip() in (name, base_name) for x in re.sub(r" の更新と", "・", re.search(r"（(.*)）", s).group(1)).split("・"))]
            source = {"source": doc_sources, "source_kind": "文書の冒頭（出どころ）",
                      "source_lines": [head["line_start"], head["line_end"]], "source_segments": segs}
            if not segs:
                issues.append({"table": key, "line": h_line, "col": None, "raw": h_title, "problem": "出典が見つからない"})

        pre = paragraphs(lines, h_line + 1, b - 1)
        post = paragraphs(lines, e + 1, own_end)
        title_stage = re.search(r"([ABC]) 段", h_title)
        columns = []
        for ck, kd, hraw in zip(spec["keys"], spec["kinds"], header + [""] * (len(spec["keys"]) - len(header))):
            ht = header_text(hraw)
            st = re.search(r"([ABC]) 段", ht)
            columns.append({"key": ck, "kind": kd, "header_ja": ht, "header_raw": hraw, "stage": st.group(1) if st else None})
        post_hoc = ("探索" in h_title) or any("判定には用いない" in flat(p["text"]) for p in pre)
        table = {
            "name": name, "key": key, "title": h_title, "heading_level": h_level, "heading_line": h_line,
            "parent": parent, "table_lines": [b, e], "stage": title_stage.group(1) if title_stage else None,
            "post_hoc": post_hoc, **source,
            "columns": columns,
            "preamble": [p["text"] for p in pre], "postscript": [p["text"] for p in post],
            "groups": built["groups"], "row_count": len(built["rows"]), "rows": built["rows"],
        }
        if key == "表6c":
            post_6c(table)
        if key == "表6d":
            for r in table["rows"]:
                r["stage"] = r["stage"]["stage"] if isinstance(r["stage"], dict) else r["stage"]
        tables[key] = table

    for key, t in tables.items():
        if not t["post_hoc"] and t["parent"] and t["parent"] in tables:
            t["post_hoc"] = tables[t["parent"]]["post_hoc"]
    for key in EXPECTED_TABLES:
        if key not in tables:
            issues.append({"table": key, "line": None, "col": None, "raw": "", "problem": "表が見つからない"})

    # 表を持たない節（表7 の前書き・表4 の記述）
    sections = {}
    with_table = {t["heading_line"] for t in tables.values()}
    for ln, lv, title in headings:
        if lv < 2 or ln in with_table:
            continue
        name = name_of(title)
        parent = None
        if lv >= 3:
            ph = [x for x in headings if x[0] < ln and x[1] == 2]
            parent = name_of(ph[-1][2]) if ph else None
        key = name if name.startswith("表") else f"{parent}_{name}"
        paras = paragraphs(lines, ln + 1, next_heading_line(ln) - 1)
        sections[key] = {"title": title, "heading_level": lv, "heading_line": ln, "parent": parent,
                         "post_hoc": "探索" in title or any("判定には用いない" in flat(p["text"]) for p in paras),
                         "paragraphs": [p["text"] for p in paras]}
    for key, t in tables.items():
        if not t["post_hoc"] and t["parent"] in sections:
            t["post_hoc"] = sections[t["parent"]]["post_hoc"]

    # 規準・段の定義
    crit_line = next((i for i, ln in enumerate(lines, 1) if CRITERION_RE.search(ln)), None)
    if crit_line is None:
        issues.append({"table": None, "line": None, "col": None, "raw": "", "problem": "凍結した判定規準の文が見つからない"})
    sign = next((SIGN_RE.search(ln).group(0) for ln in lines if SIGN_RE.search(ln)), None)
    bold_rule = next((BOLD_RULE_RE.search(flat(p["text"])).group(1) for p in all_paras if BOLD_RULE_RE.search(flat(p["text"]))), None)
    occ = extract_stage_defs(all_paras)
    stage_defs = {}
    for letter in "ABC":
        first = next((o for o in occ if o["stage"] == letter), None)
        stage_defs[letter] = None if first is None else {"text": first["text"], "line": first["line"]}
        if first is None:
            issues.append({"table": None, "line": None, "col": None, "raw": "", "problem": f"{letter} 段の定義が見つからない"})
    m_n = re.search(r"(\d[\d,]*)名", tables["表1"]["title"]) if "表1" in tables else None

    doc = {
        "meta": {
            "source_md": SRC.relative_to(ROOT).as_posix(),
            "generated_by": Path(__file__).resolve().relative_to(ROOT).as_posix(),
            "document_title": lines[0].lstrip("# ").strip(),
            "document_header": flat(head["text"]),
            "document_sources": doc_sources,
            "n_subjects_decision_test": to_int(m_n.group(1)) if m_n else None,
            "criterion": {
                "text": CRITERION_RE.pattern.replace("\\", ""),
                "line": crit_line,
                "min_median_abs_rho": 0.30,
                "strata_required": 6,
                "sign_prediction": sign,
                "bold_rule": bold_rule,
            },
            "stage_definitions": {**stage_defs, "occurrences": occ},
            "table_order": list(tables),
        },
        "tables": tables,
        "sections": sections,
        "issues": issues,
    }
    return doc


def dumps(doc: dict) -> str:
    return json.dumps(doc, ensure_ascii=False, indent=2, allow_nan=False) + "\n"


# ---------------------------------------------------------------------------
# 自己検査
# ---------------------------------------------------------------------------

def row(doc: dict, table: str, rid: str, **match):
    for r in doc["tables"][table]["rows"]:
        if r["id"] == rid and all(r.get(k) == v for k, v in match.items()):
            return r
    raise KeyError(f"{table} に id={rid} {match} の行が無い")


def selftest(doc: dict) -> int:
    T = doc["tables"]
    checks = [
        ("表1 凍結版 ΔT", lambda: (row(doc, "表1", "pda_frozen")["dt_pwv"]["rho"], row(doc, "表1", "pda_frozen")["dt_pwv"]["strata"]), (0.223, "6/6")),
        ("表1 凍結版 RI・判定", lambda: (row(doc, "表1", "pda_frozen")["ri_pvr"]["rho"], row(doc, "表1", "pda_frozen")["ri_pvr"]["strata"], row(doc, "表1", "pda_frozen")["verdict"]["verdict"]), (0.207, "5/6", "不成立")),
        ("表1 特徴点法 ΔT（太字・成立）", lambda: (row(doc, "表1", "landmark")["dt_pwv"]["rho"], row(doc, "表1", "landmark")["dt_pwv"]["bold"], row(doc, "表1", "landmark")["verdict"]["verdict"]), (0.710, True, "成立")),
        ("表1 第2版 歪みガウス（段ごと）", lambda: (row(doc, "表1", "pda_v2_skewgauss")["dt_pwv"]["adopted"], row(doc, "表1", "pda_v2_skewgauss")["dt_pwv"]["stages"]["C"]["rho"], row(doc, "表1", "pda_v2_skewgauss")["dt_pwv"]["stages"]["A"]["rho"]), ({"n": 2, "of": 4374}, 0.167, None)),
        ("表1 第2版 ガンマ RI A 段", lambda: (row(doc, "表1", "pda_v2_gamma")["ri_pvr"]["stages"]["A"]["rho"], row(doc, "表1", "pda_v2_gamma")["ri_pvr"]["stages"]["A"]["strata"]), (0.609, "4/4")),
        ("表2 心拍数 分解法 ΔT", lambda: (row(doc, "表2", "heart_rate")["pda_dt"]["effect_pct"], row(doc, "表2", "heart_rate")["pda_dt"]["rho"], row(doc, "表2", "pwv")["landmark_dt"]["effect_pct"]), (-10.9, -0.54, -31.2)),
        ("表2b 脈波伝播速度", lambda: (row(doc, "表2b", "pwv")["dt_minus1sd"]["value"], row(doc, "表2b", "pwv")["ri_plus1sd"]["value"]), (332.3, 0.647)),
        ("表2c 起始部→指尖", lambda: (row(doc, "表2c", "aorta_to_finger")["median"]["value"], row(doc, "表2c", "aorta_to_finger")["p5_p95"]["lo"], row(doc, "表2c", "aorta_to_finger")["p5_p95"]["hi"]), (96.0, 66.0, 120.0)),
        ("表3 ガウス 2 成分", lambda: (row(doc, "表3", "gauss_m2")["dt_pwv"]["rho"], row(doc, "表3", "gauss_m2")["dt_pwv"]["strata"], row(doc, "表3", "gauss_m2")["nrmse_median"]["value"], row(doc, "表3", "gauss_m2")["boundary_fraction"]["value"]), (0.54, "4/4", 0.0491, 4.0)),
        ("表3 ガンマ 3 成分（同 の解決）", lambda: (row(doc, "表3", "gamma_frozen_m3")["wang_pass"]["value"], row(doc, "表3", "gamma_wide_m4")["label_ja"], row(doc, "表3", "gamma_wide_m4")["basis_ja"]), (15.3, "同", "ガンマ（広い探索範囲）")),
        ("表4 Couceiro RI（R1_d）", lambda: (row(doc, "表4", "couceiro2015")["ri_pvr"]["rho"], row(doc, "表4", "couceiro2015")["ri_pvr"]["prefix"], row(doc, "表4", "tigges2017")["dt_pwv"]["rho"], row(doc, "表4", "landmark_ref")["dt_pwv"]["rho"]), (0.585, "R1_d", 0.578, 0.705)),
        ("表4 逸脱表", lambda: (T["表4_逸脱表"]["row_count"], "Kaiser" in row(doc, "表4_逸脱表", "tigges2017")["deviation_ja"]["text"]), (5, True)),
        ("表5 型3・型4", lambda: (row(doc, "表5", "type3")["amp_ratio_C"]["rho"], row(doc, "表5", "type3")["landmark_dt_C"]["rho"], row(doc, "表5", "type4")["n"], row(doc, "表5", "type4")["strata_count"], row(doc, "表5", "all")["n"]), (0.815, 0.430, 105, 3, 4374)),
        ("表5b 型1", lambda: (row(doc, "表5b", "type1")["pwv_iqr_width_m_s"]["value"], row(doc, "表5b", "type1")["pvr_iqr_width"]["value"], row(doc, "表5b", "type1")["strata_ge8"]["num"], row(doc, "表5b", "type1")["min_stratum_n"]["value"], row(doc, "表5b", "ratio_type1_type3")["pwv_iqr_width_m_s"]["value"]), (0.114, 3.71e7, 6, 53, 0.080)),
        ("表6 0.65 倍の打ち切り", lambda: (row(doc, "表6", "trunc065")["dt_pwv_C"]["rho"], row(doc, "表6", "trunc065")["dt_pwv_C"]["strata"], row(doc, "表6", "trunc065")["pass_rate"]["value"], row(doc, "表6", "trunc065")["dt_offset_vs_landmark_ms_A"]["value"]), (0.596, "6/6", 0.413, 25.8)),
        ("表6 凍結版・特徴点法・群", lambda: (row(doc, "表6", "fb")["dt_offset_vs_landmark_ms_A"]["value"], row(doc, "表6", "landmark")["dt_offset_vs_landmark_ms_A"]["value"], row(doc, "表6", "twostage")["group"], row(doc, "表6", "deriv")["group"], row(doc, "表6", "landmark")["group"], row(doc, "表6", "landmark")["reference"], T["表6"]["row_count"]), (98.5, 0.0, "下降を説明する項を足す", "下降を当てはめの対象から外す・残差の中で小さくする", None, True, 13)),
        ("表6b 貯留槽の項", lambda: (row(doc, "表6b", "reservoir")["boundary_fraction"]["value"], [(x["param"], x["bound"], x["fraction"], x["bold"]) for x in row(doc, "表6b", "reservoir")["breakdown"]["items"]], [(x["param"], x["parenthetical"]) for x in row(doc, "表6b", "conv")["breakdown"]["items"]]), (0.903, [("g", "hi", 0.61, True), ("τ", "lo", 0.21, True)], [("α1", False), ("μ1", False), ("τ", True)])),
        ("表6c 1 次微分 C 段 雑音 2%", lambda: (row(doc, "表6c", "deriv", stage="C")["dt_pwv"]["0.02"]["rho"], row(doc, "表6c", "deriv", stage="C")["dt_pwv"]["0"]["rho"]), (0.347, 0.687)),
        ("表6c 凍結版 通過率", lambda: ({k: row(doc, "表6c", "fb", stage="A")["pass_rate"][k] for k in NOISE_LEVELS}, row(doc, "表6c", "fb", stage="B")["pass_rate"]), ({"0": 0.901, "0.01": 0.881, "0.02": 0.862}, None)),
        ("表6c 特徴点法（同左）", lambda: (row(doc, "表6c", "landmark", stage="C")["dt_pwv"]["0.01"]["rho"], row(doc, "表6c", "landmark", stage="C")["ri_pvr"]["0.02"]["same_as_left"], row(doc, "表6c", "trunc065", stage="B")["ri_pvr"]["0.01"]["rho"], row(doc, "表6c", "trunc065", stage="B")["ri_pvr"]["0.01"]["bold"], T["表6c"]["row_count"]), (0.430, True, 0.266, False, 11)),
        ("表6d 全例・型1（打ち切りと特徴点法）", lambda: (row(doc, "表6d", "dt_trunc065_dmu001", stage="C")["all"]["rho"], row(doc, "表6d", "dt_trunc065_dmu001", stage="C")["all"]["strata"], row(doc, "表6d", "dt_trunc065_dmu001", stage="A")["type1"]["rho"], row(doc, "表6d", "dt_landmark", stage="C")["all"]["rho"], row(doc, "表6d", "dt_fb", stage="C")["type1"].get("rho"), row(doc, "表6d", "ri_deriv", stage="C")["all"]["rho"], T["表6d"]["row_count"]), (0.559, "6/6", 0.193, 0.710, None, 0.394, 8)),
        ("表6e C6・C7b・C8", lambda: ("−0.542" in row(doc, "表6e", "c6")["deriv"]["text"], row(doc, "表6e", "c6")["fb"]["text"], "−0.489" in row(doc, "表6e", "c7b")["trunc065"]["text"], "−3.9%" in row(doc, "表6e", "c8_dt")["deriv"]["text"], T["表6e"]["row_count"]), (True, "−0.124", True, True, 5)),
        ("表7a 型3 特徴点法", lambda: (row(doc, "表7a", "type3_landmark")["n"]["value"], row(doc, "表7a", "type3_landmark")["dt_diff_ms"]["value"], row(doc, "表7a", "type3_landmark")["rho_pooled"]["value"], row(doc, "表7a", "type1_pda_ppg")["dt_diff_ms"]["value"]), (2758, 114.0, -0.022, 257.8)),
        ("表7b 圧波形 ΔT A 段", lambda: (row(doc, "表7b", "pressure")["dt_pwv_A"]["rho"], row(doc, "表7b", "pressure")["dt_pwv_A"]["strata"], row(doc, "表7b", "pressure")["dt_pwv_A"]["bold"], row(doc, "表7b", "pressure")["adoption_rate"]["value"], row(doc, "表7b", "ppg")["adoption_rate"]["value"]), (0.486, "6/6", True, 84.5, 92.3)),
        ("規準の文", lambda: doc["meta"]["criterion"]["text"], "全6層で予測の符号を持ち、かつ中央値 |ρ| ≥ 0.30"),
        ("段の定義", lambda: tuple(bool(doc["meta"]["stage_definitions"][k]) for k in "ABC") + ("732" in doc["meta"]["stage_definitions"]["B"]["text"],), (True, True, True, True)),
        ("出典（表6 は 表6b の出典を共有）", lambda: (T["表6"]["source_kind"], T["表6"]["source"] == T["表6b"]["source"], "50_reservoir_bench" in T["表6"]["source"], T["表7a"]["source_kind"], "51_pwdb_wave_separation" in T["表7a"]["source"], T["表1"]["source_kind"]), ("出典（明示）", True, True, "出典（上位の節）", True, "文書の冒頭（出どころ）")),
        ("全 14 表", lambda: sorted(T), sorted(EXPECTED_TABLES)),
        ("読めなかったセル", lambda: doc["issues"], []),
        ("決定性（2 回読んで同じ）", lambda: dumps(parse_document()) == dumps(doc), True),
    ]
    if OUT.exists():
        checks.append(("決定性（書いてある JSON と同じ）", lambda: OUT.read_text(encoding="utf-8") == dumps(doc), True))
    fails = 0
    for label, fn, want in checks:
        try:
            got = fn()
        except Exception as e:
            got = f"<{type(e).__name__}: {e}>"
        ok = got == want
        fails += 0 if ok else 1
        print(f"{'ok ' if ok else 'NG '} {label}" + ("" if ok else f"\n     得た値 {got!r}\n     期待値 {want!r}"))
    print(f"selftest: {len(checks) - fails}/{len(checks)} 通過")
    return 0 if fails == 0 else 1


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--selftest", action="store_true", help="既知の値と照合して終わる（書かない）")
    ap.add_argument("--out", type=Path, default=OUT, help="書き先（既定は data/paper2_numbers.json）")
    a = ap.parse_args()
    doc = parse_document()
    if a.selftest:
        return selftest(doc)
    a.out.parent.mkdir(parents=True, exist_ok=True)
    a.out.write_text(dumps(doc), encoding="utf-8")
    print(f"書いた: {a.out}")
    for key in doc["meta"]["table_order"]:
        print(f"  {key}: {doc['tables'][key]['row_count']} 行")
    if doc["issues"]:
        print(f"読めなかったセル {len(doc['issues'])} 件:")
        for it in doc["issues"]:
            print(f"  {it}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
