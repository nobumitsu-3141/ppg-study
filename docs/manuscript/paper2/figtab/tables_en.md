# Paper 2: tables (English)

All numbers are read by `build_tables.py` from `data/paper2_numbers.json` (a mechanical parse of `../02_tables.md` by `data/extract_tables.py`); none is typed by hand. Verdicts (pass/fail) are those of `docs/research/roadmap_v1.md` §9 and are not changed. Tables 4 onward are exploratory, post hoc descriptions made after the prespecified decision and are not used for it. Every table that shows tiers A/B/C carries the tier note as a footnote. Footnote letters (a, b, …) are attached to the caption or to column headers.

## Table 1

**Table 1.** Prespecified analysis items: rule, date frozen, result, verdict and source<sup>a</sup>. Criterion frozen before the run: within-stratum Spearman ρ with the predicted sign in all 6 strata and median |ρ| ≥ 0.30.

| Item | Role | Rule (date frozen) | Result | Verdict<sup>b</sup> | Source |
|---|---|---|---|---|---|
| Frozen decomposition (two skew-Gaussian components): ΔT × aortic PWV (Q1), RI × peripheral vascular resistance (Q2) | Primary questions Q1 and Q2 (table 2, row 1) | Within-stratum (six strata) Spearman ρ with the predicted sign in every stratum (ΔT negative, RI positive) and median \|ρ\| ≥ 0.3; strata of at least 8 subjects; pooled correlations are reference values only [frozen 2026-09-03 (before script 20 was run); the question itself on 2026-08-30 (roadmap §3, study 0)] | ΔT 0.223 (6/6); RI 0.207 (5/6) | fail | lab_log 2026-09-03 (prespecified criteria of study 0; results of study 0); roadmap §8, §9; reproduced in entry 12 |
| Rebuilt decomposition, skew-Gaussian route (primary route; src/pda2.py) | Primary question: was the failure of the frozen version an implementation problem? (table 2, row 2) | Definition of 'pass' 1–3: both questions pass in all three tiers A, B and C, without an asterisk; if script 27 splits the verdict, 'pass' is not written [frozen 2026-09-04 (gate0_rules_v2, pda2_thresholds_v2); pda2 version 048d2b43bb05 fixed on 2026-09-05] | ΔT: accepted 2/4,374; tiers A and B not evaluable; tier C 0.167. RI: tiers A and B not evaluable; tier C 0.354 (3/6) | fail (tiers A and B not evaluable; tier C fails). Decomposition is not adopted as a vascular index | gate0_rules_v2.md; pda2_final_summary.md §1–2; entry 12 §1–3; roadmap §9 |
| Rebuilt decomposition, gamma route (reported alongside) | Robustness check (table 2, row 3) | 'A pass of the gamma route alone is not written as a pass of PDA'; the proportion of parameters on a bound and the script-27 part-B (refitting) 'widen the search bounds' verdict are reported alongside [frozen 2026-09-04] | ΔT: accepted 103; tier A 0.798 (3/4 strata); tier C 0.556 (6/6). RI: tier A 0.609 (4/4); tier C 0.280 (6/6) | fail (the verdict splits across thresholds and conditions in script 27) | gate0_rules_v2.md; entries 12, 13 |
| Fiducial-point analysis (indices supplied with PWDB, same waveforms): ΔT, RI; secondary SI, AGI_mod, AI, ΔT × carotid–femoral PWV | Control: only the index construction differs (table 2, row 4) | Same criterion imported from script 20. Reading fixed before the run: 'fiducial-point analysis also fails → the failure is not specific to PDA'; 'only fiducial-point analysis passes → the failure is specific to PDA'; 'model-derived PTT not strongly negative → doubt the comparison itself' [frozen 2026-09-03 (before script 23 was run)] | ΔT 0.710 (6/6); RI 0.504 (6/6). Secondary: SI 0.710 and AGI_mod 0.885 pass, AI 0.143 fails | pass (AI alone fails). The failure is specific to decomposition; the full withdrawal was retracted | lab_log 2026-09-03 (control experiment; correction of the verdict); roadmap §8; reproduced in entry 12 |
| Early amplitude ratio Am_b/Am_p1 (Hellqvist 2024) × aortic PWV | Fourth method, exploratory (table 2, row 5) | 'If it passes and is at least equal to the median of fiducial-point ΔT (a difference within 0.05 counts as equal), the candidate primary index of study 2 switches to Am_b/Am_p1 and ΔT becomes secondary'; 'a 5–95% width below 0.05 is read as no discrimination' [frozen 2026-09-04] | 0.836 (6/6); against carotid–femoral PWV 0.758 (5/6), a fail | pass (fails against carotid–femoral PWV). Candidate primary index of study 2 switched to Am_b/Am_p1 | gate0_rules_v2.md; entry 12 §3-4 |
| Positive control: model-derived pulse transit time × aortic PWV | Check of the analysis pipeline (table 2, row 6) | 2026-09-03: if not strongly negative, doubt the comparison itself. 2026-09-04: the whole table is void unless median \|ρ\| ≥ 0.50 with every stratum negative [frozen 2026-09-03 (script 23); 2026-09-04 (quantified in gate0_rules_v2)] | 0.571 (6/6) | pass; the table is valid | lab_log 2026-09-03 (correction of the verdict); gate0_rules_v2.md; entries 11, 12 §0 |
| ΔT with p1 (Hellqvist's systolic peak) as the systolic reference | Exploratory (note to table 2) | 'If p1-based ΔT and our own fiducial-point ΔT differ greatly in type 3, replace the systolic reference of fiducial-point ΔT by p1' [frozen 2026-09-04] | 0.423 (5/6); in the same 4,269 subjects, below our own fiducial-point ΔT 0.536 | fail; p1 is not adopted (the rule's row does not apply) | gate0_rules_v2.md; entry 12 §3-5 |
| DPS (difference of component widths, Goswami 2010) | Descriptive | 'If the DPS of the rebuilt skew-Gaussian route is monotonic in the true value, add it as a secondary index of study 2 (sign not decided post hoc; reported as description)' [frozen 2026-09-04] | The primary (skew-Gaussian) route accepted 2 beats, so tier A is not evaluable; tier-C values are reported as description only | descriptive only (the rule presupposes an accepted decomposition, so it is not applied) | gate0_rules_v2.md; entry 12 §3-7 |
| Waveform-type distribution (script 26, table 2) and handling of types 3 and 4 | Condition for reading the verdict | 'If type 3 is frequent, the PDA verdict rests on type-1 beats and type 3 is read with fiducial points, p1 and the early amplitude ratio; report n of type 3 and the script-27 part-A "include type 3" verdict'; 'no ΔT-type index can be defined for type 4; report its n and discuss it with the early amplitude ratio only' [frozen 2026-09-04] | type 1 891 (20.4%); type 3 3,378 (77.2%); type 4 105 (2.4%) | read as the rule prescribes: the decomposition verdict rests on type-1 beats; type 3 read with fiducial points, p1 and the early amplitude ratio; type 4 with the early amplitude ratio only | gate0_rules_v2.md; entry 12 §1, §3-6 |
| Threshold sensitivity analysis (script 27): part A, acceptance recomputed without refitting; part B, refitted on a fixed subset of 624 subjects under 14 conditions | Check that the conclusion is not a product of the thresholds | 'If every threshold gives the same answer, the conclusion is not a product of the thresholds; if it splits, write the range and do not write pass'. The part-B subset is fixed to subj_no % 7 == 0 and is not re-chosen after seeing results [frozen 2026-09-04 (lab_log: thresholds frozen before the decision test)] | The skew-Gaussian route fails at every threshold; the gamma route splits in both part A and part B | reflected in the two rebuilt-version rows of table 2 | pda2_thresholds_v2.md; entry 12 §2 |
| Table 3: within-stratum main effect of each varied factor (descriptive) | Mechanism, descriptive | 'If the main factor moving ΔT is PWV and the main factor moving RI is MBP, the concept holds' [frozen 2026-09-03] | Decomposition ΔT: PWV −17.0 (−0.26), heart rate −10.9 (−0.54), aortic diameter −12.6 (−0.37)%. Fiducial-point ΔT: PWV −31.2, heart rate −2.6%. Decomposition RI: heart rate −40.3 (−0.37), PWV +33.7 (−0.17), mean arterial pressure +24.2 (−0.00)% | not as conceived: for decomposition ΔT the heart-rate effect is of the same order as that of pulse wave velocity, and the main factor of RI is not mean arterial pressure (MBP) | lab_log 2026-09-03 (results of study 0; correction of the verdict); entry 12; table 3 (02_tables table 2) |
| Table 3b: one-factor-at-a-time sweep (descriptive) | Mechanism, descriptive | As above (values of the subjects in which one factor alone is varied) [frozen 2026-09-03] | The PWV row reverses most: ΔT 332.3 → 352.8 → 251.2 ms, RI 0.325 → 0.254 → 0.647 | the response is not monotonic (the correspondence of the components exchanges) | lab_log 2026-09-03 (results of study 0); table 3b (02_tables table 2b) |
| Table 3c: true transit times from the model onset-time table (descriptive) | True values, descriptive | 'Compare the width of the true radial→finger transit time with the within-case SD of T2−T1 in VitalDB (≈18 ms)' [frozen 2026-09-03] | Aortic root→finger 96 ms (66–120 ms), radial→finger 8 ms (4–16 ms). ρ(aortic PWV, root→finger) −0.99 (6/6); ρ(decomposition ΔT, same) +0.19 (6/6) | the width of the true radial→finger transit time is narrower than the VitalDB within-case SD; decomposition ΔT barely tracks the true transit time | lab_log 2026-09-03 (results of study 0); table 3c (02_tables table 2c) |

