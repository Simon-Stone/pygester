## Conformal Off-Policy Evaluation in Markov Decision Processes

Daniele Foffano ∗ , Alessio Russo ∗ and Alexandre Proutiere

Abstract -Reinforcement Learning aims at identifying and evaluating efficient control policies from data. In many realworld applications, the learner is not allowed to experiment and cannot gather data in an online manner (this is the case when experimenting is expensive, risky or unethical). For such applications, the reward of a given policy (the target policy) must be estimated using historical data gathered under a different policy (the behavior policy). Most methods for this learning task, referred to as Off-Policy Evaluation (OPE), do not come with accuracy and certainty guarantees. We present a novel OPE method based on Conformal Prediction that outputs an interval containing the true reward of the target policy with a prescribed level of certainty. The main challenge in OPE stems from the distribution shift due to the discrepancies between the target and the behavior policies. We propose and empirically evaluate different ways to deal with this shift. Some of these methods yield conformalized intervals with reduced length compared to existing approaches, while maintaining the same certainty level.

## I. INTRODUCTION

In this work, we consider the problem of off-policy evaluation (OPE) in finite time-horizon Markov Decision Processes (MDPs). This problem is concerned with the task of learning the expected cumulative reward of a target policy from data gathered under a different behavior policy. In fact, OPE has attracted a lot of attention recently [10], [23], [19], [25], [5], [15] since it is particularly relevant in real-world scenarios where the learner is not allowed to experiment and deploy the target policy to infer its value. In these scenarios, testing a new policy in an online manner can be indeed too risky or unethical (e.g., in finance or healthcare).

The main challenge in OPE algorithms stems from the distribution shift of the target and behavior policies. To address this issue, researchers have developed various solutions, often based on Importance Sampling methods (refer to §II and to [29] for a recent survey). Lastly, while existing OPE algorithms sometimes enjoy asymptotic convergence properties, most of them do not come with accuracy and certainty guarantees [25], [26], [7].

To that aim, we are concerned with devising OPE estimators that enjoy non-asymptotic performance guarantees. We leverage techniques from Conformal Prediction (CP) [30], [28], [21], which, directly from the data, allow to build conformalized sets that provably includes the true value of the quantity to be estimated with a prescribed level of certainty. Furthermore, CP is a distribution-free method, thus circumventing the burden of estimating a model while providing non-asymptotic guarantees. Due to these desirable properties, CP has been applied with success in many fields, including medicine [14], [33], [16], aerospace engineering [32], finance [31] and safe motion planning [13].

∗ Equal contribution

Daniele Foffano, Alessio Russo and Alexandre Proutiere are in the Division of Decision and Control Systems of the EECS School at KTH Royal Institute of Technology, Stockholm, Sweden. {foffano,alessior,alepro}@kth.se

Nevertheless, standard CP assumes to be trained on i.i.d. data, and that at test time the data comes from the same distribution from which the training data was drawn (a.k.a. as distribution/covariates shift ). This latter assumption is violated in OPE problems, since the training data is gathered using a policy than is different from the target policy to be evaluated. A solution to address the distribution shift is to leverage the concept of weighted exchangeability [28], [12].

By exploiting the concept of weighted exchengeability, we study the conformalized OPE problem for Markov Decision Processes (MDPs). Our method builds on top of the technique described in [24], which introduces conformalized OPE for contextual bandit models (which can be seen as MDPs with i.i.d. states). Compared to [24], we have to handle additional difficulties, including the inherent dependence in the data (which consists of trajectories of a controlled Markov chain) and the statistical hardness of dealing with the distribution shift when the time horizon grows large.

Contribution-wise, we present and empirically evaluate CP algorithms that yield conformalized intervals with reduced length compared to existing approaches, while maintaining the same certainty level. These algorithms are based on the two following new components. (i) Asymmetric score functions: existing CP approaches use symmetric score functions and hence, for our problem, would output conformalized intervals centered on the value of the behavior policy. We introduce asymmetric score functions, so that the CP algorithm yields an interval that efficiently moves its center to follow the distribution shift. In turn, CP with asymmetric score functions results in intervals of smaller size. (ii) We propose methods to address the distribution shift in MDPs.

