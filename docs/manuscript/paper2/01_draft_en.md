# DRAFT — Paper 2, Manuscript v0.1 (working draft, 2026-09-07)

**Status.** First full pass. All numbers are from the frozen judgment recorded in
`docs/research/roadmap_v1.md` §9 and `docs/research/lab_log.md` (追記12, 13, 18).
`[[ ]]` marks what still has to be supplied. Framing and figure plan: `00_outline.md`.

**Scope.** In-silico only (Pulse Wave Database, 4,374 virtual subjects; literature
replication on 624). Real-monitor identifiability is a separate report (Paper 3).

**Tables** are written out in `02_tables.md`; **figures** are in `figures/`.

---

## Title

Pulse decomposition indices of the photoplethysmogram do not track aortic stiffness or
peripheral resistance in silico, whereas fiducial-point indices from the same waveforms do:
a prespecified study in 4,374 virtual subjects

**Running title.** Construct validity of photoplethysmographic pulse decomposition

---

## Abstract (structured, ~250 words)

**Objective.** Photoplethysmographic (PPG) vascular indices are usually built either by
locating fiducial points on the waveform or by decomposing the pulse into component waves.
Decomposition is preferred when the dicrotic notch is absent, because it returns a value
regardless. Whether the values it returns track the vascular quantities they are meant to
represent has not been tested against known truth. We tested this.

**Approach.** We used the Pulse Wave Database, the output of a one-dimensional
haemodynamic model in which aortic pulse wave velocity (PWV) and peripheral vascular
resistance are known by construction (4,374 virtual subjects; six age strata, six
haemodynamic factors varied at three levels). Before running the analysis we froze the
decision rule: an index is considered valid only if the within-age-stratum Spearman
correlation has the predicted sign in all six strata and the median |ρ| is at least 0.30.
A positive control (model-derived pulse transit time versus aortic PWV) was required to
pass before any other row was read. The same digital PPG waveforms were analysed by
two-component pulse decomposition, by fiducial-point analysis, and by an upstroke-only
amplitude ratio.

**Main results.** The positive control passed (ρ = 0.571, 6/6 strata). Decomposition-derived
ΔT versus aortic PWV reached |ρ| = 0.167 and RI versus peripheral resistance 0.354; both
failed. Fiducial-point ΔT and RI from the *same waveforms* reached 0.710 and 0.504, and the
upstroke amplitude ratio reached 0.836; all passed. The negative result did not depend on
implementation (a version rebuilt from five source papers gave the same value), on the basis
function (twelve combinations of basis and component count peaked at 0.56), or on published
fitting conditions (six literature protocols reproduced from full text peaked at 0.578).
Adding components lowered the fitting residual while lowering the correlation with truth.

**Significance.** [[one sentence — write last]]

**Keywords.** photoplethysmography; pulse decomposition analysis; pulse wave analysis;
arterial stiffness; construct validity; in-silico validation

---

## 1. Introduction

The digital photoplethysmogram is recorded continuously in almost every anaesthetised
patient, and its shape changes with vascular state. Two families of indices are built from
it. **Fiducial-point analysis** locates the systolic peak, the dicrotic notch and the
diastolic peak directly on the waveform, and forms the interval ΔT between the systolic and
diastolic peaks and the reflection index RI as the ratio of their heights. **Pulse
decomposition analysis** instead fits the beat as a sum of component waves and forms the
same two quantities from the positions and amplitudes of the fitted components (Figure 1).

Decomposition was introduced to solve a specific problem. As arteries stiffen the dicrotic
notch flattens and finally disappears, so fiducial-point analysis fails in exactly the
subjects in which a stiffness index is most wanted. Because the model supplies the position
of the second component even when nothing is visible on the waveform, decomposition returns
a value in those beats. This advantage is real and has been repeatedly demonstrated
[Rubins 2008; Goswami 2010; Couceiro 2015].

What has been demonstrated, however, is not the same thing as validity. The literature on
pulse decomposition has evaluated **goodness of fit** (corrected Akaike information
criterion across four basis functions and six component counts [Tigges 2017]; residual sum
of squares and insensitivity to initial values [Basso 2024]), **robustness to noise and
motion** (normalised RMSE of the second derivative of the reconstructed waveform across
nineteen algorithms [Fleischhauer 2020]), and **whether the fit reproduces the measured
fiducial points** [Wang 2013] — in which the fiducial points are the reference, not the
decomposition. Where a decomposition-derived index has been compared with a physiological
reference, the comparison has been pooled across a wide age range in small samples
[Goswami 2010, n = 113; Couceiro 2015, n = 43].