<sup>a</sup> Rule texts from lab_log 2026-09-03 (prespecified criteria of study 0), `docs/research/gate0_rules_v2.md` (2026-09-04) and lab_log 2026-09-04 (thresholds frozen before the decision test). Verdicts are identical to `docs/research/roadmap_v1.md` §9. Result values are read from tables 1, 2, 2b and 2c of `02_tables.md` (`data/paper2_numbers.json`). 'Entry n' is a numbered addendum of lab_log. The random-beat invariants (script 28) are an implementation check, not an analysis item, and are omitted.

<sup>b</sup> Tier A, subjects accepted by the method itself; tier B, subjects accepted by every compared method; tier C, all subjects regardless of acceptance

## Table 2

**Table 2.** Median within-age-stratum Spearman rank correlation (decision test, 4,374 subjects, 6 strata)<sup>a</sup>. Criterion frozen before the run: predicted sign in all 6 strata and median |ρ| ≥ 0.30 (ΔT × aortic PWV negative, RI × peripheral vascular resistance positive). Magnitudes are shown; the number in parentheses is the number of strata with the predicted sign<sup>b</sup>.

| Index construction | ΔT × aortic PWV | RI × peripheral vascular resistance | Verdict |
|---|---|---|---|
| Decomposition, frozen version (two skew-Gaussian components) | 0.223 (6/6) | 0.207 (5/6) | fail |
| Decomposition, rebuilt version, skew-Gaussian route<sup>c</sup> | accepted 2/4,374; tiers A and B not evaluable; tier C 0.167 | tiers A and B not evaluable; tier C 0.354 (3/6) | fail |
| Decomposition, rebuilt version, gamma route<sup>c</sup> | accepted 103; tier A 0.798 (3/4 strata); tier C 0.556 (6/6) | tier A 0.609 (4/4); tier C 0.280 (6/6) | fail |
| **Fiducial-point analysis (same waveforms, database-supplied)** | **0.710 (6/6)** | **0.504 (6/6)** | **pass** |
| **Early amplitude ratio Am_b/Am_p1** | **0.836 (6/6)** | not evaluated | **pass** |
| Model-derived pulse transit time (positive control) | 0.571 (6/6) | — | pass |

