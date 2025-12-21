import json
import os
import glob
import logging
from typing import Dict, List, Callable, Optional, Any
from src.actions.action import Action
from src.actions.json_conditions import condition_evaluator, action_executor
from src.actions.link_actions import get_link_action_library
from src.core.access_levels import NodeAccessLevel
logger = logging.getLogger(__name__)

class ActionManager:

    def __init__(self):
        pass

    def validate_action_json(self, action_data: Dict[str, Any]) -> Dict[str, Any]:
        errors = []
        warnings = []
        required_fields = ['name', 'action_type', 'cost', 'duration', 'success_probability', 'precondition', 'postcondition', 'detection_probability', 'damage_gain']
        for field in required_fields:
            if field not in action_data:
                errors.append(f'Missing required field: {field}')
        if 'name' in action_data and (not isinstance(action_data['name'], str)):
            errors.append("'name' must be a string")
        if 'action_type' in action_data:
            if action_data['action_type'] not in ['node', 'link']:
                errors.append("'action_type' must be 'node' or 'link'")
        if 'cost' in action_data:
            if not isinstance(action_data['cost'], (int, float)) or action_data['cost'] < 0:
                errors.append("'cost' must be a non-negative number")
        if 'duration' in action_data:
            if not isinstance(action_data['duration'], (int, float)) or action_data['duration'] <= 0:
                errors.append("'duration' must be a positive number")
        if 'success_probability' in action_data:
            prob = action_data['success_probability']
            if not isinstance(prob, (int, float)) or not 0 <= prob <= 1:
                errors.append("'success_probability' must be a number between 0 and 1")
        if 'damage_gain' in action_data:
            dg = action_data['damage_gain']
            if not isinstance(dg, dict):
                errors.append("'damage_gain' must be a dictionary")
            else:
                required_dg_fields = ['one_off_damage', 'one_off_gain', 'time_damage', 'time_gain']
                for field in required_dg_fields:
                    if field not in dg:
                        errors.append(f"'damage_gain' missing required field: {field}")
                    elif not isinstance(dg[field], (int, float)):
                        errors.append(f"'damage_gain.{field}' must be a number")
        if 'precondition' in action_data and (not isinstance(action_data['precondition'], dict)):
            errors.append("'precondition' must be a dictionary")
        if 'postcondition' in action_data and (not isinstance(action_data['postcondition'], dict)):
            errors.append("'postcondition' must be a dictionary")
        if 'detection_probability' in action_data and (not isinstance(action_data['detection_probability'], dict)):
            errors.append("'detection_probability' must be a dictionary")
        return {'valid': len(errors) == 0, 'errors': errors, 'warnings': warnings}

    def create_function_from_spec(self, spec: Dict[str, Any]) -> Callable:
        if spec['type'] == 'function_ref':
            error_msg = f"function_ref '{spec['function']}' is no longer supported. Please convert to JSON conditions."
            logger.error(error_msg)
            raise ValueError(f"function_ref system has been removed. Convert '{spec['function']}' to JSON conditions.")
        elif spec['type'] == 'json_condition':
            return lambda node, access, actor: condition_evaluator.evaluate_condition(spec, node, access, actor)
        elif spec['type'] == 'compound':
            return lambda node, access, actor: condition_evaluator.evaluate_condition(spec, node, access, actor)
        elif spec['type'] in ['access_check', 'software_check', 'version_check', 'property_check', 'vulnerability_check', 'assets_check']:
            return lambda node, access, actor: condition_evaluator.evaluate_condition(spec, node, access, actor)
        elif spec['type'] == 'constant':
            value = spec['value']
            return lambda node, access, actor: value
        elif spec['type'] == 'zero':
            return lambda node, access, actor: 0.0
        elif spec['type'] == 'lambda':
            expression = spec['expression']
            if expression == 'zero':
                return lambda node, access, actor: 0.0
            else:
                try:
                    return eval(f'lambda node, access, actor: {expression}')
                except:
                    return lambda node, access, actor: 0.0
        elif spec['type'] == 'node_property_based':

            def detection_function(node, access, actor):
                base_prob = spec.get('base_probability', 0.0)
                modifier_sum = 0.0
                for modifier in spec.get('property_modifiers', []):
                    prop_name = modifier['property']
                    prop_value = None
                    if hasattr(node, prop_name):
                        prop_value = getattr(node, prop_name)
                        if 'nested_property' in modifier and isinstance(prop_value, dict):
                            nested_prop = modifier['nested_property']
                            prop_value = prop_value.get(nested_prop)
                    if prop_value is not None:
                        if 'value' in modifier:
                            if prop_value == modifier['value']:
                                modifier_sum += modifier.get('probability_modifier', 0.0)
                        elif 'values' in modifier:
                            if prop_value in modifier['values']:
                                modifier_sum += modifier.get('probability_modifier', 0.0)
                return min(1.0, base_prob + modifier_sum)
            return detection_function
        else:
            raise ValueError(f"Unknown function spec type: {spec['type']}")

    def create_postcondition_from_spec(self, spec: Dict[str, Any]) -> Callable:
        if spec['type'] == 'function_ref':
            return self.get_function(spec['function'])
        elif spec['type'] == 'compound':
            return lambda node, access, actor: action_executor.execute_postcondition(spec, node, access, actor)
        elif spec.get('type') in ['set_access', 'set_property', 'set_software', 'add_vulnerability', 'remove_vulnerability', 'increment_counter', 'set_links_access', 'set_access_neighbors', 'clear_assets']:
            return lambda node, access, actor: action_executor.execute_postcondition(spec, node, access, actor)
        else:
            return self.create_function_from_spec(spec)

    def action_from_json(self, action_data: Dict[str, Any]) -> Action:
        validation = self.validate_action_json(action_data)
        if not validation['valid']:
            error_msg = f"Invalid action configuration for '{action_data.get('name', 'unknown')}':\n"
            error_msg += '\n'.join((f'  - {err}' for err in validation['errors']))
            logger.error(error_msg)
            raise ValueError(error_msg)
        if validation['warnings']:
            for warning in validation['warnings']:
                logger.warning(f"Action '{action_data['name']}': {warning}")
        try:
            precondition = self.create_function_from_spec(action_data['precondition'])
            postcondition = self.create_postcondition_from_spec(action_data['postcondition'])
            detection_probability = self.create_function_from_spec(action_data['detection_probability'])
            damage_gain = action_data['damage_gain']
            one_off_damage = lambda node, access, actor: damage_gain['one_off_damage']
            one_off_gain = lambda node, access, actor: damage_gain['one_off_gain']
            time_damage = lambda node, access, actor: damage_gain['time_damage']
            time_gain = lambda node, access, actor: damage_gain['time_gain']
            action = Action(name=action_data['name'], precondition=precondition, postcondition=postcondition, cost=action_data['cost'], duration=action_data['duration'], success_probability=action_data['success_probability'], action_type=action_data['action_type'], detection_probability=detection_probability, one_off_damage=one_off_damage, one_off_gain=one_off_gain, time_damage=time_damage, time_gain=time_gain)
            action._json_data = action_data
            logger.debug(f'Created action: {action.name}')
            return action
        except Exception as e:
            raise ValueError(f"Error creating action '{action_data.get('name', 'unknown')}': {e}")

    def action_to_json(self, action: Action) -> Dict[str, Any]:

        def get_function_spec(func):
            if hasattr(func, '__name__') and func.__name__ in self.function_registry:
                return {'type': 'function_ref', 'function': func.__name__}
            elif hasattr(func, '__name__') and func.__name__ == '<lambda>':
                try:
                    test_result = func(None, None, None)
                    if isinstance(test_result, (int, float)):
                        return {'type': 'constant', 'value': test_result}
                except:
                    pass
                return {'type': 'constant', 'value': 0.0}
            else:
                return {'type': 'constant', 'value': 0.0}
        action_data = {'name': action.name, 'action_type': action.action_type, 'cost': action.cost, 'duration': action.duration, 'success_probability': action.success_probability, 'precondition': get_function_spec(action.precondition), 'postcondition': get_function_spec(action.postcondition), 'detection_probability': get_function_spec(action.detection_probability), 'damage_gain': {'one_off_damage': 0.0, 'one_off_gain': 0.0, 'time_damage': 0.0, 'time_gain': 0.0}}
        try:
            action_data['damage_gain']['one_off_damage'] = action.one_off_damage(None, None, None)
            action_data['damage_gain']['one_off_gain'] = action.one_off_gain(None, None, None)
            action_data['damage_gain']['time_damage'] = action.time_damage(None, None, None)
            action_data['damage_gain']['time_gain'] = action.time_gain(None, None, None)
        except:
            pass
        return action_data

    def load_actions_from_directory(self, directory_path: str) -> List[Action]:
        actions = []
        if not os.path.exists(directory_path):
            return actions
        json_files = glob.glob(os.path.join(directory_path, '*.json'))
        for json_file in json_files:
            try:
                with open(json_file, 'r') as f:
                    action_data = json.load(f)
                    action = self.action_from_json(action_data)
                    actions.append(action)
            except Exception as e:
                logger.warning(f'Failed to load action from {json_file}: {e}')
        return actions

    def load_all_actions(self) -> Dict[str, List[Action]]:
        base_dir = os.path.join(os.path.dirname(__file__), 'library')
        attacks_dir = os.path.join(base_dir, 'attacks')
        attack_actions = self.load_actions_from_directory(attacks_dir)
        defenses_dir = os.path.join(base_dir, 'defenses')
        defense_actions = self.load_actions_from_directory(defenses_dir)
        return {'attack_actions': attack_actions, 'defense_actions': defense_actions}

    def get_attack_actions(self) -> List[Action]:
        actions = self.load_all_actions()
        attack_actions = actions.get('attack_actions', [])
        link_actions = get_link_action_library()
        attack_actions.extend(link_actions.values())
        return attack_actions

    def get_defense_actions(self) -> List[Action]:
        actions = self.load_all_actions()
        return actions.get('defense_actions', [])

    def get_all_available_actions(self) -> List[Action]:
        all_actions = self.load_all_actions()
        return all_actions.get('attack_actions', []) + all_actions.get('defense_actions', [])

    def load_specific_actions(self, action_names: List[str]) -> List[Action]:
        all_actions = self.get_all_available_actions()
        return [action for action in all_actions if action.name in action_names]

    def load_actions_from_file(self, file_path: str) -> Dict[str, List[Action]]:
        with open(file_path, 'r') as f:
            data = json.load(f)
        actions = {}
        for action_category, action_list in data['action_types'].items():
            actions[action_category] = []
            for action_data in action_list:
                action = self.action_from_json(action_data)
                actions[action_category].append(action)
        return actions

    def save_actions_to_file(self, actions: Dict[str, List[Action]], file_path: str):
        data = {'action_types': {}}
        for action_category, action_list in actions.items():
            data['action_types'][action_category] = []
            for action in action_list:
                action_data = self.action_to_json(action)
                data['action_types'][action_category].append(action_data)
        with open(file_path, 'w') as f:
            json.dump(data, f, indent=2)

    def save_action_to_file(self, action: Action, file_path: str):
        action_data = self.action_to_json(action)
        with open(file_path, 'w') as f:
            json.dump(action_data, f, indent=2)

    def save_action_to_library(self, action: Action, action_type: str='attacks') -> str:
        base_dir = os.path.join(os.path.dirname(__file__), 'library')
        target_dir = os.path.join(base_dir, action_type)
        if not os.path.exists(target_dir):
            os.makedirs(target_dir)
        filename = action.name.lower().replace(' ', '_').replace('-', '_') + '.json'
        file_path = os.path.join(target_dir, filename)
        self.save_action_to_file(action, file_path)
        return file_path

    def save_actions(self, attack_actions: List[Action], defense_actions: List[Action], file_path: str=None):
        if file_path:
            actions = {'attack_actions': attack_actions, 'defense_actions': defense_actions}
            self.save_actions_to_file(actions, file_path)
        else:
            for action in attack_actions:
                self.save_action_to_library(action, 'attacks')
            for action in defense_actions:
                self.save_action_to_library(action, 'defenses')
