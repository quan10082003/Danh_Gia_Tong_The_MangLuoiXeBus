
import os
import sys
import shutil
import pandas as pd

# Add project root to sys.path to enable importing from src
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
if project_root not in sys.path:
    sys.path.append(project_root)

from src.config_loader import load_config
from src.modules.prepare_bus_score_data.ridership_prepare_processor import RidershipPrepareData
from src.modules.core_data_processor.vehicle_processor import VehicleData

test_name = "test_ridership_prepare_processor"

def main():
    # Setup paths
    config = load_config()
    
    # Inputs
    EVENTS_PATH = config.data.matsim.before.output.events
    if not os.path.exists(EVENTS_PATH) and os.path.exists(EVENTS_PATH + ".gz"):
         EVENTS_PATH += ".gz"
         
    # We need the vehicle type mapping. We can generate it or use an existing one.
    # Let's generate it to be safe, reusing logic from test_vehicle_processor
    VEHICLE_XML_PATH = config.data.matsim.before.input.transit_vehicle
    TEST_OUTPUT_DIR = os.path.join(config.test.output, test_name)
    VEHICLE_CSV_PATH = os.path.join(TEST_OUTPUT_DIR, "vehicles.csv")
    RIDERSHIP_OUTPUT_CSV = os.path.join(TEST_OUTPUT_DIR, "ridership_with_types.csv")
    
    # Cleanup previous runs
    if os.path.exists(TEST_OUTPUT_DIR):
        shutil.rmtree(TEST_OUTPUT_DIR)
    os.makedirs(TEST_OUTPUT_DIR, exist_ok=True)
        
    print("--- Step 1: Prepare Vehicle Types (XML -> CSV) ---")
    print(f"Reading vehicles from: {VEHICLE_XML_PATH}")
    vehicle_data = VehicleData(VEHICLE_XML_PATH)
    vehicle_data.process()
    vehicle_data.save_vehicles_to_csv(VEHICLE_CSV_PATH)
    
    print("\n--- Step 2: Process Ridership with Types ---")
    print(f"Using Events: {EVENTS_PATH}")
    print(f"Using Vehicle Types: {VEHICLE_CSV_PATH}")
    
    dataset = RidershipPrepareData(EVENTS_PATH, VEHICLE_CSV_PATH)
    dataset.process()
    dataset.save_ridership_to_csv(RIDERSHIP_OUTPUT_CSV)
    
    # Verification
    print("\n--- Step 3: Verify Output ---")
    if os.path.exists(RIDERSHIP_OUTPUT_CSV):
        df = pd.read_csv(RIDERSHIP_OUTPUT_CSV)
        print(f"Output columns: {list(df.columns)}")
        if "vehTypeList" in df.columns:
            print("SUCCESS: 'vehTypeList' column found.")
            print("Sample data:")
            print(df[["vehIDList", "vehTypeList"]].head())
        else:
            print("FAILURE: 'vehTypeList' column MISSING.")
    else:
        print("FAILURE: Output file not created.")

if __name__ == "__main__":
    main()
