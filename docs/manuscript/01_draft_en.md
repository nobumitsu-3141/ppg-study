# DRAFT — Manuscript v0.1 (working draft, 2026-08-29)

**Status**: Methods are complete and frozen (SAP v0.3). Introduction and Discussion are
first drafts. Results are placeholders pending the 874-case confirmatory run.
Placeholders are marked `[[ ]]`.

**Framing**: reference-free premise test as the primary analysis (see `00_outline_ja.md` §0).

---

## Title

Photoplethysmographic vascular indices explain little of intraoperative pulse-wave
transit time variation: a prespecified reference-free analysis of 874 surgical cases

## Abstract (structured, ~250 words — write last)

**Background.** [[Transit-time based CO estimation; error correlates with vascular state;
calibration constant contains no vascular information; the untested premise.]]

**Methods.** [[874 cases from VitalDB with PPG, ECG, arterial pressure and continuous CO.
Prespecified analysis plan frozen before analysis. Primary analysis reference-free:
within-case regression of change in PWTT on changes in pulse-decomposition-derived
transit time (ΔT) and reflection index (RI).]]

**Results.** [[r² =; coefficients =; measurement quality evidence; secondary accuracy
analysis.]]

**Conclusions.** [[Beat-to-beat PWTT variation is largely not explained by PPG-derived
vascular indices, bounding the achievable benefit of vascular correction of the
calibration constant.]]

---

## 1. Introduction

Continuous, non-invasive estimation of cardiac output (CO) remains an unmet need in
perioperative care. Among the available approaches, estimation from pulse-wave transit
time (PWTT) — implemented commercially as esCCO — is attractive because it requires only
the electrocardiogram and the photoplethysmogram, both of which are already recorded in
essentially every anaesthetised patient. [[refs: Sugo 2010; Yamada 2012]]

Validation studies have repeatedly shown, however, that the error of this approach is not
random. Agreement with reference CO deteriorates in a structured way that correlates with
the vascular state of the patient, in particular with systemic vascular resistance and
effective arterial elastance. [[refs: Biais 2015; Magliocca 2018]] This is mechanistically
plausible: the transformation from transit time to stroke volume is mediated by arterial
properties, yet the subject-specific calibration constant is derived from demographic
variables (age, sex, height, weight) and, once calibrated, is held fixed for the remainder
of the case. It therefore carries no information about the patient's vascular state and
cannot follow changes in it.

This observation invites an apparently natural remedy: if the calibration constant could
be corrected dynamically using a continuously available marker of vascular state, the
structured component of the error might be removed. The photoplethysmogram itself offers
such markers. Decomposition of the pulse into forward and reflected components yields a
stiffness index (from the interval between component peaks) and a reflection index (from
the ratio of component amplitudes), both of which have been used as non-invasive
descriptors of arterial stiffness and wave reflection. [[refs: Millasseau; Rubins 2008;
Goswami 2010; Baruch]]

That remedy, however, rests on a premise that has not been tested directly: **that the
variation in PWTT which we wish to correct is in fact driven by the vascular state that
these indices measure.** PWTT is not a purely vascular interval. Measured from the R wave,
it contains the pre-ejection period, which varies with preload, afterload and
contractility, in addition to the true arterial transit time. [[refs: PEP/PTT literature]]
If the intraoperative variation of PWTT is dominated by its cardiac component, then no
correction based on vascular indices — however well those indices are measured — can
recover it.

We therefore asked, before asking whether such a correction improves accuracy, whether its
premise holds. Using a public perioperative waveform database and an analysis plan frozen
before any waveform was examined, we quantified how much of the within-case, beat-to-beat
variation in PWTT is explained by simultaneously measured pulse-decomposition indices.
This primary question requires no reference CO measurement at all, and is therefore immune
to the limitations of the reference standards available in such databases.

---

## 2. Methods

### 2.1 Study design, data source and ethics

This was a retrospective analysis of VitalDB, a publicly available database of
high-resolution perioperative waveforms and monitor parameters recorded at Seoul National
University Hospital. [[ref: Lee 2022, PMID 35676300]] The database contains 6,388 cases
with anonymised waveform data released for unrestricted research use.

Because the study used only anonymised, publicly released data and involved no patient
contact, the institutional ethics committee of [[Goto Chuoh Hospital]] was formally
consulted and responded that ethics committee review was not required. The written
response is retained by the authors.

The statistical analysis plan, including all index definitions, quality thresholds, the
model specification and the interpretation rules, was finalised and frozen before any
waveform data were analysed. Development and verification of the measurement pipeline used
synthetic signals with known ground truth. The frozen plan and the complete analysis code
are publicly available. [[GitHub URL]]

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

### 2.3 Signal processing

All processing was performed in non-overlapping 60-second windows.

