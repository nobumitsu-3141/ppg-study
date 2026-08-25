# -*- coding: utf-8 -*-
"""合成コホート生成（ウィンドウレベル）― モデル・統計・交差検証の機構検証用。

波形→PDA→SI・RI の層は tests/test_pda_synthetic.py で検証済みなので、
ここでは1分ウィンドウに集約された特徴量 {PWTT, SI, RI, HR, CO_ref} を直接生成する。

生成モデル（スライド6.1〜6.3の構造をそのまま数式化）:
  - 真のSVが時間変動し、血管状態 vasc(t)（SVR・スティフネスの合成因子）も独立に変動する
  - PWTT = a_i − b・(SV/SV0) + c・vasc + ノイズ
      c≠0 が「PWTTに血管側が混入する」= esCCO誤差の源（effectコホート）
      c=0 なら補正の余地なし（nullコホート: 偽陽性の検出用）
  - SI・RI は vasc を反映（+測定ノイズ）
  - CO_ref = SV×HR に参照法の測定誤差（約7%）を乗せる
"""
from __future__ import annotations

import numpy as np


def make_cohort(n_cases: int = 60, n_windows: int = 30, effect: bool = True,
                seed: int = 0) -> list[dict]:
    """症例のリストを返す。各症例: dict(caseid, height, windows=dict of arrays, truth)."""
    rng = np.random.default_rng(seed)
    c_vasc = 0.025 if effect else 0.0   # PWTTへの血管状態の混入係数 [s]（SV由来の変化と同程度）
    cases = []
    for i in range(n_cases):
        height = rng.uniform(1.50, 1.85)
        sv0 = rng.uniform(45, 95)                       # baseline SV [mL]
        pwtt0 = rng.uniform(0.18, 0.30)                 # baseline PWTT [s]
        si0 = rng.uniform(6.0, 11.0)
        ri0 = rng.uniform(0.35, 0.75)
        t = np.arange(n_windows)
        # SV: ゆっくり±25%変動 + イベント（出血/輸液様のステップ）
        sv = sv0 * (1 + 0.22 * np.sin(2 * np.pi * t / rng.uniform(18, 40) + rng.uniform(0, 6))
                    + 0.07 * rng.standard_normal(n_windows).cumsum() / np.sqrt(n_windows))
        sv = np.clip(sv, 0.5 * sv0, 1.6 * sv0)
        # 血管状態: SVとは独立に変動（昇圧薬・麻酔深度などを想定）
        vasc = (0.8 * np.sin(2 * np.pi * t / rng.uniform(12, 30) + rng.uniform(0, 6))
                + 0.5 * rng.standard_normal(n_windows).cumsum() / np.sqrt(n_windows))
        hr = np.clip(70 + 12 * rng.standard_normal(n_windows).cumsum() / np.sqrt(n_windows), 45, 110)

        pwtt = (pwtt0 - 0.055 * (sv / sv0 - 1) + c_vasc * vasc
                + 0.003 * rng.standard_normal(n_windows))
        si = si0 + 1.1 * vasc + 0.25 * rng.standard_normal(n_windows)
        ri = np.clip(ri0 + 0.09 * vasc + 0.025 * rng.standard_normal(n_windows), 0.05, 1.5)
        co_ref = sv * hr / 1000.0 * (1 + 0.07 * rng.standard_normal(n_windows))  # [L/min]

        cases.append({
            "caseid": i, "height": height,
            "windows": {"pwtt": pwtt, "si": si, "ri": ri, "hr": hr, "co_ref": co_ref},
            "truth": {"sv": sv, "vasc": vasc, "effect": effect},
        })
    return cases
