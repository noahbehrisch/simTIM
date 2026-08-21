
Good afternoon, and thank you for joining my presentation. My name is Noah Behrisch, I am a student at Martin Luther University Halle-Wittenberg, and I co-authored this paper with Zoltán Mann from the University of Münster. simTIM: a temporal cybersecurity simulator.

Imagine you are a security analyst/network planner/etc. at an organization. You have been given a budget and the task to improve security in the company network. Which servers are particularly vulnerable and need hardening? How to optimize the network topology?

You would like what-if analysis. This is the reason there has been much research into modelling cybersecurity.

One of these research efforts is the TIM meta-model, proposed by Zoltán Mann. TIM is an acronym for "Time Is Money", and it models an organization's IT assets. It combines three families of security models: the graph structure of attack graphs, the probabilistic events of stochastic models, and the attacker–defender framing of game theory.
The network is composed of nodes and links, which model servers, routers and the connections between them. There are attackers trying to make a monetary gain by exploiting the system, and defenders trying to minimize damage to it. Both of these actors have a host of actions they can employ to pursue their goal.

An important addition the TIM meta-model makes is the ability to model physical time.
In real life, the duration of an attack and how quickly the defenders can respond is crucial, but former models did not capture this dimension.

The original TIM paper had a small proof-of-concept program, implementing only a subset of TIM's capabilities. This is where simTIM comes into play. simTIM aims to be a full implementation of the TIM meta-model, with a user-friendly graphical interface, easily configurable simulations, Monte Carlo runs and visualization along the way.


Instead of talking about it, I will now show you a quick demonstration.
Let's say we want to run a simulation of one week, which I have preset. Because simTIM has stochastic elements, we don't just want one run but potentially many, to see trends. For the purposes of this demonstration we will do three runs. Right now there are three different detection biases, applied globally. Here we set the bias to early, meaning the probability that an action is detected is highest just after the action starts.

Next we will choose a network. Networks are stored in JSON format, so they can be saved to file and loaded. simTIM comes with a network creation tool that lets users create their network easily via a GUI.

Here we define how many attackers there are, which strategy they employ, what their capacity is — meaning how many actions they can carry out at once — and of course how much money they start out with. I choose the escalation strategy, meaning the attacker tries to gain high privilege and move laterally through the network. Capacity is infinite.

Next, our defender. The defender also gets a budget and a strategy, though its capacity is limited.

This is the action configuration. Here the defense capabilities can be modeled. Attackers could be allowed to have zero-day exploits, to better reflect reality. Actions are mapped to the MITRE ATT&CK and D3FEND matrices.

This next tab is the scenario comparison. This is an easy way to compare different parameters of the simulation against each other, like different defense strategies, network topologies, etc. Scenario comparison. For this demo I will compare different defense durations.

Here is a short overview of all the parameters and now we can run the simulation.

Clicking on the results button takes us to this dashboard, giving an overview of all the results. The next tabs are the different event histories, for every run and for each actor. This is a timeline of the economic impact, showing system damage, attacker gain and defender cost. Next is a timeline of the access the attacker has to the nodes, but the following tab shows this even better: the attack path. Here you can see our network and when I press play we see in real time how the attacker propagates through the network and which access they have at any given point in time.
The last tab is the statistical analysis where you can see the outcomes of the scenario comparison.

simTIM is an open-source project that is still under development. You can find it on GitHub and are welcome to try it out. Extensibility was a main consideration when developing simTIM. Networks and actions are JSON. Strategies and detection engines are Python classes that can easily be extended.

Thank you for listening!
