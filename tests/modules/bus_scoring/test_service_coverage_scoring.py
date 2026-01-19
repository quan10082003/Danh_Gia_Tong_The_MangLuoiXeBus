#BEFORE
import os
import sys
import shutil
import json

# Add project root to sys.path to enable importing from src
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
if project_root not in sys.path:
    sys.path.append(project_root)

from src.config_loader import load_config
from src.modules.bus_scoring.service_coverage_scoring import start_scoring
from src.modules.core_data_processor.plan_input_processor import PlanInputData

test_name = "test_service_coverage_scoring"

def main():
    # Setup paths
    config = load_config()
    
    # Inputs
    SCHEDULE_PATH = config.data.matsim.before.input.transit_schedule
    PLANS_PATH = config.data.matsim.static_input.plan # "plans_scale0.375true.xml"
    
    # Resolve absolute paths if needed
    if not os.path.isabs(SCHEDULE_PATH):
        SCHEDULE_PATH = os.path.join(project_root, SCHEDULE_PATH)
    if not os.path.isabs(PLANS_PATH):
        PLANS_PATH = os.path.join(project_root, PLANS_PATH)

    TEST_OUTPUT_DIR = os.path.join(config.test.output, test_name)
    
    # Cleanup previous runs
    if os.path.exists(TEST_OUTPUT_DIR):
        shutil.rmtree(TEST_OUTPUT_DIR)
    os.makedirs(TEST_OUTPUT_DIR, exist_ok=True)

    # Step 0: Pre-process Plans to Homes CSV happens inside start_scoring now
    
    print(f"--- Running Service Coverage Scoring ---")
    
    # We can call start_scoring directly which wraps everything
    result = start_scoring(SCHEDULE_PATH, PLANS_PATH, TEST_OUTPUT_DIR, radius=400.0)
    
    # Save to JSON
    json_output_path = os.path.join(TEST_OUTPUT_DIR, "coverage_score.json")
    with open(json_output_path, 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=4)
    
    # Save to JSON
    json_output_path = os.path.join(TEST_OUTPUT_DIR, "coverage_score.json")
    with open(json_output_path, 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=4)
        
    print(f"Score saved to: {json_output_path}")
    print(f"Result: {json.dumps(result, indent=4)}")

if __name__ == "__main__":
    main()
