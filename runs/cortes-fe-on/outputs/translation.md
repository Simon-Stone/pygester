# Translation (Scaffold)

## Status
Direct markdown translation pipeline not wired to LLM yet.

## Canonical plaintext excerpt

```
UTILITY-DIRECTED CONFORMAL PREDICTION: A DECISION-AWARE FRAMEWORK FOR ACTIONABLE UNCERTAINTY QUANTIFICATION

Santiago Cortes-Gomez, Carlos Pati˜ no ∗ , Yewon Byun, Zhiwei Steven Wu, Eric Horvitz † &amp;Bryan Wilder

Machine Learning Department, Carnegie Mellon University

∗ University of Amsterdam

† Microsoft

{ scortesg, yewonb, zstevenwu, bwilder } @cs.cmu.edu

carlos.patino.paz@student.uva.nl

horvitz@microsoft.com
ABSTRACT

Interest has been growing in decision-focused machine learning methods which train models to account for how their predictions are used in downstream optimization problems. Doing so can often improve performance on subsequent decision problems. However, current methods for uncertainty quantification do not incorporate any information about downstream decisions. We develop a methodology based on conformal prediction to identify prediction sets that account for a downstream cost function, making them more appropriate to inform high-stakes decision-making. Our approach harnesses the strengths of conformal methods-modularity, model-agnosticism, and statistical coverage guarantees-while incorporating downstream decisions and user-specified utility functions. We prove that our methods retain standard coverage guarantees. Empirical evaluation across a range of datasets and utility metrics demonstrates that our methods achieve significantly lower costs than standard conformal methods. We present a real-world use case in healthcare diagnosis, where our method effectively incorporates the hierarchical structure of dermatological diseases. The method successfully generates sets with coherent diagnostic meaning, potentially aiding triage for dermatology diagnosis and illustrating how our method can ground high-stakes decision-making employing domain knowledge.
1 INTRODUCTION

Uncertainty quantification in classification problems is increasingly addressed through a model-agnostic technique known as conformal prediction Vovk et al. (2005); Angelopoulos &amp; Bates (2021). Instead of outputting a single label and confidence, conformal prediction outputs a set of outcomes with guaranteed statistical coverage, ensuring that the true outcome is included in the set with a pre-specified, target confidence level. This procedure for quantifying uncertainty through inference about sets of outcomes, has been leveraged to enable safer decision-making based on machine learning model outputs. As an example, in dermatology diagnosis, a conformal analysis might predict that the patient's illness is a member of a set of possible mutually exclusive classes, such as [eczema or psoriasis]. That is, a guarantee is provided that the true condition is highly likely to be included in the predicted set, making inference about the set a more robust estimate than raw model outputs about singular outcomes. Recent efforts have pursued uses of conformal prediction to develop AI systems that can support decisions in high-stakes situations (Vemula et al., 2018; Dvij
```

## Next
- integrate translation prompt template
- section-by-section transform
- preserve equations/tables/citations with provenance