action_manager = ActionManager()

def get_attack_actions():
    return action_manager.get_attack_actions()

def get_defense_actions():
    return action_manager.get_defense_actions()

def get_all_available_actions():
    return action_manager.get_all_available_actions()

def load_actions_from_directory(directory_path: str):
    return action_manager.load_actions_from_directory(directory_path)

def load_all_actions():
    return action_manager.load_all_actions()

def load_specific_actions(action_names: List[str]):
    return action_manager.load_specific_actions(action_names)

def save_action_to_file(action: Action, file_path: str):
    return action_manager.save_action_to_file(action, file_path)

def save_action_to_library(action: Action, action_type: str='attacks'):
    return action_manager.save_action_to_library(action, action_type)

def save_actions(attack_actions: List[Action], defense_actions: List[Action], file_path: str=None):
    return action_manager.save_actions(attack_actions, defense_actions, file_path)

def list_available_actions() -> Dict[str, List[str]]:
    base_dir = os.path.join(os.path.dirname(__file__), 'library')
    result = {}
    attacks_dir = os.path.join(base_dir, 'attacks')
    if os.path.exists(attacks_dir):
        attack_files = glob.glob(os.path.join(attacks_dir, '*.json'))
        result['attacks'] = [os.path.basename(f) for f in attack_files]
    defenses_dir = os.path.join(base_dir, 'defenses')
    if os.path.exists(defenses_dir):
        defense_files = glob.glob(os.path.join(defenses_dir, '*.json'))
        result['defenses'] = [os.path.basename(f) for f in defense_files]
    return result

