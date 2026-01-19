#BEFORE
import os
import sys
import shutil
import pandas as pd
import json

# Add project root to sys.path to enable importing from src
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
if project_root not in sys.path:
    sys.path.append(project_root)

from src.config_loader import load_config
from src.modules.core_data_processor.vehicle_processor import VehicleData
from src.modules.prepare_bus_score_data.ridership_prepare_processor import RidershipPrepareData
from src.modules.bus_scoring.travel_time_scoring import calculate_travel_time_scores

test_name = "test_travel_time_scoring_flow"

def main():
    # Setup paths
    config = load_config()
    
    # Inputs
    VEHICLE_XML_PATH = config.data.matsim.before.input.transit_vehicle
    if not os.path.isabs(VEHICLE_XML_PATH):
        VEHICLE_XML_PATH = os.path.join(project_root, VEHICLE_XML_PATH)

    EVENTS_PATH = config.data.matsim.before.output.events
    if not os.path.exists(EVENTS_PATH) and os.path.exists(EVENTS_PATH + ".gz"):
         EVENTS_PATH += ".gz"
         
    TEST_OUTPUT_DIR = os.path.join(config.test.output, test_name)
    VEHICLES_CSV = os.path.join(TEST_OUTPUT_DIR, "vehicles.csv")
    RIDERSHIP_CSV = os.path.join(TEST_OUTPUT_DIR, "ridership_with_types.csv")
    
    # Cleanup previous runs
    if os.path.exists(TEST_OUTPUT_DIR):
        shutil.rmtree(TEST_OUTPUT_DIR)
    os.makedirs(TEST_OUTPUT_DIR, exist_ok=True)
        
    print("--- Step 1: Process Vehicles (XML -> CSV) ---")
    vehicle_data = VehicleData(VEHICLE_XML_PATH)
    vehicle_data.process()
    vehicle_data.save_vehicles_to_csv(VEHICLES_CSV)
    
    print("\n--- Step 2: Prepare Ridership Data (Events + Vehicles -> Ridership CSV) ---")
    ridership_data = RidershipPrepareData(EVENTS_PATH, VEHICLES_CSV)
    ridership_data.process()
    ridership_data.save_ridership_to_csv(RIDERSHIP_CSV)
    
    print("\n--- Step 3: Calculate Travel Time Scores ---")
    print(f"Using Prepared Data: {RIDERSHIP_CSV}")
    
    scores = calculate_travel_time_scores(RIDERSHIP_CSV)
    
    # Save to JSON
    json_output_path = os.path.join(TEST_OUTPUT_DIR, "travel_time_scores.json")
    with open(json_output_path, 'w', encoding='utf-8') as f:
        json.dump(scores, f, indent=4)
        
    print(f"Scores saved to: {json_output_path}")
    print(f"Scores content: {scores}")

if __name__ == "__main__":
    main()
