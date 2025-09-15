from actions.action_registry import action_registry
import os
import glob

def load_actions_from_directory(directory_path):
    actions = []
    if not os.path.exists(directory_path):
        return actions
    
    json_files = glob.glob(os.path.join(directory_path, "*.json"))
    for json_file in json_files:
        try:
            with open(json_file, 'r') as f:
                import json
                action_data = json.load(f)
                action = action_registry.action_from_json(action_data)
                actions.append(action)
        except Exception as e:
            print(f"Warning: Failed to load action from {json_file}: {e}")
    
    return actions

def load_all_actions():
    base_dir = os.path.join(os.path.dirname(__file__), 'library')
    
    # Load attack actions
    attacks_dir = os.path.join(base_dir, 'attacks')
    attack_actions = load_actions_from_directory(attacks_dir)
    
    # Load defense actions
    defenses_dir = os.path.join(base_dir, 'defenses')
    defense_actions = load_actions_from_directory(defenses_dir)
    
    return {
        'attack_actions': attack_actions,
        'defense_actions': defense_actions
    }

def get_attack_actions():
    actions = load_all_actions()
    return actions.get('attack_actions', [])

def get_defense_actions():
    actions = load_all_actions()
    return actions.get('defense_actions', [])

def get_all_available_actions():
    all_actions = load_all_actions()
    return all_actions.get('attack_actions', []) + all_actions.get('defense_actions', [])

def load_specific_actions(action_names):
    all_actions = get_all_available_actions()
    return [action for action in all_actions if action.name in action_names]

def save_action_to_file(action, file_path):
    action_data = action_registry.action_to_json(action)
    with open(file_path, 'w') as f:
        import json
        json.dump(action_data, f, indent=2)

def save_action_to_library(action, action_type="attacks"):
    base_dir = os.path.join(os.path.dirname(__file__), 'library')
    target_dir = os.path.join(base_dir, action_type)
    
    if not os.path.exists(target_dir):
        os.makedirs(target_dir)
    

    filename = action.name.lower().replace(' ', '_').replace('-', '_') + '.json'
    file_path = os.path.join(target_dir, filename)
    
    save_action_to_file(action, file_path)
    return file_path

def save_actions(attack_actions, defense_actions, file_path=None):
    if file_path:
        actions = {
            'attack_actions': attack_actions,
            'defense_actions': defense_actions
        }
        action_registry.save_actions_to_file(actions, file_path)
    else:
        # Save to individual files in library
        for action in attack_actions:
            save_action_to_library(action, "attacks")
        for action in defense_actions:
            save_action_to_library(action, "defenses")

all_actions = load_all_actions()
all_attack_actions = all_actions.get('attack_actions', [])
all_defense_actions = all_actions.get('defense_actions', [])

node_attack_actions = [action for action in all_attack_actions if action.is_node_action()]
link_attack_actions = [action for action in all_attack_actions if action.is_link_action()]
node_defense_actions = [action for action in all_defense_actions if action.is_node_action()]
link_defense_actions = [action for action in all_defense_actions if action.is_link_action()]


all_available_actions = get_all_available_actions()

