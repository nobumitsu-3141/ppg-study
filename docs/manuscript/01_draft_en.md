# DRAFT — Manuscript v0.1 (working draft, 2026-08-29)

**Status**: Complete draft; all confirmatory-run numbers, Tables 1 and 6, references and
the Zenodo DOI are in. Exploratory analyses added after the freeze (SVR, PWTT decomposition at the
arterial line, in-silico construct validity on the Pulse Wave Database) were integrated on
2026-09-03 (§2.10, §3.6, Discussion, Conclusion, Abstract). The only `[[ ]]` left is the
author's conflict-of-interest attestation. Outstanding before submission: assembly of
display Tables 2–5 from the Results text at submission formatting.
Reference list at the end; all previously flagged entries verified against
PubMed/publisher records on 2026-08-30 (two corrections applied: Sugo & Ochiai journal;
Basso author list and DOI).

**Framing**: reference-free premise test as the primary analysis (see `00_outline_ja.md` §0).

---

## Title

Photoplethysmographic arterial stiffness does not explain intraoperative pulse-wave
transit time variation: a prespecified, reference-free analysis of 862 surgical cases

## Abstract (structured, ~250 words — write last)

**Background.** Cardiac output estimation from pulse wave transit time (PWTT) carries an
error that correlates with vascular state, yet its calibration constant is fixed after
calibration. Correcting it with photoplethysmography-derived vascular indices has been
proposed but rests on an untested premise: that intraoperative PWTT variation reflects the
vascular state those indices measure.

**Methods.** From the VitalDB open perioperative database, 874 cases had photoplethysmogram,
ECG, arterial pressure and a continuous cardiac output track; 862 were analysable under a
statistical analysis plan frozen before the confirmatory analysis. The primary analysis
used no reference cardiac output: within-case change in PWTT was regressed on concurrent
relative changes in the pulse-decomposition component interval (ΔT, as stiffness index) and
reflection index. An exploratory positive control tested whether the indices reproduce the
known association of arterial stiffness with age. After the freeze, two further exploratory
analyses were added: decomposition of PWTT at the radial arterial line, and a test of
construct validity in a virtual population with known pulse wave velocity and peripheral
resistance (Pulse Wave Database, 4,374 subjects).

**Results.** Across 161,737 sixty-second windows, vascular indices explained essentially
none of the within-case PWTT variation (prespecified through-origin pooled r² = 0.000; with
an intercept, 0.044; coefficient per ΔSI% −0.027, per ΔRI% −0.003). By comparison, mean
arterial pressure alone explained 0.139 — three times more — so a vascular contribution to
PWTT exists but is not captured by these indices. The coefficient's sign was consistent with the vascular hypothesis in 78% of
cases, indicating a directionally correct but quantitatively negligible vascular component.
Signals were reproducible (lag-1 autocorrelation: PWTT +0.75, ΔT +0.50), and ΔT reproduced
the expected age association, whereas the reflection index did not and was judged uninterpretable in this signal source.
In the virtual population, the decomposition-derived ΔT correlated with aortic pulse
wave velocity in the predicted direction in every age group but weakly (median |ρ| 0.22),
and RI with peripheral resistance at 0.21; fiducial-point-derived indices computed from the same
waveforms met the same criterion (ΔT 0.71, reflection index 0.50, second-derivative ageing
index 0.89). Splitting
PWTT at the radial line, the term containing the pre-ejection period accounted for 7% of
within-case variance; most variation lay in the distal photoplethysmographic segment.
Correcting the calibration constant did not improve
accuracy (percentage error 27.2% versus 26.9%; difference +0.2 percentage points, 95% CI
+0.1 to +0.4).

**Conclusions.** The premise underlying vascular correction of PWTT-based cardiac output
fails quantitatively: the vascular component of intraoperative PWTT variation, though
directionally detectable, is two orders of magnitude too small to support calibration
correction from single-site photoplethysmography. Against ground truth the limitation is
specific to the decomposition: fiducial-point features of the same waveforms recovered pulse wave
velocity, so how the index is extracted matters more than the fact that it comes from
photoplethysmography. Most intraoperative PWTT variation lay in the distal
photoplethysmographic segment, whose true physiological range is far narrower, so the
measurement of transit time itself is also a target.

---

## 1. Introduction

Continuous, non-invasive estimation of cardiac output (CO) remains an unmet need in
perioperative care. Estimation from pulse wave transit time (PWTT), implemented
commercially as esCCO (Nihon Kohden, Tokyo, Japan), is attractive because it requires only
the electrocardiogram and the photoplethysmogram, both already recorded in essentially
every anaesthetised patient [Ishihara 2004; Sugo 2010]. In multicentre validation it
tracked thermodilution CO adequately enough for clinical trending [Yamada 2012], and the
originators themselves framed it as a trend monitor rather than an absolute measure
[Ishihara 2004].

Its error, however, is not random. Agreement with reference CO deteriorates in a
structured way related to the patient's vascular state, in particular to systemic vascular
resistance and effective arterial elastance [Ishihara & Tsutsui 2014; Biais 2015;
Magliocca 2018], and pooled percentage errors for non-invasive CO devices remain far above
the conventional acceptability threshold [Joosten 2017; Critchley & Critchley 1999]. This
is mechanistically unsurprising: the transformation from a transit time to a stroke volume
is mediated by arterial properties, yet the subject-specific calibration constant is
derived from demographic variables and, once set, is held fixed for the remainder of the
case. It carries no information about vascular state and cannot follow changes in it.
Improving the calibration procedure alone does not repair the method [Smetkin 2017].

An intuitive remedy follows: correct the calibration constant dynamically using a
continuously available marker of vascular state. The photoplethysmogram offers such
markers. Decomposition of the pulse into forward and reflected components yields a
stiffness index, from the interval between component peaks, and a reflection index, from
the ratio of component amplitudes; both have been used as non-invasive descriptors of
arterial stiffness and wave reflection [Millasseau 2002; Rubins 2008; Goswami 2010]. The
strategy itself has precedent in the neighbouring problem of cuffless blood pressure, where
adding a photoplethysmogram intensity ratio to pulse transit time improved accuracy [Ding
2016], and where photoplethysmographic morphology has been shown to outperform pulse
arrival time in a large perioperative database [Yang 2021]. Applied to cardiac output, the
idea was raised explicitly by the manufacturer's own investigators, who reported that
changes in systemic vascular resistance displaced esCCO and called for the effect to be
characterised [Ishihara & Tsutsui 2014]. To our knowledge it has not been tested.

The strategy rests, however, on a premise that has not itself been examined: **that the
variation in PWTT one wishes to correct is in fact driven by the vascular state these
indices measure.** PWTT measured from the R wave is not a purely vascular interval. It
comprises the pre-ejection period as well as arterial transit time, a decomposition made
explicit in the earliest work of this lineage [Ochiai 1999]. The pre-ejection period varies
with preload, afterload and contractility, and its contribution is large: pulse transit
time measured from the electrocardiogram has been judged an unreliable marker of purely
vascular function on that basis [Payne 2006], the pre-ejection period can swing by tens of
milliseconds under sympathetic stress [Pilz 2023], and it can move in the opposite
direction to vascular transit time within the same subject [Djupedal 2022]. Most directly,
the manufacturer's own group reported that the pre-ejection period accounted for
approximately half of the change in PWTT [Sugo 2012]. Independently, decomposition-derived
indices have themselves performed only modestly against vascular references, with amplitude
ratios failing altogether [Couceiro 2015].

If intraoperative PWTT variation is dominated by its cardiac component, or if these indices
do not track the vascular component that remains, then no correction built on them can
succeed, however well the indices are measured. We therefore asked whether the premise
holds before asking whether the correction works. Using a public perioperative waveform
database and an analysis plan frozen before the confirmatory analysis, we quantified how
much of the within-case, beat-to-beat variation in PWTT is explained by simultaneously
measured pulse-decomposition indices. This primary question requires no reference CO
measurement, and is therefore unaffected by the limitations of the reference standards such
databases provide.

The measurement itself is also new. Using only the single photoplethysmogram already
recorded under anaesthesia, and no additional device, we decompose each beat into component
waves (pulse decomposition analysis) and extract a stiffness index and a reflection index
beat by beat, tracking them within a case across the whole operation. These indices were
established as single resting measurements [Millasseau 2002; Millasseau 2006]; to our
knowledge they have not previously been measured through a fit as within-case
intraoperative changes at this scale. Because what the indices are worth depends on how
they are extracted, the model, the search bounds and the acceptance thresholds are given
below in the detail required to reproduce them.

## 2. Methods

### 2.1 Study design, data source and ethics

This was a retrospective analysis of VitalDB, a publicly available database of
high-resolution perioperative waveforms and monitor parameters recorded at Seoul National
University Hospital [Lee 2022]. The database contains 6,388 cases
with anonymised waveform data released for unrestricted research use.

Because the study used only anonymised, publicly released data and involved no patient
contact, the institutional ethics committee of Goto Chuoh Hospital was formally
consulted and responded that ethics committee review was not required. The written
response is retained by the authors.

The statistical analysis plan, including all index definitions, quality thresholds, the
model specification and the interpretation rules, was finalised and frozen before the
confirmatory analysis. Development and verification of the measurement pipeline used
synthetic signals with known ground truth, followed by a 15-case pilot on real waveforms
that revealed the device delay described in §2.3; the pipeline was frozen after that pilot
(plan version 0.3, 28 August 2026), and the 15 pilot cases were excluded in a prespecified
sensitivity analysis (§2.9). Two exploratory analyses (the positive control and the
window-length sensitivity analysis) were added on 29 August (version 0.3.1) and three more
after the confirmatory run (§2.10); all are labelled as such. The frozen plan and the
complete analysis code
are publicly available at https://github.com/nobumitsu-3141/ppg-pda-analysis, archived at Zenodo
(doi:10.5281/zenodo.22676038, the concept DOI, which always resolves to the latest
version; the analyses reported here used v1.0.0). The freeze itself carries an earlier third-party
timestamp (Zenodo, doi:10.5281/zenodo.22167118, archiving tag sap-v0.3 at
commit 407f226; frozen 28 August 2026). The study is reported in accordance with the
STROBE statement for observational research [von Elm 2007], and the secondary
method-comparison analysis follows the checklist of [Montenij 2016]; both completed
checklists are provided as supplements.

