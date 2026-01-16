import os
import yaml
import sys

class Config(dict):
    """
    A dictionary subclass that allows access to keys as attributes (dot notation).
    """
    def __getattr__(self, name):
        if name in self:
            return self[name]
        raise AttributeError(f"'Config' object has no attribute '{name}'")
    
    def __setattr__(self, key, value):
        self[key] = value

def dict_to_config(d):
    """
    Recursively converts a dictionary (and lists of dicts) to a Config object.
    """
    if isinstance(d, dict):
        cfg = Config()
        for key, value in d.items():
            cfg[key] = dict_to_config(value)
        return cfg
    elif isinstance(d, list):
        return [dict_to_config(item) for item in d]
    else:
        return d

def load_config(config_path=None):
    """
    Reads the config.yaml file and returns a configuration object allowing dot notation.
    
    Args:
        config_path (str, optional): Path to the config file. 
                                     If None, defaults to ../conf/config.yaml relative to this file.
    
    Returns:
        Config: A Config object representing the configuration.
    """
    if config_path is None:
        # Resolve default path relative to this file
        # This file is in src/, so project root is one level up
        current_dir = os.path.dirname(os.path.abspath(__file__)) # .../src
        project_root = os.path.dirname(current_dir) # .../Danh_Gia_Tong_The_MangLuoiXeBus
        config_path = os.path.join(project_root, 'conf', 'config.yaml')

    if not os.path.exists(config_path):
        raise FileNotFoundError(f"Config file not found at: {config_path}")

    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
            
        if not data:
            return Config()
            
        return dict_to_config(data)
    except yaml.YAMLError as exc:
        raise ValueError(f"Error parsing YAML file: {exc}")

if __name__ == "__main__":
    # Test the loader
    try:
        config = load_config()
        print("Configuration loaded successfully (YAML).")
        
        # Test generic access
        if hasattr(config, 'data'):
            print("Access via dot notation works: config.data found")
            try:
                print(f"Network Path: {config.data.matsim.before.input.network}")
            except AttributeError:
                print("Could not access matsmi.before.input.network")
                
        # Test grid access
        if hasattr(config, 'grid'):
             print(f"Grid: {config.grid.rows}x{config.grid.cols}")

    except Exception as e:
        print(f"Error loading config: {e}")
