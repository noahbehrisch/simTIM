from collections import defaultdict
from collections.abc import Iterator
from typing import Any


class OngoingActionsIndex:
    def __init__(self):
        self._actions: dict[int, dict[str, Any]] = {}
        self._by_actor: dict[str, set[int]] = defaultdict(set)
        self._by_target: dict[str, set[int]] = defaultdict(set)
        self._by_action_name: dict[str, set[int]] = defaultdict(set)
        self._by_postcondition_target: dict[str, set[int]] = defaultdict(set)

    def _get_action_id(self, action_data: dict[str, Any]) -> int:
        return action_data.get("action_instance_id", id(action_data))

    def _get_actor_id(self, action_data: dict[str, Any]) -> str:
        actor = action_data.get("actor")
        return getattr(actor, "id", str(actor)) if actor else ""

    def _get_target_id(self, action_data: dict[str, Any]) -> str:
        target = action_data.get("target")
        return getattr(target, "id", str(target)) if target else ""

    def _get_action_name(self, action_data: dict[str, Any]) -> str:
        action = action_data.get("action")
        return getattr(action, "name", "") if action else ""

    def _get_postcondition_target_id(self, action_data: dict[str, Any]) -> str:
        target = action_data.get("postcondition_target")
        return getattr(target, "id", str(target)) if target else ""

    def add(self, action_data: dict[str, Any]) -> None:
        action_id = self._get_action_id(action_data)
        if action_id in self._actions:
            return

        self._actions[action_id] = action_data

        actor_id = self._get_actor_id(action_data)
        if actor_id:
            self._by_actor[actor_id].add(action_id)

        target_id = self._get_target_id(action_data)
        if target_id:
            self._by_target[target_id].add(action_id)

        action_name = self._get_action_name(action_data)
        if action_name:
            self._by_action_name[action_name].add(action_id)

        postcond_id = self._get_postcondition_target_id(action_data)
        if postcond_id:
            self._by_postcondition_target[postcond_id].add(action_id)

    def remove(self, action_data: dict[str, Any]) -> bool:
        action_id = self._get_action_id(action_data)
        if action_id not in self._actions:
            return False

        del self._actions[action_id]

        actor_id = self._get_actor_id(action_data)
        if actor_id and action_id in self._by_actor[actor_id]:
            self._by_actor[actor_id].discard(action_id)
            if not self._by_actor[actor_id]:
                del self._by_actor[actor_id]

        target_id = self._get_target_id(action_data)
        if target_id and action_id in self._by_target[target_id]:
            self._by_target[target_id].discard(action_id)
            if not self._by_target[target_id]:
                del self._by_target[target_id]

        action_name = self._get_action_name(action_data)
        if action_name and action_id in self._by_action_name[action_name]:
            self._by_action_name[action_name].discard(action_id)
            if not self._by_action_name[action_name]:
                del self._by_action_name[action_name]

        postcond_id = self._get_postcondition_target_id(action_data)
        if postcond_id and action_id in self._by_postcondition_target[postcond_id]:
            self._by_postcondition_target[postcond_id].discard(action_id)
            if not self._by_postcondition_target[postcond_id]:
                del self._by_postcondition_target[postcond_id]

        return True

    def get_by_actor(self, actor_id: str) -> list[dict[str, Any]]:
        return [self._actions[aid] for aid in self._by_actor.get(actor_id, set())]

    def get_by_target(self, target_id: str) -> list[dict[str, Any]]:
        return [self._actions[aid] for aid in self._by_target.get(target_id, set())]

    def get_by_action_name(self, action_name: str) -> list[dict[str, Any]]:
        return [self._actions[aid] for aid in self._by_action_name.get(action_name, set())]

    def get_by_postcondition_target(self, target_id: str) -> list[dict[str, Any]]:
        return [self._actions[aid] for aid in self._by_postcondition_target.get(target_id, set())]

    def find(
        self,
        actor: Any = None,
        target: Any = None,
        action: Any = None,
    ) -> dict[str, Any] | None:
        candidates = set(self._actions.keys())

        if actor is not None:
            actor_id = getattr(actor, "id", str(actor))
            candidates &= self._by_actor.get(actor_id, set())

        if target is not None:
            target_id = getattr(target, "id", str(target))
            target_candidates = self._by_target.get(target_id, set())
            candidates &= target_candidates

        if action is not None:
            action_name = getattr(action, "name", str(action))
            candidates &= self._by_action_name.get(action_name, set())

        for action_id in candidates:
            action_data = self._actions.get(action_id)
            if action_data:
                if actor is not None and action_data.get("actor") != actor:
                    continue
                if action is not None and action_data.get("action") != action:
                    continue
                if target is not None and action_data.get("target") != target:
                    continue
                return action_data

        return None

    def find_all(
        self,
        actor: Any = None,
        target: Any = None,
        action_name: str | None = None,
    ) -> list[dict[str, Any]]:
        candidates = set(self._actions.keys())

        if actor is not None:
            actor_id = getattr(actor, "id", str(actor))
            candidates &= self._by_actor.get(actor_id, set())

        if target is not None:
            target_id = getattr(target, "id", str(target))
            target_candidates = self._by_target.get(target_id, set())
            postcond_candidates = self._by_postcondition_target.get(target_id, set())
            candidates &= target_candidates | postcond_candidates

        if action_name is not None:
            candidates &= self._by_action_name.get(action_name, set())

        return [self._actions[aid] for aid in candidates if aid in self._actions]

    def __len__(self) -> int:
        return len(self._actions)

    def __iter__(self) -> Iterator[dict[str, Any]]:
        return iter(self._actions.values())

    def __contains__(self, action_data: dict[str, Any]) -> bool:
        action_id = self._get_action_id(action_data)
        return action_id in self._actions

    def clear(self) -> None:
        self._actions.clear()
        self._by_actor.clear()
        self._by_target.clear()
        self._by_action_name.clear()
        self._by_postcondition_target.clear()

    def to_list(self) -> list[dict[str, Any]]:
        return list(self._actions.values())
