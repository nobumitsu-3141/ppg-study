# -*- coding: utf-8 -*-
"""参考文献レジストリ（1–29 は既存デックの番号を保存、30 以降が今回追加）"""

REFS = {
 1: "Allen J. Photoplethysmography and its application in clinical physiological measurement. Physiol Meas 2007;28:R1–39.",
 2: "Politi MT, et al. The dicrotic notch analyzed by a numerical model. Comput Biol Med 2016;72:54–64.",
 3: "Stergiopulos N, Westerhof BE, Westerhof N. Total arterial inertance as the fourth element of the windkessel model. Am J Physiol 1999;276:H81–8.",
 4: "Millasseau SC, et al. Determination of age-related increases in large artery stiffness by digital pulse contour analysis. Clin Sci (Lond) 2002;103:371–7.",
 5: "Dawber TR, Thomas HE, McNamara PM. Characteristics of the dicrotic notch of the arterial pulse wave in coronary heart disease. Angiology 1973;24:244–55.",
 6: "Cunningham JW, et al. Machine learning to understand genetic and clinical factors associated with the pulse waveform dicrotic notch. Circ Genom Precis Med 2023;16:e003676.",
 7: "Wilkinson IB, et al. The influence of heart rate on augmentation index and central arterial pressure in humans. J Physiol 2000;525:263–70.",
 8: "Alian AA, et al. Impact of central hypovolemia on photoplethysmographic waveform parameters in healthy volunteers. Part 1: time domain analysis. J Clin Monit Comput 2011;25:377–85.",
 9: "Cannesson M, et al. Relation between respiratory variations in pulse oximetry plethysmographic waveform amplitude and arterial pulse pressure in ventilated patients. Crit Care 2005;9:R562–8.",
10: "Pagoulatou S, et al. The effect of left ventricular contractility on arterial hemodynamics: a model-based investigation. PLoS One 2021;16(8):e0255561.",
11: "Couceiro R, et al. Multi-Gaussian fitting for the assessment of left ventricular ejection time from the photoplethysmogram. Annu Int Conf IEEE EMBC 2012;2012:3951–4.",
12: "Piccioli F, et al. The effect of cardiac properties on arterial pulse waves: an in-silico study. Int J Numer Method Biomed Eng 2022;38(12):e3658.",
13: "Awad AA, et al. The relationship between the photoplethysmographic waveform and systemic vascular resistance. J Clin Monit Comput 2007;21:365–72.",
14: "Tusman G, et al. Photoplethysmographic characterization of vascular tone mediated changes in arterial pressure: an observational study. J Clin Monit Comput 2019;33:815–24.",
15: "Chowienczyk PJ, et al. Photoplethysmographic assessment of pulse wave reflection: blunted response to endothelium-dependent β2-adrenergic vasodilation in type II diabetes mellitus. J Am Coll Cardiol 1999;34:2007–14.",
16: "Takazawa K, et al. Assessment of vasoactive agents and vascular aging by the second derivative of the photoplethysmogram waveform. Hypertension 1998;32:365–70.",
17: "Murray WB, Foster PA. The peripheral pulse wave: information overlooked. J Clin Monit 1996;12:365–77.",
18: "Bortolotto LA, et al. Assessment of vascular aging and atherosclerosis in hypertensive subjects: second derivative of photoplethysmogram versus pulse wave velocity. Am J Hypertens 2000;13:165–71.",
19: "Hashimoto J, et al. Pulse wave velocity and the second derivative of the finger photoplethysmogram in treated hypertensive patients. J Hypertens 2002;20:2415–22.",
20: "Joachim J, et al. Real-time estimation of mean arterial blood pressure based on photoplethysmography dicrotic notch and perfusion index: a pilot study. J Clin Monit Comput 2021;35:395–404.",
21: "Middleton PM, et al. Fingertip photoplethysmographic waveform variability and systemic vascular resistance in intensive care unit patients. Med Biol Eng Comput 2011;49:859–66.",
22: "Elgendi M. On the analysis of fingertip photoplethysmogram signals. Curr Cardiol Rev 2012;8:14–25.",
23: "Charlton PH, et al. Modeling arterial pulse waves in healthy aging: a database for in silico evaluation of hemodynamics and pulse wave indexes. Am J Physiol Heart Circ Physiol 2019;317:H1062–85.",
24: "Md Lazim MR, et al. Is heart rate a confounding factor for photoplethysmography markers? A systematic review. Int J Environ Res Public Health 2020;17:2591.",
25: "Aoyagi T. Pulse oximetry: its invention, theory, and future. J Anesth 2003;17:259–66.",
26: "Chan ED, Chan MM, Chan MM. Pulse oximetry: understanding its basic principles facilitates appreciation of its limitations. Respir Med 2013;107:789–99.",
27: "Millasseau SC, Kelly RP, Ritter JM, Chowienczyk PJ. The vascular impact of aging and vasoactive drugs: comparison of two digital volume pulse measurements. Am J Hypertens 2003;16:467–72.",
28: "Padilla JM, et al. Pulse wave velocity and digital volume pulse as indirect estimators of blood pressure: pilot study on healthy volunteers. Cardiovasc Eng 2009;9:104–12.",
29: "Coutrot M, et al. Noninvasive continuous detection of arterial hypotension during induction of anaesthesia using a photoplethysmographic signal: proof of concept. Br J Anaesth 2019;122:605–12.",
# ---- 今回追加（スライドで引用済みだが文献表に無かったもの／PDA 章の新規） ----
30: "Otsuka T, et al. Utility of second derivative of the finger photoplethysmogram for the estimation of the risk of coronary heart disease in the general population. Circ J 2006;70:304–10.",
31: "von Wowern E, Östling G, Nilsson PM, Olofsson P. Digital photoplethysmography for assessment of arterial stiffness: repeatability and comparison with applanation tonometry. PLoS One 2015;10(8):e0135659.",
32: "Tabara Y, et al. Usefulness of the second derivative of the finger photoplethysmogram for assessment of end-organ damage: the J-SHIPP study. Hypertens Res 2016;39:552–6.",
33: "Elgendi M, et al. Detection of a and b waves in the acceleration photoplethysmogram. Biomed Eng Online 2014;13:139.",
34: "Kohjitani A, et al. Responses of the second derivative of the finger photoplethysmogram indices and hemodynamic parameters to anesthesia induction. Hypertens Res 2012;35:53–60.",
35: "Lee QY, et al. Multivariate classification of systemic vascular resistance using photoplethysmography. Physiol Meas 2011;32:1117–32.",
36: "Wu HT, et al. Novel application of parameters in waveform contour analysis for assessing arterial stiffness in aged and atherosclerotic subjects. Atherosclerosis 2010;213:173–7.",
37: "Fry A, et al. Comparison of sociodemographic and health-related characteristics of UK Biobank participants with those of the general population. Am J Epidemiol 2017;186:1026–34.",
38: "Pal R, et al. An algorithm to detect dicrotic notch in arterial blood pressure and photoplethysmography waveforms using the iterative envelope mean method. Comput Methods Programs Biomed 2024;254:108283.",
39: "Rubins U. Finger and ear photoplethysmogram waveform analysis by fitting with Gaussians. Med Biol Eng Comput 2008;46:1271–6.",
40: "Goswami D, et al. A new two-pulse synthesis model for digital volume pulse signal analysis. Cardiovasc Eng 2010;10:109–17.",
41: "Couceiro R, et al. Assessment of cardiovascular function from multi-Gaussian fitting of a finger photoplethysmogram. Physiol Meas 2015;36:1801–25.",
42: "Tigges T, et al. Model selection for the pulse decomposition analysis of fingertip photoplethysmograms. Annu Int Conf IEEE EMBC 2017;2017:4014–7.",
43: "Fleischhauer V, et al. Pulse decomposition analysis in photoplethysmography imaging. Physiol Meas 2020;41:095009.",
44: "Basso G, et al. A skewed-Gaussian model for pulse decomposition analysis of photoplethysmography signals. Physiol Meas 2024;45(11):125005.",
45: "Baruch MC, et al. Validation of the pulse decomposition analysis algorithm using central arterial blood pressure. Biomed Eng Online 2014;13:96.",
46: "Epstein S, et al. Numerical assessment of the stiffness index. Annu Int Conf IEEE EMBC 2014;2014:1969–72.",
47: "Attivissimo F, et al. Photoplethysmography signal wavelet enhancement and novel features selection for non-invasive cuff-less blood pressure monitoring. Sensors 2023;23:2321.",
48: "Domínguez-Hernández S, Páez G, Padilla M. Harmonic-selective Gaussian filtering for morphology and timing preservation in PPG signals. Sensors 2026;26:3710.",
49: "Sološenko A, Petrėnas A, Marozas V, Sörnmo L. Modeling of the photoplethysmogram during atrial fibrillation. Comput Biol Med 2017;81:130–8.",
50: "Shin H, Noh G, Choi BM. Photoplethysmogram based vascular aging assessment using the deep convolutional neural network. Sci Rep 2022;12:11377.",
51: "Vargas JM, et al. Assessment of pulse wave velocity through weighted visibility graph metrics from photoplethysmographic signals. Sci Rep 2025;15:31128.",
53: "Ahmed A, et al. Hemoglobin oxygen saturation discrepancy using various methods in patients with sickle cell vaso-occlusive painful crisis. Eur J Haematol 2005;74:309–14.",
52: "Grabovskis A, et al. Two-stage multi-Gaussian fitting of conduit artery photoplethysmography waveform during induced unilateral hemodynamic events. J Biomed Opt 2015;20:035004.",
}