### 2.2 Cohort

Cases were required to contain all of: photoplethysmogram (SNUADC/PLETH), electrocardiogram
(SNUADC/ECG_II), invasive arterial pressure (SNUADC/ART), all sampled at 500 Hz, and a
continuous cardiac output track from any of the monitors present in the database. Of the
6,388 cases, 6,157 had PPG, 6,355 had ECG, 3,645 had arterial pressure and 993 had a CO
track; **874 cases satisfied all four requirements** and constituted the study cohort.

Where more than one CO monitor was present, a single reference was selected by a
prespecified device priority (Vigilance II, Vigileo, EV1000, CardioQ). The resulting
reference distribution was EV1000 in 552, Vigileo in 305, CardioQ in 24 and Vigilance II
in 5 cases (counts overlapping before priority was applied).

**Reference standard limitation, stated in advance.** In 857 of 874 cases (98%) the
reference CO was derived from the arterial pressure waveform (FloTrac family: Vigileo,
EV1000). Such devices estimate stroke volume from the standard deviation of the pulse
pressure with a compliance correction, so their output moves with arterial pressure and
their reliability is known to depend on systemic vascular resistance. Because the
hypothesis under test also concerns vascular state, an improvement in agreement with such
a reference could reflect either a genuine gain in CO accuracy or a shared dependence on
vascular state. Independent references within the database are limited to pulmonary artery
thermodilution (5 cases) and oesophageal Doppler (24 cases). This limitation cannot be
resolved within VitalDB, and it is the reason the primary analysis of this study was
prespecified to be reference-free.

### 2.3 Signal provenance and processing

**Provenance.** The SNUADC/PLETH channel is the photoplethysmographic waveform as output by
the bedside monitor at 500 Hz, not a research-grade optical recording. It has therefore
already passed through the manufacturer's display processing chain, whose filtering is not
publicly specified and whose gain behaviour we cannot independently verify. Two consequences
are relevant. Filtering of this kind shifts and reshapes the timing fiducial points on which
decomposition-derived intervals depend, in an age-dependent manner [Liao 2023], and any
automatic gain control would attenuate the amplitude information on which the reflection
index depends. We could not exclude automatic gain control from the available documentation.
For this reason we added, as an exploratory analysis, a positive control
(§2.6) establishing that the indices recover a known vascular relationship in these
recordings, and we report index identifiability per beat rather than assuming it.

All processing was performed in non-overlapping 60-second windows.

**Device delay of the photoplethysmographic channel.** During pipeline validation we found
that the PPG channel in this database is delayed relative to the ECG by a fixed,
case-specific interval of the order of 670 ms, reflecting the monitor's internal signal
processing. Left uncorrected this delay causes two failures: beat segmentation windows
anchored to the R wave miss the true pulse foot, and, when the delay exceeds the RR
interval, the apparent transit time wraps modulo the cardiac cycle. We therefore estimated
the delay at case level, by unwrapping candidate R-to-foot intervals against their aliases
at one and two RR intervals and selecting the branch with the widest coverage of the
record, and assigned per-beat values to the branch nearest that estimate.

**R-wave detection** used a Pan–Tompkins-style detector (differentiation, squaring, moving
average integration, percentile-based adaptive threshold).

**Beat segmentation** was driven by systolic peaks of the photoplethysmogram (minimum
prominence 0.25 of the window signal range; minimum separation 0.55 of the median RR
interval taken from the ECG). For each accepted peak the pulse foot was located as the
maximum of the smoothed second derivative preceding the peak, within a 0.45-second search
window. Beats failing a signal quality index (non-zero amplitude, absence of missing
samples, fewer than 10% of samples identical to their neighbour) were discarded.

**Effective noise and ensemble depth.** Controlling noise *before* fitting is central to
this method. On synthetic pulses at a relative noise of 0.0116, averaging four beats sent
17 of 40 beats to an incorrect solution, and 16 of those 17 passed all three convergence
checks below. Fits that survive the checks while being wrong therefore exist, and the only
defence against them is noise reduction before fitting. Ensemble depth was accordingly set
per window rather than fixed. Using the fact that white noise contributes a variance of 6σ²
to the second difference d² of the samples, we took σ̂ = 1.4826 · MAD(d²) / √6 and divided
it by the beat amplitude range to give the relative noise σ̂_rel. Averaging n beats reduces
noise by 1/√n, so to hold the post-averaging effective noise at or below a target of 0.003
we averaged

  n = clip( ⌈(σ̂_rel / 0.003)²⌉ , 4 , 16 )                                            (1)

beats. Windows that could not reach the target with 16 beats, and windows with fewer than
2n quality-passing beats, were rejected. Beats were aligned at their feet and were **not**
time-normalised: normalisation smooths the narrow forward wave more than the reflected wave
and was found on synthetic data to inflate the reflection index by 24–39%.

### 2.4 Pulse decomposition and index definitions

**Model.** Each ensemble-averaged beat, floored at its minimum and normalised by its
maximum, was represented as the sum of two skewed-Gaussian components (Azzalini form)
[Basso 2024], taken to represent the forward and reflected waves:

  g(t; a, μ, σ, α) = a · exp(−z²/2) · [ 1 + erf( αz / √2 ) ],   z = (t − μ)/σ         (2)

  ŷ(t) = g(t; a₁, μ₁, σ₁, α₁) + g(t; a₂, μ₁ + Δμ, σ₂, α₂)                             (3)

Skewness is admitted because both the forward and the reflected wave rise steeply and decay
slowly, which a symmetric Gaussian cannot reproduce on both flanks [Basso 2024]. The second
component is positioned by an offset Δμ from the first rather than by an absolute time, so
that a bound can be placed directly on the arrival interval and component order is
guaranteed. Two kernels were chosen because a systematic comparison of decomposition
algorithms found two-kernel models the most robust to noise and motion artefact while
preserving morphology as well as models with more kernels [Fleischhauer 2020]; the price of
that choice is taken up in the Limitations.

The eight parameters were fitted by trust-region-reflective non-linear least squares from
eight starting points, retaining the solution of lowest residual sum of squares. Bounds
were a₁ ∈ [0.05, 2.50]; μ₁ ∈ [0.02, max(0.60T, t_pk + 0.05)] s; σ₁ ∈ [0.015, 0.30] s;
α₁ ∈ [0, 8]; a₂ ∈ [0.02, 2.00]; Δμ ∈ [0.08, min(0.60, 0.85T)] s; σ₂ ∈ [0.015, 0.35] s;
α₂ ∈ [0, 8], where T is the beat length and t_pk the time of the maximum of the normalised
beat. Skewness was restricted to be non-negative because allowing left skew degrades the
identifiability of the amplitude ratio in waveforms without a dicrotic notch. The lower
bound on Δμ prevents the two components from degenerating onto each other; the upper bound
prevents the fit from capturing the following beat.

**Acceptance of a fit.** With a tolerance of 10⁻³, a fit was accepted only if it passed all
three of the following checks. (i) No parameter lies within 10⁻³ of a bound — the lower
skewness bound of 0 is excluded, since a symmetric Gaussian is a legitimate solution rather
than a stuck one. (ii) The smaller of the two component peak heights is at least 0.02 on
the normalised scale. (iii) Among competing solutions whose residual sum of squares is
within 1.15× that of the retained solution and whose Δμ differs by more than 0.03 s, none
differs in reflection index by more than 0.08.

The width of the residual valley obtained by fixing Δμ and refitting the remaining
parameters was computed as a diagnostic but is **not** part of the acceptance rule: on
synthetic data the ratio of valley width to ΔT had a median of 0.21 both for beats that
converged correctly and for beats that fell into an alternative solution, so no threshold
separates them.

**Index definitions.** Because a component's peak does not coincide with μ when skewness is
non-zero, the peak time t_peak,k and height h_k were located numerically on a 4,000-point
grid over the fitting interval. The indices are

  ΔT = t_peak,2 − t_peak,1                                                            (4)

  RI = h₂ / h₁                                                                        (5)

  SI = H / ΔT                                                                         (6)

where H is subject height. RI is the ratio of peak *heights*, not of the amplitude
parameters a₂/a₁; the two differ because peak height also depends on skewness and width.
Within a case H is constant, so relative changes satisfy exactly 1 + ΔSI% = 1/(1 + ΔT%):
SI and ΔT are related reciprocally, not linearly. Regressions run on the two therefore do
not coincide (r² = 0.0412 vs 0.0449), while in rank correlation, being a monotone
transformation, only the sign changes. The models below use ΔSI%, with ΔT reported
alongside for comparability with the literature.

The definitions of "stiffness index" and "reflection index" are not consistent across the
literature. We therefore compared candidate definitions on synthetic pulses with known
ground truth **before examining any real data** and froze those above (ΔT the most robust
of five candidates, RI of three). Alternative definitions (onset-to-onset ΔT defined at 20%
of component peak height, amplitude-parameter ratio, component area ratio) and a
three-kernel decomposition were prespecified as sensitivity analyses.

**PWTT** was defined as the interval from the R wave to the pulse foot, taken as the median
over the window, after resolution of the device delay described above. Because the absolute
value contains the device delay, **only within-case changes in PWTT were analysed**; no
between-case comparison of absolute PWTT, and no comparison with published absolute values,
was made.

### 2.5 Window and case eligibility