def get_action_details(action_name: str) -> Optional[Dict]:
    all_actions = get_all_available_actions()
    for action in all_actions:
        if action.name == action_name:
            return {'name': action.name, 'type': action.action_type, 'cost': action.cost, 'duration': action.duration, 'success_probability': action.success_probability}
    return None

def print_action_summary():
    available = list_available_actions()
    print('Available Actions Summary')
    print('=' * 40)
    for category, files in available.items():
        print(f'\n{category.title()}: {len(files)} actions')
        for file in files:
            action_name = file.replace('.json', '').replace('_', ' ').title()
            print(f'  - {action_name}')

def analyze_action_access_impact(action, current_access: str) -> Optional[str]:
    try:
        if hasattr(action, '_json_data'):
            postcondition = action._json_data.get('postcondition', {})
        else:
            return None
        return _analyze_postcondition_access(postcondition)
    except Exception:
        return None

def _analyze_postcondition_access(postcondition: Dict[str, Any]) -> Optional[str]:
    if postcondition.get('type') == 'compound':
        actions = postcondition.get('actions', [])
        for action in actions:
            if action.get('type') == 'set_access':
                return action.get('value')
    elif postcondition.get('type') == 'set_access':
        return postcondition.get('value')
    elif postcondition.get('type') in ['set_links_access', 'set_property', 'clear_assets', 'add_vulnerability', 'remove_vulnerability', 'increment_counter', 'set_software']:
        return 'NO_ACCESS_CHANGE'
    return None

