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
        self.capacity=capacity
        self.strategy=strategy
        self.incurredCost=0
        self.nodeAccess={}
        self.linkAccess={}
    
    def __repr__(self) -> str:
        return f"Actor(id={self.id}, capacity={self.capacity}, incurredCost={self.incurredCost})"

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

    def on_action_finished(self, action, status):
        pass

