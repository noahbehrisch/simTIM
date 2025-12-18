HELP_CONTENT = {
    "Simulation": {
        "title": "Simulation Configuration",
        "content": """Configure the core simulation parameters:

• Simulation Time: Duration of the simulation in time units (hours)
  - Longer simulations allow more complex attack chains
  - Recommended: 10-50 for basic scenarios, 100+ for APT campaigns

• Number of Runs: How many times to repeat the simulation
  - Multiple runs provide statistical confidence
  - Results are aggregated and analyzed across all runs
  - Recommended: 10-100 runs for reliable statistics

• Detection Engine: Algorithm for detecting attacks
  - Uniform: Constant detection rate throughout action duration
  - Exponential: Higher probability of early detection (realistic for IDS)
  - Linear: Detection probability increases over time

• Duration Overrides: Modify action durations for scenario comparison
  - Leave empty to use default durations from action definitions
  - Use to test "what-if" scenarios (e.g., faster patching)

Click "Start Simulation" to run with current configuration."""
    },
    
    "Network": {
        "title": "Network Configuration",
        "content": """Select and manage network topologies:

• Network File: JSON file defining nodes, links, and properties
  - Nodes represent servers, workstations, network devices
  - Links represent network connections between nodes
  - Properties include software, vulnerabilities, assets

• Available Networks:
  - demo_network: Simple 2-node example for learning
  - realistic_smb_network: Small business with 10-20 nodes
  - realistic_enterprise_network: Large organization with 100+ nodes
  - healthcare_network: HIPAA-compliant healthcare infrastructure

• Network Properties:
  - Exposed nodes: Accessible from internet (entry points)
  - Internal nodes: Only reachable after compromise
  - Critical nodes: High-value targets with sensitive data
  - Links: Show connections and attack propagation paths

Use "Visualize Network" to see topology and "Create Network" for custom designs."""
    },
    
    "Attackers": {
        "title": "Attacker Configuration",
        "content": """Configure attacking actors and their strategies:

• Attacker ID: Unique identifier for this attacker
  
• Strategy: Decision-making algorithm for choosing actions
  - Random: Select any valid action randomly (baseline)
  - Greedy: Prioritize high-value targets and high-gain actions
  - Targeted: Focus on specific objectives systematically

• Capacity: Maximum number of concurrent actions
  - Higher capacity = more aggressive attacks
  - Realistic values: 1-5 for opportunistic, 10+ for APT groups

• Budget: Maximum spending allowed for actions
  - Infinite budget: No constraints (default)
  - Limited budget: Models resource-constrained attackers

• Initial Access:
  - Attackers start with visibility to exposed nodes only
  - Must discover and compromise nodes to progress
  - Access levels: NONE → VISIBLE → USER → ADMIN

Multiple attackers can be added for coordinated attacks."""
    },
    
    "Defenders": {
        "title": "Defender Configuration",
        "content": """Configure defending actors and their strategies:

• Defender ID: Unique identifier for this defender

• Strategy: Response algorithm for defending the network
  - Reactive: Respond only when attacks are detected
  - Proactive: Patch vulnerabilities before exploitation
  - Monitoring: Focus on enhancing detection capabilities

• Capacity: Maximum number of concurrent defensive actions
  - Lower capacity = resource constraints (realistic)
  - Must prioritize which threats to address
  - Typical values: 1-3 for small teams, 5+ for SOC

• Budget: Maximum spending allowed for defensive actions
  - Models real-world budget constraints
  - Forces cost-benefit decisions

• Detection Capabilities:
  - Detection probability: Chance of spotting attacks
  - Detection timing: When during action execution detection occurs
  - Affected by detection engine and node properties

• Response Actions:
  - Patching: Remove vulnerabilities
  - Firewall rules: Block attack paths
  - Incident response: Contain and remediate

Defenders have full visibility of all nodes but limited capacity to act."""
    },
    
    "Actions": {
        "title": "Actions Library",
        "content": """Browse and manage attack and defense actions:

• Action Types:
  - Node Actions: Operate on single node (privilege escalation)
  - Link Actions: Move between nodes (lateral movement)

• Action Properties:
  - Name: Descriptive identifier
  - Cost: Economic cost to execute
  - Duration: Physical time required (hours)
  - Success Probability: Chance of successful execution
  
• Preconditions: Requirements to start action
  - Access level checks (must have USER, ADMIN, etc.)
  - Software/version checks (target must run specific software)
  - Vulnerability checks (target must have CVE-XXXX)
  - Property checks (target must have specific attributes)

• Postconditions: Effects when action succeeds
  - Set access level (escalate from USER to ADMIN)
  - Modify properties (mark as compromised, encrypted)
  - Add capabilities (persistence, command & control)

• Detection:
  - Probability of detection during execution
  - Varies by action type and target properties
  - IDS/EDR systems increase detection rates

• Economic Impact:
  - One-off damage/gain: Immediate effect on success
  - Time-proportional: Ongoing damage/gain while compromised

Use filters to find specific actions or browse by category."""
    },
    
    "Variables": {
        "title": "Scenario Variables",
        "content": """Define parameter variations for sensitivity analysis:

• Purpose: Test how changing parameters affects outcomes
  - Compare different detection engines
  - Analyze impact of action durations
  - Evaluate budget constraints

• Variable Types:
  - Detection Engine: uniform, exponential, linear
  - Action Durations: Override default timings
  - Actor Capacities: Test resource constraints
  - Budgets: Economic limitation scenarios

• Scenario Generation:
  - Creates all combinations of variable values
  - Each combination runs as separate simulation
  - Results compared in visualization

• Example Use Cases:
  - "How much does faster patching help?"
    → Vary defense_duration from 0.5 to 2.0 hours
  
  - "Which detection engine is most effective?"
    → Test uniform, exponential, linear
  
  - "What capacity does defender need?"
    → Vary defender_capacity from 1 to 5

Results show which parameters have greatest impact on security outcomes."""
    },
    
    "Overview": {
        "title": "Simulation Overview",
        "content": """Summary of all configured simulation parameters:

• Review Before Running:
  - Network topology and node count
  - Attacker configurations and strategies
  - Defender configurations and capabilities
  - Action libraries being used
  - Economic parameters and budgets

• Validation:
  - Checks for configuration errors
  - Warns about unrealistic parameters
  - Suggests improvements

• Quick Start:
  - Use default settings for first simulation
  - Modify one parameter at a time
  - Compare results to understand effects

• Common Issues:
  - No attackers defined → Add at least one
  - No defenders defined → Add at least one
  - Network file missing → Select valid network
  - Capacity too low → Defender can't respond effectively

Once validated, click "Start Simulation" to begin."""
    }
}