None of these designs can detect a specific failure mode. Fitting a beat as a sum of
component waves is an ill-posed problem: many parameter combinations give almost the same
residual (Figure 2). Every goodness-of-fit criterion is, by construction, nearly invariant to which of
those solutions the optimiser lands on, while the extracted parameters are not. A method can
therefore be excellent by every published criterion and still return a quantity that does
not track the vascular property it names.

Separating these two things requires knowing the truth. In measured data the aortic pulse
wave velocity and the peripheral vascular resistance of the subject whose finger is being
transilluminated are not available. In a validated numerical model of the arterial tree both are known exactly:
aortic pulse wave velocity is a model input, and peripheral vascular resistance is a
derived quantity fixed by the inputs (mean arterial pressure, heart rate and stroke
volume). The Pulse Wave Database [Charlton 2019] provides digital PPG
waveforms together with those quantities for 4,374 virtual subjects. Its original report
compares fiducial-point-derived indices with aortic PWV; **to our knowledge no study has
tested decomposition-derived indices against it.**

We therefore asked a single question with the decision rule fixed in advance: *do
decomposition-derived ΔT and RI track aortic PWV and peripheral resistance within age
strata, and how do they compare with indices read directly from the same waveforms?*

---

## 2. Methods

### 2.1 Data source

The Pulse Wave Database (PWDB) is the output of a one-dimensional fluid-dynamic model of
the arterial tree, published by Charlton and colleagues and distributed openly
(Zenodo doi:10.5281/zenodo.3275625) [Charlton 2019]. It contains 4,374 virtual subjects in
six age strata (25, 35, 45, 55, 65 and 75 years). Within each stratum, six haemodynamic
factors — aortic diameter, heart rate, left ventricular ejection time, mean arterial
pressure, pulse wave velocity and stroke volume — are varied in a **full factorial design**
at three levels (baseline and ±1 SD of the age-specific distribution): 3⁶ = 729 subjects per
stratum × 6 strata = 4,374. For each virtual subject the database supplies pressure, flow
velocity and luminal area at several sites, a **digital photoplethysmogram**, aortic pulse
wave velocity (a model input) and peripheral vascular resistance (**a derived quantity**,
since mean arterial pressure ≈ resistance × cardiac output). The association between RI and
peripheral vascular resistance therefore carries the effects of mean arterial pressure,
heart rate and stroke volume, **and the sign of that contamination differs by factor**.
Raising mean arterial pressure raises resistance but lowers RI (0.294 → 0.254 → 0.236 in the
single-factor sweep), pulling the association negative; raising heart rate raises cardiac
output, lowers resistance and also lowers RI (main effect −40%), pulling it positive.
**The observed association therefore cannot be attributed to resistance as such.** The
factors are separated by the main-effect analysis.

Two properties make this the appropriate substrate for the present question. The vascular
quantities are known by construction rather than estimated, and the factors are varied
**independently**, so a confounder cannot inflate an apparent association through a shared
dependence on age. Both properties make the test more demanding than a measured cohort would
be; §4.4 returns to this.

No ethical approval was required; no human data were used.

### 2.2 Waveform handling

Digital PPG waveforms were used at their native sampling rate (500 Hz), one beat per virtual
subject. Preprocessing was identical for every index family: a fourth-order zero-phase
Butterworth low-pass filter with an 18 Hz cutoff (following Tigges 2017 and Couceiro 2015),
removal of a linear baseline drawn between the beat feet
(each foot taken as the minimum within the outer 8% of the beat, following Basso 2024), and
amplitude normalisation to unit range. Because every index compared here is a ratio or an
interval, the amplitude normalisation cancels.

### 2.3 Indices

**Pulse decomposition (frozen version).** The beat is represented as the sum of two
skew-Gaussian components:

  g(t; a, μ, σ, α) = a · exp(−z²/2) · [ 1 + erf( αz / √2 ) ],   z = (t − μ)/σ         (1)

  ŷ(t) = g(t; a₁, μ₁, σ₁, α₁) + g(t; a₂, μ₁ + Δμ, σ₂, α₂)                             (2)

