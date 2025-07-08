from .actor import Actor
from simulator.network import Node
from actions.action import Action

class Defender(Actor):
    def __init__(self, id: str, role: str = "defender", capacity: int = 2) -> None:
        super().__init__(id, role, capacity)
        self.is_defender = True
        self.visible_nodes = set()
        self.compromised_nodes = set()
        self.visible_links = set()
        self.compromised_links = set()
        self.available_actions = []  # List[Action] assigned externally

    def choose_best_action(self, network_state) -> tuple:
        best = None
        best_cost = float('inf')
        for action in self.available_actions:
            if action.is_node_action():
                for node in getattr(network_state, 'nodes', []):
                    actor_access = node.access.get(self.id, None)
                    if action.precondition(node, actor_access, self.id):
                        cost = action.get_cost()
                        if cost < best_cost:
                            best = (action, node)
                            best_cost = cost
            elif action.is_link_action():
                for link in getattr(network_state, 'links', []):
                    actor_access = getattr(link, 'access', {}).get(self.id, None)
                    if action.precondition(link, actor_access, self.id):
                        cost = action.get_cost()
                        if cost < best_cost:
                            best = (action, link)
                            best_cost = cost
        return best

    def repair(self, node: Node):
        node.compromised = False
        node.repaired = True

    def on_action_finished(self, action, status):
        pass