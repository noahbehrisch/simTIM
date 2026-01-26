import glob
import json
import os


class DataLoaders:
    def load_operating_systems(self):
        os_dir = "src/networks/node_properties/operating_systems"
        os_list = []
        for filepath in glob.glob(os.path.join(os_dir, "*.json")):
            try:
                with open(filepath) as f:
                    os_data = json.load(f)
                    os_list.append(os_data["name"])
            except Exception as e:
                print(f"Error loading {filepath}: {e}")
        priority_os = []
        other_os = []
        for os_name in sorted(os_list):
            if os_name == "Ubuntu":
                priority_os.insert(0, os_name)
            elif os_name == "Windows Server":
                priority_os.append(os_name)
            else:
                other_os.append(os_name)
        return priority_os + other_os

    def load_os_data(self, os_name):
        os_dir = "src/networks/node_properties/operating_systems"
        filename = os_name.replace(" ", "_") + ".json"
        filepath = os.path.join(os_dir, filename)
        try:
            with open(filepath) as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading OS data for {os_name}: {e}")
            return {"name": os_name, "versions": []}

    def load_services(self):
        try:
            with open("src/networks/node_properties/services/services.json") as f:
                data = json.load(f)
                return data["services"]
        except Exception as e:
            print(f"Error loading services: {e}")
            return []

    def load_assets(self):
        try:
            with open("src/networks/node_properties/assets/assets.json") as f:
                data = json.load(f)
                return data["assets"]
        except Exception as e:
            print(f"Error loading assets: {e}")
            return []

    def load_categories(self):
        try:
            with open("src/networks/node_properties/categories/categories.json") as f:
                data = json.load(f)
                return data["categories"]
        except Exception as e:
            print(f"Error loading categories: {e}")
            return []