A window was analysed only if it satisfied, in order: at least 8 beats passing the signal
quality index; at least 2 accepted pulse decompositions; at least 10 beats contributing to
PWTT; arterial pressure present for at least 50% of the window; and at least 5 reference CO
samples. A case entered the analysis if it yielded at least 12 valid windows (one for
calibration and at least 11 for evaluation). Counts of windows rejected for each reason,
and of fits failing each convergence check, were recorded for every case and are reported.

### 2.6 Primary analysis: the premise test (no reference CO)

The first window of each case is the calibration point, and the relative change of a
quantity x is Δx%(t) = (x(t) − x(1)) / max( |x(1)|, 0.05 · median|x| ). The floor of 5% of
the series median absolute value in the denominator prevents the ratio from diverging in
cases whose first value is near zero. The premise test is

  ΔPWTT%(t) = β_SI · ΔSI%(t) + β_RI · ΔRI%(t) + ε(t)                                  (7)

Relative changes are zero at the calibration point, so the prespecified estimate carries no
constant column and passes through the origin. This specification is fixed in the frozen
analysis code rather than in the prose of the analysis plan: at tag sap-v0.3 (commit
407f226, 28 August 2026) the design matrix of the premise test is built from ΔSI% and ΔRI%
alone, with no column of ones, and the denominator of r² is the sum of squares about the
mean. Both are verifiable in the archived code. The denominator of the coefficient of
determination is nevertheless the sum of squares about the mean, so this r² can fall near
or below zero; it is the prespecified statistic, and the conventional r² obtained by
refitting with an intercept is reported alongside it. We report the pooled coefficient of
determination and the coefficients with 95% confidence intervals, together with the
distribution of within-case r² values. This analysis uses no
reference CO and is therefore unaffected by the limitation described in §2.2.

**Distinguishing a weak premise from noise.** A near-zero r² can arise either because the
premise is false or because the measurements are too noisy to reveal a real relationship.
To separate these, we prespecified the lag-1 autocorrelation of PWTT, ΔT and RI across
consecutive windows within each case: measurement noise dominated series have
autocorrelation near zero, whereas a series that tracks a physiological signal retains
autocorrelation even if it is unrelated to the other variables. We additionally report the
consistency of the sign of b₁ across cases, to detect a relationship that exists but points
in opposite directions in different patients.

**Positive control.** Autocorrelation alone cannot exclude a measurement failure, because a
slow artefact or a settling gain would also be autocorrelated while carrying no vascular
information. We therefore added a positive control: a relationship that must appear if the
indices carry vascular information at all. Across cases, arterial stiffening with age
shortens the interval at which the reflected wave returns, so ΔT should decrease and SI
increase with age [Millasseau 2002]. **This prediction covers only ΔT and SI, the
timing-derived indices.** The cited study compared a stiffness index built from subject
height and the time delay between direct and reflected waves against carotid–femoral pulse
wave velocity; it makes no directional prediction for an amplitude ratio. **The positive
control is therefore applied to ΔT and SI, and the age association of RI is reported
descriptively.** We tested this by Spearman rank correlation between
patient age and the case-median ΔT, SI and RI, and, as a negative control, between case
identifier and case-median ΔT. A secondary comparison contrasted cases with and without a
preoperative diagnosis of hypertension. This analysis was added after the analysis plan was
frozen and is reported as exploratory; it does not alter any prespecified endpoint.

Because the positive control is computed across cases and uses no reference cardiac output
and no within-case change, it is independent of the primary endpoint. We therefore fixed in
advance that an index failing it would still be reported in the prespecified primary
regression, but that no conclusion would be drawn from its coefficient, on the grounds that
a null cannot be interpreted for a quantity that has not been shown to be measurable. As
reported below, ΔT passed this control. **For RI, since the control makes no directional
prediction, failing it cannot serve as the basis.** We instead used the **within-case
coefficient of variation** as the measure of stability: RI should sit between 0.2 and 0.5
on physiological grounds, yet its within-case coefficient of variation was 0.680, three
times the 0.228 of ΔT. **On that ground alone we judged that RI would be reported but that no
conclusion would be drawn from its coefficient.** Both determinations rest on the controls
and on measurement stability alone, and were made before the premise-test result was
examined.

### 2.7 Secondary analysis: accuracy against reference CO

A control estimator reproducing the published PWTT form, esSV = K₀ × (β − α·PWTT) with K₀
regressed on age, sex, height and weight, was reduced to a linear relation between the
calibration-point CO and ΔPWTT. The proposed estimator applies a multiplicative correction
to its output:

  ĈO_prop(t) = ĈO_ctrl(t) · clip( 1 + c_SI · ΔSI%(t) + c_RI · ΔRI%(t) , 0.3 , 3.0 )    (8)

The correction coefficients c were obtained within each derivation fold by origin-through
least squares on the relative residual CO_ref/ĈO_ctrl − 1. Three sets of regressors were
used: (ΔSI%, ΔRI%), (ΔMAP%), and both. Both estimators were calibrated on the first window
of each case, mimicking the clinical calibration procedure, and evaluated by case-level
5-fold cross-validation with coefficients re-estimated within each training fold.

The outcome was the percentage error of Critchley and Critchley,
PE = 1.96 · SD(ĈO − CO_ref) / mean(CO_ref), computed per case; the difference between
proposed and control was tested with a case-level bootstrap (2,000 resamples). Bland–Altman
bias and limits of agreement, and four-quadrant concordance with a 0.5 L/min exclusion
zone, are reported descriptively.

Because the manufacturer's coefficients for the commercial device are not public, this
control estimator is a reproduction of the published PWTT form and not the commercial
device itself; we refer to it throughout as a PWTT-type estimator.

### 2.8 Prespecified interpretation rules

Before analysis, we established using synthetic cohorts that a significant improvement in
the accuracy comparison **cannot** distinguish a true improvement from a spurious one
produced by a reference that tracks arterial pressure (both scenarios were significant in
3/3 replicates), whereas the premise test does distinguish them (r² 0.658 versus 0.001).
Adjustment for mean arterial pressure, and incremental-value formulations, were likewise
shown to lack discriminating power because arterial pressure and the vascular indices are
strongly collinear; these are therefore reported descriptively only and are not used to
gate interpretation.

Accordingly it was fixed in advance that an improvement in the accuracy comparison would
**not** be interpreted as improved CO accuracy unless the premise test showed that the
vascular indices explain a significant part of PWTT variation; otherwise it would be
described only as improved agreement with the FloTrac-family reference. Conversely, if the
premise held but accuracy did not improve, the conclusion would be that the premise is
sound but this form of correction is inadequate.

### 2.9 Sensitivity analyses

Alternative index definitions (§2.4); three-kernel decomposition; ensemble noise target
varied to 0.002 and 0.004; signal quality threshold varied; the non-FloTrac subset (16
cases) analysed separately; and exclusion of the 15 cases used during pipeline development.
The variants requiring re-extraction were computed by a separate program that re-ran the
frozen decomposition from the raw waveforms on the same windows as the primary analysis,
taking PWTT, heart rate, pressure and reference CO from the primary run; a re-run under
identical definitions was included as a check that this harness reproduces the primary
indices.

### 2.10 Exploratory analyses added after the plan was frozen

Three analyses were added after the confirmatory run and are reported as exploratory; none
alters a prespecified endpoint. (a) *Association with systemic vascular resistance.* In the
204 cases with a resistance track from the EV1000, within-case Spearman correlations of the
windowed SI, RI and mean arterial pressure with SVR were computed and summarised as medians
with a sign test across cases. SVR from this monitor is (MAP − CVP)/CO with CO taken from
the arterial waveform, so it is partly circular and was used descriptively. (b)
*Decomposition of PWTT at the arterial line.* PWTT was split at the radial pressure
upstroke into T1 (R wave to radial upstroke: pre-ejection period plus central transit) and
T2 − T1 (radial upstroke to the photoplethysmographic foot: distal transit plus the
constant device delay), with a measurability gate fixed in advance (lag-1 autocorrelation of
Δ(T2 − T1) ≥ 0.30 and within-case coefficient of variation ≤ 0.50). The premise regression
was repeated with Δ(T2 − T1) as the dependent variable, which excludes the pre-ejection
period by construction, and the within-case variance of ΔPWTT was decomposed into the two
terms. (c) *Construct validity in silico.* The frozen decomposition was applied to the
digital photoplethysmogram of the 4,374 virtual subjects of the Pulse Wave Database
[Charlton 2019], a validated one-dimensional model population spanning six age decades in
which aortic diameter, heart rate, ejection duration, mean pressure, pulse wave velocity and
stroke volume are each varied over three levels in a full factorial design, and in which
aortic pulse wave velocity, peripheral resistance and the onset time of the pulse at every
site are known exactly. Because pulse wave velocity and ΔT both change with age, the
primary test was the Spearman correlation within each age group, with a criterion fixed
before the data were examined: an association was accepted if the correlation carried the
predicted sign in every age group and its median absolute value was at least 0.3. Main effects of each varied factor and the true transit times from the onset-time table
were reported descriptively. To separate a limitation of the decomposition from a limitation
of photoplethysmographic morphology in general, the same criterion was applied to the
fiducial-point-derived indices distributed with the database — the interval between the systolic
and diastolic peaks, the stiffness and reflection indices, the augmentation index, the
second-derivative ageing index and the model's own pulse transit time — which are computed
by the database's authors from the identical waveforms. Subjects, waveforms, ground truth,
age strata and criterion are therefore shared, and the only difference is how the index is
extracted. (d) *Premise test repeated with a construct-valid, identifiable
index.* After the confirmatory run, the premise regression was repeated using the only index
that both correlated most strongly with truth in the virtual population and met a
prespecified identifiability criterion on recorded anaesthetic monitor waveforms (median
detection rate ≥ 0.70 and lag-1 autocorrelation ≥ 0.30 in a separate 20-case series): the
upstroke amplitude ratio Am_b/Am_p1 [Hellqvist 2024]. It was computed on the same 862 cases,
the same 60-second windows and the same quality criteria as the main analysis, directly from
the first and second derivatives without any curve fitting. The design and the rules for
reading the result were fixed in a dated document before the analysis was run. Because it is
computed on the windows the main analysis accepted, windows that the main analysis rejected
at the decomposition convergence audit are not recovered.