**Device delay of the photoplethysmographic channel.** During pipeline validation we found
that the PPG channel in this database is delayed relative to the ECG by a fixed,
case-specific interval of the order of 670 ms, reflecting the monitor's internal signal
processing. Left uncorrected this delay causes two failures: beat segmentation windows
anchored to the R wave miss the true pulse foot, and, when the delay exceeds the RR
interval, the apparent transit time wraps modulo the cardiac cycle. We therefore estimated
the delay at case level and used it to resolve this ambiguity. Sixty-second windows were
sampled across the whole record; within each window, R waves were detected locally and
candidate R-to-foot intervals were formed together with their aliases at one and two RR
intervals. Candidates were pooled over the record and binned; the winning cluster was
selected by coverage (the fraction of windows contributing a candidate near the cluster
centre) rather than by tightness alone, since tightness alone selects artefact clusters.
Per-beat values were then assigned to the branch nearest the case-level estimate, with
values further than 150 ms from it discarded.

**R-wave detection** used a Pan–Tompkins-style detector (differentiation, squaring, moving
average integration, percentile-based adaptive threshold). A simpler global-amplitude
threshold was found during validation to fail catastrophically in the presence of single
large artefacts and was rejected.

**Beat segmentation** was driven by systolic peaks of the photoplethysmogram (minimum
prominence 0.25 of the window signal range; minimum separation 0.55 of the median RR
interval taken from the ECG). For each accepted peak the pulse foot was located as the
maximum of the smoothed second derivative preceding the peak, within a 0.45-second search
window. Beats failing a signal quality index (non-zero amplitude, absence of missing
samples, fewer than 10% of samples identical to their neighbour) were discarded.

**Ensemble averaging** was adaptive rather than fixed. The relative noise level of each
window, σ_rel, was estimated from the robust standard deviation of the second difference of
the signal. The number of beats to average was set to n = ⌈(σ_rel / 0.003)²⌉, bounded to
between 4 and 16 beats; windows whose effective noise remained above the target of 0.003
even with 16 beats were rejected. Beats were aligned at their feet, not time-normalised;
time normalisation was found during validation to inflate the reflection index by 24–39%.
This adaptive scheme was adopted because, at fixed averaging depth, elevated noise makes
the two-kernel decomposition converge confidently to an incorrect solution that passes all
convergence checks — a failure mode the checks cannot catch, so noise must be suppressed
before fitting.

### 2.4 Pulse decomposition and index definitions

Ensemble-averaged beats were decomposed into two skewed-Gaussian components (Azzalini
form), representing the forward and reflected waves, by non-linear least squares from eight
starting points. [[refs: Basso 2024; Fleischhauer 2020]] A fit was accepted only if it
passed three convergence checks: no parameter resting on a bound (excluding the skewness
bounds), no component collapsed to zero amplitude, and no competing solution of comparable
residual.

The definitions of "stiffness index" and "reflection index" are not consistent across the
literature. We therefore compared candidate definitions on synthetic pulses with known
ground truth **before examining any real data** and froze the following:

- **ΔT**: the interval between the peak times of the two components (most robust of five
  candidates; error ≤ 1.8 ms under favourable conditions).
- **RI**: the ratio of the **peak heights** of the two components (most robust of three
  candidates; error ≤ 0.9%). Note that this is not the ratio of the amplitude parameters,
  which differ from the peak heights because peak height depends on skewness and width.
- **SI**: subject height divided by ΔT, reported for comparability with the literature.
  Within-case relative change in SI is algebraically identical to that of ΔT, since height
  cancels.

Alternative definitions (onset-to-onset ΔT defined at 20% of component peak height,
amplitude-parameter ratio, component area ratio) and a three-kernel decomposition were
prespecified as sensitivity analyses.

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

For each case, the change in PWTT from the case's first window was regressed on the
concurrent relative changes in ΔT and RI, with an intercept:

    ΔPWTT = b₀ + b₁·ΔΔT% + b₂·ΔRI% + ε

We report the pooled coefficient of determination and the coefficients with 95% confidence
intervals, together with the distribution of within-case r² values. This analysis uses no
reference CO and is therefore unaffected by the limitation described in §2.2.

**Distinguishing a weak premise from noise.** A near-zero r² can arise either because the
premise is false or because the measurements are too noisy to reveal a real relationship.
To separate these, we prespecified the lag-1 autocorrelation of PWTT, ΔT and RI across
consecutive windows within each case: measurement noise dominated series have
autocorrelation near zero, whereas a series that tracks a physiological signal retains
autocorrelation even if it is unrelated to the other variables. We additionally report the
consistency of the sign of b₁ across cases, to detect a relationship that exists but points
in opposite directions in different patients.

### 2.7 Secondary analysis: accuracy against reference CO