We finally illustrate the performance of our algorithms numerically on the classical inventory control problem [20]. The experiments demonstrate that indeed our algorithms achieve smaller interval lengths than existing approaches, while retaining the same certainty guarantees.

## II. RELATED WORK

A. Off-Policy Evaluation (OPE)

There are mainly three classes of OPE algorithms in the literature: Direct, Importance Sampling and Doubly Robust Methods. Direct Methods (DMs) learn a model of the system [10], [23] and then evaluate the policy against it. DMs can lead to biased estimators due to a mismatch between the model and the true system. Importance Sampling (IS) is a well-known method [19], [25], [5], [15] used to correct the distribution mismatch caused by the discrepancies between the target and the behavior policies by re-weighting the sampled rewards. Still, IS-based algorithms suffer from high variance in long-horizon problems. Doubly Robust (DR) methods combine DMs and IS to obtain more robust estimators [7], [6]. [15] introduce Marginalized Importance Sampling, reducing the variance by applying IS directly on the stationary statevisitation distribution.

The aforementioned approaches only provide an accurate point-wise estimate of the policy value, without quantifying its uncertainty. [1] derived confidence intervals (CIs) using the Central Limit Theorem. In [25], [9], the authors leveraged concentration inequalities to estimate good CIs, which, however, tend to be overly-conservative. For short-horizon problems, [26], [5] approximate CIs for OPE can also be found by means of bootstrapping. [22] derives a non-asymptotic CI using concentration bounds on a kernel-based Q-function.

In [8], the authors derive an asymptotic CI using Double Reinforcement Learning (DRL), also addressing the curse of the horizon. However, the DRL method might not converge in high-dimensional RL tasks, resulting in an asymptotically biased estimator. [3], [23] derive non-asymptotic and asymptotic CIs by approximating the value function with linear functions, but their approaches might lead to a biased estimator if the model assumption is incorrect. [7] derived a CI that involves solving a linear program, but they assume the observations to be i.i.d., whereas transitions are time-dependent in many RL problems.

## B. Conformal Prediction (CP)

CP is a frequentist technique to derive CIs with a specified coverage ( i.e. , confidence) and a finite number of i.i.d. samples (we refer the reader to [17] for a comprehensive list of CP-related papers). The advantage of CP with respect to other methods is that the provided coverage guarantees are distribution-free and non-asymptotic.

CP for off-policy evaluation has been recently applied to the contextual bandit setting [24], which, in contrast to our work, has no dynamics and no time-dependent data. To address the distribution shift, the authors in [24] use of the weighted exchangeability property, which was previously introduced in [28]. In [2], the authors apply CP to predict the expected value of MDPs trajectories. They consider an online setting where they do not have to deal with the distribution shift.

## III. PRELIMINARIES

## A. Off-policy evaluation in Markov Decision Processes

We consider finite-time horizon MDPs [20]. Such an MDP is defined by a tuple M = 〈X , A , T, q, p, H 〉 , where X and A are the (finite) state and action spaces, respectively. For all ( x, a ) ∈ X×A , T ( ·| x, a ) and q ( ·| x, a ) denote the distributions of the next state and of the instantaneous reward given that the current state is x and that the decision maker selects action a (for simplicity, we assume that the transition probabilities and the reward distributions are stationary; our results can be easily generalized to non-stationary dynamics and rewards). Finally, p ∈ ∆( S ) denotes the distribution of the initial state, and H the time horizon.

In off-policy evaluation, we gather data using a behavior policy π b , and we wish to estimate the value function of different policy π . Here again for simplicity, we consider stationary policies: both π b and π are mappings between the state space and the set ∆( A ) of distributions over actions. The value function of π maps the initial state x to the expected reward gathered under π when starting in x : V π H ( x ) = E π [ ∑ H t =1 r t | x 1 = x ] , where r t ∼ q ( ·| x t , a t ) , a t ∼ π ( ·| x t ) , and x t +1 ∼ T ( ·| x t , a t ) for t = 1 , . . . , H .

## B. Standard Conformal Prediction

