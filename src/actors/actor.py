class Actor:
    def __init__(
        self, 
        id: str, 
        role: str, 
        capacity: int = None,
        strategy: str = "None"
    ):
        self.id=id
        self.role=role
        self.capacity=capacity if capacity is not None else 1
        self.strategy=strategy
        self.incurredCost=0
        self.nodeAccess={}
        self.linkAccess={}
        self.ongoing_actions = set()
        self.simulator = None
        self.running = False
        self.decision_interval = 1.0
        self.total_gain = 0.0
        self.total_damage_caused = 0.0
        self.action_history = []
        self.economic_events = []

    def __repr__(self) -> str:
        return f"Actor(id={self.id}, capacity={self.capacity}, incurredCost={self.incurredCost}, strategy={self.strategy})"

    def set_simulator(self, simulator):
        self.simulator = simulator

    def can_schedule_action(self) -> bool:
        return len(self.ongoing_actions) < self.capacity

    def schedule_action(self, action):
        if self.can_schedule_action():
            self.ongoing_actions.add(action)
        else:
            pass

    def notify_action_finished(self, action, status):
        if action in self.ongoing_actions:
            self.ongoing_actions.remove(action)
        else:
            pass
        self.on_action_finished(action, status)

    def on_action_finished(self, action, status, target=None):
        pass

    def run(self, network_state):
        if not self.simulator:
            return
        if not self.running:
            self.running = True
            self.schedule_next_decision()

    def schedule_next_decision(self):
        if self.simulator and self.running:
            self.simulator.schedule_event(
                self.simulator.current_time + self.decision_interval,
                "actor_decide",
                {"actor": self}
            )

    def make_decision(self, network_state):
        pass

    def stop_running(self):
        self.running = False

    def record_action_cost(self, action, timestamp):
        cost = action.cost
        self.incurredCost += cost
        self.action_history.append({
            'timestamp': timestamp,
            'action': action.name,
            'cost': cost,
            'type': 'cost'
        })

    def record_economic_event(self, timestamp, event_type, value, details=None):
        self.economic_events.append({
            'timestamp': timestamp,
            'type': event_type,
            'value': value,
            'details': details or {}
        })

    def calculate_total_costs(self, time_interval=None):
        if time_interval is None:
            return self.incurredCost
        start_time, end_time = time_interval
        return sum(
            event['cost'] for event in self.action_history 
            if start_time <= event['timestamp'] <= end_time
        )

    def get_economic_objective(self, time_interval=None):
        return -self.calculate_total_costs(time_interval)

    def calculate_damage_functions(self, action, target, actor_access):
        node_properties = self._get_node_properties(target)
        one_off_damage = self._calculate_one_off_damage(action.name, node_properties)
        one_off_gain = self._calculate_one_off_gain(action.name, node_properties)
        return one_off_damage, one_off_gain

    def calculate_time_proportional_rates(self, access_level, target):
        node_properties = self._get_node_properties(target)
        damage_rate = self._calculate_time_damage_rate(access_level, node_properties)
        gain_rate = self._calculate_time_gain_rate(access_level, node_properties)
        return damage_rate, gain_rate

    def _get_node_properties(self, node):
        return {
            'vulnerabilities': getattr(node, 'vulnerabilities', []),
            'assets': getattr(node, 'assets', []),
            'software': getattr(node, 'software', {}),
            'compromised': getattr(node, 'compromised', False),
            'properties': getattr(node, 'properties', {})
        }

    def _calculate_one_off_damage(self, action_name, node_properties):
        assets = node_properties.get('assets', [])
        base_damage = len(assets) * 1000.0
        sensitive_assets = [a for a in assets if 'sensitive' in str(a).lower()]
        return base_damage + len(sensitive_assets) * 5000.0

    def _calculate_one_off_gain(self, action_name, node_properties):
        return self._calculate_one_off_damage(action_name, node_properties) * 0.3

    def _calculate_time_damage_rate(self, access_level, node_properties):
        if access_level in ['NONE', 'VISIBLE']:
            return 0.0
        assets = node_properties.get('assets', [])
        base_rate = len(assets) * 10.0
        if access_level == 'ADMIN':
            return base_rate * 3.0
        elif access_level == 'USER':
            return base_rate * 1.5
        return base_rate

    def _calculate_time_gain_rate(self, access_level, node_properties):
        damage_rate = self._calculate_time_damage_rate(access_level, node_properties)
        return damage_rate * 0.2