### 2.11 Software

Analyses were performed in Python 3.9.6 with NumPy 2.0.2, SciPy 1.13.1 and pandas 2.3.3.
All analysis code, the frozen analysis plan and the synthetic-data verification suite are
available at https://github.com/nobumitsu-3141/ppg-pda-analysis and archived at
doi:10.5281/zenodo.22676038 (concept DOI, resolving to the latest version; the analyses
used v1.0.0); the freeze of the plan carries an earlier
timestamp at doi:10.5281/zenodo.22167118. The scripts that carry the confirmatory and
exploratory analyses (23 of 37) run their verification suite offline under --selftest; the
data-acquisition, figure and table scripts operate on downloaded or already-extracted data.

---

## 3. Results

> **Pending the 874-case confirmatory run.** Structure and the pilot values (n = 15) are
> given so that the narrative can be assembled immediately when the run completes.

### 3.1 Cohort and data yield

Of the 874 eligible cases, 862 (98.6%) yielded at least 12 valid windows and entered the
analysis, contributing 161,737 sixty-second windows (Figure 1). The reference CO device in
the analysed cases was EV1000 in 545, Vigileo in 301, CardioQ in 11 and Vigilance II in 5;
846 of 862 (98.1%) references were therefore arterial-waveform-derived, and the 16 cases
with an independent reference are reported descriptively only. Of 232,451 windows examined,
70% passed all quality gates; the leading reasons for rejection were failure to reach the
ensemble noise target (12%), missing reference CO (6%), missing arterial pressure (4%),
fewer than two accepted decompositions (3%) and an insufficient number of quality-passing
beats (2%). Of 2,692,082 fitted segments, 72% passed all convergence checks; 22% were
rejected for a parameter at its bound, 8% for a competing solution and under 0.1% for
component collapse (categories overlap). Patient, procedure and recording
characteristics are shown in Table 1: the cohort was middle-aged to elderly (median 61
years), predominantly ASA 1–2 general-surgical and thoracic patients under general
anaesthesia, with long recordings (median 257 minutes) yielding a median of 177 valid
windows per case.

**Table 1. Characteristics of the analysed cases (n = 862).**

| Characteristic | Value |
|---|---|
| Age, years | 61 (51–70) |
| Male sex | 517 (60%) |
| Height, cm | 163 (157–170) |
| Weight, kg | 61 (54–69) |
| Body mass index, kg/m² | 23.0 (20.7–25.2) |
| ASA physical status 1 / 2 / 3 / ≥4 | 158 (18%) / 531 (62%) / 148 (17%) / 8 (1%) — not recorded 17 (2%) |
| Preoperative hypertension | 328 (38%) |
| Preoperative diabetes | 119 (14%) |
| Emergency surgery | 76 (9%) |
| Department: general surgery / thoracic / urology / gynaecology | 615 (71%) / 215 (25%) / 28 (3%) / 4 (<1%) |
| Commonest procedure types | hepatic 149 (17%); transplantation 125 (15%); biliary–pancreatic 122 (14%); major resection 109 (13%) |
| Anaesthesia | general, 862 (100%) |
| Recording length, min | 257 (182–338) |
| Valid 60-s windows per case | 177 (104–255) |
| Photoplethysmographic channel apparent lag, ms | 660 (644–676) |
| Reference CO device: EV1000 / Vigileo / CardioQ / Vigilance II | 545 (63%) / 301 (35%) / 11 (1%) / 5 (1%) |

Values are median (IQR) or n (%).

### 3.2 Measurement quality

Consecutive-window lag-1 autocorrelation was +0.75 for PWTT, +0.50 for the ΔT-based index
and +0.43 for RI, indicating series that track reproducible physiology rather than noise
(Table 3, Figure 3b). In the exploratory positive control (849 adults, Figure 3a), ΔT
shortened with age
(ρ = −0.197, 95% CI −0.261 to −0.131, p < 0.0001) and was shorter in patients with
preoperative hypertension (median 259 versus 267 ms). RI showed no association with age
(ρ = +0.041, p = 0.23), but since the cited study makes no directional prediction for an
amplitude ratio **this is descriptive**. The judgement on RI rests on its **within-case
coefficient of variation of 0.680** (ΔT: 0.228), far too large for a ratio that should sit
between 0.2 and 0.5, and it was accordingly judged uninterpretable in this signal source
(§2.6). The negative-control association between case identifier and ΔT was ρ = +0.078
(95% CI +0.011 to +0.145), essentially unchanged after adjustment for age, heart rate,
mean arterial pressure and reference device (ρ = +0.072). It is therefore not attributable
to demographic or measured case-mix drift (case identifier was uncorrelated with age,
ρ = −0.025); its origin is unidentified, but it carries an order of magnitude less
variance than the age association (0.6% versus 3.9%) and does not affect the
interpretation of the positive control. We report it for completeness.

### 3.3 Primary analysis — premise test

Across 161,737 windows in 862 cases, the vascular indices explained essentially none of the
within-case variation in PWTT: the prespecified pooled estimate, fitted through the origin
because all relative changes are zero at calibration, was r² = 0.000, with coefficients of
−0.027 per ΔSI% and −0.003 per ΔRI% (Table 2, Figure 2). Refitting with an intercept — the
conventional coefficient of determination, reported here as an exploratory sensitivity
analysis — gave r² = 0.044. The reflection index contributed almost nothing to either:
omitting it left r² at 0.041 and shifted the stiffness coefficient only from −0.024 to
−0.022, so the conclusion does not depend on including an index whose validity we could not
establish (§3.2). The within-case coefficient on ΔSI% carried the sign predicted by
the vascular hypothesis in 78% of cases — far beyond chance in 862 cases — but its
magnitude was negligible: a 10% change in the stiffness index predicted a 0.27% change in
PWTT, against within-case PWTT excursions of several percent. The median within-case r² was
0.101. The vascular component of intraoperative PWTT variation is therefore directionally
detectable but roughly two orders of magnitude too small to be useful for correction.

### 3.4 Secondary analysis — accuracy

The vascular correction did not improve agreement with the reference: median percentage
error was 26.9% for the control PWTT-type estimator and 27.2% for the corrected estimator,
a difference of +0.2 percentage points (95% CI +0.1 to +0.4) — that is, the correction
produced a small but statistically significant worsening, consistent with adding noise
rather than information. Bland–Altman bias of the corrected estimator was −0.07 L/min
(limits of agreement −3.28 to +3.14 L/min) and four-quadrant concordance (0.5 L/min
exclusion zone) was 0.56 (Table 4, Figure 4). Descriptively, percentage error was flat
across adjustment sets (control 26.9%; with blood pressure 27.0%; with vascular indices
27.2%; with both 27.1%), as prespecified these comparisons carry no interpretive weight
(§2.8). The prespecified futility criterion was met.

### 3.5 Sensitivity analyses

Excluding the 15 cases used during pipeline development left every conclusion unchanged
(847 cases, 158,445 windows: premise r² = 0.005 with coefficients −0.028 and −0.003;
within-case r² median 0.102 with 78% sign consistency; percentage error 26.9% in both
arms, difference +0.2 percentage points, 95% CI +0.1 to +0.3). In the 16 cases with a
reference independent of the arterial pressure waveform, results are reported
descriptively in Table 5. Aggregating windows to 5 and 20 minutes reduced percentage
error in both arms, as expected when comparing monitors with differing response times
(control 26.9% at 60 s; 23.9% at 5 min, 844 cases; 21.5% at 20 min in the 606 cases with
sufficient data), but the correction improved accuracy at no aggregation level (difference
−0.1 points, 95% CI −0.2 to +0.1 at 5 min; −0.2, 95% CI −0.5 to +0.0 at 20 min) —
the accuracy null is therefore not an artefact of the 60-second window. Adding heart rate
to the premise regression raised the explained fraction from 0.000 to 0.077 while leaving
the vascular coefficients essentially unchanged (ΔSI% −0.020, ΔRI% −0.003, ΔHR% −0.057):
within-case PWTT variation tracks heart rate, not the vascular indices, and the vascular
null is not produced by heart-rate confounding.

Nine variants requiring re-extraction were computed on the same windows (Table 6): the two
alternative amplitude definitions and the onset-to-onset timing definition prespecified in
§2.4, a three-kernel decomposition, the ensemble noise target moved to 0.002 and to 0.004,
and the signal-quality threshold moved to 5% and to 20%. Re-running the frozen
decomposition from the raw waveforms under identical definitions reproduced ΔT and RI
exactly in all 161,737 windows, so the remaining rows differ from the primary analysis
only by the definition that was changed. Across the nine variants the vascular-explained fraction of ΔPWTT ranged
from −0.051 to 0.005 and the coefficient on ΔSI% from −0.004 to −0.032, and the correction
worsened percentage error in every one (difference +0.1 to +0.4 points, all 95% CIs
excluding zero). Neither a third kernel nor either alternative amplitude definition raised
the explained fraction. The two variants that discard the noisiest windows — the stricter
noise target, retaining 144,112 of 161,737 windows, and the stricter quality threshold,
retaining 137,600 — did not raise it either (0.005 and −0.036), so the null is not produced
by dilution from measurement noise. The two variants whose ΔSI% coefficient differed
materially, onset-to-onset timing and the three-kernel fit, were also the two with the
lowest within-case sign consistency (61% and 67%, against 78% in the primary analysis),
consistent with a noisier estimate of the same quantity rather than a different one.

**Table 6. Sensitivity of the premise test and of accuracy to index definition, kernel
count and pre-processing thresholds.**

