# DRAFT — Manuscript v0.1 (working draft, 2026-08-29)

**Status**: Introduction, Methods and Discussion are complete drafts with citations.
Results are placeholders pending the 874-case confirmatory run. Placeholders are `[[ ]]`.
Reference list at the end; entries marked ★ still need their bibliographic details
confirmed against PubMed before submission.

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
database and an analysis plan frozen before any waveform was examined, we quantified how
much of the within-case, beat-to-beat variation in PWTT is explained by simultaneously
measured pulse-decomposition indices. This primary question requires no reference CO
measurement, and is therefore unaffected by the limitations of the reference standards such
databases provide.

## 2. Methods

### 2.1 Study design, data source and ethics

This was a retrospective analysis of VitalDB, a publicly available database of
high-resolution perioperative waveforms and monitor parameters recorded at Seoul National
University Hospital [Lee 2022]. The database contains 6,388 cases
with anonymised waveform data released for unrestricted research use.

Because the study used only anonymised, publicly released data and involved no patient
contact, the institutional ethics committee of [[Goto Chuoh Hospital]] was formally
consulted and responded that ethics committee review was not required. The written
response is retained by the authors.

The statistical analysis plan, including all index definitions, quality thresholds, the
model specification and the interpretation rules, was finalised and frozen before any
waveform data were analysed. Development and verification of the measurement pipeline used
synthetic signals with known ground truth. The frozen plan and the complete analysis code
are publicly available [[GitHub URL]], with a third-party timestamp of the freeze
[[Zenodo DOI; commit hash; 28 August 2026]]. The study is reported in accordance with the
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
are relevant. Filtering of this kind shifts and reshapes the timing landmarks on which
decomposition-derived intervals depend, in an age-dependent manner [Liao 2023], and any
automatic gain control would attenuate the amplitude information on which the reflection
index depends. We could not exclude automatic gain control from the available documentation.
For this reason we prespecified [[/ added as an exploratory analysis]] a positive control
(§2.6) establishing that the indices recover a known vascular relationship in these
recordings, and we report index identifiability per beat rather than assuming it.

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

**Positive control.** Autocorrelation alone cannot exclude a measurement failure, because a
slow artefact or a settling gain would also be autocorrelated while carrying no vascular
information. We therefore added a positive control: a relationship that must appear if the
indices carry vascular information at all. Across cases, arterial stiffening with age
shortens the interval at which the reflected wave returns, so ΔT should decrease and SI
increase with age [Millasseau 2002]. We tested this by Spearman rank correlation between
patient age and the case-median ΔT, SI and RI, and, as a negative control, between case
identifier and case-median ΔT. A secondary comparison contrasted cases with and without a
preoperative diagnosis of hypertension. This analysis was added after the analysis plan was
frozen and is reported as exploratory; it does not alter any prespecified endpoint.

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

[[Numbers to be inserted from the confirmatory run; argument structure is final.]]

**Principal finding.** In [[N]] surgical cases, the within-case variation of pulse wave
transit time was largely not explained by concurrently measured photoplethysmographic
indices of arterial stiffness and wave reflection. The relationship was estimated
precisely rather than merely failing to reach significance: with [[N]] cases and [[n]]
windows per case, the confidence interval around the vascular-explained fraction was narrow
and centred near zero, which supports absence of a usable effect rather than absence of
evidence [Altman & Bland 1995].

**The null is not a measurement failure.** This is the interpretation that must be excluded
before any physiological reading is permitted, because the photoplethysmographic channel of
this database is a processed monitor output rather than a research-grade signal. Three
independent lines of evidence exclude it. First, a positive control: across cases, the
component interval and the derived stiffness index varied with age in the direction and
approximate magnitude established for digital pulse contour analysis [Millasseau 2002], and
the reflection index did likewise, while a negative control variable showed no association
[[Table 3]]. The pipeline therefore detects a vascular signal where one is known to exist.
Second, the indices retained substantial autocorrelation between consecutive windows,
indicating series that track a reproducible physiological quantity. Third, index
identifiability was established on synthetic pulses with known ground truth before any
patient data were examined, and per-beat identifiability, convergence and exclusion rates
are reported here in full [[Table 3]]. The relationship is absent, not obscured.

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
approximately half of the change in PWTT [Sugo 2012]. The present study is the human,
intraoperative, reference-free confirmation of that mechanism, and it explains why improving
the calibration procedure alone does not repair the method [Smetkin 2017].

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

**Implications.** The structured, vascular-state-related error of transit-time cardiac
output estimation is well documented, and correcting the calibration constant with a
vascular marker is the intuitive response to it. Our results bound what that strategy can
achieve from single-site photoplethysmography: if the quantity to be corrected does not
covary with the correction variable, the correction cannot work regardless of how well the
index is measured. More promising directions are those that measure and remove the cardiac
term directly — phonocardiography, impedance cardiography or bioreactance to time aortic
valve opening — or that abandon drift modelling in favour of more frequent recalibration.

**A caution for users of open waveform databases.** The photoplethysmographic channel of
this database carries a fixed processing delay of approximately [[L]] ms relative to the
electrocardiogram. Device-induced timing artefacts of this class have been documented at
scale elsewhere and are not a new phenomenon [Ruffolo 2025]; what we add is their
quantification and correction in this specific, widely used resource, where waveform
synchronisation has been assumed adequate and that assumption has been propagated into a
derived benchmark dataset [Wang 2022]. Because the delay exceeds the cardiac cycle at
higher heart rates, transit times computed without accounting for it are aliased rather than
merely offset, and beat segmentation anchored to the R wave selects the wrong part of the
pulse. Any study combining these channels must estimate and resolve it.