TOOLTIPS = {
    "sim_time": "Duration of simulation in time units (hours). Longer times allow complex multi-stage attacks.",
    "sim_runs": "Number of times to repeat simulation. More runs = better statistics.",
    "detection_engine": "Algorithm for detecting attacks:\n• Uniform: Constant rate\n• Exponential: Early detection bias\n• Linear: Late detection bias",
    "action_duration": "Override all action durations (hours). Leave empty for defaults.",
    "attack_duration": "Override only attack action durations. Leave empty for defaults.",
    "defense_duration": "Override only defense action durations. Leave empty for defaults.",
    
    "network_file": "JSON file defining network topology, nodes, and links.",
    "visualize": "Display network graph with nodes and connections.",
    "create_network": "Open network creator tool to build custom topology.",
    
    "attacker_id": "Unique identifier for this attacker (e.g., 'attacker_1', 'apt_group').",
    "attacker_strategy": "Algorithm for choosing which actions to perform:\n• Random: Any valid action\n• Greedy: High-value targets\n• Targeted: Specific goals",
    "attacker_capacity": "Maximum concurrent actions. Higher = more aggressive.",
    "attacker_budget": "Maximum spending on actions. Use 'inf' for unlimited.",
    
    "defender_id": "Unique identifier for this defender (e.g., 'defender', 'security_team').",
    "defender_strategy": "Response algorithm:\n• Reactive: Respond to detections\n• Proactive: Patch preemptively\n• Monitoring: Enhance detection",
    "defender_capacity": "Maximum concurrent actions. Limited capacity is realistic.",
    "defender_budget": "Maximum spending on defensive actions.",
    
    "action_filter": "Filter actions by name or category.",
    "action_type": "Node actions affect single node, Link actions move between nodes.",
    "success_probability": "Chance action succeeds (0.0 to 1.0). Lower = more difficult.",
    "detection_probability": "Chance defender detects this action during execution.",
}