<sup>a</sup> Source: table 1 of `02_tables.md` (`docs/research/roadmap_v1.md` §9; lab_log entry 12). Frozen version: script 20 `20_pwdb_validity.py`; fiducial-point analysis and positive control: script 23 `23_pwdb_landmarks.py`; rebuilt version and early amplitude ratio: scripts 26 `26_pwdb_compare.py` and 27 `27_threshold_sensitivity.py` (`data/pwdb/pwdb_compare.csv`, `pwdb_compare_report.txt`).

<sup>b</sup> Bold, criterion met (median |ρ| ≥ 0.30 with the predicted sign in every stratum). 'Not evaluated', the index was not evaluated; —, no such index.

<sup>c</sup> The two rebuilt-version rows accepted few beats and are given by tier. Tier A, subjects accepted by the method itself; tier B, subjects accepted by every compared method; tier C, all subjects regardless of acceptance

## Table 3

**Table 3.** Within-stratum main effect of each varied factor (difference between the +1 SD and −1 SD means ÷ stratum mean, %)<sup>a</sup>. In parentheses, the within-stratum Spearman rank correlation of the factor with the index<sup>b</sup>.

| Factor | Fiducial-point ΔT | Decomposition ΔT (frozen) | Decomposition RI (frozen) | Early amplitude ratio |
|---|---|---|---|---|
| Aortic diameter | −9.4 | −12.6 (−0.37) | +33.2 (+0.30) | +2.0 |
| Heart rate | **−2.6** | **−10.9 (−0.54)** | −40.3 (−0.37) | +4.0 |
| Ejection time | +4.6 | +0.7 (+0.09) | +3.2 (−0.10) | −1.1 |
| Mean arterial pressure | −15.1 | −7.7 (−0.09) | +24.2 (−0.00) | −4.0 |
| **Pulse wave velocity** | **−31.2** | **−17.0 (−0.26)** | **+33.7 (−0.17)** | **−7.1** |
| Stroke volume | +15.9 | −4.1 (+0.05) | +21.6 (−0.05) | −0.2 |

<sup>a</sup> Source: table 2 of `02_tables.md` (`docs/research/roadmap_v1.md` §9; lab_log entry 12; factor tables of scripts 20, 23 and 26).

<sup>b</sup> Bold, the rows and columns contrasted in the text (pulse wave velocity and heart rate). For fiducial-point ΔT the pulse-wave-velocity column is 12 times the heart-rate column; for decomposition ΔT only 1.6 times. In rank terms decomposition ΔT follows heart rate (−0.54) more than pulse wave velocity (−0.26).

## Table 3b

**Table 3b.** One-factor-at-a-time sweep (other factors at their reference values; median over age strata; ΔT in ms)<sup>a, b</sup>.

| Factor | ΔT, −1 SD | ΔT, reference | ΔT, +1 SD | RI, −1 SD | RI, reference | RI, +1 SD |
|---|---|---|---|---|---|---|
| **Pulse wave velocity** | **332.3** | **352.8** | **251.2** | **0.325** | **0.254** | **0.647** |
| Heart rate | 382.5 | 352.8 | 321.6 | 0.324 | 0.254 | 0.230 |
| Aortic diameter | 353.6 | 352.8 | 332.1 | 0.235 | 0.254 | 0.322 |
| Ejection time | 341.2 | 352.8 | 362.9 | 0.274 | 0.254 | 0.233 |
| Mean arterial pressure | 337.2 | 352.8 | 348.7 | 0.294 | 0.254 | 0.236 |
| Stroke volume | 339.5 | 352.8 | 356.7 | 0.282 | 0.254 | 0.251 |

<sup>a</sup> Source: table 2b of `02_tables.md` (lab_log 2026-09-03, results of study 0; entry 12; script 20). Values of the frozen decomposition.

<sup>b</sup> Bold, the row with the largest reversal (pulse wave velocity): ΔT moves against the prediction on the −1 SD side and RI is U-shaped. In ΔT the mean-arterial-pressure row also reverses slightly (337.2 → 352.8 → 348.7; lab_log entry 113).

## Table 3c

**Table 3c.** True transit times from the model onset-time table<sup>a, b</sup>.

| Segment | Median | 5th–95th percentile |
|---|---|---|
| Aortic root → finger | 96 ms | 66–120 ms |
| Radial → finger | 8 ms | 4–16 ms |

<sup>a</sup> Source: table 2c of `02_tables.md` (lab_log 2026-09-03, results of study 0; script 20; PWDB file `pwdb_onset_times.csv`).

<sup>b</sup> Within-stratum ρ(aortic PWV, root→finger transit time) = −0.99 (6/6); ρ(decomposition ΔT, same) = +0.19 (6/6).

## Table 4

**Table 4.** Basis function and number of components, exhaustive sweep (exploratory, post hoc)<sup>a, b, c, d</sup>.

| Basis | Components | Wang pass | Errx median [ms] | NRMSE median | Parameters on a bound | ΔT × PWV \|ρ\| |
|---|---|---|---|---|---|---|
| Skew-Gaussian, α∈[0,8] (frozen) | 2 | 0.0% | 40 | 0.0212 | 2% | 0.14 (2/4) |
| Skew-Gaussian, α∈[0,8] (frozen) | 3 | 2.0% | 24 | 0.0110 | 0% | 0.08 (4/4) |
| **Gaussian (no skew)** | **2** | **0.0%** | **30** | **0.0491** | **4%** | **0.54 (4/4)** |
| Gaussian (no skew) | 3 | 0.0% | 14 | 0.0191 | 86% | 0.55 (3/4) |
| Gaussian (no skew) | 4 | 1.0% | 15 | 0.0145 | 94% | 0.28 (3/4) |
| Gaussian (no skew) | 5 | 1.0% | 13 | 0.0084 | 92% | 0.52 (3/4) |
| Skew-Gaussian, α∈[−8,8] (Basso) | 2 | 0.0% | 40 | 0.0212 | 2% | 0.14 (2/4) |
| Skew-Gaussian, α∈[−8,8] (Basso) | 3 | 2.0% | 23 | 0.0111 | 0% | 0.12 (3/4) |
| **Gamma (frozen search bounds)** | **3** | **15.3%** | **12** | **0.0071** | **93%** | **0.56 (4/4)** |
| Gamma (frozen search bounds) | 4 | 22.4% | 10 | 0.0051 | 99% | 0.35 (3/4) |
| Gamma (wide search bounds) | 3 | 10.2% | 12 | 0.0068 | 89% | 0.55 (4/4) |
| Gamma (wide search bounds) | 4 | 31.6% | 8 | 0.0047 | 99% | 0.38 (3/4) |

