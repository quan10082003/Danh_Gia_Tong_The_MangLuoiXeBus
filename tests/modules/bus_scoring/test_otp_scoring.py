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
from src.modules.prepare_bus_score_data.on_time_performance_prepare_processor import OnTimePerformancePrepareData
from src.modules.bus_scoring.on_time_performance_scoring import calculate_otp_score

test_name = "test_otp_scoring_flow"

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
    OTP_CSV = os.path.join(TEST_OUTPUT_DIR, "otp_data.csv")
    
    # Cleanup previous runs
    if os.path.exists(TEST_OUTPUT_DIR):
        shutil.rmtree(TEST_OUTPUT_DIR)
    os.makedirs(TEST_OUTPUT_DIR, exist_ok=True)
        
    print("--- Step 1: Process Vehicles (XML -> CSV) ---")
    vehicle_data = VehicleData(VEHICLE_XML_PATH)
    vehicle_data.process()
    vehicle_data.save_vehicles_to_csv(VEHICLES_CSV)
    
    print("\n--- Step 2: Prepare OTP Data (Events + Vehicles -> OTP CSV) ---")
    otp_processor = OnTimePerformancePrepareData(EVENTS_PATH, VEHICLES_CSV)
    otp_processor.process()
    otp_processor.save_otp_data_to_csv(OTP_CSV)
    
    print("\n--- Step 3: Calculate OTP Score ---")
    print(f"Using Prepared Data: {OTP_CSV}")
    
    # Test Logic: Filter arrDelay between -3 mins (-180s) and +3 mins (180s)
    filter_col = "arrDelay"
    min_val = -180.0
    max_val = 180.0
    
    print(f"Testing condition: {min_val} <= {filter_col} <= {max_val}")
    
    result = calculate_otp_score(OTP_CSV, filter_column=filter_col, min_threshold=min_val, max_threshold=max_val)
    
    # Save to JSON
    json_output_path = os.path.join(TEST_OUTPUT_DIR, "otp_score.json")
    with open(json_output_path, 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=4)
        
    print(f"Score saved to: {json_output_path}")
    print(f"Result: {json.dumps(result, indent=4)}")

if __name__ == "__main__":
    main()
