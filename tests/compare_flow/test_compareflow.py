
import os
import sys
import shutil
import pandas as pd
import json
from enum import Enum

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if project_root not in sys.path:
    sys.path.append(project_root)

from src.config_loader import load_config

# Import Processors
from src.modules.core_data_processor.vehicle_processor import VehicleData
from src.modules.core_data_processor.plan_input_processor import PlanInputData
from src.modules.prepare_bus_score_data.ridership_prepare_processor import RidershipPrepareData
from src.modules.prepare_bus_score_data.on_time_performance_prepare_processor import OnTimePerformancePrepareData
from src.modules.bus_scoring.service_coverage_scoring import ServiceCoveragePrepareData

# Import Scoring Functions
from src.modules.bus_scoring.ridership_scoring import calculate_bus_ridership
from src.modules.bus_scoring.travel_time_scoring import calculate_travel_time_scores
from src.modules.bus_scoring.on_time_performance_scoring import calculate_otp_score

class Scenario(Enum):
    BEFORE = "before"
    AFTER = "after"

class ScenarioPaths:
    def __init__(self, config, scenario: Scenario):
        data_cfg = config.data.matsim
        scen_cfg = data_cfg.before if scenario == Scenario.BEFORE else data_cfg.after
        
        self.vehicle_xml = self._abs(scen_cfg.input.transit_vehicle)
        self.schedule_xml = self._abs(scen_cfg.input.transit_schedule)
        self.events_xml = self._abs(scen_cfg.output.events)
        
        # Check and append .gz if needed for events
        if not os.path.exists(self.events_xml) and os.path.exists(self.events_xml + ".gz"):
            self.events_xml += ".gz"
            
        # Static population plan (Same for both usually, but code allows flexibility if needed)
        self.plans_xml = self._abs(data_cfg.static_input.plan)

    def _abs(self, path):
         if not os.path.isabs(path):
             return os.path.join(project_root, path)
         return path

def run_scenario_scoring(config, scenario: Scenario, output_base_dir: str):
    print(f"\n{'='*20} Running Scenario: {scenario.value.upper()} {'='*20}")
    
    paths = ScenarioPaths(config, scenario)
    
    # Setup Output Directory for this scenario
    scen_out_dir = os.path.join(output_base_dir, scenario.value)
    os.makedirs(scen_out_dir, exist_ok=True)
    
    # Intermediate Files
    VEHICLES_CSV = os.path.join(scen_out_dir, "vehicles.csv")
    HOMES_CSV = os.path.join(scen_out_dir, "homes_processed.csv")
    RIDERSHIP_CSV = os.path.join(scen_out_dir, "ridership_processed.csv")
    OTP_CSV = os.path.join(scen_out_dir, "otp_processed.csv")
    
    scores = {}

    # --- 1. Vehicle Processing ---
    print("--- 1. Processing Vehicles ---")
    if os.path.exists(paths.vehicle_xml):
        v_proc = VehicleData(paths.vehicle_xml)
        v_proc.process()
        v_proc.save_vehicles_to_csv(VEHICLES_CSV)
    else:
        print(f"CRITICAL: Vehicle XML not found: {paths.vehicle_xml}")

    # --- 2. Plan/Population Processing (Homes) ---
    print("\n--- 2. Processing Population Plans (Homes) ---")
    if os.path.exists(paths.plans_xml):
        # Only process if output doesn't exist or force
        p_proc = PlanInputData(paths.plans_xml)
        p_proc.process()
        p_proc.save_to_csv(HOMES_CSV)
    else:
        print(f"CRITICAL: Plans XML not found: {paths.plans_xml}")


    # --- 3. Ridership & Travel Time Preparation ---
    print("\n--- 3. Preparing Ridership Data ---")
    if os.path.exists(paths.events_xml):
        r_prep = RidershipPrepareData(paths.events_xml, VEHICLES_CSV)
        r_prep.process()
        r_prep.save_ridership_to_csv(RIDERSHIP_CSV)
    else:
        print(f"CRITICAL: Events XML not found: {paths.events_xml}")

    # --- 4. OTP Preparation ---
    print("\n--- 4. Preparing OTP Data ---")
    if os.path.exists(paths.events_xml):
        otp_prep = OnTimePerformancePrepareData(paths.events_xml, VEHICLES_CSV)
        otp_prep.process()
        otp_prep.save_otp_data_to_csv(OTP_CSV)


    # --- SCORING ---
    print("\n--- 5. Calculating Scores ---")

    # A. Ridership Score
    valid_ridership = os.path.exists(RIDERSHIP_CSV)
    if valid_ridership:
        # Now returns Dict with percentage
        r_res = calculate_bus_ridership(RIDERSHIP_CSV, HOMES_CSV)
        scores['ridership_unique_persons'] = r_res['unique_persons_bus']
        scores['ridership_percentage'] = r_res['ridership_percentage']
        scores['total_population'] = r_res['total_population']
    
    # B. Travel Time Score
    if valid_ridership:
        tt_res = calculate_travel_time_scores(RIDERSHIP_CSV)
        scores['car_travel_time_total'] = tt_res['total_car_travel_time']
        scores['bus_travel_time_total'] = tt_res['total_bus_travel_time']

    # C. On-Time Performance Score
    if os.path.exists(OTP_CSV):
        # Default threshold: +- 3 mins
        otp_res = calculate_otp_score(OTP_CSV, min_threshold=-180, max_threshold=180)
        scores['otp_percentage'] = otp_res['otp_percentage']
        scores['otp_on_time_count'] = otp_res['on_time_records']
        # scores['otp_total_count'] = otp_res['total_records']
        
    # D. Service Coverage Score
    # Now uses pre-processed HOMES_CSV
    print("\n--- Calculating Service Coverage ---")
    if os.path.exists(paths.schedule_xml) and os.path.exists(HOMES_CSV):
        cov_prep = ServiceCoveragePrepareData(paths.schedule_xml, HOMES_CSV)
        cov_prep.process()
        cov_res = cov_prep.calculate_coverage(radius=400.0)
        scores['coverage_percentage'] = cov_res['percentage']
        scores['coverage_pop_covered'] = cov_res['covered_pop']
        # scores['coverage_pop_total'] = cov_res['total_pop']
    
    # Save Scenario Score JSON
    score_json_path = os.path.join(scen_out_dir, "scores.json")
    with open(score_json_path, 'w', encoding='utf-8') as f:
        json.dump(scores, f, indent=4)
        
    return scores