| Variant | Cases | Windows | Premise r² | β ΔSI% | β ΔRI% | Sign consistency | ΔPE, points (95% CI) |
|---|---|---|---|---|---|---|---|
| Primary analysis, recomputed on the same windows | 862 | 161,737 | 0.000 | −0.027 | −0.003 | 78% | +0.2 (+0.1 to +0.3) |
| Re-extraction, identical definitions | 862 | 161,737 | 0.000 | −0.027 | −0.003 | 78% | +0.2 (+0.1 to +0.3) |
| Onset-to-onset ΔT, 20% of component peak height | 862 | 161,297 | −0.041 | −0.004 | −0.004 | 61% | +0.1 (+0.0 to +0.2) |
| Amplitude-parameter ratio a₂/a₁ | 862 | 161,737 | −0.003 | −0.029 | −0.002 | 77% | +0.2 (+0.1 to +0.4) |
| Component area ratio | 862 | 161,737 | −0.012 | −0.032 | −0.001 | 81% | +0.2 (+0.1 to +0.3) |
| Three-kernel decomposition | 858 | 153,249 | −0.051 | −0.010 | −0.004 | 67% | +0.3 (+0.2 to +0.4) |
| Ensemble noise target 0.002, stricter | 852 | 144,112 | 0.005 | −0.024 | −0.003 | 77% | +0.2 (+0.1 to +0.3) |
| Ensemble noise target 0.004, looser | 862 | 161,542 | −0.001 | −0.029 | −0.002 | 78% | +0.2 (+0.1 to +0.4) |
| Signal-quality threshold 5%, stricter | 852 | 137,600 | −0.036 | −0.023 | −0.002 | 75% | +0.4 (+0.3 to +0.5) |
| Signal-quality threshold 20%, looser | 862 | 161,297 | 0.004 | −0.028 | −0.003 | 78% | +0.2 (+0.1 to +0.4) |

Premise r² is the through-origin explained fraction of within-case ΔPWTT% from ΔSI% and
ΔRI% (§2.6); it can be negative because the model carries no intercept. β are the pooled
coefficients. Sign consistency is the proportion of cases whose within-case ΔSI%
coefficient carries the majority sign. ΔPE is the proposed minus the control percentage
error in percentage points, so a positive value favours the control; control percentage
error ranged from 26.5% to 27.0% across variants. Rows 1 and 2 differ only in that row 2
re-ran the decomposition from the raw waveforms.

### 3.6 Exploratory analyses added after the plan was frozen

**Systemic vascular resistance.** In 204 cases the within-case correlation of RI with SVR
had a median of +0.098 (sign test p = 1.7 × 10⁻⁵), in the predicted direction, whereas SI
was unrelated to SVR (median +0.049, p = 0.14); mean arterial pressure correlated at +0.334
(p = 4.8 × 10⁻¹⁵).

**Decomposition of PWTT.** The distal term passed the measurability gate (lag-1
autocorrelation +0.654, coefficient of variation 0.037, no within-case drift). The interval
from the R wave to the radial upstroke, T1, was 180 ms (IQR 166–192). Δ(T2 − T1), which
contains no pre-ejection period, was explained by ΔT no better than ΔPWTT was (r² = 0.008;
within-case ρ +0.122 against +0.216 for ΔPWTT), so the null of the primary analysis is not
produced by opposing movements of the pre-ejection period and transit time. Within cases the
distal term accounted for most of the variance of ΔPWTT (r² 0.534 against 0.073 for ΔT1;
both terms together 0.977), with the caveat that any timing error in the
photoplethysmographic foot falls entirely in the distal term. Indices derived from the
arterial pressure waveform (diastolic decay time constant and maximal dP/dt) explained ΔPWTT
no better (r² = 0.015).

**Construct validity in silico.** Of 4,374 virtual subjects, 4,036 (92%) passed the
convergence checks. Within age groups ΔT correlated with aortic pulse wave velocity in the
predicted, negative direction in all six groups but weakly (ρ −0.14, −0.12, −0.09, −0.31,
−0.52 and −0.61 from age 25 to 75; median |ρ| 0.22), below the prespecified 0.3; RI
correlated with peripheral resistance positively in five of six groups (median |ρ| 0.21;
+0.49 at age 25 falling to −0.01 at 75). Neither criterion was met. In the factorial
design, pulse wave velocity had the largest main effect on ΔT (−17% from −1 SD to +1 SD),
but heart rate (−11%, ρ −0.54) and aortic diameter (−13%) were of the same order, and the
response to pulse wave velocity was not monotonic: with every other factor at baseline, ΔT
was 332, 353 and 251 ms at −1 SD, baseline and +1 SD, and RI 0.325, 0.254 and 0.647,
consistent with a change in which wave the second component captures. RI was moved most by
heart rate (−40%) and aortic diameter (+33%). Three-kernel variants performed worse. The
true transit time from the aortic root to the finger, taken from the model's onset times,
was 96 ms (5th–95th percentile 66–120) and correlated with aortic pulse wave velocity at
ρ −0.99 within age groups, whereas ΔT correlated with that same true transit time at only
+0.19. The true radial-to-finger transit was 8 ms (4–16 ms) across the whole population.

Applying the same criterion to the fiducial-point-derived indices distributed with the database
separated the two readings. The fiducial-point interval between the systolic and diastolic peaks
correlated with aortic pulse wave velocity at a median |ρ| of 0.71 (negative in all six age
groups), the fiducial-point stiffness index at 0.71, the second-derivative ageing index at 0.89
and the fiducial-point reflection index with peripheral resistance at 0.50 — all meeting the
criterion that the decomposition-derived indices failed. The model's own pulse transit time,
included as a control on the comparison itself, gave 0.57. The fiducial-point augmentation index
did not meet it (0.14). In the factorial design the fiducial-point interval was about twice as
sensitive to pulse wave velocity as the decomposition-derived one (−31% against −17% from
−1 SD to +1 SD) and about a quarter as sensitive to heart rate (−2.6% against −10.9%).
Descriptively, the fiducial-point reflection index tracked pulse wave velocity (0.69) more
closely than peripheral resistance (0.50).

*Premise test with a construct-valid index.* The index was obtained in 862 cases and 161,638
windows (0.1% loss against the 161,737 of the main analysis). Recomputed on those same
windows the main-analysis values reproduced the confirmatory run (0.044 with an intercept,
0.000 through the origin; mean arterial pressure alone 0.139). The upstroke amplitude ratio
explained 0.0002 of within-case PWTT variation with an intercept (−0.105 through the origin),
with a coefficient of −0.030 per 1%. The within-case sign agreed with prediction in 51% of
cases, which is chance level, and the median within-case rank correlation was −0.003. Its
lag-1 autocorrelation between consecutive windows was 0.394, comparable to the stiffness
index (0.496) and the reflection index (0.431). Under the prespecified reading, changing the
index does not make within-case PWTT variation explicable.

---

## 4. Discussion

**Principal finding.** In 862 surgical cases, the within-case variation of pulse wave
transit time was largely not explained by the concurrently measured, and independently
validated, photoplethysmographic index of arterial stiffness (ΔT). The relationship was estimated
precisely rather than merely failing to reach significance: with 862 cases contributing
161,737 windows, the vascular-explained fraction of PWTT variation was 0.000, and the
coefficient on the stiffness index, though directionally consistent with the vascular
hypothesis in 78% of cases, corresponds to a 0.27% change in PWTT per 10% change in the
index. This is a precise estimate of a negligible effect, not an absence of evidence
[Altman & Bland 1995].

**For the timing index, the null is not a measurement failure.** This interpretation must be
excluded before any physiological reading is permitted, because the photoplethysmographic
channel of this database is a processed monitor output rather than a research-grade signal.
Three independent lines of evidence exclude it for ΔT. First, a positive control: across
cases, the component interval varied with age in the expected direction (ρ = −0.197,
95% CI −0.261 to −0.131), as established for digital pulse contour analysis [Millasseau
2002], and was shorter in patients with a preoperative diagnosis of hypertension, while a
negative control variable carried an order of magnitude less variance (§3.2). The estimate
was computed in adults and was materially unchanged when children were included. The pipeline therefore detects a vascular signal where
one is known to exist. Second, ΔT retained substantial autocorrelation between consecutive
windows, indicating a series that tracks a reproducible physiological quantity. Third, index
identifiability was established on synthetic pulses with known ground truth before any
patient data were examined, and per-beat identifiability, convergence and exclusion rates
are reported in full (Table 3). For ΔT the relationship with PWTT is absent, not obscured.

**For the reflection index, validity could not be established, and its result is therefore
uninformative.** The basis is **measurement stability**. A ratio that should sit between
0.2 and 0.5 on physiological grounds instead varied within cases with a coefficient of
variation of 0.680 — threefold that of ΔT (0.228) — while correlating less strongly with
mean arterial pressure than ΔT did: it behaved as noise rather than as physiology. Across
849 adults it also showed no association with age (ρ = +0.041, p = 0.23), but **the cited
study predicts a direction for timing-derived indices, not for an amplitude ratio, so this
is supporting description only.**

To identify what class of signal processing could produce this specific pattern, we applied
candidate operations to synthetic pulses of known composition. Uniform gain normalisation,
whether per beat or per record, left both indices exactly intact, as it must: the reflection
index is a ratio of two component heights within one beat and is invariant to any scaling of
that beat. Gentle high-pass filtering (0.3–0.5 Hz) also preserved both, and stronger
high-pass filtering degraded the fit itself so that beats were rejected rather than
mismeasured. Only a gain that varies *within* the beat, on a timescale comparable to the
separation of the forward and reflected components, reproduced the observed pattern:
with a 0.25 s time constant the reflection index was displaced by +61% while ΔT moved
by only −9 ms. A time constant of 1 s — slower than one beat — had no effect at all.
The pattern we observe is therefore consistent with a fast, within-beat gain adjustment in
the monitor's processing chain, and not with the simple amplitude normalisation usually
invoked. We emphasise that this narrows the candidate mechanism; it is not evidence that
this particular database applies such processing. We therefore report
the reflection index but draw no conclusion from it: its null is a statement about what can
be recovered from this signal source, not about physiology. This independently reproduces
the finding of Couceiro and colleagues, whose amplitude-derived indices failed against every
vascular reference they tested [Couceiro 2015]. **This decision rests on the positive
control alone, which is independent of the primary endpoint, and was made without reference
to the premise-test result; the prespecified primary analysis was not altered.**