Conformal Prediction (CP) is a method for distributionfree uncertainty quantification of learning methods, see e.g. [30], [18], [11]. To illustrate how CP works, we consider classical supervised learning tasks and restrict our attention to split CP where the pre-training and the calibration phases are conducted on different datasets. The learner starts with a pretrained model ˆ f : X → Y that maps inputs to predicted labels (this model may also consist of upper and lower estimated quantiles if the pre-training procedure corresponds to quantile regression). She also has i.i.d. calibration data D cal = { X i , Y i } n i =1 i.i.d. ∼ P X,Y . From ˆ f and D cal , CP constructs for each possible input x a subset ˆ C n ( x ) of possible labels. More precisely, the method proceeds as follows: (i) first a score function s : X × Y → R is constructed from the model ˆ f (e.g., it could be the residuals | y -ˆ f ( x ) | if Y ⊂ R ); (ii) the scores of the various calibration samples are computed V i = s ( X i , Y i ) , and (iii) the confidence set is built according to ˆ C n ( x ) = { y ∈ Y : s ( x, y ) ≤ η } , where η = Quantile 1 -α ( 1 n +1 (∑ n i =1 δ V i + δ {∞} ) ) . If ( X 1 , Y 1 ) , . . . , ( X n +1 , Y n +1 ) are exchangeable, this construction ensures coverage with certainty level 1 -α :

<!-- formula-not-decoded -->

## IV. CONFORMALIZED OFF-POLICY EVALUATION

Our objective is to get conformalized predictions for the value function of a policy π , based on training and calibration data gathered under a different behavior policy π b . We address this distribution shift by extending and improving the techniques developed in [28], [24]. We apply the CP formalism where the input X corresponds to the initial state, and the output Y to V π H ( X ) . Our method is illustrated in Figure 1. Next, we describe its components in detail. Specifically, (i) we explain how the aforementioned distribution shift can be addressed by weighing scores; (ii) we then discuss the important choice of the score function.

## A. Weighted conformal prediction

As suggested [28], [24], we can handle the distribution shift by weighing the scores using estimates of the likelihood ratio

<!-- formula-not-decoded -->

Fig. 1. Conformal prediction for off-policy evaluation. The dataset D is collected using a behavior policy π b , which is then split into the training D tr and calibration D cal datasets. When evaluating a different policy π , there is a shift in the data distribution, and we need to learn a likelihood ratios ˆ w to compensate for this shift. The training data is used to learn estimates of the weights ˆ w and a model ˆ f used in the computation of the scores. The estimated weights are used as plug-in estimates to re-weight the cumulative distribution function of the scores ˆ F x,y n , which is then used to compute the conformalized intervals ˆ C n ( x ) .

<!-- image -->

where for any policy π ′ ∈ { π, π b } , P π ′ X,Y ( x, y ) = P π ′ Y | X ( y | x ) p ( x ) denotes the distribution of the observation ( X,Y ) under π ′ ( P π ′ Y | X is this distribution given X ), and p ( x ) is the initial state distribution, which is the same in both cases. The value of a given trajectory τ = { x 1 , a 1 , r 1 , . . . , x H , a H , r H } is y = ∑ H t =1 r t . For any policy π ′ ∈ { π, π b } , the probability of observing τ under π ′ given the initial state x 1 = x is:

<!-- formula-not-decoded -->

Hence the weights can be written as:

<!-- formula-not-decoded -->

We make the following assumption to guarantee that the above weights are always well defined, and that the calibration data is i.i.d.

Assumption 1: We assume throughout the paper that P π ( ·| x ) is absolutely continuous w.r.t. P π b ( ·| x ) for all x ∈ X . We further assume that calibration data D cal provides n i.i.d. samples ( X i , Y i ) ∼ P π b X,Y .

<!-- formula-not-decoded -->

Then, we can compute the scores V i = s ( X i , Y i ) . For each possible pair ( x, y ) , using the normalized weights, we form the distribution ˆ F x,y n := ∑ n i =1 p w i ( x, y ) δ V i + p w n +1 ( x, y ) δ ∞ , with

and the conformalized set

<!-- formula-not-decoded -->

Proposition 1: Under Assumption 1, for any score function s and any α ∈ (0 , 1) ,

<!-- formula-not-decoded -->

where P π b ,π accounts for the randomness of ( X,Y ) ∼ P π X,Y and that of the data D cal = { X i , Y i } n i =1 (with for all i ∈ [ n ] , ( X i , Y i ) ∼ P π b X,Y ).