The second component is positioned by an offset Δμ from the first, bounded to
[0.08, 0.60] s. The eight parameters are fitted by trust-region-reflective nonlinear least
squares from eight starting points, retaining the solution of lowest residual sum of
squares. With a tolerance of 10⁻³, a convergence audit rejects a solution if any parameter
lies within 10⁻³ of a search bound (the lower skewness bound of 0 excluded, a symmetric
Gaussian being a legitimate solution), if the smaller of the two component peak heights
falls below 0.02 on the normalised scale, or if among competing solutions whose residual
sum of squares is within 1.15× that of the retained solution and whose Δμ differs by more
than 0.03 s, any differs in reflection index by more than 0.08. Because a component's peak
does not coincide with μ when skewness is non-zero, peak times and heights are located
numerically on a 4,000-point grid. ΔT_PDA is the interval between the fitted component
peaks and RI_PDA the ratio of their peak *heights* — not the ratio of the amplitude
parameters a₂/a₁.

**Pulse decomposition (rebuilt version).** Rebuilt after reading five source papers in full,
adding (i) the preprocessing of Tigges 2017 and Basso 2024 described in §2.2, (ii) weighted
least squares with weights concentrated at the fiducial points, and (iii) the acceptance
criterion of Wang 2013 — **the fit is judged by whether it reproduces the positions of the
measured fiducial points, not by how small the residual is** (absolute time error summed
over fiducial points ≤ 6 ms; amplitude error ≤ 0.01). A fit was also rejected if the
uncertainty of ΔT exceeded 20 ms. The same 20 ms is applied to the standard error of ΔT, to
the spread of ΔT across competing solutions, and to near-ties between candidate reflected
waves, because all three express the same quantity and were frozen together. Two bases were
carried in parallel, skew-Gaussian and gamma.

**Fiducial-point analysis.** The systolic peak, the dicrotic notch and the diastolic peak
were located on the waveform itself. ΔT_lm is the systolic-to-diastolic peak interval,
RI_lm the ratio of their heights and SI = subject height / ΔT_lm. Where no notch was present but the
descending limb showed a well-defined change of slope (Dawber type 3), the inflection point
was used in place of the diastolic peak, and the substitution was recorded.

**Upstroke amplitude ratio.** Am_b/Am_p1 as defined by Hellqvist 2024: t_b is the first
trough of the second derivative, t_p1 is the zero-crossing of the tangent drawn to the
descending linear part of the first derivative after its first peak, so that
t_p1 = t_b − y′(t_b)/y″(t_b), and the index is y(t_b)/y(t_p1). It uses the upstroke only and
requires neither a dicrotic notch nor a diastolic peak, and involves no fitting.

The second component of the pulse is referred to as such rather than as "the reflected
wave"; the identification with peripheral reflection has been questioned for the digital
site [Epstein 2014; Hellqvist 2024], and nothing here depends on it.

### 2.4 Prespecified decision rule

The rule was written into a dated document (`gate0_rules_v2.md`) **before the analysis
script was run on the database** and was not altered afterwards.

- **Targets.** ΔT versus aortic pulse wave velocity (predicted sign: negative) and RI versus
  peripheral vascular resistance (predicted sign: positive). **The two are judged
  independently**; "the decomposition is valid" may be written only if both pass.
- **Criterion.** Within each age stratum, the Spearman correlation must have the predicted
  sign in **all six strata**, and the median |ρ| across strata must be **at least 0.30**.
  Stratifying by age removes the common cause that drives both waveform shape and PWV; §4.4
  explains why this matters for the intended application.
- **Three tiers.** Each target is evaluated on (A) the beats each method itself accepted,
  (B) the beats accepted by all methods in common, and (C) all subjects with acceptance
  ignored. **A pass requires all three tiers.** Any tier that cannot be evaluated for want
  of strata is reported as such and does not count as a pass.
- **Positive control.** The model's own aortic-root-to-digit pulse transit time versus
  aortic PWV must show a strong negative correlation. **If it does not, the entire table is
  void** and the cause is sought before any row is read.

### 2.5 Confirmatory checks of the negative

Three checks, each specified before it was run, addressed the alternative explanations for a
negative result.