SHORT = {
 1: "Allen 2007", 2: "Politi 2016", 3: "Stergiopulos 1999", 4: "Millasseau 2002",
 5: "Dawber 1973", 6: "Cunningham 2023", 7: "Wilkinson 2000", 8: "Alian 2011",
 9: "Cannesson 2005", 10: "Pagoulatou 2021", 11: "Couceiro 2012", 12: "Piccioli 2022",
13: "Awad 2007", 14: "Tusman 2019", 15: "Chowienczyk 1999", 16: "Takazawa 1998",
17: "Murray 1996", 18: "Bortolotto 2000", 19: "Hashimoto 2002", 20: "Joachim 2021",
21: "Middleton 2011", 22: "Elgendi 2012", 23: "Charlton 2019", 24: "Md Lazim 2020",
25: "Aoyagi 2003", 26: "Chan 2013", 27: "Millasseau 2003", 28: "Padilla 2009",
29: "Coutrot 2019", 30: "Otsuka 2006", 31: "von Wowern 2015", 32: "Tabara 2016",
33: "Elgendi 2014", 34: "Kohjitani 2012", 35: "Lee 2011", 36: "Wu 2010",
37: "Fry 2017", 38: "Pal 2024", 39: "Rubins 2008", 40: "Goswami 2010",
41: "Couceiro 2015", 42: "Tigges 2017", 43: "Fleischhauer 2020", 44: "Basso 2024",
45: "Baruch 2014", 46: "Epstein 2014", 47: "Attivissimo 2023", 48: "Domínguez-Hernández 2026",
49: "Sološenko 2017", 50: "Shin 2022", 51: "Vargas 2025", 52: "Grabovskis 2015", 53: "Ahmed 2005",
}


def cite(*nums, note=None):
    """統一書式の出典文字列を組み立てる： '4. Millasseau 2002　／　16. Takazawa 1998'"""
    s = "　／　".join(f"{n}. {SHORT[n]}" for n in nums)
    if note:
        s += f"（{note}）"
    return s