<sup>a</sup> Exploratory, post hoc analysis; not used for the prespecified decision. Using an improved fit as a primary analysis would require a new preregistration.

<sup>b</sup> Source: table 3 of `02_tables.md`; lab_log entry 13. Script 31 `31_pwdb_basis_explore.py` (`data/pwdb/pwdb_basis_explore.csv`).

<sup>c</sup> Subjects: 98 notched beats taken from 120 subjects, in 4 strata of at least 8 beats (smaller than the 4,374 subjects and 6 strata of the decision test, so the values are wider). Preprocessing and Wang's acceptance criterion identical to the decision test. |ρ| is the within-stratum median over all beats (acceptance ignored); in parentheses, the number of strata with the predicted sign.

<sup>d</sup> Bold, the two best-tracking rows among the decompositions.

## Table 5a

**Table 5a.** Published fitting conditions applied unchanged (exploratory, post hoc)<sup>a, b, c, d, e</sup>.

| Source of the conditions | ΔT × aortic PWV | RI × peripheral vascular resistance |
|---|---|---|
| Tigges 2017 (recommended gamma, M = 3) | **0.578 (6/6)** | — |
| Fleischhauer 2020 (two kernels) | 0.505 (5/6) | 0.314 (5/6) |
| Couceiro 2015 | 0.500 (6/6) | **R1_d 0.585 (6/6)** |
| Wang 2013 (all beats) | 0.457 (5/6) | — |
| Basso 2024 (L = 3) | — | 0.314 (6/6) |
| Goswami 2010 | — | 0.343 (5/6) |
| Reference: fiducial-point indices supplied with PWDB (Charlton) | 0.705 | 0.501 |

<sup>a</sup> Exploratory, post hoc analysis; not used for the prespecified decision. Using an improved fit as a primary analysis would require a new preregistration.

<sup>b</sup> Source: table 4 of `02_tables.md`; lab_log entry 18. Script 33 `33_pwdb_literature_replica.py` (`docs/research/results/33_literature_replica_report.txt`; lab_log entries 16–18).

<sup>c</sup> Subjects: 624 chosen systematically (subject number modulo 7 equal to 0). In the same subset the fiducial-point indices supplied with PWDB (Charlton) give ΔT 0.705 and RI 0.501. In parentheses, the number of strata with the predicted sign.

<sup>d</sup> Bold, the best condition for ΔT and the only condition whose RI exceeded the fiducial-point value.

<sup>e</sup> For RI only Couceiro's R1_d exceeds the fiducial-point value (0.585 versus 0.501). Under the prespecified rule this row is not taken into the verdict. Three caveats: in this model peripheral vascular resistance determines the diastolic decay, so part of the association is built in; measured waveforms often lack a diastolic peak; and deviations remain in our replication.

## Table 5b

**Table 5b.** Deviations from the published conditions in the replication (supplement to table 5a)<sup>a, b</sup>.

| Source | Deviation |
|---|---|
| All conditions | The optimiser was that of our environment (SciPy), not identical to the originals |
| Wang 2013 | The weight search step was set to 1 |
| Couceiro 2015 | For the 1% of beats whose fifth-component initial value could not be formed from table 1 of the original, the default was used |
| Tigges 2017 | Resampling to 40 Hz for the corrected Akaike information criterion used a Kaiser window, as the original describes |
| Common | PWDB gives one noise-free beat per subject; the conditions differ from the measured waveforms of the originals |

<sup>a</sup> Exploratory, post hoc analysis; not used for the prespecified decision. Using an improved fit as a primary analysis would require a new preregistration.

<sup>b</sup> Source: the deviation table under table 4 of `02_tables.md`; lab_log entry 18. Deviation table of script 33 (lab_log entries 17, 18).

## Table 6a

**Table 6a.** Within-age-stratum Spearman rank correlation by waveform type (exploratory, post hoc)<sup>a, b, c, d, e</sup>.

| Waveform type (n) | Fiducial-point ΔT, tier C | Decomposition ΔT (frozen), tier A | Early amplitude ratio, tier C | Fiducial-point RI, tier C | Decomposition RI (frozen), tier A |
|---|---|---|---|---|---|
| Type 1, notch present (891) | 0.343 (4/6) | 0.224 (4/6) | 0.326 (4/6) | 0.481 (6/6) | **0.554 (6/6)** |
| Type 3, inflection only (3,378) | **0.430 (6/6)** | 0.220 (6/6) | **0.815 (6/6)** | **0.550 (6/6)** | 0.233 (5/6) |
| Type 4, neither (105; 3 strata) | **0.796 (3/3)** | 0.472 (3/3) | 0.247 (0/3) | **0.888 (3/3)** | 0.637 (3/3) |
| All subjects (4,374) | **0.710 (6/6)** | 0.223 (6/6) | **0.836 (6/6)** | **0.504 (6/6)** | 0.207 (5/6) |

<sup>a</sup> Exploratory, post hoc analysis; not used for the prespecified decision. Using an improved fit as a primary analysis would require a new preregistration.

<sup>b</sup> Source: table 5 of `02_tables.md`; script 48 (`docs/research/results/48_pwdb_by_waveform_type.txt`); lab_log entry 137. Section C of script 50 reproduces the fiducial-point values of types 1 and 3 from the same input.

<sup>c</sup> Tier A, subjects accepted by the method itself; tier B, subjects accepted by every compared method; tier C, all subjects regardless of acceptance. Fiducial-point indices carry no acceptance decision and are therefore always tier C.

<sup>d</sup> Subjects as in the decision test (4,374); waveform type by `pda2.find_landmarks` (type 1, dicrotic notch and diastolic peak present as extrema; type 3, no extrema, but the inflection point of the descending limb can stand in; type 4, neither found). Six age strata, at least 8 subjects per stratum. Median |ρ|; in parentheses, the number of strata with the predicted sign. The three left columns are ΔT × aortic PWV (predicted sign negative; positive for the early amplitude ratio), the two right columns RI × peripheral vascular resistance (positive).