**What the indices measure, tested against ground truth.** The positive control shows that
ΔT carries vascular information, but not how much of ΔT is vascular. We therefore applied
the frozen decomposition to a virtual population in which the quantities the indices are
meant to index are known exactly [Charlton 2019] (§3.6). On ideal waveforms with no monitor
processing, ΔT correlated with aortic pulse wave velocity within age groups at a median of
only 0.22 and with the true aortic-root-to-finger transit time at 0.19, while that transit
time itself tracked pulse wave velocity at 0.99. ΔT is sensitive to stiffness in the
predicted direction but not specific to it: heart rate and aortic diameter moved it as much,
and its response to stiffness was discontinuous, which is the behaviour expected when the
second component switches between waves [Epstein 2014]. The null of the primary analysis is
therefore not an artefact of the monitor's photoplethysmographic channel; these indices do
not track their targets even when the signal is perfect. The alternative reading, that the null arises from
the construct-invalidity of the index itself, can be tested directly, and was. Repeating the
premise test with the index that correlated most strongly with truth in the virtual
population (0.84) and was the only one to meet the identifiability criterion on recorded
monitor waveforms lowered the explained fraction from 0.044 to 0.0002 and removed the
within-case consistency of sign (80% to 51%). Attenuation by measurement error does not
account for this: taking the lag-1 autocorrelation as an index of reliability, dilution
predicts a factor of 0.394/0.496 = 0.79, whereas the observed ratio was 0.0045. Improving the
construct validity of the index therefore does not make within-case PWTT variation
explicable. The weak association that remains for the stiffness index survives adjustment for
heart rate (coefficient −0.027 to −0.020) yet is not reproduced by an index of established
construct validity; whether it is a faint genuine vascular component, or a shared dependence
of decomposition-derived ΔT and PWTT on the timing of the pulse foot, cannot be decided from
these data.

The same experiment, however, locates that failure precisely, because the database also
provides fiducial-point-derived indices computed from the identical waveforms. Those met the
criterion the decomposition failed: the systolic-to-diastolic peak interval reached 0.71
against pulse wave velocity, the second-derivative ageing index 0.89, and the fiducial-point
reflection index 0.50 against peripheral resistance. With subjects, waveforms, ground truth
and criterion held fixed, the only difference is the extraction, so the limitation is specific to the two-kernel decomposition as implemented here and not to
photoplethysmographic morphology in general. The factorial main effects show where the
difference lies: the fiducial-point interval was twice as sensitive to pulse wave velocity and a
quarter as sensitive to heart rate, consistent with a fitted component whose position is
constrained by the length of the beat rather than by the arrival of a wave. Two qualifications keep this from being read as a general ranking of the two approaches.
First, the virtual waveforms are noise-free and carry a clear dicrotic notch and diastolic
peak, which is the condition in which fiducial-point detection is easiest; decomposition is
advocated precisely for waveforms in which those features are absent, so its claimed
advantage cannot appear in this comparison, and whether fiducial-point features are identifiable
in a processed monitor photoplethysmogram is an open question and the natural next
experiment. Second, our decomposition is one implementation among many: it uses two kernels
with no diastolic decay term and constrains both components to positive skew, choices made
to preserve amplitude identifiability in monitor waveforms without a visible notch, and
those same choices let the second kernel absorb the diastolic downslope, whose duration
scales with the cardiac cycle — which is consistent with the heart-rate confounding we
observe. A decomposition with more components and an explicit rule for identifying the
forward and reflected waves, as used elsewhere [Couceiro 2015], was not tested here. What
the comparison establishes is therefore that the information is present in the waveform and
that this decomposition does not recover it, not that decomposition as a class cannot. Finally, the weak but significant association of RI with systemic vascular
resistance in the clinical data (§3.6) should not be read as validation of RI as a
resistance index: in silico even the fiducial-point reflection index tracked pulse wave velocity
(0.69) more closely than resistance (0.50).

**Physiological interpretation.** Our result is what the mechanistic literature predicts
rather than an anomaly. PWTT measured from the R wave contains the pre-ejection period in
addition to arterial transit time [Ochiai 1999], and this cardiac term is not a small
correction: transit time measured from the electrocardiogram has been judged unreliable as a
marker of purely vascular function for this reason [Payne 2006]; pulse arrival time fails in
settings where true transit time succeeds [Zhang & Mukkamala 2011]; the decoupling between
them is intervention- and subject-dependent [Balmer 2018]; the pre-ejection period varies by
tens of milliseconds under sympathetic activation [Pilz 2023]; and it can move opposite to
vascular transit time in the same subject [Djupedal 2022], which is a direct mechanism for a
large change in PWTT accompanied by no change in vascular indices. Most pointedly, the
manufacturer's own investigators reported that the pre-ejection period accounted for
approximately half of the change in PWTT [Sugo 2012]. The present study confirms the first
half of that mechanism — the vascular indices do not explain PWTT — but not the second: when
PWTT was split at the radial line (§3.6), the term containing the pre-ejection period
accounted for only 7% of its within-case variance, and removing it did not unmask a vascular
relationship. In this intraoperative cohort the dominant variation lay in the distal,
photoplethysmographic segment. Either way, the result explains why improving the
calibration procedure alone does not repair the method [Smetkin 2017]. Consistent with
it, when heart rate — a marker of chronotropic and autonomic state — was added to the
primary regression as an exploratory analysis, it alone explained 7.7% of within-case PWTT
variation where the vascular indices explained none, and their coefficients were unchanged
by its inclusion.

**Relation to previous work.** The strategy of correcting a transit-time estimate with a
photoplethysmography-derived vascular index is not new: it has been applied to cuffless
blood pressure with measurable benefit [Ding 2016], and photoplethysmographic morphology has
been combined with pulse arrival time in this same database [Yang 2021]. What is new here is
the target — the stroke-volume calibration constant of a transit-time cardiac output method,
a question posed by the manufacturer's group and left open [Ishihara & Tsutsui 2014] — and
the reference-free test of its premise. It should also be noted that the physical
attribution of the second decomposition component to peripheral reflection is not secure
[Epstein 2014], and that decomposition-derived indices have previously performed only
modestly against vascular references, amplitude ratios worst of all [Couceiro 2015]; our
prior probability of success was therefore low, and the contribution of this work is to
convert that expectation into a measured bound.

**How much vascular signal is there to capture?** Our result bounds what *these indices*
achieve, not what any vascular marker could. Two exploratory observations delimit the
remaining space. First, mean arterial pressure — a well-measured haemodynamic variable that
is itself pressure-dependent-stiffness related through the Bramwell–Hill relation — alone
explained 0.139 of within-case PWTT variation, roughly three times the vascular indices, and
heart rate a further 0.081. A vascular contribution to intraoperative PWTT therefore exists
and is measurable; it is simply not what the pulse-decomposition indices captured. Second,
all measured variables together (indices, pressure, heart rate) explained 0.196, whereas the
lag-1 autocorrelation of PWTT (+0.75) implies a reproducible, non-noise component of roughly
0.56–0.75. A substantial reproducible fraction of PWTT variation therefore remains
unexplained by anything we measured. Splitting PWTT at the radial line (§3.6) located most
of that variance in the distal segment, whose true physiological range in a virtual
population is only 4–16 ms against a within-case standard deviation of about 18 ms here,
so it is more plausibly a property of how the photoplethysmographic foot is timed than of
the vasculature or the heart. The honest statement is not that vascular correction has no room, but that the room
lies outside what single-site photoplethysmographic decomposition indices reach.

**Implications.** The structured, vascular-state-related error of transit-time cardiac
output estimation is well documented, and correcting the calibration constant with a
vascular marker is the intuitive response to it. Our results bound what that strategy can
achieve from single-site photoplethysmography: if the quantity to be corrected does not
covary with the correction variable, the correction cannot work regardless of how well the
index is measured. Notably, even mean arterial pressure — which explains three times more of
the PWTT variation — did not improve accuracy when added to the estimator (§3.4), so a
larger explained fraction alone does not guarantee a usable correction. More promising directions are those that address the measurement of transit time itself —
the timing of the photoplethysmographic foot and the device delay that precedes it — or
that abandon drift modelling in favour of more frequent recalibration. Measuring the cardiac
term directly, by phonocardiography, impedance cardiography or bioreactance, remains worth
testing, but this cohort does not support it as the dominant term.

**A caution for users of open waveform databases.** The photoplethysmographic channel of
this database lags the electrocardiogram by a large, case-specific and near-constant
interval — in this cohort a case-level median of 660 ms with a tight interquartile range
(644–676 ms). This apparent lag comprises the device's processing delay plus the
physiological transit time. Using the arterial line to separate them, the interval from the
R wave to the radial pressure upstroke was 180 ms (IQR 166–192), a value consistent with a
pre-ejection period of 80–120 ms plus an aortic-to-radial transit of 60–100 ms; the
remaining 479 ms (IQR 464–492) is the device processing delay plus the radial-to-finger
transit, which is 4–16 ms in a validated virtual population (§3.6); the processing delay
itself is therefore of the order of 460–475 ms. Device-induced timing artefacts of this class have been documented at
scale elsewhere and are not a new phenomenon [Ruffolo 2025]; what we add is their
quantification and correction in this specific, widely used resource, where waveform
synchronisation has been assumed adequate and that assumption has been propagated into a
derived benchmark dataset [Wang 2022]. Because the delay exceeds the cardiac cycle at
higher heart rates, transit times computed without accounting for it are aliased rather than
merely offset, and beat segmentation anchored to the R wave selects the wrong part of the
pulse. Any study combining these channels must estimate and resolve it.

