import os
import sys
import shutil

# Add project root to sys.path to enable importing from src
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
if project_root not in sys.path:
    sys.path.append(project_root)

from src.config_loader import load_config
from src.modules.core_data_processor.schedule_processor import TransitScheduleData

test_name = os.path.basename(__file__)

def main():
    # Setup paths
    config = load_config()

    SCHEDULE_PATH = config.data.matsim.before.input.transit_schedule
    TEST_OUTPUT = os.path.join(config.test.output, test_name)
    
    STOPS_PATH = os.path.join(TEST_OUTPUT, "stops.csv")
    ROUTES_PATH = os.path.join(TEST_OUTPUT, "routes.csv")
    ROUTE_STOPS_PATH = os.path.join(TEST_OUTPUT, "route_stops.csv")
    ROUTE_LINKS_PATH = os.path.join(TEST_OUTPUT, "route_links.csv")
    
    # Cleanup previous runs
    if os.path.exists(TEST_OUTPUT):
        shutil.rmtree(TEST_OUTPUT)
    os.makedirs(TEST_OUTPUT, exist_ok=True)
        
    print(f"Reading schedule from: {SCHEDULE_PATH}")
    schedule_data = TransitScheduleData(SCHEDULE_PATH)
    schedule_data.process()
    
    schedule_data.save_stops_to_csv(STOPS_PATH)
    schedule_data.save_routes_to_csv(ROUTES_PATH)
    schedule_data.save_route_stops_to_csv(ROUTE_STOPS_PATH)
    schedule_data.save_route_links_to_csv(ROUTE_LINKS_PATH)
    
    print(f"Test complete. Outputs in {TEST_OUTPUT}")

if __name__ == "__main__":
    main()