<sup>e</sup> Bold, criterion met (median |ρ| ≥ 0.30 with the predicted sign in every stratum).

## Table 6b

**Table 6b.** Within-stratum spread of the true values themselves (restriction of range; exploratory, post hoc, tier C)<sup>a, b, c, d</sup>.

| Waveform type | Width of aortic PWV [m/s] | Width of peripheral vascular resistance | Strata with ≥ 8 subjects | Smallest stratum n |
|---|---|---|---|---|
| Type 1, notch present | **0.114** | 3.71×10⁷ | 6 / 6 | 53 |
| Type 3, inflection only | **1.431** | 4.58×10⁷ | 6 / 6 | 405 |
| Type 4, neither | 0.934 | 2.48×10⁷ | 3 / 6 | 29 |
| Type 1 ÷ type 3 | **0.080** | 0.810 | — | — |

<sup>a</sup> Exploratory, post hoc analysis; not used for the prespecified decision. Using an improved fit as a primary analysis would require a new preregistration.

<sup>b</sup> Source: table 5b of `02_tables.md`; script 50 (`docs/research/results/50_reservoir_bench_BC.txt`); lab_log entry 147.

<sup>c</sup> Tier A, subjects accepted by the method itself; tier B, subjects accepted by every compared method; tier C, all subjects regardless of acceptance

<sup>d</sup> Type-1 values must not be read as a failure of the methods: restricted to type 1, aortic PWV barely varies within an age stratum. The interquartile range was taken per age stratum and its median across strata is shown (units as distributed with PWDB). This table was made after the weakness of type 1 was seen; no prediction was fixed and no test is made. Bold, the values contrasted in the text.

## Table 7

**Table 7.** Diagnosis and the corresponding modifications: what was changed, the observation behind it, the prediction fixed before the run, and the result (type 3; exploratory, post hoc)<sup>a, b, c, d</sup>.

| Modification (no.) | What was changed | Observation behind it (source) | Prediction fixed before the run (source) | Result (type 3: ΔT tier C, RI tier C, pass rate) | Reading |
|---|---|---|---|---|---|
| (0) Frozen fit (no diastolic term) | Nothing changed: fit_beat of src/pda.py with its default arguments (delay bound 0.08 s) | Control; checks that the replica behaves exactly like the original (entry 142) | P10: ΔT, RI and acceptance match script 26 for all subjects; fiducial-point ρ by type reproduces script 48 (entry 143) | ΔT tier C 0.207 (6/6); RI tier C 0.184 (4/6); pass rate 0.901 | Identical to script 26 for every subject: section C reads the same beats, truth and rules (entry 144) |
| (2) Second-component delay bound 0.08 → 0.01 s | Only the lower bound of Δμ relaxed from 0.08 to 0.01 s; otherwise the frozen fit | In synthetic beats frozen ΔT piled up at the bound near 150 ms and RI reversed sign (entries 141, 143) | P7: type 3, tier C: fraction at the Δμ bound exceeds (4) by ≥ 0.10 (entry 143) | ΔT tier C 0.206 (6/6); RI tier C 0.180 (5/6); pass rate 0.899 | No beat in any type sits at the bound; the Δμ bound is not the cause (entry 144) |
| (4) Reservoir term (forward wave convolved, τ ≥ 0.05 s) | Reservoir term added: forward wave convolved with a unit-area exponential kernel (parameters g, τ; τ ≥ 0.05 s) | Candidate (1) of entry 139; two-element Windkessel solution. In synthetic beats ρ 1.00, no degeneracy, accepted (entry 143) | P6, P8, P9: type-3 tier-A ΔT meets criterion; RI positive even at 75 years; type-1 ΔT too (entry 143) | ΔT tier C 0.245 (3/6); RI tier C 0.274 (5/6); pass rate 0.088 | All three 'no'; g at its upper and τ at its lower bound, i.e. degenerate (entries 144, 146) |
| (4c) Reservoir term, τ ≥ 0.15 s | Same as (4) except the lower bound of the reservoir time constant τ (0.05 → 0.15 s) | Degeneracy diagnosis of entry 146 (kernel → δ as τ → 0); 0.15 s is physiological and 3× forward-wave width | 'Fixed before seeing the result; if it still fails, adding a term fails even when degeneracy is blocked' (entry 146) | ΔT tier C 0.187 (4/6); RI tier C 0.418 (6/6); pass rate 0.035 | The pile-up merely moved to the new bound; degeneracy persists and the pass rate is the lowest (entry 147) |
| (3) Free exponential decay term | A free exponential decay d·exp(−(t−t0)/τ) added (same form as A1 of script 24; 10 parameters) | Script-24 term, untested on PWDB (entry 139); failed in synthetic beats, but the decline dominates real data (entry 144 §4) | No numerical prediction: 'see how it behaves in real data' (entries 144, 145) | ΔT tier C 0.272 (6/6); RI tier C 0.258 (6/6); pass rate 0.591 | Only slightly better than the frozen fit; τ reaches its lower bound, degenerating like (4) (entry 146) |
| (7) Output-side convolution of the two-component sum | Two-component sum replaced by its convolution with a unit-area exponential kernel (9 parameters); ΔT, RI from unconvolved peaks | Closest to the generation of the PWDB PPG (Charlton 2019, eq. A1), without the degenerate direction of (4) (entry 149) | Caveat: 'the PWDB PPG is generated in this form, so favoured in silico'; expected to work (entries 149, 152) | ΔT tier C 0.267 (2/6); RI tier C 0.361 (4/6); pass rate 0.728 | Fits waveform best yet ΔT tracks worse than frozen fit; freedom for the decline leaves component 2 undetermined (entry 152) |
| (8) Two-stage: τ from the last 30%, deconvolve, then frozen fit | τ estimated from the last 30% of the beat, deconvolution x = y + τ·y′, then the frozen fit | Corresponds to reservoir studies that estimate the time constant from late diastole (entry 149) | 'Uses a derivative, so sensitive to noise'; no numerical prediction (entry 149) | ΔT tier C 0.012 (4/6); RI tier C 0.195 (6/6); pass rate 0.086 | Deconvolution overshoots, lifting diastole; the width of component 2 hits its upper bound; pass rate near the lowest (entry 152) |
| (6b) Fit truncated at 0.65 of the beat length | Residual taken up to 0.65 of the beat only; bounds, starts, peaks use the full beat; Δμ bound unchanged | Candidate (3) of entry 139; 0.65 was set (script 24, entry 139) before real data were seen (entry 145) | 'Main fraction stays 0.65T; not re-chosen after seeing the numbers' (entry 145); (6b) should equal (6) (entry 144) | ΔT tier C **0.596 (6/6)**; RI tier C 0.107 (6/6); pass rate 0.413 | ΔT meets the criterion in tiers A and C, above fiducial-point analysis; RI only in tier A (entries 146, 147) |
| (6c) Truncated at 0.55 of the beat | Differs from (6b) only in the truncation fraction (0.55; Δμ bound 0.08 s unchanged) | Descriptive check that the conclusion is insensitive to the chosen fraction (entry 145, rule 2) | 'Even if 0.55 or 0.75 comes out better, the main fraction is written as 0.65T' (entry 145, rule 3) | ΔT tier C 0.582 (6/6); RI tier C 0.182 (3/6); pass rate 0.156 | Tier C at the level of 0.65, all strata in direction; lowest pass rate among the fractions (entry 147) |
| (6d) Truncated at 0.75 of the beat | Differs from (6b) only in the truncation fraction (0.75) | As above (descriptive sensitivity check; the rules of entry 145) | As above (the rules of entry 145) | ΔT tier C 0.545 (6/6); RI tier C 0.149 (6/6); pass rate 0.726 | Same level in tier C, in direction; the highest pass rate among the fractions (entry 147) |
| (6e) Truncated at an absolute 0.45 s (at most 0.90 of the beat) | Differs from (6b) only in how the cut is placed: absolute 0.45 s (at most 0.90 of the beat) | W1: cutting at a fraction of the beat makes the cut position a function of heart rate (entries 148, 149) | 'See whether cutting at an absolute time gives the same conclusion' (entry 149) | ΔT tier C **0.724 (6/6)**; RI tier C 0.110 (3/6); pass rate 0.187 | Same direction, same or higher level than the fractional cut; not a product of heart-rate dependence (entry 152) |
| (9) Residual taken in the first-derivative domain | Residual taken between d/dt(g1+g2) and y′; model, bounds, starts and solution choice as in the frozen fit | Candidate (3) of entry 139, second half: the decline shrinks under differentiation, pulling component 2 less (entry 149) | 'Pass rate < 0.30 or type-3 tier-C ΔT < 0.30 at 0.01 noise → derivative domain noise-sensitive' (entry 153 §5) | ΔT tier C **0.687 (6/6)**; RI tier C **0.416 (6/6)**; pass rate 0.510 | Only version meeting tier-C criterion for both ΔT and RI; degrades at 2% noise, rejects stiff subjects (entries 152, 158) |
| Fiducial-point analysis (database-supplied; reference) | No fit; ΔT and RI taken from the fiducial points supplied with PWDB (Charlton 2019, table A3 rules) | Control of the decision test (2026-09-03, 2026-09-06) | Settled in the decision test; script-48 P1 (criterion in types 1 and 3) missed for type 1 (entry 137) | ΔT tier C 0.430 (6/6); RI tier C 0.550 (6/6); pass rate — | Reference for type 3; tier B is a subset favourable to decomposition, hence below tier C (entry 158) |

