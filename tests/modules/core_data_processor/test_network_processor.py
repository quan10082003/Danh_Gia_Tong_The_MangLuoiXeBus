import os
import sys
import shutil

from src.config_loader import load_config
from src.modules.core_data_processor.network_processor import NetworkData

test_name = os.path.basename(__file__)

def main():
    # Setup paths
    config = load_config()

    NETWORK_PATH = config.data.matsim.static_input.network
    TEST_OUTPUT = os.path.join(config.test.output, test_name)
    NODE_PATH = os.path.join(TEST_OUTPUT, "nodes.csv")
    LINK_PATH = os.path.join(TEST_OUTPUT, "links.csv")
    
    # Cleanup previous runs
    if os.path.exists(TEST_OUTPUT):
        shutil.rmtree(TEST_OUTPUT)
    
    os.makedirs(TEST_OUTPUT, exist_ok=True)
    
    print(f"Reading network from: {NETWORK_PATH}")
    network_data = NetworkData(NETWORK_PATH)
    network_data.process()
    
    network_data.save_nodes_to_csv(NODE_PATH)
    network_data.save_links_to_csv(LINK_PATH)
    print(f"Test complete. Outputs in {TEST_OUTPUT}")

if __name__ == "__main__":
    main()