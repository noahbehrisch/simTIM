# Camera-Ready TODO — Based on Peer Review

**Paper:** SimTIM: A Temporal Cybersecurity Simulator (Submission 83)

---

## Must-Do (address to satisfy R1 / strengthen acceptance)

- [ ] **Add subtitle "Short paper"** to the paper title
- [ ] **Shorten the abstract** *(R3)*
- [ ] **Expand related work section** *(R1, R2, R3)*: Add substantive comparison with existing simulators, not just categorization. Ideally include a comparison table covering key features (time modeling, economics, partial observability, Monte Carlo, GUI, extensibility) across simTIM and comparable tools.
- [ ] **Add empirical validation / case study** *(R1, R2, R3)*: Include a concrete example showing how an organization could use simTIM to improve its security posture. Even a small illustrative experiment with measurable outcomes (e.g., comparing defender strategies on a sample network) would significantly strengthen the paper.
- [ ] **Sharpen novelty framing in the introduction** *(R1)*: Clearly articulate what simTIM contributes *beyond* implementing TIM — e.g., the extensible architecture, JSON condition language, GUI, detection engine abstraction, Monte Carlo support.

## Should-Do (improve quality and address weaker concerns)

- [ ] **Acknowledge limitations of current strategies** *(R1)*: Add a sentence in the strategies section or conclusion noting that current strategies are intentionally simple baselines, and that the pluggable architecture is designed to accommodate more advanced (e.g., learning-based) strategies in future work.
- [ ] **Add scalability discussion** *(R2)*: Briefly discuss the computational complexity of the Monte Carlo engine and any known limits for large networks (number of nodes, actions, runs). Can go in the Implementation or Conclusions section.
- [ ] **Address manual model dependency** *(R1)*: Acknowledge the reliance on manually defined networks and actions; frame the JSON-based formats and GUI network creator as mitigations, and note automation (e.g., from CMDBs or CVE feeds) as future work.

## Nice-to-Have

- [ ] Add GitHub repository link (placeholder currently in paper — fill in for final version)
- [ ] Consider adding a small performance/timing table for the Monte Carlo runs
