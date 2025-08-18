from .actor import Actor
from simulator.graph import Node, Link
from actions.action import Action

class Attacker(Actor):
    def __init__(self, id: str, role: str = "attacker", capacity: int = 2, strategy: str = "none") -> None:
        super().__init__(id, role, capacity, strategy)
        self.is_attacker = True
        self.visible_nodes = set()
        self.compromised_nodes = set()
        self.visible_links = set()
        self.compromised_links = set()
        self.available_actions = []
    
    def choose_action(self, network_state):
        match self.strategy:
            case "greedy":
                self.choose_best_action(network_state)
            case "random":
                self.choose_random_action(network_state)
            case _:
                self.choose_best_action(network_state)

    def choose_best_action(self, network_state) -> tuple:
        print(f"[DEBUG] Attacker {self.id} choosing best action")
        visible_nodes = list(self.visible_nodes)
        visible_links = list(self.visible_links)
        best = None
        best_gain = float('-inf')
        print("[DEBUG] Available actions:", self.available_actions)
        for action in self.available_actions:
            if action.is_node_action():
                for node in visible_nodes:
                    # Skip nodes this attacker has already compromised (by id)
                    if hasattr(node, 'id') and node.id in self.compromised_nodes:
                        continue
                    actor_access = node.access.get(self.id, None)
                    if action.precondition(node, actor_access, self.id):
                        gain = action.get_one_off_gain(node, actor_access, self.id)
                        print(f"[DEBUG] Action: {action}, Node: {node}, Gain: {gain}")
                        if gain > best_gain:
                            best = (action, node)
                            best_gain = gain
            elif action.is_link_action():
                for link in visible_links:
                    # Skip links this attacker has already compromised (by id)
                    if hasattr(link, 'id') and link.id in self.compromised_links:
                        continue
                    actor_access = getattr(link, 'access', {}).get(self.id, None)
                    if action.precondition(link, actor_access, self.id):
                        gain = action.get_one_off_gain(link, actor_access, self.id)
                        print(f"[DEBUG] Action: {action}, Link: {link}, Gain: {gain}")
                        if gain > best_gain:
                            best = (action, link)
                            best_gain = gain
        print("[DEBUG] Best action selected:", best)
        return best

    def choose_random_action(self, network_state) -> tuple:
        import random
        visible_nodes = list(self.visible_nodes)
        visible_links = list(self.visible_links)
        possible_actions = []

        print("[DEBUG] Available actions:", self.available_actions)
        for action in self.available_actions:
            if action.is_node_action():
                for node in visible_nodes:
                    if hasattr(node, 'id') and node.id in self.compromised_nodes:
                        continue
                    actor_access = node.access.get(self.id, None)
                    if action.precondition(node, actor_access, self.id):
                        print(f"[DEBUG] Valid action: {action}, Node: {node}")
                        possible_actions.append((action, node))
            elif action.is_link_action():
                for link in visible_links:
                    if hasattr(link, 'id') and link.id in self.compromised_links:
                        continue
                    actor_access = getattr(link, 'access', {}).get(self.id, None)
                    if action.precondition(link, actor_access, self.id):
                        print(f"[DEBUG] Valid action: {action}, Link: {link}")
                        possible_actions.append((action, link))

        chosen_action = random.choice(possible_actions) if possible_actions else None
        print("[DEBUG] Randomly chosen action:", chosen_action)
        return chosen_action

    def exploit(self, node: Node):
        node.compromised = True
        if hasattr(node, 'id'):
            self.compromised_nodes.add(node.id)

    def gain_visibility(self, node: Node):
        self.visible_nodes.add(node)

    def gain_link_visibility(self, link: Link):
        self.visible_links.add(link)

    def compromise_link(self, link: Link):
        self.compromised_links.add(link)

    def on_action_finished(self, action, status, target=None):
        # Track successful node compromises by id for any node action
        if status == "success" and target is not None:
            if hasattr(target, 'id'):
                self.compromised_nodes.add(target.id)