<sup>a</sup> Exploratory, post hoc analysis; not used for the prespecified decision. Using an improved fit as a primary analysis would require a new preregistration.

<sup>b</sup> Source: table 6 of `02_tables.md`; script 50 (`docs/research/results/50_reservoir_bench_BC.txt`, `50_reservoir_bench_C14.txt`); lab_log entries 144, 146, 147, 149, 151, 152. Text columns condense `data/prespec_chronology.json` (reconstructed from lab_log) to at most 20 words and were checked against the entries cited; the numeric column is identical to table 6 of `02_tables.md` (table 8 of this set). 'Entry n' is a numbered addendum of lab_log.

<sup>c</sup> Tier A, subjects accepted by the method itself; tier B, subjects accepted by every compared method; tier C, all subjects regardless of acceptance

<sup>d</sup> Bold, criterion met (median |ρ| ≥ 0.30 with the predicted sign in every stratum).

## Table 8

**Table 8.** Type-3 correlations when the handling of the diastolic decline is changed (exploratory, post hoc, 4,374 subjects)<sup>a, b, c, d, e</sup>.

| Handling of the diastolic decline | ΔT × PWV, tier A | ΔT × PWV, tier C | RI × resistance, tier A | RI × resistance, tier C | Pass rate | ΔT offset from the supplied fiducial point (tier A) |
|---|---|---|---|---|---|---|
| (0) Frozen fit (no diastolic term) | 0.220 (6/6) | 0.207 (6/6) | 0.233 (5/6) | 0.184 (4/6) | 0.901 | +98.5 ms |
| (2) Second-component delay bound 0.08 → 0.01 s | 0.216 (6/6) | 0.206 (6/6) | 0.236 (6/6) | 0.180 (5/6) | 0.899 | +97.9 ms |
| **Add a term for the diastolic decline** | | | | | | |
| (4) Reservoir term (forward wave convolved, τ ≥ 0.05 s) | 0.457 (5/6) | 0.245 (3/6) | 0.635 (5/6) | 0.274 (5/6) | 0.088 | +138.2 ms |
| (4c) Reservoir term, τ ≥ 0.15 s | 0.508 (3/4) | 0.187 (4/6) | 0.270 (4/4) | 0.418 (6/6) | 0.035 | +69.4 ms |
| (3) Free exponential decay term | 0.267 (5/6) | 0.272 (6/6) | 0.268 (6/6) | 0.258 (6/6) | 0.591 | +96.7 ms |
| (7) Output-side convolution of the two-component sum | 0.042 (4/6) | 0.267 (2/6) | 0.381 (5/6) | 0.361 (4/6) | 0.728 | +84.7 ms |
| (8) Two-stage: τ from the last 30%, deconvolve, then frozen fit | 0.102 (4/5) | 0.012 (4/6) | 0.060 (2/5) | 0.195 (6/6) | 0.086 | +80.3 ms |
| **Exclude or down-weight the diastolic decline** | | | | | | |
| **(6b) Fit truncated at 0.65 of the beat length** | **0.828 (6/6)** | **0.596 (6/6)** | **0.530 (6/6)** | 0.107 (6/6) | 0.413 | **+25.8 ms** |
| (6c) Truncated at 0.55 of the beat | 0.728 (4/6) | 0.582 (6/6) | 0.444 (6/6) | 0.182 (3/6) | 0.156 | +44.5 ms |
| (6d) Truncated at 0.75 of the beat | 0.662 (6/6) | 0.545 (6/6) | 0.326 (6/6) | 0.149 (6/6) | 0.726 | +78.7 ms |
| (6e) Truncated at an absolute 0.45 s (at most 0.90 of the beat) | **0.711 (6/6)** | **0.724 (6/6)** | 0.461 (4/6) | 0.110 (3/6) | 0.187 | +42.0 ms |
| **(9) Residual taken in the first-derivative domain** | **0.523 (6/6)** | **0.687 (6/6)** | **0.336 (6/6)** | **0.416 (6/6)** | 0.510 | +88.8 ms |
| Fiducial-point analysis (database-supplied; reference) | — | 0.430 (6/6) | — | 0.550 (6/6) | — | 0 (reference) |

