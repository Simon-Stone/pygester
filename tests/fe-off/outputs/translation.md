# Translation (Scaffold)

## Status
Direct markdown translation pipeline not wired to LLM yet.

## Canonical plaintext excerpt

```
Conformal Off-Policy Evaluation in Markov Decision Processes

Daniele Foffano ∗ , Alessio Russo ∗ and Alexandre Proutiere

Abstract -Reinforcement Learning aims at identifying and evaluating efficient control policies from data. In many realworld applications, the learner is not allowed to experiment and cannot gather data in an online manner (this is the case when experimenting is expensive, risky or unethical). For such applications, the reward of a given policy (the target policy) must be estimated using historical data gathered under a different policy (the behavior policy). Most methods for this learning task, referred to as Off-Policy Evaluation (OPE), do not come with accuracy and certainty guarantees. We present a novel OPE method based on Conformal Prediction that outputs an interval containing the true reward of the target policy with a prescribed level of certainty. The main challenge in OPE stems from the distribution shift due to the discrepancies between the target and the behavior policies. We propose and empirically evaluate different ways to deal with this shift. Some of these methods yield conformalized intervals with reduced length compared to existing approaches, while maintaining the same certainty level.
I. INTRODUCTION

In this work, we consider the problem of off-policy evaluation (OPE) in finite time-horizon Markov Decision Processes (MDPs). This problem is concerned with the task of learning the expected cumulative reward of a target policy from data gathered under a different behavior policy. In fact, OPE has attracted a lot of attention recently [10], [23], [19], [25], [5], [15] since it is particularly relevant in real-world scenarios where the learner is not allowed to experiment and deploy the target policy to infer its value. In these scenarios, testing a new policy in an online manner can be indeed too risky or unethical (e.g., in finance or healthcare).

The main challenge in OPE algorithms stems from the distribution shift of the target and behavior policies. To address this issue, researchers have developed various solutions, often based on Importance Sampling methods (refer to §II and to [29] for a recent survey). Lastly, while existing OPE algorithms sometimes enjoy asymptotic convergence properties, most of them do not come with accuracy and certainty guarantees [25], [26], [7].

To that aim, we are concerned with devising OPE estimators that enjoy non-asymptotic performance guarantees. We leverage techniques from Conformal Prediction (CP) [30], [28], [21], which, directly from the data, allow to build conformalized sets that provably includes the true value of the quantity to be estimated with a prescribed level of certainty. Furthermore, CP is a distribution-free method, thus circumventing the burden of estimating a model while providing non-asymptotic guarantees. Due to these desirable properties, CP has been applied with success in many fields, including medicine [14], [33], [16], aerospace engineering [
```

## Next
- integrate translation prompt template
- section-by-section transform
- preserve equations/tables/citations with provenance
