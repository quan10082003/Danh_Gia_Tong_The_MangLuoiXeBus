import os
import sys
import shutil

from src.config_loader import load_config
from src.modules.core_data_processor.vehicle_processor import VehicleData

test_name = "test_vehicle_processor"

def main():
    # Setup paths
    config = load_config()

    VEHICLE_PATH = config.data.matsim.before.input.transit_vehicle
    TEST_OUTPUT = os.path.join(config.test.output, test_name)
    VEH_TYPE_PATH = os.path.join(TEST_OUTPUT, "vehicles.csv")
    
    # Cleanup previous runs
    if os.path.exists(TEST_OUTPUT):
        shutil.rmtree(TEST_OUTPUT)
    os.makedirs(TEST_OUTPUT, exist_ok=True)
        
    print(f"Reading vehicles from: {VEHICLE_PATH}")
    vehicle_data = VehicleData(VEHICLE_PATH)
    vehicle_data.process()
    vehicle_data.save_vehicles_to_csv(VEH_TYPE_PATH)
    
    print(f"Test complete. Outputs in {TEST_OUTPUT}")

if __name__ == "__main__":
    main()