**Limitations.** First, the reference CO available in this database is predominantly derived
from the arterial pressure waveform (846 of 862 analysed cases, FloTrac family) and is not an
independent standard; this affects the secondary accuracy analysis but not the primary
premise test, which uses no reference CO. The independent references available — pulmonary
artery thermodilution in 5 cases and oesophageal Doppler in 11 — are too few for inference
and are reported descriptively only. Second, the secondary accuracy analysis used 60-second
windows, whereas comparison of CO monitors with differing response times has been argued to
require moving averages of 20–30 minutes [Sugo & Ochiai 2025]; we therefore repeated it at
5 and 20 minutes as a sensitivity analysis; percentage error fell with averaging in both
arms, but the correction improved accuracy at no aggregation level (§3.5), and note that this consideration does not
apply to the beat-level, reference-free primary analysis. Third, the study is a
retrospective analysis of a single database from a single centre, without a controlled
vasomotor challenge; the cohort characteristics are reported in full so that transportability
can be judged. Fourth, the manufacturer's coefficients are not public, so the control
estimator reproduces the published PWTT form rather than the commercial device. Fifth, component assignment in a two-kernel decomposition is not guaranteed to correspond
to distinct physical waves [Epstein 2014]; a three-kernel decomposition, prespecified as a
sensitivity analysis, did not raise the explained fraction (Table 6), and in silico the
response of both indices to stiffness was discontinuous (§3.6). More specifically, the
comparison of decomposition algorithms we relied on for the choice of two kernels also
reports that two kernels condense all reflections into one component and thereby preclude
assessing the relationship between the systolic component and specific reflections
[Fleischhauer 2020]; our indices are such a relationship, so the model order was not
well matched to the quantity we set out to measure. Related choices point the same way:
the model carries no term for the diastolic decay, so a component must absorb it, and a
data-driven comparison of basis functions on 7805 real pulses selected a three-component
Gamma model — whose exponential tail can represent that decay — far more often than any
two-component model [Tigges 2017]. Nor did our convergence checks test whether the fitted
components landed on the intended waveform fiducial points, a criterion argued to be essential
because vascular indices depend on fiducial-point positions rather than on overall fit quality
[Wang 2013]. Sixth, stiffness and reflection indices were
developed largely as resting measures, and their extrapolation to acute intraoperative
change is itself an assumption. Seventh, the three analyses in §3.6 were added after the plan
was frozen and are exploratory; the virtual population models healthy ageing without
anaesthesia or vasoactive drugs, so it tests how the indices are constructed, not how they
behave intraoperatively. Relatedly, this study tested decomposition-derived indices, which
were prespecified; the in-silico comparison indicates that a fiducial-point-derived index might
have behaved differently, and our findings should not be read as a statement about
photoplethysmographic vascular indices in general. Nor should the in-silico comparison be
read as a general ranking of decomposition against fiducial-point analysis: the virtual waveforms
are noise-free with clearly visible fiducial points, the condition least favourable to
decomposition, and our two-kernel implementation was configured for the opposite case. Finally, the photoplethysmographic channel is a processed monitor
output. Timing information demonstrably survives that processing, as the positive
control shows, but amplitude information appears not to: the reflection index failed the
same control, so this study can say nothing about whether wave reflection tracks PWTT.
Testing that would require a photoplethysmographic source with documented gain behaviour.

**Conclusion.** In a large perioperative waveform database, beat-to-beat variation in pulse
wave transit time was largely unexplained by a photoplethysmography-derived index of
arterial stiffness, despite evidence that this index was measured well enough to detect a
known vascular signal; the corresponding amplitude-derived index could not be validated in
this signal source. Tested against ground truth in a virtual population, neither
decomposition-derived index tracked its intended target closely enough to serve as a
correction variable, whereas fiducial-point-derived indices of the same waveforms did; the limitation therefore lies in
what this decomposition extracts rather than in the monitor's signal or in
photoplethysmographic morphology as such. Whether a different decomposition would recover
the same information was not tested. Dynamic correction of the calibration
constant of transit-time cardiac output estimation using these indices has little room to
work. Two directions follow, and both are testable in existing data: whether fiducial-point
features survive in a processed monitor photoplethysmogram well enough to repeat the premise
test, and the measurement of transit time itself, since most of the intraoperative variation
lay in the distal photoplethysmographic segment, whose true physiological range is far too
narrow to account for it.

## Figure legends

**Figure 1. Flow of cases.** Cases in the source database, the four track requirements
applied in turn, the eligible cohort, and the cases excluded at analysis with the reason
and count for each step.

**Figure 2. Premise test.** (a) One representative case: relative change from the
calibration point in PWTT and in each vascular index, against time. (b) Distribution of
the within-case coefficient of determination across cases, with the median marked. Windows
falling outside the plotted range are counted in the corner of each panel.

**Figure 3. Measurement quality and positive control.** (a) Positive control: component
interval ΔT against age across cases, with the rank correlation and the number of cases.
(b) Reproducibility: distribution of the lag-1 autocorrelation between consecutive windows
for PWTT and for each index.

**Figure 4. Agreement with the reference cardiac output.** Bland-Altman plots for the
control estimator and for the estimator with the calibration constant corrected, on the
same axes, with bias, limits of agreement and percentage error annotated.

Figures are produced by `analysis/scripts/07_figures.py` in the archived code.

## Statements

- **Ethics**: This study analysed only anonymised, publicly released data with no patient
  contact. The ethics committee of Goto Chuoh Hospital determined that committee review was
  not required (response dated 28 August 2026). Collection of the source database was
  approved by the Institutional Review Board of Seoul National University Hospital with
  waiver of written informed consent [Lee 2022].
- **Data availability**: VitalDB is publicly available at https://vitaldb.net .
  All analysis code, the prespecified analysis plan and the synthetic-data verification
  suite are at https://github.com/nobumitsu-3141/ppg-pda-analysis, archived at
  doi:10.5281/zenodo.22676038 (concept DOI, resolving to the latest version; the
  analyses used v1.0.0); the freeze of the plan carries an earlier timestamp at
  doi:10.5281/zenodo.22167118.
- **Funding**: None.
- **Conflicts of interest**: None declared. [[投稿前に先生ご自身の最終確認を]]
- **Author contributions**: NK designed the study, wrote the analysis code, performed
  the analysis and wrote the manuscript.


---

## References

> **照合状況（2026-08-30）**: ★印だった10件を PubMed・出版社ページ・DOIリゾルバで
> 照合済み。訂正2件: Sugo & Ochiai 2025 の誌名は BMC Biomed Eng、Basso 2024 の
> 著者は Basso G, Haakma R, Vullings R（DOI は ad9662 が正）。
> 引用形式は投稿先の規定に合わせて最終整形する。

### esCCO / PWTT法

1. Ochiai R, Takeda J, Hosaka H, et al. The relationship between modified pulse wave transit
   time and cardiovascular changes in isoflurane anesthetized dogs. J Clin Monit Comput.
   1999;15(7-8):493-501. PMID 12578047.
2. Ishihara H, Okawa H, Tanabe K, et al. A new non-invasive continuous cardiac output trend
   solely utilizing routine cardiovascular monitors. J Clin Monit Comput. 2004;18(5-6):313-20.
   PMID 15957621.
3. Sugo Y, Ukawa T, Takeda S, et al. A novel continuous cardiac output monitor based on pulse
   wave transit time. Annu Int Conf IEEE Eng Med Biol Soc. 2010;2010:2853-6. PMID 21095971.
4. Sugo Y, Sakai T, Terao M, et al. The comparison of a novel continuous cardiac output
   monitor based on pulse wave transit time and echo Doppler during exercise. Annu Int Conf
   IEEE Eng Med Biol Soc. 2012;2012:236-9. PMID 23365874.
   **← PEPがPWTT変化の約半分を占めるとした、メーカー側の報告。考察の要**
5. Yamada T, Tsutsui M, Sugo Y, et al. Multicenter study verifying a method of noninvasive
   continuous cardiac output measurement using pulse wave transit time: a comparison with
   intermittent bolus thermodilution cardiac output. Anesth Analg. 2012;115(1):82-7.
   PMID 22467885.
6. Ishihara H, Sugo Y, Tsutsui M, et al. The ability of a new continuous cardiac output
   monitor to measure trends in cardiac output following implementation of a patient
   information calibration and an automated exclusion algorithm. J Clin Monit Comput.
   2012;26(6):465-71. PMID 22854918.
7. Ishihara H, Tsutsui M. Impact of changes in systemic vascular resistance on a novel
   non-invasive continuous cardiac output measurement system based on pulse wave transit
   time: a report of two cases. J Clin Monit Comput. 2014;28(4):423-7. PMID 24197827.
   **← 本研究の仮説を提示し検証を呼びかけた文献**
8. Biais M, Berthezène R, Petit L, et al. Ability of esCCO to track changes in cardiac
   output. Br J Anaesth. 2015;115(3):403-10. PMID 26209443.
9. Smetkin AA, Hussain A, Fot EV, et al. Estimated continuous cardiac output based on pulse
   wave transit time in off-pump coronary artery bypass grafting: a comparison with
   transpulmonary thermodilution. J Clin Monit Comput. 2017;31(2):361-70. PMID 26951494.
10. Magliocca A, Rezoagli E, Anderson TA, et al. Cardiac output measurements based on the
    pulse wave transit time and thoracic impedance exhibit limited agreement with
    thermodilution method during orthotopic liver transplantation. Anesth Analg.
    2018;126(1):85-92. PMID 28598912.
11. Sugo Y, Ochiai R. Moving-average processing enables accurate quantification of time
    delay and compares the trending ability of cardiac output monitors with different
    response times. BMC Biomed Eng. 2025;7(1):14. PMID 41047412.
    doi:10.1186/s42490-025-00101-8 **← 副次解析のウィンドウ長への批判に先回り**