The proof of the proposition is similar to that of [24, Proposition 4.1], and is omitted due to space constraints. The complete proofs of all results can be found in the companion technical report 1 . Proposition 1 shows that, in absence of data from the target policy, we can still use a shifted CDF of the scores to assess the target policy. The result however relies on the assumption that the weights w ( x, y ) are known. In practice, we could use the training data to learn these weights, refer to Section V for details. The next proposition quantifies the impact of the error in this estimation procedure on the coverage. Its proof follows the same arguments as those in [24].

Proposition 2: Assume that the conformalized sets (3) are defined using estimated the weights ˆ w ( x, y ) satisfying E π b [ ˆ w ( X,Y ) r ] ≤ M r r &lt; ∞ for some r ≥ 2 . Define ∆ w = 1 2 E π b | ˆ w ( X,Y ) -w ( X,Y ) | . Then

<!-- formula-not-decoded -->

If, in addition, the non-conformity scores { V i } n i =1 have no ties almost surely, then we also have

<!-- formula-not-decoded -->

for some positive constant c depending on M r and r only.

## B. Selecting the score function

The choice of the score function critically impacts the size and center of the conformalized sets ˆ C n ( x ) . In previous work [21], [24], the pre-training procedure outputs some estimated quantiles q α lo ( x ) and q α hi ( x ) for the value of the behavior policy with initial state x , and the use of the symmetric score function

<!-- formula-not-decoded -->

is advocated. This choice yields a set ˆ C n ( x ) centered ¯ q π b ( x ) = ( q α lo ( x ) + q α hi ( x )) / 2 . Indeed, in view of (3) and (6), there is η ( x ) ∈ R such that ˆ C n ( x ) = [¯ q π b ( x ) -η ( x ) , ¯ q π b ( x ) + η ( x )] (note that when n grows large, η ( x ) becomes independent of x ). Having ˆ C n ( x ) centered on the estimated median value for π b is of course very problematic when the values of π b and π significantly differ. In this case, the length of ˆ C n ( x ) becomes unnecessarily large. Next we propose methods and score functions that efficiently re-center ˆ C n ( x ) around the value of π (instead of π b ), and that in turn yield much smaller conformalized sets.

1 Find the technical report and the code here https://github. com/danielefoffano/Conformal\_OPE\_MDP/blob/main/ Conformal\_OPE\_in\_MDP.pdf

Fig. 2. Symmetry problem. For the original confidence set with one single quantile, and score function s ( x, y ) = max( q α lo ( x ) -y, y -q α hi ( x )) , we obtain a set that is symmetric around its middle point ( q α lo ( x )+ q α hi ( x )) / 2 . We can break this symmetry by considering two different score quantiles, one for q α lo ( x ) -y and one for y -q α hi ( x ) , thus leading to a less conservative conformalized set.

<!-- image -->

1) Double-quantile score: a first idea is to break the symmetry of the score function used in [24] by considering the following confidence set

<!-- formula-not-decoded -->

where ˆ F x,y n, 0 := ∑ n i =1 p w i ( x, y ) δ V i, 0 + p w n +1 ( x, y ) δ ∞ and ˆ F x,y n, 1 := ∑ n i =1 p w i ( x, y ) δ V i, 1 + p w n +1 ( x, y ) δ ∞ , with V i, 0 = q α lo ( X i ) -Y i and V i, 1 = Y i -q α hi ( X i ) . In essence, we separately look at the lower and upper quantiles of the shifted distribution of the scores. A graphical illustration is provided in Fig. 2. The new construction of ˆ C n ( x ) does not affect coverage guarantees:

Proposition 3: Under Assumption 1, for α ∈ (0 , 1) the sets ˆ C n ( x ) in (7) satisfies

<!-- formula-not-decoded -->

We also obtain the following guarantees in case w ( x, y ) is replaced by ˆ w ( x, y ) .

Proposition 4: Let ˆ C n ( x ) be as in (7) with weights w ( x, y ) replaced by ˆ w ( x, y ) . Under the same assumptions as in Proposition 2, we have

<!-- formula-not-decoded -->

If, in addition, non-conformity scores { V i, 0 } n i =1 and { V i, 1 } n i =1 have no ties almost surely, then we also have

<!-- formula-not-decoded -->