<sup>a</sup> Exploratory, post hoc analysis; not used for the prespecified decision. Using an improved fit as a primary analysis would require a new preregistration.

<sup>b</sup> Source: table 6 of `02_tables.md`; script 50 (`docs/research/results/50_reservoir_bench_BC.txt`, `50_reservoir_bench_C14.txt`); lab_log entries 144, 146, 147, 149, 151, 152.

<sup>c</sup> Tier A, subjects accepted by the method itself; tier B, subjects accepted by every compared method; tier C, all subjects regardless of acceptance. Pass rate: the fraction accepted under the same convergence checks as the frozen version (parameters on a bound, component height, difference in reflection coefficient between competing solutions), i.e. the fraction remaining in tier A.

<sup>d</sup> Refits of the same beats of the same 4,374 subjects. The two-kernel model has no term for the diastolic decline, so versions that change only its handling are grouped into those that add a term for the decline and those that exclude it from the fit or down-weight it in the residual. The main fraction 0.65 was fixed before this analysis and was not re-chosen after seeing these numbers (lab_log entry 145). The last column is the median difference between the peak of the second component and the diastolic fiducial point supplied with PWDB (positive, second component later).

<sup>e</sup> Bold, criterion met (median |ρ| ≥ 0.30 with the predicted sign in every stratum).

## Table 9

**Table 9.** Tier B and runs with added noise (type 3; exploratory, post hoc)<sup>a, b, c, d, e, f</sup>.

| Handling of the diastolic decline | Tier | ΔT × PWV, no noise | 1% | 2% | RI × resistance, no noise | 1% | 2% | Pass rate, none / 1% / 2% |
|---|---|---|---|---|---|---|---|---|
| (0) Frozen fit (no diastolic term) | A | 0.220 | 0.213 | 0.209 | 0.233 | 0.246 | 0.253 | 0.901 / 0.881 / 0.862 |
|  | B | **0.510** | **0.532** | **0.563** | 0.184 | 0.201 | 0.134 |  |
|  | C | 0.207 | 0.138 | 0.130 | 0.184 | 0.189 | 0.173 |  |
| (6b) Fit truncated at 0.65 of the beat length | A | **0.828** | **0.819** | **0.786** | **0.530** | **0.493** | **0.414** | 0.413 / 0.379 / 0.350 |
|  | B | **0.630** | **0.609** | **0.651** | **0.381** | 0.266 | 0.168 |  |
|  | C | **0.596** | **0.486** | **0.454** | 0.107 | 0.075 | 0.083 |  |
| (9) Residual taken in the first-derivative domain | A | **0.523** | **0.370** | **0.416** | **0.336** | 0.103 | 0.181 | 0.510 / 0.326 / 0.290 |
|  | B | **0.622** | **0.642** | **0.659** | **0.435** | **0.318** | 0.176 |  |
|  | C | **0.687** | **0.337** | **0.347** | **0.416** | 0.196 | 0.173 |  |
| Fiducial-point analysis (database-supplied; reference) | B | **0.373** | 0.411 | **0.487** | **0.562** | **0.405** | **0.384** | — |
|  | C | **0.430** | (as at left) | (as at left) | **0.550** | (as at left) | (as at left) | — |

<sup>a</sup> Exploratory, post hoc analysis; not used for the prespecified decision. Using an improved fit as a primary analysis would require a new preregistration.

<sup>b</sup> Source: table 6c of `02_tables.md`; script 50 (`docs/research/results/50_reservoir_bench_B3.txt`, `50_reservoir_bench_noise0.01.txt`, `50_reservoir_bench_noise0.02.txt`); lab_log entry 158.

<sup>c</sup> Tier A, subjects accepted by the method itself; tier B, subjects accepted by every compared method; tier C, all subjects regardless of acceptance. Tier B here: subjects accepted by all three of the frozen fit, the 0.65T truncation and the derivative-domain version (732; 388 at 1% noise, 323 at 2%); tier C, all type-3 subjects (3,378).

<sup>d</sup> Noise is white Gaussian noise whose SD is the stated fraction of the peak-to-trough amplitude of the beat; waveform type and fiducial points were assigned on the beat before noise was added.

<sup>e</sup> The fiducial-point reference (tier C) is computed on the noise-free beats, so in the noise columns it is not a like-for-like comparison.

<sup>f</sup> Bold, criterion met (median |ρ| ≥ 0.30 with the predicted sign in every stratum).

## Table S1

