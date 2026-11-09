# Response to the editor and reviewers

Manuscript: JES-2026-0001 (fictional) — "Logistic regression versus nearest-centroid classification under class overlap: a synthetic benchmark", Journal of Example Studies (fictional)

Thank you for the careful reading. Each comment is answered below, with the location of every change in the revised manuscript. Section, table and figure numbers refer to the revised version.

## Editor

| # | Comment | Response | Change in the manuscript | Status |
|---|---|---|---|---|
| E.1 | Please shorten the abstract to at most 150 words and make sure the conclusion is limited to the tested covariance setting. | The abstract was shortened from 120 to 101 words and its last sentence now limits the conclusion to equal isotropic covariance. | Abstract | Done |

## Reviewer 1

| # | Comment | Response | Change in the manuscript | Status |
|---|---|---|---|---|
| R1.1 | The paper should test unequal covariances, where logistic regression is expected to help. | The question is important, and the revised Discussion now explains why the result is expected to change with unequal covariances: the Bayes boundary is then no longer the perpendicular bisector of the means. A full experiment with unequal covariances would change the scope of this short communication, so it is named as the next controlled comparison rather than added here. | Section 4, second paragraph | Partly done |
| R1.2 | The introduction attributes the equivalence between the nearest-centroid boundary and the Bayes boundary to Fisher (1936). Fisher derived the linear discriminant; the equivalence under isotropic covariance is a consequence, not his statement. | Agreed. The sentence now states that the equivalence follows from the linear discriminant of Fisher (1936) under isotropic covariance, instead of attributing the equivalence to Fisher. | Section 1, first paragraph, last two sentences | Done |

## Reviewer 2

| # | Comment | Response | Change in the manuscript | Status |
|---|---|---|---|---|
| R2.1 | Table 1 reports means only. Please add the standard deviations over seeds. | Table 1 now gives the mean ± standard deviation over the five seeds for both classifiers. | Table 1 and its caption | Done |

## Changes made without a request

| # | Change | Reason | Location | In the paper |
|---|---|---|---|---|
| O1 | Re-ran run_benchmark.py and make_ledger.py from a clean folder before resubmission; every number in the ledger was unchanged. | Check that the revised manuscript still matches the result files. | — | No (record only) |
