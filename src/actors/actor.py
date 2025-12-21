class Actor:

    def __init__(self, id: str, role: str, capacity: int=None, strategy: str='None', budget: float=float('inf')):
        self.id = id
        self.role = role
        self.capacity = capacity if capacity is not None else 1
        self.strategy = strategy
        self.budget = budget
        self.incurredCost = 0
        self.ongoing_actions = set()
        self.simulator = None
        self.running = False
        self.decision_interval = 1.0
        self.total_gain = 0.0
        self.action_history = []
        self.economic_events = []

    def run(self):
        if not self.running:
            return
        if self.can_schedule_action():
            self.make_decision(self.simulator.network if self.simulator else None)
        if self.running and self.simulator:
            self.simulator.schedule_event(self.simulator.current_time + self.decision_interval, 'actor_run', {'actor': self})

    def __repr__(self) -> str:
        return f'Actor(id={self.id}, capacity={self.capacity}, budget={self.budget}, incurredCost={self.incurredCost}, strategy={self.strategy})'

    def can_schedule_action(self) -> bool:
        capacity_ok = self.capacity == float('inf') or len(self.ongoing_actions) < self.capacity
        budget_ok = self.budget == float('inf') or self.incurredCost < self.budget
        return capacity_ok and budget_ok

    def schedule_action(self, action):
        if self.can_schedule_action():
            self.ongoing_actions.add(action)

    def notify_action_finished(self, action, status):
        if action in self.ongoing_actions:
            self.ongoing_actions.remove(action)
        self.on_action_finished(action, status)

    def on_action_finished(self, action, status, target=None):
        pass

    def make_decision(self, network_state):
        pass

    def record_action_cost(self, action, timestamp):
        cost = action.cost
        self.incurredCost += cost
        self.action_history.append({'timestamp': timestamp, 'action': action.name, 'cost': cost, 'type': 'cost'})

    def get_concurrent_actions_count(self):
        return len(self.ongoing_actions)

    def record_economic_event(self, timestamp, event_type, value, details=None):
        self.economic_events.append({'timestamp': timestamp, 'type': event_type, 'value': value, 'details': details or {}})