1. **Implementation.** The rebuilt version of §2.3 was run on the same subjects.
2. **Basis function.** Gaussian, skew-Gaussian and gamma bases were crossed with component
   counts of two to five (twelve combinations), with the normalised RMSE of the fit recorded
   alongside the correlation with truth.
3. **Published conditions.** The initial values, bounds, constraints, objective functions and
   resampling of six source papers (Goswami 2010, Tigges 2017, Wang 2013, Couceiro 2015,
   Fleischhauer 2020, Basso 2024) were transcribed from the full texts and applied unchanged
   to a systematic subset of 624 subjects. Every deviation forced by our environment is
   listed in a deviations table (table 4).

### 2.6 Descriptive analyses

Within-stratum main effects of each varied factor were computed as the difference between
the +1 SD and −1 SD means divided by the stratum mean. Single-factor sweeps report the
stratum median of each index at the three levels of one factor with all others at baseline.
Waveforms were classified by the visibility of the dicrotic notch (Dawber type 1: notch
present; type 3: inflection only; type 4: neither).

### 2.7 Software and reproducibility

Python, NumPy, SciPy and pandas. The version identifier of the decomposition module was
`048d2b43bb05` for the confirmatory run, and the interpreter and library versions are
recorded in every output row of the result table
[[read the `python_version`, `numpy_version` and `scipy_version` columns of
`data/pwdb/pwdb_compare.csv` on the machine that produced the confirmatory run and insert
them here; the copy in the cloud environment is a self-test subset and its versions differ]].
Analysis code, the frozen decision document and the result tables are archived at
https://github.com/nobumitsu-3141/ppg-pda-analysis (doi:10.5281/zenodo.22676039, release v1.0.0).

---

## 3. Results

### 3.1 Positive control

The model-derived aortic-root-to-digit transit time correlated with aortic PWV at a median
within-stratum ρ of **0.571** with the predicted sign in 6/6 strata. The table was therefore
read. The truth values were mutually consistent: aortic PWV against the model's own
root-to-digit transit time gave ρ = **−0.99** (6/6).

### 3.2 Principal comparison

**Table 1.** Median within-stratum Spearman correlation. The predicted signs are negative for
ΔT versus PWV and positive for RI versus resistance; magnitudes are shown.

| Index construction | ΔT × aortic PWV | RI × peripheral resistance | Verdict |
|---|---|---|---|
| Decomposition, frozen version (2 components) | 0.223 (6/6) | 0.207 (5/6) | fail |
| Decomposition, rebuilt version — skew-Gaussian | accepted 2/4,374; tier C 0.167 | tier C 0.354 (3/6) | fail |
| Decomposition, rebuilt version — gamma | accepted 103; tier A 0.798 (3/4 strata); tier C 0.556 | tier A 0.609 (4/4); tier C 0.280 | fail |
| **Fiducial-point analysis (same waveforms)** | **0.710 (6/6)** | **0.504 (6/6)** | **pass** |
| **Upstroke amplitude ratio Am_b/Am_p1** | **0.836 (6/6)** | — | **pass** |
| Model-derived transit time (positive control) | 0.571 (6/6) | — | pass |

Neither decomposition route passed. The skew-Gaussian route accepted almost no beats
(2 of 4,374) because the right-skewed tail filled in the shallow notch and displaced the
fiducial points by 15–25 ms, more than the 6 ms tolerance of the Wang criterion; tiers A and
B could therefore not be evaluated, and tier C did not reach the threshold. The gamma route
accepted 103 beats and passed some tiers but not all, and **87.4% of accepted beats had at
least one parameter resting on a search bound**. Widening the bounds moved the correlation
among *accepted* beats to 0.119, but left the all-subject value unchanged at 0.55 (§3.3);
the right reading of the pinning is therefore that the parameters of this family are not
identified in these beats, rather than that the search range fixes the answer.

Two further fiducial-point indices passed (SI versus PWV 0.710; the second-derivative ageing
index AGI_mod 0.885) and one failed (augmentation index versus resistance 0.143). Defining
the systolic anchor as p1 rather than as the waveform peak did not help (0.423, 5/6, against
0.536 for our own fiducial ΔT in the same 4,269 subjects).