def main():
    test_name = "compare_flow_full"
    config = load_config()
    output_base_dir = os.path.join(config.test.output, test_name)
    
    # Clean previous run
    if os.path.exists(output_base_dir):
        shutil.rmtree(output_base_dir)
    os.makedirs(output_base_dir, exist_ok=True)
    
    # Run Scenarios
    before_scores = run_scenario_scoring(config, Scenario.BEFORE, output_base_dir)
    after_scores = run_scenario_scoring(config, Scenario.AFTER, output_base_dir)
    
    # JSON Comparison Output
    print(f"\n{'='*20} COMPARISON RESULTS {'='*20}")

    comparison_json = {
        "ridership": {},
        "travel_time": {},
        "otp": {},
        "coverage": {}
    }

    # Ridership
    comparison_json["ridership"]["unique_users"] = {
        "before": before_scores.get("ridership_unique_persons", 0),
        "after": after_scores.get("ridership_unique_persons", 0),
        "diff": after_scores.get("ridership_unique_persons", 0) - before_scores.get("ridership_unique_persons", 0),
        "percent_change": round((after_scores.get("ridership_unique_persons", 0) - before_scores.get("ridership_unique_persons", 0)) / before_scores.get("ridership_unique_persons", 1) * 100, 2)
    }
    comparison_json["ridership"]["usage_percentage"] = {
        "before": before_scores.get("ridership_percentage", 0),
        "after": after_scores.get("ridership_percentage", 0),
        "diff": after_scores.get("ridership_percentage", 0) - before_scores.get("ridership_percentage", 0)
    }
    comparison_json["ridership"]["total_population"] = {
        "before": before_scores.get("total_population", 0),
        "after": after_scores.get("total_population", 0)
    }

    # Travel Time
    comparison_json["travel_time"]["total_bus_time"] = {
        "before": before_scores.get("bus_travel_time_total", 0),
        "after": after_scores.get("bus_travel_time_total", 0),
        "diff": after_scores.get("bus_travel_time_total", 0) - before_scores.get("bus_travel_time_total", 0),
        "percent_change": round((after_scores.get("bus_travel_time_total", 0) - before_scores.get("bus_travel_time_total", 0)) / before_scores.get("bus_travel_time_total", 1) * 100, 2)
    }
    comparison_json["travel_time"]["total_car_time"] = {
        "before": before_scores.get("car_travel_time_total", 0),
        "after": after_scores.get("car_travel_time_total", 0),
        "diff": after_scores.get("car_travel_time_total", 0) - before_scores.get("car_travel_time_total", 0),
        "percent_change": round((after_scores.get("car_travel_time_total", 0) - before_scores.get("car_travel_time_total", 0)) / before_scores.get("car_travel_time_total", 1) * 100, 2)
    }

    # OTP
    comparison_json["otp"]["on_time_percentage"] = {
        "before": before_scores.get("otp_percentage", 0),
        "after": after_scores.get("otp_percentage", 0),
        "diff": after_scores.get("otp_percentage", 0) - before_scores.get("otp_percentage", 0)
    }
    
    # Coverage
    comparison_json["coverage"]["population_covered_percent"] = {
        "before": before_scores.get("coverage_percentage", 0),
        "after": after_scores.get("coverage_percentage", 0),
        "diff": after_scores.get("coverage_percentage", 0) - before_scores.get("coverage_percentage", 0)
    }
    comparison_json["coverage"]["population_covered_count"] = {
        "before": before_scores.get("coverage_pop_covered", 0),
        "after": after_scores.get("coverage_pop_covered", 0),
        "diff": after_scores.get("coverage_pop_covered", 0) - before_scores.get("coverage_pop_covered", 0)
    }

    # Save Comparison JSON
    comp_json_path = os.path.join(output_base_dir, "comparison_summary.json")
    with open(comp_json_path, 'w', encoding='utf-8') as f:
        json.dump(comparison_json, f, indent=4)
    
    print(json.dumps(comparison_json, indent=4))
    print(f"\nFull results saved to: {output_base_dir}")

if __name__ == "__main__":
    main()