**Limitations.** First, the reference CO available in this database is predominantly derived
from the arterial pressure waveform ([[857]] of [[874]] cases, FloTrac family) and is not an
independent standard; this affects the secondary accuracy analysis but not the primary
premise test, which uses no reference CO. The independent references available — pulmonary
artery thermodilution in 5 cases and oesophageal Doppler in 24 — are too few for inference
and are reported descriptively only. Second, the secondary accuracy analysis used 60-second
windows, whereas comparison of CO monitors with differing response times has been argued to
require moving averages of 20–30 minutes [Sugo & Ochiai 2025]; we therefore repeated it at
[[5 and 20]] minutes as a sensitivity analysis, and note that this consideration does not
apply to the beat-level, reference-free primary analysis. Third, the study is a
retrospective analysis of a single database from a single centre, without a controlled
vasomotor challenge; the cohort characteristics are reported in full so that transportability
can be judged. Fourth, the manufacturer's coefficients are not public, so the control
estimator reproduces the published PWTT form rather than the commercial device. Fifth,
component assignment in a two-kernel decomposition is not guaranteed to correspond to
distinct physical waves [Epstein 2014]. Sixth, stiffness and reflection indices were
developed largely as resting measures, and their extrapolation to acute intraoperative
change is itself an assumption. Finally, the photoplethysmographic channel is a processed
monitor output; although the positive control indicates that vascular information survives
that processing, we cannot exclude that automatic gain control attenuates amplitude-derived
information, and conclusions resting on the reflection index should be read with that in
mind.

**Conclusion.** In a large perioperative waveform database, beat-to-beat variation in pulse
wave transit time was largely unexplained by photoplethysmography-derived indices of
arterial stiffness and wave reflection, despite evidence that those indices were measured
well enough to detect a known vascular signal. Dynamic correction of the calibration
constant of transit-time cardiac output estimation using these indices therefore has little
room to work. Methods that resolve the cardiac component of transit time, rather than model
its vascular component, are the more promising direction.

## Statements

- **Ethics**: [[The ethics committee of Goto Chuoh Hospital determined that review was not
  required for this analysis of anonymised public data (response dated 2026-08-28).]]
- **Data availability**: VitalDB is publicly available at https://vitaldb.net .
  All analysis code and the prespecified analysis plan are at [[GitHub URL]].
- **Funding**: None.
- **Conflicts of interest**: [[None declared / to be confirmed.]]
- **Author contributions**: [[to be completed]]


---

## References

> **確認事項**: 以下は文献調査で得た書誌情報。**投稿前に全件PubMedで原典を開き、
> 巻・号・頁と著者名を照合すること**（★印は書誌の一部が未照合）。
> 引用形式は投稿先の規定に合わせて整形する。

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
11. ★ Sugo Y, Ochiai R. [CO monitor response-time comparison requiring 20–30 min moving
    averages]. 2025. PMID 41047412. **← 副次解析のウィンドウ長への批判に先回りするため必読**

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
19. Rubins U, et al. [First Gaussian-fit reflection index]. 2008. PMID 18855034. ★
20. Goswami D, et al. [First decomposition-derived SI and RI]. 2010. PMID 20734136. ★
21. Epstein S, Vergnaud AC, Elliott P, Chowienczyk P, Alastruey J. Numerical assessment of
    the stiffness index. Annu Int Conf IEEE Eng Med Biol Soc. 2014;2014:1969-72.
    PMID 25570367.
22. Couceiro R, Carvalho P, Paiva RP, et al. Assessment of cardiovascular function from
    multi-Gaussian fitting of a finger photoplethysmogram. Physiol Meas.
    2015;36(9):1801-25. PMID 26235798. **← 振幅比がすべての血管参照に対して失敗**
23. Tigges T, et al. Model selection for the pulse decomposition analysis of fingertip
    photoplethysmograms. Annu Int Conf IEEE Eng Med Biol Soc. 2017. PMID 29060777.
24. Fleischhauer V, et al. [Two-kernel Gamma+Gaussian most robust to noise and motion].
    2020. PMID 33021236. ★ **← 2カーネル選択の根拠（Methods）**
25. Basso G, Sorelli M, Bocchi L, et al. A skewed-Gaussian model for pulse decomposition
    analysis of photoplethysmography signals. Physiol Meas. 2024;45(11). PMID 39577084.
    **← 本研究の当てはめモデルの原典。投稿先第一候補と同じ誌**

### PTT・PPGを用いた補正の先行研究（新規性の申告に必須）

26. Ding XR, Zhang YT, Liu J, Dai WX, Tsang HK. Continuous cuffless blood pressure estimation
    using pulse transit time and photoplethysmogram intensity ratio. IEEE Trans Biomed Eng.
    2016;63(5):964-72. PMID 26415147.
27. ★ Yang S, et al. [PPG morphology combined with pulse arrival time for blood pressure,
    VitalDB, 1,376 patients]. IEEE J Biomed Health Inform. 2021. PMID 32750963.
    **← 引用漏れは隠蔽と受け取られる。最重要**
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
35. ★ Altman DG, Bland JM. Absence of evidence is not evidence of absence. BMJ. 1995.
    PMID 7647644. **← 精密な陰性であると主張する根拠**
36. ★ von Elm E, Altman DG, Egger M, et al. The Strengthening the Reporting of Observational
    Studies in Epidemiology (STROBE) statement. 2007. PMID 18064739.
37. ★ Montenij LJ, et al. [Method-comparison checklist for cardiac output validation].
    2016. PMID 27199309. **← 麻酔科の査読者が当てるチェックリスト**
38. ★ Md Lazin bin Md Lazim MR, et al. [Heart rate confounding in PTT-based estimation].
    2020. PMID 32290168.