**Table S1.** Parameters that reached a search bound (type 3, tier C, top two)<sup>a, b, c, d, e</sup>.

| Handling of the diastolic decline | Fraction of beats at a bound | Breakdown |
|---|---|---|
| (0) Frozen fit (no diastolic term) | 0.072 | α1:hi 0.04; σ1:hi 0.03 |
| (4) Reservoir term (forward wave convolved, τ ≥ 0.05 s) | 0.903 | **g:hi 0.61**; **τ:lo 0.21** |
| (4c) Reservoir term, τ ≥ 0.15 s | 0.932 | **τ:lo 0.88**; g:hi 0.56 |
| (3) Free exponential decay term | 0.372 | **τ:lo 0.33** |
| (7) Output-side convolution of the two-component sum | 0.254 | α1:hi 0.25; μ1:lo 0.02 (τ:lo 0.00) |
| (8) Two-stage: τ from the last 30%, deconvolve, then frozen fit | 0.914 | **σ2:hi 0.70**; μ1:lo 0.35 |
| (6b) Fit truncated at 0.65 of the beat length | 0.562 | σ2:hi 0.30; α2:hi 0.23 |
| (6e) Truncated at an absolute 0.45 s (at most 0.90 of the beat) | 0.803 | σ2:hi 0.39; α2:hi 0.39 |
| (9) Residual taken in the first-derivative domain | 0.319 | σ2:hi 0.23; Δμ:lo 0.11 |

<sup>a</sup> Exploratory, post hoc analysis; not used for the prespecified decision. Using an improved fit as a primary analysis would require a new preregistration.

<sup>b</sup> Source: table 6b of `02_tables.md`; script 50 (`docs/research/results/50_reservoir_bench_BC.txt`, `50_reservoir_bench_C14.txt`); lab_log entries 144, 146, 147, 149, 151, 152.

<sup>c</sup> Tier A, subjects accepted by the method itself; tier B, subjects accepted by every compared method; tier C, all subjects regardless of acceptance

<sup>d</sup> a1, μ1, σ1 and α1 are the height, position, width and skewness of the first component; a2, Δμ, σ2 and α2 the same for the second; g and τ the gain and time constant of the reservoir term. ':lo' lower bound, ':hi' upper bound. A beat can reach bounds in several parameters, so the fractions do not sum to 1.

<sup>e</sup> Bold, the parameters discussed in the text as the sign of degeneracy.

## Table S2a

**Table S2a.** Difference between each method's ΔT and the arrival time ΔT_true of the linearly separated backward wave (tier C)<sup>a, b, c, d, e</sup>.

| Waveform type | Method | n | Median difference | Pooled Spearman ρ |
|---|---|---|---|---|
| Type 1 | Decomposition (PPG) | 315 | +257.8 ms | −0.135 |
| Type 1 | Decomposition (pressure) | 315 | +255.4 ms | −0.107 |
| Type 1 | Fiducial-point (supplied) | 315 | +222.0 ms | −0.385 |
| Type 3 | Decomposition (PPG) | 2,771 | +219.0 ms | +0.041 |
| Type 3 | Decomposition (pressure) | 2,771 | +187.6 ms | +0.059 |
| Type 3 | Fiducial-point (supplied) | 2,758 | +114.0 ms | −0.022 |
| Type 4 | Decomposition (PPG) | 105 | +13.1 ms | +0.500 |
| Type 4 | Fiducial-point (supplied) | 72 | +38.2 ms | −0.538 |

<sup>a</sup> Exploratory, post hoc analysis; not used for the prespecified decision. Using an improved fit as a primary analysis would require a new preregistration.

<sup>b</sup> Source: table 7a of `02_tables.md`; script 51 (`docs/research/results/51_wave_separation.txt`); lab_log entries 150, 152.

<sup>c</sup> Tier A, subjects accepted by the method itself; tier B, subjects accepted by every compared method; tier C, all subjects regardless of acceptance

<sup>d</sup> The backward wave was obtained from the digital pressure P and flow velocity U of PWDB by linear wave separation, P_f = (ΔP + ρc·ΔU)/2 and P_b = (ΔP − ρc·ΔU)/2 (ρc, slope of the early-systolic P–U loop; baseline, minimum within the beat); ΔT_true is the difference between the peak times of P_b and P_f.

<sup>e</sup> n, subjects in which the separation could be evaluated (1,183 excluded because ρc could not be estimated or the backward wave was essentially absent). Difference = (method's ΔT) − (ΔT_true). ρ is the Spearman correlation pooled over age strata.

## Table S2b

**Table S2b.** The same frozen decomposition applied to the digital pressure waveform (within-stratum Spearman; all 4,374 subjects)<sup>a, b, c, d, e</sup>.

| Waveform fitted | ΔT × PWV, tier A | ΔT × PWV, tier C | RI × resistance, tier A | RI × resistance, tier C | Acceptance rate |
|---|---|---|---|---|---|
| PPG (primary analysis of this paper) | 0.223 (6/6) | 0.205 (6/6) | 0.207 (5/6) | 0.171 (4/6) | 92.3% |
| Digital pressure waveform | **0.486 (6/6)** | **0.313 (6/6)** | 0.225 (6/6) | 0.220 (5/6) | 84.5% |
| Fiducial-point analysis (supplied; PPG; reference) | — | 0.710 (6/6) | — | 0.504 (6/6) | — |

<sup>a</sup> Exploratory, post hoc analysis; not used for the prespecified decision. Using an improved fit as a primary analysis would require a new preregistration.

<sup>b</sup> Source: table 7b of `02_tables.md`; script 51 (`docs/research/results/51_wave_separation.txt`); lab_log entries 150, 152.

<sup>c</sup> Tier A, subjects accepted by the method itself; tier B, subjects accepted by every compared method; tier C, all subjects regardless of acceptance

<sup>d</sup> Restricted to type 3, ΔT of the pressure waveform is 0.400 (6/6) in tier A, meeting the criterion, and 0.227 (6/6) in tier C, not meeting it.

<sup>e</sup> Bold, criterion met (median |ρ| ≥ 0.30 with the predicted sign in every stratum).
