# 論文1 表2〜表7（投稿体裁）― Results 本文から組み上げた

**作成 2026-09-07。**表1（患者背景）と表6（感度解析・再抽出系）は `01_draft_en.md` 本文に既にある。
本ファイルはそこから欠けていた表2〜表5 を組み、2026-09-07 に追加した探索的解析の表7 を加えたものである。
数値はすべて `01_draft_en.md` の Results と `docs/research/lab_log.md` から取った。

`[[ ]]` は本文に数値が無く、解析出力から読み直して埋める箇所である。

---

## Table 2. Premise test: within-case variation of PWTT explained by the vascular indices

Dependent variable is ΔPWTT% (relative change from the case's first window). 862 cases,
161,737 windows. The prespecified estimate is fitted through the origin because every
relative change is zero at calibration; the estimate with an intercept is reported as an
exploratory sensitivity analysis.

| Model | r² | β per ΔSI% (95% CI) | β per ΔRI% (95% CI) |
|---|---|---|---|
| **Prespecified, through the origin** | **0.000** | **−0.027 (−0.033 to −0.021)** | **−0.003 (−0.004 to −0.001)** |
| With an intercept (exploratory) | 0.044 | −0.022 (−0.027 to −0.016) | −0.001 (−0.002 to −0.000) |
| ΔSI% only, through the origin | 0.041 | −0.022 | — |
| ΔSI% + ΔRI% + ΔHR% (exploratory) | 0.077 | −0.020 | −0.003 (β ΔHR% −0.057) |
| ΔMAP% only (exploratory, for comparison) | 0.139 | — | — |

| Within-case diagnostics | Value |
|---|---|
| Median within-case r² | 0.101 |
| Cases with the predicted sign on ΔSI% | 78% |
| Effect size | a 10% change in the stiffness index predicts a 0.27% change in PWTT |

> Confidence intervals are from a case-level bootstrap with 2,000 resamples and seed 0 —
> the resampling scheme used for ΔPE in Table 4 — computed by
> `analysis/scripts/41_fill_tables.py` on the machine and feature cache of the confirmatory
> run (`docs/research/results/41_fill_tables_mac1.txt`, 2026-09-12, 161,737 windows). The
> script checks that the point estimates reproduce `premise_test` and
> `premise_with_intercept` exactly before reporting the intervals.
> They are given for the two rows the script recomputes; the remaining rows come from
> `09_extra_sensitivity.py` and carry no interval here.
>
> **The intervals exclude zero, and that is the point of the table rather than a caveat
> to it.** With 862 cases and 161,737 windows the coefficients are estimated precisely;
> what they show is that the effect, while distinguishable from zero, is about two orders
> of magnitude too small to serve as a correction input. A 10% change in the stiffness
> index moves PWTT by 0.27%.
>
> At four decimals the upper bound of β per ΔRI% in the intercept model is −0.0002
> (`41_fill_tables_mac1.txt`); it is printed as −0.000 at three decimals. All four
> intervals exclude zero.

---

## Table 3. Measurement quality

| Quantity | Value |
|---|---|
| Windows examined | 232,451 |
| Windows passing all quality gates | 70% |
| — rejected: ensemble noise target not reached | 12% |
| — rejected: reference CO missing | 6% |
| — rejected: arterial pressure missing | 4% |
| — rejected: fewer than two accepted decompositions | 3% |
| — rejected: too few quality-passing beats | 2% |
| Fitted segments | 2,692,082 |
| Segments passing all convergence checks | 72% |
| — rejected: a parameter at its bound | 22% |
| — rejected: a competing solution | 8% |
| — rejected: component collapse | < 0.1% |

Categories of rejection overlap.

| Lag-1 autocorrelation between consecutive windows | Value |
|---|---|
| PWTT | +0.75 |
| ΔT-based index | +0.50 |
| RI | +0.43 |
| Am_b/Am_p1 (2026-09-07 exploratory analysis) | +0.394 |
| Mean arterial pressure (2026-09-07 exploratory analysis) | +0.695 |

| Exploratory positive and negative controls (849 adults) | Value |
|---|---|
| ΔT versus age | ρ = −0.197 (95% CI −0.261 to −0.131), p < 0.0001 |
| ΔT, hypertensive versus not | median 259 versus 267 ms |
| RI versus age | ρ = +0.041, p = 0.23 — judged uninterpretable in this signal source |
| Negative control: case identifier versus ΔT | ρ = +0.078 (95% CI +0.011 to +0.145) |
| — after adjustment for age, heart rate, mean pressure, device | ρ = +0.072 |
| — variance carried, against the age association | 0.6% versus 3.9% |

---

## Table 4. Secondary analysis: agreement with the reference cardiac output

Cross-validated at case level; the reference is arterial-waveform-derived in 846 of 862
cases, so under the prespecified interpretation rules (§2.8) these rows carry no
interpretive weight on their own.

| Estimator | Percentage error | Difference against control |
|---|---|---|
| Control (PWTT only) | 26.9% | — |
| **Proposed (vascular correction)** | **27.2%** | **+0.2 points (95% CI +0.1 to +0.4)** |
| Control + mean arterial pressure | 27.0% | +0.3 points (95% CI +0.2 to +0.5) |
| Control + vascular indices + mean arterial pressure | 27.1% | +0.3 points (95% CI +0.1 to +0.5) |

| Bland–Altman and trending, corrected estimator | Value |
|---|---|
| Bias | −0.07 L/min |
| Limits of agreement | −3.28 to +3.14 L/min |
| Four-quadrant concordance (0.5 L/min exclusion zone) | 0.56 |

The prespecified futility criterion was met.

---

## Table 5. Sensitivity analyses not requiring re-extraction

Table 6 (in the main text) covers the nine variants that required re-extraction.

| Analysis | Cases | Windows | Premise r² | β ΔSI% | Sign consistency | ΔPE, points (95% CI) |
|---|---|---|---|---|---|---|
| Primary analysis | 862 | 161,737 | 0.000 | −0.027 | 78% | +0.2 (+0.1 to +0.4) |
| Excluding the 15 pipeline-development cases | 847 | 158,445 | 0.005 | −0.028 | 78% | +0.2 (+0.1 to +0.3) |
| Windows aggregated to 5 minutes | 844 | 31,934 | — | — | — | 0.0 (−0.2 to +0.1) |
| Windows aggregated to 20 minutes | 606 | 6,838 | — | — | — | −0.2 (−0.5 to +0.0) |
| Heart rate added to the premise regression | 862 | 161,737 | 0.077 | −0.020 | 74% | — |

Percentage error for the control estimator fell with aggregation (26.9% at 60 s, 24.0% at
5 min, 21.8% at 20 min), as expected when comparing monitors of differing response time;
the correction improved accuracy at no level.

> **照合済み（2026-09-11、lab_log 追記101）。**以前この表の 5 分・20 分の行は、症例をファイル名順に並べる
> 別プログラム（09番）の出力から採っており、主解析（対象症例一覧の行順）と 5-fold の割り付けが違っていた。
> 60 秒の行が 27.1%・+0.1〜+0.3 と 0.1 ポイントずれていたのはそのためである。並びを主解析にそろえて
> 3 行を同じ計算から採り直した（41番・09番）。60 秒の行は主解析の確定値（27.2%、+0.1〜+0.4）に一致する。
> ウィンドウ数と区間は確定解析の機械で回した 41番の値（`41_fill_tables_mac1.txt`、追記111）。

| Reference independent of the arterial pressure waveform (descriptive only) | Value |
|---|---|
| Cases | 16 (CardioQ 11, Vigilance II 5) |
| Percentage error, control / proposed | 41.0% / 41.6% |
| Direction of the difference | Correction worse by 0.6 points (descriptive only, no test) |
The 16 cases are taken from the validation folds of the primary case-level cross-validation (models fitted on the derivation folds); no model was refitted on these cases alone.

---

## Table 7. Premise test repeated with a construct-valid, identifiable index (exploratory, added 2026-09-07)

Design frozen before the analysis was run (`docs/research/sap_1_amb_exploratory_v0.md`).
All four rows are computed on the same windows. Source:
`docs/research/results/36_amb_premise_report.txt`.

| Explanatory variables (dependent: ΔPWTT%) | Windows | r² through origin | r² with intercept | Coefficients |
|---|---|---|---|---|
| **ΔAm% (upstroke amplitude ratio)** | 161,638 | −0.105 | **0.0002** | −0.030 |
| ΔAm% + ΔMAP% | 161,638 | 0.094 | 0.141 | −0.084 / −0.078 |
| ΔSI% + ΔRI% (main analysis, recomputed) | 161,638 | 0.000 | 0.044 | −0.027 / −0.003 |
| ΔMAP% only | 161,638 | 0.088 | 0.139 | −0.076 |

The third and fourth rows reproduce the confirmatory run (0.044/0.000 and 0.139), which
serves as an internal control on the recomputation.

| Within-case diagnostics | ΔAm% | ΔSI% | ΔRI% | ΔMAP% |
|---|---|---|---|---|
| Cases with the predicted sign | 51% | 80% | 74% | 89% |
| Median within-case r² | 0.027 | 0.051 | 0.041 | 0.110 |
| Median within-case rank correlation | −0.003 | −0.216 | −0.131 | −0.363 |

862 cases; 161,638 of 161,737 windows (0.1% loss). Under the prespecified reading
(r² < 0.05), changing the index does not make within-case PWTT variation explicable.