**The decisive comparison is within a row of the same waveforms.** Changing only the method
of extraction moved ΔT versus aortic PWV from 0.167 to 0.710 and then to 0.836. Had the
waveforms not carried the information, the fiducial-point indices would have failed too.

### 3.3 The negative does not depend on implementation, basis or published conditions

**Implementation.** The rebuilt version, incorporating the preprocessing, weighting and
acceptance criterion of five source papers, gave 0.167 — the same result as the frozen
version within the resolution of the decision rule.

**Basis function (table 3).** This sweep was run after the confirmatory judgment and is
reported as exploratory; it uses the 98 notch-bearing beats available from 120 subjects in
four strata, so its values are wider than those of the confirmatory run. Across twelve
combinations of basis and component count the best value reached was **0.56**, below the
0.710 obtained by fiducial-point analysis on the same subjects. Four observations recur:

- **The failure of the skew-Gaussian family is not a matter of the sign of the skew.**
  Allowing left skew, as Basso 2024 does, reproduced the frozen row exactly at two components
  and almost exactly at three: the optimiser does not select left skew.
- **The plain two-Gaussian basis tracks truth best (0.54, 4/4 strata) while fitting worst**
  (normalised RMSE 4.9%, Wang pass rate 0%, parameters on a bound in only 4% of beats).
  Skewness improves the fit from 0.049 to 0.021 and simultaneously detaches the component
  peaks from the fiducial points.
- **Goodness of fit and validity move in opposite directions.** For the gamma basis,
  increasing from three to four components lowered the normalised RMSE from 0.0071 to 0.0051
  while lowering |ρ| from 0.56 to 0.35; for the Gaussian basis, going from two to four
  components lowered |ρ| from 0.54 to 0.28. Raising the acceptance rate of the fit and
  tracking pulse wave velocity are opposing directions.
- **No basis reaches fiducial-point analysis.** The structure of the table is that the closer
  the fitted component peaks lie to the fiducial points themselves, the better the tracking —
  which is an argument for measuring the fiducial points directly.

**Published conditions (table 4).** Applied unchanged to 624 subjects, none of the six
published protocols reached the fiducial-point value (0.705 in the same subset). The best was
0.578 (the gamma, three-component model recommended by Tigges 2017). For RI, one protocol
did exceed fiducial-point analysis: Couceiro's R1_d reached 0.585 against 0.501. Under the
prespecified rule this row is not taken into the verdict; §4.3 discusses why it is
nevertheless the one result consistent with the proposed mechanism.

### 3.4 Where the decomposition-derived index does respond

Main effects within strata (table 2) show that decomposition-derived ΔT is not inert. Its
largest single main effect is that of pulse wave velocity (−17.0%). What distinguishes it
from the fiducial-point index is the size of the competing effects.

| Factor | Fiducial ΔT | Decomposition ΔT | Am_b/Am_p1 |
|---|---|---|---|
| Aortic diameter | −9.4% | −12.6% | +2.0% |
| Heart rate | **−2.6%** | **−10.9%** | +4.0% |
| Ejection time | +4.6% | +0.7% | −1.1% |
| Mean arterial pressure | −15.1% | −7.7% | −4.0% |
| **Pulse wave velocity** | **−31.2%** | **−17.0%** | **−7.1%** |
| Stroke volume | +15.9% | −4.1% | −0.2% |

For fiducial ΔT the pulse-wave-velocity column is twelve times the heart-rate column; for the
decomposition it is 1.6 times. Ranking within a stratum reflects this: for decomposition ΔT
the correlation with heart rate (ρ = −0.54) is stronger than the correlation with pulse wave
velocity (ρ = −0.26). **The ordering of subjects is governed by heart rate rather than by the
property the index names.**

### 3.5 The response is not monotone

Single-factor sweeps (table 2b and figure 3) show that the pulse-wave-velocity row alone is not
monotone. Decomposition ΔT was 332.3, 352.8 and 251.2 ms at −1 SD, baseline and +1 SD: the
−1 SD step moves in the direction opposite to prediction. RI was 0.325, 0.254 and 0.647,
a U shape. The heart-rate and aortic-diameter rows are monotone. This reconciles the largest
main effect with the small rank correlation (ΔT: −17.0% main effect, ρ = −0.26; RI: +33.7%,
ρ = −0.17): **a rank correlation assumes monotonicity, and across a range that crosses the
turning point it cannot be established in principle.**

