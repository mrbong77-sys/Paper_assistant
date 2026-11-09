---
title: "Logistic regression versus nearest-centroid classification under class overlap: a synthetic benchmark"
---

<!-- identifying -->
Authors: Demo Author (Example University). This example manuscript is fictional and was written to show the Paper Assistant workflow.
<!-- /identifying -->

# Abstract

Practitioners often assume that a fitted linear model such as logistic regression classifies better than a nearest-centroid rule when classes overlap. This assumption was tested on synthetic two-class Gaussian data with equal, isotropic covariance and class separations of 0.5 to 3.0 standard deviations. Each of {{num:n_seeds}} fixed seeds gave {{num:n_train}} training points and {{num:n_test}} test points per separation. Logistic regression did not outperform the nearest-centroid rule. The nearest-centroid rule was more accurate in {{num:sign_neg}} of {{num:n_cells}} runs and logistic regression in {{num:sign_pos}} (exact sign test, p = {{num:sign_p}}). The mean differences stayed within half a point at every separation. Both classifiers were within {{num:max_gap_bayes}} of the Bayes-optimal accuracy. Under equal isotropic covariance, the nearest-centroid rule is therefore a sufficient baseline.

**Keywords:** binary classification; baseline selection; class overlap; synthetic benchmark

# 1. Introduction

Choosing a baseline classifier for a small labelled dataset is a routine decision. Logistic regression [@Cox1958] is a common default because it fits a decision boundary to the data, whereas a nearest-centroid rule only compares distances to the class means. When two classes share one isotropic covariance, however, the Bayes decision boundary is the perpendicular bisector of the two means. The nearest-centroid rule uses this boundary, and it is also the linear discriminant of @Fisher1936 for this covariance.

It is therefore not clear whether the extra flexibility of logistic regression improves test accuracy when classes overlap, or only adds estimation noise. This study asks two research questions (RQs). RQ1: for class separations of 0.5 to 3.0 standard deviations, is the test accuracy of logistic regression higher than that of a nearest-centroid rule? RQ2: how far is each classifier from the Bayes-optimal accuracy?

The contributions are a controlled comparison on synthetic data, an exact paired test over all runs, and the gap of both classifiers to the Bayes-optimal accuracy.

# 2. Methods

**Data.** Each run drew two balanced classes in two dimensions with standard deviation 1 in both coordinates. The class means differed by d along the first coordinate, with d in {0.5, 1.0, 1.5, 2.0, 3.0}. Each of the {{num:n_cells}} runs (five separations, {{num:n_seeds}} seeds) used {{num:n_train}} training points and {{num:n_test}} test points from the same generator.

**Classifiers.** Logistic regression was fitted by batch gradient descent (300 iterations, learning rate 0.5) with a decision threshold of 0.5. The nearest-centroid rule assigned each test point to the class with the closer training mean.

**Analysis.** The primary measure was test accuracy. For each separation, the mean and the standard deviation over seeds were computed. The per-run differences (logistic regression minus nearest centroid) were compared with an exact two-sided sign test, ties excluded. The Bayes-optimal accuracy for separation d is Φ(d/2).

# 3. Results

Logistic regression was not more accurate than the nearest-centroid rule at any separation (Table 1, Figure 1). Over all runs, the nearest-centroid rule was more accurate in {{num:sign_neg}} runs, logistic regression in {{num:sign_pos}}, and {{num:sign_ties}} runs were tied (exact sign test, p = {{num:sign_p}}). The mean difference ranged from {{num:diff_d2p0}} to {{num:diff_d1p5}}.

| Separation d | Logistic regression | Nearest centroid | Difference | Bayes-optimal |
|---|---|---|---|---|
| 0.5 | {{num:acc_lr_d0p5}} | {{num:acc_nc_d0p5}} | {{num:diff_d0p5}} | {{num:acc_bayes_d0p5}} |
| 1.0 | {{num:acc_lr_d1p0}} | {{num:acc_nc_d1p0}} | {{num:diff_d1p0}} | {{num:acc_bayes_d1p0}} |
| 1.5 | {{num:acc_lr_d1p5}} | {{num:acc_nc_d1p5}} | {{num:diff_d1p5}} | {{num:acc_bayes_d1p5}} |
| 2.0 | {{num:acc_lr_d2p0}} | {{num:acc_nc_d2p0}} | {{num:diff_d2p0}} | {{num:acc_bayes_d2p0}} |
| 3.0 | {{num:acc_lr_d3p0}} | {{num:acc_nc_d3p0}} | {{num:diff_d3p0}} | {{num:acc_bayes_d3p0}} |

Table 1. Mean test accuracy over five seeds. Difference: logistic regression minus nearest centroid, computed before rounding.

![Figure 1. Test accuracy against class separation. Points are means over five seeds; error bars are one standard deviation; the dotted line is the Bayes-optimal accuracy.](../06_figures/out/fig1_accuracy.png)

Both classifiers stayed within {{num:max_gap_bayes}} of the Bayes-optimal accuracy at every separation.

# 4. Discussion

The answer to RQ1 is negative. With equal isotropic covariance, logistic regression gave no accuracy gain over the nearest-centroid rule, and the nearest-centroid rule was slightly more accurate in most runs. This agrees with the shape of the Bayes rule for this covariance, which the nearest-centroid rule matches with fewer estimated parameters. For RQ2, both classifiers were close to the Bayes-optimal accuracy, so neither had much room to improve.

The comparison is limited to two-dimensional, equal-covariance Gaussian classes. With unequal covariances or correlated features the nearest-centroid boundary is no longer the Bayes boundary, and the result may differ; that setting needs its own test. Both classifiers are available in standard libraries such as scikit-learn [@Pedregosa2011], so the benchmark can be extended to those settings.

# 5. Conclusions

Under equal isotropic covariance, a nearest-centroid rule is a sufficient baseline for binary classification with overlapping classes: logistic regression did not improve test accuracy at any of five separations. A study with unequal covariances would show where the extra flexibility of logistic regression begins to pay off.

# Declarations

<!-- identifying -->
**Author contributions.** Demo Author designed the study, ran the analysis and wrote the manuscript.
**Funding.** None.
**Competing interests.** None.
<!-- /identifying -->
**Data and code availability.** The data are generated by `05_data/scripts/run_benchmark.py` with fixed seeds; all numbers come from `05_data/numbers.csv`.
**Use of generative AI.** Claude (Anthropic) was used to draft and edit the text and to write the analysis scripts; the author checked every number against the result files.

# References
