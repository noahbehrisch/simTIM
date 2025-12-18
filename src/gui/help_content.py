HELP_CONTENT = {
    "Simulation": {
        "title": "Simulation Configuration",
        "content": """• Simulation Time: Duration in hours
• Number of Runs: Repeat count for statistics
• Detection Engine: uniform (constant) | exponential (early bias) | linear (late bias)
• Duration Overrides: Test what-if scenarios"""
    },
    
    "Network": {
        "title": "Network Configuration",
        "content": """• Network File: JSON defining nodes and connections
• Exposed nodes: Internet-accessible entry points
• Internal nodes: Reachable after compromise"""
    },
    
    "Attackers": {
        "title": "Attacker Configuration",
        "content": """• Strategy: random | greedy | targeted
• Capacity: Max concurrent actions
• Budget: Max spending (use 'inf' for unlimited)
• Access levels: NONE → VISIBLE → USER → ADMIN"""
    },
    
    "Defenders": {
        "title": "Defender Configuration",
        "content": """• Strategy: reactive | proactive | monitoring
• Capacity: Max concurrent actions (lower = realistic constraints)
• Budget: Max spending
• Full visibility but limited capacity"""
    },
    
    "Actions": {
        "title": "Actions Library",
        "content": """• Node Actions: Single node operations
• Link Actions: Movement between nodes
• Preconditions: Requirements to execute
• Postconditions: Effects on success"""
    },
    
    "Variables": {
        "title": "Scenario Variables",
        "content": """Define parameter variations for sensitivity analysis.
Tests all combinations of variable values.
Compare outcomes across scenarios."""
    },
    
    "Overview": {
        "title": "Simulation Overview",
        "content": """Review configuration before running.
Validates settings and checks for errors."""
    }
}

TOOLTIPS = {
    "sim_time": "Duration in hours",
    "sim_runs": "Repeat count",
    "detection_engine": "uniform | exponential | linear",
    "action_duration": "Override all durations",
    "attack_duration": "Override attack durations",
    "defense_duration": "Override defense durations",
    
    "network_file": "JSON topology file",
    "visualize": "Display network graph",
    "create_network": "Build custom network",
    
    "attacker_id": "Unique identifier",
    "attacker_strategy": "random | greedy | targeted",
    "attacker_capacity": "Max concurrent actions",
    "attacker_budget": "Max spending ('inf' for unlimited)",
    
    "defender_id": "Unique identifier",
    "defender_strategy": "reactive | proactive | monitoring",
    "defender_capacity": "Max concurrent actions",
    "defender_budget": "Max spending",
    
    "action_filter": "Filter by name",
    "action_type": "Node or Link action",
    "success_probability": "0.0 to 1.0",
    "detection_probability": "Detection chance",
}
