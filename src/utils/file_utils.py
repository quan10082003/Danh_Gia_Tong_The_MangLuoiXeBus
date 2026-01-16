import csv
import json
import os
from typing import List, Dict, Any

def save_csv_from_list(data: List[Dict[str, Any]], output_path: str):
    if not data:
        print(f"No data to save to {output_path}")
        return

    try:
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        # Determine keys and row data based on whether item is dict or object
        first_item = data[0]
        if isinstance(first_item, dict):
            keys = first_item.keys()
            rows = data
        else:
            # Assume it's an object, use __dict__
            keys = first_item.__dict__.keys()
            rows = [item.__dict__ for item in data]

        with open(output_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=keys)
            writer.writeheader()    
            writer.writerows(rows)
            
        print(f"Successfully saved {len(data)} rows to {output_path}")

    except Exception as e:
        print(f"Error saving CSV to {output_path}: {e}")
        raise

def save_json(data: Any, output_path: str, indent: int = 4):
    try:
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=indent, ensure_ascii=False)
        print(f"Successfully saved JSON to {output_path}")

    except Exception as e:
        print(f"Error saving JSON to {output_path}: {e}")
        raise
