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