Inspection of the fitted beats indicates why. When the reflection moves forward into systole,
the second component latches onto a different physical feature — the late-systolic wave
rather than the diastolic wave — and the correspondence between component and event changes.
This is the concrete form of the caution raised by Epstein 2014 that fitted components need
not correspond to physical waves, and here it occurs in noiseless, ideal waveforms.

### 3.6 Waveform types and true transit times

Waveform types were: type 1 (notch present) 891 (20.4%), type 3 (inflection only) 3,378
(77.2%), type 4 (neither) 105 (2.4%). Decomposition verdicts rest on type 1 beats; type 3 was
read with fiducial points, the p1 construction and the upstroke ratio.

The model's true transit times were 96 ms (5th–95th centile 66–120) from the aortic root to
the digit and **8 ms (4–16)** from the radial artery to the digit, the latter spanning only
12 ms across all ages and all six factors at ±1 SD. Decomposition-derived ΔT tracked the true
transit time hardly at all (median within-stratum ρ = +0.19).

---

## 4. Discussion

### 4.1 What was and was not shown

Photoplethysmographic indices obtained by decomposing the pulse into component waves did not
track aortic pulse wave velocity or peripheral vascular resistance within age strata in a
population where both are known. Indices read directly from the same waveforms did. The
result is a statement about **extraction**, not about the waveform: the information was
present, and one family of methods recovered it while the other did not.

Two things this does not show. It does not show that decomposition is erroneous.
Decomposition-derived and fiducial-derived ΔT and RI are **structurally different
quantities**: the measured second peak height includes the tail of the forward wave, so
RI_PDA is systematically smaller and ΔT_PDA systematically larger than their fiducial
counterparts, as Goswami 2010 derived and observed. Our result is that, of these two
different quantities, only the latter tracked truth in this population. Nor does it show that
decomposition-derived indices carry no information: §3.4 shows a clear main effect of pulse
wave velocity. What they lack is **specificity**.

### 4.2 The result does not contradict the existing literature

The properties that the decomposition literature has established — goodness of fit,
robustness to noise and motion, and the return of a value when no notch is visible — were not
tested here and are not in question. They are, in our own subsequent work on recorded monitor
waveforms, reproduced. What was tested here is a different property, and one that the
published evaluation designs cannot detect.

The reason is structural. Because the fitting problem is ill-posed, many parameter
combinations give nearly the same residual, so **any criterion based on the residual is close
to invariant across those solutions while the parameters differ**. Our own data show the
consequence directly: adding components improved the fit and degraded the correlation with
truth (§3.3). A method may therefore be optimal by corrected AIC, by residual sum of squares
and by noise robustness, and still fail the test reported here.

Two features of the present design also make it more demanding than the designs used
previously, and both are deliberate. Correlations are computed **within age strata**, which
removes the common cause that drives both waveform shape and stiffness; published
correlations are pooled across wide age ranges. And the six factors are varied
**independently**, so confounders subtract from the apparent association instead of adding
to it, as they would in a cohort where diameter, heart rate and pulse wave velocity all
co-vary with age.

### 4.3 Mechanism

Five mechanisms are consistent with our observations; they are not exclusive and we have not
separated their contributions.

1. **Non-identifiability.** Parameters rest on search bounds in 87.4% of accepted gamma-route
   beats, and widening those bounds does not reduce the proportion (89–99%), so the pinning
   indicates that the parameters of this family are not identified in these beats rather than
   that the bounds themselves fix the answer. Adding components lowers the residual and the
   correlation together, and the same waveform yields ΔT values from 264 to 640 ms depending
   on the basis. When the problem is ill-posed, what the fit returns is decided as much by the
   design of the search as by the data.
2. **Non-monotone response** (§3.5), which alone is sufficient to defeat a rank criterion over
   a wide enough range.
3. **No physiological event corresponding to the second component.** If the second peak at the
   digital site is not a peripheral reflection [Epstein 2014; Hellqvist 2024], the fitted
   second component is a mathematical part with no reason for its position to track a
   vascular property. This is a defect of the premise, not of the model used here.
4. **Contamination by the forward-wave tail** [Goswami 2010], whose separation depends on how
   fast the chosen basis decays — another statement of mechanism 1.