### 前駆出期（PEP）とPWTTの分解 ― 考察の骨格

12. Payne RA, Symeonides CN, Webb DJ, Maxwell SR. Pulse transit time measured from the ECG:
    an unreliable marker of beat-to-beat blood pressure. J Appl Physiol. 2006;100(1):136-41.
    PMID 16141378.
13. Zhang G, Gao M, Xu D, Olivier NB, Mukkamala R. Pulse arrival time is not an adequate
    surrogate for pulse transit time as a marker of blood pressure. J Appl Physiol.
    2011;111(6):1681-6. PMID 21960657.
14. Balmer J, Pretty C, Davidson S, et al. Pre-ejection period, the reason why the
    electrocardiogram Q-wave is an unreliable indicator of pulse wave initialization.
    Physiol Meas. 2018;39(9):095005. PMID 30109991.
15. Djupedal H, Nøstdahl T, Hisdal J, et al. Effects of experimental hypovolemia and pain on
    pre-ejection period and pulse transit time in healthy volunteers. Physiol Rep.
    2022;10(12):e15355. PMID 35748055.
16. Pilz N, Patzak A, Bothe TL. The pre-ejection period is a highly stress dependent
    parameter of paramount importance for pulse-wave-velocity based applications. Front
    Cardiovasc Med. 2023;10:1138356. PMID 36873391.

### 脈波分解（PDA）とSI・RI

17. Millasseau SC, Kelly RP, Ritter JM, Chowienczyk PJ. Determination of age-related
    increases in large artery stiffness by digital pulse contour analysis. Clin Sci (Lond).
    2002;103(4):371-7. PMID 12241535. **← 陽性対照（加齢とSI）の根拠**
18. Millasseau SC, Ritter JM, Takazawa K, Chowienczyk PJ. Contour analysis of the
    photoplethysmographic pulse measured at the finger. J Hypertens. 2006;24(8):1449-56.
    PMID 16877944.
19. Rubins U. Finger and ear photoplethysmogram waveform analysis by fitting with
    Gaussians. Med Biol Eng Comput. 2008;46(12):1271-1276. PMID 18855034.
20. Goswami D, Chaudhuri K, Mukherjee J. A new two-pulse synthesis model for digital
    volume pulse signal analysis. Cardiovasc Eng. 2010;10(3):109-117. PMID 20734136.
21. Epstein S, Vergnaud AC, Elliott P, Chowienczyk P, Alastruey J. Numerical assessment of
    the stiffness index. Annu Int Conf IEEE Eng Med Biol Soc. 2014;2014:1969-72.
    PMID 25570367.
22. Couceiro R, Carvalho P, Paiva RP, et al. Assessment of cardiovascular function from
    multi-Gaussian fitting of a finger photoplethysmogram. Physiol Meas.
    2015;36(9):1801-25. PMID 26235798. **← 振幅比がすべての血管参照に対して失敗**
23. Tigges T, Pielmus A, Klum M, Feldheiser A, Hunsicker O, Orglmeister R. Model selection
    for the pulse decomposition analysis of fingertip photoplethysmograms. Annu Int Conf
    IEEE Eng Med Biol Soc. 2017;2017:4014-4017. PMID 29060777.
    **← 実測7,805拍・AICc で 3ガンマが最良（28.1%）、Normal 2成分は 1.2%。Limitations で引く**
24. Fleischhauer V, Ruprecht N, Sorelli M, Bocchi L, Zaunseder S. Pulse decomposition
    analysis in photoplethysmography imaging. Physiol Meas. 2020;41(9):095009.
    PMID 33021236. **← 2カーネル選択の根拠（Methods）。ただし同論文は「2カーネルでは
    反射が単一成分に凝縮され、収縮期成分と特定の反射との関係を評価できない」とも述べており、
    Methods と Limitations の両方でこの留保を引く。投稿先第一候補と同じ誌**
25. Basso G, Haakma R, Vullings R. A skewed-Gaussian model for pulse decomposition
    analysis of photoplethysmography signals. Physiol Meas. 2024;45(11):115006.
    PMID 39577084. doi:10.1088/1361-6579/ad9662
    **← 本研究の当てはめモデルの原典。投稿先第一候補と同じ誌**
### PTT・PPGを用いた補正の先行研究（新規性の申告に必須）

26. Ding XR, Zhang YT, Liu J, Dai WX, Tsang HK. Continuous cuffless blood pressure estimation
    using pulse transit time and photoplethysmogram intensity ratio. IEEE Trans Biomed Eng.
    2016;63(5):964-72. PMID 26415147.
27. Yang S, Sohn J, Lee S, Lee J, Kim HC. Estimation and validation of arterial blood
    pressure using photoplethysmogram morphology features in conjunction with pulse
    arrival time in large open databases. IEEE J Biomed Health Inform.
    2021;25(4):1018-1030. PMID 32750963. **← 引用漏れは隠蔽と受け取られる。最重要**
28. Lee J, Yang S, Lee S, Kim HC. Analysis of pulse arrival time as an indicator of blood
    pressure in a large surgical biosignal database. J Clin Med. 2019;8(11):1773.
    PMID 31653002.

### データベースと信号の由来

29. Lee HC, Park Y, Yoon SB, Yang SM, Park D, Jung CW. VitalDB, a high-fidelity
    multi-parameter vital signs database in surgical patients. Sci Data. 2022;9(1):279.
    PMID 35676300. doi:10.1038/s41597-022-01411-5
30. Wang W, Mohseni P, Kilgore KL, Najafizadeh L. PulseDB: a large, cleaned dataset based on
    MIMIC-III and VitalDB for benchmarking cuff-less blood pressure estimation methods.
    Front Digit Health. 2022;4:1090854. PMID 36844249.
    **← VitalDBの波形同期を問題なしとする記載。本研究の遅延定量と対立**
31. Ruffolo I, Siddiqui A, Nguyen B, et al. High-fidelity measurement of pulse arrival time
    in critically ill children using standard bedside monitoring equipment. Physiol Meas.
    2025;46(11). PMID 41187451. **← 装置由来タイミング破綻の先行報告。「発見」と書かないための引用**
32. Liao S, Liu H, Chen W, et al. Filtering-induced changes of pulse transmit time across
    different ages: a neglected concern in photoplethysmography-based cuffless blood
    pressure measurement. Front Physiol. 2023;14:1172150. PMID 37560157.

### 統計・報告基準

33. Critchley LA, Critchley JA. A meta-analysis of studies using bias and precision
    statistics to compare cardiac output measurement techniques. J Clin Monit Comput.
    1999;15(2):85-91. PMID 12578081. **← 30%基準の出典**
34. Joosten A, Desebbe O, Suehiro K, et al. Accuracy and precision of non-invasive cardiac
    output monitoring devices in perioperative medicine: a systematic review and
    meta-analysis. Br J Anaesth. 2017;118(3):298-310. PMID 28203792.
35. Altman DG, Bland JM. Absence of evidence is not evidence of absence. BMJ.
    1995;311(7003):485. PMID 7647644. **← 精密な陰性であると主張する根拠**
36. von Elm E, Altman DG, Egger M, Pocock SJ, Gøtzsche PC, Vandenbroucke JP; STROBE
    Initiative. The Strengthening the Reporting of Observational Studies in Epidemiology
    (STROBE) statement: guidelines for reporting observational studies. Lancet.
    2007;370(9596):1453-1457. PMID 18064739.（このPMIDはLancet版。他誌の同時掲載と識別子を混ぜない）
37. Montenij LJ, Buhre WF, Jansen JR, Kruitwagen CL, de Waal EE. Methodology of method
    comparison studies evaluating the validity of cardiac output monitors: a stepwise
    approach and checklist. Br J Anaesth. 2016;116(6):750-758. PMID 27199309.
    **← 麻酔科の査読者が当てるチェックリスト**
38. Md Lazin Md Lazim MR, Aminuddin A, Chellappan K, Ugusman A, Hamid AA,
    Wan Ahmad WAN, Mohamad MSF. Is heart rate a confounding factor for
    photoplethysmography markers? A systematic review. Int J Environ Res Public Health.
    2020;17(7):2591. PMID 32290168.
    **← 実はPPG血管指標へのHR交絡の系統的レビュー。感度解析Bの引用として最適**

### 仮想集団（研究0・in silico 検証）

39. Charlton PH, Mariscal Harana J, Vennin S, Li Y, Chowienczyk P, Alastruey J. Modeling
    arterial pulse waves in healthy aging: a database for in silico evaluation of
    hemodynamics and pulse wave indexes. Am J Physiol Heart Circ Physiol.
    2019;317(5):H1062-H1085. PMID 31442381. doi:10.1152/ajpheart.00218.2019
    **← 2026-09-09 に PubMed（PMID 31442381）で著者・表題・巻号・頁を照合済み。データ: doi:10.5281/zenodo.3275625**

### 凍結後に追加（探索的解析・考察で引く）

40. Hellqvist H, Karlsson M, Hoffman J, Kahan T, Spaak J. Estimation of aortic stiffness by finger photoplethysmography using enhanced pulse wave analysis and machine learning. Front Cardiovasc Med. 2024;11:1350726. doi:10.3389/fcvm.2024.1350726.
    **← 早期振幅比 Am_b/Am_p1 の原典。§2.10(d) と §3.6 で引く。2026-09-07 に出版社PDF
    （1ページ目の CITATION 欄）で照合済み**

41. Wang L, Xu L, Feng S, Meng MQ-H, Wang K. Multi-Gaussian fitting for pulse waveform
    using weighted least squares and multi-criteria decision making method. Comput Biol
    Med. 2013;43(11):1661-1672. PMID 24209911. doi:10.1016/j.compbiomed.2013.08.004.
    **← 特徴点の時間位置の誤差（Errx < 6 ms）を当てはめの採否規準に据えた原典。2026-09-09 に PubMed で照合済み。誤った PMID 24209920（別論文）を 24209911 に訂正した**
