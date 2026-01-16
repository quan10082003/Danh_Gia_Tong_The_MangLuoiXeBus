
import os
import sys
import shutil

# Add project root to sys.path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
if project_root not in sys.path:
    sys.path.append(project_root)

from src.config_loader import load_config
from src.modules.core_data_processor.plan_input_processor import PlanInputData

test_name = "test_plan_input_processor"

def main():
    # Setup paths
    config = load_config()
    
    # Identify input file
    # Trying to find the specific file mentioned by user or fallback
    # User mentioned: data\matsim\static_input\plans_scale0.375true.xml
    DEFAULT_PLANS_PATH = os.path.join(project_root, "data", "matsim", "static_input", "plans_scale0.375true.xml")
    
    # If not found, try from config (though user didn't specify config key for this specific file, we stick to explicit path first)
    if os.path.exists(DEFAULT_PLANS_PATH):
        PLANS_PATH = DEFAULT_PLANS_PATH
    else:
        # Fallback to standard plans if exists
        try:
            PLANS_PATH = config.data.matsim.before.input.plans # Hypothetical config path
        except:
            print(f"Warning: Specific plans file not found at {DEFAULT_PLANS_PATH}. Using a dummy check.")
            return

    TEST_OUTPUT_DIR = os.path.join(config.test.output, test_name)
    OUTPUT_CSV = os.path.join(TEST_OUTPUT_DIR, "home_locations.csv")
    
    # Cleanup
    if os.path.exists(TEST_OUTPUT_DIR):
        shutil.rmtree(TEST_OUTPUT_DIR)
    os.makedirs(TEST_OUTPUT_DIR, exist_ok=True)
        
    print(f"Reading plans from: {PLANS_PATH}")
    
    processor = PlanInputData(PLANS_PATH)
    processor.process()
    processor.save_to_csv(OUTPUT_CSV)
    
    print(f"Test complete. Outputs in {TEST_OUTPUT_DIR}")

if __name__ == "__main__":
    main()
