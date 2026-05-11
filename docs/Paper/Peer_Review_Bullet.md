# Peer Review — Extracted Action Items

**Paper:** SimTIM: A Temporal Cybersecurity Simulator (Submission 83)
**Scores:** R1: -2 (reject) | R2: +2 (accept) | R3: +2 (accept)

---

## Weak Points (all reviewers)

- **Related work too thin** *(R1, R2, R3)*: Section is too short; mainly categorizes prior work without substantive comparison. Needs rigorous comparison of simulation outcomes against other simulators or known datasets.
- **Lack of empirical validation** *(R1, R2, R3)*: No evidence of predictive accuracy, no real-world use case, no comparison against baselines or datasets.
- **Results are sketchy** *(R3)*: Some results on how an organization was benefitted by the tool would be more impactful and convincing.

## Weak Points (individual reviewers)

- **Novelty framing** *(R1)*: Paper inherits conceptual foundation from TIM; novelty is limited to operationalizing it. Needs clearer articulation of what simTIM contributes beyond implementing TIM.
- **Simplistic strategies** *(R1)*: Attacker/defender strategies (greedy, random, escalation, reactive, proactive) are far from real-world adversaries. Paper does not demonstrate the extensibility with more advanced or realistic behaviors.
- **Manual model dependency** *(R1)*: Heavy reliance on manually defined models and parameters — not discussed or addressed.
- **Scalability not discussed** *(R2)*: No discussion of computational scalability of the Monte Carlo engine for very large enterprise networks.
- **Abstract too long** *(R3)*: Abstract should be shortened.

---

## Weak Points — Verbatim from Reviews

### Review 1

- The paper inherits much of its conceptual foundation from the TIM meta-model; the novelty of this work is therefore limited. The main contribution is turning TIM into a usable tool.
- The positioning with respect to existing work is weak. The related work section is quite short and mainly categorizes some prior simulators without providing a meaningful comparison.
- The attacker and defender strategies are quite simplistic. Attackers follow strategies such as "greedy" (maximize expected profit), "random", or "escalation-based", while defenders use reactive or proactive heuristics. These are far from representing real-world adversaries, which are often adaptive, coordinated, and learning-based. While the framework allows adding new strategies, the paper does not demonstrate this capability with more advanced or realistic behaviors.
- An important issue is the heavy reliance on manually defined models and parameters.

### Review 2

- The most notable limitation is the lack of empirical validation; while the tool is shown to be feature-rich, its predictive accuracy is not tested against real-world datasets or existing simulator baselines.
- The paper lacks a detailed discussion on the computational scalability of the Monte Carlo engine for very large enterprise networks.

### Review 3

- Results are a bit sketchy.