5. **Degrees of freedom without information.** Fiducial-point analysis reads three points;
   decomposition fits 8 to 20 parameters and constructs two points from them. Additional
   parameters do not add information to the waveform, only error to the estimate.

The single row in which decomposition exceeded fiducial-point analysis is consistent with
this account. Couceiro's R1_d (§3.3) is the amplitude of a late component divided by the peak
of the reconstructed main forward wave, that is, a diastolic height **with the forward-wave
tail removed** — precisely the operation mechanism 4 describes. Decomposition appears to help
for that one operation and not for timing. Three cautions attach to it: in this model
peripheral resistance governs diastolic decay, so part of the association is built in
(a caution recorded in the frozen rules); RI-type indices require a diastolic peak, which is
often unavailable in recorded waveforms; and our reproduction carries the deviations listed
in table 4.

### 4.4 Why the criterion was stratified by age

A pooled correlation across a wide age range is inflated by the common dependence of both
variables on age, and in our data the within-stratum correlation of decomposition ΔT varies
from −0.14 in the youngest stratum to −0.61 in the oldest. The stratified criterion was not
chosen to be severe but to match the intended use. In the application that motivated this
work — correcting a calibration constant that already contains age and body size — an index
whose information is age adds nothing. **The question that has to be answered is whether two
subjects of the same age can be ordered by stiffness, and that is what a within-stratum rank
correlation asks.**

### 4.5 Limitations

The database is the output of a one-dimensional fluid model and contains **no optical
element**: tissue scattering, the venous component and the non-pulsatile component are
absent. A property of the real photoplethysmogram that decomposition captures optically would
not appear here. The waveforms are noiseless, single-beat and free of motion, so the noise
robustness claimed for decomposition cannot show itself; we note, however, that **this cannot
be the reason decomposition loses**, since fitting is easier without noise. The model
represents healthy ageing and contains no disease, anaesthesia or vasoactive drug. Charlton's
subsequent work reports that stiffness indices perform better in vivo than in silico, which
would counsel caution about generalising a negative — although in our hands the
fiducial-point indices performed *well* in silico, so that argument does not account for the
present negative. The literature replication retains deviations (optimiser and resampling
details) listed in table 4, and a different implementation by the original authors could
give different values. The non-monotonicity of §3.5 is visible because six factors are varied
independently at ±1 SD; whether a comparable range occurs in patients cannot be decided here.
Finally, the conclusion concerns the six published protocols and twelve bases tested, not
pulse decomposition in general.

### 4.6 Implications

For investigators building vascular indices from the photoplethysmogram, the practical point
is that **the criteria by which decomposition methods are usually selected cannot detect this
failure**, and that a construct-validity check against known truth is cheap: the database is
open and the analysis takes hours. Where the dicrotic notch is unavailable, an upstroke-only
index is an alternative that requires no diastolic feature and, in this population,
outperformed both families (0.836).

---

## 5. Conclusion

In a population of 4,374 virtual subjects with known vascular properties, photoplethysmographic
indices obtained by pulse decomposition did not track aortic pulse wave velocity or peripheral
vascular resistance under a decision rule fixed in advance, while indices read directly from
the same waveforms did. The negative was not attributable to implementation, to the basis
function or to published fitting conditions, and goodness of fit moved opposite to validity.
Decomposition-derived and fiducial-derived indices are different quantities; in this population
only the latter tracked truth.

---

## Figure legends

**Figure 1. What each family measures.** Schematic of a single beat, contrasting the
quantities formed by pulse decomposition analysis with those read directly at the fiducial
points.

**Figure 2. The fit is ill-posed.** Two decompositions of the same beat with almost the
same residual but the second component placed differently, and the resulting difference in
ΔT and RI.

**Figure 3. Single-factor sweeps.** Median index value within age stratum against each of
the six factors varied one at a time at three levels, showing that the pulse-wave-velocity
row alone is not monotone.

Figures are produced by the archived code; the underlying values are in tables 1 to 4.

## Statements

**Data availability.** The Pulse Wave Database is openly available at
doi:10.5281/zenodo.3275625. Analysis code, the prespecified decision document and all result
tables are archived at https://github.com/nobumitsu-3141/ppg-pda-analysis
(doi:10.5281/zenodo.22676039, release v1.0.0).
**Ethics.** Not required; no human participants or human data.
**Funding.** [[none / to declare]]
**Conflicts of interest.** [[author attestation]]
**Author contributions.** [[CRediT]]

---

## References (to be formatted to journal style)

Entries 1–9 are copied from the reference list of Paper 1, where they were verified against
PubMed/publisher records on 2026-08-30 (two corrections were applied there: the Sugo &
Ochiai journal, and the Basso author list and DOI). Entries 10–11 are **not yet verified**
and must be checked before submission.

1. Charlton PH, Mariscal Harana J, Vennin S, Li Y, Chowienczyk P, Alastruey J. Modeling
   arterial pulse waves in healthy aging: a database for in silico evaluation of
   hemodynamics and pulse wave indexes. *Am J Physiol Heart Circ Physiol*
   2019;317(5):H1062–H1085. PMID 31442381. doi:10.1152/ajpheart.00218.2019.
   Data: doi:10.5281/zenodo.3275625
2. Rubins U. Finger and ear photoplethysmogram waveform analysis by fitting with Gaussians.
   *Med Biol Eng Comput* 2008;46(12):1271–1276. PMID 18855034
3. Goswami D, Chaudhuri K, Mukherjee J. A new two-pulse synthesis model for digital volume
   pulse signal analysis. *Cardiovasc Eng* 2010;10(3):109–117. PMID 20734136
4. Wang L, Xu L, Feng S, Meng MQ-H, Wang K. Multi-Gaussian fitting for pulse waveform using
   weighted least squares and multi-criteria decision making method. *Comput Biol Med*
   2013;43(11):1661–1672. PMID 24209911. doi:10.1016/j.compbiomed.2013.08.004
5. Epstein S, Vergnaud AC, Elliott P, Chowienczyk P, Alastruey J. Numerical assessment of
   the stiffness index. *Annu Int Conf IEEE Eng Med Biol Soc* 2014;2014:1969–1972.
   PMID 25570367
6. Couceiro R, Carvalho P, Paiva RP, Henriques J, Quintal I, Antunes M, et al. Assessment of
   cardiovascular function from multi-Gaussian fitting of a finger photoplethysmogram.
   *Physiol Meas* 2015;36(9):1801–1825. PMID 26235798
7. Tigges T, Pielmus A, Klum M, Feldheiser A, Hunsicker O, Orglmeister R. Model selection
   for the pulse decomposition analysis of fingertip photoplethysmograms. *Annu Int Conf
   IEEE Eng Med Biol Soc* 2017;2017:4014–4017. PMID 29060777
8. Fleischhauer V, Ruprecht N, Sorelli M, Bocchi L, Zaunseder S. Pulse decomposition
   analysis in photoplethysmography imaging. *Physiol Meas* 2020;41(9):095009. PMID 33021236
9. Basso G, Haakma R, Vullings R. A skewed-Gaussian model for pulse decomposition analysis
   of photoplethysmography signals. *Physiol Meas* 2024;45(11):115006. PMID 39577084.
   doi:10.1088/1361-6579/ad9662
10. Hellqvist H, Karlsson M, Hoffman J, Kahan T, Spaak J. Estimation of aortic stiffness by finger photoplethysmography using enhanced pulse wave analysis and machine learning. Front Cardiovasc Med. 2024;11:1350726. doi:10.3389/fcvm.2024.1350726.
    *Verified 2026-09-07 against the publisher PDF held on file (citation block, page 1).*
11. Dawber TR, Thomas HE Jr, McNamara PM. Characteristics of the dicrotic notch of the arterial pulse wave in coronary heart disease. Angiology. 1973;24(4):244-255. PMID 4699520
    *Verified against PubMed on 2026-09-09 (PMID 4699520): authors, title, journal, year,
    volume, issue and pages all match. The second author is indexed as "Thomas HE Jr";
    Tigges 2017 renders the same author as "J. H. Emerson Thomas", which is incorrect.
    The citation is therefore primary, not secondary. The 1973 full text has not been read;
    it is cited only for the waveform classification, which Tigges reproduces.*

> Entries 1–9 were verified for Paper 1 on 2026-08-30; entry 10 was verified on 2026-09-07
> from the publisher PDF. Entry 11 is a secondary citation and is marked as such.
