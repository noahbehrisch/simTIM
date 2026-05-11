# Peer Reviews — Submission 83

**Title:** SimTIM: A Temporal Cybersecurity Simulator

---

## Review 1

**Overall evaluation:** SCORE: -2 (reject)

### Major Strong Points

The main strength of the paper lies in its engineering effort and system integration. The simulator is clearly designed with usability in mind: the GUI, JSON-based configuration of actions, and modular architecture. Another positive aspect is the explicit support for partial observability and probabilistic detection, where attackers initially only see exposed nodes and defenders receive probabilistic alerts.

### Major Weak Points

- The paper inherits much of its conceptual foundation from the TIM meta-model; the novelty of this work is therefore limited. The main contribution is turning TIM into a usable tool.
- The positioning with respect to existing work is weak. The related work section is quite short and mainly categorizes some prior simulators without providing a meaningful comparison.
- The attacker and defender strategies are quite simplistic. Attackers follow strategies such as "greedy" (maximize expected profit), "random", or "escalation-based", while defenders use reactive or proactive heuristics. These are far from representing real-world adversaries, which are often adaptive, coordinated, and learning-based. While the framework allows adding new strategies, the paper does not demonstrate this capability with more advanced or realistic behaviors.
- An important issue is the heavy reliance on manually defined models and parameters.

### Detailed Comments

This paper introduces simTIM, a cybersecurity simulator built on top of an existing TIM meta-model, with the goal of helping organizations reason about cyber risk and evaluate defense strategies through simulation. The system models infrastructures as graphs of nodes and links and represents attackers and defenders as agents executing actions with probabilistic outcomes, costs, and durations. The simulator supports temporal dynamics, partial observability, and Monte Carlo simulations, and provides a GUI for configuring scenarios and visualizing results. The contribution is primarily the design and implementation of this tool, along with a description of its architecture and capabilities.

The paper addresses a relevant problem and presents a reasonably well-engineered system. However, it reads much more like a tool demonstration paper than a solid research contribution. The core issue is that most of the paper is devoted to describing features and implementation details, while evidence of scientific contribution, validation, and differentiation from prior work remains weak.

---

## Review 2

**Overall evaluation:** SCORE: +2 (accept)

### Major Strong Points

The paper provides a significant technical contribution by operationalizing the TIM meta-model into a functional, open-source tool. Its primary value lies in the modular architecture that separates simulation logic from user-defined strategies, combined with a JSON-based condition language that lowers the barrier for custom action modeling. The integration of physical time and financial impact provides a holistic view of cyber risk that is often absent in purely technical simulators.

### Major Weak Points

- The most notable limitation is the lack of empirical validation; while the tool is shown to be feature-rich, its predictive accuracy is not tested against real-world datasets or existing simulator baselines.
- The paper lacks a detailed discussion on the computational scalability of the Monte Carlo engine for very large enterprise networks.

### Detailed Comments

This paper addresses the difficulty organizations face in quantifying the value of cybersecurity investments. By introducing simTIM, the authors provide a framework that successfully integrates time and money — two often-separated dimensions of risk — into a single simulation environment. The modularity of detection engines and strategies is a significant strength, allowing engineers and researchers to plug in custom logic without needing to alter the core engine. However, the related work section is somewhat brief and inward-looking. While it effectively highlights the tool's features and its position within the Kavak taxonomy [^kavak], it lacks a rigorous comparison of simulation outcomes against known datasets or other simulators. Despite this, the open-source nature of the project and the clarity of the implementation make it a valuable contribution to the field of cyber defense decision support.

---

## Review 3

**Overall evaluation:** SCORE: +2 (accept)

### Major Strong Points

An interesting and useful tool named SimTIM has been developed. Supplementary material has been shared.

### Major Weak Points

- Results are a bit sketchy.

### Detailed Comments

The tool as developed by the authors and described in this paper appears to be useful. The background material is well-presented in the paper. It is easy to read and follow the discussions.

Some extension ideas have also been suggested by the authors, which is commendable.

The related work section is a little too short, but given the page limit, it is acceptable. The abstract can be shortened.

Some results on how any organization was benefitted by the tool would have been more impactful and convincing.

---

[^kavak]: Kavak et al., "Simulation for cybersecurity: state of the art and future directions", 2021.
