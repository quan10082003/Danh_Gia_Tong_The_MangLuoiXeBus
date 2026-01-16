
import os
import sys
import shutil
import pandas as pd

# Add project root to sys.path to enable importing from src
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
if project_root not in sys.path:
    sys.path.append(project_root)

from src.config_loader import load_config
from src.modules.core_data_processor.vehicle_processor import VehicleData
from src.modules.bus_scoring.ridership import calculate_bus_ridership

test_name = "test_ridership_flow"

def main():
    # Setup paths
    config = load_config()
    
    # Input 1: Vehicle XML (Source)
    VEHICLE_XML_PATH = config.data.matsim.before.input.transit_vehicle
    if not os.path.isabs(VEHICLE_XML_PATH):
        VEHICLE_XML_PATH = os.path.join(project_root, VEHICLE_XML_PATH)

    # Input 2: Legs CSV (Existing Output)
    LEGS_PATH = config.data.matsim.before.output.legs
    TEST_OUTPUT_DIR = os.path.join(config.test.output, test_name)
    PROCESSED_VEHICLES_CSV = os.path.join(TEST_OUTPUT_DIR, "vehicles.csv")
    
    # Cleanup previous runs
    if os.path.exists(TEST_OUTPUT_DIR):
        shutil.rmtree(TEST_OUTPUT_DIR)
    os.makedirs(TEST_OUTPUT_DIR, exist_ok=True)
        
    print("--- Step 1: Process Vehicles (XML -> CSV) ---")
    vehicle_data = VehicleData(VEHICLE_XML_PATH)
    vehicle_data.process()
    vehicle_data.save_vehicles_to_csv(PROCESSED_VEHICLES_CSV)
    
    print("\n--- Step 2: Calculate Bus Ridership ---")
    print(f"Using Legs Data: {LEGS_PATH}")
    print(f"Using Vehicle Data: {PROCESSED_VEHICLES_CSV}")
    
    unique_persons = calculate_bus_ridership(LEGS_PATH, PROCESSED_VEHICLES_CSV)
    print(f"\nSUCCESS: Calculated Bus Ridership (Unique Persons): {unique_persons}")

if __name__ == "__main__":
    main()
