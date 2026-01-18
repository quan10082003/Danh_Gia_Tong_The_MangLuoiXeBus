
import xml.etree.ElementTree as ET
import json
import os
import logging
from typing import List
from src.utils.file_utils import save_csv_from_list

class Vehicle:
    def __init__(self, id: str, type_id: str):
        self.id: str = id
        self.type_id: str = type_id

class VehicleData:
    def __init__(self, vehicle_path: str):
        self.vehicle_path = vehicle_path
        self.vehicle_list: List[Vehicle] = []

    def process(self):
        tree = ET.parse(self.vehicle_path)
        root = tree.getroot()
        
        # Handle namespaces by inspecting the tag name
        # MATSim XML files usually have namespaces, causing findall('vehicle') to fail
        for child in root:
            # Extract tag name without namespace (e.g., {url}vehicle -> vehicle)
            tag = child.tag.split('}')[-1] if '}' in child.tag else child.tag
            
            if tag == 'vehicle':
                veh_id = child.get('id')
                veh_type_id = child.get('type')
                self.vehicle_list.append(Vehicle(veh_id, veh_type_id))
            
        # Save Outputs
        
    
    def save_vehicles_to_csv(self, vehicles_csv_path: str):
        print(f"Saving processed vehicles to: {vehicles_csv_path}")
        save_csv_from_list(self.vehicle_list, vehicles_csv_path)