A control estimator reproducing the published PWTT form, esSV = K₀ × (β − α·PWTT) with K₀
regressed on age, sex, height and weight, was compared with a proposed estimator in which
the calibration constant was corrected as K = K₀ × f(ΔT, RI), f being linear in the
within-case relative changes of the two indices. Both were calibrated on the first window
of each case, mimicking the clinical calibration procedure, and evaluated by case-level
5-fold cross-validation with coefficients re-estimated within each training fold.

The outcome was the percentage error of Critchley and Critchley; the difference between
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
varied to 0.002 and 0.004; signal quality threshold varied; the non-FloTrac subset (29
cases) analysed separately; and exclusion of the 15 cases used during pipeline development.

### 2.10 Software

[[Python 3.x, NumPy, SciPy, pandas. All analysis code, the frozen analysis plan and the
synthetic-data test suite are available at <GitHub URL>.]]

---

## 3. Results

> **Pending the 874-case confirmatory run.** Structure and the pilot values (n = 15) are
> given so that the narrative can be assembled immediately when the run completes.

### 3.1 Cohort and data yield
[[Figure 1 flow diagram. Cases analysed of 874; windows analysed; rejection breakdown;
patient and procedure characteristics in Table 1.]]

### 3.2 Measurement quality
[[Table 3. Pilot: pulse decomposition accepted in 77% of fits; lag-1 autocorrelation
PWTT +0.79, ΔT-based index +0.65, RI +0.47.]]

### 3.3 Primary analysis — premise test
[[Table 2, Figure 2. Pilot: pooled r² ≈ 0; within-case r² median 0.103; sign of the ΔT
coefficient negative in 10 of 15 cases with all |coefficients| ≤ 0.05.]]

### 3.4 Secondary analysis — accuracy
[[Table 4, Figure 4. Pilot: percentage error 27.8% control versus 27.6% proposed;
difference +0.8% (95% CI −0.4 to +2.2).]]

### 3.5 Sensitivity analyses
[[Table 5.]]

---

## 4. Discussion

[[Draft to be completed against the final numbers; structure fixed as follows.]]

**Principal finding.** In 874 surgical cases, the within-case variation of pulse-wave
transit time was largely not explained by concurrently measured photoplethysmographic
indices of arterial stiffness and wave reflection.

**This is not a measurement failure.** The indices retained substantial autocorrelation
between consecutive windows, indicating that they track a reproducible physiological
signal rather than noise; the decomposition converged in the large majority of fits; and
index identifiability had been established on synthetic pulses with known ground truth
before any real data were examined. The relationship is absent, not obscured.

**Physiological interpretation.** PWTT measured from the R wave contains the pre-ejection
period as well as the arterial transit time. The pre-ejection period varies with preload,
afterload and contractility — precisely the quantities that change most during anaesthesia
and surgery. Our finding is consistent with intraoperative PWTT variation being dominated
by this cardiac component. [[refs]]

**Implications.** The structured, vascular-state-related error of transit-time CO
estimation is well documented, and correcting the calibration constant with a vascular
marker is an intuitive response to it. Our results bound what that strategy can achieve
with photoplethysmography-derived indices: if the quantity to be corrected does not vary
with the correction variable, the correction cannot work regardless of how well the index
is measured. More promising directions are those that separate the cardiac component of
PWTT (for example by phonocardiography or impedance), or that increase the frequency of
recalibration rather than modelling the drift.

**A methodological caution for users of open waveform databases.** The photoplethysmographic
channel of this database carries a fixed processing delay of the order of 670 ms relative
to the electrocardiogram. Because it exceeds the cardiac cycle at higher heart rates, naive
computation of transit time yields values that are not merely offset but aliased, and beat
segmentation anchored to the R wave selects the wrong part of the pulse. Any study using
these channels together must estimate and resolve this delay.

**Limitations.** (1) The reference CO available in this database is predominantly derived
from the arterial pressure waveform and is not an independent standard; this affects the
secondary accuracy analysis but not the primary premise test, which uses no reference CO.
(2) Single database, single centre, retrospective. (3) The manufacturer's coefficients are
not public, so the control estimator reproduces the published PWTT form rather than the
commercial device. (4) Component assignment in a two-kernel decomposition is not guaranteed
to correspond to distinct physical waves; we mitigated but cannot exclude misassignment.
(5) Stiffness and reflection indices were developed largely as resting measures, and their
extrapolation to acute intraoperative change is itself an assumption.

**Conclusion.** [[Three sentences.]]

---

## Statements

- **Ethics**: [[The ethics committee of Goto Chuoh Hospital determined that review was not
  required for this analysis of anonymised public data (response dated 2026-08-28).]]
- **Data availability**: VitalDB is publicly available at https://vitaldb.net .
  All analysis code and the prespecified analysis plan are at [[GitHub URL]].
- **Funding**: None.
- **Conflicts of interest**: [[None declared / to be confirmed.]]
- **Author contributions**: [[to be completed]]