for some positive constant c depending only on M r and r .

2) Shifted values: a second idea is to simply shift the values of the behavior policy π b using the likelihood ratios w ( x, y ) , as one would in important sampling methods. This can be done by simply using s ( x, y ) = y . This choice of score function makes sense intuitively: if we are interested in the value of the target policy π , then we may look at the shifted distribution of the values of the behavior policy.

We may also combine this choice with the double-quantile idea and construct ˆ C n ( x ) as

<!-- formula-not-decoded -->

where ˆ C n, 0 = { y ∈ R : y ≥ Quantile α/ 2 ( ˆ F x,y n )} and ˆ C n, 1 = { y ∈ R : y ≤ Quantile 1 -α/ 2 ( ˆ F x,y n )} . Propositions 3 and 4 also hold for this choice.

## V. OFFLINE ESTIMATION OF THE LIKELIHOOD RATIOS

In this section, we present various ways to estimate the likelihood ratios w ( x, y ) , and discuss their pros and cons.

## A. Monte-Carlo method

To estimate w ( x, y ) , we need to compute P π X,Y ( x, y ) and P π b X,Y ( x, y ) . Recall that the likelihood ratio is equal to

<!-- formula-not-decoded -->

where τ is a trajectory of length H . Since P π ( τ | x ) (sim. P π b ( τ | x ) ) depends on the transition kernel T and the reward distribution q , one needs to estimate these distributions from the data. We may proceed as follows:

- 1) We use the training data D tr to compute an estimate ( ˆ T, ˆ q ) of ( T, q ) (through maximum likelihood).
- 2) Compute an estimate of ˆ w ( x, y ) through Monte-Carlo sampling:

<!-- formula-not-decoded -->

where r ( k ) t and r ( k ) ′ t are sequences of rewards generated, respectively, by starting in x and following π and π b , and h is the number of Monte Carlo samples. These trajectories are generated using ˆ T and ˆ q , estimated in the previous step.

This approach has various shortcomings. First it requires us to estimate the model ( T, q ) . Then it forces us to generate a large number of trajectories, which is heavy computationally. Finally, the term 1 { y = ∑ H t =1 r t } is going to be 0 most of the times. A possible way to alleviate this issue consists in not including the last reward in the trajectory τ . This implies that we replace 1 { y = ∑ H t =1 r t } by ˆ q ( y -∑ H -1 n =1 r n | x H , a H ) . As it turns out, this naive Monte-Carlo method, used with success in simple scenarios (contextual bandits [24]), does not work in MDPs.

## B. Empirical and gradient-based methods

Next we present an alternative and more scalable way to estimate the weights w ( x, y ) from the training dataset D tr . We make use of the following simple rewriting of the likelihood ratio (also suggested in [24]):

<!-- formula-not-decoded -->

Next, observe that:

<!-- formula-not-decoded -->

Hence, learning w amounts to learning the following expectation:

<!-- formula-not-decoded -->

1) Empirical estimator: this method applies to the case x and y belong to some finite spaces X and Y only. In this case, we can directly estimate w ( x, y ) from the training data D tr by simply computing

<!-- formula-not-decoded -->

where the training data D tr consists of m trajectories generated under π b , the i -th trajectory in this dataset is τ i = ( x ( i ) t , a ( i ) t , r ( i ) t ) H t =1 , D tr ( x, y ) are trajectories with initial state and the accumulated reward x and y , respectively, and N ( x, y ) = |D tr ( x, y ) | . When the likelihood ratios are bounded, we can quantify the accuracy of the above estimates using standard concentration results:

Proposition 5: Let ( ε, δ ) ∈ (0 , 1) . Assume the ratio ∏ H t =1 π ( a t | x t ) / ∏ H t =1 π b ( a t | x t ) to be bounded in [ m,M ] for all possible trajectories of horizon H generated under π b . If min x,y N ( x, y ) ≥ ( M -m ) 2 2 ε 2 ln 2 |X||Y| δ , then

<!-- formula-not-decoded -->

Furthermore, we also have ∆ w ≤ ( M -m ) |X||Y| √ π 2 √ 2 min x,y N ( x,y ) .

The quantities M and m are usually function of the horizon H (in general one can choose m = 0 ). For example, in case A is finite, we obtain: