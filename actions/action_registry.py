import json
import importlib
from typing import Dict, List, Callable, Any
from actions.action import Action

class ActionRegistry:
    def __init__(self):
        self.function_registry = {}
        self.register_builtin_functions()
    
    def register_function(self, name: str, func: Callable):
        self.function_registry[name] = func
    
    def register_builtin_functions(self):
        try:
            from actions.action_attack import (
                compromise_tapestry_pre, compromise_tapestry_post,
                port_scan_pre, port_scan_post,
                simple_user_attack_pre, simple_user_attack_post,
                reconnaissance_pre, reconnaissance_post,
                privilege_escalation_pre, privilege_escalation_post,
                data_exfiltration_pre, data_exfiltration_post,
                compromise_mysql_pre, compromise_mysql_post,
                tapestry_detection_probability
            )
            
            self.register_function("compromise_tapestry_pre", compromise_tapestry_pre)
            self.register_function("compromise_tapestry_post", compromise_tapestry_post)
            self.register_function("port_scan_pre", port_scan_pre)
            self.register_function("port_scan_post", port_scan_post)
            self.register_function("simple_user_attack_pre", simple_user_attack_pre)
            self.register_function("simple_user_attack_post", simple_user_attack_post)
            self.register_function("reconnaissance_pre", reconnaissance_pre)
            self.register_function("reconnaissance_post", reconnaissance_post)
            self.register_function("privilege_escalation_pre", privilege_escalation_pre)
            self.register_function("privilege_escalation_post", privilege_escalation_post)
            self.register_function("data_exfiltration_pre", data_exfiltration_pre)
            self.register_function("data_exfiltration_post", data_exfiltration_post)
            self.register_function("compromise_mysql_pre", compromise_mysql_pre)
            self.register_function("compromise_mysql_post", compromise_mysql_post)
            self.register_function("tapestry_detection_probability", tapestry_detection_probability)
            
        except ImportError as e:
            print(f"Warning: Could not import attack functions: {e}")
        
        try:
            from actions.action_defense import (
                upgrade_mysql_pre, upgrade_mysql_post,
                system_patch_pre, system_patch_post,
                firewall_update_pre, firewall_update_post,
                ids_deploy_pre, ids_deploy_post,
                incident_response_pre, incident_response_post,
                security_monitoring_pre, security_monitoring_post,
                vuln_remediation_pre, vuln_remediation_post
            )
            
            self.register_function("upgrade_mysql_pre", upgrade_mysql_pre)
            self.register_function("upgrade_mysql_post", upgrade_mysql_post)
            self.register_function("system_patch_pre", system_patch_pre)
            self.register_function("system_patch_post", system_patch_post)
            self.register_function("firewall_update_pre", firewall_update_pre)
            self.register_function("firewall_update_post", firewall_update_post)
            self.register_function("ids_deploy_pre", ids_deploy_pre)
            self.register_function("ids_deploy_post", ids_deploy_post)
            self.register_function("incident_response_pre", incident_response_pre)
            self.register_function("incident_response_post", incident_response_post)
            self.register_function("security_monitoring_pre", security_monitoring_pre)
            self.register_function("security_monitoring_post", security_monitoring_post)
            self.register_function("vuln_remediation_pre", vuln_remediation_pre)
            self.register_function("vuln_remediation_post", vuln_remediation_post)
            
        except ImportError as e:
            print(f"Warning: Could not import defense functions: {e}")
    
    def get_function(self, name: str) -> Callable:
        if name in self.function_registry:
            return self.function_registry[name]
        else:
            raise ValueError(f"Function '{name}' not found in registry")
    
    def create_function_from_spec(self, spec: Dict[str, Any]) -> Callable:
        if spec["type"] == "function_ref":
            return self.get_function(spec["function"])
        elif spec["type"] == "constant":
            value = spec["value"]
            return lambda node, access, actor: value
        elif spec["type"] == "zero":
            return lambda node, access, actor: 0.0
        elif spec["type"] == "lambda":
            # Handle simple lambda expressions
            expression = spec["expression"]
            if expression == "zero":
                return lambda node, access, actor: 0.0
            else:
                # For more complex expressions, try to evaluate
                try:
                    return eval(f"lambda node, access, actor: {expression}")
                except:
                    return lambda node, access, actor: 0.0
        else:
            raise ValueError(f"Unknown function spec type: {spec['type']}")
    
    def action_from_json(self, action_data: Dict[str, Any]) -> Action:
        precondition = self.create_function_from_spec(action_data["precondition"])
        postcondition = self.create_function_from_spec(action_data["postcondition"])
        detection_probability = self.create_function_from_spec(action_data["detection_probability"])
        
        damage_gain = action_data["damage_gain"]
        one_off_damage = lambda node, access, actor: damage_gain["one_off_damage"]
        one_off_gain = lambda node, access, actor: damage_gain["one_off_gain"]
        time_damage = lambda node, access, actor: damage_gain["time_damage"]
        time_gain = lambda node, access, actor: damage_gain["time_gain"]
        
        return Action(
            name=action_data["name"],
            precondition=precondition,
            postcondition=postcondition,
            cost=action_data["cost"],
            duration=action_data["duration"],
            success_probability=action_data["success_probability"],
            action_type=action_data["action_type"],
            detection_probability=detection_probability,
            one_off_damage=one_off_damage,
            one_off_gain=one_off_gain,
            time_damage=time_damage,
            time_gain=time_gain
        )
    
    def action_to_json(self, action: Action) -> Dict[str, Any]:
        def get_function_spec(func):
            if hasattr(func, '__name__') and func.__name__ in self.function_registry:
                return {"type": "function_ref", "function": func.__name__}
            elif hasattr(func, '__name__') and func.__name__ == '<lambda>':
                # Handle lambda functions by checking if they return constants
                try:
                    test_result = func(None, None, None)
                    if isinstance(test_result, (int, float)):
                        return {"type": "constant", "value": test_result}
                except:
                    pass
                return {"type": "constant", "value": 0.0}
            else:
                return {"type": "constant", "value": 0.0}
        
        action_data = {
            "name": action.name,
            "action_type": action.action_type,
            "cost": action.cost,
            "duration": action.duration,
            "success_probability": action.success_probability,
            "precondition": get_function_spec(action.precondition),
            "postcondition": get_function_spec(action.postcondition),
            "detection_probability": get_function_spec(action.detection_probability),
            "damage_gain": {
                "one_off_damage": 0.0,
                "one_off_gain": 0.0, 
                "time_damage": 0.0,
                "time_gain": 0.0
            }
        }
        
        # Try to get actual damage/gain values
        try:
            action_data["damage_gain"]["one_off_damage"] = action.one_off_damage(None, None, None)
            action_data["damage_gain"]["one_off_gain"] = action.one_off_gain(None, None, None)
            action_data["damage_gain"]["time_damage"] = action.time_damage(None, None, None)
            action_data["damage_gain"]["time_gain"] = action.time_gain(None, None, None)
        except:
            pass
            
        return action_data
    
    def load_actions_from_file(self, file_path: str) -> Dict[str, List[Action]]:
        with open(file_path, 'r') as f:
            data = json.load(f)
        
        actions = {}
        for action_category, action_list in data["action_types"].items():
            actions[action_category] = []
            for action_data in action_list:
                action = self.action_from_json(action_data)
                actions[action_category].append(action)
        
        return actions
    
    def save_actions_to_file(self, actions: Dict[str, List[Action]], file_path: str):
        data = {"action_types": {}}
        
        for action_category, action_list in actions.items():
            data["action_types"][action_category] = []
            for action in action_list:
                action_data = self.action_to_json(action)
                data["action_types"][action_category].append(action_data)
        
        with open(file_path, 'w') as f:
            json.dump(data, f, indent=2)

# Global registry instance
action_registry = ActionRegistry()
