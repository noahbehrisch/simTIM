import os
import json
import glob
from typing import List, Dict, Optional
from src.actions.action_manager import (

    load_actions_from_directory, 
    save_action_to_library, 
    get_all_available_actions,
    action_manager
)

def list_available_actions() -> Dict[str, List[str]]:
    base_dir = os.path.join(os.path.dirname(__file__), 'library')
    result = {}
    attacks_dir = os.path.join(base_dir, 'attacks')
    if os.path.exists(attacks_dir):
        attack_files = glob.glob(os.path.join(attacks_dir, "*.json"))
        result['attacks'] = [os.path.basename(f) for f in attack_files]
    defenses_dir = os.path.join(base_dir, 'defenses')
    if os.path.exists(defenses_dir):
        defense_files = glob.glob(os.path.join(defenses_dir, "*.json"))
        result['defenses'] = [os.path.basename(f) for f in defense_files]
    return result

def get_action_details(action_name: str) -> Optional[Dict]:
    all_actions = get_all_available_actions()
    for action in all_actions:
        if action.name == action_name:
            return {
                'name': action.name,
                'type': action.action_type,
                'cost': action.cost,
                'duration': action.duration,
                'success_probability': action.success_probability
            }
    return None

def create_action_from_template(name: str, action_type: str = "node") -> Dict:
    template = {
        "name": name,
        "action_type": action_type,
        "cost": 100.0,
        "duration": 1.0,
        "success_probability": 0.8,
        "precondition": {
            "type": "constant",
            "value": True
        },
        "postcondition": {
            "type": "function_ref",
            "function": "your_postcondition_function"
        },
        "detection_probability": {
            "type": "constant",
            "value": 0.1
        },
        "damage_gain": {
            "one_off_damage": 0.0,
            "one_off_gain": 0.0,
            "time_damage": 0.0,
            "time_gain": 0.0
        }
    }
    return template

def validate_action_json(action_data: Dict) -> List[str]:
    errors = []
    required_fields = [
        'name', 'action_type', 'cost', 'duration', 'success_probability',
        'precondition', 'postcondition', 'detection_probability', 'damage_gain'
    ]
    for field in required_fields:
        if field not in action_data:
            errors.append(f"Missing required field: {field}")
    if 'action_type' in action_data:
        if action_data['action_type'] not in ['node', 'link']:
            errors.append("action_type must be 'node' or 'link'")
    if 'success_probability' in action_data:
        prob = action_data['success_probability']
        if not (0.0 <= prob <= 1.0):
            errors.append("success_probability must be between 0.0 and 1.0")
    return errors

def load_scenario_actions(scenario_name: str) -> List:
    scenario_dir = os.path.join(os.path.dirname(__file__), 'scenarios', scenario_name)
    if os.path.exists(scenario_dir):
        return load_actions_from_directory(scenario_dir)
    else:
        print(f"Scenario '{scenario_name}' not found")
        return []

def save_scenario_actions(scenario_name: str, actions: List) -> str:
    scenario_dir = os.path.join(os.path.dirname(__file__), 'scenarios', scenario_name)
    os.makedirs(scenario_dir, exist_ok=True)
    for action in actions:
        filename = action.name.lower().replace(' ', '_').replace('-', '_') + '.json'
        file_path = os.path.join(scenario_dir, filename)
        action_data = action_manager.action_to_json(action)
        with open(file_path, 'w') as f:
            json.dump(action_data, f, indent=2)
    return scenario_dir

def delete_action_file(action_name: str, action_category: str = None) -> bool:
    base_dir = os.path.join(os.path.dirname(__file__), 'library')
    if action_category:
        search_dirs = [os.path.join(base_dir, action_category)]
    else:
        search_dirs = [os.path.join(base_dir, 'attacks'), os.path.join(base_dir, 'defenses')]
    for search_dir in search_dirs:
        if os.path.exists(search_dir):
            files = glob.glob(os.path.join(search_dir, "*.json"))
            for file_path in files:
                try:
                    with open(file_path, 'r') as f:
                        action_data = json.load(f)
                        if action_data.get('name') == action_name:
                            os.remove(file_path)
                            return True
                except:
                    continue
    return False

def print_action_summary():
    available = list_available_actions()
    print("Available Actions Summary")
    print("=" * 40)
    for category, files in available.items():
        print(f"\n{category.title()}: {len(files)} actions")
        for file in files:
            action_name = file.replace('.json', '').replace('_', ' ').title()
            print(f"  - {action_name}")
if __name__ == "__main__":
    print_action_summary()