def would_action_improve_access(action, node, current_access, actor_id: str) -> bool:
    if hasattr(action, 'is_link_action') and action.is_link_action():
        if hasattr(node, 'successful_actions_by_actor'):
            actor_actions = node.successful_actions_by_actor.get(actor_id, set())
            if action.name in actor_actions:
                return False
        return True
    if not hasattr(node, 'id') or not hasattr(node, 'access'):
        return False
    try:
        if isinstance(current_access, str):
            current_level = NodeAccessLevel.from_string(current_access)
        else:
            current_level = current_access
        current_access_str = current_level.to_string() if hasattr(current_level, 'to_string') else str(current_level)
        predicted_access = analyze_action_access_impact(action, current_access_str)
        if predicted_access == 'NO_ACCESS_CHANGE':
            if hasattr(node, 'successful_actions_by_actor'):
                actor_actions = node.successful_actions_by_actor.get(actor_id, set())
                if action.name in actor_actions:
                    print(f"[DEBUG would_improve] {action.name} on {getattr(node, 'id', '?')}: Already executed, returning False")
                    return False
                else:
                    print(f"[DEBUG would_improve] {action.name} on {getattr(node, 'id', '?')}: First time, returning True")
            else:
                print(f"[DEBUG would_improve] {action.name} on {getattr(node, 'id', '?')}: No history, returning True")
            return True
        elif predicted_access:
            predicted_level = NodeAccessLevel.from_string(predicted_access)
            return predicted_level > current_level
        action_name_lower = action.name.lower()
        if any((keyword in action_name_lower for keyword in ['scan', 'reconnaissance', 'discovery'])):
            if hasattr(node, 'successful_actions_by_actor'):
                actor_actions = node.successful_actions_by_actor.get(actor_id, set())
                if action.name in actor_actions:
                    return False
            return True
        if any((keyword in action_name_lower for keyword in ['phishing', 'exploitation', 'brute'])):
            target_level = NodeAccessLevel.USER
        elif any((keyword in action_name_lower for keyword in ['privilege', 'escalation', 'admin'])):
            target_level = NodeAccessLevel.ADMIN
        elif any((keyword in action_name_lower for keyword in ['exfiltration', 'data', 'steal'])):
            return current_level >= NodeAccessLevel.USER and (not _has_already_exfiltrated(node, actor_id))
        elif current_level == NodeAccessLevel.VISIBLE:
            target_level = NodeAccessLevel.USER
        elif current_level == NodeAccessLevel.USER:
            target_level = NodeAccessLevel.ADMIN
        else:
            return False
        return target_level > current_level
    except Exception:
        current_level = NodeAccessLevel.from_string(current_access)
        return current_level < NodeAccessLevel.ADMIN
    return False

def _has_already_exfiltrated(node, actor_id: str) -> bool:
    if not hasattr(node, 'assets') or len(node.assets) == 0:
        return True
    if hasattr(node, 'successful_actions_by_actor'):
        actor_actions = node.successful_actions_by_actor.get(actor_id, set())
        if 'Data Exfiltration' in actor_actions:
            return True
    return False
if __name__ == '__main__':
    print_action_summary()
all_actions = load_all_actions()
all_attack_actions = all_actions.get('attack_actions', [])
all_defense_actions = all_actions.get('defense_actions', [])
node_attack_actions = [action for action in all_attack_actions if action.is_node_action()]
link_attack_actions = [action for action in all_attack_actions if action.is_link_action()]
node_defense_actions = [action for action in all_defense_actions if action.is_node_action()]
link_defense_actions = [action for action in all_defense_actions if action.is_link_action()]
all_available_actions = get_all_available_actions()
action_registry = action_manager